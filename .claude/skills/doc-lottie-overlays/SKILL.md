---
name: "doc-lottie-overlays"
description: "Generates sleek, <15 KB transparent Bodymovin/Lottie (.json) vector overlays in batch from storyboard.json (--project-dir) onto FreeCut track_fg_3 synced to spoken words, enforcing v7.0 anti-spam rotation across brackets, ink underlines, arrows, circles, and OCR-aligned highlights."
---

# Editorial Lottie Vector Overlays (`doc-lottie-overlays` v7.0)

Generates ultra-lightweight (`< 15 KB`) transparent Bodymovin `.json` vector animations placed on `track_fg_3` (`type` `"lottie"`).

## Zero-Bloat Batch Workflow & v7.0 Anti-Spam Rules
1. Do **NOT** run `generate_lottie.py` 20+ separate times in the shell! Declare `lottie_overlay` (`file`, `kind`, `x`, `y`, `width`, `height`, `offset_frames`) on selective scenes inside `storyboard.json` — `finish_freecut.py` generates all `.json` files in `< 0.2s` in one call!
2. **NO YELLOW HIGHLIGHTER SPAM (`<= 2` per 10 minutes!)**: Never put `marker_highlight` on every news clip! `assemble_freecut.py` v7.0 automatically rotates 5 press treatments (`tilted_3d_push`, `dossier_focus_brackets`, `pull_quote_editorial`, `headline_underline_ink`, and RapidOCR-aligned `ocr_marker_highlight` capped at `<= 2` per 10 min).

## Available Presets (`kind`)

| `kind` | Purpose | Recommended Placement (`16:9` center-origin) |
|---|---|---|
| `focus_corner_brackets` | Crisp investigative viewfinder brackets locking onto evidence or subjects | Around headline/subject (`width` 720, `height` 180) |
| `handdrawn_underline` | Organic cubic-bezier ink underline sweeping under key numbers or headlines | Beneath headline/stat (`width` 640, `height` 95) |
| `pointer_arrow` | Curved editorial callout arrow pointing at a detail | Near target (`width` 360, `height` 220) |
| `minimal_lower_third` | Vertical accent pillar + subtle dark glass lower-third rule | Varied left/right safe zones (`width` 760, `height` 150) |
| `handdrawn_circle` | Organic ink ring drawing around visual evidence | Around detail (`width` 440, `height` 440) |
| `pulse_beacon` | Cartographic / telemetry sonar ring | On map target (`width` 240, `height` 240) |
| `marker_highlight` | Translucent yellow marker sweep (**strictly `<= 2` per 10-min video!**) | RapidOCR-aligned over key headline (`#FACC15`) |

## Batch CLI Usage

```bash
python -B "<SKILL_DIR>/scripts/generate_lottie.py" --project-dir "<project_dir>"
```
*(Single-file mode `--kind <preset> --duration 4.0 --out "<file.json>"` also remains supported.)*
