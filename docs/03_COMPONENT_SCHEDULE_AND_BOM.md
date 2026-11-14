# Component Schedule, Material Schedule and Bill of Materials — Caramel Shell 2S (Rev B)

- Dimensions are finished sizes in mm.
- The Blender object names (prefix in brackets) match `docs/component_dump.csv`. That file lists every object with its bounding box.
- **Cost fields are left blank on purpose.** Fill them in with local supplier prices; none have been invented.

## 1. Component schedule

| # | Part (Blender prefix) | Qty | Material | Size / section | Manufacturing method | Connection | Purpose |
|---|---|---|---|---|---|---|---|
| 1 | Front seat rail (`FR_A`) | 1 | Beech KD 8–12 % | 38 × 120 × 1525 | Planed, crosscut, bored | 2 dowels + M8 cross-dowel bolt each end, glue | Front spring anchor, front-edge loads |
| 2 | Rear seat rail (`FR_B`) | 1 | Beech | 38 × 86 × 1525 | Same | Same | Rear spring anchor |
| 3 | Side seat rails (`FR_C`) | 2 | Beech | 38 × 120 × 578 | Same | Glued + screwed to the inner arm panel; bolted through | Arm ↔ seat box, leg blocks |
| 4 | Centre stretcher (`FR_D`) | 1 | Beech | 32 × 70 × 522 + tenons | Tenoned both ends | M&T + glue + stretcher blocks | Spring-pull strut, centre-foot carrier |
| 5 | Lower cross members (`FR_E`) | 2 | Beech | 32 × 50 × 522 | Round tenons Ø12 | Glue | Rack stability, dust-cover support |
| 6 | Back base rail (`FR_H_Back_Base`) | 1 | Beech | 38 × 90 × 1540 | Planed | Dowels into the rear leg blocks + back formers | Back former seat |
| 7 | Inner arm panels (`FR_F`) | 2 | Birch ply 18 (EN 636-2) | ≈578 × 450 profile, leaning | CNC-routed | Glue + screws to the side rail; rails dowelled/bolted | Arm stiffness |
| 8 | Arm ribs (`FR_G`) | 6 | Birch ply 18 | D-profile ring, 70 wide | CNC-routed | Half-lap onto stringers, glue + staples | Arm shape |
| 9 | Back formers (`FR_J_Back`) | 4 | Birch ply 18 | Back profile ring | CNC | Same | Back shape and recline |
| 10 | Corner formers (`FR_J_Corner`) | 2 | Birch ply 18 | Corner profile ring | CNC | Same | Corner shape |
| 11 | Continuous rails / stringers (`FR_I`, `FR_K`, `FR_H_Inner`) | 6 runs | Beech 28 × 28 (laminated on corners) | ≈2700 developed length each | Straight runs planed; corners bent-laminated from 3 × 9 mm or stacked CNC ply | Half-lap into ribs, glue + screw | Rim spine, rib alignment, webbing anchor |
| 12 | Bending-ply outer skin (`RF_Bending_Ply`) | 1 set (≈3 panels) | Poplar bending ply 5 | ≈2.5 m² | Cut, cross-grain bent | Glue + 10 mm staples at 50 mm | Curved foam substrate |
| 13 | Corner blocks (`RF_L`) | 4 | Beech | 60 × 60 triangle × 100 | Bandsaw | Glue + 2 × 4.5 × 50 screws | Seat-box racking |
| 14 | Stretcher blocks (`RF_N`) | 4 | Beech | 40 × 40 triangle × 60 | Bandsaw | Glue + 1 screw | Stretcher joint |
| 15 | Leg blocks, front (`RF_M_..._Front`) | 2 | Beech | 72 × 87 × 40 | Planed, M8 insert | Glue + 4 screws | Leg mount |
| 16 | Leg blocks, rear (`RF_M_..._Rear`) | 2 | Beech | 100 × 100 × 45 | Same | Same | Leg mount |
| 17 | Centre support block | 1 | Beech | 90 × 80 × 16 | Planed | Glue + screws under the stretcher | Centre foot mount |
| 18 | Dowels (`JN_Dowel`) | 8 | Beech, fluted | Ø10 × 40 | Bought in | PVAc D3 | Rail-end joints |
| 19 | M8 × 100 bolts + cross dowels (`JN_Bolt`, `JN_CrossDowel`) | 4 + 4 | Zinc-plated steel | M8 × 100; Ø10 × 35 cross dowel | Bought in | Torque about 8 N·m | Rail-end clamping |
| 20 | Tenons (`JN_Tenon`) | 2 + 4 | Beech | 24 × 25 × 50; Ø12 × 24 | Machined | Glue | Stretcher / cross members |
| 21 | Screws (`JN_Screw`) | ≈40 | Steel, zinc | 4.5 × 50 | — | — | Blocks |
| 22 | Sinuous springs (`SP_Sinuous`) | 12 | Spring steel, Ø4.1 (8 ga) | ≈560 clip-to-clip, 22 arc | Bought, pre-formed | Clips | Seat suspension |
| 23 | Spring clips (`CL_`) | 24 | Steel + plastic liner | 40 × 20 | Bought in | 2 ring-shank nails each | Spring anchor, anti-squeak |
| 24 | Helical tie springs | 30 | Steel, coated | Ø8 coil × ≈60 | Bought in | Hooked | Load sharing |
| 25 | Back elastic webbing (`SP_Back`) | ≈6.5 m | Elastic webbing 50 mm | 10 vertical + 2 horizontal straps | Cut, 10 % pre-tension | Staples (4 per end), folded | Back support |
| 26 | Spring insulator (`DK_Spring_Insulator`) | ≈1 m² | Needle-punched felt 300 g/m² | 1402 × 573 × 5 | Cut | Staples to rails | Protects foam from springs |
| 27 | Deck foam pad (`DK_Deck_Foam`) | 1 | HR30 | 1402 × 573 × 20 | Cut | Spray-glue to the felt | Deck comfort |
| 28 | Decking cloth (`DK_Decking`) | ≈1.2 m² | Non-woven PP 80–100 g/m² | — | Cut | Staples | Deck finish under the cushions |
| 29 | Front edge foam (`FM_Front_Edge`, `FM_Front_Bullnose`) | 1 + 1 | HR35 firm | 1394 × 60 × 108; roll Ø38 | Cut / rolled | Spray glue | Base band shape |
| 30 | Shell firm foam (`FM_Shell_Firm`) | 1 set | HR35 firm | 20 thick, ≈3.2 m² | CNC / hand cut | Spray glue to the bending ply | Arm/back form |
| 31 | Shell soft foam (`FM_Shell_Soft`) | 1 set | HR30 | 22 thick, ≈3.4 m² | Cut | Spray glue | Arm/back comfort |
| 32 | Shell wadding (`FB_Shell_Wadding`) | ≈3.6 m² | Polyester 150 g/m² | — | Cut | Spray tack | Smooth fabric line |
| 33 | Seat cushion core (`CU_Seat_*_Core`) | 2 | HR40 | 665 × 479 × 114 | Bandknife | Glued to the comfort layer | Support |
| 34 | Seat comfort layer (`CU_Seat_*_Comfort`) | 2 | HR35 | 665 × 479 × 25 | Bandknife | Spray glue | Initial softness |
| 35 | Seat fibre wrap (`CU_Seat_*_Fibre`) | 2 | Bonded polyester 200 g/m² | Wraps the foam | Cut | Spray tack | Crown, softness |
| 36 | Seat ticking (`CU_Seat_*_Ticking`) | 2 | Cotton ticking 150 g/m² | Sewn box | Sewn | — | Insert containment |
| 37 | Seat cover (`CU_Seat_*_Cover`) | 2 | Bouclé | 701 × 515 × 175 boxed, 560 rear zip | Sewn, rear zip | — | Finish |
| 38 | Back cushion core (`CU_Back_*_Core`) | 2 | HR30 | ≈651 × 470 × 135→100 | Bandknife + CNC lumbar | — | Back support |
| 39 | Back fibre layer (`CU_Back_*_Fibre`) | 2 | Siliconised hollow fibre in compartments | ≈22 | Blown / filled | Sewn compartments | Softness |
| 40 | Back ticking (`CU_Back_*_Ticking`) | 2 | Cotton ticking | Sewn | Sewn | — | Insert containment |
| 41 | Back cover (`CU_Back_*_Cover`) | 2 | Bouclé | 701 × 520 × 185 | Sewn, bottom zip | Hook-and-loop tabs to the deck | Finish |
| 42 | Shell cover (`UP_Shell_Cover`) | 1 | Bouclé | Outer back + 2 outer arms + inside back + 2 inside arms + 2 arm-front panels | Sewn | Staples to the base stringers / rails | Finish |
| 43 | Front base band (`UP_Front_Base_Band`) | 1 | Bouclé | 1446 × ≈300 developed | Sewn | Staples under the rail | Finish |
| 44 | Seams / zips (`ST_`) | — | Polyester bonded thread Tex 70; #5 nylon coil zips | — | — | — | Assembly |
| 45 | Dust cover (`FD_Dust_Cover`) | 1 | Black non-woven 70 g/m² | 1790 × 845 | Cut | Staples, 30 mm pitch | Underside finish |
| 46 | Legs (`LG_Leg`) | 4 | Solid oak | Ø80 × 94, R6 edges | Turned, oiled / lacquered | M8 hanger bolt | Support |
| 47 | Hanger bolts + inserts (`LG_HangerBolt`, `LG_Threaded_Insert`) | 4 + 4 | Zinc steel | M8 × 48; M8 × 16 insert | Bought in | — | Leg fixing |
| 48 | Felt glides (`LG_Glide`) | 4 | Felt | Ø64 × 5 | Bought in | Adhesive / nail | Floor protection |
| 49 | Centre foot (`LG_Centre_Support`) | 1 | Polymer, adjustable | Ø40 × 98 | Bought in | M8 insert | Rear-rail mid support |

## 2. Material schedule

| Material | Grade / spec | Key properties (assumed) | Use |
|---|---|---|---|
| European beech | KD 8–12 % MC, FAS / select, straight grain, no knots in rails | ρ 720 kg/m³, E 14 000 MPa, MOR ≈ 100 MPa | Rails, blocks, stringers |
| Birch plywood | 18 mm, EN 636-2, BB/CP, ≥ 13 plies | ρ 680, E ≈ 9 000 / 6 000 MPa | Ribs, formers, inner arm panels |
| Bending plywood | Poplar 5 mm, cross-grain | ρ 450 | Outer skin |
| HR foam 40 | ≥ 40 kg/m³, IFD25 150–170 N, SF ≥ 2.4, CMHR where required | — | Seat core |
| HR foam 35 | 35 kg/m³, comfort IFD25 90–110 N; firm IFD25 ≈ 200 N | — | Comfort layer, firm shell, front edge |
| HR foam 30 | 30 kg/m³, IFD25 70–90 N | — | Back core, soft shell, deck pad |
| Polyester fibre | Bonded 200 g/m² wrap; 150 g/m² wadding; siliconised hollow-fibre fill | — | Wraps |
| Bouclé / teddy fabric | ≈ 550–650 g/m², Martindale ≥ 40 000, pilling ≥ 4, seam slippage ≤ 6 mm at 120 N, fire spec per market | — | Upholstery |
| Ticking | Cotton 150 g/m² | — | Cushion inner |
| Spring steel | 8-ga Ø4.1, phosphate- or paint-coated, EN 10270-1 grade SH or equal | Rm ≈ 1600–1800 MPa | Springs |
| Oak | Solid, KD | ρ 700 | Legs |
| PVAc adhesive | D3 (EN 204) | — | Joinery |
| Contact / spray adhesive | Foam grade, solvent- or water-based | — | Foam laminating |

## 3. Bill of materials (per sofa)

| Item | Estimated quantity | Specification | Recommended quality | Purpose | Alternatives | Unit cost | Total |
|---|---|---|---|---|---|---|---|
| Beech timber | ≈ 0.050 m³ finished (≈ 0.075 m³ rough) | KD, select | Straight grain, no knots in rails | Rails, blocks, stringers | Ash, maple, hard maple; LVL for rails | | |
| Birch plywood 18 | ≈ 1.6 m² (≈ 0.6 sheet 2500 × 1250) | EN 636-2 BB/CP | — | Ribs, formers, panels | Poplar ply 18 (lighter, weaker) | | |
| Bending ply 5 | ≈ 2.6 m² | Poplar, cross-grain | — | Skin | 3 mm hardboard | | |
| Dowels Ø10 × 40 | 8 (+ spares) | Fluted beech | — | Joints | — | | |
| M8 × 100 bolts + cross dowels | 4 + 4 | Zinc | — | Joints | Furniture connector bolts | | |
| Screws 4.5 × 50 / 4 × 30 | ≈ 60 | Zinc, pozi | — | Blocks, panels | — | | |
| Wood glue PVAc D3 | ≈ 0.4 kg | EN 204 D3 | — | Joints | PU adhesive | | |
| Sinuous springs 8-ga | 12 | ≈ 560 span, pre-formed | Supplier load-deflection data | Seat | 9-ga for softer seat | | |
| Spring clips + nails | 24 + 48 | Lined clips, ring nails | — | Spring anchor | Spring rails with hooks | | |
| Helical tie springs | 30 | Coated | — | Ties | Clip-on links | | |
| Elastic webbing 50 | ≈ 6.5 m | 50 mm, ≥ 60 % elongation | — | Back | Back sinuous springs 11-ga | | |
| Felt insulator | ≈ 1 m² | 300 g/m² | — | Deck | Hessian + felt | | |
| HR40 foam | ≈ 0.073 m³ | See §2 | Certified density / IFD | Seat core | — | | |
| HR35 foam | ≈ 0.090 m³ incl. shell firm + edge | See §2 | — | Comfort, firm | — | | |
| HR30 foam | ≈ 0.18 m³ incl. back, shell soft, deck | See §2 | — | Back, shell soft | — | | |
| Polyester fibre | ≈ 2.1 kg total (wrap 200 g/m², wadding 150 g/m², fill) | — | — | Wraps, fill | Feather/fibre blend for back | | |
| Bouclé fabric | **≈ 11–12 linear m at 140 cm width** (estimate, add 10 % for pattern/pile direction) | ≈ 600 g/m² | Martindale ≥ 40 000 | Covers | Wool-blend bouclé | | |
| Cotton ticking | ≈ 4.5 m² | 150 g/m² | — | Inner cushions | Non-woven | | |
| Thread | ≈ 1 cone | Bonded polyester Tex 70 | — | Sewing | — | | |
| Zippers | 2 × 600 + 2 × 650 | #5 nylon coil | — | Cushions | — | | |
| Hook-and-loop | ≈ 0.6 m | 25 mm | — | Back cushion retention | — | | |
| Upholstery staples | ≈ 1500 | 80-series, 8–10 mm | — | Fabric, webbing, felt | — | | |
| Contact adhesive | ≈ 1.5 l | Foam grade | Low VOC | Foam bonding | — | | |
| Oak legs | 4 | Ø80 × 94 turned | KD oak | Legs | Ash, beech stained | | |
| Hanger bolts + inserts | 4 + 4 | M8 | — | Leg fixing | Leg plates | | |
| Felt glides | 4 | Ø64 | — | Floor | PTFE glides | | |
| Centre foot | 1 | Adjustable Ø40, M8 | — | Mid support | Fixed 98 mm foot | | |
| Dust cover | ≈ 1.6 m² | 70 g/m² black non-woven | — | Underside | Cambric | | |

**Mass check:** the model computes 69 kg (`docs/mass_report.csv`). Packaged weight including the carton will be about 80 kg.
