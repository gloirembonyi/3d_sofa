# Caramel Shell 2S — parametric bouclé sofa (Blender 5.3)

A fully editable, manufacturable two-seat shell sofa recreated from `reference/reference_upholstered.jpg`. It includes the internal frame, suspension, layered padding, upholstery and documentation.

## Folder

```
sofa_vip/
  blend/sofa_caramel_shell.blend   editable scene (generated)
  scripts/sofa_build.py            builds the whole scene from scratch (parametric, P = {...} at top)
  scripts/render_views.py          renders presentation views, sections, exploded view, drawings
  scripts/mass_properties.py       mass + centre of gravity from the real geometry
  renders/                         Cycles images (01 hero ... 12 load paths); renders/preview = quick checks
  drawings/                        orthographic technical views (A-I) with dimensions
  docs/01_STAGE1_design_specification.md
  docs/02_ENGINEERING_REPORT.md    ergonomics, frame + spring calcs, stability, test plan, weak points
  docs/03_COMPONENT_SCHEDULE_AND_BOM.md
  docs/04_MANUFACTURING_GUIDE.md   23 workshop stages
  docs/05_QC_CHECKLIST.md
  docs/component_dump.csv          every object with its size (auto)
  docs/mass_report.csv             mass / CoG per part (auto)
  reference/                       your reference photo
```

## Rebuild / render

```powershell
$B = "C:\Program Files\Blender Foundation\Blender 5.3\blender.exe"
& $B -b --factory-startup -P scripts\sofa_build.py                      # build + save .blend
& $B -b blend\sofa_caramel_shell.blend -P scripts\render_views.py           # all Cycles views + drawings (~40 min CPU)
& $B -b blend\sofa_caramel_shell.blend -P scripts\render_views.py -- 01_hero  # one view
& $B -b blend\sofa_caramel_shell.blend -P scripts\render_views.py -- --quick  # fast Workbench previews
& $B -b blend\sofa_caramel_shell.blend -P scripts\mass_properties.py
```

## Using the .blend

- **Collections** `00_REFERENCE_IMAGES` … `18_DIMENSIONS_AND_LABELS` (+ `19_ENVIRONMENT`).
  - Hide `11_UPHOLSTERY` to see the foam, the foam collections to see the frame, and so on.
- **Exploded view:** select `SOFA_ROOT` → Object Properties → Custom Properties → `explode`.
  - 0 = assembled, 1 = exploded. Drivers move every part along its assembly direction.
- **Cameras:**
  - `CAM_01` … `CAM_11` for presentation.
  - `DRW_*` orthographic cameras for drawings.
- **Section cutters:** the `EH_CUTTER_*` boxes in `17_ENGINEERING_HELPERS`. Add a Boolean (Difference) modifier with a cutter to any layer to inspect it.
- **Units:** geometry lives in millimetres inside `SOFA_ROOT` (scale 0.001), so the scene is true size in metres and the display reads mm.
- **Changing a dimension:** edit `P` at the top of `scripts/sofa_build.py` and re-run. The shell profile, frame, cushions and dimension lines regenerate consistently.

## Status (honest)

- **Done:**
  - Geometry for the exterior, internal frame, joinery, springs, deck, layered foams, fibre, ticking, covers, legs and dust cover.
  - Procedural bouclé, wood and foam materials.
  - Interior scene, cameras, exploded view, sections and orthographic drawings.
  - Hand calculations, mass/CoG from the model, BOM, manufacturing guide and QC list.
- **Not done:** no FEA and no physical or lab tests. The workflow and test plan are in the report. Spring stiffness, spring pull and foam firmness are supplier or test inputs.
- **Model simplifications:** see `docs/02_ENGINEERING_REPORT.md` §11.
- **Tooling:** the Blender MCP server was not used. Everything runs headless through Blender's Python API, which keeps the build fully reproducible.

## 3D web configurator (`web/`)

A Next.js 15 + React Three Fiber (three.js) + drei site that loads the real Blender model:
- **Material:** bouclé, velvet, linen or leather (physically based, with fabric sheen).
- **Colours:** preset colours per material plus a custom colour picker.
- **Legs:** four leg finishes.
- **Scatter cushions:** on or off.
- **Backdrops:** four choices.
- **Camera:** drag to rotate, scroll or pinch to zoom, and six camera presets.
- **Overlays:** auto-rotate, dimensions overlay, **inside view** (the frame, springs and webbing through translucent upholstery), and numbered feature hotspots.
- **Sharing:** save a PNG, or copy a shareable link (the link query string stores the configuration).

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.3\blender.exe" -b blend\sofa_caramel_shell.blend -P scripts\export_web.py   # re-export GLBs + textures
cd web
npm install
npm run dev        # http://localhost:3000 while editing
npm run build      # static site in web/out (host on Netlify, Vercel, S3, any web server)
npm start          # serve web/out on http://localhost:3000
```

Link options: `?fabric=velvet&colour=1f5040&legs=Walnut&pillows=1&view=detail&xray=1&spin=0`
## Deploy on Vercel

The repo is ready to deploy as-is:

1. In Vercel, choose **Add New → Project** and import `gloirembonyi/3d_sofa`.
2. Leave every setting at its default and click **Deploy**.
   - The root `vercel.json` installs and builds the app in `web/` (`npm ci` then `npm run build`) and serves the static export from `web/out`.
   - `web/.npmrc` sets `legacy-peer-deps=true`, because `three-gpu-pathtracer` needs `three-mesh-bvh` 0.9 while drei pins 0.8; both versions install side by side.
3. Models, textures and the Draco decoder are served with long-term cache headers.

Alternative setup: set **Root Directory** to `web` in the Vercel project settings. Vercel then detects Next.js itself, and the root `vercel.json` is ignored.

Photoreal (path-traced) renders run on the visitor's own GPU in the browser, so nothing heavy runs on Vercel.