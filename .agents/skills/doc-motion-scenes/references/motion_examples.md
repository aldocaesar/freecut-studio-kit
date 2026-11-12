# Creative Bespoke Motion Architecture Guide (`v8.0`)

> **Golden Rule:** These snippets show **how `window.__setFrame(frameIdx, fps)` and `MotionKit` physics work** — they are **NOT** templates to copy verbatim! Every `motion/SXX.html` must invent its own visual world, SVG geometry, layout, and choreography around the spoken sentence and the project's `style_dna`.

---

## 1. Minimal Deterministic Scene Skeleton (Custom SVG + CSS + `MotionKit` Physics)

```html
<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@600;700&family=JetBrains+Mono:wght@600&display=swap" />
  <style>
    /* Always derive CSS variables from storyboard.json -> style_dna! */
    :root {
      --bg: #FFF8E7;
      --ink: #141824;
      --accent: #FF2A5F;
      --accent-2: #FFD60A;
      --font-head: 'Space Grotesk', sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    html, body {
      width: 1920px;
      height: 1080px;
      overflow: hidden;
      background: var(--bg);
      color: var(--ink);
      font-family: var(--font-head);
    }
    #camera {
      position: relative;
      width: 1920px;
      height: 1080px;
      transform-origin: 50% 50%;
      will-change: transform;
    }
  </style>
</head>
<body>
  <div id="camera">
    <svg id="stage" viewBox="0 0 1920 1080" width="1920" height="1080"></svg>
  </div>

  <script src="../../../.agents/skills/doc-motion-scenes/kit/motion-kit.js"></script>
  <script>
    const DURATION = 5.4; // Match scene (end_ms - start_ms) / 1000
    const cam = document.getElementById('camera');
    const stage = document.getElementById('stage');
    MotionKit.injectFilmGrain(0.03);

    // Build custom bespoke SVG/DOM elements once at load time...
    const trail = MotionKit.svgEl('path', {
      d: 'M 220 760 C 620 260, 1240 880, 1680 340',
      fill: 'none',
      stroke: 'var(--accent)',
      'stroke-width': 8,
      'stroke-linecap': 'round'
    }, stage);
    const runner = MotionKit.svgEl('circle', { r: 22, fill: 'var(--accent-2)', stroke: 'var(--ink)', 'stroke-width': 5 }, stage);

    window.__setFrame = function (frameIdx, fps) {
      const t = frameIdx / (fps || 30);

      // 1. Continuous 2.5D camera drift across 0..DURATION (guarantees live 78% -> 94% tail!)
      cam.style.transform = MotionKit.rostrumTransform(t, DURATION, {
        scaleFrom: 0.98,
        scaleTo: 1.035,
        xFrom: -14,
        xTo: 14,
        yFrom: 6,
        yTo: -6
      });

      // 2. Progressive curve draw + object riding the curve tangent
      const pDraw = MotionKit.progress(t, 0.2, DURATION * 0.68, MotionKit.easeInOutCubic);
      MotionKit.strokeProgress(trail, pDraw);
      const pos = MotionKit.pointOnPath(trail, pDraw);
      const bob = MotionKit.oscillate(t, 1.8, 7, 0);
      runner.setAttribute('cx', pos.x.toFixed(1));
      runner.setAttribute('cy', (pos.y + bob).toFixed(1));
    };
    window.__setFrame(0, 30);
  </script>
</body>
</html>
```

---

## 2. Four Creative Techniques to Mix & Invent Per Genre

1. **Bespoke Illustrated Object / Prop Choreography (SVG + Spring Physics):**
   - Draw recognizable stylized props in clean vector geometry (e.g., rattling doors/windows, gauges, scales, bottles, arcade machines, retro CRT frames, Hourglasses, vaults, rockets, musical waveforms, lab flasks, stadium scoreboards).
   - Drive impacts with `MotionKit.spring(t - hitTime, { stiffness: 260, damping: 14 })` and continuous secondary motion with `MotionKit.oscillate(t, freq, amp, phase)`.
2. **Canvas2D Procedural Fields + Crisp HTML/SVG Foreground:**
   - Layer a `<canvas width="1920" height="1080">` behind an `<svg>` or HTML typography stage to draw shockwave rings, confetti/coins, radar sweeps, starfields, acoustic spectrum bars, fluid waves, or grid deformations computed purely from `t` and `MotionKit.hashNoise(i)`.
3. **Expressive Kinetic Typography & Spatial Diagrams:**
   - Break away from tiny left-aligned card headers! Use oversized cropped background numerals, circular rotating SVG `<textPath>` seals, stepped diagonal words, or split duotone stages whose colors come straight from `style_dna`.
4. **Real Geodesic Cartography (When the Narration Names Real Countries/Routes):**
   - Load `kit/world-atlas.js` + `kit/motion-kit.js` and call `MotionKit.renderWorldAtlas(svgEl, { projection: 'orthographic' | 'naturalEarth', rotate: [lon, lat], oceanFill, landFill, accent, focusCountries, routes, pins })`, animating `rotate` or `routes[i].progress` smoothly with `t`.

---

## 3. Anti-Clone Checklist Before Rendering

- **Different Skeleton Every Scene:** If `S03.html` is a split portal, `S06.html` might be a full-scene architectural shockwave illustration, `S11.html` a central object with bezier particle trails, and `S18.html` an isometric/grid stamp counter. Never copy-paste one `SXX.html` into the next and only swap text!
- **Safe Margins (`16:9` -> `>= 96px` horizontal, `>= 80px` vertical; `9:16` -> `top >= 240px`, `bottom >= 360px`):** Keep all key text and badges inside `MotionKit.safeZone(W, H)` with `overflow: visible` on internal labels so nothing clips.
- **Zero Domain Leakage:** Every single string, number, badge, and label in `motion/SXX.html` must come 100% from the current video's transcript and story.
