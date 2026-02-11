import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { loadModules, loadModuleDocs } from '../lib/data';
import ModuleDetail from '../components/modules/ModuleDetail';
import EmptyState from '../components/shared/EmptyState';

export default function ModuleDetailPage() {
  const { name } = useParams<{ name: string }>();
  const navigate = useNavigate();

  const { data: modules, isLoading: modulesLoading } = useQuery({
    queryKey: ['modules'],
    queryFn: loadModules,
  });

  const { data: docs } = useQuery({
    queryKey: ['module-docs'],
    queryFn: loadModuleDocs,
  });

  if (modulesLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="text-[#71717a]">Loading module...</div>
      </div>
    );
  }

  const module = modules?.find((m) => m.module.name === name);

  if (!module) {
    return (
      <EmptyState
        title="Module not found"
        message={`No module named "${name}" was found.`}
        icon="search"
        action={{ label: 'Back to Modules', onClick: () => navigate('/modules') }}
      />
    );
  }

  const moduleDoc = docs?.[name ?? ''];

  return <ModuleDetail module={module} docs={moduleDoc} />;
}
