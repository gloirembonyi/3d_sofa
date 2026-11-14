"""
mass_properties.py - computes volume, mass and centre of gravity of every
sofa component from the actual Blender geometry (evaluated meshes incl. modifiers).

  blender -b blend/sofa_caramel_shell.blend -P scripts/mass_properties.py

Writes docs/mass_report.csv and prints totals.  Densities are assumptions
(kg/m3) - thin textiles use an equivalent density = areal mass / modelled thickness.
"""
import bpy, bmesh, os, csv
from mathutils import Vector

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DENSITY = {  # kg/m3
    "MAT_Wood_Beech": 720, "MAT_Plywood_Birch": 680, "MAT_Plywood_Bending": 450, "MAT_Wood_Oak_Legs": 700,
    "MAT_Glue_Dowel": 720, "MAT_Steel_Spring": 7850, "MAT_Steel_Zinc": 7850, "MAT_Plastic_Black": 1100,
    "MAT_Glide_Felt": 300, "MAT_Foam_HR40_Core": 40, "MAT_Foam_HR35_Comfort": 35, "MAT_Foam_HR30_Back": 30,
    "MAT_Foam_Firm_Shell": 35, "MAT_Foam_Soft_Shell": 30, "MAT_Fibre_Polyester": 20,
    "MAT_Ticking_Cotton": 190,      # ~150 g/m2 over 0.8 mm
    "MAT_Boucle_Caramel": 260,      # ~600 g/m2 over 2.0-2.5 mm
    "MAT_Decking_Grey": 70, "MAT_Felt_Insulator": 60, "MAT_DustCover_Black": 70,
    "MAT_Thread_Seam": 400, "MAT_Zipper": 2000,
}
SOFA_COLLS = ["01_MAIN_FRAME", "02_WOODEN_REINFORCEMENTS", "03_FRAME_JOINTS", "04_LEGS_AND_GLIDES",
              "05_SEAT_SUSPENSION", "06_SPRING_CLIPS", "07_SEAT_FOAM", "08_BACK_FOAM", "09_ARMREST_FOAM",
              "10_CUSHION_TICKING", "11_UPHOLSTERY", "12_STITCHING_AND_SEAMS", "13_FABRIC_DETAILS"]

dg = bpy.context.evaluated_depsgraph_get()
rows, tot_m, mom = [], 0.0, Vector()
by_mat = {}
for cn in SOFA_COLLS:
    for ob in bpy.data.collections[cn].all_objects:
        if ob.type not in ('MESH', 'CURVE'):
            continue
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        bm = bmesh.new(); bm.from_mesh(me)
        vol_mm3 = abs(bm.calc_volume(signed=False))
        # centroid (world, metres) - vertex average of evaluated mesh
        mw = ob.matrix_world
        cen = sum((mw @ v.co for v in bm.verts), Vector()) / max(1, len(bm.verts))
        bm.free(); ev.to_mesh_clear()
        mat = ob.material_slots[0].material.name if ob.material_slots and ob.material_slots[0].material else "?"
        rho = DENSITY.get(mat, 700)
        mass = vol_mm3 * 1e-9 * rho
        tot_m += mass; mom += cen * mass
        by_mat[mat] = by_mat.get(mat, 0.0) + mass
        rows.append((cn, ob.name, mat, round(vol_mm3 / 1e6, 4), rho, round(mass, 3),
                     round(cen.x * 1000), round(cen.y * 1000), round(cen.z * 1000)))

cog = mom / tot_m
out = os.path.join(PROJECT, "docs", "mass_report.csv")
with open(out, "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["collection", "object", "material", "volume_dm3", "density_kg_m3", "mass_kg",
                "cx_mm", "cy_mm", "cz_mm"])
    w.writerows(rows)
    w.writerow([])
    for k, v in sorted(by_mat.items(), key=lambda kv: -kv[1]):
        w.writerow(["MATERIAL_TOTAL", k, "", "", DENSITY.get(k, 700), round(v, 3)])
    w.writerow(["TOTAL", "", "", "", "", round(tot_m, 2),
                round(cog.x * 1000), round(cog.y * 1000), round(cog.z * 1000)])
print(f"MASS TOTAL {tot_m:.2f} kg  CoG = ({cog.x*1000:.0f}, {cog.y*1000:.0f}, {cog.z*1000:.0f}) mm")
for k, v in sorted(by_mat.items(), key=lambda kv: -kv[1]):
    print(f"  {k:28s} {v:7.2f} kg")
