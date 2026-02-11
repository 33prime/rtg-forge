import type { ProfileData } from '../../lib/types';
import ProfileCard from './ProfileCard';
import EmptyState from '../shared/EmptyState';

interface ProfileGridProps {
  profiles: ProfileData[];
}

export default function ProfileGrid({ profiles }: ProfileGridProps) {
  if (profiles.length === 0) {
    return (
      <EmptyState
        title="No profiles found"
        message="No profiles have been configured yet."
        icon="empty"
      />
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {profiles.map((p) => (
        <ProfileCard key={p.profile.name} profile={p} />
      ))}
    </div>
  );
}
