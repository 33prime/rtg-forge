import { useState } from 'react';
import Card from '../components/shared/Card';

type Phase = 'all' | 'now' | 'next' | 'future' | 'vision';

interface RoadmapItem {
  title: string;
  description: string;
  phase: 'now' | 'next' | 'future' | 'vision';
  category: 'core' | 'intelligence' | 'developer-experience' | 'platform' | 'community';
  impact: 'foundation' | 'high' | 'transformative';
}

const phases: { value: Phase; label: string; description: string; color: string; bg: string; border: string }[] = [
  { value: 'now', label: 'Now', description: 'Active development', color: 'text-green-400', bg: 'bg-green-500/10', border: 'border-green-500/20' },
  { value: 'next', label: 'Next', description: 'Up next', color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/20' },
  { value: 'future', label: 'Future', description: 'Planned', color: 'text-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/20' },
  { value: 'vision', label: 'Vision', description: 'Long-term', color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/20' },
];

const categories: { value: string; label: string; icon: string }[] = [
  { value: 'core', label: 'Core Engine', icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z' },
  { value: 'intelligence', label: 'Intelligence', icon: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z' },
  { value: 'developer-experience', label: 'Developer Experience', icon: 'M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z' },
  { value: 'platform', label: 'Platform', icon: 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10' },
  { value: 'community', label: 'Community', icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z' },
];

const roadmapItems: RoadmapItem[] = [
  // ── NOW ──────────────────────────────────────────────
  {
    title: 'Seed Correction Data',
    description: 'Retroactively analyze existing projects to capture 20-30 initial corrections. Run Claude with and without skills on the same codebases and record every delta. This seeds the learning loop with real data.',
    phase: 'now',
    category: 'intelligence',
    impact: 'foundation',
  },
  {
    title: 'Complete Stub Modules',
    description: 'Build out meeting_intelligence and icp_signal_extraction from stubs to full contract-compliant modules. Prove the extraction pattern works at scale beyond the single stakeholder_enrichment module.',
    phase: 'now',
    category: 'core',
    impact: 'foundation',
  },
  {
    title: 'Finish Stub Skills',
    description: 'Complete the skills currently marked "under development" — module-extraction, code-review, and mcp-server-patterns. Fill in the SKILL.md content with real patterns and examples.',
    phase: 'now',
    category: 'core',
    impact: 'foundation',
  },
  {
    title: 'Forge Explorer Roadmap Page',
    description: 'Add this roadmap page to the Explorer to demo the vision and track progress transparently.',
    phase: 'now',
    category: 'developer-experience',
    impact: 'foundation',
  },

  // ── NEXT ─────────────────────────────────────────────
  {
    title: 'Automatic Correction Capture',
    description: 'Detect when Claude rewrites code after a skill loads and auto-capture the before/after delta — no manual /capture-correction step needed. Corrections accumulate as a natural byproduct of building.',
    phase: 'next',
    category: 'intelligence',
    impact: 'high',
  },
  {
    title: 'Post-Build Audit Command',
    description: 'New /audit command that compares finished code against loaded skills and flags potential corrections automatically. Runs as a final step before deployment.',
    phase: 'next',
    category: 'developer-experience',
    impact: 'high',
  },
  {
    title: 'Production Readiness Checklist',
    description: 'New /production-readiness command that audits a project against its profile — security, performance, dependency compliance, RLS policies, environment variables, and test coverage.',
    phase: 'next',
    category: 'developer-experience',
    impact: 'high',
  },
  {
    title: 'Semantic Skill Matching',
    description: 'Replace keyword-based recommend_skills with embedding-based semantic search. Match skills to tasks by meaning, not just word overlap. Critical as the skill count grows beyond 50.',
    phase: 'next',
    category: 'intelligence',
    impact: 'high',
  },
  {
    title: 'Correction Dashboard in Explorer',
    description: 'Interactive dashboard showing correction frequency by skill, trending patterns, impact distribution, and correction rate over time. Transform the Explorer from read-only browsing to an analytics command center.',
    phase: 'next',
    category: 'developer-experience',
    impact: 'high',
  },
  {
    title: 'Module Upgrade Paths',
    description: 'Detect when projects use older versions of forge module patterns. New /upgrade-module command shows what changed and proposes a migration plan.',
    phase: 'next',
    category: 'developer-experience',
    impact: 'high',
  },

  // ── FUTURE ───────────────────────────────────────────
  {
    title: 'Multi-Tenant Organization Model',
    description: 'Add organizations, teams, and shared forges in Supabase. Each org has its own correction pool, skill overrides, and profiles. Cross-team analytics show org-wide patterns.',
    phase: 'future',
    category: 'platform',
    impact: 'transformative',
  },
  {
    title: 'Cross-Project Analytics',
    description: 'Dashboard showing patterns across all projects in an org: "Your top 10 Claude mistakes across 47 projects." Identify systemic issues that affect the whole team, not just one codebase.',
    phase: 'future',
    category: 'platform',
    impact: 'transformative',
  },
  {
    title: 'Auto-Extraction Pipeline',
    description: 'Claude Code proactively proposes module, decision, and skill additions without being asked. After every build, an extraction scoring step identifies forge contribution candidates when novelty thresholds are met.',
    phase: 'future',
    category: 'intelligence',
    impact: 'transformative',
  },
  {
    title: 'Cross-Module Relationship Graph',
    description: 'Understand which modules commonly appear together, which decisions informed which module designs, and which skills are prerequisites for which modules. Visual dependency graph in the Explorer.',
    phase: 'future',
    category: 'core',
    impact: 'high',
  },
  {
    title: 'Production Feedback Loop',
    description: 'Connect Sentry and Langfuse to the forge. Production errors and LLM performance data become a new correction source — the forge learns not just from building, but from running.',
    phase: 'future',
    category: 'intelligence',
    impact: 'transformative',
  },
  {
    title: 'Profile Marketplace',
    description: 'Organizations can publish and share profiles. A "Supabase + FastAPI + React" profile from one team can be forked and customized by another, carrying all accumulated corrections and skills.',
    phase: 'future',
    category: 'community',
    impact: 'high',
  },

  // ── VISION ───────────────────────────────────────────
  {
    title: 'The Knowledge Moat',
    description: 'Every project built with Forge deposits knowledge back. The accumulated understanding of what works, what doesn\'t, and why creates a compounding advantage impossible to replicate by starting fresh. The forge doesn\'t just store code — it stores judgment.',
    phase: 'vision',
    category: 'platform',
    impact: 'transformative',
  },
  {
    title: 'Empirical CLAUDE.md for Every Project',
    description: 'Every project gets an auto-generated CLAUDE.md pre-loaded with guidance ranked by empirical correction frequency. "Patterns Claude Gets Wrong Here" isn\'t a guess — it\'s measured data from every previous project with this tech stack.',
    phase: 'vision',
    category: 'intelligence',
    impact: 'transformative',
  },
  {
    title: 'Developer Command Center',
    description: 'Forge becomes the primary workspace for the AI-native developer — no traditional IDE needed. Scout, build, audit, optimize, deploy, and monitor all from Claude Code powered by organizational knowledge that gets smarter with every developer who uses it.',
    phase: 'vision',
    category: 'platform',
    impact: 'transformative',
  },
  {
    title: 'Community Flywheel',
    description: 'Open the correction and skill evolution pipeline to the community. Every developer contributes signal. Skills self-improve from collective usage. The more developers using Forge, the more powerful it becomes for everyone.',
    phase: 'vision',
    category: 'community',
    impact: 'transformative',
  },
];

const impactConfig: Record<string, { label: string; color: string; bg: string }> = {
  foundation: { label: 'Foundation', color: 'text-[#a1a1aa]', bg: 'bg-[#27272a]' },
  high: { label: 'High Impact', color: 'text-primary-light', bg: 'bg-primary/10' },
  transformative: { label: 'Transformative', color: 'text-amber-400', bg: 'bg-amber-500/10' },
};

export default function Roadmap() {
  const [activePhase, setActivePhase] = useState<Phase>('all');
  const [activeCategory, setActiveCategory] = useState<string>('all');

  const filtered = roadmapItems.filter((item) => {
    if (activePhase !== 'all' && item.phase !== activePhase) return false;
    if (activeCategory !== 'all' && item.category !== activeCategory) return false;
    return true;
  });

  const phaseGroups = activePhase === 'all'
    ? phases.map((p) => ({ ...p, items: filtered.filter((i) => i.phase === p.value) }))
    : phases.filter((p) => p.value === activePhase).map((p) => ({ ...p, items: filtered }));

  return (
    <div className="space-y-10">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-[#fafafa]">Roadmap</h1>
        <p className="mt-1 text-[#a1a1aa]">
          Where Forge is headed — from today&apos;s foundations to the long-term vision.
          Every feature makes the flywheel spin faster.
        </p>
      </div>

      {/* The Vision Statement */}
      <section>
        <div className="rounded-lg border border-primary/20 bg-primary/5 p-6">
          <div className="flex items-start gap-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
              <svg className="h-5 w-5 text-primary-light" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
              </svg>
            </div>
            <div>
              <h2 className="text-sm font-semibold text-[#fafafa]">The AI-Native Developer Command Center</h2>
              <p className="mt-2 text-sm leading-relaxed text-[#a1a1aa]">
                After the platform builds a project, developers use Forge to optimize, harden for production,
                and ensure every module and line of code is top tier — using their local Claude Code instance
                powered by organization-level skills and rules.
                The secret weapon: <span className="text-primary-light font-medium">human refinement</span>.
                Every correction, every decision, every extracted pattern makes the forge smarter for every developer.
                The more people using it, the more powerful it becomes.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          {phases.map((p) => {
            const count = roadmapItems.filter((i) => i.phase === p.value).length;
            return (
              <button
                key={p.value}
                onClick={() => setActivePhase(activePhase === p.value ? 'all' : p.value)}
                className={`rounded-lg border p-4 text-left transition-colors ${
                  activePhase === p.value
                    ? `${p.border} ${p.bg}`
                    : 'border-border bg-surface hover:bg-surface-hover'
                }`}
              >
                <div className={`text-2xl font-bold ${p.color}`}>{count}</div>
                <div className="mt-1 text-sm font-medium text-[#fafafa]">{p.label}</div>
                <div className="text-xs text-[#71717a]">{p.description}</div>
              </button>
            );
          })}
        </div>
      </section>

      {/* Category Filters */}
      <section>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setActiveCategory('all')}
            className={`rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
              activeCategory === 'all'
                ? 'bg-primary/20 text-primary-light'
                : 'bg-[#27272a] text-[#a1a1aa] hover:bg-[#3f3f46] hover:text-[#fafafa]'
            }`}
          >
            All Categories
          </button>
          {categories.map((cat) => (
            <button
              key={cat.value}
              onClick={() => setActiveCategory(activeCategory === cat.value ? 'all' : cat.value)}
              className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
                activeCategory === cat.value
                  ? 'bg-primary/20 text-primary-light'
                  : 'bg-[#27272a] text-[#a1a1aa] hover:bg-[#3f3f46] hover:text-[#fafafa]'
              }`}
            >
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d={cat.icon} />
              </svg>
              {cat.label}
            </button>
          ))}
        </div>
      </section>

      {/* Roadmap Items by Phase */}
      {phaseGroups.map((group) => {
        if (group.items.length === 0) return null;
        return (
          <section key={group.value}>
            <div className="mb-4 flex items-center gap-3">
              <div className={`h-3 w-3 rounded-full ${group.bg} ring-2 ${group.border}`} />
              <h2 className="text-lg font-semibold text-[#fafafa]">{group.label}</h2>
              <span className="text-xs text-[#71717a]">{group.description}</span>
              <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${group.bg} ${group.color}`}>
                {group.items.length}
              </span>
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {group.items.map((item) => {
                const cat = categories.find((c) => c.value === item.category);
                const imp = impactConfig[item.impact] || { label: 'Foundation', color: 'text-[#a1a1aa]', bg: 'bg-[#27272a]' };
                return (
                  <Card key={item.title}>
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-2">
                        {cat && (
                          <svg className="h-4 w-4 text-[#71717a]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                            <path strokeLinecap="round" strokeLinejoin="round" d={cat.icon} />
                          </svg>
                        )}
                        <span className="text-xs text-[#71717a]">{cat?.label}</span>
                      </div>
                      <span className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium ${imp.bg} ${imp.color}`}>
                        {imp.label}
                      </span>
                    </div>
                    <h3 className="mt-3 text-sm font-semibold text-[#fafafa]">{item.title}</h3>
                    <p className="mt-2 text-xs leading-relaxed text-[#71717a]">{item.description}</p>
                  </Card>
                );
              })}
            </div>
          </section>
        );
      })}

      {/* The Flywheel */}
      <section>
        <h2 className="mb-4 text-lg font-semibold text-[#fafafa]">The Flywheel</h2>
        <div className="rounded-lg border border-border bg-surface p-6">
          <p className="text-sm text-[#a1a1aa] mb-6">
            Every feature on this roadmap exists to make one loop spin faster:
          </p>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-5">
            {[
              { step: '1', title: 'Build', desc: 'Developer builds a project using Forge skills and modules', icon: 'M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z' },
              { step: '2', title: 'Capture', desc: 'Corrections recorded — what Claude got wrong, which skill fixed it', icon: 'M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z' },
              { step: '3', title: 'Learn', desc: 'Intelligence layer aggregates patterns, council debates updates', icon: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z' },
              { step: '4', title: 'Evolve', desc: 'Skills update with evidence-backed patterns, CLAUDE.md regenerates', icon: 'M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15' },
              { step: '5', title: 'Compound', desc: 'Next project starts smarter — fewer mistakes, better code, faster builds', icon: 'M13 7h8m0 0v8m0-8l-8 8-4-4-6 6' },
            ].map((item) => (
              <div key={item.step} className="rounded-lg border border-border-subtle bg-[#09090b] p-4 text-center">
                <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
                  <svg className="h-5 w-5 text-primary-light" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d={item.icon} />
                  </svg>
                </div>
                <div className="mt-3 text-xs font-bold text-primary-light">{item.step}</div>
                <div className="mt-1 text-sm font-semibold text-[#fafafa]">{item.title}</div>
                <p className="mt-2 text-[11px] leading-relaxed text-[#71717a]">{item.desc}</p>
              </div>
            ))}
          </div>
          <p className="mt-6 text-center text-xs text-[#71717a] italic">
            Every developer who uses Forge makes it smarter for every other developer. That&apos;s the moat.
          </p>
        </div>
      </section>

      {/* Get Involved CTA */}
      <section>
        <div className="rounded-lg border border-border bg-surface p-6 text-center">
          <h2 className="text-lg font-semibold text-[#fafafa]">Shape the Future of Forge</h2>
          <p className="mt-2 text-sm text-[#a1a1aa] max-w-xl mx-auto">
            This roadmap is built by the community. Every correction you capture,
            every module you extract, and every skill you improve moves us forward.
            Start with <code className="text-primary-light">/scout-modules</code> in any project.
          </p>
        </div>
      </section>
    </div>
  );
}
