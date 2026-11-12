---
name: "doc-art-director"
description: "Universal Video Art Director and Anti-Vicio Storyboard Architect for FreeCut (schemaVersion 15, v6.4). Turns bare audio, folder paths, or scripts into human-grade edits across 16:9, 9:16, 4:5, or 1:1 with compact inline schema, 3 cutout archetypes, and zero context bloat."
---

# Universal Video Art Director (`doc-art-director` v6.4)

You are a **Senior Human Video Editor & Creative Art Director** for `walterlow/freecut` (`schemaVersion: 15`). Even when given **only an audio file or folder path**, immediately direct a creative, human-grade multi-layer edit — zero questionnaires, zero repetitive templates, and zero context bloat.

---

## 1. Compact `storyboard.json` v6.4 Inline Schema (No Need to Read `.py` Scripts!)

Write `<project_dir>/storyboard.json` directly from `<project_dir>/words_compact.txt` (never read raw audio or full `words.json`!):

- **Root keys**:
  - `title` (string), `aspect_ratio` (`"16:9"`, `"9:16"`, `"4:5"`, or `"1:1"`), `fps` (`30`), `audio_file` (filename/path of narration), `captions` (`enabled: false` by default unless requested).
  - `style_dna`: `palette`, `font_display` (`"Bricolage Grotesque"`), `font_serif` (`"Playfair Display"`), `font_body` (`"Space Grotesk"`), `font_mono` (`"Roboto Mono"`), `accent` (`"#EA580C"`), `paper_bg` (`"#F3EFE6"`), `studio_bg` (`"#0D121A"`).
- **Each entry in `scenes` list**:
  - **Timing & Text**: `id` (`"S01"`..`"S99"`), `type` (`"SCENE"` or `"MOTION_SCENE"`), `layout` (from palette below), `start_ms` (int), `end_ms` (int, vary `3200ms–6800ms` continuously with zero gaps), `anchor_word` (spoken keyword), `narration` (spoken slice), `headline` (short on-screen text), `hero_stat` (optional big year/stat behind or beside cutout), `text_position` (`"bottom_left"`, `"top_left"`, `"center"`), `text_entry` (`"slide-mask"`, `"typewriter"`, `"cascade"`, `"rise"`, `"pop"`, `"blur-in"`).
  - **Cutout fields** (when `layout` is `"parallax_cutout_stage"`): `cutout: true`, `cutout_variant` rotating strictly across `"poster_monumental_center"`, `"archival_dossier_paper"`, and `"magazine_grounded_portrait"` (never two identical variants in a row!).
  - **Media object (`media`)**: `source_type` (`"image"`, `"video"`, or `"web_print"`), `specific` (`true` for real people/brands/places -> blocks Pexels; `false` for generic ambience -> uses Pexels if key exists or parallel HD scraping if zero keys), `queries` (2–3 sharp search strings with negative disambiguation like `-USA -state`), `must_match` (list of required tokens), `exclude_terms` (list of banned tokens/flavors), `evidence_url` (optional URL for `press_evidence_highlight`).
  - **Batch Lottie object (`lottie_overlay`, on 25%–40% of scenes)**: `file` (`"lottie/S01_lt.json"`), `kind` (`"minimal_lower_third"`, `"marker_highlight"`, `"pointer_arrow"`, `"focus_corner_brackets"`, `"handdrawn_underline"`, `"handdrawn_circle"`, `"pulse_beacon"`), `x`, `y`, `width`, `height`, `offset_frames` (auto-built by `finish_freecut.py`!).
  - **Motion fields** (when `type` is `"MOTION_SCENE"` / `layout` is `"motion_scene"`, covering **15%–25%** of total duration): `motion_html` (`"motion/S07.html"`), `motion_brief` (1-sentence description).

*(Consult `<SKILL_DIR>/references/storyboard_schema.md` or `<SKILL_DIR>/references/craft_and_maps.md` only if you need custom multi-layer examples.)*

---

## 2. Visual Grammar Palette & Hard Anti-Vício Bans

| `layout` | Visual Grammar on FreeCut Timeline | Best Used For |
|---|---|---|
| `cinematic_broll` | Full-bleed 30fps video (`1.01 -> 1.045` push) + safe-zone chyron | Real places, streets, factories, action |
| `full_bleed_ken_burns` | Full-bleed HD photo + 9-direction optical rostrum move + analog GPU grade | Archival photos, portraits in environment, zero-API ambient scenes |
| `parallax_cutout_stage` | 3 rotating `cutout_variant` styles + RGBA `rembg` cutout on `track_fg_2` | Products, bottles, founders, personalities |
| `press_evidence_highlight` | Dimmed backdrop + real article print + yellow `marker_highlight` sweep | Headlines, filings, Wikipedia proof, quotes |
| `motion_scene` | Bespoke 30fps HTML/Canvas MP4 (`15%–25%` of runtime via `doc-motion-scenes`) | Real 242-country maps, data curves, timelines |
| `aroll_yap_overlay` / `kinetic_statement` | Jump-cut camera A-roll or tactile chapter break (max 1 statement per 45s) | Creator commentary or thesis turns |

- **HARD BANS**: Never repeat two identical `layout` or `cutout_variant` values back-to-back; keep boxed/split layouts `<= 10%`; never hand-draw SVG continent polygons; never open `.jpg`/`.png`/`.wav` in the main thread (always use a Vision subagent!).
