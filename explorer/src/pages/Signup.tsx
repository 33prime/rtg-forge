import { useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import RtgSubmark from '../components/branding/RtgSubmark';

export default function Signup() {
  const { user, loading, signUp } = useAuth();
  const [displayName, setDisplayName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

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

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    setSubmitting(true);
    const { error: err } = await signUp(email, password, displayName);
    if (err) {
      setError(err);
    } else {
      setSuccess(true);
    }
    setSubmitting(false);
  };

  if (success) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#09090b] px-4">
        <div className="w-full max-w-sm">
          <div className="mb-8 flex justify-center">
            <RtgSubmark />
          </div>
          <div className="rounded-xl border border-border bg-surface p-6 text-center">
            <h1 className="mb-2 text-xl font-semibold text-[#fafafa]">Check your email</h1>
            <p className="text-sm text-[#a1a1aa]">
              We sent a confirmation link to <strong className="text-[#fafafa]">{email}</strong>.
              Click it to activate your account.
            </p>
          </div>
          <p className="mt-4 text-center text-sm text-[#71717a]">
            <Link to="/login" className="text-primary-light hover:underline">
              Back to sign in
            </Link>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#09090b] px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex justify-center">
          <RtgSubmark />
        </div>

        <div className="rounded-xl border border-border bg-surface p-6">
          <h1 className="mb-6 text-center text-xl font-semibold text-[#fafafa]">
            Create your account
          </h1>

          {error && (
            <div className="mb-4 rounded-lg bg-red-500/10 px-3 py-2 text-sm text-red-400">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="displayName" className="mb-1 block text-sm text-[#a1a1aa]">
                Display Name
              </label>
              <input
                id="displayName"
                type="text"
                required
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                className="w-full rounded-lg border border-border bg-[#09090b] px-3 py-2 text-sm text-[#fafafa] outline-none transition-colors focus:border-primary"
              />
            </div>
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
            <div>
              <label htmlFor="confirmPassword" className="mb-1 block text-sm text-[#a1a1aa]">
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full rounded-lg border border-border bg-[#09090b] px-3 py-2 text-sm text-[#fafafa] outline-none transition-colors focus:border-primary"
              />
            </div>
            <button
              type="submit"
              disabled={submitting}
              className="w-full rounded-lg bg-primary py-2.5 text-sm font-medium text-white transition-colors hover:bg-primary-dark disabled:opacity-50"
            >
              {submitting ? 'Creating account...' : 'Create Account'}
            </button>
          </form>
        </div>

        <p className="mt-4 text-center text-sm text-[#71717a]">
          Already have an account?{' '}
          <Link to="/login" className="text-primary-light hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
