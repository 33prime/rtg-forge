import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { loadSkills } from '../lib/data';
import SkillGrid from '../components/skills/SkillGrid';
import FilterBar from '../components/shared/FilterBar';

const filters = [
  {
    label: 'Tier',
    value: 'tier',
    options: [
      { label: 'Foundation', value: 'foundation' },
      { label: 'Specialized', value: 'specialized' },
      { label: 'Workflow', value: 'workflow' },
    ],
  },
  {
    label: 'Category',
    value: 'category',
    options: [
      { label: 'Stack', value: 'stack' },
      { label: 'Practices', value: 'practices' },
      { label: 'Workflows', value: 'workflows' },
    ],
  },
];

export default function SkillCatalog() {
  const [searchValue, setSearchValue] = useState('');
  const [activeFilters, setActiveFilters] = useState<Record<string, string>>({});

  const { data: skills, isLoading } = useQuery({
    queryKey: ['skills'],
    queryFn: loadSkills,
  });

  const filteredSkills = useMemo(() => {
    if (!skills) return [];

    return skills.filter((s) => {
      const matchesSearch =
        !searchValue ||
        s.skill.name.toLowerCase().includes(searchValue.toLowerCase()) ||
        s.skill.description.toLowerCase().includes(searchValue.toLowerCase()) ||
        s.skill.relevance_tags.some((t) =>
          t.toLowerCase().includes(searchValue.toLowerCase())
        );

      const matchesTier =
        !activeFilters['tier'] ||
        s.skill.tier === activeFilters['tier'];

      const matchesCategory =
        !activeFilters['category'] ||
        s.skill.category === activeFilters['category'];

      return matchesSearch && matchesTier && matchesCategory;
    });
  }, [skills, searchValue, activeFilters]);

  const handleFilterChange = (key: string, value: string) => {
    setActiveFilters((prev) => ({ ...prev, [key]: value }));
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="text-[#71717a]">Loading skills...</div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-[#fafafa]">Skills</h1>
        <p className="mt-1 text-[#a1a1aa]">
          Browse and explore all available skills
        </p>
      </div>

      <FilterBar
        filters={filters}
        activeFilters={activeFilters}
        onFilterChange={handleFilterChange}
        searchValue={searchValue}
        onSearchChange={setSearchValue}
        placeholder="Search skills..."
      />

      <SkillGrid skills={filteredSkills} grouped={!searchValue && Object.keys(activeFilters).every((k) => !activeFilters[k])} />
    </div>
  );
}
