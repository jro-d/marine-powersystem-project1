# Prompt: 3-Cubicle (3-Board) 6.6 kV Marine Switchboard & Withdrawable VCB Digital Twin (`vcb.html`)

Copy and paste the prompt block below into **Gemini Argon** (either standalone or alongside your existing `vcb.html`) to generate the **3-Cubicle 6.6 kV Switchboard Lineup** matching the 3-board switchboard in the Vessel Overview.

```markdown
Build a complete, standalone, single-file `index.html` 3D interactive CAD Digital Twin and Racking/Teardown Simulator for a **3-Cubicle (3-Board) 6.6 kV, 3-Phase, 60 Hz, 31.5 kA IEC 62271-200 Form 4b Marine High-Voltage Switchboard Lineup & Withdrawable Vacuum Circuit Breaker (VCB)** using Three.js (`v0.160.0` via ES Module importmap with `OrbitControls` and `RoomEnvironment`).

The switchboard must be modeled as a **3-Bay / 3-Cubicle Lineup (`2.40 m` wide × `1.40 m` deep × `2.20 m` high, centered at `X = -0.80 m, 0.00 m, +0.80 m`)** so that it matches our 3-panel marine switchboard in the ship's machinery space overview:
- **Bay 1 (Left Cubicle, `X = -0.80 m` — Generator / Outgoing Feeder Panel with Open Door & Active Racking VCB Truck)**
- **Bay 2 (Center Cubicle, `X = 0.00 m` — 6.6 kV Bus-Tie & Check-Synchronizer Panel)**
- **Bay 3 (Right Cubicle, `X = +0.80 m` — 6.6 kV Transformer Feeder Panel)**

Follow every architectural, material, kinematic, and UI rule below without simplification:

### 1. Scene, Renderer, Camera & Smooth Non-Jumping Zoom (MANDATORY)
- **Renderer**: `THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" })`, `ACESFilmicToneMapping`, `toneMappingExposure = 1.05`, `shadowMap.enabled = true` (`PCFSoftShadowMap`, `2048x2048`).
- **Environment & Background**: `PMREMGenerator.fromScene(new RoomEnvironment(), 0.04).texture`, light studio drafting background `0xf2f4f7` with subtle grid (`0xdde2e8` / `0xe8ecf0`).
- **Camera**: `PerspectiveCamera(36, window.innerWidth / window.innerHeight, 0.1, 100)` at `[-3.2, 2.0, 4.2]`, target `[0, 1.05, 0]`.
- **Smooth Clamped Wheel Zoom (CRITICAL)**:
  - Set `controls.enableZoom = false` on `OrbitControls` so the browser/trackpad wheel never jumps inside the cabinet.
  - Attach a custom `{ passive: false }` `wheel` listener on `renderer.domElement`:
    ```js
    renderer.domElement.addEventListener('wheel', (e) => {
      e.preventDefault();
      const delta = THREE.MathUtils.clamp(e.deltaY, -100, 100);
      const zoomFactor = 1 + (delta > 0 ? 0.042 : -0.042) * (Math.abs(delta) / 100);
      const offset = camera.position.clone().sub(controls.target);
      const newDist = THREE.MathUtils.clamp(offset.length() * zoomFactor, controls.minDistance, controls.maxDistance);
      offset.setLength(newDist);
      camera.position.copy(controls.target).add(offset);
    }, { passive: false });
    ```
  - Set `controls.minDistance = 1.8`, `controls.maxDistance = 12.0`.

### 2. Physically Based Material Palette (`MeshStandardMaterial`)
- **Pebble Grey Enclosure Sheet Metal (`0x9aa3ad`)**: `roughness: 0.42`, `metalness: 0.35`, `side: THREE.DoubleSide`
- **Dark Slate Base Plinth & Corner Structural Frames (`0x3e4c59`)**: `roughness: 0.50`, `metalness: 0.45`
- **Galvanized Internal Form 4b Partition Plates (`0x8c96a0`)**: `roughness: 0.38`, `metalness: 0.60`
- **Maroon Cycloaliphatic Epoxy Resin (`0x8c2d26`)**: `roughness: 0.28`, `metalness: 0.05` (APG embedded poles, inter-bay bushings & standoff insulators)
- **95% Alumina Ceramic (`0xf0ede6`)**: `roughness: 0.18`, `metalness: 0.05` (vacuum interrupter bottles)
- **Electrolytic High-Conductivity Copper (`0xd97742`)**: `roughness: 0.22`, `metalness: 0.88` (3-bay main busbars, risers, tulip fingers, vacuum stems)
- **Silver-Plated Contact Surfaces & Chrome Hardware (`0xd8dee4`)**: `roughness: 0.18`, `metalness: 0.85`
- **Cast-Resin CT Toroids (`0xb87333`)**: `roughness: 0.40`, `metalness: 0.15`
- **Clear Polycarbonate Viewing Glass (`0xd8ecff`)**: `transparent: true`, `opacity: 0.25`, `depthWrite: false`

### 3. Six Cohesive Functional Sub-Assemblies (`parts` Registry)

1. **`cubicle_frame` — 3-Bay Form 4b Armored Cubicle Lineup (`CF`)**:
   - **3-Cubicle Steel Frame (`2.40 m` wide × `1.40 m` deep × `2.20 m` high, bay centers at `bays = [-0.80, 0.00, +0.80]`)**:
     - Continuous heavy base plinth (`2.44 m × 0.12 m × 1.44 m` at `Y = 0.06 m`), top overhanging drip canopy (`2.46 m × 0.06 m × 1.48 m` at `Y = 2.23 m`), and 3 upward-hinged top arc-fault pressure relief flaps (`[-0.80, 0, +0.80]`).
     - 4 vertical structural column frames at `X = -1.20, -0.40, +0.40, +1.20` and 2 internal metallic inter-cubicle division walls (`X = -0.40` and `X = +0.40`) separating Bays 1, 2, and 3.
     - Internal horizontal Form 4b metallic partitions separating the Upper LV Relay Chambers, Middle VCB Chambers, Top Rear Busbar Chamber, and Bottom Rear Cable Chambers across all 3 bays.
   - **Upper LV Instrumentation & Relay Compartments (All 3 Bays, `Y = 1.35 m` to `2.18 m`)**:
     - Across all 3 bays (`X = -0.80, 0.00, +0.80`), build front LV panel doors with:
       - A continuous horizontal black/slate **Mimic Bus Diagram Line** running across all 3 panels (`Y = 1.88 m`), with vertical feeder/tie drop lines and red/green breaker status blocks.
       - **3 Square Analog Panel Meters per bay** (`Ammeter`, `Voltmeter`, `kW / Synchroscope`) with white dial faces, dark bezels, and red needles.
       - **Microprocessor Protection Relay (`ANSI 51 / 67N / 25`)** per bay with dark bezel, glowing cyan LCD screen (`0x38bdf8`), status LEDs, and tactile function keys.
       - Red/Green/Amber indicator lamps and a black rotary control switch at the lower LV door of each bay.
   - **Lower VCB Compartment Doors (Bay 1 Open `110°`, Bays 2 & 3 Closed with Viewing Windows)**:
     - **Bay 1 (`X = -0.80 m`)**: Left-hinged heavy lower steel door (`pivot` at `[-1.18, 0.72, 0.70]`) swung open `110°` (`doorPivot.rotation.y = -1.92`), constructed using `THREE.Shape` + `path.holes` + `THREE.ExtrudeGeometry` so the central `0.35 m × 0.45 m` inspection window is a **true hollow cutout** with a dark bevel frame and transparent polycarbonate pane (`opacity: 0.25, depthWrite: false`). Include two extendable telescopic racking rails (`X = -1.08` and `-0.52`) protruding forward from Bay 1's floor.
     - **Bays 2 & 3 (`X = 0.00 m` and `+0.80 m`)**: Closed lower compartment doors, each built with the same `THREE.ExtrudeGeometry` hollow viewing window cutout (`0.35 m × 0.45 m`) + clear polycarbonate glass pane so the stationary VCB units inside Bays 2 and 3 are visible through the glass, plus chrome vertical handles and bottom stamped ventilation louver slots.
   - **Explode Vector**: `[0, 0, 0]` (anchor reference; side/rear panels ghost when another part is isolated).

2. **`busbars` — Continuous 3-Bay 6.6 kV Electrolytic Copper Busbars & Risers (`BB`)**:
   - Located in the top-rear busbar chamber (`Y = 1.55 m` to `2.05 m`, `Z = -0.15 m` to `-0.45 m`).
   - **3 Continuous Horizontal Main Busbars (`2.32 m` wide × `0.07 m` high × `0.08 m` deep)** spanning across all 3 cubicles (`X = -1.16 m` to `+1.16 m`), supported by 9 ribbed maroon cycloaliphatic standoff insulators (3 per bay) and passing through Form 4b inter-bay insulating partition bushings at `X = -0.40 m` and `X = +0.40 m`.
   - Color-coded heat-shrink phase sleeves in every bay: **Phase L1 (`0xdc2626` Red)**, **Phase L2 (`0xeab308` Yellow)**, **Phase L3 (`0x2563eb` Blue)**.
   - **9 Vertical Copper Drop-Down Risers** (3 per bay at `dx = -0.22, 0, +0.22` around each bay center) descending to the upper stationary spout bushings and down to the lower cable chamber.
   - **Explode Vector**: `[0, 0.55, -0.45]` (upward and aft).

3. **`shutters` — Automatic IP2X Safety Shutters & Stationary Spout Plate (`SS`)**:
   - Mounted at the rear wall of Bay 1's breaker compartment (`X = -0.80 m, Z = -0.05 m`), with matching stationary spout assemblies visible in Bays 2 and 3:
     - 6 stationary maroon epoxy spout bushings (3 upper line-side at `Y = 1.12 m`, 3 lower load-side at `Y = 0.72 m`) housing recessed copper fixed pin contacts.
     - **Animated Upper & Lower Steel Safety Shutters (`shutterUpper`, `shutterLower`)** in Bay 1 with yellow/black diagonal hazard stripes (`DANGER 6.6 kV LIVE BUSBARS`) and side scissor-cam linkages.
     - When Bay 1's VCB truck racks out past `22%`, `shutterUpper` and `shutterLower` automatically slide vertically over the live 6.6 kV spouts (`IP2X` protection) and open smoothly as the truck racks into `SERVICE (0%)`.
   - **Explode Vector**: `[0, 0.25, -0.15]`.

4. **`vcb_truck` — Monolithic Withdrawable VCB Truck, Spring Drive & Control Fascia (`TR`)**:
   - **Active Racking VCB Truck in Bay 1 (`breakerTruckGroup` at `X = -0.80 m`)**:
     - Every component on the withdrawable breaker carriage (`chassis`, `flanged steel wheels`, `lead-screw collar`, `front operating fascia`, `spring mechanism`, `epoxy poles`, `vacuum bottles`, `tulip contacts`) MUST be parented inside a single root `THREE.Group` named `breakerTruckGroup` so it rolls out along the telescopic rails (`Z = 0.00 m -> +0.58 m`) as one cohesive unit during Racking (`0%` to `100%`).
     - Detailed sheet-metal front fascia (`0.68 m × 0.56 m`) featuring:
       - Top nameplate (`VCB-01 · 6.6 kV VACUUM BREAKER · IEC 62271-100 · Ir 1250 A · Isc 31.5 kA`)
       - Recessed green `PUSH ON (I)` and red `PUSH OFF (O)` mechanical pushbuttons
       - Manual spring-charging pull handle
       - Mechanical flag window for `CLOSED (I)` (`0xdc2626` Red) / `OPEN (O)` (`0x16a34a` Green)
       - Mechanical flag window for `SPRING CHARGED` (`0xeab308` Yellow) / `DISCHARGED`
       - 5-digit mechanical operations counter (`0 1 4 8 2`)
       - Bottom brass lead-screw racking port with Castell interlock keyhole.
     - Behind the fascia (revealed on Explode): yellow-chromate helical closing & tripping springs, cam shaft, auxiliary contact block, and motor-charging gearhead.
     - Also place stationary/service-position VCB front fascias inside Bays 2 and 3 (`X = 0.00 m` and `+0.80 m`) visible through their closed lower door windows.
   - **Explode Vector**: `[0, 0, 0.75]` (forward along the rails; front fascia cover shifts an additional `+0.28 m` forward to expose the internal spring drive).

5. **`epoxy_poles` — Maroon Embedded Cycloaliphatic Epoxy Poles & Tulip Contacts (`EP`)**:
   - Mounted atop `breakerTruckGroup` in Bay 1 (`X = -0.80 m` with phase spacing `dx = -0.22, 0, +0.22`, plus visible pole tops in Bays 2 & 3):
   - 3 ribbed maroon cycloaliphatic epoxy resin insulation cylinders (`0x8c2d26`) with shed skirts and front cutaway windows so the internal ceramic vacuum bottles are visible.
   - 6 rearward-projecting copper conductor arms (3 upper, 3 lower) tipped with **12-finger crown-spring silver-plated copper tulip contact clusters** (`0xd97742` / `0xd8dee4`) that mate into the stationary spout bushings at `SERVICE (0%)`.
   - **Explode Vector**: `[0, 0.38, 0.75]` (lifts upward above the truck during Explode while tracking the truck's `Z` racking position).

6. **`vacuum_interrupters` — 95% Alumina Ceramic Vacuum Bottles & Moving Contact Stems (`VI`)**:
   - Nested concentrically inside the 3 maroon epoxy poles of Bay 1 (`breakerTruckGroup`):
   - 95% alumina ceramic cylindrical envelopes (`0xf0ede6`) with glazed shed rings, brazed copper end-caps, internal copper vapor-condensation arc shields, stationary upper copper contact stems, and lower moving copper contact stems with stainless-steel metallic bellows and insulated fiberglass pushrods.
   - When the user clicks **CLOSE VCB (I)** / **TRIP VCB (O)**, the lower moving copper contact stems physically stroke `12 mm` vertically inside the cutaway vacuum bottles.
   - **Explode Vector**: `[0, 0.72, 0.75]` (lifts vertically out of the top of the maroon epoxy poles during Explode).

7. **`cable_ct_bay` — 3-Bay Toroidal CTs, Stress Cones & Armored XLPE Cables (`CB`)**:
   - Located in the lower-rear cable compartment across all 3 bays (`bays = [-0.80, 0.00, +0.80]`, `Y = 0.12 m` to `0.68 m`, `Z = -0.32 m`):
   - **9 Cast-Resin Toroidal Current Transformers (`0xb87333`)** (3 per bay) with secondary terminal boxes (`ANSI 51 / 67N`).
   - **9 Elastomeric HV Stress Cones** with braided copper earthing tails bonded to the continuous horizontal copper earth bar (`2.32 m` wide) and **9 Black XLPE 6.6 kV Armored Power Cables** rising through brass gland plates in the floor.
   - **Explode Vector**: `[0, -0.15, -0.55]` (aft and slightly downward).

### 4. Interactive Controls, Dual Sliders & Native-Color Ghost Isolation (CRITICAL)
- **Top-Left Header**: Title `6.6 kV 3-Cubicle Marine Switchboard & Withdrawable VCB`, subtitle `IEC 62271-200 Form 4b · 3-Panel Lineup (Incomer / Bus-Tie / Feeder) · 31.5 kA`.
- **Top-Right Pill Toolbar**: `Reset View`, `Auto-Rotate`, `Toggle Labels`, `X-Ray / Solid Enclosure`.
- **Bottom Dock Control Bar**:
  - **Racking Position Slider (`0%` to `100%`)**: Translates `breakerTruckGroup` in Bay 1 (`Z = 0.00 m` Service -> `+0.25 m` Test/Disconnected -> `+0.58 m` Withdrawn on Rails) and automatically closes/opens `shutterUpper` & `shutterLower` past `22%`.
  - **Explode Assembly Slider (`0%` to `100%`)**: Separates all sub-assemblies along their explode vectors and opens the front fascia of the VCB truck to reveal the spring mechanism and vacuum bottles.
  - **Breaker State Toggle Button (`CLOSE VCB (I)` / `TRIP VCB (O)`)**: Updates the mechanical flag indicators (`CLOSED`/`OPEN`, `CHARGED`/`DISCHARGED`) and strokes the moving vacuum contact stems.
  - **IEC Interlock Guard**: Disable closing when `0% < Racking < 35%` (between Service and Test) and display an interlock status badge (`SERVICE · BUS CONNECTED`, `INTERLOCKED · IN TRANSIT`, `TEST · ISOLATED`, `WITHDRAWN · ON RAILS`).
- **Native-Color Ghosting on Part Selection (NO Color Bleed)**:
  - During initialization, clone both `mesh.userData.origMaterial = mesh.material.clone()` and `mesh.userData.ghostMaterial = mesh.material.clone()` (`transparent: true, opacity: 0.14, depthWrite: false`) for every mesh.
  - Never mutate material `.color` when ghosting; non-selected parts must retain their native copper, maroon, ceramic, and steel colors at `14%` opacity.

### 5. Divided Left & Right Callout Columns with Long SVG Leader Lines (MANDATORY)
- Divide the 3D callout badges into **Left** (`CF`, `SS`, `VI`, `TR` at `LEFT_X = 24px`) and **Right** (`BB`, `EP`, `CB` at `RIGHT_X = window.innerWidth - 204px`) vertical screen-margin columns based on the projected 2D `X` coordinate of each part's 3D anchor relative to the switchboard center.
- Run a vertical collision-avoidance pass (`MIN_GAP = 42px`) on each column every frame so callout badges never overlap at any camera angle, racking position, or explode percentage.
- Draw crisp 2-segment SVG `<polyline>` leader lines (`anchor (ax, ay) -> elbow (elbowX, ly) -> badge edge (badgeEdgeX, ly)`) with a `3px` anchor dot at `(ax, ay)`.

Return the complete, self-contained `index.html` file with zero external local assets.
```
