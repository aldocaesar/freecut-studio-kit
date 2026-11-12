# `storyboard.json` v8.0 Schema & Genre-Adaptive Examples (`doc-art-director`)

Every project writes `<project_dir>/storyboard.json` anchored to exact timestamps from `<project_dir>/words_compact.txt`. Notice how `style_dna` (`accent`, `accent_secondary`, `paper_bg`, `studio_bg`, and all 4 Google Fonts) changes completely to fit the genre!

## Root & Scene Example

```json
{
  "title": "Project Title",
  "aspect_ratio": "16:9",
  "fps": 30,
  "audio_file": "narration.mp3",
  "captions": { "enabled": false },
  "style_dna": {
    "mood": "genre_specific_visual_world",
    "font_display": "Syne",
    "font_serif": "Instrument Serif",
    "font_body": "Plus Jakarta Sans",
    "font_mono": "JetBrains Mono",
    "accent": "#2563EB",
    "accent_secondary": "#F59E0B",
    "paper_bg": "#F8F6F0",
    "studio_bg": "#0F172A"
  },
  "scenes": [
    {
      "id": "S01",
      "type": "SCENE",
      "layout": "cinematic_broll",
      "start_ms": 0,
      "end_ms": 4600,
      "anchor_word": "abertura",
      "narration": "Spoken slice from words_compact.txt...",
      "headline": "Um Novo Universo Visual",
      "text_position": "bottom_left",
      "text_entry": "slide-mask",
      "media": {
        "source_type": "video",
        "specific": false,
        "queries": ["aerial city lights dusk timelapse", "modern skyline twilight drone"]
      }
    },
    {
      "id": "S02",
      "type": "SCENE",
      "layout": "parallax_cutout_stage",
      "cutout": true,
      "cutout_variant": "poster_monumental_center",
      "subject_side": "center",
      "monumental_word": "ORIGEM",
      "start_ms": 4600,
      "end_ms": 9200,
      "anchor_word": "personagem",
      "narration": "Spoken slice...",
      "kicker": "PROTAGONISTA",
      "headline": "Quem mudou as regras do jogo",
      "media": {
        "source_type": "image",
        "specific": true,
        "queries": ["Named Person official portrait photo"],
        "must_match": ["person"]
      }
    },
    {
      "id": "S03",
      "type": "MOTION_SCENE",
      "layout": "motion_scene",
      "start_ms": 9200,
      "end_ms": 14800,
      "narration": "Spoken slice...",
      "motion_html": "motion/S03.html",
      "motion_brief": "Custom SVG/Canvas physical metaphor tailored to this exact sentence, styled with style_dna (#2563EB, #F59E0B, #F8F6F0, Syne + JetBrains Mono) and continuous live motion through 100%."
    },
    {
      "id": "S04",
      "type": "SCENE",
      "layout": "full_bleed_ken_burns",
      "silent_visual": true,
      "start_ms": 14800,
      "end_ms": 19100,
      "narration": "Spoken slice...",
      "media": {
        "source_type": "image",
        "specific": false,
        "queries": ["sunlit courtyard architecture wide shot", "warm street afternoon shadows"]
      }
    }
  ]
}
```

## Autonomous Audio-Only Creative Checklist (`v8.0`)
1. **Check `creator_memory.py --summary`:** Contrast `style_dna` colors, Google Fonts, and `S01` opening layout against `Last Video` so back-to-back projects never look cloned.
2. **Respect Genre:** Zero `press_evidence_highlight` or investigative brackets on comedy, entertainment, pop culture, or fictional stories.
3. **Optional `monumental_word` & `kicker`:** Use `monumental_word` sparingly (`1–2` hero cutouts max per minute), never on every single cutout.
4. **Bespoke Creative LLM Motion (`15%–25%` of runtime):** Invent each `motion/SXX.html` around the spoken metaphor using custom SVG/Canvas2D/CSS + `MotionKit` physics (`spring`, `progress`, `stagger`, `strokeProgress`, `pointOnPath`, `oscillate`, `rostrumTransform`, and `renderWorldAtlas` for real geography).
