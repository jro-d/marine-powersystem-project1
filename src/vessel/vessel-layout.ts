import GA from './general-arrangement.json';

/** Display dimensions, in consistent scene units (approximately four metres each).
 * These are illustrative proportions, not a dimensional ship design.
 * Coordinates: X = stern to bow, Y = height, Z = port to starboard.
 *
 * Positions, decks, bulkheads, cargo bays and equipment slots come from general-arrangement.json, which the
 * Blender hull generator (scripts/blender/hull_lib.py) reads as well. Edit that file, not the constants here.
 */
export interface VesselPlacement {
  position: [number, number, number]; // Centre in plan, bottom of equipment in height.
  size: [number, number, number]; // Maximum assembled width, height, depth.
  rotation?: number;
  // 'cargo' equipment is a container that sits inside a stack of the cargo bays.
  space: 'hull' | 'house' | 'deck' | 'external' | 'cargo';
}

/** The general-arrangement spec shared with the Blender hull generator. */
export const GENERAL_ARRANGEMENT = GA;

type Table = [number, number][];

export const SHIP = {
  mainDeck: GA.hull.mainDeck,
  keel: GA.hull.keel,
  waterline: GA.hull.waterline,
  house: { minX: GA.house.minX, maxX: GA.house.maxX, halfWidth: GA.house.halfWidth, roof: GA.house.roofLimit },
  // Plan outline of the main deck: x (stern to bow) and half-beam. The bow is flared and raked.
  stations: [
    [-19.7, 1.90], [-17.4, 1.90], [-16.2, 2.93], [-13.5, 3.56], [-9, 3.85],
    [9.5, 3.85], [11.2, 3.85], [17.2, 3.85],
    [18.5, 3.54], [20.0, 3.01], [21.2, 2.36], [22.2, 1.70], [23.0, 1.21], [23.8, 0.67], [24.4, 0.25], [24.7, 0.05]
  ] as Table,
  // Half-width of the flat of the bottom. It stays wide under the bow thruster, then closes into the forefoot.
  bottom: [
    [-17.4, 0.58], [-16.2, 1.67], [-13.5, 2.53], [-9, 2.88],
    [9.5, 2.88], [11.2, 2.88], [17.2, 2.88],
    [18.0, 2.76], [20.2, 2.13], [21.5, 1.38], [22.5, 0.58], [23.3, 0.09]
  ] as Table,
  // Keel line: flat for most of the length, rising under the stern run and into the forefoot.
  keelLine: [[-17.4, -2.15], [-16.6, -3.15], [20.8, -3.15], [22.6, -2.45], [23.5, -2.0]] as Table
};

export const CARGO = {
  bays: GA.cargo.bays, length: GA.cargo.length, width: GA.cargo.width, height: GA.cargo.height,
  rowPitch: GA.cargo.rowPitch, rows: GA.cargo.rows
};

/** Display scale applied to an equipment model's slot size (0.75 by default, see equipmentScale in the spec). */
export function equipmentScale(id: string): number {
  return (GA.equipmentScale.overrides as Record<string, number>)[id] ?? GA.equipmentScale.default;
}

function lerpTable(table: Table, x: number): number {
  if (x <= table[0][0]) return table[0][1];
  for (let i = 1; i < table.length; i++) {
    const [x1, y1] = table[i], [x0, y0] = table[i - 1];
    if (x <= x1) return y0 + (y1 - y0) * (x - x0) / (x1 - x0);
  }
  return table[table.length - 1][1];
}
const clamp01 = (v: number) => Math.max(0, Math.min(1, v));
const smooth = (a: number, b: number, v: number) => { const t = clamp01((v - a) / (b - a)); return t * t * (3 - 2 * t); };

export const hullStart = SHIP.stations[0][0];
export const hullEnd = SHIP.stations[SHIP.stations.length - 1][0];
/** Height of the keel line at x. */
export function keelAt(x: number): number { return lerpTable(SHIP.keelLine, x); }

/** Half-beam of the hull at plan position x and height. Returns 0 outside the hull or below the local keel line. */
export function halfBeamAt(x: number, height = SHIP.mainDeck): number {
  if (x < hullStart || x > hullEnd) return 0;
  const keel = keelAt(x);
  if (height < keel - 1e-6) return 0;
  const t = clamp01((height - keel) / (SHIP.mainDeck - keel));
  const deckWidth = lerpTable(SHIP.stations, x);
  const flat = Math.min(deckWidth, lerpTable(SHIP.bottom, x));
  // Midships the sides rise with a rounded bilge; towards the bow they flare outwards instead.
  const w = smooth(9, 14.5, x);
  const shape = (1 - Math.pow(1 - t, 2.4)) * (1 - w) + Math.pow(t, 1.35) * w;
  return flat + (deckWidth - flat) * shape;
}

type SpecEquipment = { position: number[]; size: number[]; rotationDeg?: number; space: string };

export const vesselLayout: Record<string, VesselPlacement> = Object.fromEntries(
  Object.entries(GA.equipment as Record<string, SpecEquipment>).map(([id, e]) => {
    const placement: VesselPlacement = {
      position: [e.position[0], e.position[1], e.position[2]],
      size: [e.size[0], e.size[1], e.size[2]],
      space: e.space as VesselPlacement['space']
    };
    if (e.rotationDeg !== undefined) placement.rotation = e.rotationDeg * Math.PI / 180;
    return [id, placement];
  })
);

// ============================================================================
// PHASE 3: SOLAS BLACKOUT RECOVERY 5-STAGE SEQUENTIAL WATERFALL
// ============================================================================
export interface SolasWaterfallStage {
  stageNumber: 1 | 2 | 3 | 4 | 5;
  id: string;
  timeWindowLabel: string;
  startSec: number;
  endSec: number;
  shortTitle: string;
  description: string;
  sourcesToStart: string[];
  breakersToClose: string[];
}

export interface SolasWaterfallStatus {
  active: boolean;
  completed: boolean;
  elapsedSec: number;
  totalDurationSec: number;
  progressPercent: number;
  currentStageIndex: number; // 0..4 (-1 when inactive)
  currentStage: SolasWaterfallStage | null;
  timeScale: number; // Default 2.5x so users can observe the 50s SOLAS sequence smoothly, or toggle 1x/5x
}

/**
 * All main 6.6 kV and 440 V load feeder breakers that must open upon blackout
 * so loads NEVER energize simultaneously upon main breaker closure.
 */
export const MAIN_BLACKOUT_SHED_BREAKERS: string[] = [
  'propFeed',
  'bowFeed',
  'txAFeed',
  'txAOut',
  'txBFeed',
  'txBOut',
  'reeferAFeed',
  'reeferBFeed',
  'conAAcb',
  'conBAcb',
  'fire1Feed',
  'fire2Feed',
  'cooling1Feed',
  'cooling2Feed',
  'craneFeed',
  'ballastFeed',
  'bilgeFeed',
  'galley440Feed',
  'navFeed',
  'lightAFeed',
  'galleySmallFeed'
];

export const SOLAS_WATERFALL_STAGES: SolasWaterfallStage[] = [
  {
    stageNumber: 1,
    id: 'stage-1-esb',
    timeWindowLabel: 'T = 0s – 10s',
    startSec: 0,
    endSec: 10,
    shortTitle: 'ESB & Emergency DG',
    description: 'T = 0s–10s: Bridge Nav & GMDSS bridged by 24 V DC UPS (0 ms break) → Emergency DG auto-starts → ESB online (Steering, NavCom, Fire Pump)',
    sourcesToStart: ['eg'],
    breakersToClose: ['egBreaker', 'navEmFeed', 'eSteerFeed', 'eLightFeed', 'eRadioFeed', 'eFireFeed']
  },
  {
    stageNumber: 2,
    id: 'stage-2-aux1',
    timeWindowLabel: 'T = 10s – 20s',
    startSec: 10,
    endSec: 20,
    shortTitle: 'Main DGs & Stage 1 Aux',
    description: 'T = 10s–20s: Primary DGs (DG 1 & DG 2) auto-sync → 6.6 kV Bus A & B → TX A & TX B → Stage 1 Auxiliaries (SW Cooling Pumps 1 & 2)',
    sourcesToStart: ['dg1', 'dg2'],
    breakersToClose: ['gb1', 'gb2', 'tie', 'txAFeed', 'txAOut', 'txBFeed', 'txBOut', 'cooling1Feed', 'cooling2Feed']
  },
  {
    stageNumber: 3,
    id: 'stage-3-aux2',
    timeWindowLabel: 'T = 20s – 30s',
    startSec: 20,
    endSec: 30,
    shortTitle: 'Stage 2 Control & Domestic',
    description: 'T = 20s–30s: Stage 2 Auxiliaries: Close Control Transformers (TX CON A & B), 220 V Bus Tie, Nav Bridge, Lighting & Small Appliances',
    sourcesToStart: [],
    breakersToClose: ['conAAcb', 'conBAcb', 'consumerTie', 'navFeed', 'lightAFeed', 'galleySmallFeed']
  },
  {
    stageNumber: 4,
    id: 'stage-4-ess',
    timeWindowLabel: 'T = 30s – 45s',
    startSec: 30,
    endSec: 45,
    shortTitle: 'Stage 3 Essential Loads',
    description: 'T = 30s–45s: Stage 3 Essential Service Loads (Fire Pumps 1 & 2, Ballast & Bilge Pumps)',
    sourcesToStart: [],
    breakersToClose: ['fire1Feed', 'fire2Feed', 'ballastFeed', 'bilgeFeed']
  },
  {
    stageNumber: 5,
    id: 'stage-5-heavy',
    timeWindowLabel: 'T > 45s',
    startSec: 45,
    endSec: 55,
    shortTitle: 'Heavy & Non-Essential Loads',
    description: 'T > 45s: Non-Essential & Heavy Motors (Reefer Transformers A & B, 440 V Galley Primary Board, Deck Crane, Propulsion VFD & Bow Thruster)',
    sourcesToStart: [],
    breakersToClose: ['reeferAFeed', 'reeferBFeed', 'craneFeed', 'galley440Feed', 'bowFeed', 'propFeed']
  }
];

export function createInitialWaterfallStatus(): SolasWaterfallStatus {
  return {
    active: false,
    completed: false,
    elapsedSec: 0,
    totalDurationSec: 55,
    progressPercent: 0,
    currentStageIndex: -1,
    currentStage: null,
    timeScale: 2.5
  };
}

