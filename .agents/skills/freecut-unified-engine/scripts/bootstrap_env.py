#!/usr/bin/env python3
"""
bootstrap_env.py — Zero-ZIP First-Run Auto-Installer for Editor-FreeCut (v6.3)
==============================================================================
Enables 1-click sharing of `Editor-FreeCut` via an OpenBot shareable bot link:
OpenBot's link installs the profile and the 4 `SKILL.md` files; when a new user
sends their first task on a fresh PC, the bot pulls the kit from its public
GitHub repo (if `scripts/` is not present yet) and runs `bootstrap_env.py` to
auto-install missing Python libraries, FFmpeg, and Playwright Chromium with
zero manual `.zip` files or paid API keys.

Usage:
  python bootstrap_env.py
  python bootstrap_env.py --with-freecut-ui ./freecut-app
  python bootstrap_env.py --setup-keys
"""
import argparse
import importlib.util
import io
import os
import platform
import shutil
import ssl
import subprocess
import sys
import urllib.request
import zipfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import _runtime_env  # noqa: E402

_runtime_env.init()

DOCTOR_SCRIPT = os.path.join(SCRIPT_DIR, "doctor.py")

REQUIRED_PIP_PACKAGES = [
    ("faster_whisper", "faster-whisper>=1.0.0"),
    ("edge_tts", "edge-tts>=6.1.12"),
    ("PIL", "Pillow>=10.2.0"),
    ("numpy", "numpy>=1.26.0"),
    ("cv2", "opencv-python-headless>=4.9.0"),
    ("bs4", "beautifulsoup4>=4.12.0"),
    ("requests", "requests>=2.31.0"),
    ("yt_dlp", "yt-dlp>=2024.8.6"),
    ("rembg", "rembg>=2.0.57"),
    ("onnxruntime", "onnxruntime>=1.17.0"),
    ("rapidocr_onnxruntime", "rapidocr-onnxruntime>=1.3.0"),
    ("playwright", "playwright>=1.44.0"),
]


def _run(cmd, check=False):
    print(f"[bootstrap] $ {' '.join(cmd)}", flush=True)
    return subprocess.run(cmd, stdin=subprocess.DEVNULL, check=check)


def _download_zip(url: str) -> bytes:
    try:
        return urllib.request.urlopen(url, timeout=60).read()
    except Exception:
        ctx = ssl._create_unverified_context()
        return urllib.request.urlopen(url, context=ctx, timeout=60).read()


def ensure_ffmpeg():
    _runtime_env.ensure_runtime_paths()
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        print("[bootstrap] FFmpeg & FFprobe already on PATH.", flush=True)
        return
    sys_name = platform.system().lower()
    print(f"[bootstrap] FFmpeg missing — attempting automatic install ({sys_name})...", flush=True)
    if sys_name == "windows" and shutil.which("winget"):
        _run(
            [
                "winget",
                "install",
                "--id",
                "Gyan.FFmpeg",
                "-e",
                "--accept-source-agreements",
                "--accept-package-agreements",
            ]
        )
    elif sys_name == "darwin" and shutil.which("brew"):
        _run(["brew", "install", "ffmpeg"])
    elif sys_name == "linux" and shutil.which("apt-get"):
        _run(["sudo", "-n", "apt-get", "update"])
        _run(["sudo", "-n", "apt-get", "install", "-y", "ffmpeg"])
    _runtime_env.ensure_runtime_paths()


def ensure_nodejs():
    _runtime_env.ensure_runtime_paths()
    if shutil.which("npm.cmd") or shutil.which("npm"):
        return
    sys_name = platform.system().lower()
    print(f"[bootstrap] Node.js missing — attempting automatic install ({sys_name})...", flush=True)
    if sys_name == "windows" and shutil.which("winget"):
        _run(
            [
                "winget",
                "install",
                "--id",
                "OpenJS.NodeJS.LTS",
                "-e",
                "--accept-source-agreements",
                "--accept-package-agreements",
            ]
        )
    elif sys_name == "darwin" and shutil.which("brew"):
        _run(["brew", "install", "node"])
    elif sys_name == "linux" and shutil.which("apt-get"):
        _run(["sudo", "-n", "apt-get", "update"])
        _run(["sudo", "-n", "apt-get", "install", "-y", "nodejs", "npm"])
    _runtime_env.ensure_runtime_paths()


def ensure_pip_packages():
    _runtime_env.ensure_user_site()
    missing_specs = []
    for mod_name, pip_spec in REQUIRED_PIP_PACKAGES:
        if importlib.util.find_spec(mod_name) is None:
            missing_specs.append(pip_spec)
    if not missing_specs:
        print("[bootstrap] All required Python packages already installed.", flush=True)
        return
    print(
        f"[bootstrap] Installing {len(missing_specs)} missing Python package(s): {', '.join(missing_specs)}",
        flush=True,
    )
    attempts = [
        [sys.executable, "-m", "pip", "install", "--upgrade"] + missing_specs,
        [sys.executable, "-m", "pip", "install", "--user", "--upgrade"] + missing_specs,
        [sys.executable, "-m", "pip", "install", "--break-system-packages", "--upgrade"] + missing_specs,
    ]
    for cmd in attempts:
        res = _run(cmd, check=False)
        if res.returncode == 0:
            _runtime_env.ensure_runtime_paths()
            return
    raise RuntimeError(f"Failed to install required Python packages: {missing_specs}")


def ensure_playwright_chromium():
    print("[bootstrap] Ensuring Playwright Chromium headless browser is installed...", flush=True)
    _run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)


def install_freecut_ui(target_dir: str):
    target_abs = os.path.abspath(target_dir)
    if not os.path.isdir(target_abs):
        if shutil.which("git"):
            _run(["git", "clone", "--depth", "1", "https://github.com/walterlow/freecut.git", target_abs], check=True)
        else:
            print("[bootstrap] git not found — downloading walterlow/freecut via HTTPS zip...", flush=True)
            raw = _download_zip("https://github.com/walterlow/freecut/archive/refs/heads/main.zip")
            tmp_extract = target_abs + "_tmp_zip"
            shutil.rmtree(tmp_extract, ignore_errors=True)
            with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                zf.extractall(tmp_extract)
            entries = [os.path.join(tmp_extract, d) for d in os.listdir(tmp_extract)]
            src_root = entries[0] if len(entries) == 1 and os.path.isdir(entries[0]) else tmp_extract
            shutil.move(src_root, target_abs)
            shutil.rmtree(tmp_extract, ignore_errors=True)
    ensure_nodejs()
    npm_bin = shutil.which("npm.cmd") or shutil.which("npm")
    if npm_bin:
        subprocess.run([npm_bin, "install"], cwd=target_abs, stdin=subprocess.DEVNULL, check=False)
        print(f"[bootstrap] FreeCut Web UI ready at {target_abs} (run `npm run dev` to open).", flush=True)


def setup_optional_env_keys(env_path: str):
    """Interactive terminal helper (outside OpenBot) to add/update optional keys anytime without reinstalling."""
    keys = [
        ("PEXELS_API_KEY", "Stock video/image fallback for generic B-roll (optional)"),
        ("GROQ_API_KEY", "Cloud ultra-fast Whisper alignment (optional; free local faster-whisper is default)"),
        ("ASSEMBLYAI_API_KEY", "Cloud word-timestamp alignment (optional)"),
        ("ELEVENLABS_API_KEY", "Premium studio voiceover TTS (optional; free edge-tts is default)"),
    ]
    existing = {}
    if os.path.isfile(env_path):
        for line in open(env_path, "r", encoding="utf-8", errors="ignore"):
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                existing[k.strip()] = v.strip()

    print("\n[bootstrap] Optional Accelerator API Keys (Press ENTER to skip any — 0 keys are mandatory!):")
    changed = False
    for k, desc in keys:
        cur = "SET" if existing.get(k) else "empty"
        try:
            val = input(f"  {k} [{cur}] ({desc}): ").strip()
        except EOFError:
            break
        if val:
            existing[k] = val
            changed = True

    if changed:
        with open(env_path, "w", encoding="utf-8") as fh:
            for k, v in existing.items():
                fh.write(f"{k}={v}\n")
        print(f"[bootstrap] Saved updated keys to {env_path}")
    else:
        print("[bootstrap] Kept 100% Free standalone defaults (you can run `--setup-keys` anytime later).")


def main():
    ap = argparse.ArgumentParser(description="Auto-install Editor-FreeCut runtime dependencies on a fresh machine.")
    ap.add_argument("--with-freecut-ui", help="Optional folder where walterlow/freecut web UI should be cloned & installed")
    ap.add_argument("--setup-keys", action="store_true", help="Interactively configure optional accelerator API keys (.env) anytime")
    ap.add_argument("--force", action="store_true", help="Run installers even if doctor.py already reports READY")
    args = ap.parse_args()

    if args.setup_keys:
        ws_env = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", "..", ".env"))
        setup_optional_env_keys(ws_env)

    if not args.force and os.path.isfile(DOCTOR_SCRIPT):
        probe = subprocess.run([sys.executable, DOCTOR_SCRIPT], stdin=subprocess.DEVNULL, capture_output=True, text=True)
        if probe.returncode == 0:
            print("[bootstrap] Environment already [READY] (0 missing dependencies).", flush=True)
            if args.with_freecut_ui:
                install_freecut_ui(args.with_freecut_ui)
            sys.exit(0)

    ensure_ffmpeg()
    ensure_pip_packages()
    ensure_playwright_chromium()
    if args.with_freecut_ui:
        install_freecut_ui(args.with_freecut_ui)

    if os.path.isfile(DOCTOR_SCRIPT):
        final = subprocess.run([sys.executable, DOCTOR_SCRIPT], stdin=subprocess.DEVNULL)
        sys.exit(final.returncode)


if __name__ == "__main__":
    main()
