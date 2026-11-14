# Engineering Report — Caramel Shell 2S (Rev B)

Covers Stages 2, 3, 5, 6, 8 and 11 of the brief. Units are mm, N, MPa and kg.

**Status legend:**
- **[CALC]** hand calculation.
- **[MODEL]** computed from the Blender geometry.
- **[ASSUMED]** input value that must be confirmed.
- **[TEST]** needs a physical test.

No finite-element analysis and no laboratory testing have been carried out. The FEA workflow and test plan are prepared in §9–10.

Rev B replaces the Stage 1 numbers (Rev A) wherever they differ. The exterior was re-proportioned to match the reference photo more closely.

---

## 1. Final dimensions (Rev B)

| Parameter | Value | Note |
|---|---|---|
| Overall W × D × H | **1900 × 900 × 780** | Arms bulge to ±952 at about 30 % height |
| Clear width between arms (at the inner face, deck level) | **1410** | Arms lean outward 55 mm toward the top, so the clear width at the elbows is about 1500 |
| Arm width (base / rim) | **≈245 / ≈180** | Tapered, embracing arms as in the reference |
| Arm height at the front → at the back junction | **640 → 760** | Rim flows continuously into the 780 back |
| Arm front | 150 mm circular nose in plan and side | Continuous round D-shaped front |
| Seat height (cushion crown, unloaded) | **≈445** | Loaded ≈ 380–395 [CALC/TEST] |
| Deck height at the front | 264 | Front base band (bullnose) |
| Seat cushions | 2 × 701 W × 515 D × 175 T | 14 mm domed crown, 9 mm billowed sides, ≈55 mm edge radius |
| Back cushions | 2 × 701 W × 520 H × 185→150 T | Pillow form, 20 mm lumbar crown, 10° recline |
| Effective seat depth | **≈530 uncompressed, ≈505 loaded** | Front of cushion to back-cushion face at seat level |
| Seat rake / seat-to-back angle | 0.85° cushion, 10° back recline → **≈101° seat-to-back** | 0.85° is the cushion bottom; the occupant's pelvis settles further on the soft rear |
| Legs | Ø80 × 94 oak + 5 mm felt glide | Frame underside at 100 |
| Leg centres | front (±870, −310), rear (±800, +290) | Hidden centre foot at (0, +190) |

## 2. Ergonomics (Stage 2)

- **User range:** about 5th-percentile female (stature ≈ 152 cm) to 95th-percentile male (≈ 188 cm).
  - Buttock–popliteal length runs from about 432 (P5 female) to 550 (P95 male).
  - A 505–530 effective depth supports 90–100 % of the thigh for large users. Small users can sit upright with their knees at the cushion edge. A 50 mm scatter cushion brings very small users to about 455.
- **Seat height:** 445 unloaded, about 385 loaded. Popliteal height plus shoe is about 395 (P5 F) to 520 (P95 M).
  - The loaded height sits at the low, lounge end, matching the reference's relaxed character. Rising is helped by the firm front base band (high front-edge support).
- **Back:** a 10° recline with a lumbar crown about 180–250 above the compressed seat supports the lumbar curve. The back cushion top at ≈745 supports the mid-thoracic region of an average adult (not the head; this is a conversation sofa).
- **Arms:** the arm rim at the front is ≈255 above the loaded seat, rising to ≈375 at the back. The elbow-rest zone sits in the front half, within the comfortable 200–280 range above the compressed seat. The rounded rim (≈90 mm radius) avoids pressure points on the forearm.
- **Seat-to-back ≈ 101° + cushion compression ≈ 105° effective.** Relaxed but upright, suitable for conversation and TV.

## 3. Structural frame (Stage 3)

### 3.1 Members (all modelled in collection `01_MAIN_FRAME` / `02_WOODEN_REINFORCEMENTS`)

| ID | Member | Section | Material | Purpose |
|---|---|---|---|---|
| A | Front seat rail | 38 × 120 × 1525 | Beech, KD 8–12 % MC | Front spring anchor; front-edge loads |
| B | Rear seat rail | 38 × 86 × 1525 | Beech | Rear spring anchor |
| C | Side seat rails (×2) | 38 × 120 × 578 | Beech | Ties the arm to the seat box; carries the leg blocks |
| D | Centre stretcher | 32 × 70 × 522 | Beech | **Strut against spring pull**; carries the centre foot |
| E | Lower cross members (×2) | 32 × 50 × 522 | Beech | Diagonal stability and dust-cover support (below spring travel) |
| F | Inner arm panels (×2) | 18 ply, leaning with the arm | Birch ply EN 636-2 | Arm stiffness; seat-rail connection face |
| G | Arm ribs (3 per arm) | 18 ply ring, 70 wide | Birch ply | Gives the arm its D profile |
| H | Back base rail | 38 × 90 × 1540 | Beech | Back formers sit on it |
| H2 | Inner lower rail (continuous) | 28 × 28 laminated | Beech / stacked ply in corners | Webbing anchor; arm–back tie |
| I | Top rail (continuous U) | 28 × 28 laminated | Beech | Arm + back rim spine |
| J | Back formers (4) + corner formers (2) | 18 ply ring | Birch ply | Back profile and recline |
| K | Outer stringers ×3 + inner top stringer | 28 × 28 laminated | Beech | Hold the ribs in line; support the bending ply |
| L | Corner blocks (×4) | 60 × 60 triangle × 100 | Beech | Racking resistance of the seat box |
| M | Leg blocks (×4) + centre block | 45 thick | Beech | M8 inserts for the legs |
| N | Stretcher blocks (×4) | 40 × 40 triangle × 60 | Beech | Stretcher–rail joint reinforcement |
| — | Outer skin | 5 mm bending ply | Poplar | Continuous curved substrate for glued foam |

**Joinery** (collection `03_FRAME_JOINTS`):
- Ø10 × 40 fluted beech dowels, 2 per rail end, with PVAc D3 glue.
- M8 × 100 bolt with an M8 cross-dowel at each rail end, through side rail, panel and rail.
- Stretcher: 24 × 25 × 50 tenons into both rails.
- Cross members: Ø12 round tenons.
- Corner blocks: glued, plus 2 × 4.5 × 50 screws each.

### 3.2 Design loads [ASSUMED — verify against the purchased EN 12520:2024 text]

- Service: 3 adults × 100 kg crowded, or 2 × 110 kg, with a dynamic factor of 1.5 → **4400 N** on the seat.
- Static test-style loads: seat 1300 N, front edge 1300 N, back 450 N per seat position, arm downward 750 N, arm sideways 400 N.
- Material values:
  - Beech E = 14 000 MPa; allowable bending 15 MPa (MOR ≈ 100 ÷ 6.5).
  - Birch ply: allowable bending ≈ 20 MPa.
  - Steel: spring wire tensile strength ≈ 1600–1800 MPa.

### 3.3 Calculations [CALC]

Spans are clear spans between the inner arm panels: L = 1525, or 2 × 746 with the stretcher and centre foot. Simply supported spans give conservative results.

| Check | Load | Result | Verdict |
|---|---|---|---|
| Front rail, vertical, 1300 N point at mid-span (L 1525) | M = 495 625 N·mm; W = 91 200 mm³ | σ = 5.4 MPa; δ = 1.25 mm | ✅ SF ≈ 2.8 on the allowable |
| Front rail, vertical, 2200 N UDL (50 % of 4400) | — | σ = 4.7 MPa; δ = 1.4 mm | ✅ |
| Front rail, horizontal spring pull, **no stretcher** | 12 springs, ≈2350 N total [ASSUMED] | σ = 15.5 MPa; **δ = 14 mm inward bow** | ❌ Rejected |
| Same, **with centre stretcher** (2 × 746) | — | σ = 3.7 MPa; δ = 0.9 mm | ✅ |
| Rear rail 38 × 86, 2640 N UDL (60 % of 4400), **no centre support** | W = 46 840 mm³ | σ = 11 MPa; δ = 4.3 mm | ⚠ Marginal |
| Rear rail **with the centre foot under the stretcher–rear-rail junction** (set 1 mm clear, engages after 1 mm) | Continuous over the support | σ ≈ 2.6 MPa; δ ≤ 1 mm | ✅ The design change in Rev B moved the foot here |
| Leg bearing, 1400 N per front leg | Ø80 end grain | 0.28 MPa | ✅ Trivial |
| Leg racking, 10 % horizontal (140 N × 94 mm) | Bolt tension via a 40 mm bearing lever | ≈330 N on the M8 | ✅ Needs a flat, tight leg seat |
| Arm sideways 400 N at 640 high → arm–seat joint at 160 | M = 192 000 N·mm; couple across dowels 60 apart | ≈1600 N per rail-end joint (2 dowels + M8) | ✅ Margin ≈ 3 [TEST]. The U-shell continuity takes a large share, so this is conservative |
| Back 2 × 450 N at 650 | M = 414 000 N·mm shared by 4 back formers + 2 corner formers + arm rear ribs + continuous rails | ≈2 MPa in the ply rings | ✅ |

### 3.4 Load path

1. Occupant → cushion → sinuous springs → front and rear seat rails (≈45/55).
2. Rails → dowels, cross-dowel bolts and corner blocks → inner arm panels and side rails.
3. Side rails → leg blocks → M8 inserts → oak legs → felt glides → floor.
4. Rear-rail mid-span → stretcher → centre foot → floor.
5. Back loads → back formers → back base rail and rear rail → rear leg blocks.
6. Arm loads → ribs and inner panel → side rail and leg blocks. Racking is closed by the continuous U top rail.

The red and green arrows in `17_ENGINEERING_HELPERS` visualise these paths (render `12_load_paths`).

## 4. Suspension (Stage 5)

**Selected: sinuous (S-type) springs.** They are durable and low-cost, standard in workshops, suit a loose-cushion deck, and match the reference frame photo.

- Elastic webbing was rejected for the seat (creep and sag at this span) but **used for the back**: 50 mm elastic webbing, 10 vertical + 2 horizontal straps, about 10 % pre-tension.
- Pocket coils are an upgrade option. 8-way hand-tied was rejected (labour cost and deck height).

| Item | Spec |
|---|---|
| Springs | **12 × 8-gauge (Ø4.1 mm)** sinuous, 2 bays × 6 |
| Spacing | 116.8 mm centres (≈ industry 100–130 mm for seats); edge springs ≈ 45 mm from the inner arm face |
| Span | 560 mm clip to clip (y −311 → +249); the rear clip line is 34 mm lower → about 3.5° deck rake |
| Arc (crown) | 22 mm above the chord, installed |
| Clips | Nailed steel clips (2 nails) with a **plastic anti-squeak liner** between wire and steel |
| Ties | 3 rows of helical tie springs (Ø8 coil, 1.6 mm wire) between adjacent springs → load sharing, no twisting |
| Over the springs | Needle-punched felt insulator (≈300 g/m², 5 mm) → 20 mm HR30 deck pad → non-woven decking cloth |

**Deflection [ASSUMED → TEST].** One 100 kg adult puts about 735 N on the seat, shared by about 4–5 springs → 150–185 N per spring.
- With an assumed stiffness of about 6 N/mm per spring (typical published range for 8-ga at about 560 mm span), the deck deflects **≈ 25–30 mm**.
- That is inside the 25–40 mm target. Supplier load–deflection curves must replace this assumption.

**Spring pull on the rails [ASSUMED].** 150 N installed, rising to ≈400 N on loaded springs. A sinuous spring is not an inextensible cable, so cable formulas overestimate. A bench test with a load cell on a clip is in the test plan.

**Squeak prevention.**
- Lined clips, so no metal-to-metal contact.
- Insulator felt between springs and foam.
- Helical ties are coated, or sleeved where they cross the stretcher.
- The stretcher top is 37 mm below the spring line at mid-span, so springs never touch wood under load. The lower cross members are 50 mm high and stay below spring travel.

## 5. Cushions and padding (Stage 6)

Density (durability) and firmness (IFD 25 % / EN ISO 2439 hardness) are specified **separately**. Higher density does not mean firmer.

| Part | Build (outer → inner) | Foam spec [ASSUMED, confirm with supplier] |
|---|---|---|
| Seat cushion 175 | Bouclé cover (zip at the rear) → cotton ticking → 200 g/m² bonded polyester wrap (≈15 mm loft) → **25 mm comfort layer** → **114 mm core** | Comfort: HR 35 kg/m³, IFD25 ≈ 90–110 N (≈ 20–25 lbf). Core: HR 40 kg/m³, IFD25 ≈ 150–170 N (≈ 34–38 lbf), support factor ≥ 2.4 |
| Back cushion | Cover → compartmented ticking → siliconised hollow-fibre layer (≈22 mm) → **HR30 soft core** with a lumbar crown | HR 30 kg/m³, IFD25 ≈ 70–90 N |
| Arms and shell | Cover → 150 g/m² wadding → **22 mm soft foam** → **20 mm firm foam** glued to the 5 mm bending-ply skin | Soft: HR 30, IFD25 ≈ 80 N. Firm: HR 35, IFD25 ≈ 200 N |
| Front base band | Cover → firm foam block + Ø38 bullnose roll | HR 35 firm |

- **Loaded seat sink [CALC estimate]:** about 45–60 mm cushion + 25–30 mm deck → **loaded seat ≈ 380–390**. HR40 at 114 mm keeps the occupant well clear of the springs: about 40 % compression at the ischial peak, below the roughly 65–70 % where the support curve "bottoms".
- **Fire safety:** in the UK this means BS 5852 / the Furniture and Furnishings (Fire) (Safety) Regulations and CMHR foams. In the EU it means EN 1021-1/-2, plus national rules. **The target market must be confirmed;** it changes the foam grades and may require an FR interliner.

## 6. Legs (Stage 7)

- **Legs:** Ø80 × 94 solid oak, 6 mm edge round-over, M8 hanger bolt into an M8 threaded insert in a 45 mm beech leg block. The block is glued and screwed to the side rail and the outer base stringer.
- **Glides:** 5 mm felt, Ø64.
- **Centre foot:** height-adjustable black polymer, Ø40. It is set **1 mm clear of the floor**, so it cannot cause rocking on uneven floors and engages only under load.
- **Front legs:** inset 140 mm from the front face (centre) and 82 mm from the side.
- **Rear legs:** inset under the shell corner, hidden from the front.

## 7. Mass and stability (Stage 8)

**Mass [MODEL]**, from `scripts/mass_properties.py` using the evaluated Blender volumes × assumed densities:
- Total ≈ 69.0 kg.
- Breakdown: beech 29.4, birch ply 9.6, bouclé 5.8, bending ply 3.5, foams 11.9, fibre 2.1, steel 3.5, legs 1.3 kg.
- CoG at **(0, +54, 319)** mm, slightly rearward because of the shell.
- Full table: `docs/mass_report.csv`.

**Stability [CALC]** (W = 677 N):

| Case | Tipping line | Result |
|---|---|---|
| Forward: vertical load on the seat front edge (y = −385) | Front legs y = −310 | Tipping load = 677 × 364 / 75 ≈ **3 290 N** > 1300 N → SF 2.5 ✅ |
| Rearward, empty sofa, horizontal push at the 780 rim | Rear legs y = +290 | **≈ 205 N** (677 × 236 / 780); felt-glide friction ≈ 0.3 × 677 ≈ 203 N, so tipping and sliding are about equal ⚠ |
| Rearward with a seated occupant (600 N at y = −150) | — | ≈ 560 N ✅ |
| Sideways: 1300 N on the outer arm edge (x = 952) | Leg line x ≈ 860 | Tipping load ≈ 6 300 N ✅ |

**Recommendation:** move the rear legs 40 mm rearward (to y = +330, with a slimmer leg block) if the shell bottom allows. That raises the empty rear-tip force to ≈ 240 N. Rearward stability must be verified to EN 1022 with the purchased standard.

## 8. Weak points and engineering review (Stage 11)

| # | Risk | Status / mitigation |
|---|---|---|
| W1 | Front rail bows from spring pull | **Fixed:** centre stretcher |
| W2 | Rear rail sag (38 × 86 over 1525) | **Fixed:** centre foot moved under the stretcher–rear-rail junction |
| W3 | Arm pulled outward at the seat joint | Dowels + glue + M8 cross-dowel + corner block; the continuous U top rail closes the racking path. **[TEST]** arm sideways and fatigue |
| W4 | Ply rib ↔ stringer joints (glue line in end grain) | Specify notched (half-lap) rib seats + glue + 2 staples / 1 screw each |
| W5 | Spring clip nails pulling out of the 38 mm beech top | 2 ring-shank nails per clip, ≥ 25 mm penetration. **[TEST]** pull-out |
| W6 | Spring fatigue / set | 8-ga, ≤ 30 mm working deflection. Supplier certificate for 50 000 cycles |
| W7 | Squeaks | Liners, felt, coated ties, wood–metal clearances (§4) |
| W8 | Seat foam sag | HR40 core; ≤ 5 % height loss after the fatigue test is the target. **[TEST]** |
| W9 | Back cushion collapse | HR30 core + fibre shell; check after the back fatigue test |
| W10 | Bouclé pilling and loop snagging at the arm rims | Martindale ≥ 40 000; ≥ 4 on the pilling test (EN ISO 12945-2) |
| W11 | Rear tipping when empty (≈ equal to the sliding force) | Move the rear legs rearward; verify to EN 1022 |
| W12 | Model-only simplifications | See §11 |

## 9. FEA workflow (prepared, **not run**)

1. Export the frame collections (01–03) as STEP/STL from Blender, or rebuild the members parametrically in **FreeCAD**. Clean solids are needed, and FreeCAD's Part workbench is preferable to mesh STL.
2. Use the **FreeCAD FEM workbench with the CalculiX solver**, or Ansys / SolidWorks Simulation if available. Assign:
   - Orthotropic beech (E_L 14 000, E_R 2 300, E_T 1 100 MPa).
   - Birch ply (E ≈ 9 000 / 6 000 MPa).
3. Model the joints as bonded contacts, or with springs representing dowel stiffness (≈ 3–5 kN/mm per dowel pair) for a more realistic racking result.
4. Load cases from §3.2. Springs are applied as line loads at the clip lines, both vertical and horizontal components.
5. Supports: pin at the four leg centres; compression-only at the centre foot.
6. Outputs: rail stresses and deflections, ply-rib stress, joint forces. Compare with §3.3.

Blender rigid-body physics is **not** structural analysis. It is only suitable for demonstrating, for example, cushions dropping onto the deck.

## 10. Preliminary test plan (EN 12520:2024 with EN 1728 methods, EN 1022 stability)

Loads and cycles must be taken from the purchased standards. The values below are planning placeholders.

| Test (EN 1728 clause family) | Planning value | Pass criteria |
|---|---|---|
| Seat static | 1300 N × 10 | No fracture, no loosened joints, no permanent deformation affecting function |
| Seat front-edge static | 1300 N × 10 | Same; front rail and spring clips intact |
| Back static (with seat load) | 450–560 N | Same |
| Arm downward static | 750 N | Same |
| Arm sideways static | 400 N | Same; joint gap ≤ 0.5 mm |
| Seat + back fatigue | 50 000 / 25 000+ cycles | No breakage; foam height loss ≤ 5 %; no squeak |
| Arm fatigue | Per standard | Same |
| Seat impact | Per standard (drop mass) | No breakage |
| Leg forward / sideways static | Per standard | No loosening of the M8 inserts |
| Stability (EN 1022): forward, rearward, sideways | Per standard | No overturning |
| Additional: spring-clip pull-out, spring load–deflection, foam IFD / density certificates, fabric Martindale / pilling / seam slippage | Supplier and lab | Meets the spec |

## 11. Model limitations (honest list)

- **Cushions are modelled unloaded.** No soft-body compression simulation was run.
- **Some hidden overlaps exist where parts meet:** rail ends pass through the inner face of the arm cover below deck level, inside the base band; and the ply ribs and stringers overlap at their joints.
  - None is visible in the finished renders. They appear only in cut sections.
- **Joints are represented** (dowels, bolts, cross dowels, tenons, screws) but not machined into the mating parts. Rib–stringer notches are not cut in the mesh.
- **Fabric is a procedural shader** (Voronoi loops + noise + bump), not hair-particle teddy pile.
- **All structural numbers are hand calculations** from stated assumptions.
