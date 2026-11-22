"""
Render quick preview stills of a hull GLB (or the current scene) so hull variants can be compared side by side.

Usage (from the project root):
    D:/Blender/blender.exe --background --factory-startup --python scripts/blender/render_hull_preview.py -- public/models/blender-hull-V8A.glb out_dir [label]

Renders four views (3/4 bow, 3/4 stern, profile, top-down) with EEVEE so embedded textures show up.
"""
import bpy  # type: ignore
import math
import os
import sys
from mathutils import Vector  # type: ignore

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
glb = os.path.abspath(argv[0]) if argv else None
out_dir = os.path.abspath(argv[1]) if len(argv) > 1 else os.path.abspath("hull_previews")
label = argv[2] if len(argv) > 2 else (os.path.splitext(os.path.basename(glb))[0] if glb else "scene")
os.makedirs(out_dir, exist_ok=True)

if glb:
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.import_scene.gltf(filepath=glb)

# optional 5th arg: comma-separated name fragments to hide (e.g. "ShipHull,Main_Deck" for an x-ray of the internals)
hide = argv[4].split(",") if len(argv) > 4 and argv[4] else []
for o in list(bpy.data.objects):
    if any(h in o.name for h in hide):
        o.hide_render = True

scene = bpy.context.scene
try:
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1600
scene.render.resolution_y = 900
scene.render.film_transparent = False
scene.view_settings.view_transform = 'AgX' if 'AgX' in [v.identifier for v in scene.view_settings.bl_rna.properties['view_transform'].enum_items] else 'Filmic'

world = bpy.data.worlds.new("PreviewWorld") if scene.world is None else scene.world
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.78, 0.84, 0.90, 1.0)
    bg.inputs[1].default_value = 0.9

sun_data = bpy.data.lights.new("PreviewSun", type='SUN')
sun_data.energy = 3.2
sun_data.angle = math.radians(8)
sun = bpy.data.objects.new("PreviewSun", sun_data)
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(35))
scene.collection.objects.link(sun)
fill_data = bpy.data.lights.new("PreviewFill", type='SUN')
fill_data.energy = 1.0
fill = bpy.data.objects.new("PreviewFill", fill_data)
fill.rotation_euler = (math.radians(60), math.radians(-20), math.radians(-150))
scene.collection.objects.link(fill)

cam_data = bpy.data.cameras.new("PreviewCam")
cam_data.lens = 40
cam_data.clip_end = 500
cam = bpy.data.objects.new("PreviewCam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

target = Vector((2.0, 0.0, 0.0))
views = {
    "bow34":   (Vector((40.0, 26.0, 12.0)), Vector((6.0, 0.0, -0.5)), 'PERSP'),
    "stern34": (Vector((-40.0, -24.0, 9.0)), Vector((-8.0, 0.0, -0.5)), 'PERSP'),
    "profile": (Vector((2.5, -70.0, -0.2)), Vector((2.5, 0.0, -0.2)), 'ORTHO'),
    "plan":    (Vector((2.5, 0.0, 60.0)), Vector((2.5, 0.0, 0.0)), 'ORTHO'),
    "stern_low": (Vector((-30.0, -11.0, -3.6)), Vector((-17.0, 0.0, -1.6)), 'PERSP'),
    "xray":    (Vector((-2.0, -30.0, 14.0)), Vector((-2.0, 0.0, -1.0)), 'PERSP'),
    "bow_close": (Vector((30.0, -9.0, 1.5)), Vector((21.0, 0.0, -0.4)), 'PERSP'),
    "house":   (Vector((-1.0, -12.0, 6.5)), Vector((-11.0, 0.0, 2.5)), 'PERSP'),
    "bt_close": (Vector((21.8, -7.5, -1.3)), Vector((18.3, 0.0, -2.3)), 'PERSP'),
    "bt_below": (Vector((20.1, -2.5, -9.0)), Vector((20.1, 0.0, -2.2)), 'PERSP'),
    "lifeboat": (Vector((-22.0, -9.0, 5.5)), Vector((-14.5, 0.0, 2.2)), 'PERSP'),
    "lifeboat_side": (Vector((-15.0, -16.0, 2.6)), Vector((-14.8, 0.0, 2.3)), 'PERSP'),
}
only = argv[3].split(",") if len(argv) > 3 else list(views.keys())
for name, (eye, look, kind) in views.items():
    if name not in only:
        continue
    cam.location = eye
    cam.rotation_euler = (look - eye).to_track_quat('-Z', 'Y').to_euler()
    cam_data.type = kind
    cam_data.ortho_scale = 48.0
    scene.render.filepath = os.path.join(out_dir, f"{label}_{name}.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", scene.render.filepath)
