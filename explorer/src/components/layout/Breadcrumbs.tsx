import { Link, useLocation } from 'react-router-dom';

const labelMap: Record<string, string> = {
  modules: 'Modules',
  skills: 'Skills',
  profiles: 'Profiles',
  search: 'Search',
  stack: 'Stack',
  practices: 'Practices',
  workflows: 'Workflows',
};

function formatSegment(segment: string): string {
  return labelMap[segment] ?? segment.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function Breadcrumbs() {
  const location = useLocation();
  const segments = location.pathname.split('/').filter(Boolean);

  if (segments.length === 0) {
    return <span className="text-sm text-[#a1a1aa]">Dashboard</span>;
  }

  return (
    <nav className="flex items-center gap-1.5 text-sm">
      <Link to="/" className="text-[#71717a] transition-colors hover:text-[#fafafa]">
        Home
      </Link>
      {segments.map((segment, i) => {
        const path = '/' + segments.slice(0, i + 1).join('/');
        const isLast = i === segments.length - 1;

        return (
          <span key={path} className="flex items-center gap-1.5">
            <span className="text-[#71717a]">/</span>
            {isLast ? (
              <span className="text-[#fafafa] font-medium">{formatSegment(segment)}</span>
            ) : (
              <Link to={path} className="text-[#71717a] transition-colors hover:text-[#fafafa]">
                {formatSegment(segment)}
              </Link>
            )}
          </span>
        );
      })}
    </nav>
  );
}
