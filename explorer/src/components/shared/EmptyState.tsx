interface EmptyStateProps {
  title: string;
  message?: string;
  icon?: 'search' | 'empty' | 'coming-soon';
  action?: {
    label: string;
    onClick: () => void;
  };
}

const icons = {
  search: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z',
  empty: 'M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4',
  'coming-soon': 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z',
};

export default function EmptyState({ title, message, icon = 'empty', action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="mb-4 rounded-full bg-surface p-4">
        <svg className="h-8 w-8 text-[#71717a]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d={icons[icon]} />
        </svg>
      </div>
      <h3 className="mb-1 text-lg font-semibold text-[#fafafa]">{title}</h3>
      {message && <p className="mb-4 max-w-sm text-sm text-[#71717a]">{message}</p>}
      {action && (
        <button
          onClick={action.onClick}
          className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-dark"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}
