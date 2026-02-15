/**
 * Call Intelligence Module — Detail View Component.
 *
 * Full call analysis view with:
 *   - Video player with highlight timeline markers
 *   - Synchronized transcript with clickable timestamps
 *   - Key moments panel
 *   - Tabbed analysis (Summary, Features, Signals, Coaching)
 *
 * Dependencies: recharts, lucide-react, shadcn/ui.
 * Adapt imports to match your component library paths.
 */

'use client';

import {
  ArrowLeft,
  Lightbulb,
  Loader2,
  Play,
  RefreshCw,
  Sparkles,
  Target,
  ThumbsDown,
  ThumbsUp,
  TrendingDown,
  TrendingUp,
} from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { CallIntelligenceState } from './useCallIntelligence';
import type { Highlight, HighlightType } from './types';
import {
  formatDuration,
  formatTimestamp,
  HIGHLIGHT_MARKER_COLORS,
  HIGHLIGHT_STYLES,
  parseTimestamp,
  scoreColor,
} from './utils';

interface Props {
  recordingId: string;
  calls: CallIntelligenceState;
  onBack: () => void;
}

type AnalysisTab = 'summary' | 'features' | 'signals' | 'coaching';

export function CallDetailView({ recordingId, calls, onBack }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [videoDuration, setVideoDuration] = useState(0);
  const [activeHighlight, setActiveHighlight] = useState<Highlight | null>(null);
  const [activeTab, setActiveTab] = useState<AnalysisTab>('summary');

  const recording = calls.recordings.find((r) => r.id === recordingId);
  const transcript = calls.transcripts[recordingId];
  const analysis = calls.analyses[recordingId];
  const features = calls.featureInsights[recordingId] ?? [];
  const sigs = calls.signals[recordingId] ?? [];
  const moments = calls.coachingMoments[recordingId] ?? [];
  const isReanalyzing = calls.reanalyzing === recordingId;

  // Build highlights from features + coaching
  const highlights = buildHighlights(features, moments);

  // Video event listeners
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const onMeta = () => setVideoDuration(video.duration);
    const onTime = () => {
      if (activeHighlight && video.currentTime >= activeHighlight.endSeconds) {
        video.pause();
      }
    };

    video.addEventListener('loadedmetadata', onMeta);
    video.addEventListener('timeupdate', onTime);
    return () => {
      video.removeEventListener('loadedmetadata', onMeta);
      video.removeEventListener('timeupdate', onTime);
    };
  }, [activeHighlight]);

  const seekTo = (seconds: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = seconds;
    }
  };

  const playHighlight = (h: Highlight) => {
    setActiveHighlight(h);
    seekTo(h.startSeconds);
    videoRef.current?.play();
  };

  if (!recording) {
    return <div className="p-8 text-center text-gray-500">Recording not found</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <button onClick={onBack} className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900">
          <ArrowLeft className="h-4 w-4" /> Back to recordings
        </button>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500">
            {formatDuration(recording.duration_seconds)}
          </span>
          <button
            onClick={() => calls.reanalyzeCall(recordingId)}
            disabled={isReanalyzing}
            className="flex items-center gap-2 rounded-md bg-gray-900 px-3 py-1.5 text-sm text-white hover:bg-gray-700 disabled:opacity-50"
          >
            {isReanalyzing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            Re-analyze
          </button>
        </div>
      </div>

      {/* Contact info */}
      <div>
        <h2 className="text-xl font-semibold">{recording.contact_name || 'Unknown Contact'}</h2>
        {recording.contact_email && (
          <p className="text-sm text-gray-500">{recording.contact_email}</p>
        )}
      </div>

      {/* Video player */}
      {recording.video_url && (
        <div className="rounded-lg overflow-hidden bg-black">
          <video
            ref={videoRef}
            src={recording.video_url}
            controls
            className="w-full max-h-[400px]"
          />
          {/* Highlight markers on timeline */}
          {videoDuration > 0 && highlights.length > 0 && (
            <div className="relative h-3 bg-gray-800">
              {highlights.map((h) => {
                const left = (h.startSeconds / videoDuration) * 100;
                const width = Math.max(
                  ((h.endSeconds - h.startSeconds) / videoDuration) * 100,
                  0.5
                );
                return (
                  <button
                    key={h.id}
                    onClick={() => playHighlight(h)}
                    className="absolute top-0 h-full opacity-80 hover:opacity-100 transition-opacity"
                    style={{
                      left: `${left}%`,
                      width: `${width}%`,
                      backgroundColor: HIGHLIGHT_MARKER_COLORS[h.type],
                    }}
                    title={h.title}
                  />
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Key Moments */}
      {highlights.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-2">Key Moments</h3>
          <div className="flex gap-2 overflow-x-auto pb-2">
            {highlights.map((h) => {
              const style = HIGHLIGHT_STYLES[h.type];
              const isActive = activeHighlight?.id === h.id;
              return (
                <button
                  key={h.id}
                  onClick={() => playHighlight(h)}
                  className={`flex-shrink-0 rounded-lg border p-3 text-left w-48 transition-all ${style.bg} ${style.border} ${isActive ? 'ring-2 ring-offset-1 ring-gray-400' : ''}`}
                >
                  <div className="flex items-center gap-1.5 mb-1">
                    <span className={`text-xs font-medium ${style.text}`}>{style.label}</span>
                    {isActive && <Play className="h-3 w-3 text-gray-500" />}
                  </div>
                  <div className="text-xs font-medium text-gray-900 line-clamp-2">{h.title}</div>
                  {h.quote && (
                    <div className="mt-1 text-xs text-gray-500 line-clamp-1 italic">
                      &ldquo;{h.quote}&rdquo;
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Transcript + Analysis layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Transcript panel */}
        {transcript && (
          <div className="rounded-lg border bg-white p-4 max-h-[600px] overflow-y-auto">
            <h3 className="text-sm font-medium text-gray-700 mb-3">
              Transcript
              {transcript.word_count && (
                <span className="ml-2 text-gray-400 font-normal">
                  ({transcript.word_count.toLocaleString()} words)
                </span>
              )}
            </h3>
            <div className="space-y-3">
              {transcript.segments.length > 0 ? (
                transcript.segments.map((seg, i) => {
                  const speaker =
                    transcript.speaker_map[seg.speaker] ?? seg.speaker;
                  return (
                    <div key={i} className="group">
                      <div className="flex items-baseline gap-2">
                        <button
                          onClick={() => seekTo(seg.start)}
                          className="text-xs text-blue-500 hover:text-blue-700 font-mono shrink-0"
                        >
                          {formatTimestamp(seg.start)}
                        </button>
                        <span className="text-xs font-medium text-gray-500">{speaker}</span>
                      </div>
                      <p className="text-sm text-gray-800 ml-16">{seg.text}</p>
                    </div>
                  );
                })
              ) : (
                <p className="text-sm text-gray-700 whitespace-pre-wrap">
                  {transcript.full_text}
                </p>
              )}
            </div>
          </div>
        )}

        {/* Analysis panel */}
        {analysis && (
          <div className="rounded-lg border bg-white p-4 max-h-[600px] overflow-y-auto">
            {/* Tab navigation */}
            <div className="flex gap-1 mb-4 border-b">
              {(['summary', 'features', 'signals', 'coaching'] as AnalysisTab[]).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-3 py-2 text-sm font-medium capitalize transition-colors ${
                    activeTab === tab
                      ? 'border-b-2 border-gray-900 text-gray-900'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>

            {/* Summary tab */}
            {activeTab === 'summary' && (
              <div className="space-y-4">
                {/* Score cards */}
                <div className="grid grid-cols-3 gap-3">
                  <ScoreCard label="Engagement" score={analysis.engagement_score} max={10} />
                  <ScoreCard
                    label="Readiness"
                    score={analysis.prospect_readiness?.urgency_score ?? null}
                    max={10}
                  />
                  <ScoreCard
                    label="Talk Ratio"
                    value={
                      analysis.talk_ratio
                        ? `${Math.round(analysis.talk_ratio.prospect * 100)}% prospect`
                        : null
                    }
                  />
                </div>

                {/* Executive summary */}
                {analysis.executive_summary && (
                  <div>
                    <h4 className="text-xs font-medium text-gray-500 mb-1">Executive Summary</h4>
                    <p className="text-sm text-gray-800 whitespace-pre-wrap">
                      {analysis.executive_summary}
                    </p>
                  </div>
                )}

                {/* Engagement timeline chart */}
                {analysis.engagement_timeline && analysis.engagement_timeline.length > 0 && (
                  <div>
                    <h4 className="text-xs font-medium text-gray-500 mb-2">
                      Engagement Timeline
                    </h4>
                    <ResponsiveContainer width="100%" height={150}>
                      <LineChart data={analysis.engagement_timeline}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="timestamp" tick={{ fontSize: 10 }} />
                        <YAxis domain={[0, 10]} tick={{ fontSize: 10 }} />
                        <Tooltip />
                        <Line
                          type="monotone"
                          dataKey="level"
                          stroke="#0d9488"
                          strokeWidth={2}
                          dot={{ r: 3 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {/* Custom dimensions */}
                {analysis.custom_dimensions &&
                  Object.keys(analysis.custom_dimensions).length > 0 && (
                    <div>
                      <h4 className="text-xs font-medium text-gray-500 mb-1">
                        Custom Dimensions
                      </h4>
                      <pre className="text-xs bg-gray-50 p-3 rounded overflow-x-auto">
                        {JSON.stringify(analysis.custom_dimensions, null, 2)}
                      </pre>
                    </div>
                  )}
              </div>
            )}

            {/* Features tab */}
            {activeTab === 'features' && (
              <div className="space-y-3">
                {features.length === 0 && (
                  <p className="text-sm text-gray-500 py-4 text-center">No feature insights</p>
                )}
                {features.map((f) => (
                  <div key={f.id} className="rounded border p-3">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-sm">{f.feature_name}</span>
                      <ReactionBadge reaction={f.reaction} />
                      {f.is_aha_moment && (
                        <span className="inline-flex items-center gap-1 rounded-full bg-yellow-50 px-2 py-0.5 text-xs text-yellow-700">
                          <Lightbulb className="h-3 w-3" /> Aha!
                        </span>
                      )}
                      {f.is_feature_request && (
                        <span className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2 py-0.5 text-xs text-blue-700">
                          <Sparkles className="h-3 w-3" /> Request
                        </span>
                      )}
                    </div>
                    {f.description && (
                      <p className="text-xs text-gray-600">{f.description}</p>
                    )}
                    {f.quote && (
                      <p className="text-xs text-gray-500 italic mt-1">
                        &ldquo;{f.quote}&rdquo;
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Signals tab */}
            {activeTab === 'signals' && (
              <div className="space-y-3">
                {sigs.length === 0 && (
                  <p className="text-sm text-gray-500 py-4 text-center">No signals extracted</p>
                )}
                {sigs.map((s) => (
                  <div key={s.id} className="rounded border p-3">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-700">
                        {s.signal_type.replace(/_/g, ' ')}
                      </span>
                      <span className="font-medium text-sm">{s.title}</span>
                      {s.intensity != null && (
                        <span className={`text-xs font-bold ${scoreColor(s.intensity)}`}>
                          {s.intensity}/10
                        </span>
                      )}
                    </div>
                    {s.description && (
                      <p className="text-xs text-gray-600">{s.description}</p>
                    )}
                    {s.quote && (
                      <p className="text-xs text-gray-500 italic mt-1">
                        &ldquo;{s.quote}&rdquo;
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Coaching tab */}
            {activeTab === 'coaching' && (
              <div className="space-y-3">
                {moments.length === 0 && (
                  <p className="text-sm text-gray-500 py-4 text-center">
                    No coaching moments
                  </p>
                )}
                {moments.map((m) => {
                  const Icon = MOMENT_ICONS[m.moment_type] ?? Target;
                  const color = MOMENT_COLORS[m.moment_type] ?? 'text-gray-600';
                  return (
                    <div key={m.id} className="rounded border p-3">
                      <div className="flex items-center gap-2 mb-1">
                        <Icon className={`h-4 w-4 ${color}`} />
                        <span className="font-medium text-sm">{m.title}</span>
                        <span className="text-xs text-gray-400 capitalize">
                          {m.moment_type.replace(/_/g, ' ')}
                        </span>
                      </div>
                      {m.description && (
                        <p className="text-xs text-gray-600">{m.description}</p>
                      )}
                      {m.suggestion && (
                        <p className="text-xs text-teal-700 mt-1">
                          <strong>Suggestion:</strong> {m.suggestion}
                        </p>
                      )}
                      {m.quote && (
                        <p className="text-xs text-gray-500 italic mt-1">
                          &ldquo;{m.quote}&rdquo;
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* No analysis yet */}
        {!analysis && !calls.loading && (
          <div className="rounded-lg border bg-white p-8 text-center">
            <p className="text-gray-500">
              {recording.status === 'analyzing'
                ? 'Analysis in progress...'
                : 'No analysis available. Click Re-analyze to start.'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function buildHighlights(
  features: { id: string; feature_name: string; reaction: string; is_aha_moment: boolean; description: string | null; quote: string | null; timestamp_start: string | null; timestamp_end: string | null }[],
  moments: { id: string; moment_type: string; title: string; description: string | null; quote: string | null; timestamp_start: string | null; timestamp_end: string | null }[],
): Highlight[] {
  const highlights: Highlight[] = [];

  for (const f of features) {
    const start = parseTimestamp(f.timestamp_start);
    const end = parseTimestamp(f.timestamp_end) || start + 15;
    if (start === 0 && end === 15 && !f.timestamp_start) continue;
    const type: HighlightType = f.is_aha_moment
      ? 'aha_moment'
      : (f.reaction as HighlightType) ?? 'positive';
    highlights.push({
      id: f.id,
      type,
      title: f.feature_name,
      description: f.description,
      quote: f.quote,
      startSeconds: start,
      endSeconds: end,
    });
  }

  for (const m of moments) {
    const start = parseTimestamp(m.timestamp_start);
    const end = parseTimestamp(m.timestamp_end) || start + 15;
    if (start === 0 && end === 15 && !m.timestamp_start) continue;
    highlights.push({
      id: m.id,
      type: m.moment_type as HighlightType,
      title: m.title,
      description: m.description,
      quote: m.quote,
      startSeconds: start,
      endSeconds: end,
    });
  }

  return highlights.sort((a, b) => a.startSeconds - b.startSeconds);
}

function ScoreCard({
  label,
  score,
  max,
  value,
}: {
  label: string;
  score?: number | null;
  max?: number;
  value?: string | null;
}) {
  const display = value ?? (score != null ? `${score}/${max}` : '--');
  return (
    <div className="rounded-lg bg-gray-50 p-3 text-center">
      <div className="text-xs text-gray-500">{label}</div>
      <div
        className={`text-lg font-bold mt-1 ${score != null ? scoreColor(score, max ?? 10) : 'text-gray-400'}`}
      >
        {display}
      </div>
    </div>
  );
}

function ReactionBadge({ reaction }: { reaction: string }) {
  const config: Record<string, { icon: typeof ThumbsUp; color: string }> = {
    positive: { icon: ThumbsUp, color: 'text-emerald-600' },
    negative: { icon: ThumbsDown, color: 'text-red-600' },
    neutral: { icon: Target, color: 'text-gray-500' },
    confused: { icon: TrendingDown, color: 'text-orange-500' },
  };
  const { icon: Icon, color } = config[reaction] ?? config.neutral;
  return <Icon className={`h-3.5 w-3.5 ${color}`} />;
}

const MOMENT_ICONS: Record<string, typeof ThumbsUp> = {
  strength: TrendingUp,
  improvement: TrendingDown,
  missed_opportunity: Target,
  objection_handled: ThumbsUp,
  objection_missed: ThumbsDown,
};

const MOMENT_COLORS: Record<string, string> = {
  strength: 'text-blue-600',
  improvement: 'text-purple-600',
  missed_opportunity: 'text-gray-500',
  objection_handled: 'text-emerald-600',
  objection_missed: 'text-red-600',
};
