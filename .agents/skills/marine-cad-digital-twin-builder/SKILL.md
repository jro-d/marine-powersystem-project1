---
name: marine-cad-digital-twin-builder
description: >-
  Comprehensive architectural, visual, and kinematic specification for building
  production-grade, standalone Three.js 3D interactive digital twins and exploded
  teardown simulators of marine engineering & high-voltage machinery (e.g., diesel
  generators, 6.6 kV switchboards & VCBs, transformers, drives, pumps, purifiers,
  and thrusters). Use whenever creating, updating, or integrating a 3D equipment
  teardown model.
version: 2.1.0
---

# Marine CAD Digital Twin Builder (`marine-cad-digital-twin-builder`)

## 1. Purpose & Scope
This skill defines the mandatory engineering, 3D procedural CAD modeling, kinematic math, PBR material palette, and UI/UX standards for building standalone, single-file Three.js interactive 3D digital twins of marine machinery and electrical equipment (e.g., 4-stroke medium-speed diesel generators, 6.6 kV Form 4b switchboards with withdrawable VCBs, transformers, VFD drives, purifiers, pumps, and thrusters).

Every model built with this skill must be delivered as a **single, self-contained HTML file (`< 1 MB`)** with zero external asset dependencies, running at 60 FPS with unlocked 360° camera orbiting and smooth, non-jumping wheel zoom.

---

## 2. Core Architectural Rules

### 2.1. Monolithic Sub-Assembly Hierarchy (Zero Floating or Disconnected Parts)
- **Physical Rigidity Rule:** Parts that move together in the real world (such as a withdrawable circuit breaker truck, a rotor shaft assembly, or a piston/wrist-pin crown) **must** be grouped inside a single parent `THREE.Group` (e.g., `breakerTruckGroup` or `crankshaftGroup`).
- **Single-Parameter Translation/Rotation:** When racking out a withdrawable carriage or rotating a shaft, **only** the master parent group's transform (`breakerTruckGroup.position.z` or `flywheelGroup.rotation.z`) may be animated. Never translate child sub-components independently during operational movement, and never leave components hovering on thin stalks disconnected from their structural frame.
- **Subsystem Hierarchy Inside Master Groups:** If a monolithic moving assembly contains multiple selectable subsystems (e.g., `vcbTruck`, `epoxyPoles`, and `vacuumInterrupters` all riding on the same withdrawable breaker carriage), attach those subsystem `THREE.Group`s as **direct children** of the master `breakerTruckGroup` so they automatically inherit its operational translation while still supporting individual explosion offsets and ghost-opacity isolation.

### 2.2. Floor-Safe, Unobstructed 3D Exploded Teardown
- **Strict Floor Clearance (`y >= 0`):** Every subsystem explosion vector `explodeVectors[key]` must keep all geometry strictly **above** the studio plinth surface (`y = 0.0`) at all explosion percentages (`0%` to `100%`).
  - **NEVER** assign negative vertical (`-Y`) explosion vectors to bottom-mounted subsystems (such as bedplates, sumps, lower cable compartments, or draw-out trucks). Instead, explode lower assemblies horizontally along `+Z`, `-Z`, or `±X`, or slightly upward (`+Y`).
- **Zero-Occlusion Separation:** Stagger explosion vectors across orthogonal and diagonal axes so that internal assemblies (e.g., vacuum interrupter bottles inside epoxy poles, or pistons/conrods inside cylinder liners) lift clear of their outer housings and every subsystem is 100% visible at `100%` explosion.
- **Dynamic Dashed Centerline Guides:** Render `THREE.LineDashedMaterial` (`color: 0xc25b2a`, `dashSize: 0.08`, `gapSize: 0.05`) connecting each exploded subsystem's home anchor to its displaced position whenever `explodeFactor > 0.02`.

### 2.3. Native-Color Ghost-Opacity Subsystem Isolation (`opacity: 0.14`)
- **Per-Material Cloned `origMaterial` & `ghostMaterial` (Never Use a Shared Grey/Yellow Ghost Material):**
  - During initialization (`prepareSubsystemMaterials()`), clone every mesh's material per subsystem into **both** `obj.userData.origMaterial` AND `obj.userData.ghostMaterial = origClone.clone()` with:
    ```js
    ghostClone.transparent = true;
    ghostClone.opacity = 0.14;
    ghostClone.depthWrite = false;
    ```
  - **Why this is mandatory:** Each ghosted (non-selected) part **must retain its own native material color** (e.g., marine engine green, maroon epoxy, copper busbars, pebble grey steel) at low opacity (`0.14`), matching the Diesel Generator and VCB teardown standard.
  - **Dynamic Status Flag Rule:** If any mesh changes color dynamically in the animation loop (such as mechanical `OPEN/CLOSED` or `CHARGED/DISCHARGED` indicator flags), **always** mutate `mesh.userData.origMaterial.color` and `mesh.userData.ghostMaterial.color` on that specific mesh—never mutate a shared material reference!
- **Translucent Context Preservation:** When a user selects a subsystem (via the left equipment sidebar, a floating 3D callout pill, or direct 3D raycaster click):
  - Keep **all** subsystems `visible = true`.
  - Render the selected subsystem using `obj.userData.origMaterial` at full opacity (`1.0`).
  - Render all non-selected subsystems using `obj.userData.ghostMaterial` (`transparent: true`, `opacity: 0.14`, `depthWrite: false`) so the user sees the highlighted assembly in its exact spatial and color context.
- **Cutaway / X-Ray Glass Mode:** Maintain a dedicated `matGlassCutaway` (`THREE.MeshPhysicalMaterial`, `opacity: 0.22`, `transmission: 0.84`, `depthWrite: false`) for outer housings (crankcase walls, cubicle side/door panels, cast epoxy pole barrels) so internal moving parts (crankshafts, vacuum contacts, bellows) can be inspected live during operation. Pre-compile both `matGlassCutaway` and `ghostMaterial` in `warmShaders()`.

---

## 3. High-Precision Procedural CAD Geometry Standards

### 3.1. Zero Z-Fighting & True Extruded Cutout Apertures
- **Never Overlap Coplanar Boxes for Windows or Doors:** Placing a solid glass/bezel `BoxGeometry` inside a solid door `BoxGeometry` of similar thickness causes severe black grain/flickering (Z-fighting) on the front or back face of the panel.
- **Mandatory Extruded Cutout Rule:** Whenever a door, bulkhead, or cover plate has a viewing window, louver grille, or instrument cutout:
  1. Construct the outer panel profile using `THREE.Shape`.
  2. Punch the exact window aperture using `THREE.Path` pushed into `shape.holes`.
  3. Extrude the perforated panel with `THREE.ExtrudeGeometry(shape, { depth, bevelEnabled: false })`.
  4. Frame the hole with a hollow picture-frame bezel (`bezelShape.holes.push(winHolePath)`) slightly thicker than the door (`depth + 0.010 m`), and mount the thinner glass pane (`depth * 0.35`) centered inside the open hole.

### 3.2. Mechanical & Electrical CAD Detailing Checklist
- **Structural Frames & Bedplates:** Use composite I-beams (top flange, web plate, bottom flange), machined top mounting rails, triangular `THREE.ExtrudeGeometry` web gusset stiffeners, and multi-layer elastomeric anti-vibration chocks with hex hold-down bolts.
- **Cast Housings & Cylinders:** Use scalloped profiles, cast vertical diaphragm ribs, horizontal cooling fins, perimeter hex bolt/nut arrays (`CylinderGeometry(r, r, h, 6)`), lifting lugs (`TorusGeometry`), and spring-loaded relief valves with perforated bronze flame traps.
- **Piping, Conduits & Helical Springs:** Use `THREE.CatmullRomCurve3` + `THREE.TubeGeometry` for curved high-pressure fuel lines, exhaust branches, armored HV conduits, and multi-turn helical operating springs.
- **High-Voltage & Switchgear Details:** Include double-bar copper busbars with phase sleeves (`L1` Coral Red, `L2` Warm Amber, `L3` Cobalt Blue), shedded DMC/porcelain standoff insulators, 18-finger silver-plated tulip contact clusters with garter springs, alumina ceramic vacuum bottles with CuCr contacts and accordion stainless bellows, toroidal CTs, and canvas-textured engraved operator nameplates (`#f4f6f8` white label strips with crisp slate typography).

---

## 4. Soft Industrial CAD Palette & Light-Studio Environment

### 4.1. Soft Cool-Slate & Muted Industrial Color Palette
Avoid harsh jet-blacks (`#000000` / `#0f172a`) or overly dark charcoals on 3D equipment. All machinery and enclosures must use soft, light-balanced industrial CAD tones that read clearly under studio lighting:
| Component Category | Hex Color | Material Properties |
| :--- | :--- | :--- |
| **Enclosure / Cabinet Panels** | `#c9d2db` | `roughness: 0.42`, `metalness: 0.16`, subtle powder bump |
| **Structural Trim / Upright Posts** | `#9aa8b6` | `roughness: 0.45`, `metalness: 0.22` |
| **Mobile Carriage / Mechanism Box** | `#8796a5` | `roughness: 0.44`, `metalness: 0.28` |
| **Bezels / Conduits / Base Plinths** | `#738291` | `roughness: 0.46`, `metalness: 0.26` (replaces dark charcoal) |
| **Marine Engine Sage Enamel** | `#3b6254` | `roughness: 0.44`, `metalness: 0.22`, cast iron bump |
| **Cast Epoxy Poles / Insulators** | `#a6534c` / `#b35d56` | Soft terracotta-rose / coral-brick, `roughness: 0.36` |
| **Alumina Ceramic / Label Strips** | `#f4f6f8` | Crisp off-white, `roughness: 0.18`, `metalness: 0.06` |
| **Silver Contacts / Polished Steel** | `#e6ecf2` / `#e2e8f0` | `roughness: 0.18–0.22`, `metalness: 0.82–0.88` |
| **Copper Busbars / Coils** | `#d47a42` | `roughness: 0.28`, `metalness: 0.80` |
| **Toroidal CTs / Bronze Fittings** | `#b8804c` / `#d8b25c` | Warm ochre resin / satin brass |

### 4.2. Unified Light Studio Plinth & Lighting (Diesel Generator Standard)
- **Scene Background:** `new THREE.Color(0xf1f3f6)` with radial CSS container backdrop (`#f8fafc` to `#eaedf1`).
- **Two-Tier Architectural Concrete Plinth (No Wireframe Grid):**
  - Upper slab (`#f8fafc`, `roughness: 0.85`, `metalness: 0.05`) at `y = -0.04 m` (top surface at `y = 0.0`).
  - Lower curb (`#e2e8f0`, `roughness: 0.80`, `metalness: 0.08`) slightly wider/deeper at `y = -0.09 m`.
  - Sized generously so withdrawn trucks or exploded parts remain over the plinth.
  - **Do not** add a wireframe `THREE.GridHelper` on top of the plinth; use a `ShadowMaterial({ opacity: 0.16 })` contact shadow plane at `y = 0.001 m`.
- **Studio Lighting Rig:**
  - `HemisphereLight(0xffffff, 0xdbe2ea, 1.20)`
  - `DirectionalLight(0xfffdf9, 1.35)` at `(8, 14, 7)` with `2048×2048` `PCFSoftShadowMap` (`bias: -0.0003`)
  - `DirectionalLight(0xe2e8f0, 0.80)` fill light at `(-8, 7, -6)`
  - `DirectionalLight(0xffffff, 0.50)` rim light at `(-4, 5, 9)`
  - `ACESFilmicToneMapping` at `toneMappingExposure = 1.12`.

---

## 5. Mathematical Kinematics, Smooth Wheel Zoom & Unlocked 360° Controls

### 5.1. Concentric Rotation & Right-Handed Coordinate Lock
- **No Coin-Tumble Rule:** Never animate `mesh.rotation.z` directly on a `CylinderGeometry` that already has `mesh.rotation.x = Math.PI / 2` applied to orient its axis. Always place the rotated cylinder inside a parent `THREE.Group` aligned with the shaft axis and rotate the parent group concentrically.
- **Exact Right-Handed Slider-Crank Lock:** In Three.js right-handed coordinates, rotating a crankpin at local `(0, R, 0)` around `+Z` by angle `theta` places the pin at:
  ```js
  const pinX = -R * Math.sin(theta);
  const pinY = crankY + R * Math.cos(theta);
  const wristY = pinY + Math.sqrt(L * L - pinX * pinX);
  const rodRotZ = Math.asin(pinX / L);
  ```
- **Realistic Mechanical Interlocks:** Enforce real-world IEC/SOLAS safety interlocks in the UI with a floating toast notification (e.g., block VCB racking while breaker contacts are `CLOSED`; block door closure while the truck is racked out on extension rails; require spring charging before closing).

### 5.2. Unrestricted 360° OrbitControls & Non-Jumping Custom Wheel Zoom
- **Full 360° Orbit:** Set `controls.minAzimuthAngle = -Infinity` and `controls.maxAzimuthAngle = Infinity` for full 360° horizontal rotation, and `controls.maxPolarAngle = Math.PI * 0.495` to prevent camera clipping below the studio floor.
- **Mandatory Custom Wheel Zoom Handler (Prevents 1-Scroll Jumping Inside Equipment):**
  - Three.js `r160+` `OrbitControls` divides `event.deltaY` by `(window.devicePixelRatio | 0)`, which evaluates to `0` (`Infinity` zoom jump) when browser zoom `< 100%` or jumps wildly on high-resolution scroll wheels.
  - Always set `controls.enableZoom = false;`, set `controls.minDistance` well outside the equipment's bounding radius (e.g., `1.65 m` for a cubicle or `3.5 m` for a large genset), and attach this deterministic `wheel` listener on `renderer.domElement`:
    ```js
    controls.enableZoom = false;
    controls.minDistance = 1.65;
    controls.maxDistance = 8.5;

    renderer.domElement.addEventListener('wheel', (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (e.deltaY === 0) return;
      isCameraTweening = false;
      const offset = new THREE.Vector3().subVectors(camera.position, controls.target);
      const dist = offset.length();
      if (dist < 0.001) return;
      const dir = e.deltaY > 0 ? 1 : -1;
      const nextDist = Math.max(controls.minDistance, Math.min(controls.maxDistance, dist * (1 + dir * 0.042)));
      offset.normalize().multiplyScalar(nextDist);
      camera.position.copy(controls.target).add(offset);
      controls.update();
    }, { passive: false });
    ```
- **Non-Locking Camera Presets:** Camera lerp transitions (`isCameraTweening = true`) may only run when triggered by a preset selection or `Reset view`, and must immediately release (`controls.addEventListener('start', () => { isCameraTweening = false; })`) the moment the user clicks, touches, or scrolls the viewport.

---

## 6. Left & Right Divided Callout Columns with Long SVG Leader Lines

### 6.1. Two-Column Flanking Callout Architecture (Zero Overlap)
- **Never place callout pills directly on top of the 3D equipment center** where they overlap each other and obscure the machinery.
- **Divide all callout labels into 2 groups (`side: 'left'` and `side: 'right'`)**:
  - **Left Column (`side: 'left'`):** Positioned along a vertical column to the **left** of the 3D equipment (`transform: translate(-100%, -50%)` so the right edge of the pill meets the leader line).
  - **Right Column (`side: 'right'`):** Positioned along a vertical column to the **right** of the 3D equipment (`transform: translate(0%, -50%)` so the left edge of the pill meets the leader line).
- **Vertical Anti-Overlap Solver (`resolveVerticalSpacing`):**
  - On every frame, project each visible callout's 3D anchor `(pos + explodeVector * explodeFactor + operationalOffset)` to screen coordinates `(anchorX, anchorY)`.
  - Sort left-side items by `anchorY` ascending and right-side items by `anchorY` ascending, and enforce a minimum vertical separation (`minGap = 48px`) with a forward pass (push down) and backward pass (pull up within `[92, window.innerHeight - 76]`).
- **Long SVG Leader Lines & Anchor Dots:**
  - Place a full-viewport `<svg class="w-full h-full absolute inset-0 pointer-events-none">` inside `#callouts-container` behind the HTML pills.
  - Ensure each column sits at least `80px–220px` clear of the projected 3D anchors (`baseLeftColX = centerX - colSpread`, `baseRightColX = centerX + colSpread`).
  - Draw a `<polyline>` leader line from the pill's inner edge `(colX, labelY)` out to the 3D part's projected `(anchorX, anchorY)` (using a horizontal segment + short angled segment if `|labelY - anchorY| >= 3`), terminated by a `<circle r="2.6">` dot at `(anchorX, anchorY)`. Highlight both the pill and leader line in `#ea580c` when its subsystem is isolated.

---

## 7. Consistent Minimal Light-Studio UI Layout & App Integration

### 7.1. Standalone Teardown UI Layout
1. **Left Equipment Sidebar (`260px–280px` fixed white panel):**
   - Top domain selector pill (`MV Switchgear` / `Power Generation`).
   - Equipment title & IEC/SOLAS specification subtitle.
   - `Equipment` header with `Show all` reset link.
   - 7 subsystem isolation buttons, each featuring a 2-letter mono badge (`CF`, `TR`, `EP`, `VI`, `SS`, `BB`, `CB`), title, concise spec subtitle, and `↗` indicator.
   - Bottom `2×2` live telemetry/nameplate strip with an animated green `ONLINE` / `ENERGIZED` status indicator.
2. **Top-Left Floating Pill Bar:**
   - `← Vessel view` / `← Topic library` link (`href="../index.html"` opening in the **same tab**) and `Kinematic & IEC proof` modal trigger button.
3. **Left & Right Divided Callout Pills + SVG Leader Lines:**
   - Flanking the 3D model with long leader lines and zero overlap.
4. **Right Floating Inspector Card (`320px–340px` translucent white card):**
   - Header bar with 6-dot Inspector icon, active BOM code badge (`ASSY-01`), Auto-Tour button, and telemetry drawer collapse button.
   - Active component title & engineering description.
   - `View` toggle pills (`Labels`, `Cutaway glass`, `Telemetry`).
   - Camera preset selector (`Overview`, `Front Fascia`, `Disconnect Tulips`, `Vacuum Cutaway`, `Shutters`).
   - Interactive operational sliders (`Racking` / `Throttle Load`, `Exploded teardown` with `0%` and `100%` quick buttons) and action buttons.
   - Collapsible live HTML5 2D telemetry canvases (e.g., P-V Indicator diagram or Contact Travel curve + 3-Phase 60 Hz AC waveforms).
   - Footer bar with `[ Reset view ] [ + ] [ − ]` buttons.

### 7.2. Integration into the Marine Power System Simulator App
1. **File Placement:** Place the standalone HTML file in `public/teardowns/<id>.html` (e.g., `public/teardowns/dg.html`, `public/teardowns/vcb.html`).
2. **Same-Tab Navigation:** In `src/main.ts`, the green **"Inspect Live 3D Teardown"** button (`#openLiveTeardown`) must navigate in the **same tab** (`window.location.href = activeTeardownUrl;`), never `window.open(..., '_blank')`.
3. **Clean Right-Hand Inspector Panel in Main App:**
   - Do **not** render legacy embedded 3D preview canvases (`.exploded-section`), `Open assembly and specs` buttons, `Enlarge` buttons, parts chip lists, or `Explode / Fit all` sliders in the main app's right Inspector panel. Keep only the **"Inspect Live 3D Teardown"** button so the right panel stays clean and uncluttered.
4. **Consistent Vessel Overview 3D Representation:** When a major piece of equipment's appearance is upgraded in its 3D teardown, update its procedural 3D representation in `src/vessel_scene.ts` so the Vessel Overview matches the teardown's visual identity.
