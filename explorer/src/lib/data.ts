import type { ModuleManifest, SkillMeta, ProfileData } from './types';

const DATA_BASE = '/data';

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${DATA_BASE}/${path}`);
  if (!res.ok) throw new Error(`Failed to load ${path}`);
  return res.json() as Promise<T>;
}

export async function loadModules(): Promise<ModuleManifest[]> {
  return fetchJson<ModuleManifest[]>('modules-index.json');
}

export async function loadModuleDocs(): Promise<Record<string, string>> {
  return fetchJson<Record<string, string>>('modules-docs.json');
}

export async function loadModuleSources(): Promise<Record<string, Record<string, string>>> {
  return fetchJson<Record<string, Record<string, string>>>('modules-sources.json');
}

export async function loadSkills(): Promise<SkillMeta[]> {
  return fetchJson<SkillMeta[]>('skills-index.json');
}

export async function loadSkillDocs(): Promise<Record<string, string>> {
  return fetchJson<Record<string, string>>('skills-docs.json');
}

export async function loadProfiles(): Promise<ProfileData[]> {
  return fetchJson<ProfileData[]>('profiles-index.json');
}
