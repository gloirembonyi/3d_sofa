"""
render_views.py - renders presentation images, sections, exploded view and
orthographic technical drawings from blend/sofa_caramel_shell.blend.

  blender -b blend/sofa_caramel_shell.blend -P scripts/render_views.py -- [--quick] [view ...]

--quick : Workbench preview renders (fast geometry check) into renders/preview/
views   : any of the keys in VIEWS / DRAWINGS (default: all)
"""
import bpy, os, sys
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
QUICK = "--quick" in argv
WANT = [a for a in argv if not a.startswith("--")]

sc = bpy.context.scene
ROOT = bpy.data.objects["SOFA_ROOT"]
COLL = {c.name: c for c in bpy.data.collections}

UPHOLSTERY = ["07_SEAT_FOAM", "08_BACK_FOAM", "09_ARMREST_FOAM", "10_CUSHION_TICKING", "11_UPHOLSTERY",
              "12_STITCHING_AND_SEAMS", "13_FABRIC_DETAILS"]
STRUCT = ["01_MAIN_FRAME", "02_WOODEN_REINFORCEMENTS", "03_FRAME_JOINTS", "04_LEGS_AND_GLIDES",
          "05_SEAT_SUSPENSION", "06_SPRING_CLIPS"]
ALL_SOFA = STRUCT + UPHOLSTERY

# name: (camera, visible collections, extra hidden objects (prefix), cutter, explode, env, engine)
VIEWS = {
    "01_hero":          ("CAM_01_Hero_ThreeQuarter", ALL_SOFA, [], None, 0, True),
    "02_front":         ("CAM_02_Front", ALL_SOFA, [], None, 0, True),
    "03_side":          ("CAM_03_Side", ALL_SOFA, [], None, 0, True),
    "04_rear":          ("CAM_04_Rear", ALL_SOFA, [], None, 0, True),
    "05_fabric_closeup": ("CAM_05_Fabric_Closeup", ALL_SOFA, [], None, 0, True),
    "06_cushion_construction": ("CAM_06_Cushion_Construction", ALL_SOFA, [], "EH_CUTTER_Right_Half_x250", 0, True),
    "07_exposed_frame": ("CAM_07_Exposed_Frame", STRUCT, ["RF_Bending_Ply", "SP_Back_Elastic", "DK_"], None, 0, True),
    "08_spring_closeup": ("CAM_08_Spring_Closeup", STRUCT + ["13_FABRIC_DETAILS"],
                          ["RF_Bending_Ply", "DK_", "FD_Dust"], None, 0, True),
    "09_exploded":      ("CAM_09_Exploded", ALL_SOFA + ["18d_EXPLODE_LABELS"], [], None, 1, False),
    "10_cutaway":       ("CAM_10_Cutaway", ALL_SOFA, [], "EH_CUTTER_Right_Half_x250", 0, True),
    "11_arm_section":   ("CAM_11_Arm_Section", ALL_SOFA, [], "EH_CUTTER_Arm_Section_y-120", 0, True),
    "12_load_paths":    ("CAM_07_Exposed_Frame", STRUCT + ["17_ENGINEERING_HELPERS"],
                         ["RF_Bending_Ply", "EH_CUTTER", "SOFA_ROOT", "DK_"], None, 0, True),
}
DRAWINGS = {
    "DRW_A_front_elevation": ("DRW_A_Front", ALL_SOFA + ["18a_DIM_FRONT"], [], None),
    "DRW_B_side_elevation": ("DRW_B_Side", ALL_SOFA + ["18b_DIM_SIDE"], [], None),
    "DRW_C_rear_elevation": ("DRW_C_Rear", ALL_SOFA, [], None),
    "DRW_D_top_view": ("DRW_D_Top", ALL_SOFA + ["18c_DIM_TOP"], [], None),
    "DRW_E_bottom_view": ("DRW_E_Bottom", ALL_SOFA, [], None),
    "DRW_F_structural_frame_top": ("DRW_D_Top", STRUCT, ["RF_Bending_Ply", "SP_Back", "SP_", "CL_"], None),
    "DRW_F2_structural_frame_front": ("DRW_A_Front", STRUCT, ["RF_Bending_Ply", "SP_Back"], None),
    "DRW_G_suspension_detail_top": ("DRW_D_Top", STRUCT, ["RF_Bending_Ply", "SP_Back", "DK_"], None),
    "DRW_H_seat_cushion_section": ("DRW_H_Seat_Section", ALL_SOFA, [], "EH_CUTTER_Seat_Section_x360"),
    "DRW_I_arm_section": ("DRW_I_Arm_Section", ALL_SOFA, [], "EH_CUTTER_Arm_Section_y-120"),
}


def sofa_objects():
    out = []
    for cn in ALL_SOFA:
        out += list(COLL[cn].all_objects)
    return out


def set_state(visible, hide_prefixes, explode, env):
    for c in bpy.data.collections:
        c.hide_render = True
    for cn in ["15_LIGHTING", "16_CAMERA"] + visible + (["19_ENVIRONMENT"] if env else []):
        COLL[cn].hide_render = False
        if cn.startswith("18"):
            COLL["18_DIMENSIONS_AND_LABELS"].hide_render = False
        if cn == "17_ENGINEERING_HELPERS":
            pass
    for ob in bpy.data.objects:
        ob.hide_render = any(ob.name.startswith(p) for p in hide_prefixes) or ob.name.startswith("EH_CUTTER") \
            or ob.name in ("MATERIAL_LIBRARY", "REF_Upholstered_Photo", "ST_Shell_Rim_Seam_Continuous")
    ROOT["explode"] = float(explode)
    ROOT.location = ROOT.location   # touch
    bpy.context.view_layer.update()


def world_bbox(ob):
    pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return (min(p.x for p in pts), max(p.x for p in pts), min(p.y for p in pts), max(p.y for p in pts),
            min(p.z for p in pts), max(p.z for p in pts))


ADDED = []
HIDDEN_BY_CUT = []


def apply_cut(cutter_name):
    cut = bpy.data.objects[cutter_name]
    cb = world_bbox(cut)
    for ob in sofa_objects():
        if ob.hide_render:
            continue
        b = world_bbox(ob)
        inside = b[0] >= cb[0] and b[1] <= cb[1] and b[2] >= cb[2] and b[3] <= cb[3]
        overlap = not (b[1] < cb[0] or b[0] > cb[1] or b[3] < cb[2] or b[2] > cb[3])
        if inside:
            ob.hide_render = True; HIDDEN_BY_CUT.append(ob)
        elif overlap:
            if ob.type == 'MESH':
                md = ob.modifiers.new("CUT", 'BOOLEAN'); md.object = cut; md.operation = 'DIFFERENCE'
                for solver in ('MANIFOLD', 'EXACT'):
                    try:
                        md.solver = solver; break
                    except Exception:
                        continue
                ADDED.append((ob, md))
            else:   # curves (springs, seams, ties) cannot be booleaned: hide any that reach into the cut
                ob.hide_render = True; HIDDEN_BY_CUT.append(ob)


def clear_cut():
    for ob, md in ADDED:
        ob.modifiers.remove(md)
    ADDED.clear(); HIDDEN_BY_CUT.clear()


def setup_cycles(res, samples):
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = 'OPENIMAGEDENOISE'
    except Exception:
        pass
    sc.cycles.max_bounces = 8
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = False


def setup_workbench(res, drawing=True):
    sc.render.engine = 'BLENDER_WORKBENCH'
    sh = sc.display.shading
    sh.light = 'STUDIO'
    sh.color_type = 'MATERIAL'
    sh.show_object_outline = True
    sh.object_outline_color = (0, 0, 0)
    sh.show_cavity = True
    sh.cavity_type = 'BOTH'
    sh.show_shadows = False
    sc.world.color = (1, 1, 1)
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = False
    try:
        sc.view_settings.view_transform = 'Standard'
        sc.view_settings.look = 'None'
        sc.view_settings.exposure = 0.0
    except Exception:
        pass


def render_to(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sc.render.filepath = path
    sc.render.image_settings.file_format = 'PNG'
    bpy.ops.render.render(write_still=True)
    print("RENDERED", path, flush=True)


def main():
    out_r = os.path.join(PROJECT, "renders", "preview" if QUICK else "")
    out_d = os.path.join(PROJECT, "drawings")
    for key, (cam, vis, hide, cutter, explode, env) in VIEWS.items():
        if WANT and key not in WANT:
            continue
        set_state(vis, hide, explode, env if not QUICK else False)
        bg = sc.world.node_tree.nodes.get("Background")
        if bg:   # light studio-grey void when there is no room, room daylight otherwise
            bg.inputs["Color"].default_value = (0.80, 0.84, 0.92, 1) if env else (0.92, 0.91, 0.89, 1)
            bg.inputs["Strength"].default_value = 0.35 if env else 0.9
        if cutter:
            apply_cut(cutter)
        sc.camera = bpy.data.objects[cam]
        if QUICK:
            setup_workbench((960, 640))
        else:
            hero = key in ("01_hero",)
            setup_cycles((1600, 1067) if hero else (1280, 853), 128 if hero else 48)
            try:
                sc.view_settings.view_transform = 'AgX'
                sc.view_settings.look = 'AgX - Medium High Contrast'
                sc.view_settings.exposure = -0.4
            except Exception:
                pass
        render_to(os.path.join(out_r, key + ".png"))
        clear_cut()
    if QUICK and not any(k in DRAWINGS for k in WANT):
        return
    for key, (cam, vis, hide, cutter) in DRAWINGS.items():
        if WANT and key not in WANT:
            continue
        set_state(vis, hide, 0, False)
        if cutter:
            apply_cut(cutter)
        sc.camera = bpy.data.objects[cam]
        setup_workbench((1800, 1200))
        render_to(os.path.join(out_d, key + ".png"))
        clear_cut()


main()
