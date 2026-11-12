---
name: "doc-lottie-overlays"
description: "Generates sleek, <15 KB transparent Bodymovin/Lottie (.json) vector overlays in batch from storyboard.json (--project-dir) or individually onto FreeCut track_fg_3 synced to spoken words."
---

# Editorial Lottie Vector Overlays (`doc-lottie-overlays` v6.4)

Generates ultra-lightweight (`< 15 KB`) transparent Bodymovin `.json` vector animations placed on `track_fg_3` (`type: "lottie"`).

## Zero-Bloat Batch Workflow (Preferred for Long Videos!)
Do **NOT** run `generate_lottie.py` 20+ separate times in the shell! Simply declare `lottie_overlay` (`file`, `kind`, `x`, `y`, `width`, `height`, `offset_frames`) on 25%–40% of scenes inside `storyboard.json` — `finish_freecut.py` (or `generate_lottie.py --project-dir "<project_dir>"`) generates all `.json` files in `< 0.2s` in one call!

## Available Presets (`kind`)

| `kind` | Purpose | Recommended Placement (`16:9` center-origin) |
|---|---|---|
| `marker_highlight` | Translucent marker-pen sweep over newspaper/article clippings (`press_evidence_highlight`) | Over headline/quote (`width: 780, height: 96`, `#FACC15`) |
| `pointer_arrow` | Curved editorial callout arrow pointing at a subject or detail | Near target (`width: 360, height: 220`) |
| `minimal_lower_third` | Vertical accent pillar + subtle dark glass lower-third rule | `x: -450, y: 385, width: 760, height: 150` |
| `focus_corner_brackets` | Crisp investigative viewfinder brackets locking onto an entity | Around subject (`width: 640, height: 480`) |
| `handdrawn_underline` | Organic cubic-bezier ink underline under key numbers/dates | Beneath hero stat (`width: 640, height: 110`) |
| `handdrawn_circle` | Organic ink ring drawing around visual evidence | Around detail (`width: 440, height: 440`) |
| `pulse_beacon` | Cartographic / telemetry sonar ring | On map target (`width: 240, height: 240`) |

## Batch or Single CLI Usage

```bash
python "<SKILL_DIR>/scripts/generate_lottie.py" --project-dir "<project_dir>"
```
*(Single-file mode `--kind <preset> --duration 4.0 --out "<file.json>"` also remains supported.)*
