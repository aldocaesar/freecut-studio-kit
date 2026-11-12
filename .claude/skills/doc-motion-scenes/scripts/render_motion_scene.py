#!/usr/bin/env python3
"""
Deterministic Headless Motion Graphics Renderer for FreeCut (v7.0)
Renders self-contained HTML/CSS/SVG/Canvas/WebGL/MapLibre scenes frame-by-frame
into crisp H.264 MP4 @ 30fps across ANY aspect ratio (16:9, 9:16, 4:5, 1:1),
using native ThreadPoolExecutor(max_workers=3) + 4-frame Dead-Tail Motion Detector
+ automatic paginated `motion/motion_contact_sheet.jpg` (20%, 50%, 78%, 94%).

Scene contract:
  window.__setFrame(frameIdx, fps) -> updates DOM/SVG/Canvas synchronously (or returns a Promise)

Usage:
  python -B render_motion_scene.py --project-dir ./my_project
  python -B render_motion_scene.py --project-dir ./my_project --workers 3 --force
  python -B render_motion_scene.py --html motion/S07.html --out motion/S07.mp4 --duration 6.5
"""
import argparse
import concurrent.futures
import io
import json
import os
import pathlib
import site
import subprocess
import sys

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

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

from PIL import Image, ImageDraw, ImageFont, ImageOps  # noqa: E402

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


def _extract_cached_frames(mp4_path: str, duration_s: float) -> list[bytes]:
    frames = []
    for pct in (0.20, 0.50, 0.78, 0.94):
        ts = max(0.05, min(max(0.05, duration_s - 0.08), duration_s * pct))
        cmd = [
            "ffmpeg", "-nostdin", "-ss", f"{ts:.2f}", "-i", mp4_path,
            "-frames:v", "1", "-f", "image2pipe", "-vcodec", "mjpeg", "-q:v", "3", "-",
        ]
        res = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True)
        if res.returncode == 0 and res.stdout:
            frames.append(res.stdout)
    return frames


def _compute_tail_motion_diff(samples: list[bytes]) -> float:
    """Computes mean pixel delta (0..255) between 78% and 94% frames to catch frozen motion tails."""
    if len(samples) < 4 or not samples[2] or not samples[3]:
        return 9.9
    try:
        with Image.open(io.BytesIO(samples[2])) as im_a, Image.open(io.BytesIO(samples[3])) as im_b:
            ga = im_a.convert("L").resize((160, 90))
            gb = im_b.convert("L").resize((160, 90))
            pa = ga.tobytes()
            pb = gb.tobytes()
            return sum(abs(a - b) for a, b in zip(pa, pb)) / max(1, len(pa))
    except Exception:
        return 9.9


def render_html_to_mp4(
    html_path: str,
    out_mp4: str,
    duration_s: float,
    fps: int = 30,
    width: int = 1920,
    height: int = 1080,
    preview_jpg: str = None,
    force: bool = False,
) -> list[bytes]:
    from playwright.sync_api import sync_playwright

    abs_html = os.path.abspath(html_path)
    if not os.path.isfile(abs_html):
        raise FileNotFoundError(f"Motion HTML scene not found: {abs_html}")

    abs_out = os.path.abspath(out_mp4)
    os.makedirs(os.path.dirname(abs_out), exist_ok=True)
    total_frames = max(1, int(round(duration_s * fps)))

    # Incremental cache skip when MP4 is already newer than HTML
    if (
        not force
        and os.path.isfile(abs_out)
        and os.path.getsize(abs_out) >= 2000
        and os.path.getmtime(abs_out) >= os.path.getmtime(abs_html)
    ):
        samples = _extract_cached_frames(abs_out, duration_s)
        if preview_jpg and samples and not os.path.isfile(preview_jpg):
            with open(preview_jpg, "wb") as pf:
                pf.write(samples[min(1, len(samples) - 1)])
        print(f"[render_motion] CACHED -> {out_mp4} ({total_frames}f @ {fps}fps)", flush=True)
        return samples

    mid_frame = max(0, int(total_frames * 0.68))
    sample_indices = {
        max(0, int(total_frames * 0.20)): 0,
        max(0, int(total_frames * 0.50)): 1,
        max(0, min(total_frames - 2, int(total_frames * 0.78))): 2,
        max(0, min(total_frames - 1, int(total_frames * 0.94))): 3,
    }
    sampled_bytes = [None, None, None, None]
    file_url = pathlib.Path(abs_html).as_uri()

    ffmpeg_cmd = [
        "ffmpeg", "-nostdin", "-y",
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
        abs_out,
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
            page.evaluate("([f, r]) => Promise.resolve(window.__setFrame(f, r))", [f_idx, fps])
            jpg_bytes = page.screenshot(type="jpeg", quality=93, animations="disabled")
            proc.stdin.write(jpg_bytes)
            if f_idx in sample_indices:
                sampled_bytes[sample_indices[f_idx]] = jpg_bytes
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

    if not os.path.isfile(abs_out) or os.path.getsize(abs_out) < 2000:
        raise RuntimeError(f"Rendered MP4 invalid or empty: {out_mp4}")

    clean_samples = [b for b in sampled_bytes if b is not None]
    tail_diff = _compute_tail_motion_diff(clean_samples)
    tail_tag = f"tail_diff={tail_diff:.2f}" if tail_diff >= 0.18 else f"WARN_STATIC_TAIL({tail_diff:.3f})"
    print(f"[render_motion] OK -> {out_mp4} ({total_frames}f @ {fps}fps, {width}x{height}, {duration_s:.2f}s, {tail_tag})", flush=True)
    return clean_samples


def render_motion_contact_sheets(records: list[dict], motion_dir: str, max_rows_per_sheet: int = 8) -> list[str]:
    """Builds paginated `motion/motion_contact_sheet.jpg` grids (<=8 motion scenes per sheet, 4 frames per row: 20%, 50%, 78%, 94%)."""
    if not records:
        return []
    os.makedirs(motion_dir, exist_ok=True)
    try:
        font_hdr = ImageFont.truetype("arialbd.ttf", 19)
        font_sub = ImageFont.truetype("arial.ttf", 14)
    except Exception:
        font_hdr = ImageFont.load_default()
        font_sub = font_hdr

    total_batches = (len(records) + max_rows_per_sheet - 1) // max_rows_per_sheet
    out_paths = []
    sheet_w = 1860
    row_h = 322
    pad_top = 64

    for b_idx in range(total_batches):
        batch = records[b_idx * max_rows_per_sheet : (b_idx + 1) * max_rows_per_sheet]
        sheet_h = pad_top + len(batch) * row_h + 24
        canvas = Image.new("RGB", (sheet_w, sheet_h), (14, 18, 26))
        draw = ImageDraw.Draw(canvas)
        title = f"MOTION GRAPHICS QA v7.0 — BATCH {b_idx + 1}/{total_batches} (Verify palette diversity, zero clipped text & live 78%->94% tail)"
        draw.text((24, 20), title, fill=(248, 250, 252), font=font_hdr)

        for r_i, rec in enumerate(batch):
            y0 = pad_top + r_i * row_h
            frames = rec.get("samples") or []
            tdiff = _compute_tail_motion_diff(frames)
            live_status = f"LIVE TAIL Δ={tdiff:.2f}" if tdiff >= 0.18 else f"STATIC TAIL Δ={tdiff:.3f}!"
            hdr_col = (251, 191, 36) if tdiff >= 0.18 else (248, 113, 113)
            draw.rectangle([16, y0, sheet_w - 16, y0 + row_h - 12], fill=(22, 28, 38), outline=(45, 55, 72), width=1)
            hdr = f"{rec['sid']} • {rec['dur_s']:.1f}s ({int(round(rec['dur_s']*rec['fps']))}f) • {live_status} • {rec['brief'][:105]}"
            draw.text((30, y0 + 10), hdr, fill=hdr_col, font=font_hdr)

            labels = ("20% Entrada", "50% Meio", "78% Clímax", "94% Cauda Viva")
            thumb_w, thumb_h = 432, 232
            for c_i in range(4):
                tx = 30 + c_i * (thumb_w + 18)
                ty = y0 + 64
                draw.text((tx + 4, y0 + 42), labels[c_i], fill=(203, 213, 225), font=font_sub)
                if c_i < len(frames) and frames[c_i]:
                    with Image.open(io.BytesIO(frames[c_i])) as im:
                        th = ImageOps.contain(im.convert("RGB"), (thumb_w, thumb_h), Image.Resampling.LANCZOS)
                        paste_x = tx + (thumb_w - th.width) // 2
                        paste_y = ty + (thumb_h - th.height) // 2
                        draw.rectangle([tx, ty, tx + thumb_w, ty + thumb_h], fill=(10, 12, 18), outline=(65, 78, 98), width=1)
                        canvas.paste(th, (paste_x, paste_y))
                else:
                    draw.rectangle([tx, ty, tx + thumb_w, ty + thumb_h], fill=(35, 20, 20), outline=(180, 60, 60), width=2)

        fname = "motion_contact_sheet.jpg" if b_idx == 0 else f"motion_contact_sheet_batch_{b_idx + 1}.jpg"
        out_p = os.path.join(motion_dir, fname)
        canvas.save(out_p, "JPEG", quality=90)
        out_paths.append(out_p)
    return out_paths


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
    ap.add_argument("--workers", type=int, default=3, help="Parallel Playwright render workers (default: 3)")
    ap.add_argument("--force", action="store_true", help="Re-render even if MP4 is newer than HTML")
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

        def _job(sc: dict) -> dict:
            sid = sc["id"]
            dur_s = max(1.5, (sc["end_ms"] - sc["start_ms"]) / 1000.0)
            html_file = sc.get("motion_html") or os.path.join(motion_dir, f"{sid}.html")
            if not os.path.isabs(html_file) and not os.path.isfile(html_file):
                html_file = os.path.join(args.project_dir, html_file)
            out_mp4 = os.path.join(motion_dir, f"{sid}.mp4")
            prev_jpg = os.path.join(motion_dir, f"{sid}_preview.jpg")
            samples = render_html_to_mp4(
                html_file, out_mp4, dur_s, fps=fps, width=w, height=h, preview_jpg=prev_jpg, force=args.force
            )
            brief = sc.get("motion_brief") or sc.get("headline") or sc.get("narration") or sid
            return {"sid": sid, "dur_s": dur_s, "fps": fps, "brief": str(brief).replace("\n", " "), "samples": samples}

        workers = max(1, min(int(args.workers or 3), len(motion_scenes)))
        results_by_id = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(_job, sc): sc["id"] for sc in motion_scenes}
            for fut in concurrent.futures.as_completed(futs):
                sid = futs[fut]
                results_by_id[sid] = fut.result()

        ordered_records = [results_by_id[sc["id"]] for sc in motion_scenes if sc["id"] in results_by_id]
        sheets = render_motion_contact_sheets(ordered_records, motion_dir)
        for sp in sheets:
            print(f"[render_motion] Motion QA contact sheet ready: {sp}", flush=True)
        return

    if not (args.html and args.out and args.duration):
        ap.error("Provide either --project-dir OR (--html, --out, --duration)")

    w = args.width or 1920
    h = args.height or 1080
    prev = os.path.splitext(args.out)[0] + "_preview.jpg"
    render_html_to_mp4(args.html, args.out, args.duration, fps=args.fps, width=w, height=h, preview_jpg=prev, force=args.force)


if __name__ == "__main__":
    main()
