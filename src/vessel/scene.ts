import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { connections, equipment, type SimState, type ModelType, type Connection, connectionState } from '../core/network';
import { createModel, type ModelInstance } from '../assemblies/models';
import {
  createVessel,
  createVesselEquipment,
  propellerAssembly,
  transformerAssembly,
  driveAssembly,
  motorAssembly,
  steeringAssembly,
  reeferAssembly,
  pumpAssembly,
  esbCubicleAssembly,
  batterySystemAssembly,
  airCompressorAssembly,
  ventFanAssembly,
  ballastOwsAssembly,
  galleyBoardAssembly,
  shorePowerAssembly,
  bridgeNavComAssembly
} from './vessel';
import { vesselLayout, SHIP } from './vessel-layout';

export type ConnectionTier = 'hv' | 'lv' | 'consumer' | 'emergency' | 'mechanical';
export type FlowFilterMode = 'all' | 'focus' | 'hv' | 'lv' | 'consumer' | 'emergency';

const C = { live: 0xdc2626, dead: 0x6b7f8f, open: 0xdf8a1c, selected: 0x0b2a3b };
const BG = { vessel: 0xf8fafc, exploded: 0xeceef0 };
const UP_AXIS = new THREE.Vector3(0, 1, 0);

const TIER_STYLE: Record<ConnectionTier, { live: number; aura: number; pulse: number; pulseHalo: number; radius: number }> = {
  hv:         { live: 0xdc2626, aura: 0xef4444, pulse: 0xfef08a, pulseHalo: 0xfacc15, radius: 0.015 },
  lv:         { live: 0x2563eb, aura: 0x3b82f6, pulse: 0xe0f2fe, pulseHalo: 0x38bdf8, radius: 0.011 },
  consumer:   { live: 0x16a34a, aura: 0x22c55e, pulse: 0xdcfce7, pulseHalo: 0x4ade80, radius: 0.0095 },
  emergency:  { live: 0xea580c, aura: 0xf97316, pulse: 0xfef3c7, pulseHalo: 0xfbbf24, radius: 0.012 },
  mechanical: { live: 0x5f7a8b, aura: 0x5f7a8b, pulse: 0x5f7a8b, pulseHalo: 0x5f7a8b, radius: 0.045 }
};

const HV_CONN_IDS = new Set([
  'gb1', 'gb2', 'shoreBreaker', 'gb3', 'gb4', 'tie',
  'propFeed', 'driveMotor', 'reeferAFeed', 'txAFeed', 'txBFeed', 'reeferBFeed', 'bowFeed'
]);
const CONSUMER_CONN_IDS = new Set([
  'txConAOut', 'txConBOut', 'consumerTie', 'lightAFeed', 'galleySmallFeed', 'navFeed'
]);
const EMERGENCY_CONN_IDS = new Set([
  'esbTieFeed', 'egBreaker', 'eSteerFeed', 'eFireFeed', 'eLightFeed', 'eRadioFeed', 'navEmFeed'
]);

export function getConnectionTier(c: Connection): ConnectionTier {
  if (c.id === 'shaft') return 'mechanical';
  if (EMERGENCY_CONN_IDS.has(c.id)) return 'emergency';
  if (CONSUMER_CONN_IDS.has(c.id)) return 'consumer';
  if (HV_CONN_IDS.has(c.id)) return 'hv';
  return 'lv';
}

export function getEquipmentTier(id: string): ConnectionTier {
  if (id === 'prop') return 'mechanical';
  if (['eg', 'eBus', 'eSteer', 'eFire', 'eLights', 'eRadio'].includes(id)) return 'emergency';
  if (['txConA', 'txConB', 'consumerA', 'consumerB', 'lightsA', 'galleySmall', 'nav'].includes(id)) return 'consumer';
  if (['dg1', 'dg2', 'dg3', 'dg4', 'shore', 'busA', 'busB', 'drive', 'motor', 'bow', 'txA', 'txB', 'txReeferA', 'txReeferB'].includes(id)) return 'hv';
  return 'lv';
}

/**
 * Segregated 3D shipboard cable trunk router.
 * Routes Port and Starboard equipment along dedicated side cable trays, pump headers,
 * and vertical superstructure risers instead of collapsing all paths onto Z = 0.
 */
function buildCableWaypoints(c: Connection, a: THREE.Vector3, b: THREE.Vector3): THREE.Vector3[] {
  const V = (x: number, y: number, z: number) => new THREE.Vector3(x, y, z);
  switch (c.id) {
    // Direct single-segment links
    case 'shaft':
    case 'lvTie':
    case 'consumerTie':
    case 'txConAOut':
    case 'txConBOut':
    case 'egBreaker':
      return [a, b];

    // Flexible reefer container plug loops
    case 'reeferPlug':
    case 'reeferPlugA':
    case 'reeferPlugB':
      return [a, V((a.x + b.x) / 2, Math.min(a.y, b.y) - 0.08, (a.z + b.z) / 2), b];

    // 6.6 kV Bus Tie across Engine Control Room
    case 'tie':
      return [a, V(a.x, a.y + 0.12, 0), V(b.x, b.y + 0.12, 0), b];

    // 6.6 kV Generators & Shore Connection
    case 'gb1':
    case 'gb4':
      return [a, V(a.x, b.y, a.z), V(b.x, b.y, a.z), b];
    case 'gb2':
      return [a, V(a.x, -0.08, -1.05), V(b.x, -0.08, -1.05), V(b.x, b.y, -1.05), b];
    case 'gb3':
      return [a, V(a.x, -0.08, 1.05), V(b.x, -0.08, 1.05), V(b.x, b.y, 1.05), b];
    case 'shoreBreaker':
      return [a, V(a.x, 0.82, -2.45), V(b.x, 0.82, -2.45), V(b.x, b.y, -1.05), b];

    // 6.6 kV Propulsion & Bow Thruster Trunks
    case 'propFeed':
      return [a, V(a.x, -0.18, -0.95), V(b.x, -0.18, -0.95), V(b.x, b.y, b.z), b];
    case 'driveMotor':
      return [a, V(a.x, b.y, a.z), V(b.x, b.y, a.z), b];
    case 'bowFeed':
      return [a, V(a.x, -0.58, 0.68), V(18.6, -0.58, 0.68), V(18.6, b.y, 0), b];

    // 6.6 kV Transformer Primary Feeders
    case 'txAFeed':
      return [a, V(a.x, -0.22, -0.72), V(b.x, -0.22, -0.72), V(b.x, -0.22, b.z), b];
    case 'txBFeed':
      return [a, V(a.x, -0.22, 0.72), V(b.x, -0.22, 0.72), V(b.x, -0.22, b.z), b];
    case 'reeferAFeed':
      return [a, V(a.x, b.y, -1.12), V(b.x, b.y, -1.12), b];
    case 'reeferBFeed':
      return [a, V(a.x, b.y, 1.12), V(b.x, b.y, 1.12), b];

    // 440 V Transformer Secondary Incomers
    case 'txAOut':
    case 'txBOut':
      return [a, V(a.x, b.y, a.z), V(b.x, b.y, a.z), b];
    case 'txReeferAOut':
      return [a, V(a.x, 0.88, -2.15), V(b.x, 0.88, -2.15), V(b.x, b.y, b.z), b];
    case 'txReeferBOut':
      return [a, V(a.x, 0.88, 2.15), V(b.x, 0.88, 2.15), V(b.x, b.y, b.z), b];

    // 440 V Port Engine Room Pump Header Tray (z = -1.65, y = -1.12)
    case 'fire1Feed':
    case 'cooling1Feed':
    case 'airCompFeed':
      return [a, V(a.x, -1.12, -1.65), V(b.x, -1.12, -1.65), V(b.x, b.y, b.z), b];

    // 440 V Starboard Engine Room Pump Header Tray (z = +1.65, y = -1.12)
    case 'fire2Feed':
    case 'cooling2Feed':
    case 'ballastFeed':
    case 'bilgeFeed':
      return [a, V(a.x, -1.12, 1.65), V(b.x, -1.12, 1.65), V(b.x, b.y, b.z), b];

    // 440 V Deck & Superstructure Feeders
    case 'craneFeed':
      return [a, V(a.x, 0.82, -0.90), V(b.x, 0.82, -0.90), b];
    case 'galley440Feed':
      return [a, V(a.x, 0.92, -0.85), V(b.x, 0.92, -0.85), b];
    case 'conAAcb':
      return [a, V(a.x, 0.96, -1.45), V(b.x, 0.96, -1.45), b];
    case 'conBAcb':
      return [a, V(a.x, 0.96, 1.45), V(b.x, 0.96, 1.45), b];
    case 'ventFanFeed':
      return [a, V(a.x, 0.96, 1.15), V(b.x, 0.96, 1.15), b];

    // 220 V Domestic & Bridge Risers
    case 'lightAFeed':
      return [a, V(b.x, a.y, a.z), V(b.x, b.y, a.z), b];
    case 'galleySmallFeed':
      return [a, V(b.x, b.y, a.z), b];
    case 'navFeed':
      return [a, V(b.x, a.y, a.z), V(b.x, 3.52, a.z), V(b.x, 3.52, 0), b];

    // SOLAS 440 V / 24 V DC Emergency Trunks
    case 'esbTieFeed':
      return [a, V(a.x, a.y, -1.35), V(b.x, a.y, -1.35), b];
    case 'eSteerFeed':
      return [a, V(b.x, 2.35, -1.35), V(b.x, b.y, -1.35), b];
    case 'eFireFeed':
      return [a, V(a.x, -1.55, -1.35), V(a.x, -1.55, 0.95), V(b.x, -1.55, 0.95), b];
    case 'eLightFeed':
      return [a, V(a.x, b.y, -1.35), V(b.x, b.y, -1.35), b];
    case 'eRadioFeed':
      return [a, V(b.x, 3.52, -1.35), V(b.x, 3.52, 1.25), b];
    case 'navEmFeed':
      return [a, V(b.x, 3.52, -1.35), V(b.x, 3.52, 0), b];

    default: {
      const sideZ = Math.abs(a.z) > 0.1 ? a.z : b.z;
      return [a, V(a.x, a.y, sideZ), V(b.x, a.y, sideZ), V(b.x, b.y, sideZ), b];
    }
  }
}

/**
 * Traces the active upstream supply chain and downstream branches for a selected equipment or connection.
 */
function computeFocusedCircuit(selection: string, state: SimState, live: Set<string>): { edges: Set<string>; nodes: Set<string> } {
  const edges = new Set<string>();
  const nodes = new Set<string>();
  if (!selection) return { edges, nodes };

  const TIE_IDS = new Set(['tie', 'lvTie', 'consumerTie']);
  const BUS_IDS = new Set(['busA', 'busB', 'lvBusA', 'lvBusB', 'consumerA', 'consumerB', 'eBus', 'reeferA', 'reeferB']);

  const selConn = connections.find(c => c.id === selection);
  const startNodes = selConn ? [selConn.from, selConn.to] : [selection];
  if (selConn) edges.add(selConn.id);
  for (const n of startNodes) nodes.add(n);

  // 1. Upstream BFS (trace back toward power sources)
  const upQueue = [...startNodes];
  const upVisited = new Set<string>(startNodes);
  while (upQueue.length > 0) {
    const curr = upQueue.shift()!;
    const incoming = connections.filter(c => c.to === curr && !TIE_IDS.has(c.id));
    const liveIncoming = incoming.filter(c => connectionState(c, state, live) === 'live');
    const chosenIncoming = liveIncoming.length > 0 ? liveIncoming : incoming;

    let fedDirectly = false;
    for (const c of chosenIncoming) {
      if (connectionState(c, state, live) === 'live' || !live.has(curr)) {
        edges.add(c.id);
        nodes.add(c.from);
        if (connectionState(c, state, live) === 'live') fedDirectly = true;
        if (!upVisited.has(c.from)) {
          upVisited.add(c.from);
          upQueue.push(c.from);
        }
      }
    }

    // Cross bus-tie only if this bus is not already directly fed on its own side
    if (!fedDirectly) {
      const ties = connections.filter(c => TIE_IDS.has(c.id) && (c.from === curr || c.to === curr));
      for (const t of ties) {
        if (connectionState(t, state, live) === 'live') {
          const other = t.from === curr ? t.to : t.from;
          edges.add(t.id);
          nodes.add(other);
          if (!upVisited.has(other)) {
            upVisited.add(other);
            upQueue.push(other);
          }
        }
      }
    }
  }

  // 2. Downstream trace
  if (BUS_IDS.has(selection)) {
    // For a switchboard busbar, highlight its direct outgoing feeders and bus-tie
    for (const c of connections) {
      if (c.from === selection || (TIE_IDS.has(c.id) && c.to === selection)) {
        edges.add(c.id);
        nodes.add(c.from);
        nodes.add(c.to);
      }
    }
  } else {
    // For generators, transformers, drives, and loads, trace downstream chain
    const downQueue = selConn ? [selConn.to] : [selection];
    const downVisited = new Set<string>(downQueue);
    while (downQueue.length > 0) {
      const curr = downQueue.shift()!;
      for (const c of connections) {
        if (c.from === curr && !TIE_IDS.has(c.id)) {
          edges.add(c.id);
          nodes.add(c.to);
          if (!BUS_IDS.has(c.to) && !downVisited.has(c.to)) {
            downVisited.add(c.to);
            downQueue.push(c.to);
          }
        }
      }
    }
  }

  return { edges, nodes };
}

function renderer(host: HTMLElement): THREE.WebGLRenderer {
  const r = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  r.setPixelRatio(Math.min(devicePixelRatio, 2));
  r.setSize(Math.max(1, host.clientWidth), Math.max(1, host.clientHeight));
  r.outputColorSpace = THREE.SRGBColorSpace;
  host.appendChild(r.domElement);
  return r;
}
function lights(scene: THREE.Scene) {
  scene.add(new THREE.HemisphereLight(0xffffff, 0x8fa6b4, 2.4));
  const key = new THREE.DirectionalLight(0xffffff, 2.2); key.position.set(-5, 12, 8); scene.add(key);
  const fill = new THREE.DirectionalLight(0xbfd8e6, 1); fill.position.set(8, 3, -8); scene.add(fill);
}
function lineBetween(a: THREE.Vector3, b: THREE.Vector3, radius = .012, auraColor = 0xff3b3b): THREE.Mesh {
  const diff = b.clone().sub(a);
  const len = Math.max(.001, diff.length());
  const mesh = new THREE.Mesh(
    new THREE.CylinderGeometry(radius, radius, len, 8),
    new THREE.MeshBasicMaterial({ color: C.dead, transparent: true, opacity: .5, depthWrite: false })
  );
  // Outer voltage-tinted glow aura mesh (visible when energized)
  const glow = new THREE.Mesh(
    new THREE.CylinderGeometry(radius * 1.85, radius * 1.85, len, 8),
    new THREE.MeshBasicMaterial({
      color: auraColor,
      transparent: true,
      opacity: 0.26,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    })
  );
  glow.userData.glowAura = true;
  glow.visible = false;
  mesh.add(glow);
  mesh.position.copy(a).add(b).multiplyScalar(.5);
  mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), diff.normalize());
  mesh.userData.path = true;
  return mesh;
}

/**
 * Clean white ocean floor with a subtle engineering grid texture and soft radial falloff.
 * Provides a bright, unobstructed backdrop so the ship hull, interior equipment, and
 * animated electrical power flows read cleanly without dark color cast.
 */
function createNetFloor(): THREE.Mesh {
  const material = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    side: THREE.DoubleSide,
    vertexShader: `
      varying vec3 vWorld;
      void main() {
        vec4 world = modelMatrix * vec4(position, 1.0);
        vWorld = world.xyz;
        gl_Position = projectionMatrix * viewMatrix * world;
      }
    `,
    fragmentShader: `
      varying vec3 vWorld;
      void main() {
        vec2 p = vWorld.xz;

        // Net grid lines: 1m fine net mesh and 5m primary net cords
        vec2 gridFine = abs(fract(p - 0.5) - 0.5) / fwidth(p);
        float lineFine = 1.0 - min(min(gridFine.x, gridFine.y), 1.0);

        vec2 gridMajor = abs(fract(p / 5.0 - 0.5) - 0.5) / fwidth(p / 5.0);
        float lineMajor = 1.0 - min(min(gridMajor.x, gridMajor.y), 1.0);

        // Subtle intersection accents
        vec2 knotDelta = abs(fract(p - 0.5) - 0.5);
        float knots = smoothstep(0.10, 0.0, length(knotDelta)) * 0.25;

        // Combined subtle grid line intensity
        float net = clamp(max(lineFine * 0.30, lineMajor * 0.65) + knots, 0.0, 1.0);

        // Soft radial fade so the floor blends seamlessly into the light horizon
        float dist = length(p);
        float fade = smoothstep(80.0, 24.0, dist);

        // Pure white ocean floor base transitioning gently toward studio horizon
        vec3 coreWhite = vec3(1.0, 1.0, 1.0);       // #ffffff
        vec3 outerWhite = vec3(0.973, 0.980, 0.988); // #f8fafc
        vec3 floorBase = mix(coreWhite, outerWhite, smoothstep(8.0, 55.0, dist));

        // Crisp, subtle architectural slate grid lines on white
        vec3 netFineColor = vec3(0.886, 0.910, 0.941);  // #e2e8f0
        vec3 netMajorColor = vec3(0.796, 0.835, 0.882); // #cbd5e1
        vec3 knotColor = vec3(0.720, 0.780, 0.845);

        vec3 netCol = mix(netFineColor, netMajorColor, lineMajor);
        netCol = mix(netCol, knotColor, clamp(knots * 2.0, 0.0, 1.0));

        vec3 col = mix(floorBase, netCol, net);

        // Solid crisp white floor fading smoothly at far perimeter
        float alpha = fade * 0.98;
        gl_FragColor = vec4(col, alpha);
      }
    `
  });

  const geometry = new THREE.PlaneGeometry(180, 180);
  geometry.rotateX(-Math.PI / 2);
  const floor = new THREE.Mesh(geometry, material);
  floor.position.y = SHIP.keel - 0.05;
  floor.renderOrder = -100;
  floor.frustumCulled = false;
  return floor;
}

export class VesselView {
  private renderer: THREE.WebGLRenderer;
  private scene = new THREE.Scene();
  private camera = new THREE.PerspectiveCamera(43, 1, .1, 160);
  private controls: OrbitControls;
  private hull = createVessel();
  private objects = new Map<string, THREE.Group>();
  private paths = new Map<string, THREE.Group>();
  private labels = new Map<string, HTMLDivElement>();
  private ray = new THREE.Raycaster();
  private pointer = new THREE.Vector2();
  private pointerDown = new THREE.Vector2();
  private live = new Set<string>();
  private state!: SimState;
  private selection = 'busA';
  private labelsVisible = true;
  private flowFilter: FlowFilterMode = 'all';
  private focusedEdges = new Set<string>();
  private focusedNodes = new Set<string>();
  private phase = 0;
  private floor = createNetFloor();
  private lastTime = 0;
  onSelect: (id: string) => void = () => {};

  constructor(private host: HTMLElement) {
    this.renderer = renderer(host);
    this.scene.background = new THREE.Color(BG.vessel);
    lights(this.scene);
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.target.set(0, .5, 0);
    this.controls.enableDamping = true;
    this.controls.minDistance = 3;
    this.controls.maxDistance = 95;
    this.controls.maxPolarAngle = Math.PI * .62;
    this.scene.add(this.hull);
    this.scene.add(this.floor);
    for (const e of equipment) {
      const group = createVesselEquipment(e);
      const placement = vesselLayout[e.id];
      const isReefer = e.id === 'reeferUnit' || e.id === 'reeferUnitA' || e.id === 'reeferUnitB';
      const eqScale = isReefer ? 1.0 : (e.id === 'prop' ? 0.75 * 1.20 : 0.75);
      const size = placement.size.map(v => v * eqScale), inContainer = placement.space === 'cargo';
      const radius = inContainer ? .22 : Math.max(.12, Math.max(size[0], size[2]) / 2 + .04);
      const halo = new THREE.Mesh(new THREE.RingGeometry(radius, radius + .022, 32), new THREE.MeshBasicMaterial({ color: C.dead, transparent: true, opacity: .45, side: THREE.DoubleSide, depthWrite: false }));
      halo.rotation.x = -Math.PI / 2; halo.position.y = .012; halo.userData.halo = true;
      // A container's ring sits just outside its refrigeration end, which faces -x when the container is rotated half a turn.
      if (inContainer) halo.position.x = (placement.rotation === Math.PI ? -1 : 1) * (size[0] / 2 + .15);
      group.add(halo);
      this.objects.set(e.id, group); this.scene.add(group);
      const label = document.createElement('div'); label.className = 'vessel-label'; label.textContent = e.short;
      label.dataset.defaultVisible = String(!!e.label3d);
      label.dataset.tier = getEquipmentTier(e.id);
      label.style.pointerEvents = 'auto';
      label.style.cursor = 'pointer';
      label.addEventListener('click', (ev) => {
        ev.stopPropagation();
        this.onSelect(e.id);
      });
      this.host.appendChild(label); this.labels.set(e.id, label);
    }
    for (const c of connections) {
      const a = this.endpoint(c.from), b = this.endpoint(c.to);
      const tier = getConnectionTier(c);
      const style = TIER_STYLE[tier];
      const group = new THREE.Group();
      const points = buildCableWaypoints(c, a, b);
      const route = new THREE.CurvePath<THREE.Vector3>();
      for (let i = 1; i < points.length; i++) {
        if (points[i - 1].distanceTo(points[i]) < .015) continue;
        route.add(new THREE.LineCurve3(points[i - 1], points[i]));
        group.add(lineBetween(points[i - 1], points[i], style.radius, style.aura));
      }
      const routeLen = route.getLength();
      const pulseOffsets = routeLen < 1.3 ? [0] : routeLen < 3.6 ? [0, 0.5] : [0, 0.33, 0.66];
      const pulseLen = Math.min(0.20, Math.max(0.08, routeLen * 0.14));
      const pulseRad = style.radius * 1.18;
      for (const offset of pulseOffsets) {
        // Tapered directional pulse capsule oriented along the cable tangent
        const pulse = new THREE.Mesh(
          new THREE.CylinderGeometry(pulseRad * 0.45, pulseRad * 1.15, pulseLen, 8),
          new THREE.MeshBasicMaterial({ color: style.pulse, transparent: true, opacity: 0.96 })
        );
        const pulseHalo = new THREE.Mesh(
          new THREE.CylinderGeometry(pulseRad * 1.1, pulseRad * 1.65, pulseLen * 1.12, 8),
          new THREE.MeshBasicMaterial({
            color: style.pulseHalo,
            transparent: true,
            opacity: 0.36,
            blending: THREE.AdditiveBlending,
            depthWrite: false
          })
        );
        pulse.add(pulseHalo);
        pulse.userData.pulse = true;
        pulse.userData.route = route;
        pulse.userData.offset = offset;
        group.add(pulse);
      }
      const gap = new THREE.Mesh(new THREE.TorusGeometry(.042, .009, 6, 14), new THREE.MeshBasicMaterial({ color: C.open, transparent: true, opacity: 0.85, side: THREE.DoubleSide }));
      if (route.curves.length > 0) gap.position.copy(route.getPoint(.45));
      gap.userData.gap = true; group.add(gap);
      this.paths.set(c.id, group); this.scene.add(group);
    }
    this.renderer.domElement.addEventListener('pointerdown', e => this.pointerDown.set(e.clientX, e.clientY));
    this.renderer.domElement.addEventListener('click', e => this.click(e));
    new ResizeObserver(() => this.resize()).observe(host);
    this.resize(); this.resetCamera(); this.animate(0);
  }
  private endpoint(id: string) {
    const object = this.objects.get(id)!;
    if (id === 'reeferUnit' || id === 'reeferUnitA' || id === 'reeferUnitB') {
      // The supply plugs into the inlet on the refrigeration end of the container.
      const placement = vesselLayout[id], direction = placement.rotation === Math.PI ? -1 : 1;
      return object.position.clone().add(new THREE.Vector3(direction * (placement.size[0] / 2 + .05), .28, 0));
    }
    if (id === 'prop') {
      return object.position.clone();
    }
    if (id === 'crane') {
      // Anchor cable at the crane deck pedestal base rather than mid-air on the boom
      return object.position.clone().add(new THREE.Vector3(0, 0.22, 0));
    }
    const point = object.position.clone(); point.y += object.userData.height * (id === 'motor' ? .4464 : .5); return point;
  }
  private resize() {
    const w = this.host.clientWidth, h = this.host.clientHeight; if (!w || !h) return;
    this.camera.aspect = w / h; this.camera.updateProjectionMatrix(); this.renderer.setSize(w, h);
  }
  private click(event: MouseEvent) {
    if (this.pointerDown.distanceTo(new THREE.Vector2(event.clientX, event.clientY)) > 5) return;
    const rect = this.renderer.domElement.getBoundingClientRect();
    this.pointer.set((event.clientX - rect.left) / rect.width * 2 - 1, -(event.clientY - rect.top) / rect.height * 2 + 1);
    this.ray.setFromCamera(this.pointer, this.camera);
    const hit = this.ray.intersectObjects([...this.objects.values()], true).find(h => h.object.userData.eqId);
    if (hit) this.onSelect(hit.object.userData.eqId as string);
  }
  private isConnectionHighlighted(c: Connection): boolean {
    const tier = getConnectionTier(c);
    if (this.flowFilter === 'focus') return this.focusedEdges.has(c.id);
    if (this.flowFilter === 'hv') return tier === 'hv' || tier === 'mechanical';
    if (this.flowFilter === 'lv') return tier === 'lv';
    if (this.flowFilter === 'consumer') return tier === 'consumer';
    if (this.flowFilter === 'emergency') return tier === 'emergency';
    return true;
  }
  private isEquipmentInFilter(id: string): boolean {
    if (id === this.selection) return true;
    const tier = getEquipmentTier(id);
    if (this.flowFilter === 'focus') return this.focusedNodes.has(id);
    if (this.flowFilter === 'hv') return tier === 'hv' || tier === 'mechanical';
    if (this.flowFilter === 'lv') return tier === 'lv';
    if (this.flowFilter === 'consumer') return tier === 'consumer';
    if (this.flowFilter === 'emergency') return tier === 'emergency';
    return true;
  }
  update(state: SimState, live: Set<string>, selection: string) {
    this.state = state; this.live = live; this.selection = selection;
    const focused = computeFocusedCircuit(selection, state, live);
    this.focusedEdges = focused.edges;
    this.focusedNodes = focused.nodes;

    for (const [id, group] of this.objects) {
      const halo = group.children.find(o => o.userData.halo) as THREE.Mesh;
      const eqTier = getEquipmentTier(id);
      const tierColor = TIER_STYLE[eqTier].live;
      const inFocus = this.focusedNodes.has(id);
      const inFilter = this.isEquipmentInFilter(id);
      (halo.material as THREE.MeshBasicMaterial).color.setHex(
        id === selection ? C.selected : live.has(id) ? tierColor : C.dead
      );
      (halo.material as THREE.MeshBasicMaterial).opacity =
        id === selection ? .95 : !inFilter ? .08 : inFocus ? .55 : .28;
    }
    for (const rId of ['reeferUnit', 'reeferUnitA', 'reeferUnitB']) {
      const reeferOn = live.has(rId);
      this.objects.get(rId)?.traverse(o => {
        if (!o.userData.statusLight) return;
        const material = (o as THREE.Mesh).material as THREE.MeshStandardMaterial;
        material.color.setHex(reeferOn ? 0x41ff9a : 0x7a2a2a); material.emissive.setHex(reeferOn ? 0x1fb868 : 0x000000);
      });
    }
    for (const c of connections) {
      const status = connectionState(c, state, live);
      const tier = getConnectionTier(c);
      const style = TIER_STYLE[tier];
      const inFocus = this.focusedEdges.has(c.id);
      const inFilter = this.isConnectionHighlighted(c);
      const isLiveCable = status === 'live' && c.id !== 'shaft';
      const isOverviewBus = selection === 'busA' || selection === 'busB';

      for (const child of this.paths.get(c.id)!.children) {
        if (child.userData.pulse) {
          child.visible = isLiveCable && inFilter;
          const pulseScale = (this.flowFilter === 'all' && !inFocus) ? (isOverviewBus ? 0.88 : 0.65) : 1.08;
          child.scale.setScalar(pulseScale);
          continue;
        }
        if (child.userData.gap) {
          child.visible = status === 'open' && inFilter;
          continue;
        }
        const mat = (child as THREE.Mesh).material as THREE.MeshBasicMaterial;
        mat.color.setHex(
          c.id === 'shaft' ? style.live : status === 'live' ? style.live : status === 'open' ? C.open : C.dead
        );
        if (!inFilter) {
          mat.opacity = status === 'live' ? .07 : .03;
        } else if (c.id === 'shaft') {
          mat.opacity = inFocus ? .95 : .55;
        } else if (status === 'live') {
          mat.opacity = (this.flowFilter === 'all' && !inFocus) ? (isOverviewBus ? .78 : .34) : .98;
        } else if (status === 'open') {
          mat.opacity = inFocus ? .30 : .10;
        } else {
          mat.opacity = inFocus ? .34 : .12;
        }
        const aura = child.children.find(ch => ch.userData.glowAura) as THREE.Mesh | undefined;
        if (aura) {
          aura.visible = isLiveCable && inFilter && (inFocus || isOverviewBus || this.flowFilter !== 'all');
          if (aura.material instanceof THREE.MeshBasicMaterial) {
            aura.material.opacity = inFocus ? 0.32 : 0.14;
          }
        }
      }
    }
  }
  setShell(visible: boolean) { this.hull.visible = visible; }
  setLabels(visible: boolean) { this.labelsVisible = visible; }
  setFlowFilter(mode: FlowFilterMode) {
    this.flowFilter = mode;
    if (this.state) this.update(this.state, this.live, this.selection);
  }
  getFlowFilter(): FlowFilterMode { return this.flowFilter; }
  focusSelection() {
    const id = this.objects.has(this.selection) ? this.selection : connections.find(c => c.id === this.selection)?.to;
    if (!id) return;
    const bounds = new THREE.Box3().setFromObject(this.objects.get(id)!);
    const target = bounds.getCenter(new THREE.Vector3());
    const distance = Math.max(4.2, bounds.getSize(new THREE.Vector3()).length() * 2.5);
    const direction = this.camera.position.clone().sub(this.controls.target).normalize();
    this.controls.target.copy(target); this.camera.position.copy(target).addScaledVector(direction, distance); this.controls.update();
  }
  resetCamera() {
    const distance = Math.max(19.5 / (Math.max(.6, this.camera.aspect) * Math.tan(THREE.MathUtils.degToRad(21.5))), 29);
    this.controls.target.set(0, .5, 0);
    this.camera.position.copy(new THREE.Vector3(-.55, .70, 1).normalize().multiplyScalar(distance).add(this.controls.target));
    this.controls.update();
  }
  private updateLabels() {
    const occupied: { x: number; y: number; halfW: number }[] = [];
    const entries = [...this.labels.entries()].sort(([a], [b]) =>
      (Number(b === this.selection) * 4 + Number(this.focusedNodes.has(b)) * 2 + Number(this.live.has(b))) -
      (Number(a === this.selection) * 4 + Number(this.focusedNodes.has(a)) * 2 + Number(this.live.has(a)))
    );
    for (const [id, label] of entries) {
      const inFilter = this.isEquipmentInFilter(id);
      if (!this.labelsVisible || !inFilter || (label.dataset.defaultVisible !== 'true' && id !== this.selection)) {
        label.style.display = 'none';
        continue;
      }
      const object = this.objects.get(id)!;
      const point = object.position.clone(); point.y += object.userData.height + .22; point.project(this.camera);
      const x = (point.x + 1) * this.host.clientWidth / 2, y = (-point.y + 1) * this.host.clientHeight / 2;
      const halfW = (label.textContent?.length || 8) * 2.65 + 7;
      const occluded = id !== this.selection && occupied.some(p => Math.abs(p.x - x) < (p.halfW + halfW + 4) && Math.abs(p.y - y) < 16);
      const visible = point.z < 1 && x > halfW && x < this.host.clientWidth - halfW && y > 38 && y < this.host.clientHeight - 12 && !occluded;
      label.style.display = visible ? '' : 'none';
      if (visible) occupied.push({ x, y, halfW });
      label.style.left = `${x}px`; label.style.top = `${y}px`;
      label.classList.toggle('is-live', this.live.has(id));
      label.classList.toggle('is-selected', id === this.selection);
    }
  }
  private animate = (time: number) => {
    requestAnimationFrame(this.animate);
    const dt = Math.min(.05, (time - this.lastTime) / 1000);
    this.phase += dt; this.lastTime = time;
    if (!this.host.clientWidth || !this.host.clientHeight) return;
    // The reefer's condenser fan turns only while the container is supplied.
    for (const rId of ['reeferUnit', 'reeferUnitA', 'reeferUnitB']) {
      if (this.live.has(rId)) {
        this.objects.get(rId)?.traverse(o => { if (o.userData.spin) o.rotation.x += dt * 9; });
      }
    }
    // Main propulsion propeller spins when propulsion is energized, or continuously in inspect mode
    const isPropulsionActive = this.live.has('prop') || this.live.has('motor');
    const isInspectingPropeller = this.selection === 'prop';
    if (isPropulsionActive || isInspectingPropeller) {
      propellerAssembly.updateRotation(dt, isPropulsionActive ? 45 : 18);
    }
    // Update explosion lerp interpolation smoothly every frame
    propellerAssembly.updateExplosion(dt);
    // Update transformer cooling fans when energized, or during inspection
    const isTxActive = ['txA', 'txB', 'txReeferA', 'txReeferB', 'txConA', 'txConB'].some(id => this.live.has(id));
    const isInspectingTx = ['txA', 'txB', 'txReeferA', 'txReeferB', 'txConA', 'txConB'].includes(this.selection);
    if (isTxActive || isInspectingTx) {
      transformerAssembly.updateRotation(dt, isTxActive ? 1200 : 600);
    }
    // Update transformer explosion lerp interpolation smoothly every frame
    transformerAssembly.updateExplosion(dt);
    // Update drive cooling pump when energized, or during inspection
    const isDriveActive = this.live.has('drive');
    const isInspectingDrive = this.selection === 'drive';
    if (isDriveActive || isInspectingDrive) {
      driveAssembly.updateRotation(dt, isDriveActive ? 1800 : 900);
    }
    // Update drive explosion lerp interpolation smoothly every frame
    driveAssembly.updateExplosion(dt);
    // Update electric propulsion motor rotor and cooling fan when energized, or during inspection
    const isMotorActive = this.live.has('motor') || this.live.has('prop');
    const isInspectingMotor = this.selection === 'motor';
    if (isMotorActive || isInspectingMotor) {
      motorAssembly.updateRotation(dt, isMotorActive ? 250 : 80);
    }
    // Update motor explosion lerp interpolation smoothly every frame
    motorAssembly.updateExplosion(dt);
    // Update steering gear kinematics (rudder oscillation and hydraulic ram pistons)
    const isSteeringActive = this.live.has('steering') || this.live.has('eSteer');
    const isInspectingSteering = this.selection === 'steering' || this.selection === 'eSteer';
    if (isSteeringActive || isInspectingSteering) {
      steeringAssembly.updateKinematics(dt, isSteeringActive ? 1.0 : 0.4);
    }
    // Update steering gear explosion lerp interpolation smoothly every frame
    steeringAssembly.updateExplosion(dt);
    // Update reefer distribution panel explosion lerp smoothly every frame
    reeferAssembly.updateExplosion(dt);
    // Update pumps rotation and explosion
    pumpAssembly.updateRotation(dt, this.live);
    pumpAssembly.updateExplosion(dt);
    // Kinematic updates for 8 consumer assemblies
    esbCubicleAssembly.updateKinematics(dt, 0, this.live.has('eBus'));
    batterySystemAssembly.updateKinematics(dt, 0, this.live.has('eRadio'));
    airCompressorAssembly.updateKinematics(dt, 1200, this.live.has('airCompressor'));
    ventFanAssembly.updateKinematics(dt, 1750, this.live.has('ventFan'));
    ballastOwsAssembly.updateKinematics(dt, 1800, this.live.has('ballast'));
    galleyBoardAssembly.updateKinematics(dt, 0, this.live.has('galley440'));
    shorePowerAssembly.updateKinematics(dt, 8, this.live.has('shore'));
    bridgeNavComAssembly.updateKinematics(dt, 24, this.live.has('nav'));

    // Explosion updates for 8 consumer assemblies
    esbCubicleAssembly.updateExplosion(dt);
    batterySystemAssembly.updateExplosion(dt);
    airCompressorAssembly.updateExplosion(dt);
    ventFanAssembly.updateExplosion(dt);
    ballastOwsAssembly.updateExplosion(dt);
    galleyBoardAssembly.updateExplosion(dt);
    shorePowerAssembly.updateExplosion(dt);
    bridgeNavComAssembly.updateExplosion(dt);

    // Bow thruster spins when energized
    if (this.live.has('bow')) {
      this.objects.get('bow')?.traverse(o => { if (o.userData.spinImpeller) o.rotation.x += dt * 18; });
    }
    this.controls.update(); this.updateLabels();
    if (this.state) for (const c of connections) {
      if (connectionState(c, this.state, this.live) !== 'live') continue;
      for (const child of this.paths.get(c.id)!.children) if (child.userData.pulse && child.visible) {
        const route = child.userData.route as THREE.CurvePath<THREE.Vector3>;
        const offset = child.userData.offset || 0;
        const t = (this.phase * .38 + offset) % 1;
        child.position.copy(route.getPoint(t));
        const tangent = route.getTangent(t);
        if (tangent && tangent.lengthSq() > 0.0001) {
          child.quaternion.setFromUnitVectors(UP_AXIS, tangent);
        }
      }
    }
    this.renderer.render(this.scene, this.camera);
  };
}

export class ExplodedView {
  private renderer: THREE.WebGLRenderer;
  private scene = new THREE.Scene();
  private camera = new THREE.PerspectiveCamera(43, 1, .1, 100);
  private controls: OrbitControls;
  private ray = new THREE.Raycaster();
  private pointer = new THREE.Vector2();
  private instance?: ModelInstance;
  private exploded = false;
  private selectedPart?: string;
  private focused = false;
  private partLabel = document.createElement('div');
  private pointerStart = new THREE.Vector2();
  onPart: (id: string) => void = () => {};

  constructor(private host: HTMLElement) {
    this.renderer = renderer(host); this.scene.background = new THREE.Color(BG.exploded); lights(this.scene);
    this.camera.position.set(5.6, 3.5, 7.8);
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true; this.controls.minDistance = .5; this.controls.maxDistance = 90;
    this.partLabel.className='equipment-part-label';this.partLabel.hidden=true;host.appendChild(this.partLabel);
    this.renderer.domElement.addEventListener('pointerdown',e=>this.pointerStart.set(e.clientX,e.clientY));
    this.renderer.domElement.addEventListener('click', e => this.click(e));
    new ResizeObserver(() => this.resize()).observe(host); this.resize(); this.animate();
  }
  element() { return this.host; }
  private resize() {
    const w = this.host.clientWidth, h = this.host.clientHeight; if (!w || !h) return;
    this.camera.aspect = w / h; this.camera.updateProjectionMatrix(); this.renderer.setSize(w, h);
    if(this.focused)this.focusPart();else this.fitModelView();
  }
  setModel(type?: ModelType) {
    if (this.instance) {
      this.scene.remove(this.instance.group);
      this.instance.group.traverse(o => {
        if (o instanceof THREE.Mesh || o instanceof THREE.Line) {
          o.geometry.dispose(); const materials = Array.isArray(o.material) ? o.material : [o.material]; materials.forEach(m => m.dispose());
        }
      });
    }
    this.instance = type ? createModel(type) : undefined; this.exploded = false; this.selectedPart = undefined;
    this.partLabel.hidden=true;
    if (this.instance) this.scene.add(this.instance.group);
    this.fitModelView();
  }
  private fitModelView() {
    if (!this.instance) return;
    this.focused=false;
    const bounds = new THREE.Box3();
    const boxes:THREE.Box3[]=[];
    for (const part of this.instance.parts) {
      part.group.visible=true;
      const box = new THREE.Box3().setFromObject(part.group);
      const target = this.exploded ? part.exploded : part.base;
      box.translate(target.clone().sub(part.group.position)); bounds.union(box);boxes.push(box);
    }
    this.frameBounds(bounds,boxes);
  }
  private frameBounds(bounds: THREE.Box3,boxes:THREE.Box3[]=[bounds]) {
    const center = bounds.getCenter(new THREE.Vector3());
    const direction = new THREE.Vector3(1,.6,1.6).normalize();
    const right = new THREE.Vector3().crossVectors(new THREE.Vector3(0,1,0),direction).normalize();
    const up = new THREE.Vector3().crossVectors(direction,right);
    const tan = Math.tan(THREE.MathUtils.degToRad(this.camera.fov/2));
    let distance = 1;
    for(const box of boxes)for(const x of [box.min.x,box.max.x])for(const y of [box.min.y,box.max.y])for(const z of [box.min.z,box.max.z]){
      const corner=new THREE.Vector3(x,y,z).sub(center),depth=corner.dot(direction);
      distance=Math.max(distance,depth+Math.abs(corner.dot(right))/(tan*this.camera.aspect),depth+Math.abs(corner.dot(up))/tan);
    }
    distance*=1.1;
    this.controls.target.copy(center);
    this.camera.position.copy(center).addScaledVector(direction,distance);
    this.controls.update();
  }
  resetView() { this.fitModelView(); }
  focusPart() {
    const part=this.instance?.parts.find(p=>p.spec.id===this.selectedPart);
    if(!part)return;
    this.focused=true;
    // Snap to the chosen assembly state before fitting a small component.
    for(const p of this.instance!.parts){p.group.position.copy(this.exploded?p.exploded:p.base);p.group.visible=p===part;}
    this.frameBounds(new THREE.Box3().setFromObject(part.group));
  }
  setExploded(value: boolean) { this.exploded = value; this.fitModelView(); }
  isExploded() { return this.exploded; }
  setPart(id?: string) {
    this.selectedPart = id;
    const index=this.instance?.parts.findIndex(p=>p.spec.id===id)??-1;
    this.partLabel.hidden=index<0;
    if(index>=0)this.partLabel.textContent=`${String(index+1).padStart(2,'0')} · ${this.instance!.parts[index].spec.name}`;
    if(this.focused&&index>=0)this.focusPart();
  }
  private click(event: MouseEvent) {
    if (!this.instance) return;
    if(this.pointerStart.distanceTo(new THREE.Vector2(event.clientX,event.clientY))>5)return;
    const rect = this.renderer.domElement.getBoundingClientRect();
    this.pointer.set((event.clientX - rect.left) / rect.width * 2 - 1, -(event.clientY - rect.top) / rect.height * 2 + 1);
    this.ray.setFromCamera(this.pointer, this.camera);
    const hit = this.ray.intersectObject(this.instance.group, true).find(h => h.object.userData.partId && (!this.focused || h.object.userData.partId===this.selectedPart));
    const id = hit?.object.userData.partId as string | undefined;
    if (id) { this.setPart(id); this.onPart(id); }
  }
  private animate = () => {
    requestAnimationFrame(this.animate);
    if (!this.host.isConnected || !this.host.clientWidth || !this.host.clientHeight) return;
    this.controls.update();
    if (this.instance) for (const part of this.instance.parts) {
      part.group.position.lerp(this.exploded ? part.exploded : part.base, .13);
      part.group.traverse(o => { if (o instanceof THREE.Mesh) (o.material as THREE.MeshStandardMaterial).emissive.setHex(part.spec.id === this.selectedPart ? 0x365443 : 0x000000); });
    }
    this.renderer.render(this.scene, this.camera);
  };
}
