import { readFile, stat } from 'node:fs/promises';
import path from 'node:path';

const dist = path.resolve('dist');
const html = await readFile(path.join(dist, 'index.html'), 'utf8');
const entry = html.match(/<script[^>]+src="\/?([^\"]+\.js)"/)?.[1];
if (!entry) throw new Error('Could not identify the built application entry');
let manifest = {};
try { manifest = JSON.parse(await readFile(path.join(dist, '.vite/manifest.json'), 'utf8')); }
catch (error) { if (error.code !== 'ENOENT') throw error; }
const files = new Set([entry]);
const visit = (key) => {
  const item = manifest[key];
  if (!item) return;
  files.add(item.file);
  for (const dependency of item.imports ?? []) {
    if (!files.has(manifest[dependency]?.file)) visit(dependency);
  }
};
for (const [key, item] of Object.entries(manifest)) if (item.isEntry) visit(key);
const bytes = (await Promise.all([...files].filter((file) => file.endsWith('.js')).map(async (file) => (await stat(path.join(dist, file))).size))).reduce((sum, size) => sum + size, 0);
console.log(`Entry JavaScript plus static imports: ${(bytes / 1000).toFixed(2)} kB (limit 400 kB)`);
if (bytes >= 400000) throw new Error('Main JavaScript exceeds the 400 kB budget');
