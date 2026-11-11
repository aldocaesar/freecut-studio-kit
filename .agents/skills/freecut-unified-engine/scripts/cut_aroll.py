#!/usr/bin/env python3
"""
A-Roll / Talking-Head ("Yap") Smart Silence Cutter & Jump-Cut Planner (v6.0)
============================================================================
Turns raw camera / talking-head recordings (.mp4 / .mov) + `words.json` into
tight, human-paced `aroll_cuts.json` segments:
  - Cuts dead air > `max_pause_ms` (default 320ms) while preserving natural `pad_ms` (75ms) breath tails
    so syllables are NEVER clipped.
  - Alternates subtle optical framing (`1.00x` <-> `1.07x` punch-in) on hard jump cuts (`gap >= 450ms`)
    to mask cuts cleanly like a senior human editor (`diretor-de-edicao` / `craft.md`).
  - Remaps `words.json` into `words_cut.json` on the compressed timeline if requested!
"""
import argparse
import json
import os
import sys


def build_aroll_cuts(
    words: list,
    max_pause_ms: int = 320,
    pad_before_ms: int = 65,
    pad_after_ms: int = 85,
    punch_scale: float = 1.07,
) -> dict:
    if not words:
        return {"segments": [], "remapped_words": [], "saved_ms": 0}

    # Group words separated by pauses <= max_pause_ms into continuous speech chunks
    raw_chunks = []
    cur = [words[0]]
    for w in words[1:]:
        gap = w["start_ms"] - cur[-1]["end_ms"]
        if gap > max_pause_ms:
            raw_chunks.append(cur)
            cur = [w]
        else:
            cur.append(w)
    if cur:
        raw_chunks.append(cur)

    segments = []
    remapped_words = []
    timeline_cursor_ms = 0
    zoom_toggle = False

    for idx, chunk in enumerate(raw_chunks):
        src_start = max(0, chunk[0]["start_ms"] - pad_before_ms)
        src_end = chunk[-1]["end_ms"] + pad_after_ms
        if idx > 0:
            prev_src_end = segments[-1]["source_end_ms"]
            if src_start < prev_src_end:
                src_start = prev_src_end
            raw_gap = chunk[0]["start_ms"] - raw_chunks[idx - 1][-1]["end_ms"]
            if raw_gap >= 450:
                zoom_toggle = not zoom_toggle

        dur_ms = max(80, src_end - src_start)
        scale = round(punch_scale if zoom_toggle else 1.0, 4)

        seg = {
            "index": idx + 1,
            "source_start_ms": int(src_start),
            "source_end_ms": int(src_end),
            "timeline_start_ms": int(timeline_cursor_ms),
            "timeline_end_ms": int(timeline_cursor_ms + dur_ms),
            "duration_ms": int(dur_ms),
            "scale": scale,
            "text": " ".join(w["word"] for w in chunk),
        }
        segments.append(seg)

        offset_shift = src_start - timeline_cursor_ms
        for w in chunk:
            ns = max(timeline_cursor_ms, w["start_ms"] - offset_shift)
            ne = min(timeline_cursor_ms + dur_ms, max(ns + 20, w["end_ms"] - offset_shift))
            remapped_words.append({
                "word": w["word"],
                "start_ms": int(ns),
                "end_ms": int(ne),
                "source_start_ms": int(w["start_ms"]),
                "source_end_ms": int(w["end_ms"]),
                "confidence": w.get("confidence", 1.0),
            })

        timeline_cursor_ms += dur_ms

    orig_dur = words[-1]["end_ms"]
    saved_ms = max(0, orig_dur - timeline_cursor_ms)
    return {
        "segments": segments,
        "remapped_words": remapped_words,
        "original_duration_ms": int(orig_dur),
        "edited_duration_ms": int(timeline_cursor_ms),
        "saved_ms": int(saved_ms),
    }


def main():
    ap = argparse.ArgumentParser(description="A-Roll / Talking-Head Silence Cutter & Punch-In Planner")
    ap.add_argument("--project-dir", required=True)
    ap.add_argument("--max-pause-ms", type=int, default=320)
    ap.add_argument("--punch-scale", type=float, default=1.07)
    ap.add_argument("--overwrite-words", action="store_true", help="Replace words.json with compressed timeline timestamps")
    args = ap.parse_args()

    words_path = os.path.join(args.project_dir, "words.json")
    if not os.path.isfile(words_path):
        sys.exit(f"[ERROR] Run transcribe_audio.py first — missing {words_path}")

    words = json.load(open(words_path, "r", encoding="utf-8"))
    plan = build_aroll_cuts(words, max_pause_ms=args.max_pause_ms, punch_scale=args.punch_scale)

    out_path = os.path.join(args.project_dir, "aroll_cuts.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)

    if args.overwrite_words:
        os.replace(words_path, os.path.join(args.project_dir, "words_raw_untrimmed.json"))
        with open(words_path, "w", encoding="utf-8") as f:
            json.dump(plan["remapped_words"], f, ensure_ascii=False, indent=2)

    print(
        f"[cut_aroll] OK -> {len(plan['segments'])} tight segments | "
        f"{plan['original_duration_ms']/1000:.1f}s -> {plan['edited_duration_ms']/1000:.1f}s "
        f"(saved {plan['saved_ms']/1000:.1f}s dead air) -> {out_path}"
    )


if __name__ == "__main__":
    main()
