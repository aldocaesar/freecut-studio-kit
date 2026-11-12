/**
 * FreeCut Universal Studio — Documentary & Editorial Motion Kit (v7.0)
 * Zero-dependency deterministic frame engine + 8 Editorial Chapter Palettes +
 * 10 Declarative Visual Archetypes (Real GIS Atlas, 2.5D Camera Journey,
 * Follow-Tip Data Curve, Mechanical Odometer, 3D UI Social Feed, Overhead Dossier Desk,
 * Directed Cash-Flow Network, Diagonal Versus Split, 100-Block Waffle Scale, Kinetic Manifesto)
 * with continuous live drift through 100% of clip duration (zero static tails).
 *
 * Driven frame-by-frame via window.__setFrame(frameIdx, fps) in Playwright Chromium.
 */
(function (global) {
  'use strict';

  const SVG_NS = 'http://www.w3.org/2000/svg';
  const DEG2RAD = Math.PI / 180;
  const RAD2DEG = 180 / Math.PI;

  function clamp01(v) {
    return v < 0 ? 0 : v > 1 ? 1 : v;
  }

  function lerp(a, b, t) {
    return a + (b - a) * t;
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

  // Exponential decay out (snappy, zero overshoot)
  function easeOutExpo(t) {
    const x = clamp01(t);
    return x === 1 ? 1 : 1 - Math.pow(2, -10 * x);
  }

  // Critically / slightly under-damped physical spring (deterministic closed-form)
  function spring(tSeconds, opts) {
    if (tSeconds <= 0) return 0;
    const stiffness = (opts && opts.stiffness) || 170;
    const damping = (opts && opts.damping) || 24;
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

  /**
   * Safe zones per aspect ratio (craft.md §5b)
   */
  function safeZone(width, height) {
    const ratio = width / Math.max(1, height);
    if (ratio < 0.65) {
      // 9:16 Reels / TikTok / Shorts
      return { top: 240, bottom: 360, left: 64, right: 140, format: '9:16' };
    }
    if (ratio < 0.9) {
      // 4:5 Feed
      return { top: 96, bottom: 140, left: 72, right: 72, format: '4:5' };
    }
    if (ratio < 1.15) {
      // 1:1 Square
      return { top: 84, bottom: 110, left: 72, right: 72, format: '1:1' };
    }
    // 16:9 YouTube / Documentary
    return { top: 76, bottom: 92, left: 108, right: 108, format: '16:9' };
  }

  /**
   * Rostrum 2.5D camera transform string
   */
  function rostrumTransform(t, totalDuration, opts) {
    const p = easeInOutCubic(clamp01(t / Math.max(0.001, totalDuration)));
    const s0 = (opts && opts.scaleFrom) !== undefined ? opts.scaleFrom : 1.0;
    const s1 = (opts && opts.scaleTo) !== undefined ? opts.scaleTo : 1.055;
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

  function strokeProgress(pathEl, p) {
    if (!pathEl) return;
    if (!pathEl.__totalLen) {
      pathEl.__totalLen = pathEl.getTotalLength ? pathEl.getTotalLength() : 1000;
      pathEl.style.strokeDasharray = `${pathEl.__totalLen}`;
    }
    const c = clamp01(p);
    pathEl.style.strokeDashoffset = `${(pathEl.__totalLen * (1 - c)).toFixed(2)}`;
  }

  function injectFilmGrain(opacity) {
    if (document.getElementById('__mk_grain')) return;
    const op = opacity !== undefined ? opacity : 0.04;
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

  // =========================================================================
  // REAL GEODESIC CARTOGRAPHY ENGINE (Natural Earth + Spherical Slerp)
  // =========================================================================

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

  /**
   * Natural Earth I polynomial projection (matches standard world editorial atlases)
   */
  const NE_A0 = 0.8707, NE_A1 = -0.131979, NE_A2 = -0.013791, NE_A3 = 0.003971, NE_A4 = -0.001529;
  const NE_B0 = 1.007226, NE_B1 = 0.015085, NE_B2 = -0.044475, NE_B3 = 0.028874, NE_B4 = -0.005916;

  function createProjector(opts) {
    const type = (opts.projection || 'naturalEarth').toLowerCase();
    const box = opts.viewportBox || { x: 0, y: 0, width: opts.width || 1920, height: opts.height || 1080 };
    const center = opts.center || [0, 10]; // [lon, lat]
    const rotLon = -(opts.rotate ? opts.rotate[0] : center[0]) * DEG2RAD;
    const rotLat = -(opts.rotate ? opts.rotate[1] : center[1]) * DEG2RAD;

    // Auto-compute scale & translation from fitBounds if provided
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
        if (cosc < -0.02) return null; // Backside of globe clipped!
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

      // Default: Natural Earth I
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

  /**
   * True spherical great-circle interpolation (SLERP on unit sphere)
   */
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
      // Guard against antimeridian wrap jumps
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
   * Renders a real Natural Earth cartographic atlas into `svgRoot`.
   * Requires `<script src=".../kit/world-atlas.js"></script>` (window.WORLD_ATLAS_GEOJSON).
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

    // Viewport clip path
    const clipId = '__mk_atlas_clip';
    const clip = svgEl('clipPath', { id: clipId }, defs);
    if (type === 'orthographic' || type === 'globe') {
      svgEl('circle', { cx: cx.toFixed(1), cy: cy.toFixed(1), r: scale.toFixed(1) }, clip);
      const grad = svgEl('radialGradient', { id: '__mk_globe_ocean', cx: '38%', cy: '32%', r: '70%' }, defs);
      svgEl('stop', { offset: '0%', 'stop-color': cfg.oceanHighlight || '#162844' }, grad);
      svgEl('stop', { offset: '100%', 'stop-color': cfg.oceanFill || '#09111E' }, grad);
    } else {
      svgEl('rect', { x: box.x, y: box.y, width: box.width, height: box.height, rx: cfg.borderRadius || 0 }, clip);
    }

    const rootG = svgEl('g', { 'clip-path': `url(#${clipId})` }, svgRoot);

    // 1. Ocean / Sphere Backdrop
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

    // 2. Graticule & Equator
    if (cfg.showGraticule !== false) {
      const gratG = svgEl('g', {
        fill: 'none',
        stroke: cfg.graticuleColor || 'rgba(148, 163, 184, 0.13)',
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
          stroke: cfg.equatorColor || 'rgba(245, 158, 11, 0.35)',
          'stroke-width': '1.6',
          'stroke-dasharray': '7 7',
        }, rootG);
        if (cfg.equatorLabel) {
          const eqPt = project(cfg.equatorLabelLon !== undefined ? cfg.equatorLabelLon : (cfg.center ? cfg.center[0] - 18 : -18), 0);
          if (eqPt) {
            const lbl = svgEl('text', {
              x: eqPt[0].toFixed(1),
              y: (eqPt[1] - 10).toFixed(1),
              fill: cfg.equatorLabelColor || 'rgba(245, 158, 11, 0.78)',
              'font-family': cfg.fontMono || "'JetBrains Mono', monospace",
              'font-size': '12',
              'font-weight': '600',
              'letter-spacing': '2.2',
            }, rootG);
            lbl.textContent = cfg.equatorLabel;
          }
        }
      }
    }

    // 3. Country Polygons (Base + Highlighted ISO-A3 Countries)
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
          fill: fc.fill || '#EA580C',
          'fill-opacity': (lerp(0.18, fc.fillOpacity !== undefined ? fc.fillOpacity : 0.85, hp)).toFixed(3),
          stroke: fc.stroke || '#FDBA74',
          'stroke-width': (fc.strokeWidth || 2.2).toFixed(1),
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

    // Sphere rim stroke for globe
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

    // 4. Geodesic Routes (True Great Circle Slerp)
    const routeHeads = [];
    if (Array.isArray(cfg.routes)) {
      const routeG = svgEl('g', {}, svgRoot);
      for (const rt of cfg.routes) {
        const p = clamp01(rt.progress !== undefined ? rt.progress : 1);
        if (p <= 0.001) {
          routeHeads.push(null);
          continue;
        }
        // Optional full ghost guide line
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
              stroke: rt.color || '#F97316',
              'stroke-opacity': '0.16',
              'stroke-width': (rt.width || 3.5),
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
            stroke: rt.color || '#F97316',
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
            fill: rt.color || '#F97316',
            'fill-opacity': '0.24',
          }, routeG);
          svgEl('circle', {
            cx: lastScreen[0].toFixed(1),
            cy: lastScreen[1].toFixed(1),
            r: '5.5',
            fill: '#FFFFFF',
            stroke: rt.color || '#F97316',
            'stroke-width': '3',
          }, routeG);
        }
        routeHeads.push(lastScreen);
      }
    }

    // 5. Coordinate Pins & Anti-Collision Callout Labels
    const pinPositions = [];
    if (Array.isArray(cfg.pins)) {
      const pinG = svgEl('g', {}, svgRoot);
      for (const pin of cfg.pins) {
        const pt = project(pin.coords[0], pin.coords[1]);
        pinPositions.push(pt);
        if (!pt) continue;
        const pp = clamp01(pin.progress !== undefined ? pin.progress : 1);
        if (pp <= 0.01) continue;

        const col = pin.color || '#F97316';
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
            'font-family': cfg.fontSans || "'Inter', 'Plus Jakarta Sans', system-ui, sans-serif",
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

  // =========================================================================
  // EDITORIAL CHAPTER PALETTES (v7.0 — Breaks Dark-Navy Monotony)
  // =========================================================================

  const PALETTES = {
    warm_archive_paper: {
      name: 'warm_archive_paper',
      bg: '#F4EDE1',
      surface: '#FFFDF8',
      surfaceAlt: '#EAE0CE',
      ink: '#181411',
      muted: '#6B6054',
      accent: '#C84B31',
      accent2: '#1D4ED8',
      grid: 'rgba(24, 20, 17, 0.08)',
      border: 'rgba(24, 20, 17, 0.14)',
      isLight: true,
    },
    editorial_blush_ivory: {
      name: 'editorial_blush_ivory',
      bg: '#FBF3F1',
      surface: '#FFFFFF',
      surfaceAlt: '#F5E4E0',
      ink: '#221218',
      muted: '#7D5864',
      accent: '#D92662',
      accent2: '#EA580C',
      grid: 'rgba(34, 18, 24, 0.07)',
      border: 'rgba(217, 38, 98, 0.18)',
      isLight: true,
    },
    swiss_emerald_ivory: {
      name: 'swiss_emerald_ivory',
      bg: '#F1F6F3',
      surface: '#FFFFFF',
      surfaceAlt: '#DFECE5',
      ink: '#0D231B',
      muted: '#49685C',
      accent: '#059669',
      accent2: '#D97706',
      grid: 'rgba(13, 35, 27, 0.08)',
      border: 'rgba(5, 150, 105, 0.18)',
      isLight: true,
    },
    newsprint_crimson_ink: {
      name: 'newsprint_crimson_ink',
      bg: '#EEEAE2',
      surface: '#FAF8F4',
      surfaceAlt: '#E2DDD2',
      ink: '#141413',
      muted: '#57534E',
      accent: '#B91C1C',
      accent2: '#1E293B',
      grid: 'rgba(20, 20, 19, 0.09)',
      border: 'rgba(20, 20, 19, 0.16)',
      isLight: true,
    },
    terracotta_ochre_sand: {
      name: 'terracotta_ochre_sand',
      bg: '#F2E5D5',
      surface: '#FCF7F0',
      surfaceAlt: '#E5D3BD',
      ink: '#261810',
      muted: '#785A46',
      accent: '#C2410C',
      accent2: '#0F766E',
      grid: 'rgba(38, 24, 16, 0.08)',
      border: 'rgba(194, 65, 12, 0.18)',
      isLight: true,
    },
    cobalt_blueprint: {
      name: 'cobalt_blueprint',
      bg: '#0B1E38',
      surface: '#122B4E',
      surfaceAlt: '#193863',
      ink: '#F8FAFC',
      muted: '#93C5FD',
      accent: '#38BDF8',
      accent2: '#FACC15',
      grid: 'rgba(147, 197, 253, 0.12)',
      border: 'rgba(56, 189, 248, 0.25)',
      isLight: false,
    },
    plum_velvet_editorial: {
      name: 'plum_velvet_editorial',
      bg: '#1D1026',
      surface: '#2A1837',
      surfaceAlt: '#382049',
      ink: '#FAF5FF',
      muted: '#D8B4FE',
      accent: '#F43F5E',
      accent2: '#FBBF24',
      grid: 'rgba(216, 180, 254, 0.11)',
      border: 'rgba(244, 63, 94, 0.28)',
      isLight: false,
    },
    charcoal_gold_ledger: {
      name: 'charcoal_gold_ledger',
      bg: '#131518',
      surface: '#1D2025',
      surfaceAlt: '#272B32',
      ink: '#F5F5F4',
      muted: '#A8A29E',
      accent: '#EAB308',
      accent2: '#34D399',
      grid: 'rgba(245, 245, 244, 0.08)',
      border: 'rgba(234, 179, 8, 0.26)',
      isLight: false,
    },
  };

  function resolvePalette(nameOrObj) {
    if (!nameOrObj) return PALETTES.warm_archive_paper;
    if (typeof nameOrObj === 'string') {
      return PALETTES[nameOrObj] || PALETTES.warm_archive_paper;
    }
    return Object.assign({}, PALETTES.warm_archive_paper, nameOrObj);
  }

  function applyScenePalette(rootEl, nameOrObj) {
    const pal = resolvePalette(nameOrObj);
    const el = rootEl || (typeof document !== 'undefined' ? document.documentElement : null);
    if (el && el.style) {
      el.style.setProperty('--mk-bg', pal.bg);
      el.style.setProperty('--mk-surface', pal.surface);
      el.style.setProperty('--mk-surface-alt', pal.surfaceAlt);
      el.style.setProperty('--mk-ink', pal.ink);
      el.style.setProperty('--mk-muted', pal.muted);
      el.style.setProperty('--mk-accent', pal.accent);
      el.style.setProperty('--mk-accent2', pal.accent2);
      el.style.setProperty('--mk-grid', pal.grid);
      el.style.setProperty('--mk-border', pal.border);
      if (typeof document !== 'undefined' && document.body) {
        document.body.style.background = pal.bg;
        document.body.style.color = pal.ink;
      }
    }
    return pal;
  }

  function htmlEl(tag, styles, parent, text) {
    const el = document.createElement(tag);
    if (styles) Object.assign(el.style, styles);
    if (text !== undefined && text !== null) el.textContent = String(text);
    if (parent) parent.appendChild(el);
    return el;
  }

  // =========================================================================
  // MONOTONE DATA CURVE ENGINE (v7.0 — Follow-Tip Camera + Light/Dark Palettes)
  // =========================================================================

  function renderDataCurve(svgRoot, opts) {
    if (!svgRoot || !opts || !Array.isArray(opts.points) || opts.points.length < 2) return null;
    while (svgRoot.firstChild) svgRoot.removeChild(svgRoot.firstChild);

    const pal = opts.palette ? resolvePalette(opts.palette) : null;
    const isLight = opts.isLight !== undefined ? opts.isLight : (pal ? pal.isLight : false);
    const W = opts.width || 1920;
    const H = opts.height || 1080;
    const liveTime = Number(opts.time || 0);
    svgRoot.setAttribute('viewBox', `0 0 ${W} ${H}`);

    const rawBox = opts.plotBox || { x: 140, y: 260, width: W - 320, height: H - 440 };
    const box = { x: rawBox.x, y: rawBox.y, width: rawBox.width, height: rawBox.height };

    // Anti-collision safe zone against right-side subject cutouts (#subject / .cutout-hero)
    let safeRightX = opts.rightSafeX;
    if (safeRightX === undefined && typeof document !== 'undefined') {
      const cutEl = document.querySelector('#subject, .cutout-hero, [data-cutout-right]');
      if (cutEl && cutEl.getBoundingClientRect) {
        const r = cutEl.getBoundingClientRect();
        if (r.width > 80 && r.left > W * 0.42 && r.left < W) {
          safeRightX = Math.max(box.x + 360, r.left - 85);
        }
      }
    }
    if (safeRightX !== undefined) {
      box.width = Math.max(360, Math.min(box.width, safeRightX - box.x));
    }

    const pts = opts.points;
    const minV = opts.minValue !== undefined ? opts.minValue : Math.min(...pts.map((d) => d.value)) * 0.9;
    const maxV = opts.maxValue !== undefined ? opts.maxValue : Math.max(...pts.map((d) => d.value)) * 1.08;
    const spanV = Math.max(1e-6, maxV - minV);
    const col = opts.color || (pal ? pal.accent : '#EA580C');
    const p = clamp01(opts.progress !== undefined ? opts.progress : 1);

    const defs = svgEl('defs', {}, svgRoot);
    const grad = svgEl('linearGradient', { id: '__mk_curve_fill', x1: '0', y1: '0', x2: '0', y2: '1' }, defs);
    svgEl('stop', { offset: '0%', 'stop-color': col, 'stop-opacity': isLight ? '0.24' : '0.32' }, grad);
    svgEl('stop', { offset: '100%', 'stop-color': col, 'stop-opacity': '0.01' }, grad);

    const clip = svgEl('clipPath', { id: '__mk_curve_clip' }, defs);
    svgEl('rect', {
      x: box.x - 4,
      y: box.y - 36,
      width: (box.width + 8) * p,
      height: box.height + 72,
    }, clip);

    const coords = pts.map((d, idx) => {
      const sx = box.x + (box.width * idx) / (pts.length - 1);
      const sy = box.y + box.height - ((d.value - minV) / spanV) * box.height;
      return { x: sx, y: sy, label: d.label, value: d.value, callout: d.callout || d.milestone || null };
    });

    const exactIdx = p * (coords.length - 1);
    const i0 = Math.floor(exactIdx);
    const i1 = Math.min(coords.length - 1, i0 + 1);
    const frac = exactIdx - i0;
    const headX = lerp(coords[i0].x, coords[i1].x, frac);
    const headY = lerp(coords[i0].y, coords[i1].y, frac);
    const headVal = lerp(coords[i0].value, coords[i1].value, frac);

    // Optional followTip camera group: tracks the rising tip early, then pulls back into full panorama + live drift
    const worldG = svgEl('g', {}, svgRoot);
    if (opts.followTip) {
      const pullBack = easeInOutCubic(clamp01((p - 0.58) / 0.42));
      const camZoom = lerp(1.26, 1.0, pullBack) + Math.sin(liveTime * 0.85) * 0.008;
      const focusX = lerp(headX, W * 0.5, pullBack) + Math.cos(liveTime * 0.7) * 6;
      const focusY = lerp(headY, H * 0.5, pullBack) + Math.sin(liveTime * 0.6) * 4;
      const tx = W * 0.5 - focusX * camZoom;
      const ty = H * 0.5 - focusY * camZoom;
      worldG.setAttribute('transform', `translate(${tx.toFixed(2)}, ${ty.toFixed(2)}) scale(${camZoom.toFixed(4)})`);
    } else if (liveTime > 0) {
      const dx = Math.sin(liveTime * 0.65) * 4.5;
      const dy = Math.cos(liveTime * 0.55) * 3.0;
      const sc = 1 + Math.sin(liveTime * 0.45) * 0.006;
      worldG.setAttribute('transform', `translate(${(W * 0.5 * (1 - sc) + dx).toFixed(2)}, ${(H * 0.5 * (1 - sc) + dy).toFixed(2)}) scale(${sc.toFixed(4)})`);
    }

    // Subtle horizontal reference grid
    const gridN = opts.gridLines !== undefined ? opts.gridLines : 4;
    const gridCol = opts.gridColor || (pal ? pal.grid : (isLight ? 'rgba(15, 23, 42, 0.09)' : 'rgba(148, 163, 184, 0.16)'));
    const gridG = svgEl('g', {}, worldG);
    for (let i = 0; i <= gridN; i++) {
      const gy = box.y + (box.height * i) / gridN;
      svgEl('line', {
        x1: box.x,
        y1: gy.toFixed(1),
        x2: box.x + box.width,
        y2: gy.toFixed(1),
        stroke: gridCol,
        'stroke-width': i === gridN ? '1.8' : '1',
      }, gridG);
    }

    // Smooth Catmull-Rom -> Cubic Bezier spline
    let lineD = `M ${coords[0].x.toFixed(1)},${coords[0].y.toFixed(1)}`;
    for (let i = 0; i < coords.length - 1; i++) {
      const p0 = coords[Math.max(0, i - 1)];
      const p1 = coords[i];
      const p2 = coords[i + 1];
      const p3 = coords[Math.min(coords.length - 1, i + 2)];
      const cp1x = p1.x + (p2.x - p0.x) / 6;
      const cp1y = p1.y + (p2.y - p0.y) / 6;
      const cp2x = p2.x - (p3.x - p1.x) / 6;
      const cp2y = p2.y - (p3.y - p1.y) / 6;
      lineD += ` C ${cp1x.toFixed(1)},${cp1y.toFixed(1)} ${cp2x.toFixed(1)},${cp2y.toFixed(1)} ${p2.x.toFixed(1)},${p2.y.toFixed(1)}`;
    }

    const areaD = `${lineD} L ${coords[coords.length - 1].x.toFixed(1)},${(box.y + box.height).toFixed(1)} L ${coords[0].x.toFixed(1)},${(box.y + box.height).toFixed(1)} Z`;

    const curveG = svgEl('g', { 'clip-path': 'url(#__mk_curve_clip)' }, worldG);
    svgEl('path', { d: areaD, fill: 'url(#__mk_curve_fill)' }, curveG);
    svgEl('path', {
      d: lineD,
      fill: 'none',
      stroke: col,
      'stroke-width': opts.strokeWidth || 5.5,
      'stroke-linecap': 'round',
    }, curveG);

    const lblCol = opts.labelColor || (pal ? pal.muted : (isLight ? '#475569' : 'rgba(203, 213, 225, 0.90)'));
    const pillBg = isLight ? 'rgba(255, 255, 255, 0.95)' : 'rgba(15, 23, 42, 0.92)';
    const pillFg = isLight ? (pal ? pal.ink : '#0F172A') : '#F8FAFC';
    const dotBg = isLight ? '#FFFFFF' : '#0F172A';

    for (let idx = 0; idx < coords.length; idx++) {
      const c = coords[idx];
      const t = svgEl('text', {
        x: c.x.toFixed(1),
        y: (box.y + box.height + 38).toFixed(1),
        'text-anchor': 'middle',
        fill: lblCol,
        'font-family': opts.fontMono || "'JetBrains Mono', 'Consolas', monospace",
        'font-size': '16',
        'font-weight': '700',
      }, worldG);
      t.textContent = c.label;

      const nodeThresh = idx / Math.max(1, coords.length - 1);
      if (c.callout && p >= nodeThresh - 0.02) {
        const pop = clamp01((p - (nodeThresh - 0.02)) / 0.14);
        svgEl('circle', {
          cx: c.x.toFixed(1),
          cy: c.y.toFixed(1),
          r: '5.5',
          fill: dotBg,
          stroke: col,
          'stroke-width': '3',
          opacity: pop.toFixed(3),
        }, worldG);
        const pillW = Math.max(118, c.callout.length * 11 + 28);
        const pillH = 34;
        const py = c.y - 48;
        const mg = svgEl('g', { opacity: pop.toFixed(3) }, worldG);
        svgEl('rect', {
          x: (c.x - pillW * 0.5).toFixed(1),
          y: py.toFixed(1),
          width: pillW.toFixed(1),
          height: pillH,
          rx: '17',
          fill: pillBg,
          stroke: col,
          'stroke-opacity': '0.65',
          'stroke-width': '1.6',
        }, mg);
        const mt = svgEl('text', {
          x: c.x.toFixed(1),
          y: (py + 22.5).toFixed(1),
          'text-anchor': 'middle',
          fill: pillFg,
          'font-family': opts.fontMono || "'JetBrains Mono', 'Consolas', monospace",
          'font-size': '15',
          'font-weight': '800',
        }, mg);
        mt.textContent = c.callout;
      }
    }

    if (p > 0.02) {
      const pulseR = 14 + Math.sin(liveTime * 4.2) * 4.5;
      svgEl('line', {
        x1: headX.toFixed(1),
        y1: headY.toFixed(1),
        x2: headX.toFixed(1),
        y2: (box.y + box.height).toFixed(1),
        stroke: col,
        'stroke-opacity': '0.28',
        'stroke-dasharray': '5 5',
        'stroke-width': '1.5',
      }, worldG);
      svgEl('circle', { cx: headX.toFixed(1), cy: headY.toFixed(1), r: pulseR.toFixed(1), fill: col, 'fill-opacity': '0.22' }, worldG);
      svgEl('circle', { cx: headX.toFixed(1), cy: headY.toFixed(1), r: '6.8', fill: '#FFFFFF', stroke: col, 'stroke-width': '3.4' }, worldG);
    }

    return { headX, headY, headVal, coords };
  }

  // =========================================================================
  // ARCHETYPE 3: 2.5D SPATIAL CAMERA JOURNEY (Vox / Johnny Harris Infinite Desk)
  // =========================================================================

  function renderCameraJourney(container, opts) {
    if (!container || !opts || !Array.isArray(opts.stops) || !opts.stops.length) return null;
    const pal = resolvePalette(opts.palette || 'warm_archive_paper');
    const W = opts.width || 1920;
    const H = opts.height || 1080;
    const t = Number(opts.time || 0);
    const dur = Math.max(1.5, Number(opts.duration || 8));
    const p = clamp01(t / dur);

    container.innerHTML = '';
    Object.assign(container.style, {
      position: 'relative',
      width: `${W}px`,
      height: `${H}px`,
      overflow: 'hidden',
      background: pal.bg,
      color: pal.ink,
      fontFamily: opts.fontSans || "'Space Grotesk', 'Plus Jakarta Sans', system-ui, sans-serif",
    });

    const stops = opts.stops;
    const worldW = 3600;
    const worldH = 2200;

    // Determine active camera target along stops -> final pullback overview in last 18%
    const overviewPhase = clamp01((p - 0.80) / 0.20);
    const travelP = clamp01(p / 0.80) * (stops.length - 1);
    const idx0 = Math.min(stops.length - 1, Math.floor(travelP));
    const idx1 = Math.min(stops.length - 1, idx0 + 1);
    const segT = easeInOutCubic(travelP - idx0);

    const sx = lerp(stops[idx0].x, stops[idx1].x, segT);
    const sy = lerp(stops[idx0].y, stops[idx1].y, segT);
    const sZoom = lerp(stops[idx0].zoom || 1.12, stops[idx1].zoom || 1.12, segT);

    // Center bounding box of all stops for panoramic finale
    const minX = Math.min(...stops.map((s) => s.x));
    const maxX = Math.max(...stops.map((s) => s.x));
    const minY = Math.min(...stops.map((s) => s.y));
    const maxY = Math.max(...stops.map((s) => s.y));
    const midX = (minX + maxX) * 0.5;
    const midY = (minY + maxY) * 0.5;
    const fitZoom = Math.min(0.84, Math.min((W * 0.72) / Math.max(500, maxX - minX + 520), (H * 0.68) / Math.max(380, maxY - minY + 380)));

    const camX = lerp(sx, midX, easeInOutCubic(overviewPhase)) + Math.sin(t * 0.8) * 14;
    const camY = lerp(sy, midY, easeInOutCubic(overviewPhase)) + Math.cos(t * 0.65) * 10;
    const camZ = lerp(sZoom, fitZoom, easeInOutCubic(overviewPhase)) * (1 + Math.sin(t * 0.55) * 0.012);
    const camRot = Math.sin(t * 0.45) * 0.55;

    const world = htmlEl('div', {
      position: 'absolute',
      left: '0px',
      top: '0px',
      width: `${worldW}px`,
      height: `${worldH}px`,
      backgroundImage: `linear-gradient(to right, ${pal.grid} 1px, transparent 1px), linear-gradient(to bottom, ${pal.grid} 1px, transparent 1px)`,
      backgroundSize: '80px 80px',
      transformOrigin: '0 0',
      transform: `translate(${(W * 0.5 - camX * camZ).toFixed(2)}px, ${(H * 0.52 - camY * camZ).toFixed(2)}px) scale(${camZ.toFixed(4)}) rotate(${camRot.toFixed(3)}deg)`,
    }, container);

    // SVG path connecting stops
    const svg = svgEl('svg', {
      viewBox: `0 0 ${worldW} ${worldH}`,
      style: `position:absolute;inset:0;width:${worldW}px;height:${worldH}px;overflow:visible;pointer-events:none;`,
    }, world);

    if (stops.length >= 2) {
      let d = `M ${stops[0].x} ${stops[0].y}`;
      for (let i = 0; i < stops.length - 1; i++) {
        const a = stops[i];
        const b = stops[i + 1];
        const cx1 = lerp(a.x, b.x, 0.5);
        const cy1 = a.y;
        const cx2 = lerp(a.x, b.x, 0.5);
        const cy2 = b.y;
        d += ` C ${cx1} ${cy1}, ${cx2} ${cy2}, ${b.x} ${b.y}`;
      }
      svgEl('path', {
        d,
        fill: 'none',
        stroke: pal.border,
        'stroke-width': '5',
        'stroke-dasharray': '12 12',
      }, svg);

      const pathEl = svgEl('path', {
        d,
        fill: 'none',
        stroke: pal.accent,
        'stroke-width': '7',
        'stroke-linecap': 'round',
      }, svg);
      strokeProgress(pathEl, clamp01(p / 0.82), 4200);
    }

    // Render spatial stop cards
    stops.forEach((st, idx) => {
      const appearAt = (idx / Math.max(1, stops.length)) * 0.68;
      const sp = spring(Math.max(0, (p - appearAt) * dur), { stiffness: 175, damping: 21 });
      const cardW = st.width || 430;
      const card = htmlEl('div', {
        position: 'absolute',
        left: `${st.x - cardW * 0.5}px`,
        top: `${st.y - 125}px`,
        width: `${cardW}px`,
        padding: '26px 30px',
        background: pal.surface,
        border: `2px solid ${idx === idx1 || overviewPhase > 0.4 ? pal.accent : pal.border}`,
        borderRadius: '18px',
        boxShadow: pal.isLight ? '0 24px 55px rgba(24,20,17,0.12)' : '0 24px 60px rgba(0,0,0,0.48)',
        transform: `scale(${(0.75 + 0.25 * sp).toFixed(3)}) translateY(${((1 - sp) * 34).toFixed(1)}px)`,
        opacity: clamp01(sp * 1.2).toFixed(3),
      }, world);

      const badgeRow = htmlEl('div', { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }, card);
      htmlEl('span', {
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: '16px',
        fontWeight: '800',
        letterSpacing: '2px',
        textTransform: 'uppercase',
        color: pal.accent,
        background: pal.surfaceAlt,
        padding: '5px 12px',
        borderRadius: '999px',
      }, badgeRow, st.tag || `ETAPA 0${idx + 1}`);

      if (st.year) {
        htmlEl('span', {
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: '18px',
          fontWeight: '700',
          color: pal.muted,
        }, badgeRow, st.year);
      }

      if (st.photo) {
        htmlEl('img', {
          width: '100%',
          height: '165px',
          objectFit: 'cover',
          borderRadius: '10px',
          marginBottom: '14px',
          border: `1px solid ${pal.border}`,
        }, card).src = st.photo;
      }

      if (st.stat) {
        htmlEl('div', {
          fontSize: '46px',
          fontWeight: '900',
          lineHeight: '1.02',
          letterSpacing: '-1.5px',
          color: pal.ink,
          marginBottom: '6px',
        }, card, st.stat);
      }

      htmlEl('div', {
        fontSize: '25px',
        fontWeight: '800',
        lineHeight: '1.2',
        color: pal.ink,
        marginBottom: st.sub ? '8px' : '0',
      }, card, st.title || '');

      if (st.sub) {
        htmlEl('div', {
          fontSize: '17px',
          fontWeight: '500',
          lineHeight: '1.35',
          color: pal.muted,
        }, card, st.sub);
      }
    });

    // Top persistent editorial header banner
    if (opts.kicker || opts.headline) {
      const hdr = htmlEl('div', {
        position: 'absolute',
        left: '78px',
        top: '56px',
        padding: '16px 26px',
        background: pal.isLight ? 'rgba(255,253,248,0.90)' : 'rgba(15,23,42,0.86)',
        borderLeft: `5px solid ${pal.accent}`,
        borderRadius: '0 12px 12px 0',
        boxShadow: '0 12px 32px rgba(0,0,0,0.08)',
      }, container);
      if (opts.kicker) {
        htmlEl('div', {
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: '14px',
          fontWeight: '800',
          letterSpacing: '2.4px',
          textTransform: 'uppercase',
          color: pal.accent,
          marginBottom: '4px',
        }, hdr, opts.kicker);
      }
      if (opts.headline) {
        htmlEl('div', {
          fontSize: '28px',
          fontWeight: '800',
          letterSpacing: '-0.6px',
          color: pal.ink,
        }, hdr, opts.headline);
      }
    }

    return { camX, camY, camZ };
  }

  // =========================================================================
  // ARCHETYPE 4: MECHANICAL ODOMETER & CONTRAST LEDGER
  // =========================================================================

  function renderOdometerCounter(container, opts) {
    if (!container || !opts) return null;
    const pal = resolvePalette(opts.palette || 'charcoal_gold_ledger');
    const W = opts.width || 1920;
    const H = opts.height || 1080;
    const t = Number(opts.time || 0);
    const dur = Math.max(1.5, Number(opts.duration || 8));
    const p = clamp01(t / dur);

    container.innerHTML = '';
    Object.assign(container.style, {
      position: 'relative',
      width: `${W}px`,
      height: `${H}px`,
      overflow: 'hidden',
      background: pal.bg,
      color: pal.ink,
      fontFamily: opts.fontSans || "'Space Grotesk', system-ui, sans-serif",
    });

    // Live drifting subtle background ledger lines
    const bgGrid = htmlEl('div', {
      position: 'absolute',
      inset: '-80px',
      backgroundImage: `linear-gradient(to right, ${pal.grid} 1px, transparent 1px), linear-gradient(to bottom, ${pal.grid} 1px, transparent 1px)`,
      backgroundSize: '96px 96px',
      transform: `translate(${(t * 14) % 96}px, ${(t * 8) % 96}px)`,
    }, container);
    void bgGrid;

    const rollEase = easeOutExpo(clamp01(p / 0.68));
    const targetVal = Number(opts.targetValue || 750);
    const curVal = lerp(Number(opts.startValue || 0), targetVal, rollEase);
    const decimals = opts.decimals || 0;
    const formatted = curVal.toFixed(decimals);

    const cardScale = 1 + Math.sin(t * 0.7) * 0.008;
    const stage = htmlEl('div', {
      position: 'absolute',
      left: '110px',
      right: '110px',
      top: '120px',
      bottom: '120px',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      transform: `scale(${cardScale.toFixed(4)})`,
    }, container);

    // Top row
    const topBar = htmlEl('div', { display: 'flex', justifyContent: 'space-between', alignItems: 'center' }, stage);
    htmlEl('div', {
      fontFamily: "'JetBrains Mono', monospace",
      fontSize: '18px',
      fontWeight: '800',
      letterSpacing: '3px',
      textTransform: 'uppercase',
      color: pal.accent,
      padding: '8px 18px',
      border: `1.5px solid ${pal.border}`,
      borderRadius: '999px',
      background: pal.surface,
    }, topBar, opts.kicker || 'AUDITORIA FINANCEIRA');

    htmlEl('div', {
      fontFamily: "'JetBrains Mono', monospace",
      fontSize: '16px',
      color: pal.muted,
    }, topBar, opts.codeLabel || `FONTE VERIFICADA • T+${t.toFixed(1)}s`);

    // Center mechanical odometer drums
    const midWrap = htmlEl('div', { display: 'flex', flexDirection: 'column', gap: '18px' }, stage);
    if (opts.headline) {
      htmlEl('div', {
        fontSize: '38px',
        fontWeight: '700',
        color: pal.muted,
        letterSpacing: '-0.6px',
      }, midWrap, opts.headline);
    }

    const drumRow = htmlEl('div', { display: 'flex', alignItems: 'baseline', gap: '10px', flexWrap: 'wrap' }, midWrap);
    if (opts.prefix) {
      htmlEl('span', {
        fontSize: '86px',
        fontWeight: '800',
        color: pal.accent,
        marginRight: '10px',
      }, drumRow, opts.prefix);
    }

    const drumH = opts.drumHeight || 168;
    for (let i = 0; i < formatted.length; i++) {
      const ch = formatted[i];
      if (ch >= '0' && ch <= '9') {
        const digit = Number(ch);
        const slot = htmlEl('div', {
          width: `${Math.round(drumH * 0.66)}px`,
          height: `${drumH}px`,
          overflow: 'hidden',
          background: pal.surface,
          border: `2px solid ${pal.border}`,
          borderRadius: '16px',
          position: 'relative',
          boxShadow: pal.isLight ? 'inset 0 6px 16px rgba(0,0,0,0.06)' : 'inset 0 10px 24px rgba(0,0,0,0.55)',
        }, drumRow);
        const strip = htmlEl('div', {
          position: 'absolute',
          left: '0',
          top: '0',
          width: '100%',
          transform: `translateY(${(-digit * drumH + Math.sin(t * 2.2 + i) * 1.5).toFixed(1)}px)`,
        }, slot);
        for (let d = 0; d <= 9; d++) {
          htmlEl('div', {
            height: `${drumH}px`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: `${Math.round(drumH * 0.72)}px`,
            fontWeight: '900',
            color: pal.ink,
          }, strip, String(d));
        }
      } else {
        htmlEl('span', {
          fontSize: `${Math.round(drumH * 0.65)}px`,
          fontWeight: '900',
          color: pal.muted,
          padding: '0 4px',
        }, drumRow, ch === '.' ? ',' : ch);
      }
    }

    if (opts.suffix) {
      htmlEl('span', {
        fontSize: '78px',
        fontWeight: '900',
        color: pal.ink,
        letterSpacing: '-2px',
        marginLeft: '14px',
      }, drumRow, opts.suffix);
    }

    // Bottom contrast bar (e.g. R$ 750 MI vs 0,2% resolvidas)
    if (opts.contrastLabel) {
      const cProg = easeOutQuint(clamp01((p - 0.34) / 0.38));
      const cBox = htmlEl('div', {
        background: pal.surface,
        border: `1.5px solid ${pal.border}`,
        borderRadius: '18px',
        padding: '26px 34px',
        opacity: cProg.toFixed(3),
        transform: `translateY(${((1 - cProg) * 26).toFixed(1)}px)`,
      }, stage);

      const rowLbl = htmlEl('div', { display: 'flex', justifyContent: 'space-between', marginBottom: '14px', alignItems: 'baseline' }, cBox);
      htmlEl('span', { fontSize: '24px', fontWeight: '700', color: pal.ink }, rowLbl, opts.contrastLabel);
      htmlEl('span', {
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: '30px',
        fontWeight: '900',
        color: pal.accent2,
      }, rowLbl, opts.contrastValue || '');

      const track = htmlEl('div', {
        width: '100%',
        height: '18px',
        background: pal.surfaceAlt,
        borderRadius: '999px',
        overflow: 'hidden',
        position: 'relative',
      }, cBox);
      const ratio = clamp01(Number(opts.contrastRatio !== undefined ? opts.contrastRatio : 0.08));
      htmlEl('div', {
        width: `${Math.max(1.2, ratio * 100 * cProg).toFixed(2)}%`,
        height: '100%',
        background: pal.accent2,
        borderRadius: '999px',
      }, track);
    }

    return { curVal };
  }

  // =========================================================================
  // ARCHETYPE 5: 3D PERSPECTIVE SOCIAL / UI FEED STAGE
  // =========================================================================

  function renderUIFeed3D(container, opts) {
    if (!container || !opts) return null;
    const pal = resolvePalette(opts.palette || 'editorial_blush_ivory');
    const W = opts.width || 1920;
    const H = opts.height || 1080;
    const t = Number(opts.time || 0);
    const dur = Math.max(1.5, Number(opts.duration || 8));
    const p = clamp01(t / dur);

    container.innerHTML = '';
    Object.assign(container.style, {
      position: 'relative',
      width: `${W}px`,
      height: `${H}px`,
      overflow: 'hidden',
      background: pal.bg,
      color: pal.ink,
      perspective: '1500px',
      fontFamily: opts.fontSans || "'Plus Jakarta Sans', system-ui, sans-serif",
    });

    // Left editorial thesis column
    const leftCol = htmlEl('div', {
      position: 'absolute',
      left: '108px',
      top: '150px',
      width: '720px',
      zIndex: '4',
    }, container);

    const enterP = easeOutQuint(clamp01(p / 0.28));
    leftCol.style.opacity = enterP.toFixed(3);
    leftCol.style.transform = `translateY(${((1 - enterP) * 32).toFixed(1)}px)`;

    htmlEl('div', {
      fontFamily: "'JetBrains Mono', monospace",
      fontSize: '16px',
      fontWeight: '800',
      letterSpacing: '2.8px',
      textTransform: 'uppercase',
      color: pal.accent,
      marginBottom: '18px',
    }, leftCol, opts.kicker || 'ECONOMIA DA ATENÇÃO');

    htmlEl('div', {
      fontSize: '68px',
      fontWeight: '900',
      lineHeight: '1.04',
      letterSpacing: '-2px',
      color: pal.ink,
      marginBottom: '24px',
    }, leftCol, opts.headline || '');

    if (opts.subheadline) {
      htmlEl('div', {
        fontSize: '26px',
        fontWeight: '500',
        lineHeight: '1.42',
        color: pal.muted,
        marginBottom: '36px',
      }, leftCol, opts.subheadline);
    }

    const metrics = opts.metrics || [];
    const mRow = htmlEl('div', { display: 'flex', gap: '22px', flexWrap: 'wrap' }, leftCol);
    metrics.forEach((m, idx) => {
      const mp = spring(Math.max(0, t - 0.35 - idx * 0.22), { stiffness: 180, damping: 20 });
      const box = htmlEl('div', {
        background: pal.surface,
        border: `1.5px solid ${pal.border}`,
        borderRadius: '16px',
        padding: '18px 26px',
        boxShadow: '0 16px 38px rgba(0,0,0,0.06)',
        transform: `scale(${(0.84 + 0.16 * mp).toFixed(3)})`,
        opacity: clamp01(mp * 1.2).toFixed(3),
      }, mRow);
      htmlEl('div', { fontSize: '38px', fontWeight: '900', color: pal.accent, letterSpacing: '-1px' }, box, m.value);
      htmlEl('div', { fontFamily: "'JetBrains Mono', monospace", fontSize: '14px', fontWeight: '700', color: pal.muted, textTransform: 'uppercase', letterSpacing: '1.4px' }, box, m.label);
    });

    // Right 3D Tilted Glass Device Mockup with continuous floating tilt
    const rotY = -18 + Math.sin(t * 0.9) * 4.5;
    const rotX = 7 + Math.cos(t * 0.75) * 2.5;
    const floatY = Math.sin(t * 1.25) * 12;

    const phone = htmlEl('div', {
      position: 'absolute',
      right: '210px',
      top: '95px',
      width: '450px',
      height: '870px',
      borderRadius: '48px',
      background: '#120D16',
      border: `8px solid ${pal.isLight ? '#2A1F2D' : '#334155'}`,
      boxShadow: '0 45px 95px rgba(20, 10, 24, 0.28)',
      overflow: 'hidden',
      transformStyle: 'preserve-3d',
      transform: `translateY(${floatY.toFixed(1)}px) rotateY(${rotY.toFixed(2)}deg) rotateX(${rotX.toFixed(2)}deg)`,
    }, container);

    if (opts.screenImage) {
      htmlEl('img', {
        position: 'absolute',
        inset: '0',
        width: '100%',
        height: '100%',
        objectFit: 'cover',
        opacity: '0.82',
        transform: `scale(${(1.03 + p * 0.08).toFixed(3)})`,
      }, phone).src = opts.screenImage;
    }

    // Dark gradient overlay inside phone for crisp UI legibility
    htmlEl('div', {
      position: 'absolute',
      inset: '0',
      background: 'linear-gradient(180deg, rgba(0,0,0,0.62) 0%, rgba(0,0,0,0.12) 40%, rgba(0,0,0,0.82) 100%)',
    }, phone);

    // Animated Instagram-style multi-story segmented progress bars at top!
    const segCount = opts.storySegments || 12;
    const segBar = htmlEl('div', {
      position: 'absolute',
      top: '26px',
      left: '22px',
      right: '22px',
      display: 'flex',
      gap: '5px',
    }, phone);
    const activeFloat = p * segCount;
    for (let s = 0; s < segCount; s++) {
      const fillPct = clamp01(activeFloat - s) * 100;
      const segTrack = htmlEl('div', {
        flex: '1',
        height: '4px',
        background: 'rgba(255,255,255,0.28)',
        borderRadius: '4px',
        overflow: 'hidden',
      }, segBar);
      htmlEl('div', {
        width: `${fillPct.toFixed(1)}%`,
        height: '100%',
        background: '#FFFFFF',
      }, segTrack);
    }

    // Live viewer pill inside phone
    const liveUsers = Math.round(lerp(opts.liveStart || 320000, opts.livePeak || 912000, easeOutQuint(clamp01(p / 0.75))) + Math.sin(t * 5) * 1850);
    const topHud = htmlEl('div', {
      position: 'absolute',
      top: '46px',
      left: '24px',
      right: '24px',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
    }, phone);
    htmlEl('div', {
      background: '#E11D48',
      color: '#FFFFFF',
      fontSize: '14px',
      fontWeight: '800',
      padding: '6px 14px',
      borderRadius: '999px',
      letterSpacing: '1.2px',
    }, topHud, opts.liveBadge || '● AO VIVO');
    htmlEl('div', {
      background: 'rgba(0,0,0,0.55)',
      color: '#FFFFFF',
      fontFamily: "'JetBrains Mono', monospace",
      fontSize: '15px',
      fontWeight: '700',
      padding: '6px 14px',
      borderRadius: '999px',
    }, topHud, `👁 ${(liveUsers / 1000).toFixed(0)} mil`);

    // Rising engagement / notification cards floating in 3D around phone
    const cards = opts.feedCards || [
      { user: 'Novo Story #08', text: 'Link de compra fixado na tela' },
      { user: 'Pico simultâneo', text: '+900 mil pessoas assistindo' },
      { user: ' Engajamento diário', text: 'Rotina em tempo real 24/7' },
    ];
    cards.forEach((c, idx) => {
      const cp = spring(Math.max(0, t - 0.5 - idx * 0.45), { stiffness: 165, damping: 19 });
      const bob = Math.sin(t * 1.8 + idx * 1.4) * 7;
      const bubble = htmlEl('div', {
        position: 'absolute',
        right: idx % 2 === 0 ? '575px' : '125px',
        top: `${265 + idx * 195 + bob}px`,
        width: '295px',
        padding: '16px 20px',
        background: pal.surface,
        border: `1.5px solid ${pal.border}`,
        borderRadius: '16px',
        boxShadow: '0 20px 45px rgba(0,0,0,0.14)',
        transform: `scale(${(0.7 + 0.3 * cp).toFixed(3)})`,
        opacity: clamp01(cp * 1.2).toFixed(3),
        zIndex: '6',
      }, container);
      htmlEl('div', { fontSize: '13px', fontWeight: '800', color: pal.accent, textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '4px' }, bubble, c.user);
      htmlEl('div', { fontSize: '17px', fontWeight: '700', color: pal.ink, lineHeight: '1.25' }, bubble, c.text);
    });

    return { liveUsers };
  }

  // =========================================================================
  // ARCHETYPE 6: TACTILE OVERHEAD DOSSIER DESK (Investigative Paper & Stamp)
  // =========================================================================

  function renderDossierDesk(container, opts) {
    if (!container || !opts) return null;
    const pal = resolvePalette(opts.palette || 'newsprint_crimson_ink');
    const W = opts.width || 1920;
    const H = opts.height || 1080;
    const t = Number(opts.time || 0);
    const dur = Math.max(1.5, Number(opts.duration || 8));
    const p = clamp01(t / dur);

    container.innerHTML = '';
    Object.assign(container.style, {
      position: 'relative',
      width: `${W}px`,
      height: `${H}px`,
      overflow: 'hidden',
      background: pal.bg,
      color: pal.ink,
      fontFamily: opts.fontSans || "'Plus Jakarta Sans', system-ui, sans-serif",
    });

    // Continuous rostrum overhead camera push + subtle rotation across entire scene
    const camScale = lerp(1.0, 1.075, p);
    const camRot = lerp(-1.1, 0.8, p);
    const desk = htmlEl('div', {
      position: 'absolute',
      inset: '0',
      backgroundImage: `radial-gradient(${pal.grid} 1.5px, transparent 1.5px)`,
      backgroundSize: '34px 34px',
      transform: `scale(${camScale.toFixed(4)}) rotate(${camRot.toFixed(3)}deg)`,
      transformOrigin: '50% 50%',
    }, container);

    // Background secondary folder sheet
    htmlEl('div', {
      position: 'absolute',
      left: '260px',
      top: '125px',
      width: '1380px',
      height: '830px',
      background: pal.surfaceAlt,
      borderRadius: '10px',
      border: `1.5px solid ${pal.border}`,
      transform: 'rotate(-2.4deg)',
      boxShadow: '0 24px 60px rgba(0,0,0,0.12)',
    }, desk);

    // Primary investigative document sheet sliding in
    const docEnter = easeOutQuint(clamp01(p / 0.25));
    const doc = htmlEl('div', {
      position: 'absolute',
      left: '290px',
      top: '110px',
      width: '1340px',
      height: '850px',
      background: pal.surface,
      borderRadius: '8px',
      border: `1.5px solid ${pal.border}`,
      padding: '58px 74px',
      boxSizing: 'border-box',
      boxShadow: '0 32px 80px rgba(0,0,0,0.16)',
      transform: `translateY(${((1 - docEnter) * 70).toFixed(1)}px) rotate(0.6deg)`,
    }, desk);

    // Document masthead
    const mast = htmlEl('div', {
      display: 'flex',
      justifyContent: 'space-between',
      borderBottom: `3px solid ${pal.ink}`,
      paddingBottom: '18px',
      marginBottom: '34px',
    }, doc);
    htmlEl('div', {
      fontFamily: "'JetBrains Mono', monospace",
      fontSize: '18px',
      fontWeight: '800',
      letterSpacing: '2.5px',
      color: pal.accent,
      textTransform: 'uppercase',
    }, mast, opts.kicker || 'AUTO DE INFRAÇÃO & DOSSIÊ PÚBLICO');
    htmlEl('div', {
      fontFamily: "'JetBrains Mono', monospace",
      fontSize: '17px',
      fontWeight: '700',
      color: pal.muted,
    }, mast, opts.docNumber || 'PROC. Nº 2025/GO-MP');

    htmlEl('div', {
      fontFamily: "'Playfair Display', Georgia, serif",
      fontSize: '56px',
      fontWeight: '900',
      lineHeight: '1.08',
      color: pal.ink,
      marginBottom: '34px',
    }, doc, opts.headline || '');

    // Clauses / Evidence rows with progressive ink highlight
    const clauses = opts.clauses || [];
    clauses.forEach((cl, idx) => {
      const startAt = 0.18 + idx * 0.16;
      const hlProg = easeOutQuint(clamp01((p - startAt) / 0.20));
      const row = htmlEl('div', {
        display: 'flex',
        alignItems: 'baseline',
        gap: '22px',
        padding: '18px 20px',
        marginBottom: '14px',
        borderBottom: `1px dashed ${pal.border}`,
        position: 'relative',
      }, doc);

      if (cl.highlight) {
        htmlEl('div', {
          position: 'absolute',
          left: '0',
          top: '6px',
          bottom: '6px',
          width: `${(hlProg * 100).toFixed(1)}%`,
          background: 'rgba(185, 28, 28, 0.11)',
          borderLeft: `5px solid ${pal.accent}`,
          pointerEvents: 'none',
        }, row);
      }

      htmlEl('span', {
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: '17px',
        fontWeight: '800',
        color: pal.accent,
        minWidth: '140px',
      }, row, cl.tag || `ITEM 0${idx + 1}`);

      htmlEl('span', {
        fontSize: '25px',
        fontWeight: '700',
        color: pal.ink,
        lineHeight: '1.3',
      }, row, cl.text || '');
    });

    // Rubber Stamp Slam at p >= 0.56
    if (opts.stampText && p >= 0.52) {
      const sp = spring((p - 0.52) * dur, { stiffness: 260, damping: 18 });
      const stampScale = lerp(2.1, 1.0, clamp01(sp));
      htmlEl('div', {
        position: 'absolute',
        right: '86px',
        bottom: '68px',
        padding: '16px 34px',
        border: `6px solid ${pal.accent}`,
        borderRadius: '12px',
        color: pal.accent,
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: '34px',
        fontWeight: '900',
        letterSpacing: '4px',
        textTransform: 'uppercase',
        transform: `rotate(-9deg) scale(${stampScale.toFixed(3)})`,
        opacity: clamp01((p - 0.52) * 8).toFixed(3),
        boxShadow: `inset 0 0 0 2px ${pal.accent}`,
      }, doc, opts.stampText);
    }

    return { camScale };
  }

  // =========================================================================
  // ARCHETYPE 7: DIRECTED NETWORK & CASH-FLOW GRAPH (Live Streaming Packets)
  // =========================================================================

  function renderNetworkGraph(svgRoot, opts) {
    if (!svgRoot || !opts || !Array.isArray(opts.nodes)) return null;
    while (svgRoot.firstChild) svgRoot.removeChild(svgRoot.firstChild);

    const pal = resolvePalette(opts.palette || 'terracotta_ochre_sand');
    const W = opts.width || 1920;
    const H = opts.height || 1080;
    const t = Number(opts.time || 0);
    const dur = Math.max(1.5, Number(opts.duration || 8));
    const p = clamp01(t / dur);
    svgRoot.setAttribute('viewBox', `0 0 ${W} ${H}`);

    // Background rect + subtle drift group
    svgEl('rect', { x: 0, y: 0, width: W, height: H, fill: pal.bg }, svgRoot);

    const camScale = 1 + Math.sin(t * 0.6) * 0.012;
    const gWorld = svgEl('g', {
      transform: `translate(${(W * 0.5 * (1 - camScale) + Math.sin(t * 0.7) * 8).toFixed(2)}, ${(H * 0.5 * (1 - camScale) + Math.cos(t * 0.5) * 6).toFixed(2)}) scale(${camScale.toFixed(4)})`,
    }, svgRoot);

    const nodeMap = {};
    opts.nodes.forEach((n) => { nodeMap[n.id] = n; });

    // Header text in SVG
    if (opts.kicker) {
      const kt = svgEl('text', {
        x: 96,
        y: 86,
        fill: pal.accent,
        'font-family': "'JetBrains Mono', monospace",
        'font-size': '17',
        'font-weight': '800',
        'letter-spacing': '2.6',
      }, gWorld);
      kt.textContent = opts.kicker.toUpperCase();
    }
    if (opts.headline) {
      const ht = svgEl('text', {
        x: 96,
        y: 142,
        fill: pal.ink,
        'font-family': "'Space Grotesk', system-ui, sans-serif",
        'font-size': '46',
        'font-weight': '800',
      }, gWorld);
      ht.textContent = opts.headline;
    }

    // Edges + continuously flowing packets right through t == dur!
    (opts.edges || []).forEach((ed, idx) => {
      const a = nodeMap[ed.from];
      const b = nodeMap[ed.to];
      if (!a || !b) return;
      const ep = easeOutQuint(clamp01((p - 0.10 - idx * 0.07) / 0.28));
      if (ep <= 0.01) return;

      const mx = (a.x + b.x) * 0.5;
      const my = (a.y + b.y) * 0.5 - (ed.curve !== undefined ? ed.curve : 55);
      const pathD = `M ${a.x} ${a.y} Q ${mx} ${my} ${b.x} ${b.y}`;
      const col = ed.accent ? pal.accent : pal.accent2;

      const pEl = svgEl('path', {
        d: pathD,
        fill: 'none',
        stroke: col,
        'stroke-width': ed.width || 4,
        'stroke-opacity': (0.55 * ep).toFixed(3),
      }, gWorld);
      strokeProgress(pEl, ep, 1400);

      // 3 streaming pulse packets along quadratic Bezier
      for (let k = 0; k < 3; k++) {
        const u = ((t * 0.42 + k / 3 + idx * 0.17) % 1);
        const px = (1 - u) * (1 - u) * a.x + 2 * (1 - u) * u * mx + u * u * b.x;
        const py = (1 - u) * (1 - u) * a.y + 2 * (1 - u) * u * my + u * u * b.y;
        svgEl('circle', {
          cx: px.toFixed(1),
          cy: py.toFixed(1),
          r: '6.5',
          fill: col,
          opacity: ep.toFixed(3),
        }, gWorld);
      }

      if (ed.label && ep > 0.55) {
        const lx = 0.25 * a.x + 0.5 * mx + 0.25 * b.x;
        const ly = 0.25 * a.y + 0.5 * my + 0.25 * b.y - 12;
        const lt = svgEl('text', {
          x: lx.toFixed(1),
          y: ly.toFixed(1),
          'text-anchor': 'middle',
          fill: pal.ink,
          'font-family': "'JetBrains Mono', monospace",
          'font-size': '15',
          'font-weight': '800',
        }, gWorld);
        lt.textContent = ed.label;
      }
    });

    // Nodes
    opts.nodes.forEach((n, idx) => {
      const np = spring(Math.max(0, t - idx * 0.14), { stiffness: 185, damping: 20 });
      const bw = n.width || 270;
      const bh = n.height || 108;
      const ng = svgEl('g', {
        transform: `translate(${n.x}, ${n.y}) scale(${(0.6 + 0.4 * np).toFixed(3)})`,
        opacity: clamp01(np * 1.25).toFixed(3),
      }, gWorld);

      svgEl('rect', {
        x: -bw * 0.5,
        y: -bh * 0.5,
        width: bw,
        height: bh,
        rx: '20',
        fill: n.primary ? pal.accent : pal.surface,
        stroke: n.primary ? pal.accent : pal.border,
        'stroke-width': '2.5',
      }, ng);

      const t1 = svgEl('text', {
        x: 0,
        y: n.sub ? -8 : 8,
        'text-anchor': 'middle',
        fill: n.primary ? '#FFFFFF' : pal.ink,
        'font-family': "'Space Grotesk', system-ui, sans-serif",
        'font-size': n.primary ? '26' : '22',
        'font-weight': '800',
      }, ng);
      t1.textContent = n.label;

      if (n.sub) {
        const t2 = svgEl('text', {
          x: 0,
          y: 24,
          'text-anchor': 'middle',
          fill: n.primary ? 'rgba(255,255,255,0.88)' : pal.muted,
          'font-family': "'JetBrains Mono', monospace",
          'font-size': '15',
          'font-weight': '700',
        }, ng);
        t2.textContent = n.sub;
      }
    });

    return { nodes: opts.nodes.length };
  }

  // =========================================================================
  // ARCHETYPE 8: DIAGONAL VERSUS SPLIT (Two Worlds Colliding)
  // =========================================================================

  function renderVersusSplit(container, opts) {
    if (!container || !opts) return null;
    const pal = resolvePalette(opts.palette || 'plum_velvet_editorial');
    const W = opts.width || 1920;
    const H = opts.height || 1080;
    const t = Number(opts.time || 0);
    const dur = Math.max(1.5, Number(opts.duration || 8));
    const p = clamp01(t / dur);

    container.innerHTML = '';
    Object.assign(container.style, {
      position: 'relative',
      width: `${W}px`,
      height: `${H}px`,
      overflow: 'hidden',
      background: pal.bg,
      fontFamily: opts.fontSans || "'Space Grotesk', system-ui, sans-serif",
    });

    const sweep = easeOutQuint(clamp01(p / 0.34));
    const splitShift = lerp(18, 50, sweep) + Math.sin(t * 1.1) * 2.4;
    const skew = 7;

    // Left / Warm editorial side
    const leftSide = htmlEl('div', {
      position: 'absolute',
      inset: '0',
      background: opts.leftBg || '#F7EFE6',
      color: '#181311',
      clipPath: `polygon(0 0, ${(splitShift + skew).toFixed(2)}% 0, ${(splitShift - skew).toFixed(2)}% 100%, 0 100%)`,
    }, container);

    // Right / Contrasting institutional side
    const rightSide = htmlEl('div', {
      position: 'absolute',
      inset: '0',
      background: opts.rightBg || pal.bg,
      color: pal.ink,
      clipPath: `polygon(${(splitShift + skew).toFixed(2)}% 0, 100% 0, 100% 100%, ${(splitShift - skew).toFixed(2)}% 100%)`,
    }, container);

    const fillHalf = (parent, sideCfg, isRight) => {
      if (sideCfg.image) {
        htmlEl('img', {
          position: 'absolute',
          [isRight ? 'right' : 'left']: '0',
          bottom: '0',
          width: '48%',
          height: '88%',
          objectFit: 'cover',
          opacity: '0.26',
          transform: `scale(${(1.02 + p * 0.06).toFixed(3)})`,
        }, parent).src = sideCfg.image;
      }
      const box = htmlEl('div', {
        position: 'absolute',
        [isRight ? 'right' : 'left']: '105px',
        top: '210px',
        width: '670px',
        textAlign: isRight ? 'right' : 'left',
      }, parent);

      htmlEl('div', {
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: '17px',
        fontWeight: '800',
        letterSpacing: '2.6px',
        textTransform: 'uppercase',
        color: sideCfg.accent || (isRight ? pal.accent : '#C84B31'),
        marginBottom: '16px',
      }, box, sideCfg.kicker || '');

      htmlEl('div', {
        fontSize: '64px',
        fontWeight: '900',
        lineHeight: '1.05',
        letterSpacing: '-1.8px',
        marginBottom: '20px',
      }, box, sideCfg.title || '');

      if (sideCfg.stat) {
        htmlEl('div', {
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: '42px',
          fontWeight: '900',
          color: sideCfg.accent || pal.accent2,
          marginBottom: '12px',
        }, box, sideCfg.stat);
      }

      if (sideCfg.sub) {
        htmlEl('div', {
          fontSize: '24px',
          fontWeight: '500',
          opacity: '0.84',
          lineHeight: '1.38',
        }, box, sideCfg.sub);
      }
    };

    fillHalf(leftSide, opts.left || {}, false);
    fillHalf(rightSide, opts.right || {}, true);

    // Diagonal glowing divider blade + VS medallion
    const blade = svgEl('svg', {
      viewBox: `0 0 ${W} ${H}`,
      style: 'position:absolute;inset:0;width:100%;height:100%;pointer-events:none;',
    }, container);
    const xTop = ((splitShift + skew) / 100) * W;
    const xBot = ((splitShift - skew) / 100) * W;
    svgEl('line', {
      x1: xTop.toFixed(1),
      y1: 0,
      x2: xBot.toFixed(1),
      y2: H,
      stroke: pal.accent,
      'stroke-width': '6',
    }, blade);

    const badgeSp = spring(Math.max(0, t - 0.25), { stiffness: 210, damping: 18 });
    htmlEl('div', {
      position: 'absolute',
      left: `${((xTop + xBot) * 0.5 - 46).toFixed(1)}px`,
      top: `${H * 0.5 - 46}px`,
      width: '92px',
      height: '92px',
      borderRadius: '999px',
      background: pal.accent,
      color: '#FFFFFF',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: "'JetBrains Mono', monospace",
      fontSize: '26px',
      fontWeight: '900',
      boxShadow: '0 18px 45px rgba(0,0,0,0.38)',
      transform: `scale(${badgeSp.toFixed(3)})`,
    }, container, opts.badge || 'VS');

    return { splitShift };
  }

  // =========================================================================
  // ARCHETYPE 9: PROPORTIONAL 100-BLOCK WAFFLE MATRIX (Scale & Inequality)
  // =========================================================================

  function renderWaffleScale(svgRoot, opts) {
    if (!svgRoot || !opts) return null;
    while (svgRoot.firstChild) svgRoot.removeChild(svgRoot.firstChild);

    const pal = resolvePalette(opts.palette || 'swiss_emerald_ivory');
    const W = opts.width || 1920;
    const H = opts.height || 1080;
    const t = Number(opts.time || 0);
    const dur = Math.max(1.5, Number(opts.duration || 8));
    const p = clamp01(t / dur);
    svgRoot.setAttribute('viewBox', `0 0 ${W} ${H}`);

    svgEl('rect', { x: 0, y: 0, width: W, height: H, fill: pal.bg }, svgRoot);

    // Left narrative block
    const gText = svgEl('g', {}, svgRoot);
    const kt = svgEl('text', {
      x: 108,
      y: 195,
      fill: pal.accent,
      'font-family': "'JetBrains Mono', monospace",
      'font-size': '17',
      'font-weight': '800',
      'letter-spacing': '2.6',
    }, gText);
    kt.textContent = (opts.kicker || 'ESCALA PROPORCIONAL').toUpperCase();

    const lines = String(opts.headline || '').split('\n');
    lines.forEach((ln, idx) => {
      const ht = svgEl('text', {
        x: 108,
        y: 268 + idx * 66,
        fill: pal.ink,
        'font-family': "'Space Grotesk', system-ui, sans-serif",
        'font-size': '56',
        'font-weight': '900',
      }, gText);
      ht.textContent = ln;
    });

    if (opts.bigStat) {
      const st = svgEl('text', {
        x: 108,
        y: 295 + lines.length * 66 + 74,
        fill: pal.accent,
        'font-family': "'JetBrains Mono', monospace",
        'font-size': '92',
        'font-weight': '900',
      }, gText);
      st.textContent = opts.bigStat;
    }
    if (opts.subheadline) {
      const sub = svgEl('text', {
        x: 108,
        y: 295 + lines.length * 66 + 132,
        fill: pal.muted,
        'font-family': "'Plus Jakarta Sans', system-ui, sans-serif",
        'font-size': '25',
        'font-weight': '600',
      }, gText);
      sub.textContent = opts.subheadline;
    }

    // Right 10x10 (100-unit) proportional grid with continuous wave breathing
    const cols = opts.cols || 10;
    const rows = opts.rows || 10;
    const total = cols * rows;
    const highlighted = Math.max(1, Math.min(total, Math.round(Number(opts.highlightCount || 96))));
    const cell = opts.cellSize || 58;
    const gap = opts.gap || 12;
    const gx0 = opts.gridX || 1040;
    const gy0 = opts.gridY || 195;

    const fillReveal = easeOutQuint(clamp01(p / 0.65)) * total;
    for (let i = 0; i < total; i++) {
      const r = Math.floor(i / cols);
      const c = i % cols;
      const active = i < fillReveal;
      const isHi = i < highlighted;
      const wave = Math.sin(t * 2.6 - (r + c) * 0.35) * 2.2;
      const sc = active ? 1 : 0.45;
      const cx = gx0 + c * (cell + gap);
      const cy = gy0 + r * (cell + gap) + wave;

      svgEl('rect', {
        x: cx.toFixed(1),
        y: cy.toFixed(1),
        width: (cell * sc).toFixed(1),
        height: (cell * sc).toFixed(1),
        rx: '11',
        fill: !active ? pal.surfaceAlt : (isHi ? pal.accent : pal.accent2),
        opacity: active ? (isHi ? '0.92' : '1') : '0.32',
      }, svgRoot);
    }

    return { total, highlighted };
  }

  // =========================================================================
  // ARCHETYPE 10: SWISS KINETIC MANIFESTO POSTER
  // =========================================================================

  function renderKineticManifesto(container, opts) {
    if (!container || !opts) return null;
    const pal = resolvePalette(opts.palette || 'warm_archive_paper');
    const W = opts.width || 1920;
    const H = opts.height || 1080;
    const t = Number(opts.time || 0);
    const dur = Math.max(1.5, Number(opts.duration || 6));

    container.innerHTML = '';
    Object.assign(container.style, {
      position: 'relative',
      width: `${W}px`,
      height: `${H}px`,
      overflow: 'hidden',
      background: pal.bg,
      color: pal.ink,
      fontFamily: opts.fontSans || "'Space Grotesk', system-ui, sans-serif",
    });

    if (opts.watermark) {
      htmlEl('div', {
        position: 'absolute',
        right: '-30px',
        bottom: '-70px',
        fontSize: '360px',
        fontWeight: '900',
        color: pal.ink,
        opacity: '0.045',
        letterSpacing: '-12px',
        transform: `translateX(${(-t * 18).toFixed(1)}px)`,
        pointerEvents: 'none',
      }, container, opts.watermark);
    }

    const wrap = htmlEl('div', {
      position: 'absolute',
      left: '130px',
      right: '130px',
      top: '180px',
    }, container);

    if (opts.kicker) {
      htmlEl('div', {
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: '18px',
        fontWeight: '800',
        letterSpacing: '3px',
        textTransform: 'uppercase',
        color: pal.accent,
        marginBottom: '28px',
      }, wrap, opts.kicker);
    }

    const words = String(opts.statement || '').split(/\s+/).filter(Boolean);
    const lineWrap = htmlEl('div', { display: 'flex', flexWrap: 'wrap', gap: '18px 24px', alignItems: 'baseline' }, wrap);
    words.forEach((w, idx) => {
      const wp = spring(Math.max(0, t - idx * 0.08), { stiffness: 200, damping: 22 });
      const isAccent = opts.highlightWords && opts.highlightWords.some((hw) => w.toLowerCase().includes(hw.toLowerCase()));
      htmlEl('span', {
        fontSize: `${opts.fontSize || 88}px`,
        fontFamily: isAccent ? "'Playfair Display', Georgia, serif" : 'inherit',
        fontStyle: isAccent ? 'italic' : 'normal',
        fontWeight: '900',
        lineHeight: '1.06',
        letterSpacing: '-2.2px',
        color: isAccent ? pal.accent : pal.ink,
        transform: `translateY(${((1 - wp) * 42).toFixed(1)}px)`,
        opacity: clamp01(wp * 1.25).toFixed(3),
      }, lineWrap, w);
    });

    return { words: words.length };
  }

  global.MotionKit = {
    PALETTES,
    resolvePalette,
    applyScenePalette,
    clamp01,
    lerp,
    easeOutQuint,
    easeInOutCubic,
    easeOutExpo,
    spring,
    progress,
    stagger,
    safeZone,
    rostrumTransform,
    strokeProgress,
    injectFilmGrain,
    greatCirclePoints,
    renderWorldAtlas,
    renderDataCurve,
    renderCameraJourney,
    renderOdometerCounter,
    renderUIFeed3D,
    renderDossierDesk,
    renderNetworkGraph,
    renderVersusSplit,
    renderWaffleScale,
    renderKineticManifesto,
  };
})(window);
