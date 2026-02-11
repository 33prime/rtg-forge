import type { ModuleManifest } from '../../lib/types';
import Card from '../shared/Card';
import Badge from '../shared/Badge';

interface ModuleCardProps {
  module: ModuleManifest;
}

export default function ModuleCard({ module: m }: ModuleCardProps) {
  const depsCount =
    (m.module.dependencies.python?.length ?? 0) +
    (m.module.dependencies.services?.length ?? 0) +
    (m.module.dependencies.modules?.length ?? 0);

  return (
    <Card href={`/modules/${m.module.name}`}>
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-sm font-semibold text-[#fafafa]">{m.module.name}</h3>
        <Badge variant={m.module.status}>{m.module.status}</Badge>
      </div>

      <p className="mt-2 line-clamp-1 text-sm text-[#a1a1aa]">{m.module.description}</p>

      <div className="mt-4 flex items-center gap-3">
        <Badge variant={m.module.category}>{m.module.category}</Badge>
        <span className="text-xs text-[#71717a]">{depsCount} deps</span>
        {m.health.last_validated && (
          <span className="text-xs text-[#71717a]">
            Validated: {m.health.last_validated}
          </span>
        )}
      </div>
    </Card>
  );
}
