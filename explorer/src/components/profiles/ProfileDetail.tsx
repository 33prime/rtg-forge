import { useState } from 'react';
import type { ProfileData } from '../../lib/types';
import Tabs from '../shared/Tabs';
import Badge from '../shared/Badge';
import ConstraintsTable from './ConstraintsTable';

interface ProfileDetailProps {
  profile: ProfileData;
}

const tabs = [
  { label: 'Overview', value: 'overview' },
  { label: 'Constraints', value: 'constraints' },
  { label: 'Configuration', value: 'config' },
];

export default function ProfileDetail({ profile: p }: ProfileDetailProps) {
  const [activeTab, setActiveTab] = useState('overview');

  return (
    <div>
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <h1 className="text-2xl font-bold text-[#fafafa]">{p.profile.display_name}</h1>
          <Badge variant={p.profile.maturity}>{p.profile.maturity}</Badge>
        </div>
        <p className="text-[#a1a1aa]">{p.profile.description}</p>
        <div className="mt-2 flex items-center gap-4 text-sm text-[#71717a]">
          <span>v{p.profile.version}</span>
          <span>by {p.profile.vendor}</span>
          {p.profile.vendor_url && (
            <a
              href={p.profile.vendor_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary-light hover:underline"
            >
              Website
            </a>
          )}
          {p.base?.extends && (
            <span>extends: <span className="text-primary-light">{p.base.extends}</span></span>
          )}
        </div>
      </div>

      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      <div className="mt-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <div className="rounded-lg border border-border bg-surface p-4">
                <h3 className="mb-1 text-sm font-semibold text-[#fafafa]">Profile Name</h3>
                <p className="text-sm text-[#a1a1aa]">{p.profile.name}</p>
              </div>
              <div className="rounded-lg border border-border bg-surface p-4">
                <h3 className="mb-1 text-sm font-semibold text-[#fafafa]">Maturity</h3>
                <Badge variant={p.profile.maturity}>{p.profile.maturity}</Badge>
              </div>
              <div className="rounded-lg border border-border bg-surface p-4">
                <h3 className="mb-1 text-sm font-semibold text-[#fafafa]">Vendor</h3>
                <p className="text-sm text-[#a1a1aa]">{p.profile.vendor}</p>
              </div>
            </div>

            {p.constraints && (
              <div>
                <h2 className="mb-4 text-lg font-semibold text-[#fafafa]">Constraints Summary</h2>
                <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                  <div className="rounded-lg border border-border bg-surface p-4">
                    <div className="text-2xl font-bold text-green-400">
                      {p.constraints.required ? Object.keys(p.constraints.required).length : 0}
                    </div>
                    <div className="text-sm text-[#71717a]">Required</div>
                  </div>
                  <div className="rounded-lg border border-border bg-surface p-4">
                    <div className="text-2xl font-bold text-[#a1a1aa]">
                      {p.constraints.allowed ? Object.keys(p.constraints.allowed).length : 0}
                    </div>
                    <div className="text-sm text-[#71717a]">Allowed Categories</div>
                  </div>
                  <div className="rounded-lg border border-border bg-surface p-4">
                    <div className="text-2xl font-bold text-red-400">
                      {p.constraints.forbidden ? Object.keys(p.constraints.forbidden).length : 0}
                    </div>
                    <div className="text-sm text-[#71717a]">Forbidden Categories</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'constraints' && (
          <ConstraintsTable constraints={p.constraints} />
        )}

        {activeTab === 'config' && (
          <div className="space-y-4">
            <div className="rounded-lg border border-border bg-[#09090b] p-4">
              <h3 className="mb-3 text-sm font-semibold text-[#fafafa]">Profile Configuration</h3>
              <dl className="space-y-3">
                <div className="flex gap-3">
                  <dt className="min-w-[140px] text-sm text-[#71717a]">Name</dt>
                  <dd className="text-sm text-[#a1a1aa]">{p.profile.name}</dd>
                </div>
                <div className="flex gap-3">
                  <dt className="min-w-[140px] text-sm text-[#71717a]">Display Name</dt>
                  <dd className="text-sm text-[#a1a1aa]">{p.profile.display_name}</dd>
                </div>
                <div className="flex gap-3">
                  <dt className="min-w-[140px] text-sm text-[#71717a]">Version</dt>
                  <dd className="text-sm text-[#a1a1aa]">{p.profile.version}</dd>
                </div>
                <div className="flex gap-3">
                  <dt className="min-w-[140px] text-sm text-[#71717a]">Maturity</dt>
                  <dd><Badge variant={p.profile.maturity}>{p.profile.maturity}</Badge></dd>
                </div>
                <div className="flex gap-3">
                  <dt className="min-w-[140px] text-sm text-[#71717a]">Vendor</dt>
                  <dd className="text-sm text-[#a1a1aa]">{p.profile.vendor}</dd>
                </div>
                {p.base?.extends && (
                  <div className="flex gap-3">
                    <dt className="min-w-[140px] text-sm text-[#71717a]">Extends</dt>
                    <dd className="text-sm text-primary-light">{p.base.extends}</dd>
                  </div>
                )}
              </dl>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
