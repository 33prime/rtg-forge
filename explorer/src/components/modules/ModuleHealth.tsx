import type { ModuleManifest } from '../../lib/types';

interface ModuleHealthProps {
  health: ModuleManifest['health'];
}

export default function ModuleHealth({ health }: ModuleHealthProps) {
  const coverageColor =
    health.test_coverage >= 80
      ? 'bg-green-500'
      : health.test_coverage >= 50
        ? 'bg-yellow-500'
        : 'bg-red-500';

  return (
    <div className="space-y-6">
      <div>
        <h3 className="mb-3 text-sm font-semibold text-[#fafafa]">Last Validated</h3>
        <p className="text-sm text-[#a1a1aa]">{health.last_validated || 'Never'}</p>
      </div>

      <div>
        <h3 className="mb-3 text-sm font-semibold text-[#fafafa]">Test Coverage</h3>
        <div className="flex items-center gap-3">
          <div className="flex-1 overflow-hidden rounded-full bg-[#09090b] h-2.5">
            <div
              className={`h-full rounded-full ${coverageColor} transition-all`}
              style={{ width: `${Math.min(100, health.test_coverage)}%` }}
            />
          </div>
          <span className="text-sm font-medium text-[#a1a1aa]">
            {health.test_coverage}%
          </span>
        </div>
      </div>

      <div>
        <h3 className="mb-3 text-sm font-semibold text-[#fafafa]">Known Issues</h3>
        {health.known_issues.length === 0 ? (
          <p className="text-sm text-[#71717a]">No known issues</p>
        ) : (
          <ul className="space-y-2">
            {health.known_issues.map((issue, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-[#a1a1aa]">
                <svg className="mt-0.5 h-4 w-4 flex-shrink-0 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                {issue}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
