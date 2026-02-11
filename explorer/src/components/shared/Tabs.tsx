import { clsx } from 'clsx';

interface Tab {
  label: string;
  value: string;
}

interface TabsProps {
  tabs: Tab[];
  activeTab: string;
  onChange: (value: string) => void;
}

export default function Tabs({ tabs, activeTab, onChange }: TabsProps) {
  return (
    <div className="flex border-b border-border">
      {tabs.map((tab) => (
        <button
          key={tab.value}
          onClick={() => onChange(tab.value)}
          className={clsx(
            'relative px-4 py-2.5 text-sm font-medium transition-colors',
            activeTab === tab.value
              ? 'text-primary-light'
              : 'text-[#71717a] hover:text-[#a1a1aa]'
          )}
        >
          {tab.label}
          {activeTab === tab.value && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-light" />
          )}
        </button>
      ))}
    </div>
  );
}
