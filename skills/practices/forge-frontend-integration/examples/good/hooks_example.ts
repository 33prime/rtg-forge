/**
 * GOOD: Typed hooks with one hook per endpoint, proper cache invalidation,
 * and clean separation from components.
 *
 * This file is ~80% portable between projects. Only API_BASE changes.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type {
  FormDefinition,
  FormListResponse,
  CreateFormRequest,
  SubmitResponseRequest,
  SubmissionResponse,
  ProgressResponse,
} from './types';

const API_BASE = '/api/v1/intake';

// --- Queries: one per GET endpoint ---

export function useFormDefinitions(params?: { limit?: number; offset?: number }) {
  return useQuery<FormListResponse>({
    queryKey: ['forms', params],
    queryFn: async () => {
      const search = new URLSearchParams();
      if (params?.limit) search.set('limit', String(params.limit));
      if (params?.offset) search.set('offset', String(params.offset));
      const res = await fetch(`${API_BASE}/forms?${search}`);
      if (!res.ok) throw new Error('Failed to load forms');
      return res.json();
    },
  });
}

export function useFormDefinition(formId: string) {
  return useQuery<FormDefinition>({
    queryKey: ['forms', formId],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/forms/${formId}`);
      if (!res.ok) throw new Error('Form not found');
      return res.json();
    },
    enabled: !!formId,
  });
}

export function useParticipantProgress(participantId: string) {
  return useQuery<ProgressResponse>({
    queryKey: ['progress', participantId],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/progress/${participantId}`);
      if (!res.ok) throw new Error('Failed to load progress');
      return res.json();
    },
    enabled: !!participantId,
  });
}

// --- Mutations: one per write endpoint, with cache invalidation ---

export function useCreateForm() {
  const queryClient = useQueryClient();

  return useMutation<FormDefinition, Error, CreateFormRequest>({
    mutationFn: async (body) => {
      const res = await fetch(`${API_BASE}/forms`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error('Failed to create form');
      return res.json();
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['forms'] });
    },
  });
}

export function useSubmitResponse() {
  const queryClient = useQueryClient();

  return useMutation<SubmissionResponse, Error, SubmitResponseRequest & { formId: string }>({
    mutationFn: async ({ formId, ...body }) => {
      const res = await fetch(`${API_BASE}/forms/${formId}/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error('Failed to submit response');
      return res.json();
    },
    onSuccess: (_, variables) => {
      // Invalidate progress — submission changes completion state
      void queryClient.invalidateQueries({ queryKey: ['progress', variables.participant_id] });
    },
  });
}
