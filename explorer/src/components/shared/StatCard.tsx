import { clsx } from 'clsx';

interface StatCardProps {
  value: number | string;
  label: string;
  sublabel?: string;
  color?: 'primary' | 'green' | 'blue' | 'amber' | 'red';
}

const colorClasses: Record<string, string> = {
  primary: 'border-t-primary',
  green: 'border-t-green-500',
  blue: 'border-t-blue-500',
  amber: 'border-t-amber-500',
  red: 'border-t-red-500',
};

export default function StatCard({ value, label, sublabel, color = 'primary' }: StatCardProps) {
  return (
    <div
      className={clsx(
        'rounded-lg border border-border border-t-2 bg-surface p-5',
        colorClasses[color]
      )}
    >
      <div className="text-3xl font-bold text-[#fafafa]">{value}</div>
      <div className="mt-1 text-sm font-medium text-[#a1a1aa]">{label}</div>
      {sublabel && (
        <div className="mt-0.5 text-xs text-[#71717a]">{sublabel}</div>
      )}
    </div>
  );
}
