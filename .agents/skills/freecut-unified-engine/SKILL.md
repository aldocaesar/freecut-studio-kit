---
name: "freecut-unified-engine"
description: "Universal standalone video production engine for walterlow/freecut (Schema v15 + Workspace v2 pre-cache, v8.0) — Virgin-PC first-run onboarding, anti-clone creator memory, Pixabay HD stock video/photo + zero-key scraping, chameleon per-video style_dna, bespoke creative LLM motion graphics, and 1-command finish_freecut.py pipeline."
---

# FreeCut Unified Engine (`freecut-unified-engine` v8.0)

Deterministic Python CLI pipeline turning **only an audio file (`.mp3`/`.wav`/`.m4a`), a folder path (audio + optional `.srt`), a camera video, or a text script** into a creative, zero-freeze, instant-opening `walterlow/freecut` project (`freecut_workspace/` + `.freecut.zip`) — **100% standalone, zero mandatory paid APIs, first-class Pixabay API support, persistent creator memory across videos, zero `.pyc` pollution (`-B`), and context-safe for 10–20+ minute videos**.

All scripts live in `<SKILL_DIR>/scripts/` (always invoke `python -B`, or `python3 -B` on macOS/Linux).

---

## Anti-Context-Overflow & Bytecode Laws (MANDATORY!)
1. **ALWAYS run Python with `-B` (`python -B`)**: Keeps `.agents/skills/` 100% clean of `__pycache__` so OpenBot skill publishing stays `installed`.
2. **NEVER `read_file` audio/video (`.wav`/`.mp3`/`.mp4`) or full `words.json`**: Read **only** `<project_dir>/words_compact.txt` (~75 lines for a 10-min video with exact `word@sec` timestamps) or `subtitles.srt`.
3. **NEVER `read_file` skill `.py`/`.js` source files** unless debugging an actual `Traceback`.
4. **MULTIMODAL SUBAGENT ISOLATION**: Never open `contact_sheet*.jpg`, `motion_contact_sheet*.jpg`, `cutouts/*.png`, or `SXX_preview.jpg` in the main thread! Delegate Vision QA to an isolated subagent (`invoke_subagent` / `Task`) that inspects all sheets, runs `--select` / `--scene` fixes, and returns **only `<= 15` lines of text**.
5. **NO `manage_task` polling loops**: When waiting on a `10s–15m` background `task-XX` or subagent, keep the turn alive using `schedule(DurationSeconds=45, TimerCondition="any", Prompt="Check completion")`.

---

## 0. Virgin-PC First-Run Auto-Setup, Pixabay Key Check & Creator Memory
1. **If `<SKILL_DIR>/scripts/doctor.py` is missing** (fresh install via OpenBot share link), unpack the public kit with native OS tools:
   - **Windows (PowerShell)**:
```powershell
curl.exe -fsSL "https://github.com/aldocaesar/freecut-studio-kit/archive/refs/heads/main.zip" -o ".freecut-kit.zip"; Expand-Archive -Force ".freecut-kit.zip" ".freecut-kit"; Copy-Item -Recurse -Force ".freecut-kit/freecut-studio-kit-main/.agents/skills/*" ".agents/skills/"; New-Item -ItemType Directory -Force ".claude/skills" | Out-Null; Copy-Item -Recurse -Force ".freecut-kit/freecut-studio-kit-main/.claude/skills/*" ".claude/skills/"; foreach ($f in "AGENTS.md","CLAUDE.md","install.ps1","install.sh","doctor.py","requirements.txt",".env.example",".gitignore") { if (-not (Test-Path $f)) { Copy-Item ".freecut-kit/freecut-studio-kit-main/$f" $f } }; Remove-Item -Recurse -Force ".freecut-kit",".freecut-kit.zip"
```
   - **macOS / Linux**:
```bash
curl -fsSL "https://github.com/aldocaesar/freecut-studio-kit/archive/refs/heads/main.zip" -o .freecut-kit.zip && unzip -qo .freecut-kit.zip -d .freecut-kit && mkdir -p .agents/skills .claude/skills && cp -R .freecut-kit/freecut-studio-kit-main/.agents/skills/* .agents/skills/ && cp -R .freecut-kit/freecut-studio-kit-main/.claude/skills/* .claude/skills/ && for f in AGENTS.md CLAUDE.md install.ps1 install.sh doctor.py requirements.txt .env.example .gitignore; do test -f "$f" || cp ".freecut-kit/freecut-studio-kit-main/$f" "$f"; done && rm -rf .freecut-kit .freecut-kit.zip
```
2. **If the user pastes or sends an API key directly in chat (even on their very 1st message!)**:
   - **In OpenBot**: Save it immediately with `openbot.save_api_key(name="PIXABAY_API_KEY", key="<pasted_value>", notes="Pixabay HD stock video & photo API")` (use exact uppercase env name: `PIXABAY_API_KEY`, `GROQ_API_KEY`, `ASSEMBLYAI_API_KEY`, `ELEVENLABS_API_KEY`, `TMDB_API_KEY`, or `PEXELS_API_KEY`; **never** repeat the key in chat or write it into `.env` without asking!). `_runtime_env.py` automatically loads saved OpenBot Vault keys into RAM on every future script run across Windows, macOS, and Linux.
   - **Outside OpenBot (Claude Code / Antigravity / Cursor CLI)**: Write `PIXABAY_API_KEY=<value>` directly into gitignored `<WORKSPACE>/.env` without echoing the secret.
   - Then immediately run `python -B "<SKILL_DIR>/scripts/bootstrap_env.py" --mark-onboarded` in the same turn (installing any missing virgin-PC packages and marking `.freecut-setup-done.json` **without** asking the onboarding question again!). If the message had **only** the key, confirm in 2 short lines that the key is saved and the engine is ready for their audio; if they sent **key + audio together**, proceed straight into Step 1 and edit the video in the same turn!
3. **Otherwise, if `<WORKSPACE>/.freecut-setup-done.json` is missing (First-Time Use without a pasted key)**:
   - Run `install.ps1` / `install.sh` (if Python 3 is missing), then `python -B "<SKILL_DIR>/scripts/bootstrap_env.py"`.
   - Check `openbot.list_api_keys` first; if `PIXABAY_API_KEY` is not saved yet, ask **once** (`openbot.ask_user` in OpenBot, or 1 concise question in CLI) whether the user wants:
     - **(Recommended) Add FREE `PIXABAY_API_KEY`** (instant free signup at `https://pixabay.com/api/docs/` covering 1080p HD stock videos + photos, since Pexels paused new API keys; use `openbot.request_api_key(name="PIXABAY_API_KEY", ...)`), OR
     - **Run 100% Free Zero-Key now** (multi-engine HD web scraping + local `faster-whisper`).
   - Run `python -B "<SKILL_DIR>/scripts/bootstrap_env.py" --mark-onboarded` so all future runs skip onboarding and start editing immediately!
4. **Recall & Persist Creator Context Memory (`creator_memory.py`)**:
   - Before planning any video, run `python -B "<SKILL_DIR>/scripts/creator_memory.py" --summary` (plus `openbot.search_memories` in OpenBot) to load the creator's default aspect ratio, channel niche, durable feedback rules, recurring entities, and last edit's opening/palettes.
   - Whenever the user gives style feedback or channel preferences (e.g., *"sempre 9:16"*, *"mais paletas claras"*, *"sem legenda"*), persist it immediately via:
```bash
python -B "<SKILL_DIR>/scripts/creator_memory.py" --remember "<preference>"
```

---

## 1. Bare-Audio Word-Level Alignment (`words_compact.txt`)
- **Audio Only / Video / Folder with Audio (+ optional `.srt`)**:
```bash
python -B "<SKILL_DIR>/scripts/transcribe_audio.py" --audio "<audio_or_video>" --out-dir "<project_dir>" --lang auto
```
*(If the folder already contains an `.srt`, append `--from-srt "<file.srt>"` for instant `0.2s` alignment!)*
- **Text Script Only (`.txt`)**:
```bash
python -B "<SKILL_DIR>/scripts/generate_voiceover.py" --script "<project_dir>/roteiro.txt" --out-dir "<project_dir>" --lang pt-BR
```
- **Camera A-Roll ("Yap")**: `python -B "<SKILL_DIR>/scripts/cut_aroll.py" --project-dir "<project_dir>" --max-pause-ms 320`
- Next, combine `<project_dir>/words_compact.txt` + `creator_memory.py --summary` to write `<project_dir>/storyboard.json` (`doc-art-director`) with zero questionnaires.

---

## 2. Duration-Aware Parallel Media Hunter (`PIXABAY_API_KEY` + Web Scrapers) & Subagent Vision QA
```bash
python -B "<SKILL_DIR>/scripts/fetch_media.py" --project-dir "<project_dir>"
```
- **Smart Routing**:
  - `specific: true` (real people, brands, headlines, places) -> **strictly blocks generic stock** (Pixabay/Pexels) and hunts verified real photos/clips via Bing, News RSS, Wikimedia, Yandex, TMDB, Playwright, and `yt-dlp`.
  - `specific: false` (atmospheric B-roll) -> uses **`PIXABAY_API_KEY`** as primary co-engine for 1080p HD stock videos & photos (with automatic `<=95`-char query cap and 2–3 core-noun tag fallback so verbose prompts never return 0 hits; legacy `PEXELS_API_KEY` or 100% free zero-key scraping also supported), downloading `_b2.mp4` / `_b3.mp4` secondary angles on beats `> 5.8s` so **no video ever freezes**!
- **SUBAGENT VISION QA**: Launch **1 subagent** (`invoke_subagent`) to inspect every `media/contact_sheet*.jpg`, swap better candidates via `python -B "<SKILL_DIR>/scripts/fetch_media.py" --project-dir "<project_dir>" --select S02=3 S09=2`, re-hunt weak rows via `--scene S14`, and reply with a short `<= 15`-line summary.

---

## 3. One-Command v8.0 Finalizer (`finish_freecut.py` -> Stop at `freecut_workspace`!)
After writing bespoke, metaphor-driven `motion/SXX.html` scenes (`doc-motion-scenes` — zero canned widgets, each scene uniquely choreographed around the spoken beat and `style_dna`), run **one command**:
```bash
python -B "<SKILL_DIR>/scripts/finish_freecut.py" --project-dir "<project_dir>"
```
1. Generates all `lottie_overlay` JSONs in batch (`generate_lottie.py --project-dir`),
2. Renders all `motion/*.html` in parallel (`ThreadPoolExecutor(max_workers=3)`) + builds 4-column `motion/motion_contact_sheet.jpg` (`20% / 50% / 78% / 94%` live-tail check),
3. Assembles `freecut_workspace` + `<Title>.freecut.zip` with **Exact Schema v15 Zero-Rewrite Parity** (`didNormalizationChange = false`) and **Pre-Baked Workspace v2 Cold-Open Caches** (`thumbnail.jpg`, `WFORM` v1 `multi-res.bin`, `1fps` `filmstrip`),
4. Runs strict `validate_freecut.py` (`PASS` = 0 schema, cold-open cache, freeze, highlighter-spam, or cloning errors),
5. Automatically updates `<WORKSPACE>/.freecut-creator-memory.json` (`creator_memory.py --record-project`) so the next bare-audio drop remembers this edit!
- Have **1 subagent** review `motion/motion_contact_sheet*.jpg` (re-running `finish_freecut.py --force-motion` if any HTML needed adjustment), then **STOP** (do NOT render `.mp4` unless requested) and instruct the user to open `<project_dir>/freecut_workspace` directly via FreeCut's **Workspace Folder** selector (~1–2s instant load in Chrome).
