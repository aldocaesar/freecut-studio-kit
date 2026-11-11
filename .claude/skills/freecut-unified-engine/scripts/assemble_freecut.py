#!/usr/bin/env python3
"""
assemble_freecut.py (v6.3 — Native FreeCut TextMotion, Multi-Span Editorial & 3-Archetype Cutouts)
==================================================================================================
Compiles a human-grade documentary timeline directly into:
  1. `<project_dir>/freecut_workspace/` — Ready to open & render immediately in FreeCut (browser).
  2. `<project_dir>/<SafeTitle>.freecut.zip` — Portable FreeCut project bundle.

Strictly follows `walterlow/freecut` schemaVersion 15 (`vcy-AGOSTO` architecture, zero `FREECUT-card` boxes):
  - Center-origin coordinates (`1920x1080`, `1080x1920`, `1080x1350`, `1080x1080`) @ 30fps.
  - All clip-local keyframes clamped to `[0, durationInFrames - 1]` (zero trimmed out-of-clip keyframes).
  - Native `TextMotionSpec` (`textMotion: {in, out, loop}`), `TextSpan[]` (`textSpans` multi-font lockups),
    `MotionModifier[]` (`motionModifiers` Clipe Motion), and `LottieItem` (`frameRate`, `totalFrames`).
  - 3 Distinct Cutout Editorial Archetypes (`poster_monumental_center`, `archival_dossier_paper`,
    `magazine_grounded_portrait`) with automatic bottom-edge portrait grounding (zero floating chopped torsos).
"""
import argparse
import glob
import hashlib
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
import time
import uuid
import wave
import zipfile
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFilter
import numpy as np

ASPECT_DIMENSIONS = {
    "16:9": (1920, 1080),
    "9:16": (1080, 1920),
    "4:5": (1080, 1350),
    "1:1": (1080, 1080),
}

CANVAS_W = 1920
CANVAS_H = 1080
FPS = 30

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BUNDLED_SFX_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "assets", "sfx"))
LOTTIE_GEN_SCRIPT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "doc-lottie-overlays", "scripts", "generate_lottie.py"))

TRACKS = [
    {
        "id": "track_captions",
        "name": "Dynamic Subtitles",
        "kind": "video",
        "height": 72,
        "locked": False,
        "visible": True,
        "muted": False,
        "solo": False,
        "order": 0,
        "syncLock": True,
        "volume": 0,
    },
    {
        "id": "track_text",
        "name": "Text & Editorial Titles",
        "kind": "video",
        "height": 96,
        "locked": False,
        "visible": True,
        "muted": False,
        "solo": False,
        "order": 1,
        "syncLock": True,
        "volume": 0,
    },
    {
        "id": "track_fg_3",
        "name": "Lottie & Vector Overlays",
        "kind": "video",
        "height": 88,
        "locked": False,
        "visible": True,
        "muted": False,
        "solo": False,
        "order": 2,
        "syncLock": True,
        "volume": 0,
    },
    {
        "id": "track_fg_2",
        "name": "Foreground Cutouts",
        "kind": "video",
        "height": 88,
        "locked": False,
        "visible": True,
        "muted": False,
        "solo": False,
        "order": 3,
        "syncLock": True,
        "volume": 0,
    },
    {
        "id": "track_fg_1",
        "name": "Film & Analog Grade (GPU)",
        "kind": "video",
        "height": 84,
        "locked": False,
        "visible": True,
        "muted": False,
        "solo": False,
        "order": 4,
        "syncLock": True,
        "volume": 0,
    },
    {
        "id": "track_anchor",
        "name": "Main Visuals (Anchor)",
        "kind": "video",
        "height": 110,
        "locked": False,
        "visible": True,
        "muted": False,
        "solo": False,
        "order": 5,
        "syncLock": True,
        "volume": 0,
    },
    {
        "id": "track_bg",
        "name": "Atmospheric Backdrop",
        "kind": "video",
        "height": 96,
        "locked": False,
        "visible": True,
        "muted": False,
        "solo": False,
        "order": 6,
        "syncLock": True,
        "volume": 0,
    },
    {
        "id": "track_sfx",
        "name": "Sound Effects (SFX)",
        "kind": "audio",
        "height": 80,
        "locked": False,
        "visible": True,
        "muted": False,
        "solo": False,
        "order": 7,
        "syncLock": True,
        "volume": 0,
    },
    {
        "id": "track_audio",
        "name": "Narration (VO)",
        "kind": "audio",
        "height": 100,
        "locked": False,
        "visible": True,
        "muted": False,
        "solo": False,
        "order": 8,
        "syncLock": True,
        "volume": 0,
    },
    {
        "id": "track_bgm",
        "name": "Music Bed (BGM)",
        "kind": "audio",
        "height": 76,
        "locked": False,
        "visible": True,
        "muted": False,
        "solo": False,
        "order": 9,
        "syncLock": True,
        "volume": 0,
    },
]

LIGHT_BG_HEXES = {"#FAF9F6", "#F5F5F7", "#F9F9FB", "#FFFFFF", "#F4F1EA", "#F6F3EC", "#EFECE4", "#F8FAFC", "#F3EFE6"}

# Exact FreeCut `TextMotionEffect` presets (`src/shared/typography/text-motion/text-motion-presets.ts`)
FREECUT_TEXT_IN_PRESETS: Dict[str, Dict[str, Any]] = {
    "typewriter": {"presetId": "typewriter", "durationFrames": 1, "staggerFrames": 2, "intensity": 1.0, "order": "forward", "easing": "linear", "seed": 0, "unit": "character"},
    "fade-up": {"presetId": "fade-up", "durationFrames": 12, "staggerFrames": 3, "intensity": 1.0, "order": "forward", "easing": "ease-out", "seed": 0, "unit": "word"},
    "rise": {"presetId": "rise", "durationFrames": 14, "staggerFrames": 4, "intensity": 1.0, "order": "forward", "easing": "ease-out", "seed": 0, "unit": "line"},
    "cascade": {"presetId": "cascade", "durationFrames": 10, "staggerFrames": 2, "intensity": 1.0, "order": "forward", "easing": "overshoot", "seed": 0, "unit": "character"},
    "pop": {"presetId": "pop", "durationFrames": 10, "staggerFrames": 3, "intensity": 1.0, "order": "forward", "easing": "overshoot", "seed": 0, "unit": "word"},
    "blur-in": {"presetId": "blur-in", "durationFrames": 14, "staggerFrames": 3, "intensity": 1.0, "order": "forward", "easing": "ease-out", "seed": 0, "unit": "word"},
    "slide-mask": {"presetId": "slide-mask", "durationFrames": 14, "staggerFrames": 4, "intensity": 1.0, "order": "forward", "easing": "ease-out", "seed": 0, "unit": "line"},
    "wave-in": {"presetId": "wave-in", "durationFrames": 12, "staggerFrames": 2, "intensity": 1.0, "order": "forward", "easing": "ease-out", "seed": 0, "unit": "character"},
}

FREECUT_TEXT_OUT_PRESETS: Dict[str, Dict[str, Any]] = {
    "fade-down": {"presetId": "fade-down", "durationFrames": 10, "staggerFrames": 2, "intensity": 1.0, "order": "forward", "easing": "ease-in", "seed": 0, "unit": "word"},
    "sink": {"presetId": "sink", "durationFrames": 12, "staggerFrames": 3, "intensity": 1.0, "order": "forward", "easing": "ease-in", "seed": 0, "unit": "line"},
    "pop-out": {"presetId": "pop-out", "durationFrames": 9, "staggerFrames": 2, "intensity": 1.0, "order": "backward", "easing": "ease-in", "seed": 0, "unit": "word"},
    "blur-out": {"presetId": "blur-out", "durationFrames": 11, "staggerFrames": 2, "intensity": 1.0, "order": "forward", "easing": "ease-in", "seed": 0, "unit": "word"},
    "typewriter-erase": {"presetId": "typewriter-erase", "durationFrames": 1, "staggerFrames": 1, "intensity": 1.0, "order": "backward", "easing": "linear", "seed": 0, "unit": "character"},
}

FREECUT_TEXT_LOOP_PRESETS: Dict[str, Dict[str, Any]] = {
    "pulse": {"presetId": "pulse", "durationFrames": 42, "staggerFrames": 4, "intensity": 0.42, "order": "center", "easing": "ease-in-out", "seed": 0, "unit": "whole-clip"},
    "wave": {"presetId": "wave", "durationFrames": 48, "staggerFrames": 3, "intensity": 0.35, "order": "forward", "easing": "ease-in-out", "seed": 0, "unit": "word"},
    "shimmer": {"presetId": "shimmer", "durationFrames": 45, "staggerFrames": 3, "intensity": 0.50, "order": "forward", "easing": "ease-in-out", "seed": 0, "unit": "character"},
    "swing": {"presetId": "swing", "durationFrames": 54, "staggerFrames": 4, "intensity": 0.30, "order": "center", "easing": "ease-in-out", "seed": 0, "unit": "whole-clip"},
}

LEGACY_ENTRY_ALIAS = {
    "slide_up": "fade-up",
    "slide_down": "rise",
    "slide_left": "slide-mask",
    "slide_right": "slide-mask",
    "fade": "blur-in",
    "blur": "blur-in",
}
LEGACY_EXIT_ALIAS = {
    "fade": "fade-down",
    "slide_down": "fade-down",
    "slide_up": "sink",
    "pop": "pop-out",
    "blur": "blur-out",
}

PT_STOPWORDS = {"da", "de", "do", "das", "dos", "e", "em", "na", "no", "nas", "nos", "ao", "aos", "para", "por", "com", "um", "uma"}
ACRONYM_KEEP = {"PLC", "D2C", "B2B", "EUA", "ONU", "PIB", "IA", "TV", "CEO", "CFO", "IPO", "TI", "SP", "RJ", "BR", "UK", "US", "EU"}


def get_uid() -> str:
    return str(uuid.uuid4())


def det_uid(seed: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, seed))


def ms_to_frames(ms: float) -> int:
    return max(1, int(round((float(ms) / 1000.0) * FPS)))


def last_kf(dur_f: int) -> int:
    """Valid inclusive last frame index inside a FreeCut clip (`[0, durationInFrames - 1]`)."""
    return max(0, int(dur_f) - 1)


def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def detect_mime(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    return {
        ".mp4": "video/mp4",
        ".mov": "video/quicktime",
        ".webm": "video/webm",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".m4a": "audio/mp4",
        ".aac": "audio/aac",
        ".ogg": "audio/ogg",
        ".oga": "audio/ogg",
        ".opus": "audio/ogg",
        ".flac": "audio/flac",
        ".json": "application/json",
        ".lottie": "application/octet-stream",
    }.get(ext, "application/octet-stream")


def probe_media(filepath: str) -> Dict[str, Any]:
    mime = detect_mime(filepath)
    if mime == "application/json":
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                d = json.load(f)
            fr = float(d.get("fr", 30) or 30)
            frames = max(1.0, float(d.get("op", 90)) - float(d.get("ip", 0)))
            return {
                "width": int(d.get("w", 1920)),
                "height": int(d.get("h", 1080)),
                "duration": round(max(0.5, frames / fr), 3),
                "fps": int(round(fr)),
                "total_frames": max(1, int(round(frames))),
                "codec": "lottie",
            }
        except Exception:
            return {"width": 1920, "height": 1080, "duration": 3.0, "fps": 30, "total_frames": 90, "codec": "lottie"}

    if mime.startswith("image/"):
        try:
            with Image.open(filepath) as im:
                w, h = im.size
            return {"width": w, "height": h, "duration": 0.0, "fps": FPS, "codec": "image"}
        except Exception:
            return {"width": 1920, "height": 1080, "duration": 0.0, "fps": FPS, "codec": "image"}

    if filepath.lower().endswith(".wav"):
        try:
            with wave.open(filepath, "rb") as wf:
                dur = wf.getnframes() / float(wf.getframerate())
            return {"width": 0, "height": 0, "duration": round(dur, 4), "fps": FPS, "codec": "pcm_s16le"}
        except Exception:
            pass

    try:
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            filepath,
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        info = json.loads(res.stdout or "{}")
        fmt_dur = float(info.get("format", {}).get("duration", 0.0) or 0.0)
        w, h, codec, fps = 0, 0, "unknown", FPS
        for st in info.get("streams", []):
            if st.get("codec_type") == "video":
                w = int(st.get("width", 1920) or 1920)
                h = int(st.get("height", 1080) or 1080)
                codec = st.get("codec_name", "h264")
                r_fps = st.get("r_frame_rate", "30/1")
                if "/" in r_fps:
                    num, den = r_fps.split("/", 1)
                    if float(den) > 0:
                        fps = int(round(float(num) / float(den)))
                if fmt_dur <= 0 and st.get("duration"):
                    fmt_dur = float(st["duration"])
                break
            elif st.get("codec_type") == "audio" and codec == "unknown":
                codec = st.get("codec_name", "mp3")
                if fmt_dur <= 0 and st.get("duration"):
                    fmt_dur = float(st["duration"])
        return {
            "width": w,
            "height": h,
            "duration": round(max(0.1, fmt_dur), 4),
            "fps": fps or FPS,
            "codec": codec,
        }
    except Exception:
        return {"width": 1920 if mime.startswith("video/") else 0, "height": 1080 if mime.startswith("video/") else 0, "duration": 1.0, "fps": FPS, "codec": "unknown"}


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    h = hex_color.strip().lstrip("#")
    if len(h) != 6:
        return (16, 21, 30)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def is_light_hex(hex_color: str) -> bool:
    if not hex_color:
        return False
    if hex_color.upper() in LIGHT_BG_HEXES:
        return True
    r, g, b = hex_to_rgb(hex_color)
    lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
    return lum > 0.62


def generate_editorial_canvas(out_path: str, bg_hex: str, seed_str: str) -> str:
    """Generates a tactile editorial matte (warm archival paper or deep studio slate) with subtle grain & vignette."""
    if os.path.isfile(out_path) and os.path.getsize(out_path) > 5000:
        return out_path
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    r, g, b = hex_to_rgb(bg_hex)
    light = is_light_hex(bg_hex)

    yy, xx = np.mgrid[0:CANVAS_H, 0:CANVAS_W].astype(np.float32)
    nx = (xx - CANVAS_W * 0.5) / (CANVAS_W * 0.5)
    ny = (yy - CANVAS_H * 0.5) / (CANVAS_H * 0.5)
    dist2 = nx * nx + ny * ny

    rng = np.random.default_rng(abs(hash(seed_str)) % (2**32))
    grain = rng.normal(0.0, 3.2 if light else 2.6, size=(CANVAS_H, CANVAS_W, 1)).astype(np.float32)

    base = np.zeros((CANVAS_H, CANVAS_W, 3), dtype=np.float32)
    base[:, :, 0] = r
    base[:, :, 1] = g
    base[:, :, 2] = b

    if light:
        vig = np.clip(dist2 * 11.0, 0.0, 16.0)[:, :, None]
        arr = np.clip(base - vig + grain, 0, 255).astype(np.uint8)
    else:
        lift = np.clip((1.0 - dist2) * 11.0, -14.0, 11.0)[:, :, None]
        arr = np.clip(base + lift + grain, 0, 255).astype(np.uint8)

    img = Image.fromarray(arr)
    draw = ImageDraw.Draw(img)
    rule_col = (max(0, r - 18), max(0, g - 18), max(0, b - 16)) if light else (min(255, r + 16), min(255, g + 18), min(255, b + 24))
    draw.line([(96, 84), (CANVAS_W - 96, 84)], fill=rule_col, width=1)
    draw.line([(96, CANVAS_H - 84), (CANVAS_W - 96, CANVAS_H - 84)], fill=rule_col, width=1)

    img.save(out_path, "JPEG", quality=93, subsampling=0)
    return out_path


def generate_fallback_blur_plate(src_img_path: str, out_plate_path: str) -> str:
    """Creates a rich dark blurred backdrop plate; avoids turning white studio photos into muddy #565656 gray."""
    if os.path.isfile(out_plate_path) and os.path.getsize(out_plate_path) > 5000:
        return out_plate_path
    os.makedirs(os.path.dirname(out_plate_path), exist_ok=True)
    with Image.open(src_img_path) as im:
        rgb = im.convert("RGB")
        sample = np.asarray(rgb.resize((96, 96)), dtype=np.float32)
        if sample.mean() > 195.0:
            return generate_editorial_canvas(out_plate_path, "#0E1522", out_plate_path)
        scale = max(CANVAS_W / rgb.width, CANVAS_H / rgb.height)
        resized = rgb.resize((int(rgb.width * scale) + 4, int(rgb.height * scale) + 4), Image.Resampling.LANCZOS)
        left = (resized.width - CANVAS_W) // 2
        top = (resized.height - CANVAS_H) // 2
        cropped = resized.crop((left, top, left + CANVAS_W, top + CANVAS_H))
        blurred = cropped.filter(ImageFilter.GaussianBlur(radius=38))
        arr = (np.asarray(blurred, dtype=np.float32) * 0.34).clip(0, 255).astype(np.uint8)
        Image.fromarray(arr).save(out_plate_path, "JPEG", quality=88)
    return out_plate_path


def inspect_cutout_alpha(filepath: str) -> Tuple[bool, float, Tuple[int, int, int]]:
    """
    Analyzes an RGBA cutout PNG to detect:
      1. `is_bottom_cropped`: True if opaque subject is sliced at the bottom edge (e.g. waist-cropped portrait),
         so the assembler grounds it flush to the bottom canvas edge instead of floating a chopped torso!
      2. `bbox_aspect`: Tight opaque width / height ratio.
      3. `accent_rgb`: Vibrant brand/wardrobe hue sampled from opaque pixels.
    """
    try:
        with Image.open(filepath) as im:
            rgba = im.convert("RGBA")
            arr = np.asarray(rgba)
        if arr.shape[2] < 4:
            return False, arr.shape[1] / max(1.0, float(arr.shape[0])), (200, 75, 49)
        alpha = arr[:, :, 3]
        ys, xs = np.where(alpha > 24)
        if len(xs) < 40:
            return False, arr.shape[1] / max(1.0, float(arr.shape[0])), (200, 75, 49)
        x0, x1 = int(xs.min()), int(xs.max())
        y0, y1 = int(ys.min()), int(ys.max())
        bw = max(1, x1 - x0 + 1)
        bh = max(1, y1 - y0 + 1)
        bot_rows = alpha[-max(3, arr.shape[0] // 80) :, x0 : x1 + 1]
        bot_span = float((bot_rows > 120).any(axis=0).mean()) if bot_rows.size > 0 else 0.0
        touches_bottom = (y1 >= arr.shape[0] - 4) and (bot_span > 0.28)

        # Sample vibrant opaque pixels for bespoke studio spotlight tinting
        rgb_pts = arr[alpha > 180][:, :3].astype(np.float32)
        if len(rgb_pts) > 50:
            mx = rgb_pts.max(axis=1)
            mn = rgb_pts.min(axis=1)
            sat = (mx - mn) / np.maximum(1.0, mx)
            vivid = rgb_pts[(sat > 0.25) & (mx > 60) & (mx < 248)]
            chosen = vivid.mean(axis=0) if len(vivid) > 30 else rgb_pts.mean(axis=0)
            accent_rgb = (int(chosen[0]), int(chosen[1]), int(chosen[2]))
        else:
            accent_rgb = (200, 75, 49)
        return bool(touches_bottom), bw / float(bh), accent_rgb
    except Exception:
        return False, 0.75, (200, 75, 49)


def generate_cutout_stage_backdrop(
    out_path: str,
    archetype: str,
    accent_rgb: Tuple[int, int, int],
    seed_str: str,
    subject_x_norm: float = 0.0,
) -> str:
    """
    Renders bespoke art-directed 1920x1080/1080x1920 studio & paper backdrops for `parallax_cutout_stage`
    (replaces ugly muddy gray blurred white-BG plates forever):
      - `poster_monumental_center`: Deep botanical emerald-obsidian spotlight stage + subtle horizon pedestal.
      - `archival_dossier_paper`  : Warm tactile cream archival newsprint + offset ochre/terracotta sun-disc stamp.
      - `magazine_grounded_portrait`: Rich rose-obsidian magazine studio + diagonal key/rim light behind subject.
    """
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    yy, xx = np.mgrid[0:CANVAS_H, 0:CANVAS_W].astype(np.float32)
    nx = (xx - CANVAS_W * (0.5 + subject_x_norm * 0.42)) / (CANVAS_W * 0.5)
    ny = (yy - CANVAS_H * 0.48) / (CANVAS_H * 0.5)
    dist2 = nx * nx + ny * ny
    rng = np.random.default_rng(abs(hash(seed_str)) % (2**32))

    if archetype == "archival_dossier_paper":
        base = np.zeros((CANVAS_H, CANVAS_W, 3), dtype=np.float32)
        base[:, :, 0], base[:, :, 1], base[:, :, 2] = 243.0, 239.0, 230.0
        vig = np.clip(((xx - CANVAS_W * 0.5) / (CANVAS_W * 0.5)) ** 2 + ny * ny, 0.0, 2.2)[:, :, None] * 9.5
        grain = rng.normal(0.0, 3.1, size=(CANVAS_H, CANVAS_W, 1)).astype(np.float32)
        arr = np.clip(base - vig + grain, 0, 255).astype(np.uint8)
        img = Image.fromarray(arr)
        draw = ImageDraw.Draw(img)

        # Warm botanical disc & editorial registration lines behind the cutout column
        disc_cx = int(CANVAS_W * (0.5 + subject_x_norm))
        disc_cy = int(CANVAS_H * 0.51)
        disc_r = int(min(CANVAS_W, CANVAS_H) * 0.30)
        draw.ellipse(
            [disc_cx - disc_r, disc_cy - disc_r, disc_cx + disc_r, disc_cy + disc_r],
            fill=(230, 216, 192),
            outline=(200, 75, 49),
            width=2,
        )
        outer_r = disc_r + 18
        draw.ellipse(
            [disc_cx - outer_r, disc_cy - outer_r, disc_cx + outer_r, disc_cy + outer_r],
            outline=(212, 198, 175),
            width=1,
        )
        margin_x = max(64, int(CANVAS_W * 0.05))
        margin_y = max(56, int(CANVAS_H * 0.075))
        draw.line([(margin_x, margin_y), (CANVAS_W - margin_x, margin_y)], fill=(208, 198, 182), width=1)
        draw.line([(margin_x, CANVAS_H - margin_y), (CANVAS_W - margin_x, CANVAS_H - margin_y)], fill=(208, 198, 182), width=1)
        draw.rectangle([margin_x, margin_y + 18, margin_x + 5, CANVAS_H - margin_y - 18], fill=(200, 75, 49))
        img.save(out_path, "JPEG", quality=94, subsampling=0)
        return out_path

    if archetype == "magazine_grounded_portrait":
        # Rich rose-noir / plum editorial studio with warm rim-light behind portrait
        spot = np.exp(-dist2 * 1.55)[:, :, None]
        ar, ag, ab = accent_rgb
        glow_col = np.array([max(78.0, ar * 0.42), max(26.0, ag * 0.20), max(56.0, ab * 0.34)], dtype=np.float32)
        dark_col = np.array([10.0, 8.0, 14.0], dtype=np.float32)
        grain = rng.normal(0.0, 2.3, size=(CANVAS_H, CANVAS_W, 1)).astype(np.float32)
        arr = np.clip(dark_col[None, None, :] + spot * glow_col[None, None, :] + grain, 0, 255).astype(np.uint8)
        img = Image.fromarray(arr)
        draw = ImageDraw.Draw(img)
        mx = max(64, int(CANVAS_W * 0.05))
        my = max(56, int(CANVAS_H * 0.075))
        draw.line([(mx, my), (CANVAS_W - mx, my)], fill=(58, 36, 52), width=1)
        draw.line([(mx, CANVAS_H - my), (CANVAS_W - mx, CANVAS_H - my)], fill=(44, 28, 40), width=1)
        # Subtle editorial vertical column divider
        div_x = int(CANVAS_W * 0.51)
        draw.line([(div_x, my + 24), (div_x, CANVAS_H - my - 24)], fill=(48, 30, 44), width=1)
        img.save(out_path, "JPEG", quality=94, subsampling=0)
        return out_path

    # Default (`poster_monumental_center`): Deep botanical emerald-obsidian spotlight + studio floor horizon
    spot = np.exp(-dist2 * 1.65)[:, :, None]
    dark_col = np.array([5.0, 11.0, 10.0], dtype=np.float32)
    glow_col = np.array([14.0, 52.0, 42.0], dtype=np.float32)
    floor_band = np.clip((yy - CANVAS_H * 0.76) / (CANVAS_H * 0.24), 0.0, 1.0)[:, :, None] * np.array([4.0, 10.0, 9.0])
    grain = rng.normal(0.0, 2.4, size=(CANVAS_H, CANVAS_W, 1)).astype(np.float32)
    arr = np.clip(dark_col[None, None, :] + spot * glow_col[None, None, :] + floor_band + grain, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr)
    draw = ImageDraw.Draw(img)
    mx = max(64, int(CANVAS_W * 0.05))
    my = max(56, int(CANVAS_H * 0.075))
    horizon_y = int(CANVAS_H * 0.80)
    draw.line([(mx, horizon_y), (CANVAS_W - mx, horizon_y)], fill=(24, 58, 50), width=1)
    draw.line([(mx, my), (CANVAS_W - mx, my)], fill=(22, 48, 42), width=1)
    img.save(out_path, "JPEG", quality=94, subsampling=0)
    return out_path


def _smart_title_case(raw: str) -> str:
    """Converts shouting ALL-CAPS strings into human editorial Title Case while preserving acronyms & mixed case."""
    s = (raw or "").strip()
    if not s:
        return s
    letters = [c for c in s if c.isalpha()]
    if letters and sum(1 for c in letters if c.islower()) >= max(2, len(letters) // 5):
        return s
    words = s.split()
    out = []
    for idx, w in enumerate(words):
        clean = w.strip(".,!?:;()[]{}\"'")
        low = clean.lower()
        up = clean.upper()
        if up in ACRONYM_KEEP or clean.startswith("R$") or any(ch.isdigit() for ch in clean):
            out.append(w.upper() if up in ACRONYM_KEEP else w)
        elif idx > 0 and low in PT_STOPWORDS:
            out.append(w.lower())
        else:
            out.append(w[:1].upper() + w[1:].lower())
    return " ".join(out)


def build_text_motion(
    in_preset: str,
    out_preset: Optional[str],
    dur_f: int,
    loop_preset: Optional[str] = None,
) -> Dict[str, Any]:
    """Builds a real `walterlow/freecut` `TextMotionSpec` (`in`, `out`, optional `loop`)."""
    in_key = LEGACY_ENTRY_ALIAS.get(in_preset, in_preset)
    if in_key not in FREECUT_TEXT_IN_PRESETS:
        in_key = "fade-up"
    in_cfg = dict(FREECUT_TEXT_IN_PRESETS[in_key])
    if in_key != "typewriter":
        in_cfg["durationFrames"] = min(int(in_cfg["durationFrames"]), max(4, dur_f // 4))

    spec: Dict[str, Any] = {"in": in_cfg}

    if out_preset and dur_f >= 24:
        out_key = LEGACY_EXIT_ALIAS.get(out_preset, out_preset)
        if out_key not in FREECUT_TEXT_OUT_PRESETS:
            out_key = "fade-down"
        out_cfg = dict(FREECUT_TEXT_OUT_PRESETS[out_key])
        if out_key != "typewriter-erase":
            out_cfg["durationFrames"] = min(int(out_cfg["durationFrames"]), max(4, dur_f // 5))
        spec["out"] = out_cfg

    if loop_preset and loop_preset in FREECUT_TEXT_LOOP_PRESETS and dur_f >= 36:
        spec["loop"] = dict(FREECUT_TEXT_LOOP_PRESETS[loop_preset])

    return spec


def build_motion_modifier(
    seed_str: str,
    mod_type: str = "float-drift",
    amplitude: float = 0.26,
    frequency: float = 0.20,
) -> Dict[str, Any]:
    """Builds a real `walterlow/freecut` `MotionModifier` (`Clipe Motion`)."""
    hval = abs(hash(seed_str))
    return {
        "id": det_uid(f"{seed_str}_mod_{mod_type}"),
        "type": mod_type,
        "enabled": True,
        "amplitude": round(float(amplitude), 2),
        "frequency": round(float(frequency), 2),
        "phaseFrames": int(hval % 24),
        "seed": int((hval % 900) + 100),
    }


def _split_editorial_clauses(headline: str) -> Tuple[str, str]:
    """Splits a single-string headline by `\n`, `•`, `—`, or `|` into `(primary_title, secondary_context)`."""
    raw = (headline or "").strip()
    if "\n" in raw:
        parts = [p.strip() for p in raw.splitlines() if p.strip()]
        if len(parts) >= 2:
            return parts[0], " • ".join(parts[1:])
    for sep in (" • ", " — ", " – ", " | ", " - "):
        if sep in raw:
            a, b = raw.split(sep, 1)
            return a.strip(), b.strip()
    return raw, ""


def build_cutout_editorial_lockup(
    scene: Dict[str, Any],
    archetype: str,
) -> Tuple[str, List[Dict[str, Any]], str, str, Optional[str]]:
    """
    Returns `(plain_text, text_spans, primary_font, in_preset, monumental_bg_token)` tailored to each of the
    3 distinct cutout archetypes so consecutive cutout scenes NEVER share font, layout, or visual hierarchy.
    """
    raw_hl = (scene.get("headline") or scene.get("caption") or "").strip()
    hero_stat = (scene.get("hero_stat") or "").strip()
    explicit_kicker = (scene.get("kicker") or scene.get("eyebrow") or "").strip()
    explicit_sub = (scene.get("subheadline") or "").strip()

    primary_raw, secondary_raw = _split_editorial_clauses(raw_hl)
    title_clean = _smart_title_case(primary_raw or hero_stat or "Destaque")

    # Extract concise monumental background token (year / number / short brand stem) for Archetype 0
    bg_token = None
    stat_source = f"{hero_stat} {raw_hl}".strip()
    m_num = re.search(r"\b\d{4}\b|\b\d+(?:[.,]\d+)?[%BMK]?\b", stat_source)
    if m_num:
        bg_token = m_num.group(0)
    elif title_clean:
        bg_token = title_clean.split()[0].upper()[:7]

    spans: List[Dict[str, Any]] = []

    if archetype == "poster_monumental_center":
        kicker_parts = [p for p in (explicit_kicker or hero_stat, secondary_raw) if p]
        kicker = " • ".join(kicker_parts).upper() if kicker_parts else "ARQUIVO DOCUMENTAL"
        spans.append(
            {
                "text": f"{kicker}\n",
                "fontFamily": "Roboto Mono",
                "fontSize": 19,
                "fontWeight": "bold",
                "fontStyle": "normal",
                "color": "#FACC15",
                "letterSpacing": 2.4,
            }
        )
        spans.append(
            {
                "text": title_clean + (f"\n" if explicit_sub else ""),
                "fontFamily": "Space Grotesk",
                "fontSize": 58,
                "fontWeight": "bold",
                "fontStyle": "normal",
                "color": "#F8FAFC",
                "letterSpacing": -1.2,
            }
        )
        if explicit_sub:
            spans.append(
                {
                    "text": explicit_sub,
                    "fontFamily": "DM Sans",
                    "fontSize": 26,
                    "fontWeight": "medium",
                    "fontStyle": "normal",
                    "color": "#CBD5E1",
                    "letterSpacing": -0.2,
                }
            )
        plain = "".join(s["text"] for s in spans)
        return plain, spans, "Space Grotesk", "typewriter", bg_token

    if archetype == "archival_dossier_paper":
        kicker = (explicit_kicker or secondary_raw or hero_stat or "REGISTRO LOCAL").upper()
        spans.append(
            {
                "text": f"{kicker}\n",
                "fontFamily": "Roboto Mono",
                "fontSize": 20,
                "fontWeight": "bold",
                "fontStyle": "normal",
                "color": "#C84B31",
                "letterSpacing": 2.0,
            }
        )
        spans.append(
            {
                "text": title_clean + (f"\n" if explicit_sub else ""),
                "fontFamily": "Playfair Display",
                "fontSize": 80,
                "fontWeight": "bold",
                "fontStyle": "italic",
                "color": "#14181F",
                "letterSpacing": -1.4,
            }
        )
        if explicit_sub:
            spans.append(
                {
                    "text": explicit_sub,
                    "fontFamily": "DM Sans",
                    "fontSize": 28,
                    "fontWeight": "medium",
                    "fontStyle": "normal",
                    "color": "#475569",
                    "letterSpacing": -0.2,
                }
            )
        plain = "".join(s["text"] for s in spans)
        return plain, spans, "Playfair Display", "cascade", None

    # `magazine_grounded_portrait`
    kicker = (explicit_kicker or hero_stat or "PERFIL EDITORIAL").upper()
    sub_line = explicit_sub or secondary_raw
    spans.append(
        {
            "text": f"{kicker}\n",
            "fontFamily": "Roboto Mono",
            "fontSize": 19,
            "fontWeight": "bold",
            "fontStyle": "normal",
            "color": "#F472B6",
            "letterSpacing": 2.4,
        }
    )
    spans.append(
        {
            "text": title_clean + ("\n" if sub_line else ""),
            "fontFamily": "Bricolage Grotesque",
            "fontSize": 68,
            "fontWeight": "bold",
            "fontStyle": "normal",
            "color": "#FFFFFF",
            "letterSpacing": -1.5,
        }
    )
    if sub_line:
        spans.append(
            {
                "text": _smart_title_case(sub_line),
                "fontFamily": "Playfair Display",
                "fontSize": 38,
                "fontWeight": "normal",
                "fontStyle": "italic",
                "color": "#E2E8F0",
                "letterSpacing": -0.4,
            }
        )
    plain = "".join(s["text"] for s in spans)
    return plain, spans, "Bricolage Grotesque", "slide-mask", None


def build_callout_spans(raw_text: str, scene_idx: int) -> Tuple[str, List[Dict[str, Any]], str, str]:
    """Formats full-bleed / B-roll lower-thirds & callouts with varied editorial fonts + eyebrow/stat highlights."""
    txt = (raw_text or "").strip()
    primary_raw, secondary_raw = _split_editorial_clauses(txt)
    callout_presets = ["slide-mask", "fade-up", "rise", "blur-in"]
    chosen_in = callout_presets[scene_idx % len(callout_presets)]

    # Case 1: Explicit location/context separator (`KIGALI, RUANDA — ÁFRICA ORIENTAL`)
    if secondary_raw:
        accents = ["#FACC15", "#34D399", "#F59E0B", "#38BDF8"]
        acc = accents[scene_idx % len(accents)]
        head_fonts = ["Space Grotesk", "Bricolage Grotesque", "Playfair Display"]
        hf = head_fonts[scene_idx % len(head_fonts)]
        spans = [
            {
                "text": f"{secondary_raw.upper()}\n",
                "fontFamily": "Roboto Mono",
                "fontSize": 18,
                "fontWeight": "bold",
                "fontStyle": "normal",
                "color": acc,
                "letterSpacing": 2.0,
            },
            {
                "text": _smart_title_case(primary_raw),
                "fontFamily": hf,
                "fontSize": 42,
                "fontWeight": "bold",
                "fontStyle": "italic" if hf == "Playfair Display" else "normal",
                "color": "#FFFFFF",
                "letterSpacing": -0.8,
            },
        ]
        return "".join(s["text"] for s in spans), spans, hf, chosen_in

    # Case 2: Headline starts with or contains a monetary/numeric stat (`R$ 1,3 BILHÃO EM FATURAMENTO...`)
    m_stat = re.match(r"^((?:R\$|US\$|\$)?\s*\d[\d.,]*(?:\s*(?:BILH[ÕO]ES|BILH[ÃA]O|MILH[ÕO]ES|MIL|%|KM))?)\s+(.+)$", txt, flags=re.IGNORECASE)
    if m_stat:
        stat_tok = m_stat.group(1).strip().upper()
        rest_tok = _smart_title_case(m_stat.group(2).strip())
        spans = [
            {
                "text": f"{stat_tok}\n",
                "fontFamily": "Oswald",
                "fontSize": 52,
                "fontWeight": "bold",
                "fontStyle": "normal",
                "color": "#FACC15",
                "letterSpacing": 0.4,
            },
            {
                "text": rest_tok,
                "fontFamily": "Inter Tight",
                "fontSize": 32,
                "fontWeight": "semibold",
                "fontStyle": "normal",
                "color": "#F8FAFC",
                "letterSpacing": -0.4,
            },
        ]
        return "".join(s["text"] for s in spans), spans, "Oswald", "pop"

    # Case 3: Closing thesis / editorial sentence -> Playfair Display italic or Inter Tight
    is_thesis = txt.endswith(".") and len(txt.split()) >= 6
    fam = "Playfair Display" if is_thesis else "Inter Tight"
    clean = _smart_title_case(txt) if not is_thesis else (txt[:1].upper() + txt[1:].lower())
    spans = [
        {
            "text": clean,
            "fontFamily": fam,
            "fontSize": 42 if is_thesis else 38,
            "fontWeight": "bold",
            "fontStyle": "italic" if is_thesis else "normal",
            "color": "#FFFFFF",
            "letterSpacing": -0.6,
        }
    ]
    return clean, spans, fam, ("blur-in" if is_thesis else chosen_in)


def build_statement_spans(raw_text: str, on_light_bg: bool) -> Tuple[str, List[Dict[str, Any]], str]:
    """Splits punchy kinetic statements into a contrast setup + climax serif/display punch word."""
    txt = (raw_text or "").strip()
    words = txt.split()
    main_col = "#14181F" if on_light_bg else "#F8FAFC"
    muted_col = "#475569" if on_light_bg else "#94A3B8"
    accent_col = "#C84B31" if on_light_bg else "#FACC15"
    if len(words) >= 3:
        setup = " ".join(words[:-1]).upper()
        punch = words[-1].upper()
        spans = [
            {
                "text": f"{setup}\n",
                "fontFamily": "Space Grotesk",
                "fontSize": 42,
                "fontWeight": "semibold",
                "fontStyle": "normal",
                "color": muted_col,
                "letterSpacing": 2.2,
            },
            {
                "text": punch,
                "fontFamily": "Playfair Display",
                "fontSize": 88,
                "fontWeight": "bold",
                "fontStyle": "italic",
                "color": accent_col if len(punch) <= 12 else main_col,
                "letterSpacing": -1.5,
            },
        ]
        return "".join(s["text"] for s in spans), spans, "Playfair Display"
    spans = [
        {
            "text": txt,
            "fontFamily": "Oswald",
            "fontSize": 72,
            "fontWeight": "bold",
            "fontStyle": "normal",
            "color": main_col,
            "letterSpacing": -0.8,
        }
    ]
    return txt, spans, "Oswald"


def pick_bundled_sfx(seed_str: str, gentle: bool = True, layout: str = "") -> Optional[Tuple[str, float]]:
    """Returns (sfx_filepath, calibrated_negative_db) matched to the physical editorial action."""
    if not os.path.isdir(BUNDLED_SFX_DIR):
        return None
    candidates = sorted(
        glob.glob(os.path.join(BUNDLED_SFX_DIR, "*.mp3")) + glob.glob(os.path.join(BUNDLED_SFX_DIR, "*.wav"))
    )
    if not candidates:
        return None
    by_name = lambda kw: [p for p in candidates if kw in os.path.basename(p).lower()]
    if layout in ("press_evidence_highlight", "editorial_backdrop_frame", "split_editorial_slide"):
        pool = by_name("paper") + by_name("shutter")
    elif layout == "motion_scene":
        pool = by_name("riser") + by_name("air-woosh")
    elif layout == "kinetic_statement":
        pool = by_name("click") + by_name("whoosh")
    else:
        pool = by_name("air-woosh") + by_name("click")
    if not pool:
        pool = by_name("air-woosh") or candidates
    rng = random.Random(seed_str)
    chosen = rng.choice(pool)
    bname = os.path.basename(chosen).lower()
    base_db = -26.0 if ("click" in bname or "shutter" in bname) else (-25.0 if "air-woosh" in bname else -24.2)
    final_db = round(base_db + rng.uniform(-1.3, 1.1), 1)
    return chosen, max(-32.0, min(-20.0, final_db))


def find_narration_file(project_dir: str, storyboard: Dict[str, Any]) -> str:
    for key in ("audio_file", "aroll_file"):
        explicit = storyboard.get(key)
        if explicit:
            p = explicit if os.path.isabs(explicit) else os.path.join(project_dir, explicit)
            if os.path.isfile(p):
                return p
    for name in (
        "extracted_audio.wav",
        "narration.mp3",
        "narration.wav",
        "narration.m4a",
        "voiceover.mp3",
        "voiceover.wav",
        "audio.mp3",
        "audio.wav",
        "audio.m4a",
    ):
        p = os.path.join(project_dir, name)
        if os.path.isfile(p):
            return p
    candidates = []
    for ext in ("*.mp3", "*.wav", "*.m4a", "*.ogg", "*.opus", "*.oga", "*.aac", "*.flac", "*.mp4", "*.mov"):
        candidates.extend(glob.glob(os.path.join(project_dir, ext)))
    if not candidates:
        raise FileNotFoundError(f"No narration audio/video (.mp3/.wav/.m4a/.ogg/.opus/.mp4) found in {project_dir}")
    return candidates[0]


def find_word_offset_frames(words: List[Dict[str, Any]], start_ms: float, end_ms: float, anchor_word: str) -> int:
    """Finds exact frame offset inside [start_ms, end_ms] when `anchor_word` is spoken."""
    if not words or not anchor_word:
        return 4
    needle = anchor_word.strip().lower()
    for w in words:
        ws = float(w.get("start_ms", 0))
        if start_ms - 150 <= ws <= end_ms + 150:
            tok = str(w.get("word", "")).strip(".,!?:;\"'()[]{}").lower()
            if needle in tok or tok in needle:
                return max(0, int(round(((ws - start_ms) / 1000.0) * FPS)))
    return 4


def resolve_scene_media(project_dir: str, scene: Dict[str, Any], layout: str) -> Tuple[Optional[str], str]:
    """Returns (filepath, media_kind: 'video'|'image'|'none')."""
    sid = scene["id"]
    if layout in ("kinetic_statement", "custom_layers"):
        return None, "none"
    if layout == "motion_scene":
        mp4 = scene.get("motion_file") or os.path.join("motion", f"{sid}.mp4")
        full = mp4 if os.path.isabs(mp4) else os.path.join(project_dir, mp4)
        if os.path.isfile(full):
            return full, "video"

    explicit = scene.get("media_file") or (scene.get("media", {}) if isinstance(scene.get("media"), dict) else {}).get("file")
    if explicit:
        full = explicit if os.path.isabs(explicit) else os.path.join(project_dir, explicit)
        if os.path.isfile(full):
            return full, ("video" if detect_mime(full).startswith("video/") else "image")

    vid_path = os.path.join(project_dir, "media", "videos", f"{sid}.mp4")
    cut_path = os.path.join(project_dir, "media", "cutouts", f"{sid}_cutout.png")
    prt_path = os.path.join(project_dir, "media", "prints", f"{sid}_print.png")
    img_orig = os.path.join(project_dir, "media", "images", f"{sid}.jpg")
    img_16x9 = os.path.join(project_dir, "media", "images", f"{sid}_16x9.jpg")

    if layout == "parallax_cutout_stage":
        if os.path.isfile(cut_path):
            return cut_path, "image"
        if os.path.isfile(img_orig):
            return img_orig, "image"
    if layout == "press_evidence_highlight":
        if os.path.isfile(prt_path):
            return prt_path, "image"
        if os.path.isfile(img_orig):
            return img_orig, "image"
    if layout == "cinematic_broll" and os.path.isfile(vid_path):
        return vid_path, "video"
    if layout == "full_bleed_ken_burns":
        if os.path.isfile(img_16x9):
            return img_16x9, "image"
        if os.path.isfile(img_orig):
            return img_orig, "image"
        if os.path.isfile(vid_path):
            return vid_path, "video"
    if layout in ("editorial_backdrop_frame", "split_editorial_slide", "aroll_yap_overlay"):
        if layout == "aroll_yap_overlay" and os.path.isfile(cut_path):
            return cut_path, "image"
        if os.path.isfile(img_orig):
            return img_orig, "image"
        if os.path.isfile(vid_path):
            return vid_path, "video"
        if os.path.isfile(img_16x9):
            return img_16x9, "image"

    if os.path.isfile(vid_path):
        return vid_path, "video"
    if os.path.isfile(img_orig):
        return img_orig, "image"
    if os.path.isfile(img_16x9):
        return img_16x9, "image"
    if os.path.isfile(cut_path):
        return cut_path, "image"
    matches = sorted(glob.glob(os.path.join(project_dir, "media", "images", f"{sid}*.*")))
    for m in matches:
        if "_cand" not in os.path.basename(m):
            return m, "image"
    return None, "none"


def append_native_text_item(
    items: List[Dict[str, Any]],
    all_keyframes: List[Dict[str, Any]],
    item_id: str,
    from_f: int,
    dur_f: int,
    label: str,
    text: str,
    x: int,
    y: int,
    width: int,
    height: int,
    font_size: int = 48,
    font_family: str = "Inter",
    font_weight: str = "bold",
    font_style: str = "normal",
    color: str = "#FFFFFF",
    text_align: str = "left",
    entry_type: str = "fade-up",
    exit_type: Optional[str] = "fade-down",
    loop_type: Optional[str] = None,
    text_spans: Optional[List[Dict[str, Any]]] = None,
    opacity: float = 1.0,
    on_light_bg: bool = False,
    over_busy_media: bool = True,
    letter_spacing: float = -0.8,
    line_height: float = 1.16,
    track_id: str = "track_text",
) -> None:
    if on_light_bg:
        if color.upper() in ("#FFFFFF", "#FFF", "#FAF9F6", "#FFD54F", "#FFCC00"):
            color = "#14181F"
        stroke_cfg = {"width": 0, "color": "#000000"}
        shadow_cfg = {"offsetX": 0, "offsetY": 0, "blur": 0, "color": "transparent"}
    else:
        stroke_cfg = {"width": 2 if over_busy_media else 0, "color": "rgba(0,0,0,0.72)" if over_busy_media else "#000000"}
        shadow_cfg = (
            {"offsetX": 0, "offsetY": 4, "blur": 18, "color": "rgba(0,0,0,0.86)"}
            if over_busy_media
            else {"offsetX": 0, "offsetY": 2, "blur": 10, "color": "rgba(0,0,0,0.45)"}
        )

    clean_text = "".join(str(sp.get("text", "")) for sp in text_spans) if text_spans else text.strip()
    item_doc: Dict[str, Any] = {
        "id": item_id,
        "trackId": track_id,
        "from": int(from_f),
        "durationInFrames": int(dur_f),
        "label": label,
        "type": "text",
        "text": clean_text,
        "fontSize": int(font_size),
        "fontFamily": font_family,
        "fontWeight": font_weight,
        "fontStyle": font_style,
        "color": color,
        "textAlign": text_align,
        "verticalAlign": "middle",
        "lineHeight": line_height,
        "letterSpacing": letter_spacing,
        "opacity": round(float(opacity), 3),
        "transform": {
            "x": int(x),
            "y": int(y),
            "width": int(width),
            "height": int(height),
            "scaleX": 1.0,
            "scaleY": 1.0,
            "rotation": 0.0,
        },
        "stroke": stroke_cfg,
        "textShadow": shadow_cfg,
        "textMotion": build_text_motion(entry_type, exit_type, int(dur_f), loop_preset=loop_type),
        "originId": item_id,
    }
    if text_spans:
        item_doc["textSpans"] = text_spans

    items.append(item_doc)


def build_ken_burns_keyframes(
    sid: str,
    dur_f: int,
    camera_hint: Optional[str],
    prev_vector: Optional[str],
) -> Tuple[int, int, int, int, int, int, int, int, str, str]:
    """
    Returns (start_x, start_y, start_w, start_h, end_x, end_y, end_w, end_h, easing, chosen_vector).
    Guarantees 5%+ overscan so black canvas borders NEVER leak, and avoids repeating `prev_vector`.
    """
    rng = random.Random(f"{sid}_kb_v5")
    vectors = [
        "push_in_center",
        "pull_out_center",
        "push_in_top_left",
        "push_in_top_right",
        "pan_left_right",
        "pan_right_left",
        "tilt_bottom_top",
        "pull_out_top",
    ]
    if camera_hint and camera_hint in vectors:
        vec = camera_hint
    else:
        pool = [v for v in vectors if v != prev_vector] or vectors
        vec = rng.choice(pool)

    safety = 0.055
    delta = rng.uniform(0.065, 0.115)
    jx = rng.randint(-3, 3)
    jy = rng.randint(-3, 3)
    easing = rng.choice(["ease-out", "ease-in-out", "linear"])

    if vec.startswith("push_in"):
        s_scale = 1.0 + safety
        e_scale = 1.0 + safety + delta
        sw, sh = int(CANVAS_W * s_scale), int(CANVAS_H * s_scale)
        ew, eh = int(CANVAS_W * e_scale), int(CANVAS_H * e_scale)
        max_x = max(0, (ew - CANVAS_W) // 2 - 6)
        max_y = max(0, (eh - CANVAS_H) // 2 - 6)
        sx, sy = jx, jy
        if "top_left" in vec:
            ex, ey = int(max_x * 0.55), int(max_y * 0.45)
        elif "top_right" in vec:
            ex, ey = -int(max_x * 0.55), int(max_y * 0.45)
        else:
            ex, ey = -jx, int(max_y * 0.22)
    elif vec.startswith("pull_out"):
        s_scale = 1.0 + safety + delta
        e_scale = 1.0 + safety
        sw, sh = int(CANVAS_W * s_scale), int(CANVAS_H * s_scale)
        ew, eh = int(CANVAS_W * e_scale), int(CANVAS_H * e_scale)
        max_y = max(0, (sw - CANVAS_W) // 4)
        sx, sy = jx, (int(max_y * 0.4) if "top" in vec else jy)
        ex, ey = 0, 0
    else:
        fixed = 1.0 + safety + delta * 0.65
        sw = ew = int(CANVAS_W * fixed)
        sh = eh = int(CANVAS_H * fixed)
        max_x = max(8, (sw - CANVAS_W) // 2 - 8)
        max_y = max(8, (sh - CANVAS_H) // 2 - 8)
        if vec == "pan_left_right":
            sx, ex = max_x, -max_x
            sy, ey = jy, -jy
        elif vec == "pan_right_left":
            sx, ex = -max_x, max_x
            sy, ey = jy, -jy
        else:
            sx, ex = jx, -jx
            sy, ey = -max_y, max_y

    return sx, sy, sw, sh, ex, ey, ew, eh, easing, vec


def add_gpu_adjustment(
    items: List[Dict[str, Any]],
    sid: str,
    start_f: int,
    dur_f: int,
    grade_style: str,
) -> None:
    rng = random.Random(f"{sid}_gpu_grade")
    effects_list: List[Dict[str, Any]] = []

    if grade_style == "cinematic_retro":
        effects_list.extend(
            [
                {
                    "id": det_uid(f"{sid}_eff_crt"),
                    "effect": {
                        "type": "gpu-effect",
                        "gpuEffectType": "gpu-crt",
                        "params": {
                            "curvature": round(rng.uniform(0.08, 0.14), 2),
                            "scanlines": round(rng.uniform(0.10, 0.16), 2),
                            "vignette": round(rng.uniform(0.16, 0.24), 2),
                            "chroma": round(rng.uniform(0.08, 0.16), 2),
                        },
                    },
                    "enabled": True,
                },
                {
                    "id": det_uid(f"{sid}_eff_grain"),
                    "effect": {
                        "type": "gpu-effect",
                        "gpuEffectType": "gpu-grain",
                        "params": {"amount": round(rng.uniform(0.018, 0.032), 3), "size": 0.9, "speed": 1},
                    },
                    "enabled": True,
                },
            ]
        )
    elif grade_style == "vintage_sepia":
        effects_list.extend(
            [
                {
                    "id": det_uid(f"{sid}_eff_sepia"),
                    "effect": {"type": "gpu-effect", "gpuEffectType": "gpu-sepia", "params": {"amount": 0.24}},
                    "enabled": True,
                },
                {
                    "id": det_uid(f"{sid}_eff_contrast"),
                    "effect": {"type": "gpu-effect", "gpuEffectType": "gpu-contrast", "params": {"amount": 1.08}},
                    "enabled": True,
                },
            ]
        )
    elif grade_style == "noir_bw":
        effects_list.extend(
            [
                {
                    "id": det_uid(f"{sid}_eff_bw"),
                    "effect": {"type": "gpu-effect", "gpuEffectType": "gpu-grayscale", "params": {"amount": 0.85}},
                    "enabled": True,
                },
                {
                    "id": det_uid(f"{sid}_eff_contrast"),
                    "effect": {"type": "gpu-effect", "gpuEffectType": "gpu-contrast", "params": {"amount": 1.16}},
                    "enabled": True,
                },
            ]
        )
    else:  # documentary_clean / modern_grain
        effects_list.extend(
            [
                {
                    "id": det_uid(f"{sid}_eff_vig"),
                    "effect": {
                        "type": "gpu-effect",
                        "gpuEffectType": "gpu-vignette",
                        "params": {"amount": round(rng.uniform(0.28, 0.42), 2), "size": 0.52, "softness": 0.55, "roundness": 1},
                    },
                    "enabled": True,
                },
                {
                    "id": det_uid(f"{sid}_eff_grain"),
                    "effect": {
                        "type": "gpu-effect",
                        "gpuEffectType": "gpu-grain",
                        "params": {"amount": round(rng.uniform(0.014, 0.026), 3), "size": 0.85, "speed": 1},
                    },
                    "enabled": True,
                },
            ]
        )

    adj_id = det_uid(f"{sid}_adjustment")
    items.append(
        {
            "id": adj_id,
            "type": "adjustment",
            "trackId": "track_fg_1",
            "from": start_f,
            "durationInFrames": dur_f,
            "label": f"{sid}_{grade_style.upper()}",
            "effects": effects_list,
            "effectOpacity": 1,
            "originId": adj_id,
        }
    )


def assemble_project(project_dir: str, force_captions: bool = False) -> Tuple[str, str]:
    global CANVAS_W, CANVAS_H, FPS
    project_dir = os.path.abspath(project_dir)
    sb_path = os.path.join(project_dir, "storyboard.json")
    if not os.path.isfile(sb_path):
        raise FileNotFoundError(f"storyboard.json not found in {project_dir}")

    with open(sb_path, "r", encoding="utf-8") as f:
        storyboard = json.load(f)

    aspect_ratio = str(storyboard.get("aspect_ratio") or "16:9").strip()
    base_w_dim, base_h_dim = ASPECT_DIMENSIONS.get(aspect_ratio, (1920, 1080))
    CANVAS_W = int(storyboard.get("width") or base_w_dim)
    CANVAS_H = int(storyboard.get("height") or base_h_dim)
    FPS = int(storyboard.get("fps") or 30)
    is_vertical = CANVAS_H > CANVAS_W

    words_path = os.path.join(project_dir, "words.json")
    words_list: List[Dict[str, Any]] = json.load(open(words_path, "r", encoding="utf-8")) if os.path.isfile(words_path) else []

    aroll_cuts_path = os.path.join(project_dir, "aroll_cuts.json")
    aroll_cuts: Dict[str, Any] = json.load(open(aroll_cuts_path, "r", encoding="utf-8")) if os.path.isfile(aroll_cuts_path) else {}

    scenes: List[Dict[str, Any]] = storyboard.get("scenes", [])
    if not scenes:
        raise ValueError("storyboard.json contains 0 scenes")

    title = storyboard.get("title", "Documentary_Project")
    safe_title = "".join(c if (c.isalnum() or c in "_- ") else "" for c in title).strip().replace(" ", "_")[:48] or "FreeCut_Doc"
    project_id = det_uid(f"freecut_v6_{safe_title}_{CANVAS_W}x{CANVAS_H}")

    style_dna = storyboard.get("style_dna", {})
    font_display = style_dna.get("font_display", "Montserrat")
    font_body = style_dna.get("font_body", "Inter")
    accent_hex = style_dna.get("accent", "#C84B31")
    paper_hex = style_dna.get("paper_bg", "#F4F1EA")
    studio_hex = style_dna.get("studio_bg", "#10151E")

    narration_path = find_narration_file(project_dir, storyboard)
    narration_meta = probe_media(narration_path)
    audio_dur_ms = int(round(narration_meta["duration"] * 1000.0))
    sb_end_ms = max(int(s.get("end_ms", 0)) for s in scenes)
    total_dur_ms = max(audio_dur_ms, sb_end_ms)

    items: List[Dict[str, Any]] = []
    all_keyframes: List[Dict[str, Any]] = []
    manifest_media: List[Dict[str, Any]] = []
    media_files_to_zip: List[Tuple[str, str]] = []
    seen_media_ids = set()
    media_id_to_filepath: Dict[str, str] = {}
    used_zip_names = set()

    def register_media(filepath: str) -> Tuple[str, Dict[str, Any]]:
        abs_p = os.path.abspath(filepath)
        sha256 = compute_sha256(abs_p)
        media_id = str(uuid.uuid5(uuid.NAMESPACE_OID, sha256))
        meta = probe_media(abs_p)
        media_id_to_filepath[media_id] = abs_p
        if media_id in seen_media_ids:
            return media_id, meta
        seen_media_ids.add(media_id)

        base_name = os.path.basename(abs_p)
        if base_name in used_zip_names:
            stem, ext = os.path.splitext(base_name)
            base_name = f"{stem}_{media_id[:6]}{ext}"
        used_zip_names.add(base_name)
        rel_path = f"media/{base_name}"

        manifest_media.append(
            {
                "originalId": media_id,
                "relativePath": rel_path,
                "fileName": base_name,
                "fileSize": os.path.getsize(abs_p),
                "sha256": sha256,
                "mimeType": detect_mime(abs_p),
                "metadata": {
                    "duration": meta["duration"],
                    "width": meta["width"],
                    "height": meta["height"],
                    "fps": meta["fps"],
                    "codec": meta["codec"],
                    "bitrate": 0,
                },
            }
        )
        media_files_to_zip.append((abs_p, rel_path))
        return media_id, meta

    # 1. Master Narration Audio (`track_audio`)
    vo_media_id, vo_meta = register_media(narration_path)
    vo_item_id = det_uid(f"{project_id}_vo")
    vo_dur_s = round(vo_meta["duration"], 4)
    items.append(
        {
            "id": vo_item_id,
            "trackId": "track_audio",
            "from": 0,
            "durationInFrames": ms_to_frames(vo_dur_s * 1000.0),
            "label": os.path.basename(narration_path),
            "type": "audio",
            "mediaRef": vo_media_id,
            "sourceStart": 0.0,
            "sourceEnd": vo_dur_s,
            "sourceDuration": vo_dur_s,
            "volume": 1.0,
            "originId": vo_item_id,
        }
    )

    # Optional Ducked Music Bed (`track_bgm`)
    bgm_rel = storyboard.get("bgm_file")
    if bgm_rel:
        bgm_full = bgm_rel if os.path.isabs(bgm_rel) else os.path.join(project_dir, bgm_rel)
        if os.path.isfile(bgm_full):
            bgm_mid, bgm_meta = register_media(bgm_full)
            bgm_id = det_uid(f"{project_id}_bgm")
            bgm_dur_s = round(min(bgm_meta["duration"], total_dur_ms / 1000.0), 4)
            items.append(
                {
                    "id": bgm_id,
                    "trackId": "track_bgm",
                    "from": 0,
                    "durationInFrames": ms_to_frames(bgm_dur_s * 1000.0),
                    "label": os.path.basename(bgm_full),
                    "type": "audio",
                    "mediaRef": bgm_mid,
                    "sourceStart": 0.0,
                    "sourceEnd": bgm_dur_s,
                    "sourceDuration": round(bgm_meta["duration"], 4),
                    "volume": float(storyboard.get("bgm_db", -20.5)),
                    "originId": bgm_id,
                }
            )

    prev_kb_vector: Optional[str] = None
    anchor_scene_records: List[Dict[str, Any]] = []
    split_side_toggle = 0
    boxed_card_count = 0
    cutout_free_counter = 0
    max_boxed_cards = max(1, len(scenes) // 10)

    # 2. Build Scene Items
    for idx, scene in enumerate(scenes):
        sid = scene["id"]
        start_ms = float(scene["start_ms"])
        end_ms = float(scene["end_ms"])
        dur_ms = max(400.0, end_ms - start_ms)
        start_f = int(round((start_ms / 1000.0) * FPS))
        dur_f = ms_to_frames(dur_ms)
        end_kf = last_kf(dur_f)

        raw_layout = (scene.get("layout") or scene.get("scene_type") or scene.get("layout_style") or "full_bleed_ken_burns").lower().strip()
        layout_map = {
            "broll": "cinematic_broll",
            "video": "cinematic_broll",
            "full_screen": "full_bleed_ken_burns",
            "ken_burns": "full_bleed_ken_burns",
            "cutout": "parallax_cutout_stage",
            "cutout_stage": "parallax_cutout_stage",
            "subject_cutout": "parallax_cutout_stage",
            "evidence": "press_evidence_highlight",
            "web_print": "press_evidence_highlight",
            "aroll": "aroll_yap_overlay",
            "yap": "aroll_yap_overlay",
            "custom": "custom_layers",
            "backdrop_frame": "editorial_backdrop_frame",
            "portrait_frame": "editorial_backdrop_frame",
            "split": "split_editorial_slide",
            "split_info_slide": "split_editorial_slide",
            "statement": "kinetic_statement",
            "text_only": "kinetic_statement",
            "motion": "motion_scene",
        }
        layout = layout_map.get(raw_layout, raw_layout)

        # Anti-Vício Upgrade: never allow repetitive boxed/split slides; upgrade to cutout parallax or full-bleed!
        cut_candidate = os.path.join(project_dir, "media", "cutouts", f"{sid}_cutout.png")
        if layout in ("editorial_backdrop_frame", "split_editorial_slide"):
            if os.path.isfile(cut_candidate):
                layout = "parallax_cutout_stage"
            elif boxed_card_count >= max_boxed_cards:
                layout = "full_bleed_ken_burns"
            else:
                boxed_card_count += 1

        media_path, media_kind = resolve_scene_media(project_dir, scene, layout)
        if layout not in ("kinetic_statement", "custom_layers") and not media_path:
            print(f"  [WARN] {sid}: media missing for layout={layout}, falling back to kinetic_statement")
            layout = "kinetic_statement"

        scene_bg_hex = scene.get("bg_color", "")
        on_light_canvas = False
        has_custom_entrance = False
        anchor_item_id = det_uid(f"{sid}_anchor")

        # ── LAYOUT A: KINETIC STATEMENT ─────────────────────────────
        if layout == "kinetic_statement":
            bg_hex = scene_bg_hex or (paper_hex if idx % 2 == 1 else studio_hex)
            on_light_canvas = is_light_hex(bg_hex)
            canvas_path = os.path.join(project_dir, "media", "backdrops", f"{sid}_canvas.jpg")
            generate_editorial_canvas(canvas_path, bg_hex, f"{sid}_statement")
            bg_mid, bg_meta = register_media(canvas_path)
            items.append(
                {
                    "id": anchor_item_id,
                    "trackId": "track_anchor",
                    "from": start_f,
                    "durationInFrames": dur_f,
                    "label": f"{sid}_statement_matte",
                    "type": "image",
                    "mediaRef": bg_mid,
                    "sourceWidth": bg_meta["width"],
                    "sourceHeight": bg_meta["height"],
                    "volume": 1.0,
                    "transform": {
                        "x": 0,
                        "y": 0,
                        "width": int(CANVAS_W * 1.02),
                        "height": int(CANVAS_H * 1.02),
                        "scaleX": 1.0,
                        "scaleY": 1.0,
                    },
                    "motionModifiers": [build_motion_modifier(f"{sid}_matte", "breath-pulse", 0.14, 0.15)],
                    "originId": anchor_item_id,
                }
            )
            stmt_raw = scene.get("headline") or scene.get("caption") or scene.get("narration", "")
            stmt_plain, stmt_spans, stmt_font = build_statement_spans(stmt_raw, on_light_canvas)
            append_native_text_item(
                items=items,
                all_keyframes=all_keyframes,
                item_id=det_uid(f"{sid}_stmt_txt"),
                from_f=start_f,
                dur_f=dur_f,
                label=f"{sid}_statement_text",
                text=stmt_plain,
                x=0,
                y=-12,
                width=int(CANVAS_W * (0.86 if is_vertical else 0.74)),
                height=360,
                font_size=int(scene.get("font_size", 74)),
                font_family=stmt_font,
                font_weight="bold",
                color="#14181F" if on_light_canvas else "#F8FAFC",
                text_align="center",
                entry_type=scene.get("text_entry", "pop"),
                exit_type="blur-out",
                loop_type="pulse",
                text_spans=stmt_spans,
                on_light_bg=on_light_canvas,
                over_busy_media=False,
                letter_spacing=-1.0,
                line_height=1.18,
            )
            has_custom_entrance = True

        # ── LAYOUT B: CINEMATIC B-ROLL OR MOTION SCENE ──────────────
        elif layout in ("cinematic_broll", "motion_scene") or (layout == "full_bleed_ken_burns" and media_kind == "video"):
            vid_mid, vid_meta = register_media(media_path)
            src_dur_f = max(1, int(round(vid_meta["duration"] * FPS)))
            src_end_f = min(dur_f, src_dur_f)
            # Subtle 1.01 -> 1.04 optical push on B-roll (keep motion_scene 1:1 crisp!)
            s_w = CANVAS_W if layout == "motion_scene" else int(CANVAS_W * 1.01)
            s_h = CANVAS_H if layout == "motion_scene" else int(CANVAS_H * 1.01)
            e_w = CANVAS_W if layout == "motion_scene" else int(CANVAS_W * 1.045)
            e_h = CANVAS_H if layout == "motion_scene" else int(CANVAS_H * 1.045)

            items.append(
                {
                    "id": anchor_item_id,
                    "trackId": "track_anchor",
                    "from": start_f,
                    "durationInFrames": dur_f,
                    "label": f"{sid}_{layout}",
                    "type": "video",
                    "mediaRef": vid_mid,
                    "sourceWidth": vid_meta["width"],
                    "sourceHeight": vid_meta["height"],
                    "sourceStart": 0,
                    "sourceEnd": src_end_f,
                    "sourceDuration": src_dur_f,
                    "volume": 0.0,
                    "embeddedAudioMuted": True,
                    "transform": {
                        "x": 0,
                        "y": 0,
                        "width": s_w,
                        "height": s_h,
                        "scaleX": 1.0,
                        "scaleY": 1.0,
                    },
                    "originId": anchor_item_id,
                }
            )
            if layout != "motion_scene" and end_kf > 0:
                all_keyframes.append(
                    {
                        "itemId": anchor_item_id,
                        "properties": [
                            {
                                "property": "width",
                                "keyframes": [
                                    {"id": get_uid(), "frame": 0, "value": s_w, "easing": "linear"},
                                    {"id": get_uid(), "frame": end_kf, "value": e_w, "easing": "linear"},
                                ],
                            },
                            {
                                "property": "height",
                                "keyframes": [
                                    {"id": get_uid(), "frame": 0, "value": s_h, "easing": "linear"},
                                    {"id": get_uid(), "frame": end_kf, "value": e_h, "easing": "linear"},
                                ],
                            },
                        ],
                    }
                )

        # ── LAYOUT C: FULL-BLEED KEN BURNS PHOTO ────────────────────
        elif layout == "full_bleed_ken_burns":
            img_mid, img_meta = register_media(media_path)
            sx, sy, sw, sh, ex, ey, ew, eh, kb_ease, chosen_vec = build_ken_burns_keyframes(
                sid, dur_f, scene.get("camera_motion"), prev_kb_vector
            )
            prev_kb_vector = chosen_vec
            items.append(
                {
                    "id": anchor_item_id,
                    "trackId": "track_anchor",
                    "from": start_f,
                    "durationInFrames": dur_f,
                    "label": f"{sid}_ken_burns",
                    "type": "image",
                    "mediaRef": img_mid,
                    "sourceWidth": img_meta["width"],
                    "sourceHeight": img_meta["height"],
                    "volume": 1.0,
                    "transform": {
                        "x": sx,
                        "y": sy,
                        "width": sw,
                        "height": sh,
                        "scaleX": 1.0,
                        "scaleY": 1.0,
                    },
                    "originId": anchor_item_id,
                }
            )
            if end_kf > 0:
                all_keyframes.append(
                    {
                        "itemId": anchor_item_id,
                        "properties": [
                            {
                                "property": "width",
                                "keyframes": [
                                    {"id": get_uid(), "frame": 0, "value": sw, "easing": kb_ease},
                                    {"id": get_uid(), "frame": end_kf, "value": ew, "easing": kb_ease},
                                ],
                            },
                            {
                                "property": "height",
                                "keyframes": [
                                    {"id": get_uid(), "frame": 0, "value": sh, "easing": kb_ease},
                                    {"id": get_uid(), "frame": end_kf, "value": eh, "easing": kb_ease},
                                ],
                            },
                            {
                                "property": "x",
                                "keyframes": [
                                    {"id": get_uid(), "frame": 0, "value": sx, "easing": kb_ease},
                                    {"id": get_uid(), "frame": end_kf, "value": ex, "easing": kb_ease},
                                ],
                            },
                            {
                                "property": "y",
                                "keyframes": [
                                    {"id": get_uid(), "frame": 0, "value": sy, "easing": kb_ease},
                                    {"id": get_uid(), "frame": end_kf, "value": ey, "easing": kb_ease},
                                ],
                            },
                        ],
                    }
                )

        # ── LAYOUT D: EDITORIAL BACKDROP FRAME (Uncropped Portrait / Product / Evidence) ──
        elif layout == "editorial_backdrop_frame":
            plate_path = os.path.join(project_dir, "media", "backdrops", f"{sid}_plate_v63.jpg")
            if not os.path.isfile(plate_path) and media_kind == "image":
                generate_fallback_blur_plate(media_path, plate_path)
            if os.path.isfile(plate_path):
                bg_mid, bg_meta = register_media(plate_path)
                bg_id = det_uid(f"{sid}_bg_plate")
                items.append(
                    {
                        "id": bg_id,
                        "trackId": "track_bg",
                        "from": start_f,
                        "durationInFrames": dur_f,
                        "label": f"{sid}_blur_plate",
                        "type": "image",
                        "mediaRef": bg_mid,
                        "sourceWidth": bg_meta["width"],
                        "sourceHeight": bg_meta["height"],
                        "volume": 1.0,
                        "transform": {
                            "x": 0,
                            "y": 0,
                            "width": int(CANVAS_W * 1.03),
                            "height": int(CANVAS_H * 1.03),
                            "scaleX": 1.0,
                            "scaleY": 1.0,
                        },
                        "originId": bg_id,
                    }
                )
                if end_kf > 0:
                    all_keyframes.append(
                        {
                            "itemId": bg_id,
                            "properties": [
                                {
                                    "property": "width",
                                    "keyframes": [
                                        {"id": get_uid(), "frame": 0, "value": int(CANVAS_W * 1.03), "easing": "linear"},
                                        {"id": get_uid(), "frame": end_kf, "value": int(CANVAS_W * 1.08), "easing": "linear"},
                                    ],
                                },
                                {
                                    "property": "height",
                                    "keyframes": [
                                        {"id": get_uid(), "frame": 0, "value": int(CANVAS_H * 1.03), "easing": "linear"},
                                        {"id": get_uid(), "frame": end_kf, "value": int(CANVAS_H * 1.08), "easing": "linear"},
                                    ],
                                },
                            ],
                        }
                    )

            fg_mid, fg_meta = register_media(media_path)
            has_bottom_caption = bool(scene.get("headline") or scene.get("caption"))
            max_h = 740 if has_bottom_caption else 860
            max_w = 1320
            aspect = (fg_meta["width"] / float(fg_meta["height"])) if fg_meta["height"] > 0 else 1.0
            base_h = max_h
            base_w = int(round(base_h * aspect))
            if base_w > max_w:
                base_w = max_w
                base_h = int(round(base_w / max(0.1, aspect)))

            target_x = 0
            target_y = -62 if has_bottom_caption else 0
            rng_fr = random.Random(f"{sid}_frame")
            rot = round(rng_fr.choice([-1, 0, 1]) * rng_fr.uniform(0.4, 1.1), 2)
            end_w, end_h = int(base_w * 1.045), int(base_h * 1.045)
            intro_f = min(max(2, end_kf - 2), min(13, max(6, dur_f // 6)))
            init_y = target_y + 48

            fg_item: Dict[str, Any] = {
                "id": anchor_item_id,
                "trackId": "track_anchor",
                "from": start_f,
                "durationInFrames": dur_f,
                "label": f"{sid}_framed_subject",
                "type": "video" if media_kind == "video" else "image",
                "mediaRef": fg_mid,
                "sourceWidth": fg_meta["width"],
                "sourceHeight": fg_meta["height"],
                "volume": 0.0 if media_kind == "video" else 1.0,
                "transform": {
                    "x": target_x,
                    "y": init_y,
                    "width": base_w,
                    "height": base_h,
                    "scaleX": 1.0,
                    "scaleY": 1.0,
                    "rotation": rot,
                    "cornerRadius": 18,
                    "dropShadow": {"blur": 32, "color": "rgba(0,0,0,0.58)", "offsetX": 0, "offsetY": 12},
                },
                "originId": anchor_item_id,
            }
            if media_kind == "video":
                s_dur_f = max(1, int(round(fg_meta["duration"] * FPS)))
                fg_item.update({"sourceStart": 0, "sourceEnd": min(dur_f, s_dur_f), "sourceDuration": s_dur_f})
            items.append(fg_item)

            if end_kf > intro_f:
                all_keyframes.append(
                    {
                        "itemId": anchor_item_id,
                        "properties": [
                            {
                                "property": "y",
                                "keyframes": [
                                    {"id": get_uid(), "frame": 0, "value": init_y, "easing": "ease-out"},
                                    {"id": get_uid(), "frame": intro_f, "value": target_y, "easing": "ease-out"},
                                    {"id": get_uid(), "frame": end_kf, "value": target_y, "easing": "linear"},
                                ],
                            },
                            {
                                "property": "width",
                                "keyframes": [
                                    {"id": get_uid(), "frame": 0, "value": base_w, "easing": "linear"},
                                    {"id": get_uid(), "frame": end_kf, "value": end_w, "easing": "linear"},
                                ],
                            },
                            {
                                "property": "height",
                                "keyframes": [
                                    {"id": get_uid(), "frame": 0, "value": base_h, "easing": "linear"},
                                    {"id": get_uid(), "frame": end_kf, "value": end_h, "easing": "linear"},
                                ],
                            },
                        ],
                    }
                )
            has_custom_entrance = True

            if has_bottom_caption:
                cap_raw = scene.get("headline") or scene.get("caption")
                c_plain, c_spans, c_font, c_in = build_callout_spans(cap_raw, idx)
                append_native_text_item(
                    items=items,
                    all_keyframes=all_keyframes,
                    item_id=det_uid(f"{sid}_frame_cap"),
                    from_f=start_f + 4,
                    dur_f=max(10, dur_f - 4),
                    label=f"{sid}_caption",
                    text=c_plain,
                    x=0,
                    y=405,
                    width=1360,
                    height=140,
                    font_size=int(scene.get("font_size", 40)),
                    font_family=c_font,
                    font_weight="bold",
                    color="#F8FAFC",
                    text_align="center",
                    entry_type=c_in,
                    exit_type="fade-down",
                    text_spans=c_spans,
                    on_light_bg=False,
                    over_busy_media=True,
                )

        # ── LAYOUT E: SPLIT EDITORIAL SLIDE (Asymmetric 55/45 — Zero Overlap) ──
        elif layout == "split_editorial_slide":
            bg_hex = scene_bg_hex or (paper_hex if split_side_toggle % 2 == 0 else studio_hex)
            on_light_canvas = is_light_hex(bg_hex)
            canvas_path = os.path.join(project_dir, "media", "backdrops", f"{sid}_canvas.jpg")
            generate_editorial_canvas(canvas_path, bg_hex, f"{sid}_split")
            bg_mid, bg_meta = register_media(canvas_path)
            bg_id = det_uid(f"{sid}_split_bg")
            items.append(
                {
                    "id": bg_id,
                    "trackId": "track_bg",
                    "from": start_f,
                    "durationInFrames": dur_f,
                    "label": f"{sid}_editorial_canvas",
                    "type": "image",
                    "mediaRef": bg_mid,
                    "sourceWidth": bg_meta["width"],
                    "sourceHeight": bg_meta["height"],
                    "volume": 1.0,
                    "transform": {
                        "x": 0,
                        "y": 0,
                        "width": int(CANVAS_W * 1.01),
                        "height": int(CANVAS_H * 1.01),
                        "scaleX": 1.0,
                        "scaleY": 1.0,
                    },
                    "originId": bg_id,
                }
            )

            media_side = scene.get("media_side")
            if media_side not in ("left", "right"):
                media_side = "left" if split_side_toggle % 2 == 0 else "right"
            split_side_toggle += 1

            fg_mid, fg_meta = register_media(media_path)
            aspect = (fg_meta["width"] / float(fg_meta["height"])) if fg_meta["height"] > 0 else 1.33
            max_w, max_h = 830, 810
            base_w = max_w
            base_h = int(round(base_w / max(0.15, aspect)))
            if base_h > max_h:
                base_h = max_h
                base_w = int(round(base_h * aspect))

            media_x = -430 if media_side == "left" else 430
            text_x = 435 if media_side == "left" else -435
            offscreen_x = (-960 - base_w // 2 - 40) if media_side == "left" else (960 + base_w // 2 + 40)
            intro_f = min(max(2, end_kf - 2), min(14, max(6, dur_f // 6)))
            end_w, end_h = int(base_w * 1.04), int(base_h * 1.04)

            split_item: Dict[str, Any] = {
                "id": anchor_item_id,
                "trackId": "track_anchor",
                "from": start_f,
                "durationInFrames": dur_f,
                "label": f"{sid}_split_media",
                "type": "video" if media_kind == "video" else "image",
                "mediaRef": fg_mid,
                "sourceWidth": fg_meta["width"],
                "sourceHeight": fg_meta["height"],
                "volume": 0.0 if media_kind == "video" else 1.0,
                "transform": {
                    "x": offscreen_x,
                    "y": 0,
                    "width": base_w,
                    "height": base_h,
                    "scaleX": 1.0,
                    "scaleY": 1.0,
                    "rotation": -0.8 if media_side == "left" else 0.8,
                    "cornerRadius": 16,
                    "dropShadow": {"blur": 26, "color": "rgba(0,0,0,0.32)" if on_light_canvas else "rgba(0,0,0,0.55)", "offsetX": 0, "offsetY": 10},
                },
                "originId": anchor_item_id,
            }
            if media_kind == "video":
                s_dur_f = max(1, int(round(fg_meta["duration"] * FPS)))
                split_item.update({"sourceStart": 0, "sourceEnd": min(dur_f, s_dur_f), "sourceDuration": s_dur_f})
            items.append(split_item)

            if end_kf > intro_f:
                all_keyframes.append(
                    {
                        "itemId": anchor_item_id,
                        "properties": [
                            {
                                "property": "x",
                                "keyframes": [
                                    {"id": get_uid(), "frame": 0, "value": offscreen_x, "easing": "ease-out"},
                                    {"id": get_uid(), "frame": intro_f, "value": media_x, "easing": "ease-out"},
                                    {"id": get_uid(), "frame": end_kf, "value": media_x, "easing": "linear"},
                                ],
                            },
                            {
                                "property": "width",
                                "keyframes": [
                                    {"id": get_uid(), "frame": 0, "value": base_w, "easing": "linear"},
                                    {"id": get_uid(), "frame": end_kf, "value": end_w, "easing": "linear"},
                                ],
                            },
                            {
                                "property": "height",
                                "keyframes": [
                                    {"id": get_uid(), "frame": 0, "value": base_h, "easing": "linear"},
                                    {"id": get_uid(), "frame": end_kf, "value": end_h, "easing": "linear"},
                                ],
                            },
                        ],
                    }
                )
            has_custom_entrance = True

            split_txt = scene.get("headline") or scene.get("caption") or scene.get("narration", "")
            s_plain, s_spans, s_font, s_in = build_callout_spans(split_txt, idx)
            append_native_text_item(
                items=items,
                all_keyframes=all_keyframes,
                item_id=det_uid(f"{sid}_split_txt"),
                from_f=start_f + 4,
                dur_f=max(10, dur_f - 4),
                label=f"{sid}_split_text",
                text=s_plain,
                x=text_x,
                y=0,
                width=790,
                height=360,
                font_size=int(scene.get("font_size", 46)),
                font_family=s_font,
                font_weight="bold",
                color="#14181F" if on_light_canvas else "#F8FAFC",
                text_align="left",
                entry_type=s_in,
                exit_type="fade-down",
                text_spans=s_spans,
                on_light_bg=on_light_canvas,
                over_busy_media=False,
                letter_spacing=-0.9,
            )

        # ── LAYOUT F: PARALLAX CUTOUT STAGE (3 Distinct Editorial Archetypes + Grounded Portraits!) ──
        elif layout == "parallax_cutout_stage":
            is_bottom_cropped, _, accent_rgb = inspect_cutout_alpha(media_path)
            explicit_var = (scene.get("cutout_variant") or "").strip().lower()
            valid_archetypes = ("poster_monumental_center", "archival_dossier_paper", "magazine_grounded_portrait")
            if explicit_var in valid_archetypes:
                archetype = explicit_var
            elif is_bottom_cropped:
                archetype = "magazine_grounded_portrait"
            else:
                archetype = valid_archetypes[cutout_free_counter % 2]
                cutout_free_counter += 1

            on_light_canvas = (archetype == "archival_dossier_paper")
            st_plain, st_spans, st_font, st_in, bg_token = build_cutout_editorial_lockup(scene, archetype)

            # Subject horizontal placement normalized in [-0.5, +0.5]
            if is_vertical or archetype == "poster_monumental_center":
                subj_x_norm = 0.0
            elif archetype == "archival_dossier_paper":
                subj_x_norm = 0.21
            else:
                subj_x_norm = 0.21

            stage_plate_path = os.path.join(project_dir, "media", "backdrops", f"{sid}_{archetype}_v63.jpg")
            generate_cutout_stage_backdrop(stage_plate_path, archetype, accent_rgb, f"{sid}_{archetype}", subject_x_norm=subj_x_norm)
            bg_mid, bg_meta = register_media(stage_plate_path)

            # In `poster_monumental_center`, backdrop goes on `track_bg` so giant monumental display type sits on `track_anchor` BEHIND `track_fg_2`!
            use_monumental_bg_type = (archetype == "poster_monumental_center" and bool(bg_token))
            plate_track = "track_bg" if use_monumental_bg_type else "track_anchor"
            plate_item_id = det_uid(f"{sid}_stage_bg") if use_monumental_bg_type else anchor_item_id

            items.append(
                {
                    "id": plate_item_id,
                    "trackId": plate_track,
                    "from": start_f,
                    "durationInFrames": dur_f,
                    "label": f"{sid}_{archetype}_plate",
                    "type": "image",
                    "mediaRef": bg_mid,
                    "sourceWidth": bg_meta["width"],
                    "sourceHeight": bg_meta["height"],
                    "volume": 1.0,
                    "transform": {
                        "x": 0,
                        "y": 0,
                        "width": int(CANVAS_W * 1.04),
                        "height": int(CANVAS_H * 1.04),
                        "scaleX": 1.0,
                        "scaleY": 1.0,
                    },
                    "motionModifiers": [build_motion_modifier(f"{sid}_plate", "breath-pulse", 0.12, 0.14)],
                    "originId": plate_item_id,
                }
            )
            if end_kf > 0:
                all_keyframes.append(
                    {
                        "itemId": plate_item_id,
                        "properties": [
                            {
                                "property": "width",
                                "keyframes": [
                                    {"id": get_uid(), "frame": 0, "value": int(CANVAS_W * 1.04), "easing": "linear"},
                                    {"id": get_uid(), "frame": end_kf, "value": int(CANVAS_W * 1.01), "easing": "linear"},
                                ],
                            },
                            {
                                "property": "height",
                                "keyframes": [
                                    {"id": get_uid(), "frame": 0, "value": int(CANVAS_H * 1.04), "easing": "linear"},
                                    {"id": get_uid(), "frame": end_kf, "value": int(CANVAS_H * 1.01), "easing": "linear"},
                                ],
                            },
                        ],
                    }
                )

            if use_monumental_bg_type:
                mon_txt = "  ".join(list(str(bg_token))) if len(str(bg_token)) == 4 and str(bg_token).isdigit() else str(bg_token)
                mon_x = 0
                mon_y = int(CANVAS_H * (0.02 if is_vertical else -0.10))
                append_native_text_item(
                    items=items,
                    all_keyframes=all_keyframes,
                    item_id=anchor_item_id,
                    from_f=start_f,
                    dur_f=dur_f,
                    label=f"{sid}_monumental_bg_type",
                    text=mon_txt,
                    x=mon_x,
                    y=mon_y,
                    width=int(CANVAS_W * (0.90 if is_vertical else 0.84)),
                    height=420,
                    font_size=220 if is_vertical else 330,
                    font_family="Bebas Neue",
                    font_weight="bold",
                    color="#6EE7B7",
                    text_align="center",
                    entry_type="rise",
                    exit_type="fade-down",
                    opacity=0.24,
                    on_light_bg=False,
                    over_busy_media=False,
                    letter_spacing=12.0,
                    line_height=1.0,
                    track_id="track_anchor",
                )

            cut_mid, cut_meta = register_media(media_path)
            cut_id = det_uid(f"{sid}_fg_cutout")
            c_aspect = (cut_meta["width"] / float(cut_meta["height"])) if cut_meta["height"] > 0 else 0.75

            if is_bottom_cropped:
                max_ch = int(CANVAS_H * (0.60 if is_vertical else 0.85))
                max_cw = int(CANVAS_W * (0.86 if is_vertical else 0.45))
            elif archetype == "poster_monumental_center":
                max_ch = int(CANVAS_H * (0.52 if is_vertical else 0.64))
                max_cw = int(CANVAS_W * (0.74 if is_vertical else 0.34))
            else:
                max_ch = int(CANVAS_H * (0.56 if is_vertical else 0.80))
                max_cw = int(CANVAS_W * (0.76 if is_vertical else 0.36))

            cw = int(round(max_ch * c_aspect))
            ch = max_ch
            if cw > max_cw:
                cw = max_cw
                ch = int(round(cw / max(0.15, c_aspect)))

            cx = int(CANVAS_W * subj_x_norm)
            intro_f = min(max(2, end_kf - 2), min(14, max(6, dur_f // 6)))

            if is_bottom_cropped:
                # Ground waist/chest-cropped portraits FLUSH to the bottom canvas edge on every frame!
                cw0, ch0 = int(cw * 0.95), int(ch * 0.95)
                cw_end, ch_end = int(cw * 1.035), int(ch * 1.035)
                bottom_edge = (CANVAS_H // 2) + 12
                y0 = int(bottom_edge - (ch0 // 2) + 34)
                y_mid = int(bottom_edge - (ch // 2))
                y_end = int(bottom_edge - (ch_end // 2))
                cut_rot = 0.0
                cut_mod = build_motion_modifier(f"{sid}_cut", "breath-pulse", 0.16, 0.16)
            else:
                cw0, ch0 = int(cw * 0.94), int(ch * 0.94)
                cw_end, ch_end = int(cw * 1.04), int(ch * 1.04)
                if archetype == "poster_monumental_center" and not is_vertical:
                    cy_base = -int(CANVAS_H * 0.085)
                else:
                    cy_base = int(CANVAS_H * (0.12 if is_vertical else 0.01))
                y0 = cy_base + 36
                y_mid = cy_base
                y_end = cy_base - 8
                cut_rot = -3.5 if archetype == "archival_dossier_paper" else 0.0
                cut_mod = build_motion_modifier(
                    f"{sid}_cut",
                    "sway" if archetype == "archival_dossier_paper" else "float-drift",
                    0.24,
                    0.19,
                )

            shadow_col = "rgba(28,18,10,0.34)" if on_light_canvas else "rgba(0,0,0,0.72)"
            items.append(
                {
                    "id": cut_id,
                    "trackId": "track_fg_2",
                    "from": start_f,
                    "durationInFrames": dur_f,
                    "label": f"{sid}_cutout_{archetype}",
                    "type": "image",
                    "mediaRef": cut_mid,
                    "sourceWidth": cut_meta["width"],
                    "sourceHeight": cut_meta["height"],
                    "volume": 1.0,
                    "transform": {
                        "x": cx,
                        "y": y0,
                        "width": cw0,
                        "height": ch0,
                        "scaleX": 1.0,
                        "scaleY": 1.0,
                        "rotation": cut_rot,
                        "cornerRadius": 0,
                        "dropShadow": {"blur": 36, "color": shadow_col, "offsetX": 0, "offsetY": 16},
                    },
                    "motionModifiers": [cut_mod],
                    "originId": cut_id,
                }
            )
            if end_kf > intro_f:
                kf_props = [
                    {
                        "property": "y",
                        "keyframes": [
                            {"id": get_uid(), "frame": 0, "value": y0, "easing": "ease-out"},
                            {"id": get_uid(), "frame": intro_f, "value": y_mid, "easing": "ease-out"},
                            {"id": get_uid(), "frame": end_kf, "value": y_end, "easing": "linear"},
                        ],
                    },
                    {
                        "property": "width",
                        "keyframes": [
                            {"id": get_uid(), "frame": 0, "value": cw0, "easing": "ease-out"},
                            {"id": get_uid(), "frame": intro_f, "value": cw, "easing": "ease-out"},
                            {"id": get_uid(), "frame": end_kf, "value": cw_end, "easing": "linear"},
                        ],
                    },
                    {
                        "property": "height",
                        "keyframes": [
                            {"id": get_uid(), "frame": 0, "value": ch0, "easing": "ease-out"},
                            {"id": get_uid(), "frame": intro_f, "value": ch, "easing": "ease-out"},
                            {"id": get_uid(), "frame": end_kf, "value": ch_end, "easing": "linear"},
                        ],
                    },
                ]
                all_keyframes.append({"itemId": cut_id, "properties": kf_props})
            has_custom_entrance = True

            has_stage_txt = bool(scene.get("headline") or scene.get("caption") or scene.get("hero_stat"))
            if has_stage_txt:
                t_box_h = 340
                if is_vertical:
                    tx, ty, tw, talign = 0, -int(CANVAS_H * 0.28), int(CANVAS_W * 0.86), "center"
                elif archetype == "poster_monumental_center":
                    tx, ty, tw, talign, t_box_h = 0, int(CANVAS_H * 0.355), int(CANVAS_W * 0.74), "center", 190
                elif archetype == "archival_dossier_paper":
                    tx, ty, tw, talign = -int(CANVAS_W * 0.19), -int(CANVAS_H * 0.01), int(CANVAS_W * 0.42), "left"
                else:
                    tx, ty, tw, talign = -int(CANVAS_W * 0.23), -int(CANVAS_H * 0.01), int(CANVAS_W * 0.40), "left"

                out_p = "blur-out" if archetype == "archival_dossier_paper" else "fade-down"
                append_native_text_item(
                    items=items,
                    all_keyframes=all_keyframes,
                    item_id=det_uid(f"{sid}_stage_txt"),
                    from_f=start_f + 3,
                    dur_f=max(12, dur_f - 4),
                    label=f"{sid}_stage_lockup",
                    text=st_plain,
                    x=tx,
                    y=ty,
                    width=tw,
                    height=t_box_h,
                    font_size=int(scene.get("font_size", 68)),
                    font_family=st_font,
                    font_weight="bold",
                    color="#14181F" if on_light_canvas else "#F8FAFC",
                    text_align=talign,
                    entry_type=st_in,
                    exit_type=out_p,
                    text_spans=st_spans,
                    on_light_bg=on_light_canvas,
                    over_busy_media=not on_light_canvas,
                    line_height=1.22,
                )

        # ── LAYOUT G: PRESS EVIDENCE HIGHLIGHT (Real Clipping + Animated Marker Sweep) ──
        elif layout == "press_evidence_highlight":
            plate_path = os.path.join(project_dir, "media", "backdrops", f"{sid}_plate_v63.jpg")
            if not os.path.isfile(plate_path):
                generate_fallback_blur_plate(media_path, plate_path)
            bg_mid, bg_meta = register_media(plate_path)
            bg_id = det_uid(f"{sid}_ev_bg")
            items.append(
                {
                    "id": bg_id,
                    "trackId": "track_bg",
                    "from": start_f,
                    "durationInFrames": dur_f,
                    "label": f"{sid}_evidence_bg",
                    "type": "image",
                    "mediaRef": bg_mid,
                    "sourceWidth": bg_meta["width"],
                    "sourceHeight": bg_meta["height"],
                    "volume": 1.0,
                    "transform": {"x": 0, "y": 0, "width": int(CANVAS_W * 1.04), "height": int(CANVAS_H * 1.04), "scaleX": 1.0, "scaleY": 1.0},
                    "originId": bg_id,
                }
            )
            ev_mid, ev_meta = register_media(media_path)
            ev_aspect = (ev_meta["width"] / float(ev_meta["height"])) if ev_meta["height"] > 0 else 1.5
            max_ew = int(CANVAS_W * (0.88 if is_vertical else 0.74))
            max_eh = int(CANVAS_H * (0.55 if is_vertical else 0.76))
            ew = max_ew
            eh = int(round(ew / max(0.2, ev_aspect)))
            if eh > max_eh:
                eh = max_eh
                ew = int(round(eh * ev_aspect))

            items.append(
                {
                    "id": anchor_item_id,
                    "trackId": "track_anchor",
                    "from": start_f,
                    "durationInFrames": dur_f,
                    "label": f"{sid}_press_print",
                    "type": "image",
                    "mediaRef": ev_mid,
                    "sourceWidth": ev_meta["width"],
                    "sourceHeight": ev_meta["height"],
                    "volume": 1.0,
                    "transform": {
                        "x": 0,
                        "y": -20 if scene.get("caption") else 0,
                        "width": ew,
                        "height": eh,
                        "scaleX": 1.0,
                        "scaleY": 1.0,
                        "rotation": -0.6,
                        "cornerRadius": 6,
                        "dropShadow": {"blur": 40, "color": "rgba(0,0,0,0.68)", "offsetX": 0, "offsetY": 16},
                    },
                    "originId": anchor_item_id,
                }
            )
            if end_kf > 0:
                all_keyframes.append(
                    {
                        "itemId": anchor_item_id,
                        "properties": [
                            {
                                "property": "width",
                                "keyframes": [
                                    {"id": get_uid(), "frame": 0, "value": ew, "easing": "ease-out"},
                                    {"id": get_uid(), "frame": end_kf, "value": int(ew * 1.045), "easing": "linear"},
                                ],
                            },
                            {
                                "property": "height",
                                "keyframes": [
                                    {"id": get_uid(), "frame": 0, "value": eh, "easing": "ease-out"},
                                    {"id": get_uid(), "frame": end_kf, "value": int(eh * 1.045), "easing": "linear"},
                                ],
                            },
                        ],
                    }
                )
            # Auto-attach translucent yellow marker highlight Lottie synced to anchor_word!
            if not scene.get("lottie_overlay") and os.path.isfile(LOTTIE_GEN_SCRIPT):
                auto_lot = os.path.join(project_dir, "lottie", f"{sid}_marker.json")
                if not os.path.isfile(auto_lot):
                    subprocess.run(
                        [sys.executable, LOTTIE_GEN_SCRIPT, "--kind", "marker_highlight", "--accent", "#FACC15", "--duration", str(round(dur_ms / 1000.0, 2)), "--out", auto_lot],
                        capture_output=True,
                    )
                if os.path.isfile(auto_lot):
                    off_f = find_word_offset_frames(words_list, start_ms, end_ms, scene.get("anchor_word", ""))
                    scene = dict(scene)
                    scene["lottie_overlay"] = {
                        "file": auto_lot,
                        "x": int(scene.get("highlight_x", 0)),
                        "y": int(scene.get("highlight_y", -int(eh * 0.16))),
                        "width": int(ew * 0.72),
                        "height": 96,
                        "offset_frames": off_f,
                    }
            has_custom_entrance = True

        # ── LAYOUT H: A-ROLL / TALKING-HEAD YAP OVERLAY ───────────────
        elif layout == "aroll_yap_overlay":
            aroll_src = storyboard.get("aroll_file") or narration_path
            if not os.path.isabs(aroll_src):
                aroll_src = os.path.join(project_dir, aroll_src)
            if os.path.isfile(aroll_src) and detect_mime(aroll_src).startswith("video/"):
                ar_mid, ar_meta = register_media(aroll_src)
                ar_src_dur = max(1, int(round(ar_meta["duration"] * FPS)))
                punch = 1.07 if (idx % 2 == 1) else 1.01
                items.append(
                    {
                        "id": anchor_item_id,
                        "trackId": "track_anchor",
                        "from": start_f,
                        "durationInFrames": dur_f,
                        "label": f"{sid}_aroll_cam",
                        "type": "video",
                        "mediaRef": ar_mid,
                        "sourceWidth": ar_meta["width"],
                        "sourceHeight": ar_meta["height"],
                        "sourceStart": min(ar_src_dur - 1, start_f),
                        "sourceEnd": min(ar_src_dur, start_f + dur_f),
                        "sourceDuration": ar_src_dur,
                        "volume": 0.0,
                        "embeddedAudioMuted": True,
                        "transform": {
                            "x": 0,
                            "y": 0,
                            "width": int(CANVAS_W * punch),
                            "height": int(CANVAS_H * punch),
                            "scaleX": 1.0,
                            "scaleY": 1.0,
                        },
                        "originId": anchor_item_id,
                    }
                )
            if media_path:
                ov_mid, ov_meta = register_media(media_path)
                ov_id = det_uid(f"{sid}_yap_pop")
                off_f = find_word_offset_frames(words_list, start_ms, end_ms, scene.get("anchor_word", ""))
                pop_dur = max(12, dur_f - off_f - 4)
                ov_aspect = (ov_meta["width"] / float(ov_meta["height"])) if ov_meta["height"] > 0 else 1.0
                ow = int(CANVAS_W * (0.56 if is_vertical else 0.30))
                oh = int(round(ow / max(0.2, ov_aspect)))
                ox = 0 if is_vertical else int(CANVAS_W * 0.28)
                oy = -int(CANVAS_H * 0.26) if is_vertical else -int(CANVAS_H * 0.12)
                items.append(
                    {
                        "id": ov_id,
                        "trackId": "track_fg_2",
                        "from": start_f + off_f,
                        "durationInFrames": pop_dur,
                        "label": f"{sid}_yap_visual",
                        "type": "video" if media_kind == "video" else "image",
                        "mediaRef": ov_mid,
                        "sourceWidth": ov_meta["width"],
                        "sourceHeight": ov_meta["height"],
                        "volume": 0.0 if media_kind == "video" else 1.0,
                        "transform": {
                            "x": ox,
                            "y": oy,
                            "width": ow,
                            "height": oh,
                            "scaleX": 1.0,
                            "scaleY": 1.0,
                            "cornerRadius": 0 if media_path.endswith(".png") else 14,
                            "dropShadow": {"blur": 28, "color": "rgba(0,0,0,0.55)", "offsetX": 0, "offsetY": 10},
                        },
                        "motionModifiers": [build_motion_modifier(f"{sid}_yap", "float-drift", 0.20, 0.22)],
                        "originId": ov_id,
                    }
                )
                has_custom_entrance = True

        # ── LAYOUT I: CUSTOM MANUAL MULTI-LAYER NLE MODE (For Frontier AI Full Control) ──
        elif layout == "custom_layers":
            for l_idx, lyr in enumerate(scene.get("layers", [])):
                l_type = str(lyr.get("type", "image")).lower()
                l_track = lyr.get("track") or ("track_text" if l_type == "text" else "track_anchor")
                l_off_f = ms_to_frames(lyr["offset_ms"]) if lyr.get("offset_ms") else 0
                if lyr.get("anchor_word"):
                    l_off_f = find_word_offset_frames(words_list, start_ms, end_ms, lyr["anchor_word"])
                l_dur_f = ms_to_frames(lyr["duration_ms"]) if lyr.get("duration_ms") else max(6, dur_f - l_off_f)
                l_id = det_uid(f"{sid}_custom_{l_idx}")

                if l_type == "text":
                    append_native_text_item(
                        items=items,
                        all_keyframes=all_keyframes,
                        item_id=l_id,
                        from_f=start_f + l_off_f,
                        dur_f=l_dur_f,
                        label=f"{sid}_lyr_{l_idx}",
                        text=str(lyr.get("text", "")),
                        x=int(lyr.get("x", 0)),
                        y=int(lyr.get("y", 0)),
                        width=int(lyr.get("width", int(CANVAS_W * 0.7))),
                        height=int(lyr.get("height", 200)),
                        font_size=int(lyr.get("font_size", 52)),
                        font_family=lyr.get("font_family", font_display),
                        font_weight=lyr.get("font_weight", "bold"),
                        font_style=lyr.get("font_style", "normal"),
                        color=lyr.get("color", "#FFFFFF"),
                        text_align=lyr.get("text_align", "center"),
                        entry_type=lyr.get("entry_type", "fade-up"),
                        exit_type=lyr.get("exit_type", "fade-down"),
                        loop_type=lyr.get("loop_type"),
                        text_spans=lyr.get("text_spans"),
                        opacity=float(lyr.get("opacity", 1.0)),
                        on_light_bg=bool(lyr.get("on_light_bg", False)),
                        over_busy_media=bool(lyr.get("over_busy_media", True)),
                        track_id=l_track,
                    )
                else:
                    lf = lyr.get("file", "")
                    lfull = lf if os.path.isabs(lf) else os.path.join(project_dir, lf)
                    if not os.path.isfile(lfull):
                        continue
                    l_mid, l_meta = register_media(lfull)
                    if l_idx == 0 and l_track == "track_anchor":
                        l_id = anchor_item_id
                    actual_t = "lottie" if lfull.endswith(".json") else ("video" if detect_mime(lfull).startswith("video/") else "image")
                    item_obj: Dict[str, Any] = {
                        "id": l_id,
                        "trackId": l_track,
                        "from": start_f + l_off_f,
                        "durationInFrames": l_dur_f,
                        "label": f"{sid}_lyr_{l_idx}",
                        "type": actual_t,
                        "mediaRef": l_mid,
                        "sourceWidth": l_meta["width"],
                        "sourceHeight": l_meta["height"],
                        "volume": 0.0 if actual_t in ("video", "lottie") else 1.0,
                        "transform": {
                            "x": int(lyr.get("x", 0)),
                            "y": int(lyr.get("y", 0)),
                            "width": int(lyr.get("width", l_meta["width"] or CANVAS_W)),
                            "height": int(lyr.get("height", l_meta["height"] or CANVAS_H)),
                            "scaleX": 1.0,
                            "scaleY": 1.0,
                            "rotation": float(lyr.get("rotation", 0.0)),
                            "cornerRadius": int(lyr.get("cornerRadius", 0)),
                        },
                        "originId": l_id,
                    }
                    if actual_t == "video":
                        sd = max(1, int(round(l_meta["duration"] * FPS)))
                        item_obj.update({"sourceStart": 0, "sourceEnd": min(l_dur_f, sd), "sourceDuration": sd})
                    elif actual_t == "lottie":
                        item_obj.update(
                            {
                                "frameRate": int(l_meta.get("fps", 30)),
                                "totalFrames": int(l_meta.get("total_frames", max(1, l_dur_f))),
                                "loop": False,
                            }
                        )
                    items.append(item_obj)
            has_custom_entrance = True

        # ── OPTIONAL TEXT CALLOUTS FOR FULL-BLEED / B-ROLL SCENES (Aspect-Ratio Safe!) ────
        if layout in ("cinematic_broll", "full_bleed_ken_burns") and (scene.get("headline") or scene.get("caption")):
            call_raw = scene.get("headline") or scene.get("caption")
            c_plain, c_spans, c_font, c_in = build_callout_spans(call_raw, idx)
            pos_hint = scene.get("text_position", "bottom_center" if is_vertical else "bottom_left")
            if is_vertical:
                tx, ty, tw, talign = 0, (int(CANVAS_H * 0.24) if pos_hint != "top_left" else -int(CANVAS_H * 0.32)), int(CANVAS_W * 0.84), "center"
            elif pos_hint == "top_left":
                tx, ty, tw, talign = -int(CANVAS_W * 0.25), -int(CANVAS_H * 0.36), int(CANVAS_W * 0.42), "left"
            elif pos_hint == "bottom_center":
                tx, ty, tw, talign = 0, int(CANVAS_H * 0.36), int(CANVAS_W * 0.72), "center"
            else:
                tx, ty, tw, talign = -int(CANVAS_W * 0.22), int(CANVAS_H * 0.35), int(CANVAS_W * 0.46), "left"

            append_native_text_item(
                items=items,
                all_keyframes=all_keyframes,
                item_id=det_uid(f"{sid}_callout_txt"),
                from_f=start_f + 5,
                dur_f=max(12, dur_f - 8),
                label=f"{sid}_callout",
                text=c_plain,
                x=tx,
                y=ty,
                width=tw,
                height=165,
                font_size=int(scene.get("font_size", 40)),
                font_family=c_font,
                font_weight="bold",
                color="#FFFFFF",
                text_align=talign,
                entry_type=scene.get("text_entry", c_in),
                exit_type="fade-down",
                text_spans=c_spans,
                on_light_bg=False,
                over_busy_media=True,
                line_height=1.20,
            )

        # ── OPTIONAL TRANSPARENT LOTTIE OVERLAY (`track_fg_3`) ───────
        lottie_cfg = scene.get("lottie_overlay")
        if isinstance(lottie_cfg, dict) and lottie_cfg.get("file"):
            l_file = lottie_cfg["file"]
            l_full = l_file if os.path.isabs(l_file) else os.path.join(project_dir, l_file)
            if os.path.isfile(l_full):
                l_mid, l_meta = register_media(l_full)
                l_id = det_uid(f"{sid}_lottie_ov")
                lw = int(lottie_cfg.get("width", l_meta["width"]))
                lh = int(lottie_cfg.get("height", l_meta["height"]))
                lx = int(lottie_cfg.get("x", 0))
                ly = int(lottie_cfg.get("y", 0))
                l_off = int(lottie_cfg.get("offset_frames", 4))
                l_dur = max(12, min(dur_f - l_off, int(round(l_meta["duration"] * FPS))))
                items.append(
                    {
                        "id": l_id,
                        "trackId": "track_fg_3",
                        "from": start_f + l_off,
                        "durationInFrames": l_dur,
                        "label": f"{sid}_lottie_{os.path.splitext(os.path.basename(l_full))[0]}",
                        "type": "lottie",
                        "mediaRef": l_mid,
                        "sourceWidth": l_meta["width"],
                        "sourceHeight": l_meta["height"],
                        "frameRate": int(l_meta.get("fps", 30)),
                        "totalFrames": int(l_meta.get("total_frames", max(1, l_dur))),
                        "loop": False,
                        "volume": 0.0,
                        "transform": {
                            "x": lx,
                            "y": ly,
                            "width": lw,
                            "height": lh,
                            "scaleX": 1.0,
                            "scaleY": 1.0,
                            "rotation": 0.0,
                            "cornerRadius": 0,
                        },
                        "originId": l_id,
                    }
                )

        # ── CAUSAL SFX ON PHYSICAL ENTRANCES (`track_sfx`) ───────────
        sfx_cfg = scene.get("sfx", {})
        sfx_explicit_off = isinstance(sfx_cfg, dict) and sfx_cfg.get("enabled") is False
        should_sfx = (start_f > 0) and not sfx_explicit_off and (
            has_custom_entrance or layout == "motion_scene" or (isinstance(sfx_cfg, dict) and sfx_cfg.get("enabled") is True)
        )
        if should_sfx:
            picked = pick_bundled_sfx(f"{sid}_sfx", gentle=(layout != "kinetic_statement"), layout=layout)
            if picked:
                sfx_path, sfx_db = picked
                sfx_mid, sfx_meta = register_media(sfx_path)
                sfx_id = det_uid(f"{sid}_sfx")
                sfx_dur_s = round(min(1.4, sfx_meta["duration"]), 4)
                sfx_dur_f = max(4, min(dur_f, int(round(sfx_dur_s * FPS))))
                items.append(
                    {
                        "id": sfx_id,
                        "trackId": "track_sfx",
                        "from": start_f,
                        "durationInFrames": sfx_dur_f,
                        "label": os.path.basename(sfx_path),
                        "type": "audio",
                        "mediaRef": sfx_mid,
                        "sourceStart": 0.0,
                        "sourceEnd": sfx_dur_s,
                        "sourceDuration": round(sfx_meta["duration"], 4),
                        "volume": sfx_db,
                        "originId": sfx_id,
                    }
                )

        # ── GPU ANALOG GRADE (`track_fg_1`) ON ~30% OF PHOTO/B-ROLL SCENES ──
        gpu_grade = scene.get("gpu_grade")
        if gpu_grade and gpu_grade != "none":
            add_gpu_adjustment(items, sid, start_f, dur_f, gpu_grade)
        elif layout in ("cinematic_broll", "full_bleed_ken_burns", "editorial_backdrop_frame") and not on_light_canvas:
            rng_adj = random.Random(f"{project_id}_{sid}_adj")
            if rng_adj.random() < 0.34:
                chosen_grade = rng_adj.choice(["documentary_clean", "documentary_clean", "cinematic_retro"])
                add_gpu_adjustment(items, sid, start_f, dur_f, chosen_grade)

        anchor_scene_records.append(
            {
                "sid": sid,
                "item_id": anchor_item_id,
                "layout": layout,
                "has_custom_entrance": has_custom_entrance,
                "transition": scene.get("transition"),
            }
        )

    # 3. Curated Documentary Transitions between Full-Frame Anchor Clips
    transitions_list: List[Dict[str, Any]] = []
    rng_tr = random.Random(f"{project_id}_transitions")
    doc_presets = ["dissolve", "dissolve", "blurDissolve", "filmGateSlip"]

    for i in range(len(anchor_scene_records) - 1):
        left = anchor_scene_records[i]
        right = anchor_scene_records[i + 1]
        # Never crossfade into/out of framed slides with custom offscreen entrances or light paper splits
        if left["has_custom_entrance"] or right["has_custom_entrance"]:
            continue
        explicit_tr = right.get("transition")
        if explicit_tr == "cut":
            continue
        preset = explicit_tr if explicit_tr in ("dissolve", "blurDissolve", "slide", "wipe", "filmGateSlip") else rng_tr.choice(doc_presets)
        tr_obj: Dict[str, Any] = {
            "id": det_uid(f"{project_id}_trans_{i}"),
            "leftClipId": left["item_id"],
            "rightClipId": right["item_id"],
            "trackId": "track_anchor",
            "type": "crossfade",
            "durationInFrames": rng_tr.randint(10, 15),
            "presentation": preset,
            "timing": "linear",
            "alignment": 0.5,
        }
        if preset in ("slide", "wipe"):
            tr_obj["direction"] = rng_tr.choice(["from-left", "from-right"])
        transitions_list.append(tr_obj)

    # 3b. Optional Word-Aligned Phrase Captions (`track_captions`)
    cap_cfg = storyboard.get("captions")
    cap_enabled = force_captions or (cap_cfg is True) or (isinstance(cap_cfg, dict) and cap_cfg.get("enabled", False))
    if cap_enabled and words_list:
        max_w_chunk = 3 if is_vertical else 5
        chunks: List[List[Dict[str, Any]]] = []
        buf: List[Dict[str, Any]] = []
        for w in words_list:
            buf.append(w)
            gap_break = len(buf) >= 2 and (w["start_ms"] - buf[-2]["end_ms"] > 420)
            if gap_break and len(buf) > 1:
                last_w = buf.pop()
                chunks.append(buf)
                buf = [last_w]
                continue
            if len(buf) >= max_w_chunk or str(w.get("word", "")).endswith((".", "!", "?", ":", ";")):
                chunks.append(buf)
                buf = []
        if buf:
            chunks.append(buf)

        cap_y = int(CANVAS_H * 0.28) if is_vertical else int(CANVAS_H * 0.39)
        cap_w = int(CANVAS_W * (0.86 if is_vertical else 0.72))
        cap_fs = 50 if is_vertical else 42
        for c_idx, ch_words in enumerate(chunks):
            cs_f = int(round((ch_words[0]["start_ms"] / 1000.0) * FPS))
            ce_f = max(cs_f + 6, int(round((ch_words[-1]["end_ms"] / 1000.0) * FPS)))
            cdur = ce_f - cs_f
            ctxt = " ".join(str(x["word"]) for x in ch_words).strip()
            if not ctxt:
                continue
            cid = det_uid(f"{project_id}_cap_{c_idx}")
            items.append(
                {
                    "id": cid,
                    "trackId": "track_captions",
                    "from": cs_f,
                    "durationInFrames": cdur,
                    "label": f"cap_{c_idx+1}",
                    "type": "text",
                    "text": ctxt,
                    "fontSize": cap_fs,
                    "fontFamily": "Plus Jakarta Sans",
                    "fontWeight": "bold",
                    "color": "#FFFFFF",
                    "textAlign": "center",
                    "verticalAlign": "middle",
                    "lineHeight": 1.15,
                    "letterSpacing": -0.5,
                    "transform": {"x": 0, "y": cap_y, "width": cap_w, "height": 130, "scaleX": 1.0, "scaleY": 1.0, "rotation": 0.0},
                    "stroke": {"width": 4, "color": "rgba(0,0,0,0.88)"},
                    "textShadow": {"offsetX": 0, "offsetY": 4, "blur": 14, "color": "rgba(0,0,0,0.85)"},
                    "textMotion": build_text_motion("pop", None, cdur),
                    "originId": cid,
                }
            )

    # 4. Write `<SafeTitle>.freecut.zip` + `freecut_workspace/`
    now_ms = int(time.time() * 1000)
    project_json = {
        "id": project_id,
        "name": safe_title,
        "description": f"Human-Grade Documentary Timeline — {title}",
        "createdAt": now_ms,
        "updatedAt": now_ms,
        "duration": round(total_dur_ms / 1000.0, 3),
        "metadata": {
            "width": CANVAS_W,
            "height": CANVAS_H,
            "fps": FPS,
            "backgroundColor": "#0B0E14",
        },
        "timeline": {
            "tracks": TRACKS,
            "items": items,
            "transitions": transitions_list,
            "keyframes": all_keyframes,
        },
        "schemaVersion": 15,
    }

    manifest = {
        "version": "1.0",
        "createdAt": now_ms,
        "editorVersion": "1.0.0",
        "projectId": project_id,
        "projectName": safe_title,
        "media": manifest_media,
        "checksum": "",
    }
    manifest["checksum"] = hashlib.sha256(
        json.dumps(manifest, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()

    output_zip = os.path.join(project_dir, f"{safe_title}.freecut.zip")
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("project.json", json.dumps(project_json, indent=2, ensure_ascii=False))
        zf.writestr("manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
        for src_path, zip_rel in media_files_to_zip:
            zf.write(src_path, zip_rel)

    # Build directly openable `freecut_workspace/`
    workspace_dir = os.path.join(project_dir, "freecut_workspace")
    if os.path.exists(workspace_dir):
        shutil.rmtree(workspace_dir, ignore_errors=True)
    ws_proj_dir = os.path.join(workspace_dir, "projects", project_id)
    os.makedirs(ws_proj_dir, exist_ok=True)

    with open(os.path.join(workspace_dir, ".freecut-workspace.json"), "w", encoding="utf-8") as f:
        json.dump({"schemaVersion": "2.0", "createdAt": now_ms}, f, indent=2, ensure_ascii=False)

    with open(os.path.join(workspace_dir, "index.json"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "version": "1.0",
                "updatedAt": now_ms,
                "projects": [{"id": project_id, "name": safe_title, "updatedAt": now_ms}],
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    ws_items = []
    for it in items:
        wit = dict(it)
        if "mediaRef" in wit:
            wit["mediaId"] = wit.pop("mediaRef")
        ws_items.append(wit)

    ws_project = json.loads(json.dumps(project_json))
    ws_project["timeline"]["items"] = ws_items
    with open(os.path.join(ws_proj_dir, "project.json"), "w", encoding="utf-8") as f:
        json.dump(ws_project, f, indent=2, ensure_ascii=False)

    for entry in manifest_media:
        mid = entry["originalId"]
        mdir = os.path.join(workspace_dir, "media", mid)
        os.makedirs(mdir, exist_ok=True)
        meta_doc = {
            "id": mid,
            "storageType": "workspace",
            "fileName": entry["fileName"],
            "fileSize": entry["fileSize"],
            "mimeType": entry["mimeType"],
            "contentHash": entry["sha256"],
            "duration": entry["metadata"]["duration"],
            "width": entry["metadata"]["width"],
            "height": entry["metadata"]["height"],
            "fps": entry["metadata"]["fps"],
            "codec": entry["metadata"]["codec"],
            "bitrate": 0,
            "tags": [],
            "createdAt": now_ms,
            "updatedAt": now_ms,
        }
        with open(os.path.join(mdir, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(meta_doc, f, indent=2, ensure_ascii=False)
        src_p = media_id_to_filepath[mid]
        shutil.copy2(src_p, os.path.join(mdir, entry["fileName"]))

    with open(os.path.join(ws_proj_dir, "media-links.json"), "w", encoding="utf-8") as f:
        json.dump(
            {"version": "1.0", "mediaIds": [{"id": e["originalId"], "addedAt": now_ms} for e in manifest_media]},
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"[assemble_freecut] OK -> Workspace: {workspace_dir}")
    print(f"[assemble_freecut] OK -> Bundle   : {output_zip} ({os.path.getsize(output_zip) // 1024} KB)")
    return workspace_dir, output_zip


def main():
    ap = argparse.ArgumentParser(description="Compile FreeCut workspace & .freecut.zip v6 (Multi-Format, Zero Card Vices)")
    ap.add_argument("--project-dir", required=True, help="Path to documentary/video project folder")
    ap.add_argument("--captions", action="store_true", help="Force dynamic word-aligned subtitles on track_captions")
    args = ap.parse_args()
    assemble_project(args.project_dir, force_captions=args.captions)


if __name__ == "__main__":
    main()
