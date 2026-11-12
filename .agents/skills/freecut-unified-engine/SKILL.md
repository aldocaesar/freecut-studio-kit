---
name: "freecut-unified-engine"
description: "Universal standalone video production engine for walterlow/freecut (schemaVersion 15, v6.3) — auto-installs dependencies on any fresh PC from GitHub, runs FREE local faster-whisper word-level transcription (+ .srt / optional Groq & AssemblyAI), FREE edge-tts voiceover, A-roll silence trimmer (cut_aroll.py), Multi-Source Entity Hunter + rembg RGBA Cutouts + Vision Contact Sheet QA (fetch_media.py), Native Timeline Assembler (assemble_freecut.py), and Anti-Vicio Schema Validator (validate_freecut.py)."
---

# FreeCut Unified Engine (`freecut-unified-engine` v6.3)

Deterministic Python CLI pipeline that turns **just an audio file (`.mp3`/`.wav`/`.m4a`/`.ogg`/`.opus`), a camera video (`.mp4`/`.mov`), an `.srt`, or a text script (`.txt`)** into a creative, validated `walterlow/freecut` project (`freecut_workspace/` + `.freecut.zip`) — **100% standalone, with ZERO dependency on private services or mandatory paid APIs**.

All scripts live in `scripts/` inside this skill folder (`<SKILL_DIR>/scripts/`). On macOS/Linux where `python` is named `python3`, invoke scripts with `python3`.

---

## 0. First-Run Auto-Setup & Optional API Onboarding (`bootstrap_env.py` & `doctor.py`)
OpenBot shareable agent links (`https://openbot.run/agents/...`) carry the agent profile and the 4 `SKILL.md` markdown files (not `.py`, `.js`, `.mp3`, or `AGENTS.md`). On a fresh PC, **on the very first message** (even a greeting or the first audio file), check if `<SKILL_DIR>/scripts/doctor.py` exists. If missing:

1. **Download & unpack the public studio kit (`https://github.com/aldocaesar/freecut-studio-kit`) into `<WORKSPACE>`** using native OS tools (works even before Python or Git is installed) so `.agents/skills`, `.claude/skills`, `AGENTS.md`, `CLAUDE.md`, `install.ps1`, and `install.sh` are all populated:
   - **Windows (PowerShell)**:
```powershell
curl.exe -fsSL "https://github.com/aldocaesar/freecut-studio-kit/archive/refs/heads/main.zip" -o ".freecut-kit.zip"; Expand-Archive -Force ".freecut-kit.zip" ".freecut-kit"; Copy-Item -Recurse -Force ".freecut-kit/freecut-studio-kit-main/.agents/skills/*" ".agents/skills/"; New-Item -ItemType Directory -Force ".claude/skills" | Out-Null; Copy-Item -Recurse -Force ".freecut-kit/freecut-studio-kit-main/.claude/skills/*" ".claude/skills/"; foreach ($f in "AGENTS.md","CLAUDE.md","install.ps1","install.sh","doctor.py","requirements.txt",".env.example") { if (-not (Test-Path $f)) { Copy-Item ".freecut-kit/freecut-studio-kit-main/$f" $f } }; Remove-Item -Recurse -Force ".freecut-kit",".freecut-kit.zip"
```
   - **macOS / Linux (Bash/Zsh)**:
```bash
curl -fsSL "https://github.com/aldocaesar/freecut-studio-kit/archive/refs/heads/main.zip" -o .freecut-kit.zip && unzip -qo .freecut-kit.zip -d .freecut-kit && mkdir -p .agents/skills .claude/skills && cp -R .freecut-kit/freecut-studio-kit-main/.agents/skills/* .agents/skills/ && cp -R .freecut-kit/freecut-studio-kit-main/.claude/skills/* .claude/skills/ && for f in AGENTS.md CLAUDE.md install.ps1 install.sh doctor.py requirements.txt .env.example; do test -f "$f" || cp ".freecut-kit/freecut-studio-kit-main/$f" "$f"; done && rm -rf .freecut-kit .freecut-kit.zip
```
2. **Install / verify runtime tools (`doctor.py` & `bootstrap_env.py`)**:
   - If Python 3 is not installed yet on a fresh PC, run `powershell -ExecutionPolicy Bypass -File .\install.ps1` (Windows) or `bash ./install.sh` (macOS/Linux) so Python 3 + FFmpeg + Chromium are installed automatically.
   - Otherwise run `doctor.py`, and if any dependency is missing, run `bootstrap_env.py` (auto-installs FFmpeg, Python packages, `faster-whisper`, `rembg`, and Playwright Chromium; pass `--with-freecut-ui ./freecut-app` if the user also wants the local FreeCut Web UI installed):
```bash
python "<SKILL_DIR>/scripts/doctor.py"
python "<SKILL_DIR>/scripts/bootstrap_env.py"
```
3. **One-Time Optional Accelerator Prompt (0 Mandatory Keys!)**:
   - Check saved keys (`openbot.list_api_keys` in OpenBot, or `.env` in terminal). On first setup only, offer **once** via `openbot.ask_user` whether the user wants to **Skip & run 100% Free now** (recommended default) or add optional keys (`PEXELS_API_KEY` for generic stock B-roll, `GROQ_API_KEY` / `ASSEMBLYAI_API_KEY` for cloud Whisper speed, `ELEVENLABS_API_KEY` for studio TTS) via `openbot.request_api_key`.
   - Skipping never blocks anything, and the user can add keys later anytime in chat (or via `python bootstrap_env.py --setup-keys` in terminal) without reinstalling. When running Python scripts with a vault file path from `openbot.list_api_keys`, pass `--vault-key <VAR_NAME> "<vault_file_path>"` (reads directly into process memory without printing or saving to `.env`).

---

## 1. Audio, Voiceover & Word-Level Alignment (100% Standalone!)

### Case A — User provides Audio (`.mp3`/`.wav`/`.m4a`/`.ogg`/`.opus`) or Video (`.mp4`/`.mov`)
```bash
python "<SKILL_DIR>/scripts/transcribe_audio.py" --audio "<project_dir>/audio.mp3" --out-dir "<project_dir>" --lang auto
```
- Normalizes mobile/WhatsApp voice notes (`.opus`/`.ogg`/`.aac`/`.flac`) to `44.1 kHz` WAV, uses `--from-srt` if provided, uses cloud Whisper if configured, and **by default runs 100% FREE local `faster-whisper`** (GPU CUDA or automatic CPU `int8` fallback) to produce `<project_dir>/words.json` + `<project_dir>/subtitles.srt`.

### Case B — User provides ONLY a Text Script (`.txt` or chat text)
```bash
python "<SKILL_DIR>/scripts/generate_voiceover.py" --script "<project_dir>/roteiro.txt" --out-dir "<project_dir>" --lang pt-BR
```
- Generates neural voiceover + millisecond word sync via **100% FREE `edge-tts`** (or `--engine elevenlabs` when configured).

### Case C — User provides Camera A-Roll / Talking-Head Video ("Yap")
```bash
python "<SKILL_DIR>/scripts/cut_aroll.py" --project-dir "<project_dir>" --max-pause-ms 320
```
- Trims silences `>320ms` with `75ms` breath pads and alternating `1.00x / 1.07x` jump-cut punch-in zooms.

---

## 2. Multi-Source Exact Media, `rembg` Cutouts & Vision QA (`fetch_media.py`)

```bash
python "<SKILL_DIR>/scripts/fetch_media.py" --project-dir "<project_dir>"
```
- Hunts real editorial photos/videos in parallel (Bing Images, Bing News real article OpenGraph scraper, Wikimedia Commons, Yandex, Playwright Chromium headless browser fallback, and YouTube `yt-dlp`; stock Pexels/Pixabay matched to aspect ratio ONLY when `specific` is `false`), extracts **RGBA cutouts (`media/cutouts/<sid>_cutout.png`)** via `rembg`, and captures **press clippings (`media/prints/<sid>_print.png`)**.
- **MANDATORY BATCH VISION QA & RE-QUERY LOOP**:
  1. Visually open **every** generated batch grid (`media/contact_sheet.jpg`, `media/contact_sheet_batch_2.jpg`, etc. — up to 8 scenes per batch covering specific photos, Pexels/ambient photos, 3-frame video strips, and web prints).
  2. For each row, verify exact entity/country/packaging, zero watermarks, zero awkward face crops, and clean video frames: if Candidate 2, 3, or 4 is better, swap immediately via `--select S02=3`; if none of the candidates or video frames fit, refine `queries` / `must_match` / `exclude_terms` in `storyboard.json` and re-run `fetch_media.py --project-dir "<project_dir>" --scene S02` until 100% of rows pass!

---

## 3. Native Multi-Format FreeCut Assembly & Validation

```bash
python "<SKILL_DIR>/scripts/assemble_freecut.py" --project-dir "<project_dir>"
python "<SKILL_DIR>/scripts/validate_freecut.py" --project-dir "<project_dir>"
```
- Supports `16:9`, `9:16`, `4:5`, `1:1`, optional `--captions`, native `textMotion` (`typewriter`, `slide-mask`, `cascade`, `rise`, `pop`, `blur-in`, `fade-up`, `fade-down`, `blur-out`, `pulse`), multi-font `textSpans`, `motionModifiers` (`float-drift`, `sway`, `breath-pulse`), 3 distinct `parallax_cutout_stage` archetypes, and keyframes clamped to `durationInFrames - 1`.
- **DEFAULT DELIVERY RULE (DO NOT RENDER MP4 BY DEFAULT!)**: Once `validate_freecut.py` returns `PASS` and `freecut_workspace` is verified on disk, **STOP** and immediately deliver the copyable path and `file:///` URL to `<project_dir>/freecut_workspace` (plus `<Title>.freecut.zip`). Run `render_preview.py` **only** if the user explicitly asks to export a direct `.mp4` on the PC.
