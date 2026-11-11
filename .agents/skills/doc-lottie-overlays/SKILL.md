---
name: doc-lottie-overlays
description: Generates sleek, <15 KB transparent Bodymovin/Lottie (.json) vector overlays (`minimal_lower_third`, `marker_highlight`, `pointer_arrow`, `focus_corner_brackets`, `handdrawn_underline`, `handdrawn_circle`, `pulse_beacon`) placed natively on FreeCut's `track_fg_3` synced to spoken words.
---

# Editorial Lottie Vector Overlays (`doc-lottie-overlays` v6)

Generates ultra-lightweight (`< 15 KB`) transparent Bodymovin `.json` vector animations placed on `track_fg_3` (`type: "lottie"`), following zero-chrome motion restraint (`text-to-lottie` craft).

## Available Presets (`--kind`)

| `--kind` | Purpose | Recommended Placement (`16:9` center-origin) |
|---|---|---|
| `marker_highlight` | Translucent marker-pen sweep over newspaper/article clippings (`press_evidence_highlight`) | Over headline/quote (`width: 780, height: 96`, `#FACC15`) |
| `pointer_arrow` | Curved editorial callout arrow pointing at a subject or detail | Near target (`width: 360, height: 220`) |
| `minimal_lower_third` | Vertical accent pillar + subtle dark glass lower-third rule | `x: -450, y: 385, width: 760, height: 150` |
| `focus_corner_brackets` | Crisp investigative viewfinder brackets locking onto an entity | Around subject (`width: 640, height: 480`) |
| `handdrawn_underline` | Organic cubic-bezier ink underline under key numbers/dates | Beneath hero stat (`width: 640, height: 110`) |
| `handdrawn_circle` | Organic ink ring drawing around visual evidence | Around detail (`width: 440, height: 440`) |
| `pulse_beacon` | Cartographic / telemetry sonar ring | On map target (`width: 240, height: 240`) |

## Usage

```bash
python "<SKILL_DIR>/scripts/generate_lottie.py" \
  --kind marker_highlight \
  --accent "#FACC15" \
  --duration 4.2 \
  --out "<project_dir>/lottie/S04_marker.json"
```

## Editorial Restraint Rules
- Use overlays on **25%–40% of scenes**, timed to the spoken `anchor_word` (`offset_frames`), never plastered mechanically on every single cut.
- Keep `sfx` subtle (`-24 dB` to `-28 dB`) and causal — only when a physical visual element enters or sweeps.
