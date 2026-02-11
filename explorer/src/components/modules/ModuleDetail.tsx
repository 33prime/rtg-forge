import { useState } from 'react';
import type { ModuleManifest } from '../../lib/types';
import Tabs from '../shared/Tabs';
import MarkdownRenderer from '../shared/MarkdownRenderer';
import ModuleManifestView from './ModuleManifest';
import ModuleHealth from './ModuleHealth';
import Badge from '../shared/Badge';
import TagList from '../shared/TagList';

interface ModuleDetailProps {
  module: ModuleManifest;
  docs?: string;
  sources?: Record<string, string>;
}

const tabs = [
  { label: 'Documentation', value: 'docs' },
  { label: 'Source', value: 'source' },
  { label: 'Manifest', value: 'manifest' },
  { label: 'API', value: 'api' },
  { label: 'Dependencies', value: 'deps' },
  { label: 'Health', value: 'health' },
];

function getLanguage(filename: string): string {
  if (filename.endsWith('.py')) return 'python';
  if (filename.endsWith('.sql')) return 'sql';
  if (filename.endsWith('.toml')) return 'toml';
  if (filename.endsWith('.ts') || filename.endsWith('.tsx')) return 'typescript';
  return '';
}

function SourceViewer({ sources }: { sources: Record<string, string> }) {
  const [activeFile, setActiveFile] = useState(Object.keys(sources)[0] ?? '');
  const fileNames = Object.keys(sources).sort((a, b) => {
    const order = ['__init__.py', 'router.py', 'service.py', 'models.py', 'config.py'];
    const ai = order.indexOf(a);
    const bi = order.indexOf(b);
    if (ai !== -1 && bi !== -1) return ai - bi;
    if (ai !== -1) return -1;
    if (bi !== -1) return 1;
    return a.localeCompare(b);
  });

  return (
    <div className="flex gap-4">
      <div className="w-48 shrink-0">
        <nav className="space-y-0.5">
          {fileNames.map((name) => (
            <button
              key={name}
              onClick={() => setActiveFile(name)}
              className={`w-full rounded px-3 py-1.5 text-left text-xs font-mono transition-colors ${
                activeFile === name
                  ? 'bg-primary/10 text-primary-light'
                  : 'text-[#a1a1aa] hover:bg-surface-hover hover:text-[#fafafa]'
              }`}
            >
              {name}
            </button>
          ))}
        </nav>
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-mono text-[#71717a]">{activeFile}</span>
          <button
            onClick={() => {
              void navigator.clipboard.writeText(sources[activeFile] ?? '');
            }}
            className="rounded px-2 py-1 text-xs text-[#a1a1aa] transition-colors hover:bg-surface-hover hover:text-[#fafafa]"
          >
            Copy
          </button>
        </div>
        <div className="rounded-lg border border-border bg-[#09090b] overflow-auto max-h-[600px]">
          <MarkdownRenderer
            content={`\`\`\`${getLanguage(activeFile)}\n${sources[activeFile] ?? ''}\n\`\`\``}
          />
        </div>
      </div>
    </div>
  );
}

export default function ModuleDetail({ module: m, docs, sources }: ModuleDetailProps) {
  const [activeTab, setActiveTab] = useState('docs');

  return (
    <div className="flex gap-6">
      <div className="flex-1 min-w-0">
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl font-bold text-[#fafafa]">{m.module.name}</h1>
            <Badge variant={m.module.status}>{m.module.status}</Badge>
            <Badge variant={m.module.category}>{m.module.category}</Badge>
          </div>
          <p className="text-[#a1a1aa]">{m.module.description}</p>
        </div>

        <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

        <div className="mt-6">
          {activeTab === 'docs' && (
            docs ? (
              <MarkdownRenderer content={docs} />
            ) : (
              <p className="text-[#71717a]">No documentation available.</p>
            )
          )}

          {activeTab === 'source' && (
            sources && Object.keys(sources).length > 0 ? (
              <SourceViewer sources={sources} />
            ) : (
              <p className="text-[#71717a]">No source files available.</p>
            )
          )}

          {activeTab === 'manifest' && <ModuleManifestView manifest={m} />}

          {activeTab === 'api' && (
            <div className="space-y-4">
              <div className="rounded-lg border border-border bg-[#09090b] p-4">
                <div className="flex items-start gap-3 mb-3">
                  <span className="text-sm font-medium text-[#a1a1aa]">Prefix</span>
                  <code className="text-sm text-primary-light">{m.module.api.prefix}</code>
                </div>
                <div className="flex items-start gap-3">
                  <span className="text-sm font-medium text-[#a1a1aa]">Auth Required</span>
                  <span className={m.module.api.auth_required ? 'text-amber-400 text-sm' : 'text-green-400 text-sm'}>
                    {m.module.api.auth_required ? 'Yes' : 'No'}
                  </span>
                </div>
              </div>
              {m.module.database.tables.length > 0 && (
                <div className="rounded-lg border border-border bg-[#09090b] p-4">
                  <h3 className="mb-3 text-sm font-semibold text-[#fafafa]">Database Tables</h3>
                  <TagList tags={m.module.database.tables} />
                  <div className="mt-3 flex items-start gap-3">
                    <span className="text-sm font-medium text-[#a1a1aa]">RLS Required</span>
                    <span className={m.module.database.requires_rls ? 'text-amber-400 text-sm' : 'text-green-400 text-sm'}>
                      {m.module.database.requires_rls ? 'Yes' : 'No'}
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'deps' && (
            <div className="space-y-4">
              <div className="rounded-lg border border-border bg-[#09090b] p-4">
                <h3 className="mb-3 text-sm font-semibold text-[#fafafa]">Python Packages</h3>
                {m.module.dependencies.python.length > 0 ? (
                  <TagList tags={m.module.dependencies.python} />
                ) : (
                  <p className="text-sm text-[#71717a]">None</p>
                )}
              </div>
              <div className="rounded-lg border border-border bg-[#09090b] p-4">
                <h3 className="mb-3 text-sm font-semibold text-[#fafafa]">Services</h3>
                {m.module.dependencies.services.length > 0 ? (
                  <TagList tags={m.module.dependencies.services} />
                ) : (
                  <p className="text-sm text-[#71717a]">None</p>
                )}
              </div>
              <div className="rounded-lg border border-border bg-[#09090b] p-4">
                <h3 className="mb-3 text-sm font-semibold text-[#fafafa]">Module Dependencies</h3>
                {m.module.dependencies.modules.length > 0 ? (
                  <TagList tags={m.module.dependencies.modules} />
                ) : (
                  <p className="text-sm text-[#71717a]">None</p>
                )}
              </div>
            </div>
          )}

          {activeTab === 'health' && <ModuleHealth health={m.health} />}
        </div>
      </div>

      <aside className="hidden w-72 shrink-0 xl:block">
        <div className="sticky top-6 space-y-4">
          <div className="rounded-lg border border-border bg-surface p-4">
            <h3 className="mb-3 text-sm font-semibold text-[#fafafa]">Quick Info</h3>
            <dl className="space-y-2">
              <div className="flex justify-between">
                <dt className="text-xs text-[#71717a]">Version</dt>
                <dd className="text-xs text-[#a1a1aa]">{m.module.version}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-xs text-[#71717a]">Author</dt>
                <dd className="text-xs text-[#a1a1aa]">{m.module.author}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-xs text-[#71717a]">Complexity</dt>
                <dd><Badge variant={m.ai.complexity}>{m.ai.complexity}</Badge></dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-xs text-[#71717a]">Setup Time</dt>
                <dd className="text-xs text-[#a1a1aa]">{m.ai.estimated_setup_minutes} min</dd>
              </div>
            </dl>
          </div>

          <div className="rounded-lg border border-border bg-surface p-4">
            <h3 className="mb-3 text-sm font-semibold text-[#fafafa]">AI Context</h3>
            <p className="mb-2 text-xs text-[#71717a]">Use when:</p>
            <p className="text-xs text-[#a1a1aa]">{m.ai.use_when}</p>
          </div>

          {m.ai.related_modules.length > 0 && (
            <div className="rounded-lg border border-border bg-surface p-4">
              <h3 className="mb-3 text-sm font-semibold text-[#fafafa]">Related Modules</h3>
              <TagList tags={m.ai.related_modules} />
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}
