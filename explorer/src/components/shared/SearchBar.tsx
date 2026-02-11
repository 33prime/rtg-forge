import { useNavigate } from 'react-router-dom';
import { useEffect } from 'react';

export default function SearchBar() {
  const navigate = useNavigate();

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        navigate('/search');
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [navigate]);

  return (
    <button
      onClick={() => navigate('/search')}
      className="flex items-center gap-2 rounded-lg border border-border bg-[#09090b] px-3 py-1.5 text-sm text-[#71717a] transition-colors hover:border-[#3f3f46] hover:text-[#a1a1aa]"
    >
      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
      <span>Search...</span>
      <kbd className="ml-2 rounded border border-border bg-surface px-1.5 py-0.5 text-[10px] font-medium text-[#71717a]">
        {'\u2318'}K
      </kbd>
    </button>
  );
}
