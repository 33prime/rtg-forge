import { useQuery } from '@tanstack/react-query';
import { loadProfiles } from '../lib/data';
import ProfileGrid from '../components/profiles/ProfileGrid';

export default function ProfileCatalog() {
  const { data: profiles, isLoading } = useQuery({
    queryKey: ['profiles'],
    queryFn: loadProfiles,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="text-[#71717a]">Loading profiles...</div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-[#fafafa]">Profiles</h1>
        <p className="mt-1 text-[#a1a1aa]">
          Project profiles define the technology stack and constraints
        </p>
      </div>

      <ProfileGrid profiles={profiles ?? []} />
    </div>
  );
}
