import { useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import RtgSubmark from '../components/branding/RtgSubmark';

export default function Login() {
  const { user, loading, signIn } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-[#09090b]">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  if (user) return <Navigate to="/" replace />;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    const { error: err } = await signIn(email, password);
    if (err) setError(err);
    setSubmitting(false);
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#09090b] px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex justify-center">
          <RtgSubmark />
        </div>

        <div className="rounded-xl border border-border bg-surface p-6">
          <h1 className="mb-6 text-center text-xl font-semibold text-[#fafafa]">
            Sign in to Forge Explorer
          </h1>

          {error && (
            <div className="mb-4 rounded-lg bg-red-500/10 px-3 py-2 text-sm text-red-400">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="mb-1 block text-sm text-[#a1a1aa]">
                Email
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg border border-border bg-[#09090b] px-3 py-2 text-sm text-[#fafafa] outline-none transition-colors focus:border-primary"
              />
            </div>
            <div>
              <label htmlFor="password" className="mb-1 block text-sm text-[#a1a1aa]">
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg border border-border bg-[#09090b] px-3 py-2 text-sm text-[#fafafa] outline-none transition-colors focus:border-primary"
              />
            </div>
            <button
              type="submit"
              disabled={submitting}
              className="w-full rounded-lg bg-primary py-2.5 text-sm font-medium text-white transition-colors hover:bg-primary-dark disabled:opacity-50"
            >
              {submitting ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
        </div>

        <p className="mt-4 text-center text-sm text-[#71717a]">
          Don&apos;t have an account?{' '}
          <Link to="/signup" className="text-primary-light hover:underline">
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
}
