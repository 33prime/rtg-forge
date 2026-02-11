import type { ModuleManifest as ModuleManifestType } from '../../lib/types';
import TomlView from '../shared/TomlView';

interface ModuleManifestProps {
  manifest: ModuleManifestType;
}

export default function ModuleManifestView({ manifest }: ModuleManifestProps) {
  return (
    <div className="space-y-4">
      <TomlView data={manifest as unknown as Record<string, unknown>} />
    </div>
  );
}
