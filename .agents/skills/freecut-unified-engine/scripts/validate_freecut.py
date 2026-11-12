#!/usr/bin/env python3
"""
validate_freecut.py (v7.1 — Strict Schema v15 + Workspace v2 Cold-Open Cache & Anti-Vício Auditor)
==================================================================================================
Audits `<project_dir>/freecut_workspace` AND `<project_dir>` editorial artifacts
against BOTH `walterlow/freecut` (`5ceeeb3`) schemaVersion 15 / Workspace v2 AND v7.1 quality gates:
  1. Multi-format canvas (`1920x1080`, `1080x1920`, `1080x1350`, `1080x1080`) @ 30fps.
  2. Zero-Rewrite Normalization Parity (`didNormalizationChange == false`):
     - Track `height == 100` (`DEFAULT_TRACK_HEIGHT`) + `kind in ("video", "audio")`
     - `animationVersion == 2` on 100% of keyframe entries
     - `0 <= transform.rotation < 360` and zero unintentional same-track overlaps
     - Integer frame `sourceStart/sourceEnd/sourceDuration` on both `video` and `audio` items
     - `mimeType == "application/lottie+json"` on all Lottie assets
  3. Instant Chrome Cold-Open Pre-Caches (Workspace v2):
     - `projects/<id>/thumbnail.jpg` (`> 0` bytes)
     - `media/<id>/thumbnail.jpg` (`> 0` bytes) on 100% of image & video assets
     - `media/<id>/cache/filmstrip/meta.json` (`version == 2`, `isComplete == true`) + `0.jpg..N.jpg` on 100% of videos
     - `media/<id>/cache/waveform/multi-res.bin` (`WFORM` v1 + 4 levels `[500, 100, 25, 10]`) on 100% of audio & video assets
  4. HARD ZERO-FREEZE, Sub-Shot Pacing (`<= 6.8s`), Monumental Word Fit, Press Highlighter Cap, & Motion Anti-Clone Gates.
"""
import argparse
import collections
import glob
import hashlib
import json
import math
import os
import re
import struct
import sys
import zipfile

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

VALID_RESOLUTIONS = {(1920, 1080), (1080, 1920), (1080, 1350), (1080, 1080)}
MAP_KEYWORDS = ("equador", "equator", "africa", "áfrica", "américa", "america", "oceano", "atlantic", "continent", "mapa", "world map")
LIGHT_PALETTE_MARKERS = (
    "warm_archive_paper",
    "editorial_blush_ivory",
    "swiss_emerald_ivory",
    "newsprint_crimson_ink",
    "terracotta_ochre_sand",
    "#f4ede1",
    "#fbf3f1",
    "#f1f6f3",
    "#eeeae2",
    "#f2e5d5",
    "#f6f2e8",
    "#faf8f4",
    "#fffdf8",
)


def _detect_motion_engine(raw_html: str) -> str:
    m = re.search(
        r"MotionKit\.(renderWorldAtlas|renderDataCurve|renderCameraJourney|renderOdometerCounter|renderUIFeed3D|renderDossierDesk|renderNetworkGraph|renderVersusSplit|renderWaffleScale|renderKineticManifesto)",
        raw_html,
    )
    if m:
        eng = m.group(1)
        if eng == "renderWorldAtlas" and "orthographic" in raw_html:
            return "renderWorldAtlas:orthographic"
        return eng
    return "custom_dom"


def audit_motion_scenes_v7(project_dir: str, errors: list, stats: dict):
    motion_dir = os.path.join(project_dir, "motion")
    if not os.path.isdir(motion_dir):
        return
    html_files = sorted(glob.glob(os.path.join(motion_dir, "*.html")))
    stats["motion_htmls"] = len(html_files)
    if not html_files:
        return

    cutout_motions = 0
    light_motions = 0
    prev_engine = None
    prev_file = None

    for html_p in html_files:
        bname = os.path.basename(html_p)
        raw = open(html_p, "r", encoding="utf-8", errors="ignore").read()
        low = raw.lower()

        uses_real_gis = (
            "world-atlas.js" in low
            or "world_atlas_geojson" in low
            or "renderworldatlas" in low
            or "maplibregl" in low
            or "d3.geo" in low
        )
        if not uses_real_gis and any(k in low for k in MAP_KEYWORDS) and re.search(r"<path[^>]+d=['\"]M\s*\d+[,\s]+\d+\s+L\s*\d+", raw):
            errors.append(
                f"Anti-Vício Map Failure in {bname}: hand-coded SVG polygon map detected! "
                "Use `world-atlas.js` + `MotionKit.renderWorldAtlas(...)` or `maplibregl`."
            )

        if "_cutout.png" in low or 'id="subject"' in low or "class=\"cutout" in low:
            cutout_motions += 1

        if any(tok in low for tok in LIGHT_PALETTE_MARKERS):
            light_motions += 1

        eng = _detect_motion_engine(raw)
        if eng != "custom_dom" and eng == prev_engine:
            errors.append(
                f"Anti-Vício Consecutive Motion Clone: {prev_file} and {bname} both use `{eng}` back-to-back!"
            )
        prev_engine = eng
        prev_file = bname

    stats["motion_light_palettes"] = light_motions
    stats["motion_cutouts"] = cutout_motions

    if len(html_files) >= 4:
        max_cut = max(2, int(math.floor(len(html_files) * 0.25)))
        if cutout_motions > max_cut:
            errors.append(
                f"Anti-Vício Motion Cutout Overuse: {cutout_motions}/{len(html_files)} motion scenes contain subject cutouts "
                f"(max allowed={max_cut}, <=25% rule)."
            )
        min_light = int(math.ceil(len(html_files) * 0.40))
        if light_motions < min_light:
            errors.append(
                f"Anti-Vício Dark Motion Monotony: only {light_motions}/{len(html_files)} motion scenes use light/warm/editorial palettes "
                f"(need >={min_light}). Rotate `MotionKit.PALETTES`!"
            )


def _verify_waveform_bin(bin_path: str) -> str | None:
    if not os.path.isfile(bin_path) or os.path.getsize(bin_path) < 96:
        return f"Missing or truncated waveform multi-res.bin: {bin_path}"
    raw = open(bin_path, "rb").read(96)
    magic, ver, dur, ch, lvl_cnt = struct.unpack("<5sBfBB36x", raw[:48])
    if magic != b"WFORM" or ver != 1 or lvl_cnt != 4 or ch not in (1, 2) or dur <= 0:
        return f"Invalid WFORM header in {bin_path}: magic={magic!r}, ver={ver}, lvl={lvl_cnt}, ch={ch}, dur={dur}"
    floats_per_sample = 2 if ch >= 2 else 1
    expected_rates = (500, 100, 25, 10)
    expected_offset = 96
    for idx in range(4):
        srate, scount, doff, _ = struct.unpack("<HIIH", raw[48 + idx * 12 : 60 + idx * 12])
        if srate != expected_rates[idx] or scount < 1 or doff != expected_offset:
            return f"Invalid WFORM level[{idx}] in {bin_path}: rate={srate}, count={scount}, offset={doff} (expected {expected_offset})"
        expected_offset += scount * floats_per_sample * 4
    actual_size = os.path.getsize(bin_path)
    if actual_size != expected_offset:
        return f"WFORM byte size mismatch in {bin_path}: got {actual_size}, expected {expected_offset}"
    return None


def validate_workspace(ws_dir: str) -> tuple[bool, list, dict]:
    errors = []
    stats = {
        "items": 0,
        "videos": 0,
        "images": 0,
        "cutouts": 0,
        "texts": 0,
        "callouts": 0,
        "lotties": 0,
        "marker_lotties": 0,
        "adjustments": 0,
        "sfx": 0,
        "transitions": 0,
        "fonts": 0,
        "text_motions": 0,
        "motion_modifiers": 0,
        "frozen_videos": 0,
        "cached_thumbnails": 0,
        "cached_filmstrips": 0,
        "cached_waveforms": 0,
    }

    ws_marker_p = os.path.join(ws_dir, ".freecut-workspace.json")
    if not os.path.isfile(ws_marker_p):
        errors.append(f"Missing .freecut-workspace.json in {ws_dir}")
    else:
        ws_m = json.load(open(ws_marker_p, "r", encoding="utf-8"))
        if ws_m.get("schemaVersion") != "2.0":
            errors.append(f"Invalid .freecut-workspace.json schemaVersion: {ws_m.get('schemaVersion')} (expected '2.0')")

    idx_path = os.path.join(ws_dir, "index.json")
    if not os.path.isfile(idx_path):
        return False, [f"Missing index.json in {ws_dir}"], stats

    idx = json.load(open(idx_path, "r", encoding="utf-8"))
    projects = idx.get("projects", [])
    if not projects:
        return False, ["index.json lists 0 projects"], stats

    pid = projects[0]["id"]
    proj_dir_ws = os.path.join(ws_dir, "projects", pid)
    proj_path = os.path.join(proj_dir_ws, "project.json")
    if not os.path.isfile(proj_path):
        return False, [f"Missing project.json at {proj_path}"], stats

    cover_p = os.path.join(proj_dir_ws, "thumbnail.jpg")
    if not os.path.isfile(cover_p) or os.path.getsize(cover_p) == 0:
        errors.append(f"Missing pre-baked project cover thumbnail.jpg at {cover_p}")

    links_p = os.path.join(proj_dir_ws, "media-links.json")
    if not os.path.isfile(links_p):
        errors.append(f"Missing media-links.json at {links_p}")

    proj = json.load(open(proj_path, "r", encoding="utf-8"))
    if proj.get("schemaVersion") != 15:
        errors.append(f"Invalid schemaVersion: {proj.get('schemaVersion')} (expected 15)")

    meta = proj.get("metadata", {})
    w, h = meta.get("width"), meta.get("height")
    fps = int(meta.get("fps") or 30)
    if (w, h) not in VALID_RESOLUTIONS:
        errors.append(f"Invalid canvas resolution: {w}x{h} (expected one of {sorted(VALID_RESOLUTIONS)})")

    tl = proj.get("timeline", {})
    tracks = tl.get("tracks", [])
    for trk in tracks:
        if trk.get("kind") not in ("video", "audio"):
            errors.append(f"Track {trk.get('id')} missing explicit kind='video'|'audio'")
        if trk.get("height") != 100:
            errors.append(f"Track {trk.get('id')} height={trk.get('height')} (expected 100 DEFAULT_TRACK_HEIGHT for zero-rewrite load)")
    for req_tl_k in ("masterBusDb", "currentFrame", "zoomLevel", "scrollPosition"):
        if req_tl_k not in tl:
            errors.append(f"timeline.{req_tl_k} missing (triggers normalization rewrite on open)")

    items = tl.get("items", [])
    transitions = tl.get("transitions", [])
    keyframes = tl.get("keyframes", [])
    stats["items"] = len(items)
    stats["transitions"] = len(transitions)

    half_w = (w or 1920) * 0.5
    half_h = (h or 1080) * 0.5
    boxed_slides = 0
    anchor_clips = 0
    max_end_frame = 0
    used_fonts = set()
    cutout_archetypes = []
    callout_coords = collections.Counter()

    checked_media_ids = set()
    item_ids = set()
    item_dur_map = {}
    item_label_map = {}
    for it in items:
        iid = it.get("id")
        item_ids.add(iid)
        dur_f = int(it.get("durationInFrames", 0))
        from_f = int(it.get("from", 0))
        max_end_frame = max(max_end_frame, from_f + dur_f)
        item_dur_map[iid] = dur_f
        itype = it.get("type")
        tid = it.get("trackId", "")
        lbl = str(it.get("label", ""))
        item_label_map[iid] = lbl

        tr_init = it.get("transform")
        if isinstance(tr_init, dict) and tr_init.get("rotation") is not None:
            rot_v = float(tr_init["rotation"])
            if rot_v < 0.0 or rot_v >= 360.0:
                errors.append(f"Item {lbl} has unnormalized rotation={rot_v} (expected [0, 360))")

        if it.get("motionModifiers"):
            stats["motion_modifiers"] += len(it["motionModifiers"])

        if tid == "track_anchor":
            anchor_clips += 1
            # v7.0 Sub-Shot Pacing Gate: single B-roll / Ken Burns clip must not exceed 6.8s (204 frames @ 30fps)
            if ("_broll" in lbl or "_cinematic_broll" in lbl or "_ken_burns" in lbl) and dur_f > int(fps * 6.8):
                errors.append(
                    f"Single Media Shot Overrun on {lbl}: {dur_f}f ({dur_f/fps:.2f}s > 6.8s cap). Subdivide into 2–3 sub-shots!"
                )
        if "_split_media" in lbl or "_framed_subject" in lbl:
            boxed_slides += 1
        if tid == "track_fg_2" and itype == "image":
            stats["cutouts"] += 1
            if "_cutout_" in lbl:
                cutout_archetypes.append((from_f, lbl.split("_cutout_", 1)[1]))

        if "FREECUT-card" in lbl or itype == "shape":
            errors.append(f"Banned box/card item detected: {lbl} ({itype})")

        mid = it.get("mediaId") or it.get("mediaRef")
        if itype in ("video", "image", "audio", "lottie"):
            if not mid:
                errors.append(f"Item {lbl} ({itype}) missing mediaId")
            elif mid not in checked_media_ids:
                checked_media_ids.add(mid)
                mdir = os.path.join(ws_dir, "media", mid)
                mmeta_p = os.path.join(mdir, "metadata.json")
                if not os.path.isfile(mmeta_p):
                    errors.append(f"Missing media metadata.json for {lbl} -> {mid}")
                else:
                    mmeta = json.load(open(mmeta_p, "r", encoding="utf-8"))
                    f_p = os.path.join(mdir, mmeta["fileName"])
                    if not os.path.isfile(f_p) or os.path.getsize(f_p) == 0:
                        errors.append(f"Missing or 0-byte media file: {f_p}")
                    mmime = str(mmeta.get("mimeType", ""))
                    if itype == "lottie" and mmime != "application/lottie+json":
                        errors.append(f"Lottie media {mmeta.get('fileName')} has mimeType='{mmime}' (expected 'application/lottie+json')")
                    if mmime.startswith(("image/", "video/")):
                        th_p = os.path.join(mdir, "thumbnail.jpg")
                        if not os.path.isfile(th_p) or os.path.getsize(th_p) == 0 or not mmeta.get("thumbnailId"):
                            errors.append(f"Missing pre-baked thumbnail.jpg / thumbnailId for {mmeta.get('fileName')} ({mid})")
                        else:
                            stats["cached_thumbnails"] += 1
                    if mmime.startswith("video/"):
                        fs_meta_p = os.path.join(mdir, "cache", "filmstrip", "meta.json")
                        fs_0_p = os.path.join(mdir, "cache", "filmstrip", "0.jpg")
                        if not os.path.isfile(fs_meta_p) or not os.path.isfile(fs_0_p) or os.path.getsize(fs_0_p) == 0:
                            errors.append(f"Missing pre-baked filmstrip cache for video {mmeta.get('fileName')} ({mid})")
                        else:
                            fs_m = json.load(open(fs_meta_p, "r", encoding="utf-8"))
                            if fs_m.get("version") != 2 or not fs_m.get("isComplete"):
                                errors.append(f"Incomplete/legacy filmstrip meta.json for {mmeta.get('fileName')}: {fs_m}")
                            else:
                                stats["cached_filmstrips"] += 1
                    if mmime.startswith(("audio/", "video/")):
                        wf_bin_p = os.path.join(mdir, "cache", "waveform", "multi-res.bin")
                        wf_err = _verify_waveform_bin(wf_bin_p)
                        if wf_err:
                            errors.append(f"{mmeta.get('fileName')}: {wf_err}")
                        else:
                            stats["cached_waveforms"] += 1

        if itype == "video":
            stats["videos"] += 1
            for k in ("sourceStart", "sourceEnd", "sourceDuration"):
                if not isinstance(it.get(k), int):
                    errors.append(f"Video {lbl} property '{k}' must be int frames, got {type(it.get(k)).__name__}")
            if all(isinstance(it.get(k), int) for k in ("sourceStart", "sourceEnd", "sourceDuration")):
                ss, se, sd = it["sourceStart"], it["sourceEnd"], it["sourceDuration"]
                avail_span = se - ss
                if dur_f > avail_span or se > sd or dur_f > sd:
                    stats["frozen_videos"] += 1
                    errors.append(
                        f"VIDEO_FREEZE_OVERRUN on {lbl}: durationInFrames={dur_f} exceeds video span [{ss}..{se}] (sourceDuration={sd})!"
                    )
            if it.get("volume", 0.0) != 0.0:
                errors.append(f"Video {lbl} must have volume=0 (muted against VO)")

        elif itype == "image":
            stats["images"] += 1

        elif itype == "lottie":
            stats["lotties"] += 1
            if "marker" in lbl.lower():
                stats["marker_lotties"] += 1
            if not isinstance(it.get("frameRate"), int) or not isinstance(it.get("totalFrames"), int):
                errors.append(f"Lottie {lbl} must define integer 'frameRate' and 'totalFrames'")

        elif itype == "adjustment":
            stats["adjustments"] += 1

        elif itype == "audio":
            for k in ("sourceStart", "sourceEnd", "sourceDuration"):
                if not isinstance(it.get(k), int):
                    errors.append(f"Audio {lbl} property '{k}' must be int frames, got {type(it.get(k)).__name__}")
            vol = float(it.get("volume", 0.0))
            if tid == "track_sfx":
                stats["sfx"] += 1
                if vol > -15.0:
                    errors.append(f"SFX {lbl} volume too loud ({vol} dB > -15.0 dB)")
            elif tid == "track_bgm":
                if vol > -12.0:
                    errors.append(f"BGM {lbl} volume too loud ({vol} dB > -12.0 dB)")
            elif tid == "track_audio":
                if not (-3.0 <= vol <= 3.0):
                    errors.append(f"VO {lbl} volume should be ~0 dB unity gain, got {vol} dB")

        elif itype == "text":
            stats["texts"] += 1
            txt = (it.get("text") or "").strip()
            if not txt:
                errors.append(f"Empty text item {iid}")
            if "textAnimation" in it:
                errors.append(f"Text {lbl} uses non-existent 'textAnimation' instead of FreeCut native 'textMotion'")
            if isinstance(it.get("textMotion"), dict) and it["textMotion"].get("in"):
                stats["text_motions"] += 1
            else:
                errors.append(f"Text {lbl} missing native FreeCut 'textMotion.in' preset")

            if it.get("fontFamily"):
                used_fonts.add(it["fontFamily"])
            for sp in it.get("textSpans") or []:
                if sp.get("fontFamily"):
                    used_fonts.add(sp["fontFamily"])

            tr = it.get("transform", {})
            tx, ty, tw = tr.get("x", 0), tr.get("y", 0), tr.get("width", 400)
            if abs(tx) + (tw / 2.0) > half_w + 50:
                errors.append(f"Text '{txt[:24]}' overflows horizontal canvas (x={tx}, w={tw}, canvas={w})")
            if abs(ty) > half_h - 30:
                errors.append(f"Text '{txt[:24]}' too close to top/bottom edge (y={ty}, canvas_h={h})")

            # v7.0 Monumental Word Integrity Gate
            if "_monumental_bg_type" in lbl:
                compact_mon = txt.replace(" ", "")
                if compact_mon.isdigit() and len(compact_mon) < 4:
                    errors.append(f"Monumental Hero Bare Digit Error on {lbl}: '{txt}' (use 4-digit year, formatted stat, or full word)")
                fs = int(it.get("fontSize", 200))
                if fs * len(txt) * 0.52 > tw * 1.18:
                    errors.append(f"Monumental Hero Clipping Risk on {lbl}: '{txt}' @ {fs}px exceeds box width {tw}px")

            if "_callout" in lbl:
                stats["callouts"] += 1
                callout_coords[(int(tx), int(ty))] += 1

    # v7.0 Press Highlighter Cap (`<= 2` yellow marker Lotties per 10 minutes)
    timeline_minutes = max(1.0, (max_end_frame / float(fps)) / 60.0)
    max_markers_allowed = max(2, int(math.ceil((timeline_minutes / 10.0) * 2.0)))
    if stats["marker_lotties"] > max_markers_allowed:
        errors.append(
            f"Anti-Vício Marker Highlighter Spam: {stats['marker_lotties']} yellow marker overlays used "
            f"(max allowed={max_markers_allowed} for {timeline_minutes:.1f} min). Rotate the 5 press treatments!"
        )

    # v7.0 Callout Zone Diversity Gate (`<= 32%` in any single `(x, y)` coordinate)
    if stats["callouts"] >= 8:
        top_coord, top_cnt = callout_coords.most_common(1)[0]
        share = top_cnt / float(stats["callouts"])
        if share > 0.32:
            errors.append(
                f"Anti-Vício Callout Corner Monotony: {top_cnt}/{stats['callouts']} ({share*100:.1f}%) callouts stuck at {top_coord} (max 32%)!"
            )

    stats["fonts"] = len(used_fonts)
    if anchor_clips >= 6 and len(used_fonts) < 3:
        errors.append(f"Anti-Vício Typography Monotony: only {len(used_fonts)} font(s) used ({sorted(used_fonts)}); use >=3 paired editorial fonts!")

    # Anti-Vício Cutout Diversity Gate: consecutive cutout scenes must NOT repeat the same archetype
    cutout_archetypes.sort(key=lambda x: x[0])
    for i in range(len(cutout_archetypes) - 1):
        if cutout_archetypes[i][1] == cutout_archetypes[i + 1][1]:
            errors.append(f"Anti-Vício Repetitive Cutout Archetype: '{cutout_archetypes[i][1]}' used twice in a row!")

    # Strict Keyframe Bounds & Schema v15 `animationVersion: 2` Gate
    for kf_entry in keyframes:
        kiid = kf_entry.get("itemId")
        if kf_entry.get("animationVersion") != 2:
            errors.append(f"Keyframe entry for {kiid} missing animationVersion=2 (got {kf_entry.get('animationVersion')})")
        if kiid not in item_dur_map:
            errors.append(f"Keyframe entry references unknown itemId {kiid}")
            continue
        cdur = item_dur_map[kiid]
        clbl = item_label_map.get(kiid, kiid)
        for prop in kf_entry.get("properties", []):
            pname = prop.get("property")
            for kf in prop.get("keyframes", []):
                fr = kf.get("frame", -1)
                if not isinstance(fr, int) or fr < 0 or fr >= cdur:
                    errors.append(
                        f"Out-of-clip keyframe on {clbl}.{pname}: frame={fr} outside [0, {cdur - 1}] (causes FreeCut 'Quadros-chave aparados'!)"
                    )

    # Strict Same-Track Zero-Overlap Gate (matches FreeCut `repairOverlappingItems`)
    tr_pairs = set()
    for tr in transitions:
        lc, rc = tr.get("leftClipId"), tr.get("rightClipId")
        if lc and rc:
            tr_pairs.add((lc, rc))
            tr_pairs.add((rc, lc))
    by_trk = collections.defaultdict(list)
    for it in items:
        by_trk[it.get("trackId", "")].append(it)
    for tid_k, t_items in by_trk.items():
        t_sorted = sorted(t_items, key=lambda x: int(x.get("from", 0)))
        for i in range(len(t_sorted) - 1):
            a, b = t_sorted[i], t_sorted[i + 1]
            a_end = int(a.get("from", 0)) + int(a.get("durationInFrames", 0))
            if int(b.get("from", 0)) < a_end and (a.get("id"), b.get("id")) not in tr_pairs:
                errors.append(
                    f"Same-track overlap on {tid_k}: {a.get('label')} ends@{a_end} > {b.get('label')} starts@{b.get('from')}"
                )

    # Anti-Vício Gate 1: Strict <= 10% Boxed/Split card ratio cap
    max_allowed_boxed = max(1, anchor_clips // 10)
    if anchor_clips >= 5 and boxed_slides > max_allowed_boxed:
        errors.append(
            f"Anti-Vício Card Overuse: {boxed_slides}/{anchor_clips} scenes use boxed/split frames "
            f"(max allowed={max_allowed_boxed}, <=10% rule). Use full_bleed_ken_burns, parallax_cutout_stage, press_evidence_highlight, or motion_scene!"
        )

    # Anti-Vício Gate 3: Ban consecutive framed/split/statement slides
    anchor_sorted = sorted([it for it in items if it.get("trackId") == "track_anchor"], key=lambda x: x.get("from", 0))
    for i in range(len(anchor_sorted) - 1):
        l1 = str(anchor_sorted[i].get("label", ""))
        l2 = str(anchor_sorted[i + 1].get("label", ""))
        for tag in ("_split_media", "_framed_subject", "_statement_matte"):
            if tag in l1 and tag in l2:
                errors.append(f"Anti-Vício Consecutive Layout Failure: '{l1}' followed immediately by '{l2}' ({tag}).")

    for tr in transitions:
        if tr.get("leftClipId") not in item_ids or tr.get("rightClipId") not in item_ids:
            errors.append(f"Transition {tr.get('id')} references non-existent clip ID")

    parent_proj_dir = os.path.dirname(os.path.abspath(ws_dir))
    audit_motion_scenes_v7(parent_proj_dir, errors, stats)

    # Verify V8 `JSON.stringify` SHA-256 checksum parity on `<SafeTitle>.freecut.zip` if present
    for zp in glob.glob(os.path.join(parent_proj_dir, "*.freecut.zip")):
        try:
            with zipfile.ZipFile(zp, "r") as zf:
                m_obj = json.loads(zf.read("manifest.json").decode("utf-8"))
                stored_cs = m_obj.get("checksum", "")
                def _v8_num(o):
                    if isinstance(o, bool) or o is None or isinstance(o, (int, str)):
                        return o
                    if isinstance(o, float):
                        return int(o) if math.isfinite(o) and o.is_integer() else o
                    if isinstance(o, list):
                        return [_v8_num(x) for x in o]
                    if isinstance(o, dict):
                        return {k: _v8_num(v) for k, v in o.items()}
                    return o
                m_for_hash = _v8_num(dict(m_obj))
                m_for_hash["checksum"] = ""
                expected_cs = hashlib.sha256(
                    json.dumps(m_for_hash, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
                ).hexdigest()
                if stored_cs != expected_cs:
                    errors.append(f"Bundle {os.path.basename(zp)} manifest checksum mismatch against Chrome V8 JSON.stringify")
                if "cover.jpg" not in zf.namelist():
                    errors.append(f"Bundle {os.path.basename(zp)} missing cover.jpg")
        except Exception as exc:
            errors.append(f"Bundle {os.path.basename(zp)} unreadable: {exc}")

    return len(errors) == 0, errors, stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", help="Path to freecut_workspace folder")
    ap.add_argument("--project-dir", help="Path to parent documentary project folder")
    args = ap.parse_args()

    ws = args.workspace or (os.path.join(args.project_dir, "freecut_workspace") if args.project_dir else None)
    if not ws:
        ap.error("Provide --workspace or --project-dir")

    ok, errors, stats = validate_workspace(ws)
    print(f"[validate_freecut v7] Stats: {json.dumps(stats)}")
    if ok:
        print("[validate_freecut v7] PASS — 0 schema, freeze, or editorial anti-vício errors! Ready to open & render in FreeCut.")
        sys.exit(0)
    else:
        print(f"[validate_freecut v7] FAIL — {len(errors)} error(s):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
