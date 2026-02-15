"""Call Intelligence service — orchestrates the full recording→analysis pipeline.

This is the main business logic layer. It coordinates:
  1. Bot scheduling (Recall.ai)
  2. Webhook handling (status updates)
  3. Transcription (Deepgram)
  4. Analysis (Claude via the analysis engine)
  5. Result storage (Supabase)
  6. Notifications (Slack)

NO FastAPI imports — this file is framework-agnostic per the Forge contract.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from supabase import AsyncClient as SupabaseClient

from .analysis.dimensions import resolve_dimensions
from .analysis.engine import AnalysisEngine, AnalysisError
from .config import CallIntelligenceConfig
from .models import (
    AnalysisResult,
    AnalyzeResponse,
    RecordingStatus,
    ScheduleRecordingRequest,
    ScheduleRecordingResponse,
    Transcript,
)
from .providers.deepgram import DeepgramClient, DeepgramError
from .providers.notifications import send_slack_notification
from .providers.recall import RecallClient, RecallError

logger = logging.getLogger(__name__)


class CallIntelligenceService:
    """Main service class — stateless, receives dependencies via constructor."""

    def __init__(
        self,
        settings: CallIntelligenceConfig,
        supabase: SupabaseClient,
    ) -> None:
        self.settings = settings
        self.db = supabase
        self.recall = RecallClient(settings)
        self.deepgram = DeepgramClient(settings)
        self.engine = AnalysisEngine(settings)

    # ------------------------------------------------------------------
    # 1. Schedule recording bot
    # ------------------------------------------------------------------

    async def schedule_bot(self, req: ScheduleRecordingRequest) -> ScheduleRecordingResponse:
        """Schedule a Recall.ai recording bot for a meeting."""
        if not self.recall.is_supported_platform(req.meeting_url):
            row = await self._insert_recording(req, RecordingStatus.skipped, {
                "reason": f"Unsupported platform: {req.meeting_url}"
            })
            return ScheduleRecordingResponse(
                success=False,
                recording_id=UUID(row["id"]),
                status=RecordingStatus.skipped,
                message="Meeting platform not supported",
            )

        row = await self._insert_recording(req, RecordingStatus.pending)
        recording_id = row["id"]

        if not self.settings.recall_api_key:
            await self._update_status(recording_id, RecordingStatus.failed, {
                "error": "RECALL_API_KEY not configured"
            })
            return ScheduleRecordingResponse(
                success=False,
                recording_id=UUID(recording_id),
                status=RecordingStatus.failed,
                message="Recall API key not configured",
            )

        try:
            bot_data = await self.recall.create_bot(req.meeting_url)
        except RecallError as e:
            await self._update_status(recording_id, RecordingStatus.failed, {"error": str(e)})
            return ScheduleRecordingResponse(
                success=False,
                recording_id=UUID(recording_id),
                status=RecordingStatus.failed,
                message=str(e),
            )

        bot_id = bot_data.get("id") or bot_data.get("bot_id")
        recall_status = (
            bot_data.get("status_changes", [{}])[0].get("code", "scheduled")
            if bot_data.get("status_changes")
            else "scheduled"
        )
        await self.db.table("call_recordings").update({
            "recall_bot_id": str(bot_id),
            "recall_status": recall_status,
            "status": RecordingStatus.bot_scheduled.value,
            "updated_at": _now(),
        }).eq("id", recording_id).execute()

        return ScheduleRecordingResponse(
            success=True,
            recording_id=UUID(recording_id),
            recall_bot_id=str(bot_id),
            status=RecordingStatus.bot_scheduled,
        )

    # ------------------------------------------------------------------
    # 2. Handle Recall.ai webhook
    # ------------------------------------------------------------------

    async def handle_recall_event(self, event: str, bot_id: str, payload: dict) -> None:
        """Process a Recall.ai webhook event.

        This runs as a background task — must not raise unhandled exceptions.
        """
        rec = None
        try:
            rec = await self._find_recording_by_bot(bot_id)
            if not rec:
                logger.info("No recording found for bot %s — ignoring", bot_id)
                return

            recording_id = rec["id"]

            if any(k in event for k in ("joining", "in_waiting_room", "in_call", "recording")):
                await self._update_status(recording_id, RecordingStatus.recording, recall_status=event)

            elif any(k in event for k in ("done", "complete", "ended")):
                await self._handle_call_completed(recording_id, bot_id, event, payload)

            elif any(k in event for k in ("fatal", "error", "failed")):
                await self._update_status(recording_id, RecordingStatus.failed,
                                          error_log={"event": event, "data": payload},
                                          recall_status=event)
            else:
                logger.info("Unhandled Recall event: %s", event)

        except Exception as e:
            logger.exception("Error handling Recall event %s for bot %s: %s", event, bot_id, e)
            try:
                if rec:
                    await self._update_status(rec["id"], RecordingStatus.failed,
                                              error_log={"error": str(e), "event": event})
            except Exception:
                logger.exception("Failed to update recording status after error")

    async def _handle_call_completed(
        self, recording_id: str, bot_id: str, event: str, payload: dict,
    ) -> None:
        """Handle bot.done — fetch URLs, transcribe, trigger analysis."""
        media = {"recording_url": None, "video_url": None, "audio_url": None}
        duration = None

        if self.settings.recall_api_key:
            try:
                bot_data = await self.recall.fetch_bot(bot_id)
                media = self.recall.extract_media_urls(bot_data)
                duration = self.recall.compute_duration(bot_data)
            except RecallError as e:
                logger.warning("Failed to fetch bot details: %s", e)

        await self.db.table("call_recordings").update({
            **media,
            "duration_seconds": duration,
            "recall_status": "done",
            "status": RecordingStatus.transcribing.value,
            "updated_at": _now(),
        }).eq("id", recording_id).execute()

        audio_source = media.get("audio_url") or media.get("video_url") or media.get("recording_url")
        if self.settings.deepgram_api_key and audio_source:
            try:
                transcript = await self.deepgram.transcribe_url(audio_source)
                await self._save_transcript(recording_id, transcript)
                await self._update_status(recording_id, RecordingStatus.analyzing)
                asyncio.create_task(self._run_analysis_safe(recording_id))
            except DeepgramError as e:
                logger.error("Transcription failed: %s", e)
                await self._update_status(recording_id, RecordingStatus.failed,
                                          error_log={"error": f"Transcription failed: {e}"})
        else:
            logger.warning("No Deepgram key or audio source — marking complete without analysis")
            await self._update_status(recording_id, RecordingStatus.complete)

    # ------------------------------------------------------------------
    # 3. Run analysis
    # ------------------------------------------------------------------

    async def analyze_call(
        self,
        recording_id: str | UUID,
        context_blocks: dict[str, str] | None = None,
    ) -> AnalyzeResponse:
        """Run the analysis engine on a recording's transcript."""
        recording_id = str(recording_id)

        res = await self.db.table("call_transcripts").select("*").eq(
            "call_recording_id", recording_id
        ).order("created_at", desc=True).limit(1).execute()

        if not res.data:
            return AnalyzeResponse(success=False, message="No transcript found")

        transcript_data = res.data[0]
        segments = transcript_data.get("segments", [])
        speaker_map = transcript_data.get("speaker_map", {})
        if segments:
            lines = []
            for seg in segments:
                speaker = speaker_map.get(seg["speaker"], seg["speaker"])
                lines.append(f"[{speaker}]: {seg['text']}")
            transcript_text = "\n".join(lines)
        else:
            transcript_text = transcript_data.get("full_text", "")

        if not transcript_text.strip():
            return AnalyzeResponse(success=False, message="Transcript is empty")

        dimensions = resolve_dimensions(
            self.settings.get_active_packs(),
            self._load_custom_dimensions(),
        )

        try:
            result, raw_response = await self.engine.analyze(
                transcript_text, dimensions, context_blocks
            )
        except AnalysisError as e:
            await self._update_status(recording_id, RecordingStatus.failed,
                                      error_log={"error": f"Analysis failed: {e}"})
            return AnalyzeResponse(success=False, message=str(e))

        tokens_used = raw_response.get("usage", {}).get("output_tokens", 0)
        analysis_id = await self._save_analysis(recording_id, result, raw_response, tokens_used)
        await self._save_child_records(recording_id, analysis_id, result)
        await self._update_status(recording_id, RecordingStatus.complete)
        await self._notify(recording_id, result)

        return AnalyzeResponse(
            success=True,
            analysis_id=UUID(analysis_id),
            engagement_score=result.engagement_score,
            tokens_used=tokens_used,
            dimensions_processed=[d.key for d in dimensions],
        )

    async def _run_analysis_safe(self, recording_id: str) -> None:
        """Wrapper for fire-and-forget analysis — catches all exceptions."""
        try:
            await self.analyze_call(recording_id)
        except Exception as e:
            logger.exception("Background analysis failed for %s: %s", recording_id, e)
            try:
                await self._update_status(recording_id, RecordingStatus.failed,
                                          error_log={"error": f"Analysis failed: {e}"})
            except Exception:
                logger.exception("Failed to update status after analysis error")

    # ------------------------------------------------------------------
    # 4. List / get recordings
    # ------------------------------------------------------------------

    async def list_recordings(self) -> list[dict]:
        res = await self.db.table("call_recordings").select("*").order(
            "created_at", desc=True
        ).execute()
        return res.data or []

    async def get_recording(self, recording_id: str | UUID) -> dict | None:
        res = await self.db.table("call_recordings").select("*").eq(
            "id", str(recording_id)
        ).maybe_single().execute()
        return res.data

    async def get_call_details(self, recording_id: str | UUID) -> dict:
        """Fetch all analysis data for a recording (parallel queries)."""
        rid = str(recording_id)
        transcript_q = self.db.table("call_transcripts").select("*").eq("call_recording_id", rid).maybe_single().execute()
        analysis_q = self.db.table("call_analyses").select("*").eq("call_recording_id", rid).order("created_at", desc=True).limit(1).execute()
        features_q = self.db.table("call_feature_insights").select("*").eq("call_recording_id", rid).execute()
        signals_q = self.db.table("call_signals").select("*").eq("call_recording_id", rid).execute()
        coaching_q = self.db.table("call_coaching_moments").select("*").eq("call_recording_id", rid).execute()

        transcript_res, analysis_res, features_res, signals_res, coaching_res = await asyncio.gather(
            transcript_q, analysis_q, features_q, signals_q, coaching_q
        )

        return {
            "transcript": transcript_res.data,
            "analysis": analysis_res.data[0] if analysis_res.data else None,
            "feature_insights": features_res.data or [],
            "signals": signals_res.data or [],
            "coaching_moments": coaching_res.data or [],
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _insert_recording(
        self, req: ScheduleRecordingRequest, status: RecordingStatus, error_log: dict | None = None,
    ) -> dict:
        res = await self.db.table("call_recordings").insert({
            "meeting_url": req.meeting_url,
            "contact_name": req.contact_name,
            "contact_email": req.contact_email,
            "contact_metadata": req.contact_metadata,
            "status": status.value,
            "error_log": error_log,
        }).execute()
        return res.data[0]

    async def _update_status(
        self, recording_id: str, status: RecordingStatus,
        error_log: dict | None = None, recall_status: str | None = None,
    ) -> None:
        update: dict[str, Any] = {"status": status.value, "updated_at": _now()}
        if error_log is not None:
            update["error_log"] = error_log
        if recall_status is not None:
            update["recall_status"] = recall_status
        await self.db.table("call_recordings").update(update).eq("id", recording_id).execute()

    async def _find_recording_by_bot(self, bot_id: str) -> dict | None:
        res = await self.db.table("call_recordings").select("id, status").eq(
            "recall_bot_id", bot_id
        ).maybe_single().execute()
        return res.data

    async def _save_transcript(self, recording_id: str, transcript: Transcript) -> None:
        await self.db.table("call_transcripts").delete().eq("call_recording_id", recording_id).execute()
        await self.db.table("call_transcripts").insert({
            "call_recording_id": recording_id,
            "full_text": transcript.full_text,
            "segments": [s.model_dump() for s in transcript.segments],
            "speaker_map": transcript.speaker_map,
            "word_count": transcript.word_count,
            "duration_seconds": transcript.duration_seconds,
        }).execute()

    async def _save_analysis(
        self, recording_id: str, result: AnalysisResult, raw_response: dict, tokens_used: int,
    ) -> str:
        res = await self.db.table("call_analyses").insert({
            "call_recording_id": recording_id,
            "analysis_model": self.settings.analysis_model,
            "analysis_tokens_used": tokens_used,
            "executive_summary": result.executive_summary,
            "engagement_score": result.engagement_score,
            "prospect_readiness_score": result.prospect_readiness.urgency_score,
            "talk_ratio": result.talk_ratio.model_dump(),
            "engagement_timeline": [p.model_dump() for p in result.engagement_timeline],
            "prospect_readiness": result.prospect_readiness.model_dump(),
            "custom_dimensions": result.custom_dimensions,
            "raw_analysis": raw_response,
        }).execute()
        return res.data[0]["id"]

    async def _save_child_records(
        self, recording_id: str, analysis_id: str, result: AnalysisResult,
    ) -> None:
        """Save feature insights, signals, coaching moments, etc. in parallel."""
        tasks = []
        if result.feature_insights:
            rows = [{"call_analysis_id": analysis_id, "call_recording_id": recording_id, **f.model_dump()} for f in result.feature_insights]
            tasks.append(self.db.table("call_feature_insights").insert(rows).execute())
        if result.signals:
            rows = [{"call_analysis_id": analysis_id, "call_recording_id": recording_id, **s.model_dump()} for s in result.signals]
            tasks.append(self.db.table("call_signals").insert(rows).execute())
        if result.coaching_moments:
            rows = [{"call_analysis_id": analysis_id, "call_recording_id": recording_id, **m.model_dump()} for m in result.coaching_moments]
            tasks.append(self.db.table("call_coaching_moments").insert(rows).execute())
        if result.content_nuggets:
            rows = [{"call_analysis_id": analysis_id, "call_recording_id": recording_id, **n.model_dump()} for n in result.content_nuggets]
            tasks.append(self.db.table("call_content_nuggets").insert(rows).execute())
        if result.competitive_intel:
            rows = [{"call_analysis_id": analysis_id, "call_recording_id": recording_id, **c.model_dump()} for c in result.competitive_intel]
            tasks.append(self.db.table("call_competitive_mentions").insert(rows).execute())
        if tasks:
            await asyncio.gather(*tasks)

    async def _notify(self, recording_id: str, result: AnalysisResult) -> None:
        if not self.settings.slack_webhook_url:
            return
        rec = await self.get_recording(recording_id)
        contact_name = (rec or {}).get("contact_name", "Unknown")
        module_config = self.settings.load_module_config()
        template = module_config.get("notifications", {}).get(
            "slack_template",
            "Call analysis complete for {contact_name} — Engagement: {engagement_score}/10",
        )
        await send_slack_notification(
            self.settings.slack_webhook_url, template,
            {"contact_name": contact_name, "engagement_score": result.engagement_score,
             "readiness_score": result.prospect_readiness.urgency_score},
        )

    def _load_custom_dimensions(self) -> list[dict] | None:
        config = self.settings.load_module_config()
        dims = config.get("analysis", {}).get("custom_dimensions", [])
        return [d for d in dims if not d.get("_example")] or None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
