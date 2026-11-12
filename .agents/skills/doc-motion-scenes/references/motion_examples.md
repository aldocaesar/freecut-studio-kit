# Motion Graphics Scene Templates (`doc-motion-scenes` v7.0)

Every `<project_dir>/motion/SXX.html` must expose deterministic frame stepping via `window.__setFrame = function(frameIdx, fps) { ... }`, load `world-atlas.js` + `motion-kit.js` (note: from `<agent_root>/projects/<slug>/motion/SXX.html`, the kit path is `../../../.agents/skills/doc-motion-scenes/kit/`), and **animate continuously until `t == duration`** (pass `time: t, duration: DUR` so `78% -> 94%` never freezes).

## Anti-Cloning Rules (`v7.0` Hard Gates)
1. **Never clone `#080C14` dark navy slides**: Rotate across `MotionKit.PALETTES` (`warm_archive_paper`, `editorial_blush_ivory`, `swiss_emerald_ivory`, `newsprint_crimson_ink`, `terracotta_ochre_sand`, `cobalt_blueprint`, `plum_velvet_editorial`, `charcoal_gold_ledger`). At least **50% of motion scenes** in a video must use light/warm/colored palettes.
2. **Never repeat the same `motion_family` back-to-back**: Choose from the 10 engines below so consecutive motion scenes have completely different spatial choreography.
3. **Cap right-side subject cutouts in motion scenes at `<= 20%`**: Let the typography, 3D UI, camera journey, map, dossier desk, or network graph be the hero — do NOT paste `#subject` on the right of every chart!

---

## 1. Geodesic Atlas (`MotionKit.renderWorldAtlas` — `projection: 'naturalEarth'`)
```javascript
MotionKit.renderWorldAtlas(document.getElementById('atlas-svg'), {
  width: 1920, height: 1080,
  projection: 'naturalEarth',
  fitBounds: [[-85, -36], [18, 45]],
  padding: 0.16,
  oceanFill: '#0B1E38', landFill: '#163256', landStroke: 'rgba(147,197,253,0.24)',
  focusCountries: [
    { iso: 'USA', fill: '#38BDF8', stroke: '#E0F2FE', fillOpacity: 0.85 },
    { iso: 'BRA', fill: '#FACC15', stroke: '#FEF9C3', fillOpacity: 0.90, progress: p },
  ],
  routes: [{ from: [-74.17, 40.73], to: [-49.26, -16.68], progress: routeP, color: '#FACC15', width: 4.5 }],
  pins: [
    { coords: [-74.17, 40.73], label: 'Danbury, EUA', sublabel: 'ORIGEM', color: '#38BDF8', labelSide: 'left' },
    { coords: [-49.26, -16.68], label: 'Goiânia, GO', sublabel: 'POLO DIGITAL', color: '#FACC15', labelSide: 'right', progress: p },
  ],
});
```

## 2. 3D Rotating Orthographic Globe (`MotionKit.renderWorldAtlas` — `projection: 'orthographic'`)
```javascript
MotionKit.renderWorldAtlas(document.getElementById('globe-svg'), {
  width: 1920, height: 1080,
  projection: 'orthographic',
  center: [MotionKit.lerp(-46, 52, p), MotionKit.lerp(-14, 24, p)],
  scale: 430 + Math.sin(t * 0.8) * 8,
  oceanFill: '#EAE0CE', landFill: '#C8B89D', landStroke: 'rgba(24,20,17,0.22)',
  focusCountries: [{ iso: 'BRA', fill: '#C84B31' }, { iso: 'ARE', fill: '#0F766E', progress: p }],
  routes: [{ from: [-46.63, -23.55], to: [55.27, 25.20], progress: routeP, color: '#C84B31', width: 4.5 }],
});
```

## 3. Follow-Tip Editorial Data Curve (`MotionKit.renderDataCurve`)
```javascript
MotionKit.renderDataCurve(document.getElementById('curve-svg'), {
  width: 1920, height: 1080,
  palette: 'swiss_emerald_ivory',
  followTip: true,
  time: t,
  progress: MotionKit.progress(t, 0.2, DUR * 0.72, MotionKit.easeInOutCubic),
  plotBox: { x: 150, y: 270, width: 1620, height: 590 },
  points: [
    { label: '2021', value: 10, callout: 'R$ 10 MI' },
    { label: '2022', value: 168, callout: 'R$ 168 MI' },
    { label: '2023', value: 325, callout: 'R$ 325 MI' },
    { label: '2024', value: 750, callout: 'R$ 750 MI' },
  ],
});
```

## 4. 2.5D Spatial Camera Journey (`MotionKit.renderCameraJourney`)
```javascript
MotionKit.renderCameraJourney(document.getElementById('stage'), {
  palette: 'warm_archive_paper', time: t, duration: DUR,
  kicker: 'LINHA DO TEMPO ESPACIAL', headline: 'Da Dança Caseira à Holding Bilionária',
  stops: [
    { x: 900, y: 780, year: '2016', tag: 'ORIGEM', stat: '100 MIL', title: 'Quarto em Governador Valadares', sub: 'Primeiros vídeos sem roteiro fixo', zoom: 1.18 },
    { x: 1750, y: 1080, year: '2020', tag: 'ESCALA', stat: '10 MILHÕES', title: 'Mudança para Londrina e Goiânia', sub: 'Lives diárias viram hábito nacional', zoom: 1.15 },
    { x: 2620, y: 760, year: '2021', tag: 'VIRADA', stat: 'WEPINK', title: 'De Publi para Sócia Majoritária', sub: ' Audiência convertida em estoque próprio', zoom: 1.18 },
  ],
});
```

## 5. Mechanical Odometer & Contrast Ledger (`MotionKit.renderOdometerCounter`)
```javascript
MotionKit.renderOdometerCounter(document.getElementById('stage'), {
  palette: 'charcoal_gold_ledger', time: t, duration: DUR,
  kicker: 'BALANÇO AUDITADO • 2024',
  headline: 'Faturamento Bruto Anual Declarado',
  prefix: 'R$', targetValue: 750, suffix: 'MILHÕES',
  contrastLabel: 'Índice de Resolução Inicial vs Volume de Queixas (Reclame Aqui / Procon)',
  contrastValue: '90 MIL QUEIXAS', contrastRatio: 0.14,
});
```

## 6. 3D Perspective Social UI Feed (`MotionKit.renderUIFeed3D`)
```javascript
MotionKit.renderUIFeed3D(document.getElementById('stage'), {
  palette: 'editorial_blush_ivory', time: t, duration: DUR,
  kicker: 'ENGENHARIA DE RETENÇÃO',
  headline: 'A Novela Real de 24 Horas',
  subheadline: 'Dezenas de micro-episódios diários transformam rotina doméstica em vitrine contínua.',
  screenImage: '../media/images/S17.jpg',
  liveStart: 280000, livePeak: 920000,
  metrics: [{ value: '50M+', label: 'Seguidores' }, { value: '900K', label: 'Pico em Live' }],
});
```

## 7. Tactile Overhead Investigative Dossier Desk (`MotionKit.renderDossierDesk`)
```javascript
MotionKit.renderDossierDesk(document.getElementById('stage'), {
  palette: 'newsprint_crimson_ink', time: t, duration: DUR,
  kicker: 'MINISTÉRIO PÚBLICO & PROCON-GO', docNumber: 'ACP • 2025/GO',
  headline: 'Autuação por Atrasos, Reembolsos e Vícios em Lives',
  clauses: [
    { tag: 'CLÁUSULA 01', text: 'Mais de 90 mil reclamações registradas em 12 meses de operação.', highlight: true },
    { tag: 'CLÁUSULA 02', text: 'Indenização por danos morais coletivos fixada em R$ 5 milhões.', highlight: true },
    { tag: 'CLÁUSULA 03', text: 'Proibição de novas lives promocionais sem estoque comprovado.', highlight: false },
  ],
  stampText: 'MULTA R$ 5 MI',
});
```

## 8. Directed Network & Cash-Flow Graph (`MotionKit.renderNetworkGraph`)
```javascript
MotionKit.renderNetworkGraph(document.getElementById('net-svg'), {
  palette: 'terracotta_ochre_sand', time: t, duration: DUR,
  kicker: 'ARQUITETURA DE AFILIAÇÃO', headline: 'Como o Tráfego dos Stories Alimenta as Plataformas',
  nodes: [
    { id: 'stories', x: 340, y: 560, label: 'Stories Diários', sub: '50M Seguidores' },
    { id: 'link', x: 960, y: 380, label: 'Link de Cadastro', sub: 'Comissão / CPA + RevShare', primary: true },
    { id: 'plataforma', x: 1580, y: 560, label: 'Operadoras de Bets', sub: 'Volume Bilionário' },
    { id: 'holding', x: 960, y: 780, label: 'Cachês Publicitários', sub: 'Contratos Milionários' },
  ],
  edges: [
    { from: 'stories', to: 'link', label: 'CLIQUE DIRETO', accent: true, curve: 65 },
    { from: 'link', to: 'plataforma', label: 'DEPÓSITO PIX', accent: true, curve: 65 },
    { from: 'plataforma', to: 'holding', label: 'REPASSE CONTRATUAL', accent: false, curve: -65 },
  ],
});
```

## 9. Diagonal Versus Split (`MotionKit.renderVersusSplit`)
```javascript
MotionKit.renderVersusSplit(document.getElementById('stage'), {
  palette: 'plum_velvet_editorial', time: t, duration: DUR,
  left: { kicker: 'IMAGEM PÚBLICA', title: 'Família, Fé e Carisma Popular', stat: '53 MILHÕES', sub: 'Maior vitrine digital do país' },
  right: { kicker: 'ESCRUTÍNIO NO SENADO', title: 'CPI das Bets em Brasília', stat: 'MAIO • 2025', sub: 'Questionamentos sobre contratos e publicidade' },
});
```

## 10. Proportional 100-Block Waffle Matrix (`MotionKit.renderWaffleScale`)
```javascript
MotionKit.renderWaffleScale(document.getElementById('waffle-svg'), {
  palette: 'swiss_emerald_ivory', time: t, duration: DUR,
  kicker: 'DIMENSÃO DEMOGRÁFICA', headline: '1 Influenciadora =\n1/4 do Brasil Conectado',
  bigStat: '53 MILHÕES', subheadline: 'Audiência superior à população inteira da Colômbia ou Espanha.',
  highlightCount: 78,
});
```
