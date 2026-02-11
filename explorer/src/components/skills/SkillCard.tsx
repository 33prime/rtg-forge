import type { SkillMeta } from '../../lib/types';
import Card from '../shared/Card';
import Badge from '../shared/Badge';
import TagList from '../shared/TagList';

interface SkillCardProps {
  skill: SkillMeta;
}

export default function SkillCard({ skill: s }: SkillCardProps) {
  return (
    <Card href={`/skills/${s.skill.category}/${s.skill.name}`}>
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-sm font-semibold text-[#fafafa]">{s.skill.name}</h3>
        <Badge variant={s.skill.tier}>{s.skill.tier}</Badge>
      </div>

      <p className="mt-2 line-clamp-1 text-sm text-[#a1a1aa]">{s.skill.description}</p>

      <div className="mt-3">
        <TagList tags={s.skill.relevance_tags} limit={3} />
      </div>

      <div className="mt-3 flex items-center gap-3 text-xs text-[#71717a]">
        <span>{s.optimization.token_count.toLocaleString()} tokens</span>
        <span>weight: {s.skill.priority_weight}</span>
      </div>
    </Card>
  );
}
