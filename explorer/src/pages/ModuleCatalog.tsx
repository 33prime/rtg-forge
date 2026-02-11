import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { loadModules } from '../lib/data';
import ModuleGrid from '../components/modules/ModuleGrid';
import FilterBar from '../components/shared/FilterBar';

const filters = [
  {
    label: 'Category',
    value: 'category',
    options: [
      { label: 'Enrichment', value: 'enrichment' },
      { label: 'Intelligence', value: 'intelligence' },
      { label: 'Extraction', value: 'extraction' },
      { label: 'Integration', value: 'integration' },
    ],
  },
  {
    label: 'Status',
    value: 'status',
    options: [
      { label: 'Stable', value: 'stable' },
      { label: 'Draft', value: 'draft' },
      { label: 'Deprecated', value: 'deprecated' },
    ],
  },
];

export default function ModuleCatalog() {
  const [searchValue, setSearchValue] = useState('');
  const [activeFilters, setActiveFilters] = useState<Record<string, string>>({});

  const { data: modules, isLoading } = useQuery({
    queryKey: ['modules'],
    queryFn: loadModules,
  });

  const filteredModules = useMemo(() => {
    if (!modules) return [];

    return modules.filter((m) => {
      const matchesSearch =
        !searchValue ||
        m.module.name.toLowerCase().includes(searchValue.toLowerCase()) ||
        m.module.description.toLowerCase().includes(searchValue.toLowerCase());

      const matchesCategory =
        !activeFilters['category'] ||
        m.module.category === activeFilters['category'];

      const matchesStatus =
        !activeFilters['status'] ||
        m.module.status === activeFilters['status'];

      return matchesSearch && matchesCategory && matchesStatus;
    });
  }, [modules, searchValue, activeFilters]);

  const handleFilterChange = (key: string, value: string) => {
    setActiveFilters((prev) => ({ ...prev, [key]: value }));
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="text-[#71717a]">Loading modules...</div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-[#fafafa]">Modules</h1>
        <p className="mt-1 text-[#a1a1aa]">
          Browse and explore all available modules
        </p>
      </div>

      <FilterBar
        filters={filters}
        activeFilters={activeFilters}
        onFilterChange={handleFilterChange}
        searchValue={searchValue}
        onSearchChange={setSearchValue}
        placeholder="Search modules..."
      />

      <ModuleGrid modules={filteredModules} />
    </div>
  );
}
