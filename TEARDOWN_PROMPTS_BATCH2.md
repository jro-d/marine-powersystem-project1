# Marine 3D Digital Twin & Teardown Prompts — Batch 2 (`v2.1.0` Specification)

Each prompt below is self-contained and embeds the full **`marine-cad-digital-twin-builder` (`v2.1.0`)** specification (including native-color ghost isolation, smooth `4.2%` non-jumping wheel zoom, and divided Left/Right callout columns with long horizontal SVG leader lines).

### Equipment Mapping & Target Filenames
Because multiple pump nodes in the simulator share the same mechanical design, **only 2 pump prompts** are needed to cover all 7 fluid pumps (`cooling1`, `cooling2`, `fire1`, `fire2`, `eFire`, `ballast`, `bilge`):

1. **Horizontal Centrifugal Pump Skid (`cooling1`, `cooling2`, `fire1`, `fire2`, `eFire`)** → `public/teardowns/centrifugal_pump.html` *(1 model covers all 5 Sea Water Cooling & Fire Pumps)*
2. **Ballast / Bilge Pump & 15 ppm OWS Skid (`ballast`, `bilge`)** → `public/teardowns/ballast_ows_pump.html` *(1 model covers both Ballast & Bilge/OWS pumping)*
3. **Navigation Bridge Console & S-Band Radar (`nav`)** → `public/teardowns/nav_bridge.html`
4. **440 V / 220 V Marine Galley & SOLAS Shunt-Trip (`galley440`, `galleySmall`)** → `public/teardowns/galley.html`
5. **24 V DC Battery Bank & Float/Boost Charger UPS (`eRadio`)** → `public/teardowns/battery_24v.html`

---

## 1. Horizontal Marine Centrifugal Pump & 440 V Motor Skid (`cooling1`, `cooling2`, `fire1`, `fire2`, `eFire`)

```markdown
Build a complete, standalone, single-file `index.html` 3D interactive CAD Digital Twin and Exploded Teardown Viewer for a **440 V, 3-Phase, 60 Hz, 75 kW Horizontal End-Suction Marine Centrifugal Pump & TEFC Induction Motor Skid (Sea Water Cooling & Fire Main Service)** using Three.js (`v0.160.0` via ES Module importmap with `OrbitControls` and `RoomEnvironment`).

Follow these exact architectural, visual, kinematic, and UI requirements:

### 1. Scene, Renderer, Camera & Smooth Clamped Zoom (MANDATORY)
- **Renderer**: `THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" })`, `ACESFilmicToneMapping`, `toneMappingExposure = 1.05`, `shadowMap.enabled = true` (`PCFSoftShadowMap`, `2048x2048`).
- **Environment & Background**: `PMREMGenerator.fromScene(new RoomEnvironment(), 0.04).texture`, light studio drafting background `0xf2f4f7` with subtle grid (`0xdde2e8` / `0xe8ecf0`).
- **Camera**: `PerspectiveCamera(35, window.innerWidth / window.innerHeight, 0.1, 100)` at `[-2.8, 2.0, 3.6]`, target `[0, 0.75, 0]`.
- **Smooth Non-Jumping Wheel Zoom**:
  - Set `controls.enableZoom = false` on `OrbitControls`.
  - Attach a custom `{ passive: false }` `wheel` listener on `renderer.domElement` that scales the camera-to-target distance by `4.2%` per scroll notch (`zoomFactor = 1 ± 0.042 * (Math.abs(clampedDelta) / 100)`), clamped between `controls.minDistance = 1.6` and `controls.maxDistance = 10.0`.

### 2. Physically Based Material Palette (`MeshStandardMaterial`)
- **Dark Slate Fabricated Skid Steel (`0x2c3a47`)**: `roughness: 0.50`, `metalness: 0.45`
- **Marine Machinery Blue-Teal Motor Finish (`0x266478`)**: `roughness: 0.36`, `metalness: 0.32`
- **Cast Nickel-Aluminum-Bronze Volute & Impeller (`0xc88a32`)**: `roughness: 0.25`, `metalness: 0.85` (seawater corrosion-resistant bronze)
- **Machined Stainless Steel Shaft & Flanges (`0xd0d7de`)**: `roughness: 0.18`, `metalness: 0.88`
- **Silicon-Carbide & Elastomer Mechanical Seal (`0x1e242b` / `0xd4af37`)**: `roughness: 0.28`, `metalness: 0.65`
- **Safety Yellow Coupling Guard (`0xeab308`)**: `roughness: 0.35`, `metalness: 0.25`

### 3. Seven Cohesive Functional Sub-Assemblies (`parts` Registry)
Every mesh must belong to one of these 7 logical sub-assemblies with `mesh.userData.partId`:

1. **`pump_skid` — Fabricated Steel Baseplate Skid & Anti-Vibration Mounts (`SK`)**:
   - Rigid welded channel-steel bedplate (`2.40 m` long along `X` × `0.18 m` high × `1.00 m` wide) with raised machined mounting pedestals for the motor (`X = -0.60 m`) and volute casing (`X = +0.65 m`), drip rim coaming, drain plug, and 6 foundation anchor bolts with resilient rubber vibration isolators.
   - **Explode Vector**: `[0, -0.40, 0]`

2. **`drive_motor` — 440 V 75 kW TEFC Squirrel-Cage Induction Motor (`MO`)**:
   - Mounted at `X = -0.60 m, Y = 0.72 m`.
   - Cylindrical cast-iron frame (`R = 0.34 m, L = 0.95 m`) with 24 radial longitudinal cooling fins, heavy mounting feet, non-drive-end (`NDE`) louvered fan cowl (`X = -1.12 m`), internal cooling fan blades, and a top-mounted `IP56` 440 V terminal box (`[-0.55, 1.15, 0]`) with brass armored cable glands and earthing stud.
   - **Explode Vector**: `[-0.85, 0.20, 0]`

3. **`shaft_coupling` — Stainless Pump Shaft, Flexible Pin-Bush Coupling & Safety Guard (`SH`)**:
   - Precision ground 316L stainless-steel pump shaft (`R = 0.055 m`) spanning from the motor drive end (`X = -0.05 m`) into the volute hub (`X = +0.68 m`), supported by a heavy-duty cast-iron bearing bracket (`X = +0.25 m`) with oil sight glass and constant-level oiler bottle.
   - Flexible elastomeric pin-and-bush shaft coupling (`X = -0.05 m`) covered by a removable perforated safety-yellow steel coupling guard (`0xeab308`).
   - **Explode Vector**: `[-0.25, 0.55, 0]`

4. **`mechanical_seal` — Cartridge Mechanical Shaft Seal & Stuffing Box Cover (`SL`)**:
   - Positioned at `X = +0.48 m, Y = 0.72 m`.
   - Rear casing stuffing-box cover plate (`R = 0.36 m`), cartridge mechanical shaft seal with silicon-carbide/tungsten-carbide stationary & rotating seal rings, stainless wave spring collar, bronze gland follower plate with 4 tightening studs, and braided copper seal-flush cooling line from the discharge throat.
   - **Explode Vector**: `[0.15, 0.45, 0.45]`

5. **`impeller` — Enclosed Backward-Curved Bronze Centrifugal Impeller (`IM`)**:
   - Positioned concentrically inside the volute at `X = +0.68 m, Y = 0.72 m`.
   - Cast nickel-aluminum-bronze enclosed centrifugal impeller (`0xc88a32`, `R = 0.28 m`) featuring 6 sculpted 3D backward-curved hydrodynamic vanes between front and rear shrouds, replaceable bronze wear rings, central keyed hub bore, and locked impeller nose nut.
   - **Continuous Rotation**: Group the impeller, pump shaft, and flexible coupling inside a rotating pivot (`rotatingGroup` at `Y = 0.72 m`) that spins smoothly around the `X`-axis when the pump is running.
   - **Explode Vector**: `[0.55, 0.25, 0.65]` (pulls out clearly so the curved bronze vanes are in full view).

6. **`volute_casing` — Spiral Cast-Bronze Volute Casing (`VC`)**:
   - Centered at `X = +0.68 m, Y = 0.72 m`.
   - Thick-walled expanding spiral volute scroll casing (`0xc88a32` or semi-transparent cutaway in X-Ray mode) with 16 perimeter casing flange bolts, casing drain plug, air vent cock, and pedestal support foot bolted to the skid.
   - **Explode Vector**: `[0.65, 0, -0.35]`

7. **`suction_discharge` — End-Suction & Top-Discharge Marine Flanged Nozzles (`SD`)**:
   - **Axial End-Suction Spool & DIN/JIS Marine Flange (`X = +1.05 m, Y = 0.72 m`)**: Flanged suction reducer nozzle with 8 bolt holes, compound vacuum/pressure gauge (`-1 to +3 bar`), and bolted flange face.
   - **Vertical Top-Discharge Throat & High-Pressure Flange (`X = +0.68 m, Y = 1.25 m`)**: Vertical discharge nozzle rising from the volute cutwater throat with a 12-bolt high-pressure flange, glycerin-filled discharge pressure gauge (`0–16 bar` with brass pigtail siphon tube), and bronze check-valve boss.
   - **Explode Vector**: `[1.10, 0.45, 0]`

### 4. Interactive Controls, Pump Speed Slider & Native-Color Ghost Isolation
- **Top-Left Header**: `440 V Marine Centrifugal Pump & Motor Skid` (`75 kW End-Suction Volute · Sea Water Cooling & Fire Main Service · 180 m³/h @ 8.5 bar`).
- **Top-Right Pill Toolbar**: `Reset View`, `Auto-Rotate`, `Toggle Labels`, `X-Ray Volute`.
- **Bottom Dock**:
  - **Explode Assembly Slider (`0%` to `100%`)**
  - **Impeller Speed Slider (`0 RPM` to `1800 RPM`, default `1760 RPM`)**: Controls the real-time rotation speed of the bronze impeller, shaft, and coupling, and updates live telemetry (`Flow: 180 m³/h · Head: 85 mLC · Current: 118 A @ 440 V`).
- **Native-Color Ghosting (CRITICAL)**: Clone `origMaterial` and `ghostMaterial` (`opacity: 0.14, transparent: true, depthWrite: false`) per mesh at init. Never overwrite material `.color` when ghosting.

### 5. Divided Left & Right Callout Columns with Long SVG Leader Lines
- Place Left column (`MO`, `SH`, `SK` at `LEFT_X = 24px`) and Right column (`SD`, `VC`, `IM`, `SL` at `RIGHT_X = window.innerWidth - 204px`) with vertical collision avoidance (`MIN_GAP = 42px`) and 2-segment SVG `<polyline>` leader lines.

Return the complete, self-contained `index.html` file.
```

---

## 2. Vertical Ballast / Bilge Pump & 15 ppm Oily Water Separator (OWS) Skid (`ballast`, `bilge`)

```markdown
Build a complete, standalone, single-file `index.html` 3D interactive CAD Digital Twin and Exploded Teardown Viewer for a **440 V Marine Vertical Ballast / Bilge Pump & IMO MEPC.107(49) 15 ppm Oily Water Separator (OWS) Skid** using Three.js (`v0.160.0` via ES Module importmap with `OrbitControls` and `RoomEnvironment`).

Follow these exact architectural, visual, kinematic, and UI requirements:

### 1. Scene, Renderer, Camera & Smooth Clamped Zoom (MANDATORY)
- **Renderer**: `THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" })`, `ACESFilmicToneMapping`, `toneMappingExposure = 1.05`, `shadowMap.enabled = true` (`PCFSoftShadowMap`, `2048x2048`).
- **Environment & Background**: `PMREMGenerator.fromScene(new RoomEnvironment(), 0.04).texture`, light studio drafting background `0xf2f4f7`.
- **Camera**: `PerspectiveCamera(35, window.innerWidth / window.innerHeight, 0.1, 100)` at `[-3.0, 2.2, 3.8]`, target `[0, 0.95, 0]`.
- **Smooth Non-Jumping Wheel Zoom**: Set `controls.enableZoom = false` and attach a custom `{ passive: false }` `wheel` listener that scales distance by `4.2%` per notch (`minDistance = 1.8`, `maxDistance = 11.0`).

### 2. Physically Based Material Palette (`MeshStandardMaterial`)
- **Marine Green Skid & OWS Vessel Finish (`0x2d6a4f`)**: `roughness: 0.38`, `metalness: 0.30`
- **Cast Bronze Vertical Pump Casing & Impeller (`0xc88a32`)**: `roughness: 0.26`, `metalness: 0.85`
- **Dark Slate Bedplate & Motor Housing (`0x2c3a47`)**: `roughness: 0.45`, `metalness: 0.50`
- **Oleophilic Stainless & Brass Coalescer Internals (`0xd4af37` / `0xd0d7de`)**: `roughness: 0.25`, `metalness: 0.82`
- **Pebble Grey PLC Control Cabinet (`0x9aa3ad`)**: `roughness: 0.40`, `metalness: 0.35`

### 3. Seven Cohesive Functional Sub-Assemblies (`parts` Registry)

1. **`pump_casing` — Cast-Bronze Vertical Centrifugal Ballast/Bilge Pump Casing (`PC`)**:
   - Mounted on the left side of the heavy steel skid (`X = -0.65 m, Y = 0.48 m`).
   - Heavy seawater-resistant cast-bronze vertical volute casing with radially opposed suction and discharge flanged branches (`DN150`), priming chamber, and compound pressure/vacuum gauges.
   - **Explode Vector**: `[-0.55, -0.15, 0]`

2. **`pump_impeller` — Double-Curvature Enclosed Bronze Impeller & Vertical Shaft (`PI`)**:
   - Nested inside `pump_casing` at `X = -0.65 m, Y = 0.48 m`.
   - Multi-vane enclosed bronze centrifugal impeller keyed to a vertical 316L stainless-steel shaft with mechanical seal cartridge. Spins continuously around the `Y`-axis when energized.
   - **Explode Vector**: `[-0.55, 0.35, 0.55]`

3. **`vertical_motor` — 440 V Vertical Flange-Mounted Drive Motor (`VM`)**:
   - Bolted atop the vertical pump lantern bracket at `X = -0.65 m, Y = 1.25 m`.
   - Vertical TEFC squirrel-cage induction motor (`0x2c3a47`) with radial cooling ribs, top drip-proof rain canopy, lifting eye bolts, and moisture-sealed 440 V terminal box.
   - **Explode Vector**: `[-0.55, 0.85, 0]`

4. **`ows_vessel` — Two-Stage Bilge OWS Coalescer Pressure Vessel (`OW`)**:
   - Mounted on the right side of the common steel skid (`X = +0.45 m, Y = 0.85 m`).
   - Vertical cylindrical welded steel pressure vessel (`R = 0.42 m, H = 1.45 m`) with dished top head, 16-bolt main inspection flange, top oil-collecting dome, ultrasonic oil/water interface sensor probe, steam/electric heating coil boss, and interconnecting flanged piping from the pump.
   - **Explode Vector**: `[0.45, -0.10, -0.25]`

5. **`coalescer_filter` — Oleophilic Coalescer Matrix Pack & Baffle Plates (`CF`)**:
   - Nested inside `ows_vessel` (`X = +0.45 m, Y = 0.85 m`).
   - Upper and lower perforated stainless baffle plates and a multi-stage corrugated oleophilic coalescer filter cartridge (`0xd4af37`) that aggregates microscopic oil droplets (`< 15 ppm`).
   - **Explode Vector**: `[0.45, 0.85, 0.35]` (lifts vertically out of the OWS pressure vessel).

6. **`ocm_monitor` — IMO 15 ppm Bilge Alarm Oil Content Monitor & 3-Way Valve (`OC`)**:
   - Mounted at the front-right of the skid (`X = +0.82 m, Y = 0.95 m, Z = +0.38 m`).
   - Optical laser scattering 15 ppm Oil Content Monitor (`OCM`) enclosure with digital ppm readout (`02.4 PPM · OVERBOARD PERMITTED`), sample flow sight tube, and a pneumatic/solenoid **3-Way Automatic Recirculation / Overboard Diversion Valve** on the effluent pipe.
   - **Explode Vector**: `[0.85, 0.25, 0.55]`

7. **`plc_panel` — Automated PLC Skid Control Console (`CP`)**:
   - Mounted on a central pedestal (`X = -0.08 m, Y = 1.15 m, Z = +0.35 m`).
   - Stainless IP55 control cabinet with glowing cyan HMI mimic screen, `PUMP RUN` / `15 PPM ALARM` / `RECIRCULATE` indicator lamps, rotary isolator switch, and emergency stop button.
   - **Explode Vector**: `[0, 0.55, 0.65]`

### 4. Interactive Controls, Native-Color Ghosting & Divided Callout Columns
- **Bottom Dock**: Explode Assembly Slider (`0%` to `100%`) + Pump & OWS Mode Toggle (`RUN NORMAL (<15 PPM)` / `SIMULATE >15 PPM OIL ALARM` which switches the 3-way valve indicator to recirculation).
- **Native-Color Ghosting**: Clone `origMaterial` and `ghostMaterial` (`opacity: 0.14`) per mesh; never overwrite `.color`.
- **Divided Left & Right Callout Columns**: Left (`VM`, `PI`, `PC` at `LEFT_X = 24px`) and Right (`CP`, `CF`, `OW`, `OC` at `RIGHT_X = window.innerWidth - 204px`) with collision avoidance (`MIN_GAP = 42px`) and long SVG `<polyline>` leader lines.

Return the complete, self-contained `index.html` file.
```

---

## 3. Navigation Bridge Integrated Console & Mainmast S-Band Radar (`nav`)

```markdown
Build a complete, standalone, single-file `index.html` 3D interactive CAD Digital Twin and Exploded Teardown Viewer for a **SOLAS Integrated Navigation Bridge Console (Dual ARPA Radar / ECDIS / Autopilot Helm / COLREG Light Control Panel) & Mainmast S-Band Slotted-Waveguide Radar Scanner** using Three.js (`v0.160.0` via ES Module importmap with `OrbitControls` and `RoomEnvironment`).

Follow these exact architectural, visual, kinematic, and UI requirements:

### 1. Scene, Renderer, Camera & Smooth Clamped Zoom (MANDATORY)
- **Renderer**: `THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" })`, `ACESFilmicToneMapping`, `toneMappingExposure = 1.05`, `shadowMap.enabled = true`.
- **Environment & Background**: `PMREMGenerator.fromScene(new RoomEnvironment(), 0.04).texture`, light studio drafting background `0xf2f4f7`.
- **Camera**: `PerspectiveCamera(35, window.innerWidth / window.innerHeight, 0.1, 100)` at `[-3.2, 2.3, 4.0]`, target `[0, 1.05, 0]`.
- **Smooth Non-Jumping Wheel Zoom**: Set `controls.enableZoom = false` and attach a custom `{ passive: false }` `wheel` listener scaling distance by `4.2%` per notch (`minDistance = 1.8`, `maxDistance = 12.0`).

### 2. Physically Based Material Palette (`MeshStandardMaterial`)
- **Matte Anti-Glare Bridge Console Slate (`0x283442`)**: `roughness: 0.55`, `metalness: 0.35`
- **Anodized Dark Aluminum Bezel & Helm Frame (`0x1b222c`)**: `roughness: 0.35`, `metalness: 0.65`
- **Marine White Radar Pedestal & S-Band Array Radome (`0xf0f4f8`)**: `roughness: 0.25`, `metalness: 0.15`
- **Glowing ARPA / ECDIS Display Screens (`0x0f293a` with `emissive: 0x22d3ee`, `emissiveIntensity: 0.35`)**
- **Brushed Stainless Steel Telegraph Levers & Hardware (`0xd8dee4`)**: `roughness: 0.20`, `metalness: 0.88`
- **Tinned Copper Bus & Dual-Feed ABT Internals (`0xd97742`)**: `roughness: 0.25`, `metalness: 0.85`

### 3. Six Cohesive Functional Sub-Assemblies (`parts` Registry)

1. **`bridge_console` — Ergonomic 3-Bay Integrated Bridge Desk Console & Helm (`BC`)**:
   - Wide 3-section angled marine bridge console (`2.40 m` wide × `1.15 m` high × `0.95 m` deep) with anti-glare overhang visor, stainless grab rails, central spoked **Autopilot Helm Wheel**, twin **Engine Order Telegraph / Azimuth Thruster Pitch Levers** on the right wing, and removable front/rear service access panels.
   - **Explode Vector**: `[0, -0.25, 0]`

2. **`arpa_ecdis_displays` — Dual 27-Inch ARPA Radar & ECDIS Multi-Function Displays (`MD`)**:
   - Flush-mounted into the angled upper console deck (`X = -0.72 m, 0.00 m, +0.72 m`):
     - Left Display: **S-Band ARPA Radar PPI Scope** with concentric range rings, heading line, and target vectors.
     - Center Display: **Conning & Rudder Angle / ROT / Speed Log Display**.
     - Right Display: **ECDIS Electronic Navigational Chart Display** with vessel trackline and safety depth contours, plus trackball & rotary encoder keyboards.
   - **Explode Vector**: `[0, 0.38, 0.45]`

3. **`colreg_light_panel` — SOLAS COLREG Navigation Light Matrix & Dual Selector Switches (`NL`)**:
   - Mounted on the left wing console panel (`X = -0.75 m, Y = 0.85 m, Z = +0.28 m`).
   - Engraved vessel silhouette mimic plate with glowing LED status points for **Masthead Forward/Aft, Port Red (`0xdc2626`), Starboard Green (`0x16a34a`), Stern White, and Not-Under-Command (NUC)** lights, accompanied by **Main / Standby Filament Rotary Selector Switches** and current-sensing filament failure monitoring cards.
   - **Explode Vector**: `[-0.55, 0.45, 0.55]`

4. **`abt_ups_module` — 220 V Automatic Bus Transfer (ABT) & 24 V DC Transitional UPS (`AB`)**:
   - Housed inside the lower console equipment bay (`Y = 0.42 m, Z = -0.05 m`), revealed when exploded or in X-Ray mode:
   - Dual-supply **Normal (220 V Bus B) / Emergency (440 V/220 V ESB)** motorized changeover contactors, solid-state `0 ms` static transfer switch, and a **24 V DC Transitional UPS Inverter & Audible Power-Loss Alarm Buzzer** (`SOLAS II-1/42 & 43`).
   - **Explode Vector**: `[0, -0.10, -0.55]`

5. **`radar_pedestal` — Mainmast Radar Scanner Pedestal & Harmonic Gearbox (`RP`)**:
   - Mounted on an elevated structural mast platform behind/above the console (`X = 0, Y = 1.55 m, Z = -0.30 m`).
   - Cast marine aluminum radar transceiver pedestal housing the magnetron/solid-state S-Band transceiver module, brushless servo motor, precision **Harmonic Reduction Gearbox**, and coaxial rotary joint.
   - **Explode Vector**: `[0, 0.55, -0.35]`

6. **`sband_scanner` — 12-Foot Aerodynamic S-Band Slotted-Waveguide Scanner Bar (`RS`)**:
   - Mounted atop `radar_pedestal` at `Y = 1.98 m, Z = -0.30 m`.
   - Streamlined `2.60 m` wide white fiberglass S-Band slotted-waveguide antenna array bar (`0xf0f4f8`) with aerodynamic end-caps, bird spikes, and rotary mounting yoke.
   - **Continuous Rotation**: Spins smoothly around the vertical `Y`-axis at `24 RPM` (`48 RPM` high-speed mode) when energized.
   - **Explode Vector**: `[0, 1.05, -0.35]`

### 4. Interactive Controls, Native-Color Ghosting & Divided Callout Columns
- **Bottom Dock**: Explode Assembly Slider (`0%` to `100%`) + Radar Scanner Speed Slider (`0 RPM` / `24 RPM Normal` / `48 RPM High-Speed HSC`).
- **Native-Color Ghosting**: Clone `origMaterial` and `ghostMaterial` (`opacity: 0.14`) per mesh; never overwrite `.color`.
- **Divided Left & Right Callout Columns**: Left (`NL`, `MD`, `BC` at `LEFT_X = 24px`) and Right (`RS`, `RP`, `AB` at `RIGHT_X = window.innerWidth - 204px`) with collision avoidance (`MIN_GAP = 42px`) and long SVG `<polyline>` leader lines.

Return the complete, self-contained `index.html` file.
```

---

## 4. 440 V / 220 V Marine Galley Switchboard, Cooking Range & SOLAS Shunt-Trip (`galley440`, `galleySmall`)

```markdown
Build a complete, standalone, single-file `index.html` 3D interactive CAD Digital Twin and Exploded Teardown Viewer for a **440 V / 220 V Marine Galley Primary Distribution Switchboard, Commercial Stainless Cooking Island (Roasting Ovens, Cast-Iron Marine Hotplates, Deep Fat Fryers & Exhaust Hood), and SOLAS II-2 Reg 9.2 Outdoor Emergency Shunt-Trip Station** using Three.js (`v0.160.0` via ES Module importmap with `OrbitControls` and `RoomEnvironment`).

Follow these exact architectural, visual, kinematic, and UI requirements:

### 1. Scene, Renderer, Camera & Smooth Clamped Zoom (MANDATORY)
- **Renderer**: `THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" })`, `ACESFilmicToneMapping`, `toneMappingExposure = 1.05`, `shadowMap.enabled = true`.
- **Environment & Background**: `PMREMGenerator.fromScene(new RoomEnvironment(), 0.04).texture`, light studio drafting background `0xf2f4f7`.
- **Camera**: `PerspectiveCamera(35, window.innerWidth / window.innerHeight, 0.1, 100)` at `[-3.2, 2.1, 4.0]`, target `[0, 0.95, 0]`.
- **Smooth Non-Jumping Wheel Zoom**: Set `controls.enableZoom = false` and attach a custom `{ passive: false }` `wheel` listener scaling distance by `4.2%` per notch (`minDistance = 1.8`, `maxDistance = 11.5`).

### 2. Physically Based Material Palette (`MeshStandardMaterial`)
- **Brushed 316 Marine Stainless Steel (`0xd4dbe2`)**: `roughness: 0.24`, `metalness: 0.82` (cooking range, fryers, ovens & exhaust canopy)
- **Switchboard Slate Enclosure (`0x3e4c59` / `0x9aa3ad`)**: `roughness: 0.42`, `metalness: 0.38`
- **Cast-Iron Hotplate Elements (`0x1e242b`, glowing `emissive: 0xea580c` when energized)**: `roughness: 0.55`, `metalness: 0.45`
- **Electrolytic Copper 3-Phase Busbars (`0xd97742`)**: `roughness: 0.22`, `metalness: 0.88`
- **SOLAS Safety Yellow (`0xfacc15`) & Emergency Red (`0xdc2626`)**: `roughness: 0.32`, `metalness: 0.15`

### 3. Six Cohesive Functional Sub-Assemblies (`parts` Registry)

1. **`galley_switchboard` — 440 V / 220 V Galley Primary Switchboard Enclosure (`GS`)**:
   - Positioned at the left of the galley assembly (`X = -0.85 m, Y = 0.95 m`).
   - Marine IP44 drip-proof steel switchboard cubicle (`0.80 m × 1.85 m × 0.55 m`) with hinged front door (extruded viewing window), digital voltmeter/ammeter (`440 V · 3-Phase`), `GALLEY POWER LIVE` / `SHUNT TRIPPED` indicator lamps, and bottom armored cable gland plate.
   - **Explode Vector**: `[-0.55, 0, -0.25]`

2. **`mccb_busbar_bank` — 3-Phase Copper Busbars & Group Feeder MCCB Bank (`MB`)**:
   - Mounted inside `galley_switchboard` (`X = -0.85 m, Y = 1.00 m`).
   - 3-phase electrolytic copper busbars (`L1, L2, L3`) with a main `250 A` Incoming Molded Case Circuit Breaker (`MCCB`) and 6 outgoing branch thermal-magnetic MCCBs feeding the Roasting Ovens (`440 V`), Deep Fat Fryers (`440 V`), Marine Range Hotplates (`440 V`), and Small Galley Appliances (`220 V`).
   - **Explode Vector**: `[-0.55, 0.25, 0.55]`

3. **`shunt_trip_relay` — SOLAS 24 V DC Electromagnetic Shunt-Trip Release Module (`SR`)**:
   - Mounted directly alongside the main incoming MCCB (`X = -0.72 m, Y = 1.22 m, Z = +0.10 m`).
   - Electromagnetic 24 V DC shunt-trip solenoid coil, mechanical trip striker bar coupled to the main MCCB toggle mechanism, and auxiliary fire-alarm interlock relay that simultaneously trips both cooking power and the galley exhaust hood fan upon emergency activation.
   - **Explode Vector**: `[-0.25, 0.48, 0.68]`

4. **`cooking_island` — Commercial Stainless Marine Range, Roasting Ovens & Deep Fryers (`CI`)**:
   - Positioned at `X = +0.35 m, Y = 0.52 m`.
   - Heavy 316 stainless-steel marine galley cooking island (`1.55 m` wide × `0.92 m` high × `0.85 m` deep) featuring:
     - **6 Square Cast-Iron Marine Boiling Plates** on top surrounded by adjustable **Stainless Storm Fiddle Rails (Sea Bars)** that prevent pots from sliding in rough seas.
     - **Twin Lower Convection Roasting Ovens** with insulated glass doors, heavy marine latches, and temperature dials (`50°C–300°C`).
     - **Twin Commercial Deep Fat Fryers** on the right bay with stainless wire baskets, high-limit thermostat capillary sensors (`230°C` auto cut-out), and oil drain valves.
   - **Explode Vector**: `[0.45, -0.15, 0]`

5. **`exhaust_canopy` — Stainless Galley Exhaust Hood, Baffle Grease Filters & Fire Damper (`EH`)**:
   - Suspended above the cooking island at `X = +0.35 m, Y = 1.68 m`.
   - Brushed stainless canopy hood with removable inclined **Labyrinth Grease Baffle Filters**, vapor-proof LED work lights, fixed wet-chemical fire extinguishing nozzles, and a top exhaust duct collar with a **SOLAS Quick-Closing Fire Damper Blade**.
   - **Explode Vector**: `[0.45, 0.65, 0]`

6. **`outdoor_shunt_station` — SOLAS II-2 Reg 9.2 Outdoor Emergency Shunt-Trip Station (`ES`)**:
   - Mounted on a bulkhead pedestal to the far left ("Outside Galley Corridor", `X = -1.55 m, Y = 1.10 m, Z = +0.35 m`).
   - High-visibility safety-yellow weatherproof enclosure (`0xfacc15`), spring-loaded transparent protective flip-up safety flap (`60%` exploded forward), and a **40 mm Red Latching Twist-to-Reset Mushroom Emergency Stop Pushbutton (`0xdc2626`)** labeled `EMERGENCY GALLEY POWER & VENTILATION SHUTDOWN — OUTSIDE GALLEY`.
   - **Explode Vector**: `[-1.05, 0.15, 0.65]`

### 4. Interactive Controls, Emergency Shunt-Trip Button & Divided Callout Columns
- **Bottom Dock**:
  - **Explode Assembly Slider (`0%` to `100%`)**
  - **Interactive `TEST SOLAS EMERGENCY SHUNT TRIP` / `RESET GALLEY ACB` Button**: Pressing this depresses the red mushroom button on the outdoor station, actuates the shunt-trip striker inside the switchboard, extinguishes the glowing orange cast-iron hotplates, and closes the exhaust hood fire damper!
- **Native-Color Ghosting**: Clone `origMaterial` and `ghostMaterial` (`opacity: 0.14`) per mesh; never overwrite `.color`.
- **Divided Left & Right Callout Columns**: Left (`ES`, `SR`, `MB`, `GS` at `LEFT_X = 24px`) and Right (`EH`, `CI` at `RIGHT_X = window.innerWidth - 204px`) with collision avoidance (`MIN_GAP = 42px`) and long SVG `<polyline>` leader lines.

Return the complete, self-contained `index.html` file.
```

---

## 5. 24 V DC Marine Battery Bank Rack & Automatic Float/Boost Charger UPS (`eRadio`)

```markdown
Build a complete, standalone, single-file `index.html` 3D interactive CAD Digital Twin and Exploded Teardown Viewer for a **SOLAS 24 V DC / 600 Ah VRLA Deep-Cycle Marine Battery Bank Rack & Dual Automatic Float/Boost Thyristor Charger Cabinet (GMDSS Radio, Navigation & Emergency Automation UPS)** using Three.js (`v0.160.0` via ES Module importmap with `OrbitControls` and `RoomEnvironment`).

Follow these exact architectural, visual, kinematic, and UI requirements:

### 1. Scene, Renderer, Camera & Smooth Clamped Zoom (MANDATORY)
- **Renderer**: `THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" })`, `ACESFilmicToneMapping`, `toneMappingExposure = 1.05`, `shadowMap.enabled = true`.
- **Environment & Background**: `PMREMGenerator.fromScene(new RoomEnvironment(), 0.04).texture`, light studio drafting background `0xf2f4f7`.
- **Camera**: `PerspectiveCamera(35, window.innerWidth / window.innerHeight, 0.1, 100)` at `[-3.0, 2.1, 3.8]`, target `[0, 0.95, 0]`.
- **Smooth Non-Jumping Wheel Zoom**: Set `controls.enableZoom = false` and attach a custom `{ passive: false }` `wheel` listener scaling distance by `4.2%` per notch (`minDistance = 1.7`, `maxDistance = 11.0`).

### 2. Physically Based Material Palette (`MeshStandardMaterial`)
- **Acid-Resistant Epoxy Dark Slate Battery Rack (`0x263238`)**: `roughness: 0.45`, `metalness: 0.40`
- **VRLA AGM Battery Cell Casings (`0x37474f` body with `0x1e88e5` flame-retardant ABS top lids)**: `roughness: 0.32`, `metalness: 0.12`
- **Tinned Electrolytic Copper Inter-Cell Busbars (`0xd97742` / `0xd8dee4`)**: `roughness: 0.20`, `metalness: 0.88`
- **Red Positive (`0xdc2626`) & Black Negative (`0x18181b`) Terminal Boots**: `roughness: 0.35`, `metalness: 0.10`
- **Pebble Grey Charger Cabinet Sheet Metal (`0x9aa3ad`)**: `roughness: 0.40`, `metalness: 0.35`

### 3. Seven Cohesive Functional Sub-Assemblies (`parts` Registry)

1. **`battery_rack` — Two-Tier Acid-Resistant Marine Battery Rack & Sea-Fastening Clamps (`BR`)**:
   - Positioned on the right side (`X = +0.42 m, Y = 0.65 m`).
   - Heavy welded angle-steel 2-tier marine battery rack (`1.35 m` wide × `1.15 m` high × `0.75 m` deep) with acid-resistant HDPE containment drip trays under both tiers, front fiberglass anti-roll sea-fastening retaining bars (preventing battery movement up to `22.5°` ship roll), ventilation louvers, and deck earthing lug.
   - **Explode Vector**: `[0.35, -0.25, 0]`

2. **`vrla_cells` — 12 × 2 V (600 Ah) VRLA AGM Deep-Cycle Marine Battery Cells (`VC`)**:
   - Arranged in two tiers of 6 cells each (`6 × 2 V` lower tier + `6 × 2 V` upper tier = `24 V DC nominal / 27.6 V float`) inside `battery_rack` (`X = +0.42 m`).
   - Tall industrial prismatic 2 V / 600 Ah Valve-Regulated Lead-Acid (`VRLA AGM`) cells with flame-arresting pressure relief vent plugs, twin heavy lead-brass M10 terminal pillars per cell, and cell numbering decals (`CELL 01` to `CELL 12`).
   - **Explode Vector**: `[0.45, 0.35, 0.45]`

3. **`dc_busbars_pos` — Positive (`+24 V`) Inter-Cell Copper Links & Main Fuse (`BP`)**:
   - Solid tinned copper inter-cell series busbars linking positive terminals with red heat-shrink insulation sleeves (`0xdc2626`), positive takeoff busbar, and a heavy-duty `250 A` NH HRC DC battery fuse in a ceramic holder.
   - **Explode Vector**: `[0.25, 0.65, 0.72]`

4. **`dc_busbars_neg` — Negative (`0 V`) Inter-Cell Copper Links & Measurement Shunt (`BN`)**:
   - Solid tinned copper negative series links with black protective boots (`0x18181b`), negative collector bar, and a precision `300 A / 60 mV` manganin brass current-measuring shunt resistor (`ammeterShunt`).
   - **Explode Vector**: `[0.68, 0.65, 0.72]`

5. **`charger_cabinet` — Dual Automatic Float/Boost Charger & UPS Distribution Cubicle (`CC`)**:
   - Positioned on the left side (`X = -0.68 m, Y = 0.95 m`).
   - Marine IP22 ventilated steel cabinet (`0.78 m × 1.85 m × 0.65 m`) with hinged front door (extruded viewing window), top cooling louvers, DC distribution circuit breakers (`GMDSS Radio`, `Gyro & Nav Aids`, `DG Starting & Governor Control`, `HV VCB Trip Coils`), and DC earth-fault insulation monitor (`> 100 kΩ OK`).
   - **Explode Vector**: `[-0.55, 0, -0.25]`

6. **`rectifier_tx` — Galvanic Isolation Transformer & 6-Pulse Thyristor (SCR) Bridge (`RT`)**:
   - Mounted inside `charger_cabinet` (`X = -0.68 m, Y = 0.78 m`).
   - 3-phase `440 V / 24 V` copper-wound galvanic isolation transformer, extruded aluminum heatsink carrying the **6-Pulse SCR Thyristor Controlled Rectifier Bridge**, DC smoothing choke inductor, and electrolytic ripple filter capacitors.
   - **Explode Vector**: `[-0.68, 0.20, 0.55]`

7. **`ammeter_panel` — Center-Zero Charge/Discharge DC Ammeter & Float/Boost Controller (`AM`)**:
   - Mounted on the upper front door of `charger_cabinet` (`X = -0.68 m, Y = 1.48 m, Z = +0.34 m`).
   - Large analog **Center-Zero DC Ammeter (`-150 A DISCHARGE ← 0 → +150 A CHARGE`)** with an animated pivoting needle (`needleMesh`), digital DC Voltmeter (`27.6 V FLOAT`), `AC SUPPLY HEALTHY` / `FLOAT CHARGE` / `BOOST CHARGE` / `BATTERY DISCHARGING` LEDs, and a rotary `FLOAT / BOOST / TEST` mode selector switch.
   - **Explode Vector**: `[-0.68, 0.55, 0.75]`

### 4. Interactive Controls, Charge/Discharge Simulation & Divided Callout Columns
- **Bottom Dock**:
  - **Explode Assembly Slider (`0%` to `100%`)**
  - **Operating Mode Selector (`FLOAT CHARGE (+18 A @ 27.6 V)` / `BOOST CHARGE (+85 A @ 28.8 V)` / `AC BLACKOUT — BATTERY DISCHARGE (-64 A @ 24.2 V)`)**: Smoothly rotates the center-zero ammeter needle between `+charge` and `-discharge` and updates the charger status LEDs and live telemetry!
- **Native-Color Ghosting**: Clone `origMaterial` and `ghostMaterial` (`opacity: 0.14`) per mesh; never overwrite `.color`.
- **Divided Left & Right Callout Columns**: Left (`AM`, `RT`, `CC` at `LEFT_X = 24px`) and Right (`BP`, `BN`, `VC`, `BR` at `RIGHT_X = window.innerWidth - 204px`) with collision avoidance (`MIN_GAP = 42px`) and long SVG `<polyline>` leader lines.

Return the complete, self-contained `index.html` file.
```
