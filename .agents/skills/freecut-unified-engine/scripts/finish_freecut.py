#!/usr/bin/env python3
"""
finish_freecut.py — Single-Command Finalizer Pipeline for FreeCut (v6.4)
========================================================================
Eliminates mid-run stalls on long 10–20 min videos by chaining the entire
tail of production into ONE deterministic CLI call:
  1. Batch-generates any missing Lottie JSON overlays (`generate_lottie.py --project-dir`)
  2. Renders all `MOTION_SCENE` clips in parallel (`render_motion_scene.py --workers 3`)
     + generates paginated `motion/motion_contact_sheet.jpg`
  3. Assembles the 10-track native `freecut_workspace` + `<Title>.freecut.zip`
  4. Runs strict schemaVersion 15 + anti-vício validation (`validate_freecut.py`)

Usage:
  python finish_freecut.py --project-dir ./projects/my_video
"""
import argparse
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
import _runtime_env  # noqa: E402

_runtime_env.init()

SKILLS_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
LOTTIE_SCRIPT = os.path.join(SKILLS_ROOT, "doc-lottie-overlays", "scripts", "generate_lottie.py")
MOTION_SCRIPT = os.path.join(SKILLS_ROOT, "doc-motion-scenes", "scripts", "render_motion_scene.py")
ASSEMBLE_SCRIPT = os.path.join(SCRIPT_DIR, "assemble_freecut.py")
VALIDATE_SCRIPT = os.path.join(SCRIPT_DIR, "validate_freecut.py")


def _run_step(label: str, cmd: list[str]):
    print(f"\n[finish_freecut] >>> {label}", flush=True)
    res = subprocess.run(cmd, stdin=subprocess.DEVNULL)
    if res.returncode != 0:
        sys.exit(res.returncode)


def main():
    ap = argparse.ArgumentParser(description="Run Lottie + Parallel Motion Render + FreeCut Assembly + Validation in one step.")
    ap.add_argument("--project-dir", required=True, help="Target project directory containing storyboard.json")
    ap.add_argument("--workers", type=int, default=3, help="Parallel motion render workers (default: 3)")
    ap.add_argument("--force-motion", action="store_true", help="Force re-render of all motion scenes")
    ap.add_argument("--captions", action="store_true", help="Enable word-level captions track")
    args = ap.parse_args()

    proj = os.path.abspath(args.project_dir)
    if not os.path.isfile(os.path.join(proj, "storyboard.json")):
        sys.exit(f"[finish_freecut] ERROR: storyboard.json not found in {proj}")

    if os.path.isfile(LOTTIE_SCRIPT):
        _run_step("Step 1/4: Batch Lottie Overlays", [sys.executable, LOTTIE_SCRIPT, "--project-dir", proj])

    if os.path.isfile(MOTION_SCRIPT):
        m_cmd = [sys.executable, MOTION_SCRIPT, "--project-dir", proj, "--workers", str(args.workers)]
        if args.force_motion:
            m_cmd.append("--force")
        _run_step("Step 2/4: Parallel 30fps Motion Graphics + motion_contact_sheet.jpg", m_cmd)

    a_cmd = [sys.executable, ASSEMBLE_SCRIPT, "--project-dir", proj]
    if args.captions:
        a_cmd.append("--captions")
    _run_step("Step 3/4: Native 10-Track FreeCut Workspace Assembly", a_cmd)

    _run_step("Step 4/4: Schema v15 & Anti-Vício Validation", [sys.executable, VALIDATE_SCRIPT, "--project-dir", proj])

    ws = os.path.join(proj, "freecut_workspace")
    print(f"\n[finish_freecut] READY -> {ws}", flush=True)


if __name__ == "__main__":
    main()
