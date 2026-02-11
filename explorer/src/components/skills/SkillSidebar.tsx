import { Link } from 'react-router-dom';
import type { SkillMeta } from '../../lib/types';
import Badge from '../shared/Badge';
import TagList from '../shared/TagList';

interface SkillSidebarProps {
  skill: SkillMeta;
}

export default function SkillSidebar({ skill: s }: SkillSidebarProps) {
  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-border bg-surface p-4">
        <h3 className="mb-3 text-sm font-semibold text-[#fafafa]">Metadata</h3>
        <dl className="space-y-2">
          <div className="flex justify-between">
            <dt className="text-xs text-[#71717a]">Tier</dt>
            <dd><Badge variant={s.skill.tier}>{s.skill.tier}</Badge></dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-xs text-[#71717a]">Category</dt>
            <dd><Badge variant={s.skill.category}>{s.skill.category}</Badge></dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-xs text-[#71717a]">Version</dt>
            <dd className="text-xs text-[#a1a1aa]">{s.skill.version}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-xs text-[#71717a]">Priority Weight</dt>
            <dd className="text-xs text-[#a1a1aa]">{s.skill.priority_weight}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-xs text-[#71717a]">Token Count</dt>
            <dd className="text-xs text-[#a1a1aa]">{s.optimization.token_count.toLocaleString()}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-xs text-[#71717a]">Last Optimized</dt>
            <dd className="text-xs text-[#a1a1aa]">{s.optimization.last_optimized}</dd>
          </div>
        </dl>
      </div>

      {s.relationships.prerequisites.length > 0 && (
        <div className="rounded-lg border border-border bg-surface p-4">
          <h3 className="mb-3 text-sm font-semibold text-[#fafafa]">Prerequisites</h3>
          <ul className="space-y-1.5">
            {s.relationships.prerequisites.map((prereq) => (
              <li key={prereq}>
                <Link
                  to={`/skills/${prereq}`}
                  className="text-xs text-primary-light hover:underline"
                >
                  {prereq}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}

      {s.relationships.complements.length > 0 && (
        <div className="rounded-lg border border-border bg-surface p-4">
          <h3 className="mb-3 text-sm font-semibold text-[#fafafa]">Complements</h3>
          <ul className="space-y-1.5">
            {s.relationships.complements.map((comp) => (
              <li key={comp}>
                <Link
                  to={`/skills/${comp}`}
                  className="text-xs text-primary-light hover:underline"
                >
                  {comp}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}

      {s.tracking.common_mistakes.length > 0 && (
        <div className="rounded-lg border border-border bg-surface p-4">
          <h3 className="mb-3 text-sm font-semibold text-[#fafafa]">Common Mistakes</h3>
          <ul className="space-y-2">
            {s.tracking.common_mistakes.map((mistake, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-[#a1a1aa]">
                <svg className="mt-0.5 h-3 w-3 flex-shrink-0 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
                {mistake}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="rounded-lg border border-border bg-surface p-4">
        <h3 className="mb-3 text-sm font-semibold text-[#fafafa]">Relevance Tags</h3>
        <TagList tags={s.skill.relevance_tags} />
      </div>
    </div>
  );
}
