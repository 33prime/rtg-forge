import { clsx } from 'clsx';

interface FilterOption {
  label: string;
  value: string;
  options: { label: string; value: string }[];
}

interface FilterBarProps {
  filters: FilterOption[];
  activeFilters: Record<string, string>;
  onFilterChange: (key: string, value: string) => void;
  searchValue: string;
  onSearchChange: (value: string) => void;
  placeholder?: string;
}

export default function FilterBar({
  filters,
  activeFilters,
  onFilterChange,
  searchValue,
  onSearchChange,
  placeholder = 'Search...',
}: FilterBarProps) {
  return (
    <div className="mb-6 flex flex-wrap items-center gap-4">
      <div className="relative flex-1 min-w-[200px]">
        <svg
          className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#71717a]"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          type="text"
          value={searchValue}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder={placeholder}
          className="w-full rounded-lg border border-border bg-[#09090b] py-2 pl-10 pr-4 text-sm text-[#fafafa] placeholder-[#71717a] outline-none transition-colors focus:border-primary"
        />
      </div>

      {filters.map((filter) => (
        <div key={filter.value} className="flex items-center gap-2">
          <span className="text-xs font-medium text-[#71717a]">{filter.label}:</span>
          <div className="flex gap-1">
            <button
              onClick={() => onFilterChange(filter.value, '')}
              className={clsx(
                'rounded-full px-3 py-1 text-xs font-medium transition-colors',
                !activeFilters[filter.value]
                  ? 'bg-primary/10 text-primary-light'
                  : 'text-[#71717a] hover:text-[#a1a1aa]'
              )}
            >
              All
            </button>
            {filter.options.map((opt) => (
              <button
                key={opt.value}
                onClick={() => onFilterChange(filter.value, opt.value)}
                className={clsx(
                  'rounded-full px-3 py-1 text-xs font-medium transition-colors',
                  activeFilters[filter.value] === opt.value
                    ? 'bg-primary/10 text-primary-light'
                    : 'text-[#71717a] hover:text-[#a1a1aa]'
                )}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
