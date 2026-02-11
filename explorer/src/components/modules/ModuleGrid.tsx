import type { ModuleManifest } from '../../lib/types';
import ModuleCard from './ModuleCard';
import EmptyState from '../shared/EmptyState';

interface ModuleGridProps {
  modules: ModuleManifest[];
}

export default function ModuleGrid({ modules }: ModuleGridProps) {
  if (modules.length === 0) {
    return (
      <EmptyState
        title="No modules found"
        message="Try adjusting your search or filter criteria."
        icon="search"
      />
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {modules.map((m) => (
        <ModuleCard key={m.module.name} module={m} />
      ))}
    </div>
  );
}
