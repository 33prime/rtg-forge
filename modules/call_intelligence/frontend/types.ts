/**
 * Call Intelligence Module — TypeScript types.
 *
 * These are standalone types for the module. They do NOT depend
 * on any external type definitions from your project.
 */

// ---------------------------------------------------------------------------
// Recording
// ---------------------------------------------------------------------------

export type RecordingStatus =
  | 'pending'
  | 'bot_scheduled'
  | 'recording'
  | 'transcribing'
  | 'analyzing'
  | 'complete'
  | 'skipped'
  | 'failed';

export interface CallRecording {
  id: string;
  contact_name: string | null;
  contact_email: string | null;
  contact_metadata: Record<string, unknown>;
  recall_bot_id: string | null;
  recall_status: string | null;
  recording_url: string | null;
  audio_url: string | null;
  video_url: string | null;
  duration_seconds: number | null;
  meeting_url: string | null;
  status: RecordingStatus;
  error_log: unknown;
  created_at: string;
  updated_at: string;
}

// ---------------------------------------------------------------------------
// Transcript
// ---------------------------------------------------------------------------

export interface TranscriptSegment {
  speaker: string;
  text: string;
  start: number;
  end: number;
}

export interface CallTranscript {
  id: string;
  call_recording_id: string;
  full_text: string;
  segments: TranscriptSegment[];
  speaker_map: Record<string, string>;
  word_count: number | null;
  duration_seconds: number | null;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Analysis
// ---------------------------------------------------------------------------

export interface EngagementPoint {
  timestamp: string;
  level: number;
  note: string;
}

export interface TalkRatio {
  presenter: number;
  prospect: number;
}

export interface ProspectReadiness {
  urgency_score: number;
  mode: 'exploring' | 'evaluating' | 'ready_to_buy' | 'not_interested';
  accelerators: string[];
  follow_up_strategy: string;
}

export interface CallAnalysis {
  id: string;
  call_recording_id: string;
  analysis_model: string | null;
  analysis_tokens_used: number | null;
  executive_summary: string | null;
  engagement_score: number | null;
  prospect_readiness_score: number | null;
  talk_ratio: TalkRatio | null;
  engagement_timeline: EngagementPoint[] | null;
  prospect_readiness: ProspectReadiness | null;
  custom_dimensions: Record<string, unknown>;
  raw_analysis: unknown;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Feature Insights
// ---------------------------------------------------------------------------

export type Reaction = 'positive' | 'negative' | 'neutral' | 'confused';

export interface CallFeatureInsight {
  id: string;
  call_analysis_id: string;
  call_recording_id: string;
  feature_name: string;
  reaction: Reaction;
  is_feature_request: boolean;
  is_aha_moment: boolean;
  description: string | null;
  quote: string | null;
  timestamp_start: string | null;
  timestamp_end: string | null;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Signals
// ---------------------------------------------------------------------------

export interface CallSignal {
  id: string;
  call_analysis_id: string;
  call_recording_id: string;
  signal_type: string;
  title: string;
  description: string | null;
  intensity: number | null;
  quote: string | null;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Coaching Moments
// ---------------------------------------------------------------------------

export type MomentType =
  | 'strength'
  | 'improvement'
  | 'missed_opportunity'
  | 'objection_handled'
  | 'objection_missed';

export interface CallCoachingMoment {
  id: string;
  call_analysis_id: string;
  call_recording_id: string;
  moment_type: MomentType;
  title: string;
  description: string | null;
  suggestion: string | null;
  quote: string | null;
  timestamp_start: string | null;
  timestamp_end: string | null;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Highlights (merged from features + coaching for the timeline)
// ---------------------------------------------------------------------------

export type HighlightType =
  | 'aha_moment'
  | 'positive'
  | 'negative'
  | 'confused'
  | 'strength'
  | 'improvement'
  | 'missed_opportunity';

export interface Highlight {
  id: string;
  type: HighlightType;
  title: string;
  description: string | null;
  quote: string | null;
  startSeconds: number;
  endSeconds: number;
}

// ---------------------------------------------------------------------------
// API response shapes
// ---------------------------------------------------------------------------

export interface CallDetails {
  transcript: CallTranscript | null;
  analysis: CallAnalysis | null;
  feature_insights: CallFeatureInsight[];
  signals: CallSignal[];
  coaching_moments: CallCoachingMoment[];
}

export interface ScheduleResponse {
  success: boolean;
  recording_id: string | null;
  recall_bot_id: string | null;
  status: RecordingStatus;
  message: string;
}

export interface AnalyzeResponse {
  success: boolean;
  analysis_id: string | null;
  engagement_score: number | null;
  tokens_used: number | null;
  dimensions_processed: string[];
  message: string;
}
