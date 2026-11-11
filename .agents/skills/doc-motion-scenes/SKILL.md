---
name: doc-motion-scenes
description: Builds bespoke, human-grade 30fps Motion Graphics scenes (`15%–25%` of video) across any aspect ratio (`16:9`, `9:16`, `4:5`, `1:1`) with REAL Natural Earth offline GeoJSON cartography (`world-atlas.js` + `MotionKit.renderWorldAtlas`), MapLibre street-level vector maps, monotone data curves (`MotionKit.renderDataCurve`), transparent `rembg` entity cutouts, 2.5D rostrum camera moves, and optical film grain.
---

# Documentary & Editorial Motion Scenes (`doc-motion-scenes` v6)

Creates **15% to 25%** of the video's runtime as bespoke, deterministic 30fps H.264 clips (`<project_dir>/motion/SXX.mp4`) placed on FreeCut's `track_anchor`.

## Hard Anti-Slop Rules
1. **NEVER hand-type fake SVG polygon continents** (`<path d="M 380,340 L ...">`). `validate_freecut.py` will **FAIL** your build! Always use `kit/world-atlas.js` + `MotionKit.renderWorldAtlas(...)` (offline 242-country Natural Earth GeoJSON + true spherical great-circle routes) or `maplibre-gl`!
2. **NEVER build "floating card on left + 2 simple bars on right"**: Integrate **transparent RGBA cutouts (`../media/cutouts/S02_cutout.png`)** directly into the composition or use progressive monotone curves (`MotionKit.renderDataCurve`) and full-canvas choreography.
3. **MANDATORY SHARED CUTOUT RULE**: Motion scenes (`motion/SXX.html`) MUST import the **exact verified cutout already approved on the timeline (`../media/cutouts/{sid}_cutout.png`)** — NEVER embed separate unverified web URLs or mismatched bottle/product variants!
4. **DATA CURVE COLLISION GUARD (`rightSafeX` + `callout`)**: Whenever placing a person/product cutout on the right (`#subject` / `.cutout-hero`), pass `rightSafeX: 1020` (or keep `plotBox.x + plotBox.width <= 1020`) AND include `callout` strings on both the baseline jump point and peak point (e.g. `{ label: '2024', value: 740, callout: 'R$ 740 MI' }`) so X-axis labels never hide behind shoulders.
5. **ALWAYS inspect `motion/SXX_preview.jpg` with Vision** after rendering to verify zero text clipping, zero line-over-label collisions, and crisp visual hierarchy!

---

## Scene Contract & Rendering

Every `<project_dir>/motion/SXX.html` must expose `window.__setFrame = function(frameIdx, fps) { ... }`.
Include both bundled kit scripts using relative or absolute paths:
```html
<script src=".../doc-motion-scenes/kit/world-atlas.js"></script>
<script src=".../doc-motion-scenes/kit/motion-kit.js"></script>
```

### Example A — Real Geodesic Atlas / 3D Globe (`MotionKit.renderWorldAtlas`)
```javascript
const routeP = MotionKit.progress(t, 0.8, 2.6, MotionKit.easeInOutCubic);
const rwaP   = MotionKit.progress(t, 2.2, 0.8);

const atlas = MotionKit.renderWorldAtlas(document.getElementById('atlas-svg'), {
  width: 1920,
  height: 1080,
  projection: 'naturalEarth', // or 'orthographic' for 3D rotating globe!
  fitBounds: [[-78, -36], [52, 26]],
  padding: 0.18,
  oceanFill: 'transparent',
  landFill: '#162032',
  landStroke: 'rgba(226,232,240,0.18)',
  showEquator: true,
  equatorLabel: 'LINHA DO EQUADOR • 0°',
  equatorLabelLon: -18,
  focusCountries: [
    { iso: 'BRA', fill: '#D97706', stroke: '#FDE68A', fillOpacity: 0.82 },
    { iso: 'RWA', fill: '#EA580C', stroke: '#FFEDD5', fillOpacity: 0.92, progress: rwaP },
  ],
  routes: [
    { from: [-43.17, -22.90], to: [30.06, -1.94], progress: routeP, color: '#F97316', width: 4.5 },
  ],
  pins: [
    { coords: [-43.17, -22.90], label: 'Brasil', sublabel: '14°S • TROPICAL', color: '#F59E0B', labelSide: 'left' },
    { coords: [30.06, -1.94], label: 'Kigali, Ruanda', sublabel: '1.9°S • ALTITUDE 1.567m', color: '#EA580C', labelSide: 'right', progress: rwaP },
  ],
});
```

### Example B — Progressive Data Curve (`MotionKit.renderDataCurve`)
```javascript
const info = MotionKit.renderDataCurve(document.getElementById('curve-svg'), {
  width: 1920,
  height: 1080,
  plotBox: { x: 160, y: 280, width: 1600, height: 520 },
  color: '#EA580C',
  progress: MotionKit.progress(t, 0.4, 2.8, MotionKit.easeInOutCubic),
  points: [
    { label: '1990', value: 18 },
    { label: '2000', value: 34 },
    { label: '2010', value: 61 },
    { label: '2024', value: 94 },
  ],
});
```

### Rendering CLI (Auto-Detects `aspect_ratio` from `storyboard.json`)
```bash
python "<SKILL_DIR>/scripts/render_motion_scene.py" --project-dir "<project_dir>"
```
Then inspect every `<project_dir>/motion/SXX_preview.jpg` before running `assemble_freecut.py`!
