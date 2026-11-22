// Real-hull lookups for the QA scripts, from the sections table the Blender build writes next to each GLB
// (public/models/<hull>.sections.json, see export_sections in scripts/blender/hull_lib.py).
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';

export function sectionsPath(root, glbFile) {
  return path.join(root, 'public', 'models', glbFile.replace(/\.glb$/, '.sections.json'));
}

/** Index i and fraction t so that a[i] <= v <= a[i + 1]; null outside the table. */
function bracket(a, v) {
  if (v < a[0] || v > a[a.length - 1]) return null;
  let lo = 0, hi = a.length - 1;
  while (hi - lo > 1) {
    const mid = (lo + hi) >> 1;
    if (a[mid] <= v) lo = mid; else hi = mid;
  }
  return { i: lo, t: (v - a[lo]) / (a[lo + 1] - a[lo]) };
}

export function loadHullSections(file) {
  if (!existsSync(file)) throw new Error(`${file} is missing: rebuild the hull (npm run build:hull:v8c) to write it.`);
  const s = JSON.parse(readFileSync(file, 'utf8'));
  const along = (values, x) => {
    const b = bracket(s.x, x);
    if (!b) return null;
    const a = values[b.i], c = values[b.i + 1];
    if (a === null || c === null) return a ?? c;
    return a + (c - a) * b.t;
  };
  return {
    ...s,
    /** Inner half-breadth of the shell at (x, y); 0 outside the hull. Bilinear between frames and waterlines. */
    halfBreadth(x, y) {
      const bx = bracket(s.x, x);
      if (!bx) return 0;
      // between the keel and the first waterline the hull keeps the first waterline's width
      const by = bracket(s.y, Math.max(y, s.y[0]));
      if (!by) return 0;
      const h = s.halfBreadth;
      const at = (i) => h[i][by.i] + (h[i][by.i + 1] - h[i][by.i]) * by.t;
      return at(bx.i) + (at(bx.i + 1) - at(bx.i)) * bx.t;
    },
    /** Lowest hull point on the centreline at x (null where there is no hull). */
    keel: (x) => along(s.keel, x),
    /** Main-deck height at the side, and the half-width there. */
    deck: (x) => along(s.deck, x),
    deckHalfWidth: (x) => along(s.deckHalfWidth, x) ?? 0
  };
}
