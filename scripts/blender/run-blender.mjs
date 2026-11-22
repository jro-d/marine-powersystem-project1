// Run one or more Blender generator scripts headless:  node scripts/blender/run-blender.mjs generate_hull_v8c.py [more.py ...]
// Blender is found via $BLENDER_PATH, then PATH, then the usual install folders.
import { spawnSync } from 'node:child_process';
import { existsSync, readdirSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..', '..');

function findBlender() {
  if (process.env.BLENDER_PATH && existsSync(process.env.BLENDER_PATH)) return process.env.BLENDER_PATH;
  const probe = spawnSync(process.platform === 'win32' ? 'where' : 'which', ['blender'], { encoding: 'utf8' });
  if (probe.status === 0 && probe.stdout.trim()) return probe.stdout.trim().split(/\r?\n/)[0];
  const candidates = ['D:/Blender/blender.exe', 'C:/Blender/blender.exe', '/Applications/Blender.app/Contents/MacOS/Blender', '/usr/bin/blender', '/snap/bin/blender'];
  for (const base of ['C:/Program Files/Blender Foundation', 'D:/Program Files/Blender Foundation']) {
    if (existsSync(base)) for (const dir of readdirSync(base).sort().reverse()) candidates.push(path.join(base, dir, 'blender.exe'));
  }
  return candidates.find((c) => existsSync(c));
}

const blender = findBlender();
if (!blender) {
  console.error('Blender not found. Install Blender 4.2+ or set BLENDER_PATH to blender(.exe).');
  process.exit(1);
}
const scripts = process.argv.slice(2);
if (!scripts.length) {
  console.error('Usage: node scripts/blender/run-blender.mjs <script.py> [...]');
  process.exit(1);
}
for (const s of scripts) {
  const script = path.isAbsolute(s) ? s : path.join(here, s);
  console.log(`\n> ${path.basename(blender)} --background --python ${path.relative(root, script)}`);
  const r = spawnSync(blender, ['--background', '--factory-startup', '--python-exit-code', '1', '--python', script], { cwd: root, stdio: 'inherit' });
  if (r.status !== 0) process.exit(r.status ?? 1);
}
