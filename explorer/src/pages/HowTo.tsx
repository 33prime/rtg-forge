import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Card from '../components/shared/Card';

const levels = [
  {
    title: 'Observer',
    xp: '0 XP',
    range: 'Starting out',
    description: 'Has access to the forge, browses modules and skills.',
    criteria: ['Onboarded to RTG Forge', 'Browsed the Explorer', 'Read the North Star doc'],
    color: 'text-[#71717a]',
    bg: 'bg-[#71717a]/10',
    border: 'border-[#71717a]/30',
  },
  {
    title: 'Consumer',
    xp: '100 XP',
    range: '1-2 modules used',
    description: 'Actively uses forge modules in their projects via /use-module.',
    criteria: [
      'Used /use-module to install a module into a project',
      'Adapted a module to a specific use case',
      'Reported an issue or improvement for a module',
    ],
    color: 'text-blue-400',
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/30',
  },
  {
    title: 'Contributor',
    xp: '500 XP',
    range: '1-3 modules contributed',
    description: 'Extracts modules from real projects and adds them to the forge.',
    criteria: [
      'Ran /scout-modules on a project and identified candidates',
      'Extracted at least 1 module via /prepare-module + /add-module',
      'Module passes contract validation (all 6 required files)',
      'Wrote a MODULE.md with real documentation',
    ],
    color: 'text-primary-light',
    bg: 'bg-primary/10',
    border: 'border-primary/30',
  },
  {
    title: 'Forgemaster',
    xp: '2000 XP',
    range: '5+ modules, cross-project impact',
    description: 'Builds modules others actively use. Improves skills and profiles.',
    criteria: [
      'Contributed 5+ modules with stable status',
      'At least 2 modules have been used by other team members',
      'Improved or created at least 1 skill',
      'Identified and logged architectural decisions',
      'Modules include frontend/ integration layer',
    ],
    color: 'text-amber-400',
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/30',
  },
];

const xpActions = [
  { action: 'Browse a module in the Explorer', xp: 5 },
  { action: 'Use a module in a project (/use-module)', xp: 25 },
  { action: 'Run /scout-modules on a project', xp: 15 },
  { action: 'Extract a module (/prepare-module + /add-module)', xp: 100 },
  { action: 'Module reaches stable status', xp: 50 },
  { action: 'Add frontend/ integration layer to a module', xp: 40 },
  { action: 'Improve an existing skill (SKILL.md update)', xp: 30 },
  { action: 'Report and fix a module issue', xp: 20 },
  { action: 'Another team member uses your module', xp: 75 },
  { action: 'Log an architectural decision', xp: 35 },
];

const workflows = [
  {
    step: '1',
    title: 'Scout',
    command: '/scout-modules',
    description: 'Scan any codebase to identify features that could become forge modules. Get a scored report of candidates.',
    icon: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z',
  },
  {
    step: '2',
    title: 'Prepare',
    command: '/prepare-module',
    description: 'Describe a specific feature. Claude maps all related files in your codebase to the forge contract structure.',
    icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2',
  },
  {
    step: '3',
    title: 'Extract',
    command: '/add-module',
    description: 'Takes the module map and extracts the code into the forge with the proper six-file structure, manifest, and docs.',
    icon: 'M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12',
  },
  {
    step: '4',
    title: 'Use',
    command: '/use-module',
    description: 'Install a forge module into a new project. Claude reads your codebase, interviews you, and adapts the code to fit.',
    icon: 'M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4',
  },
];

const mcpConfigCloud = `{
  "mcpServers": {
    "rtg-forge": {
      "type": "sse",
      "url": "https://rtg-forge-mcp-production.up.railway.app/sse"
    }
  }
}`;

const mcpConfigLocal = `{
  "mcpServers": {
    "rtg-forge": {
      "command": "uv",
      "args": [
        "run",
        "--directory", "/path/to/rtg-forge/mcp-server",
        "python", "-m", "forge_mcp.server"
      ],
      "env": {
        "FORGE_ROOT": "/path/to/rtg-forge"
      }
    }
  }
}`;

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }}
      className="rounded bg-[#27272a] px-2 py-1 text-xs text-[#a1a1aa] transition-colors hover:bg-[#3f3f46] hover:text-[#fafafa]"
    >
      {copied ? 'Copied!' : 'Copy'}
    </button>
  );
}

function McpSetupSection() {
  const [tab, setTab] = useState<'cloud' | 'local'>('cloud');

  return (
    <section>
      <h2 className="mb-4 text-lg font-semibold text-[#fafafa]">MCP Server Setup</h2>
      <div className="rounded-lg border border-border bg-surface p-6 space-y-5">
        <p className="text-sm text-[#a1a1aa]">
          The RTG Forge MCP server gives Claude Code direct access to forge tools. Choose your setup:
        </p>

        {/* Tabs */}
        <div className="flex gap-1 rounded-lg bg-[#09090b] p-1">
          <button
            onClick={() => setTab('cloud')}
            className={`flex-1 rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
              tab === 'cloud' ? 'bg-primary/20 text-primary-light' : 'text-[#71717a] hover:text-[#a1a1aa]'
            }`}
          >
            Cloud (Recommended)
          </button>
          <button
            onClick={() => setTab('local')}
            className={`flex-1 rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
              tab === 'local' ? 'bg-primary/20 text-primary-light' : 'text-[#71717a] hover:text-[#a1a1aa]'
            }`}
          >
            Local
          </button>
        </div>

        {tab === 'cloud' ? (
          <>
            <div className="flex gap-4">
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/20 text-xs font-bold text-primary-light">1</div>
              <div>
                <p className="text-sm font-medium text-[#fafafa]">Open your Claude config</p>
                <p className="text-xs text-[#71717a] mt-0.5">
                  Edit <code className="text-primary-light">~/.claude.json</code> (global config for Claude Code).
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/20 text-xs font-bold text-primary-light">2</div>
              <div className="flex-1">
                <p className="text-sm font-medium text-[#fafafa]">Add the cloud MCP config</p>
                <p className="text-xs text-[#71717a] mt-1">No repo clone needed. Just paste this config and you&apos;re done.</p>
                <div className="mt-2 relative">
                  <div className="absolute right-2 top-2">
                    <CopyButton text={mcpConfigCloud} />
                  </div>
                  <pre className="rounded-lg bg-[#09090b] border border-border-subtle p-4 text-xs text-[#a1a1aa] overflow-x-auto">
                    <code>{mcpConfigCloud}</code>
                  </pre>
                </div>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/20 text-xs font-bold text-primary-light">3</div>
              <div>
                <p className="text-sm font-medium text-[#fafafa]">Restart Claude Code</p>
                <p className="text-xs text-[#71717a] mt-0.5">
                  Close and reopen Claude Code. All forge tools will be available in every session — no local install required.
                </p>
              </div>
            </div>
          </>
        ) : (
          <>
            <div className="flex gap-4">
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/20 text-xs font-bold text-primary-light">1</div>
              <div>
                <p className="text-sm font-medium text-[#fafafa]">Clone the repo and open your Claude config</p>
                <p className="text-xs text-[#71717a] mt-0.5">
                  Clone <code className="text-primary-light">rtg-forge</code> locally, then edit <code className="text-primary-light">~/.claude.json</code>.
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/20 text-xs font-bold text-primary-light">2</div>
              <div className="flex-1">
                <p className="text-sm font-medium text-[#fafafa]">Add the local MCP config</p>
                <div className="mt-2 relative">
                  <div className="absolute right-2 top-2">
                    <CopyButton text={mcpConfigLocal} />
                  </div>
                  <pre className="rounded-lg bg-[#09090b] border border-border-subtle p-4 text-xs text-[#a1a1aa] overflow-x-auto">
                    <code>{mcpConfigLocal}</code>
                  </pre>
                </div>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/20 text-xs font-bold text-primary-light">3</div>
              <div>
                <p className="text-sm font-medium text-[#fafafa]">Update the path</p>
                <p className="text-xs text-[#71717a] mt-0.5">
                  Replace <code className="text-primary-light">/path/to/rtg-forge</code> with the actual path to your local clone.
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/20 text-xs font-bold text-primary-light">4</div>
              <div>
                <p className="text-sm font-medium text-[#fafafa]">Restart Claude Code</p>
                <p className="text-xs text-[#71717a] mt-0.5">
                  Close and reopen Claude Code. The forge tools will be available in every session.
                </p>
              </div>
            </div>
          </>
        )}
      </div>
    </section>
  );
}

export default function HowTo() {
  const navigate = useNavigate();

  return (
    <div className="space-y-10">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-[#fafafa]">How To Use RTG Forge</h1>
        <p className="mt-1 text-[#a1a1aa]">
          Everything you need to go from browsing modules to contributing your own.
        </p>
      </div>

      {/* What is RTG Forge */}
      <section>
        <h2 className="mb-4 text-lg font-semibold text-[#fafafa]">What is RTG Forge?</h2>
        <div className="rounded-lg border border-border bg-surface p-6">
          <p className="text-sm leading-relaxed text-[#a1a1aa]">
            RTG Forge is a <span className="text-[#fafafa] font-medium">self-populating knowledge system</span> where
            AI extracts, stores, and applies everything learned from building software — so no pattern
            is ever built from scratch twice.
          </p>
          <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-3">
            <div className="rounded-lg border border-border-subtle bg-[#09090b] p-4">
              <div className="text-sm font-semibold text-[#fafafa]">Skills</div>
              <div className="text-xs text-primary-light mt-1">How we write code</div>
              <p className="mt-2 text-xs text-[#71717a]">Coding standards and patterns that make Claude write better code.</p>
            </div>
            <div className="rounded-lg border border-border-subtle bg-[#09090b] p-4">
              <div className="text-sm font-semibold text-[#fafafa]">Modules</div>
              <div className="text-xs text-primary-light mt-1">What we build</div>
              <p className="mt-2 text-xs text-[#71717a]">Proven backend features with source, docs, and API contracts ready to adapt.</p>
            </div>
            <div className="rounded-lg border border-border-subtle bg-[#09090b] p-4">
              <div className="text-sm font-semibold text-[#fafafa]">Decisions</div>
              <div className="text-xs text-primary-light mt-1">Why we chose this approach</div>
              <p className="mt-2 text-xs text-[#71717a]">Architectural decisions capturing what was chosen, what was rejected, and why.</p>
            </div>
          </div>
        </div>
      </section>

      {/* The Workflow */}
      <section>
        <h2 className="mb-4 text-lg font-semibold text-[#fafafa]">The Workflow</h2>
        <p className="mb-4 text-sm text-[#a1a1aa]">
          Four commands. That's it. Run them in any Claude Code session.
        </p>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          {workflows.map((w) => (
            <div key={w.step} className="rounded-lg border border-border bg-surface p-5">
              <div className="flex items-center gap-3 mb-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-sm font-bold text-primary-light">
                  {w.step}
                </div>
                <svg className="h-5 w-5 text-[#a1a1aa]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d={w.icon} />
                </svg>
              </div>
              <h3 className="text-sm font-semibold text-[#fafafa]">{w.title}</h3>
              <code className="mt-1 block text-xs text-primary-light">{w.command}</code>
              <p className="mt-2 text-xs text-[#71717a] leading-relaxed">{w.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Quick Start */}
      <section>
        <h2 className="mb-4 text-lg font-semibold text-[#fafafa]">Quick Start (Your First 10 Minutes)</h2>
        <div className="rounded-lg border border-border bg-surface p-6 space-y-4">
          <div className="flex gap-4">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/20 text-xs font-bold text-primary-light">1</div>
            <div>
              <p className="text-sm font-medium text-[#fafafa]">Browse the Explorer</p>
              <p className="text-xs text-[#71717a] mt-0.5">You're already here. Check out the <button onClick={() => navigate('/modules')} className="text-primary-light hover:underline">Modules</button> and <button onClick={() => navigate('/skills')} className="text-primary-light hover:underline">Skills</button> pages to see what's available.</p>
            </div>
          </div>
          <div className="flex gap-4">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/20 text-xs font-bold text-primary-light">2</div>
            <div>
              <p className="text-sm font-medium text-[#fafafa]">Open any project in Claude Code</p>
              <p className="text-xs text-[#71717a] mt-0.5">The forge MCP server is configured globally. Every Claude Code session has access to forge tools.</p>
            </div>
          </div>
          <div className="flex gap-4">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/20 text-xs font-bold text-primary-light">3</div>
            <div>
              <p className="text-sm font-medium text-[#fafafa]">Run <code className="text-primary-light">/scout-modules</code></p>
              <p className="text-xs text-[#71717a] mt-0.5">Claude scans the codebase and identifies features that could become forge modules. No commitment — just a report.</p>
            </div>
          </div>
          <div className="flex gap-4">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/20 text-xs font-bold text-primary-light">4</div>
            <div>
              <p className="text-sm font-medium text-[#fafafa]">Pick one and extract it</p>
              <p className="text-xs text-[#71717a] mt-0.5">Run <code className="text-primary-light">/prepare-module</code> then <code className="text-primary-light">/add-module</code>. Your first contribution to the forge.</p>
            </div>
          </div>
          <div className="flex gap-4">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/20 text-xs font-bold text-primary-light">5</div>
            <div>
              <p className="text-sm font-medium text-[#fafafa]">Use it in another project</p>
              <p className="text-xs text-[#71717a] mt-0.5">Open a different project, run <code className="text-primary-light">/use-module</code>, and watch Claude adapt the code to fit.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Levels / Gamification */}
      <section>
        <h2 className="mb-2 text-lg font-semibold text-[#fafafa]">Forge Levels</h2>
        <p className="mb-4 text-sm text-[#a1a1aa]">
          Your contributions to the forge earn XP and unlock levels. The more you contribute, the smarter the forge gets for everyone.
        </p>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {levels.map((level) => (
            <div key={level.title} className={`rounded-lg border ${level.border} bg-surface p-5`}>
              <div className="flex items-center justify-between mb-3">
                <h3 className={`text-sm font-bold ${level.color}`}>{level.title}</h3>
                <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${level.bg} ${level.color}`}>
                  {level.xp}
                </span>
              </div>
              <p className="text-xs text-[#a1a1aa] mb-3">{level.description}</p>
              <ul className="space-y-1.5">
                {level.criteria.map((c, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-[#71717a]">
                    <span className="mt-0.5 shrink-0">
                      <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4" />
                      </svg>
                    </span>
                    {c}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      {/* XP Actions */}
      <section>
        <h2 className="mb-4 text-lg font-semibold text-[#fafafa]">How to Earn XP</h2>
        <div className="rounded-lg border border-border bg-surface overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                <th className="px-5 py-3 text-left text-xs font-medium text-[#71717a] uppercase tracking-wider">Action</th>
                <th className="px-5 py-3 text-right text-xs font-medium text-[#71717a] uppercase tracking-wider">XP</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle">
              {xpActions
                .sort((a, b) => b.xp - a.xp)
                .map((item) => (
                  <tr key={item.action} className="hover:bg-surface-hover transition-colors">
                    <td className="px-5 py-3 text-sm text-[#a1a1aa]">{item.action}</td>
                    <td className="px-5 py-3 text-right">
                      <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${
                        item.xp >= 75 ? 'bg-amber-500/10 text-amber-400' :
                        item.xp >= 30 ? 'bg-primary/10 text-primary-light' :
                        'bg-[#27272a] text-[#a1a1aa]'
                      }`}>
                        +{item.xp} XP
                      </span>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Key Principles */}
      <section>
        <h2 className="mb-4 text-lg font-semibold text-[#fafafa]">Key Principles</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Card>
            <h3 className="text-sm font-semibold text-[#fafafa]">Build Forge-Ready From Day One</h3>
            <p className="mt-2 text-xs text-[#71717a] leading-relaxed">
              Every backend feature should follow the six-file structure: __init__.py, router.py, service.py, models.py, config.py, migrations/.
              When it's time to extract, it's a copy — not a refactor.
            </p>
          </Card>
          <Card>
            <h3 className="text-sm font-semibold text-[#fafafa]">Service Layer Has Zero Framework Imports</h3>
            <p className="mt-2 text-xs text-[#71717a] leading-relaxed">
              Business logic in service.py must never import from FastAPI or any HTTP framework.
              This is what makes modules portable across projects.
            </p>
          </Card>
          <Card>
            <h3 className="text-sm font-semibold text-[#fafafa]">Frontend = Types + Hooks + Fresh UI</h3>
            <p className="mt-2 text-xs text-[#71717a] leading-relaxed">
              Modules include types.ts (mirroring models.py) and hooks.ts (one per endpoint).
              Components are always built fresh to match the target project's design system.
            </p>
          </Card>
          <Card>
            <h3 className="text-sm font-semibold text-[#fafafa]">Quality Over Quantity</h3>
            <p className="mt-2 text-xs text-[#71717a] leading-relaxed">
              Ten deeply documented modules beat a hundred shallow ones.
              Every module should have real docs, passing tests, and actual usage before reaching stable status.
            </p>
          </Card>
        </div>
      </section>

      {/* MCP Server Setup */}
      <McpSetupSection />

      {/* Commands Reference */}
      <section>
        <h2 className="mb-4 text-lg font-semibold text-[#fafafa]">Command Reference</h2>
        <div className="rounded-lg border border-border bg-surface overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                <th className="px-5 py-3 text-left text-xs font-medium text-[#71717a] uppercase tracking-wider">Command</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-[#71717a] uppercase tracking-wider">Purpose</th>
                <th className="px-5 py-3 text-left text-xs font-medium text-[#71717a] uppercase tracking-wider">When to Use</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle">
              <tr className="hover:bg-surface-hover transition-colors">
                <td className="px-5 py-3"><code className="text-xs text-primary-light">/scout-modules</code></td>
                <td className="px-5 py-3 text-sm text-[#a1a1aa]">Scan codebase for module candidates</td>
                <td className="px-5 py-3 text-xs text-[#71717a]">Starting a new project or auditing an existing one</td>
              </tr>
              <tr className="hover:bg-surface-hover transition-colors">
                <td className="px-5 py-3"><code className="text-xs text-primary-light">/prepare-module</code></td>
                <td className="px-5 py-3 text-sm text-[#a1a1aa]">Map specific feature files to forge structure</td>
                <td className="px-5 py-3 text-xs text-[#71717a]">You know which feature to extract</td>
              </tr>
              <tr className="hover:bg-surface-hover transition-colors">
                <td className="px-5 py-3"><code className="text-xs text-primary-light">/add-module</code></td>
                <td className="px-5 py-3 text-sm text-[#a1a1aa]">Extract and add module to the forge</td>
                <td className="px-5 py-3 text-xs text-[#71717a]">After /prepare-module has mapped the files</td>
              </tr>
              <tr className="hover:bg-surface-hover transition-colors">
                <td className="px-5 py-3"><code className="text-xs text-primary-light">/use-module</code></td>
                <td className="px-5 py-3 text-sm text-[#a1a1aa]">Install a forge module into your project</td>
                <td className="px-5 py-3 text-xs text-[#71717a]">Starting a feature that the forge already has</td>
              </tr>
              <tr className="hover:bg-surface-hover transition-colors">
                <td className="px-5 py-3"><code className="text-xs text-primary-light">/health-check</code></td>
                <td className="px-5 py-3 text-sm text-[#a1a1aa]">Validate modules and skills</td>
                <td className="px-5 py-3 text-xs text-[#71717a]">Periodic maintenance</td>
              </tr>
              <tr className="hover:bg-surface-hover transition-colors">
                <td className="px-5 py-3"><code className="text-xs text-primary-light">/sync-skills</code></td>
                <td className="px-5 py-3 text-sm text-[#a1a1aa]">Copy skills to local Claude config</td>
                <td className="px-5 py-3 text-xs text-[#71717a]">After skills are updated in the forge</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
