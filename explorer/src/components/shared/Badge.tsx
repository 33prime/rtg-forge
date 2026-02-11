import { clsx } from 'clsx';

type BadgeVariant =
  | 'stable' | 'draft' | 'deprecated'
  | 'foundation' | 'specialized' | 'workflow'
  | 'seed' | 'developing' | 'production' | 'battle-tested'
  | 'enrichment' | 'intelligence' | 'extraction' | 'integration'
  | 'stack' | 'practices' | 'workflows'
  | 'low' | 'medium' | 'high'
  | 'default';

interface BadgeProps {
  variant: BadgeVariant;
  children: React.ReactNode;
  className?: string;
}

const variantClasses: Record<BadgeVariant, string> = {
  // Status
  stable: 'bg-green-500/10 text-green-400 border-green-500/20',
  draft: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
  deprecated: 'bg-red-500/10 text-red-400 border-red-500/20',

  // Tier
  foundation: 'bg-green-500/10 text-green-400 border-green-500/20',
  specialized: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  workflow: 'bg-purple-500/10 text-purple-400 border-purple-500/20',

  // Maturity
  seed: 'bg-red-500/10 text-red-400 border-red-500/20',
  developing: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
  production: 'bg-green-500/10 text-green-400 border-green-500/20',
  'battle-tested': 'bg-blue-500/10 text-blue-400 border-blue-500/20',

  // Category (module)
  enrichment: 'bg-teal-500/10 text-teal-400 border-teal-500/20',
  intelligence: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  extraction: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  integration: 'bg-amber-500/10 text-amber-400 border-amber-500/20',

  // Category (skill)
  stack: 'bg-teal-500/10 text-teal-400 border-teal-500/20',
  practices: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
  workflows: 'bg-orange-500/10 text-orange-400 border-orange-500/20',

  // Complexity
  low: 'bg-green-500/10 text-green-400 border-green-500/20',
  medium: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
  high: 'bg-red-500/10 text-red-400 border-red-500/20',

  // Default
  default: 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20',
};

export default function Badge({ variant, children, className }: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium',
        variantClasses[variant] ?? variantClasses.default,
        className
      )}
    >
      {children}
    </span>
  );
}
