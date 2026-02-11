import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { loadModules, loadSkills, loadProfiles } from '../lib/data';
import StatCard from '../components/shared/StatCard';
import Card from '../components/shared/Card';

export default function Dashboard() {
  const navigate = useNavigate();

  const { data: modules } = useQuery({
    queryKey: ['modules'],
    queryFn: loadModules,
  });

  const { data: skills } = useQuery({
    queryKey: ['skills'],
    queryFn: loadSkills,
  });

  const { data: profiles } = useQuery({
    queryKey: ['profiles'],
    queryFn: loadProfiles,
  });

  const stableModules = modules?.filter((m) => m.module.status === 'stable').length ?? 0;
  const totalModules = modules?.length ?? 0;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-[#fafafa]">Dashboard</h1>
        <p className="mt-1 text-[#a1a1aa]">
          Overview of your RTG Forge ecosystem
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          value={totalModules}
          label="Total Modules"
          sublabel={`${stableModules} stable`}
          color="primary"
        />
        <StatCard
          value={skills?.length ?? 0}
          label="Total Skills"
          sublabel="Across all categories"
          color="blue"
        />
        <StatCard
          value={profiles?.length ?? 0}
          label="Active Profiles"
          sublabel="Configured"
          color="amber"
        />
        <StatCard
          value={stableModules === totalModules && totalModules > 0 ? 'Healthy' : 'Mixed'}
          label="Health Status"
          sublabel={`${stableModules}/${totalModules} stable`}
          color="green"
        />
      </div>

      <div>
        <h2 className="mb-4 text-lg font-semibold text-[#fafafa]">Quick Links</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <Card onClick={() => navigate('/modules')}>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                <svg className="h-5 w-5 text-primary-light" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                </svg>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-[#fafafa]">Modules</h3>
                <p className="text-xs text-[#71717a]">Browse and manage modules</p>
              </div>
            </div>
          </Card>

          <Card onClick={() => navigate('/skills')}>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-500/10">
                <svg className="h-5 w-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-[#fafafa]">Skills</h3>
                <p className="text-xs text-[#71717a]">Explore skill definitions</p>
              </div>
            </div>
          </Card>

          <Card onClick={() => navigate('/profiles')}>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-500/10">
                <svg className="h-5 w-5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
              </div>
              <div>
                <h3 className="text-sm font-semibold text-[#fafafa]">Profiles</h3>
                <p className="text-xs text-[#71717a]">View project profiles</p>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {modules && modules.length > 0 && (
        <div>
          <h2 className="mb-4 text-lg font-semibold text-[#fafafa]">Recent Modules</h2>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {modules.slice(0, 3).map((m) => (
              <Card key={m.module.name} href={`/modules/${m.module.name}`}>
                <h3 className="text-sm font-semibold text-[#fafafa]">{m.module.name}</h3>
                <p className="mt-1 line-clamp-1 text-xs text-[#a1a1aa]">{m.module.description}</p>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
