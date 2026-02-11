import type { ProfileData } from '../../lib/types';
import Card from '../shared/Card';
import Badge from '../shared/Badge';

interface ProfileCardProps {
  profile: ProfileData;
}

export default function ProfileCard({ profile: p }: ProfileCardProps) {
  const skillCount = p.constraints?.required
    ? Object.keys(p.constraints.required).length
    : 0;

  return (
    <Card href={`/profiles/${p.profile.name}`}>
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-[#fafafa]">{p.profile.display_name}</h3>
          <p className="text-xs text-[#71717a]">{p.profile.name}</p>
        </div>
        <Badge variant={p.profile.maturity}>{p.profile.maturity}</Badge>
      </div>

      <p className="mt-2 line-clamp-2 text-sm text-[#a1a1aa]">{p.profile.description}</p>

      <div className="mt-4 flex items-center gap-4 text-xs text-[#71717a]">
        <span>{p.profile.vendor}</span>
        {p.base?.extends && (
          <span>extends: {p.base.extends}</span>
        )}
        {skillCount > 0 && (
          <span>{skillCount} required</span>
        )}
      </div>
    </Card>
  );
}
