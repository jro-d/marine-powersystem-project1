"""
V8-C  "Modern Feeder (high detail)"  ->  public/models/blender-hull-V8C.glb

A contemporary feeder container ship: deep-blue topsides with weathering (rust weeps under plate seams, grime),
black boot-top, raised forecastle with bulwark + cap rail and breakwater, bigger bulb, more flare and stem rake,
fire main along the deck, vents / air pipes / manholes, framed windows, tripod mast with radomes and antennas,
SCR casings on the funnel, free-fall lifeboat on a stern ramp, rescue-boat davit, life-raft canisters,
sea chests and everything from V8-A underneath.

Run:  blender --background --python scripts/blender/generate_hull_v8c.py      (or: npm run build:hull:v8c)
"""
import os, sys, importlib
_here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() and os.path.exists(os.path.abspath(__file__)) else os.path.join(os.getcwd(), "scripts", "blender")
sys.path.insert(0, _here)
import hull_lib  # noqa: E402
importlib.reload(hull_lib)

CONFIG = dict(
    name="V8C Modern Feeder",
    export="blender-hull-V8C.glb",
    ship_name="ASCEND MARINER",
    seed=37,
    form=dict(stretch=6.0, beam_scale=1.15, keel_drop=0.5, bulb=1.12, flare=1.15, stem_rake=1.90,
              fc_rise=0.25, fc_step=1.0, fc_step_x=18.0, bulwark=0.45),
    palette=dict(
        # linear colour values (as in Blender's Base Color); textures are encoded to match
        topsides=(0.012, 0.035, 0.11), bottom=(0.45, 0.05, 0.035), boot=(0.012, 0.012, 0.014), boot_band=(-1.45, -1.08),
        deck=(0.06, 0.17, 0.09), hatch=(0.05, 0.12, 0.08), house=(0.80, 0.82, 0.82), house_deck=(0.20, 0.22, 0.23),
        window=(0.01, 0.03, 0.06), funnel=(0.80, 0.80, 0.78), funnel_band=(0.01, 0.06, 0.30), hardware=(0.03, 0.035, 0.04),
        accent=(0.75, 0.45, 0.02), rail=(0.65, 0.68, 0.65), pad=(0.03, 0.30, 0.42), internal=(0.10, 0.22, 0.28),
        grating=(0.14, 0.18, 0.20)),
    textures=dict(rust=0.55, grime=0.35, deck_wear=0.30),
    features=["bilge_keels", "anodes", "sea_chests", "markings", "deck_fittings", "fire_main", "window_frames",
              "modern_mast", "freefall", "funnel_detail", "bulwark_cap"],
)

if __name__ == "__main__":
    hull_lib.build(CONFIG)
