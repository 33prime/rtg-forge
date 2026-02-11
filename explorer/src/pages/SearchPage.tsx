import { useState, useEffect, useRef, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { loadModules, loadSkills, loadProfiles } from '../lib/data';
import { buildSearchIndex, search } from '../lib/search';
import type { SearchResult } from '../lib/types';
import Badge from '../components/shared/Badge';
import EmptyState from '../components/shared/EmptyState';

const typeLabels: Record<string, string> = {
  module: 'Modules',
  skill: 'Skills',
  profile: 'Profiles',
};

const typeBadgeVariant: Record<string, 'enrichment' | 'specialized' | 'production'> = {
  module: 'enrichment',
  skill: 'specialized',
  profile: 'production',
};

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const { data: modules } = useQuery({
    queryKey: ['modules'],
    queryFn: loadModules,
  });

  const { data: skills } = useQuery({
    queryKey: ['skills'],
    queryFn: loadSkills,
  });

  const { data: profiles } = useQuery({
    queryKey: ['profiles'],
    queryFn: loadProfiles,
  });

  useEffect(() => {
    if (modules && skills && profiles) {
      buildSearchIndex(modules, skills, profiles);
    }
  }, [modules, skills, profiles]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        inputRef.current?.focus();
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const results = useMemo(() => search(query), [query]);

  const grouped = useMemo(() => {
    const groups: Record<string, SearchResult[]> = {};
    for (const r of results) {
      const existing = groups[r.type] ?? [];
      existing.push(r);
      groups[r.type] = existing;
    }
    return groups;
  }, [results]);

  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-8">
        <div className="relative">
          <svg
            className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-[#71717a]"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search modules, skills, profiles..."
            className="w-full rounded-xl border border-border bg-surface py-4 pl-12 pr-4 text-lg text-[#fafafa] placeholder-[#71717a] outline-none transition-colors focus:border-primary"
          />
        </div>
      </div>

      {query && results.length === 0 && (
        <EmptyState
          title="No results"
          message={`No results found for "${query}". Try a different search term.`}
          icon="search"
        />
      )}

      {!query && (
        <div className="text-center py-12">
          <p className="text-[#71717a]">Start typing to search across modules, skills, and profiles</p>
          <p className="mt-2 text-xs text-[#52525b]">
            Press <kbd className="rounded border border-border bg-surface px-1.5 py-0.5 text-[10px]">{'\u2318'}K</kbd> to focus
          </p>
        </div>
      )}

      {query && results.length > 0 && (
        <div className="space-y-8">
          {(['module', 'skill', 'profile'] as const).map((type) => {
            const items = grouped[type];
            if (!items || items.length === 0) return null;

            return (
              <div key={type}>
                <h2 className="mb-3 text-sm font-semibold text-[#71717a] uppercase tracking-wider">
                  {typeLabels[type]} ({items.length})
                </h2>
                <div className="space-y-2">
                  {items.map((r) => (
                    <button
                      key={r.url}
                      onClick={() => navigate(r.url)}
                      className="flex w-full items-start gap-3 rounded-lg border border-border bg-surface p-4 text-left transition-colors hover:border-[#3f3f46] hover:bg-surface-hover"
                    >
                      <Badge variant={typeBadgeVariant[r.type] ?? 'default'}>{r.type}</Badge>
                      <div className="flex-1 min-w-0">
                        <h3 className="text-sm font-semibold text-[#fafafa]">{r.name}</h3>
                        <p className="mt-0.5 line-clamp-1 text-xs text-[#a1a1aa]">
                          {r.description}
                        </p>
                      </div>
                      {r.category && (
                        <span className="text-xs text-[#71717a]">{r.category}</span>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
