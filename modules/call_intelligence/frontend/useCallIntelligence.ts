/**
 * Call Intelligence Module — React data hook.
 *
 * Fetches recordings and analysis data from the FastAPI backend.
 * Replace API_BASE_URL with your actual endpoint.
 *
 * Usage:
 *   const calls = useCallIntelligence();
 *   // calls.recordings, calls.loading, calls.fetchDetails(id), etc.
 */

import { useCallback, useEffect, useState } from 'react';
import type {
  AnalyzeResponse,
  CallAnalysis,
  CallCoachingMoment,
  CallDetails,
  CallFeatureInsight,
  CallRecording,
  CallSignal,
  CallTranscript,
} from './types';

// --- CONFIGURE THIS ---
// Point to your FastAPI backend where the module router is mounted.
// Example: "https://your-api.railway.app/api/call-intelligence"
const API_BASE_URL =
  process.env.NEXT_PUBLIC_CALL_INTELLIGENCE_URL || '/api/call-intelligence';

// Optional: API key header for authenticated requests
const API_KEY = process.env.NEXT_PUBLIC_CALL_INTELLIGENCE_KEY || '';

function headers(): HeadersInit {
  const h: Record<string, string> = { 'Content-Type': 'application/json' };
  if (API_KEY) h['X-API-Key'] = API_KEY;
  return h;
}

export interface CallIntelligenceState {
  recordings: CallRecording[];
  transcripts: Record<string, CallTranscript>;
  analyses: Record<string, CallAnalysis>;
  featureInsights: Record<string, CallFeatureInsight[]>;
  signals: Record<string, CallSignal[]>;
  coachingMoments: Record<string, CallCoachingMoment[]>;
  loading: boolean;
  reanalyzing: string | null;

  // Aggregate stats
  totalCalls: number;
  avgEngagement: number;

  // Actions
  fetchRecordings: () => Promise<void>;
  fetchDetails: (recordingId: string) => Promise<void>;
  reanalyzeCall: (recordingId: string) => Promise<AnalyzeResponse | null>;
}

export function useCallIntelligence(): CallIntelligenceState {
  const [recordings, setRecordings] = useState<CallRecording[]>([]);
  const [transcripts, setTranscripts] = useState<Record<string, CallTranscript>>({});
  const [analyses, setAnalyses] = useState<Record<string, CallAnalysis>>({});
  const [featureInsights, setFeatureInsights] = useState<Record<string, CallFeatureInsight[]>>({});
  const [signals, setSignals] = useState<Record<string, CallSignal[]>>({});
  const [coachingMoments, setCoachingMoments] = useState<Record<string, CallCoachingMoment[]>>({});
  const [loading, setLoading] = useState(true);
  const [reanalyzing, setReanalyzing] = useState<string | null>(null);

  const fetchRecordings = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE_URL}/recordings`, { headers: headers() });
      if (res.ok) {
        const data: CallRecording[] = await res.json();
        setRecordings(data);
      }
    } catch (err) {
      console.error('Failed to fetch recordings:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchDetails = useCallback(async (recordingId: string) => {
    try {
      const res = await fetch(`${API_BASE_URL}/recordings/${recordingId}/details`, {
        headers: headers(),
      });
      if (!res.ok) return;
      const data: CallDetails = await res.json();

      if (data.transcript) {
        setTranscripts((prev) => ({ ...prev, [recordingId]: data.transcript! }));
      }
      if (data.analysis) {
        setAnalyses((prev) => ({ ...prev, [recordingId]: data.analysis! }));
      }
      setFeatureInsights((prev) => ({ ...prev, [recordingId]: data.feature_insights }));
      setSignals((prev) => ({ ...prev, [recordingId]: data.signals }));
      setCoachingMoments((prev) => ({ ...prev, [recordingId]: data.coaching_moments }));
    } catch (err) {
      console.error('Failed to fetch call details:', err);
    }
  }, []);

  const reanalyzeCall = useCallback(async (recordingId: string): Promise<AnalyzeResponse | null> => {
    try {
      setReanalyzing(recordingId);
      const res = await fetch(`${API_BASE_URL}/recordings/${recordingId}/analyze`, {
        method: 'POST',
        headers: headers(),
        body: JSON.stringify({ recording_id: recordingId }),
      });
      if (res.ok) {
        const data: AnalyzeResponse = await res.json();
        // Refresh details after re-analysis
        await fetchDetails(recordingId);
        return data;
      }
      return null;
    } catch (err) {
      console.error('Failed to re-analyze call:', err);
      return null;
    } finally {
      setReanalyzing(null);
    }
  }, [fetchDetails]);

  useEffect(() => {
    fetchRecordings();
  }, [fetchRecordings]);

  // Aggregate stats
  const completedRecordings = recordings.filter((r) => r.status === 'complete');
  const totalCalls = completedRecordings.length;
  const analysisValues = Object.values(analyses);
  const avgEngagement =
    analysisValues.length > 0
      ? Math.round(
          analysisValues.reduce((sum, a) => sum + (a.engagement_score ?? 0), 0) /
            analysisValues.length
        )
      : 0;

  return {
    recordings,
    transcripts,
    analyses,
    featureInsights,
    signals,
    coachingMoments,
    loading,
    reanalyzing,
    totalCalls,
    avgEngagement,
    fetchRecordings,
    fetchDetails,
    reanalyzeCall,
  };
}
