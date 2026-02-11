import type { SkillMeta } from '../../lib/types';
import Badge from '../shared/Badge';
import MarkdownRenderer from '../shared/MarkdownRenderer';
import SkillSidebar from './SkillSidebar';

interface SkillDetailProps {
  skill: SkillMeta;
  docs?: string;
}

export default function SkillDetail({ skill: s, docs }: SkillDetailProps) {
  return (
    <div className="flex gap-6">
      <div className="flex-1 min-w-0">
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl font-bold text-[#fafafa]">{s.skill.name}</h1>
            <Badge variant={s.skill.tier}>{s.skill.tier}</Badge>
            <Badge variant={s.skill.category}>{s.skill.category}</Badge>
            <span className="text-sm text-[#71717a]">v{s.skill.version}</span>
          </div>
          <p className="text-[#a1a1aa]">{s.skill.description}</p>
        </div>

        {docs ? (
          <MarkdownRenderer content={docs} />
        ) : (
          <p className="text-[#71717a]">No documentation available for this skill.</p>
        )}
      </div>

      <aside className="hidden w-72 shrink-0 xl:block">
        <div className="sticky top-6">
          <SkillSidebar skill={s} />
        </div>
      </aside>
    </div>
  );
}
