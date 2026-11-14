"""
sales_shots.py - catalogue / marketing images for Caramel Shell 2S.

  blender -b blend/sofa_caramel_shell.blend -P scripts/sales_shots.py -- [--quick] [shot ...]

Builds in memory (the .blend is not modified):
  20_STUDIO       seamless grey cyclorama + softbox lighting
  21_LIFESTYLE    styled living room: herringbone oak, panelled grey wall, arched glass cabinet,
                  sideboard + marble lamp + arc print, arc-pattern rug, travertine table, window + plant
  22_ACCESSORIES  scatter cushions (bouclé / velvet / linen) with piping, dents and corner ears
Renders JPEGs to renders/sales/.
"""
import bpy, bmesh, os, sys, math, random
from math import radians, sin, cos, pi, exp, sqrt
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
QUICK = "--quick" in argv
WANT = [a for a in argv if not a.startswith("--")]
OUT = os.path.join(PROJECT, "renders", "sales")
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
ROOT = bpy.data.objects["SOFA_ROOT"]
RND = random.Random(11)

COLL = {c.name: c for c in bpy.data.collections}
SOFA_VISIBLE = ["04_LEGS_AND_GLIDES", "11_UPHOLSTERY", "12_STITCHING_AND_SEAMS", "13_FABRIC_DETAILS"]
ALWAYS_HIDE = ("ST_Shell_Rim_Seam_Continuous", "MATERIAL_LIBRARY", "REF_Upholstered_Photo",
               "LG_Centre_Support_Adjustable_D40")


def new_coll(name):
    c = bpy.data.collections.new(name); sc.collection.children.link(c); COLL[name] = c; return c


S_C, L_C, A_C, LT_S, LT_L = (new_coll(n) for n in
                             ("20_STUDIO", "21_LIFESTYLE", "22_ACCESSORIES", "23_LIGHTS_STUDIO", "24_LIGHTS_LIFESTYLE"))


# =============================================================== materials
def mat(name, rgb, rough=0.5, metal=0.0, sheen=0.0, coat=0.0, trans=0.0, emit=None):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    o = nt.nodes.new("ShaderNodeOutputMaterial"); b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs[0], o.inputs[0])
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Sheen Weight"].default_value = sheen
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Transmission Weight"].default_value = trans
    if emit:
        b.inputs["Emission Color"].default_value = (*emit[0], 1); b.inputs["Emission Strength"].default_value = emit[1]
    m.diffuse_color = (*rgb, 1)
    return m, nt, b


def noise_bump(nt, b, scale, strength, stretch=(1, 1, 1), coord="Object"):
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = stretch
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = 8
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = strength
    nt.links.new(tc.outputs[coord], mp.inputs["Vector"]); nt.links.new(mp.outputs[0], nz.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return nz


def boucle(name, dark, light, sheen_tint=(1.0, 0.62, 0.32), sheen=0.4):
    """Bouclé (object space in mm): Voronoi curls + smooth cells + fibre fuzz, clump colour variation."""
    m, nt, b = mat(name, light, 0.96, sheen=sheen)
    N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord")
    v1 = N.new("ShaderNodeTexVoronoi"); v1.feature = 'F1'; v1.inputs["Scale"].default_value = 0.17
    v2 = N.new("ShaderNodeTexVoronoi"); v2.feature = 'SMOOTH_F1'; v2.inputs["Scale"].default_value = 0.31
    v2.inputs["Smoothness"].default_value = 0.6
    fib = N.new("ShaderNodeTexNoise"); fib.inputs["Scale"].default_value = 1.1; fib.inputs["Detail"].default_value = 8
    fib.inputs["Roughness"].default_value = 0.7
    clump = N.new("ShaderNodeTexNoise"); clump.inputs["Scale"].default_value = 0.04; clump.inputs["Detail"].default_value = 3
    for n in (v1, v2, fib, clump):
        L.new(tc.outputs["Object"], n.inputs["Vector"])
    h1 = N.new("ShaderNodeMath"); h1.operation = 'MULTIPLY_ADD'
    L.new(v1.outputs["Distance"], h1.inputs[0]); h1.inputs[1].default_value = 0.6; L.new(v2.outputs["Distance"], h1.inputs[2])
    h = N.new("ShaderNodeMath"); h.operation = 'MULTIPLY_ADD'
    L.new(fib.outputs["Fac"], h.inputs[0]); h.inputs[1].default_value = 0.35; L.new(h1.outputs[0], h.inputs[2])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.9; bp.inputs["Distance"].default_value = 2.6
    L.new(h.outputs[0], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    cm = N.new("ShaderNodeMath"); cm.operation = 'MULTIPLY_ADD'
    L.new(clump.outputs["Fac"], cm.inputs[0]); cm.inputs[1].default_value = 0.7; L.new(v1.outputs["Distance"], cm.inputs[2])
    r1 = N.new("ShaderNodeValToRGB")
    r1.color_ramp.elements[0].position = 0.25; r1.color_ramp.elements[0].color = (*dark, 1)
    r1.color_ramp.elements[1].position = 1.05; r1.color_ramp.elements[1].color = (*light, 1)
    L.new(cm.outputs[0], r1.inputs["Fac"])
    r2 = N.new("ShaderNodeValToRGB")
    r2.color_ramp.elements[0].position = 0.0; r2.color_ramp.elements[0].color = (0.72, 0.72, 0.72, 1)
    r2.color_ramp.elements[1].position = 0.8; r2.color_ramp.elements[1].color = (1, 1, 1, 1)
    L.new(h.outputs[0], r2.inputs["Fac"])
    mix = N.new("ShaderNodeMix"); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'; mix.inputs[0].default_value = 1.0
    L.new(r1.outputs["Color"], mix.inputs[6]); L.new(r2.outputs["Color"], mix.inputs[7])
    L.new(mix.outputs[2], b.inputs["Base Color"])
    b.inputs["Sheen Roughness"].default_value = 0.5
    b.inputs["Sheen Tint"].default_value = (*sheen_tint, 1)
    b.inputs["Specular IOR Level"].default_value = 0.15
    return m


COLOURWAYS = {
    "caramel": boucle("SALES_Boucle_Caramel", (0.085, 0.030, 0.007), (0.40, 0.16, 0.040)),
    "ivory": boucle("SALES_Boucle_Ivory", (0.36, 0.32, 0.25), (0.70, 0.65, 0.55), (1.0, 0.97, 0.9)),
    "sage": boucle("SALES_Boucle_Sage", (0.06, 0.08, 0.05), (0.27, 0.32, 0.22), (0.9, 1.0, 0.85)),
    "charcoal": boucle("SALES_Boucle_Charcoal", (0.018, 0.018, 0.018), (0.11, 0.105, 0.10), (0.9, 0.9, 0.9)),
    "terracotta": boucle("SALES_Boucle_Terracotta", (0.11, 0.028, 0.012), (0.46, 0.13, 0.065), (1.0, 0.6, 0.45)),
}
FABRIC_SLOTS = [s for ob in bpy.data.objects for s in getattr(ob, "material_slots", [])
                if s.material and s.material.name == "MAT_Boucle_Caramel"]


def set_colour(key):
    for s in FABRIC_SLOTS:
        s.material = COLOURWAYS[key]


# oak legs with vertical grain (mm object space)
oakleg_m, ont, ob_ = mat("SALES_Oak_Leg", (0.45, 0.31, 0.17), 0.42)
_tc = ont.nodes.new("ShaderNodeTexCoord"); _mp = ont.nodes.new("ShaderNodeMapping")
_mp.inputs["Scale"].default_value = (1.0, 1.0, 0.08); ont.links.new(_tc.outputs["Object"], _mp.inputs["Vector"])
_wv = ont.nodes.new("ShaderNodeTexWave"); _wv.wave_type = 'BANDS'; _wv.bands_direction = 'X'
_wv.inputs["Scale"].default_value = 0.09; _wv.inputs["Distortion"].default_value = 6; _wv.inputs["Detail"].default_value = 4
ont.links.new(_mp.outputs[0], _wv.inputs["Vector"])
_rp = ont.nodes.new("ShaderNodeValToRGB")
_rp.color_ramp.elements[0].color = (0.36, 0.24, 0.13, 1); _rp.color_ramp.elements[1].color = (0.58, 0.43, 0.27, 1)
ont.links.new(_wv.outputs["Fac"], _rp.inputs["Fac"]); ont.links.new(_rp.outputs["Color"], ob_.inputs["Base Color"])
for o in bpy.data.objects:
    if o.name.startswith("LG_Leg_"):
        o.material_slots[0].material = oakleg_m


# =============================================================== geometry helpers (metres)
def obj_from(name, v, f, coll, m, smooth=True, loc=(0, 0, 0), rot=(0, 0, 0), recalc=True):
    me = bpy.data.meshes.new(name); me.from_pydata(v, [], f); me.validate()
    if recalc:
        bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = smooth
    me.materials.append(m)
    ob = bpy.data.objects.new(name, me); ob.location = loc; ob.rotation_euler = rot
    coll.objects.link(ob)
    return ob


def bevel(ob, w, seg=3, angle=40):
    md = ob.modifiers.new("Bevel", 'BEVEL'); md.width = w; md.segments = seg
    md.limit_method = 'ANGLE'; md.angle_limit = radians(angle)


def cube(name, x0, x1, y0, y1, z0, z1, coll, m, bev=0.0):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    ob = obj_from(name, v, f, coll, m, smooth=bool(bev))
    if bev:
        bevel(ob, bev)
    return ob


def lathe(name, cx, cy, prof, coll, m, segs=64, ribs=0, rib_amp=0.03):
    """Revolve a (r, z) profile around a vertical axis."""
    v, f = [], []
    n = len(prof)
    for k in range(segs):
        a = 2 * pi * k / segs
        rr = 1 + (rib_amp * abs(cos(a * ribs / 2)) if ribs else 0)
        v += [(cx + r * rr * cos(a), cy + r * rr * sin(a), z) for r, z in prof]
    for k in range(segs):
        k2 = (k + 1) % segs
        for i in range(n - 1):
            f.append((k * n + i, k2 * n + i, k2 * n + i + 1, k * n + i + 1))
    return obj_from(name, v, f, coll, m)


def cyl(name, cx, cy, z0, z1, r0, coll, m, r1=None, segs=64, bev=0.0):
    r1 = r0 if r1 is None else r1
    ob = lathe(name, cx, cy, [(0.0, z0), (r0, z0), (r1, z1), (0.0, z1)], coll, m, segs)
    if bev:
        bevel(ob, bev)
    return ob


def xz_prism(name, pts, y0, y1, coll, m, bev=0.0):
    """Extrude an (x, z) outline along Y."""
    n = len(pts)
    v = [(x, y0, z) for x, z in pts] + [(x, y1, z) for x, z in pts]
    f = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    ob = obj_from(name, v, f, coll, m, smooth=False)
    if bev:
        bevel(ob, bev, 2)
    return ob


def arc_pts(cx, cz, r, a0, a1, step=6):
    k = max(2, int(abs(a1 - a0) / step) + 1)
    return [(cx + r * cos(radians(a0 + (a1 - a0) * i / (k - 1))), cz + r * sin(radians(a0 + (a1 - a0) * i / (k - 1))))
            for i in range(k)]


def sphere(name, loc, scale, coll, m, rot=(0, 0, 0), seg=(16, 10)):
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg[0], v_segments=seg[1], radius=1.0); bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(m)
    ob = bpy.data.objects.new(name, me); ob.location = loc; ob.scale = scale; ob.rotation_euler = rot
    coll.objects.link(ob); return ob


def area(name, coll, loc, target, energy, size, color=(1, 1, 1), sy=None):
    ld = bpy.data.lights.new(name, 'AREA'); ld.energy = energy; ld.size = size; ld.color = color
    if sy:
        ld.shape = 'RECTANGLE'; ld.size_y = sy
    ob = bpy.data.objects.new(name, ld); ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    coll.objects.link(ob); return ob


# =============================================================== STUDIO (grey seamless cyc)
cyc_m, _, CYC_BSDF = mat("SALES_Cyclorama_Grey", (0.30, 0.295, 0.285), 0.9)
prof = [(0.0, 0.0), (2.0, 0.0), (4.0, 0.0)] + [(5.0 + 1.8 * sin(radians(a)), 1.8 - 1.8 * cos(radians(a)))
                                               for a in range(6, 91, 6)] + [(6.8, 4.0), (6.8, 8.0)]
cy_ob = lathe("STU_Cyclorama", 0, 0, prof, S_C, cyc_m, segs=72)
md = cy_ob.modifiers.new("Sub", 'SUBSURF'); md.levels = 1; md.render_levels = 2
area("STU_Key_Softbox", LT_S, (-2.6, -2.4, 2.6), (0, 0, 0.4), 560, 2.4, (1.0, 0.96, 0.9))
area("STU_Fill", LT_S, (3.0, -2.2, 1.4), (0, 0, 0.4), 150, 3.0, (0.95, 0.97, 1.0))
area("STU_Top", LT_S, (0, 0.2, 3.6), (0, 0, 0), 200, 3.0)
area("STU_Rim", LT_S, (1.2, 3.0, 2.2), (0, 0, 0.5), 300, 2.0, (1.0, 0.92, 0.85))

# =============================================================== LIFESTYLE ROOM
YW = 1.62          # back wall plane
XR = 2.75          # right (window) wall plane

# --- herringbone oak floor (real planks, per-plank tone + UV grain) ---------------
PL, PW, GAP = 0.60, 0.10, 0.0015
verts, faces, uvs, rnd = [], [], [], []
s2 = 1 / sqrt(2)


def rot45(x, y):
    return ((x + y) * s2, (y - x) * s2 - 1.2)


for j in range(-18, 19):
    for n in range(-110, 111):
        bx, by = j * PL + n * PW, -j * PL + n * PW
        for o, ld, wd in (((bx, by), (PL, 0), (0, PW)), ((bx + PL, by + PW - PL), (0, PL), (PW, 0))):
            cxx = o[0] + (ld[0] + wd[0]) / 2; cyy = o[1] + (ld[1] + wd[1]) / 2
            wx, wy = rot45(cxx, cyy)
            if not (-5.0 < wx < 4.0 and -6.5 < wy < YW + 0.1):
                continue
            Lv = Vector((ld[0], ld[1])); Wv = Vector((wd[0], wd[1]))
            Ln, Wn = Lv.normalized(), Wv.normalized()
            p0 = Vector(o) + Ln * GAP + Wn * GAP
            corners = [p0, p0 + Lv - Ln * 2 * GAP, p0 + Lv - Ln * 2 * GAP + Wv - Wn * 2 * GAP, p0 + Wv - Wn * 2 * GAP]
            uv = [(0, 0), (PL, 0), (PL, PW), (0, PW)]
            if Lv.x * Wv.y - Lv.y * Wv.x < 0:
                corners = [corners[0], corners[3], corners[2], corners[1]]; uv = [uv[0], uv[3], uv[2], uv[1]]
            r = RND.random(); off = RND.uniform(0, 5)
            base = len(verts)
            for c in corners:
                x, y = rot45(c.x, c.y); verts.append((x, y, 0.0))
            faces.append((base, base + 1, base + 2, base + 3))
            uvs.append([(u + off, v_ + r * 3) for u, v_ in uv]); rnd.append(r)
me = bpy.data.meshes.new("LS_Floor_Herringbone"); me.from_pydata(verts, [], faces)
uvl = me.uv_layers.new(name="UVMap")
for fi, poly in enumerate(me.polygons):
    for k, li in enumerate(poly.loop_indices):
        uvl.data[li].uv = uvs[fi][k]
at = me.attributes.new("plank_rand", 'FLOAT', 'FACE')
at.data.foreach_set("value", rnd)
fm, fnt, fb = mat("LS_Floor_Oak_Herringbone", (0.55, 0.42, 0.31), 0.42, coat=0.15)
N_, L_ = fnt.nodes, fnt.links
atn = N_.new("ShaderNodeAttribute"); atn.attribute_name = "plank_rand"
tone = N_.new("ShaderNodeValToRGB")
tone.color_ramp.elements[0].color = (0.40, 0.29, 0.21, 1); tone.color_ramp.elements[1].color = (0.62, 0.48, 0.37, 1)
L_.new(atn.outputs["Fac"], tone.inputs["Fac"])
uvn = N_.new("ShaderNodeUVMap"); uvn.uv_map = "UVMap"
gw = N_.new("ShaderNodeTexWave"); gw.bands_direction = 'Y'; gw.inputs["Scale"].default_value = 55
gw.inputs["Distortion"].default_value = 9; gw.inputs["Detail"].default_value = 3
L_.new(uvn.outputs["UV"], gw.inputs["Vector"])
gr = N_.new("ShaderNodeValToRGB")
gr.color_ramp.elements[0].color = (0.80, 0.78, 0.76, 1); gr.color_ramp.elements[1].color = (1, 1, 1, 1)
L_.new(gw.outputs["Fac"], gr.inputs["Fac"])
mx = N_.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs[0].default_value = 1.0
L_.new(tone.outputs["Color"], mx.inputs[6]); L_.new(gr.outputs["Color"], mx.inputs[7])
L_.new(mx.outputs[2], fb.inputs["Base Color"])
fbp = N_.new("ShaderNodeBump"); fbp.inputs["Strength"].default_value = 0.06
L_.new(gw.outputs["Fac"], fbp.inputs["Height"]); L_.new(fbp.outputs["Normal"], fb.inputs["Normal"])
me.materials.append(fm)
for p in me.polygons:
    p.use_smooth = False
fl = bpy.data.objects.new("LS_Floor_Herringbone", me); L_C.objects.link(fl)
gap_m, _, _ = mat("LS_Floor_Gap", (0.10, 0.07, 0.05), 0.8)
cube("LS_Floor_Underlay", -6, 5, -7, 2.0, -0.02, -0.001, L_C, gap_m)

# --- walls: soft warm grey with raised panel mouldings ------------------------------
wall_m, _, _ = mat("LS_Wall_Grey", (0.42, 0.41, 0.395), 0.85)
trim_m, _, _ = mat("LS_Wall_Trim", (0.47, 0.46, 0.445), 0.55)
cube("LS_Wall_Back", -6, XR, YW, YW + 0.1, 0, 3.4, L_C, wall_m)
cube("LS_Skirting", -6, XR, YW - 0.02, YW, 0, 0.16, L_C, trim_m, 0.004)
cube("LS_Dado_Rail", -6, XR, YW - 0.028, YW, 0.95, 1.00, L_C, trim_m, 0.008)
cube("LS_Cornice", -6, XR, YW - 0.06, YW, 3.25, 3.4, L_C, trim_m, 0.01)
for x0 in [-4.2 + i * 1.05 for i in range(7)]:
    for z0, z1 in ((0.28, 0.82), (1.15, 3.05)):
        x1, t = x0 + 0.90, 0.024
        for nm, a, b_, c, d in (("B", x0, x1, z0, z0 + t), ("T", x0, x1, z1 - t, z1),
                                ("L", x0, x0 + t, z0, z1), ("R", x1 - t, x1, z0, z1)):
            cube(f"LS_Moulding_{nm}_{x0:.2f}_{z0}", a, b_, YW - 0.016, YW, c, d, L_C, trim_m, 0.005)
cube("LS_Wall_Right_A", XR, XR + 0.15, -7, -0.75, 0, 3.4, L_C, wall_m)
cube("LS_Wall_Right_B", XR, XR + 0.15, 1.15, YW + 0.1, 0, 3.4, L_C, wall_m)
cube("LS_Wall_Right_Sill", XR, XR + 0.15, -0.75, 1.15, 0, 0.42, L_C, wall_m)
cube("LS_Wall_Right_Head", XR, XR + 0.15, -0.75, 1.15, 2.85, 3.4, L_C, wall_m)
cube("LS_Window_Sill", XR - 0.06, XR + 0.15, -0.8, 1.2, 0.40, 0.44, L_C, trim_m, 0.005)
frame_m, _, _ = mat("LS_Window_Frame_White", (0.78, 0.77, 0.75), 0.4)
for y in (-0.75, 0.175, 1.10):
    cube(f"LS_Win_Stile_{y}", XR - 0.03, XR + 0.08, y, y + 0.05, 0.44, 2.85, L_C, frame_m, 0.004)
for z in (0.44, 1.60, 2.15, 2.80):
    cube(f"LS_Win_Rail_{z}", XR - 0.03, XR + 0.08, -0.75, 1.15, z, z + 0.05, L_C, frame_m, 0.004)
for y in (-0.29, 0.64):
    cube(f"LS_Win_Bar_{y}", XR - 0.01, XR + 0.04, y, y + 0.022, 0.44, 2.85, L_C, frame_m, 0.002)
cube("LS_Window_Reveal_L", XR, XR + 0.15, -0.80, -0.75, 0.42, 2.85, L_C, trim_m)
garden_m, gnt, gb = mat("LS_Outside_Garden", (0.3, 0.45, 0.25), 1.0, emit=((0.55, 0.72, 0.45), 0.9))
gz = gnt.nodes.new("ShaderNodeTexNoise"); gz.inputs["Scale"].default_value = 3.5; gz.inputs["Detail"].default_value = 6
gr2 = gnt.nodes.new("ShaderNodeValToRGB")
gr2.color_ramp.elements[0].color = (0.25, 0.40, 0.18, 1); gr2.color_ramp.elements[1].color = (0.85, 0.92, 0.80, 1)
gnt.links.new(gz.outputs["Fac"], gr2.inputs["Fac"]); gnt.links.new(gr2.outputs["Color"], gb.inputs["Emission Color"])
cube("LS_Outside", XR + 1.5, XR + 1.55, -4, 3, -0.5, 4.5, L_C, garden_m)

# --- arched black glass cabinet (behind the sofa, right) ---------------------------
blk_m, bnt, bbs = mat("LS_Ebonised_Oak", (0.022, 0.022, 0.024), 0.45)
noise_bump(bnt, bbs, 4.0, 0.08, stretch=(1, 1, 18))
oak_m, _, _ = mat("LS_Oak_Light", (0.50, 0.37, 0.24), 0.5)
glass_m, _, _ = mat("LS_Glass", (0.9, 0.9, 0.9), 0.02, trans=1.0)
brass_m, _, _ = mat("LS_Brass", (0.80, 0.58, 0.30), 0.28, metal=1.0)
CX0, CX1, CY0, CY1, ZS = 0.30, 1.50, 1.12, 1.56, 1.85
R = (CX1 - CX0) / 2; CXC = (CX0 + CX1) / 2
cube("LS_Cab_Plinth", CX0, CX1, CY0, CY1, 0, 0.10, L_C, blk_m, 0.004)
cube("LS_Cab_Side_L", CX0, CX0 + 0.04, CY0, CY1, 0.10, ZS, L_C, blk_m, 0.003)
cube("LS_Cab_Side_R", CX1 - 0.04, CX1, CY0, CY1, 0.10, ZS, L_C, blk_m, 0.003)
xz_prism("LS_Cab_Arch_Shell", arc_pts(CXC, ZS, R, 0, 180) + arc_pts(CXC, ZS, R - 0.045, 180, 0), CY0, CY1, L_C, blk_m)
xz_prism("LS_Cab_Back", [(CX0, 0.10), (CX1, 0.10)] + arc_pts(CXC, ZS, R, 0, 180), CY1 - 0.02, CY1 - 0.005, L_C, oak_m)
for z in (0.10, 0.55, 0.98, 1.40, 1.82):
    cube(f"LS_Cab_Shelf_{z}", CX0 + 0.04, CX1 - 0.04, CY0 + 0.04, CY1 - 0.02, z, z + 0.022, L_C, oak_m, 0.002)
for nm, a, b_ in (("L", CX0, CX0 + 0.055), ("C", CXC - 0.03, CXC + 0.03), ("R", CX1 - 0.055, CX1)):
    cube(f"LS_Cab_Stile_{nm}", a, b_, CY0 - 0.02, CY0 + 0.01, 0.10, ZS, L_C, blk_m, 0.004)
cube("LS_Cab_Rail_Bottom", CX0, CX1, CY0 - 0.02, CY0 + 0.01, 0.10, 0.20, L_C, blk_m, 0.004)
xz_prism("LS_Cab_Arch_Frame", arc_pts(CXC, ZS, R, 0, 180) + arc_pts(CXC, ZS, R - 0.06, 180, 0), CY0 - 0.02, CY0 + 0.01,
         L_C, blk_m)
xz_prism("LS_Cab_Glass", [(CX0 + 0.04, 0.2), (CX1 - 0.04, 0.2)] + arc_pts(CXC, ZS, R - 0.05, 0, 180),
         CY0 - 0.006, CY0 - 0.002, L_C, glass_m)
for x in (CXC - 0.06, CXC + 0.05):
    cube(f"LS_Cab_Handle_{x:.2f}", x, x + 0.012, CY0 - 0.05, CY0 - 0.02, 0.85, 1.35, L_C, brass_m, 0.004)
book_cols = [(0.62, 0.58, 0.50), (0.20, 0.22, 0.25), (0.45, 0.28, 0.16), (0.70, 0.68, 0.64), (0.12, 0.18, 0.20),
             (0.55, 0.40, 0.30)]
bmats = [mat(f"LS_Book_{i}", c, 0.6)[0] for i, c in enumerate(book_cols)]
for z in (0.122, 0.572, 1.002, 1.422):
    x = CX0 + 0.07
    while x < CXC - 0.12:
        w = RND.uniform(0.018, 0.035); h = RND.uniform(0.18, 0.27)
        cube(f"LS_CabBook_{z}_{x:.3f}", x, x + w, CY1 - 0.24, CY1 - 0.04, z, z + h, L_C, RND.choice(bmats))
        x += w + 0.002
vase_m, _, _ = mat("LS_Ceramic_White", (0.78, 0.76, 0.72), 0.3, coat=0.3)
lathe("LS_Cab_Vase_1", CXC + 0.30, CY1 - 0.20, [(0, 1.002), (0.07, 1.002), (0.11, 1.10), (0.09, 1.22), (0.04, 1.28),
                                                (0.045, 1.32), (0, 1.32)], L_C, vase_m)
lathe("LS_Cab_Vase_2", CXC + 0.22, CY1 - 0.18, [(0, 0.572), (0.06, 0.572), (0.08, 0.66), (0.03, 0.74), (0, 0.74)], L_C,
      bpy.data.materials["LS_Book_1"])
lathe("LS_Cab_Bowl", CXC + 0.28, CY1 - 0.22, [(0, 1.422), (0.05, 1.422), (0.11, 1.49), (0.105, 1.495), (0, 1.45)], L_C,
      vase_m)

# --- grey sideboard (behind the sofa, left) with lamp, print, books ----------------
sb_m, _, _ = mat("LS_Sideboard_Grey", (0.11, 0.12, 0.13), 0.45)
SX0, SX1, SY0, SY1 = -2.55, -0.65, 1.16, 1.58
cube("LS_SB_Body", SX0, SX1, SY0, SY1, 0.14, 0.86, L_C, sb_m, 0.006)
cube("LS_SB_Top", SX0 - 0.02, SX1 + 0.02, SY0 - 0.02, SY1, 0.86, 0.89, L_C, sb_m, 0.006)
for x in (SX0 + 0.05, SX1 - 0.09):
    for y in (SY0 + 0.04, SY1 - 0.08):
        cube(f"LS_SB_Leg_{x:.2f}_{y:.2f}", x, x + 0.04, y, y + 0.04, 0.0, 0.14, L_C, sb_m, 0.004)
dark_m, _, _ = mat("LS_SB_Recess", (0.05, 0.055, 0.06), 0.6)
for i in range(3):
    x0 = SX0 + 0.04 + i * 0.61
    cube(f"LS_SB_Door_{i}", x0, x0 + 0.58, SY0 - 0.012, SY0, 0.18, 0.82, L_C, sb_m, 0.004)
    for k in range(2):
        ax = x0 + 0.145 + k * 0.29
        xz_prism(f"LS_SB_Arch_{i}_{k}", [(ax - 0.09, 0.30)] + arc_pts(ax, 0.55, 0.09, 180, 0) + [(ax + 0.09, 0.30)],
                 SY0 - 0.016, SY0 - 0.011, L_C, dark_m)
marble_m, mnt, mb = mat("LS_Marble", (0.80, 0.79, 0.77), 0.22, coat=0.4)
mz = mnt.nodes.new("ShaderNodeTexNoise"); mz.inputs["Scale"].default_value = 14; mz.inputs["Detail"].default_value = 10
mz.inputs["Distortion"].default_value = 4
mr = mnt.nodes.new("ShaderNodeValToRGB")
mr.color_ramp.elements[0].position = 0.46; mr.color_ramp.elements[0].color = (0.30, 0.30, 0.31, 1)
mr.color_ramp.elements[1].position = 0.52; mr.color_ramp.elements[1].color = (0.82, 0.81, 0.79, 1)
mnt.links.new(mz.outputs["Fac"], mr.inputs["Fac"]); mnt.links.new(mr.outputs["Color"], mb.inputs["Base Color"])
LX, LY = -1.15, 1.38
lathe("LS_Lamp_Base_Marble", LX, LY, [(0, 0.89), (0.07, 0.89), (0.11, 0.97), (0.12, 1.06), (0.08, 1.15), (0.025, 1.19),
                                     (0, 1.19)], L_C, marble_m, segs=10)
cyl("LS_Lamp_Neck", LX, LY, 1.19, 1.27, 0.012, L_C, brass_m)
shade_m, _, _ = mat("LS_Lamp_Shade_Linen", (0.74, 0.71, 0.66), 0.9, trans=0.25, emit=((1.0, 0.80, 0.55), 0.35))
lathe("LS_Lamp_Shade", LX, LY, [(0.23, 1.25), (0.13, 1.50), (0.128, 1.50), (0.226, 1.25)], L_C, shade_m)
bulb = bpy.data.lights.new("LS_Lamp_Bulb", 'POINT'); bulb.energy = 25; bulb.color = (1.0, 0.76, 0.48)
bulb.shadow_soft_size = 0.05
ob = bpy.data.objects.new("LS_Lamp_Bulb", bulb); ob.location = (LX, LY, 1.36); LT_L.objects.link(ob)
frame_oak, _, _ = mat("LS_Frame_Oak", (0.45, 0.32, 0.20), 0.5)
paper_m, _, _ = mat("LS_Print_Paper", (0.70, 0.68, 0.64), 0.9)
ink_m, _, _ = mat("LS_Print_Ink", (0.025, 0.025, 0.025), 0.7)
art = []
art.append(cube("LS_Art_Frame", -0.37, 0.37, -0.025, 0.0, 0.0, 1.0, L_C, frame_oak, 0.004))
art.append(cube("LS_Art_Paper", -0.33, 0.33, -0.03, -0.025, 0.04, 0.96, L_C, paper_m))
art.append(xz_prism("LS_Art_Disc", arc_pts(0, 0.80, 0.09, 0, 360, 10)[:-1], -0.034, -0.031, L_C, ink_m))
for i, r in enumerate([0.08 + 0.022 * k for k in range(7)]):
    art.append(xz_prism(f"LS_Art_Arc_{i}", arc_pts(0, 0.50, r, 0, 180) + arc_pts(0, 0.50, r - 0.008, 180, 0),
                        -0.034, -0.031, L_C, ink_m))
art.append(xz_prism("LS_Art_HalfDisc", arc_pts(0, 0.22, 0.20, 0, 180), -0.034, -0.031, L_C, ink_m))
art.append(xz_prism("LS_Art_Dot", arc_pts(0, 0.09, 0.05, 0, 360, 12)[:-1], -0.034, -0.031, L_C, ink_m))
art_root = bpy.data.objects.new("LS_Art_Root", None); L_C.objects.link(art_root)
art_root.location = (-2.05, YW - 0.12, 0.89); art_root.rotation_euler = (radians(-8), 0, 0)
for a in art:
    a.parent = art_root
for i, c in enumerate(((0.70, 0.68, 0.63), (0.15, 0.16, 0.18), (0.55, 0.45, 0.35))):
    cube(f"LS_SB_Book_{i}", -1.62, -1.38, 1.30, 1.48, 0.89 + 0.03 * i, 0.89 + 0.03 * i + 0.028, L_C,
         mat(f"LS_SBBook_{i}", c, 0.6)[0], 0.002)
lathe("LS_SB_Object", -1.50, 1.39, [(0, 0.98), (0.05, 0.98), (0.06, 1.03), (0.035, 1.10), (0, 1.12)], L_C, vase_m)

# --- plant in ribbed black pot (right corner) ----------------------------------------
pot_m, _, _ = mat("LS_Planter_Black", (0.035, 0.035, 0.038), 0.5)
lathe("LS_Planter", 2.25, 1.15, [(0, 0.0), (0.20, 0.0), (0.24, 0.05), (0.25, 0.55), (0.23, 0.56), (0, 0.50)], L_C, pot_m,
      segs=160, ribs=48, rib_amp=0.035)
leaf_m, _, lb = mat("LS_Leaf_Green", (0.08, 0.17, 0.05), 0.42, sheen=0.2)
lb.inputs["Subsurface Weight"].default_value = 0.15
leaf2_m, _, _ = mat("LS_Leaf_Variegated", (0.20, 0.28, 0.08), 0.45)
stem_m, _, _ = mat("LS_Stem", (0.10, 0.12, 0.05), 0.7)
pbase = Vector((2.25, 1.15, 0.52))
for i in range(90):
    a = RND.uniform(0, 2 * pi); h = RND.uniform(0.65, 1.9)
    r = RND.uniform(0.04, 0.38) * (1.3 - (h - 0.6) / 1.6)
    p = Vector((2.25 + r * cos(a), 1.15 + r * sin(a) * 0.8, h))
    sphere(f"LS_Leaf_{i}", p, (0.075, 0.035, 0.004), L_C, leaf_m if i % 3 else leaf2_m,
           rot=(RND.uniform(-0.8, 0.8), RND.uniform(-0.6, 0.6), a + RND.uniform(-0.5, 0.5)), seg=(10, 6))
    d = p - pbase
    so = cyl(f"LS_Stem_{i}", 0, 0, 0, d.length, 0.0035, L_C, stem_m, segs=5)
    so.location = pbase; so.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()

# --- rug with concentric-arc fan pattern ------------------------------------------------
rug_m, rnt, rb = mat("LS_Rug_Arcs", (0.60, 0.57, 0.51), 1.0, sheen=0.3)
N_, L_ = rnt.nodes, rnt.links
tcr = N_.new("ShaderNodeTexCoord"); sep = N_.new("ShaderNodeSeparateXYZ"); L_.new(tcr.outputs["Object"], sep.inputs[0])


def M(op, a, b=None):
    n = N_.new("ShaderNodeMath"); n.operation = op
    for i, x in enumerate((a, b)):
        if x is None:
            continue
        if isinstance(x, (int, float)):
            n.inputs[i].default_value = x
        else:
            L_.new(x, n.inputs[i])
    return n.outputs[0]


S = 4.2
xs, ys = M('MULTIPLY', sep.outputs[0], S), M('MULTIPLY', sep.outputs[1], S)
row = M('FLOOR', ys)
xs2 = M('ADD', xs, M('MULTIPLY', M('MODULO', row, 2.0), 0.5))
fx = M('SUBTRACT', M('FRACT', xs2), 0.5); fy = M('FRACT', ys)
d = M('SQRT', M('ADD', M('MULTIPLY', fx, fx), M('MULTIPLY', fy, fy)))
line = M('MULTIPLY', M('LESS_THAN', M('FRACT', M('MULTIPLY', d, 11.0)), 0.24), M('LESS_THAN', d, 0.5))
mixr = N_.new("ShaderNodeMix"); mixr.data_type = 'RGBA'
mixr.inputs[6].default_value = (0.60, 0.57, 0.51, 1); mixr.inputs[7].default_value = (0.16, 0.15, 0.14, 1)
L_.new(line, mixr.inputs[0]); L_.new(mixr.outputs[2], rb.inputs["Base Color"])
noise_bump(rnt, rb, 350.0, 0.35)
cube("LS_Rug", -1.30, 1.95, -2.55, -0.15, 0.0, 0.012, L_C, rug_m, 0.005)

# --- travertine coffee table + books ----------------------------------------------------
trav_m, tnt, tb_ = mat("LS_Travertine", (0.56, 0.51, 0.44), 0.6)
noise_bump(tnt, tb_, 30.0, 0.15, stretch=(1, 1, 6))
cyl("LS_CoffeeTable_Top", 1.30, -1.35, 0.36, 0.40, 0.48, L_C, trav_m, bev=0.014)
lathe("LS_CoffeeTable_Base", 1.30, -1.35, [(0, 0.0), (0.32, 0.0), (0.30, 0.10), (0.27, 0.36), (0, 0.36)], L_C, trav_m)
zb = 0.40
for i, c in enumerate(((0.72, 0.70, 0.66), (0.18, 0.19, 0.21), (0.62, 0.55, 0.46))):
    bo = cube(f"LS_Book_Table_{i}", -0.12, 0.12, -0.085, 0.085, zb, zb + 0.026, L_C, mat(f"LS_TBook_{i}", c, 0.6)[0], 0.002)
    bo.location = (1.12, -1.20, 0); bo.rotation_euler = (0, 0, radians(18 + 10 * i)); zb += 0.026

# --- lights -------------------------------------------------------------------------------
sun = bpy.data.lights.new("LS_Sun", 'SUN'); sun.energy = 3.0; sun.angle = radians(1.2); sun.color = (1.0, 0.93, 0.82)
SUN = bpy.data.objects.new("LS_Sun", sun); SUN.rotation_euler = (radians(55), 0, radians(105)); LT_L.objects.link(SUN)
WIN = area("LS_Window_Glow", LT_L, (XR - 0.05, 0.2, 1.65), (0, 0.2, 1.0), 160, 2.0, (0.92, 0.96, 1.0), sy=2.4)
area("LS_Fill_Camera_Side", LT_L, (-2.4, -3.6, 2.0), (0, 0, 0.5), 80, 2.5, (1.0, 0.95, 0.9))
area("LS_Ceiling_Bounce", LT_L, (0, -0.5, 3.2), (0, -0.5, 0), 60, 3.5, (1.0, 0.97, 0.93))


# =============================================================== SCATTER CUSHIONS (mm, parented to SOFA_ROOT)
def pillow(name, w, h, th, m, loc, rot, seed, pipe=True):
    rr = random.Random(seed); ph = rr.uniform(0, 6)
    N = 22
    idx, pverts, pfaces, boundary = {}, [], [], set()

    def key(i, j, s):
        return (i, j, 0) if i in (0, N) or j in (0, N) else (i, j, s)
    for s in (1, -1):
        for i in range(N + 1):
            for j in range(N + 1):
                k_ = key(i, j, s)
                if k_ in idx:
                    continue
                u, v = -1 + 2 * i / N, -1 + 2 * j / N
                e = (1 - u * u) * (1 - v * v)
                k = e ** 0.5
                x = u * w / 2 * (1 - 0.07 * (1 - v * v))
                y = v * h / 2 * (1 - 0.07 * (1 - u * u))
                zz = s * th / 2 * k
                zz *= 1 - 0.32 * exp(-(u / 0.28) ** 2) * max(0.0, v) ** 3
                zz += s * th * 0.05 * (1 - e) ** 2 * sin(10 * u + 8 * v + ph)
                y -= 0.03 * h * k
                zz += 0.03 * th * (1 - v) * k * s
                idx[k_] = len(pverts); pverts.append((x, y, zz))
                if k_[2] == 0:
                    boundary.add(idx[k_])
        for i in range(N):
            for j in range(N):
                q = (idx[key(i, j, s)], idx[key(i + 1, j, s)], idx[key(i + 1, j + 1, s)], idx[key(i, j + 1, s)])
                pfaces.append(q if s > 0 else tuple(reversed(q)))
    ob = obj_from(name, pverts, pfaces, A_C, m)
    me = ob.data
    try:
        cr = me.attributes.new("crease_edge", 'FLOAT', 'EDGE')
        vals = [0.85 if (e.vertices[0] in boundary and e.vertices[1] in boundary) else 0.0 for e in me.edges]
        cr.data.foreach_set("value", vals)
    except Exception as ex:
        print("crease skipped", ex)
    sd = ob.modifiers.new("Sub", 'SUBSURF'); sd.levels = 2; sd.render_levels = 3
    ob.parent = ROOT; ob.location = loc; ob.rotation_euler = [radians(a) for a in rot]
    if pipe:
        loop = [(i, 0) for i in range(N)] + [(N, j) for j in range(N)] + [(i, N) for i in range(N, 0, -1)] + \
               [(0, j) for j in range(N, 0, -1)]
        cu = bpy.data.curves.new(name + "_Piping", 'CURVE'); cu.dimensions = '3D'
        cu.bevel_depth = 3.2; cu.bevel_resolution = 3
        sp = cu.splines.new('NURBS'); sp.points.add(len(loop) - 1)
        for n_, (i, j) in enumerate(loop):
            x, y, zz = pverts[idx[(i, j, 0)]]; sp.points[n_].co = (x, y, zz, 1)
        sp.use_cyclic_u = True; sp.order_u = 4
        cu.materials.append(m)
        po = bpy.data.objects.new(name + "_Piping", cu); A_C.objects.link(po); po.parent = ob
    return ob


grey_boucle = boucle("ACC_Boucle_Grey", (0.10, 0.10, 0.10), (0.42, 0.41, 0.39), (0.95, 0.95, 0.95))
velvet_m, _, vb = mat("ACC_Velvet_Rust", (0.16, 0.040, 0.016), 0.85, sheen=1.0)
vb.inputs["Specular IOR Level"].default_value = 0.15
noise_bump(_, vb, 0.6, 0.15) if False else None
vb.inputs["Sheen Roughness"].default_value = 0.22; vb.inputs["Sheen Tint"].default_value = (1.0, 0.55, 0.35, 1)
linen_m, lnt, lb2 = mat("ACC_Linen_Oatmeal", (0.42, 0.37, 0.29), 0.92, sheen=0.4)
noise_bump(lnt, lb2, 0.35, 0.5, stretch=(1, 10, 1))
pillow("ACC_Pillow_L_GreyBoucle", 450, 450, 175, grey_boucle, (-470, 90, 675), (75, 0, 14), 1)
pillow("ACC_Pillow_L_RustVelvet", 400, 400, 160, velvet_m, (-285, 15, 640), (78, -3, 7), 2)
pillow("ACC_Pillow_R_Linen", 450, 450, 175, linen_m, (465, 85, 672), (75, 0, -13), 3)


# =============================================================== shots
def cam(name, loc, target, lens=50, fstop=None):
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.clip_start = 0.02; cd.clip_end = 100; cd.sensor_width = 36
    if fstop:
        cd.dof.use_dof = True; cd.dof.aperture_fstop = fstop
        cd.dof.focus_distance = (Vector(target) - Vector(loc)).length
    ob = bpy.data.objects.new(name, cd); ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    sc.collection.objects.link(ob); return ob


def C(loc, target, lens=50, fstop=None):
    return dict(loc=loc, target=target, lens=lens, fstop=fstop)


# name: (camera, set, cushions, colour, (w, h), samples, mood)
SHOTS = {
    "L01_lifestyle_hero": (C((-1.45, -2.25, 1.05), (0.20, 0.15, 0.55), 30), "life", False, "caramel", (1600, 1600), 128, "day"),
    "L02_lifestyle_wide_room": (C((-0.55, -4.9, 1.50), (0.15, 0.4, 0.95), 24), "life", False, "caramel", (1800, 1200), 128, "day"),
    "L03_lifestyle_front_styled": (C((0.05, -3.9, 0.95), (0.05, 0.3, 0.62), 35), "life", True, "caramel", (1800, 1200), 128, "day"),
    "L04_lifestyle_portrait_styled": (C((-1.45, -2.35, 1.00), (-0.15, 0.1, 0.52), 40), "life", True, "caramel", (1200, 1500), 128, "day"),
    "L05_lifestyle_window_side": (C((2.25, -2.85, 1.25), (-0.15, 0.2, 0.55), 32), "life", False, "caramel", (1800, 1200), 128, "day"),
    "L06_lifestyle_golden_hour": (C((-1.45, -2.25, 1.05), (0.20, 0.15, 0.55), 30), "life", True, "caramel", (1600, 1600), 128, "golden"),
    "S01_studio_three_quarter_left": (C((-2.35, -3.05, 1.15), (0.02, 0, 0.36)), "studio", False, "caramel", (1600, 1200), 96, "grey"),
    "S02_studio_front": (C((0, -4.6, 0.62), (0, 0, 0.40)), "studio", False, "caramel", (1600, 1000), 80, "grey"),
    "S03_studio_three_quarter_right": (C((2.35, -3.05, 1.15), (-0.02, 0, 0.36)), "studio", False, "caramel", (1600, 1200), 80, "grey"),
    "S04_studio_side_profile": (C((-4.3, -0.08, 0.55), (0, -0.08, 0.40)), "studio", False, "caramel", (1600, 1000), 80, "grey"),
    "S05_studio_rear_three_quarter": (C((2.3, 3.1, 1.35), (0, 0, 0.38)), "studio", False, "caramel", (1600, 1200), 80, "grey"),
    "S06_studio_birdseye": (C((0, -1.9, 3.9), (0, -0.05, 0.25)), "studio", False, "caramel", (1600, 1200), 80, "grey"),
    "S07_studio_styled_cushions": (C((-2.1, -2.9, 1.05), (0.05, 0, 0.42)), "studio", True, "caramel", (1600, 1200), 96, "grey"),
    "S08_studio_charcoal_backdrop": (C((-2.35, -3.05, 1.15), (0.02, 0, 0.36)), "studio", False, "caramel", (1600, 1200), 96, "dark"),
    "D01_detail_boucle_macro": (C((-1.20, -0.85, 0.92), (-0.84, -0.40, 0.62), 100, 8.0), "life", False, "caramel", (1600, 1200), 96, "day"),
    "D02_detail_arm_curve": (C((-1.55, -1.30, 0.92), (-0.83, -0.33, 0.52), 85, 4.0), "life", True, "caramel", (1600, 1200), 96, "day"),
    "D03_detail_oak_leg": (C((-1.20, -1.00, 0.13), (-0.87, -0.31, 0.07), 85, 5.6), "life", False, "caramel", (1600, 1200), 96, "day"),
    "D04_detail_cushions": (C((0.75, -1.65, 1.05), (-0.20, 0.05, 0.58), 50, 5.6), "life", True, "caramel", (1600, 1200), 96, "day"),
}
SHOTS["S07_studio_styled_cushions_4K"] = (C((-2.1, -2.9, 1.05), (0.05, 0, 0.42)), "studio", True, "caramel", (3840, 2880), 256, "grey")
for col in ("ivory", "sage", "charcoal", "terracotta"):
    SHOTS[f"C_{col}_studio"] = (C((-2.35, -3.05, 1.15), (0.02, 0, 0.36)), "studio", False, col, (1600, 1200), 80, "grey")


def set_mood(mood):
    bg = sc.world.node_tree.nodes["Background"]
    if mood in ("grey", "dark"):
        CYC_BSDF.inputs["Base Color"].default_value = (0.30, 0.295, 0.285, 1) if mood == "grey" else (0.045, 0.045, 0.05, 1)
        bg.inputs["Color"].default_value = (0.6, 0.6, 0.6, 1); bg.inputs["Strength"].default_value = 0.10
    else:
        bg.inputs["Color"].default_value = (0.78, 0.84, 0.95, 1); bg.inputs["Strength"].default_value = 0.30
        if mood == "golden":
            SUN.rotation_euler = (radians(76), 0, radians(112)); sun.energy = 4.0; sun.color = (1.0, 0.68, 0.40)
            WIN.data.color = (1.0, 0.78, 0.55); WIN.data.energy = 120; bulb.energy = 45
        else:
            SUN.rotation_euler = (radians(55), 0, radians(105)); sun.energy = 3.0; sun.color = (1.0, 0.93, 0.82)
            WIN.data.color = (0.92, 0.96, 1.0); WIN.data.energy = 160; bulb.energy = 25


def show(set_name, cushions):
    for c in bpy.data.collections:
        c.hide_render = True
    for n in SOFA_VISIBLE:
        COLL[n].hide_render = False
    (S_C if set_name == "studio" else L_C).hide_render = False
    (LT_S if set_name == "studio" else LT_L).hide_render = False
    A_C.hide_render = not cushions
    for ob in bpy.data.objects:
        if ob.name in ALWAYS_HIDE or ob.name.startswith("EH_"):
            ob.hide_render = True


sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.cycles.use_denoising = True
try:
    sc.cycles.denoiser = 'OPENIMAGEDENOISE'
except Exception:
    pass
sc.cycles.max_bounces = 10
sc.render.film_transparent = False
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Medium High Contrast'
sc.render.image_settings.file_format = 'JPEG'
sc.render.image_settings.quality = 92
ROOT["explode"] = 0.0

for key, (cargs, set_name, cushions, colour, res, spp, mood) in SHOTS.items():
    if WANT and key not in WANT:
        continue
    show(set_name, cushions)
    set_mood(mood)
    set_colour(colour)
    sc.camera = cam("SALESCAM_" + key, **cargs)
    sc.render.resolution_x, sc.render.resolution_y = (res[0] // 2, res[1] // 2) if QUICK else res
    sc.cycles.samples = 16 if QUICK else spp
    sc.view_settings.exposure = -0.25 if set_name == "studio" else -0.2
    sc.render.filepath = os.path.join(OUT, ("quick_" if QUICK else "") + key + ".jpg")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", sc.render.filepath, flush=True)
set_colour("caramel")
