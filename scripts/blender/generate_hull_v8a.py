"""
V8-A  "Classic Refined"  ->  public/models/blender-hull-V8A.glb

The V7 look (navy-cyan topsides, red-oxide bottom, white boot-top, orange funnel) rebuilt properly:
fair girth-sampled shell with a real flat bottom + round bilge, crisp boot-top band, welded-plate textures,
non-skid deck, folding hatch covers with container sockets, lowered counter with a NACA rudder tucked under it,
flush bow-thruster tunnel, bilge keels, anodes, draft marks / load line / name, davit lifeboats, platforms and
foundation seats generated from vessel-layout.ts.

Run:  blender --background --python scripts/blender/generate_hull_v8a.py      (or: npm run build:hull:v8a)
"""
import os, sys, importlib
_here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() and os.path.exists(os.path.abspath(__file__)) else os.path.join(os.getcwd(), "scripts", "blender")
sys.path.insert(0, _here)
import hull_lib  # noqa: E402
importlib.reload(hull_lib)

CONFIG = dict(
    name="V8A Classic Refined",
    export="blender-hull-V8A.glb",
    ship_name="ASCEND MARINER",
    seed=11,
    form=dict(stretch=6.0, beam_scale=1.15, keel_drop=0.5, bulb=1.0, flare=1.0, stem_rake=1.62,
              fc_rise=0.68, bulwark=0.36),
    palette=dict(
        # linear colour values (as in Blender's Base Color); textures are encoded to match
        topsides=(0.05, 0.22, 0.42), bottom=(0.34, 0.07, 0.05), boot=(0.85, 0.90, 0.92), boot_band=(-1.36, -1.14),
        deck=(0.10, 0.20, 0.27), hatch=(0.07, 0.14, 0.20), house=(0.78, 0.86, 0.90), house_deck=(0.12, 0.22, 0.28),
        window=(0.02, 0.06, 0.10), funnel=(0.70, 0.13, 0.04), funnel_band=(0.90, 0.90, 0.90), hardware=(0.04, 0.07, 0.09),
        accent=(0.40, 0.08, 0.05), rail=(0.55, 0.65, 0.72), pad=(0.03, 0.30, 0.42), internal=(0.12, 0.27, 0.36),
        grating=(0.15, 0.22, 0.27)),
    textures=dict(rust=0.0, grime=0.08, deck_wear=0.12),
    features=["bilge_keels", "anodes", "markings", "deck_fittings", "bulwark_cap"],
)

if __name__ == "__main__":
    hull_lib.build(CONFIG)
