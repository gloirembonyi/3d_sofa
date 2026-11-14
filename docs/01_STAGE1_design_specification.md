# STAGE 1 — Reference Analysis & Design Specification

Project: two-seat sculptural bouclé sofa (working name **"Caramel Shell 2S"**)
Units: millimetres. Revision: S1-A, 2026-11-14.
> **Superseded in part by Rev B.** The exterior was re-proportioned to match the reference: arm 245 tapered, 1410 between arms, 150 mm round arm noses, cushions 701 wide, effective seat depth about 530. See `02_ENGINEERING_REPORT.md` §1 for the current values.

Status: **Design proposal.** Every number below is a design target or a hand calculation. Nothing here has been simulated or physically tested yet.

---

## 1. What the reference image shows

Only **one** image was received (the finished, upholstered sofa). The exposed-frame image mentioned in the brief was not attached. Section 7 lists what changes if it arrives.

### 1.1 Form reading

| Feature | Observation | Design consequence |
|---|---|---|
| Overall form | Arms and back read as **one continuous wrap-around shell** (a tub). The rim runs from the back around the corners and down each arm. | Build the shell as one frame: back formers, curved corner formers and arm ribs joined into a single skeleton. Do not make it as a box with separate arm blocks. |
| Arm top line | Perspective shows the rim **sloping down toward the front**. It is highest where it meets the back and lowest at the arm front. | Arm height is **640 at the front, rising to about 760** at the back junction. The brief's 620 is a little low for this silhouette. |
| Arm front | Large **D-shaped** face. The inner side is near-vertical, the outer side bulges out, and the bottom edge rolls under. | Arm cross-section is a constant D profile, built from CNC plywood ribs with a bent skin on the outer curve. |
| Arm width | About 1/4 of the sofa width at the base, slightly narrower at the rim. | 240 at the base and 215 at the rim. The average is close to the brief's 230. |
| Back | **Two pillow-like back sections** separated by a deep vertical split. Their tops sit just under the shell rim. | Two **loose back cushions** on hook-and-loop tabs, set inside a padded shell. They are easy to service and can be re-plumped. |
| Seat | **Two thick loose seat cushions** with rounded edges, a soft crown and no boxing welt visible. The seam is rolled or hidden. | Cushions about 170 thick with a waterfall or rolled front and a hidden side seam. |
| Base | A **rounded upholstered plinth band** (bullnose) runs under the cushions between the arms. About 100 of it is visible, and it is roughly flush with the arm fronts. | An upholstered front seat rail with a bullnose foam roll. The lower edge tucks under so the band reads slim. |
| Legs | **4 short, chunky, cylindrical light-oak legs**, set under the arms and inset from the corners. | Ø80 × 95 solid oak + 5 mm glide. The frame underside is at 100. |
| Fabric | Warm caramel/cognac **teddy bouclé** with dense, irregular looped pile and a matte look. | Procedural fabric shader (Voronoi + noise loops + displacement or bump), with the pile scale about 2–4 mm. |
| Ground clearance | The shell bottom nearly touches the leg tops. The sofa sits low and heavy. | Frame underside at 100 and the upholstery bottom roll at about 105. |

### 1.2 Things the image cannot tell us (assumptions)

- **Exact proportions.** It is a single perspective photo, so the dimensions below come from ratios combined with the brief's targets.
- **Whether the seat cushion sits on a sprung deck or a solid platform.** I assume a sprung deck, per the brief.
- **Fixed or knock-down (KD) arms.** I assume a fully glued frame, which is stiffer. A KD variant is noted as an option.
- **Rear view.** I assume a fully upholstered, finished back, with the shell continuous all round.

---

## 2. Proposed overall dimensions (S1-A)

Coordinate system for Blender: **X** is width (centred on 0), **−Y** is the front of the sofa, **Z** is up, and the floor is at Z = 0.

| Parameter | Brief | **Proposed** | Reason |
|---|---|---|---|
| Overall width | 1900 | **1900** | Kept. It gives a generous 2-seater. |
| Overall depth | 900 | **900** | Kept. |
| Overall height (back rim) | 780 | **780** | Kept. |
| Seat height, cushion crown, unloaded | 440 | **440** | Kept. Expected loaded height is about 390–400. |
| Effective seat depth (front edge to back-cushion face) | 560 | **540** | Lounge-style depth with the back cushion in place. Section 4 covers the user range. |
| Clear width between arms | 1450 | **1440** | 1900 − 2 × 230 (mean arm width). |
| Arm height at front | 620 | **640** | Matches the reference's sloping rim. That puts the arm about 245 above the loaded seat, which is still within the elbow-rest range. |
| Arm height at back junction | — | **760** | Gives the continuous shell rim. |
| Arm width | 230 | **240 base / 215 rim** | Gives the D-profile bulge. |
| Leg height (to frame) | 100 | **95 leg + 5 glide = 100** | Kept. |
| Leg diameter | — | **Ø80** | Matches the chunky reference legs. |
| Seat cushions | 2 | **2 × 725 W × 590 D × 170 T** | 2 × 725 = 1450 into a 1440 well. The 10 mm interference gives a snug, crowned fit. |
| Back cushions | 2 | **2 × 720 W × 480 H × 180→140 T** | Tapered, with the thickest part at the lumbar zone. |
| Seat deck height (top of padded springs, front) | — | **270** | 270 + 170 cushion = 440. |
| Seat rake | — | **3° back** | Pelvis settles back and the cushion does not slide forward. The rear deck sits about 34 lower. |
| Seat-to-back angle | — | **≈105°** | Relaxed upright posture for conversation and TV. |

### 2.1 Vertical stack at the seat front (unloaded)

```
 440  ── seat cushion crown
       170  seat cushion (fibre wrap + comfort layer + HR core)
 270  ── deck surface
        20  deck foam pad + insulator felt + decking fabric
 250  ── sinuous spring crown (arc ~30 above clip line)
 220  ── top of front seat rail (38 × 120 beech)
 100  ── frame underside
   0  ── floor (95 oak leg + 5 glide)
```

### 2.2 Depth stack at seat level (front → back)

```
Y=0     arm front / bullnose front face
0–20    bullnose padding + fabric
20–58   front seat rail (38 thick)
20–560  effective seat depth (540)
560–740 back cushion (180 thick at lumbar)
740–900 back shell: soft foam, firm foam, 18 ply former, outer foam, fabric (≈160)
```

---

## 3. Proposed engineering solution (summary; full detail in Stage 3)

### 3.1 Frame concept: hybrid hardwood + birch plywood

| Zone | Material | Section (finished) | Role |
|---|---|---|---|
| Front seat rail | KD beech, 8–12 % MC | 38 × 120 | Main seat beam. Anchors the front spring clips. |
| Rear seat rail | KD beech | 38 × 120 | Rear spring anchor and back-frame base. |
| Centre seat stretcher (front→back) | KD beech | 32 × 70 | **Strut against spring pull** and mount for the hidden centre support. |
| Arm frames (×2) | 18 mm birch plywood (EN 636-2) ribs: front D-former, mid rib, rear rib | 18 ply + beech 25 × 45 stringers | Shaped arm skeleton. The inner arm panel is solid 18 ply and carries the seat rails. |
| Arm outer skin | 5 mm bending plywood (poplar) | 5 | Continuous curved surface that the foam is glued to. |
| Back formers (×4) | 18 mm birch ply, side profile with recline + rounded top | 18 | Give the back its shape and recline. |
| Back rails | Beech top rail 32 × 70; bottom rail 32 × 90 | — | Tie the back formers together and anchor the back webbing. |
| Shell corners (×2) | Stacked/laminated CNC ply blocks + bending ply skin | 2 × 18 | Continuous radius from back into arm. |
| Leg blocks (×4 + 1 centre) | Beech | 45 × 120 × 120 | M8 threaded insert for each leg. |
| Corner blocks | Beech, glued + 2 screws each | 45 × 45 triangular | Rack resistance at every seat-box corner. |

Joinery: Ø10 × 40 fluted beech dowels + PVAc D3 glue (EN 204 D3) on all rail-to-panel joints, mortise-and-tenon at the stretcher, glued and screwed corner blocks, and an M8 bolt + cross-dowel at the rail-to-arm joints for extra pull-out strength.

### 3.2 Key finding from preliminary calcs: the front rail needs a centre strut

Sinuous springs pull the front and rear rails **toward each other** horizontally, and the pull rises when someone sits. Across a 1440 clear span that load acts on the rail's weak axis.

Assumptions: beech E = 14 000 MPa; allowable bending ≈ 15 MPa (MOR ≈ 100 MPa ÷ ~6.5 for defects, duration and variability); 12 springs with an estimated 150 N installed pull each plus 250 N extra on the 4 loaded springs, giving about 2350 N spread along the rail. **The spring-pull figure is an estimate and must be replaced with supplier data.**

| Case (front rail 38 × 120 beech) | Bending stress | Deflection |
|---|---|---|
| Spring pull, weak axis, **no centre strut** (L = 1440) | 14.6 MPa (≈ allowable) | **11.9 mm inward bow** ✗ |
| Spring pull, weak axis, **with centre stretcher** (2 × L ≈ 704) | 3.5 MPa | 0.7 mm ✓ |
| EN-style 1300 N point load at mid-span, vertical, no strut | 5.1 MPa | 1.1 mm ✓ |

**Decision:** add the 32 × 70 centre front-to-back stretcher, plus a **hidden adjustable centre support foot** under it. The foot is set about 1 mm off the floor so it cannot cause rocking, and it engages under load.

### 3.3 Suspension: sinuous (S-type) springs, confirmed

| Option | Verdict |
|---|---|
| **Sinuous springs** | ✅ **Selected.** Durable and cheap, suits a loose-cushion deck, a standard workshop skill, and the reference shows them. |
| Elastic webbing (seat) | ✗ Sags over time under a 170 mm cushion at this span. Used **for the back** instead. |
| Pocket coils | Possible premium upgrade, but needs a solid deck board and adds height. |
| 8-way hand-tied | ✗ Too labour-intensive and too tall for this low-profile deck. |

Preliminary spec:
- **12 springs, 8-gauge (Ø4.1 mm)**, 2 bays × 6 springs at about 117 mm centres.
- Clear span front rail → rear rail is about 640 mm. 8-gauge suits roughly 560–660 mm spans.
- Arc height about 30 mm. Target deflection 25–40 mm under one seated adult. **This needs supplier load–deflection data or a test.**
- Each spring is fixed by a **nailed clip with a plastic anti-squeak liner** at the front and rear rails.
- **3 rows of helical tie springs** link the springs across the width so they share load and do not twist.
- Over the springs: a spring insulator (needle-punched felt, about 300 g/m²), then a 20 mm deck foam pad, then non-woven decking fabric.
- Back suspension: **50 mm elastic webbing** at about 10 % pre-tension, vertical straps at about 90 mm centres, plus 2 horizontal straps.

### 3.4 Cushion and padding concept (detail in Stage 6)

| Part | Build-up (outer → inner) |
|---|---|
| Seat cushion (170) | Bouclé cover → ticking → 200 g/m² bonded polyester wrap → **25 mm HR comfort layer (≈35 kg/m³, soft)** → **120 mm HR core (≈40 kg/m³, medium-firm)** → wrap underside |
| Back cushion | Cover → compartmented ticking with siliconised hollow fibre (top third) → **HR 30 kg/m³ soft core** with a lumbar crown |
| Arms and shell | Cover → 150 g/m² wadding → **20–25 mm soft foam** → **30–40 mm firm foam** → bending ply / ply former |
| Bullnose base | Cover → wadding → firm 35 kg/m³ roll |

Density and firmness are specified **separately**: density in kg/m³ for durability, and firmness as IFD 25 % or EN ISO 2439 hardness for feel. Final firmness values are set in Stage 6.

### 3.5 Preliminary mass and stability (to be refined in Stage 3 / 11)

- **Estimated sofa mass: 55–65 kg** (frame ~28, foam and fibre ~18, fabric ~7, springs ~3, legs ~1.5, misc ~3).
- **Rearward tip, empty sofa, push at the 780 rim:** about 270 N needed. Felt glides slide at roughly 180 N first, so the sofa slides before it tips. ✓
- **Forward tip, 1300 N on the front edge:** about 3800 N would be needed. ✓ This depends on keeping the front legs at **≤100 mm inset**.
- **Leg load:** about 1500 N each under design load, which is 0.3 MPa bearing on Ø80. Trivial. The critical detail is a **flat, tight end-grain seat and the M8 insert in the 45 mm beech block**.

### 3.6 Design load basis (assumed; to be verified against EN 12520:2024)

Values are typical of domestic seating test regimes. **I do not have the 2024 standard's text, so every load here must be checked against the purchased standard.**

- Design users: 3 adults × 100 kg crowded, or 2 × 110 kg, with a dynamic factor of 1.5 for dropping into the seat.
- Seat static about 1300 N, front-edge static about 1300 N, back static about 450–560 N, arm downward about 750 N, arm sideways about 400 N.
- Fatigue: seat and back cycling of 50 000 / 25 000+ order.

---

## 4. Intended user range (summary; detailed in Stage 2)

- Designed for about **5th-percentile female (≈155 cm) to 95th-percentile male (≈190 cm)**.
- At a 540 effective depth, a 95th-percentile male (buttock-to-knee ≈ 620, buttock-to-popliteal ≈ 550) gets full thigh support.
- Smaller users sink into the soft back cushion, which reduces their effective depth to about 480–500. A scatter cushion is the conventional answer for very short users. This is a deliberate lounge-style trade-off that matches the reference.

---

## 5. Blender build plan

- Blender **5.3** is installed at `C:\Program Files\Blender Foundation\Blender 5.3`. The scene will be generated headless (`blender -b -P sofa_build.py`), so it can be reproduced from scratch and rendered without the UI.
- Collections `00_REFERENCE_IMAGES` … `18_DIMENSIONS_AND_LABELS` as specified.
- One parametric `PARAMS` dictionary at the top of the script holds every dimension in this document. Changing a value rebuilds the whole sofa consistently.
- Planned project layout:
  ```
  sofa_vip/
    docs/       stage reports, calcs, BOM, manufacturing guide, QC checklist
    scripts/    sofa_build.py (+ modules)
    blend/      sofa_caramel_shell.blend
    renders/    hero, views, close-ups, exploded, cutaway
    drawings/   orthographic + section views with dimensions
    reference/  your reference image(s)
  ```

---

## 6. Risks identified at Stage 1

| # | Risk | Mitigation (stage) |
|---|---|---|
| R1 | Front rail bows inward from spring pull | Centre stretcher + centre support (S3) ✓ planned |
| R2 | Arm torn outward when someone leans or sits on it | Dowel + glue + M8 cross-dowel bolts, inner arm ply panel, and a corner block at each arm-to-rail joint (S3) |
| R3 | Back shell racks or loosens at the corners | Laminated corner formers and a continuous top rail (S3) |
| R4 | Spring clips squeak | Plastic-lined clips, insulator felt, helical ties, and no metal-to-metal contact (S5) |
| R5 | Seat cushion foam sags or bottoms out | HR ≥ 40 kg/m³ core, 120 mm core thickness, and a deflection check (S6) |
| R6 | Bouclé pills or wears at the arm rims and front edge | Martindale ≥ 40 000 spec and a tight, wadded rim (S7) |
| R7 | Spring-pull and deflection figures are estimates | Replace with supplier data and a physical deck test (S11) |

---

## 7. Open points needing your input (do not block Stage 2)

1. **Exposed-frame reference image.** Please share its file path. I will compare it with the frame proposed here and say where I would follow it and where I would deviate.
2. **Target market and regulations.** Fire safety rules differ by country (UK furniture regulations / BS 5852 and EN 1021, for example). They change the foam spec (for instance CMHR) and the interliner, so please confirm where the sofa will be sold.
3. **Fixed frame vs knock-down arms.** The default is a fully glued frame. A KD variant adds bolt-on arms for flat shipping.

---

**Stage 1 check:**
- Dimensions are internally consistent: 1900 = 1440 + 2 × 230 and 440 = 270 + 170.
- Every structural member listed has a purpose.
- One structural risk (R1) has already been designed out.
- No Blender geometry yet, which is expected at this stage.
