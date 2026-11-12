#!/usr/bin/env python3
"""
creator_memory.py — Persistent Channel & Anti-Clone Style Memory for FreeCut (v8.0)
===================================================================================
Stores durable per-workspace creator rules, recurring entities, and a rolling
anti-repetition log of recent projects in `<WORKSPACE>/.freecut-creator-memory.json`
(gitignored & excluded from shareable bundles).

Key v8.0 Guarantees:
  1. NEVER auto-locks a single video's `style_dna.accent` as permanent channel accent
     (only explicit `--accent` from user brand feedback locks `profile.accent_color`).
  2. Tracks recent videos' `style_dna` (colors, fonts, mood), `opening_layout`, and
     `motion_briefs` so the next video intentionally picks a fresh, genre-authentic
     visual identity and never clones palettes or motion scenes back-to-back.
"""
import argparse
import datetime
import json
import os
import sys

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_WS_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", ".."))
MEMORY_FILENAME = ".freecut-creator-memory.json"


def _default_state() -> dict:
    return {
        "version": "8.0",
        "updated_at": "",
        "profile": {
            "default_aspect_ratio": "16:9",
            "language": "auto",
            "niche": "",
            "captions_default": False,
            "accent_color": "",
        },
        "style_rules": [],
        "recurring_entities": [],
        "recent_projects": [],
    }


def memory_path(ws_root: str = "") -> str:
    root = os.path.abspath(ws_root or DEFAULT_WS_ROOT)
    return os.path.join(root, MEMORY_FILENAME)


def load_memory(ws_root: str = "") -> dict:
    p = memory_path(ws_root)
    base = _default_state()
    if not os.path.isfile(p):
        return base
    try:
        with open(p, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        if isinstance(raw, dict):
            prof = raw.get("profile")
            if isinstance(prof, dict):
                base["profile"].update(prof)
            for k in ("style_rules", "recurring_entities", "recent_projects"):
                if isinstance(raw.get(k), list):
                    base[k] = raw[k]
            base["updated_at"] = str(raw.get("updated_at") or "")
    except Exception:
        pass
    return base


def save_memory(data: dict, ws_root: str = "") -> str:
    p = memory_path(ws_root)
    data["version"] = "8.0"
    data["updated_at"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    return p


def record_project(project_dir: str, ws_root: str = "") -> str:
    sb_path = os.path.join(os.path.abspath(project_dir), "storyboard.json")
    if not os.path.isfile(sb_path):
        return ""
    try:
        with open(sb_path, "r", encoding="utf-8") as fh:
            sb = json.load(fh)
    except Exception:
        return ""

    mem = load_memory(ws_root)
    scenes = sb.get("scenes") or []
    dur_ms = max((int(s.get("end_ms") or 0) for s in scenes), default=0)
    motion_briefs = []
    for s in scenes:
        if str(s.get("layout") or "").lower() in ("motion_scene", "motion") or str(s.get("media_type") or "").upper() == "MOTION_SCENE":
            mb = str(s.get("motion_brief") or s.get("headline") or s.get("id") or "").strip()
            if mb:
                motion_briefs.append(mb[:72])

    slug = os.path.basename(os.path.abspath(project_dir))
    aspect = str(sb.get("aspect_ratio") or mem["profile"].get("default_aspect_ratio") or "16:9")
    dna = sb.get("style_dna") or {}
    fonts = [f for f in (dna.get("font_display"), dna.get("font_serif"), dna.get("font_body")) if f]
    entry = {
        "slug": slug,
        "title": str(sb.get("title") or slug)[:80],
        "aspect_ratio": aspect,
        "duration_s": round(dur_ms / 1000.0, 1),
        "scenes": len(scenes),
        "opening_layout": str(scenes[0].get("layout") if scenes else ""),
        "mood": str(dna.get("mood") or dna.get("genre") or ""),
        "accent": str(dna.get("accent") or ""),
        "accent_secondary": str(dna.get("accent_secondary") or ""),
        "studio_bg": str(dna.get("studio_bg") or ""),
        "paper_bg": str(dna.get("paper_bg") or ""),
        "fonts": fonts[:3],
        "motion_briefs": motion_briefs[:5],
        "recorded_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
    }

    recent = [r for r in mem.get("recent_projects", []) if r.get("slug") != slug]
    recent.insert(0, entry)
    mem["recent_projects"] = recent[:8]
    return save_memory(mem, ws_root)


def format_summary(ws_root: str = "") -> str:
    p = memory_path(ws_root)
    setup_done = os.path.isfile(os.path.join(os.path.dirname(p), ".freecut-setup-done.json"))
    if not os.path.isfile(p):
        return (
            f"[CREATOR MEMORY] Clean slate (onboarding={'DONE' if setup_done else 'FIRST_RUN'}) | "
            "defaults: aspect=16:9, captions=off, bespoke genre-driven style_dna & 100% custom LLM motion scenes."
        )
    mem = load_memory(ws_root)
    prof = mem["profile"]
    lines = [
        f"[CREATOR MEMORY] onboarding={'DONE' if setup_done else 'FIRST_RUN'} | "
        f"default_aspect={prof.get('default_aspect_ratio', '16:9')} | "
        f"lang={prof.get('language', 'auto')} | "
        f"captions={'on' if prof.get('captions_default') else 'off'}"
        + (f" | niche={prof['niche']}" if prof.get("niche") else "")
        + (f" | locked_brand_accent={prof['accent_color']}" if prof.get("accent_color") else " | palette=chameleon_per_video")
    ]
    if mem.get("style_rules"):
        lines.append("  Durable Creator Rules:")
        for r in mem["style_rules"][-12:]:
            lines.append(f"    - {r}")
    if mem.get("recurring_entities"):
        lines.append("  Recurring Entities: " + ", ".join(mem["recurring_entities"][:12]))
    if mem.get("recent_projects"):
        last = mem["recent_projects"][0]
        lines.append(
            f"  Last Video ({last.get('slug')}): {last.get('aspect_ratio')} • {last.get('duration_s')}s • "
            f"opened=`{last.get('opening_layout')}` • accent={last.get('accent')}/{last.get('accent_secondary')} • "
            f"bg={last.get('studio_bg')}/{last.get('paper_bg')} • fonts={last.get('fonts')}"
        )
        lines.append(
            "  ANTI-CLONE DIRECTIVE: Do NOT repeat the last video's accent hexes, backdrops, font pairing, "
            "opening layout, or motion metaphors unless explicitly locked in Durable Creator Rules!"
        )
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Read or update persistent FreeCut creator context memory.")
    ap.add_argument("--workspace", default="", help="Workspace root (auto-detected if omitted)")
    ap.add_argument("--summary", action="store_true", help="Print compact <=20-line memory digest")
    ap.add_argument("--remember", action="append", default=[], help="Save a durable style/editing rule")
    ap.add_argument("--forget", default="", help="Remove style rules matching substring")
    ap.add_argument("--aspect-ratio", choices=["16:9", "9:16", "4:5", "1:1"], help="Set default aspect ratio")
    ap.add_argument("--lang", help="Set default language code (e.g., pt-BR, en, es, auto)")
    ap.add_argument("--niche", help="Set channel niche/theme summary")
    ap.add_argument("--captions", choices=["on", "off"], help="Set default captions preference")
    ap.add_argument("--accent", help="Lock/clear brand accent hex color (pass 'auto' or '' to unlock)")
    ap.add_argument("--entity", action="append", default=[], help="Register recurring person/brand/channel entity")
    ap.add_argument("--record-project", help="Record completed project storyboard metadata")
    args = ap.parse_args()

    changed = False
    mem = load_memory(args.workspace)

    if args.aspect_ratio:
        mem["profile"]["default_aspect_ratio"] = args.aspect_ratio
        changed = True
    if args.lang:
        mem["profile"]["language"] = args.lang.strip()
        changed = True
    if args.niche is not None:
        mem["profile"]["niche"] = args.niche.strip()[:140]
        changed = True
    if args.captions:
        mem["profile"]["captions_default"] = args.captions == "on"
        changed = True
    if args.accent is not None:
        val = args.accent.strip()
        mem["profile"]["accent_color"] = "" if val.lower() in ("", "auto", "none", "chameleon") else val[:16]
        changed = True
    if args.forget:
        needle = args.forget.strip().lower()
        before = len(mem["style_rules"])
        mem["style_rules"] = [r for r in mem["style_rules"] if needle not in r.lower()]
        changed = changed or (len(mem["style_rules"]) != before)
    for rule in args.remember:
        r_clean = " ".join(rule.strip().split())
        if r_clean and r_clean.lower() not in {x.lower() for x in mem["style_rules"]}:
            mem["style_rules"].append(r_clean[:220])
            mem["style_rules"] = mem["style_rules"][-20:]
            changed = True
    for ent in args.entity:
        e_clean = " ".join(ent.strip().split())
        if e_clean and e_clean.lower() not in {x.lower() for x in mem["recurring_entities"]}:
            mem["recurring_entities"].append(e_clean[:80])
            mem["recurring_entities"] = mem["recurring_entities"][-25:]
            changed = True

    if changed:
        save_memory(mem, args.workspace)

    if args.record_project:
        record_project(args.record_project, args.workspace)

    if args.summary or not (changed or args.record_project):
        print(format_summary(args.workspace))


if __name__ == "__main__":
    main()
