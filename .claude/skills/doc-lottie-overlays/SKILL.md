---
name: "doc-lottie-overlays"
description: "Generates sleek, <15 KB transparent Bodymovin/Lottie (.json) vector overlays in batch from storyboard.json (--project-dir) onto FreeCut track_fg_3 synced to spoken words, styled from style_dna and matched strictly to the video's genre (v8.0)."
---

# Genre-Matched Lottie Vector Overlays (`doc-lottie-overlays` v8.0)

Generates ultra-lightweight (`< 15 KB`) transparent Bodymovin `.json` vector animations placed on `track_fg_3` (`type` `"lottie"`), inheriting colors directly from `storyboard.json -> style_dna` (`accent` & `accent_secondary`).

## Genre Discipline & Anti-Spam Rules
1. **Batch Only:** Declare `lottie_overlay` (`file`, `kind`, `x`, `y`, `width`, `height`, `offset_frames`) on selective scenes (`15%–30%` of scenes — never spam every clip!) inside `storyboard.json`. `finish_freecut.py` builds all `.json` files in `< 0.2s`.
2. **Match Overlay to Genre (Zero Investigative Vices in Entertainment/Comedy!):**
   - **Comedy / Pop / Gaming / Creator / Lifestyle:** Use `spark_burst`, `pointer_arrow`, `handdrawn_circle`, or `handdrawn_underline`. **NEVER** put investigative `focus_corner_brackets`, `pulse_beacon`, or `marker_highlight` on humor/fiction/pop crossover videos!
   - **Journalism / Investigation / Documentary:** Rotate `focus_corner_brackets`, `handdrawn_underline`, `minimal_lower_third`, `pointer_arrow`, and `marker_highlight` (`<= 2` yellow markers per 10 min!).
   - **Geography / Telemetry / Science:** Use `pulse_beacon` or `pointer_arrow` ONLY on real coordinates, maps, or technical diagrams.

## Available Presets (`kind`)

| `kind` | Genre Fit & Purpose | Typical Size (`16:9` center-origin) |
|---|---|---|
| `spark_burst` | Radial 8-ray starburst pop for punchlines, pop culture, milestones, reveals | `width` 280, `height` 280 |
| `pointer_arrow` | Curved callout arrow pointing at a character, prop, or detail | `width` 360, `height` 220 |
| `handdrawn_underline` | Organic cubic-bezier stroke sweeping under a key number or title | `width` 620, `height` 95 |
| `handdrawn_circle` | Organic ring drawing around a detail on screen | `width` 420, `height` 420 |
| `minimal_lower_third` | Clean accent pillar + subtle rule | `width` 760, `height` 150 |
| `focus_corner_brackets` | *Journalism/Investigation only:* viewfinder brackets on evidence | `width` 720, `height` 180 |
| `pulse_beacon` | *Maps/Telemetry only:* sonar ring on real geographic target | `width` 240, `height` 240 |
| `marker_highlight` | *Press proof only (`<= 2` per 10 min):* RapidOCR-aligned `#FACC15` sweep | Over headline |

## Batch CLI Usage

```bash
python -B "<SKILL_DIR>/scripts/generate_lottie.py" --project-dir "<project_dir>"
```
