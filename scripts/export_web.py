"""
export_web.py - exports the sofa for the web configurator.

  blender -b blend/sofa_caramel_shell.blend -P scripts/export_web.py

Writes (into web/public/):
  models/sofa.glb    upholstery shell, base band, seat + back cushions, oak legs, glides, scatter pillows
  models/frame.glb   internal frame, reinforcements, joinery, springs, clips, back webbing (for the X-ray view)
  textures/*.png     tileable PBR maps (normal + colour-variation) for boucle, velvet, linen, leather, oak

Notes
  * Procedural Blender shaders cannot travel in glTF, so geometry gets box-projected UVs
    (1 UV unit = TILE metres) and the look is rebuilt in three.js from the generated maps.
  * Blender Z-up is converted to glTF Y-up by the exporter (sofa front = +Z in three.js).
"""
import bpy, os, sys, runpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
PUB = os.path.join(PROJECT, "web", "public")
MODELS = os.path.join(PUB, "models"); TEX = os.path.join(PUB, "textures")
os.makedirs(MODELS, exist_ok=True); os.makedirs(TEX, exist_ok=True)
TILE = 0.12            # metres covered by one texture tile

# ---------------------------------------------------------------- build pillows (reuse sales_shots, render nothing)
sys.argv = [sys.argv[0], "--", "__no_render__"]
runpy.run_path(os.path.join(HERE, "sales_shots.py"), run_name="__sales__")

dg = bpy.context.evaluated_depsgraph_get()
scene = bpy.context.scene
web = bpy.data.collections.new("WEB_EXPORT"); scene.collection.children.link(web)
MATS = {}


def mat(name, rgb, rough=0.8, metal=0.0):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes.get("Principled BSDF")
    if b:
        b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
        b.inputs["Metallic"].default_value = metal
    MATS[name] = m
    return m


def box_uv(me):
    """Box projection in world metres -> UVs, vectorised."""
    for l in list(me.uv_layers):
        me.uv_layers.remove(l)
    uvl = me.uv_layers.new(name="UVMap")
    nl = len(me.loops)
    if nl == 0:
        return
    vco = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", vco); vco = vco.reshape(-1, 3)
    lv = np.empty(nl, dtype=np.int64); me.loops.foreach_get("vertex_index", lv)
    pn = np.empty(len(me.polygons) * 3); me.polygons.foreach_get("normal", pn); pn = pn.reshape(-1, 3)
    ps = np.empty(len(me.polygons), dtype=np.int64); me.polygons.foreach_get("loop_start", ps)
    pt = np.empty(len(me.polygons), dtype=np.int64); me.polygons.foreach_get("loop_total", pt)
    lp = np.repeat(np.arange(len(me.polygons)), pt)
    ax = np.argmax(np.abs(pn), axis=1)[lp]
    co = vco[lv]
    u = np.where(ax == 0, co[:, 1], co[:, 0])
    v = np.where(ax == 2, co[:, 1], co[:, 2])
    uv = np.stack([u, v], axis=1) / TILE
    uvl.data.foreach_set("uv", uv.ravel())


def export_copy(src, name, material, uv=True):
    ev = src.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=False, depsgraph=dg)
    me.transform(src.matrix_world)
    me.materials.clear(); me.materials.append(material)
    for p in me.polygons:
        p.use_smooth = True
    if uv:
        box_uv(me)
    ob = bpy.data.objects.new(name, me)
    web.objects.link(ob)
    return ob


def objs(prefix=None, coll=None):
    out = []
    pool = bpy.data.collections[coll].all_objects if coll else bpy.data.objects
    for o in pool:
        if o.type in ('MESH', 'CURVE') and (prefix is None or o.name.startswith(prefix)):
            out.append(o)
    return out


# ---------------------------------------------------------------- sofa.glb
fabric = mat("fabric", (0.40, 0.16, 0.04), 0.95)
wood = mat("wood", (0.50, 0.35, 0.20), 0.5)
glide = mat("glide", (0.08, 0.08, 0.08), 1.0)
pmats = {"GreyBoucle": mat("pillow_grey", (0.42, 0.41, 0.39), 0.95),
         "RustVelvet": mat("pillow_rust", (0.16, 0.04, 0.016), 0.8),
         "Linen": mat("pillow_linen", (0.42, 0.37, 0.29), 0.92)}
sofa_objs = []
names = {"UP_Shell_Cover_Boucle_Arms_Back": "Fabric_Shell", "UP_Front_Base_Band_Boucle": "Fabric_Base",
         "CU_Seat_L_Cover_Boucle": "Fabric_SeatL", "CU_Seat_R_Cover_Boucle": "Fabric_SeatR",
         "CU_Back_L_Cover_Boucle": "Fabric_BackL", "CU_Back_R_Cover_Boucle": "Fabric_BackR"}
for src, dst in names.items():
    sofa_objs.append(export_copy(bpy.data.objects[src], dst, fabric))
for o in objs("LG_Leg_"):
    sofa_objs.append(export_copy(o, "Leg_" + o.name.split("_")[2] + o.name.split("_")[3], wood))
for o in objs("LG_Glide_"):
    sofa_objs.append(export_copy(o, "Glide_" + o.name.split("_")[2] + o.name.split("_")[3], glide, uv=False))
for o in objs("ACC_Pillow_"):
    key = next(k for k in pmats if k in o.name)
    nm = "Pillow_" + key + ("_Piping" if o.name.endswith("_Piping") else "")
    sofa_objs.append(export_copy(o, nm, pmats[key]))

# ---------------------------------------------------------------- frame.glb
beech = mat("beech", (0.55, 0.36, 0.21), 0.6)
ply = mat("ply", (0.66, 0.50, 0.33), 0.6)
steel = mat("steel", (0.62, 0.63, 0.65), 0.35, 1.0)
plastic = mat("plastic", (0.03, 0.03, 0.03), 0.5)
felt = mat("felt", (0.30, 0.28, 0.25), 1.0)
frame_objs = []
for cn in ("01_MAIN_FRAME", "02_WOODEN_REINFORCEMENTS", "03_FRAME_JOINTS", "05_SEAT_SUSPENSION", "06_SPRING_CLIPS"):
    for o in objs(coll=cn):
        if o.name.startswith(("RF_Bending_Ply", "DK_")):
            continue
        mname = o.material_slots[0].material.name if o.material_slots and o.material_slots[0].material else ""
        m = {"MAT_Wood_Beech": beech, "MAT_Plywood_Birch": ply, "MAT_Glue_Dowel": beech, "MAT_Steel_Spring": steel,
             "MAT_Steel_Zinc": steel, "MAT_Plastic_Black": plastic}.get(mname, felt)
        frame_objs.append(export_copy(o, "Frame_" + o.name[:50], m, uv=False))


def export(path, obs):
    for o in scene.objects:
        o.select_set(False)
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    kw = dict(filepath=path, export_format='GLB', use_selection=True, export_apply=True, export_yup=True,
              export_texcoords=True, export_normals=True, export_materials='EXPORT',
              export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6)
    try:
        bpy.ops.export_scene.gltf(**kw)
    except TypeError:
        kw.pop("export_draco_mesh_compression_level"); bpy.ops.export_scene.gltf(**kw)
    print("EXPORTED", path, round(os.path.getsize(path) / 1e6, 2), "MB", len(obs), "objects", flush=True)


export(os.path.join(MODELS, "sofa.glb"), sofa_objs)
export(os.path.join(MODELS, "frame.glb"), frame_objs)

# ---------------------------------------------------------------- tileable texture maps
rng = np.random.default_rng(7)


def periodic_noise(n, freqs, amps):
    """Tileable noise from a sum of integer-frequency cosines."""
    y, x = np.mgrid[0:n, 0:n] / n
    h = np.zeros((n, n))
    for f, a in zip(freqs, amps):
        waves = 48
        for _ in range(waves):                    # many random directions -> isotropic, no grating
            ang = rng.uniform(0, np.pi); r = f * rng.uniform(0.6, 1.0)
            kx, ky = int(round(r * np.cos(ang))), int(round(r * np.sin(ang)))
            if kx == 0 and ky == 0:
                continue
            h += a / np.sqrt(waves) * np.cos(2 * np.pi * (kx * x + ky * y) + rng.uniform(0, 2 * np.pi))
    return h


def worley(n, cells, f2=False):
    """Tileable Worley (F1, optionally F2-F1) on a jittered grid."""
    pts = (np.stack(np.meshgrid(np.arange(cells), np.arange(cells), indexing="ij"), -1) + rng.random((cells, cells, 2))) / cells
    y, x = np.mgrid[0:n, 0:n] / n
    ci, cj = (x * cells).astype(int), (y * cells).astype(int)
    d1 = np.full((n, n), 9.0); d2 = np.full((n, n), 9.0)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            ii, jj = (ci + di) % cells, (cj + dj) % cells
            p = pts[ii, jj]
            dx = x - p[..., 0]; dy = y - p[..., 1]
            dx -= np.round(dx); dy -= np.round(dy)
            d = np.sqrt(dx * dx + dy * dy) * cells
            d2 = np.where(d < d1, d1, np.minimum(d2, d)); d1 = np.minimum(d1, d)
    return (d2 - d1) if f2 else d1


def save_rgb(name, rgb):
    n = rgb.shape[0]
    img = bpy.data.images.new(name, n, n, alpha=False)
    rgba = np.concatenate([np.clip(rgb, 0, 1), np.ones((n, n, 1))], axis=2)
    img.pixels.foreach_set(rgba.astype(np.float32).ravel())
    img.filepath_raw = os.path.join(TEX, name + ".png"); img.file_format = 'PNG'
    img.save()
    print("TEXTURE", name, flush=True)


def normal_from_height(h, strength):
    dx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5 * strength
    dy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5 * strength
    nz = np.ones_like(h)
    nv = np.stack([-dx, -dy, nz], -1)
    nv /= np.linalg.norm(nv, axis=2, keepdims=True)
    return nv * 0.5 + 0.5


def norm01(a):
    return (a - a.min()) / (a.max() - a.min() + 1e-9)


def make(name, h, strength, var_lo, var_hi, extra_var=None):
    h = norm01(h)
    save_rgb(name + "_normal", normal_from_height(h, strength))
    v = var_lo + (var_hi - var_lo) * (h if extra_var is None else norm01(0.85 * h + 0.15 * extra_var))
    save_rgb(name + "_color", np.repeat(v[..., None], 3, axis=2))


N = 1024
# boucle: two overlapping layers of round loops (~4-5 mm in a 120 mm tile) + fibre fuzz
l1 = np.clip(1 - worley(N, 26) / 0.62, 0, 1) ** 0.7
l2 = np.clip(1 - worley(N, 19) / 0.62, 0, 1) ** 0.7
fuzz = periodic_noise(N, [96, 160], [0.5, 0.35])
clump = periodic_noise(N, [1, 2], [1.0, 0.5])
make("boucle", np.maximum(l1, 0.85 * l2) + 0.06 * fuzz, 6.0, 0.70, 1.0)   # no low-freq clump: it repeats per tile as stripes
# velvet: very soft crush pattern
make("velvet", periodic_noise(N, [4, 9, 20], [1.0, 0.5, 0.2]), 1.2, 0.80, 1.0)
# linen: woven warp/weft with slubs
y, x = np.mgrid[0:N, 0:N] / N
T = 96
warp = 0.5 + 0.5 * np.sin(2 * np.pi * x * T); weft = 0.5 + 0.5 * np.sin(2 * np.pi * y * T)
check = np.sign(np.sin(np.pi * x * T)) * np.sign(np.sin(np.pi * y * T))
slub = periodic_noise(N, [6, 14], [1.0, 0.5])
make("linen", np.where(check > 0, warp, weft) + 0.06 * slub, 5.0, 0.80, 1.0)
# leather: pebbled grain (F2-F1 creases) + pores
grain = np.clip(worley(N, 40, f2=True) / 0.6, 0, 1)
make("leather", grain ** 0.5 + 0.08 * periodic_noise(N, [180], [1.0]), 4.0, 0.78, 1.0)
# oak: long grain lines (vertical in v)
gl = np.sin(2 * np.pi * (x * 22 + 0.25 * periodic_noise(N, [2, 3], [1, 0.5]))) * 0.5 + 0.5
make("oak", gl + 0.15 * periodic_noise(N, [40], [1.0]), 1.5, 0.70, 1.0)
print("EXPORT_WEB DONE", flush=True)
