# Motion Graphics Scene Templates (`doc-motion-scenes` v6.3)

Every `<project_dir>/motion/SXX.html` must expose deterministic frame stepping via `window.__setFrame = function(frameIdx, fps) { ... }` and load `world-atlas.js` + `motion-kit.js`.

## Example A — Real 242-Country Geodesic Atlas / 3D Globe (`MotionKit.renderWorldAtlas`)

```html
<script src="../.agents/skills/doc-motion-scenes/kit/world-atlas.js"></script>
<script src="../.agents/skills/doc-motion-scenes/kit/motion-kit.js"></script>
<script>
window.__setFrame = function(frameIdx, fps) {
  const t = frameIdx / fps;
  const routeP = MotionKit.progress(t, 0.8, 2.6, MotionKit.easeInOutCubic);
  const rwaP   = MotionKit.progress(t, 2.2, 0.8);

  MotionKit.renderWorldAtlas(document.getElementById('atlas-svg'), {
    width: 1920,
    height: 1080,
    projection: 'naturalEarth', // or 'orthographic' for 3D rotating globe
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
};
</script>
```

## Example B — Progressive Monotone Data Curve (`MotionKit.renderDataCurve`)

When placing a person/product cutout on the right side of the frame, pass `rightSafeX: 1020` (or keep `plotBox.x + plotBox.width <= 1020`) so X-axis labels never collide with shoulders:

```javascript
const info = MotionKit.renderDataCurve(document.getElementById('curve-svg'), {
  width: 1920,
  height: 1080,
  rightSafeX: 1020,
  plotBox: { x: 140, y: 280, width: 860, height: 520 },
  color: '#EA580C',
  progress: MotionKit.progress(t, 0.4, 2.8, MotionKit.easeInOutCubic),
  points: [
    { label: '2021', value: 10, callout: 'INÍCIO' },
    { label: '2022', value: 168 },
    { label: '2023', value: 325 },
    { label: '2024', value: 750, callout: 'R$ 750 MI' },
  ],
});
```
