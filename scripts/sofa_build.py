"""
sofa_build.py  -  Caramel Shell 2S : parametric two-seat bouclé shell sofa
=========================================================================
Generates the complete, editable Blender scene from scratch:
frame, joinery, legs, sinuous-spring suspension, deck, layered foam,
fibre, ticking, upholstery, seams, materials, interior, cameras,
engineering helpers, dimensions and an exploded-view control.

Run (headless):
    blender -b -P scripts/sofa_build.py
Output:
    blend/sofa_caramel_shell.blend
    docs/component_dump.csv

UNITS
  All sofa geometry is authored in MILLIMETRES inside an empty "SOFA_ROOT"
  that is scaled 0.001, so the sofa is real-size in metres for lighting /
  cameras while every vertex, modifier width and offset stays in mm.
  Scene units display millimetres.
AXES
  X = width (centred), -Y = FRONT of sofa, +Z = up, floor at Z = 0.
EXPLODED VIEW
  Select SOFA_ROOT -> Object Properties -> Custom Properties -> "explode"
  (0 = assembled, 1 = fully exploded). Driven by simple-expression drivers.
"""
import bpy, bmesh, math, os, csv
from math import sin, cos, radians, pi, hypot, exp
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
BLEND_OUT = os.path.join(PROJECT, "blend", "sofa_caramel_shell.blend")
REF_IMG = os.path.join(PROJECT, "reference", "reference_upholstered.jpg")
DUMP_CSV = os.path.join(PROJECT, "docs", "component_dump.csv")

# ---------------------------------------------------------------------------
# DESIGN PARAMETERS (mm) - see docs/01_STAGE1_design_specification.md
# ---------------------------------------------------------------------------
P = dict(
    W=1900, D=900, H=780,
    X_ARM_IN=705.0,       # inner face of arm upholstery
    Y_BACK_IN=270.0,      # inner face of back shell at its base
    R_CORNER=120.0,       # plan radius of inner shell line at back corners
    Y_ARM0=-300.0,        # where the straight arm starts (150 mm rounded nose in front of it)
    ZB=100.0,             # frame underside / shell bottom
    ARM_W=235.0, BACK_W=170.0,
    ARM_H_FRONT=640.0, ARM_H_BACK=760.0, BACK_H=780.0,
    # seat box
    FRONT_RAIL=(-330.0, -292.0, 100.0, 220.0),   # y0,y1,z0,z1 (38x120 beech)
    REAR_RAIL=(230.0, 268.0, 100.0, 186.0),      # 38x86 beech
    PANEL_X=(762.5, 780.5),                      # inner arm ply panel |x|
    SIDE_RAIL_X=(780.5, 818.5),
    # suspension
    SPR_Y0=-311.0, SPR_Y1=249.0, SPR_Z0=223.0, SPR_Z1=189.0, SPR_CROWN=22.0,
    SPR_WIRE_R=2.05, SPR_A=17.0, SPR_PITCH=22.0,
    # cushions
    SEAT_CUSH=(709.0, 515.0, 175.0), SEAT_CUSH_Y=(-425.0, 90.0), SEAT_FRONT_BOTTOM_Z=264.0,
    SEAT_RAKE_DEG=0.85,
    BACK_CUSH=(701.0, 185.0, 150.0, 520.0),  # width, t_bottom, t_top, height
    BACK_CUSH_ORIGIN=(90.0, 247.0), BACK_TILT_DEG=10.0,
    # legs
    LEG_D=80.0, LEG_H=94.0, GLIDE_H=5.0,
    LEG_FRONT=(870.0, -310.0), LEG_REAR=(800.0, 290.0),
)

X_ARM_IN, Y_BACK_IN, R_C, Y_ARM0, ZB = P["X_ARM_IN"], P["Y_BACK_IN"], P["R_CORNER"], P["Y_ARM0"], P["ZB"]
ARM_LEN = (Y_BACK_IN - R_C) - Y_ARM0
CL = pi / 2 * R_C
BACK_HALF = X_ARM_IN - R_C
TOTAL = 2 * (ARM_LEN + CL + BACK_HALF)

COLL_NAMES = [
    "00_REFERENCE_IMAGES", "01_MAIN_FRAME", "02_WOODEN_REINFORCEMENTS", "03_FRAME_JOINTS",
    "04_LEGS_AND_GLIDES", "05_SEAT_SUSPENSION", "06_SPRING_CLIPS", "07_SEAT_FOAM", "08_BACK_FOAM",
    "09_ARMREST_FOAM", "10_CUSHION_TICKING", "11_UPHOLSTERY", "12_STITCHING_AND_SEAMS",
    "13_FABRIC_DETAILS", "14_MATERIALS", "15_LIGHTING", "16_CAMERA", "17_ENGINEERING_HELPERS",
    "18_DIMENSIONS_AND_LABELS", "19_ENVIRONMENT",
]
C = {}
MATS = {}
EX = {}          # object name -> explode offset (mm, parent space)
ROOT = None


# ---------------------------------------------------------------------------
# SCENE SETUP
# ---------------------------------------------------------------------------
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.length_unit = 'MILLIMETERS'
    sc.unit_settings.scale_length = 1.0
    for n in COLL_NAMES:
        c = bpy.data.collections.new(n)
        sc.collection.children.link(c)
        C[n] = c
    for sub in ("18a_DIM_FRONT", "18b_DIM_SIDE", "18c_DIM_TOP", "18d_EXPLODE_LABELS"):
        c = bpy.data.collections.new(sub)
        C["18_DIMENSIONS_AND_LABELS"].children.link(c)
        C[sub] = c


def make_root():
    global ROOT
    ROOT = bpy.data.objects.new("SOFA_ROOT", None)
    ROOT.empty_display_type = 'PLAIN_AXES'
    ROOT.empty_display_size = 200
    ROOT.scale = (0.001, 0.001, 0.001)
    C["17_ENGINEERING_HELPERS"].objects.link(ROOT)
    ROOT["explode"] = 0.0
    try:
        ROOT.id_properties_ui("explode").update(min=0.0, max=1.0, soft_min=0.0, soft_max=1.0,
                                                description="0 = assembled, 1 = exploded assembly view")
    except Exception:
        pass


def link(ob, coll, ex=(0, 0, 0)):
    C[coll].objects.link(ob)
    ob.parent = ROOT
    EX[ob.name] = ex
    return ob


# ---------------------------------------------------------------------------
# MATERIALS (procedural)
# ---------------------------------------------------------------------------
def _new_mat(name):
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (600, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled"); bsdf.location = (300, 0)
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    MATS[name] = m
    return m, nt, bsdf


def _set(node, key, val):
    try:
        node.inputs[key].default_value = val
    except Exception:
        pass


def mat_simple(name, rgb, rough=0.6, metal=0.0, sheen=0.0, vp=None, bump_scale=None, bump_str=0.2):
    m, nt, b = _new_mat(name)
    _set(b, "Base Color", (*rgb, 1)); _set(b, "Roughness", rough); _set(b, "Metallic", metal)
    if sheen:
        _set(b, "Sheen Weight", sheen); _set(b, "Sheen Roughness", 0.5)
    if bump_scale:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        nz = nt.nodes.new("ShaderNodeTexNoise"); _set(nz, "Scale", bump_scale); _set(nz, "Detail", 6.0)
        bp = nt.nodes.new("ShaderNodeBump"); _set(bp, "Strength", bump_str); _set(bp, "Distance", 0.5)
        nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
        nt.links.new(nz.outputs["Fac"], bp.inputs["Height"])
        nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    m.diffuse_color = (*(vp or rgb), 1)
    return m


def mat_boucle():
    """Teddy/bouclé: curly loop bumps (Voronoi) + fibre noise + clump colour variation + sheen."""
    m, nt, b = _new_mat("MAT_Boucle_Caramel")
    N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord"); tc.location = (-1300, 0)
    vor = N.new("ShaderNodeTexVoronoi"); vor.location = (-1000, 200)
    vor.feature = 'F1'; _set(vor, "Scale", 0.17); _set(vor, "Randomness", 1.0)       # ~6 mm curls
    vor2 = N.new("ShaderNodeTexVoronoi"); vor2.location = (-1000, -50)
    vor2.feature = 'DISTANCE_TO_EDGE'; _set(vor2, "Scale", 0.33)
    fib = N.new("ShaderNodeTexNoise"); fib.location = (-1000, -300)
    _set(fib, "Scale", 1.1); _set(fib, "Detail", 8.0); _set(fib, "Roughness", 0.7)  # fine fibres
    clump = N.new("ShaderNodeTexNoise"); clump.location = (-1000, 450)
    _set(clump, "Scale", 0.04); _set(clump, "Detail", 3.0)                           # ~25 mm clumps
    for n in (vor, vor2, fib, clump):
        L.new(tc.outputs["Object"], n.inputs["Vector"])
    # height = 0.5*vor + 0.25*edge + 0.25*fibre
    m1 = N.new("ShaderNodeMath"); m1.operation = 'MULTIPLY_ADD'; m1.location = (-700, 100)
    L.new(vor.outputs["Distance"], m1.inputs[0]); m1.inputs[1].default_value = 0.55
    L.new(vor2.outputs["Distance"], m1.inputs[2])
    m2 = N.new("ShaderNodeMath"); m2.operation = 'MULTIPLY_ADD'; m2.location = (-500, 0)
    L.new(fib.outputs["Fac"], m2.inputs[0]); m2.inputs[1].default_value = 0.35
    L.new(m1.outputs[0], m2.inputs[2])
    bump = N.new("ShaderNodeBump"); bump.location = (-200, -200)
    _set(bump, "Strength", 1.0); _set(bump, "Distance", 3.5)
    L.new(m2.outputs[0], bump.inputs["Height"])
    L.new(bump.outputs["Normal"], b.inputs["Normal"])
    # colour: clump variation + loop shading
    cm = N.new("ShaderNodeMath"); cm.operation = 'MULTIPLY_ADD'; cm.location = (-700, 400)
    L.new(clump.outputs["Fac"], cm.inputs[0]); cm.inputs[1].default_value = 0.7
    L.new(vor.outputs["Distance"], cm.inputs[2])
    ramp = N.new("ShaderNodeValToRGB"); ramp.location = (-450, 400)
    ramp.color_ramp.elements[0].position = 0.25
    ramp.color_ramp.elements[0].color = (0.085, 0.030, 0.007, 1)
    ramp.color_ramp.elements[1].position = 1.05
    ramp.color_ramp.elements[1].color = (0.400, 0.160, 0.040, 1)
    L.new(cm.outputs[0], ramp.inputs["Fac"])
    L.new(ramp.outputs["Color"], b.inputs["Base Color"])
    _set(b, "Roughness", 0.96); _set(b, "Specular IOR Level", 0.15)
    _set(b, "Sheen Weight", 0.35); _set(b, "Sheen Roughness", 0.5)
    _set(b, "Sheen Tint", (1.0, 0.62, 0.32, 1))
    m.diffuse_color = (0.42, 0.20, 0.07, 1)
    return m


def mat_wood(name, c_light, c_dark, scale=0.12, rough=0.5, world=False):
    m, nt, b = _new_mat(name)
    N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1.0, 1.0, 6.0)
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    wv = N.new("ShaderNodeTexWave"); wv.wave_type = 'RINGS'
    _set(wv, "Scale", scale); _set(wv, "Distortion", 5.0); _set(wv, "Detail", 3.0); _set(wv, "Detail Scale", 1.5)
    L.new(mp.outputs[0], wv.inputs["Vector"])
    rp = N.new("ShaderNodeValToRGB")
    rp.color_ramp.elements[0].color = (*c_dark, 1); rp.color_ramp.elements[1].color = (*c_light, 1)
    rp.color_ramp.elements[0].position = 0.15; rp.color_ramp.elements[1].position = 0.75
    L.new(wv.outputs["Fac"], rp.inputs["Fac"]); L.new(rp.outputs["Color"], b.inputs["Base Color"])
    bp = N.new("ShaderNodeBump"); _set(bp, "Strength", 0.08)
    L.new(wv.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    _set(b, "Roughness", rough)
    m.diffuse_color = (*c_light, 1)
    return m


def mat_floor():
    m, nt, b = _new_mat("MAT_Env_Floor_Oak")
    N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord")
    br = N.new("ShaderNodeTexBrick")
    _set(br, "Scale", 1.0); _set(br, "Mortar Size", 0.0015); _set(br, "Brick Width", 1.1)
    _set(br, "Row Height", 0.14); _set(br, "Color1", (0.42, 0.29, 0.18, 1)); _set(br, "Color2", (0.33, 0.22, 0.13, 1))
    _set(br, "Mortar", (0.12, 0.08, 0.05, 1)); _set(br, "Bias", 0.0)
    br.offset = 0.37
    L.new(tc.outputs["Object"], br.inputs["Vector"])
    nz = N.new("ShaderNodeTexNoise"); _set(nz, "Scale", 60.0); _set(nz, "Detail", 4.0)
    mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1.0, 25.0, 1.0)
    L.new(tc.outputs["Object"], mp.inputs["Vector"]); L.new(mp.outputs[0], nz.inputs["Vector"])
    mix = N.new("ShaderNodeMath"); mix.operation = 'MULTIPLY_ADD'
    L.new(nz.outputs["Fac"], mix.inputs[0]); mix.inputs[1].default_value = 0.25; mix.inputs[2].default_value = 0.85
    hue = N.new("ShaderNodeHueSaturation")
    L.new(br.outputs["Color"], hue.inputs["Color"]); L.new(mix.outputs[0], hue.inputs["Value"])
    L.new(hue.outputs["Color"], b.inputs["Base Color"])
    bp = N.new("ShaderNodeBump"); _set(bp, "Strength", 0.3)
    L.new(br.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    _set(b, "Roughness", 0.45)
    m.diffuse_color = (0.4, 0.28, 0.17, 1)
    return m


def build_materials():
    mat_boucle()
    mat_simple("MAT_Lining_Interior", (0.30, 0.28, 0.26), 0.9, bump_scale=2.0)
    mat_simple("MAT_DustCover_Black", (0.015, 0.015, 0.015), 0.95, bump_scale=3.0)
    mat_simple("MAT_Decking_Grey", (0.07, 0.07, 0.075), 0.95, bump_scale=3.0)
    mat_simple("MAT_Felt_Insulator", (0.33, 0.30, 0.26), 1.0, bump_scale=1.5, bump_str=0.4)
    mat_simple("MAT_Ticking_Cotton", (0.86, 0.85, 0.80), 0.85, bump_scale=2.5, bump_str=0.1)
    mat_simple("MAT_Fibre_Polyester", (0.93, 0.93, 0.91), 1.0, sheen=1.0, bump_scale=0.6, bump_str=0.5)
    mat_simple("MAT_Foam_HR40_Core", (0.82, 0.74, 0.48), 0.9, bump_scale=1.2, bump_str=0.35)
    mat_simple("MAT_Foam_HR35_Comfort", (0.60, 0.62, 0.62), 0.9, bump_scale=1.2, bump_str=0.35)
    mat_simple("MAT_Foam_HR30_Back", (0.55, 0.70, 0.55), 0.9, bump_scale=1.2, bump_str=0.35)
    mat_simple("MAT_Foam_Firm_Shell", (0.25, 0.37, 0.52), 0.9, bump_scale=1.2, bump_str=0.35)
    mat_simple("MAT_Foam_Soft_Shell", (0.86, 0.78, 0.40), 0.9, bump_scale=1.2, bump_str=0.35)
    mat_simple("MAT_Steel_Spring", (0.55, 0.56, 0.58), 0.35, metal=1.0)
    mat_simple("MAT_Steel_Zinc", (0.75, 0.75, 0.73), 0.3, metal=1.0)
    mat_simple("MAT_Plastic_Black", (0.02, 0.02, 0.02), 0.45)
    mat_simple("MAT_Glide_Felt", (0.18, 0.18, 0.18), 1.0, bump_scale=2.0)
    mat_simple("MAT_Thread_Seam", (0.20, 0.08, 0.025), 0.8)
    mat_simple("MAT_Zipper", (0.10, 0.06, 0.03), 0.4, metal=0.6)
    mat_simple("MAT_Glue_Dowel", (0.72, 0.58, 0.40), 0.6)
    mat_simple("MAT_Helper_Red", (0.8, 0.05, 0.03), 0.5)
    mat_simple("MAT_Helper_Green", (0.05, 0.6, 0.1), 0.5)
    mat_simple("MAT_Dim_Black", (0.0, 0.0, 0.0), 1.0)
    mat_wood("MAT_Wood_Oak_Legs", (0.50, 0.35, 0.20), (0.34, 0.22, 0.11), scale=0.10, rough=0.5)
    mat_wood("MAT_Wood_Beech", (0.50, 0.31, 0.18), (0.40, 0.24, 0.13), scale=0.08, rough=0.6)
    mat_wood("MAT_Plywood_Birch", (0.62, 0.47, 0.30), (0.52, 0.38, 0.22), scale=0.05, rough=0.6)
    mat_wood("MAT_Plywood_Bending", (0.64, 0.52, 0.36), (0.55, 0.43, 0.28), scale=0.05, rough=0.65)
    mat_floor()
    mat_simple("MAT_Env_Wall", (0.48, 0.45, 0.41), 0.9)
    mat_simple("MAT_Env_Rug", (0.26, 0.245, 0.22), 1.0, sheen=0.2, bump_scale=40.0, bump_str=0.4)
    mat_simple("MAT_Env_Stone", (0.62, 0.59, 0.54), 0.7, bump_scale=8.0, bump_str=0.15)
    mat_simple("MAT_Env_Cabinet", (0.05, 0.055, 0.06), 0.5)
    mat_simple("MAT_Env_Canvas", (0.85, 0.83, 0.78), 0.9)
    mat_simple("MAT_Env_Leaf", (0.12, 0.22, 0.06), 0.6)
    # Material holder object so 14_MATERIALS is not empty and every material is listed
    me = bpy.data.meshes.new("MATERIAL_LIBRARY")
    me.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    for m in MATS.values():
        me.materials.append(m)
    ob = bpy.data.objects.new("MATERIAL_LIBRARY", me)
    C["14_MATERIALS"].objects.link(ob)
    ob.hide_render = True; ob.hide_viewport = True


# ---------------------------------------------------------------------------
# GEOMETRY HELPERS
# ---------------------------------------------------------------------------
def mesh_obj(name, verts, faces, coll, mat, smooth=True, ex=(0, 0, 0), loc=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.validate()
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    if isinstance(mat, (list, tuple)):
        for mm in mat:
            me.materials.append(MATS[mm])
    elif mat:
        me.materials.append(MATS[mat])
    for p in me.polygons:
        p.use_smooth = smooth
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    return link(ob, coll, ex)


def add_bevel(ob, width, segs=2, angle=35):
    md = ob.modifiers.new("Bevel", 'BEVEL')
    md.width = width; md.segments = segs
    md.limit_method = 'ANGLE'; md.angle_limit = radians(angle)
    md.harden_normals = False
    return md


def add_subsurf(ob, vp=1, rd=2):
    md = ob.modifiers.new("Subdivision", 'SUBSURF')
    md.levels = vp; md.render_levels = rd
    return md


def add_solidify(ob, t, offset=0.0):
    md = ob.modifiers.new("Solidify", 'SOLIDIFY')
    md.thickness = t; md.offset = offset; md.use_even_offset = False; md.use_quality_normals = True
    return md


def add_wn(ob):
    try:
        md = ob.modifiers.new("WeightedNormal", 'WEIGHTED_NORMAL'); md.keep_sharp = True
    except Exception:
        pass


def box(name, x0, x1, y0, y1, z0, z1, coll, mat, bevel=1.5, ex=(0, 0, 0)):
    cx, cy, cz = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
    hx, hy, hz = abs(x1 - x0) / 2, abs(y1 - y0) / 2, abs(z1 - z0) / 2
    v = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
         (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    ob = mesh_obj(name, v, f, coll, mat, smooth=True, ex=ex, loc=(cx, cy, cz))
    if bevel:
        add_bevel(ob, min(bevel, hx * 0.9, hy * 0.9, hz * 0.9), 2)
        add_wn(ob)
    return ob


def cylinder(name, center, radius, length, axis, coll, mat, segs=32, bevel=0.0, ex=(0, 0, 0)):
    v, f = [], []
    for k in (-0.5, 0.5):
        for i in range(segs):
            a = 2 * pi * i / segs
            v.append((radius * cos(a), radius * sin(a), k * length))
    for i in range(segs):
        j = (i + 1) % segs
        f.append((i, j, segs + j, segs + i))
    f.append(tuple(reversed(range(segs)))); f.append(tuple(range(segs, 2 * segs)))
    if axis == 'X':
        v = [(z, y, -x) for x, y, z in v]
    elif axis == 'Y':
        v = [(x, z, -y) for x, y, z in v]
    ob = mesh_obj(name, v, f, coll, mat, smooth=True, ex=ex, loc=center)
    if bevel:
        add_bevel(ob, bevel, 3, 40)
    add_wn(ob)
    return ob


def prism(name, poly, z0, z1, coll, mat, bevel=1.0, ex=(0, 0, 0)):
    n = len(poly)
    v = [(x, y, z0) for x, y in poly] + [(x, y, z1) for x, y in poly]
    f = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        f.append((i, j, n + j, n + i))
    ob = mesh_obj(name, v, f, coll, mat, smooth=True, ex=ex)
    if bevel:
        add_bevel(ob, bevel, 2); add_wn(ob)
    return ob


def loft(rings, closed=False, cap_start=False, cap_end=False):
    m = len(rings[0]); verts, faces = [], []
    for r in rings:
        verts += [tuple(p) for p in r]
    nseg = m if closed else m - 1
    for i in range(len(rings) - 1):
        for j in range(nseg):
            j2 = (j + 1) % m
            faces.append((i * m + j, i * m + j2, (i + 1) * m + j2, (i + 1) * m + j))
    if cap_start:
        faces.append(tuple(reversed(range(m))))
    if cap_end:
        k = (len(rings) - 1) * m
        faces.append(tuple(range(k, k + m)))
    return verts, faces


def poly_curve(name, pts_list, coll, mat, radius, cyclic=False, ex=(0, 0, 0), res=2):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'; cu.bevel_depth = radius; cu.bevel_resolution = res
    cu.use_fill_caps = True
    for pts in pts_list:
        sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
        for i, p in enumerate(pts):
            sp.points[i].co = (p[0], p[1], p[2], 1.0)
        sp.use_cyclic_u = cyclic
    cu.materials.append(MATS[mat])
    ob = bpy.data.objects.new(name, cu)
    return link(ob, coll, ex)


# ---------------------------------------------------------------------------
# SHELL PATH (plan) + CROSS-SECTION PROFILE
# The arms + back are ONE continuous shell swept along a U-shaped path that
# follows the inner face: left arm -> left corner -> back -> right corner -> right arm.
# ---------------------------------------------------------------------------
def path_left(s):
    if s <= ARM_LEN:
        return (-X_ARM_IN, Y_ARM0 + s, -1.0, 0.0, 0.0, 1.0)
    s2 = s - ARM_LEN
    if s2 <= CL:
        a = pi - s2 / R_C
        cx, cy = -X_ARM_IN + R_C, Y_BACK_IN - R_C
        return (cx + R_C * cos(a), cy + R_C * sin(a), cos(a), sin(a), sin(a), -cos(a))
    s3 = s2 - CL
    return (-BACK_HALF + s3, Y_BACK_IN, 0.0, 1.0, 1.0, 0.0)


def path_point(s):
    if s <= TOTAL / 2:
        return path_left(s)
    x, y, nx, ny, tx, ty = path_left(TOTAL - s)
    return (-x, y, -nx, ny, tx, -ty)


def shape_at(d):
    """Section parameters vs distance d from the arm front (symmetric)."""
    if d <= ARM_LEN:
        f = d / ARM_LEN; sm = f * f * (3 - 2 * f)
        return dict(w=P["ARM_W"], h=P["ARM_H_FRONT"] + (P["ARM_H_BACK"] - P["ARM_H_FRONT"]) * (0.4 * f + 0.6 * sm),
                    lean=55.0, zi=250.0)
    g = (d - ARM_LEN) / CL
    if g <= 1.0:
        sm = g * g * (3 - 2 * g)
        return dict(w=P["ARM_W"] - (P["ARM_W"] - P["BACK_W"]) * sm, h=P["ARM_H_BACK"] + 20.0 * sm,
                    lean=55.0 + 20.0 * sm, zi=250.0 - 38.0 * sm)
    return dict(w=P["BACK_W"], h=P["BACK_H"], lean=75.0, zi=212.0)


def profile(sh, ext=False):
    """Open cross-section (u = outward from inner face, z = up). Starts at the inner/bottom,
    runs up the inner face, over the rounded rim, down the bulging outer face and tucks
    under the frame (where the fabric is stapled). ext=True closes the arm FRONT down to the floor."""
    w, h, lean, zi = sh["w"], sh["h"], sh["lean"], sh["zi"]
    rt, ro = 0.45 * w, 0.42 * w
    zt = h - rt
    pts = [(0.25 * w, ZB + 1.0), (0.05 * w, ZB + 12.0), (0.0, ZB + 50.0)] if ext else \
          [(0.0, zi - 15.0), (0.0, zi - 10.0), (0.0, zi - 5.0)]
    pts += [(0.0, zi), (0.0, zi + 0.4 * (zt - zi)), (0.0, zi + 0.75 * (zt - zi)), (0.0, zt)]
    i_inner_top = len(pts) - 1
    for a in (150, 120):
        pts.append((rt + rt * cos(radians(a)), zt + rt * sin(radians(a))))
    pts.append((rt, h)); i_top = len(pts) - 1
    cx, cz = w - ro, h - ro
    for a in (60, 30, 0):
        pts.append((cx + ro * cos(radians(a)), cz + ro * sin(radians(a))))
    i_ou = len(pts) - 1
    H = h - ZB
    pts.append((1.03 * w, ZB + 0.55 * H))
    pts.append((1.05 * w, ZB + 0.30 * H)); i_om = len(pts) - 1
    pts.append((1.03 * w, ZB + 0.12 * H)); i_ol = len(pts) - 1
    pts += [(0.93 * w, ZB + 8.0), (0.82 * w, ZB + 0.5), (0.62 * w, ZB + 1.0)]
    out = []
    for u, z in pts:
        fr = min(max((z - zi) / (h - zi), 0.0), 1.0)
        out.append((u + lean * fr * max(0.0, 1.0 - u / w), z))
    idx = dict(inner_bottom=3, inner_top=i_inner_top, top=i_top, outer_upper=i_ou,
               outer_mid=i_om, outer_low=i_ol, n=len(out))
    return out, idx


def offset_open(pts, d):
    """Offset an open polyline toward the shell interior (right-hand side) by d."""
    n = len(pts); segn = []
    for i in range(n - 1):
        (u0, z0), (u1, z1) = pts[i], pts[i + 1]
        du, dz = u1 - u0, z1 - z0; L = hypot(du, dz) or 1e-9
        segn.append((dz / L, -du / L))
    out = []
    for i, (u, z) in enumerate(pts):
        if i == 0:
            nn, k = segn[0], 1.0
        elif i == n - 1:
            nn, k = segn[-1], 1.0
        else:
            a, b = segn[i - 1], segn[i]
            sx, sz = a[0] + b[0], a[1] + b[1]; L = hypot(sx, sz) or 1e-9
            nn = (sx / L, sz / L); k = max(0.55, nn[0] * a[0] + nn[1] * a[1])
        out.append((u + nn[0] * d / k, z + nn[1] * d / k))
    return out


NOSE_LEN = 150.0   # rounded arm front (plan + side), superellipse fall-off
NOSE = []
for _dy in (-150.0, -149.3, -147.0, -143.0, -137.0, -128.0, -116.0, -101.0, -83.0, -62.0, -40.0, -18.0):
    _s = (1.0 - abs(_dy / NOSE_LEN) ** 2.0) ** 0.5          # circular fall-off -> continuous round front
    NOSE.append((_dy, max(0.12, _s)))


def make_station(s, nose_dy=0.0, scale=1.0, ext=None):
    x, y, nx, ny, tx, ty = path_point(s)
    d = min(s, TOTAL - s)
    if ext is None:
        ext = True   # inner face runs down to the frame everywhere (one uniform section -> no ridges)
    return dict(s=s, x=x, y=y, nx=nx, ny=ny, tx=tx, ty=ty, shape=shape_at(d),
                scale=scale, nose_dy=nose_dy, ext=ext)


def stations(step=24.0, nose=True):
    sts = []
    if nose:
        for dy, sc in NOSE:
            sts.append(make_station(0.0, dy, sc))
    n = int(TOTAL / step)
    for i in range(n + 1):
        sts.append(make_station(TOTAL * i / n))
    if nose:
        for dy, sc in reversed(NOSE):
            sts.append(make_station(TOTAL, dy, sc))
    return sts


def station_2d(st, d):
    base, idx = profile(st["shape"], st["ext"])
    pts = offset_open(base, d) if d else list(base)
    sc = st["scale"]
    if sc < 1.0:
        us = [p[0] for p in base]
        uc = 0.5 * (min(us) + max(us))                      # centre of section width
        za = ZB + 0.04 * (st["shape"]["h"] - ZB)            # nose rounds in plan; bottom stays down on the frame line
        su = 1.0 - (1.0 - sc) * 0.75
        sz_ = 1.0 - (1.0 - sc) * 0.40
        pts = [(uc + su * (u - uc), za + sz_ * (z - za)) for u, z in pts]
    return pts, idx


def to3d(st, u, z, d=0.0):
    y = st["y"]
    if st["nose_dy"]:
        y += st["nose_dy"] * (1.0 - min(d, 0.9 * NOSE_LEN) / NOSE_LEN)
    return Vector((st["x"] + st["nx"] * u, y + st["ny"] * u, z))


def station_pts(st, d):
    pts, idx = station_2d(st, d)
    return [to3d(st, u, z, d) for u, z in pts], idx


# ---------------------------------------------------------------------------
# 1. MAIN FRAME + REINFORCEMENTS + JOINTS
# ---------------------------------------------------------------------------
def build_frame():
    F, R, J = "01_MAIN_FRAME", "02_WOODEN_REINFORCEMENTS", "03_FRAME_JOINTS"
    px0, px1 = P["PANEL_X"]; sx0, sx1 = P["SIDE_RAIL_X"]
    fy0, fy1, fz0, fz1 = P["FRONT_RAIL"]; ry0, ry1, rz0, rz1 = P["REAR_RAIL"]
    # --- seat box ---
    box("FR_A_Front_Seat_Rail_Beech_38x120", -px0, px0, fy0, fy1, fz0, fz1, F, "MAT_Wood_Beech")
    box("FR_B_Rear_Seat_Rail_Beech_38x86", -px0, px0, ry0, ry1, rz0, rz1, F, "MAT_Wood_Beech")
    for sgn, side in ((-1, "L"), (1, "R")):
        a, b = sorted((sgn * sx0, sgn * sx1))
        box(f"FR_C_Side_Seat_Rail_{side}_Beech_38x120", a, b, -330.0, 248.0, 100.0, 220.0, F, "MAT_Wood_Beech")
    box("FR_D_Centre_Stretcher_Beech_32x70", -16, 16, fy1, ry0, 116.0, 186.0, F, "MAT_Wood_Beech")
    for sgn, side in ((-1, "L"), (1, "R")):
        box(f"FR_E_Lower_Cross_Member_{side}_Beech_32x50", sgn * 368 - 16, sgn * 368 + 16, fy1, ry0, 100.0, 150.0,
            F, "MAT_Wood_Beech")
    box("FR_H_Back_Base_Rail_Beech_38x90", -770, 770, 332.0, 370.0, 100.0, 190.0, F, "MAT_Wood_Beech")

    # --- inner arm panels (18 mm birch ply), top follows arm height ---
    for sgn, side in ((-1, "L"), (1, "R")):
        ys = [-330.0 + i * (248.0 + 330.0) / 16 for i in range(17)]
        top, shp = [], []
        for y in ys:
            d = min(max(y - Y_ARM0, 0.0), ARM_LEN)
            sh = shape_at(d)
            top.append(sh["h"] - 0.45 * sh["w"] - 70.0); shp.append(sh)
        poly_yz = [(ys[0], 100.0, shp[0])] + list(zip(ys, top, shp)) + [(ys[-1], 100.0, shp[-1])]
        n = len(poly_yz)

        def lean_x(z, sh):   # panel follows the outward-leaning inner face of the arm
            return sh["lean"] * min(max((z - sh["zi"]) / (sh["h"] - sh["zi"]), 0.0), 1.0)
        v = [(sgn * (px0 + lean_x(z, sh)), y, z) for y, z, sh in poly_yz] + \
            [(sgn * (px1 + lean_x(z, sh)), y, z) for y, z, sh in poly_yz]
        f = [tuple(reversed(range(n))), tuple(range(n, 2 * n))] + \
            [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
        ob = mesh_obj(f"FR_F_Inner_Arm_Panel_{side}_Birch_Ply_18", v, f, F, "MAT_Plywood_Birch", smooth=True)
        add_bevel(ob, 1.0); add_wn(ob)

    # --- shell ribs / formers (CNC 18 mm birch ply with lightening hole) ---
    rib_s = [("FR_G_Arm_Rib_Front", 20.0), ("FR_G_Arm_Rib_Mid", 280.0), ("FR_G_Arm_Rib_Rear", 530.0),
             ("FR_J_Corner_Former", ARM_LEN + CL / 2)]
    for xb in (420.0, 140.0):
        rib_s.append((f"FR_J_Back_Former_x{int(xb)}", ARM_LEN + CL + (BACK_HALF - xb)))
    for name, s in rib_s:
        for side, ss in (("L", s), ("R", TOTAL - s)):
            st = make_station(ss, ext=False)
            outer, _ = station_pts(st, 57.5)
            c = sum(outer, Vector()) / len(outer)
            inner = [c + 0.55 * (p - c) for p in outer]
            t = Vector((st["tx"], st["ty"], 0.0)).normalized() * 9.0
            n = len(outer)
            v = [p - t for p in outer] + [p - t for p in inner] + [p + t for p in outer] + [p + t for p in inner]
            f = []
            for j in range(n):
                k = (j + 1) % n
                f.append((j, k, n + k, n + j))                       # face A
                f.append((2 * n + j, 3 * n + j, 3 * n + k, 2 * n + k))  # face B
                f.append((j, 2 * n + j, 2 * n + k, k))               # outer edge
                f.append((n + j, n + k, 3 * n + k, 3 * n + j))       # inner edge
            ob = mesh_obj(f"{name}_{side}_Birch_Ply_18", v, f, F, "MAT_Plywood_Birch", smooth=False)
            add_bevel(ob, 1.0, 1, 50)

    # --- continuous shell stringers (laminated beech / stacked ply in corners) ---
    sts = [make_station(20.0, ext=False)] + [st for st in stations(nose=False) if 20.0 < st["s"] < TOTAL - 20.0] + \
          [make_station(TOTAL - 20.0, ext=False)]
    for key, label in (("top", "I_Top_Rail"), ("outer_upper", "K_Outer_Upper_Stringer"),
                       ("outer_mid", "K_Outer_Mid_Stringer"), ("outer_low", "K_Outer_Base_Stringer"),
                       ("inner_top", "K_Inner_Top_Stringer"), ("inner_bottom", "H_Inner_Lower_Rail")):
        rings = []
        for st in sts:
            pts, idx = station_2d(st, 57.5 + 16.0)
            u, z = pts[idx[key]]
            rings.append([to3d(st, u + du, z + dz) for du, dz in ((-14, -14), (14, -14), (14, 14), (-14, 14))])
        v, f = loft(rings, closed=True, cap_start=True, cap_end=True)
        ob = mesh_obj(f"FR_{label}_Beech_28x28_continuous", v, f, F, "MAT_Wood_Beech", smooth=False)
        add_bevel(ob, 1.0, 1, 50)

    # --- bending-ply outer skin (5 mm) over arms + back ---
    sts_skin = [st for st in stations(nose=False)]
    rings = []
    for st in sts_skin:
        pts, idx = station_2d(st, 55.0)
        rings.append([to3d(st, u, z) for u, z in pts[idx["top"]:]])
    v, f = loft(rings)
    ob = mesh_obj("RF_Bending_Ply_Outer_Skin_5mm", v, f, R, "MAT_Plywood_Bending", ex=(0, 0, 800))
    add_solidify(ob, 5.0); add_subsurf(ob, 1, 1)

    # --- corner blocks (glued + 2 screws each) ---
    for sgn, side in ((-1, "L"), (1, "R")):
        for yy, dirn, tag in ((fy1, 1, "Front"), (ry0, -1, "Rear")):
            poly = [(sgn * px0, yy), (sgn * (px0 - 60), yy), (sgn * px0, yy + dirn * 60)]
            if sgn * dirn < 0:
                poly = list(reversed(poly))
            prism(f"RF_L_Corner_Block_{tag}_{side}_Beech", poly, 110.0, 210.0, R, "MAT_Wood_Beech")
            for zz in (135.0, 185.0):
                cylinder(f"JN_Screw_CornerBlock_{tag}_{side}_z{int(zz)}",
                         (sgn * (px0 - 22), yy + dirn * 22, zz), 2.25, 50, 'X', J, "MAT_Steel_Zinc", 8)
        # stretcher blocks
    for yy, dirn, tag in ((fy1, 1, "Front"), (ry0, -1, "Rear")):
        for sgn, side in ((-1, "L"), (1, "R")):
            poly = [(sgn * 16, yy), (sgn * 56, yy), (sgn * 16, yy + dirn * 40)]
            if sgn * dirn < 0:
                poly = list(reversed(poly))
            prism(f"RF_N_Stretcher_Block_{tag}_{side}_Beech", poly, 120.0, 180.0, R, "MAT_Wood_Beech")

    # --- leg mounting blocks ---
    lf, lr = P["LEG_FRONT"], P["LEG_REAR"]
    for sgn, side in ((-1, "L"), (1, "R")):
        a, b = sorted((sgn * (lf[0] - 36), sgn * (lf[0] + 36)))
        box(f"RF_M_Leg_Block_Front_{side}_Beech_45", a, b, lf[1] - 42, lf[1] + 45, 100.0, 140.0, R, "MAT_Wood_Beech")
        a, b = sorted((sgn * (lr[0] - 38), sgn * (lr[0] + 38)))
        box(f"RF_M_Leg_Block_Rear_{side}_Beech_45", a, b, 252.0, 328.0, 100.0, 145.0, R, "MAT_Wood_Beech")
    box("RF_M_Centre_Support_Block_Beech", -45, 45, 150, 230, 100.0, 116.0, R, "MAT_Wood_Beech")  # under stretcher/rear-rail junction

    # --- joinery: dowels, M8 bolts + cross dowels, tenons ---
    for sgn, side in ((-1, "L"), (1, "R")):
        for rail, yc, zs, zb_ in (("Front", (fy0 + fy1) / 2, (130.0, 190.0), 160.0),
                                  ("Rear", (ry0 + ry1) / 2, (120.0, 165.0), 143.0)):
            for zz in zs:
                cylinder(f"JN_Dowel_10x40_{rail}Rail_{side}_z{int(zz)}", (sgn * (px0 - 8), yc, zz), 5.0, 40, 'X', J,
                         "MAT_Glue_Dowel", 12)
            cylinder(f"JN_Bolt_M8x100_{rail}Rail_{side}", (sgn * (sx1 - 50), yc, zb_), 4.0, 100, 'X', J,
                     "MAT_Steel_Zinc", 12)
            cylinder(f"JN_CrossDowel_M8_10x35_{rail}Rail_{side}", (sgn * (px0 - 32), yc, zb_), 5.0, 35, 'Z', J,
                     "MAT_Steel_Zinc", 12)
    box("JN_Tenon_Stretcher_Front_24x25x50", -12, 12, fy1 - 25, fy1, 126, 176, J, "MAT_Glue_Dowel", 0.5)
    box("JN_Tenon_Stretcher_Rear_24x25x50", -12, 12, ry0, ry0 + 25, 126, 166, J, "MAT_Glue_Dowel", 0.5)
    for sgn, side in ((-1, "L"), (1, "R")):
        for yy in (fy1 - 12, ry0 + 12):
            cylinder(f"JN_Tenon_CrossMember_{side}_y{int(yy)}", (sgn * 368, yy, 125), 6.0, 24, 'Y', J,
                     "MAT_Glue_Dowel", 12)


# ---------------------------------------------------------------------------
# 2. LEGS, GLIDES, HARDWARE
# ---------------------------------------------------------------------------
def build_legs():
    L_ = "04_LEGS_AND_GLIDES"
    lf, lr = P["LEG_FRONT"], P["LEG_REAR"]
    r = P["LEG_D"] / 2
    for (lx, ly), tag in ((lf, "Front"), (lr, "Rear")):
        for sgn, side in ((-1, "L"), (1, "R")):
            x = sgn * lx
            cylinder(f"LG_Leg_{tag}_{side}_Oak_D80x94", (x, ly, 5.0 + 47.0), r, 94.0, 'Z', L_,
                     "MAT_Wood_Oak_Legs", 48, bevel=6.0, ex=(0, 0, -320))
            cylinder(f"LG_Glide_{tag}_{side}_Felt_D64x5", (x, ly, 2.5), 32.0, 5.0, 'Z', L_,
                     "MAT_Glide_Felt", 32, bevel=1.0, ex=(0, 0, -400))
            cylinder(f"LG_HangerBolt_M8_{tag}_{side}", (x, ly, 94.0), 4.0, 48.0, 'Z', L_, "MAT_Steel_Zinc", 12,
                     ex=(0, 0, -200))
            cylinder(f"LG_Threaded_Insert_M8_{tag}_{side}", (x, ly, 108.0), 6.0, 16.0, 'Z', L_, "MAT_Steel_Zinc",
                     12, ex=(0, 0, 0))
    cylinder("LG_Centre_Support_Adjustable_D40", (0, 190, 1.0 + 49.0), 20.0, 98.0, 'Z', L_, "MAT_Plastic_Black",
             24, bevel=2.0, ex=(0, 0, -320))
    # dust cover (stapled to frame underside)
    pts = []
    rx, ry_f, ry_b, rr = 815.0, -380.0, 345.0, 150.0   # kept well inside the band / shell tuck lines
    for cx, cy, a0 in ((rx - rr, ry_b - rr, 0), (-rx + rr, ry_b - rr, 90), (-rx + rr, ry_f + rr, 180),
                       (rx - rr, ry_f + rr, 270)):
        for k in range(7):
            a = radians(a0 + 15 * k)
            pts.append((cx + rr * cos(a), cy + rr * sin(a)))
    prism("FD_Dust_Cover_Black_Nonwoven", pts, 99.0, 100.0, "13_FABRIC_DETAILS", "MAT_DustCover_Black", bevel=0,
          ex=(0, 0, -160))


# ---------------------------------------------------------------------------
# 3. SUSPENSION: sinuous springs, clips, helical ties
# ---------------------------------------------------------------------------
def spring_z(y):
    t = min(max((y - P["SPR_Y0"]) / (P["SPR_Y1"] - P["SPR_Y0"]), 0.0), 1.0)
    return P["SPR_Z0"] + (P["SPR_Z1"] - P["SPR_Z0"]) * t + 4 * P["SPR_CROWN"] * t * (1 - t)


SPRING_X = [-660 + i * (584 / 5) for i in range(6)]
SPRING_X = SPRING_X + [-x for x in reversed(SPRING_X)]


def build_springs():
    S, CLP = "05_SEAT_SUSPENSION", "06_SPRING_CLIPS"
    a, p = P["SPR_A"], P["SPR_PITCH"]
    y0, y1 = P["SPR_Y0"], P["SPR_Y1"]
    nb = int((y1 - y0) / p)
    for k, xc in enumerate(SPRING_X):
        pts2 = []
        for i in range(nb + 1):
            s = 1 if i % 2 == 0 else -1
            yi = y0 + i * p
            pts2.append((-s * a, yi)); pts2.append((s * a, yi))
            if i < nb:
                cy = yi + p / 2
                for kk in range(1, 8):
                    ph = radians(-90 + 180 * kk / 8)
                    pts2.append((s * a + s * (p / 2) * cos(ph), cy + (p / 2) * sin(ph)))
        last_x = pts2[-1][0]
        pts2.append((last_x, y1))
        pts3 = [(xc + x, y, spring_z(y)) for x, y in pts2]
        poly_curve(f"SP_Sinuous_Spring_{k + 1:02d}_8ga_4.1mm", [pts3], S, "MAT_Steel_Spring",
                   P["SPR_WIRE_R"], ex=(0, 0, 330), res=2)
        # clips: steel base + plastic anti-squeak liner + steel tab + 2 nails
        for yy, tag in ((y0, "Front"), (y1, "Rear")):
            zr = spring_z(yy) - 3.0   # rail top
            v, f, mi = [], [], []

            def add_box(x0_, x1_, ya, yb, za, zb2, m_i):
                base = len(v)
                for zz in (za, zb2):
                    v.extend([(x0_, ya, zz), (x1_, ya, zz), (x1_, yb, zz), (x0_, yb, zz)])
                for fc in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
                    f.append(tuple(base + q for q in fc)); mi.append(m_i)
            add_box(xc - 20, xc + 20, yy - 10, yy + 10, zr, zr + 1.2, 0)
            add_box(xc - 18, xc + 18, yy - 9, yy + 9, zr + 1.2, zr + 5.8, 1)
            add_box(xc - 20, xc + 20, yy - 10, yy + 10, zr + 5.8, zr + 7.0, 0)
            for nx_ in (-14, 14):
                add_box(xc + nx_ - 1.2, xc + nx_ + 1.2, yy - 1.2, yy + 1.2, zr - 25, zr + 7.2, 0)
            ob = mesh_obj(f"CL_Spring_Clip_{tag}_{k + 1:02d}", v, f, CLP, ["MAT_Steel_Zinc", "MAT_Plastic_Black"],
                          smooth=False, ex=(0, 0, 330))
            for poly_, m_i in zip(ob.data.polygons, mi):
                poly_.material_index = m_i
    # helical tie springs between adjacent springs (3 rows)
    splines = []
    half = a + p / 2
    for t in (0.25, 0.5, 0.75):
        yy = y0 + t * (y1 - y0)
        zz = spring_z(yy)
        for bay in (SPRING_X[:6], SPRING_X[6:]):
            for i in range(5):
                xa, xb = bay[i] + half, bay[i + 1] - half
                n = 140
                pts = []
                for j in range(n + 1):
                    u = j / n; ang = u * 2 * pi * 14
                    pts.append((xa + (xb - xa) * u, yy + 4.0 * cos(ang), zz + 4.0 * sin(ang)))
                splines.append(pts)
    poly_curve("SP_Helical_Tie_Springs_x30", splines, S, "MAT_Steel_Zinc", 0.8, ex=(0, 0, 330), res=1)


def deck_layer(name, z_off, thick, mat, coll, ex):
    xs = [-701 + i * 1402 / 24 for i in range(25)]
    ys = [-305 + i * (268 + 305) / 30 for i in range(31)]
    v = []
    for y in ys:
        zb_ = spring_z(min(y, P["SPR_Y1"])) + P["SPR_WIRE_R"] + z_off + thick / 2
        for x in xs:
            v.append((x, y, zb_))
    f = []
    nx = len(xs)
    for j in range(len(ys) - 1):
        for i in range(nx - 1):
            f.append((j * nx + i, j * nx + i + 1, (j + 1) * nx + i + 1, (j + 1) * nx + i))
    ob = mesh_obj(name, v, f, coll, mat, ex=ex)
    add_solidify(ob, thick)
    return ob


def build_deck():
    deck_layer("DK_Spring_Insulator_Felt_5mm", 0.0, 5.0, "MAT_Felt_Insulator", "05_SEAT_SUSPENSION", (0, 0, 430))
    deck_layer("DK_Deck_Foam_Pad_HR30_20mm", 5.0, 20.0, "MAT_Foam_HR30_Back", "07_SEAT_FOAM", (0, 0, 500))
    deck_layer("DK_Decking_Cloth_Nonwoven", 25.0, 1.5, "MAT_Decking_Grey", "13_FABRIC_DETAILS", (0, 0, 570))
    # front edge: foam strip + bullnose roll
    box("FM_Front_Edge_Strip_Firm_35", -697, 697, -410, -350, 112.0, 220.0, "07_SEAT_FOAM", "MAT_Foam_Firm_Shell",
        bevel=6.0, ex=(0, -150, 560))
    cylinder("FM_Front_Bullnose_Roll_Firm_35", (0, -395, 241), 19.0, 1394, 'X', "07_SEAT_FOAM",
             "MAT_Foam_Firm_Shell", 24, ex=(0, -150, 620))
    # upholstered front band (C-profile, open at the back, fabric stapled under the rail)
    prof = [(-290, 264), (-400, 264.5), (-419, 262.5), (-430, 255), (-435.5, 240), (-437, 195), (-434.5, 145),
            (-427, 115), (-414, 101), (-395, 97.5), (-345, 97.5)]
    rings = []
    for i in range(41):
        x = -760 + 1520 * i / 40   # ends run into the arm noses (hidden inside the arm cover)
        rings.append([(x, y, z) for y, z in prof])
    v, f = loft(rings, closed=True, cap_start=True, cap_end=True)
    ob = mesh_obj("UP_Front_Base_Band_Boucle", v, f, "11_UPHOLSTERY", "MAT_Boucle_Caramel", ex=(0, 0, 2600))
    add_subsurf(ob, 1, 2); add_solidify(ob, 2.5)


# ---------------------------------------------------------------------------
# 4. SHELL LAYERS (arm + back padding and covering)
# ---------------------------------------------------------------------------
def shell_layer(name, d_mid, thick, coll, mat, ex, closed=False):
    sts = stations()
    rings = [station_pts(st, d_mid)[0] for st in sts]
    v, f = loft(rings, closed=closed, cap_start=True, cap_end=True)
    ob = mesh_obj(name, v, f, coll, mat, ex=ex)
    add_subsurf(ob, 1, 2)
    add_solidify(ob, thick)
    return ob


def build_shell():
    shell_layer("UP_Shell_Cover_Boucle_Arms_Back", 1.25, 2.5, "11_UPHOLSTERY", "MAT_Boucle_Caramel", (0, 0, 2600), closed=True)
    shell_layer("FB_Shell_Polyester_Wadding_150gsm", 6.5, 7.5, "09_ARMREST_FOAM", "MAT_Fibre_Polyester", (0, 0, 2150))
    shell_layer("FM_Shell_Soft_Foam_HR30_22mm", 21.5, 22.0, "09_ARMREST_FOAM", "MAT_Foam_Soft_Shell", (0, 0, 1700))
    shell_layer("FM_Shell_Firm_Foam_HR35_20mm", 42.5, 20.0, "09_ARMREST_FOAM", "MAT_Foam_Firm_Shell", (0, 0, 1250))
    # back suspension: 50 mm elastic webbing on the back formers
    st = make_station(ARM_LEN + CL + BACK_HALF, ext=False)
    pts, idx = station_2d(st, 60.0)
    line = pts[idx["inner_bottom"]:idx["inner_top"] + 1]
    straps = []
    for x in (-560, -470, -330, -235, -45, 45, 235, 330, 470, 560):
        straps.append(x)
    v, f = [], []
    for x in straps:
        base = len(v)
        for u, z in line:
            y = Y_BACK_IN + u
            v += [(x - 25, y, z), (x + 25, y, z)]
        for i in range(len(line) - 1):
            f.append((base + 2 * i, base + 2 * i + 1, base + 2 * i + 3, base + 2 * i + 2))
    for zz in (380.0, 600.0):
        # horizontal straps behind the verticals
        u_at = None
        for (u0, z0), (u1, z1) in zip(line[:-1], line[1:]):
            if z0 <= zz <= z1:
                u_at = u0 + (u1 - u0) * (zz - z0) / (z1 - z0)
        u_at = (u_at or 60.0) + 2.0
        base = len(v)
        v += [(-600, Y_BACK_IN + u_at, zz - 25), (600, Y_BACK_IN + u_at, zz - 25),
              (600, Y_BACK_IN + u_at, zz + 25), (-600, Y_BACK_IN + u_at, zz + 25)]
        f.append((base, base + 1, base + 2, base + 3))
    ob = mesh_obj("SP_Back_Elastic_Webbing_50mm", v, f, "05_SEAT_SUSPENSION", "MAT_Plastic_Black", ex=(0, 200, 330))
    add_solidify(ob, 1.5)


# ---------------------------------------------------------------------------
# 5. CUSHIONS (layered)
# ---------------------------------------------------------------------------
def lattice_surface(X, Y, Z):
    """Quad surface of a box lattice with explicit (non-uniform) loop positions.
    Loops placed close to the borders act as subdivision 'support loops' -> controlled soft radii."""
    vid, verts, faces = {}, [], []

    def v(i, j, k):
        key = (i, j, k)
        if key not in vid:
            vid[key] = len(verts); verts.append((X[i], Y[j], Z[k]))
        return vid[key]
    nx, ny, nz = len(X) - 1, len(Y) - 1, len(Z) - 1
    for i in range(nx):
        for j in range(ny):
            faces.append((v(i, j, 0), v(i, j + 1, 0), v(i + 1, j + 1, 0), v(i + 1, j, 0)))
            faces.append((v(i, j, nz), v(i + 1, j, nz), v(i + 1, j + 1, nz), v(i, j + 1, nz)))
    for j in range(ny):
        for k in range(nz):
            faces.append((v(0, j, k), v(0, j, k + 1), v(0, j + 1, k + 1), v(0, j + 1, k)))
            faces.append((v(nx, j, k), v(nx, j + 1, k), v(nx, j + 1, k + 1), v(nx, j, k + 1)))
    for i in range(nx):
        for k in range(nz):
            faces.append((v(i, 0, k), v(i + 1, 0, k), v(i + 1, 0, k + 1), v(i, 0, k + 1)))
            faces.append((v(i, ny, k), v(i, ny, k + 1), v(i + 1, ny, k + 1), v(i + 1, ny, k)))
    return verts, faces


def _loops(size, r, inner=(-0.3, -0.1, 0.1, 0.3)):
    a = min(r / size, 0.18)
    return [-0.5, -0.5 + a] + [p for p in inner if -0.5 + a < p < 0.5 - a] + [0.5 - a, 0.5]


def soft_box_geom(sx, sy, sz, crown=0.0, bulge=0.0, r=55.0):
    X = _loops(sx, r)
    Y = _loops(sy, r, (-0.25, 0.0, 0.25))
    a_b, a_t = min(0.65 * r / sz, 0.2), min(r / sz, 0.3)
    Z = [-0.5, -0.5 + a_b, 0.0, 0.5 - a_t, 0.5] if a_t < 0.45 else [-0.5, 0.5]
    vv, f = lattice_surface(X, Y, Z)
    v = []
    for x, y, z in vv:
        nx_, ny_, nz_ = 2 * x, 2 * y, 2 * z
        Xo, Yo, Zo = x * sx, y * sy, z * sz
        Zo += crown * (1 - nx_ * nx_) * (1 - ny_ * ny_) * max(nz_, 0)          # domed top
        Zo -= 0.3 * crown * (1 - nx_ * nx_) * (1 - ny_ * ny_) * max(-nz_, 0)   # slight belly under
        Xo += bulge * nx_ * (1 - nz_ * nz_) * (1 - 0.6 * ny_ * ny_)            # side panels billow
        Yo += bulge * ny_ * (1 - nz_ * nz_) * (1 - 0.6 * nx_ * nx_)
        v.append((Xo, Yo, Zo))
    return v, f


def soft_box(name, size, coll, mat, loc, rot_x, crown, bulge, radius, shell=None, ex=(0, 0, 0)):
    v, f = soft_box_geom(*size, crown=crown, bulge=bulge, r=radius)
    ob = mesh_obj(name, v, f, coll, mat, ex=ex, loc=loc)
    ob.rotation_euler = (radians(rot_x), 0, 0)
    add_subsurf(ob, 2, 3)
    if shell:
        add_solidify(ob, shell, offset=-1.0)   # thickness grows inward from the nominal surface
    return ob


def back_cushion_geom(sx, tb, tt, sz, lumbar, inset=0.0):
    """Pillow-style back cushion: local origin at bottom-front centre, +Y = backwards, +Z = up."""
    X = _loops(sx, 55.0)
    Yn = [0.0, 0.2, 0.5, 0.8, 1.0]
    Zn = [0.0, 0.07, 0.25, 0.45, 0.65, 0.82, 0.92, 1.0]
    vv, f = lattice_surface(X, Yn, Zn)
    v = []
    for x, yf, zf in vv:
        nx_ = 2 * x
        Z = inset + zf * (sz - 2 * inset)
        t = (tb + (tt - tb) * zf) - 2 * inset
        t *= 1.0 + 0.10 * sin(pi * zf) * (1 - nx_ * nx_)                 # plump middle
        Y = inset + yf * t
        Y -= lumbar * exp(-((zf - 0.35) / 0.2) ** 2) * (1 - yf) * (1 - nx_ * nx_)
        Z += 14.0 * (1 - nx_ * nx_) * (1 - abs(2 * yf - 1)) * (zf ** 6)  # domed top edge
        X = x * (sx - 2 * inset) * (1.0 + 0.012 * sin(pi * zf))
        v.append((X, Y, Z))
    return v, f


def build_cushions():
    sx, sy, sz = P["SEAT_CUSH"]
    yfront, yrear = P["SEAT_CUSH_Y"]
    rake = P["SEAT_RAKE_DEG"]
    yc = (yfront + yrear) / 2
    zc = P["SEAT_FRONT_BOTTOM_Z"] - (yc - yfront) * math.tan(radians(rake)) + sz / 2
    for sgn, side in ((-1, "L"), (1, "R")):
        loc = (sgn * (sx / 2 + 2), yc, zc)
        exy = 0
        soft_box(f"CU_Seat_{side}_Cover_Boucle", (sx, sy, sz), "11_UPHOLSTERY", "MAT_Boucle_Caramel", loc, -rake,
                 18, 12, 72, 2.0, ex=(0, -900, 0))
        soft_box(f"CU_Seat_{side}_Ticking_Cotton", (sx - 4, sy - 4, sz - 4), "10_CUSHION_TICKING",
                 "MAT_Ticking_Cotton", loc, -rake, 17, 11, 70, 0.8, ex=(0, -1400, 0))
        soft_box(f"CU_Seat_{side}_Fibre_Wrap_200gsm", (sx - 6, sy - 6, sz - 6), "10_CUSHION_TICKING",
                 "MAT_Fibre_Polyester", loc, -rake, 16, 10, 68, 15.0, ex=(0, -1900, 0))
        # foam stack inside fibre: 114 mm HR40 core + 25 mm HR35 comfort top
        fx, fy = sx - 36, sy - 36
        core_h, top_h = 114.0, 25.0
        zb_local = -(sz - 36) / 2
        ca, sa = cos(radians(-rake)), sin(radians(-rake))

        def lloc(zl):
            return (loc[0], loc[1] - zl * sa, loc[2] + zl * ca)
        soft_box(f"CU_Seat_{side}_Core_HR40_114mm", (fx, fy, core_h), "07_SEAT_FOAM", "MAT_Foam_HR40_Core",
                 lloc(zb_local + core_h / 2), -rake, 0, 0, 12, ex=(0, -2400, 0))
        soft_box(f"CU_Seat_{side}_Comfort_HR35_25mm", (fx, fy, top_h), "07_SEAT_FOAM", "MAT_Foam_HR35_Comfort",
                 lloc(zb_local + core_h + top_h / 2), -rake, 6, 0, 8, ex=(0, -2400, 220))
        # side seam + rear zipper (follow the cover)
        r = 70.0; hx, hy = sx / 2 + 2.0, sy / 2 + 2.0   # seam sits in the billowed side, hidden in the pile
        pts = []
        for cx, cy, a0 in ((hx - r, hy - r, 0), (-hx + r, hy - r, 90), (-hx + r, -hy + r, 180), (hx - r, -hy + r, 270)):
            for k in range(7):
                a = radians(a0 + 15 * k)
                pts.append((cx + r * cos(a), cy + r * sin(a), 0.0))
        sm = poly_curve(f"ST_Seat_{side}_Side_Seam", [pts], "12_STITCHING_AND_SEAMS", "MAT_Thread_Seam", 0.9,
                        cyclic=True, ex=(0, -900, 0))
        sm.location = loc; sm.rotation_euler = (radians(-rake), 0, 0)
        zp = box(f"ST_Seat_{side}_Rear_Zipper_560", -280, 280, -2, 2, -5, 5, "12_STITCHING_AND_SEAMS", "MAT_Zipper",
                 bevel=0.8, ex=(0, -900, 0))
        zp.location = (loc[0], loc[1] + sy / 2 + 4.0, loc[2] - 25)
        zp.rotation_euler = (radians(-rake), 0, 0)

    # back cushions
    bw, tb, tt, bh = P["BACK_CUSH"]
    by, bz = P["BACK_CUSH_ORIGIN"]
    tilt = -P["BACK_TILT_DEG"]
    for sgn, side in ((-1, "L"), (1, "R")):
        loc = (sgn * (bw / 2 + 2), by, bz)
        exy, exz = -600, 150
        for nm, ins, coll, mat, shell, lum, dz in (
                ("Cover_Boucle", 0.0, "11_UPHOLSTERY", "MAT_Boucle_Caramel", 2.0, 20.0, 0),
                ("Ticking_Compartment", 2.0, "10_CUSHION_TICKING", "MAT_Ticking_Cotton", 0.8, 19.0, -300),
                ("Fibre_Hollow_Siliconised", 3.0, "10_CUSHION_TICKING", "MAT_Fibre_Polyester", 22.0, 18.0, -600),
                ("Core_HR30_Soft", 25.0, "08_BACK_FOAM", "MAT_Foam_HR30_Back", None, 12.0, -900)):
            v, f = back_cushion_geom(bw, tb, tt, bh, lum, ins)
            ob = mesh_obj(f"CU_Back_{side}_{nm}", v, f, coll, mat, loc=loc, ex=(2300, exy + dz, exz))
            ob.rotation_euler = (radians(tilt), 0, 0)
            add_subsurf(ob, 2, 3)
            if shell:
                add_solidify(ob, shell, offset=-1.0)


# ---------------------------------------------------------------------------
# 6. SEAMS ON THE SHELL
# ---------------------------------------------------------------------------
def build_shell_seams():
    sts = [st for st in stations(nose=False) if 60.0 < st["s"] < TOTAL - 60.0]
    rim = []
    for st in sts:
        pts, idx = station_2d(st, 0.0)
        u, z = pts[idx["outer_upper"]]
        rim.append(tuple(to3d(st, u - 4.0, z)))   # hidden in the pile
    rs = poly_curve("ST_Shell_Rim_Seam_Continuous", [rim], "12_STITCHING_AND_SEAMS", "MAT_Thread_Seam", 1.6,
                    ex=(0, 0, 2600))
    rs.hide_render = True   # seam line kept for documentation; sunk in the pile, not rendered
    for s, side in ():   # front-panel seam loop disabled (caused surface slivers)
        st = make_station(s, -30.0, 0.95)
        pts, _ = station_pts(st, -1.5)
        poly_curve(f"ST_Arm_Front_Panel_Seam_{side}", [[tuple(p) for p in pts]], "12_STITCHING_AND_SEAMS",
                   "MAT_Thread_Seam", 1.6, cyclic=True, ex=(0, 0, 2600))


# ---------------------------------------------------------------------------
# 7. ENGINEERING HELPERS + DIMENSIONS + LABELS
# ---------------------------------------------------------------------------
def arrow(name, tip, direction, length, coll, mat, r=8.0):
    d = Vector(direction).normalized()
    tipv = Vector(tip)
    start = tipv - d * length
    shaft_end = tipv - d * (r * 4)
    poly_curve(name + "_Shaft", [[tuple(start), tuple(shaft_end)]], coll, mat, r * 0.5)
    # cone
    segs = 16
    ax = d
    up = Vector((0, 0, 1)) if abs(ax.z) < 0.9 else Vector((1, 0, 0))
    u = ax.cross(up).normalized(); w = ax.cross(u).normalized()
    v = [tuple(tipv)] + [tuple(shaft_end + (u * cos(2 * pi * i / segs) + w * sin(2 * pi * i / segs)) * r * 1.6)
                         for i in range(segs)]
    f = [(0, 1 + i, 1 + (i + 1) % segs) for i in range(segs)] + [tuple(range(segs, 0, -1))]
    mesh_obj(name + "_Head", v, f, coll, mat, smooth=False)


def build_helpers():
    H = "17_ENGINEERING_HELPERS"
    for sgn, side in ((-1, "L"), (1, "R")):
        arrow(f"EH_Load_Seat_{side}_1300N", (sgn * 360, -150, 450), (0, 0, -1), 350, H, "MAT_Helper_Red", 10)
        arrow(f"EH_Load_Arm_{side}_750N", (sgn * 830, -200, 700), (0, 0, -1), 250, H, "MAT_Helper_Red", 8)
        arrow(f"EH_Load_Arm_Sideways_{side}_400N", (sgn * 960, -200, 600), (sgn, 0, 0), 250, H, "MAT_Helper_Red", 8)
        arrow(f"EH_Load_Back_{side}_450N", (sgn * 360, 330, 650), (0, 1, 0), 300, H, "MAT_Helper_Red", 8)
        for (lx, ly), tag in ((P["LEG_FRONT"], "F"), (P["LEG_REAR"], "R")):
            arrow(f"EH_Reaction_Leg_{tag}{side}", (sgn * lx, ly, 0), (0, 0, 1), 250, H, "MAT_Helper_Green", 7)
    # centre of mass marker (estimated, empty sofa)
    me = bpy.data.meshes.new("EH_CoG_Estimated")
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=25); bm.to_mesh(me); bm.free()
    me.materials.append(MATS["MAT_Helper_Red"])
    ob = bpy.data.objects.new("EH_CoG_Estimated_Empty_Sofa", me); ob.location = (0, 40, 330)
    link(ob, H)
    # cutter boxes used by render_views.py for sections (never rendered themselves)
    for name, b in (("EH_CUTTER_Right_Half_x250", (250, 1300, -1300, 1300, -50, 1200)),
                    ("EH_CUTTER_Seat_Section_x360", (360, 1300, -1300, 1300, -50, 1200)),
                    ("EH_CUTTER_Arm_Section_y-120", (-1300, -500, -1300, -120, -50, 1200))):
        ob = box(name, *b, H, "MAT_Helper_Red", bevel=0)
        ob.display_type = 'WIRE'; ob.hide_render = True


def text(name, body, loc, rot, size, coll, ex=None):
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = body; cu.size = size; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
    cu.materials.append(MATS["MAT_Dim_Black"])
    ob = bpy.data.objects.new(name, cu)
    ob.location = loc; ob.rotation_euler = [radians(a) for a in rot]
    return link(ob, coll, ex or (0, 0, 0))


def dim(name, p1, p2, tick_dir, label, coll, text_rot, text_off, size=34):
    p1, p2, td = Vector(p1), Vector(p2), Vector(tick_dir).normalized() * 18
    poly_curve(name, [[tuple(p1), tuple(p2)], [tuple(p1 - td), tuple(p1 + td)], [tuple(p2 - td), tuple(p2 + td)]],
               coll, "MAT_Dim_Black", 1.6, res=0)
    text(name + "_Text", label, tuple((p1 + p2) / 2 + Vector(text_off)), text_rot, size, coll)


def build_dimensions():
    Fr, Si, To = "18a_DIM_FRONT", "18b_DIM_SIDE", "18c_DIM_TOP"
    y = -700; fr = (90, 0, 0)
    dim("DIM_F_Overall_Width", (-950, y, -70), (950, y, -70), (0, 0, 1), "1900", Fr, fr, (0, 0, -45))
    dim("DIM_F_Clear_Seat_Width", (-705, y, 880), (705, y, 880), (0, 0, 1), "1410 between arms", Fr, fr, (0, 0, 40))
    dim("DIM_F_Overall_Height", (-1060, y, 0), (-1060, y, 780), (1, 0, 0), "780", Fr, fr, (-75, 0, 0))
    dim("DIM_F_Arm_Height_Front", (1060, y, 0), (1060, y, 640), (1, 0, 0), "640 arm", Fr, fr, (95, 0, 0))
    dim("DIM_F_Seat_Height", (1330, y, 0), (1330, y, 444), (1, 0, 0), "445 seat", Fr, fr, (95, 0, 0))
    dim("DIM_F_Arm_Width", (-950, y, 820), (-705, y, 820), (0, 0, 1), "245", Fr, fr, (0, 0, 40))
    dim("DIM_F_Leg_Height", (-1170, y, 0), (-1170, y, 100), (1, 0, 0), "100 leg", Fr, fr, (-95, 0, 0))
    x = -1150; sr = (90, 0, -90)
    dim("DIM_S_Overall_Depth", (x, -450, -70), (x, 450, -70), (0, 0, 1), "900", Si, sr, (0, 0, -45))
    dim("DIM_S_Seat_Depth_Effective", (x, -425, 500), (x, 105, 500), (0, 0, 1), "~530 effective seat depth", Si, sr,
        (0, 0, 40))
    dim("DIM_S_Back_Height", (x, 560, 0), (x, 560, 780), (0, 1, 0), "780", Si, sr, (0, 75, 0))
    dim("DIM_S_Seat_Height", (x, -560, 0), (x, -560, 444), (0, 1, 0), "445 seat", Si, sr, (0, -100, 120))
    dim("DIM_S_Deck_Height", (x, -800, 0), (x, -800, 264), (0, 1, 0), "264 deck", Si, sr, (0, -105, 0))
    z = 1000
    dim("DIM_T_Overall_Width", (-950, -620, z), (950, -620, z), (0, 1, 0), "1900", To, (0, 0, 0), (0, -45, 0))
    dim("DIM_T_Overall_Depth", (1080, -450, z), (1080, 450, z), (1, 0, 0), "900", To, (0, 0, 90), (45, 0, 0))
    dim("DIM_T_Cushion_Width", (2, -560, z), (703, -560, z), (0, 1, 0), "701 cushion", To, (0, 0, 0), (0, -40, 0))
    dim("DIM_T_Leg_Centres_X", (-870, -760, z), (870, -760, z), (0, 1, 0), "1740 front leg c/c", To, (0, 0, 0),
        (0, -40, 0))


# (number, text, unused, label position in mm - valid for explode = 1)
EXPLODE_LABELS = [
    (1, "Wooden frame", None, (-1350, 0, 380)),
    (2, "Bending-ply skin, blocks", None, (-1350, 0, 1250)),
    (3, "Joinery (dowels, M8 bolts)", None, (-1350, 0, 120)),
    (4, "Legs, glides, centre foot", None, (-1350, 0, -260)),
    (5, "Spring clips + liners", None, (-1350, 0, 560)),
    (6, "Sinuous springs x12", None, (-1350, 0, 700)),
    (7, "Felt / deck foam / decking", None, (-1350, 0, 860)),
    (8, "Seat row 4: HR40 core + HR35 comfort", None, (1600, -1700, 80)),
    (9, "Back cushion layers (HR30 core)", None, (2000, -1300, 1350)),
    (10, "Shell foam firm + soft", None, (-1350, 0, 1900)),
    (11, "Seat row 3: polyester fibre wrap", None, (1600, -1700, 210)),
    (12, "Seat row 2: cotton ticking", None, (1600, -1700, 340)),
    (13, "Bouclé upholstery", None, (-1350, 0, 3050)),
    (14, "Seat row 1: bouclé covers, seams, zips", None, (1600, -1700, 470)),
    (15, "Dust cover", None, (-1350, 0, -110)),
]


def build_labels():
    for n, txt, _, pos in EXPLODE_LABELS:
        ob = text(f"LBL_{n:02d}", f"{n}  {txt}", (pos[0], pos[1], pos[2]), (72, 0, -35), 85, "18d_EXPLODE_LABELS",
                  ex=(0, 0, 0))
        ob.data.align_x = 'RIGHT' if pos[0] < 0 else ('CENTER' if n == 9 else 'LEFT')
        EX[ob.name] = (0, 0, 0)
        ob.hide_render = False


# ---------------------------------------------------------------------------
# 8. ENVIRONMENT, LIGHTS, CAMERAS (metres, not parented to SOFA_ROOT)
# ---------------------------------------------------------------------------
def env_box(name, x0, x1, y0, y1, z0, z1, mat, bevel=0.0):
    cx, cy, cz = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
    hx, hy, hz = (x1 - x0) / 2, (y1 - y0) / 2, (z1 - z0) / 2
    v = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
         (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me = bpy.data.meshes.new(name); me.from_pydata(v, [], f); me.materials.append(MATS[mat])
    ob = bpy.data.objects.new(name, me); ob.location = (cx, cy, cz)
    C["19_ENVIRONMENT"].objects.link(ob)
    if bevel:
        md = ob.modifiers.new("Bevel", 'BEVEL'); md.width = bevel; md.segments = 3
    return ob


def env_cyl(name, cx, cy, z0, z1, r, mat, segs=64):
    v, f = [], []
    for z in (z0, z1):
        for i in range(segs):
            a = 2 * pi * i / segs; v.append((cx + r * cos(a), cy + r * sin(a), z))
    for i in range(segs):
        j = (i + 1) % segs; f.append((i, j, segs + j, segs + i))
    f += [tuple(reversed(range(segs))), tuple(range(segs, 2 * segs))]
    me = bpy.data.meshes.new(name); me.from_pydata(v, [], f); me.materials.append(MATS[mat])
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me); C["19_ENVIRONMENT"].objects.link(ob)
    md = ob.modifiers.new("Bevel", 'BEVEL'); md.width = 0.01; md.segments = 3
    md.limit_method = 'ANGLE'
    return ob


def build_environment():
    env_box("ENV_Floor_Oak", -6, 6, -6, 4, -0.02, 0.0, "MAT_Env_Floor_Oak")
    env_box("ENV_Wall_Back", -6, 6, 1.25, 1.35, 0, 3.2, "MAT_Env_Wall")
    env_box("ENV_Wall_Left", -3.6, -3.5, -6, 1.35, 0, 3.2, "MAT_Env_Wall")
    env_box("ENV_Skirting_Back", -6, 6, 1.22, 1.25, 0, 0.12, "MAT_Env_Wall")
    env_box("ENV_Rug", -1.3, 1.5, -2.6, -0.25, 0.0, 0.008, "MAT_Env_Rug", 0.003)
    env_cyl("ENV_Coffee_Table_Top", 1.05, -1.55, 0.36, 0.40, 0.42, "MAT_Env_Stone")
    env_cyl("ENV_Coffee_Table_Base", 1.05, -1.55, 0.0, 0.36, 0.26, "MAT_Env_Stone")
    env_box("ENV_Sideboard", -3.3, -1.75, 0.80, 1.22, 0.0, 0.78, "MAT_Env_Cabinet", 0.01)
    env_box("ENV_Art_Frame", -2.9, -2.1, 1.20, 1.22, 0.78, 1.85, "MAT_Env_Cabinet")
    env_box("ENV_Art_Canvas", -2.86, -2.14, 1.195, 1.20, 0.82, 1.81, "MAT_Env_Canvas")
    env_cyl("ENV_Planter", 2.1, 0.95, 0.0, 0.55, 0.22, "MAT_Env_Cabinet")

    # world
    w = bpy.data.worlds.new("World_Interior")
    bpy.context.scene.world = w
    try:
        w.use_nodes = True
    except Exception:
        pass
    nt = w.node_tree
    bg = nt.nodes.get("Background") or nt.nodes.new("ShaderNodeBackground")
    out = nt.nodes.get("World Output") or nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(bg.outputs[0], out.inputs[0])
    bg.inputs["Color"].default_value = (0.80, 0.84, 0.92, 1); bg.inputs["Strength"].default_value = 0.35
    w.color = (1, 1, 1)

    Lc = C["15_LIGHTING"]
    sun = bpy.data.lights.new("LT_Sun_Daylight", 'SUN'); sun.energy = 2.4; sun.angle = radians(3)
    sun.color = (1.0, 0.95, 0.88)
    ob = bpy.data.objects.new("LT_Sun_Daylight", sun); ob.rotation_euler = (radians(52), 0, radians(38))
    Lc.objects.link(ob)
    win = bpy.data.lights.new("LT_Window_Area", 'AREA'); win.energy = 450; win.size = 2.5; win.shape = 'RECTANGLE'
    win.size_y = 2.0; win.color = (0.95, 0.97, 1.0)
    ob = bpy.data.objects.new("LT_Window_Area", win); ob.location = (3.2, -0.6, 1.5)
    ob.rotation_euler = (0, radians(90), 0); Lc.objects.link(ob)
    fill = bpy.data.lights.new("LT_Fill_Front", 'AREA'); fill.energy = 120; fill.size = 2.0
    ob = bpy.data.objects.new("LT_Fill_Front", fill); ob.location = (-1.0, -3.6, 1.8)
    ob.rotation_euler = (radians(65), 0, radians(-15)); Lc.objects.link(ob)


def add_cam(name, loc, target, lens=50.0, ortho=None):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens; cd.clip_start = 0.02; cd.clip_end = 200
    cd.sensor_width = 36
    if ortho:
        cd.type = 'ORTHO'; cd.ortho_scale = ortho
    ob = bpy.data.objects.new(name, cd)
    ob.location = loc
    d = Vector(target) - Vector(loc)
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    C["16_CAMERA"].objects.link(ob)
    return ob


def build_cameras():
    hero = add_cam("CAM_01_Hero_ThreeQuarter", (-1.85, -2.55, 1.05), (0.12, 0.0, 0.40), 40)
    add_cam("CAM_02_Front", (0, -4.6, 0.45), (0, 0, 0.40), 50)
    add_cam("CAM_03_Side", (-4.4, -0.05, 0.45), (0, -0.05, 0.40), 50)
    add_cam("CAM_04_Rear", (1.1, 3.9, 1.0), (0, 0, 0.38), 45)
    add_cam("CAM_05_Fabric_Closeup", (-1.10, -1.30, 0.88), (-0.62, -0.38, 0.47), 55)
    add_cam("CAM_06_Cushion_Construction", (1.25, -1.05, 0.78), (0.27, -0.12, 0.33), 50)
    add_cam("CAM_07_Exposed_Frame", (-2.05, -2.75, 1.45), (0.0, 0.0, 0.30), 45)
    add_cam("CAM_08_Spring_Closeup", (-0.15, -1.15, 0.95), (0.30, -0.05, 0.20), 50)
    add_cam("CAM_09_Exploded", (-5.6, -9.6, 4.3), (0.85, -1.1, 1.05), 38)
    add_cam("CAM_10_Cutaway", (2.25, -2.6, 1.35), (0.05, 0.0, 0.33), 45)
    add_cam("CAM_11_Arm_Section", (-1.25, -1.55, 0.85), (-0.82, -0.12, 0.42), 50)
    # orthographic drawing cameras
    add_cam("DRW_A_Front", (0.08, -5, 0.40), (0.08, 0, 0.40), ortho=3.1)
    add_cam("DRW_B_Side", (-5, -0.12, 0.40), (0, -0.12, 0.40), ortho=2.15)
    add_cam("DRW_C_Rear", (0, 5, 0.40), (0, 0, 0.40), ortho=2.6)
    add_cam("DRW_D_Top", (0, -0.05, 6), (0, -0.05, 0), ortho=2.7)
    add_cam("DRW_E_Bottom", (0, 0, -5), (0, 0, 0.5), ortho=2.4)
    add_cam("DRW_H_Seat_Section", (5, 0, 0.40), (0, 0, 0.40), ortho=1.3)
    add_cam("DRW_I_Arm_Section", (-0.83, -5, 0.40), (-0.83, 0, 0.40), ortho=0.85)
    bpy.context.scene.camera = hero


# ---------------------------------------------------------------------------
# 9. REFERENCE IMAGE, EXPLODE DRIVERS, UVs, RENDER DEFAULTS
# ---------------------------------------------------------------------------
def build_reference():
    if not os.path.exists(REF_IMG):
        return
    img = bpy.data.images.load(REF_IMG)
    ob = bpy.data.objects.new("REF_Upholstered_Photo", None)
    ob.empty_display_type = 'IMAGE'; ob.data = img; ob.empty_display_size = 1.6
    ob.location = (0, 1.6, 0.9); ob.rotation_euler = (radians(90), 0, 0)
    C["00_REFERENCE_IMAGES"].objects.link(ob)
    ob.hide_render = True


def add_explode_drivers():
    for name, off in EX.items():
        ob = bpy.data.objects.get(name)
        if ob is None or not any(off):
            continue
        for i in range(3):
            if abs(off[i]) < 1e-6:
                continue
            fc = ob.driver_add("location", i)
            drv = fc.driver
            drv.type = 'SCRIPTED'
            var = drv.variables.new(); var.name = "e"; var.type = 'SINGLE_PROP'
            var.targets[0].id_type = 'OBJECT'; var.targets[0].id = ROOT
            var.targets[0].data_path = '["explode"]'
            drv.expression = f"{ob.location[i]:.3f} + e*{off[i]:.1f}"


def uv_upholstery():
    vl = bpy.context.view_layer
    for ob in list(C["11_UPHOLSTERY"].objects):
        if ob.type != 'MESH':
            continue
        try:
            for o in vl.objects:
                o.select_set(False)
            vl.objects.active = ob; ob.select_set(True)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.smart_project(angle_limit=radians(60), island_margin=0.01)
            bpy.ops.object.mode_set(mode='OBJECT')
        except Exception as e:
            print("UV skipped for", ob.name, e)
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except Exception:
                pass


def render_defaults():
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 96
    try:
        sc.cycles.use_denoising = True
    except Exception:
        pass
    sc.render.resolution_x, sc.render.resolution_y = 1600, 1067
    sc.render.resolution_percentage = 100
    try:
        sc.view_settings.view_transform = 'AgX'
        sc.view_settings.look = 'AgX - Medium High Contrast'
        sc.view_settings.exposure = -0.4
    except Exception:
        pass
    for n in ("17_ENGINEERING_HELPERS", "18_DIMENSIONS_AND_LABELS", "00_REFERENCE_IMAGES"):
        C[n].hide_render = True
    C["17_ENGINEERING_HELPERS"].hide_viewport = False


def dump_components():
    rows = []
    for cname in COLL_NAMES[1:14]:
        for ob in C[cname].all_objects:
            if ob.type not in ('MESH', 'CURVE'):
                continue
            d = ob.dimensions
            mat = ob.material_slots[0].material.name if ob.material_slots and ob.material_slots[0].material else ""
            rows.append((cname, ob.name, mat, round(d.x, 1), round(d.y, 1), round(d.z, 1)))
    with open(DUMP_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["collection", "object", "material", "dim_x_mm", "dim_y_mm", "dim_z_mm"])
        w.writerows(rows)
    return len(rows)


def main():
    reset_scene()
    make_root()
    build_materials()
    build_frame()
    build_legs()
    build_springs()
    build_deck()
    build_shell()
    build_cushions()
    build_shell_seams()
    build_helpers()
    build_dimensions()
    build_labels()
    build_environment()
    build_cameras()
    build_reference()
    add_explode_drivers()
    uv_upholstery()
    render_defaults()
    bpy.context.view_layer.update()
    n = dump_components()
    os.makedirs(os.path.dirname(BLEND_OUT), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_OUT)
    print(f"SOFA BUILD OK: {n} components, saved {BLEND_OUT}")


if __name__ == "__main__":
    main()
