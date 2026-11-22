import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { HULL_VARIANTS, applyAppHullStyle, isHullVariant, type HullVariant } from '../vessel/hull-style';
import { resolvePublicAsset } from '../vessel/assets';

type Mode = 'textured' | 'glass' | 'xray';
const XRAY_HIDE = ['ShipHull', 'Main_Deck', 'CargoBay', 'Hatch_', 'Accommodation', 'House_Deck', 'Bridge_Window', 'Deck_Safety', 'Deck_Mooring', 'Anchor_Chain', 'Bilge_Keel', 'Hull_Markings', 'Deck_Fittings'];

const view = document.getElementById('view')!;
const status = document.getElementById('status')!;
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(2, window.devicePixelRatio));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
view.prepend(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xdfe6ec);
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
scene.add(new THREE.HemisphereLight(0xffffff, 0x8fa6b4, 1.2));
const sun = new THREE.DirectionalLight(0xffffff, 1.8);
sun.position.set(-12, 30, 18);
scene.add(sun);
const grid = new THREE.GridHelper(70, 35, 0xb8c4cc, 0xccd5dc);
grid.position.y = -3.2;
scene.add(grid);

const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 500);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;

// Camera presets in three.js space (x stern->bow, y up, z starboard)
const CAMS: Record<string, [number, number, number, number, number, number]> = {
  bow: [40, 12, -26, 6, -0.5, 0],
  stern: [-38, 9, 24, -8, -0.5, 0],
  profile: [2.5, 0, 62, 2.5, -0.2, 0],
  plan: [2.5, 58, 0.01, 2.5, 0, 0],
  under: [-24, -10, 14, -15, -2, 0],
  house: [-1, 6.5, 12, -11, 2.5, 0]
};
function setCam(name: string) {
  const c = CAMS[name];
  camera.position.set(c[0], c[1], c[2]);
  controls.target.set(c[3], c[4], c[5]);
  controls.update();
  document.querySelectorAll<HTMLButtonElement>('#cams button').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.cam === name)));
}

const loader = new GLTFLoader();
const cache = new Map<HullVariant, { gltf: THREE.Group; bytes: number }>();
let current: THREE.Object3D | null = null;
let variant: HullVariant = 'v8c';
let mode: Mode = 'textured';

async function fetchHull(v: HullVariant) {
  const hit = cache.get(v);
  if (hit) return hit;
  const url = resolvePublicAsset(HULL_VARIANTS[v].file);
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${HULL_VARIANTS[v].file}: HTTP ${res.status}`);
  const buf = await res.arrayBuffer();
  const gltf = await loader.parseAsync(buf, url.substring(0, url.lastIndexOf('/') + 1));
  const entry = { gltf: gltf.scene, bytes: buf.byteLength };
  cache.set(v, entry);
  return entry;
}

function statsOf(root: THREE.Object3D) {
  let tris = 0, meshes = 0;
  const textures = new Set<THREE.Texture>();
  root.traverse((o) => {
    if (!(o instanceof THREE.Mesh)) return;
    meshes++;
    const g = o.geometry as THREE.BufferGeometry;
    tris += (g.index ? g.index.count : g.attributes.position.count) / 3;
    (Array.isArray(o.material) ? o.material : [o.material]).forEach((m) => {
      for (const k of ['map', 'normalMap', 'roughnessMap'] as const) {
        const t = (m as THREE.MeshStandardMaterial)[k];
        if (t) textures.add(t);
      }
    });
  });
  return { tris: Math.round(tris), meshes, textures: textures.size };
}

function present(base: THREE.Group): THREE.Object3D {
  const root = base.clone(true);
  root.traverse((o) => {
    if (o instanceof THREE.Mesh) o.material = Array.isArray(o.material) ? o.material.map((m) => m.clone()) : o.material.clone();
  });
  if (mode === 'glass') applyAppHullStyle(root);
  if (mode === 'xray') {
    root.traverse((o) => {
      if (XRAY_HIDE.some((h) => o.name.includes(h))) o.visible = false;
    });
  }
  return root;
}

async function show() {
  status.textContent = `loading ${HULL_VARIANTS[variant].file}…`;
  try {
    const { gltf } = await fetchHull(variant);
    if (current) scene.remove(current);
    current = present(gltf);
    scene.add(current);
    scene.background = new THREE.Color(mode === 'glass' ? 0xf8fafc : 0xdfe6ec);
    const s = statsOf(gltf);
    status.textContent = `${HULL_VARIANTS[variant].label} · ${s.meshes} meshes · ${s.tris.toLocaleString()} tris · ${s.textures} textures`;
    (document.getElementById('open') as HTMLAnchorElement).href = `./?hull=${variant}`;
    const u = new URL(window.location.href);
    u.searchParams.set('hull', variant);
    history.replaceState(null, '', u);
  } catch (err) {
    status.textContent = `Could not load ${HULL_VARIANTS[variant].file}. Run the matching Blender script first. (${(err as Error).message})`;
  }
  document.querySelectorAll<HTMLButtonElement>('#variants .card').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.v === variant)));
  document.querySelectorAll<HTMLButtonElement>('#modes button').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.mode === mode)));
}

// Variant cards (with file size once loaded)
const list = document.getElementById('variants')!;
for (const [key, info] of Object.entries(HULL_VARIANTS)) {
  const card = document.createElement('button');
  card.className = 'card';
  card.dataset.v = key;
  card.innerHTML = `<b>${info.label}</b><span>${info.blurb}</span><div class="stats"></div>`;
  card.addEventListener('click', () => { variant = key as HullVariant; show(); });
  list.appendChild(card);
  fetchHull(key as HullVariant)
    .then(({ gltf, bytes }) => {
      const s = statsOf(gltf);
      card.querySelector('.stats')!.textContent = `${(bytes / 1e6).toFixed(1)} MB · ${(s.tris / 1000).toFixed(0)}k tris · ${s.textures} tex`;
    })
    .catch(() => { card.querySelector('.stats')!.textContent = 'not built yet'; });
}
document.querySelectorAll<HTMLButtonElement>('#modes button').forEach((b) => b.addEventListener('click', () => { mode = b.dataset.mode as Mode; show(); }));
document.querySelectorAll<HTMLButtonElement>('#cams button').forEach((b) => b.addEventListener('click', () => setCam(b.dataset.cam!)));

const requested = new URLSearchParams(window.location.search).get('hull');
if (isHullVariant(requested)) variant = requested;

function resize() {
  const w = view.clientWidth, h = view.clientHeight;
  renderer.setSize(w, h, false);
  camera.aspect = w / Math.max(1, h);
  camera.updateProjectionMatrix();
}
new ResizeObserver(resize).observe(view);
resize();
setCam('bow');
show();
renderer.setAnimationLoop(() => { controls.update(); renderer.render(scene, camera); });
