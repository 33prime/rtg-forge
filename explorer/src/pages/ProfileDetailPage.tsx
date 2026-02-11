import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { loadProfiles } from '../lib/data';
import ProfileDetail from '../components/profiles/ProfileDetail';
import EmptyState from '../components/shared/EmptyState';

export default function ProfileDetailPage() {
  const { name } = useParams<{ name: string }>();
  const navigate = useNavigate();

  const { data: profiles, isLoading } = useQuery({
    queryKey: ['profiles'],
    queryFn: loadProfiles,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="text-[#71717a]">Loading profile...</div>
      </div>
    );
  }

  const profile = profiles?.find((p) => p.profile.name === name);

  if (!profile) {
    return (
      <EmptyState
        title="Profile not found"
        message={`No profile named "${name}" was found.`}
        icon="search"
        action={{ label: 'Back to Profiles', onClick: () => navigate('/profiles') }}
      />
    );
  }

  return <ProfileDetail profile={profile} />;
}
