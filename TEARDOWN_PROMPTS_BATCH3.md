# Marine 3D Digital Twin & Teardown Prompts — Batch 3 (`v2.1.0` Specification)

Each of the 9 prompts below is self-contained and embeds the full **`marine-cad-digital-twin-builder` (`v2.1.0`)** specification (native-color ghost isolation at `14%` opacity, smooth `4.2%` non-jumping wheel zoom, and divided Left/Right callout columns with long horizontal SVG `<polyline>` leader lines).

### Remaining 9 Equipment Prompts & Target Filenames
1. **Electro-Hydraulic Steering Gear Unit (`eSteer`, `steering`)** → `public/teardowns/steering_gear.html`
2. **Main Starting Air Compressor & 30-Bar Receiver Skid (`airCompressor`)** → `public/teardowns/air_compressor.html`
3. **6.6 kV High-Voltage Shore Connection & Cable Reel (`shore`)** → `public/teardowns/shore_power.html`
4. **Engine Room Heavy Axial Ventilation Fan & Fire Damper (`ventFan`)** → `public/teardowns/vent_fan.html`
5. **440 V / 600 kW SOLAS Emergency Diesel Generator (`eg`)** → `public/teardowns/edg.html`
6. **440 V SOLAS Emergency Switchboard & ABT (`eBus`, `esb`)** → `public/teardowns/esb.html`
7. **Electro-Hydraulic Pedestal Deck Cargo Crane (`crane`)** → `public/teardowns/deck_crane.html`
8. **40-Foot Integral Refrigerated Container & Nose Reefer Unit (`reeferUnitA`, `reeferUnitB`)** → `public/teardowns/reefer_container.html`
9. **440 V / 220 V Drawout Air Circuit Breaker (ACB) Switchboard (`lvBusA`, `lvBusB`, `consumerA`, `consumerB`)** → `public/teardowns/lv_acb.html`

---

## 1. Twin-Ram Electro-Hydraulic Steering Gear Unit (`eSteer`, `steering`)

```markdown
Build a complete, standalone, single-file `index.html` 3D interactive CAD Digital Twin and Exploded Teardown Viewer for a **SOLAS Ch. II-1 Reg. 29 Twin-Ram Rapson-Slide Electro-Hydraulic Marine Steering Gear Unit (`±35°` Rudder Actuator with Dual 440 V Hydraulic Power Units)** using Three.js (`v0.160.0` via ES Module importmap with `OrbitControls` and `RoomEnvironment`).

Follow these exact architectural, visual, kinematic, and UI requirements:

### 1. Scene, Renderer, Camera & Smooth Clamped Zoom (MANDATORY)
- **Renderer**: `THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" })`, `ACESFilmicToneMapping`, `toneMappingExposure = 1.05`, `shadowMap.enabled = true` (`PCFSoftShadowMap`, `2048x2048`).
- **Environment & Background**: `PMREMGenerator.fromScene(new RoomEnvironment(), 0.04).texture`, light studio drafting background `0xf2f4f7` with subtle grid (`0xdde2e8` / `0xe8ecf0`).
- **Camera**: `PerspectiveCamera(35, window.innerWidth / window.innerHeight, 0.1, 100)` at `[-3.4, 2.4, 4.2]`, target `[0, 0.85, 0]`.
- **Smooth Non-Jumping Wheel Zoom**:
  - Set `controls.enableZoom = false` on `OrbitControls`.
  - Attach a custom `{ passive: false }` `wheel` listener on `renderer.domElement` that scales the camera-to-target distance by `4.2%` per scroll notch (`zoomFactor = 1 ± 0.042 * (Math.abs(clampedDelta) / 100)`), clamped between `controls.minDistance = 1.8` and `controls.maxDistance = 12.0`.

### 2. Physically Based Material Palette (`MeshStandardMaterial`)
- **Heavy Steering Foundation Bedplate (`0x263238`)**: `roughness: 0.50`, `metalness: 0.48`
- **Marine Machinery Teal-Green Hydraulic Cylinders & Reservoir (`0x2b6e68`)**: `roughness: 0.36`, `metalness: 0.32`
- **Hard-Chrome Plated Hydraulic Rams & Rudder Stock (`0xdce3ea`)**: `roughness: 0.12`, `metalness: 0.92`
- **Forged Alloy Steel Rapson-Slide Tiller Crosshead (`0x475569`)**: `roughness: 0.35`, `metalness: 0.72`
- **Phosphor-Bronze Swivel Guide Blocks & Carrier Bearing (`0xc88a32`)**: `roughness: 0.25`, `metalness: 0.86`
- **High-Pressure Hydraulic Steel Piping & Brass Valves (`0xd4af37`)**: `roughness: 0.24`, `metalness: 0.82`

### 3. Seven Cohesive Functional Sub-Assemblies (`parts` Registry)

1. **`steering_bedplate` — Welded Hull Foundation Bedplate & Rudder Carrier Bearing (`FB`)**:
   - Massive welded box-girder steel bedplate (`2.80 m` wide × `0.24 m` high × `1.80 m` deep) with central circular pedestal housing the heavy bronze-lined **Rudder Carrier Thrust Bearing**, perimeter oil-drip coaming, foundation chocks, and 16 holding-down bolts.
   - **Explode Vector**: `[0, -0.45, 0]`

2. **`rudder_stock_tiller` — Forged Rudder Stock, Keyed Hub & Forked Rapson-Slide Tiller (`RT`)**:
   - Central vertical forged alloy-steel **Rudder Stock (`R = 0.20 m, H = 1.45 m`)** passing through the carrier bearing at `[0, 0.75, 0]`, crowned with a heavy keyed split-clamp **Forked Tiller Arm** extending forward (`+Z`) with precision-machined internal guideways and a top mechanical brass **Rudder Angle Pointer Scale (`-35° PORT ← 0° → +35° STBD`)**.
   - **Explode Vector**: `[0, 0.75, 0]`

3. **`hydraulic_rams` — Opposed Double-Acting Chrome Hydraulic Rams & Bronze Trunnion Blocks (`HR`)**:
   - Two heavy opposed horizontal cylinders (`Z = +0.55 m`) with a single through-going hard-chrome-plated **Double-Ended Hydraulic Ram (`R = 0.11 m, L = 1.95 m`)** along the `X`-axis.
   - Central phosphor-bronze **Rapson-Slide Swivel Crosshead Block** pinned to the middle of the ram that slides and pivots inside the forked tiller arm to convert linear hydraulic stroke into `±35°` rudder torque.
   - **Explode Vector**: `[0, 0.35, 0.55]`

4. **`ram_cylinders` — Twin Cast-Steel Hydraulic Cylinders & Stuffing Box Glands (`CY`)**:
   - Port (`X = -0.85 m, Z = +0.55 m`) and Starboard (`X = +0.85 m, Z = +0.55 m`) flanged cast-steel hydraulic cylinder barrels (`0x2b6e68`) with heavy 12-stud bronze stuffing-box gland followers, wiper seals, air-bleed cocks, and spherical rear trunnion mounts bolted to the bedplate.
   - **Explode Vector**: `[0, 0.05, 0.85]`

5. **`hpu_pumps` — Dual Redundant 440 V Electro-Hydraulic Power Units (`HP`)**:
   - Mounted aft of the tiller at Port (`X = -0.78 m, Z = -0.48 m`) and Starboard (`X = +0.78 m, Z = -0.48 m`):
     - **HPU No. 1 (Main 440 V Bus)** and **HPU No. 2 (SOLAS Emergency Switchboard `eSteer` Supply)**: Each comprises a horizontal 440 V / 45 kW squirrel-cage induction motor coupled to a **Hele-Shaw / Axial-Piston Variable-Delivery Hydraulic Pump**, mounted atop its own independent steel hydraulic oil reservoir tank with oil level sight glass and breather filter.
   - **Explode Vector**: `[0, 0.25, -0.75]`

6. **`manifold_valves` — Directional Proportional Solenoid Valves & Automatic Isolating Bypass Block (`MV`)**:
   - Central high-pressure steel valve chest (`[0, 0.92, -0.18]`) linking both HPUs to the port and starboard cylinders via seamless high-pressure steel cross-pipes (`210 bar`):
   - Dual proportional directional solenoid pilot valves (`SOL A / SOL B`), shock-relief safety valves (`245 bar`), and the automatic **SOLAS Leak-Isolation & Bypass Valve Block** (which isolates a ruptured cylinder/line while preserving steering on the remaining system).
   - **Explode Vector**: `[0, 0.65, -0.35]`

7. **`telemetry_follow_up` — Rotary Feedback Transmitter & Local Emergency Trick-Wheel Box (`FT`)**:
   - Mounted atop the rudder stock head and forward pedestal (`[0, 1.38, +0.15]`):
   - Geared potentiometer/synchro **Follow-Up Feedback Transmitter (`FU`)** sending actual rudder angle back to the bridge autopilot, limit switches (`±37°` hard-over cut-out), and a local chromed **Emergency Hand-Steering Trick Wheel** with pressure gauges (`0–250 bar`).
   - **Explode Vector**: `[0, 1.15, 0.25]`

### 4. Interactive Controls, Rudder Angle Slider & Native-Color Ghost Isolation
- **Top-Left Header**: `SOLAS Twin-Ram Electro-Hydraulic Steering Gear` (`Rapson-Slide ±35° Actuator · Dual 440 V HPU (Main & ESB) · 28s Hard-Over to Hard-Over`).
- **Bottom Dock**:
  - **Explode Assembly Slider (`0%` to `100%`)**
  - **Interactive Helm / Rudder Angle Slider (`-35° PORT` to `+35° STBD`, default `0° MIDSHIPS`)**: Smoothly translates the chrome hydraulic ram left/right along `X` while trigonometrically rotating the forked tiller and rudder stock by `θ` (`ramX = R_lever * Math.tan(θ)`) so the bronze crosshead slides realistically inside the tiller fork!
- **Native-Color Ghosting**: Clone `origMaterial` and `ghostMaterial` (`opacity: 0.14, transparent: true, depthWrite: false`) per mesh at init. Never mutate `.color` when ghosting.
- **Divided Left & Right Callout Columns**: Left (`FT`, `RT`, `CY`, `FB` at `LEFT_X = 24px`) and Right (`MV`, `HR`, `HP` at `RIGHT_X = window.innerWidth - 204px`) with collision avoidance (`MIN_GAP = 42px`) and long SVG `<polyline>` leader lines.

Return the complete, self-contained `index.html` file.
```

---

## 2. Main Starting Air Compressor & 30-Bar Receiver Bottle Skid (`airCompressor`)

```markdown
Build a complete, standalone, single-file `index.html` 3D interactive CAD Digital Twin and Exploded Teardown Viewer for a **440 V, 30-Bar Two-Stage Water-Cooled Reciprocating Marine Starting Air Compressor & Vertical Air Receiver Bottle Skid** using Three.js (`v0.160.0` via ES Module importmap with `OrbitControls` and `RoomEnvironment`).

Follow these exact architectural, visual, kinematic, and UI requirements:

### 1. Scene, Renderer, Camera & Smooth Clamped Zoom (MANDATORY)
- **Renderer**: `THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" })`, `ACESFilmicToneMapping`, `toneMappingExposure = 1.05`, `shadowMap.enabled = true`.
- **Environment & Background**: `PMREMGenerator.fromScene(new RoomEnvironment(), 0.04).texture`, light studio drafting background `0xf2f4f7`.
- **Camera**: `PerspectiveCamera(35, window.innerWidth / window.innerHeight, 0.1, 100)` at `[-3.2, 2.2, 4.0]`, target `[0, 1.0, 0]`.
- **Smooth Non-Jumping Wheel Zoom**: Set `controls.enableZoom = false` and attach a custom `{ passive: false }` `wheel` listener scaling distance by `4.2%` per notch (`minDistance = 1.8`, `maxDistance = 11.5`).

### 2. Physically Based Material Palette (`MeshStandardMaterial`)
- **Machinery Green Compressor Crankcase & Air Receiver Bottle (`0x2d6a4f`)**: `roughness: 0.36`, `metalness: 0.32`
- **Dark Cast-Iron Finned Cylinders & Bedplate (`0x263238`)**: `roughness: 0.45`, `metalness: 0.55`
- **Electrolytic Finned Copper Intercooler & Aftercooler Tubes (`0xd97742`)**: `roughness: 0.22`, `metalness: 0.88`
- **Marine Blue-Grey 440 V Drive Motor (`0x2b5b70`)**: `roughness: 0.38`, `metalness: 0.35`
- **Forged Brass Valves, Pressure Gauges & Relief Safety Valve (`0xd4af37`)**: `roughness: 0.24`, `metalness: 0.85`
- **Safety Yellow Perforated V-Belt Guard (`0xeab308`)**: `roughness: 0.35`, `metalness: 0.25`

### 3. Seven Cohesive Functional Sub-Assemblies (`parts` Registry)

1. **`compressor_skid` — Rigid Welded Steel Base Skid & Crankcase Oil Sump (`CS`)**:
   - Heavy welded channel-steel skid (`2.50 m` wide × `0.18 m` high × `1.30 m` deep) supporting the motor (`X = -0.75 m`), two-stage compressor crankcase (`X = +0.05 m`), and vertical 30-bar air receiver bottle (`X = +0.85 m`). Includes cast-iron compressor crankcase with oil sight glass, breather cap, and anti-vibration mounts.
   - **Explode Vector**: `[0, -0.40, 0]`

2. **`drive_motor_440v` — 440 V 30 kW TEFC Squirrel-Cage Induction Motor (`DM`)**:
   - Mounted at `X = -0.75 m, Y = 0.58 m`.
   - Ribbed cast-iron 440 V motor frame (`0x2b5b70`), top IP56 terminal box with armored cable glands, slide-rail belt-tensioning base bolts, and drive-end multi-groove V-belt sheave pulley.
   - **Explode Vector**: `[-0.75, 0.15, 0.25]`

3. **`vbelt_flywheel` — 4-Groove V-Belt Drive, Spoked Fan Flywheel & Safety Guard (`VB`)**:
   - Spanning from the motor sheave (`X = -0.75 m`) to the compressor crankshaft (`X = +0.05 m`) at `Z = +0.38 m`:
   - Large cast-iron **6-Spoke Aerofoil Cooling Flywheel Pulley (`R = 0.38 m`)** that blows cooling air across the cylinders, 4 matched rubber V-belts, and a removable safety-yellow steel mesh belt guard (`0xeab308`).
   - **Continuous Rotation**: Rotate the flywheel pulley and motor sheave smoothly when the compressor is running.
   - **Explode Vector**: `[-0.35, 0.25, 0.75]`

4. **`two_stage_cylinders` — Stepped V-Twin LP (6 Bar) & HP (30 Bar) Compression Cylinders (`TC`)**:
   - Mounted atop the compressor crankcase at `X = +0.05 m, Y = 0.95 m` in a `90°` V-twin configuration:
     - **Stage 1 Low-Pressure (`LP`) Cylinder (Left V-Bank)**: Large bore (`R = 0.20 m`) finned cast-iron cylinder with cylindrical intake air filter silencer and concentric suction/delivery reed valves.
     - **Stage 2 High-Pressure (`HP`) Cylinder (Right V-Bank)**: Smaller bore (`R = 0.12 m`) high-pressure cylinder compressing air from `6 bar` to `30 bar`, with internal cutaway/ghostable pistons and connecting rods driven by the crankshaft.
   - **Explode Vector**: `[0.05, 0.65, 0.25]`

5. **`intercooler_coil` — Finned Copper Intercooler, Aftercooler & Moisture Separator (`IC`)**:
   - Spanning across the front/rear of the V-cylinders (`X = +0.05 m, Y = 1.05 m, Z = -0.22 m`):
   - Multi-pass spiral-finned copper **Intercooler Tube Bundle (`0xd97742`)** linking the LP discharge to the HP suction, copper **Aftercooler Coil** discharging to the receiver bottle, and brass cyclone oil/water moisture separator trap.
   - **Explode Vector**: `[0.05, 0.85, -0.50]`

6. **`air_receiver_bottle` — 30-Bar Vertical Forged-Steel Starting Air Receiver Bottle (`AR`)**:
   - Mounted upright on the right side of the skid (`X = +0.85 m, Y = 1.10 m, Z = -0.10 m`).
   - Seamless green pressure vessel (`R = 0.36 m, H = 1.85 m`, `0x2d6a4f`) with hemispherical dished heads, bolted oval inspection manhole door, top brass **Main Starting Air Stop Valve** & **Spring-Loaded Safety Relief Valve (`33 bar`)**, pressure gauge (`0–40 bar`), and stencil decal (`MAIN STARTING AIR RECEIVER · 30.0 BAR · TEST 45 BAR`).
   - **Explode Vector**: `[0.75, 0.20, -0.25]`

7. **`unloader_panel` — Automatic Solenoid Unloader, Drain Trap & Local Starter Panel (`UL`)**:
   - Mounted at the front-center of the skid (`X = +0.35 m, Y = 0.65 m, Z = +0.35 m`):
   - 24 V DC **Automatic Solenoid Unloader & Condensate Purge Valve** (venting LP/HP interstage pressure on startup so the motor starts unloaded), pressure switch (`AUTO START @ 25 BAR / STOP @ 30 BAR`), and local IP55 starter box with LP/HP interstage pressure gauges.
   - **Explode Vector**: `[0.35, -0.10, 0.65]`

### 4. Interactive Controls, Compressor RPM Slider & Divided Callout Columns
- **Bottom Dock**: Explode Assembly Slider (`0%` to `100%`) + Compressor Speed Slider (`0 RPM Unloaded` to `1200 RPM Charging 30 Bar`).
- **Native-Color Ghosting**: Clone `origMaterial` and `ghostMaterial` (`opacity: 0.14`) per mesh; never overwrite `.color`.
- **Divided Left & Right Callout Columns**: Left (`VB`, `DM`, `CS` at `LEFT_X = 24px`) and Right (`IC`, `TC`, `AR`, `UL` at `RIGHT_X = window.innerWidth - 204px`) with collision avoidance (`MIN_GAP = 42px`) and long SVG `<polyline>` leader lines.

Return the complete, self-contained `index.html` file.
```

---

## 3. 6.6 kV High-Voltage Shore Connection (HVSC / Cold Ironing) & Cable Reel (`shore`)

```markdown
Build a complete, standalone, single-file `index.html` 3D interactive CAD Digital Twin and Exploded Teardown Viewer for a **6.6 kV, 3-Phase, 60 Hz, 7.5 MVA IEC/ISO/IEEE 80005-1 High-Voltage Shore Connection (HVSC / Cold Ironing) Motorized Cable Reel & Interlocked Shore Receiving Switchboard Cubicle** using Three.js (`v0.160.0` via ES Module importmap with `OrbitControls` and `RoomEnvironment`).

Follow these exact architectural, visual, kinematic, and UI requirements:

### 1. Scene, Renderer, Camera & Smooth Clamped Zoom (MANDATORY)
- **Renderer**: `THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" })`, `ACESFilmicToneMapping`, `toneMappingExposure = 1.05`, `shadowMap.enabled = true`.
- **Environment & Background**: `PMREMGenerator.fromScene(new RoomEnvironment(), 0.04).texture`, light studio drafting background `0xf2f4f7`.
- **Camera**: `PerspectiveCamera(35, window.innerWidth / window.innerHeight, 0.1, 100)` at `[-3.4, 2.3, 4.2]`, target `[0, 1.05, 0]`.
- **Smooth Non-Jumping Wheel Zoom**: Set `controls.enableZoom = false` and attach a custom `{ passive: false }` `wheel` listener scaling distance by `4.2%` per notch (`minDistance = 1.8`, `maxDistance = 12.0`).

### 2. Physically Based Material Palette (`MeshStandardMaterial`)
- **Marine Deck Grey Reel Stand & HVSC Cubicle (`0x8e99a4` / `0x2c3a47`)**: `roughness: 0.40`, `metalness: 0.38`
- **Safety Orange / Yellow Motorized Cable Reel Drum (`0xd97706`)**: `roughness: 0.34`, `metalness: 0.30`
- **Black EPR-Insulated 6.6 kV Trailing Cable (`0x18181b`)**: `roughness: 0.55`, `metalness: 0.10`
- **Electrolytic Copper Slip-Rings & Earthing Knife Blades (`0xd97742`)**: `roughness: 0.20`, `metalness: 0.88`
- **Anodized Silver-Grey IEC 80005-1 Connector Plug (`0xcbd5e1`)**: `roughness: 0.25`, `metalness: 0.80`

### 3. Seven Cohesive Functional Sub-Assemblies (`parts` Registry)

1. **`reel_drum_frame` — Motorized Marine Cable Reel Drum & Slip-Ring Collector (`RD`)**:
   - Mounted on the left side of the heavy deck skid (`X = -0.60 m, Y = 1.05 m`).
   - Twin A-frame pedestal stanchions supporting a large spoked radial **Cable Reel Drum (`R = 0.72 m, W = 0.75 m`, `0xd97706`)** and a central weatherproof **6.6 kV Copper Slip-Ring & Fiber-Optic Rotary Joint Collector Housing** that transfers power from the rotating drum to the stationary cubicle.
   - **Explode Vector**: `[-0.55, 0.15, 0]`

2. **`hv_flexible_cable` — 6.6 kV Triple-Core EPR Shielded Cold-Ironing Cable (`HC`)**:
   - Coiled in multi-layer concentric turns around `reel_drum_frame` (`X = -0.60 m, Y = 1.05 m`) with the bitter end paying out forward through a 4-roller stainless deck fairlead (`[-0.60, 0.35, +0.65]`).
   - Heavy `3 × 185 mm²` 6.6 kV flexible trailing cable containing 3 phase cores, concentric copper earth screen, 2 pilot control wires, and integrated optical fibers.
   - **Explode Vector**: `[-0.55, 0.35, 0.55]`

3. **`iec_connector_plug` — IEC/IEEE 80005-1 High-Voltage Shore Coupling Plug (`CP`)**:
   - Positioned at the forward fairlead cradle (`X = -0.60 m, Y = 0.32 m, Z = +0.82 m`).
   - Heavy cast-aluminum/stainless **IEC 80005-1 HVSC Connector Plug Head** featuring 3 silver-plated phase socket tubes (`L1, L2, L3`), central oversized ground pin, **2 shorter Early-Break Pilot Interlock Pins** (which break the safety loop before main contacts separate), and mechanical bayonet locking ring.
   - **Explode Vector**: `[-0.55, -0.15, 1.05]`

4. **`planetary_drive` — Constant-Tension Geared Spooling Drive Motor (`PD`)**:
   - Bolted to the outboard A-frame of the reel (`X = -1.15 m, Y = 0.95 m`).
   - 440 V VFD-controlled electric motor coupled to a planetary bevel reduction gearbox and electromagnetic fail-safe brake that automatically spools the cable and maintains constant tension as the ship rises/falls with the tide.
   - **Explode Vector**: `[-1.15, 0.15, 0]`

5. **`hvsc_cubicle` — 6.6 kV Shore Receiving & Synchronizing Switchboard Cubicle (`SC`)**:
   - Mounted on the right side of the deck skid (`X = +0.65 m, Y = 1.05 m`).
   - IP56 marine stainless/steel enclosure (`0.95 m × 1.95 m × 0.90 m`) with hinged front door (extruded viewing window), **Phase-Sequence & Check-Synchronizer Relay (`ANSI 25 / 47`)** with glowing cyan LCD, `SHORE CABLE CONNECTED` / `PILOT LOOP CLOSED` / `EARTH SWITCH OPEN` lamps, and red emergency shore-trip mushroom button.
   - **Explode Vector**: `[0.55, 0, -0.25]`

6. **`earth_switch_blades` — 3-Pole High-Current Earthing Knife Switch & Busbars (`ES`)**:
   - Mounted inside `hvsc_cubicle` (`X = +0.65 m, Y = 0.95 m`):
   - 3 maroon epoxy standoff bushings carrying 6.6 kV copper busbars (`L1, L2, L3`), surge arresters, and a **3-Pole Motorized/Manual Copper Knife-Blade Earthing Switch** that solidly grounds the shore cable cores to the ship's hull whenever shore power is disconnected.
   - **Explode Vector**: `[0.65, 0.25, 0.55]`

7. **`castell_interlock` — Trapped-Key Castell Interlock & Pilot Supervision Module (`CI`)**:
   - Mounted on the inner front panel of `hvsc_cubicle` (`X = +0.65 m, Y = 1.35 m, Z = +0.35 m`):
   - Brass **Castell Trapped-Key Mechanical Interlock Box** (preventing closure of the Earthing Switch while `shoreBreaker` is closed, or opening of the HVSC door while live) and the `24 V DC` Pilot Loop Continuity Relay.
   - **Explode Vector**: `[0.65, 0.55, 0.78]`

### 4. Interactive Controls, Reel Spooling & Earth Switch Toggle
- **Bottom Dock**:
  - **Explode Assembly Slider (`0%` to `100%`)**
  - **Interactive `ROTATE CABLE REEL` Toggle & `OPEN / CLOSE EARTH SWITCH` Button**: Spins the motorized drum and pivots the 3 copper earthing knife blades (`CLOSED · GROUNDED` vs `OPEN · READY FOR 6.6 kV`).
- **Native-Color Ghosting**: Clone `origMaterial` and `ghostMaterial` (`opacity: 0.14`) per mesh; never overwrite `.color`.
- **Divided Left & Right Callout Columns**: Left (`PD`, `RD`, `HC`, `CP` at `LEFT_X = 24px`) and Right (`CI`, `ES`, `SC` at `RIGHT_X = window.innerWidth - 204px`) with collision avoidance (`MIN_GAP = 42px`) and long SVG `<polyline>` leader lines.

Return the complete, self-contained `index.html` file.
```

---

## 4. Engine Room Heavy Axial Ventilation Fan & SOLAS Fire Damper (`ventFan`)

```markdown
Build a complete, standalone, single-file `index.html` 3D interactive CAD Digital Twin and Exploded Teardown Viewer for a **440 V, 45 kW Reversible Engine Room Heavy Axial Supply Ventilation Fan, Aerofoil Impeller, SOLAS Quick-Closing Fire Damper, and Local Star-Delta Starter Box** using Three.js (`v0.160.0` via ES Module importmap with `OrbitControls` and `RoomEnvironment`).

Follow these exact architectural, visual, kinematic, and UI requirements:

### 1. Scene, Renderer, Camera & Smooth Clamped Zoom (MANDATORY)
- **Renderer**: `THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" })`, `ACESFilmicToneMapping`, `toneMappingExposure = 1.05`, `shadowMap.enabled = true`.
- **Environment & Background**: `PMREMGenerator.fromScene(new RoomEnvironment(), 0.04).texture`, light studio drafting background `0xf2f4f7`.
- **Camera**: `PerspectiveCamera(35, window.innerWidth / window.innerHeight, 0.1, 100)` at `[-3.0, 2.0, 3.8]`, target `[0, 0.95, 0]`.
- **Smooth Non-Jumping Wheel Zoom**: Set `controls.enableZoom = false` and attach a custom `{ passive: false }` `wheel` listener scaling distance by `4.2%` per notch (`minDistance = 1.6`, `maxDistance = 11.0`).

### 2. Physically Based Material Palette (`MeshStandardMaterial`)
- **Hot-Dip Galvanized Steel Cylindrical Trunk Casing (`0x9aa5b1`)**: `roughness: 0.38`, `metalness: 0.62`, `side: THREE.DoubleSide`
- **Cast Marine Aluminum 8-Blade Aerofoil Impeller (`0xd8dee4`)**: `roughness: 0.20`, `metalness: 0.88`
- **Marine Blue-Teal In-Stream 440 V Motor (`0x266478`)**: `roughness: 0.36`, `metalness: 0.35`
- **SOLAS Fire-Red Quick-Closing Damper Blades & Actuator (`0xdc2626`)**: `roughness: 0.32`, `metalness: 0.25`
- **Dark Slate Starter Enclosure & Mounting Saddles (`0x2c3a47`)**: `roughness: 0.45`, `metalness: 0.48`

### 3. Six Cohesive Functional Sub-Assemblies (`parts` Registry)

1. **`fan_casing` — Heavy Galvanized Cylindrical Duct Casing & Inspection Hatch (`FC`)**:
   - Horizontal cylindrical steel ventilation trunk (`R = 0.68 m, L = 1.45 m` along `Z`-axis, centered at `[0, 1.00, 0]`) supported on twin welded deck cradle saddles.
   - Features internal aerodynamic stator guide-vane struts, hinged bolted side inspection hatch with sight glass, acoustic stiffening ribs, and external junction conduit.
   - **Explode Vector**: `[0, -0.25, 0]`

2. **`companion_flanges` — Drilled DIN/JIS Companion Duct Flanges & Wire Intake Guard (`CF`)**:
   - Front (`Z = +0.74 m`) and Rear (`Z = -0.74 m`) rolled angle-steel companion flanges (`R_outer = 0.78 m`) with 24 Bolt-M16 fasteners, neoprene air-seal gaskets, and a concentric stainless wire-mesh intake protective screen at the forward bellmouth.
   - **Explode Vector**: `[0, 0, 0.95]`

3. **`axial_impeller` — 8-Blade Adjustable-Pitch Cast-Aluminum Aerofoil Impeller (`AI`)**:
   - Centered inside the duct at `[0, 1.00, +0.18]`.
   - Precision-machined cast-aluminum hub (`R = 0.24 m`) with nose spinner cone and **8 Twisted 3D Aerofoil Blades (`R_tip = 0.64 m`)** secured by root clamping bolts.
   - **Continuous Rotation**: Spins smoothly around the `Z`-axis (`1750 RPM` scaled visual speed) when energized.
   - **Explode Vector**: `[0, 0, 0.55]`

4. **`instream_motor` — 440 V 45 kW In-Stream IP56 Marine Flange Motor (`IM`)**:
   - Mounted coaxially inside the aerodynamic stator struts at `[0, 1.00, -0.18]`.
   - Finned cylindrical Class-H insulated 440 V induction motor (`0x266478`) cooled directly by the forced-draft airstream, with sealed grease-lubricated bearings and armored power cable routed out through a hollow aerodynamic strut to the external starter box.
   - **Explode Vector**: `[0, 0, -0.55]`

5. **`fire_damper` — SOLAS Quick-Closing Multi-Blade Fire Damper & Spring Actuator (`FD`)**:
   - Bolted to the aft discharge end of the fan casing (`[0, 1.00, -0.68]`):
   - Circular damper collar housing **4 Pivoting Red Steel Fire-Damper Louver Blades (`0xdc2626`)** linked by an external tie-rod to a **Pneumatic / Spring-Return Fail-Safe SOLAS Actuator Cylinder** with a `72°C` thermal fusible link and manual remote-release lever (`OPEN 90°` in normal operation; snaps `CLOSED 0°` on fire/blackout shutdown).
   - **Explode Vector**: `[0, 0.15, -0.95]`

6. **`starter_box` — Local Star-Delta Starter, Reversing Contactor & Isolator Panel (`SB`)**:
   - Mounted on a side bracket at `[+0.88, 1.00, +0.05]`:
   - Weatherproof IP56 steel starter enclosure with lockable rotary main isolator handle, internal `Main / Star / Delta` 440 V contactors (visible when door opens on explode), thermal overload relay, ammeter (`0–100 A`), `SUPPLY / EXHAUST REVERSIBLE` selector switch, and `EMERGENCY FIRE STOP INTERLOCK` lamp.
   - **Explode Vector**: `[0.75, 0.15, 0.25]`

### 4. Interactive Controls, Airflow Speed & Fire Damper Trip Toggle
- **Bottom Dock**:
  - **Explode Assembly Slider (`0%` to `100%`)**
  - **Fan Speed Slider (`0 RPM` to `1750 RPM`)**
  - **Interactive `TRIP SOLAS FIRE DAMPER` / `RESET DAMPER` Button**: Immediately stops the impeller and rotates the 4 red fire-damper blades `90°` shut to seal the engine room ventilation trunk!
- **Native-Color Ghosting**: Clone `origMaterial` and `ghostMaterial` (`opacity: 0.14`) per mesh; never overwrite `.color`.
- **Divided Left & Right Callout Columns**: Left (`FD`, `IM`, `FC` at `LEFT_X = 24px`) and Right (`CF`, `AI`, `SB` at `RIGHT_X = window.innerWidth - 204px`) with collision avoidance (`MIN_GAP = 42px`) and long SVG `<polyline>` leader lines.

Return the complete, self-contained `index.html` file.
```

---

## 5. 440 V / 600 kW SOLAS Emergency Diesel Generator (`eg` / `EDG`)

```markdown
Build a complete, standalone, single-file `index.html` 3D interactive CAD Digital Twin and Exploded Teardown Viewer for a **SOLAS Ch. II-1 Reg. 42 & 43 Autonomous 440 V, 60 Hz, 600 kW (750 kVA), 1800 RPM High-Speed Emergency Diesel Generator (EDG) with Radiator Cooling & Dual Independent Starting Systems** using Three.js (`v0.160.0` via ES Module importmap with `OrbitControls` and `RoomEnvironment`).

Follow these exact architectural, visual, kinematic, and UI requirements:

### 1. Scene, Renderer, Camera & Smooth Clamped Zoom (MANDATORY)
- **Renderer**: `THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" })`, `ACESFilmicToneMapping`, `toneMappingExposure = 1.05`, `shadowMap.enabled = true`.
- **Environment & Background**: `PMREMGenerator.fromScene(new RoomEnvironment(), 0.04).texture`, light studio drafting background `0xf2f4f7`.
- **Camera**: `PerspectiveCamera(35, window.innerWidth / window.innerHeight, 0.1, 100)` at `[-3.4, 2.2, 4.2]`, target `[0, 0.95, 0]`.
- **Smooth Non-Jumping Wheel Zoom**: Set `controls.enableZoom = false` and attach a custom `{ passive: false }` `wheel` listener scaling distance by `4.2%` per notch (`minDistance = 1.8`, `maxDistance = 12.0`).

### 2. Physically Based Material Palette (`MeshStandardMaterial`)
- **SOLAS Emergency Caterpillar-Yellow / Amber Engine Block (`0xd97706`)**: `roughness: 0.34`, `metalness: 0.28`
- **Dark Slate Common Skid & Alternator Stator Frame (`0x263238`)**: `roughness: 0.45`, `metalness: 0.50`
- **Copper Alternator Windings & Radiator Core (`0xd97742`)**: `roughness: 0.22`, `metalness: 0.88`
- **Stainless Exhaust Heat-Shield & Turbocharger (`0xd0d7de`)**: `roughness: 0.22`, `metalness: 0.85`
- **SOLAS Red Hydraulic Accumulator & Starting Air Bottles (`0xdc2626`)**: `roughness: 0.30`, `metalness: 0.35`

### 3. Seven Cohesive Functional Sub-Assemblies (`parts` Registry)

1. **`edg_skid_tank` — Common Steel Baseframe with Integral 24-Hour Fuel Oil Belly Tank (`SK`)**:
   - Heavy welded channel-steel skid (`2.90 m` long along `X` × `0.26 m` high × `1.20 m` wide) incorporating an integral SOLAS `18-to-24 hour` diesel fuel belly tank with fuel level sight gauge, quick-closing remote fuel shut-off valve (`SOLAS II-2`), drip tray, and 8 captive spring-elastomer vibration isolators.
   - **Explode Vector**: `[0, -0.45, 0]`

2. **`diesel_v12_engine` — High-Speed 1800 RPM V12 Turbocharged Diesel Prime Mover (`EN`)**:
   - Mounted at `X = -0.25 m, Y = 0.82 m` (`0xd97706`):
   - Compact high-speed 4-stroke V12 diesel block with 12 individual cylinder head rocker covers (`6 Port + 6 Starboard` angled at `60°`), common-rail fuel injection gallery, twin spin-on lube oil & duplex fuel filters, and a `220 V` thermostatically controlled **Jacket-Water Pre-Heater** (keeping standby engine temperature at `45°C` for instant `<10s` blackout starting).
   - **Explode Vector**: `[-0.15, 0.25, 0]`

3. **`turbo_exhaust` — Twin Rear Turbochargers, Charge-Air Cooler & Insulated Exhaust Manifold (`TE`)**:
   - Mounted atop the V-valley and rear of the engine (`X = -0.35 m, Y = 1.38 m`):
   - Stainless-cladded water-cooled exhaust manifolds feeding twin high-efficiency radial turbochargers, air-to-air / water-cooled aftercooler housing, and dual heavy-duty pleated cylindrical intake air filters.
   - **Explode Vector**: `[-0.25, 0.75, 0]`

4. **`radiator_fan` — Skid-Mounted Tropical Finned Radiator & Pusher Cooling Fan (`RD`)**:
   - Mounted at the forward end of the skid (`X = -1.25 m, Y = 0.98 m`) so the EDG requires zero seawater cooling pumps (able to run even when the main engine room is flooded):
   - Vertical brass/copper finned radiator core (`1.10 m × 1.15 m`) with top expansion header tank, belt-driven **8-Blade Pusher Cooling Fan** behind a perforated safety guard, and rubber coolant hoses connected to the engine thermostat housing.
   - **Continuous Rotation**: Rotate the 8-blade radiator fan and alternator rotor smoothly when the EDG is running.
   - **Explode Vector**: `[-1.05, 0.15, 0]`

5. **`dual_starters` — SOLAS Dual Independent Starting Systems (24 V DC Electric + Hydraulic/Air Starter) (`ST`)**:
   - Mounted along the starboard side of the engine (`X = -0.20 m, Y = 0.65 m, Z = +0.52 m`):
   - **Primary Starter**: Heavy-duty `24 V DC` dual-redundant electric starter motors with dedicated AGM starter battery crate on the skid.
   - **Secondary Independent Starter (`SOLAS II-1/44`)**: Hydraulic rack-and-pinion starter motor driven by two red vertical **Nitrogen-Charged Hydraulic Piston Accumulator Bottles (`210 bar`, `0xdc2626`)** with a manual hand-jacking recharge pump and pressure gauge (`-0°C` cold-start capable).
   - **Explode Vector**: `[-0.15, 0.05, 0.75]`

6. **`brushless_alternator` — 440 V 750 kVA 4-Pole Brushless Synchronous Alternator (`AL`)**:
   - Coupled to the flywheel housing at the aft end (`X = +0.85 m, Y = 0.78 m`):
   - Cylindrical dark-slate stator frame (`R = 0.44 m, L = 0.95 m`), internal 4-pole salient-pole copper rotor with coaxial brushless exciter and rotating diode bridge (revealed when exploded), automatic voltage regulator (`AVR`), and top `440 V` main terminal box.
   - **Explode Vector**: `[0.85, 0.20, 0]`

7. **`auto_start_panel` — SOLAS Auto-Start (`<10s` Blackout Sensing) Local Control Panel (`CP`)**:
   - Mounted on vibration isolators at the aft-right corner (`X = +0.95 m, Y = 1.18 m, Z = +0.48 m`):
   - IP55 steel control cabinet with glowing microprocessor controller (`AUTO READY · BLACKOUT TIMER 0.0s · JACKET 48°C`), analog `V / Hz / RPM / Oil Bar` gauges, `AUTO / TEST / MANUAL` mode selector, and red Emergency Stop button.
   - **Explode Vector**: `[0.85, 0.55, 0.65]`

### 4. Interactive Controls, Blackout Auto-Start Simulation & Divided Callout Columns
- **Bottom Dock**:
  - **Explode Assembly Slider (`0%` to `100%`)**
  - **Engine Speed / Blackout Test Toggle (`STANDBY (0 RPM · Pre-Heated 48°C)` / `SIMULATE BLACKOUT AUTO-START (1800 RPM · 440 V 60 Hz)`)**: Spins up the radiator fan and alternator rotor to `1800 RPM` and updates the control panel telemetry!
- **Native-Color Ghosting**: Clone `origMaterial` and `ghostMaterial` (`opacity: 0.14`) per mesh; never overwrite `.color`.
- **Divided Left & Right Callout Columns**: Left (`RD`, `TE`, `EN`, `SK` at `LEFT_X = 24px`) and Right (`CP`, `AL`, `ST` at `RIGHT_X = window.innerWidth - 204px`) with collision avoidance (`MIN_GAP = 42px`) and long SVG `<polyline>` leader lines.

Return the complete, self-contained `index.html` file.
```

---

## 6. 440 V SOLAS Emergency Switchboard (ESB) & Interlock Panel (`eBus`, `esb`)

```markdown
Build a complete, standalone, single-file `index.html` 3D interactive CAD Digital Twin and Exploded Teardown Viewer for a **SOLAS Ch. II-1 440 V / 220 V Emergency Switchboard (ESB) 2-Bay Cubicle with EDG Incomer ACB, Normal/Emergency Bus-Tie Interlock ACB, and Automatic Bus Transfer (ABT)** using Three.js (`v0.160.0` via ES Module importmap with `OrbitControls` and `RoomEnvironment`).

Follow these exact architectural, visual, kinematic, and UI requirements:

### 1. Scene, Renderer, Camera & Smooth Clamped Zoom (MANDATORY)
- **Renderer**: `THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" })`, `ACESFilmicToneMapping`, `toneMappingExposure = 1.05`, `shadowMap.enabled = true`.
- **Environment & Background**: `PMREMGenerator.fromScene(new RoomEnvironment(), 0.04).texture`, light studio drafting background `0xf2f4f7`.
- **Camera**: `PerspectiveCamera(35, window.innerWidth / window.innerHeight, 0.1, 100)` at `[-2.8, 2.0, 3.8]`, target `[0, 1.05, 0]`.
- **Smooth Non-Jumping Wheel Zoom**: Set `controls.enableZoom = false` and attach a custom `{ passive: false }` `wheel` listener scaling distance by `4.2%` per notch (`minDistance = 1.7`, `maxDistance = 11.0`).

### 2. Physically Based Material Palette (`MeshStandardMaterial`)
- **Pebble Grey Switchboard Sheet Metal (`0x9aa3ad`) with SOLAS Red Header Stripe (`0xdc2626`)**: `roughness: 0.40`, `metalness: 0.36`, `side: THREE.DoubleSide`
- **Dark Slate Base Plinth & Internal Partitions (`0x3e4c59`)**: `roughness: 0.48`, `metalness: 0.45`
- **Electrolytic Copper 440 V / 220 V Busbars (`0xd97742`)**: `roughness: 0.20`, `metalness: 0.88`
- **Black Thermoset Molded ACB & MCCB Casings (`0x1e242b`)**: `roughness: 0.42`, `metalness: 0.25`
- **Clear Polycarbonate Inspection Windows (`0xd8ecff`)**: `transparent: true`, `opacity: 0.25`, `depthWrite: false`

### 3. Seven Cohesive Functional Sub-Assemblies (`parts` Registry)

1. **`esb_frame` — 2-Bay SOLAS Emergency Switchboard Frame & Drip Canopy (`EF`)**:
   - 2-bay marine switchboard enclosure (`1.70 m` wide × `2.15 m` high × `1.10 m` deep, Bay 1 at `X = -0.42 m`, Bay 2 at `X = +0.42 m`) with dark base plinth, top drip-proof overhang canopy, prominent red top header nameplate (`440 V / 220 V EMERGENCY SWITCHBOARD — SOLAS CH. II-1`), insulated front handrail bar, and internal Form 3b compartment partitions.
   - **Explode Vector**: `[0, 0, 0]`

2. **`esb_doors` — Hinged Front Doors with Extruded Cutout Windows & Mimic Bus (`ED`)**:
   - **Bay 1 (`X = -0.42 m` — 440 V EDG Incomer & Bus-Tie Section)**: Hinged front door with `THREE.ExtrudeGeometry` hollow viewing window cutout over the drawout ACB and engraved **Normal (Main 440 V Bus) ↔ Bus-Tie ACB ↔ ESB ↔ EDG ACB** mimic diagram with red/green LED status blocks.
   - **Bay 2 (`X = +0.42 m` — Essential 440 V & 220 V Emergency Feeders)**: Hinged door exposing flush rotary handles for the SOLAS essential feeders (`Emergency Fire Pump`, `Emergency Steering Gear`, `Navigation Bridge ABT`, `24V GMDSS Charger`, `Emergency Lighting`).
   - **Explode Vector**: `[0, 0, 0.78]`

3. **`esb_busbar_440v` — 440 V Emergency Copper Busbar Section (`BA`)**:
   - Located in the upper-rear busbar chamber of Bay 1 & 2 (`Y = 1.55 m, Z = -0.25 m`):
   - Heavy 3-phase electrolytic copper busbars (`L1` Red, `L2` Yellow, `L3` Blue, `1200 A` rated) mounted on ribbed standoff insulators with vertical copper risers dropping to the Tie/EDG ACBs and feeder MCCB bank.
   - **Explode Vector**: `[-0.35, 0.45, -0.40]`

4. **`esb_busbar_220v` — 220 V Transformed Emergency Busbar & Step-Down Transformer (`BB`)**:
   - Located in the lower/rear section of Bay 2 (`X = +0.42 m, Y = 0.55 m, Z = -0.18 m`):
   - Internal `440 V / 220 V, 50 kVA` dry-type emergency lighting/nav transformer feeding the `220 V` insulated copper busbar section and 440 V / 220 V Insulation Monitoring Devices (`IMD`).
   - **Explode Vector**: `[0.45, -0.15, -0.45]`

5. **`interlock_tie_acb` — Mechanical & Electrical Interlocked Normal/EDG Drawout ACBs (`TA`)**:
   - Mounted in the middle compartment of Bay 1 (`X = -0.42 m, Y = 0.85 m, Z = +0.05 m`):
   - Twin drawout 440 V **Air Circuit Breakers (`Bus-Tie ACB` from Main 440 V Bus & `EDG Incomer ACB` from Emergency Generator)** linked by a visible **Bowden-Cable / Walking-Beam Mechanical Interlock Linkage** (preventing both ACBs from closing simultaneously unless synchronized during return-to-normal transfer), complete with motorized spring charging, green/red `ON/OFF` buttons, and electronic trip units (`ETU`).
   - **Explode Vector**: `[-0.42, -0.05, 0.52]`

6. **`metering_synchro_panel` — Digital Multifunction Metering, Synchroscope & PMS Controller (`MP`)**:
   - Mounted in the upper instrument compartment (`Y = 1.72 m, Z = +0.38 m`):
   - Analog/LED circular **Synchroscope** (for blackless return-to-normal transfer from EDG back to Main Switchboard), 3 square analog gauges (`440 V`, `60.0 Hz`, `kW`), and glowing cyan microprocessor **ESB Automatic Transfer Controller**.
   - **Explode Vector**: `[0, 0.50, 0.65]`

7. **`essential_feeder_mccbs` — SOLAS Essential Feeder MCCB Bank & Control Wiring Loom (`CW`)**:
   - Mounted in Bay 2 (`X = +0.42 m, Y = 1.05 m, Z = +0.08 m`):
   - Vertical stack of 6 molded-case circuit breakers (`eSteer`, `eFire`, `nav`, `eRadio`, `eLights`, `Submersible Bilge Pump`) flanked by slotted grey DIN-rail wiring trunking, halogen-free blue control wiring harnesses, and CT test terminal blocks.
   - **Explode Vector**: `[0.45, 0.10, 0.48]`

### 4. Interactive Controls, Normal vs Blackout Interlock Toggle & Divided Callout Columns
- **Bottom Dock**:
  - **Explode Assembly Slider (`0%` to `100%`)**
  - **Interactive `TRANSFER MODE: NORMAL (MAIN BUS TIE CLOSED)` ↔ `BLACKOUT (TIE OPEN · EDG ACB CLOSED)` Button**: Actuates the mechanical walking-beam interlock between the two ACBs and updates the mimic bus LEDs!
- **Native-Color Ghosting**: Clone `origMaterial` and `ghostMaterial` (`opacity: 0.14`) per mesh; never overwrite `.color`.
- **Divided Left & Right Callout Columns**: Left (`MP`, `TA`, `ED`, `EF` at `LEFT_X = 24px`) and Right (`BA`, `CW`, `BB` at `RIGHT_X = window.innerWidth - 204px`) with collision avoidance (`MIN_GAP = 42px`) and long SVG `<polyline>` leader lines.

Return the complete, self-contained `index.html` file.
```

---

## 7. Electro-Hydraulic Pedestal Deck Cargo Crane (`crane`)

```markdown
Build a complete, standalone, single-file `index.html` 3D interactive CAD Digital Twin and Exploded Teardown Viewer for a **440 V, 40-Ton SWL Marine Electro-Hydraulic Pedestal Slewing Deck Cargo Crane (Internal 440 V HPU, Slewing Bearing Ring, Luffing Cylinders, Hoist Winch & Operator Cabin)** using Three.js (`v0.160.0` via ES Module importmap with `OrbitControls` and `RoomEnvironment`).

Follow these exact architectural, visual, kinematic, and UI requirements:

### 1. Scene, Renderer, Camera & Smooth Clamped Zoom (MANDATORY)
- **Renderer**: `THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" })`, `ACESFilmicToneMapping`, `toneMappingExposure = 1.05`, `shadowMap.enabled = true`.
- **Environment & Background**: `PMREMGenerator.fromScene(new RoomEnvironment(), 0.04).texture`, light studio drafting background `0xf2f4f7`.
- **Camera**: `PerspectiveCamera(35, window.innerWidth / window.innerHeight, 0.1, 100)` at `[-4.2, 3.0, 4.8]`, target `[0, 1.55, 0]`.
- **Smooth Non-Jumping Wheel Zoom**: Set `controls.enableZoom = false` and attach a custom `{ passive: false }` `wheel` listener scaling distance by `4.2%` per notch (`minDistance = 2.2`, `maxDistance = 14.0`).

### 2. Physically Based Material Palette (`MeshStandardMaterial`)
- **Marine Crane Safety Yellow / Amber Boom & Turret (`0xeab308` / `0xd97706`)**: `roughness: 0.35`, `metalness: 0.30`
- **Pebble Grey Cylindrical Deck Pedestal (`0x9aa3ad`)**: `roughness: 0.42`, `metalness: 0.38`
- **Hard-Chrome Luffing Hydraulic Cylinders (`0xdce3ea`)**: `roughness: 0.14`, `metalness: 0.90`
- **Machined Alloy Steel Slewing Ring & Planetary Winch (`0x3e4c59`)**: `roughness: 0.32`, `metalness: 0.75`
- **High-Visibility Red-and-Yellow Swivel Cargo Hook Block (`0xdc2626`)**: `roughness: 0.35`, `metalness: 0.35`

### 3. Seven Cohesive Functional Sub-Assemblies (`parts` Registry)

1. **`pedestal_column` — Cylindrical Steel Deck Pedestal & Slip-Ring Collector (`PC`)**:
   - Vertical cylindrical steel pedestal column (`R = 0.58 m, H = 1.15 m` centered at `[0, 0.58, 0]`) with a 36-bolt base deck flange, watertight access door, internal spiral ladder, and central **440 V 360° Continuous Electrical Slip-Ring Collector Column**.
   - **Explode Vector**: `[0, -0.45, 0]`

2. **`slewing_bearing` — 3-Row Roller Slewing Ring & Twin Planetary Slewing Drives (`SB`)**:
   - Mounted atop `pedestal_column` at `[0, 1.18, 0]`:
   - Heavy machined internal-gear **Slewing Bearing Ring (`R = 0.62 m`)** with inner/outer bolt circles, driven by two vertical hydraulic planetary slewing gearmotors with pinion gears engaging the internal ring teeth.
   - **Explode Vector**: `[0, 0.15, 0]`

3. **`turret_hpu` — Rotating Crane Turret House & Internal 440 V Electro-Hydraulic Power Pack (`TH`)**:
   - Mounted on the slewing ring (`[0, 1.65, -0.15]`, parented inside a rotatable `turretGroup` so the entire upper crane slews cleanly around `Y`):
   - Enclosed steel machinery turret housing a **440 V / 280 kW Squirrel-Cage Electric Motor** driving twin axial-piston hydraulic pumps, a `600 L` hydraulic oil tank with oil cooler fan, and the main proportional hydraulic control valve bank.
   - **Explode Vector**: `[0, 0.45, -0.45]`

4. **`operator_cabin` — Ergonomic Panoramic Glass Operator Cabin & Joystick Console (`OC`)**:
   - Cantilevered on the starboard side of `turret_hpu` (`[+0.68, 1.72, +0.25]`):
   - Weatherproof panoramic marine crane cabin with tinted polycarbonate floor-to-ceiling windows (`opacity: 0.28, depthWrite: false`), windshield wiper, air-conditioning unit, suspension seat, dual electro-hydraulic master joysticks, and **Safe Working Load (`SWL 40T`) Load-Moment Indicator Screen**.
   - **Explode Vector**: `[0.75, 0.45, 0.25]`

5. **`luffing_cylinders` — Twin Double-Acting Hydraulic Luffing Cylinders (`LC`)**:
   - Pivoting between the front lower turret ears (`[±0.32, 1.45, +0.35]`) and the underside of the box-section jib boom:
   - Twin heavy hydraulic cylinders with hard-chrome piston rods (`0xdce3ea`) and counterbalance holding valves that raise and lower the crane boom angle (`20°` to `70°`).
   - **Explode Vector**: `[0, 0.55, 0.55]`

6. **`jib_boom` — Box-Section Welded Steel Luffing Jib Boom & Head Sheaves (`JB`)**:
   - Hinged at the turret boom foot pins (`[0, 1.50, +0.25]`):
   - Tapered welded box-girder steel crane boom (`2.65 m` long, angled upward at `38°`) painted safety yellow with `SWL 40t × 28m` stencil, walkway handrail, floodlights, and twin grooved steel wire-rope head sheaves at the boom tip (`[0, 3.05, +2.10]`).
   - **Explode Vector**: `[0, 0.85, 0.65]`

7. **`hoist_winch_hook` — Planetary Hoist Winch Drum, Wire Rope & 40T Swivel Hook Block (`HW`)**:
   - **Hoist Winch Drum**: Grooved steel cable drum with hydraulic planetary drive and fail-safe multi-disc brake mounted inside the upper turret/boom root (`[0, 1.95, -0.05]`).
   - **Wire Rope & Hook Block**: 4-part steel wire rope reeving descending from the boom tip sheaves to a weighted yellow/red striped **40-Ton Swivel Cargo Hook Block** (`[0, 1.35, +2.10]`) with forged ramshorn/single hook and safety latch.
   - **Explode Vector**: `[0, 0.65, 1.05]`

### 4. Interactive Controls, Turret Slewing Slider & Divided Callout Columns
- **Bottom Dock**:
  - **Explode Assembly Slider (`0%` to `100%`)**
  - **Interactive Turret Slew Angle Slider (`-90° PORT` to `+90° STBD`)**: Smoothly rotates `turretGroup` (turret, HPU, cabin, boom, luffing cylinders, and hook block) on the slewing ring!
- **Native-Color Ghosting**: Clone `origMaterial` and `ghostMaterial` (`opacity: 0.14`) per mesh; never overwrite `.color`.
- **Divided Left & Right Callout Columns**: Left (`TH`, `SB`, `PC` at `LEFT_X = 24px`) and Right (`JB`, `HW`, `LC`, `OC` at `RIGHT_X = window.innerWidth - 204px`) with collision avoidance (`MIN_GAP = 42px`) and long SVG `<polyline>` leader lines.

Return the complete, self-contained `index.html` file.
```

---

## 8. 40-Foot Integral Refrigerated Container & Nose Reefer Machinery Unit (`reeferUnitA`, `reeferUnitB`)

```markdown
Build a complete, standalone, single-file `index.html` 3D interactive CAD Digital Twin and Exploded Teardown Viewer for a **440 V, 3-Phase, 60 Hz 40-Foot High-Cube Integral Marine Refrigerated Container (ISO Reefer) & Nose-Mounted Refrigeration Machinery Unit (Semi-Hermetic Compressor, Condenser Fan, Evaporator Coil & Digital Controller)** using Three.js (`v0.160.0` via ES Module importmap with `OrbitControls` and `RoomEnvironment`).

Follow these exact architectural, visual, kinematic, and UI requirements:

### 1. Scene, Renderer, Camera & Smooth Clamped Zoom (MANDATORY)
- **Renderer**: `THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" })`, `ACESFilmicToneMapping`, `toneMappingExposure = 1.05`, `shadowMap.enabled = true`.
- **Environment & Background**: `PMREMGenerator.fromScene(new RoomEnvironment(), 0.04).texture`, light studio drafting background `0xf2f4f7`.
- **Camera**: `PerspectiveCamera(35, window.innerWidth / window.innerHeight, 0.1, 100)` at `[-3.4, 2.1, 4.2]`, target `[0, 1.05, 0]`.
- **Smooth Non-Jumping Wheel Zoom**: Set `controls.enableZoom = false` and attach a custom `{ passive: false }` `wheel` listener scaling distance by `4.2%` per notch (`minDistance = 1.8`, `maxDistance = 12.0`).

### 2. Physically Based Material Palette (`MeshStandardMaterial`)
- **Insulated White Reefershell Corrugated Corten Steel (`0xf1f5f9`)**: `roughness: 0.32`, `metalness: 0.22`, `side: THREE.DoubleSide`
- **Anodized Aluminum T-Bar Floor & Reefer Frame (`0xcbd5e1`)**: `roughness: 0.28`, `metalness: 0.78`
- **Dark Slate Semi-Hermetic Reciprocating/Scroll Compressor (`0x263238`)**: `roughness: 0.42`, `metalness: 0.55`
- **Copper & Aluminum Finned Condenser / Evaporator Coils (`0xd97742`)**: `roughness: 0.24`, `metalness: 0.85`
- **Safety Red CEE 32A 440V Shore/Deck Plug & Cable (`0xdc2626`)**: `roughness: 0.35`, `metalness: 0.20`

### 3. Seven Cohesive Functional Sub-Assemblies (`parts` Registry)

1. **`container_shell` — Cutaway 40-Foot High-Cube Insulated Container Body & T-Bar Floor (`CS`)**:
   - Scaled compact architectural cutaway representation (`2.60 m` long along `X` × `1.85 m` high × `1.55 m` wide, with the nose machinery end facing `X = -1.30 m` and cargo doors at `X = +1.30 m`):
   - Corrugated white steel side walls (`0xf1f5f9`, with a clean cutaway window on the near side revealing the internal yellow polyurethane foam insulation layer and extruded aluminum **T-Bar Airflow Floor Grating**), 8 ISO corner castings with twistlock apertures, and rear double cargo doors with 4 vertical chrome locking bars.
   - **Explode Vector**: `[0.45, 0, 0]`

2. **`nose_frame_chassis` — Nose-Mount Aluminum Refrigeration Unit Frame & Access Doors (`NF`)**:
   - Bolted into the forward nose opening of the container (`X = -1.30 m, Y = 1.02 m`):
   - Structural marine-grade aluminum bulkhead frame separating the cold cargo space (`-25°C`) from the ambient machinery bay, with hinged lower service doors and fresh-air make-up vent slide.
   - **Explode Vector**: `[-0.35, 0, 0]`

3. **`compressor_receiver` — 440 V Semi-Hermetic Compressor & Refrigerant Receiver (`CM`)**:
   - Mounted in the lower nose machinery bay (`X = -1.42 m, Y = 0.45 m, Z = -0.22 m`):
   - 440 V semi-hermetic reciprocating/scroll refrigerant compressor (`0x263238`) with bolted cylinder heads, suction/discharge service valves, horizontal liquid refrigerant receiver tank with sight glass, filter-drier, and copper suction/discharge refrigeration lines.
   - **Explode Vector**: `[-0.85, -0.25, -0.25]`

4. **`condenser_fan_coil` — Air-Cooled Finned Copper Condenser Coil & Axial Fan (`CF`)**:
   - Mounted in the center-lower nose bay (`X = -1.45 m, Y = 0.72 m, Z = +0.18 m`):
   - Circular/rectangular copper-tube aluminum-fin condenser radiator coil (`0xd97742`), 5-blade axial **Condenser Cooling Fan** (`condenserFanGroup`, spins continuously when running), and protective black wire grille.
   - **Explode Vector**: `[-0.95, 0.05, 0.35]`

5. **`evaporator_blowers` — Upper Internal Evaporator Coil & Twin Circulation Fans (`EB`)**:
   - Mounted inside the upper cold plenum behind the nose bulkhead (`X = -1.05 m, Y = 1.55 m`):
   - Multi-row finned copper evaporator cooling coil with electric defrost heating rods and **Twin High-Velocity Axial Evaporator Fans** (`evapFanGroup`) that force chilled `-25°C` air down the front wall, along the bottom T-bar floor channels, and back through the top cargo return grille.
   - **Explode Vector**: `[-0.45, 0.55, 0]`

6. **`control_box_pti` — Microprocessor Temperature Controller, USD Logger & 440 V Contactors (`CB`)**:
   - Mounted on the front-right nose panel (`X = -1.45 m, Y = 1.15 m, Z = +0.42 m`):
   - Weatherproof white/grey control cabinet with glowing cyan LCD temperature controller (`SETPOINT: -25.0°C · SUPPLY: -25.2°C · RETURN: -23.8°C`), USDA pulp-temperature sensor ports, internal 440 V phase-reversal contactors, and `18 m` coiled **440 V 32 A 4-Pin CEE Power Cable & Red Plug (`3P+E`, `4h` clock position)**.
   - **Explode Vector**: `[-0.85, 0.25, 0.65]`

7. **`water_cooled_condenser` — Optional Below-Deck Seawater Shell-and-Tube Condenser (`WC`)**:
   - Mounted in the lower-left machinery recess (`X = -1.40 m, Y = 0.42 m, Z = +0.35 m`):
   - CuNi (Copper-Nickel) shell-and-tube water-cooled condenser with brass Hansen quick-connect cooling water couplings for operation in enclosed below-deck cargo holds.
   - **Explode Vector**: `[-0.75, -0.30, 0.55]`

### 4. Interactive Controls, Reefer Mode Toggle & Divided Callout Columns
- **Bottom Dock**:
  - **Explode Assembly Slider (`0%` to `100%`)**
  - **Operating Mode Selector (`FROZEN CARGO (-25.0°C · High Speed)` / `CHILLED FRUIT (+2.0°C · Modulating)` / `DEFROST CYCLE (Fans Off · Heaters On)`)**: Controls the rotation speed of the condenser and evaporator fans and updates the controller display!
- **Native-Color Ghosting**: Clone `origMaterial` and `ghostMaterial` (`opacity: 0.14`) per mesh; never overwrite `.color`.
- **Divided Left & Right Callout Columns**: Left (`EB`, `NF`, `CF`, `CM` at `LEFT_X = 24px`) and Right (`CS`, `CB`, `WC` at `RIGHT_X = window.innerWidth - 204px`) with collision avoidance (`MIN_GAP = 42px`) and long SVG `<polyline>` leader lines.

Return the complete, self-contained `index.html` file.
```

---

## 9. 440 V / 220 V Low-Voltage Switchboard & Drawout Air Circuit Breaker (`lvBusA`, `lvBusB`, `consumerA`, `consumerB`)

```markdown
Build a complete, standalone, single-file `index.html` 3D interactive CAD Digital Twin and Racking/Teardown Simulator for a **3-Cubicle 440 V, 3-Phase, 60 Hz, 3200 A / 65 kA IEC 61439-2 Marine Main Low-Voltage Switchboard Lineup & Withdrawable Air Circuit Breaker (ACB) with Arc Chutes & Electronic Trip Unit (ETU)** using Three.js (`v0.160.0` via ES Module importmap with `OrbitControls` and `RoomEnvironment`).

Follow these exact architectural, visual, kinematic, and UI requirements:

### 1. Scene, Renderer, Camera & Smooth Clamped Zoom (MANDATORY)
- **Renderer**: `THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" })`, `ACESFilmicToneMapping`, `toneMappingExposure = 1.05`, `shadowMap.enabled = true`.
- **Environment & Background**: `PMREMGenerator.fromScene(new RoomEnvironment(), 0.04).texture`, light studio drafting background `0xf2f4f7`.
- **Camera**: `PerspectiveCamera(36, window.innerWidth / window.innerHeight, 0.1, 100)` at `[-3.2, 2.0, 4.2]`, target `[0, 1.05, 0]`.
- **Smooth Non-Jumping Wheel Zoom**: Set `controls.enableZoom = false` and attach a custom `{ passive: false }` `wheel` listener scaling distance by `4.2%` per notch (`minDistance = 1.8`, `maxDistance = 12.0`).

### 2. Physically Based Material Palette (`MeshStandardMaterial`)
- **Pebble Grey Switchboard Sheet Metal (`0x9aa3ad`)**: `roughness: 0.42`, `metalness: 0.35`, `side: THREE.DoubleSide`
- **Dark Slate Base Plinth & ACB Molded Frame (`0x263238` / `0x3e4c59`)**: `roughness: 0.45`, `metalness: 0.42`
- **Electrolytic High-Current 440 V Copper Busbars (`0xd97742`)**: `roughness: 0.20`, `metalness: 0.88`
- **De-Ion Steel Splitter Plates & Ceramic Arc Chute Housings (`0xb45309` / `0xd8dee4`)**: `roughness: 0.30`, `metalness: 0.55`
- **Silver-Alloy Main & Arcing Contact Fingers (`0xe2e8f0`)**: `roughness: 0.16`, `metalness: 0.90`

### 3. Seven Cohesive Functional Sub-Assemblies (`parts` Registry)

1. **`lv_cubicle_lineup` — 3-Bay IEC 61439-2 Form 4b Low-Voltage Switchboard Lineup (`LC`)**:
   - **3-Cubicle Steel Lineup (`2.40 m` wide × `1.30 m` deep × `2.15 m` high, bay centers at `bays = [-0.80, 0.00, +0.80]`)**:
     - Continuous base plinth, top drip-proof overhang canopy with insulated front grab rail, and upper LV metering doors across all 3 bays (`Bay 1: TX A 440V Incomer`, `Bay 2: 440V Bus-Tie ACB`, `Bay 3: Group MCCB Motor & Pump Feeders`) featuring a continuous horizontal **440 V Mimic Bus Diagram**, 3 square analog gauges per bay, and digital power management relays.
     - **Bay 1 Lower ACB Door (`X = -0.80 m`)**: Swung open `110°` (`-1.92 rad`) with a true `THREE.ExtrudeGeometry` cutout window and extendable steel drawout rails.
     - **Bay 2 Lower Door (`X = 0.00 m`)**: Closed door with extruded cutout window showing the Bus-Tie ACB fascia inside.
     - **Bay 3 Lower Door (`X = +0.80 m`)**: Compartmentalized outgoing **MCCB Feeder Drawer Matrix** (6 modular plug-in motor starter / pump feeder drawers with rotary handles and ammeters).
   - **Explode Vector**: `[0, 0, 0]`

2. **`lv_copper_busbars` — 3200 A Double-Bar Electrolytic Copper Busbars & Drop Risers (`LB`)**:
   - Spanning across all 3 cubicles in the rear busbar chamber (`X = -1.14 m` to `+1.14 m, Y = 1.55 m, Z = -0.28 m`):
   - Heavy **Double-Laminated Flat Copper Busbars per Phase (`2 × 100×10 mm` per phase)** for high `65 kA` short-circuit electrodynamic withstand, with `L1` Red, `L2` Yellow, `L3` Blue phase markers, DMC glass-polyester comb busbar supports, and heavy copper drop risers to all 3 bays.
   - **Explode Vector**: `[0, 0.50, -0.45]`

3. **`drawout_cassette` — Fixed Drawout Cassette Cradle & Automatic Safety Shutters (`DC`)**:
   - Mounted inside Bay 1's breaker compartment (`X = -0.80 m, Y = 0.72 m, Z = -0.05 m`):
   - Galvanized steel fixed cassette guide frame with 6 rear copper cluster stab terminals (3 upper line, 3 lower load) protected by sliding insulated **IP20 Safety Shutters (`shutterUpper`, `shutterLower`)** that automatically cover the live 440 V busbar stabs when the ACB is racked out past `25%`.
   - **Explode Vector**: `[0, 0.15, -0.20]`

4. **`acb_carriage` — Monolithic Withdrawable 3200 A Air Circuit Breaker (`acbTruckGroup`) (`AC`)**:
   - Parented inside a single root `THREE.Group` (`acbTruckGroup` at `X = -0.80 m`) so the entire ACB carriage, contacts, arc chutes, and ETU translate together along `Z` (`0.00 m CONNECTED` -> `+0.22 m TEST` -> `+0.52 m DISCONNECTED`) during Racking (`0%` to `100%`):
   - Molded thermoset phase barriers, heavy stored-energy closing/opening spring mechanism, manual charging pump handle, mechanical `ON (I)` Red / `OFF (O)` Green and `CHARGED` / `DISCHARGED` flags, and fold-out racking crank handle.
   - **Explode Vector**: `[0, 0, 0.70]`

5. **`etu_protection_unit` — Microprocessor Electronic Trip Unit (`LSIG` Protection) (`ET`)**:
   - Mounted on the front fascia of `acbTruckGroup` (`X = -0.68 m, Y = 0.72 m`):
   - Removable modular **Electronic Trip Unit (`ETU`)** with backlit cyan LCD load bargraph, rotary dial settings for **Long-Time (`L` Overload), Short-Time (`S` Selective Delay), Instantaneous (`I` Short-Circuit), and Ground-Fault (`G`)** pickup curves, thermal memory LED, and test port.
   - **Explode Vector**: `[0, 0.10, 1.05]` (detaches forward from the ACB front fascia during Explode).

6. **`silver_contact_clusters` — Multi-Finger Silver-Alloy Main & Arcing Contact Jaw (`SC`)**:
   - Mounted inside the 3 poles of `acbTruckGroup` (`X = -0.80 m`, phase spacing `dx = -0.20, 0, +0.20`):
   - Spring-loaded copper-silver parallel **Main Contact Finger Bridges** and higher-mounted sacrificial tungsten-silver **Arcing Contact Horns** that close first and open last to commutate the `440 V` interruption arc upward into the arc chutes. Pivots `18°` open/closed when the ACB toggles.
   - **Explode Vector**: `[0, 0.28, 0.70]`

7. **`deion_arc_chutes` — Removable Ceramic & Steel-Grid De-Ion Arc Quenching Chutes (`CH`)**:
   - Seated atop the 3 poles of `acbTruckGroup` (`X = -0.80 m, Y = 1.08 m`, `dx = -0.20, 0, +0.20`):
   - 3 removable finned ceramic/thermoset **De-Ion Arc Chute Chambers** containing stacks of 18 V-notched ferromagnetic steel splitter plates and top exhaust de-ionizer mesh grilles that cool, lengthen, and split the 440 V electric arc into series sub-arcs until extinguished at current zero.
   - **Explode Vector**: `[0, 0.65, 0.70]` (lifts vertically out of the top of the ACB poles during Explode, just like real ACB maintenance inspection!).

### 4. Interactive Controls, Dual Sliders (Racking + Explode) & Divided Callout Columns
- **Bottom Dock**:
  - **ACB Racking Slider (`0% CONNECTED` → `50% TEST` → `100% WITHDRAWN`)**: Rolls `acbTruckGroup` out along the cassette rails and closes the safety shutters past `25%`.
  - **Explode Assembly Slider (`0%` to `100%`)**: Lifts the 3 De-Ion Arc Chutes vertically out of the ACB, detaches the Electronic Trip Unit (`ETU`) forward, and exposes the silver contact fingers.
  - **Interactive `CLOSE ACB (I)` / `TRIP ACB (O)` Button** with interlock protection in transit.
- **Native-Color Ghosting**: Clone `origMaterial` and `ghostMaterial` (`opacity: 0.14`) per mesh; never overwrite `.color`.
- **Divided Left & Right Callout Columns**: Left (`LC`, `CH`, `AC`, `ET` at `LEFT_X = 24px`) and Right (`LB`, `DC`, `SC` at `RIGHT_X = window.innerWidth - 204px`) with collision avoidance (`MIN_GAP = 42px`) and long SVG `<polyline>` leader lines.

Return the complete, self-contained `index.html` file.
```
