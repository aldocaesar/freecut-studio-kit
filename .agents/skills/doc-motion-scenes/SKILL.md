---
name: "doc-motion-scenes"
description: "Builds bespoke 30fps Motion Graphics scenes (15%-25% of video) across 16:9, 9:16, 4:5, and 1:1 with parallel ThreadPoolExecutor(max_workers=3) rendering, automatic motion_contact_sheet.jpg grids, offline 242-country GeoJSON maps, and monotone data curves."
---

# Documentary & Editorial Motion Scenes (`doc-motion-scenes` v6.4)

Creates **15% to 25%** of the video's runtime as bespoke, deterministic 30fps H.264 clips (`<project_dir>/motion/SXX.mp4`) placed on FreeCut's `track_anchor`.

Consult `<SKILL_DIR>/references/motion_examples.md` once for ready-to-adapt `MotionKit.renderWorldAtlas` and `MotionKit.renderDataCurve` patterns (never `read_file` `.py`/`.js` kit source files!).

---

## Hard Anti-Slop & Context-Isolation Rules
1. **NEVER hand-type fake SVG polygon continents**: `validate_freecut.py` will **FAIL** the build! Load `kit/world-atlas.js` + `kit/motion-kit.js` (relative path from `<SKILL_DIR>/kit/`) and call `MotionKit.renderWorldAtlas(...)` (offline 242-country Natural Earth GeoJSON + spherical great-circle routes, `naturalEarth` or `orthographic` 3D globe) or `maplibre-gl`.
2. **MANDATORY SHARED CUTOUT + SAFE CHART MARGINS**: Import verified cutouts (`../media/cutouts/<sid>_cutout.png`) and pass `rightSafeX: 1020` + `callout` badges on `MotionKit.renderDataCurve` whenever placing a portrait/product on the right so X-axis labels never collide.
3. **SUBAGENT MOTION QA (`motion/motion_contact_sheet.jpg`)**:
   - `render_motion_scene.py` renders in parallel (`ThreadPoolExecutor(max_workers=3)`, incremental cache skip for unchanged HTMLs) and auto-generates `motion/motion_contact_sheet.jpg` (`20% / 55% / 85%` frames per scene).
   - **Never** open `motion_contact_sheet*.jpg` or `SXX_preview.jpg` in the main conversation! Delegate visual inspection of `motion/motion_contact_sheet*.jpg` to an isolated subagent (`invoke_subagent` / `Task`) that returns only compact text!

---

## Scene Contract & Parallel Rendering CLI
1. Every `<project_dir>/motion/SXX.html` must define `window.__setFrame = function(frameIdx, fps)` for deterministic 30fps capture.
2. Prefer running `finish_freecut.py --project-dir "<project_dir>"` (which runs Lottie + parallel Motion render + Assembly + Validation together), or run standalone:

```bash
python "<SKILL_DIR>/scripts/render_motion_scene.py" --project-dir "<project_dir>" --workers 3
```
