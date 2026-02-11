import { useState, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useClickOutside } from '../../hooks/useClickOutside';

function getInitials(displayName: string | undefined, email: string | undefined): string {
  return (displayName || email || '?')
    .split(/[\s@]/)
    .filter(Boolean)
    .slice(0, 2)
    .map((s) => s[0]?.toUpperCase())
    .join('');
}

export default function UserMenu() {
  const { profile, signOut } = useAuth();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const close = useCallback(() => setOpen(false), []);
  useClickOutside(ref, close);

  const handleSignOut = useCallback(() => {
    setOpen(false);
    signOut();
  }, [signOut]);

  const initials = getInitials(profile?.display_name, profile?.email);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/20 text-xs font-semibold text-primary-light transition-colors hover:bg-primary/30"
      >
        {initials}
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-48 rounded-lg border border-border bg-surface py-1 shadow-lg">
          <div className="border-b border-border px-3 py-2">
            <p className="text-sm font-medium text-[#fafafa] truncate">
              {profile?.display_name}
            </p>
            <p className="text-xs text-[#71717a] truncate">{profile?.email}</p>
          </div>
          <Link
            to="/me"
            onClick={close}
            className="block px-3 py-2 text-sm text-[#a1a1aa] transition-colors hover:bg-surface-hover hover:text-[#fafafa]"
          >
            My Profile
          </Link>
          <button
            onClick={handleSignOut}
            className="w-full text-left px-3 py-2 text-sm text-[#a1a1aa] transition-colors hover:bg-surface-hover hover:text-[#fafafa]"
          >
            Sign Out
          </button>
        </div>
      )}
    </div>
  );
}
