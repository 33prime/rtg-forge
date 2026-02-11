import FlexSearch from 'flexsearch';
import type { ModuleManifest, SkillMeta, ProfileData, SearchResult } from './types';

interface IndexedItem {
  id: number;
  type: 'module' | 'skill' | 'profile';
  name: string;
  description: string;
  category?: string;
  url: string;
  searchText: string;
}

let index: FlexSearch.Index | null = null;
let items: IndexedItem[] = [];

export function buildSearchIndex(
  modules: ModuleManifest[],
  skills: SkillMeta[],
  profiles: ProfileData[]
): void {
  index = new FlexSearch.Index({
    tokenize: 'forward',
    resolution: 9,
  });

  items = [];
  let id = 0;

  for (const m of modules) {
    const item: IndexedItem = {
      id,
      type: 'module',
      name: m.module.name,
      description: m.module.description,
      category: m.module.category,
      url: `/modules/${m.module.name}`,
      searchText: [
        m.module.name,
        m.module.description,
        m.ai.use_when,
        m.module.category,
      ].join(' '),
    };
    items.push(item);
    index.add(id, item.searchText);
    id++;
  }

  for (const s of skills) {
    const item: IndexedItem = {
      id,
      type: 'skill',
      name: s.skill.name,
      description: s.skill.description,
      category: s.skill.category,
      url: `/skills/${s.skill.category}/${s.skill.name}`,
      searchText: [
        s.skill.name,
        s.skill.description,
        s.skill.relevance_tags.join(' '),
        s.skill.category,
        s.skill.tier,
      ].join(' '),
    };
    items.push(item);
    index.add(id, item.searchText);
    id++;
  }

  for (const p of profiles) {
    const item: IndexedItem = {
      id,
      type: 'profile',
      name: p.profile.name,
      description: p.profile.description,
      category: p.profile.maturity,
      url: `/profiles/${p.profile.name}`,
      searchText: [
        p.profile.name,
        p.profile.display_name,
        p.profile.description,
        p.profile.vendor,
      ].join(' '),
    };
    items.push(item);
    index.add(id, item.searchText);
    id++;
  }
}

export function search(query: string): SearchResult[] {
  if (!index || !query.trim()) return [];

  const resultIds = index.search(query, { limit: 50 });

  const results: SearchResult[] = [];
  for (const id of resultIds) {
    const item = items[id as number];
    if (item) {
      results.push({
        type: item.type,
        name: item.name,
        description: item.description,
        category: item.category,
        url: item.url,
        score: 1 - results.length / 50,
      });
    }
  }

  return results;
}

export function searchByType(query: string, type: 'module' | 'skill' | 'profile'): SearchResult[] {
  return search(query).filter((r) => r.type === type);
}
