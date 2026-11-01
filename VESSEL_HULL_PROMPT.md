# Gemini Argon Prompt — Procedural 3D Vessel Hull & Structural Shell Only

> [!IMPORTANT]
> **Do NOT attach `/marine-cad-digital-twin-builder` when sending this prompt to Gemini Argon.**
> This prompt is specifically engineered so Argon builds **only** the ship's hull, internal machinery deck flats, accommodation superstructure, bridge, funnel, stern skeg/rudder, and bow thruster tunnel opening inside a drop-in `createVesselHull(THREE)` function—with **zero** jagged waterline edges, **no** front collision bulkhead, and **no** exploded teardown UI.

---

## Copy & Paste This Prompt into Gemini Argon

```markdown
Build a standalone, single-file Three.js (`r160` ES module) 3D CAD viewer for a **Procedural Marine Container Ship Hull & Internal Structural Shell** in Low-Opacity Ghost X-Ray style.

### CRITICAL SCOPE RULES (READ CAREFULLY)
1. **HULL & STRUCTURE ONLY — NO EQUIPMENT OR TEARDOWN UI:**
   - Build **ONLY** the ship's structural hull, underwater body, boot-topping waterline band, topsides, bulwarks, internal horizontal machinery deck flats, aft accommodation superstructure, navigation bridge wings, funnel, stern skeg & rudder, bow thruster tunnel aperture, and weather-deck hatch coamings.
   - **DO NOT** build any internal electrical or mechanical equipment (no generators, switchboards, transformers, motors, or cables—those already exist in our main simulator and will be placed inside this hull).
   - **DO NOT** build a forward collision bulkhead in the bow (keep the forward bow thruster space completely open and unobstructed).
   - **DO NOT** add exploded-view sliders, floating 3D callout labels, or telemetry graphs. Only include a minimal top-right floating control pill with:
     * `Hull Opacity` slider (`5%` to `85%`, default `22%`)
     * `Ghost X-Ray Mode` vs `Solid CAD Mode` toggle button
     * `Show Internal Deck Flats` toggle button
     * `Reset Camera` button
2. **DROP-IN MODULE ARCHITECTURE (`createVesselHull(THREE)`):**
   - Encapsulate all ship geometry creation inside a single, clean, self-contained factory function `function createVesselHull(THREE)` that returns a `THREE.Group` positioned at world origin `(0, 0, 0)`. We will copy `createVesselHull(THREE)` directly into our TypeScript simulator (`src/vessel/vessel.ts`).

---

### EXACT COORDINATE SYSTEM & HULL LINES (MANDATORY LOCK)
Our simulator places 35 pieces of marine machinery and cable routes at exact world coordinates where:
- **X-axis** = Stern (`-19.7`) to Bow (`+24.7`)
- **Y-axis** = Vertical elevation (`keel = -3.15`, `waterline = -1.25`, `mainDeck = +0.90`)
- **Z-axis** = Port (`-Z`) to Starboard (`+Z`), symmetrical about `Z = 0`

Use this exact parametric hull definition so every existing machine in our app sits on its exact deck flat:

```js
const SHIP = {
  mainDeck: 0.90,
  keel: -3.15,
  waterline: -1.25,
  house: { minX: -13.5, maxX: -7.3, halfWidth: 2.65, roof: 4.70 },
  // Plan outline of the main deck: [x, halfBeam]
  stations: [
    [-19.7, 1.90], [-17.4, 1.90], [-16.2, 2.93], [-13.5, 3.56], [-9.0, 3.85],
    [9.5, 3.85], [11.2, 3.85], [17.2, 3.85],
    [18.5, 3.54], [20.0, 3.01], [21.2, 2.36], [22.2, 1.70], [23.0, 1.21], [23.8, 0.67], [24.4, 0.25], [24.7, 0.02]
  ],
  // Half-width of the flat of bottom: [x, halfFlat]
  bottom: [
    [-17.4, 0.58], [-16.2, 1.67], [-13.5, 2.53], [-9.0, 2.88],
    [9.5, 2.88], [11.2, 2.88], [17.2, 2.88],
    [18.0, 2.76], [20.2, 2.13], [21.5, 1.38], [22.5, 0.58], [23.3, 0.08]
  ],
  // Keel elevation profile: [x, keelY]
  keelLine: [
    [-19.7, -0.40], [-17.4, -2.15], [-16.6, -3.15], [20.8, -3.15], [22.6, -2.45], [23.8, -1.80], [24.7, 0.90]
  ]
};
```

---

### SOLVING THE JAGGED WATERLINE BUG (TRUE HORIZONTAL WATERPLANE SLICING)
In our previous `.glb` model, assigning red/white/blue materials to quad faces created ugly saw-tooth stair-stepping along the curved bow and stern.
**You must eliminate this completely by constructing the outer hull shell as 3 horizontally sliced parametric lofted bands along exact `Y` elevations** (with high longitudinal & vertical station resolution, e.g. `160` X-stations × `24` Y-slices per band):
1. **Lower Underwater Anti-Fouling Hull (`y` from `keelAt(x)` up to `y = -1.35`):**
   - Soft muted terracotta/red-oxide marine anti-fouling tone (`#b86b64`, `roughness: 0.45`, `metalness: 0.15`, `transparent: true`, `opacity: 0.22`, `depthWrite: false`, `side: THREE.DoubleSide`).
   - Include a smooth hydrodynamic **bulbous bow** protruding forward around `x = 23.0 to 24.5, y = -2.85 to -1.55` and a sculpted **stern skeg / shaft bossing** leading to the propeller aperture at `(-17.38, -2.22, 0)`.
2. **Crisp Horizontal Boot-Topping Waterline Stripe (`y = -1.35` to `y = -1.15`):**
   - Because its bottom edge is strictly `y = -1.35` and its top edge is strictly `y = -1.15` at every X station, this white/ice-slate band (`#f8fafc`, `opacity: 0.38`) will be **razor-sharp and 100% horizontal** from stem to stern with zero jagged steps!
3. **Upper Topsides Hull Shell (`y = -1.15` up to `y = +0.90` Main Deck, plus raked bow bulwark flaring smoothly up to `y = +1.45` forward of `x = 18.0`):**
   - Soft cool marine slate-blue (`#6c92a6`, `roughness: 0.42`, `metalness: 0.18`, `transparent: true`, `opacity: 0.22`, `depthWrite: false`, `side: THREE.DoubleSide`).
   - Add a crisp 3D gunwale/sheer rail tube or `LineSegments` feature line along the top deck edge and waterline seams so the ship's silhouette reads like a precision naval architecture CAD model.

---

### INTERNAL HORIZONTAL MACHINERY DECK FLATS & COMPARTMENT PLATFORMS
Inside the hull, build clean horizontal translucent structural steel deck plates (`#94a3b8`, `opacity: 0.24`, `depthWrite: false`) with crisp perimeter edge lines (`#64748b`, `opacity: 0.45`) trimmed accurately to `halfBeamAt(x, y) - 0.08` so they never poke through the outer hull skin:
1. **Lower Propulsion & Tank-Top Flat (`y = -2.62`):**
   - Aft propulsion motor seating flat from `x = -16.2` to `x = -11.5`.
   - Forward bow-thruster flat from `x = 18.8` to `x = 21.4` with a circular / cylindrical athwartships **Bow Thruster Tunnel ring** (`radius = 0.55`, centered at `x = 20.1, y = -1.95`, running port-to-starboard from `-halfBeam` to `+halfBeam` with protective grille bars). **Do NOT place any vertical bulkhead wall in the bow!**
2. **Main Engine Room Machinery Flat (`y = -1.74`):**
   - Runs from `x = -12.5` to `x = +13.0` (supports the 4 main Diesel Generators at `x = -8.8, -5.9`, Main Transformers TX A/B at `x = -4.0`, Propulsion VFD at `x = -11.3`, and auxiliary pumps).
   - Include a central open machinery well / stairwell cutout where appropriate and clean longitudinal I-beam under-deck stiffener lines.
3. **Switchboard & Steering Mezzanine Flat (`y = -0.32`):**
   - Runs from `x = -16.8` to `x = -3.2` (supports Steering Gear at `x = -14.65`, 6.6 kV Main Switchboards Bus A/B at `x = -8.7, -6.8`, and 440 V Switchboards at `x = -4.25`), plus a forward mezzanine section from `x = 2.4` to `x = 4.8` for Reefer Transformers (`x = 3.5`).
4. **Main Weather Deck (`y = +0.90`):**
   - Continuous weather deck plate trimmed to the exact `SHIP.stations` plan outline (`x = -19.7` to `+24.7`), with raised hatch coaming pads (`#7b99a8`, `opacity: 0.28`) at the 4 cargo bay stations (`x = -4.4, -1.15, 2.1, 9.9`, width `Z = ±2.72`).
   - Clean, non-pixelated forecastle deck details forward (`x = 19.5` to `24.0`): two symmetrical anchor windlass pedestals and fairlead chocks in soft slate steel (`#738291`)—**no orange floor patches!**

---

### AFT ACCOMMODATION SUPERSTRUCTURE, BRIDGE & FUNNEL (`x = -13.5` to `-7.3`)
Build a crisp, multi-tier naval architectural accommodation block & navigation bridge in soft cool light grey (`#cbd5e1` / `#e2e8f0`, `opacity: 0.22`, `depthWrite: false`, with subtle `#64748b` architectural edge outlines) so internal equipment on the house decks remains clearly visible:
1. **Main House Tier 1 (`y = 0.90` to `2.35`, `x = -13.5` to `-7.3`, `z = ±2.65`):**
   - Houses the 440 V Galley and 220 V Sub-boards at `y = 1.02`.
2. **Emergency Switchboard & EDG Tier 2 (`y = 2.35` to `3.42`, `x = -13.3` to `-7.5`, `z = ±2.45`):**
   - Internal floor plate at `y = 2.33` supporting the Emergency Generator (`x = -12.0`) and Emergency Switchboard (`x = -9.7`).
3. **Navigation Bridge & Wheelhouse Tier 3 (`y = 3.42` to `4.70`, `x = -10.2` to `-7.3`, `z = ±2.65`, with cantilevered port/starboard Bridge Wings extending out to `z = ±3.85`):**
   - Internal bridge deck flat at `y = 3.43` (supports Bridge Nav console at `x = -8.5` and GMDSS Radio at `x = -8.8`).
   - Angled forward wheelhouse windows (`#38bdf8`, `opacity: 0.25`) with mullions and radar mast atop the compass deck (`y = 4.70` to `6.40`).
4. **Aft Engine Uptake & Funnel Casing (`x = -13.2` to `-10.8`, `y = 3.42` to `6.10`, `z = ±1.15`):**
   - Streamlined marine funnel casing with exhaust uptakes and louver grilles.
5. **Semi-Balanced Streamlined Rudder (`x = -18.8` to `-17.8`, `y = -2.95` to `-0.85`, `z = 0`):**
   - Hydrofoil rudder blade and rudder stock aligned below the steering gear (`x = -14.65` to `-18.2`).

---

### LIGHTING, CAMERA & SMOOTH WHEEL ZOOM
- Use the clean Light-Studio backdrop (`#f8fafc`) and white ocean-floor grid plane at `y = SHIP.keel - 0.05`.
- Disable built-in `OrbitControls` wheel zoom (`controls.enableZoom = false`) and attach the deterministic `4.2%` per-notch custom wheel zoom handler so scrolling never jumps inside the ship.
- Output the complete, standalone HTML file.
```
