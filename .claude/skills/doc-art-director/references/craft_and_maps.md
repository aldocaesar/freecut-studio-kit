# Editorial Craft, Multi-Format Safe Zones & Real Cartography Reference (v6)

Distilled production rules from `diretor-de-edicao`, `motion-designer/craft.md`, `remotion-maps`, and `claude-animation-skills`.

## 1. Platform Safe Zones (Center-Origin Coordinates vs CSS Pixels)

| Aspect Ratio | Resolution | CSS Safe Margins (`top / bottom / left / right`) | FreeCut Center-Origin Safe Bounds (`x`, `y`) |
|---|---|---|---|
| `16:9` (YouTube / Doc) | `1920x1080` | `76px / 92px / 108px / 108px` | `x in [-852, +852]`, `y in [-464, +448]` |
| `9:16` (Reels / Shorts / TikTok) | `1080x1920` | `240px / 360px / 64px / 140px` *(UI icons on right & bottom!)* | `x in [-476, +400]`, `y in [-720, +600]` |
| `4:5` (Feed Portrait) | `1080x1350` | `96px / 140px / 72px / 72px` | `x in [-468, +468]`, `y in [-579, +535]` |
| `1:1` (Square) | `1080x1080` | `84px / 110px / 72px / 72px` | `x in [-468, +468]`, `y in [-456, +430]` |

## 2. Pacing & Cut Discipline (`diretor-de-edicao`)
- **Word-Beat Synchronization**: Every cut or visual entrance must land on the spoken attack of a noun, verb, or number (`words.json`), never 600ms late.
- **Breathing Room**: Follow dense data/motion scenes (`5–7s`) with full-bleed photographic or B-roll scenes (`3.5–5.5s`) where one strong image carries the emotion without text clutter.
- **One Focal Point Per Moment**: Never force the viewer to read a paragraph on the right while inspecting a complex image on the left and listening to narration at the same time. Keep on-screen text to **2–6 punchy words** or a single number/date (`hero_stat`).

## 3. Motion & Typography Craft (`motion-designer`)
- **Typography Contrast**: Pair bold geometric/editorial headlines (`700–800` weight, tight tracking `-0.02em`) with crisp mono metadata tags (`JetBrains Mono`, `12–14px`, uppercase `+0.12em` tracking).
- **Physical Easing**: Entrances decelerate (`easeOutQuint` / physical `spring`); camera moves glide (`easeInOutCubic`). Never use robotic linear slides on UI/text elements.
- **Optical Finish**: Use `MotionKit.injectFilmGrain(0.038)` and subtle radial vignette on bespoke HTML motion scenes so rendered clips blend seamlessly with photographic footage instead of looking like flat web pages.

## 4. Real Cartography Rules (`remotion-maps` + `map-route`)
1. **World / Continental / Country Comparisons (100% Offline, Zero Key)**:
   - Include `<script src="../.agents/skills/doc-motion-scenes/kit/world-atlas.js"></script>` (or workspace relative path) + `motion-kit.js`.
   - Call `MotionKit.renderWorldAtlas(svgEl, { projection: 'naturalEarth' | 'orthographic', center: [lon, lat], fitBounds: [[minLon, minLat], [maxLon, maxLat]], focusCountries: [{ iso: 'BRA', fill: '#EA580C' }, { iso: 'RWA', fill: '#16A34A' }], routes: [{ from: [-43.17, -22.90], to: [30.06, -1.94], progress }], pins: [...] })`.
   - Place pin labels on the outer clear side (`labelSide: 'left'` for western pins, `'right'` for eastern pins) so route arcs and Equator lines NEVER cross text!
2. **City / Street / Neighborhood Zooms (Online Vector Tiles, Zero Key)**:
   - Load `maplibre-gl` (`https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js`) + style `'https://tiles.openfreemap.org/styles/liberty'`, expose `window.__readyPromise` waiting for `map.once('idle')`, and drive camera bearing/pitch/zoom deterministically inside `window.__setFrame(frameIdx, fps)`.
