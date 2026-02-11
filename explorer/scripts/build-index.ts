import * as fs from 'node:fs';
import * as path from 'node:path';
import * as TOML from '@iarna/toml';

const ROOT = path.resolve(import.meta.dirname, '..', '..');
const OUT_DIR = path.resolve(import.meta.dirname, '..', 'public', 'data');

function ensureOutDir() {
  if (!fs.existsSync(OUT_DIR)) {
    fs.mkdirSync(OUT_DIR, { recursive: true });
  }
}

function readToml(filePath: string): Record<string, unknown> | null {
  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    return TOML.parse(content) as Record<string, unknown>;
  } catch {
    console.warn(`  Warning: Could not parse ${filePath}`);
    return null;
  }
}

function readMarkdown(filePath: string): string | null {
  try {
    return fs.readFileSync(filePath, 'utf-8');
  } catch {
    return null;
  }
}

function getDirs(dirPath: string): string[] {
  if (!fs.existsSync(dirPath)) return [];
  return fs
    .readdirSync(dirPath, { withFileTypes: true })
    .filter((d) => d.isDirectory() && d.name !== '_template')
    .map((d) => d.name);
}

function buildModulesIndex(): void {
  const modulesDir = path.join(ROOT, 'modules');
  const modules: Record<string, unknown>[] = [];
  const docs: Record<string, string> = {};

  for (const name of getDirs(modulesDir)) {
    const tomlPath = path.join(modulesDir, name, 'module.toml');
    const mdPath = path.join(modulesDir, name, 'MODULE.md');

    const manifest = readToml(tomlPath);
    if (manifest) {
      modules.push(manifest);
    }

    const md = readMarkdown(mdPath);
    if (md) {
      docs[name] = md;
    }
  }

  fs.writeFileSync(path.join(OUT_DIR, 'modules-index.json'), JSON.stringify(modules, null, 2));
  console.log(`  modules-index.json: ${modules.length} modules`);

  fs.writeFileSync(path.join(OUT_DIR, 'modules-docs.json'), JSON.stringify(docs, null, 2));
  console.log(`  modules-docs.json: ${Object.keys(docs).length} docs`);
}

function buildSkillsIndex(): void {
  const skillsDir = path.join(ROOT, 'skills');
  const skills: Record<string, unknown>[] = [];
  const docs: Record<string, string> = {};

  for (const category of getDirs(skillsDir)) {
    const categoryDir = path.join(skillsDir, category);
    for (const name of getDirs(categoryDir)) {
      const tomlPath = path.join(categoryDir, name, 'meta.toml');
      const mdPath = path.join(categoryDir, name, 'SKILL.md');

      const meta = readToml(tomlPath);
      if (meta) {
        skills.push(meta);
      }

      const md = readMarkdown(mdPath);
      if (md) {
        docs[`${category}/${name}`] = md;
      }
    }
  }

  fs.writeFileSync(path.join(OUT_DIR, 'skills-index.json'), JSON.stringify(skills, null, 2));
  console.log(`  skills-index.json: ${skills.length} skills`);

  fs.writeFileSync(path.join(OUT_DIR, 'skills-docs.json'), JSON.stringify(docs, null, 2));
  console.log(`  skills-docs.json: ${Object.keys(docs).length} docs`);
}

function buildProfilesIndex(): void {
  const profilesDir = path.join(ROOT, 'profiles');
  const profiles: Record<string, unknown>[] = [];

  for (const name of getDirs(profilesDir)) {
    const profilePath = path.join(profilesDir, name, 'profile.toml');
    const constraintsPath = path.join(profilesDir, name, 'constraints.toml');

    const profile = readToml(profilePath);
    if (!profile) continue;

    const constraints = readToml(constraintsPath);
    if (constraints) {
      (profile as Record<string, unknown>).constraints = constraints;
    }

    profiles.push(profile);
  }

  fs.writeFileSync(path.join(OUT_DIR, 'profiles-index.json'), JSON.stringify(profiles, null, 2));
  console.log(`  profiles-index.json: ${profiles.length} profiles`);
}

function main() {
  console.log('Building explorer data indexes...');
  console.log(`  Root: ${ROOT}`);
  console.log(`  Output: ${OUT_DIR}`);
  console.log('');

  ensureOutDir();
  buildModulesIndex();
  buildSkillsIndex();
  buildProfilesIndex();

  console.log('');
  console.log('Done!');
}

main();
