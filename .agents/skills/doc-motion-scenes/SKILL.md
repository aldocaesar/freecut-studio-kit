---
name: doc-motion-scenes
description: Design and render bespoke, one-of-a-kind 30fps HTML/CSS/SVG/Canvas2D/GIS motion graphics clips for FreeCut (v8.0). Zero canned slide templates or fixed palettes — every MOTION_SCENE is creatively invented from scratch by the LLM to embody the spoken metaphor, genre, and style_dna of the current video.
---

# Bespoke Creative LLM Motion Graphics (`doc-motion-scenes` v8.0)

Use `MOTION_SCENE` (`motion/<scene_id>.html` -> `motion/<scene_id>.mp4`) whenever the narration presents a **mechanism, physical/visual metaphor, spatial transformation, contrast, timeline, quantitative jump, or geographic route** that custom vector/canvas choreography expresses better than stock B-roll.

## 1. Core Philosophy: Zero Canned Widgets — Invent the Scene Around the Metaphor!

**Canned slide renderers (`renderUIFeed3D`, `renderDossierDesk`, `renderOdometerCounter`, `renderVersusSplit`, `renderWaffleScale`, `renderCameraJourney`, `renderNetworkGraph`, `renderDataCurve`, `renderKineticManifesto`) and fixed `PALETTES` do NOT exist (`validate_freecut.py` hard-fails if any deprecated widget name or cloned HTML skeleton is used!).**

Instead, for every `MOTION_SCENE`:
1. **Start from the exact physical or narrative metaphor of the spoken sentence:**
   - Talking about a loud 6:00 AM alarm shaking a neighborhood? Illustrate & animate architectural courtyard windows rattling on `MotionKit.spring(...)` shockwaves with expanding sound rings!
   - Talking about an absurd luxury perfume made of ham? Draw a custom SVG glass flacon spraying golden bezier vapor trails (`MotionKit.strokeProgress` + `MotionKit.pointOnPath`) toward its target!
   - Talking about compounding debt, servers overloading, cells dividing, historic treaties, or arcade power-ups? Build the **actual visual object, diagram, instrument, or stage** in crisp SVG / Canvas2D / CSS 3D — never a generic 2-column dark dashboard card!
2. **Inherit 100% of Colors & Typography from `storyboard.json -> style_dna`:**
   - Load the project's exact Google Fonts (`font_display`, `font_serif`, `font_body`, `font_mono`) via `<link rel="stylesheet" href="https://fonts.googleapis.com/css2?...">`.
   - Alternate light, vivid, pastel, warm, or deep backgrounds derived from `style_dna` (`paper_bg`, `studio_bg`, `accent`, `accent_secondary`) so consecutive motion scenes within the same video feel cohesive yet visually distinct — and two different videos NEVER look alike!
3. **Never Clone Structure Within or Across Videos:**
   - `validate_freecut.py` computes pairwise structural AST/DOM similarity across `motion/*.html` and **FAILS** if two scenes share `> 84%` structural skeleton. Give each motion scene its own spatial composition (radial, diagonal, isometric, split-stage, full-bleed SVG illustration, Canvas particle field, instrument dial, architectural elevation, or Natural Earth map).
   - Keep `media/cutouts/*.png` inside `motion/*.html` to **at most 25% of motion scenes** (prefer pure illustrated vector/canvas/typography craft).

---

## 2. Deterministic Frame Contract & `MotionKit` v8.0 Primitives

Every `motion/<ID>.html` file is rendered frame-by-frame at `30fps` in headless Chromium via `window.__setFrame(frameIdx, fps)`.

- **NEVER** rely on wall-clock `requestAnimationFrame`, `setInterval`, or unpaused CSS `@keyframes` — compute 100% of transforms, SVG attributes, and canvas draws deterministically from `const t = frameIdx / fps;`.
- Include `<script src="<ABS_OR_REL_PATH_TO>/kit/motion-kit.js"></script>` (plus `kit/world-atlas.js` **only** when rendering real geographic country maps).

### Available Pure Primitives in `window.MotionKit`
- **Math & Easing:** `clamp01(v)`, `clamp(v, min, max)`, `lerp(a, b, t)`, `remap(v, in0, in1, out0, out1)`, `easeOutQuint(t)`, `easeInOutCubic(t)`, `easeInOutSine(t)`, `easeOutExpo(t)`, `easeOutBack(t, overshoot)`
- **Deterministic Physics & Choreography:**
  - `MotionKit.spring(t - startSec, { stiffness: 180, damping: 18, mass: 1 })` — physical spring with natural settle/bounce
  - `MotionKit.progress(t, startSec, durSec, easeFn)` — normalized `[0..1]` window
  - `MotionKit.stagger(t, index, baseStart, stepSec, durSec, easeFn)` — staggered element entrances
  - `MotionKit.oscillate(t, freqHz, amplitude, phaseRad)` — continuous harmonic motion
  - `MotionKit.hashNoise(seed)` — deterministic `[0..1)` pseudo-random number for particles/textures
- **SVG, Camera & Framing:**
  - `MotionKit.strokeProgress(svgPathEl, p)` — progressive line/curve drawing (`0..1`)
  - `MotionKit.pointOnPath(svgPathEl, p)` — returns `{ x, y, angle }` along any `<path>` for moving icons, particles, or labels along curves!
  - `MotionKit.rostrumTransform(t, DURATION, { scaleFrom: 0.97, scaleTo: 1.04, xFrom: -12, xTo: 12 })` — continuous 2.5D camera glide
  - `MotionKit.safeZone(width, height)` & `MotionKit.injectFilmGrain(0.035)` & `MotionKit.svgEl(tag, attrs, parent)`
- **Real 242-Country Cartography (ONLY when a real geographic map is needed):**
  - `MotionKit.renderWorldAtlas(svgEl, { projection: 'naturalEarth' | 'orthographic' | 'mercator', center, fitBounds, oceanFill, landFill, accent, focusCountries, routes, pins })` — never hand-draw country polygons!

---

## 3. Mandatory 3-Act Choreography & Live Tail (`78% -> 94%` Never Frozen!)

`render_motion_scene.py` samples every scene at **`20%`, `50%`, `78%`, and `94%`** and checks pixel delta between `78%` and `94%`:
1. **Act I (`0%–25%`):** Stage architecture enters with staggered `spring()` / `easeOutBack()` / `strokeProgress()`.
2. **Act II (`25%–75%`):** Primary visual transformation, counter/gauge climb, path traversal (`pointOnPath`), collision, or reveal synced to the spoken beat.
3. **Act III (`75%–100%` — Mandatory Live Tail):** Keep continuous `t`-driven motion running until the very last frame (`rostrumTransform` camera glide + `oscillate(t, ...)` floating badges/particles/waves/ripples/dials) so the clip never freezes before the cut!

See [references/motion_examples.md](references/motion_examples.md) for minimal structural patterns (SVG path physics, Canvas2D + SVG hybrids, kinetic instruments, and GIS maps).

---

## 4. Parallel Render & Isolated Visual QA

Render all motion scenes in parallel (`3` workers) + build `motion/motion_contact_sheet.jpg`:
```bash
python -B "<SKILL_DIR>/scripts/render_motion_scene.py" --project-dir "<PROJECT_DIR>" --workers 3
```
*(Or run `finish_freecut.py --project-dir "<PROJECT_DIR>"` to chain Lottie + Motion + Assembly + Validation in one command.)*

**Strict Context Rule:** Never open `motion/motion_contact_sheet*.jpg` in the main agent context — delegate visual inspection to an isolated subagent (`invoke_subagent`) checking legibility, clipping, metaphor clarity, and live motion across `20% / 50% / 78% / 94%`.
