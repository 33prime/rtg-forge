import { useState, useEffect, useCallback } from 'react';
import { clsx } from 'clsx';
import { useAuth } from '../contexts/AuthContext';
import { useAllProfiles, useUpdateDisplayName } from '../hooks/useProfiles';

const LEVEL_THRESHOLDS = [
  { level: 'Observer', min: 0 },
  { level: 'Consumer', min: 100 },
  { level: 'Contributor', min: 500 },
  { level: 'Forgemaster', min: 2000 },
] as const;

function getProgress(xp: number) {
  let currentIdx = 0;
  for (let i = LEVEL_THRESHOLDS.length - 1; i >= 0; i--) {
    const threshold = LEVEL_THRESHOLDS[i];
    if (threshold && xp >= threshold.min) {
      currentIdx = i;
      break;
    }
  }
  const current = LEVEL_THRESHOLDS[currentIdx] ?? LEVEL_THRESHOLDS[0]!;
  const next = LEVEL_THRESHOLDS[currentIdx + 1];
  if (!next) return { level: current.level, pct: 100, xpInLevel: 0, xpNeeded: 0 };
  const xpInLevel = xp - current.min;
  const xpNeeded = next.min - current.min;
  return { level: current.level, pct: Math.round((xpInLevel / xpNeeded) * 100), xpInLevel, xpNeeded };
}

function getInitials(name: string): string {
  return name
    .split(/\s/)
    .filter(Boolean)
    .slice(0, 2)
    .map((s) => s[0]?.toUpperCase())
    .join('');
}

interface RoleBadgeProps {
  role: 'admin' | 'user';
}

function RoleBadge({ role }: RoleBadgeProps) {
  return (
    <span
      className={clsx(
        'rounded-full px-2 py-0.5 text-xs font-medium',
        role === 'admin' ? 'bg-amber-500/10 text-amber-400' : 'bg-primary/10 text-primary-light'
      )}
    >
      {role}
    </span>
  );
}

export default function UserProfile() {
  const { profile, refreshProfile } = useAuth();
  const [editingName, setEditingName] = useState(false);
  const [nameValue, setNameValue] = useState(profile?.display_name ?? '');

  const isAdmin = profile?.role === 'admin';
  const { data: users, isLoading: loadingUsers } = useAllProfiles(isAdmin);
  const updateName = useUpdateDisplayName();

  useEffect(() => {
    setNameValue(profile?.display_name ?? '');
  }, [profile?.display_name]);

  const saveName = useCallback(async () => {
    if (!profile || !nameValue.trim()) return;
    await updateName.mutateAsync({ userId: profile.id, displayName: nameValue.trim() });
    await refreshProfile();
    setEditingName(false);
  }, [profile, nameValue, updateName, refreshProfile]);

  const cancelEdit = useCallback(() => {
    setEditingName(false);
    setNameValue(profile?.display_name ?? '');
  }, [profile?.display_name]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter') saveName();
      if (e.key === 'Escape') cancelEdit();
    },
    [saveName, cancelEdit]
  );

  if (!profile) return null;

  const progress = getProgress(profile.xp);
  const initials = getInitials(profile.display_name);

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <h1 className="text-2xl font-bold text-[#fafafa]">My Profile</h1>

      {/* User Info Card */}
      <div className="rounded-xl border border-border bg-surface p-6">
        <div className="flex items-start gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-primary/20 text-lg font-bold text-primary-light">
            {initials}
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              {editingName ? (
                <div className="flex items-center gap-2">
                  <input
                    value={nameValue}
                    onChange={(e) => setNameValue(e.target.value)}
                    className="rounded-lg border border-border bg-[#09090b] px-2 py-1 text-sm text-[#fafafa] outline-none focus:border-primary"
                    autoFocus
                    onKeyDown={handleKeyDown}
                  />
                  <button
                    onClick={saveName}
                    disabled={updateName.isPending}
                    className="rounded bg-primary px-2 py-1 text-xs text-white"
                  >
                    {updateName.isPending ? '...' : 'Save'}
                  </button>
                  <button
                    onClick={cancelEdit}
                    className="rounded px-2 py-1 text-xs text-[#71717a] hover:text-[#fafafa]"
                  >
                    Cancel
                  </button>
                </div>
              ) : (
                <>
                  <h2 className="text-lg font-semibold text-[#fafafa]">{profile.display_name}</h2>
                  <button
                    onClick={() => setEditingName(true)}
                    className="text-xs text-[#71717a] hover:text-primary-light"
                  >
                    Edit
                  </button>
                </>
              )}
            </div>
            <p className="text-sm text-[#a1a1aa]">{profile.email}</p>
            <div className="mt-2 flex items-center gap-2">
              <RoleBadge role={profile.role} />
              <span className="text-xs text-[#71717a]">
                Member since {new Date(profile.created_at).toLocaleDateString()}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Forge Progress */}
      <div className="rounded-xl border border-border bg-surface p-6">
        <h3 className="mb-4 text-lg font-semibold text-[#fafafa]">Forge Progress</h3>
        <div className="mb-2 flex items-center justify-between text-sm">
          <span className="font-medium text-primary-light">{progress.level}</span>
          <span className="text-[#71717a]">{profile.xp} XP</span>
        </div>
        <div className="mb-4 h-2 rounded-full bg-[#27272a]">
          <div
            className="h-2 rounded-full bg-primary transition-all"
            style={{ width: `${progress.pct}%` }}
          />
        </div>
        <div className="grid grid-cols-4 gap-2">
          {LEVEL_THRESHOLDS.map((t) => (
            <div
              key={t.level}
              className={clsx(
                'rounded-lg border p-3 text-center',
                profile.xp >= t.min
                  ? 'border-primary/30 bg-primary/5'
                  : 'border-border bg-[#09090b]'
              )}
            >
              <p className={clsx('text-sm font-medium', profile.xp >= t.min ? 'text-primary-light' : 'text-[#71717a]')}>
                {t.level}
              </p>
              <p className="text-xs text-[#71717a]">{t.min} XP</p>
            </div>
          ))}
        </div>
      </div>

      {/* Admin: User List */}
      {isAdmin && (
        <div className="rounded-xl border border-border bg-surface p-6">
          <h3 className="mb-4 text-lg font-semibold text-[#fafafa]">All Users</h3>
          {loadingUsers ? (
            <div className="flex justify-center py-8">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-[#71717a]">
                    <th className="pb-2 font-medium">Name</th>
                    <th className="pb-2 font-medium">Email</th>
                    <th className="pb-2 font-medium">Role</th>
                    <th className="pb-2 font-medium">Level</th>
                    <th className="pb-2 font-medium text-right">XP</th>
                    <th className="pb-2 font-medium">Joined</th>
                  </tr>
                </thead>
                <tbody>
                  {users?.map((u) => (
                    <tr key={u.id} className="border-b border-border/50">
                      <td className="py-2 text-[#fafafa]">{u.display_name}</td>
                      <td className="py-2 text-[#a1a1aa]">{u.email}</td>
                      <td className="py-2">
                        <RoleBadge role={u.role} />
                      </td>
                      <td className="py-2 text-[#a1a1aa]">{u.forge_level}</td>
                      <td className="py-2 text-right text-[#a1a1aa]">{u.xp}</td>
                      <td className="py-2 text-[#71717a]">
                        {new Date(u.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
