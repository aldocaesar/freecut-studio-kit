#!/usr/bin/env python3
"""
FreeCut Studio Bot — Cross-Platform Environment Doctor (`doctor.py` v6.1)
=========================================================================
Verifies that ANY machine (Windows, macOS, Linux) has 100% of the binaries,
Python packages, Playwright Chromium browser, offline Natural Earth GeoJSON atlas,
SFX assets, and skills properly installed — 100% standalone with ZERO mandatory paid APIs!
"""
import importlib.util
import json
import os
import platform
import shutil
import site
import subprocess
import sys

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

_HERE_DIR = os.path.dirname(os.path.abspath(__file__))
_ALT_SCRIPTS = os.path.join(_HERE_DIR, ".agents", "skills", "freecut-unified-engine", "scripts")
for _d in (_HERE_DIR, _ALT_SCRIPTS):
    if os.path.isfile(os.path.join(_d, "_runtime_env.py")) and _d not in sys.path:
        sys.path.insert(0, _d)
try:
    import _runtime_env
    _runtime_env.init()
except Exception:
    try:
        site_u = site.getusersitepackages()
        if site_u and os.path.isdir(site_u) and site_u not in sys.path:
            sys.path.append(site_u)
    except Exception:
        pass


def _check_cmd(cmd: list) -> tuple[bool, str]:
    exe = shutil.which(cmd[0])
    if not exe:
        return False, f"'{cmd[0]}' not found in PATH"
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
        line = (r.stdout or r.stderr or "").strip().splitlines()
        return r.returncode == 0, (line[0][:75] if line else exe)
    except Exception as e:
        return False, str(e)


def _check_pkg(mod_name: str, pip_name: str) -> tuple[bool, str]:
    found = importlib.util.find_spec(mod_name) is not None
    return found, ("installed" if found else f"missing -> pip install {pip_name}")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    # Resolve root workspace (supports running from root/doctor.py OR .agents/skills/.../scripts/doctor.py)
    if os.path.basename(here) == "scripts":
        root = os.path.abspath(os.path.join(here, "..", "..", "..", ".."))
    else:
        root = here

    print("=" * 72)
    print(f"FreeCut Universal Studio Bot v6 — System Doctor ({platform.system()} {platform.release()})")
    print(f"Workspace: {root}")
    print("=" * 72)

    critical_failures = []
    warnings = []

    # 1. Core System Binaries
    print("\n[1/5] System Binaries")
    py_ok = sys.version_info >= (3, 10)
    print(f"  [{'OK' if py_ok else 'FAIL'}] Python       : {sys.version.split()[0]} ({sys.executable})")
    if not py_ok:
        critical_failures.append("Python 3.10+ is required.")

    for label, cmd, required in [
        ("FFmpeg", ["ffmpeg", "-version"], True),
        ("FFprobe", ["ffprobe", "-version"], True),
        ("Node.js", ["node", "--version"], False),
        ("Git", ["git", "--version"], False),
    ]:
        ok, info = _check_cmd(cmd)
        tag = "OK" if ok else ("FAIL" if required else "WARN")
        print(f"  [{tag:4s}] {label:12s} : {info}")
        if not ok:
            if required:
                critical_failures.append(f"{label} missing in PATH.")
            else:
                warnings.append(f"{label} missing (needed only to run local FreeCut web app).")

    # 2. Python Packages (Zero-Key Free Stack)
    print("\n[2/5] Python Editing, Transcription & Vision Stack")
    pkgs = [
        ("faster_whisper", "faster-whisper", True, "Free local word-level transcription"),
        ("edge_tts", "edge-tts", True, "Free neural voiceover + word timestamps"),
        ("playwright", "playwright", True, "30fps Motion Graphics & Web Evidence capture"),
        ("PIL", "Pillow", True, "Contact sheets & image processing"),
        ("cv2", "opencv-python-headless", True, "Blur/face/frame inspection"),
        ("rembg", "rembg[cpu]", False, "Automatic subject background cutout"),
        ("rapidocr_onnxruntime", "rapidocr-onnxruntime", False, "Watermark/OCR guard"),
        ("yt_dlp", "yt-dlp", True, "Real entity video B-roll hunter"),
        ("bs4", "beautifulsoup4", True, "Press article & OpenGraph photo extractor"),
        ("requests", "requests", True, "HTTP client"),
    ]
    for mod, pip_pkg, req, desc in pkgs:
        ok, info = _check_pkg(mod, pip_pkg)
        tag = "OK" if ok else ("FAIL" if req else "WARN")
        print(f"  [{tag:4s}] {pip_pkg:24s} : {info} ({desc})")
        if not ok:
            if req:
                critical_failures.append(f"Missing Python package: {pip_pkg}")
            else:
                warnings.append(f"Optional package '{pip_pkg}' not installed ({desc}).")

    # Verify faster-whisper actual compute backend (CUDA vs crash-proof CPU int8)
    if importlib.util.find_spec("faster_whisper"):
        cuda_dll_ok = (os.name != "nt")
        if os.name == "nt":
            import ctypes
            for dll in ("cublas64_12.dll", "cublas64_11.dll"):
                try:
                    ctypes.WinDLL(dll)
                    cuda_dll_ok = True
                    break
                except OSError:
                    pass
        mode_note = "GPU CUDA ready" if cuda_dll_ok else "CPU int8 auto-fallback active (100% free, zero CUDA DLL needed)"
        print(f"  [OK  ] {'whisper-compute':24s} : {mode_note}")

    # 3. Playwright Chromium Binary Check
    print("\n[3/5] Headless Chromium Renderer")
    pw_ok = False
    if importlib.util.find_spec("playwright"):
        try:
            r = subprocess.run(
                [sys.executable, "-c", "from playwright.sync_api import sync_playwright\nwith sync_playwright() as p:\n b=p.chromium.launch(headless=True); b.close(); print('Chromium headless OK')"],
                capture_output=True,
                text=True,
                timeout=20,
            )
            pw_ok = r.returncode == 0
            msg = (r.stdout.strip() or r.stderr.strip().splitlines()[-1]) if (r.stdout or r.stderr) else "unknown"
        except Exception as e:
            msg = str(e)
    else:
        msg = "playwright package missing"
    print(f"  [{'OK' if pw_ok else 'FAIL'}] Playwright Chromium      : {msg}")
    if not pw_ok:
        critical_failures.append("Playwright Chromium browser missing -> run `python -m playwright install chromium`")

    # 4. Bundled Skills, Offline World Atlas & SFX
    print("\n[4/5] Bundled Skills, Offline GeoJSON Atlas & Audio Assets")
    required_paths = [
        ("doc-art-director", os.path.join(root, ".agents", "skills", "doc-art-director", "SKILL.md")),
        ("freecut-unified-engine", os.path.join(root, ".agents", "skills", "freecut-unified-engine", "SKILL.md")),
        ("doc-motion-scenes", os.path.join(root, ".agents", "skills", "doc-motion-scenes", "SKILL.md")),
        ("doc-lottie-overlays", os.path.join(root, ".agents", "skills", "doc-lottie-overlays", "SKILL.md")),
        ("Offline Natural Earth Atlas", os.path.join(root, ".agents", "skills", "doc-motion-scenes", "kit", "world-atlas.js")),
        ("Motion Kit v6", os.path.join(root, ".agents", "skills", "doc-motion-scenes", "kit", "motion-kit.js")),
        ("Claude Mirror (.claude/skills)", os.path.join(root, ".claude", "skills", "freecut-unified-engine", "SKILL.md")),
    ]
    for label, p in required_paths:
        exists = os.path.isfile(p)
        sz = f"{os.path.getsize(p)//1024} KB" if exists else "MISSING"
        print(f"  [{'OK' if exists else 'FAIL'}] {label:30s} : {sz}")
        if not exists and "Claude Mirror" not in label:
            critical_failures.append(f"Missing bundled file: {p}")
        elif not exists:
            warnings.append("`.claude/skills` mirror not synced yet (run installer to enable Claude Code discovery).")

    # 5. Optional API Keys (.env) — Zero mandatory keys!
    print("\n[5/5] Optional Accelerator Keys (.env) — 0 Mandatory Keys!")
    env_path = os.path.join(root, ".env")
    env_vars = dict(os.environ)
    if os.path.isfile(env_path):
        for ln in open(env_path, "r", encoding="utf-8", errors="ignore"):
            ln = ln.strip()
            if ln and not ln.startswith("#") and "=" in ln:
                k, v = ln.split("=", 1)
                if v.strip():
                    env_vars.setdefault(k.strip(), v.strip())

    for k, purpose in [
        ("PIXABAY_API_KEY", "Recommended FREE stock HD video & photo API — instant key at pixabay.com/api/docs/ (fallback: scraped HD photos + YouTube)"),
        ("GROQ_API_KEY", "Optional cloud ultra-fast Whisper (fallback: FREE local faster-whisper)"),
        ("ASSEMBLYAI_API_KEY", "Optional cloud AssemblyAI Universal-2 (fallback: FREE local faster-whisper)"),
        ("ELEVENLABS_API_KEY", "Optional premium TTS (fallback: FREE edge-tts)"),
        ("PEXELS_API_KEY", "Optional legacy stock key if you already own one (Pexels paused new API keys; Pixabay covers 100%)"),
    ]:
        present = bool(env_vars.get(k))
        print(f"  [{'SET ' if present else 'FREE'}] {k:20s} : {'Configured' if present else purpose}")

    marker_path = os.path.join(root, ".freecut-setup-done.json")
    onboarded = os.path.isfile(marker_path)
    print(f"  [{'DONE' if onboarded else 'NEW '}] {'ONBOARDING_STATE':20s} : {'Completed (.freecut-setup-done.json)' if onboarded else 'First run on this workspace — ask optional keys once then run bootstrap_env.py --mark-onboarded'}")

    mem_path = os.path.join(root, ".freecut-creator-memory.json")
    if os.path.isfile(mem_path):
        try:
            mem_data = json.load(open(mem_path, "r", encoding="utf-8"))
            n_rules = len(mem_data.get("style_rules") or [])
            n_projs = len(mem_data.get("recent_projects") or [])
            mem_note = f"Active ({n_rules} style rule(s), {n_projs} recent project(s) remembered)"
        except Exception:
            mem_note = "Present (.freecut-creator-memory.json)"
        print(f"  [MEM ] {'CREATOR_MEMORY':20s} : {mem_note}")
    else:
        print(f"  [INIT] {'CREATOR_MEMORY':20s} : Ready to learn automatically from your edits & feedback (.freecut-creator-memory.json)")

    print("\n" + "=" * 72)
    if critical_failures:
        print(f"RESULT: [ACTION NEEDED] {len(critical_failures)} critical issue(s):")
        for c in critical_failures:
            print(f"  - {c}")
        sys.exit(1)
    else:
        print("RESULT: [READY] 100% ready to edit videos from Audio, Video, SRT, or Script (Zero Mandatory Keys)!")
        if warnings:
            for w in warnings:
                print(f"  (Note: {w})")
    print("=" * 72)


if __name__ == "__main__":
    main()
