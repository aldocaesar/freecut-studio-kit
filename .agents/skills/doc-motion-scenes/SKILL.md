---
name: doc-motion-scenes
description: Builds bespoke, human-grade 30fps Motion Graphics scenes (15%-25% of video) across 16:9, 9:16, 4:5, and 1:1 with REAL Natural Earth offline GeoJSON cartography (world-atlas.js + MotionKit.renderWorldAtlas), MapLibre street-level vector maps, monotone data curves (MotionKit.renderDataCurve), transparent rembg entity cutouts, 2.5D rostrum camera moves, and optical film grain.
---

# Documentary & Editorial Motion Scenes (`doc-motion-scenes` v6.3)

Creates **15% to 25%** of the video's runtime as bespoke, deterministic 30fps H.264 clips (`<project_dir>/motion/SXX.mp4`) placed on FreeCut's `track_anchor`.

Read `<SKILL_DIR>/references/motion_examples.md` before coding any scene for ready-to-adapt templates (`MotionKit.renderWorldAtlas`, `MotionKit.renderDataCurve`, and layout patterns).

---

## Hard Anti-Slop Rules
1. **NEVER hand-type fake SVG polygon continents** (`<path d="M 380,340 L ...">`). `validate_freecut.py` will **FAIL** the build! Always load `<SKILL_DIR>/kit/world-atlas.js` + `<SKILL_DIR>/kit/motion-kit.js` and call `MotionKit.renderWorldAtlas(...)` (offline 242-country Natural Earth GeoJSON + true spherical great-circle routes, `naturalEarth` or `orthographic` 3D globe) or `maplibre-gl` (`https://tiles.openfreemap.org/styles/liberty`).
2. **NEVER build "floating card on left + 2 simple bars on right"**: Stage transparent RGBA cutouts (`../media/cutouts/S02_cutout.png`), progressive monotone curves (`MotionKit.renderDataCurve`), or editorial timelines across the full canvas.
3. **MANDATORY SHARED CUTOUT RULE**: Motion scenes (`motion/SXX.html`) must import the **exact verified cutout already approved on the timeline (`../media/cutouts/{sid}_cutout.png`)** — never embed separate unverified web URLs or mismatched product variants.
4. **DATA CURVE COLLISION GUARD (`rightSafeX` + `callout`)**: Whenever placing a person or product cutout on the right side, pass `rightSafeX: 1020` (keeping `plotBox` left of the subject) and add `callout` badges on key milestones so X-axis labels never hide behind shoulders.
5. **ALWAYS inspect `motion/SXX_preview.jpg` with Vision** after rendering to verify zero text clipping, zero line-over-label collisions, and crisp visual hierarchy.

---

## Scene Contract & Rendering CLI

1. Every `<project_dir>/motion/SXX.html` must expose deterministic frame stepping via `window.__setFrame = function(frameIdx, fps)` so frames render identically at 30fps regardless of CPU speed.
2. Load both bundled scripts (`kit/world-atlas.js` and `kit/motion-kit.js`) via relative path from `<SKILL_DIR>/kit/`.
3. Render all `MOTION_SCENE` entries in `storyboard.json` (auto-detecting `16:9`, `9:16`, `4:5`, or `1:1` dimensions):

```bash
python "<SKILL_DIR>/scripts/render_motion_scene.py" --project-dir "<project_dir>"
```
*(On macOS/Linux where only `python3` is on PATH, run with `python3`.)*

4. Visually inspect every generated `<project_dir>/motion/SXX_preview.jpg` with Vision before running `assemble_freecut.py`.
