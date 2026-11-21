"""
V8-B  "Structural / Engineering Cutaway"  ->  public/models/blender-hull-V8B.glb

Same lines as V8-A, but built to be looked *into*: transverse frames every 0.5 m with deep web frames every 2 m,
plate floors in the double bottom, centre + side girders, side stringers, deck beams, hatch-side girders, hold
pillars, stiffened watertight bulkheads and colour-coded double-bottom tanks (ballast / fuel / lube oil / fresh
water). Light grey topsides with frame-line texture so the frame spacing reads from outside.

Run:  blender --background --python scripts/blender/generate_hull_v8b.py      (or: npm run build:hull:v8b)
"""
import os, sys, importlib
_here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() and os.path.exists(os.path.abspath(__file__)) else os.path.join(os.getcwd(), "scripts", "blender")
sys.path.insert(0, _here)
import hull_lib  # noqa: E402
importlib.reload(hull_lib)

CONFIG = dict(
    name="V8B Structural Engineering",
    export="blender-hull-V8B.glb",
    ship_name="ASCEND MARINER",
    seed=23,
    form=dict(stretch=6.0, beam_scale=1.15, keel_drop=0.5, bulb=1.0, flare=1.0, stem_rake=1.62,
              fc_rise=0.68, bulwark=0.36),
    palette=dict(
        # linear colour values (as in Blender's Base Color); textures are encoded to match
        topsides=(0.42, 0.50, 0.56), bottom=(0.36, 0.09, 0.07), boot=(0.02, 0.02, 0.025), boot_band=(-1.40, -1.12),
        deck=(0.16, 0.24, 0.19), hatch=(0.10, 0.17, 0.14), house=(0.80, 0.82, 0.82), house_deck=(0.18, 0.22, 0.22),
        window=(0.02, 0.05, 0.08), funnel=(0.10, 0.18, 0.26), funnel_band=(0.90, 0.55, 0.03), hardware=(0.05, 0.07, 0.09),
        accent=(0.90, 0.55, 0.03), rail=(0.50, 0.57, 0.62), pad=(0.03, 0.30, 0.42), internal=(0.32, 0.42, 0.48),
        grating=(0.16, 0.22, 0.26), frame=(0.78, 0.30, 0.06)),
    textures=dict(rust=0.0, grime=0.05, frame_lines=0.22, deck_wear=0.10),
    features=["structure", "tanks", "bilge_keels", "anodes", "sea_chests", "markings", "bulwark_cap"],
)

if __name__ == "__main__":
    hull_lib.build(CONFIG)
