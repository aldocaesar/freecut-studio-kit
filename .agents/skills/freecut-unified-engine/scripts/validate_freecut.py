#!/usr/bin/env python3
"""
validate_freecut.py (v7.0 — Strict Schema v15 + Zero-Freeze & Anti-Vício Editorial Auditor)
===========================================================================================
Audits `<project_dir>/freecut_workspace` AND `<project_dir>` editorial artifacts
against BOTH `walterlow/freecut` schemaVersion 15 AND v7.0 human-editing quality gates:
  1. Multi-format canvas (`1920x1080`, `1080x1920`, `1080x1350`, `1080x1080`) @ 30fps.
  2. Zero `FREECUT-card` or `shape` box overlays.
  3. HARD ZERO-FREEZE GATE: `durationInFrames <= (sourceEnd - sourceStart) <= sourceDuration`
     on 100% of `video` clips (zero frozen tail frames!).
  4. SUB-SHOT PACING GATE: Single B-roll / Ken Burns clip `<= 6.8s` (`204f` @ 30fps).
  5. MONUMENTAL WORD GATE: Zero bare 1–3 digit fragments (`'2'`, `'13'`) and optical width fit.
  6. PRESS HIGHLIGHTER CAP: Max `2` yellow `marker` Lotties per 10 minutes of timeline.
  7. TYPOGRAPHY ZONE DIVERSITY: Max `32%` of `_callout` texts in a single `(x, y)` coordinate.
  8. MOTION ANTI-CLONE GATE: Real GeoJSON maps, `<= 25%` motion cutouts, `>= 40%` light/warm/colored
     motion palettes, and zero consecutive identical `MotionKit.render*` engines.
"""
import argparse
import collections
import glob
import json
import math
import os
import re
import sys

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
    }

    idx_path = os.path.join(ws_dir, "index.json")
    if not os.path.isfile(idx_path):
        return False, [f"Missing index.json in {ws_dir}"], stats

    idx = json.load(open(idx_path, "r", encoding="utf-8"))
    projects = idx.get("projects", [])
    if not projects:
        return False, ["index.json lists 0 projects"], stats

    pid = projects[0]["id"]
    proj_path = os.path.join(ws_dir, "projects", pid, "project.json")
    if not os.path.isfile(proj_path):
        return False, [f"Missing project.json at {proj_path}"], stats

    proj = json.load(open(proj_path, "r", encoding="utf-8"))
    if proj.get("schemaVersion") != 15:
        errors.append(f"Invalid schemaVersion: {proj.get('schemaVersion')} (expected 15)")

    meta = proj.get("metadata", {})
    w, h = meta.get("width"), meta.get("height")
    fps = int(meta.get("fps") or 30)
    if (w, h) not in VALID_RESOLUTIONS:
        errors.append(f"Invalid canvas resolution: {w}x{h} (expected one of {sorted(VALID_RESOLUTIONS)})")

    tl = proj.get("timeline", {})
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
            else:
                mdir = os.path.join(ws_dir, "media", mid)
                mmeta_p = os.path.join(mdir, "metadata.json")
                if not os.path.isfile(mmeta_p):
                    errors.append(f"Missing media metadata.json for {lbl} -> {mid}")
                else:
                    mmeta = json.load(open(mmeta_p, "r", encoding="utf-8"))
                    f_p = os.path.join(mdir, mmeta["fileName"])
                    if not os.path.isfile(f_p) or os.path.getsize(f_p) == 0:
                        errors.append(f"Missing or 0-byte media file: {f_p}")

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
                errors.append(f"Video {lbl} must have volume=0.0 (muted against VO)")

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
                if not isinstance(it.get(k), (int, float)):
                    errors.append(f"Audio {lbl} missing numeric '{k}'")
            vol = float(it.get("volume", 0.0))
            if tid == "track_sfx":
                stats["sfx"] += 1
                if vol > -15.0:
                    errors.append(f"SFX {lbl} volume too loud ({vol} dB > -15.0 dB)")
            elif tid == "track_bgm":
                if vol > -12.0:
                    errors.append(f"BGM {lbl} volume too loud ({vol} dB > -12.0 dB)")
            elif tid == "track_audio":
                if abs(vol - 1.0) > 0.05:
                    errors.append(f"VO {lbl} volume should be 1.0, got {vol}")

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

    # Strict Keyframe Bounds Gate (`0 <= frame < durationInFrames` -> zero "Quadros-chave aparados"!)
    for kf_entry in keyframes:
        kiid = kf_entry.get("itemId")
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
