import Badge from './Badge';

interface TomlViewProps {
  data: Record<string, unknown>;
  depth?: number;
}

function renderValue(value: unknown, depth: number): React.ReactNode {
  if (value === null || value === undefined) {
    return <span className="text-[#71717a]">null</span>;
  }

  if (typeof value === 'boolean') {
    return (
      <span className={value ? 'text-green-400' : 'text-red-400'}>
        {value.toString()}
      </span>
    );
  }

  if (typeof value === 'number') {
    return <span className="text-amber-400">{value}</span>;
  }

  if (typeof value === 'string') {
    return <span className="text-primary-light">{value}</span>;
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return <span className="text-[#71717a]">[]</span>;
    }

    if (value.every((v) => typeof v === 'string')) {
      return (
        <div className="flex flex-wrap gap-1.5">
          {value.map((item, i) => (
            <Badge key={i} variant="default">
              {item as string}
            </Badge>
          ))}
        </div>
      );
    }

    return (
      <div className="space-y-1">
        {value.map((item, i) => (
          <div key={i} className="pl-2 border-l border-border-subtle">
            {renderValue(item, depth + 1)}
          </div>
        ))}
      </div>
    );
  }

  if (typeof value === 'object') {
    return <TomlView data={value as Record<string, unknown>} depth={depth + 1} />;
  }

  return <span className="text-[#a1a1aa]">{String(value)}</span>;
}

export default function TomlView({ data, depth = 0 }: TomlViewProps) {
  const entries = Object.entries(data);

  if (entries.length === 0) {
    return <span className="text-[#71717a]">Empty</span>;
  }

  return (
    <div className={depth > 0 ? 'space-y-2' : 'space-y-3'}>
      {entries.map(([key, value]) => {
        const isSection = typeof value === 'object' && value !== null && !Array.isArray(value);

        if (isSection && depth === 0) {
          return (
            <div key={key} className="rounded-lg border border-border bg-[#09090b] p-4">
              <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-[#71717a]">
                [{key}]
              </h3>
              <TomlView data={value as Record<string, unknown>} depth={depth + 1} />
            </div>
          );
        }

        return (
          <div key={key} className="flex items-start gap-3">
            <span className="min-w-[140px] shrink-0 text-sm font-medium text-[#a1a1aa]">
              {key}
            </span>
            <span className="text-sm">{renderValue(value, depth)}</span>
          </div>
        );
      })}
    </div>
  );
}
