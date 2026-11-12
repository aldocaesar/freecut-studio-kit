/**
 * FreeCut Universal Studio — Creative Motion Physics & GIS Primitives (v8.0)
 * ==========================================================================
 * Pure zero-dependency math, spring physics, SVG path choreography, 2.5D camera,
 * and Natural Earth 242-country geodesic cartography (`renderWorldAtlas`).
 *
 * ZERO CANNED SLIDE WIDGETS & ZERO FIXED PALETTES:
 * Every motion scene is authored creatively from scratch in HTML/CSS/SVG/Canvas2D
 * by the LLM to embody the exact visual metaphor, genre, and `style_dna` of the video,
 * driven frame-by-frame via `window.__setFrame(frameIdx, fps)` in Playwright Chromium.
 */
(function (global) {
  'use strict';

  const SVG_NS = 'http://www.w3.org/2000/svg';
  const DEG2RAD = Math.PI / 180;
  const RAD2DEG = 180 / Math.PI;

  function clamp01(v) {
    return v < 0 ? 0 : v > 1 ? 1 : v;
  }

  function clamp(v, minV, maxV) {
    return v < minV ? minV : v > maxV ? maxV : v;
  }

  function lerp(a, b, t) {
    return a + (b - a) * t;
  }

  function remap(v, inMin, inMax, outMin, outMax, clampOut) {
    const raw = (v - inMin) / (inMax - inMin || 1e-6);
    const t = clampOut === false ? raw : clamp01(raw);
    return lerp(outMin, outMax, t);
  }

  // Smooth editorial quintic deceleration
  function easeOutQuint(t) {
    const x = clamp01(t);
    return 1 - Math.pow(1 - x, 5);
  }

  // Smooth cubic S-curve for camera pans & zooms
  function easeInOutCubic(t) {
    const x = clamp01(t);
    return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
  }

  // Smooth sinusoidal S-curve
  function easeInOutSine(t) {
    return -(Math.cos(Math.PI * clamp01(t)) - 1) * 0.5;
  }

  // Exponential decay out (snappy, zero overshoot)
  function easeOutExpo(t) {
    const x = clamp01(t);
    return x === 1 ? 1 : 1 - Math.pow(2, -10 * x);
  }

  // Tactile overshoot pop (great for playful, arcade, comic, or bold UI beats)
  function easeOutBack(t, overshoot) {
    const x = clamp01(t);
    const c1 = overshoot !== undefined ? overshoot : 1.70158;
    const c3 = c1 + 1;
    return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2);
  }

  // Deterministic closed-form damped harmonic spring
  function spring(tSeconds, opts) {
    if (tSeconds <= 0) return 0;
    const stiffness = (opts && opts.stiffness) || 170;
    const damping = (opts && opts.damping) || 22;
    const mass = (opts && opts.mass) || 1;
    const w0 = Math.sqrt(stiffness / mass);
    const zeta = damping / (2 * Math.sqrt(stiffness * mass));
    if (zeta < 1) {
      const wd = w0 * Math.sqrt(1 - zeta * zeta);
      const env = Math.exp(-zeta * w0 * tSeconds);
      return 1 - env * (Math.cos(wd * tSeconds) + ((zeta * w0) / wd) * Math.sin(wd * tSeconds));
    }
    const env = Math.exp(-w0 * tSeconds);
    return 1 - env * (1 + w0 * tSeconds);
  }

  function progress(t, startSec, durSec, easeFn) {
    const raw = clamp01((t - startSec) / Math.max(0.0001, durSec));
    return easeFn ? easeFn(raw) : easeOutQuint(raw);
  }

  function stagger(t, index, baseStart, stepSec, durSec, easeFn) {
    return progress(t, baseStart + index * stepSec, durSec, easeFn || easeOutQuint);
  }

  // Deterministic pseudo-random [0, 1) from integer/float seed (safe across arbitrary frame jumps)
  function hashNoise(seed) {
    const s = Math.sin((seed + 1) * 12.9898 + 78.233) * 43758.5453123;
    return s - Math.floor(s);
  }

  // Continuous harmonic oscillation (prevents frozen tails between 78% and 94%)
  function oscillate(t, freqHz, amplitude, phaseRad) {
    const f = freqHz !== undefined ? freqHz : 0.5;
    const a = amplitude !== undefined ? amplitude : 1.0;
    const p = phaseRad || 0;
    return Math.sin(t * Math.PI * 2 * f + p) * a;
  }

  /**
   * Safe zones per aspect ratio
   */
  function safeZone(width, height) {
    const ratio = width / Math.max(1, height);
    if (ratio < 0.65) {
      return { top: 240, bottom: 360, left: 64, right: 140, format: '9:16' };
    }
    if (ratio < 0.9) {
      return { top: 96, bottom: 140, left: 72, right: 72, format: '4:5' };
    }
    if (ratio < 1.15) {
      return { top: 84, bottom: 110, left: 72, right: 72, format: '1:1' };
    }
    return { top: 76, bottom: 92, left: 108, right: 108, format: '16:9' };
  }

  /**
   * Rostrum 2.5D camera transform string
   */
  function rostrumTransform(t, totalDuration, opts) {
    const p = easeInOutCubic(clamp01(t / Math.max(0.001, totalDuration)));
    const s0 = (opts && opts.scaleFrom) !== undefined ? opts.scaleFrom : 1.0;
    const s1 = (opts && opts.scaleTo) !== undefined ? opts.scaleTo : 1.05;
    const x0 = (opts && opts.xFrom) || 0;
    const x1 = (opts && opts.xTo) || 0;
    const y0 = (opts && opts.yFrom) || 0;
    const y1 = (opts && opts.yTo) || 0;
    const r0 = (opts && opts.rotFrom) || 0;
    const r1 = (opts && opts.rotTo) || 0;

    const s = lerp(s0, s1, p);
    const x = lerp(x0, x1, p);
    const y = lerp(y0, y1, p);
    const r = lerp(r0, r1, p);
    return `translate3d(${x.toFixed(2)}px, ${y.toFixed(2)}px, 0) scale(${s.toFixed(4)}) rotate(${r.toFixed(3)}deg)`;
  }

  /**
   * Progressive SVG stroke reveal (`p` in 0..1)
   */
  function strokeProgress(pathEl, p) {
    if (!pathEl) return;
    if (!pathEl.__totalLen) {
      pathEl.__totalLen = pathEl.getTotalLength ? pathEl.getTotalLength() : 1000;
      pathEl.style.strokeDasharray = `${pathEl.__totalLen}`;
    }
    const c = clamp01(p);
    pathEl.style.strokeDashoffset = `${(pathEl.__totalLen * (1 - c)).toFixed(2)}`;
  }

  /**
   * Samples `{ x, y, angle }` at normalized `p` (0..1) along any SVG `<path>`
   */
  function pointOnPath(pathEl, p) {
    if (!pathEl || !pathEl.getTotalLength) return { x: 0, y: 0, angle: 0 };
    if (!pathEl.__totalLen) {
      pathEl.__totalLen = pathEl.getTotalLength();
    }
    const total = pathEl.__totalLen || 1;
    const d = clamp01(p) * total;
    const pt = pathEl.getPointAtLength(d);
    const dAhead = Math.min(total, d + 2.0);
    const dBehind = Math.max(0, d - 2.0);
    const p1 = pathEl.getPointAtLength(dBehind);
    const p2 = pathEl.getPointAtLength(dAhead);
    const angle = Math.atan2(p2.y - p1.y, p2.x - p1.x) * RAD2DEG;
    return { x: pt.x, y: pt.y, angle };
  }

  function injectFilmGrain(opacity) {
    if (document.getElementById('__mk_grain')) return;
    const op = opacity !== undefined ? opacity : 0.035;
    const div = document.createElement('div');
    div.id = '__mk_grain';
    div.style.cssText = [
      'position:fixed',
      'inset:0',
      'pointer-events:none',
      'z-index:9999',
      `opacity:${op}`,
      'mix-blend-mode:overlay',
      "background-image:url(\"data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.82' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")",
    ].join(';');
    document.body.appendChild(div);
  }

  function svgEl(tag, attrs, parent) {
    const el = document.createElementNS(SVG_NS, tag);
    if (attrs) {
      for (const k in attrs) {
        if (attrs[k] !== undefined && attrs[k] !== null) {
          el.setAttribute(k, String(attrs[k]));
        }
      }
    }
    if (parent) parent.appendChild(el);
    return el;
  }

  // =========================================================================
  // REAL GEODESIC CARTOGRAPHY ENGINE (Natural Earth + Spherical Slerp)
  // =========================================================================

  const NE_A0 = 0.8707, NE_A1 = -0.131979, NE_A2 = -0.013791, NE_A3 = 0.003971, NE_A4 = -0.001529;
  const NE_B0 = 1.007226, NE_B1 = 0.015085, NE_B2 = -0.044475, NE_B3 = 0.028874, NE_B4 = -0.005916;

  function createProjector(opts) {
    const type = (opts.projection || 'naturalEarth').toLowerCase();
    const box = opts.viewportBox || { x: 0, y: 0, width: opts.width || 1920, height: opts.height || 1080 };
    const center = opts.center || [0, 10];
    const rotLon = -(opts.rotate ? opts.rotate[0] : center[0]) * DEG2RAD;
    const rotLat = -(opts.rotate ? opts.rotate[1] : center[1]) * DEG2RAD;

    let scale = opts.scale;
    let cx = box.x + box.width * 0.5;
    let cy = box.y + box.height * 0.5;

    function rawProject(lonDeg, latDeg) {
      const lam = lonDeg * DEG2RAD;
      const phi = Math.max(-85 * DEG2RAD, Math.min(85 * DEG2RAD, latDeg * DEG2RAD));

      if (type === 'orthographic' || type === 'globe') {
        const dLam = lam + rotLon;
        const cosPhi = Math.cos(phi);
        const sinPhi = Math.sin(phi);
        const cosLat0 = Math.cos(-rotLat);
        const sinLat0 = Math.sin(-rotLat);
        const cosc = sinLat0 * sinPhi + cosLat0 * cosPhi * Math.cos(dLam);
        if (cosc < -0.02) return null;
        const x = cosPhi * Math.sin(dLam);
        const y = -(cosLat0 * sinPhi - sinLat0 * cosPhi * Math.cos(dLam));
        return [x, y, cosc >= 0];
      }

      if (type === 'mercator') {
        let dLam = lam - center[0] * DEG2RAD;
        while (dLam > Math.PI) dLam -= 2 * Math.PI;
        while (dLam < -Math.PI) dLam += 2 * Math.PI;
        const yMerc = Math.log(Math.tan(Math.PI / 4 + phi / 2));
        const y0 = Math.log(Math.tan(Math.PI / 4 + (center[1] * DEG2RAD) / 2));
        return [dLam, -(yMerc - y0), true];
      }

      let dLam = lam - center[0] * DEG2RAD;
      while (dLam > Math.PI) dLam -= 2 * Math.PI;
      while (dLam < -Math.PI) dLam += 2 * Math.PI;
      const phi2 = phi * phi;
      const phi4 = phi2 * phi2;
      const x = dLam * (NE_A0 + phi2 * (NE_A1 + phi2 * (NE_A2 + phi4 * (NE_A3 + phi2 * NE_A4))));
      const y = -phi * (NE_B0 + phi2 * (NE_B1 + phi2 * (NE_B2 + phi4 * (NE_B3 + phi2 * NE_B4))));

      const cPhi = center[1] * DEG2RAD;
      const cPhi2 = cPhi * cPhi;
      const cPhi4 = cPhi2 * cPhi2;
      const y0 = -cPhi * (NE_B0 + cPhi2 * (NE_B1 + cPhi2 * (NE_B2 + cPhi4 * (NE_B3 + cPhi2 * NE_B4))));
      return [x, y - y0, true];
    }

    if (opts.fitBounds && Array.isArray(opts.fitBounds) && opts.fitBounds.length === 2) {
      const [[minLon, minLat], [maxLon, maxLat]] = opts.fitBounds;
      const pad = opts.padding !== undefined ? opts.padding : 0.16;
      const samples = [
        [minLon, minLat], [maxLon, minLat], [maxLon, maxLat], [minLon, maxLat],
        [(minLon + maxLon) * 0.5, minLat], [(minLon + maxLon) * 0.5, maxLat],
      ];
      let rx0 = Infinity, rx1 = -Infinity, ry0 = Infinity, ry1 = -Infinity;
      for (const [lo, la] of samples) {
        const pt = rawProject(lo, la);
        if (pt) {
          if (pt[0] < rx0) rx0 = pt[0];
          if (pt[0] > rx1) rx1 = pt[0];
          if (pt[1] < ry0) ry0 = pt[1];
          if (pt[1] > ry1) ry1 = pt[1];
        }
      }
      const spanX = Math.max(0.02, rx1 - rx0);
      const spanY = Math.max(0.02, ry1 - ry0);
      const availW = box.width * (1 - pad * 2);
      const availH = box.height * (1 - pad * 2);
      scale = Math.min(availW / spanX, availH / spanY);
      const midX = (rx0 + rx1) * 0.5;
      const midY = (ry0 + ry1) * 0.5;
      cx = box.x + box.width * 0.5 - midX * scale;
      cy = box.y + box.height * 0.5 - midY * scale;
    } else if (!scale) {
      scale = type === 'orthographic' || type === 'globe'
        ? Math.min(box.width, box.height) * 0.41
        : box.width / 5.4;
    }

    function project(lonDeg, latDeg) {
      const raw = rawProject(lonDeg, latDeg);
      if (!raw) return null;
      return [cx + raw[0] * scale, cy + raw[1] * scale, raw[2]];
    }

    return { project, scale, cx, cy, box, type };
  }

  function greatCirclePoints(fromLonLat, toLonLat, steps, maxT) {
    const n = steps || 72;
    const tEnd = clamp01(maxT === undefined ? 1 : maxT);
    const lon1 = fromLonLat[0] * DEG2RAD, lat1 = fromLonLat[1] * DEG2RAD;
    const lon2 = toLonLat[0] * DEG2RAD, lat2 = toLonLat[1] * DEG2RAD;

    const x1 = Math.cos(lat1) * Math.cos(lon1);
    const y1 = Math.cos(lat1) * Math.sin(lon1);
    const z1 = Math.sin(lat1);

    const x2 = Math.cos(lat2) * Math.cos(lon2);
    const y2 = Math.cos(lat2) * Math.sin(lon2);
    const z2 = Math.sin(lat2);

    const dot = Math.max(-1, Math.min(1, x1 * x2 + y1 * y2 + z1 * z2));
    const omega = Math.acos(dot);
    const sinOmega = Math.sin(omega);

    const pts = [];
    const count = Math.max(1, Math.round(n * tEnd));
    for (let i = 0; i <= count; i++) {
      const t = (i / Math.max(1, count)) * tEnd;
      let x, y, z;
      if (sinOmega < 1e-6) {
        x = lerp(x1, x2, t);
        y = lerp(y1, y2, t);
        z = lerp(z1, z2, t);
      } else {
        const a = Math.sin((1 - t) * omega) / sinOmega;
        const b = Math.sin(t * omega) / sinOmega;
        x = a * x1 + b * x2;
        y = a * y1 + b * y2;
        z = a * z1 + b * z2;
      }
      const lat = Math.asin(Math.max(-1, Math.min(1, z))) * RAD2DEG;
      const lon = Math.atan2(y, x) * RAD2DEG;
      pts.push([lon, lat]);
    }
    return pts;
  }

  function ringToPath(ring, project) {
    let d = '';
    let prev = null;
    for (let i = 0; i < ring.length; i++) {
      const pt = project(ring[i][0], ring[i][1]);
      if (!pt) {
        prev = null;
        continue;
      }
      if (prev && Math.hypot(pt[0] - prev[0], pt[1] - prev[1]) > 380) {
        prev = null;
      }
      d += (prev ? 'L' : 'M') + pt[0].toFixed(1) + ',' + pt[1].toFixed(1);
      prev = pt;
    }
    if (d) d += 'Z';
    return d;
  }

  function geometryToPath(geom, project) {
    if (!geom) return '';
    if (geom.type === 'Polygon') {
      return geom.coordinates.map((r) => ringToPath(r, project)).join('');
    }
    if (geom.type === 'MultiPolygon') {
      let out = '';
      for (const poly of geom.coordinates) {
        for (const r of poly) out += ringToPath(r, project);
      }
      return out;
    }
    return '';
  }

  /**
   * Renders a real Natural Earth 242-country cartographic atlas into `svgRoot`.
   * Requires `<script src=".../kit/world-atlas.js"></script>` (window.WORLD_ATLAS_GEOJSON).
   * Caller passes colors matching the video's `style_dna` (`oceanFill`, `landFill`, `focusCountries`, `routes`, `pins`).
   */
  function renderWorldAtlas(svgRoot, opts) {
    if (!svgRoot) return null;
    const cfg = opts || {};
    const geo = cfg.geojson || global.WORLD_ATLAS_GEOJSON;
    if (!geo || !geo.features) {
      throw new Error('WORLD_ATLAS_GEOJSON missing! Include kit/world-atlas.js before rendering maps.');
    }

    while (svgRoot.firstChild) svgRoot.removeChild(svgRoot.firstChild);

    const width = cfg.width || 1920;
    const height = cfg.height || 1080;
    svgRoot.setAttribute('viewBox', `0 0 ${width} ${height}`);

    const proj = createProjector(Object.assign({ width, height }, cfg));
    const { project, scale, cx, cy, box, type } = proj;

    const defs = svgEl('defs', {}, svgRoot);
    const accentDefault = cfg.accent || '#3B82F6';

    const clipId = '__mk_atlas_clip';
    const clip = svgEl('clipPath', { id: clipId }, defs);
    if (type === 'orthographic' || type === 'globe') {
      svgEl('circle', { cx: cx.toFixed(1), cy: cy.toFixed(1), r: scale.toFixed(1) }, clip);
      const grad = svgEl('radialGradient', { id: '__mk_globe_ocean', cx: '38%', cy: '32%', r: '70%' }, defs);
      svgEl('stop', { offset: '0%', 'stop-color': cfg.oceanHighlight || '#1E3A5F' }, grad);
      svgEl('stop', { offset: '100%', 'stop-color': cfg.oceanFill || '#0B1324' }, grad);
    } else {
      svgEl('rect', { x: box.x, y: box.y, width: box.width, height: box.height, rx: cfg.borderRadius || 0 }, clip);
    }

    const rootG = svgEl('g', { 'clip-path': `url(#${clipId})` }, svgRoot);

    if (type === 'orthographic' || type === 'globe') {
      svgEl('circle', {
        cx: cx.toFixed(1),
        cy: cy.toFixed(1),
        r: scale.toFixed(1),
        fill: cfg.oceanFill ? cfg.oceanFill : 'url(#__mk_globe_ocean)',
      }, rootG);
    } else if (cfg.oceanFill && cfg.oceanFill !== 'transparent') {
      svgEl('rect', {
        x: box.x,
        y: box.y,
        width: box.width,
        height: box.height,
        fill: cfg.oceanFill,
      }, rootG);
    }

    if (cfg.showGraticule !== false) {
      const gratG = svgEl('g', {
        fill: 'none',
        stroke: cfg.graticuleColor || 'rgba(148, 163, 184, 0.14)',
        'stroke-width': '1',
      }, rootG);
      for (let lon = -150; lon <= 180; lon += 30) {
        let d = '';
        for (let lat = -80; lat <= 80; lat += 5) {
          const p = project(lon, lat);
          if (p) d += (d ? 'L' : 'M') + p[0].toFixed(1) + ',' + p[1].toFixed(1);
        }
        if (d) svgEl('path', { d }, gratG);
      }
      for (let lat = -60; lat <= 60; lat += 30) {
        if (lat === 0 && cfg.showEquator) continue;
        let d = '';
        for (let lon = -180; lon <= 180; lon += 5) {
          const p = project(lon, lat);
          if (p) d += (d ? 'L' : 'M') + p[0].toFixed(1) + ',' + p[1].toFixed(1);
        }
        if (d) svgEl('path', { d }, gratG);
      }
    }

    if (cfg.showEquator) {
      let eqD = '';
      for (let lon = -180; lon <= 180; lon += 3) {
        const p = project(lon, 0);
        if (p) eqD += (eqD ? 'L' : 'M') + p[0].toFixed(1) + ',' + p[1].toFixed(1);
      }
      if (eqD) {
        svgEl('path', {
          d: eqD,
          fill: 'none',
          stroke: cfg.equatorColor || accentDefault,
          'stroke-opacity': '0.45',
          'stroke-width': '1.6',
          'stroke-dasharray': '7 7',
        }, rootG);
      }
    }

    const focusMap = {};
    if (Array.isArray(cfg.focusCountries)) {
      for (const fc of cfg.focusCountries) {
        if (typeof fc === 'string') {
          focusMap[fc.toUpperCase()] = { iso: fc.toUpperCase() };
        } else if (fc && (fc.iso || fc.name)) {
          const key = (fc.iso || fc.name).toUpperCase();
          focusMap[key] = fc;
        }
      }
    }

    const landG = svgEl('g', {}, rootG);
    const focusG = svgEl('g', {}, rootG);

    const baseFill = cfg.landFill || '#1A2436';
    const baseStroke = cfg.landStroke || 'rgba(226, 232, 240, 0.16)';
    const baseStrokeW = cfg.landStrokeWidth || 1.0;

    for (const feat of geo.features) {
      const props = feat.properties || {};
      const iso = (props.iso || '').toUpperCase();
      const nm = (props.name || '').toUpperCase();
      const fc = focusMap[iso] || focusMap[nm];
      const d = geometryToPath(feat.geometry, project);
      if (!d) continue;

      if (fc) {
        const hp = fc.progress !== undefined ? clamp01(fc.progress) : 1;
        svgEl('path', {
          d,
          fill: fc.fill || accentDefault,
          'fill-opacity': lerp(0.18, fc.fillOpacity !== undefined ? fc.fillOpacity : 0.85, hp).toFixed(3),
          stroke: fc.stroke || '#FFFFFF',
          'stroke-width': (fc.strokeWidth || 2.0).toFixed(1),
        }, focusG);
      } else {
        svgEl('path', {
          d,
          fill: baseFill,
          stroke: baseStroke,
          'stroke-width': baseStrokeW,
        }, landG);
      }
    }

    if (type === 'orthographic' || type === 'globe') {
      svgEl('circle', {
        cx: cx.toFixed(1),
        cy: cy.toFixed(1),
        r: scale.toFixed(1),
        fill: 'none',
        stroke: cfg.sphereStroke || 'rgba(148, 163, 184, 0.35)',
        'stroke-width': '2',
      }, svgRoot);
    }

    const routeHeads = [];
    if (Array.isArray(cfg.routes)) {
      const routeG = svgEl('g', {}, svgRoot);
      for (const rt of cfg.routes) {
        const p = clamp01(rt.progress !== undefined ? rt.progress : 1);
        const rCol = rt.color || accentDefault;
        if (p <= 0.001) {
          routeHeads.push(null);
          continue;
        }
        if (rt.showGhost !== false) {
          const ghostPts = greatCirclePoints(rt.from, rt.to, 64, 1);
          let gd = '';
          for (const gp of ghostPts) {
            const s = project(gp[0], gp[1]);
            if (s) gd += (gd ? 'L' : 'M') + s[0].toFixed(1) + ',' + s[1].toFixed(1);
          }
          if (gd) {
            svgEl('path', {
              d: gd,
              fill: 'none',
              stroke: rCol,
              'stroke-opacity': '0.18',
              'stroke-width': rt.width || 3.5,
              'stroke-dasharray': '5 7',
            }, routeG);
          }
        }

        const activePts = greatCirclePoints(rt.from, rt.to, 72, p);
        let ad = '';
        let lastScreen = null;
        for (const ap of activePts) {
          const s = project(ap[0], ap[1]);
          if (s) {
            ad += (ad ? 'L' : 'M') + s[0].toFixed(1) + ',' + s[1].toFixed(1);
            lastScreen = s;
          }
        }
        if (ad) {
          svgEl('path', {
            d: ad,
            fill: 'none',
            stroke: rCol,
            'stroke-width': rt.width || 4,
            'stroke-linecap': 'round',
            'stroke-dasharray': rt.dashed ? '10 8' : undefined,
          }, routeG);
        }
        if (lastScreen && rt.showHead !== false) {
          svgEl('circle', {
            cx: lastScreen[0].toFixed(1),
            cy: lastScreen[1].toFixed(1),
            r: '13',
            fill: rCol,
            'fill-opacity': '0.24',
          }, routeG);
          svgEl('circle', {
            cx: lastScreen[0].toFixed(1),
            cy: lastScreen[1].toFixed(1),
            r: '5.5',
            fill: '#FFFFFF',
            stroke: rCol,
            'stroke-width': '3',
          }, routeG);
        }
        routeHeads.push(lastScreen);
      }
    }

    const pinPositions = [];
    if (Array.isArray(cfg.pins)) {
      const pinG = svgEl('g', {}, svgRoot);
      for (const pin of cfg.pins) {
        const pt = project(pin.coords[0], pin.coords[1]);
        pinPositions.push(pt);
        if (!pt) continue;
        const pp = clamp01(pin.progress !== undefined ? pin.progress : 1);
        if (pp <= 0.01) continue;

        const col = pin.color || accentDefault;
        const g = svgEl('g', {
          transform: `translate(${pt[0].toFixed(1)}, ${pt[1].toFixed(1)})`,
          opacity: pp.toFixed(3),
        }, pinG);

        svgEl('circle', { r: (18 * pp).toFixed(1), fill: col, 'fill-opacity': '0.20' }, g);
        svgEl('circle', { r: (7 * pp).toFixed(1), fill: col, stroke: '#FFFFFF', 'stroke-width': '2.4' }, g);

        if (pin.label) {
          const side = pin.labelSide || 'right';
          const ox = pin.offset ? pin.offset[0] : (side === 'left' ? -18 : side === 'right' ? 18 : 0);
          const oy = pin.offset ? pin.offset[1] : (side === 'top' ? -22 : side === 'bottom' ? 28 : -4);
          const anchor = side === 'left' ? 'end' : side === 'right' ? 'start' : 'middle';

          const tMain = svgEl('text', {
            x: ox,
            y: oy,
            'text-anchor': anchor,
            fill: pin.labelColor || '#F8FAFC',
            'font-family': cfg.fontSans || "'Plus Jakarta Sans', 'Inter', system-ui, sans-serif",
            'font-size': pin.fontSize || 20,
            'font-weight': '700',
          }, g);
          tMain.textContent = pin.label;

          if (pin.sublabel) {
            const tSub = svgEl('text', {
              x: ox,
              y: oy + 20,
              'text-anchor': anchor,
              fill: pin.sublabelColor || 'rgba(203, 213, 225, 0.85)',
              'font-family': cfg.fontMono || "'JetBrains Mono', monospace",
              'font-size': '13',
              'font-weight': '600',
              'letter-spacing': '1.2',
            }, g);
            tSub.textContent = pin.sublabel;
          }
        }
      }
    }

    return { project, pinPositions, routeHeads, scale, cx, cy };
  }

  global.MotionKit = {
    clamp01,
    clamp,
    lerp,
    remap,
    easeOutQuint,
    easeInOutCubic,
    easeInOutSine,
    easeOutExpo,
    easeOutBack,
    spring,
    progress,
    stagger,
    hashNoise,
    oscillate,
    safeZone,
    rostrumTransform,
    strokeProgress,
    pointOnPath,
    injectFilmGrain,
    svgEl,
    createProjector,
    greatCirclePoints,
    renderWorldAtlas,
  };
})(window);
