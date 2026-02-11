import type { SkillMeta } from '../../lib/types';
import SkillCard from './SkillCard';
import EmptyState from '../shared/EmptyState';

interface SkillGridProps {
  skills: SkillMeta[];
  grouped?: boolean;
}

const categoryLabels: Record<string, string> = {
  stack: 'Stack',
  practices: 'Practices',
  workflows: 'Workflows',
};

const categoryOrder = ['stack', 'practices', 'workflows'];

export default function SkillGrid({ skills, grouped = false }: SkillGridProps) {
  if (skills.length === 0) {
    return (
      <EmptyState
        title="No skills found"
        message="Try adjusting your search or filter criteria."
        icon="search"
      />
    );
  }

  if (!grouped) {
    return (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {skills.map((s) => (
          <SkillCard key={`${s.skill.category}/${s.skill.name}`} skill={s} />
        ))}
      </div>
    );
  }

  const groups = new Map<string, SkillMeta[]>();
  for (const s of skills) {
    const cat = s.skill.category;
    const existing = groups.get(cat) ?? [];
    existing.push(s);
    groups.set(cat, existing);
  }

  return (
    <div className="space-y-8">
      {categoryOrder.map((cat) => {
        const items = groups.get(cat);
        if (!items || items.length === 0) return null;

        return (
          <div key={cat}>
            <h2 className="mb-4 text-lg font-semibold text-[#fafafa]">
              {categoryLabels[cat] ?? cat}
              <span className="ml-2 text-sm font-normal text-[#71717a]">
                ({items.length})
              </span>
            </h2>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
              {items.map((s) => (
                <SkillCard key={`${s.skill.category}/${s.skill.name}`} skill={s} />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
