import type { ProfileData } from '../../lib/types';
import { clsx } from 'clsx';

interface ConstraintsTableProps {
  constraints: ProfileData['constraints'];
}

export default function ConstraintsTable({ constraints }: ConstraintsTableProps) {
  if (!constraints) {
    return <p className="text-sm text-[#71717a]">No constraints defined.</p>;
  }

  const requiredEntries = constraints.required
    ? Object.entries(constraints.required)
    : [];
  const allowedEntries = constraints.allowed
    ? Object.entries(constraints.allowed)
    : [];
  const forbiddenEntries = constraints.forbidden
    ? Object.entries(constraints.forbidden)
    : [];
  const overrideEntries = constraints.overrides
    ? Object.entries(constraints.overrides)
    : [];

  return (
    <div className="space-y-6">
      {constraints.description && (
        <p className="text-sm text-[#a1a1aa]">{constraints.description}</p>
      )}

      {requiredEntries.length > 0 && (
        <div>
          <h3 className="mb-3 text-sm font-semibold text-[#fafafa]">Required</h3>
          <div className="space-y-2">
            {requiredEntries.map(([key, val]) => (
              <div
                key={key}
                className={clsx(
                  'flex items-start gap-4 rounded-lg border border-border bg-[#09090b] p-3',
                  'border-l-2 border-l-green-500'
                )}
              >
                <div className="min-w-[120px]">
                  <span className="text-xs font-medium text-[#71717a]">{key}</span>
                </div>
                <div className="flex-1">
                  <span className="text-sm font-medium text-[#fafafa]">
                    {typeof val === 'object' && val !== null && 'name' in val
                      ? (val as { name: string }).name
                      : String(val)}
                  </span>
                  {typeof val === 'object' && val !== null && 'reason' in val && (
                    <p className="mt-0.5 text-xs text-[#71717a]">
                      {(val as { reason: string }).reason}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {allowedEntries.length > 0 && (
        <div>
          <h3 className="mb-3 text-sm font-semibold text-[#fafafa]">Allowed</h3>
          <div className="space-y-2">
            {allowedEntries.map(([key, values]) => (
              <div
                key={key}
                className="flex items-start gap-4 rounded-lg border border-border bg-[#09090b] p-3"
              >
                <div className="min-w-[120px]">
                  <span className="text-xs font-medium text-[#71717a]">{key}</span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {Array.isArray(values) ? (
                    values.map((v) => (
                      <span
                        key={v}
                        className="inline-flex rounded-full bg-surface px-2 py-0.5 text-xs text-[#a1a1aa]"
                      >
                        {v}
                      </span>
                    ))
                  ) : (
                    <span className="text-sm text-[#a1a1aa]">{String(values)}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {forbiddenEntries.length > 0 && (
        <div>
          <h3 className="mb-3 text-sm font-semibold text-[#fafafa]">Forbidden</h3>
          <div className="space-y-2">
            {forbiddenEntries.map(([key, values]) => (
              <div
                key={key}
                className={clsx(
                  'flex items-start gap-4 rounded-lg border border-border bg-[#09090b] p-3',
                  'border-l-2 border-l-red-500'
                )}
              >
                <div className="min-w-[120px]">
                  <span className="text-xs font-medium text-[#71717a]">{key}</span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {Array.isArray(values) ? (
                    values.map((v) => (
                      <span
                        key={v}
                        className="inline-flex rounded-full bg-red-500/10 px-2 py-0.5 text-xs text-red-400 line-through"
                      >
                        {v}
                      </span>
                    ))
                  ) : (
                    <span className="text-sm text-red-400 line-through">{String(values)}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {overrideEntries.length > 0 && (
        <div>
          <h3 className="mb-3 text-sm font-semibold text-[#fafafa]">Overrides</h3>
          <div className="space-y-2">
            {overrideEntries.map(([key, value]) => (
              <div
                key={key}
                className="flex items-start gap-4 rounded-lg border border-border bg-[#09090b] p-3 border-l-2 border-l-amber-500"
              >
                <div className="min-w-[120px]">
                  <span className="text-xs font-medium text-[#71717a]">{key}</span>
                </div>
                <span className="text-sm text-amber-400">{value}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
