#!/usr/bin/env python3
"""
Deterministic Headless Motion Graphics Renderer for FreeCut (v6.0)
Renders self-contained HTML/CSS/SVG/Canvas/WebGL/MapLibre scenes frame-by-frame
into crisp H.264 MP4 @ 30fps across ANY aspect ratio (16:9, 9:16, 4:5, 1:1)
+ mid-scene Vision QA preview frame.

Scene contract:
  window.__setFrame(frameIdx, fps)  -> updates DOM/SVG/Canvas synchronously (or returns a Promise)

Usage:
  python render_motion_scene.py --html motion/S07.html --out motion/S07.mp4 --duration 6.5
  python render_motion_scene.py --project-dir ./my_project
"""
import argparse
import json
import os
import pathlib
import site
import subprocess
import sys

_ENGINE_SCRIPTS = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "freecut-unified-engine", "scripts")
)
if os.path.isfile(os.path.join(_ENGINE_SCRIPTS, "_runtime_env.py")) and _ENGINE_SCRIPTS not in sys.path:
    sys.path.insert(0, _ENGINE_SCRIPTS)
try:
    import _runtime_env
    _runtime_env.init()
except Exception:
    try:
        _us = site.getusersitepackages()
        if _us and os.path.isdir(_us) and _us not in sys.path:
            sys.path.append(_us)
    except Exception:
        pass

ASPECT_DIMENSIONS = {
    "16:9": (1920, 1080),
    "9:16": (1080, 1920),
    "4:5": (1080, 1350),
    "1:1": (1080, 1080),
}


def resolve_dimensions(sb: dict, cli_w: int = None, cli_h: int = None):
    if cli_w and cli_h:
        return int(cli_w), int(cli_h)
    ar = str(sb.get("aspect_ratio") or "16:9").strip()
    if ar in ASPECT_DIMENSIONS:
        w, h = ASPECT_DIMENSIONS[ar]
    else:
        w, h = 1920, 1080
    return int(sb.get("width") or w), int(sb.get("height") or h)


def render_html_to_mp4(
    html_path: str,
    out_mp4: str,
    duration_s: float,
    fps: int = 30,
    width: int = 1920,
    height: int = 1080,
    preview_jpg: str = None,
):
    from playwright.sync_api import sync_playwright

    abs_html = os.path.abspath(html_path)
    if not os.path.isfile(abs_html):
        raise FileNotFoundError(f"Motion HTML scene not found: {abs_html}")

    os.makedirs(os.path.dirname(os.path.abspath(out_mp4)), exist_ok=True)
    total_frames = max(1, int(round(duration_s * fps)))
    mid_frame = max(0, int(total_frames * 0.68))
    file_url = pathlib.Path(abs_html).as_uri()

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "image2pipe",
        "-vcodec", "mjpeg",
        "-framerate", str(fps),
        "-i", "-",
        "-an",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "17",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        os.path.abspath(out_mp4),
    ]

    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--enable-webgl", "--ignore-gpu-blocklist", "--allow-file-access-from-files"],
        )
        context = browser.new_context(
            viewport={"width": width, "height": height},
            device_scale_factor=1,
        )
        page = context.new_page()
        page.goto(file_url, wait_until="load", timeout=30000)
        try:
            page.evaluate("() => document.fonts ? document.fonts.ready : Promise.resolve()")
        except Exception:
            pass
        # Support optional async scene boot (e.g. MapLibre style load or image decode)
        try:
            page.evaluate("() => window.__readyPromise ? window.__readyPromise : Promise.resolve()")
        except Exception:
            pass
        page.wait_for_timeout(120)

        has_set_frame = page.evaluate("() => typeof window.__setFrame === 'function'")
        if not has_set_frame:
            browser.close()
            proc.kill()
            raise RuntimeError(f"Scene {html_path} must define window.__setFrame(frameIdx, fps)")

        for f_idx in range(total_frames):
            page.evaluate(f"([f, r]) => Promise.resolve(window.__setFrame(f, r))", [f_idx, fps])
            jpg_bytes = page.screenshot(type="jpeg", quality=93, animations="disabled")
            proc.stdin.write(jpg_bytes)
            if preview_jpg and f_idx == mid_frame:
                os.makedirs(os.path.dirname(os.path.abspath(preview_jpg)), exist_ok=True)
                with open(preview_jpg, "wb") as pf:
                    pf.write(jpg_bytes)

        browser.close()

    proc.stdin.close()
    stderr_bytes = proc.stderr.read()
    ret = proc.wait()
    if ret != 0:
        raise RuntimeError(f"FFmpeg encode failed ({ret}): {stderr_bytes.decode('utf-8', errors='ignore')[-500:]}")

    if not os.path.isfile(out_mp4) or os.path.getsize(out_mp4) < 2000:
        raise RuntimeError(f"Rendered MP4 invalid or empty: {out_mp4}")

    print(f"[render_motion] OK -> {out_mp4} ({total_frames}f @ {fps}fps, {width}x{height}, {duration_s:.2f}s)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", help="Single HTML motion scene file")
    ap.add_argument("--out", help="Output MP4 path (single mode)")
    ap.add_argument("--duration", type=float, help="Duration in seconds (single mode)")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--width", type=int, default=None)
    ap.add_argument("--height", type=int, default=None)
    ap.add_argument("--project-dir", help="Batch render all MOTION_SCENE entries in storyboard.json")
    ap.add_argument("--scene", nargs="*", help="Optional filter of scene IDs in --project-dir mode")
    args = ap.parse_args()

    if args.project_dir:
        sb_path = os.path.join(args.project_dir, "storyboard.json")
        sb = json.load(open(sb_path, "r", encoding="utf-8"))
        fps = int(sb.get("fps") or args.fps or 30)
        w, h = resolve_dimensions(sb, args.width, args.height)
        motion_dir = os.path.join(args.project_dir, "motion")
        os.makedirs(motion_dir, exist_ok=True)
        only = set(args.scene) if args.scene else None

        motion_scenes = [
            sc for sc in sb.get("scenes", [])
            if (
                sc.get("type") == "MOTION_SCENE"
                or str(sc.get("layout", sc.get("scene_type", ""))).lower() in ("motion_scene", "motion")
            )
            and (only is None or sc["id"] in only)
        ]

        if not motion_scenes:
            print("[render_motion] No MOTION_SCENE entries found in storyboard.json.")
            return

        for sc in motion_scenes:
            sid = sc["id"]
            dur_s = max(1.5, (sc["end_ms"] - sc["start_ms"]) / 1000.0)
            html_file = sc.get("motion_html") or os.path.join(motion_dir, f"{sid}.html")
            if not os.path.isabs(html_file) and not os.path.isfile(html_file):
                html_file = os.path.join(args.project_dir, html_file)
            out_mp4 = os.path.join(motion_dir, f"{sid}.mp4")
            prev_jpg = os.path.join(motion_dir, f"{sid}_preview.jpg")
            render_html_to_mp4(html_file, out_mp4, dur_s, fps=fps, width=w, height=h, preview_jpg=prev_jpg)
        return

    if not (args.html and args.out and args.duration):
        ap.error("Provide either --project-dir OR (--html, --out, --duration)")

    w = args.width or 1920
    h = args.height or 1080
    prev = os.path.splitext(args.out)[0] + "_preview.jpg"
    render_html_to_mp4(args.html, args.out, args.duration, fps=args.fps, width=w, height=h, preview_jpg=prev)


if __name__ == "__main__":
    main()
