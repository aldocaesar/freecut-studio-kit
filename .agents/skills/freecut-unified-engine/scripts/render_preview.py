#!/usr/bin/env python3
"""
render_preview.py — Direct MP4 Renderer for FreeCut v15 Workspaces (v6.2)
=========================================================================
Renders any `<project_dir>/freecut_workspace` directly to a playable 1080p30 H.264 + AAC `.mp4`
without needing to open a browser, faithfully compositing:
  - `track_bg` & `track_anchor` (images + videos + Ken Burns keyframes + crossfade transitions)
  - `track_fg_1` (optical vignette grade)
  - `track_fg_2` (RGBA cutouts with soft Gaussian drop shadows & parallax keyframes)
  - `track_fg_3` (Lottie vector lower-thirds, underlines, marker highlights & corner brackets)
  - `track_text` & `track_captions` (wrapped typography, stroke, shadow & entry/exit animations)
  - `track_audio`, `track_sfx`, `track_bgm` (exact frame offsets & dB/linear gain mixing)
"""
import argparse
import glob
import json
import math
import os
import subprocess
import sys
import tempfile
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


def _find_project_json(workspace_or_proj: str) -> Tuple[str, str]:
    p = os.path.abspath(workspace_or_proj)
    if os.path.isfile(p) and p.endswith(".json"):
        ws = os.path.abspath(os.path.join(os.path.dirname(p), "..", ".."))
        return ws, p
    ws = os.path.join(p, "freecut_workspace") if os.path.isdir(os.path.join(p, "freecut_workspace")) else p
    matches = glob.glob(os.path.join(ws, "projects", "*", "project.json"))
    if not matches:
        raise FileNotFoundError(f"No project.json found inside {ws}")
    matches.sort(key=os.path.getmtime, reverse=True)
    return ws, matches[0]


def _resolve_media_map(ws_dir: str) -> Dict[str, str]:
    media_root = os.path.join(ws_dir, "media")
    out: Dict[str, str] = {}
    if not os.path.isdir(media_root):
        return out
    for mid in os.listdir(media_root):
        mdir = os.path.join(media_root, mid)
        if not os.path.isdir(mdir):
            continue
        for fn in os.listdir(mdir):
            if fn == "metadata.json":
                continue
            fp = os.path.join(mdir, fn)
            if os.path.isfile(fp):
                out[mid] = fp
                break
    return out


def _ease(t: float, mode: str) -> float:
    t = max(0.0, min(1.0, t))
    m = (mode or "linear").lower()
    if m == "ease-out":
        return 1.0 - (1.0 - t) ** 2.2
    if m == "ease-in":
        return t ** 2.2
    if m == "ease-in-out":
        return 3 * t * t - 2 * t * t * t
    return t


def _eval_kfs(kfs: List[Dict[str, Any]], local_frame: float, default_val: float) -> float:
    if not kfs:
        return default_val
    if local_frame <= kfs[0]["frame"]:
        return float(kfs[0]["value"])
    if local_frame >= kfs[-1]["frame"]:
        return float(kfs[-1]["value"])
    for i in range(len(kfs) - 1):
        k0, k1 = kfs[i], kfs[i + 1]
        f0, f1 = float(k0["frame"]), float(k1["frame"])
        if f0 <= local_frame <= f1:
            span = max(1e-6, f1 - f0)
            u = _ease((local_frame - f0) / span, k0.get("easing", "linear"))
            return float(k0["value"]) + (float(k1["value"]) - float(k0["value"])) * u
    return float(kfs[-1]["value"])


def _parse_rgba(color_str: str, default=(255, 255, 255, 255)) -> Tuple[int, int, int, int]:
    if not color_str:
        return default
    s = color_str.strip()
    if s.startswith("#"):
        h = s[1:]
        if len(h) == 6:
            return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255
        if len(h) == 8:
            return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(h[6:8], 16)
    if s.startswith("rgba") or s.startswith("rgb"):
        nums = s[s.find("(") + 1 : s.rfind(")")].split(",")
        r, g, b = int(float(nums[0])), int(float(nums[1])), int(float(nums[2]))
        a = int(round(float(nums[3]) * 255)) if len(nums) > 3 else 255
        return r, g, b, max(0, min(255, a))
    return default


def _load_editorial_font(family: str, size: int, weight: str = "bold", style: str = "normal") -> ImageFont.FreeTypeFont:
    fam = (family or "Inter").lower()
    is_italic = (style or "").lower() == "italic"
    is_bold = (weight or "bold").lower() in ("bold", "semibold")

    if any(k in fam for k in ("playfair", "serif", "baskerville", "cormorant", "merriweather")):
        if is_bold and is_italic:
            cands = [r"C:\Windows\Fonts\georgiaz.ttf", r"C:\Windows\Fonts\timesbi.ttf", r"C:\Windows\Fonts\georgiab.ttf"]
        elif is_italic:
            cands = [r"C:\Windows\Fonts\georgiai.ttf", r"C:\Windows\Fonts\timesi.ttf", r"C:\Windows\Fonts\georgia.ttf"]
        elif is_bold:
            cands = [r"C:\Windows\Fonts\georgiab.ttf", r"C:\Windows\Fonts\timesbd.ttf"]
        else:
            cands = [r"C:\Windows\Fonts\georgia.ttf", r"C:\Windows\Fonts\times.ttf"]
    elif any(k in fam for k in ("mono", "code", "inconsolata")):
        cands = [r"C:\Windows\Fonts\consolab.ttf", r"C:\Windows\Fonts\consola.ttf", r"C:\Windows\Fonts\courbd.ttf"]
    elif any(k in fam for k in ("bebas", "anton", "oswald", "archivo black", "barlow condensed")):
        cands = [r"C:\Windows\Fonts\impact.ttf", r"C:\Windows\Fonts\bahnschrift.ttf", r"C:\Windows\Fonts\arialbd.ttf"]
    elif any(k in fam for k in ("bricolage", "space grotesk")):
        cands = [r"C:\Windows\Fonts\trebucbd.ttf", r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\arialbd.ttf"]
    else:
        cands = (
            [r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\Montserrat-Bold.ttf", r"C:\Windows\Fonts\arialbd.ttf"]
            if is_bold
            else [r"C:\Windows\Fonts\segoeui.ttf", r"C:\Windows\Fonts\arial.ttf"]
        )

    cands += [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf" if is_italic else "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Georgia Bold Italic.ttf" if is_italic else "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ]
    for fp in cands:
        if os.path.isfile(fp):
            try:
                return ImageFont.truetype(fp, max(12, int(size)))
            except Exception:
                pass
    return ImageFont.load_default()


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_w: int) -> List[str]:
    out_lines: List[str] = []
    for para in (text or "").splitlines():
        words = para.split()
        if not words:
            out_lines.append("")
            continue
        cur = words[0]
        for w in words[1:]:
            test = f"{cur} {w}"
            bbox = draw.textbbox((0, 0), test, font=font)
            if (bbox[2] - bbox[0]) <= max_w:
                cur = test
            else:
                out_lines.append(cur)
                cur = w
        out_lines.append(cur)
    return out_lines


def _prerender_text_item(item: Dict[str, Any]) -> np.ndarray:
    tr = item.get("transform", {})
    box_w = max(64, int(tr.get("width", 800)))
    box_h = max(48, int(tr.get("height", 200)))
    pad = 48
    img = Image.new("RGBA", (box_w + pad * 2, box_h + pad * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    base_fsize = int(item.get("fontSize", 42))
    base_fam = item.get("fontFamily", "Inter")
    base_weight = item.get("fontWeight", "bold")
    base_style = item.get("fontStyle", "normal")
    base_col = item.get("color", "#FFFFFF")
    lh_mult = float(item.get("lineHeight", 1.18))

    spans = item.get("textSpans")
    if spans and isinstance(spans, list):
        # Build visual wrapped lines per span paragraph
        styled_lines: List[Tuple[str, ImageFont.FreeTypeFont, Tuple[int, int, int, int], int]] = []
        for sp in spans:
            sp_txt = str(sp.get("text", ""))
            if not sp_txt:
                continue
            sfsize = int(sp.get("fontSize", base_fsize))
            sfont = _load_editorial_font(
                sp.get("fontFamily", base_fam),
                sfsize,
                sp.get("fontWeight", base_weight),
                sp.get("fontStyle", base_style),
            )
            scol = _parse_rgba(sp.get("color", base_col))
            slh = int(round(sfsize * (1.35 if sfsize <= 24 else lh_mult)))
            cleaned = sp_txt.rstrip("\n")
            wrapped = _wrap_text(draw, cleaned, sfont, box_w)
            for wln in wrapped:
                if wln or len(wrapped) == 1:
                    styled_lines.append((wln, sfont, scol, slh))
    else:
        sfont = _load_editorial_font(base_fam, base_fsize, base_weight, base_style)
        scol = _parse_rgba(base_col)
        slh = int(round(base_fsize * lh_mult))
        styled_lines = [(ln, sfont, scol, slh) for ln in _wrap_text(draw, item.get("text", ""), sfont, box_w)]

    total_h = max(24, sum(x[3] for x in styled_lines))
    valign = item.get("verticalAlign", "middle")
    if valign == "top":
        start_y = pad
    elif valign == "bottom":
        start_y = pad + max(0, box_h - total_h)
    else:
        start_y = pad + (box_h - total_h) // 2

    align = item.get("textAlign", "left")
    stroke_cfg = item.get("stroke") or {}
    stroke_w = int(stroke_cfg.get("width", 0))
    stroke_rgba = _parse_rgba(stroke_cfg.get("color", "rgba(0,0,0,0.75)")) if stroke_w > 0 else None

    sh = item.get("textShadow")
    if sh and int(sh.get("blur", 0)) > 0:
        sh_img = Image.new("RGBA", img.size, (0, 0, 0, 0))
        sh_draw = ImageDraw.Draw(sh_img)
        sh_rgba = _parse_rgba(sh.get("color", "rgba(0,0,0,0.85)"))
        ox, oy = int(sh.get("offsetX", 0)), int(sh.get("offsetY", 4))
        cy = start_y
        for ln, lfont, _, llh in styled_lines:
            bbox = sh_draw.textbbox((0, 0), ln, font=lfont)
            lw = bbox[2] - bbox[0]
            lx = (pad + (box_w - lw) // 2) if align == "center" else ((pad + box_w - lw) if align == "right" else pad)
            sh_draw.text((lx + ox, cy + oy), ln, font=lfont, fill=sh_rgba)
            cy += llh
        blur_r = max(1, min(16, int(sh.get("blur", 12)) // 2))
        sh_img = sh_img.filter(ImageFilter.GaussianBlur(radius=blur_r))
        img = Image.alpha_composite(img, sh_img)
        draw = ImageDraw.Draw(img)

    cy = start_y
    for ln, lfont, lcol, llh in styled_lines:
        bbox = draw.textbbox((0, 0), ln, font=lfont)
        lw = bbox[2] - bbox[0]
        lx = (pad + (box_w - lw) // 2) if align == "center" else ((pad + box_w - lw) if align == "right" else pad)
        draw.text(
            (lx, cy),
            ln,
            font=lfont,
            fill=lcol,
            stroke_width=stroke_w,
            stroke_fill=stroke_rgba if stroke_w > 0 else None,
        )
        cy += llh

    arr = np.array(img, dtype=np.uint8)
    return arr[:, :, [2, 1, 0, 3]]


def _add_drop_shadow_bgra(bgra: np.ndarray, shadow_cfg: Optional[Dict[str, Any]]) -> Tuple[np.ndarray, int]:
    if not shadow_cfg or bgra.shape[2] < 4:
        return bgra, 0
    blur = max(2, min(28, int(shadow_cfg.get("blur", 28)) // 2))
    ox = int(shadow_cfg.get("offsetX", 0))
    oy = int(shadow_cfg.get("offsetY", 14))
    pad = blur * 2 + max(abs(ox), abs(oy)) + 6
    h, w = bgra.shape[:2]
    rgba = bgra[:, :, [2, 1, 0, 3]]
    pil_fg = Image.fromarray(rgba)
    alpha = pil_fg.split()[3]
    r, g, b, a_col = _parse_rgba(shadow_cfg.get("color", "rgba(0,0,0,0.68)"))

    sh_canvas = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    sh_alpha = alpha.point(lambda p: int(p * (a_col / 255.0)))
    solid = Image.new("RGBA", (w, h), (r, g, b, 255))
    sh_canvas.paste(solid, (pad + ox, pad + oy), sh_alpha)
    sh_canvas = sh_canvas.filter(ImageFilter.GaussianBlur(radius=blur))
    sh_canvas.alpha_composite(pil_fg, (pad, pad))
    out = np.array(sh_canvas, dtype=np.uint8)[:, :, [2, 1, 0, 3]]
    return out, pad


def _render_lottie_frame(lottie_data: Dict[str, Any], local_frame: int, dur_frames: int) -> Optional[np.ndarray]:
    nm = (lottie_data.get("nm") or "").lower()
    w = int(lottie_data.get("w", 1920))
    h = int(lottie_data.get("h", 1080))
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    fade_in = min(1.0, local_frame / 6.0)
    fade_out = min(1.0, max(0.0, (dur_frames - local_frame) / 8.0))
    op = fade_in * fade_out
    if op <= 0.01:
        return None

    if "lower_third" in nm or "minimal" in nm:
        prog = _ease(min(1.0, local_frame / 16.0), "ease-out")
        bw = max(4, int(720 * prog))
        draw.rounded_rectangle([96, 881, 96 + bw, 963], radius=8, fill=(16, 21, 30, int(198 * op)))
        ph = max(2, int(76 * _ease(min(1.0, local_frame / 12.0), "ease-out")))
        py0 = 922 - ph // 2
        draw.rounded_rectangle([96, py0, 101, py0 + ph], radius=2, fill=(200, 75, 49, int(255 * op)))
    elif "underline" in nm or "marker" in nm:
        prog = _ease(min(1.0, local_frame / 18.0), "ease-out")
        x0 = int(w * 0.08)
        x1 = x0 + max(4, int((w * 0.84) * prog))
        cy = h // 2
        if "marker" in nm:
            draw.rounded_rectangle([x0, cy - 18, x1, cy + 18], radius=4, fill=(250, 204, 21, int(110 * op)))
        else:
            pts = []
            steps = max(4, (x1 - x0) // 12)
            for s in range(steps + 1):
                u = s / max(1, steps)
                px = x0 + (x1 - x0) * u
                py = cy + math.sin(u * math.pi) * (-5.0)
                pts.append((px, py))
            if len(pts) >= 2:
                draw.line(pts, fill=(200, 75, 49, int(245 * op)), width=6)
    elif "bracket" in nm or "focus" in nm:
        pad = 20
        ln = 34
        col = (245, 158, 11, int(235 * op))
        for (bx, by, sx, sy) in [
            (pad, pad, 1, 1),
            (w - pad, pad, -1, 1),
            (pad, h - pad, 1, -1),
            (w - pad, h - pad, -1, -1),
        ]:
            draw.line([(bx, by), (bx + sx * ln, by)], fill=col, width=5)
            draw.line([(bx, by), (bx, by + sy * ln)], fill=col, width=5)
    else:
        return None

    arr = np.array(img, dtype=np.uint8)
    return arr[:, :, [2, 1, 0, 3]]


def _blend_bgr_or_bgra(canvas: np.ndarray, src: np.ndarray, cx: float, cy: float, target_w: int, target_h: int, opacity: float):
    if opacity <= 0.005 or target_w < 2 or target_h < 2:
        return
    ch, cw = canvas.shape[:2]
    resized = cv2.resize(src, (target_w, target_h), interpolation=cv2.INTER_LINEAR)
    x0 = int(round(cx - target_w / 2.0))
    y0 = int(round(cy - target_h / 2.0))

    sx0 = max(0, -x0)
    sy0 = max(0, -y0)
    dx0 = max(0, x0)
    dy0 = max(0, y0)
    copy_w = min(target_w - sx0, cw - dx0)
    copy_h = min(target_h - sy0, ch - dy0)
    if copy_w <= 0 or copy_h <= 0:
        return

    patch = resized[sy0 : sy0 + copy_h, sx0 : sx0 + copy_w]
    roi = canvas[dy0 : dy0 + copy_h, dx0 : dx0 + copy_w]

    if patch.shape[2] == 4:
        alpha = (patch[:, :, 3:4].astype(np.float32) / 255.0) * float(opacity)
        fg_bgr = patch[:, :, :3].astype(np.float32)
        bg_bgr = roi.astype(np.float32)
        canvas[dy0 : dy0 + copy_h, dx0 : dx0 + copy_w] = (fg_bgr * alpha + bg_bgr * (1.0 - alpha)).astype(np.uint8)
    else:
        if opacity >= 0.999:
            canvas[dy0 : dy0 + copy_h, dx0 : dx0 + copy_w] = patch
        else:
            canvas[dy0 : dy0 + copy_h, dx0 : dx0 + copy_w] = cv2.addWeighted(
                patch, float(opacity), roi, 1.0 - float(opacity), 0.0
            )


def _build_mixed_audio(pj: Dict[str, Any], media_map: Dict[str, str], fps: int, dur_sec: float, out_wav: str):
    audio_items = [
        it for it in pj["timeline"]["items"]
        if it.get("type") == "audio" and it.get("mediaId") in media_map
    ]
    if not audio_items:
        subprocess.run(
            ["ffmpeg", "-nostdin", "-y", "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo:d={dur_sec:.3f}", out_wav],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=True,
        )
        return

    cmd = ["ffmpeg", "-nostdin", "-y"]
    filter_parts = []
    mix_labels = []
    for idx, it in enumerate(audio_items):
        fp = media_map[it["mediaId"]]
        cmd += ["-i", fp]
        start_sec = float(it.get("sourceStart", 0.0))
        clip_dur = float(it.get("durationInFrames", 30)) / float(fps)
        delay_ms = max(0, int(round((float(it.get("from", 0)) / float(fps)) * 1000.0)))
        vol_raw = float(it.get("volume", 1.0))
        # Negative values in FreeCut schema v15 are dB (e.g. -24.0 dB for SFX/BGM); positive <= 2.0 are linear gain
        vol_expr = f"{vol_raw}dB" if vol_raw < 0 else f"{vol_raw:.4f}"
        lbl = f"a{idx}"
        filter_parts.append(
            f"[{idx}:a]atrim=start={start_sec:.4f}:duration={clip_dur:.4f},asetpts=PTS-STARTPTS,"
            f"aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo,"
            f"volume={vol_expr},adelay={delay_ms}|{delay_ms}[{lbl}]"
        )
        mix_labels.append(f"[{lbl}]")

    amix = f"{''.join(mix_labels)}amix=inputs={len(mix_labels)}:duration=longest:dropout_transition=0:normalize=0,alimiter=limit=0.96[aout]"
    filter_parts.append(amix)
    cmd += [
        "-filter_complex", ";".join(filter_parts),
        "-map", "[aout]",
        "-t", f"{dur_sec:.3f}",
        "-ar", "44100",
        "-ac", "2",
        "-c:a", "pcm_s16le",
        out_wav,
    ]
    res = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Audio mix failed: {res.stderr[-500:]}")


def render_workspace_to_mp4(workspace_or_proj: str, out_mp4: str, scale: float = 1.0) -> str:
    ws_dir, pj_path = _find_project_json(workspace_or_proj)
    pj = json.load(open(pj_path, "r", encoding="utf-8"))
    media_map = _resolve_media_map(ws_dir)

    meta = pj.get("metadata", {})
    W = int(round(int(meta.get("width", 1920)) * scale))
    H = int(round(int(meta.get("height", 1080)) * scale))
    W -= W % 2
    H -= H % 2
    orig_W = int(meta.get("width", 1920))
    orig_H = int(meta.get("height", 1080))
    sx_canvas = W / float(orig_W)
    sy_canvas = H / float(orig_H)

    fps = int(meta.get("fps", 30))
    dur_sec = float(pj.get("duration", 60.0))
    total_frames = max(1, int(round(dur_sec * fps)))
    bg_rgb = _parse_rgba(meta.get("backgroundColor", "#0B0E14"))
    bg_bgr = np.array([bg_rgb[2], bg_rgb[1], bg_rgb[0]], dtype=np.uint8)

    tracks = pj["timeline"]["tracks"]
    track_order = {t["id"]: int(t.get("order", 0)) for t in tracks if t.get("visible", True) and not t.get("muted", False)}

    kf_map: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    for entry in pj["timeline"].get("keyframes", []):
        props = {}
        for p in entry.get("properties", []):
            klist = sorted(p.get("keyframes", []), key=lambda k: k["frame"])
            props[p["property"]] = klist
        kf_map[entry["itemId"]] = props

    # Transitions lookup (crossfade overlap on rightClip entrance)
    items_by_id = {it["id"]: it for it in pj["timeline"]["items"]}
    crossfade_in: Dict[str, Tuple[str, int]] = {}
    for tr in pj["timeline"].get("transitions", []):
        rc = tr.get("rightClipId")
        lc = tr.get("leftClipId")
        dur_tr = int(tr.get("durationInFrames", 12))
        if rc in items_by_id and lc in items_by_id:
            crossfade_in[rc] = (lc, dur_tr)

    # Preload static images, text bitmaps, Lottie JSONs, and open video captures
    img_cache: Dict[str, Tuple[np.ndarray, int, float, float]] = {}
    text_cache: Dict[str, Tuple[np.ndarray, int]] = {}
    lottie_cache: Dict[str, Dict[str, Any]] = {}
    vid_caps: Dict[str, Tuple[cv2.VideoCapture, int]] = {}

    visual_items = [
        it for it in pj["timeline"]["items"]
        if it.get("trackId") in track_order and it.get("type") in ("image", "video", "text", "lottie", "adjustment")
    ]
    # Sort bottom-to-top (higher `order` = deeper background track)
    visual_items.sort(key=lambda it: (-track_order.get(it["trackId"], 0), it.get("from", 0)))

    for it in visual_items:
        itype = it["type"]
        iid = it["id"]
        mid = it.get("mediaId")
        if itype == "image" and mid in media_map:
            raw = cv2.imread(media_map[mid], cv2.IMREAD_UNCHANGED)
            if raw is not None:
                orig_h, orig_w = raw.shape[:2]
                rot_deg = float((it.get("transform") or {}).get("rotation", 0.0) or 0.0)
                if raw.shape[2] == 4:
                    if abs(rot_deg) > 0.05:
                        rgba_pil = Image.fromarray(raw[:, :, [2, 1, 0, 3]]).rotate(-rot_deg, resample=Image.Resampling.BICUBIC, expand=True)
                        raw = np.array(rgba_pil, dtype=np.uint8)[:, :, [2, 1, 0, 3]]
                        orig_h, orig_w = raw.shape[:2]
                    shadow_cfg = (it.get("transform") or {}).get("dropShadow")
                    padded, pad_px = _add_drop_shadow_bgra(raw, shadow_cfg)
                    img_cache[iid] = (padded, pad_px, float(orig_w), float(orig_h))
                else:
                    img_cache[iid] = (raw, 0, float(orig_w), float(orig_h))
        elif itype == "text":
            text_cache[iid] = (_prerender_text_item(it), 48)
        elif itype == "lottie" and mid in media_map:
            try:
                lottie_cache[iid] = json.load(open(media_map[mid], "r", encoding="utf-8"))
            except Exception:
                pass
        elif itype == "video" and mid in media_map:
            cap = cv2.VideoCapture(media_map[mid])
            vid_caps[iid] = (cap, -1)

    # Precompute smooth optical vignette multiplier
    yy, xx = np.ogrid[:H, :W]
    nx = (xx - W / 2.0) / (W / 2.0)
    ny = (yy - H / 2.0) / (H / 2.0)
    rad2 = nx * nx + ny * ny
    vignette_mask = np.clip(1.0 - 0.24 * np.clip(rad2 - 0.25, 0.0, 2.0), 0.58, 1.0).astype(np.float32)[:, :, None]

    os.makedirs(os.path.dirname(os.path.abspath(out_mp4)), exist_ok=True)
    fd, tmp_wav = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    fd_err, tmp_err = tempfile.mkstemp(suffix=".log")
    os.close(fd_err)

    err_fh = None
    try:
        print(f"[render_preview] Mixing audio tracks ({dur_sec:.2f}s)...", flush=True)
        _build_mixed_audio(pj, media_map, fps, dur_sec, tmp_wav)

        ff_cmd = [
            "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
            "-i", tmp_wav,
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            out_mp4,
        ]
        err_fh = open(tmp_err, "wb")
        proc = subprocess.Popen(ff_cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=err_fh)

        def _draw_single_item(canvas: np.ndarray, it: Dict[str, Any], gframe: int, extra_alpha: float = 1.0):
            iid = it["id"]
            itype = it["type"]
            local_f = gframe - int(it["from"])
            dur_f = max(1, int(it["durationInFrames"]))
            tr = it.get("transform") or {}
            kfs = kf_map.get(iid, {})

            x = _eval_kfs(kfs.get("x", []), local_f, float(tr.get("x", 0.0)))
            y = _eval_kfs(kfs.get("y", []), local_f, float(tr.get("y", 0.0)))
            w = _eval_kfs(kfs.get("width", []), local_f, float(tr.get("width", orig_W)))
            h = _eval_kfs(kfs.get("height", []), local_f, float(tr.get("height", orig_H)))
            scx = _eval_kfs(kfs.get("scaleX", []), local_f, float(tr.get("scaleX", 1.0)))
            scy = _eval_kfs(kfs.get("scaleY", []), local_f, float(tr.get("scaleY", 1.0)))
            op = _eval_kfs(kfs.get("opacity", []), local_f, float(it.get("opacity", 1.0))) * extra_alpha

            # Evaluate FreeCut native `motionModifiers` (`Clipe Motion`)
            for mod in it.get("motionModifiers") or []:
                if not mod.get("enabled", True):
                    continue
                mtype = mod.get("type", "")
                amp = float(mod.get("amplitude", 0.25))
                freq = float(mod.get("frequency", 0.20))
                phase = float(mod.get("phaseFrames", 0))
                t_rad = 2.0 * math.pi * freq * ((local_f + phase) / float(fps))
                if mtype == "float-drift":
                    y += math.sin(t_rad) * (10.0 * amp)
                    x += math.cos(t_rad * 0.7) * (5.0 * amp)
                elif mtype == "sway":
                    x += math.sin(t_rad) * (8.0 * amp)
                elif mtype == "breath-pulse":
                    pulse = 1.0 + math.sin(t_rad) * (0.025 * amp)
                    scx *= pulse
                    scy *= pulse

            if itype == "adjustment":
                canvas[:] = (canvas.astype(np.float32) * vignette_mask).astype(np.uint8)
                return

            if itype == "text" and iid in text_cache:
                tm = it.get("textMotion") or {}
                in_m = tm.get("in") or {}
                out_m = tm.get("out") or {}
                loop_m = tm.get("loop") or {}
                reveal_x_frac = 1.0

                if in_m:
                    pid = in_m.get("presetId", "fade-up")
                    in_total = 18 if pid == "typewriter" else max(6, int(in_m.get("durationFrames", 12)) + int(in_m.get("staggerFrames", 2)) * 2)
                    if local_f < in_total:
                        u = _ease(local_f / float(in_total), in_m.get("easing", "ease-out"))
                        if pid == "typewriter":
                            reveal_x_frac = max(0.04, u)
                        elif pid in ("fade-up", "rise", "slide-mask", "cascade"):
                            op *= u
                            y += (1.0 - u) * 26.0
                        elif pid == "pop":
                            op *= u
                            scx *= 0.88 + 0.12 * u
                            scy *= 0.88 + 0.12 * u
                        else:
                            op *= u

                if out_m:
                    out_total = max(6, int(out_m.get("durationFrames", 10)) + 4)
                    if local_f > dur_f - out_total:
                        u = _ease(max(0.0, (dur_f - local_f) / float(out_total)), "ease-in")
                        op *= u
                        if out_m.get("presetId") in ("fade-down", "sink"):
                            y += (1.0 - u) * 16.0

                if loop_m and loop_m.get("presetId") == "pulse":
                    lp_d = max(20, int(loop_m.get("durationFrames", 42)))
                    lp = 1.0 + math.sin(2.0 * math.pi * (local_f / float(lp_d))) * 0.018
                    scx *= lp
                    scy *= lp

                bmp, pad_px = text_cache[iid]
                if reveal_x_frac < 0.999:
                    bmp = bmp.copy()
                    cut_col = max(1, int(bmp.shape[1] * reveal_x_frac))
                    bmp[:, cut_col:, 3] = 0
                tw = int(round((w + pad_px * 2) * scx * sx_canvas))
                th = int(round((h + pad_px * 2) * scy * sy_canvas))
                cx = (orig_W / 2.0 + x) * sx_canvas
                cy = (orig_H / 2.0 + y) * sy_canvas
                _blend_bgr_or_bgra(canvas, bmp, cx, cy, tw, th, op)
                return

            if itype == "image" and iid in img_cache:
                arr, pad_px, ow, oh = img_cache[iid]
                scale_w = w / max(1.0, ow)
                scale_h = h / max(1.0, oh)
                tw = int(round((w + pad_px * 2 * scale_w) * scx * sx_canvas))
                th = int(round((h + pad_px * 2 * scale_h) * scy * sy_canvas))
                cx = (orig_W / 2.0 + x) * sx_canvas
                cy = (orig_H / 2.0 + y) * sy_canvas
                _blend_bgr_or_bgra(canvas, arr, cx, cy, tw, th, op)
                return

            if itype == "video" and iid in vid_caps:
                cap, last_idx = vid_caps[iid]
                target_idx = max(0, int(it.get("sourceStart", 0)) + max(0, local_f))
                if target_idx != last_idx + 1:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, target_idx)
                ok, vframe = cap.read()
                if not ok:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, target_idx - 1))
                    ok, vframe = cap.read()
                if ok and vframe is not None:
                    vid_caps[iid] = (cap, target_idx)
                    tw = int(round(w * scx * sx_canvas))
                    th = int(round(h * scy * sy_canvas))
                    cx = (orig_W / 2.0 + x) * sx_canvas
                    cy = (orig_H / 2.0 + y) * sy_canvas
                    _blend_bgr_or_bgra(canvas, vframe, cx, cy, tw, th, op)
                return

            if itype == "lottie" and iid in lottie_cache:
                l_arr = _render_lottie_frame(lottie_cache[iid], max(0, local_f), dur_f)
                if l_arr is not None:
                    tw = int(round(w * scx * sx_canvas))
                    th = int(round(h * scy * sy_canvas))
                    cx = (orig_W / 2.0 + x) * sx_canvas
                    cy = (orig_H / 2.0 + y) * sy_canvas
                    _blend_bgr_or_bgra(canvas, l_arr, cx, cy, tw, th, op)

        print(f"[render_preview] Rendering {total_frames} frames ({W}x{H} @ {fps}fps) -> {out_mp4}")
        for gf in range(total_frames):
            frame_bgr = np.empty((H, W, 3), dtype=np.uint8)
            frame_bgr[:] = bg_bgr

            for it in visual_items:
                f0 = int(it["from"])
                f1 = f0 + int(it["durationInFrames"])
                if not (f0 <= gf < f1):
                    continue
                iid = it["id"]
                if iid in crossfade_in:
                    left_id, tr_dur = crossfade_in[iid]
                    rel = gf - f0
                    if 0 <= rel < tr_dur and left_id in items_by_id:
                        left_it = items_by_id[left_id]
                        alpha_r = (rel + 1) / float(tr_dur + 1)
                        _draw_single_item(frame_bgr, left_it, min(gf, int(left_it["from"]) + int(left_it["durationInFrames"]) - 1), 1.0)
                        _draw_single_item(frame_bgr, it, gf, alpha_r)
                        continue
                _draw_single_item(frame_bgr, it, gf, 1.0)

            proc.stdin.write(frame_bgr.tobytes())
            if gf > 0 and gf % 450 == 0:
                print(f"  ... {gf}/{total_frames} frames ({(gf/total_frames)*100:.0f}%)", flush=True)

        proc.stdin.close()
        rc = proc.wait()
        if err_fh:
            err_fh.close()
            err_fh = None
        stderr_out = open(tmp_err, "r", encoding="utf-8", errors="ignore").read() if os.path.isfile(tmp_err) else ""
        if rc != 0 or not os.path.isfile(out_mp4):
            raise RuntimeError(f"FFmpeg MP4 encode failed (rc={rc}): {stderr_out[-600:]}")
    finally:
        if err_fh:
            try:
                err_fh.close()
            except Exception:
                pass
        for cap, _ in vid_caps.values():
            try:
                cap.release()
            except Exception:
                pass
        for tf in (tmp_wav, tmp_err):
            if os.path.isfile(tf):
                try:
                    os.remove(tf)
                except OSError:
                    pass

    sz_mb = os.path.getsize(out_mp4) / (1024 * 1024)
    print(f"[render_preview] DONE -> {out_mp4} ({sz_mb:.2f} MB)")
    return out_mp4


def main():
    ap = argparse.ArgumentParser(description="Render a FreeCut v15 workspace directly to a playable MP4 preview.")
    ap.add_argument("--project-dir", required=True, help="Project folder containing freecut_workspace/ (or workspace path)")
    ap.add_argument("--out", required=True, help="Output .mp4 path")
    ap.add_argument("--scale", type=float, default=1.0, help="Resolution scale (1.0 = full 1080p, 0.667 = 720p fast preview)")
    args = ap.parse_args()
    render_workspace_to_mp4(args.project_dir, args.out, scale=args.scale)


if __name__ == "__main__":
    main()
