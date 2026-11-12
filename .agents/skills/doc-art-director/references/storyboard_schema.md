# `storyboard.json` v6.3 Full Schema & Creative Examples (`doc-art-director`)

Every project edited by `Editor-FreeCut` writes `<project_dir>/storyboard.json` anchored to millisecond word timestamps from `<project_dir>/words.json`.

## Root & Scene Example (`16:9` Documentary / Essay)

```json
{
  "title": "Project Title",
  "aspect_ratio": "16:9",
  "fps": 30,
  "audio_file": "narration.mp3",
  "captions": { "enabled": false },
  "style_dna": {
    "palette": "investigative_amber",
    "font_display": "Bricolage Grotesque",
    "font_serif": "Playfair Display",
    "font_body": "Space Grotesk",
    "font_mono": "Roboto Mono",
    "accent": "#EA580C",
    "paper_bg": "#F3EFE6",
    "studio_bg": "#0D121A"
  },
  "scenes": [
    {
      "id": "S01",
      "type": "SCENE",
      "layout": "cinematic_broll",
      "start_ms": 0,
      "end_ms": 4800,
      "anchor_word": "Kigali",
      "narration": "Exact spoken slice from words.json...",
      "headline": "KIGALI, RUANDA",
      "text_position": "bottom_left",
      "text_entry": "slide-mask",
      "media": {
        "source_type": "video",
        "specific": true,
        "queries": ["Kigali Rwanda street market cityscape 4k", "Kigali Rwanda aerial"],
        "must_match": ["kigali"]
      },
      "lottie_overlay": {
        "file": "lottie/S01_lt.json",
        "x": -450,
        "y": 385,
        "width": 760,
        "height": 150,
        "offset_frames": 5
      }
    },
    {
      "id": "S02",
      "type": "SCENE",
      "layout": "parallax_cutout_stage",
      "cutout": true,
      "cutout_variant": "poster_monumental_center",
      "start_ms": 4800,
      "end_ms": 9600,
      "anchor_word": "garrafa",
      "narration": "Exact spoken slice...",
      "hero_stat": "1 9 5 7",
      "headline": "FANTA CITRON • BRALIRWA RUANDA",
      "text_entry": "typewriter",
      "media": {
        "source_type": "image",
        "specific": true,
        "queries": ["Fanta Citron glass bottle Bralirwa Rwanda", "Bralirwa Fanta Citron returnable bottle"],
        "must_match": ["citron", "bottle"],
        "exclude_terms": ["canette", "frappe", "can", "orange", "strawberry"]
      }
    },
    {
      "id": "S05",
      "type": "SCENE",
      "layout": "parallax_cutout_stage",
      "cutout": true,
      "cutout_variant": "archival_dossier_paper",
      "start_ms": 18200,
      "end_ms": 23400,
      "anchor_word": "maracuja",
      "narration": "Exact spoken slice...",
      "hero_stat": "AGASHYA • SINA GERARD",
      "headline": "O néctar artesanal que virou símbolo nacional",
      "text_entry": "cascade",
      "media": {
        "source_type": "image",
        "specific": true,
        "queries": ["Agashya passion fruit bottle Sina Gerard Rwanda"],
        "must_match": ["agashya"]
      }
    },
    {
      "id": "S07",
      "type": "MOTION_SCENE",
      "layout": "motion_scene",
      "start_ms": 28400,
      "end_ms": 35100,
      "narration": "Exact spoken slice...",
      "motion_html": "motion/S07.html",
      "motion_brief": "Natural Earth geodesic atlas comparing Brazil (-14,-51) and Rwanda (29.9,-1.9) across the Equator with real S02_cutout.png."
    },
    {
      "id": "S08",
      "type": "SCENE",
      "layout": "parallax_cutout_stage",
      "cutout": true,
      "cutout_variant": "magazine_grounded_portrait",
      "start_ms": 35100,
      "end_ms": 40500,
      "anchor_word": "bilhao",
      "narration": "Exact spoken slice...",
      "hero_stat": "R$ 750 MILHÕES",
      "headline": "O salto do cosmético digital no Brasil",
      "text_entry": "rise",
      "media": {
        "source_type": "image",
        "specific": true,
        "queries": ["Virginia Fonseca WePink portrait"],
        "must_match": ["virginia"]
      }
    }
  ]
}
```

## Autonomous Audio-Only Creative Checklist
When the user sends **only an audio file** (without scene instructions):
1. Infer tone, theme, and target aspect ratio (`16:9` default unless vertical/Shorts/Reels is requested or implied).
2. Never repeat two identical layouts back-to-back.
3. Rotate cutout scenes across `poster_monumental_center`, `archival_dossier_paper`, and `magazine_grounded_portrait`.
4. Include `15%–25%` bespoke 30fps `motion_scene` clips (`MotionKit.renderWorldAtlas` for geography, `MotionKit.renderDataCurve` for numbers/growth, kinetic timelines for history).
5. Pair editorial typography (`Playfair Display`, `Bricolage Grotesque`, `Space Grotesk`, `Bebas Neue`, `Oswald`, `Inter Tight`, `Roboto Mono`) with native FreeCut `textMotion` (`typewriter`, `slide-mask`, `cascade`, `rise`, `pop`, `blur-in`) and `motionModifiers` (`float-drift`, `sway`, `breath-pulse`).
