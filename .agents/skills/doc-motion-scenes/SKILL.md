---
name: "doc-motion-scenes"
description: "Builds bespoke 30fps Motion Graphics scenes (15%-25% of video, v7.0) with 10 distinct MotionKit engines, 8 light and dark editorial palettes, 4-frame dead-tail detection (20/50/78/94%), offline 242-country GeoJSON maps, and parallel ThreadPoolExecutor rendering."
---

# Documentary & Editorial Motion Scenes (`doc-motion-scenes` v7.0)

Creates **15% to 25%** of the video's runtime as bespoke, deterministic 30fps H.264 clips (`<project_dir>/motion/SXX.mp4`) placed on FreeCut's `track_anchor`.

Read `<SKILL_DIR>/references/motion_examples.md` once for copy-ready patterns of all **10 `MotionKit` v7.0 engines** and **8 chapter palettes** (never `read_file` `.py`/`.js` kit source files!).

---

## Hard v7.0 Anti-Cloning, Palette Diversity & Live-Tail Rules
1. **10 DISTINCT ENGINES (Zero Consecutive Clones!)**: Rotate across `MotionKit.renderWorldAtlas` (`naturalEarth` map), `MotionKit.renderWorldAtlas` (`orthographic` 3D rotating globe), `MotionKit.renderCameraJourney` (Vox 2.5D spatial desk), `MotionKit.renderDataCurve` (`followTip` camera curve), `MotionKit.renderOdometerCounter` (mechanical rolling digits + contrast bar), `MotionKit.renderUIFeed3D` (3D tilted glass phone + live story bars + floating notifications), `MotionKit.renderDossierDesk` (overhead paper dossier + red rubber stamp slam), `MotionKit.renderNetworkGraph` (directed cash-flow conduits with streaming packets), `MotionKit.renderVersusSplit` (diagonal razor split), and `MotionKit.renderWaffleScale` (100-block proportional matrix).
2. **8 EDITORIAL CHAPTER PALETTES (`>= 50%` Light / Warm / Colored!)**: Never default every scene to `#080C14` dark navy! Rotate `MotionKit.PALETTES` — `warm_archive_paper`, `editorial_blush_ivory`, `swiss_emerald_ivory`, `newsprint_crimson_ink`, `terracotta_ochre_sand`, `cobalt_blueprint`, `plum_velvet_editorial`, and `charcoal_gold_ledger`.
3. **CAP CUTOUTS IN MOTION AT `<= 20%`**: Do NOT paste a right-side `#subject` cutout onto every motion scene (`validate_freecut.py` v7.0 fails if `> 25%` of motions contain cutouts!). Let the 3D UI, map, camera journey, dossier desk, or odometer be the visual protagonist.
4. **CONTINUOUS ANIMATION TO `100%` (`78% -> 94%` Live-Tail Check)**: Pass `time` (`frameIdx / fps`) and `duration` into every `MotionKit` engine so camera drift, particles, story bars, or globe rotation stay alive until the final frame (`render_motion_scene.py` flags static tails!).
5. **REAL GEODESIC MAPS ONLY & SUBAGENT QA**: Always load `kit/world-atlas.js` + `kit/motion-kit.js` (relative path `../../../.agents/skills/doc-motion-scenes/kit/` from `projects/<slug>/motion/SXX.html`). Delegate inspection of the 4-column `motion/motion_contact_sheet.jpg` (`20% / 50% / 78% / 94%`) to an isolated subagent (`invoke_subagent`).

---

## Scene Contract & Parallel Rendering CLI
Every `<project_dir>/motion/SXX.html` must define `window.__setFrame = function(frameIdx, fps)`. Run via `finish_freecut.py --project-dir "<project_dir>" --force-motion` or standalone:

```bash
python -B "<SKILL_DIR>/scripts/render_motion_scene.py" --project-dir "<project_dir>" --workers 3 --force
```
