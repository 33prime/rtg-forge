/**
 * Call Intelligence Module — Utility functions.
 *
 * Standalone helpers for formatting, colors, and status labels.
 * No dependencies on external project code.
 */

import type { HighlightType, RecordingStatus } from './types';

// ---------------------------------------------------------------------------
// Recording status
// ---------------------------------------------------------------------------

export function recordingStatusColor(status: RecordingStatus): string {
  const map: Record<RecordingStatus, string> = {
    pending: 'bg-gray-100 text-gray-600',
    bot_scheduled: 'bg-blue-100 text-blue-700',
    recording: 'bg-red-100 text-red-700',
    transcribing: 'bg-amber-100 text-amber-700',
    analyzing: 'bg-amber-100 text-amber-700',
    complete: 'bg-emerald-100 text-emerald-700',
    skipped: 'bg-gray-100 text-gray-500',
    failed: 'bg-red-100 text-red-700',
  };
  return map[status] ?? 'bg-gray-100 text-gray-600';
}

export function recordingStatusLabel(status: RecordingStatus): string {
  const map: Record<RecordingStatus, string> = {
    pending: 'Pending',
    bot_scheduled: 'Bot Scheduled',
    recording: 'Recording',
    transcribing: 'Transcribing',
    analyzing: 'Analyzing',
    complete: 'Complete',
    skipped: 'Skipped',
    failed: 'Failed',
  };
  return map[status] ?? status;
}

// ---------------------------------------------------------------------------
// Duration / time formatting
// ---------------------------------------------------------------------------

export function formatDuration(seconds: number | null): string {
  if (!seconds) return '--';
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

export function formatTimestamp(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

export function parseTimestamp(ts: string | null): number {
  if (!ts) return 0;
  if (ts.includes(':')) {
    const parts = ts.split(':').map(Number);
    if (parts.length === 2) return parts[0] * 60 + parts[1];
    if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
  }
  const n = parseFloat(ts);
  return isNaN(n) ? 0 : n;
}

export function relativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

// ---------------------------------------------------------------------------
// Score colors
// ---------------------------------------------------------------------------

export function scoreColor(score: number, max: number = 10): string {
  const pct = score / max;
  if (pct >= 0.7) return 'text-emerald-600';
  if (pct >= 0.4) return 'text-amber-600';
  return 'text-red-600';
}

export function scoreBgColor(score: number, max: number = 10): string {
  const pct = score / max;
  if (pct >= 0.7) return 'bg-emerald-50';
  if (pct >= 0.4) return 'bg-amber-50';
  return 'bg-red-50';
}

// ---------------------------------------------------------------------------
// Highlight styles (for the video timeline)
// ---------------------------------------------------------------------------

export const HIGHLIGHT_STYLES: Record<
  HighlightType,
  { bg: string; border: string; text: string; label: string }
> = {
  aha_moment: { bg: 'bg-yellow-50', border: 'border-yellow-400', text: 'text-yellow-700', label: 'Aha!' },
  positive: { bg: 'bg-emerald-50', border: 'border-emerald-400', text: 'text-emerald-700', label: 'Positive' },
  negative: { bg: 'bg-red-50', border: 'border-red-400', text: 'text-red-700', label: 'Negative' },
  confused: { bg: 'bg-orange-50', border: 'border-orange-400', text: 'text-orange-700', label: 'Confused' },
  strength: { bg: 'bg-blue-50', border: 'border-blue-400', text: 'text-blue-700', label: 'Strength' },
  improvement: { bg: 'bg-purple-50', border: 'border-purple-400', text: 'text-purple-700', label: 'Improve' },
  missed_opportunity: { bg: 'bg-gray-50', border: 'border-gray-400', text: 'text-gray-700', label: 'Missed' },
};

export const HIGHLIGHT_MARKER_COLORS: Record<HighlightType, string> = {
  aha_moment: 'rgb(234, 179, 8)',
  positive: 'rgb(16, 185, 129)',
  negative: 'rgb(239, 68, 68)',
  confused: 'rgb(249, 115, 22)',
  strength: 'rgb(59, 130, 246)',
  improvement: 'rgb(168, 85, 247)',
  missed_opportunity: 'rgb(156, 163, 175)',
};
