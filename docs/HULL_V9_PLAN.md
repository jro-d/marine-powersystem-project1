# Vessel model: scan findings, implementation plan and roadmap

Status: **M1, M2 and M3 done.**
- M1 was merged in #9, M2 in #10.
- M2: `src/vessel/general-arrangement.json` is the single spec. Both `vessel-layout.ts` and `hull_lib.py` read it.
- M3 (`feat/hull-m3-real-hull-qa`): checks run against the real shell.
  - The V8-C build writes `public/models/blender-hull-V8C.sections.json` (half-breadth every 0.25 m × 0.1 m, keel and
    deck lines). `check:layout` tests every vertex of every equipment model against it; the V7 `SHIP.stations / bottom /
    keelLine` tables and `halfBeamAt` are deleted.
  - The Blender build runs a QA pass and **fails** (exit 1) on any problem; `HULL_QA=warn` exports anyway.
    It checks slots against the shell, hull-owned parts (tunnel, grids, bilge keels, anodes, sea chests, markings,
    rudder) against the shell, anything else dipping into the hull below the deck, clearances, and floating parts
    (every connected piece must link to the shell by touching or intersecting other pieces).
  - Its first run found 23 problems, all fixed: rudder 0.20 D behind the propeller (stock moved aft 0.07 to
    X = −18.12, now 0.27 D), sea-chest gratings half buried in the bilge, anodes standing off the stern run, anchors
    hanging clear of the flared bow, thruster grid bars 0.43 m inside the aft half of the mouth, draft marks floating
    below the stern run, guard rails on the mast platforms with no stanchions, a yardarm in mid-air, sidelights above
    the wing bulwark, SCR casings and top ladder rungs floating in the funnel, and the free-fall boat hovering about 5 cm
    over its rails.
  - Tunnel immersion is checked as axis ≥ 1 D and top ≥ 0.5 D below the waterline (now 1.17 D and 0.67 D). A top
    ≥ 1 D would need the tunnel lowered into the bilge turn.

The scan measurements below were taken before M1, on `main` at `b8ea922` (V8-C default hull),
using the Blender build, the exported GLBs and the running app.

Decisions taken:
- Bow thruster moved aft (now X = 18.3, axis Z = −2.30, Ø 0.90).
- Free-fall lifeboat kept, at the stern.
- `eSteer` to move onto the rudder stock in M4; no main steering gear added.
- V8-C only: V8-A, V8-B and the unused V6 deleted; V7 kept as the backup (`?hull=v7`).

M1 delivered:
- **Bow thruster** (A1–A4)
  - Exact boolean opening in the shell.
  - Tunnel end rings projected onto the hull surface.
  - Faired lip and recessed grid bars; antifouling bore.
  - App thruster drops its duplicate tunnel, and its impeller is enlarged to Ø0.81 on the tunnel axis.
- **Life-saving appliances** (B1–B7)
  - Stern free-fall boat seated bow-down on a 35° ramp, launching over the transom.
  - Recovery A-frame carrying the ensign, boarding platform and ladder.
  - Two quarter mooring winches.
  - Rescue boat in a cradle on the bridge deck with a slewing davit.
  - Life rafts in cradles on the deck-2 walkways; lifebuoys on the rails.
- **Superstructure** (C1–C3)
  - Deck-2 walkways on knee brackets, plus an aft strip.
  - Stairs from main deck → deck 2 → bridge deck that land on decks.
  - Bridge-wing brackets.

## Short answer: does the whole vessel need redesigning?

**The hull shape does not.** Every machinery item fits inside it, and the forms (bulb, flare, stern, bilge) are sound.
**How things are placed on and in the hull does.** Positions are hard-coded separately in four files and nothing checks
hull-owned parts (tunnel, lifeboats, stairs) against the real shell. That is how the two visible bugs slipped through,
so the fix is a single *General Arrangement* (GA) spec plus geometry checks, not a new ship.

---

## 1. Findings

Severity: 🔴 visibly wrong · 🟠 wrong but subtle · 🟡 tidy-up

### A. Bow thruster
| # | Sev | Finding | Evidence |
|---|---|---|---|
| A1 | 🔴 | The hull tunnel is a straight 4.7 m cylinder at X = 20.1, in the narrowing bow. Across the tunnel's 1 m footprint the hull half-width runs from **2.8 m (aft edge) to 1.6 m (forward edge)**, so the forward half **sticks out up to ~0.45 m** and the aft half is buried. The collar shows as a "C" and the grid bars poke out of the plating. | Half-width table below; `V8C_bt_close.png` |
| A2 | 🔴 | No opening is cut in the shell, so the tunnel mouth is closed plating. In the app's glass view the whole tube reads as a solid bar across the bow. | |
| A3 | 🟠 | **Two tunnels.** The app's thruster model (`models.ts`, type `thruster`) has its own tunnel, 0.63 m across and 0.93 m long, inside the hull's 0.96 m tunnel. Its propeller hub is 0.15 m below the tunnel axis. Because the model is shrunk to fit a box, the 1,250 kW motor is drawn about 0.2 m tall. | `bow` parts: tunnel Y −2.46…−1.83, hub −2.37…−2.23 |
| A4 | 🟠 | Tunnel top is at −1.67 against a waterline of −1.25: only about 0.44 × tunnel diameter of submergence (normal practice is ≥ 1 diameter). The location is also where the sections change fastest. | |

Hull half-width (V8-C) around the current tunnel:

```
   z |x   19.00  19.60  20.10  20.60  21.20
 -1.60    3.07   2.53   2.05   1.58   1.12
 -2.15    3.22   2.77   2.36   1.96   1.54     <- tunnel axis
 -2.70    2.83   2.28   1.84   1.46   1.11
```

### B. Life-saving appliances
| # | Sev | Finding |
|---|---|---|
| B1 | 🔴 | V8-C free-fall lifeboat is **pitched the wrong way**: it rises toward the stern while its ramp falls toward the stern. It should sit bow-down, sliding aft off the ramp. |
| B2 | 🔴 | The boat floats above its ramp, not resting in the rails. The ramp stands **over the aft mooring winch** and ends mid-deck, so it could not launch and blocks the mooring deck. |
| B3 | 🟠 | Boat shape reads as a flattened disc; it needs a free-fall hull form (raked keel, enclosed canopy, helm dome, release hook). |
| B4 | 🟠 | Rescue boat (V8-C) hangs outboard at bridge-deck height as a disc. Its davit has no deck at the embarkation level. |
| B5 | 🟠 | Life-raft canisters are pressed against the house wall at deck 2 with nothing under them (they look like wall lamps). |
| B6 | 🟠 | V8-A davit lifeboats hang beside the house with no embarkation deck, and the davit arms cross the windows. |
| B7 | 🟠 | Stern lifebuoys float in mid-air, 0.25 m inboard of the rail. |

### C. Superstructure
| # | Sev | Finding |
|---|---|---|
| C1 | 🔴 | External stairs land on nothing. The deck-2 landing is a floating plate; there is no open deck or walkway outside deck 2. |
| C2 | 🟠 | No open decks around the tiers. Real accommodation blocks have an open deck at each level, which is also where boats are boarded (embarkation). |
| C3 | 🟡 | Bridge wings are cantilevered with no brackets. |

### D. Machinery placement (app layout)
| # | Sev | Finding |
|---|---|---|
| D1 | 🟠 | Emergency steering gear `eSteer` sits at X = −14.65 in the engine room, **3.4 m forward of the rudder stock** (X = −18.05). Steering gear must sit on the stock, in a steering-gear room aft of the aft-peak bulkhead. There is no main steering gear in the layout at all. |
| D2 | 🟠 | Every equipment model is scaled to 75 % and then fit to its box (`EQ_SCALE`), so proportions drift (see A3). |

### E. Data consistency (root cause)
| # | Sev | Finding |
|---|---|---|
| E1 | 🟠 | Geometry facts are hard-coded in 4 places: `vessel-layout.ts` (positions + `SHIP` tables), `hull_lib.py` (bulkheads, house, bays, thruster, prop, 0.75 scale), `vessel.ts` (`EQ_SCALE`, cargo), `check-layout.mjs`. Moving anything means editing all of them. |
| E2 | 🟠 | `SHIP.stations / bottom / keelLine` still describe the **V7** envelope, and `npm run check:layout` checks against those tables, not the real hull. |
| E3 | 🟠 | Only the Blender build checks against the real shell, and only equipment boxes. Hull-owned parts (tunnel, rudder, boats, stairs) are never checked for protrusion, floating or clearance. |

### F. Tidy-up
| # | Sev | Finding |
|---|---|---|
| F1 | 🟡 | `npm run build:hull` (V7) still calls `blender` from PATH and fails on this machine; route it through `run-blender.mjs`. |
| F2 | 🟡 | `public/models/blender-hull-V6.glb` (1.9 MB) is unused but still deployed. Models total 29 MB. |
| F3 | 🟡 | The compare page downloads all four hulls (~16 MB) up front just to fill in card stats. |
| F4 | 🟡 | In the app's glass styling (0.32 opacity) the new textures barely show. A "solid hull" toggle would help. |

---

## 2. Target design (what "correct placement" means)

**Bow thruster**
- Move it aft to about **X ≈ 18.6–19.0**, centre Z ≈ −2.30, diameter 0.90. The sections there are close to wall-sided, giving submergence of about 1 diameter.
- It stays forward of the collision bulkhead (17.2), in its own thruster room.
- The final X is chosen from the half-width table so width varies less than 0.15 m across the tunnel footprint.
- **The hull owns the tunnel; the app model owns only motor, gearbox and impeller.** These are sized to the hull tunnel's diameter and sit on its axis.
- The tunnel ends are **trimmed to the hull surface**: each end-ring vertex is projected onto the shell, so the mouth matches the hull shape exactly. The shell faces inside the mouth are removed and the opening gets a faired lip and flush grid bars.

**Life-saving appliances (V8-C)**
- Free-fall davit centred on the **stern**, ramp about 35° falling aft, ending at the transom. The boat rests in the rails, bow-down, with its stern hook at the release.
- The aft mooring winch splits into two side winches clear of the launch path.
- Rescue boat on the starboard embarkation deck (deck 2) in a cradle with a slewing davit.
- Life rafts in cradles on the deck-2 rails, both sides; lifebuoys in rail brackets.

**Life-saving appliances (V8-A)**
- Gravity-davit lifeboats on a deck-2 embarkation deck each side, davits clear of the windows.

**Superstructure**
- Open walkways at decks 2 and 3 (bridge-deck overhang), with rails.
- Stairs that start and end on a deck.
- Wing brackets.

**Steering**
- Steering-gear flat aft of the aft-peak bulkhead, directly above the rudder stock (X = −18.05).
- Move `eSteer` there, and optionally add a main steering gear beside it.

---

## 3. Implementation plan

### Phase 1: Single source of truth (General Arrangement spec)
- New `src/vessel/general-arrangement.json`, read by **both** TypeScript and Blender. It contains:
  - frame spacing and numbering
  - bulkheads
  - deck and flat levels
  - house box and open decks
  - cargo bays
  - shaft / propeller / rudder-stock positions
  - thruster tunnel (X, Z, diameter)
  - life-saving stations
  - equipment slots (`position`, `size`, `rotation`, `space`) and the equipment scale
- `vessel-layout.ts` and `vessel.ts` import it; `hull_lib.py` reads it instead of regex-parsing TypeScript and dropping its own constants.
- Acceptance: the app and the check produce identical results before and after (refactor only).

### Phase 2: Checks against the real hull
- Each Blender build writes `public/models/hull-<variant>.sections.json`: half-breadth at every frame × every 0.1 waterline, plus keel and deck lines.
- `check-layout.mjs` loads the sections for the selected/default variant instead of the `SHIP` tables. The `SHIP` tables are then generated or deleted.
- Blender `validate()` gains geometry QA for hull-owned parts:
  - **protrusion**: sampled vertices of the tunnel, rudder, appendages and boats against the shell
  - **floating parts**: every outfit item must touch a deck, rail or wall
  - **clearances**: propeller tip to hull ≥ 0.25 D, propeller to rudder ≥ 0.25 D, tunnel submergence ≥ 1 D
- The build fails on any violation (done in M3; see the status at the top).

### Phase 3: Bow thruster rebuild (fixes A1–A4)
- Choose X from the section table; update the GA spec (the app's `bow` position follows automatically).
- `hull_lib`: delete shell faces inside the tunnel footprint, build the tunnel with end rings projected onto the shell, bridge the opening edge to the end ring, add a faired lip and flush grid bars. Move the bow-thruster sign above the new tunnel.
- `models.ts` thruster: drop the internal tunnel (or hide it in the vessel view), size the impeller to the hull tunnel and align it to the tunnel axis; stop the 0.75 fit-to-box shrink for the motor.
- Acceptance:
  - protrusion check = 0
  - opening visible in the textured view
  - glass view shows one tunnel with the impeller centred

### Phase 4: Superstructure and life-saving redesign (fixes B1–B7, C1–C3)
- `build_superstructure`: open decks at decks 2 and 3, stairs generated between real landings, wing brackets.
- `build_lifesaving` rewritten per station type from the GA spec:
  - `freefall_stern`
  - `davit_side`
  - `rescue_davit`
  - `raft_cradle`
  - `lifebuoy_rail`
- New free-fall boat mesh (lofted hull + canopy + helm dome) and a proper davit-boat mesh.
- V8-C aft mooring: two side winches clear of the launch path.
- Acceptance: floating-part check = 0; boat pitch bow-down along the ramp; preview sheet reviewed.

### Phase 5: Machinery placement corrections (fixes D1–D2)
- Steering-gear flat aft of the aft-peak bulkhead over the rudder stock; move `eSteer` there and optionally add main steering gear `steering` (needs a network/sim entry if it is electrical).
- Review the remaining slots against GA compartments (thruster room, pump room, ER flats).
- Acceptance: `check:layout` passes on real-hull sections; teardown links and the sim are unaffected.

### Phase 6: Tidy-up and performance (F1–F4)
- `build:hull` via `run-blender.mjs`; remove `blender-hull-V6.glb`.
- Compare page loads a hull only when selected (stats from a small manifest written by the build).
- Optional: WebP/KTX2 textures (≈ −50 % GLB size); a "Solid / Glass" hull toggle in the vessel view.

---

## 4. Roadmap

| Milestone | Phases | Outcome | Effort |
|---|---|---|---|
| **M1: Visible fixes** ✅ | 3 + 4 (inside `hull_lib`, `bow` slot moved by hand) | Thruster fits the hull with a real opening; lifeboats, stairs and rafts placed correctly. All three variants rebuilt. | 1 session |
| **M2: Single GA spec** ✅ | 1 | One file drives app + Blender; no duplicated constants | 1 session |
| **M3: Real-hull QA** ✅ | 2 | `check:layout` and the Blender build both validate against the actual shell, including protrusion, floating parts and clearance | 1 session |
| **M4: Arrangement corrections** | 5 | Steering gear on the rudder stock; compartments match the GA | ½–1 session |
| **M5: Polish** | 6 | Smaller downloads, solid/glass toggle, clean scripts | ½ session |

Recommended order: **M1 first** (it is what you see), then M2 → M3 so these bugs can't come back, then M4 and M5.
M1 can be done without M2: it only touches `hull_lib.py`, the `bow` entry in `vessel-layout.ts` and the thruster model.

## 5. Decisions needed before starting
1. **Bow thruster position:** OK to move it aft from X = 20.1 to about 18.6–19.0 (the app's `bow` equipment moves with it)?
2. **V8-C lifeboat:** free-fall boat at the stern (needs the aft mooring winch split into two side winches), or switch to davit boats on both sides like V8-A?
3. **Steering gear (M4):** move `eSteer` aft onto the rudder stock, and also add a main steering gear?
4. **Scope:** fix all three variants, or only V8-C (the default) and retire A/B?
