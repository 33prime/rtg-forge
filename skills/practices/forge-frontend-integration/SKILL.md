# Forge Frontend Integration

When a project uses an RTG Forge backend module, the frontend must integrate with its API cleanly. This skill defines how to build the TypeScript layer that bridges a forge module's API to React components.

The frontend integration has three layers. Build them in order — each one depends on the previous.

```
Layer 1: types.ts      ← mirrors models.py (portable, rarely changes)
Layer 2: hooks.ts      ← typed React Query hooks per endpoint (mostly portable)
Layer 3: components    ← UI that consumes hooks (project-specific, built fresh)
```

---

## Layer 1: Types — Mirror the Backend Models

Every forge module has a `models.py` with Pydantic schemas. The frontend gets a `types.ts` that mirrors them exactly.

### Rules

1. **One type per Pydantic model.** Request models, response models, and enums all get TypeScript equivalents.
2. **Match field names exactly.** If the backend uses `snake_case`, use `camelCase` only if the API serializes that way (check the backend's `model_config` for alias generators). When in doubt, match the JSON the API actually returns.
3. **Use `z.infer` or plain interfaces — pick one per project and be consistent.** If the project uses Zod, define schemas and infer types. If not, use plain TypeScript interfaces.
4. **Never use `any`.** If you don't know the shape, read the backend `models.py` and type it correctly.

```typescript
// types.ts — mirrors participant_intake/models.py

export interface FormDefinition {
  id: string;
  title: string;
  description: string;
  questions: FormQuestion[];
  status: FormStatus;
  created_at: string;
}

export interface FormQuestion {
  id: string;
  label: string;
  type: QuestionType;
  required: boolean;
  options?: string[];       // only for 'select' | 'multiselect'
  validation?: string;      // regex pattern
}

export type QuestionType = 'text' | 'textarea' | 'select' | 'multiselect' | 'number' | 'date' | 'email';
export type FormStatus = 'draft' | 'active' | 'closed';

// --- Request types ---

export interface CreateFormRequest {
  title: string;
  description: string;
  questions: Omit<FormQuestion, 'id'>[];
}

export interface SubmitResponseRequest {
  participant_id: string;
  answers: Record<string, string | string[] | number>;
}

// --- Response types ---

export interface FormListResponse {
  items: FormDefinition[];
  total: number;
}

export interface SubmissionResponse {
  id: string;
  participant_id: string;
  form_id: string;
  answers: Record<string, string | string[] | number>;
  submitted_at: string;
}

export interface ProgressResponse {
  participant_id: string;
  completed_forms: number;
  total_forms: number;
  percent_complete: number;
  current_step: string | null;
}
```

### How to Generate types.ts From models.py

Read the module's `models.py` and translate each model:

| Python (Pydantic) | TypeScript |
|---|---|
| `str` | `string` |
| `int`, `float`, `Decimal` | `number` |
| `bool` | `boolean` |
| `UUID` | `string` |
| `datetime` | `string` (ISO 8601) |
| `list[T]` | `T[]` |
| `dict[str, T]` | `Record<string, T>` |
| `T \| None` | `T \| null` |
| `Literal["a", "b"]` | `'a' \| 'b'` (union type) |
| Enum class | `type X = 'value1' \| 'value2'` |

---

## Layer 2: Hooks — Typed API Access

Every API endpoint gets a dedicated React Query hook. No component ever calls `fetch` directly.

### Rules

1. **One hook per endpoint.** `useFormDefinitions()`, `useFormDefinition(id)`, `useSubmitResponse()`, `useParticipantProgress(id)`. Never a generic `useApi()`.
2. **Queries for GET, mutations for POST/PUT/DELETE.** Use `useQuery` for reads, `useMutation` for writes.
3. **Return the query/mutation object directly.** Let components destructure `{ data, isLoading, error }`. Don't pre-process.
4. **Invalidate related queries after mutations.** When a form is submitted, invalidate the progress query.
5. **Type everything.** The hook's return type should flow from `types.ts`. No `any`, no `unknown` that gets cast downstream.
6. **API base path in one place.** A single constant or config value, never hardcoded in each hook.

```typescript
// hooks.ts

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

// --- Queries ---

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

// --- Mutations ---

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
      void queryClient.invalidateQueries({ queryKey: ['progress', variables.participant_id] });
      void queryClient.invalidateQueries({ queryKey: ['forms'] });
    },
  });
}
```

### Hook Naming Convention

| Endpoint | HTTP | Hook Name |
|---|---|---|
| `GET /forms` | query | `useFormDefinitions()` |
| `GET /forms/:id` | query | `useFormDefinition(id)` |
| `POST /forms` | mutation | `useCreateForm()` |
| `PUT /forms/:id` | mutation | `useUpdateForm()` |
| `DELETE /forms/:id` | mutation | `useDeleteForm()` |
| `POST /forms/:id/submit` | mutation | `useSubmitResponse()` |
| `GET /progress/:id` | query | `useParticipantProgress(id)` |

Prefix with `use`. Queries are nouns (`useFormDefinitions`). Mutations are verbs (`useCreateForm`, `useSubmitResponse`).

---

## Layer 3: Components — Project-Specific UI

Components consume hooks and render UI. This layer is **always project-specific** — it uses the project's design system, layout conventions, and interaction patterns.

### Rules

1. **Components only talk to hooks, never to the API directly.** No `fetch` calls in components.
2. **Handle all three states: loading, error, data.** Every component that uses a query handles these.
3. **Keep components presentational when possible.** A `FormQuestion` component receives props and renders. A `FormPage` component calls hooks and orchestrates.
4. **Colocate with the feature, not in a global components folder.** If it's only used by the intake feature, it lives next to the intake hooks.

```
features/
  intake/
    types.ts              # Layer 1
    hooks.ts              # Layer 2
    FormPage.tsx           # page that orchestrates
    FormRenderer.tsx       # renders a form definition
    QuestionField.tsx      # renders a single question
    ProgressBar.tsx        # shows participant progress
```

### Component Pattern

```typescript
// FormPage.tsx — orchestration component

import { useParams } from 'react-router-dom';
import { useFormDefinition, useSubmitResponse } from './hooks';
import FormRenderer from './FormRenderer';

export default function FormPage() {
  const { formId } = useParams<{ formId: string }>();
  const { data: form, isLoading, error } = useFormDefinition(formId!);
  const submitMutation = useSubmitResponse();

  if (isLoading) return <LoadingSkeleton />;
  if (error) return <ErrorState message="Could not load form" />;
  if (!form) return null;

  return (
    <FormRenderer
      form={form}
      onSubmit={(answers) => {
        submitMutation.mutate({
          formId: form.id,
          participant_id: currentParticipantId,
          answers,
        });
      }}
      isSubmitting={submitMutation.isPending}
    />
  );
}
```

```typescript
// FormRenderer.tsx — presentational component

import type { FormDefinition } from './types';
import QuestionField from './QuestionField';

interface FormRendererProps {
  form: FormDefinition;
  onSubmit: (answers: Record<string, string | string[] | number>) => void;
  isSubmitting: boolean;
}

export default function FormRenderer({ form, onSubmit, isSubmitting }: FormRendererProps) {
  // renders questions, collects answers, calls onSubmit
  // uses PROJECT-SPECIFIC styling, form library, validation
}
```

Notice: `FormRenderer` knows nothing about the API. It receives typed data and a callback. This is the cleanest boundary for a component that varies per project.

---

## What Goes in the Module vs. What's Built Fresh

When a forge module includes a `frontend/` directory, here's what's portable and what's reference:

| File | Portable? | Notes |
|---|---|---|
| `types.ts` | Yes | Mirror of `models.py`. Copy directly. |
| `hooks.ts` | Mostly | Works as-is if the project uses React Query. Only change is `API_BASE`. |
| `*.tsx` components | No — reference only | Adapt to the project's design system. |

When Claude adapts a module via `/use-module`, it should:
1. **Copy** `types.ts` as-is (adjusting field casing if the backend uses a camelCase alias)
2. **Adapt** `hooks.ts` — update `API_BASE`, adjust to the project's fetching patterns
3. **Rewrite** components entirely using the project's design system, informed by the reference

---

## Quick Reference

| Question | Answer |
|----------|--------|
| Where do API types go? | `types.ts` next to the feature — never in a global `types/` folder |
| Can components call `fetch`? | **No.** Components call hooks. Hooks call the API. |
| How do I type API responses? | Mirror the backend `models.py` into TypeScript interfaces |
| What fetching library? | React Query (`@tanstack/react-query`). One hook per endpoint. |
| How do I handle loading states? | Destructure `{ data, isLoading, error }` from every query hook |
| Where does `API_BASE` live? | One constant at the top of `hooks.ts`, or in an env-based config |
| Should I use Zod or plain interfaces? | Match whatever the project already uses. Be consistent. |
| What about WebSocket/realtime? | Supabase realtime subscriptions go in hooks too, same pattern |
