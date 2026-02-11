/**
 * BAD: Untyped API calls scattered across components with no hook layer.
 *
 * Problems:
 * - fetch calls directly in components (not reusable, not testable)
 * - No TypeScript types on responses — 'any' everywhere
 * - Hardcoded API URLs in multiple places
 * - No cache invalidation — stale data after mutations
 * - No loading/error state handling
 * - Impossible to swap API layer or adapt to a different project
 */

// BAD: This isn't a hooks file at all — it's inline in a component

export default function FormPage({ formId }: { formId: string }) {
  const [form, setForm] = useState<any>(null); // BAD: any type
  const [loading, setLoading] = useState(true);

  // BAD: fetch directly in component with useEffect
  useEffect(() => {
    fetch(`/api/v1/intake/forms/${formId}`) // BAD: hardcoded URL
      .then((res) => res.json())
      .then((data) => {
        setForm(data);
        setLoading(false);
      });
  }, [formId]);

  // BAD: another inline fetch for submission
  const handleSubmit = async (answers: any) => { // BAD: any
    await fetch(`/api/v1/intake/forms/${formId}/submit`, { // BAD: hardcoded URL
      method: 'POST',
      body: JSON.stringify({ answers }),
    });
    // BAD: no cache invalidation, no error handling, no loading state
    alert('Submitted!');
  };

  // BAD: no loading skeleton, no error state
  if (loading) return <div>Loading...</div>;

  return <div>{/* render form with untyped data */}</div>;
}

// BAD: Another component with its own duplicate fetch logic
export function ProgressPage({ participantId }: { participantId: string }) {
  const [progress, setProgress] = useState<any>(null); // BAD: any again

  useEffect(() => {
    fetch(`/api/v1/intake/progress/${participantId}`) // BAD: third hardcoded URL
      .then((r) => r.json())
      .then(setProgress);
  }, [participantId]);

  // BAD: same problems repeated in every component that needs data
  return <div>{progress?.percent_complete}%</div>;
}
