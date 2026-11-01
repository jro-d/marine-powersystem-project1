# Marine CAD Digital Twin Builder (`v2.1.0`) — 6 Equipment Teardown Prompts

> [!TIP]
> **How to Use These Prompts with Any AI Model:**
> Each section below (`Prompt 1` through `Prompt 6`) is **100% self-contained** and embeds all mandatory rules from your `marine-cad-digital-twin-builder` (`v2.1.0`) skill (Light-Studio plinth, soft industrial CAD palette, native-color ghost isolation at `opacity: 0.14`, custom non-jumping `4.2%` wheel zoom, and Left/Right divided callout columns with long SVG leader lines).
> Simply copy a prompt block and paste it into any model (or attach `SKILL.md` alongside it), then save the generated single-file HTML into `public/teardowns/`.

---

## Shared Mandatory Skill Block (Include with Every Prompt or Attach `SKILL.md`)

If the external AI model does not already have `SKILL.md` loaded in its system prompt, copy the **Shared Skill Rules Block** below together with the specific Equipment Prompt:

```markdown
### MANDATORY ARCHITECTURAL, VISUAL & UI RULES (`marine-cad-digital-twin-builder v2.1.0`)
1. **Single Self-Contained HTML File (`< 1 MB`)**:
   - Output a single standalone HTML file using Three.js (`r160` via ES module importmap or `r128`) and Tailwind CSS CDN. Zero external 3D asset files (`.glb`/`.obj`). Build all geometry procedurally in true marine millimetre/metre scale.
2. **Unified Light-Studio Environment & Plinth (Diesel Generator / VCB Standard)**:
   - Scene background: `new THREE.Color(0xf1f3f6)` and CSS `#canvas-container` radial gradient `radial-gradient(circle at 50% 45%, #f8fafc 0%, #eaedf1 100%)`.
   - Two-tier architectural concrete studio plinth at `y = 0.0` (upper slab `#f8fafc` at `y = -0.04 m`, lower curb `#e2e8f0` at `y = -0.09 m`) with a `ShadowMaterial({ opacity: 0.16 })` plane at `y = 0.001 m`. **Never** add a wireframe `GridHelper` on the floor.
   - Lighting: `HemisphereLight(0xffffff, 0xdbe2ea, 1.25)`, key `DirectionalLight(0xfffdf9, 1.35)` at `(8, 14, 7)` with `2048x2048` `PCFSoftShadowMap`, fill light `(0xe2e8f0, 0.85)`, rim light `(0xffffff, 0.55)`, and `ACESFilmicToneMapping` (`toneMappingExposure = 1.12`).
3. **Soft Industrial CAD Material Palette (No Harsh Jet-Black)**:
   - Cabinet / Enclosure Steel: `#c9d2db` (`roughness: 0.42, metalness: 0.16`)
   - Structural Trim / Frames: `#9aa8b6` (`roughness: 0.45, metalness: 0.22`)
   - Heavy Carriage / Castings: `#8796a5` (`roughness: 0.44, metalness: 0.28`)
   - Bezels / Base Channels / Conduits: `#738291` (`roughness: 0.46, metalness: 0.26`)
   - Marine Machinery Sage Enamel: `#3b6254` (`roughness: 0.44, metalness: 0.22`)
   - Cast Epoxy Resin / HV Coils: `#a6534c` (`roughness: 0.36, metalness: 0.10`)
   - Copper Busbars & Windings: `#d47a42` (`roughness: 0.28, metalness: 0.80`)
   - Nickel-Aluminium-Bronze (NAB) / Brass: `#d8b25c` (`roughness: 0.28, metalness: 0.78`)
   - Polished Shaft Steel / Silver Contacts: `#e2e8f0` (`roughness: 0.20, metalness: 0.85`)
4. **Native-Color Ghost-Opacity Subsystem Isolation (`opacity: 0.14`)**:
   - In `prepareSubsystemMaterials()`, clone every mesh's material per subsystem into **both** `obj.userData.origMaterial` AND `obj.userData.ghostMaterial = origClone.clone()` with `transparent: true, opacity: 0.14, depthWrite: false`.
   - **Never** use a single shared grey or yellow `matGhost` material! When a subsystem is isolated, non-selected subsystems must use their own `obj.userData.ghostMaterial` so every ghosted part retains its native color at low opacity (`0.14`).
   - Any dynamically colored status flags/indicators must mutate `mesh.userData.origMaterial.color` and `mesh.userData.ghostMaterial.color` on that specific mesh only.
5. **Floor-Safe Exploded Teardown (`y >= 0`) & Dashed Centerlines**:
   - Every subsystem explosion vector `explodeVectors[key]` must keep all geometry strictly above the studio plinth (`y >= 0.0`) at `0%–100%` explosion. Never explode bottom subsystems downward (`-Y`).
   - Draw dynamic `THREE.LineDashedMaterial` (`color: 0xc25b2a`) guide lines when `explodeFactor > 0.02`.
6. **Smooth, Non-Jumping Custom Wheel Zoom & Unlocked 360° Orbit**:
   - Set `controls.minAzimuthAngle = -Infinity`, `controls.maxAzimuthAngle = Infinity`, `controls.maxPolarAngle = Math.PI * 0.495`.
   - Set `controls.enableZoom = false;` (to avoid Three.js `r160` `devicePixelRatio | 0` jump bugs) and attach this exact custom wheel handler on `renderer.domElement`:
     ```js
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
7. **Left & Right Divided Callout Columns with Long SVG Leader Lines (Zero Overlap)**:
   - Divide the 7 callout labels into a **Left column (`side: 'left'`, `transform: translate(-100%, -50%)`)** and a **Right column (`side: 'right'`, `transform: translate(0%, -50%)`)** positioned well outside the 3D equipment footprint (`baseLeftColX` and `baseRightColX`).
   - Run a vertical anti-overlap solver (`resolveVerticalSpacing(items, 92, window.innerHeight - 76, 48)`) on each column every frame so labels never overlap each other.
   - Render an `<svg>` layer inside `#callouts-container` drawing long `<polyline>` leader lines and `<circle r="2.6">` anchor dots from each pill's inner edge to the projected 3D part coordinate `(anchorX, anchorY)`.
8. **Consistent Minimal Light-Studio UI Layout**:
   - **Left Sidebar (`280px` fixed white panel):** Domain pill, Equipment title & IEC/SOLAS spec subtitle, `Equipment` header with `Show all`, 7 subsystem isolation buttons with 2-letter mono badges, and bottom `2x2` live telemetry strip.
   - **Top-Left Floating Pill Bar:** `← Vessel view` (`href="../index.html"` in the same tab) and `Kinematic & IEC proof` modal button.
   - **Right Floating Inspector Card (`330px` translucent white card):** Active BOM code (`ASSY-01`), title & description, `View` toggle pills (`Labels`, `Cutaway X-Ray`, `Telemetry`), Camera preset dropdown, operational sliders + `Exploded teardown` slider (`0%` / `100%`), two live HTML5 2D telemetry canvases, and `[ Reset view ] [ + ] [ - ]` footer.
```

---

## Prompt 1: 6.6 kV / 440 V Cast-Resin Dry-Type Marine Distribution Transformer (`tx.html`)

Target file in app: `public/teardowns/tx.html`

```markdown
/marine-cad-digital-twin-builder Build the Marine 6.6 kV / 440 V Dry-Type Cast-Resin Distribution Transformer (TX A / TX B, 2,500 kVA / 2.5 MVA, 60 Hz, Vector Group Dyn11, AN/AF Cooling) as an interactive, standalone 3D digital twin simulator that users can operate and take apart.

Reference standards: IEC 60076-11 (Dry-Type Power Transformers), IEC 60092-303 (Marine Electrical Equipment - Transformers for Power and Lighting), and DNV / SOLAS Marine High-Voltage Installations.

1. GEOMETRY & 7 SELECTABLE SUBSYSTEMS (Build procedurally in true marine scale: Width 2100 mm, Depth 1350 mm, Height 2200 mm):

- `enclosure` (Badge `EN` · IP23 Marine Drip-Proof Enclosure & Louvers):
  * Bolted RAL 7032 / soft cool-slate (`#c9d2db`) steel enclosure with marine drip-proof angled top canopy (IP23 protection against falling water drops up to 60°).
  * Front and rear hinged inspection doors with **true extruded cutout viewing windows** (`THREE.Shape` + `shape.holes` + `THREE.ExtrudeGeometry`, zero Z-fighting) and perforated ventilation louver grilles.
  * Heavy base skid channels (`#738291`) with 6 resilient marine anti-vibration rubber mounts and copper frame earthing bosses.
  * Included in `cutawayMeshes` so toggling `Cutaway X-Ray` turns the enclosure panels and HV epoxy coil outer shells into translucent glass.

- `magneticCore` (Badge `MC` · 3-Limb Step-Lap CRGO Laminated Silicon-Steel Core):
  * Cold-Rolled Grain-Oriented (CRGO) laminated silicon-steel 3-limb core (`#738291` / `#8796a5`) with stepped circular cross-section limbs, top and bottom C-channel clamping yokes, high-tensile tie rods, and red/amber insulation blocks.

- `lvWindings` (Badge `LV` · Inner 440 V Foil-Wound Secondary Coils & Star Busbars):
  * 3 concentric inner Low-Voltage (440 V, 3,280 A rated) copper foil windings (`#d47a42`) mounted concentrically around the 3 core limbs with axial cooling duct spacers.
  * Heavy top/front copper star (`y`) neutral busbar and L1/L2/L3 outgoing copper risers with flexible braided copper expansion shunts.

- `hvWindings` (Badge `HV` · Outer 6.6 kV Vacuum-Cast Epoxy Resin Primary Coils & Delta Links):
  * 3 outer High-Voltage (6.6 kV, 218.7 A rated) vacuum-cast cycloaliphatic epoxy resin cylinder coils (`#a6534c` terracotta-rose) mounted concentrically outside the LV coils with radial porcelain/silicone support pads.
  * Front copper delta (`D`) phase-interconnection links and brass off-circuit tap-changer link terminal pads (`±2 × 2.5%` voltage ratio taps: Tap 1 `+5%`, Tap 2 `+2.5%`, Tap 3 `0% Nominal`, Tap 4 `-2.5%`, Tap 5 `-5%`).

- `bushingsTerminals` (Badge `BT` · 6.6 kV Shedded Porcelain Bushings, Surge Arresters & 440 V Flags):
  * 3 top-mounted 6.6 kV shedded brown/coral-red porcelain primary bushings (`U1, V1, W1`) with brass terminal stems and 3 zinc-oxide (ZnO) HV surge arresters.
  * 4 outgoing 440 V secondary copper busbar flags (`u, v, w, n`) with toroidal protection CTs and bottom brass compression cable glands.

- `coolingFans` (Badge `CF` · Cross-Flow AF Tangential Cooling Fans & PT100 Thermal Probe):
  * 2 bottom-mounted cross-flow tangential forced-air (`AF`) cooling fan assemblies (with rotating multi-blade impellers driven around their true concentric axis) directing air upward through the HV-LV annular cooling ducts.
  * Digital PT100 winding temperature controller (`NT935` style) mounted on the front enclosure header with 3-phase fiber/capillary sensor leads entering the LV/HV windings.

- `magneticFlux` (Badge `MF` · Animated 3-Phase 120° Magnetic Flux & Thermal Airflow Vectors):
  * 3-phase animated magnetic flux loops (`Φ_A`, `Φ_B`, `Φ_C`) circulating through the 3 core limbs and yokes, phase-shifted by 120° (`cos(ωt)`, `cos(ωt - 2π/3)`, `cos(ωt - 4π/3)`), plus rising convective/forced-air thermal streamlines through the winding ducts.

2. MATHEMATICAL & ELECTRICAL MODEL (Drive from Master Inputs):
- Master Input 1: Transformer Load Factor `loadPct` (`0%` no-load to `125%` overload, default `80%` = `2,000 kVA`).
- Master Input 2: Off-Circuit Tap Position (`Tap 1: +5.0%`, `Tap 2: +2.5%`, `Tap 3: 0.0% Nominal`, `Tap 4: -2.5%`, `Tap 5: -5.0%`) — interlock-protected so tap changing is blocked while transformer is energized unless switched to `DE-ENERGIZED` mode.
- Master Input 3: Cooling Mode (`AN Natural Air` up to 100% rating vs `AF Forced Air Blowers` up to 125% rating; auto-starts fans when winding temperature `T_w >= 110 °C`).
- Exact Equations (Show in `Kinematic & IEC Proof` modal and live HUD):
  * Turns Ratio (Dyn11): Primary delta voltage $V_{1\phi} = 6600\text{ V}$, Secondary star line voltage $V_{2L} = 440\text{ V}$ ($V_{2\phi} = 440/\sqrt{3} = 254.0\text{ V}$), nominal phase turns ratio $N_1/N_2 = 6600 / 254.034 = 25.98$.
  * Copper & Core Losses: Core no-load loss $P_{Fe} = 4.2\text{ kW}$; load loss $P_{Cu}(L) = 21.5\text{ kW} \times (L/100)^2$; efficiency $\eta = (S \cdot \cos\varphi) / (S \cdot \cos\varphi + P_{Fe} + P_{Cu})$.
  * Winding Hot-Spot Temperature (Class F $155\text{ }^\circ\text{C}$ insulation): $T_{hotspot} = T_{amb}(45^\circ\text{C}) + \Delta T_{core} + \Delta T_{Cu} \cdot (L/100)^{1.6} \cdot k_{AF}$ (where $k_{AF} = 0.72$ when AF blowers run).
  * Dyn11 Vector Phase Shift: Secondary 440 V line voltage leads Primary 6.6 kV line voltage by $+30^\circ$ (11 o'clock vector group).

3. FLOOR-SAFE EXPLODED VIEW VECTORS (`y >= 0` strictly):
- `magneticCore`: `(0, 0, 0)` (stationary reference on plinth)
- `enclosure`: `(0, 0.95, 0)` (lifts straight up clear of internal core & coils)
- `lvWindings`: `(-0.65, 0.18, 0)`
- `hvWindings`: `(0.65, 0.22, 0)`
- `bushingsTerminals`: `(0, 0.65, -0.55)`
- `coolingFans`: `(0, 0.05, 0.72)` (slides forward horizontally along `+Z`, never below floor!)
- `magneticFlux`: `(0, 0.40, 0)`

4. LEFT & RIGHT DIVIDED CALLOUT LABELS (4 Left, 3 Right with Long SVG Leader Lines):
- Left (`side: 'left'`): `EN · IP23 Drip-Proof Enclosure`, `HV · 6.6 kV Cast-Resin Coils`, `LV · 440 V Foil Windings`, `CF · AF Tangential Cooling Fans`.
- Right (`side: 'right'`): `BT · 6.6 kV Bushings & Arresters`, `MC · CRGO Silicon-Steel Core`, `MF · Dyn11 Core Flux & Tap Links`.

5. RIGHT INSPECTOR TELEMETRY CANVASES:
- Canvas 1: **Live Thermal Hot-Spot & Efficiency Curve** (plotting Winding Temp °C vs Load % with Class F `130 °C` alarm / `155 °C` trip thresholds and live operating dot).
- Canvas 2: **Dyn11 Primary (6.6 kV) vs Secondary (440 V, +30° Lead) 3-Phase Waveforms**.

Apply all rules from `marine-cad-digital-twin-builder v2.1.0` (native-color ghost isolation `opacity: 0.14`, custom `4.2%` wheel zoom handler, Left/Right non-overlapping callout columns with long SVG leader lines, and shader pre-warming). Output the complete, standalone HTML file.
```

---

## Prompt 2: 6.6 kV / 1,200 kW Bow Tunnel Thruster with Right-Angle Bevel Gear & CPP (`bow_thruster.html`)

Target file in app: `public/teardowns/bow_thruster.html`

```markdown
/marine-cad-digital-twin-builder Build the Marine 6.6 kV / 1,200 kW Transverse Bow Tunnel Thruster with Vertical Induction Motor, Right-Angle Spiral Bevel Gearbox, and 4-Blade Controllable Pitch Propeller (CPP) as an interactive, standalone 3D digital twin simulator that users can operate and take apart.

Reference standards: IEC 60092-501 (Electric Propulsion & Thruster Plant), DNV Pt.4 Ch.5 (Rotating Machinery & Thrusters), and SOLAS Maneuvering & Watertight Compartment Integrity.

1. GEOMETRY & 7 SELECTABLE SUBSYSTEMS (Build procedurally in true marine scale: Tunnel Diameter 1850 mm, Overall Height 3100 mm):

- `tunnelShell` (Badge `TS` · Transverse Hull Tunnel Ring, Sacrificial Zinc Anodes & Sea Grids):
  * Heavy cylindrical steel athwartships thruster tunnel shell (`#738291` / `#8796a5`, bore 1850 mm) welded into double-plate hull web frames with cast streamlining fairings, bolted stainless intake protective debris grids, and bolt-on sacrificial zinc anodes (`#e2e8f0`).
  * Top watertight bulkhead mounting flange & motor pedestal ring.
  * Included in `cutawayMeshes` so `Cutaway X-Ray` turns the upper half of the tunnel shell and pod housing into clear glass to reveal the propeller and bevel gear train inside.

- `verticalMotor` (Badge `VM` · 6.6 kV / 1,200 kW Vertical Squirrel-Cage Motor & HV Box):
  * Vertically mounted 6.6 kV / 1,200 kW marine induction motor (`#3b6254` marine sage green) bolted atop the tunnel pedestal with cast vertical cooling fins, top water-to-air heat exchanger cover, and side-mounted 6.6 kV HV terminal box (`L1, L2, L3` bushings).
  * Internal laminated stator core, copper end-windings (`#d47a42`), and concentric vertical rotor shaft with flexible pin-bush coupling.

- `bevelGearbox` (Badge `BG` · Submerged Streamlined Pod & Spiral Bevel Gear Train):
  * Hydrodynamic streamlined cast-iron/bronze submerged gear pod (`#8796a5`) suspended inside the tunnel by heavy upper and lower hydrofoil struts.
  * Internal 90° right-angle spiral bevel gear pair (vertical input pinion driving horizontal propeller crown wheel at `3.83:1` reduction: `1,150 RPM` motor -> `300 RPM` propeller shaft), tapered roller thrust bearings, and double-lip shaft seals.

- `cppHubBlades` (Badge `CP` · 4-Blade Skewed Nickel-Aluminium-Bronze CPP Hub & Blades):
  * Concentric rotating horizontal propeller hub (`#d8b25c` polished Nickel-Aluminium-Bronze) with 4 high-skewed Kaplan-style thruster blades mounted on rotatable blade trunnion palms.
  * **Critical Kinematic Rule:** All 4 blades must rotate concentrically with the hub around the horizontal tunnel axis AND simultaneously feather their blade pitch angle $\alpha \in [-25^\circ, +25^\circ]$ around each blade's radial spindle axis when the Bridge Pitch Order lever changes!

- `pitchActuator` (Badge `PA` · Hydraulic Pitch Servo Yoke, Push-Pull Rod & Header Tank):
  * Internal hollow-shaft hydraulic push-pull pitch actuating rod, sliding crosshead yoke with eccentric crank pins inside the hub, rotary oil distribution (OD) box at the gearbox rear cap, and elevated gravity lube-oil header tank with sight glass and hydraulic servo valve block.

- `slipstreamWake` (Badge `SW` · Port/Starboard Helical Water Jet Streamlines):
  * Dynamic 3D helical water-jet flow rings and axial velocity streamlines inside the tunnel that reverse direction and scale speed/opacity proportionally to the active blade pitch angle $\alpha$ (Port thrust vs Zero-Pitch neutral vs Starboard thrust).

- `foundationChocks` (Badge `FC` · Watertight Trunk Pedestal, Anti-Vibration Mounts & Bilge Sensors):
  * Heavy structural ship-frame pedestal base sitting on the studio plinth with stiffening gusset brackets, flanged seawater cooling pipes, and high-level bilge/seal-leakage float alarm sensor.

2. MATHEMATICAL & KINEMATIC MODEL (Drive from Master Inputs):
- Master Input 1: Bridge Thruster Pitch Order $\alpha \in [-25^\circ\text{ (Full Port)}, 0^\circ\text{ (Zero Thrust)}, +25^\circ\text{ (Full Starboard)}]$.
- Master Input 2: 6.6 kV Drive Motor Speed (`0 RPM` Stopped, `750 RPM` Low Speed, `1,150 RPM` Rated Synchronous/Slip Speed).
- Exact Equations (Show in `Kinematic & IEC Proof` modal and live HUD):
  * Gear Reduction Ratio: $i_{gear} = 46 / 12 = 3.833:1 \implies n_{prop} = n_{motor} / 3.833 = 300\text{ RPM}$ at $n_{motor} = 1,150\text{ RPM}$.
  * Hydraulic Servo Stroke: $s_{servo}(\alpha) = R_{pin} \cdot \sin(\alpha)$, where eccentric pin radius $R_{pin} = 85\text{ mm}$ ($\pm 35.9\text{ mm}$ axial pushrod travel).
  * Hydrodynamic Thrust Force: $T(\alpha, n) = K_T(\alpha) \cdot \rho_{sw} \cdot n_{prop}^2 \cdot D^4$, peaking at $\pm 168\text{ kN}$ ($\pm 17.1\text{ tonnes-force}$) at $\alpha = \pm 25^\circ$ and $300\text{ RPM}$ ($D = 1.80\text{ m}$, $\rho_{sw} = 1025\text{ kg/m}^3$).
  * Absorbed Electrical Power: $P_{elec}(\alpha) = P_{idle}(85\text{ kW}) + (1,115\text{ kW}) \cdot (|\alpha| / 25^\circ)^{2.4} \cdot (n_{prop}/300)^3$, with zero-pitch soft-start interlock (6.6 kV breaker can only close when $|\alpha| \le 2^\circ$ to prevent bus voltage dip!).

3. FLOOR-SAFE EXPLODED VIEW VECTORS (`y >= 0` strictly):
- `foundationChocks`: `(0, 0, 0)`
- `tunnelShell`: `(0, 0.15, -0.75)`
- `verticalMotor`: `(0, 0.95, 0)` (lifts vertically above pedestal)
- `bevelGearbox`: `(0, 0.25, 0.45)`
- `cppHubBlades`: `(-0.85, 0.25, 0.45)` (slides out axially along the tunnel axis)
- `pitchActuator`: `(0.75, 0.45, 0.35)`
- `slipstreamWake`: `(-1.25, 0.25, 0)`

4. LEFT & RIGHT DIVIDED CALLOUT LABELS (4 Left, 3 Right with Long SVG Leader Lines):
- Left (`side: 'left'`): `VM · 6.6 kV Vertical Motor (1.2 MW)`, `CP · 4-Blade Skewed NAB CPP Hub`, `SW · Transverse Jet Streamlines`, `FC · Watertight Trunk Pedestal`.
- Right (`side: 'right'`): `PA · Hydraulic Pitch Servo & OD Box`, `BG · 90° Spiral Bevel Gear Pod`, `TS · 1850 mm Tunnel & Zinc Anodes`.

5. RIGHT INSPECTOR TELEMETRY CANVASES:
- Canvas 1: **Thrust (kN) & Motor Power (kW) vs Blade Pitch Angle ($\alpha \in [-25^\circ, +25^\circ]$)** with live operating point.
- Canvas 2: **6.6 kV Motor Current & Hydraulic Pitch Servo Pressure (bar) Time Trace**.

Apply all rules from `marine-cad-digital-twin-builder v2.1.0`. Output the complete, standalone HTML file.
```

---

## Prompt 3: 440 V Marine Cargo Reefer Distribution Switchboard & Socket Rack (`reefer_board.html`)

Target file in app: `public/teardowns/reefer_board.html`

```markdown
/marine-cad-digital-twin-builder Build the Marine 440 V Cargo Reefer Distribution Switchboard & Interlocked Container Socket Rack (Reefer Board A / B, 440 V / 60 Hz / 1,500 kVA, IP56 Weatherproof / Cargo Hold Design) as an interactive, standalone 3D digital twin simulator that users can operate and take apart.

Reference standards: IEC 60092-509 (Marine Reefer Container Power Distribution), IEC 60309-5 (440 V 32 A 3P+E Marine Reefer Plugs & Interlocked Sockets), and SOLAS / DNV Cargo Hold Electrical Safety.

1. GEOMETRY & 7 SELECTABLE SUBSYSTEMS (Build procedurally in true marine scale: Width 1800 mm, Depth 950 mm, Height 2150 mm):

- `enclosureFrame` (Badge `EF` · IP56 Marine Steel Cabinet, Drip Canopy & Anti-Condensation Heaters):
  * Two-bay bolted marine switchgear cabinet (`#c9d2db` panels with `#9aa8b6` structural posts): Left Bay = 440 V Incomer & Feeder MCCB Cubicle; Right Bay = Weatherproof Recessed Reefer Socket & Mechanical Interlock Matrix.
  * Hinged front door on Left Bay with **true extruded cutout window** (`THREE.Shape` + `shape.holes` + `THREE.ExtrudeGeometry`, zero Z-fighting), neoprene IP56 compression gasket, and 3-point stainless dogging latches.
  * Bottom anti-condensation space heater strip (`220 V / 150 W`) and base plinth channel (`#738291`).

- `incomerAcb` (Badge `IA` · 1,600 A 440 V Air Circuit Breaker & Power Quality Meter):
  * Draw-out 1,600 A 440 V 3-pole Air Circuit Breaker (ACB) cassette in the upper-left bay with ribbed arc-chute chambers, mechanical `CHARGED/DISCHARGED` & `OPEN/CLOSED` flags, and digital multifunction power & THD harmonic analyzer on the upper fascia.

- `copperBusbars` (Badge `CB` · 440 V 3-Phase Copper Busbar Pan Assembly & DMC Supports):
  * Vertical and horizontal tin/copper-busbar distribution pan assembly (`#d47a42`) with color-coded phase sleeves (`L1` Red, `L2` Amber, `L3` Blue), ribbed red DMC standoff insulators (`#b35d56`), and neutral/earth reference bars.

- `mccbFeeders` (Badge `MC` · 8 × 32 A Moulded-Case Circuit Breakers & 30 mA RCM Toroids):
  * 2 vertical banks of 4 Moulded-Case Circuit Breakers (`MCCB-01` to `MCCB-08`, 440 V / 32 A thermal-magnetic trip) with rotary operating handles and individual zero-sequence Residual Current Monitoring (`RCM`, 30 mA earth-leakage pickup) toroidal cores (`#b8804c`).

- `reeferSockets` (Badge `RS` · 8 × Interlocked 440 V 32 A 4-Pin Marine Reefer Receptacles):
  * 8 heavy-duty angled brass/nickel-plated marine reefer sockets (IEC 60309-5, 440 V, 32 A, `3h` clock keyway position) arranged in a `2×4` matrix on the right bay.
  * Each socket has a spring-loaded hinged weatherproof cap, a rotary mechanical interlock switch handle (`0 OFF` / `1 ON`), and an individual LED status lens (`GREEN = Powered`, `AMBER = Standby/Unplugged`, `RED = 30 mA Earth Fault Trip`).
  * **Mechanical Interlock Rule:** A reefer plug cannot be inserted or withdrawn while its rotary switch is `ON`, and the rotary switch cannot be turned `ON` unless a plug is fully inserted!

- `containerPlugs` (Badge `CP` · Heavy-Duty Yellow/Slate Neoprene Reefer Plugs & Flexible Trailing Cables):
  * Monolithic movable group (`reeferPlugsGroup`) of 440 V 4-pin watertight reefer plugs with threaded brass locking collars, strain-relief glands, and curved `CatmullRomCurve3` flexible `4×6 mm²` neoprene trailing cables exiting toward the container bays.
  * Driven smoothly along `Z` by the `Plug Engagement & Locking Collar` slider (`0% Unplugged` -> `50% Inserted in Keyway` -> `100% Collar Locked & Switch ON`).

- `cableGlandsEarth` (Badge `CG` · Bottom Brass Stuffing Tubes, EMC Clamps & Copper PE Bar):
  * Lower cable termination chamber with incoming `3×240 mm²` 440 V feeder cables, stress boots, 12 brass deck stuffing glands, and a full-width bolted copper Protective Earth (`PE`) busbar connected to the hull pad.

2. MATHEMATICAL & ELECTRICAL MODEL (Drive from Master Inputs):
- Master Input 1: Reefer Plug Engagement & Rotary Interlock (`s_plug` from `0.0` Unplugged to `1.0` Plugged & Rotary Interlock ON).
- Master Input 2: Active Reefer Container Bays (`1` to `8` containers online) & Cargo Box Setpoint Mode (`Chilled +2 °C Modulating` vs `Deep Frozen -25 °C Pull-Down`).
- Master Input 3: Fault Simulation Button (`Inject 45 mA Moisture Earth Leakage on Socket #3` -> trips Socket #3 RCM in `< 30 ms` without tripping the main 1,600 A incomer!).
- Exact Equations (Show in `Kinematic & IEC Proof` modal and live HUD):
  * Per-Container Electrical Draw: Rated $11.5\text{ kW}$ pull-down / $6.2\text{ kW}$ holding at $440\text{ V}$, $\cos\varphi = 0.84 \implies I_{socket} = P / (\sqrt{3} \cdot 440 \cdot \cos\varphi) = 18.0\text{ A}$ pull-down ($9.7\text{ A}$ holding).
  * Diversity & Total Bus Load (8 Sockets): $P_{total} = N_{active} \cdot P_{unit} \cdot k_{div}$, plus 5th & 7th harmonic current distortion ($\text{THD}_I \approx 14.5\%$) from container compressor VFDs.
  * Earth-Leakage Protection (IEC 60092): Vector sum $\mathbf{I}_{L1} + \mathbf{I}_{L2} + \mathbf{I}_{L3} = \mathbf{I}_{\Delta}$; trips individual MCCB shunt coil when $I_{\Delta} \ge 30\text{ mA}$ within $t \le 28\text{ ms}$.

3. FLOOR-SAFE EXPLODED VIEW VECTORS (`y >= 0` strictly):
- `enclosureFrame`: `(0, 0, 0)`
- `copperBusbars`: `(0, 0.45, -0.52)`
- `incomerAcb`: `(-0.42, 0.35, 0.55)`
- `mccbFeeders`: `(-0.35, 0.12, 0.38)`
- `reeferSockets`: `(0.42, 0.20, 0.38)`
- `containerPlugs`: `(0.42, 0.20, 0.92)`
- `cableGlandsEarth`: `(0, 0.05, -0.60)` (never below `y = 0`!)

4. LEFT & RIGHT DIVIDED CALLOUT LABELS (4 Left, 3 Right with Long SVG Leader Lines):
- Left (`side: 'left'`): `EF · IP56 Marine Steel Enclosure`, `IA · 1,600 A 440 V Incomer ACB`, `MC · 32 A MCCBs & 30 mA RCMs`, `CG · Brass Glands & Copper PE Bar`.
- Right (`side: 'right'`): `CB · 440 V 3-Phase Copper Busbars`, `RS · Interlocked 440 V 32 A Sockets`, `CP · Watertight Reefer Plugs & Cables`.

5. RIGHT INSPECTOR TELEMETRY CANVASES:
- Canvas 1: **Container Pull-Down Thermal & Power Profile (Box Temp °C & kW Draw vs Time)**.
- Canvas 2: **440 V 3-Phase Current Waveform with VFD Harmonic Ripple & 30 mA RCM Threshold**.

Apply all rules from `marine-cad-digital-twin-builder v2.1.0`. Output the complete, standalone HTML file.
```

---

## Prompt 4: 6.6 kV Water-Cooled Multi-Pulse PWM Propulsion Frequency Converter / VFD (`propulsion_vfd.html`)

Target file in app: `public/teardowns/propulsion_vfd.html`

```markdown
/marine-cad-digital-twin-builder Build the Marine 6.6 kV / 6,000 kW (6.0 MW) Water-Cooled Multi-Pulse PWM Propulsion Variable Frequency Drive (Propulsion VFD Lineup: Input Isolation & Pre-Charge Bay, 24-Pulse Diode/AFE Rectifier, DC-Link Capacitor Bank, Press-Pack IGBT Inverter Stacks, and Deionized Water Cooling Skid) as an interactive, standalone 3D digital twin simulator that users can operate and take apart.

Reference standards: IEC 60092-501 (Electric Propulsion Plant), IEC 61800-4 (Medium-Voltage Adjustable Speed Power Drive Systems above 1 kV), and DNV Electric Propulsion Rules.

1. GEOMETRY & 7 SELECTABLE SUBSYSTEMS (Build procedurally in true marine scale: 4-Bay Lineup Width 2800 mm, Depth 1250 mm, Height 2250 mm):

- `cabinetLineup` (Badge `CL` · 4-Bay Form 4b Marine Drive Enclosure & Key-Interlocked Doors):
  * 4-bay bolted marine steel lineup (`#c9d2db` panels, `#9aa8b6` posts, top pressure-relief flaps, and anti-vibration base frame `#738291`):
    - Bay 1: Input Earthing, Pre-Charge & Control Rack
    - Bay 2: 24-Pulse Rectifier & DC-Link Chokes
    - Bay 3: Medium-Voltage IGBT Inverter Phase-Leg Towers (`U, V, W`)
    - Bay 4: Deionized Water Heat Exchanger, Dual Pumps & Deionizer Cartridge Skid
  * Front doors feature **true extruded cutout viewing windows** (`THREE.Shape` + `shape.holes` + `THREE.ExtrudeGeometry`, zero Z-fighting), Castell safety key locks, and an HMI operator touchscreen panel.
  * Included in `cutawayMeshes` so `Cutaway X-Ray` turns the front/side doors into clear glass.

- `rectifierStacks` (Badge `RS` · 24-Pulse Phase-Shifted Rectifier Bridges & Pre-Charge Contactor):
  * Four 6-pulse series/parallel diode/thyristor rectifier stacks (`4 × 6 = 24-pulse` harmonic cancellation architecture, `#8796a5` heatsinks with `#a6534c` epoxy insulators and copper bus links) fed by 4 phase-shifted secondary windings (`-22.5°, -7.5°, +7.5°, +22.5°`), plus a heavy DC pre-charge resistor bank and bypass contactor.

- `dcLinkBank` (Badge `DC` · 9,300 V DC-Link Polypropylene Film Capacitors & Laminated Busbars):
  * Matrix of 24 cylindrical metallized polypropylene film capacitors (`#e2e8f0` / `#9aa8b6` cans) mounted across low-inductance laminated positive/neutral/negative (`+DC / NP / -DC`) copper busplates (`#d47a42`), with active crowbar/bleeder discharge resistors and voltage transducers.

- `igbtInverter` (Badge `IG` · 3-Phase NPC Multilevel Water-Cooled IGBT Power Modules):
  * Three vertical phase-leg towers (`Phase U`, `Phase V`, `Phase W`) of 3-Level Neutral-Point-Clamped (`3L-NPC`) medium-voltage IGBT/IEGT power modules with aluminium water-cooled cold plates, fiber-optic gate-driver boards (with flashing gate-pulse LEDs), and `dV/dt` output sinus filter reactors.

- `waterCooling` (Badge `WC` · Deionized Water Plate Heat Exchanger, Dual Pumps & Ion Exchanger):
  * Stainless steel brazed-plate Raw-Seawater-to-Deionized-Water heat exchanger (`#e2e8f0`), twin redundant vertical centrifugal circulation pumps (`#3b6254`), blue/red PTFE coolant manifolds feeding the IGBT cold plates, expansion vessel, and a translucent mixed-bed ion-exchange resin polishing cartridge (maintaining conductivity `< 0.5 µS/cm`).

- `busbarsFilters` (Badge `BF` · 6.6 kV Input/Output Copper Busbars, EMC Cores & dV/dt Reactors):
  * Top and bottom heavy copper busbars (`#d47a42`) with `U, V, W` phase coding, common-mode nanocrystalline EMC chokes, and bottom outgoing 5.6 kV variable-frequency motor cable terminations.

- `controlRack` (Badge `CR` · Direct Torque / Vector Control DSP Rack & Fiber-Optic Ring):
  * Swing-frame 19-inch marine electronics rack in Bay 1 with Field-Oriented Vector Control DSP blades, fiber-optic firing link cables, and door-mounted color HMI panel with Emergency Stop mushroom button.

2. MATHEMATICAL & ELECTRICAL MODEL (Drive from Master Inputs):
- Master Input 1: Propulsion Telegraph / Speed Order $f_{out} \in [0\text{ Hz}, 60.0\text{ Hz}]$ (corresponding to `0%` Stop to `100%` Full Ahead `6,000 kW` / `145 RPM` shaft speed).
- Master Input 2: DC-Link Pre-Charge & Drive State (`ISOLATED / DISCHARGED 0 V` -> `PRE-CHARGING` -> `READY 9,330 V DC` -> `RUNNING PWM`).
- Master Input 3: Coolant Conductivity / Pump Redundancy Toggle (`Pump 1 Duty` vs `Pump 2 Standby Auto-Changeover`).
- Exact Equations (Show in `Kinematic & IEC Proof` modal and live HUD):
  * 24-Pulse Rectified DC-Link Voltage: $V_{dc} = \frac{3\sqrt{2}}{\pi} \cdot V_{LL} = 1.3505 \times 6,600\text{ V} \approx 8,913\text{ V}$ (up to $9,330\text{ V}$ at no-load), with characteristic harmonics limited to $h = 24k \pm 1$ ($23\text{rd}, 25\text{th}$, $\text{THD}_I < 3.2\%$).
  * PWM Modulation Index & Scalar/Vector $V/f$ Law: $m_a = f_{out} / 60\text{ Hz} \in [0, 1.0]$; Fundamental RMS Output Line Voltage $V_{out,LL} = m_a \cdot 5,600\text{ V}$.
  * Propeller Cube-Law Power Load: $P_{load}(f_{out}) = 6,000\text{ kW} \times (f_{out} / 60)^{3}$; IGBT & Rectifier Thermal Loss dissipated into Deionized Water: $Q_{loss} = 0.018 \cdot P_{load} + 18\text{ kW}$ ($\approx 126\text{ kW}$ heat rejection at full load).
  * Safety Interlock: Opening cabinet doors or racking out is blocked until the DC-Link capacitor bank discharges below $50\text{ V DC}$!

3. FLOOR-SAFE EXPLODED VIEW VECTORS (`y >= 0` strictly):
- `cabinetLineup`: `(0, 0, 0)`
- `controlRack`: `(-0.85, 0.15, 0.65)`
- `rectifierStacks`: `(-0.32, 0.25, 0.55)`
- `dcLinkBank`: `(0.15, 0.45, -0.55)`
- `igbtInverter`: `(0.32, 0.35, 0.60)`
- `waterCooling`: `(0.90, 0.12, 0.50)`
- `busbarsFilters`: `(0, 0.78, -0.45)`

4. LEFT & RIGHT DIVIDED CALLOUT LABELS (4 Left, 3 Right with Long SVG Leader Lines):
- Left (`side: 'left'`): `CL · 4-Bay Form 4b Drive Enclosure`, `CR · Vector Control DSP & Fiber Rack`, `RS · 24-Pulse Rectifier Bridges`, `DC · 9.3 kV DC-Link Capacitor Bank`.
- Right (`side: 'right'`): `BF · 6.6 kV Busbars & dV/dt Filters`, `IG · 3L-NPC Water-Cooled IGBT Stacks`, `WC · Deionized Water Cooling Skid`.

5. RIGHT INSPECTOR TELEMETRY CANVASES:
- Canvas 1: **3-Level NPC PWM Line-to-Line Voltage Stepped Waveform & Filtered Sinusoidal Motor Current** (dynamically scaling frequency $f_{out}$ and amplitude $m_a$ with the Speed Order slider!).
- Canvas 2: **DC-Link Voltage ($V_{dc}$), IGBT Junction Temp ($^\circ\text{C}$), and Coolant Conductivity ($\mu\text{S/cm}$) Telemetry**.

Apply all rules from `marine-cad-digital-twin-builder v2.1.0`. Output the complete, standalone HTML file.
```

---

## Prompt 5: 5.6 kV / 6,000 kW TEWAC Marine Electric Propulsion Motor (`prop_motor.html`)

Target file in app: `public/teardowns/prop_motor.html`

```markdown
/marine-cad-digital-twin-builder Build the Marine 5.6 kV / 6,000 kW (6.0 MW) Slow-Speed Synchronous / Induction Electric Propulsion Motor (TEWAC — Totally Enclosed Water-to-Air Cooled, Direct-Drive 0–145 RPM) as an interactive, standalone 3D digital twin simulator that users can operate and take apart.

Reference standards: IEC 60092-501 (Electric Propulsion Plant), IEC 60034-1 (Rotating Electrical Machines), and DNV Pt.4 Ch.8 Electrical Propulsion.

1. GEOMETRY & 7 SELECTABLE SUBSYSTEMS (Build procedurally in true marine scale: Length 4200 mm, Width 2600 mm, Height 3150 mm):

- `statorFrame` (Badge `SF` · Heavy Welded Box-Girder Stator Frame, End-Shields & SeatingFeet):
  * Massive octagonal/cylindrical welded marine steel stator frame (`#3b6254` marine sage enamel) with external axial structural ribs, bolted split end-shields (`DE` Drive-End and `NDE` Non-Drive-End), inspection manholes, and heavy side mounting feet resting on structural hull foundation girders (`#738291`) with resin chocks.
  * Included in `cutawayMeshes` so `Cutaway X-Ray` turns the upper stator shell and cooler casing into clear glass.

- `statorCoreCoils` (Badge `SC` · Laminated Silicon-Steel Stator Core & 5.6 kV Form-Wound VPI Coils):
  * Segmented laminated silicon-steel stator core with radial ventilation ducts.
  * 5.6 kV Vacuum-Pressure Impregnated (VPI) mica-insulated form-wound copper diamond coils (`#d47a42` with `#a6534c` epoxy end-winding bracing rings), PT100 slot RTDs, and copper phase collection rings.

- `rotorShaft` (Badge `RS` · Forged Alloy-Steel Rotor Shaft, Rotor Poles/Cage & Forged Coupling Flange):
  * Single monolithic rotating group (`rotorAssemblyGroup` rotating strictly around its concentric `Z` shaft axis — zero coin-wobble!):
    - Heavy forged alloy-steel shaft (`#e2e8f0`, diameter 480 mm) with integral forged aft coupling flange (`12` fitted coupling bolts) and forward shaft-grounding brush slip ring + optical encoder disc.
    - Laminated rotor spider core with salient/squirrel-cage copper damper bars, end-rings, and axial cooling fan blades.

- `sleeveBearings` (Badge `SB` · Forward & Aft Pedestal White-Metal Sleeve Bearings & Lube Rings):
  * Forward (`NDE`) and Aft (`DE`) spherically seated, split white-metal (Babbitt) hydrodynamic journal bearings (`#8796a5` housings) mounted on the end-shields/pedestals, complete with brass oil-lifting rings, sight glasses, labyrinth shaft seals, and pressurized lube-oil supply/drain piping (`#d8b25c`).

- `tewacCooler` (Badge `TC` · Top-Mounted TEWAC Double-Tube Air-to-Water Heat Exchanger & Blowers):
  * Top-mounted Totally Enclosed Water-to-Air Cooled (`TEWAC`) rectangular housing (`#c9d2db` / `#9aa8b6`) containing CuNi 90/10 double-wall safety cooling tube bundles, bronze water boxes (`#b8804c`), leak-detection drain trap, and twin motorized centrifugal circulation blowers forcing cooled air in a closed loop through the motor.

- `terminalBox` (Badge `TB` · Side-Mounted IP56 5.6 kV Phase-Segregated Terminal Box & CTs):
  * Phase-segregated medium-voltage terminal box mounted on the starboard stator flank with shedded porcelain standoff insulators (`#b35d56`), heavy copper busbars (`U1, V1, W1`), differential protection CTs (`ANSI 87M`), and surge capacitors.

- `exciterBrushes` (Badge `EB` · Brushless Exciter, Shaft Earthing Silver-Graphite Brushes & Encoder):
  * NDE brushless exciter armature & rotating rectifier bridge, plus the insulated shaft-voltage earthing brush holder (preventing VFD common-mode bearing fluting currents) and hollow-shaft incremental speed/position encoder.

2. MATHEMATICAL & KINEMATIC MODEL (Drive from Master Inputs):
- Master Input 1: Shaft Speed Order $n_{rpm} \in [0\text{ RPM}, 145\text{ RPM}]$ (reversible: Astern $-100\text{ RPM}$ to Ahead $+145\text{ RPM}$).
- Master Input 2: Sea State / Hull Fouling Torque Load Multiplier ($80\%$ Calm Sea to $115\%$ Heavy Weather).
- Exact Equations (Show in `Kinematic & IEC Proof` modal and live HUD):
  * Synchronous Electrical Frequency (12-Pole Machine, $p = 6$ pole pairs): $f_{elec} = \frac{p \cdot |n_{rpm}|}{60} = \frac{6 \cdot 145}{60} = 14.5\text{ Hz}$ rated (or 8-pole $f_{elec} = 9.67\text{ Hz}$).
  * Shaft Mechanical Torque: $\tau_{shaft} = \frac{P_{mech} \cdot 60}{2\pi \cdot n_{rpm}}$; at rated $P_{mech} = 6,000\text{ kW}$ and $n_{rpm} = 145\text{ RPM}$:
    $$\tau_{rated} = \frac{6,000,000 \times 60}{2\pi \times 145} = 395.1\text{ kN}\cdot\text{m}$$
  * Propeller Load Law: $\tau(n) = \tau_{rated} \cdot (n / 145)^2 \cdot k_{sea}$; $P_{mech}(n) = \tau(n) \cdot \omega_m$.
  * TEWAC Closed-Loop Heat Balance: Stator & rotor losses $P_{loss} \approx 180\text{ kW}$ at full load; internal air enters cooler at $68\text{ }^\circ\text{C}$ and exits at $40\text{ }^\circ\text{C}$ into $32\text{ }^\circ\text{C}$ LT freshwater cooling loop.

3. FLOOR-SAFE EXPLODED VIEW VECTORS (`y >= 0` strictly):
- `statorFrame`: `(0, 0, 0)`
- `tewacCooler`: `(0, 0.92, 0)` (lifts vertically above stator)
- `statorCoreCoils`: `(0, 0.32, -0.55)`
- `rotorShaft`: `(0, 0.22, 1.15)` (draws out axially along `+Z` clear of stator bore)
- `sleeveBearings`: `(0, 0.12, 1.65)`
- `terminalBox`: `(0.85, 0.18, 0)`
- `exciterBrushes`: `(0, 0.22, -1.25)`

4. LEFT & RIGHT DIVIDED CALLOUT LABELS (4 Left, 3 Right with Long SVG Leader Lines):
- Left (`side: 'left'`): `TC · TEWAC Air-to-Water Cooler`, `SF · Ribbed Box-Girder Stator Frame`, `SC · 5.6 kV Form-Wound VPI Coils`, `EB · Brushless Exciter & Shaft Earth`.
- Right (`side: 'right'`): `TB · IP56 5.6 kV Terminal Box & 87M CTs`, `RS · Forged 395 kNm Rotor & Flange`, `SB · Pedestal White-Metal Bearings`.

5. RIGHT INSPECTOR TELEMETRY CANVASES:
- Canvas 1: **Torque ($\text{kN}\cdot\text{m}$) & Shaft Power ($\text{MW}$) vs RPM Curve** with live operating dot.
- Canvas 2: **3-Phase VFD-Fed Stator Current Waveforms ($\theta_{elec} = p \cdot \theta_{mech}$) & Bearing Oil Temp**.

Apply all rules from `marine-cad-digital-twin-builder v2.1.0`. Output the complete, standalone HTML file.
```

---

## Prompt 6: Main Propulsion Shaftline, Thrust Block, Stern Tube Seals & 5-Blade NAB Propeller (`prop_shaft.html`)

Target file in app: `public/teardowns/prop_shaft.html`

```markdown
/marine-cad-digital-twin-builder Build the Marine Main Propulsion Shaftline, Michell Tilting-Pad Thrust Bearing Block, Oil-Lubricated Stern Tube with Forward & Aft Simplex Lip Seals, and 5-Blade High-Skew Nickel-Aluminium-Bronze (NAB) Fixed-Pitch Propeller (`0–145 RPM`, `6,000 kW` / `395 kNm` Torque, `520 kN` Axial Thrust) as an interactive, standalone 3D digital twin simulator that users can operate and take apart.

Reference standards: DNV Pt.4 Ch.4 (Rotating Propulsion Shafting & Propellers), IACS UR M68 (Shafting Alignment & Stern Tube Bearings), and MARPOL Annex I / EAL Stern Tube Sealing Systems.

1. GEOMETRY & 7 SELECTABLE SUBSYSTEMS (Build procedurally in true marine scale: Shaftline Length 5200 mm, Propeller Diameter 2400 mm):

- `shaftAndFlanges` (Badge `SF` · Forged Intermediate & Tailshaft, Integral Collars & Muff Coupling):
  * Single monolithic rotating group (`mainShaftGroup` rotating concentrically around the longitudinal `Z` axis — zero coin-wobble!):
    - Forged intermediate shaft (`#e2e8f0`, diameter 420 mm) with integral forged thrust collar (`diameter 780 mm`), bolted 12-bolt coupling flange, hydraulic SKF-style oil-injection sleeve coupling, and tapered tailshaft (`1:15` taper cone with keyless hydraulic nut).
    - Copper slip-ring band with silver-graphite passive/active Shaft Earthing Device (`SED` < 50 mV hull potential) and torsional optical torque-meter rings.

- `thrustBearing` (Badge `TB` · Michell Tilting-Pad Main Thrust Block & Hull Seating Girder):
  * Heavy cast-steel main thrust bearing housing (`#3b6254` marine sage green) bolted to reinforced double-bottom hull seating girders (`#738291`) with Chockfast resin chocks.
  * Internal ahead and astern rings of 8 kidney-shaped white-metal tilting thrust pads (`#d8b25c` / `#e2e8f0`) embracing the rotating shaft thrust collar, plus pressurized lube-oil spray nozzles and load-cell thrust pads.
  * Included in `cutawayMeshes` so `Cutaway X-Ray` turns the upper thrust block casing and stern tube boss into translucent glass.

- `sternTubeBoss` (Badge `ST` · Aft Peak Bulkhead, Cast Stern Frame Boss & White-Metal Bushes):
  * Aft Peak watertight collision bulkhead plate (`#9aa8b6`) and heavy cast-steel stern frame bossing (`#738291`) housing the press-fit forward and aft centrifugally cast white-metal (Babbitt) oil-lubricated stern tube bearing bushes (`L/D = 2.0` aft bush) with axial oil distribution grooves.

- `simplexSeals` (Badge `SS` · Forward Dry-Side & Aft Sea-Side Multi-Lip Elastomeric Stern Tube Seals):
  * Aft Simplex-Compact 4-ring elastomeric lip seal assembly (`Rings #1, #2` seawater barrier, `Ring #3, #3S` lube-oil barrier with void monitoring chamber) running on a chrome-steel ceramic-coated shaft liner, complete with cast-bronze rope guard and sacrificial zinc anode ring.
  * Forward dry-side 2-ring stern tube seal with circulation cooling loop at the engine room bulkhead.

- `lubeHeaderSystem` (Badge `LH` · Dual Gravity Lube-Oil Header Tanks, Cooler & Air-Control Unit):
  * Elevated High-Level and Low-Level gravity stern-tube lube-oil header tanks (`#c9d2db` with level sight glasses and low-level float switches), shell-and-tube lube oil cooler (`#b8804c`), duplex filter, and compressed-air pressure-compensating control panel maintaining stern tube oil pressure `0.3 bar` above external seawater head.

- `nabPropeller` (Badge `PR` · 5-Blade High-Skew Nickel-Aluminium-Bronze Propeller & Fairing Cone):
  * Attached as a child of `mainShaftGroup` so it rotates in exact lockstep with the tailshaft!
  * Precision-sculpted 5-blade high-skewed fixed-pitch marine propeller (`#d8b25c` polished Nickel-Aluminium-Bronze, `Cu3` alloy) with cambered hydrofoil blade sections, heavy boss hub, and bolted streamlined aft fairing cap cone (`cone`).

- `slipstreamWake` (Badge `SW` · Helical Propeller Slipstream Vortex & Axial Thrust Wake):
  * Dynamic 5-helix tip-vortex streamlines and axial thrust rings trailing aft of the 5 propeller blades whose rotational pitch velocity and opacity scale directly with shaft RPM and advance ratio $J$.

2. MATHEMATICAL & KINEMATIC MODEL (Drive from Master Inputs):
- Master Input 1: Shaft Speed Order $n_{rpm} \in [-100\text{ RPM (Full Astern)}, 0\text{ RPM}, +145\text{ RPM (Full Ahead)}]$.
- Master Input 2: Vessel Draft / Seawater Submergence Depth $h_{draft} \in [6.0\text{ m Ballast}, 11.5\text{ m Scantling Draft}]$.
- Master Input 3: Shaft Turning Gear Interlock Toggle (`Disengaged` vs `Engaged` — engaging turning gear locks main shaft drive and rotates shaft at `0.5 RPM` for maintenance).
- Exact Equations (Show in `Kinematic & IEC Proof` modal and live HUD):
  * Hydrodynamic Propeller Thrust & Torque:
    $$T_{thrust} = K_T \cdot \rho_{sw} \cdot n^2 \cdot D^4 = 520\text{ kN}\text{ (53.0 tonnes)}\text{ at }145\text{ RPM}$$
    $$Q_{torque} = K_Q \cdot \rho_{sw} \cdot n^2 \cdot D^5 = 395.1\text{ kN}\cdot\text{m}\text{ at }145\text{ RPM}\text{ }(P_D = 2\pi n Q = 6,000\text{ kW})$$
  * Michell Tilting-Pad Specific Bearing Pressure:
    $$p_{pad} = \frac{T_{thrust}}{A_{pads}} = \frac{520,000\text{ N}}{0.215\text{ m}^2} = 2.42\text{ MPa}\text{ (24.2 bar, well below 3.5 MPa white-metal limit)}$$
  * Hydrodynamic Oil Film Thickness (Sommerfeld / Reynolds lubrication): $h_{min} \propto \sqrt{\frac{\mu \cdot \omega}{p_{pad}}} \approx 62\text{ }\mu\text{m}$ at $145\text{ RPM}$.
  * Stern Tube Seal Differential Pressure Balance: Seawater head $P_{sea} = \rho_{sw} g h_{draft} / 10^5 = 1.16\text{ bar}$ at $11.5\text{ m}$ draft $\implies$ Header tank maintains $P_{oil} = P_{sea} + 0.30\text{ bar} = 1.46\text{ bar}$ so seawater can never ingress into the stern tube bearing!

3. FLOOR-SAFE EXPLODED VIEW VECTORS (`y >= 0` strictly):
- `sternTubeBoss`: `(0, 0, 0)` (reference hull bossing on plinth)
- `thrustBearing`: `(0, 0.35, -0.75)`
- `shaftAndFlanges`: `(0, 0.45, -0.35)`
- `simplexSeals`: `(0, 0.25, 0.65)`
- `nabPropeller`: `(0, 0.45, 1.25)` (slides aft along `+Z` off the tailshaft taper cone)
- `lubeHeaderSystem`: `(-0.85, 0.55, 0)`
- `slipstreamWake`: `(0, 0.45, 1.75)`

4. LEFT & RIGHT DIVIDED CALLOUT LABELS (4 Left, 3 Right with Long SVG Leader Lines):
- Left (`side: 'left'`): `LH · Gravity Lube Header & Cooler`, `TB · Michell Tilting-Pad Thrust Block`, `SF · Forged Shaft & SED Earthing Ring`, `ST · Stern Tube & White-Metal Bushes`.
- Right (`side: 'right'`): `SS · Aft 4-Ring Simplex Lip Seals`, `PR · 5-Blade Skewed NAB Propeller`, `SW · Helical Slipstream Vortex`.

5. RIGHT INSPECTOR TELEMETRY CANVASES:
- Canvas 1: **Propeller Open-Water Curve ($T_{thrust}\text{ kN}$, $Q_{torque}\text{ kNm}$ & Oil Film $\mu\text{m}$ vs Shaft RPM)**.
- Canvas 2: **Stern Tube Seal Differential Pressure ($P_{oil}$ vs $P_{sea}$ bar) & Thrust Pad Temperature ($^\circ\text{C}$)**.

Apply all rules from `marine-cad-digital-twin-builder v2.1.0`. Output the complete, standalone HTML file.
```
