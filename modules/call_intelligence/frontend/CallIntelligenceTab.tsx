/**
 * Call Intelligence Module — List View Component.
 *
 * Displays all call recordings in a table with summary stats.
 * Click a row to navigate to the detail view.
 *
 * Dependencies: shadcn/ui (Table, Badge), lucide-react, your project's UI kit.
 * Adapt imports to match your component library paths.
 */

'use client';

import { Mic } from 'lucide-react';
import { useState } from 'react';
import type { CallIntelligenceState } from './useCallIntelligence';
import {
  formatDuration,
  recordingStatusColor,
  recordingStatusLabel,
  relativeTime,
  scoreBgColor,
  scoreColor,
} from './utils';
import { CallDetailView } from './CallDetailView';

interface Props {
  calls: CallIntelligenceState;
}

export function CallIntelligenceTab({ calls }: Props) {
  const [activeRecordingId, setActiveRecordingId] = useState<string | null>(null);

  const handleRowClick = async (recordingId: string) => {
    setActiveRecordingId(recordingId);
    await calls.fetchDetails(recordingId);
  };

  // Show detail view if a recording is selected
  if (activeRecordingId) {
    return (
      <CallDetailView
        recordingId={activeRecordingId}
        calls={calls}
        onBack={() => setActiveRecordingId(null)}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Total Calls" value={calls.totalCalls} />
        <StatCard label="Avg Engagement" value={`${calls.avgEngagement}/10`} />
        <StatCard label="Recordings" value={calls.recordings.length} />
        <StatCard
          label="Analyzing"
          value={calls.recordings.filter((r) => r.status === 'analyzing').length}
        />
      </div>

      {/* Loading state */}
      {calls.loading && (
        <div className="text-center py-12 text-gray-500">Loading recordings...</div>
      )}

      {/* Empty state */}
      {!calls.loading && calls.recordings.length === 0 && (
        <div className="text-center py-12">
          <Mic className="mx-auto h-12 w-12 text-gray-300" />
          <h3 className="mt-4 text-lg font-medium text-gray-900">No recordings yet</h3>
          <p className="mt-2 text-sm text-gray-500">
            Schedule a recording bot for your next meeting to get started.
          </p>
        </div>
      )}

      {/* Recordings table */}
      {!calls.loading && calls.recordings.length > 0 && (
        <div className="overflow-x-auto rounded-lg border">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Contact
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Date
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Duration
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">
                  Engagement
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {calls.recordings.map((rec) => {
                const analysis = calls.analyses[rec.id];
                return (
                  <tr
                    key={rec.id}
                    onClick={() => handleRowClick(rec.id)}
                    className="cursor-pointer hover:bg-gray-50 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <div className="font-medium text-gray-900">
                        {rec.contact_name || 'Unknown'}
                      </div>
                      {rec.contact_email && (
                        <div className="text-sm text-gray-500">{rec.contact_email}</div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {relativeTime(rec.created_at)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {formatDuration(rec.duration_seconds)}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${recordingStatusColor(rec.status)}`}
                      >
                        {recordingStatusLabel(rec.status)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      {analysis?.engagement_score != null ? (
                        <span
                          className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold ${scoreBgColor(analysis.engagement_score)} ${scoreColor(analysis.engagement_score)}`}
                        >
                          {analysis.engagement_score}
                        </span>
                      ) : (
                        <span className="text-gray-300">--</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg border bg-white p-4">
      <div className="text-sm text-gray-500">{label}</div>
      <div className="mt-1 text-2xl font-semibold">{value}</div>
    </div>
  );
}
