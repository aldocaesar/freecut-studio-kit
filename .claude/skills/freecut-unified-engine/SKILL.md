---
name: "freecut-unified-engine"
description: "Universal standalone video production engine for walterlow/freecut (schemaVersion 15, v7.0) — Virgin-PC auto-setup, zero-freeze multi-shot B-roll, optical hero word fit, 5 press treatments, 6-zone typography, parallel Media Hunter + Subagent Vision QA, and 1-command finish_freecut.py pipeline."
---

# FreeCut Unified Engine (`freecut-unified-engine` v7.0)

Deterministic Python CLI pipeline turning **an audio file, a folder path (audio + optional `.srt`), a camera video, or a text script** into a creative, zero-freeze `walterlow/freecut` project (`freecut_workspace/` + `.freecut.zip`) — **100% standalone, zero mandatory paid APIs, zero `.pyc` pollution (`-B`), and context-safe for 10–20+ minute videos**.

All scripts live in `<SKILL_DIR>/scripts/` (always invoke `python -B`, or `python3 -B` on macOS/Linux).

---

## Anti-Context-Overflow & Bytecode Laws (MANDATORY!)
1. **ALWAYS run Python with `-B` (`python -B`)**: Keeps `.agents/skills/` 100% clean of `__pycache__` so OpenBot skill publishing stays `installed`.
2. **NEVER `read_file` audio/video (`.wav`/`.mp3`/`.mp4`) or full `words.json`**: Read **only** `<project_dir>/words_compact.txt` (~75 lines for a 10-min video with exact `word@sec` timestamps) or `subtitles.srt`.
3. **NEVER `read_file` skill `.py`/`.js` source files** unless debugging an actual `Traceback`.
4. **MULTIMODAL SUBAGENT ISOLATION**: Never open `contact_sheet*.jpg`, `motion_contact_sheet*.jpg`, `cutouts/*.png`, or `SXX_preview.jpg` in the main thread! Delegate Vision QA to an isolated subagent (`invoke_subagent` / `Task`) that inspects all sheets, runs `--select` / `--scene` fixes, and returns **only `<= 15` lines of text**.
5. **NO `manage_task` polling loops**: When waiting on a `10s–15m` background `task-XX` or subagent, keep the turn alive using `schedule(DurationSeconds=45, TimerCondition="any", Prompt="Check completion")`.

---

## 0. Virgin-PC First-Run Auto-Setup & One-Time Key Check
1. **If `<SKILL_DIR>/scripts/doctor.py` is missing** (fresh install via OpenBot share link), unpack the public kit with native OS tools:
   - **Windows (PowerShell)**:
```powershell
curl.exe -fsSL "https://github.com/aldocaesar/freecut-studio-kit/archive/refs/heads/main.zip" -o ".freecut-kit.zip"; Expand-Archive -Force ".freecut-kit.zip" ".freecut-kit"; Copy-Item -Recurse -Force ".freecut-kit/freecut-studio-kit-main/.agents/skills/*" ".agents/skills/"; New-Item -ItemType Directory -Force ".claude/skills" | Out-Null; Copy-Item -Recurse -Force ".freecut-kit/freecut-studio-kit-main/.claude/skills/*" ".claude/skills/"; foreach ($f in "AGENTS.md","CLAUDE.md","install.ps1","install.sh","doctor.py","requirements.txt",".env.example") { if (-not (Test-Path $f)) { Copy-Item ".freecut-kit/freecut-studio-kit-main/$f" $f } }; Remove-Item -Recurse -Force ".freecut-kit",".freecut-kit.zip"
```
   - **macOS / Linux**:
```bash
curl -fsSL "https://github.com/aldocaesar/freecut-studio-kit/archive/refs/heads/main.zip" -o .freecut-kit.zip && unzip -qo .freecut-kit.zip -d .freecut-kit && mkdir -p .agents/skills .claude/skills && cp -R .freecut-kit/freecut-studio-kit-main/.agents/skills/* .agents/skills/ && cp -R .freecut-kit/freecut-studio-kit-main/.claude/skills/* .claude/skills/ && for f in AGENTS.md CLAUDE.md install.ps1 install.sh doctor.py requirements.txt .env.example; do test -f "$f" || cp ".freecut-kit/freecut-studio-kit-main/$f" "$f"; done && rm -rf .freecut-kit .freecut-kit.zip
```
2. **If `<WORKSPACE>/.freecut-setup-done.json` is missing**:
   - Run `install.ps1` / `install.sh` (if Python 3 is missing), then `python -B "<SKILL_DIR>/scripts/bootstrap_env.py"`.
   - Offer **once** via `openbot.ask_user` — **(Recommended) Run 100% Free now** (scraped HD photos/videos + local `faster-whisper`) OR **Add optional keys** (`PEXELS_API_KEY`, `GROQ_API_KEY`, `ASSEMBLYAI_API_KEY`, `ELEVENLABS_API_KEY` via `openbot.request_api_key` and `--vault-key <NAME> "<vault_path>"`).
   - Run `python -B "<SKILL_DIR>/scripts/bootstrap_env.py" --mark-onboarded` so future runs start editing immediately with zero questions!

---

## 1. Word-Level Alignment (`words_compact.txt`)
- **Audio / Video / Folder with Audio (+ optional `.srt`)**:
```bash
python -B "<SKILL_DIR>/scripts/transcribe_audio.py" --audio "<audio_or_video>" --out-dir "<project_dir>" --lang auto
```
*(If the folder already contains an `.srt`, append `--from-srt "<file.srt>"` for instant `0.2s` alignment!)*
- **Text Script Only (`.txt`)**:
```bash
python -B "<SKILL_DIR>/scripts/generate_voiceover.py" --script "<project_dir>/roteiro.txt" --out-dir "<project_dir>" --lang pt-BR
```
- **Camera A-Roll ("Yap")**: `python -B "<SKILL_DIR>/scripts/cut_aroll.py" --project-dir "<project_dir>" --max-pause-ms 320`
- Next, read **only** `<project_dir>/words_compact.txt` and write `<project_dir>/storyboard.json` (`doc-art-director`).

---

## 2. Duration-Aware Parallel Media Hunter + Subagent Vision QA (`fetch_media.py`)
```bash
python -B "<SKILL_DIR>/scripts/fetch_media.py" --project-dir "<project_dir>"
```
- Prioritizes long HD video clips (`duration >= scene_dur + 0.8s`) and automatically downloads secondary B-roll angles (`_b2.mp4` / `_b3.mp4`) whenever a beat exceeds `5.8s` so **no video ever freezes**!
- **SUBAGENT VISION QA**: Launch **1 subagent** (`invoke_subagent`) to inspect every `media/contact_sheet*.jpg`, swap better candidates via `python -B "<SKILL_DIR>/scripts/fetch_media.py" --project-dir "<project_dir>" --select S02=3 S09=2`, re-hunt weak rows via `--scene S14`, and reply with a short text summary.

---

## 3. One-Command v7.0 Finalizer (`finish_freecut.py` -> Stop at `freecut_workspace`!)
After writing diverse `motion/SXX.html` scenes (`doc-motion-scenes`), run **one command**:
```bash
python -B "<SKILL_DIR>/scripts/finish_freecut.py" --project-dir "<project_dir>"
```
1. Generates all `lottie_overlay` JSONs in batch (`generate_lottie.py --project-dir`),
2. Renders all `motion/*.html` in parallel (`ThreadPoolExecutor(max_workers=3)`) + builds 4-column `motion/motion_contact_sheet.jpg` (`20% / 50% / 78% / 94%` live-tail check),
3. Assembles `freecut_workspace` + `<Title>.freecut.zip` with compound sub-shots (`<= 6.2s` per shot, zero video freeze), optical hero word fit, 5 rotating press treatments, and 6-zone negative-space typography,
4. Runs strict `validate_freecut.py` v7.0 (`PASS` = 0 schema, freeze, highlighter-spam, or cloning errors).
- Have **1 subagent** review `motion/motion_contact_sheet*.jpg` (re-running `finish_freecut.py --force-motion` if any HTML needed adjustment), then **STOP** (do NOT render `.mp4` unless requested) and deliver `<project_dir>/freecut_workspace`!
