---
name: freecut-unified-engine
description: Universal standalone video production engine for `walterlow/freecut` (`schemaVersion: 15`, v6): FREE local `faster-whisper` word-level transcription (+ `.srt` / optional Groq & AssemblyAI), FREE standalone `edge-tts` voiceover, A-roll silence trimmer (`cut_aroll.py`), Multi-Source Entity Hunter + `rembg` RGBA Cutouts + Web Press Evidence + Vision Contact Sheet QA (`fetch_media.py`), Multi-Format Timeline Assembler (`16:9`, `9:16`, `4:5`, `1:1` in `assemble_freecut.py`), Environment Doctor (`doctor.py`), and Anti-Vício Schema Validator (`validate_freecut.py`).
---

# FreeCut Unified Engine (`freecut-unified-engine` v6)

Deterministic Python CLI pipeline that turns **an audio file (`.mp3`/`.wav`/`.m4a`/`.ogg`/`.opus`), a camera video (`.mp4`/`.mov`), an `.srt`, or a text script (`.txt`)** into a validated, manual-grade `walterlow/freecut` project (`freecut_workspace/` + `.freecut.zip`) — **100% standalone, with ZERO dependency on private services or mandatory paid APIs**.

All scripts live in `scripts/` inside this skill folder (`<SKILL_DIR>/scripts/`).

---

## 0. First-Run Auto-Setup & Optional API Onboarding (`bootstrap_env.py` & `doctor.py`)
OpenBot shareable agent links (`https://openbot.run/agents/...`) carry `AGENTS.md` and all 4 `SKILL.md` markdown files (not `.py`/`.js`/`.mp3` files). On a fresh PC before the first video edit:
1. If `<SKILL_DIR>/scripts/doctor.py` does **not** exist yet, automatically download the public GitHub kit from `https://github.com/aldocaesar/freecut-studio-kit` (`git clone --depth 1 https://github.com/aldocaesar/freecut-studio-kit.git .freecut-kit`, or download `https://github.com/aldocaesar/freecut-studio-kit/archive/refs/heads/main.zip` via Python `urllib.request` + `zipfile` if `git` is not installed yet) and copy `.agents/skills/*` into `<WORKSPACE>/.agents/skills/`:
```bash
python -c "import io,shutil,urllib.request,zipfile; z=zipfile.ZipFile(io.BytesIO(urllib.request.urlopen('https://github.com/aldocaesar/freecut-studio-kit/archive/refs/heads/main.zip').read())); z.extractall('.freecut-kit'); shutil.copytree('.freecut-kit/freecut-studio-kit-main/.agents/skills','.agents/skills',dirs_exist_ok=True); shutil.rmtree('.freecut-kit',ignore_errors=True)"
```
2. Run `doctor.py`; if any dependency is missing, run `bootstrap_env.py` automatically (installs FFmpeg, Python deps, `faster-whisper`, `rembg`, and Playwright Chromium):
```bash
python "<SKILL_DIR>/scripts/doctor.py"
python "<SKILL_DIR>/scripts/bootstrap_env.py"
```
3. **Optional Accelerator Keys (0 Mandatory Keys!)**: Check saved keys (`openbot.list_api_keys` in OpenBot, or `.env` in terminal). On first setup, offer **once** (`openbot.ask_user`) whether the user wants to run **100% Free now (Skip keys)** or configure optional keys (`PEXELS_API_KEY` for generic stock B-roll, `GROQ_API_KEY` / `ASSEMBLYAI_API_KEY` for cloud Whisper speed, `ELEVENLABS_API_KEY` for premium TTS) via `openbot.request_api_key`. Skipping never blocks anything; the user can ask to add or replace any key later (or run `python bootstrap_env.py --setup-keys` in terminal) without reinstalling! When running Python scripts inside OpenBot with a vault key path from `list_api_keys`, inject it into process memory without printing or copying it to `.env`: on Windows PowerShell (`$env:GROQ_API_KEY = (Get-Content -LiteralPath '<path>' -Raw).Trim(); python ...`) or on macOS/Linux (`GROQ_API_KEY="$(cat '<path>')" python ...`).

---

## 1. Audio, Voiceover & Word-Level Alignment (100% Standalone!)

### Case A — User provides Audio (`.mp3`/`.wav`/`.m4a`/`.ogg`/`.opus`) or Video (`.mp4`/`.mov`) [DEFAULT]
```bash
python "<SKILL_DIR>/scripts/transcribe_audio.py" --audio "<project_dir>/audio.mp3" --out-dir "<project_dir>" --lang auto
```
- **How it works**:
  1. If `--from-srt <file.srt>` is passed, aligns instantly at zero compute cost.
  2. Automatically normalizes mobile/WhatsApp voice notes (`.opus`/`.ogg`/`.aac`/`.flac`) and video audio into crisp `44.1 kHz` WAV (`extracted_audio.wav`).
  3. If `GROQ_API_KEY` or `ASSEMBLYAI_API_KEY` is configured in `.env`, uses ultra-fast cloud word alignment (with automatic fallback to local if offline).
  4. **By default (with ZERO API keys!)**, runs **100% FREE local `faster-whisper`** (`word_timestamps=True`, `vad_filter=True`, CUDA GPU or CPU `int8`) and writes `<project_dir>/words.json` + `<project_dir>/subtitles.srt`!

### Case B — User provides ONLY a Text Script (`.txt`) and wants Voiceover generated
```bash
python "<SKILL_DIR>/scripts/generate_voiceover.py" --script "<project_dir>/roteiro.txt" --out-dir "<project_dir>" --lang pt-BR
```
- Uses **100% FREE `edge-tts`** neural voices (`WordBoundary` millisecond sync -> `narration.mp3` + `words.json` + `subtitles.srt`), or `--engine elevenlabs` if `ELEVENLABS_API_KEY` is set.

### Case C — User provides Camera A-Roll / Talking-Head Video ("Yap")
```bash
python "<SKILL_DIR>/scripts/cut_aroll.py" --project-dir "<project_dir>" --max-pause-ms 320
```
- Trims silences `>320ms` with `75ms` breath pads and generates `aroll_cuts.json` with alternating `1.00x / 1.07x` jump-cut punch-in zooms.

---

## 2. Multi-Source Exact Media, `rembg` Cutouts & Vision QA (`fetch_media.py`)

```bash
python "<SKILL_DIR>/scripts/fetch_media.py" --project-dir "<project_dir>"
```
- Hunts real editorial photos/videos (Bing, DuckDuckGo, Google News, Wikimedia Commons, YouTube `yt-dlp`; stock Pexels/Pixabay ONLY when `"specific": false`).
- Automatically extracts **RGBA transparent cutouts (`media/cutouts/{sid}_cutout.png`)** via `rembg` whenever `layout` is `parallax_cutout_stage`, `aroll_yap_overlay`, or `"cutout": true` (or on demand via `--cutout S02 S05`).
- Captures **real press/web article clippings (`media/prints/{sid}_print.png`)** when `layout` is `press_evidence_highlight` and `evidence_url` is set.
- **MANDATORY VISION QA GATE**:
  1. Inspect `<project_dir>/media/contact_sheet.jpg` visually before assembling!
  2. Swap any wrong variant/country candidate (`--select S02=3`) or re-hunt with refined queries (`--scene S02`).

---

## 3. Native Multi-Format FreeCut Assembly (`assemble_freecut.py`)

```bash
python "<SKILL_DIR>/scripts/assemble_freecut.py" --project-dir "<project_dir>"
```
- Supports `"aspect_ratio": "16:9" | "9:16" | "4:5" | "1:1"`, optional `"captions": true` (`--captions`), and optional `"bgm_file"`.
- Emits **100% native `walterlow/freecut` animations & typography**:
  - `textMotion` (`TextMotionSpec`: `in`, `out`, `loop` presets such as `typewriter`, `slide-mask`, `cascade`, `rise`, `pop`, `blur-in`, `fade-up`, `fade-down`, `blur-out`, `pulse`), never fake `"textAnimation"`.
  - `textSpans` (`TextSpan[]` multi-font editorial lockups pairing `Playfair Display`, `Bricolage Grotesque`, `Space Grotesk`, `Bebas Neue`, `Oswald`, `Inter Tight`, `DM Sans`, and `Roboto Mono`).
  - `motionModifiers` (`Clipe Motion`: `float-drift`, `sway`, `breath-pulse`), `LottieItem` (`frameRate`, `totalFrames`), and keyframes strictly clamped to `[0, durationInFrames - 1]` (zero `"Quadros-chave aparados"`).
- Stages `parallax_cutout_stage` across **3 distinct non-repeating editorial archetypes** (`poster_monumental_center` with giant type behind the cutout, `archival_dossier_paper` on warm cream newsprint with botanical stamp, and `magazine_grounded_portrait` grounding waist-cropped portraits flush to the bottom edge).

---

## 4. Strict Schema v15 + Anti-Vício Validation & Default Delivery (`validate_freecut.py`)

```bash
python "<SKILL_DIR>/scripts/validate_freecut.py" --project-dir "<project_dir>"
```
- Must return **`PASS`** (zero missing media, zero schema errors, zero excessive card-splits, zero fake hand-drawn polygon maps).
- **DEFAULT DELIVERY RULE (DO NOT RENDER MP4 BY DEFAULT!)**: Once `validate_freecut.py` returns `PASS`, **STOP** and immediately deliver the exact copyable path and `file:///` URL to `<project_dir>/freecut_workspace` (plus `<Title>.freecut.zip`) so the user opens and renders inside FreeCut!

---

## 5. Optional Direct MP4 Preview (`render_preview.py` — ONLY When Explicitly Requested!)

**DO NOT run `render_preview.py` by default.** Run it **ONLY** when the user explicitly asks you to render/export a playable `.mp4` file directly on the PC:
```bash
python "<SKILL_DIR>/scripts/render_preview.py" --project-dir "<project_dir>" --out "<project_dir>/final_preview.mp4"
```
- Composites all tracks (`track_bg`, `track_anchor`, `track_fg_1` grade, `track_fg_2` cutouts + shadows, `track_fg_3` Lottie overlays, `track_text`, `track_captions`) and mixes `track_audio` + `track_sfx` + `track_bgm` frame-accurately.
