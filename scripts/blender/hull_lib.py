"""
hull_lib.py - generator for the V8 vessel hull GLB.

The variant script (generate_hull_v8c.py) only holds a config dict and calls build(config).
Everything else lives here: the hull form, procedural textures, internal structure, outfitting and export.

Axes (Blender):  X = stern -> bow,  Y = +port / -starboard,  Z = up.
Exported with export_yup=True, so in Three.js:  x = X,  y = Z,  z = -Y.
That matches src/vessel/vessel-layout.ts (x stern->bow, y up, z port(-) / starboard(+)).

Every position shared with the app (decks, waterline, keel, bulkheads, house, cargo bays, shaft line, rudder stock,
bow thruster tunnel, equipment slots and their display scale) comes from src/vessel/general-arrangement.json, the same
file the app reads. Change the ship there, not here. That file uses three.js axes; the constants below convert them.
Object / material names carry the keywords src/vessel/hull-style.ts uses to pick the translucency.
"""
import bpy  # type: ignore
import bmesh  # type: ignore
import json
import math
import os
import sys
import time
import numpy as np
from mathutils import Vector, Matrix  # type: ignore
from mathutils.bvhtree import BVHTree  # type: ignore

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
MODELS_DIR = os.path.join(PROJECT_ROOT, "public", "models")
GA_JSON = os.path.join(PROJECT_ROOT, "src", "vessel", "general-arrangement.json")
with open(GA_JSON, encoding="utf-8") as _f:
    GA = json.load(_f)

# three.js heights (y) are Blender Z; three.js x is Blender X.
DECK_Z = GA["hull"]["mainDeck"]
WL_Z = GA["hull"]["waterline"]
KEEL_Z = GA["hull"]["keel"]
TANKTOP_Z = GA["hull"]["tankTop"]
BULKHEADS = [b["x"] for b in GA["bulkheads"]]
_H = GA["house"]
HOUSE = dict(x0=_H["minX"], x1=_H["maxX"], hw=_H["halfWidth"], d1=_H["decks"][0], d2=_H["decks"][1], d3=_H["decks"][2],
             roof=_H["wheelhouseRoof"])
BAYS = GA["cargo"]["bays"]
BAY_LEN, BAY_HW = GA["cargo"]["hatchLength"], GA["cargo"]["hatchHalfWidth"]
CARGO_ROWS, CARGO_ROW_PITCH = GA["cargo"]["rows"], GA["cargo"]["rowPitch"]
PROP_X, SHAFT_Z = GA["propulsion"]["propellerX"], GA["propulsion"]["shaftY"]
RUDDER_STOCK_X = GA["propulsion"]["rudderStockX"]
# Bow thruster: forward of the collision bulkhead where the bow is still nearly wall-sided, ~1 D below the waterline.
# The app's 'bow' slot puts its impeller hub on this axis.
BT_X, BT_Z, BT_R = GA["bowThruster"]["x"], GA["bowThruster"]["y"], GA["bowThruster"]["diameter"] / 2


def clamp01(t):
    return max(0.0, min(1.0, t))


def smoothstep(e0, e1, x):
    t = clamp01((x - e0) / (e1 - e0))
    return t * t * (3.0 - 2.0 * t)


def mix(a, b, t):
    return a + (b - a) * t


def V(x, y=0.0, z=0.0):
    return Vector((float(x), float(y), float(z)))


# ==================================================================================================
# 1. SCENE + LAYOUT
# ==================================================================================================
def reset_scene():
    for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.curves,
                 bpy.data.lights, bpy.data.cameras):
        for item in list(coll):
            coll.remove(item)


def equipment_scale(eid):
    return GA["equipmentScale"]["overrides"].get(eid, GA["equipmentScale"]["default"])


def load_layout():
    """Equipment slots from general-arrangement.json -> list of display boxes in BLENDER coordinates."""
    items = []
    for eid, e in GA["equipment"].items():
        p, s = e["position"], e["size"]
        r = math.radians(e.get("rotationDeg", 0.0))
        k = equipment_scale(eid)
        sx, sy, sz = s[0] * k, s[1] * k, s[2] * k
        if abs(math.sin(r)) > 0.5:
            sx, sz = sz, sx
        # Three (x, y, z) -> Blender (x, -z, y)
        items.append(dict(id=eid, space=e["space"], rot=r,
                          x0=p[0] - sx / 2, x1=p[0] + sx / 2,
                          y0=-(p[2] + sz / 2), y1=-(p[2] - sz / 2),
                          z0=p[1], z1=p[1] + sy, cx=p[0], cy=-p[2]))
    return items


# ==================================================================================================
# 2. PROCEDURAL TEXTURES (numpy -> packed images, exported inside the GLB)
# ==================================================================================================
def _vnoise(h, w, cy, cx, rng):
    g = rng.random((cy, cx)).astype(np.float32)
    ys = (np.arange(h) + 0.5) * cy / h
    xs = (np.arange(w) + 0.5) * cx / w
    y0 = np.floor(ys).astype(int)
    x0 = np.floor(xs).astype(int)
    fy = ys - y0
    fx = xs - x0
    fy = fy * fy * (3 - 2 * fy)
    fx = fx * fx * (3 - 2 * fx)
    y0m, y1m, x0m, x1m = y0 % cy, (y0 + 1) % cy, x0 % cx, (x0 + 1) % cx
    a = g[y0m][:, x0m]
    b = g[y0m][:, x1m]
    c = g[y1m][:, x0m]
    d = g[y1m][:, x1m]
    top = a + (b - a) * fx[None, :]
    bot = c + (d - c) * fx[None, :]
    return top + (bot - top) * fy[:, None]


def fbm(h, w, cy, cx, octaves, rng, gain=0.5):
    total = np.zeros((h, w), np.float32)
    amp, norm = 1.0, 0.0
    for o in range(octaves):
        total += amp * _vnoise(h, w, cy * 2 ** o, cx * 2 ** o, rng)
        norm += amp
        amp *= gain
    return total / norm


def _normal_from_height(hgt, strength):
    dx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) * 0.5
    dy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) * 0.5
    n = np.dstack([-dx * strength, -dy * strength, np.ones_like(hgt)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return n * 0.5 + 0.5


def make_image(name, rgb, non_color=False):
    h, w = rgb.shape[:2]
    img = bpy.data.images.new(name, width=w, height=h, alpha=False)
    rgba = np.dstack([np.clip(rgb, 0, 1), np.ones((h, w), np.float32)]).astype(np.float32)
    img.pixels.foreach_set(rgba.ravel())
    img.pack()
    if non_color:
        img.colorspace_settings.name = "Non-Color"
    return img


def _lin(c):
    """Palette colours are linear (like Principled Base Color); textures are stored sRGB, so encode them."""
    return np.array([x ** (1 / 2.2) if x > 0 else 0 for x in c[:3]], np.float32)


def tex_plating(name, color, seed, tile_u=8.0, tile_v=4.0, ppm=160, plate_len=4.0, strake=2.0,
                frame_sp=0.5, frame_lines=0.0, rust=0.0, grime=0.0, mottle=0.06, bead=1.0):
    """Welded shell plating: staggered butts, strake seams, frame dishing, paint mottle, optional rust streaks."""
    rng = np.random.default_rng(seed)
    W, H = int(tile_u * ppm), int(tile_v * ppm)
    x = (np.arange(W) + 0.5) / ppm
    v = (np.arange(H) + 0.5) / ppm
    X, Vv = np.meshgrid(x, v)
    s_idx = np.floor(Vv / strake)
    dv = np.minimum(Vv % strake, strake - Vv % strake)
    off = (s_idx % 2) * plate_len * 0.5
    du = (X - off) % plate_len
    du = np.minimum(du, plate_len - du)
    sw = 0.010
    seam = np.maximum(np.exp(-(dv / sw) ** 2), np.exp(-(du / sw) ** 2))
    dish = 0.5 * (1 - np.cos(2 * np.pi * X / frame_sp))
    hgt = bead * seam * 1.0 - dish * 0.9 * (1 - seam)
    n1 = fbm(H, W, int(tile_v * 2), int(tile_u * 2), 5, rng)
    n2 = fbm(H, W, int(tile_v * 12), int(tile_u * 12), 3, rng)
    base = _lin(color)
    shade = (1.0 - mottle) + mottle * 2 * n1 + 0.03 * (n2 - 0.5)
    shade = shade * (1 - 0.28 * seam)
    if frame_lines > 0:
        fl = np.exp(-(((X + frame_sp / 2) % frame_sp - frame_sp / 2) / 0.008) ** 2)
        shade = shade * (1 - frame_lines * fl)
    albedo = base[None, None, :] * shade[:, :, None]
    if rust > 0 or grime > 0:
        streak = np.zeros((H, W), np.float32)
        for _ in range(int(14 * tile_u / 8)):
            x0 = rng.uniform(0, tile_u)
            si = rng.integers(1, int(tile_v / strake) + 1)
            v0 = si * strake - 0.02
            L = rng.uniform(0.4, 1.6)
            wid = rng.uniform(0.02, 0.07)
            ddx = ((X - x0 + tile_u / 2) % tile_u) - tile_u / 2
            t = (v0 - Vv) / L
            m = (t > 0) & (t < 1)
            streak += np.where(m, np.exp(-(ddx / wid) ** 2) * (1 - np.clip(t, 0, 1)) ** 1.6, 0) * rng.uniform(0.5, 1.0)
        streak = np.clip(streak * (0.6 + 0.8 * n2), 0, 1)
        rust_c = _lin((0.45, 0.20, 0.08))
        a = (rust * streak)[:, :, None]
        albedo = albedo * (1 - a) + rust_c[None, None, :] * a
        g = (grime * (n1 - 0.35)).clip(0, 1)[:, :, None]
        albedo = albedo * (1 - 0.5 * g)
        rust_seam = (rust * 0.5 * seam * (n2 > 0.55)).clip(0, 1)[:, :, None]
        albedo = albedo * (1 - rust_seam) + rust_c[None, None, :] * rust_seam
    return (make_image(name + "_albedo", albedo),
            make_image(name + "_normal", _normal_from_height(hgt, 0.9), non_color=True))


def tex_deck(name, color, seed, tile=4.0, ppm=160, plate=2.0, stiff=0.0, wear=0.15, walkway=None):
    """Non-skid painted deck: plate seams, grit, scuffs; stiff>0 adds raised stiffener ribs (hatch covers)."""
    rng = np.random.default_rng(seed)
    W = H = int(tile * ppm)
    x = (np.arange(W) + 0.5) / ppm
    X, Y = np.meshgrid(x, x)
    du = np.minimum(X % plate, plate - X % plate)
    off = (np.floor(X / plate) % 2) * plate * 0.5
    dv = (Y - off) % plate
    dv = np.minimum(dv, plate - dv)
    seam = np.maximum(np.exp(-(du / 0.009) ** 2), np.exp(-(dv / 0.009) ** 2))
    grit = rng.random((H, W)).astype(np.float32)
    grit = (grit + np.roll(grit, 1, 0) + np.roll(grit, 1, 1)) / 3
    n1 = fbm(H, W, int(tile * 2), int(tile * 2), 5, rng)
    hgt = seam * 0.8 + (grit - 0.5) * 0.35
    if stiff > 0:
        rib = np.exp(-((((X + stiff / 2) % stiff) - stiff / 2) / 0.03) ** 2)
        hgt += rib * 3.0
    shade = 0.9 + 0.16 * (n1 - 0.5) + 0.06 * (grit - 0.5)
    shade *= 1 - 0.25 * seam
    scuff = np.clip((fbm(H, W, int(tile * 6), int(tile * 6), 3, rng) - 0.62) * 4, 0, 1) * wear
    base = _lin(color)
    steel = _lin((0.42, 0.40, 0.38))
    albedo = base[None, None, :] * shade[:, :, None]
    albedo = albedo * (1 - scuff[:, :, None]) + steel[None, None, :] * scuff[:, :, None]
    return (make_image(name + "_albedo", albedo),
            make_image(name + "_normal", _normal_from_height(hgt, 1.2), non_color=True))


def tex_paint(name, color, seed, tile=2.0, ppm=192, panel=0.0, grime=0.0, mottle=0.05):
    """Generic painted steel; panel>0 adds vertical panel seams (superstructure walls)."""
    rng = np.random.default_rng(seed)
    W = H = int(tile * ppm)
    x = (np.arange(W) + 0.5) / ppm
    X, Y = np.meshgrid(x, x)
    n1 = fbm(H, W, int(tile * 3), int(tile * 3), 5, rng)
    n2 = fbm(H, W, int(tile * 16), int(tile * 16), 2, rng)
    hgt = (n2 - 0.5) * 0.4
    shade = (1 - mottle) + mottle * 2 * n1
    if panel > 0:
        pl = np.exp(-((((X + panel / 2) % panel) - panel / 2) / 0.006) ** 2)
        hgt += pl * 1.0
        shade *= 1 - 0.12 * pl
    if grime > 0:
        streak = fbm(H, W, int(tile * 2), int(tile * 6), 4, rng)
        shade *= 1 - grime * 0.6 * np.clip(streak - 0.45, 0, 1)
    albedo = _lin(color)[None, None, :] * shade[:, :, None]
    return (make_image(name + "_albedo", albedo),
            make_image(name + "_normal", _normal_from_height(hgt, 1.0), non_color=True))


def tex_grating(name, color, seed, ppm=256, tile=1.0):
    """Open-grid floor grating for machinery platforms (bars every 3 cm, cross bars every 10 cm)."""
    rng = np.random.default_rng(seed)
    W = H = int(tile * ppm)
    x = (np.arange(W) + 0.5) / ppm
    X, Y = np.meshgrid(x, x)
    bar = np.exp(-((((X + 0.015) % 0.03) - 0.015) / 0.004) ** 2)
    cross = np.exp(-((((Y + 0.05) % 0.10) - 0.05) / 0.005) ** 2)
    g = np.maximum(bar, cross)
    n = fbm(H, W, 4, 4, 3, rng)
    shade = 0.35 + 0.65 * g
    shade *= 0.9 + 0.2 * n
    albedo = _lin(color)[None, None, :] * shade[:, :, None]
    return (make_image(name + "_albedo", albedo),
            make_image(name + "_normal", _normal_from_height(g * 2.0, 1.0), non_color=True))


# ==================================================================================================
# 3. MATERIALS
# ==================================================================================================
def make_mat(name, color, rough=0.55, metal=0.1, tex=None, normal_strength=0.6, emit=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.use_backface_culling = False
    rgba = (color[0], color[1], color[2], alpha)
    m.diffuse_color = rgba
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if alpha < 0.999:
        bsdf.inputs["Alpha"].default_value = alpha
        if hasattr(m, "surface_render_method"):
            m.surface_render_method = "BLENDED"
        if hasattr(m, "blend_method"):
            try:
                m.blend_method = "BLEND"
            except Exception:
                pass
    if emit > 0:
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = rgba
            bsdf.inputs["Emission Strength"].default_value = emit
    if tex:
        albedo, normal = tex
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = albedo
        t.location = (-600, 300)
        nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
        if normal is not None:
            tn = nt.nodes.new("ShaderNodeTexImage")
            tn.image = normal
            tn.location = (-600, -100)
            nm = nt.nodes.new("ShaderNodeNormalMap")
            nm.inputs["Strength"].default_value = normal_strength
            nm.location = (-300, -100)
            nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
            nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    return m


# ==================================================================================================
# 4. MESH BUILDER  (bmesh accumulator: many primitives -> one object per functional group)
# ==================================================================================================
_BOX_CORNERS = [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]
_BOX_FACES = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]


def _basis(d):
    d = d.normalized()
    helper = V(0, 0, 1) if abs(d.z) < 0.9 else V(1, 0, 0)
    a = helper.cross(d).normalized()
    b = d.cross(a)
    return a, b, d


def rot_z(a):
    return Matrix.Rotation(a, 3, "Z")


def rot_y(a):
    return Matrix.Rotation(a, 3, "Y")


def rot_x(a):
    return Matrix.Rotation(a, 3, "X")


class Builder:
    ALL = []

    def __init__(self, name, uv_scale=0.5, sharp_deg=38.0, recalc=True, bevel=0.0):
        self.name = name
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new("UVMap")
        self.flag = self.bm.faces.layers.int.new("has_uv")
        self.mats = []
        self.uv_scale = uv_scale
        self.sharp = math.radians(sharp_deg)
        self.recalc = recalc
        self.bevel = bevel
        Builder.ALL.append(self)

    def slot(self, mat):
        if mat not in self.mats:
            self.mats.append(mat)
        return self.mats.index(mat)

    def vert(self, p):
        return self.bm.verts.new(p)

    def face(self, verts, mat, uvs=None):
        try:
            f = self.bm.faces.new(verts)
        except ValueError:
            return None
        f.material_index = self.slot(mat)
        if uvs:
            for lp, uv in zip(f.loops, uvs):
                lp[self.uv].uv = uv
            f[self.flag] = 1
        return f

    def poly(self, pts, mat, uvs=None):
        return self.face([self.vert(p) for p in pts], mat, uvs)

    # ---- primitives --------------------------------------------------------------------------
    def box(self, c, size, mat, R=None):
        c = Vector(c)
        hs = Vector(size) * 0.5
        vs = []
        for sx, sy, sz in _BOX_CORNERS:
            p = Vector((sx * hs.x, sy * hs.y, sz * hs.z))
            vs.append(self.vert(c + (R @ p if R else p)))
        for f in _BOX_FACES:
            self.face([vs[i] for i in f], mat)

    def box_between(self, x0, x1, y0, y1, z0, z1, mat):
        self.box(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)), mat)

    def cyl(self, p0, p1, r0, mat, r1=None, n=16, caps=True):
        p0, p1 = Vector(p0), Vector(p1)
        r1 = r0 if r1 is None else r1
        d = p1 - p0
        if d.length < 1e-6:
            return
        a, b, dn = _basis(d)
        ring0, ring1 = [], []
        for k in range(n):
            t = 2 * math.pi * k / n
            off = a * math.cos(t) + b * math.sin(t)
            ring0.append(self.vert(p0 + off * r0))
            ring1.append(self.vert(p1 + off * r1))
        L = d.length
        circ = 2 * math.pi * max(r0, r1)
        for k in range(n):
            k2 = (k + 1) % n
            u0, u1 = k / n * circ, (k + 1) / n * circ
            self.face([ring0[k], ring0[k2], ring1[k2], ring1[k]], mat,
                      [(u0 * self.uv_scale, 0), (u1 * self.uv_scale, 0), (u1 * self.uv_scale, L * self.uv_scale), (u0 * self.uv_scale, L * self.uv_scale)])
        if caps:
            if r1 > 1e-5:
                self.face(ring1, mat)
            if r0 > 1e-5:
                self.face(list(reversed(ring0)), mat)

    def tube(self, pts, r, mat, n=8, caps=True, closed=False):
        pts = [Vector(p) for p in pts]
        if len(pts) < 2:
            return
        rings = []
        prev_a = None
        for i, p in enumerate(pts):
            if closed:
                t = (pts[(i + 1) % len(pts)] - pts[i - 1])
            else:
                t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)])
            t.normalize()
            if prev_a is None:
                a, b, _ = _basis(t)
            else:
                a = (prev_a - t * prev_a.dot(t)).normalized()
                b = t.cross(a)
            prev_a = a
            rings.append([self.vert(p + (a * math.cos(2 * math.pi * k / n) + b * math.sin(2 * math.pi * k / n)) * r) for k in range(n)])
        segs = len(pts) if closed else len(pts) - 1
        for i in range(segs):
            r0, r1 = rings[i], rings[(i + 1) % len(pts)]
            for k in range(n):
                k2 = (k + 1) % n
                self.face([r0[k], r0[k2], r1[k2], r1[k]], mat)
        if caps and not closed:
            self.face(rings[-1], mat)
            self.face(list(reversed(rings[0])), mat)

    def torus(self, c, axis, R, r, mat, n1=24, n2=8, arc=2 * math.pi):
        c = Vector(c)
        a, b, d = _basis(Vector(axis))
        full = arc >= 2 * math.pi - 1e-6
        cnt = n1 if full else n1 + 1
        rings = []
        for i in range(cnt):
            t = arc * i / n1
            radial = a * math.cos(t) + b * math.sin(t)
            centre = c + radial * R
            rings.append([self.vert(centre + (radial * math.cos(2 * math.pi * k / n2) + d * math.sin(2 * math.pi * k / n2)) * r) for k in range(n2)])
        segs = n1 if full else n1
        for i in range(segs):
            r0, r1 = rings[i], rings[(i + 1) % cnt]
            for k in range(n2):
                k2 = (k + 1) % n2
                self.face([r0[k], r1[k], r1[k2], r0[k2]], mat)

    def ellipsoid(self, c, radii, mat, R=None, nu=20, nv=10):
        c = Vector(c)
        rows = []
        for j in range(1, nv):
            phi = math.pi * j / nv - math.pi / 2
            row = []
            for i in range(nu):
                th = 2 * math.pi * i / nu
                p = Vector((math.cos(phi) * math.cos(th) * radii[0], math.cos(phi) * math.sin(th) * radii[1], math.sin(phi) * radii[2]))
                row.append(self.vert(c + (R @ p if R else p)))
            rows.append(row)
        bot = self.vert(c + ((R @ V(0, 0, -radii[2])) if R else V(0, 0, -radii[2])))
        top = self.vert(c + ((R @ V(0, 0, radii[2])) if R else V(0, 0, radii[2])))
        for i in range(nu):
            i2 = (i + 1) % nu
            self.face([bot, rows[0][i2], rows[0][i]], mat)
            self.face([top, rows[-1][i], rows[-1][i2]], mat)
            for j in range(len(rows) - 1):
                self.face([rows[j][i], rows[j][i2], rows[j + 1][i2], rows[j + 1][i]], mat)

    def loft(self, rings, mat, cap0=True, cap1=True, closed=True):
        vr = [[self.vert(Vector(p)) for p in ring] for ring in rings]
        n = len(vr[0])
        segs = n if closed else n - 1
        for i in range(len(vr) - 1):
            for k in range(segs):
                k2 = (k + 1) % n
                self.face([vr[i][k], vr[i][k2], vr[i + 1][k2], vr[i + 1][k]], mat)
        if cap0 and closed:
            self.face(list(reversed(vr[0])), mat)
        if cap1 and closed:
            self.face(vr[-1], mat)
        return vr

    def prism(self, pts, offset, mat):
        """Extrude a planar polygon loop by offset (sides + caps)."""
        off = Vector(offset)
        return self.loft([[Vector(p) for p in pts], [Vector(p) + off for p in pts]], mat)

    def strip(self, a_pts, b_pts, mat):
        """Quad strip between two polylines of equal length (open plate)."""
        va = [self.vert(Vector(p)) for p in a_pts]
        vb = [self.vert(Vector(p)) for p in b_pts]
        for i in range(len(va) - 1):
            self.face([va[i], va[i + 1], vb[i + 1], vb[i]], mat)

    def add_mesh(self, verts, faces, mat):
        vs = [self.vert(Vector(p)) for p in verts]
        for f in faces:
            self.face([vs[i] for i in f], mat)

    # ---- finish ------------------------------------------------------------------------------
    def finish(self):
        bm = self.bm
        if len(bm.faces) == 0:
            bm.free()
            return None
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        if self.recalc:
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.normal_update()
        s = self.uv_scale
        for f in bm.faces:
            f.smooth = True
            if not f[self.flag]:
                n = f.normal
                ax = max(range(3), key=lambda i: abs(n[i]))
                for lp in f.loops:
                    co = lp.vert.co
                    if ax == 0:
                        lp[self.uv].uv = (co.y * s, co.z * s)
                    elif ax == 1:
                        lp[self.uv].uv = (co.x * s, co.z * s)
                    else:
                        lp[self.uv].uv = (co.x * s, co.y * s)
        for e in bm.edges:
            if len(e.link_faces) == 2:
                try:
                    e.smooth = e.calc_face_angle(math.pi) < self.sharp
                except ValueError:
                    e.smooth = False
        bm.faces.layers.int.remove(self.flag)
        me = bpy.data.meshes.new(self.name)
        bm.to_mesh(me)
        bm.free()
        obj = bpy.data.objects.new(self.name, me)
        bpy.context.scene.collection.objects.link(obj)
        for m in self.mats:
            me.materials.append(m)
        if self.bevel > 0:
            md = obj.modifiers.new("Bevel", "BEVEL")
            md.width = self.bevel
            md.segments = 2
            md.limit_method = "ANGLE"
            md.harden_normals = False
        return obj


# ==================================================================================================
# 5. HULL FORM
# ==================================================================================================
class HullForm:
    """V7-derived lines (same envelope, so every equipment slot still fits) with:
       a true flat-of-bottom + round bilge midships, a lower stern counter that tucks the rudder under the hull,
       tunable bulb / flare / stem rake / forecastle, and even, girth-based row sampling (no staircase artefacts)."""

    def __init__(self, cfg):
        self.S = cfg.get("stretch", 6.0)
        self.BS = cfg.get("beam_scale", 1.15)
        self.KD = cfg.get("keel_drop", 0.5)
        self.bulb = cfg.get("bulb", 1.0)
        self.flare = cfg.get("flare", 1.0)
        self.rake = cfg.get("stem_rake", 1.62)
        self.fc_rise = cfg.get("fc_rise", 0.68)
        self.fc_step = cfg.get("fc_step", 0.0)
        self.fc_step_x = cfg.get("fc_step_x", 18.0)
        self.bulwark = cfg.get("bulwark", 0.36)
        self.counter = cfg.get("counter", (-1.55, -0.35))
        self.flat = cfg.get("flat_half", 2.50)
        self.stern_rise = cfg.get("stern_rise", 0.14)
        # the forecastle step happens at a fixed X; convert to the bow loft parameter
        t = clamp01((self.fc_step_x - 11.2 - self.S) / 7.7)
        self.step_u = 0.70 + 0.30 * (math.asin(t) / (math.pi / 2))

    # ---- profiles (all in the V7 pre-warp frame: keel -2.65, y before beam scale, x before stretch) ----
    def deepen(self, z):
        t = clamp01((-1.0 - z) / (-1.0 + 2.65))
        return z - self.KD * t * t * (3 - 2 * t)

    def stem_x(self, z):
        bulb_bell = math.exp(-((z + 1.92) / 0.52) ** 2)
        neck = math.exp(-((z + 1.12) / 0.48) ** 2)
        upper = smoothstep(-1.25, 1.58, z) ** 1.15
        x_base = 17.35 + 1.52 * self.bulb * bulb_bell - 0.32 * neck + self.rake * upper
        return mix(16.25, x_base, smoothstep(-2.65, -2.18, z))

    def stern_x(self, z):
        over = smoothstep(self.counter[0], self.counter[1], z) ** 1.15
        foot = 1.0 - smoothstep(-2.65, -1.65, z)
        return -16.55 - 3.15 * over - 0.55 * foot

    def z_keel(self, u):
        return -2.65 + 0.48 * ((1 - smoothstep(0, 0.12, u)) ** 1.6) + 0.68 * (smoothstep(0.92, 1.0, u) ** 2) * self.bulb

    def z_sheer(self, u):
        z = DECK_Z + self.fc_rise * (smoothstep(0.73, 0.98, u) ** 1.25) + self.stern_rise * ((1 - smoothstep(0, 0.14, u)) ** 1.5)
        if self.fc_step > 0:
            z += self.fc_step * smoothstep(self.step_u - 0.0045, self.step_u + 0.0045, u)
        return z

    def x_at(self, u, z):
        if u <= 0.70:
            return mix(self.stern_x(z), 11.2, u / 0.70)
        th = (u - 0.70) / 0.30 * (math.pi / 2)
        return mix(11.2, self.stem_x(z), math.sin(th))

    def flat_at(self, u):
        return self.flat * smoothstep(0.05, 0.26, u) * (1 - smoothstep(0.71, 0.86, u))

    def mid_half(self, u, z):
        fl = self.flat_at(u)
        R = 3.35 - fl
        dz = z + 2.65
        if dz >= R:
            return 3.35
        return fl + math.sqrt(max(0.0, R * R - (R - max(0.0, dz)) ** 2))

    def bow_w(self, z):
        bulb_v = clamp01(1 - ((z + 1.92) / (0.74 * math.sqrt(self.bulb))) ** 2)
        w_bulb = 0.88 * self.bulb * math.sqrt(bulb_v)
        ft = smoothstep(-1.45, 1.58, z)
        w_flare = 0.38 + 2.55 * (ft ** (0.82 / self.flare))
        return mix(w_bulb, w_flare, smoothstep(-1.55, -0.95, z))

    def stern_w(self, z):
        skeg = 0.22 + 0.16 * math.exp(-((z + 2.22) / 0.28) ** 2)
        upper = 2.68 * (smoothstep(-1.65, 0.25, z) ** 0.68)
        return mix(skeg, max(skeg, upper), smoothstep(-2.35, -1.10, z))

    def y_side(self, u, z):
        if u >= 1 - 1e-6:
            return 0.0
        w_mid = self.mid_half(u, z)
        if u < 0.24:
            t = u / 0.24
            th = (1 - t) * math.pi / 2
            y = mix(self.stern_w(z), w_mid, smoothstep(0, 1, t))
            keep = smoothstep(-0.85, 0.15, z)
            end = mix(math.cos(th) ** 0.85, 1.0, keep)
            if u < 0.04:
                y *= mix(end, 1.0, u / 0.04)
        elif u <= 0.70:
            y = w_mid
        else:
            tb = (u - 0.70) / 0.30
            th = tb * math.pi / 2
            wc = mix(w_mid, self.bow_w(z), smoothstep(0, 0.55, tb))
            p = mix(0.72, 1.08, math.exp(-((z + 1.05) / 0.55) ** 2))
            y = wc * (math.cos(th) ** p)
        x = self.x_at(u, z)
        r2 = ((x - 16.85) / 0.55) ** 2 + ((z - 0.55) / 0.32) ** 2
        if r2 < 1:
            y += 0.16 * (1 - r2) ** 2
        return max(0.0, y)

    def P(self, u, shift, z):
        return V(self.x_at(u, z) + shift, self.y_side(u, z) * self.BS, self.deepen(z))

    def deck_z(self, u):
        zs = self.z_sheer(u)
        if self.fc_step > 0:
            return DECK_Z if u < self.step_u + 0.0046 else max(DECK_Z, zs - self.bulwark)
        return max(DECK_Z, zs - self.bulwark)

    # ---- sampling ------------------------------------------------------------------------------
    def rows(self, ds=0.24):
        S = self.S
        cand = [(0.70 * k / 1600, 0.0) for k in range(1600)]
        if S > 0:
            n2 = int(S / 0.02)
            cand += [(0.70, S * k / n2) for k in range(n2 + 1)]
        else:
            cand += [(0.70, 0.0)]
        cand += [(0.70 + 0.30 * k / 1600, S) for k in range(1, 1601)]
        if self.fc_step > 0:
            cand += [(self.step_u - 0.0045 + 0.009 * k / 40, S) for k in range(41)]
            cand.sort(key=lambda c: (c[0], c[1]))
        probes = []
        for u, s in cand:
            zk, zs = self.z_keel(u), self.z_sheer(u)
            pts = [self.P(u, s, min(zs, max(zk + 0.01, zz))) for zz in (zs, 0.0, -1.0, -1.92, zk + 0.01)]
            probes.append(pts)
        cum = [0.0]
        for i in range(1, len(probes)):
            d = max((probes[i][k] - probes[i - 1][k]).length for k in range(5))
            cum.append(cum[-1] + d)
        total = cum[-1]
        n = max(2, int(math.ceil(total / ds)))
        out, j = [], 0
        for i in range(n + 1):
            t = total * i / n
            while j < len(cum) - 1 and cum[j + 1] < t:
                j += 1
            k = j if j + 1 >= len(cum) or (t - cum[j]) < (cum[j + 1] - t) else j + 1
            if not out or out[-1] != cand[k]:
                out.append(cand[k])
        if out[-1] != cand[-1]:
            out.append(cand[-1])
        return out

    def section(self, u, shift, nv):
        zk, zs = self.z_keel(u), self.z_sheer(u)
        raw = []
        yb = self.y_side(u, zk)
        for k in range(12):
            raw.append(V(self.x_at(u, zk) + shift, yb * self.BS * k / 12, self.deepen(zk)))
        for k in range(301):
            z = zk + (zs - zk) * k / 300
            raw.append(self.P(u, shift, z))
        g = [0.0]
        for i in range(1, len(raw)):
            g.append(g[-1] + (raw[i] - raw[i - 1]).length)
        total = g[-1]
        out, j = [], 0
        for i in range(nv + 1):
            t = total * i / nv
            while j < len(g) - 2 and g[j + 1] < t:
                j += 1
            seg = max(1e-9, g[j + 1] - g[j])
            f = clamp01((t - g[j]) / seg)
            out.append((raw[j].lerp(raw[j + 1], f), t))
        return out


# ==================================================================================================
# 6. BUILD CONTEXT
# ==================================================================================================
class Ctx:
    def __init__(self, cfg):
        self.cfg = cfg
        self.feat = set(cfg.get("features", []))
        self.form = HullForm(cfg.get("form", {}))
        self.pal = cfg["palette"]
        self.layout = load_layout()
        self.mats = {}
        self.bvh = None
        self.deck_rows = []   # (x, deck_z, half_width)

    def has(self, f):
        return f in self.feat

    # ---- hull queries (BVH on the finished shell) -------------------------------------------
    def hw(self, x, z):
        """Inner half-width of the shell at (x, z); 0 when the point is outside the hull."""
        hit = self.bvh.ray_cast(V(x, 0.0, z), V(0, 1, 0), 30.0)
        return hit[3] if hit[0] is not None else 0.0

    def keel_at(self, x, y=0.0):
        hit = self.bvh.ray_cast(V(x, y, 0.3), V(0, 0, -1), 10.0)
        return hit[0].z if hit[0] is not None else None

    def deck_at(self, x):
        r = self.deck_rows
        if x <= r[0][0]:
            return r[0][1], r[0][2]
        for i in range(1, len(r)):
            if x <= r[i][0]:
                t = (x - r[i - 1][0]) / max(1e-9, r[i][0] - r[i - 1][0])
                return mix(r[i - 1][1], r[i][1], t), mix(r[i - 1][2], r[i][2], t)
        return r[-1][1], r[-1][2]


# ==================================================================================================
# 7. SHELL + DECKS
# ==================================================================================================
def build_shell(ctx):
    F = ctx.form
    nv = ctx.cfg.get("girth_segments", 60)
    rows = F.rows(ctx.cfg.get("row_spacing", 0.22))
    TU, TV = 8.0, 4.0
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    grids = {1: [], -1: []}
    sections = []
    for (u, s) in rows:
        sec = F.section(u, s, nv)
        sections.append(sec)
        for side in (1, -1):
            grids[side].append([bm.verts.new(V(p.x, side * p.y, p.z)) for p, _ in sec])
    for side in (1, -1):
        g = grids[side]
        for i in range(len(rows) - 1):
            for j in range(nv):
                quad = [g[i][j], g[i + 1][j], g[i + 1][j + 1], g[i][j + 1]]
                if side < 0:
                    quad.reverse()
                try:
                    f = bm.faces.new(quad)
                except ValueError:
                    continue
                for lp in f.loops:
                    pass
                uv_src = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
                if side < 0:
                    uv_src.reverse()
                for lp, (ii, jj) in zip(f.loops, uv_src):
                    p, gth = sections[ii][jj]
                    lp[uvl].uv = (p.x / TU, gth / TV)
    # transom: strips across row 0
    s0 = sections[0]
    for j in range(nv):
        a, b = s0[j][0], s0[j + 1][0]
        if a.y < 2e-3 and b.y < 2e-3:
            continue
        quad = [grids[-1][0][j], grids[-1][0][j + 1], grids[1][0][j + 1], grids[1][0][j]]
        try:
            f = bm.faces.new(quad)
        except ValueError:
            continue
        for lp in f.loops:
            lp[uvl].uv = (lp.vert.co.y / TU, lp.vert.co.z / TV)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-5)
    # gentle fairing (keeps open sheer edge exact)
    for _ in range(2):
        inner = [v for v in bm.verts if not v.is_boundary and abs(v.co.y) > 1e-4]
        centre = [v for v in bm.verts if not v.is_boundary and abs(v.co.y) <= 1e-4]
        bmesh.ops.smooth_vert(bm, verts=inner, factor=0.4, use_axis_x=True, use_axis_y=True, use_axis_z=True)
        bmesh.ops.smooth_vert(bm, verts=centre, factor=0.4, use_axis_x=True, use_axis_y=False, use_axis_z=True)
    # clean boot-top band: cut the shell exactly at the band edges, then colour by height
    lo, hi = ctx.pal["boot_band"]
    for zc in (lo, hi):
        geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
        bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=(0, 0, zc), plane_no=(0, 0, 1))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    # make sure the side shell faces outward
    probe = [f for f in bm.faces if abs(f.calc_center_median().x) < 2 and abs(f.calc_center_median().z) < 0.3]
    if probe:
        c = probe[0].calc_center_median()
        if probe[0].normal.y * c.y < 0:
            for f in bm.faces:
                f.normal_flip()
    m_top, m_under, m_boot = ctx.mats["hull_top"], ctx.mats["hull_under"], ctx.mats["hull_boot"]
    for f in bm.faces:
        zc = f.calc_center_median().z
        f.material_index = 1 if zc < lo else (2 if zc < hi else 0)
        f.smooth = True
    for e in bm.edges:
        if len(e.link_faces) == 2:
            try:
                e.smooth = e.calc_face_angle(math.pi) < math.radians(50)
            except ValueError:
                pass
    ctx.bvh = BVHTree.FromBMesh(bm)
    me = bpy.data.meshes.new("ShipHull")
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new("ShipHull", me)
    bpy.context.scene.collection.objects.link(obj)
    for m in (m_top, m_under, m_boot):
        me.materials.append(m)
    ctx.shell_obj = obj
    # deck rows (x, z, half width) from the exact form, used by every deck fitting
    ctx.deck_rows = []
    for (u, s) in rows:
        dz = F.deck_z(u)
        p = F.P(u, s, dz)
        ctx.deck_rows.append((p.x, dz, p.y, u, s))
    ctx.rows = rows
    return obj


def build_decks(ctx):
    F = ctx.form
    deck = Builder("Main_Deck", uv_scale=0.25)
    md = ctx.mats["deck"]
    ncross = 10
    prev = None
    walls = []
    for (x, dz, hw, u, s) in ctx.deck_rows:
        hw = max(0.0, hw - 0.01)
        row = [V(x, -hw + 2 * hw * k / ncross, dz) for k in range(ncross + 1)]
        if prev is not None:
            if abs(prev[0].z - row[0].z) > 0.12:
                walls.append((prev, row))
            else:
                deck.strip(prev, row, md)
        prev = row
    for prev, row in walls:
        # forecastle front bulkhead (the deck steps up here)
        x = row[0].x
        hw = max(abs(prev[0].y), abs(row[0].y))
        deck.poly([V(x, -hw, prev[0].z), V(x, hw, prev[0].z), V(x, hw, row[0].z), V(x, -hw, row[0].z)], ctx.mats["house"])
        ctx.fc_front = (x, prev[0].z, row[0].z, hw)
    return deck.finish()


# ==================================================================================================
# 8. INTERNAL STRUCTURE
# ==================================================================================================


def section_outline(ctx, x, z_top, n=36, inset=0.0):
    zk = ctx.keel_at(x)
    if zk is None:
        return []
    pts = []
    for k in range(n + 1):
        z = mix(zk + 0.004, z_top, (k / n) ** 1.3)
        w = ctx.hw(x, z)
        if w > 0:
            pts.append((max(0.0, w - inset), z))
    return pts


def build_internal(ctx):
    mi = ctx.mats["internal"]
    # --- tank top (double bottom) with a recessed well for the propulsion motor -------------------------------
    motor = next((e for e in ctx.layout if e["id"] == "motor"), None)
    well = (motor["x0"] - 0.18, motor["x1"] + 0.18, max(abs(motor["y0"]), abs(motor["y1"])) + 0.22) if motor else None
    tt = Builder("EngineRoom_Conforming_TankTop", uv_scale=0.5)
    xs = np.arange(BULKHEADS[0] + 0.02, BULKHEADS[-1] - 0.02, 0.25).tolist() + [BULKHEADS[-1] - 0.02]
    for a, b in zip(xs[:-1], xs[1:]):
        wa, wb = ctx.hw(a, TANKTOP_Z) - 0.01, ctx.hw(b, TANKTOP_Z) - 0.01
        if wa <= 0 or wb <= 0:
            continue
        if well and a >= well[0] - 1e-6 and b <= well[1] + 1e-6:
            for sgn in (1, -1):
                tt.poly([V(a, sgn * well[2], TANKTOP_Z), V(b, sgn * well[2], TANKTOP_Z), V(b, sgn * wb, TANKTOP_Z), V(a, sgn * wa, TANKTOP_Z)], mi)
        else:
            tt.poly([V(a, -wa, TANKTOP_Z), V(b, -wb, TANKTOP_Z), V(b, wb, TANKTOP_Z), V(a, wa, TANKTOP_Z)], mi)
    if well:
        wz = motor["z0"] - 0.025
        x0, x1, hy = well[0], well[1], well[2]
        x0 = xs[min(range(len(xs)), key=lambda i: abs(xs[i] - x0))]
        x1 = xs[min(range(len(xs)), key=lambda i: abs(xs[i] - x1))]
        tt.poly([V(x0, -hy, wz), V(x1, -hy, wz), V(x1, hy, wz), V(x0, hy, wz)], mi)
        for (p0, p1) in [((x0, -hy), (x1, -hy)), ((x1, -hy), (x1, hy)), ((x1, hy), (x0, hy)), ((x0, hy), (x0, -hy))]:
            tt.poly([V(p0[0], p0[1], wz), V(p1[0], p1[1], wz), V(p1[0], p1[1], TANKTOP_Z), V(p0[0], p0[1], TANKTOP_Z)], mi)
    tt.finish()

    # --- watertight bulkheads, following the shell exactly -----------------------------------------------------
    for k, bx in enumerate(BULKHEADS):
        b = Builder(f"Watertight_Bulkhead_{k + 1}", uv_scale=0.5)
        top = ctx.deck_at(bx)[0] - 0.01
        pts = section_outline(ctx, bx, top, n=40, inset=0.005)
        for (y0, z0), (y1, z1) in zip(pts[:-1], pts[1:]):
            b.poly([V(bx, -y0, z0), V(bx, y0, z0), V(bx, y1, z1), V(bx, -y1, z1)], mi)
        if ctx.has("structure"):
            ms = ctx.mats["frame"]
            ymax = max(p[0] for p in pts) if pts else 0
            for yy in np.arange(-ymax + 0.5, ymax - 0.3, 0.6):
                zb = next((z for (w, z) in pts if w >= abs(yy)), None)
                if zb is None:
                    continue
                b.box(((bx + 0.05) if bx < 0 else (bx - 0.05), yy, (zb + top) / 2), (0.10, 0.025, top - zb), ms)
        b.finish()

    # --- equipment foundation seats + machinery platforms derived from vessel-layout.ts -------------------------
    pads = Builder("Pad_Foundations", uv_scale=1.0)
    mp = ctx.mats["pad"]
    platform_items = []
    for e in ctx.layout:
        if e["space"] != "hull" or e["id"] in ("bow",):
            continue
        top = e["z0"] - 0.033
        if e["id"] == "motor":
            top = e["z0"] - 0.02
        pads.box_between(e["x0"] - 0.06, e["x1"] + 0.06, e["y0"] - 0.05, e["y1"] + 0.05, top - 0.05, top, mp)
        # holding-down bolts
        for xx in (e["x0"] + 0.02, e["x1"] - 0.02):
            for yy in (e["y0"] - 0.02, e["y1"] + 0.02):
                pads.cyl((xx, yy, top), (xx, yy, top + 0.025), 0.012, ctx.mats["hardware"], n=6)
        if e["z0"] > TANKTOP_Z + 0.4:
            platform_items.append(e)
    pads.finish()
    build_platforms(ctx, platform_items)

    if ctx.has("structure"):
        build_structure(ctx)
    if ctx.has("tanks"):
        build_tanks(ctx)


def _compartment(x):
    for i in range(len(BULKHEADS) - 1):
        if BULKHEADS[i] <= x <= BULKHEADS[i + 1]:
            return i
    return -1


def build_platforms(ctx, items):
    mi = ctx.mats["grating"]
    rail = ctx.mats["rail"]
    items = sorted(items, key=lambda e: e["x0"])
    clusters = []
    for e in items:
        if clusters:
            c = clusters[-1]
            if abs(c[0]["z0"] - e["z0"]) < 0.08 and e["x0"] - max(i["x1"] for i in c) < 1.5 and _compartment(e["cx"]) == _compartment(c[0]["cx"]):
                c.append(e)
                continue
        clusters.append([e])
    floor_items = [e for e in ctx.layout if e["space"] == "hull" and e["z0"] <= TANKTOP_Z + 0.4]
    plat = Builder("Machinery_Mezzanine_Platforms", uv_scale=1.0)
    steel = Builder("Mezzanine_Pillars_Rails", uv_scale=1.0)
    for ci, c in enumerate(clusters):
        lvl = c[0]["z0"] - 0.033
        comp = _compartment(c[0]["cx"])
        x0 = min(e["x0"] for e in c) - 0.45
        x1 = max(e["x1"] for e in c) + 0.45
        if comp >= 0:
            x0 = max(x0, BULKHEADS[comp] + 0.08)
            x1 = min(x1, BULKHEADS[comp + 1] - 0.08)
        y0 = min(e["y0"] for e in c) - 0.45
        y1 = max(e["y1"] for e in c) + 0.45
        wmax = min(ctx.hw(x0, lvl - 0.05), ctx.hw(x1, lvl - 0.05)) - 0.08
        y0, y1 = max(y0, -wmax), min(y1, wmax)
        plat.box_between(x0, x1, y0, y1, lvl - 0.04, lvl, mi)
        # toe plates
        for (a, b) in [((x0, y0), (x1, y0)), ((x0, y1), (x1, y1)), ((x0, y0), (x0, y1)), ((x1, y0), (x1, y1))]:
            steel.box_between(min(a[0], b[0]) - 0.01, max(a[0], b[0]) + 0.01, min(a[1], b[1]) - 0.01, max(a[1], b[1]) + 0.01, lvl, lvl + 0.06, rail)
        # handrails (posts + two courses) on the long edges and the end away from the ladder
        rh = 0.42
        for yy in (y0 + 0.02, y1 - 0.02):
            n = max(2, int((x1 - x0) / 0.8) + 1)
            for k in range(n):
                px = mix(x0 + 0.02, x1 - 0.02, k / (n - 1))
                steel.cyl((px, yy, lvl), (px, yy, lvl + rh), 0.012, rail, n=6)
            for hgt in (rh * 0.5, rh):
                steel.cyl((x0 + 0.02, yy, lvl + hgt), (x1 - 0.02, yy, lvl + hgt), 0.011, rail, n=6)
        for hgt in (rh * 0.5, rh):
            steel.cyl((x1 - 0.02, y0 + 0.02, lvl + hgt), (x1 - 0.02, y1 - 0.02, lvl + hgt), 0.011, rail, n=6)
        # pillars to the tank top where there is no equipment underneath
        cands = []
        for k in range(int((x1 - x0) / 1.1) + 1):
            px = mix(x0 + 0.12, x1 - 0.12, k / max(1, int((x1 - x0) / 1.1)))
            for py in (y0 + 0.12, y1 - 0.12):
                cands.append((px, py))
        for (px, py) in cands:
            clear = all(not (e["x0"] - 0.1 < px < e["x1"] + 0.1 and e["y0"] - 0.1 < py < e["y1"] + 0.1) for e in floor_items)
            if clear:
                steel.cyl((px, py, TANKTOP_Z), (px, py, lvl - 0.04), 0.035, ctx.mats["hardware"], n=10)
        # inclined ladder at the aft end, down to the tank top if the space is free
        lx = x0 - 0.05
        ly = (y0 + y1) / 2
        span = lvl - TANKTOP_Z
        foot = lx - span * 0.55
        clear = all(not (e["x0"] - 0.2 < (foot + lx) / 2 < e["x1"] + 0.2 and e["y0"] - 0.2 < ly < e["y1"] + 0.2) for e in floor_items)
        if clear and comp >= 0 and foot > BULKHEADS[comp] + 0.1:
            for sy in (-0.22, 0.22):
                steel.cyl((foot, ly + sy, TANKTOP_Z), (lx, ly + sy, lvl), 0.018, rail, n=6)
            nst = int(span / 0.18)
            for k in range(1, nst):
                t = k / nst
                steel.box((mix(foot, lx, t), ly, mix(TANKTOP_Z, lvl, t)), (0.09, 0.42, 0.015), mi)
    plat.finish()
    steel.finish()


def build_structure(ctx):
    """Engineering variant: transverse frames, web frames, floors, girders, stringers, deck beams."""
    mf = ctx.mats["frame"]
    fr = Builder("Internal_Frames_Transverse", uv_scale=1.0, recalc=False)
    flo = Builder("Internal_DoubleBottom_Floors", uv_scale=1.0, recalc=False)
    lon = Builder("Internal_Longitudinal_Girders", uv_scale=1.0, recalc=False)
    x = BULKHEADS[0] + 0.5
    xs = []
    while x < BULKHEADS[-1] - 0.2:
        if all(abs(x - b) > 0.2 for b in BULKHEADS):
            xs.append(round(x, 3))
        x += 0.5
    for x in xs:
        web = abs((x / 2.0) - round(x / 2.0)) < 1e-6
        depth = 0.32 if web else 0.10
        top = ctx.deck_at(x)[0] - 0.015
        pts = section_outline(ctx, x, top, n=26)
        side = [(w, z) for (w, z) in pts if z >= TANKTOP_Z]
        if len(side) >= 2:
            for sgn in (1, -1):
                outer, inner = [], []
                for i, (w, z) in enumerate(side):
                    a = side[max(0, i - 1)]
                    b = side[min(len(side) - 1, i + 1)]
                    ty, tz = b[0] - a[0], b[1] - a[1]
                    L = math.hypot(ty, tz) or 1
                    ny, nz = -tz / L, ty / L        # inward normal (towards centreline)
                    if ny > 0:
                        ny, nz = -ny, -nz
                    outer.append(V(x, sgn * (w - 0.004), z))
                    inner.append(V(x, sgn * (w - 0.004 + ny * depth), z + nz * depth))
                fr.strip(outer, inner, mf)
            # deck beam from the side to the hatch girder
            w_top = side[-1][0]
            for sgn in (1, -1):
                fr.poly([V(x, sgn * (w_top - 0.01), top), V(x, sgn * 2.75, top), V(x, sgn * 2.75, top - (0.24 if web else 0.10)), V(x, sgn * (w_top - 0.01), top - (0.24 if web else 0.10))], mf)
        # double-bottom plate floor every metre
        if abs(x - round(x)) < 1e-6:
            bot = [(w, z) for (w, z) in pts if z <= TANKTOP_Z]
            if len(bot) >= 2:
                bot.append((ctx.hw(x, TANKTOP_Z - 0.002), TANKTOP_Z - 0.002))
                for (y0, z0), (y1, z1) in zip(bot[:-1], bot[1:]):
                    flo.poly([V(x, -y0 + 0.004, z0), V(x, y0 - 0.004, z0), V(x, y1 - 0.004, z1), V(x, -y1 + 0.004, z1)], mf)
    # centre + side girders (double bottom), side stringers, hatch side girders
    gx = np.arange(BULKHEADS[0] + 0.05, BULKHEADS[-1] - 0.05, 0.4).tolist()
    for gy in (0.0, 1.6, -1.6):
        top_pts, bot_pts = [], []
        for x in gx:
            zb = ctx.keel_at(x, gy)
            if zb is None or zb > TANKTOP_Z - 0.05:
                if top_pts:
                    lon.strip(bot_pts, top_pts, mf)
                top_pts, bot_pts = [], []
                continue
            top_pts.append(V(x, gy, TANKTOP_Z - 0.003))
            bot_pts.append(V(x, gy, zb + 0.003))
        if len(top_pts) > 1:
            lon.strip(bot_pts, top_pts, mf)
    for zs in (-0.85, 0.05):
        for sgn in (1, -1):
            a, b = [], []
            for x in gx:
                w = ctx.hw(x, zs)
                if w <= 0.2:
                    continue
                a.append(V(x, sgn * (w - 0.004), zs))
                b.append(V(x, sgn * (w - 0.26), zs))
            if len(a) > 1:
                lon.strip(a, b, mf)
    hx = np.arange(-6.1, 11.6, 0.4).tolist()
    for sgn in (1, -1):
        lon.strip([V(x, sgn * 2.75, DECK_Z - 0.012) for x in hx], [V(x, sgn * 2.75, DECK_Z - 0.34) for x in hx], mf)
        lon.strip([V(x, sgn * 2.75, DECK_Z - 0.34) for x in hx], [V(x, sgn * 2.62, DECK_Z - 0.34) for x in hx], mf)
    # hold pillars under the hatch girders
    for x in (-2.0, 1.6, 5.5, 8.4):
        for sgn in (1, -1):
            lon.cyl((x, sgn * 2.75, TANKTOP_Z), (x, sgn * 2.75, DECK_Z - 0.34), 0.05, mf, n=10)
    fr.finish()
    flo.finish()
    lon.finish()


def build_tanks(ctx):
    tanks = [
        ("Ballast_AftPeak", -19.0, -15.25, None, "tank_ballast"),
        ("Fuel_MGO_ER", -12.4, -7.2, TANKTOP_Z - 0.02, "tank_fuel"),
        ("LubeOil_Sump", -7.1, -5.0, TANKTOP_Z - 0.02, "tank_lube"),
        ("Fuel_HFO_ER", -4.9, -3.05, TANKTOP_Z - 0.02, "tank_fuel"),
        ("Ballast_DB_Hold", -2.95, 10.95, TANKTOP_Z - 0.02, "tank_ballast"),
        ("FreshWater_DB_Aux", 11.05, 17.15, TANKTOP_Z - 0.02, "tank_water"),
    ]
    for name, x0, x1, top, mk in tanks:
        b = Builder(f"Internal_Deck_Bulkhead_Tank_{name}", uv_scale=1.0)
        rings = []
        for x in np.linspace(x0, x1, max(3, int((x1 - x0) / 0.5) + 1)):
            t = top if top is not None else -0.9
            pts = section_outline(ctx, float(x), t, n=14, inset=0.035)
            if len(pts) < 3:
                continue
            ring = [V(x, -w, z) for (w, z) in pts] + [V(x, w, z) for (w, z) in reversed(pts)]
            rings.append(ring)
        if len(rings) >= 2:
            b.loft(rings, ctx.mats[mk])
        b.finish()


# ==================================================================================================
# 9. HULL APPENDAGES (rudder, shaft, bow thruster, bilge keels, anodes, sea chests)
# ==================================================================================================
def naca_ring(chord, t, x_le, y_c, z, n=24):
    pts = []
    for k in range(n):
        th = 2 * math.pi * k / n
        xc = 0.5 * (1 - math.cos(th))   # 0..1..0
        yt = 5 * t * (0.2969 * math.sqrt(xc) - 0.1260 * xc - 0.3516 * xc ** 2 + 0.2843 * xc ** 3 - 0.1036 * xc ** 4)
        sgn = 1 if th < math.pi else -1
        pts.append(V(x_le - xc * chord, y_c + sgn * yt * chord, z))
    return pts


def build_bow_thruster(ctx, n=48):
    """Transverse tunnel that follows the real hull: a clean circular hole is cut through the shell, and each end
    ring of the tunnel is projected onto the (uncut) shell surface, so the mouth matches the hull shape exactly."""
    # 1. end rings on the hull surface (both sides)
    ends = {}
    for sgn in (1, -1):
        ring = []
        for k in range(n):
            a = 2 * math.pi * k / n
            x, z = BT_X + BT_R * math.cos(a), BT_Z + BT_R * math.sin(a)
            ring.append(V(x, sgn * ctx.hw(x, z), z))
        ends[sgn] = ring
    ctx.bt_ends = ends
    # 2. tunnel tube (straight generators between the two projected ends), antifouling inside like the hull
    tb = Builder("BowThruster_Tunnel", uv_scale=1.0, recalc=False)
    rings = [[ends[-1][k].lerp(ends[1][k], t) for k in range(n)] for t in np.linspace(0, 1, 9)]
    tb.loft(rings, ctx.mats["hull_under"], cap0=False, cap1=False)
    tb.finish()
    # 3. faired lip around each mouth + grid bars recessed just inside the opening
    gr = Builder("BowThruster_Grids", uv_scale=1.0)
    for sgn in (1, -1):
        lip = [p + V(0, sgn * 0.012, 0) for p in ends[sgn]]
        gr.tube(lip, 0.026, ctx.mats["hardware"], n=8, closed=True)
        for dz in (-0.30, -0.15, 0.0, 0.15, 0.30):
            hz = math.sqrt(max(0.0, BT_R ** 2 - dz ** 2)) - 0.02
            z = BT_Z + dz
            y = sgn * (min(ctx.hw(BT_X - hz, z), ctx.hw(BT_X + hz, z), ctx.hw(BT_X, z)) - 0.07)
            gr.cyl((BT_X - hz, y, z), (BT_X + hz, y, z), 0.016, ctx.mats["hardware"], n=6)
    gr.finish()
    # 4. cut the openings in the shell (exact boolean, applied so nothing extra is exported)
    shell = ctx.shell_obj
    bpy.ops.mesh.primitive_cylinder_add(vertices=n, radius=BT_R, depth=12.0, location=(BT_X, 0, BT_Z), rotation=(math.pi / 2, 0, 0))
    cutter = bpy.context.active_object
    mod = shell.modifiers.new("BowThrusterCut", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.solver = "EXACT"
    mod.object = cutter
    if hasattr(mod, "use_hole_tolerant"):
        mod.use_hole_tolerant = True
    dg = bpy.context.evaluated_depsgraph_get()
    cut = bpy.data.meshes.new_from_object(shell.evaluated_get(dg))
    shell.modifiers.clear()
    old = shell.data
    shell.data = cut
    bpy.data.meshes.remove(old)
    cut.name = "ShipHull"
    cutter_mesh = cutter.data
    bpy.data.objects.remove(cutter)
    bpy.data.meshes.remove(cutter_mesh)


def build_appendages(ctx):
    mu = ctx.mats["hull_under"]
    hw = ctx.mats["hardware"]
    # --- shaft line: bossing, stern tube, rope guard --------------------------------------------------------
    sb = Builder("Propeller_Shaft_Bossing", uv_scale=1.0)
    exit_x = None
    for k in range(80):
        x = -15.0 - k * 0.03
        if ctx.hw(x, SHAFT_Z) < 0.16:
            exit_x = x
            break
    exit_x = exit_x or -16.6
    rings = []
    for k in range(9):
        x = mix(-15.2, exit_x - 0.10, k / 8)
        r = mix(0.30, 0.20, (k / 8) ** 1.5)
        rings.append([V(x, math.cos(2 * math.pi * i / 20) * r, SHAFT_Z + math.sin(2 * math.pi * i / 20) * r) for i in range(20)])
    sb.loft(rings, mu, cap0=False)
    sb.finish()
    st = Builder("Stern_Tube_Seal", uv_scale=1.0)
    st.cyl((exit_x - 0.10, 0, SHAFT_Z), (exit_x - 0.22, 0, SHAFT_Z), 0.21, hw, n=24)
    st.cyl((exit_x - 0.22, 0, SHAFT_Z), (PROP_X + 0.30, 0, SHAFT_Z), 0.11, hw, r1=0.10, n=20)
    st.finish()

    # --- semi-balanced rudder (NACA 0018) hung under the counter -----------------------------------------
    stock_x = RUDDER_STOCK_X
    le = stock_x + 0.22
    counter_z = None
    for k in range(120):
        z = -1.6 + k * 0.02
        hit = ctx.bvh.ray_cast(V(stock_x, 0.0, z - 0.01), V(0, 0, 1), 3.0)
        if hit[0] is not None:
            counter_z = hit[0].z
            break
    counter_z = counter_z if counter_z is not None else -0.9
    rb = Builder("SemiBalanced_Rudder", uv_scale=1.0)
    rings = []
    z_bot, z_top = -2.92, min(-1.0, counter_z - 0.10)
    for k in range(9):
        z = mix(z_bot, z_top, k / 8)
        chord = mix(0.66, 0.80, k / 8)
        rings.append(naca_ring(chord, 0.18, le - 0.04 * (1 - k / 8), 0.0, z, n=28))
    rb.loft(rings, mu)
    rb.finish()
    rs = Builder("Rudder_Stock_Assembly", uv_scale=1.0)
    rs.cyl((stock_x, 0, z_top - 0.05), (stock_x, 0, counter_z + 0.9), 0.055, hw, n=16)
    rs.cyl((stock_x, 0, counter_z - 0.02), (stock_x, 0, counter_z + 0.02), 0.13, hw, n=20)
    rs.cyl((stock_x, 0, z_top), (stock_x, 0, z_top + 0.05), 0.10, hw, n=20)
    for sgn in (1, -1):
        rs.box((stock_x - 0.25, sgn * 0.075, -2.45), (0.18, 0.03, 0.10), ctx.mats["anode"])
        rs.box((stock_x - 0.25, sgn * 0.075, -1.55), (0.18, 0.03, 0.10), ctx.mats["anode"])
    rs.finish()

    build_bow_thruster(ctx)

    if ctx.has("bilge_keels"):
        bk = Builder("Bilge_Keels", uv_scale=1.0, recalc=False)
        for sgn in (1, -1):
            outer, inner = [], []
            for x in np.arange(-6.0, 13.01, 0.5):
                d = V(0, sgn * 0.70710678, -0.70710678)
                o = V(float(x), sgn * 2.55, -2.3)
                hit = ctx.bvh.ray_cast(o, d, 4.0)
                if hit[0] is None:
                    continue
                taper = smoothstep(-6.0, -4.5, x) * (1 - smoothstep(11.5, 13.0, x))
                inner.append(hit[0])
                outer.append(hit[0] + d * (0.04 + 0.24 * taper))
            if len(inner) > 1:
                bk.strip(inner, outer, ctx.mats["hull_under"])
        bk.finish()

    if ctx.has("anodes"):
        an = Builder("Hull_Anodes", uv_scale=1.0)
        for x in (-15.6, -14.2, -11.0, -6.0, 0.0, 6.0, 12.0):
            for sgn in (1, -1):
                z = -2.25 if x > -14 else -1.9
                w = ctx.hw(x, z)
                if w > 0.1:
                    an.box((x, sgn * (w + 0.03), z), (0.30, 0.05, 0.12), ctx.mats["anode"])
        an.finish()

    if ctx.has("sea_chests"):
        sc = Builder("SeaChest_Gratings", uv_scale=1.0)
        for (x, sgn) in ((-10.6, 1), (-6.4, -1), (12.6, 1)):
            z = -2.55
            w = ctx.hw(x, z)
            for k in range(9):
                sc.box((x - 0.4 + k * 0.1, sgn * (w + 0.008), z), (0.025, 0.015, 0.36), ctx.mats["hardware"])
            sc.box((x, sgn * (w + 0.008), z + 0.19), (0.86, 0.016, 0.03), ctx.mats["hardware"])
            sc.box((x, sgn * (w + 0.008), z - 0.19), (0.86, 0.016, 0.03), ctx.mats["hardware"])
        sc.finish()


# ==================================================================================================
# 10. DECK OUTFIT (hatches, rails, mooring, anchors, fittings)
# ==================================================================================================
def plate_between(b, p0, p1, height, thick, mat):
    """Vertical plate standing on the deck between two plan points."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    c = (p0 + p1) * 0.5
    b.box((c.x, c.y, c.z + height / 2), (d.length, thick, height), mat, R=rot_z(math.atan2(d.y, d.x)))


def bollard(b, x, y, z, mat, s=1.0):
    b.box((x, y, z + 0.015 * s), (0.34 * s, 0.16 * s, 0.03 * s), mat)
    for dx in (-0.09 * s, 0.09 * s):
        b.cyl((x + dx, y, z + 0.03 * s), (x + dx, y, z + 0.20 * s), 0.045 * s, mat, n=14)
        b.cyl((x + dx, y, z + 0.20 * s), (x + dx, y, z + 0.22 * s), 0.058 * s, mat, n=14)


def chain_links(b, p0, p1, mat, link=0.09, r=0.012):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    n = max(2, int(d.length / (link * 0.78)))
    a, bb, dn = _basis(d)
    for k in range(n):
        c = p0 + d * ((k + 0.5) / n)
        side = a if k % 2 == 0 else bb
        b.torus(c, side, link * 0.36, r, mat, n1=10, n2=5)


def build_deck_outfit(ctx):
    F = ctx.form
    S = F.S
    hwm = ctx.mats["hardware"]
    rail = ctx.mats["rail"]
    acc = ctx.mats["accent"]

    # --- hatch coamings + covers (top stays below the container bottoms at 1.025) ----------------------
    hc = Builder("CargoBay_Pad_HatchCovers", uv_scale=1.0)
    co = Builder("Hatch_Coamings_Cleats", uv_scale=0.5)
    for bx in BAYS:
        x0, x1 = bx - BAY_LEN / 2, bx + BAY_LEN / 2
        co.box_between(x0 - 0.06, x1 + 0.06, -BAY_HW - 0.06, BAY_HW + 0.06, DECK_Z, DECK_Z + 0.055, acc)
        # 3 folding panels
        np_ = 3
        for k in range(np_):
            px0 = mix(x0, x1, k / np_) + 0.008
            px1 = mix(x0, x1, (k + 1) / np_) - 0.008
            hc.box_between(px0, px1, -BAY_HW, BAY_HW, DECK_Z + 0.055, 0.998, ctx.mats["hatch"])
        for k in range(1, np_):
            jx = mix(x0, x1, k / np_)
            co.box_between(jx - 0.01, jx + 0.01, -BAY_HW, BAY_HW, 0.99, 1.004, hwm)
        # side cleats and lifting lugs
        for xx in np.linspace(x0 + 0.25, x1 - 0.25, 5):
            for sgn in (1, -1):
                co.box((xx, sgn * (BAY_HW + 0.07), DECK_Z + 0.07), (0.06, 0.05, 0.05), hwm)
        # container stacking sockets at the 40' corner positions of every row
        for row in range(CARGO_ROWS):
            zc = -((row - (CARGO_ROWS - 1) / 2) * CARGO_ROW_PITCH)
            for xx in (bx - 1.49, bx + 1.49):
                co.box((xx, zc, 1.010), (0.07, 0.10, 0.025), hwm)
    hc.finish()
    co.finish()

    # --- side rails along the open deck (follow the real deck edge) ------------------------------------
    rl = Builder("Deck_Safety_Rails", uv_scale=1.0)
    fc_x = ctx.fc_front[0] if hasattr(ctx, "fc_front") else None
    xa = HOUSE["x0"] - 2.2
    xb = (fc_x - 0.1) if fc_x else 23.0
    for sgn in (1, -1):
        pts_top, pts_mid = [], []
        x = xa
        while x <= xb:
            dz, w = ctx.deck_at(x)
            if fc_x is None and dz > DECK_Z + 0.25:
                break
            y = sgn * (w - 0.10)
            rl.cyl((x, y, dz), (x, y, dz + 0.34), 0.014, rail, n=6)
            pts_top.append(V(x, y, dz + 0.34))
            pts_mid.append(V(x, y, dz + 0.18))
            x += 0.9
        rl.tube(pts_top, 0.017, rail, n=6)
        rl.tube(pts_mid, 0.012, rail, n=6)
    # stern rails around the poop
    pts = []
    for x in np.arange(-19.55, xa + 0.01, 0.6):
        dz, w = ctx.deck_at(float(x))
        pts.append((float(x), w - 0.12, dz))
    for sgn in (1, -1):
        top = [V(x, sgn * w, dz + 0.34 + 0.14) for (x, w, dz) in pts]
        for (x, w, dz) in pts:
            rl.cyl((x, sgn * w, dz + 0.14), (x, sgn * w, dz + 0.48), 0.014, rail, n=6)
        rl.tube(top, 0.017, rail, n=6)
    x, w, dz = pts[0]
    rl.tube([V(x, -w, dz + 0.48), V(x, w, dz + 0.48)], 0.017, rail, n=6)
    if ctx.has("bulwark_cap"):
        # cap rail along the bulwark top wherever the shell stands above the deck
        for sgn in (1, -1):
            seg = []
            for (rx, rdz, rw, u, s) in ctx.deck_rows:
                zs = F.z_sheer(u)
                if zs - rdz > 0.2:
                    seg.append(V(rx, sgn * (F.P(u, s, zs).y - 0.02), zs))
                elif len(seg) > 1:
                    rl.tube(seg, 0.03, acc, n=8)
                    seg = []
                else:
                    seg = []
            if len(seg) > 1:
                rl.tube(seg, 0.03, acc, n=8)
    rl.finish()

    # --- forecastle: windlasses, chain, stoppers, hawse pipes, anchors, foremast --------------------------
    mo = Builder("Deck_Mooring_Machinery", uv_scale=1.0, bevel=0.006)
    ch = Builder("Anchor_Chain_Cable", uv_scale=1.0)
    wx = 15.6 + S
    anchor_x = 16.85 + S
    for sgn in (1, -1):
        dz, w = ctx.deck_at(wx)
        wy = sgn * 0.92
        mo.box((wx, wy, dz + 0.04), (1.10, 0.74, 0.08), hwm)
        mo.box((wx - 0.30, wy, dz + 0.28), (0.46, 0.40, 0.40), hwm)               # gearbox
        mo.cyl((wx - 0.30, wy - sgn * 0.20, dz + 0.30), (wx - 0.30, wy - sgn * 0.52, dz + 0.30), 0.13, acc, n=20)  # motor
        mo.cyl((wx + 0.18, wy - 0.26, dz + 0.32), (wx + 0.18, wy + 0.26, dz + 0.32), 0.20, hwm, n=24)  # wildcat
        for dy in (-0.27, 0.27):
            mo.cyl((wx + 0.18, wy + dy - 0.02, dz + 0.32), (wx + 0.18, wy + dy + 0.02, dz + 0.32), 0.27, acc, n=24)  # brake rims
        mo.cyl((wx + 0.18, wy + sgn * 0.30, dz + 0.32), (wx + 0.18, wy + sgn * 0.62, dz + 0.32), 0.12, hwm, r1=0.15, n=20)  # warping head
        for dx in (-0.4, 0.45):
            mo.box((wx + dx, wy, dz + 0.20), (0.06, 0.70, 0.30), hwm)
        # chain stopper + hawse pipe deck opening
        aw = ctx.hw(anchor_x, 0.45)
        hx, hy = anchor_x - 0.55, sgn * min(aw - 0.35, 1.45)
        hdz = ctx.deck_at(hx)[0]
        mo.box(((wx + hx) / 2 + 0.2, (wy + hy) / 2, hdz + 0.07), (0.38, 0.22, 0.14), hwm)
        mo.cyl((hx, hy, hdz), (hx, hy, hdz + 0.08), 0.17, hwm, n=20)
        chain_links(ch, (wx + 0.18, wy, dz + 0.52), ((wx + hx) / 2 + 0.2, (wy + hy) / 2, hdz + 0.16), hwm)
        chain_links(ch, ((wx + hx) / 2 + 0.2, (wy + hy) / 2, hdz + 0.16), (hx, hy, hdz + 0.08), hwm)
        # hawse pipe down to the anchor pocket in the shell
        az = 0.45
        pocket = V(anchor_x, sgn * aw, az)
        mo.cyl((hx, hy, hdz), (pocket.x - 0.08, pocket.y - sgn * 0.12, pocket.z + 0.06), 0.11, hwm, n=16)
        mo.cyl((pocket.x - 0.04, pocket.y - sgn * 0.02, pocket.z), (pocket.x + 0.04, pocket.y + sgn * 0.05, pocket.z), 0.20, hwm, n=24)
        # stockless anchor seated in the pocket
        ax = pocket.x + 0.02
        ay = pocket.y + sgn * 0.10
        mo.cyl((ax, ay, az - 0.02), (ax - 0.06, ay, az - 0.52), 0.04, hwm, n=10)
        mo.box((ax - 0.07, ay, az - 0.58), (0.16, 0.12, 0.10), hwm)
        for dx in (-0.16, 0.16):
            mo.box((ax - 0.07 + dx, ay, az - 0.46), (0.07, 0.10, 0.30), hwm, R=rot_y(math.radians(-14 if dx < 0 else 14)))
        # bollards + fairleads near the bow and amidships
        for bx in (14.5 + S, 16.4 + S, 6.0, -1.0 + 0.0, -12.0 - 2.5):
            if 5.4 < bx < 8.6:
                continue
            bdz, bw = ctx.deck_at(bx)
            bollard(mo, bx, sgn * (bw - 0.42), bdz, hwm)
            mo.box((bx + 0.45, sgn * (bw - 0.14), bdz + 0.09), (0.30, 0.10, 0.16), hwm)
    # breakwater
    bwx = (ctx.fc_front[0] + 0.6) if hasattr(ctx, "fc_front") else 13.48 + S
    bdz, bw = ctx.deck_at(bwx)
    apex = V(bwx + 0.95, 0, bdz)
    for sgn in (1, -1):
        end = V(bwx, sgn * min(2.65, bw - 0.35), bdz)
        plate_between(mo, apex, end, 0.58, 0.05, acc)
        for k in range(1, 4):
            p = apex.lerp(end, k / 4)
            plate_between(mo, p, p + V(-0.32, 0, 0), 0.40, 0.025, hwm)   # back stays
    # foremast with masthead light + jackstaff
    fx = 17.85 + S
    fdz = ctx.deck_at(fx)[0]
    for sgn in (1, -1):
        mo.cyl((fx, sgn * 0.30, fdz), (fx + 0.12, sgn * 0.08, fdz + 1.55), 0.035, ctx.mats["house"], n=10)
    mo.box((fx + 0.12, 0, fdz + 1.30), (0.06, 0.62, 0.05), ctx.mats["house"])
    mo.box((fx + 0.13, 0, fdz + 1.62), (0.08, 0.08, 0.10), ctx.mats["light_white"])
    mo.cyl((fx + 0.12, 0, fdz + 1.55), (fx + 0.12, 0, fdz + 1.75), 0.02, rail, n=6)
    jx = 18.70 + S
    jdz = ctx.deck_at(jx)[0]
    mo.cyl((jx, 0, jdz), (jx + 0.06, 0, jdz + 0.9), 0.018, rail, n=6)
    # --- aft mooring winch, stern bollards, ensign staff ----------------------------------------------------
    awx = -15.25
    adz, aw = ctx.deck_at(awx)
    for sgn in (1, -1):
        yc = sgn * min(1.75, aw - 0.85)            # one mooring winch per quarter, clear of the free-fall ramp
        inner, outer = yc - sgn * 0.42, yc + sgn * 0.42
        mo.box((awx, yc, adz + 0.03), (1.00, 1.00, 0.06), hwm)
        mo.box((awx, inner, adz + 0.24), (0.46, 0.30, 0.36), hwm)                       # gearbox
        mo.cyl((awx + 0.22, inner, adz + 0.22), (awx + 0.58, inner, adz + 0.22), 0.13, acc, n=18)   # motor
        mo.cyl((awx, inner + sgn * 0.15, adz + 0.24), (awx, yc + sgn * 0.28, adz + 0.24), 0.16, hwm, n=20)  # drum
        for yy in (inner + sgn * 0.16, yc + sgn * 0.28):
            mo.cyl((awx, yy - 0.015, adz + 0.24), (awx, yy + 0.015, adz + 0.24), 0.24, acc, n=20)
        mo.cyl((awx, yc + sgn * 0.30, adz + 0.24), (awx, outer, adz + 0.24), 0.10, hwm, r1=0.13, n=18)   # warping head
        for bx in (-16.4, -18.6):
            bdz, bw = ctx.deck_at(bx)
            bollard(mo, bx, sgn * (bw - 0.40), bdz, hwm)
        bdz, bw = ctx.deck_at(-17.2)
        mo.box((-17.2, sgn * (bw - 0.08), bdz + 0.18), (0.36, 0.12, 0.20), hwm)
    mo.finish()
    ch.finish()

    # --- small deck fittings: vents, air pipes, hydrants, manholes ------------------------------------
    if ctx.has("deck_fittings"):
        fit = Builder("Deck_Fittings_Vents", uv_scale=1.0)
        slots = [x for x in np.arange(-5.8, 16.0, 1.6) if not (5.0 < x < 8.9)]
        for i, x in enumerate(slots):
            for sgn in (1, -1):
                dz, w = ctx.deck_at(float(x))
                y = sgn * (w - 0.55)
                if i % 3 == 0:
                    fit.cyl((x, y, dz), (x, y, dz + 0.26), 0.05, hwm, n=12)
                    fit.cyl((x, y, dz + 0.26), (x, y, dz + 0.32), 0.10, hwm, r1=0.04, n=14)      # mushroom vent
                elif i % 3 == 1:
                    fit.cyl((x, y, dz), (x, y, dz + 0.30), 0.035, hwm, n=10)                     # gooseneck air pipe
                    fit.torus((x + 0.06, y, dz + 0.30), (0, 1, 0), 0.06, 0.035, hwm, n1=12, n2=8, arc=math.pi)
                else:
                    fit.cyl((x, y, dz), (x, y, dz + 0.02), 0.16, hwm, n=16)                       # manhole cover
                    for k in range(8):
                        a = 2 * math.pi * k / 8
                        fit.cyl((x + 0.13 * math.cos(a), y + 0.13 * math.sin(a), dz + 0.02), (x + 0.13 * math.cos(a), y + 0.13 * math.sin(a), dz + 0.035), 0.012, hwm, n=6)
        if ctx.has("fire_main"):
            for sgn in (1, -1):
                pts = []
                for x in np.arange(-13.0, 17.0, 0.5):
                    dz, w = ctx.deck_at(float(x))
                    pts.append(V(float(x), sgn * (w - 0.24), dz + 0.12))
                fit.tube(pts, 0.035, ctx.mats["pipe_red"], n=10)
                for x in np.arange(-12.0, 17.0, 3.0):
                    dz, w = ctx.deck_at(float(x))
                    y = sgn * (w - 0.24)
                    fit.box((float(x), y, dz + 0.06), (0.05, 0.10, 0.12), hwm)
                    if int(x) % 6 == 0:
                        fit.cyl((float(x), y, dz + 0.12), (float(x), y, dz + 0.36), 0.03, ctx.mats["pipe_red"], n=10)
                        fit.cyl((float(x), y - sgn * 0.04, dz + 0.32), (float(x), y - sgn * 0.12, dz + 0.32), 0.022, hwm, n=8)
        fit.finish()


# ==================================================================================================
# 11. SUPERSTRUCTURE
# ==================================================================================================
def lifeboat(b, c, L, W, H, hull_mat, canopy_mat, yaw=0.0, pitch=0.0):
    R = rot_z(yaw) @ rot_y(pitch)
    c = Vector(c)
    rings = []
    n = 14
    for k in range(n + 1):
        t = k / n
        xl = (t - 0.5) * L
        f = math.sqrt(max(0.0, 1 - (2 * t - 1) ** 6)) if 0 < t < 1 else 0.02
        f = max(0.03, f)
        ring = []
        for i in range(16):
            a = 2 * math.pi * i / 16
            ca, sa = math.cos(a), math.sin(a)
            zz = sa * (H * 0.45 if sa < 0 else H * 0.15)
            ring.append(c + R @ V(xl, ca * W / 2 * f, zz * f))
        rings.append(ring)
    b.loft(rings, hull_mat)
    b.ellipsoid(c + R @ V(0, 0, H * 0.18), (L * 0.40, W * 0.44, H * 0.42), canopy_mat, R=R, nu=18, nv=8)
    b.box(c + R @ V(L * 0.16, 0, H * 0.55), (L * 0.14, W * 0.32, H * 0.12), canopy_mat, R=R)


def build_superstructure(ctx):
    mh = ctx.mats["house"]
    mw = ctx.mats["window"]
    md = ctx.mats["deck_house"]
    hwm = ctx.mats["hardware"]
    rail = ctx.mats["rail"]
    X0, X1, HW = HOUSE["x0"], HOUSE["x1"], HOUSE["hw"]
    d1, d2, d3, roof = HOUSE["d1"], HOUSE["d2"], HOUSE["d3"], HOUSE["roof"]
    t = 0.06

    hb = Builder("Accommodation_Block", uv_scale=0.25)
    # tiers 1-2: four walls (hollow, so the decks and equipment read through the translucent shell)
    hb.box_between(X0, X1, HW - t, HW, DECK_Z, d3, mh)
    hb.box_between(X0, X1, -HW, -HW + t, DECK_Z, d3, mh)
    hb.box_between(X1 - t, X1, -HW + t, HW - t, DECK_Z, d3, mh)
    hb.box_between(X0, X0 + t, -HW + t, HW - t, DECK_Z, d3, mh)
    # wheelhouse with raked front
    wx0, wx1 = -10.2, X1
    rake = 0.20
    for sgn in (1, -1):
        y = sgn * (HW - t / 2)
        pts = [V(wx0, y - t / 2, d3), V(wx1, y - t / 2, d3), V(wx1 + rake, y - t / 2, roof), V(wx0, y - t / 2, roof)]
        hb.prism(pts, (0, t, 0), mh)
    hb.box_between(wx0, wx0 + t, -HW, HW, d3, roof, mh)
    front = [V(wx1 - t, -HW, d3), V(wx1 - t, HW, d3), V(wx1 + rake - t, HW, roof), V(wx1 + rake - t, -HW, roof)]
    hb.prism(front, (t, 0, 0), mh)
    hb.finish()

    dk = Builder("House_Deck_Levels", uv_scale=0.5)
    dk.box_between(X0 + t, X1 - t, -HW + t, HW - t, d1 - 0.05, d1, md)
    dk.box_between(X0 + t, X1 - t, -HW + t, HW - t, d2 - 0.05, d2, md)
    dk.box_between(X0 - 0.12, X1 + 0.12, -HW - 0.12, HW + 0.12, d3 - 0.06, d3, md)          # bridge deck / tier 2 roof
    dk.box_between(wx0 - 0.08, wx1 + rake + 0.30, -HW - 0.10, HW + 0.10, roof, roof + 0.06, md)  # wheelhouse roof + visor
    # bridge wings
    wing_w = 3.72
    for sgn in (1, -1):
        dk.box_between(-9.7, X1 + 0.05, sgn * HW, sgn * wing_w, d3 - 0.06, d3, md)
    dk.finish()

    # --- glazing -----------------------------------------------------------------------------------------
    gl = Builder("Bridge_Window_Glazing", uv_scale=1.0)
    frames = ctx.has("window_frames")
    for sgn in (1, -1):
        for zc in ((d1 + d2) / 2 + 0.12, (d2 + d3) / 2 + 0.10):
            for x in np.arange(X0 + 0.55, X1 - 0.3, 0.86):
                if X0 + 0.9 < x < X0 + 1.4:
                    continue
                gl.box((x, sgn * (HW + 0.006), zc), (0.46, 0.014, 0.30), mw)
                if frames:
                    gl.box((x, sgn * (HW + 0.012), zc + 0.165), (0.52, 0.02, 0.03), hwm)
                    gl.box((x, sgn * (HW + 0.012), zc - 0.165), (0.52, 0.02, 0.03), hwm)
        # wheelhouse side windows
        for x in np.arange(wx0 + 0.45, wx1 - 0.2, 0.62):
            gl.box((x, sgn * (HW + 0.006), d3 + 0.62), (0.48, 0.014, 0.46), mw)
    for zc in ((d1 + d2) / 2 + 0.12, (d2 + d3) / 2 + 0.10):
        for y in np.arange(-HW + 0.6, HW - 0.4, 0.82):
            if abs(y) < 0.5:
                continue
            gl.box((X1 + 0.006, y, zc), (0.014, 0.50, 0.30), mw)
    # raked bridge front windows
    ang = math.atan2(rake, roof - d3)
    R = rot_y(ang)
    for y in np.arange(-HW + 0.32, HW - 0.2, 0.52):
        zc = d3 + 0.66
        xc = wx1 + rake * (zc - d3) / (roof - d3) + 0.008
        gl.box((xc, y, zc), (0.014, 0.46, 0.56), mw, R=R)
        if frames:
            gl.box((xc + 0.006, y + 0.25, zc), (0.02, 0.035, 0.60), hwm, R=R)
    # doors
    for sgn in (1, -1):
        gl.box((X0 + 1.15, sgn * (HW + 0.008), d1 + 0.42), (0.40, 0.016, 0.78), hwm)
        gl.box((-9.0, sgn * (HW + 0.008), d3 + 0.40), (0.40, 0.016, 0.76), hwm)
    gl.box((X0 - 0.008, 1.6, d1 + 0.42), (0.016, 0.40, 0.78), hwm)
    gl.finish()

    # --- wing bulwarks, consoles, side lights, rails, ladders -------------------------------------------
    ou = Builder("House_Outfit_Rails_Ladders", uv_scale=1.0)
    for sgn in (1, -1):
        ou.box_between(-9.7, X1 + 0.05, sgn * (wing_w - 0.04), sgn * wing_w, d3, d3 + 0.42, mh)
        ou.box_between(X1, X1 + 0.05, sgn * HW, sgn * wing_w, d3, d3 + 0.42, mh)
        ou.box((-7.6, sgn * (wing_w - 0.3), d3 + 0.30), (0.40, 0.30, 0.60), hwm)          # wing console
        ou.box((-7.62, sgn * (wing_w - 0.3), d3 + 0.66), (0.30, 0.22, 0.10), mw)
        light = ctx.mats["light_port"] if sgn > 0 else ctx.mats["light_stbd"]
        ou.box((-8.2, sgn * (wing_w + 0.03), d3 + 0.55), (0.18, 0.06, 0.14), light)       # sidelight
        ou.box((-8.2, sgn * (wing_w + 0.02), d3 + 0.66), (0.24, 0.10, 0.03), hwm)
        # rails on tier-2 roof (aft part of bridge deck)
        pts = [V(X0 - 0.08, sgn * (HW + 0.06), d3 + 0.34), V(wx0 - 0.1, sgn * (HW + 0.06), d3 + 0.34)]
        ou.tube(pts, 0.016, rail, n=6)
        for x in np.arange(X0 - 0.08, wx0 - 0.05, 0.6):
            ou.cyl((x, sgn * (HW + 0.06), d3), (x, sgn * (HW + 0.06), d3 + 0.34), 0.013, rail, n=6)
        # deck-2 open walkway along the house side (embarkation / life-raft deck), on brackets
        wo = sgn * (HW + WALK_W)
        ou.box_between(X0 - WALK_W, WALK_FWD, sgn * HW, wo, d2 - 0.05, d2, md)
        for x in np.arange(X0 + 0.25, WALK_FWD, 1.1):          # triangular knee brackets welded to the house side
            ou.prism([V(x - 0.015, sgn * HW, d2 - 0.05), V(x - 0.015, wo - sgn * 0.03, d2 - 0.05), V(x - 0.015, sgn * HW, d2 - 0.48)], (0.03, 0, 0), hwm)
        posts = np.arange(X0 - WALK_W + 0.03, WALK_FWD + 0.01, 0.6).tolist() + [WALK_FWD - 0.03]
        for x in posts:
            ou.cyl((x, wo - sgn * 0.03, d2), (x, wo - sgn * 0.03, d2 + 0.42), 0.013, rail, n=6)
        for hgt in (0.21, 0.42):
            ou.tube([V(X0 - WALK_W + 0.03, wo - sgn * 0.03, d2 + hgt), V(WALK_FWD - 0.03, wo - sgn * 0.03, d2 + hgt)], 0.014, rail, n=6)
        ou.tube([V(WALK_FWD - 0.03, sgn * HW, d2 + 0.42), V(WALK_FWD - 0.03, sgn * (HW + 0.17), d2 + 0.42)], 0.014, rail, n=6)
        ou.box((X0 + 1.15, sgn * (HW + 0.008), d2 + 0.40), (0.40, 0.016, 0.76), hwm)      # walkway door
        # stairs: main deck -> deck-2 walkway (forward end), deck-2 aft strip -> bridge deck
        stairs(ou, V(WALK_FWD + 1.30, sgn * (HW + 0.40), DECK_Z), V(WALK_FWD, sgn * (HW + 0.40), d2), 0.40, md, rail)
        stairs(ou, V(X0 - WALK_W / 2, sgn * 2.15, d2), V(X0 - WALK_W / 2, sgn * 0.95, d3), 0.40, md, rail)
        ou.box_between(X0 - WALK_W, X0 - 0.12, sgn * 0.50, sgn * 0.98, d3 - 0.05, d3, md)  # stair landing
        # bridge-wing brackets
        for x in (-9.45, -8.45, -7.45):
            ou.cyl((x, sgn * HW, d3 - 0.80), (x, sgn * (wing_w - 0.10), d3 - 0.07), 0.035, hwm, n=8)
    # deck-2 aft strip (joins the two side walkways behind the house) with its rail and a door
    ou.box_between(X0 - WALK_W, X0, -HW, HW, d2 - 0.05, d2, md)
    ou.tube([V(X0 - WALK_W + 0.03, -(HW + WALK_W) + 0.03, d2 + 0.42), V(X0 - WALK_W + 0.03, HW + WALK_W - 0.03, d2 + 0.42)], 0.014, rail, n=6)
    for y in np.arange(-(HW + WALK_W) + 0.03, HW + WALK_W, 0.6):
        ou.cyl((X0 - WALK_W + 0.03, y, d2), (X0 - WALK_W + 0.03, y, d2 + 0.42), 0.013, rail, n=6)
    ou.box((X0 - 0.008, 0.0, d2 + 0.40), (0.016, 0.40, 0.76), hwm)
    for y in (-2.2, -1.1, 1.1, 2.2):                            # knee brackets under the aft strip
        ou.prism([V(X0, y - 0.015, d2 - 0.05), V(X0 - WALK_W + 0.03, y - 0.015, d2 - 0.05), V(X0, y - 0.015, d2 - 0.48)], (0, 0.03, 0), hwm)
    # bridge-deck aft edge rail, open at the two stair landings
    for (ya, yb) in ((-(HW + 0.06), -1.02), (-0.46, 0.46), (1.02, HW + 0.06)):
        ou.tube([V(X0 - 0.10, ya, d3 + 0.34), V(X0 - 0.10, yb, d3 + 0.34)], 0.014, rail, n=6)
        for y in np.linspace(ya, yb, max(2, int(abs(yb - ya) / 0.55) + 1)):
            ou.cyl((X0 - 0.10, float(y), d3), (X0 - 0.10, float(y), d3 + 0.34), 0.012, rail, n=6)
    # compass deck rails
    for sgn in (1, -1):
        ou.tube([V(wx0 - 0.02, sgn * (HW + 0.05), roof + 0.38), V(wx1 + rake + 0.25, sgn * (HW + 0.05), roof + 0.38)], 0.014, rail, n=6)
        for x in np.arange(wx0, wx1 + rake + 0.3, 0.55):
            ou.cyl((x, sgn * (HW + 0.05), roof + 0.06), (x, sgn * (HW + 0.05), roof + 0.38), 0.012, rail, n=6)
    # deck lights + horn
    for sgn in (1, -1):
        ou.box((X1 + 0.05, sgn * 2.2, d3 - 0.20), (0.10, 0.16, 0.10), ctx.mats["light_white"])
    ou.finish()

    build_funnel(ctx)
    build_mast(ctx, wx0, wx1, roof)
    build_lifesaving(ctx)


WALK_W = 0.65         # deck-2 walkway width outside the house
WALK_FWD = -9.70      # forward end of the deck-2 side walkways


def stairs(b, p0, p1, width, tread_mat, rail_mat):
    """Straight ship's stair from p0 (foot) to p1 (head): stringers, treads and handrails."""
    p0, p1 = Vector(p0), Vector(p1)
    run = V(p1.x - p0.x, p1.y - p0.y, 0)
    side = V(-run.y, run.x, 0).normalized() * (width / 2)
    for s_ in (side, -side):
        b.cyl(p0 + s_, p1 + s_, 0.018, rail_mat, n=6)
        b.cyl(p0 + s_ + V(0, 0, 0.45), p1 + s_ + V(0, 0, 0.45), 0.013, rail_mat, n=6)
        b.cyl(p0 + s_, p0 + s_ + V(0, 0, 0.45), 0.012, rail_mat, n=6)
    rise = p1.z - p0.z
    nst = max(2, int(rise / 0.16))
    ang = math.atan2(run.y, run.x)
    for k in range(1, nst):
        c = p0.lerp(p1, k / nst)
        b.box(c, (0.12, width, 0.015), tread_mat, R=rot_z(ang))


def build_funnel(ctx):
    mf = ctx.mats["funnel"]
    mb = ctx.mats["funnel_band"]
    hwm = ctx.mats["hardware"]
    d3 = HOUSE["d3"]
    fx, fz0, fz1 = -12.25, d3, 5.75
    rake = math.radians(10)
    L0, W0 = 1.75, 1.35
    fb = Builder("Funnel_Casing", uv_scale=0.5)
    rings = []
    levels = np.linspace(fz0, fz1, 10)
    for z in levels:
        t = (z - fz0) / (fz1 - fz0)
        L = L0 * (1 - 0.10 * t)
        W = W0 * (1 - 0.06 * t)
        cx = fx - (z - fz0) * math.tan(rake)
        ring = []
        for i in range(28):
            a = 2 * math.pi * i / 28
            ca, sa = math.cos(a), math.sin(a)
            px = math.copysign(abs(ca) ** 0.45, ca) * L / 2
            py = math.copysign(abs(sa) ** 0.45, sa) * W / 2
            ring.append(V(cx + px, py, z))
        rings.append(ring)
    fb.loft(rings, mf, cap0=False)
    fb.finish()
    band = Builder("Funnel_Livery_Band", uv_scale=0.5)
    zb0, zb1 = fz1 - 0.95, fz1 - 0.45
    for (za, zb_) in ((zb0, zb1),):
        rr = []
        for z in (za, zb_):
            t = (z - fz0) / (fz1 - fz0)
            L = L0 * (1 - 0.10 * t) + 0.02
            W = W0 * (1 - 0.06 * t) + 0.02
            cx = fx - (z - fz0) * math.tan(rake)
            rr.append([V(cx + math.copysign(abs(math.cos(2 * math.pi * i / 28)) ** 0.45, math.cos(2 * math.pi * i / 28)) * L / 2,
                         math.copysign(abs(math.sin(2 * math.pi * i / 28)) ** 0.45, math.sin(2 * math.pi * i / 28)) * W / 2, z) for i in range(28)])
        band.loft(rr, mb, cap0=False, cap1=False)
    band.finish()
    top = Builder("Funnel_Top_Uptakes", uv_scale=1.0)
    cx = fx - (fz1 - fz0) * math.tan(rake)
    top.box((cx, 0, fz1 - 0.04), (L0 * 0.86, W0 * 0.90, 0.08), ctx.mats["soot"])
    for i, (dx, dy, r) in enumerate([(-0.45, -0.30, 0.09), (-0.45, 0.30, 0.09), (-0.05, -0.30, 0.09), (-0.05, 0.30, 0.09), (0.32, 0.0, 0.07), (0.32, 0.38, 0.05)]):
        top.cyl((cx + dx, dy, fz1 - 0.6), (cx + dx - 0.05, dy, fz1 + 0.38), r, ctx.mats["soot"], n=14)
        top.cyl((cx + dx - 0.05, dy, fz1 + 0.34), (cx + dx - 0.055, dy, fz1 + 0.40), r + 0.02, hwm, n=14)
    if ctx.has("funnel_detail"):
        # SCR / silencer casings + platform + ladder up the aft face
        for dy in (-0.32, 0.32):
            top.cyl((cx + 0.05, dy, fz0 + 0.2), (cx + 0.05, dy, fz0 + 1.2), 0.16, hwm, n=16)
        top.box((cx - 0.95, 0, fz1 - 0.35), (0.25, 1.1, 0.04), ctx.mats["grating"])
        for k in range(14):
            z = fz0 + 0.2 + k * 0.17
            top.box((cx - 0.88 - (z - fz0) * math.tan(rake) * 0 - 0.02, 0, z), (0.03, 0.32, 0.015), ctx.mats["rail"])
        for dy in (-0.16, 0.16):
            top.cyl((cx - 0.90, dy, fz0 + 0.1), (cx - 0.90, dy, fz1 - 0.3), 0.012, ctx.mats["rail"], n=6)
    top.finish()


def build_mast(ctx, wx0, wx1, roof):
    hwm = ctx.mats["hardware"]
    rail = ctx.mats["rail"]
    mh = ctx.mats["house"]
    mm = Builder("Radar_Mast_Antennas", uv_scale=1.0)
    mx = -8.9
    if ctx.has("modern_mast"):
        top = roof + 2.1
        for (dx, dy) in ((0.55, 0.0), (-0.45, 0.55), (-0.45, -0.55)):
            mm.cyl((mx + dx, dy, roof + 0.06), (mx + dx * 0.25, dy * 0.25, top), 0.045, mh, n=12)
        for z in (roof + 0.95, roof + 1.65):
            mm.box((mx, 0, z), (0.80, 1.80, 0.04), ctx.mats["grating"])
            mm.tube([V(mx - 0.4, -0.9, z + 0.25), V(mx + 0.4, -0.9, z + 0.25), V(mx + 0.4, 0.9, z + 0.25), V(mx - 0.4, 0.9, z + 0.25)], 0.01, rail, n=5, closed=True)
        # radar scanners
        mm.cyl((mx + 0.1, 0, roof + 1.69), (mx + 0.1, 0, roof + 1.82), 0.09, hwm, n=12)
        mm.box((mx + 0.1, 0, roof + 1.86), (0.12, 1.55, 0.09), mh)
        mm.cyl((-9.7, 0, roof + 0.06), (-9.7, 0, roof + 0.42), 0.10, hwm, n=12)
        mm.box((-9.7, 0, roof + 0.47), (0.10, 1.25, 0.08), mh)
        # satcom + VSAT radomes, GPS mushrooms, whips
        for (x, y, r) in ((-9.9, 1.6, 0.30), (-9.9, -1.6, 0.24)):
            mm.cyl((x, y, roof + 0.06), (x, y, roof + 0.45), 0.06, hwm, n=10)
            mm.ellipsoid((x, y, roof + 0.45 + r * 0.8), (r, r, r * 1.05), ctx.mats["radome"], nu=20, nv=10)
        for (x, y) in ((-8.3, 1.2), (-8.3, -1.2), (-8.6, 1.9), (-8.6, -1.9)):
            mm.cyl((x, y, roof + 0.06), (x, y, roof + 0.22), 0.02, hwm, n=6)
            mm.ellipsoid((x, y, roof + 0.25), (0.06, 0.06, 0.04), ctx.mats["radome"], nu=10, nv=6)
        for (x, y, h) in ((-10.1, 0.6, 1.4), (-10.1, -0.6, 1.4), (-8.1, 2.3, 1.1), (-8.1, -2.3, 1.1)):
            mm.cyl((x, y, roof + 0.06), (x, y, roof + h), 0.010, rail, n=5, r1=0.005)
        mm.cyl((mx, 0, top), (mx, 0, top + 0.70), 0.03, rail, n=8)
        mm.box((mx + 0.04, 0, top + 0.05), (0.08, 0.08, 0.10), ctx.mats["light_white"])
        mm.box((mx + 0.04, 0, top + 0.55), (0.08, 0.08, 0.10), ctx.mats["light_white"])
        mm.box((mx, 0, roof + 1.3), (0.06, 1.2, 0.05), mh)
        mm.cyl((mx + 0.35, 0.3, roof + 1.0), (mx + 0.55, 0.3, roof + 1.0), 0.07, ctx.mats["accent"], r1=0.12, n=12)  # horn
    else:
        top = roof + 1.9
        mm.cyl((mx, 0, roof + 0.06), (mx, 0, top), 0.06, mh, r1=0.035, n=14)
        mm.box((mx, 0, roof + 1.2), (0.08, 1.50, 0.06), mh)
        mm.box((mx + 0.18, 0, roof + 0.92), (0.50, 0.60, 0.04), ctx.mats["grating"])
        mm.cyl((mx + 0.18, 0, roof + 0.96), (mx + 0.18, 0, roof + 1.06), 0.07, hwm, n=12)
        mm.box((mx + 0.18, 0, roof + 1.10), (0.12, 1.20, 0.08), mh)
        mm.cyl((-9.8, 0, roof + 0.06), (-9.8, 0, roof + 0.36), 0.09, hwm, n=12)
        mm.box((-9.8, 0, roof + 0.41), (0.10, 1.05, 0.08), mh)
        mm.box((mx + 0.05, 0, top - 0.02), (0.08, 0.08, 0.10), ctx.mats["light_white"])
        for y in (-0.7, 0.7):
            mm.cyl((mx, y, roof + 1.23), (mx, y, roof + 1.75), 0.008, rail, n=5)
        mm.ellipsoid((-9.9, 1.5, roof + 0.40), (0.22, 0.22, 0.24), ctx.mats["radome"], nu=18, nv=9)
        mm.cyl((-9.9, 1.5, roof + 0.06), (-9.9, 1.5, roof + 0.25), 0.05, hwm, n=10)
    mm.finish()


# Free-fall launch arrangement at the stern (shared by the ramp, the boat, the A-frame and the deck outfit).
FF_ANGLE = math.radians(35.0)
FF_LOW = V(-19.80, 0.0, 1.55)          # lower (launch) end of the rails, just past the transom
FF_LEN = 3.20                          # rail length up the ramp
FF_RAIL_Y = 0.40


def ff_point(u):
    """Point on the rail top line, u metres up the ramp from the launch end."""
    return FF_LOW + V(math.cos(FF_ANGLE), 0, math.sin(FF_ANGLE)) * u


def freefall_boat(b, stern_keel, L, W, H, hull_mat, trim_mat, dark_mat):
    """Enclosed free-fall lifeboat, bow pointing down the ramp (aft, out over the stern)."""
    d = V(-math.cos(FF_ANGLE), 0, -math.sin(FF_ANGLE))    # forward (bow) direction
    n = V(-math.sin(FF_ANGLE), 0, math.cos(FF_ANGLE))     # boat 'up'
    lat = V(0, 1, 0)
    Rb = rot_y(-FF_ANGLE) @ rot_z(math.pi)                # boat-local axes -> world (x = bow)

    def P(s_, y, h):
        return stern_keel + d * s_ + lat * y + n * h

    def keel(t):
        return 0.22 * H * smoothstep(0.62, 1.0, t) ** 1.4 + 0.04 * H * (1 - smoothstep(0.0, 0.12, t))

    def top(t):
        return keel(t) + (H - keel(t)) * (1 - 0.38 * t ** 1.6)

    def half(t):
        return W / 2 * (0.80 + 0.20 * smoothstep(0.0, 0.3, t)) * math.sqrt(max(0.0, 1 - t ** 3.2))

    rings = []
    for i in range(19):
        t = i / 18
        k, tp, w = keel(t), top(t), max(0.012, half(t))
        mid, hh = (k + tp) / 2, (tp - k) / 2
        ring = []
        for j in range(20):
            a_ = 2 * math.pi * j / 20
            ca, sa = math.cos(a_), math.sin(a_)
            e = 0.62 if sa < 0 else 0.75     # deeper V below, rounded canopy above
            ring.append(P(t * L, w * math.copysign(abs(ca) ** e, ca), mid + hh * math.copysign(abs(sa) ** e, sa)))
        rings.append(ring)
    b.loft(rings, hull_mat, cap0=True, cap1=False)
    # rub rail, side windows, helm cupola with window band, stern hatch, release hook
    for sgn in (1, -1):
        rr = []
        for i in range(2, 17):
            t = i / 18
            rr.append(P(t * L, sgn * (half(t) + 0.012), keel(t) + 0.42 * (top(t) - keel(t))))
        b.tube(rr, 0.022, trim_mat, n=6)
        for t in (0.34, 0.47, 0.60, 0.73):
            b.box(P(t * L, sgn * half(t) * 0.93, keel(t) + 0.72 * (top(t) - keel(t))), (0.16, 0.06, 0.08), dark_mat, R=Rb)
    cup = P(0.17 * L, 0, top(0.17) + 0.02)
    b.ellipsoid(cup, (0.24, 0.20, 0.13), hull_mat, R=Rb, nu=16, nv=8)
    b.ellipsoid(cup + n * 0.03, (0.25, 0.205, 0.07), dark_mat, R=Rb, nu=16, nv=6)
    b.box(P(0.0, 0, keel(0) + 0.45 * H), (0.03, 0.30, 0.40), dark_mat, R=Rb)
    b.box(P(0.06 * L, 0, top(0.06) + 0.03), (0.12, 0.10, 0.06), trim_mat, R=Rb)


def rib_boat(b, c, L, W, tube_mat, hull_mat):
    path = []
    for k in range(28):
        a_ = 2 * math.pi * k / 28
        path.append(c + V(L / 2 * math.copysign(abs(math.cos(a_)) ** 0.55, math.cos(a_)) - (0.06 if math.cos(a_) > 0 else 0),
                          W / 2 * math.sin(a_), 0))
    b.tube(path, 0.075, tube_mat, n=8, closed=True)
    b.ellipsoid(c + V(0, 0, -0.07), (L * 0.47, W * 0.40, 0.10), hull_mat, nu=16, nv=6)
    b.box(c + V(-L * 0.28, 0, 0.02), (0.14, 0.14, 0.14), hull_mat)          # outboard
    b.box(c + V(0.05, 0, 0.0), (0.22, 0.20, 0.12), hull_mat)                # console


def build_lifesaving(ctx):
    lb = Builder("LifeSaving_Appliances", uv_scale=1.0)
    st = Builder("LifeSaving_Davits_Structure", uv_scale=1.0)
    orange = ctx.mats["lifeboat"]
    white = ctx.mats["house"]
    hwm = ctx.mats["hardware"]
    rail = ctx.mats["rail"]
    dark = ctx.mats["window"]
    X0, HW, d2, d3 = HOUSE["x0"], HOUSE["hw"], HOUSE["d2"], HOUSE["d3"]

    # --- free-fall lifeboat on a stern ramp (launches bow-first, aft, over the transom) --------------------
    for sgn in (1, -1):
        y = sgn * FF_RAIL_Y
        p0, p1 = ff_point(0) + V(0, y, -0.06), ff_point(FF_LEN) + V(0, y, -0.06)
        st.box((p0 + p1) * 0.5, (FF_LEN, 0.08, 0.12), hwm, R=rot_y(-FF_ANGLE))     # rail beam
        for u in (0.45, 1.65, FF_LEN - 0.08):                                          # posts down to the deck
            q = ff_point(u) + V(0, y, -0.12)
            dz = ctx.deck_at(q.x)[0]
            st.box((q.x, y, (q.z + dz) / 2), (0.10, 0.10, q.z - dz), hwm)
        q0, q1 = ff_point(0.45) + V(0, y, -0.12), ff_point(FF_LEN - 0.08) + V(0, y, -0.12)
        st.cyl(V(q0.x, y, ctx.deck_at(q0.x)[0] + 0.1), V(q1.x, y, q1.z - 0.1), 0.03, hwm, n=8)   # diagonal brace
    for u in (0.45, 1.65, FF_LEN - 0.08):
        q = ff_point(u) + V(0, 0, -0.16)
        st.box(q, (0.10, 2 * FF_RAIL_Y + 0.10, 0.08), hwm)
    # boat seated in the rails, bow down the ramp
    BL, BW, BH = 2.60, 0.86, 0.82
    n_up = V(-math.sin(FF_ANGLE), 0, math.cos(FF_ANGLE))
    stern_keel = ff_point(0.22 + BL) - n_up * 0.05
    freefall_boat(lb, stern_keel, BL, BW, BH, orange, white, dark)
    # recovery A-frame over the boat, raked aft, carrying the ensign staff
    ax_deck, ax_top, az_top = -16.90, -18.25, 4.70
    for sgn in (1, -1):
        st.cyl((ax_deck, sgn * 0.98, ctx.deck_at(ax_deck)[0]), (ax_top, sgn * 0.98, az_top), 0.065, hwm, n=12)
        st.box((ax_deck, sgn * 0.98, ctx.deck_at(ax_deck)[0] + 0.03), (0.30, 0.24, 0.06), hwm)
    st.box((ax_top, 0, az_top + 0.05), (0.16, 2.12, 0.16), hwm)
    hook_z = stern_keel.z + 1.35
    st.cyl((ax_top, 0, az_top - 0.03), (ax_top, 0, hook_z + 0.25), 0.010, hwm, n=4)
    st.box((ax_top, 0, hook_z + 0.18), (0.10, 0.08, 0.14), ctx.mats["accent"])
    st.cyl((ax_top + 0.05, 0.75, az_top + 0.12), (ax_top - 0.20, 0.75, az_top + 1.30), 0.020, rail, n=6)
    # boarding platform at the top of the ramp + vertical ladder from the deck
    px0, px1 = ff_point(FF_LEN).x - 0.18, ff_point(FF_LEN).x + 0.50
    pz = ff_point(FF_LEN).z - 0.06
    st.box_between(px0, px1, -0.80, 0.80, pz - 0.05, pz, ctx.mats["grating"])
    for sgn in (1, -1):
        st.tube([V(px0, sgn * 0.78, pz + 0.42), V(px1, sgn * 0.78, pz + 0.42), V(px1, sgn * 0.25, pz + 0.42)], 0.014, rail, n=6)
        for xx in (px0, (px0 + px1) / 2, px1):
            st.cyl((xx, sgn * 0.78, pz), (xx, sgn * 0.78, pz + 0.42), 0.012, rail, n=6)
    lx = px1 + 0.04
    ldz = ctx.deck_at(lx)[0]
    for yy in (-0.20, 0.20):
        st.cyl((lx, yy, ldz), (lx, yy, pz + 0.45), 0.016, rail, n=6)
    for z in np.arange(ldz + 0.25, pz, 0.25):
        st.cyl((lx, -0.20, float(z)), (lx, 0.20, float(z)), 0.010, rail, n=5)

    # --- rescue boat in a cradle on the bridge deck (stbd, aft), slewing davit at the deck edge ------------
    rb = V(-12.40, -1.95, d3 + 0.30)
    for dx in (-0.42, 0.42):
        st.box(rb + V(dx, 0, -0.19), (0.10, 0.56, 0.16), hwm)
    rib_boat(lb, rb, 1.45, 0.62, orange, hwm)
    dvx, dvy = -11.45, -(HW - 0.18)
    st.cyl((dvx, dvy, d3), (dvx, dvy, d3 + 1.20), 0.075, hwm, n=14)
    st.cyl((dvx, dvy, d3 + 1.18), (rb.x, rb.y, d3 + 1.18), 0.055, hwm, n=10)
    st.cyl((rb.x, rb.y, d3 + 1.15), (rb.x, rb.y, rb.z + 0.12), 0.007, hwm, n=4)
    st.box((dvx, dvy, d3 + 0.02), (0.36, 0.36, 0.04), hwm)

    # --- life-raft canisters in cradles on the deck-2 walkways ------------------------------------------
    for sgn in (1, -1):
        for x in (-11.95, -11.20):
            y = sgn * (HW + 0.34)
            st.box((x, y, d2 + 0.03), (0.56, 0.30, 0.05), hwm)
            for dx in (-0.18, 0.18):
                st.box((x + dx, y, d2 + 0.09), (0.05, 0.30, 0.10), hwm)
            lb.ellipsoid((x, y, d2 + 0.24), (0.31, 0.15, 0.15), white, nu=16, nv=8)
            lb.box((x - 0.33, y, d2 + 0.20), (0.04, 0.06, 0.08), ctx.mats["accent"])   # hydrostatic release

    # --- lifebuoys hung on the stern rail and the house walls --------------------------------------------
    for sgn in (1, -1):
        x = -18.95
        dz, w = ctx.deck_at(x)
        y = sgn * (w - 0.12 - 0.07)
        lb.torus((x, y, dz + 0.31), (0, 1, 0), 0.17, 0.040, orange, n1=20, n2=8)
        st.box((x, sgn * (w - 0.12 - 0.02), dz + 0.46), (0.06, 0.06, 0.05), hwm)
        lb.torus((X0 + 0.3, sgn * (HW + 0.05), 1.70), (0, 1, 0), 0.17, 0.040, orange, n1=20, n2=8)
    lb.finish()
    st.finish()


# ==================================================================================================
# 12. MARKINGS  (name, draft marks, load line, bow-thruster sign) projected onto the real shell
# ==================================================================================================
def text_geometry(text, size=0.3, extrude=0.006):
    cu = bpy.data.curves.new("tmp_txt", type="FONT")
    cu.body = text
    cu.size = size
    cu.extrude = extrude
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    ob = bpy.data.objects.new("tmp_txt", cu)
    bpy.context.scene.collection.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    verts = [tuple(v.co) for v in me.vertices]
    faces = [tuple(p.vertices) for p in me.polygons]
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    bpy.data.meshes.remove(me)
    return verts, faces


def rect2d(a0, a1, b0, b1, d=0.006):
    verts = [(a0, b0, 0), (a1, b0, 0), (a1, b1, 0), (a0, b1, 0), (a0, b0, d), (a1, b0, d), (a1, b1, d), (a0, b1, d)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return verts, faces


def ring2d(r0, r1, n=32, d=0.006):
    verts, faces = [], []
    for k in range(n):
        a = 2 * math.pi * k / n
        for (r, z) in ((r0, 0), (r1, 0), (r1, d), (r0, d)):
            verts.append((r * math.cos(a), r * math.sin(a), z))
    for k in range(n):
        k2 = (k + 1) % n
        for s in range(4):
            s2 = (s + 1) % 4
            faces.append((k * 4 + s, k * 4 + s2, k2 * 4 + s2, k2 * 4 + s))
    return verts, faces


def project_side(ctx, b, geo, x0, z0, side, mat, offset=0.012, scale=1.0, extrude_from=None):
    """Map 2D marking geometry (a = along reading direction, b = up, c = depth) onto the hull side."""
    verts, faces = geo
    cmin = min(v[2] for v in verts) if extrude_from is None else extrude_from
    out = []
    for (a, bb, c) in verts:
        x = x0 + (a * scale) * (-1 if side > 0 else 1)
        z = z0 + bb * scale
        w = ctx.hw(x, z)
        if w <= 0:
            w = ctx.hw(x - 0.05 * (1 if x > 0 else -1), z)
        out.append(V(x, side * (w + offset + (c - cmin)), z))
    b.add_mesh(out, faces, mat)


def project_transom(ctx, b, geo, y0, z0, mat, offset=0.012, scale=1.0):
    verts, faces = geo
    cmin = min(v[2] for v in verts)
    out = []
    for (a, bb, c) in verts:
        y = y0 - a * scale          # viewed from astern, screen-right is -Y
        z = z0 + bb * scale
        hit = ctx.bvh.ray_cast(V(-15.0, y, z), V(-1, 0, 0), 8.0)
        x = hit[0].x if hit[0] is not None else GA["hull"]["transomX"]
        out.append(V(x - offset - (c - cmin), y, z))
    b.add_mesh(out, faces, mat)


def build_markings(ctx):
    mk = Builder("Hull_Markings", uv_scale=1.0)
    white = ctx.mats["marking"]
    name = ctx.cfg.get("ship_name", "ASCEND MARINER")
    port = ctx.cfg.get("home_port", "")
    S = ctx.form.S
    for side in (1, -1):
        project_side(ctx, mk, text_geometry(name, 0.34), 14.4 + S - 1.2, 0.36, side, white)
        # draft marks (Roman numerals, classic style) fore, aft and amidships
        for xm in (22.2, -15.8, 2.6):
            for k, num in enumerate(["II", "IV", "VI", "VIII", "X", "XII", "XIV"]):
                z = KEEL_Z + 0.30 * (k + 1)
                if z > -0.6:
                    continue
                project_side(ctx, mk, text_geometry(num, 0.13), xm, z, side, white)
        # load line: deck line, Plimsoll disc, ladder
        lx = 3.6
        project_side(ctx, mk, rect2d(-0.32, 0.32, -0.012, 0.012), lx, 0.70, side, white)
        project_side(ctx, mk, ring2d(0.15, 0.175), lx, WL_Z, side, white)
        project_side(ctx, mk, rect2d(-0.26, 0.26, -0.011, 0.011), lx, WL_Z, side, white)
        for i, (lbl, dz) in enumerate((("TF", 0.13), ("F", 0.09), ("T", 0.04), ("S", 0.0), ("W", -0.04))):
            a = -0.42 if side > 0 else 0.42
            project_side(ctx, mk, rect2d(-0.07, 0.07, -0.007, 0.007), lx + (-0.50 if side < 0 else 0.50) * 1, WL_Z + dz, side, white)
            project_side(ctx, mk, text_geometry(lbl, 0.05), lx + (-0.62 if side < 0 else 0.62), WL_Z + dz, side, white)
        project_side(ctx, mk, rect2d(-0.006, 0.006, -0.07, 0.15), lx + (-0.43 if side < 0 else 0.43), WL_Z, side, white)
        project_side(ctx, mk, text_geometry("A", 0.10), lx + (-0.22 if side < 0 else 0.22), WL_Z + 0.24, side, white)
        project_side(ctx, mk, text_geometry("C", 0.10), lx + (0.22 if side < 0 else -0.22), WL_Z + 0.24, side, white)
        # bow thruster sign above the tunnel
        project_side(ctx, mk, ring2d(0.20, 0.235), BT_X, -0.55, side, white)
        for ang in (45, -45):
            g = rect2d(-0.19, 0.19, -0.018, 0.018)
            ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            gv = [(a * ca - bb * sa, a * sa + bb * ca, c) for (a, bb, c) in g[0]]
            project_side(ctx, mk, (gv, g[1]), BT_X, -0.55, side, white)
    project_transom(ctx, mk, text_geometry(name, 0.30), 0.0, 0.42, white)
    if port:
        project_transom(ctx, mk, text_geometry(port, 0.17), 0.0, 0.05, white)
    mk.finish()


# ==================================================================================================
# 13. VALIDATION + EXPORT
# ==================================================================================================
def validate(ctx):
    problems = []
    for e in ctx.layout:
        if e["space"] != "hull":
            continue
        for x in (e["x0"], e["x1"]):
            for z in (e["z0"] + 0.02, min(e["z1"], DECK_Z - 0.02)):
                need = max(abs(e["y0"]), abs(e["y1"]))
                have = ctx.hw(x, z)
                if have + 0.015 < need:
                    problems.append(f"{e['id']}: pokes through the shell at x={x:.2f} z={z:.2f} (needs {need:.2f}, hull {have:.2f})")
        for bx in BULKHEADS:
            if e["x0"] < bx < e["x1"] and e["id"] != "bow":
                problems.append(f"{e['id']}: crosses bulkhead at x={bx}")
    for e in ctx.layout:
        if e["space"] == "house":
            if not (HOUSE["x0"] <= e["x0"] and e["x1"] <= HOUSE["x1"]):
                problems.append(f"{e['id']}: outside accommodation length")
    print("\n[hull_lib] layout check:", "OK - every hull/house equipment box fits" if not problems else "")
    for p in problems:
        print("   !!", p)
    return problems


def export(ctx):
    path = os.path.join(MODELS_DIR, ctx.cfg["export"])
    os.makedirs(MODELS_DIR, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=True,
                              export_yup=True, export_image_format="JPEG", export_jpeg_quality=86, export_extras=True)
    tris = sum(len(o.data.loop_triangles) if o.data.loop_triangles else 0 for o in objs)
    size = os.path.getsize(path) / 1e6
    print(f"[hull_lib] exported {path}  ({len(objs)} objects, {size:.2f} MB)")
    return path


# ==================================================================================================
# 14. ENTRY POINT
# ==================================================================================================
def build(cfg):
    t0 = time.time()
    reset_scene()
    Builder.ALL.clear()
    ctx = Ctx(cfg)
    P = cfg["palette"]
    T = cfg.get("textures", {})
    seed = cfg.get("seed", 7)
    rust, grime = T.get("rust", 0.0), T.get("grime", 0.0)
    fl = T.get("frame_lines", 0.0)
    m = ctx.mats
    m["hull_top"] = make_mat("Hull_Topsides_Plating", P["topsides"], 0.42, 0.15,
                             tex_plating("tx_topsides", P["topsides"], seed, frame_lines=fl, rust=rust, grime=grime), 0.55)
    m["hull_under"] = make_mat("Hull_Under_AntiFouling", P["bottom"], 0.62, 0.05,
                               tex_plating("tx_bottom", P["bottom"], seed + 1, frame_lines=fl * 0.6, mottle=0.10, grime=grime * 0.5), 0.45)
    m["hull_boot"] = make_mat("Hull_Waterline_BootTop", P["boot"], 0.45, 0.05,
                              tex_plating("tx_boot", P["boot"], seed + 2, mottle=0.08), 0.45)
    m["deck"] = make_mat("Deck_Marine_Slate_NonSkid", P["deck"], 0.75, 0.05, tex_deck("tx_deck", P["deck"], seed + 3, wear=T.get("deck_wear", 0.15)), 0.5)
    m["hatch"] = make_mat("Deck_Marine_Slate_HatchCover", P["hatch"], 0.6, 0.1, tex_deck("tx_hatch", P["hatch"], seed + 4, plate=1.05, stiff=0.6, wear=0.08), 0.6)
    m["deck_house"] = make_mat("Deck_Marine_Slate_HouseDeck", P.get("house_deck", P["deck"]), 0.7, 0.05)
    m["house"] = make_mat("Superstructure_Paint", P["house"], 0.45, 0.05, tex_paint("tx_house", P["house"], seed + 5, tile=4.0, ppm=128, panel=0.8, grime=grime), 0.4)
    m["window"] = make_mat("Bridge_Window_Tint", P["window"], 0.06, 0.3, alpha=0.75)
    m["funnel"] = make_mat("Funnel_Livery_Paint", P["funnel"], 0.45, 0.05, tex_paint("tx_funnel", P["funnel"], seed + 6, grime=grime), 0.4)
    m["funnel_band"] = make_mat("Funnel_Livery_Band", P["funnel_band"], 0.4, 0.05)
    m["soot"] = make_mat("Funnel_Soot_Black", (0.05, 0.05, 0.05), 0.85, 0.2)
    m["hardware"] = make_mat("Deck_Hardware_DarkSteel", P["hardware"], 0.5, 0.45, tex_paint("tx_hw", P["hardware"], seed + 7, tile=1.0, ppm=256, mottle=0.10), 0.5)
    m["accent"] = make_mat("Deck_Hardware_Accent", P["accent"], 0.5, 0.1)
    m["rail"] = make_mat("Safety_Rail_Steel", P["rail"], 0.35, 0.5)
    m["pad"] = make_mat("Equipment_Foundation_Pad", P["pad"], 0.4, 0.3)
    m["internal"] = make_mat("Internal_Deck_Bulkhead", P["internal"], 0.55, 0.15, tex_paint("tx_internal", P["internal"], seed + 8, tile=2.0, ppm=128, panel=0.6), 0.4)
    m["grating"] = make_mat("Internal_Deck_Bulkhead_Grating", P["grating"], 0.5, 0.5, tex_grating("tx_grating", P["grating"], seed + 9), 0.8)
    m["frame"] = make_mat("Internal_Deck_Bulkhead_Frames", P.get("frame", P["internal"]), 0.5, 0.2)
    m["tank_ballast"] = make_mat("Internal_Deck_Bulkhead_Tank_Ballast", (0.20, 0.62, 0.42), 0.4, 0.0, alpha=0.5)
    m["tank_fuel"] = make_mat("Internal_Deck_Bulkhead_Tank_Fuel", (0.55, 0.36, 0.12), 0.4, 0.0, alpha=0.5)
    m["tank_lube"] = make_mat("Internal_Deck_Bulkhead_Tank_LubeOil", (0.85, 0.70, 0.18), 0.4, 0.0, alpha=0.5)
    m["tank_water"] = make_mat("Internal_Deck_Bulkhead_Tank_FreshWater", (0.22, 0.48, 0.85), 0.4, 0.0, alpha=0.5)
    m["anode"] = make_mat("Hull_Anode_Zinc", (0.62, 0.64, 0.66), 0.6, 0.7)
    m["marking"] = make_mat("Hull_Marking_White", (0.95, 0.95, 0.93), 0.5, 0.0)
    m["lifeboat"] = make_mat("LifeSaving_Orange", (0.95, 0.38, 0.06), 0.45, 0.0)
    m["radome"] = make_mat("Radome_White", (0.94, 0.95, 0.96), 0.3, 0.0)
    m["pipe_red"] = make_mat("Deck_Hardware_FireMain_Red", (0.70, 0.10, 0.08), 0.45, 0.1)
    m["light_white"] = make_mat("NavLight_White", (1.0, 0.97, 0.85), 0.2, 0.0, emit=3.0)
    m["light_port"] = make_mat("NavLight_Port_Red", (0.95, 0.08, 0.06), 0.2, 0.0, emit=3.0)
    m["light_stbd"] = make_mat("NavLight_Stbd_Green", (0.08, 0.85, 0.25), 0.2, 0.0, emit=3.0)

    print("[hull_lib] shell ...")
    build_shell(ctx)
    build_decks(ctx)
    print("[hull_lib] internal structure ...")
    build_internal(ctx)
    print("[hull_lib] appendages + outfit ...")
    build_appendages(ctx)
    build_deck_outfit(ctx)
    build_superstructure(ctx)
    if ctx.has("markings"):
        build_markings(ctx)
    for b in list(Builder.ALL):
        if b.bm.is_valid:
            b.finish()
    validate(ctx)
    path = None
    if cfg.get("export"):
        path = export(ctx)
    print(f"[hull_lib] {cfg['name']} done in {time.time() - t0:.1f}s")
    return ctx, path
