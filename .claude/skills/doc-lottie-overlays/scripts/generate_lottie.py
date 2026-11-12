#!/usr/bin/env python3
"""
generate_lottie.py (v2 — Sleek Editorial Vector Overlays for FreeCut)
=====================================================================
Generates lightweight (<15 KB) Bodymovin/Lottie `.json` transparent overlays that load natively
onto FreeCut's `track_fg_3` (`type: "lottie"`), styled with the project's Style DNA colors.

Supported `--kind` presets:
  - `minimal_lower_third`   : Sleek editorial accent pillar + subtle dark glass lower-third rule
  - `focus_corner_brackets` : Crisp investigative viewfinder corner brackets locking onto a subject
  - `handdrawn_underline`   : Organic editorial ink underline stroke sweep
  - `handdrawn_circle`      : Editorial marker ring drawing around key visual evidence
  - `pulse_beacon`          : Cartographic / telemetry pulsing target ring
"""
import argparse
import json
import os


def hex_to_rgb01(hex_str: str):
    h = hex_str.strip().lstrip("#")
    if len(h) != 6:
        return [0.784, 0.294, 0.192, 1]
    return [round(int(h[i : i + 2], 16) / 255.0, 4) for i in (0, 2, 4)] + [1]


def circle_bezier_path(cx, cy, rx, ry):
    k = 0.55228475
    return {
        "c": True,
        "v": [[cx, cy - ry], [cx + rx, cy], [cx, cy + ry], [cx - rx, cy]],
        "i": [[-rx * k, 0], [0, -ry * k], [rx * k, 0], [0, ry * k]],
        "o": [[rx * k, 0], [0, ry * k], [-rx * k, 0], [0, -ry * k]],
    }


def make_handdrawn_circle(w=520, h=520, dur_frames=90, accent="#C84B31"):
    col = hex_to_rgb01(accent)
    path1 = circle_bezier_path(0, 0, w * 0.35, h * 0.31)
    return {
        "v": "5.7.4",
        "fr": 30,
        "ip": 0,
        "op": dur_frames,
        "w": w,
        "h": h,
        "nm": "editorial_marker_circle",
        "ddd": 0,
        "assets": [],
        "layers": [
            {
                "ddd": 0,
                "ind": 1,
                "ty": 4,
                "nm": "MarkerRing",
                "sr": 1,
                "ks": {
                    "o": {
                        "a": 1,
                        "k": [
                            {"t": 0, "s": [0]},
                            {"t": 6, "s": [95]},
                            {"t": max(10, dur_frames - 12), "s": [95]},
                            {"t": dur_frames, "s": [0]},
                        ],
                    },
                    "r": {"a": 0, "k": -5},
                    "p": {"a": 0, "k": [w / 2, h / 2, 0]},
                    "a": {"a": 0, "k": [0, 0, 0]},
                    "s": {
                        "a": 1,
                        "k": [
                            {"t": 0, "s": [90, 90, 100], "i": {"x": [0.15, 0.15, 0.15], "y": [1, 1, 1]}, "o": {"x": [0.2, 0.2, 0.2], "y": [0, 0, 0]}},
                            {"t": 20, "s": [100, 100, 100]},
                        ],
                    },
                },
                "ao": 0,
                "shapes": [
                    {
                        "ty": "gr",
                        "nm": "RingGroup",
                        "it": [
                            {"ind": 0, "ty": "sh", "ks": {"a": 0, "k": path1}, "nm": "Path"},
                            {
                                "ty": "tm",
                                "s": {"a": 0, "k": 0},
                                "e": {
                                    "a": 1,
                                    "k": [
                                        {"t": 0, "s": [0], "i": {"x": [0.12], "y": [1]}, "o": {"x": [0.25], "y": [0]}},
                                        {"t": 22, "s": [100]},
                                    ],
                                },
                                "o": {"a": 0, "k": 0},
                                "m": 1,
                                "nm": "Trim",
                            },
                            {"ty": "st", "c": {"a": 0, "k": col}, "o": {"a": 0, "k": 100}, "w": {"a": 0, "k": 5.5}, "lc": 2, "lj": 2, "nm": "Stroke"},
                            {"ty": "tr", "p": {"a": 0, "k": [0, 0]}, "a": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [100, 100]}, "r": {"a": 0, "k": 0}, "o": {"a": 0, "k": 100}},
                        ],
                    }
                ],
                "ip": 0,
                "op": dur_frames,
                "st": 0,
                "bm": 0,
            }
        ],
    }


def make_handdrawn_underline(w=640, h=140, dur_frames=90, accent="#C84B31"):
    col = hex_to_rgb01(accent)
    line_path = {
        "c": False,
        "v": [[-w * 0.42, 6], [0, -5], [w * 0.42, 4]],
        "i": [[0, 0], [-w * 0.14, 2], [-w * 0.12, -2]],
        "o": [[w * 0.14, -3], [w * 0.14, -2], [0, 0]],
    }
    return {
        "v": "5.7.4",
        "fr": 30,
        "ip": 0,
        "op": dur_frames,
        "w": w,
        "h": h,
        "nm": "editorial_underline",
        "ddd": 0,
        "assets": [],
        "layers": [
            {
                "ddd": 0,
                "ind": 1,
                "ty": 4,
                "nm": "UnderlineSweep",
                "sr": 1,
                "ks": {
                    "o": {"a": 1, "k": [{"t": 0, "s": [0]}, {"t": 4, "s": [100]}, {"t": max(8, dur_frames - 12), "s": [100]}, {"t": dur_frames, "s": [0]}]},
                    "r": {"a": 0, "k": 0},
                    "p": {"a": 0, "k": [w / 2, h / 2, 0]},
                    "a": {"a": 0, "k": [0, 0, 0]},
                    "s": {"a": 0, "k": [100, 100, 100]},
                },
                "ao": 0,
                "shapes": [
                    {
                        "ty": "gr",
                        "nm": "Line",
                        "it": [
                            {"ind": 0, "ty": "sh", "ks": {"a": 0, "k": line_path}, "nm": "Path"},
                            {
                                "ty": "tm",
                                "s": {"a": 0, "k": 0},
                                "e": {"a": 1, "k": [{"t": 0, "s": [0], "i": {"x": [0.15], "y": [1]}, "o": {"x": [0.2], "y": [0]}}, {"t": 18, "s": [100]}]},
                                "o": {"a": 0, "k": 0},
                                "m": 1,
                            },
                            {"ty": "st", "c": {"a": 0, "k": col}, "o": {"a": 0, "k": 100}, "w": {"a": 0, "k": 6}, "lc": 2, "lj": 2},
                            {"ty": "tr", "p": {"a": 0, "k": [0, 0]}, "a": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [100, 100]}, "r": {"a": 0, "k": 0}, "o": {"a": 0, "k": 100}},
                        ],
                    }
                ],
                "ip": 0,
                "op": dur_frames,
                "st": 0,
                "bm": 0,
            }
        ],
    }


def make_minimal_lower_third(w=1920, h=1080, dur_frames=120, accent="#C84B31", dark="#0D121A"):
    ac = hex_to_rgb01(accent)
    dk = hex_to_rgb01(dark)
    return {
        "v": "5.7.4",
        "fr": 30,
        "ip": 0,
        "op": dur_frames,
        "w": w,
        "h": h,
        "nm": "minimal_lower_third",
        "ddd": 0,
        "assets": [],
        "layers": [
            {
                "ddd": 0,
                "ind": 1,
                "ty": 4,
                "nm": "AccentPillar",
                "sr": 1,
                "ks": {
                    "o": {"a": 1, "k": [{"t": 0, "s": [0]}, {"t": 5, "s": [100]}, {"t": max(10, dur_frames - 10), "s": [100]}, {"t": dur_frames, "s": [0]}]},
                    "r": {"a": 0, "k": 0},
                    "p": {"a": 0, "k": [96, 922, 0]},
                    "a": {"a": 0, "k": [0, 0, 0]},
                    "s": {
                        "a": 1,
                        "k": [
                            {"t": 0, "s": [100, 0, 100], "i": {"x": [0.15, 0.15, 0.15], "y": [1, 1, 1]}, "o": {"x": [0.2, 0.2, 0.2], "y": [0, 0, 0]}},
                            {"t": 14, "s": [100, 100, 100]},
                        ],
                    },
                },
                "ao": 0,
                "shapes": [
                    {
                        "ty": "gr",
                        "nm": "Pillar",
                        "it": [
                            {"ty": "rc", "d": 1, "s": {"a": 0, "k": [5, 76]}, "p": {"a": 0, "k": [0, 0]}, "r": {"a": 0, "k": 2}},
                            {"ty": "fl", "c": {"a": 0, "k": ac}, "o": {"a": 0, "k": 100}},
                            {"ty": "tr", "p": {"a": 0, "k": [0, 0]}, "a": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [100, 100]}, "r": {"a": 0, "k": 0}, "o": {"a": 0, "k": 100}},
                        ],
                    }
                ],
                "ip": 0,
                "op": dur_frames,
                "st": 0,
                "bm": 0,
            },
            {
                "ddd": 0,
                "ind": 2,
                "ty": 4,
                "nm": "BackdropPlate",
                "sr": 1,
                "ks": {
                    "o": {"a": 1, "k": [{"t": 0, "s": [0]}, {"t": 8, "s": [78]}, {"t": max(12, dur_frames - 10), "s": [78]}, {"t": dur_frames, "s": [0]}]},
                    "r": {"a": 0, "k": 0},
                    "p": {"a": 0, "k": [96, 922, 0]},
                    "a": {"a": 0, "k": [-360, 0, 0]},
                    "s": {
                        "a": 1,
                        "k": [
                            {"t": 2, "s": [0, 100, 100], "i": {"x": [0.15, 0.15, 0.15], "y": [1, 1, 1]}, "o": {"x": [0.2, 0.2, 0.2], "y": [0, 0, 0]}},
                            {"t": 18, "s": [100, 100, 100]},
                        ],
                    },
                },
                "ao": 0,
                "shapes": [
                    {
                        "ty": "gr",
                        "nm": "GlassBar",
                        "it": [
                            {"ty": "rc", "d": 1, "s": {"a": 0, "k": [720, 82]}, "p": {"a": 0, "k": [0, 0]}, "r": {"a": 0, "k": 8}},
                            {"ty": "fl", "c": {"a": 0, "k": dk}, "o": {"a": 0, "k": 100}},
                            {"ty": "tr", "p": {"a": 0, "k": [0, 0]}, "a": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [100, 100]}, "r": {"a": 0, "k": 0}, "o": {"a": 0, "k": 100}},
                        ],
                    }
                ],
                "ip": 0,
                "op": dur_frames,
                "st": 0,
                "bm": 0,
            },
        ],
    }


def make_focus_corner_brackets(w=640, h=640, dur_frames=90, accent="#C84B31"):
    col = hex_to_rgb01(accent)
    bx, by, arm = w * 0.36, h * 0.36, 42
    corners = [
        {"v": [[-bx, -by + arm], [-bx, -by], [-bx + arm, -by]]},
        {"v": [[bx - arm, -by], [bx, -by], [bx, -by + arm]]},
        {"v": [[bx, by - arm], [bx, by], [bx - arm, by]]},
        {"v": [[-bx + arm, by], [-bx, by], [-bx, by - arm]]},
    ]
    shapes = []
    for idx, c in enumerate(corners):
        p = {"c": False, "v": c["v"], "i": [[0, 0]] * 3, "o": [[0, 0]] * 3}
        shapes.append(
            {
                "ty": "gr",
                "nm": f"Corner{idx}",
                "it": [
                    {"ind": 0, "ty": "sh", "ks": {"a": 0, "k": p}},
                    {"ty": "st", "c": {"a": 0, "k": col}, "o": {"a": 0, "k": 100}, "w": {"a": 0, "k": 4}, "lc": 2, "lj": 2},
                    {"ty": "tr", "p": {"a": 0, "k": [0, 0]}, "a": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [100, 100]}, "r": {"a": 0, "k": 0}, "o": {"a": 0, "k": 100}},
                ],
            }
        )
    return {
        "v": "5.7.4",
        "fr": 30,
        "ip": 0,
        "op": dur_frames,
        "w": w,
        "h": h,
        "nm": "focus_corner_brackets",
        "ddd": 0,
        "assets": [],
        "layers": [
            {
                "ddd": 0,
                "ind": 1,
                "ty": 4,
                "nm": "Brackets",
                "sr": 1,
                "ks": {
                    "o": {"a": 1, "k": [{"t": 0, "s": [0]}, {"t": 6, "s": [92]}, {"t": max(10, dur_frames - 12), "s": [92]}, {"t": dur_frames, "s": [0]}]},
                    "r": {"a": 0, "k": 0},
                    "p": {"a": 0, "k": [w / 2, h / 2, 0]},
                    "a": {"a": 0, "k": [0, 0, 0]},
                    "s": {
                        "a": 1,
                        "k": [
                            {"t": 0, "s": [116, 116, 100], "i": {"x": [0.12, 0.12, 0.12], "y": [1, 1, 1]}, "o": {"x": [0.2, 0.2, 0.2], "y": [0, 0, 0]}},
                            {"t": 16, "s": [100, 100, 100]},
                        ],
                    },
                },
                "ao": 0,
                "shapes": shapes,
                "ip": 0,
                "op": dur_frames,
                "st": 0,
                "bm": 0,
            }
        ],
    }


def make_pulse_beacon(w=320, h=320, dur_frames=90, accent="#3B82F6"):
    col = hex_to_rgb01(accent)
    ring = circle_bezier_path(0, 0, 56, 56)
    dot = circle_bezier_path(0, 0, 10, 10)
    return {
        "v": "5.7.4",
        "fr": 30,
        "ip": 0,
        "op": dur_frames,
        "w": w,
        "h": h,
        "nm": "pulse_beacon",
        "ddd": 0,
        "assets": [],
        "layers": [
            {
                "ddd": 0,
                "ind": 1,
                "ty": 4,
                "nm": "CenterDot",
                "sr": 1,
                "ks": {
                    "o": {"a": 0, "k": 100},
                    "r": {"a": 0, "k": 0},
                    "p": {"a": 0, "k": [w / 2, h / 2, 0]},
                    "a": {"a": 0, "k": [0, 0, 0]},
                    "s": {"a": 0, "k": [100, 100, 100]},
                },
                "ao": 0,
                "shapes": [
                    {
                        "ty": "gr",
                        "it": [
                            {"ind": 0, "ty": "sh", "ks": {"a": 0, "k": dot}},
                            {"ty": "fl", "c": {"a": 0, "k": col}, "o": {"a": 0, "k": 100}},
                            {"ty": "tr", "p": {"a": 0, "k": [0, 0]}, "a": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [100, 100]}, "r": {"a": 0, "k": 0}, "o": {"a": 0, "k": 100}},
                        ],
                    }
                ],
                "ip": 0,
                "op": dur_frames,
                "st": 0,
                "bm": 0,
            },
            {
                "ddd": 0,
                "ind": 2,
                "ty": 4,
                "nm": "PulseWave",
                "sr": 1,
                "ks": {
                    "o": {"a": 1, "k": [{"t": 0, "s": [85]}, {"t": 45, "s": [0]}, {"t": 46, "s": [85]}, {"t": 90, "s": [0]}]},
                    "r": {"a": 0, "k": 0},
                    "p": {"a": 0, "k": [w / 2, h / 2, 0]},
                    "a": {"a": 0, "k": [0, 0, 0]},
                    "s": {"a": 1, "k": [{"t": 0, "s": [25, 25, 100]}, {"t": 45, "s": [135, 135, 100]}, {"t": 46, "s": [25, 25, 100]}, {"t": 90, "s": [135, 135, 100]}]},
                },
                "ao": 0,
                "shapes": [
                    {
                        "ty": "gr",
                        "it": [
                            {"ind": 0, "ty": "sh", "ks": {"a": 0, "k": ring}},
                            {"ty": "st", "c": {"a": 0, "k": col}, "o": {"a": 0, "k": 100}, "w": {"a": 0, "k": 3.5}},
                            {"ty": "tr", "p": {"a": 0, "k": [0, 0]}, "a": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [100, 100]}, "r": {"a": 0, "k": 0}, "o": {"a": 0, "k": 100}},
                        ],
                    }
                ],
                "ip": 0,
                "op": dur_frames,
                "st": 0,
                "bm": 0,
            },
        ],
    }


def make_marker_highlight(w=860, h=110, dur_frames=90, accent="#FACC15"):
    """Translucent highlighter marker sweep across a press clipping / document line."""
    col = hex_to_rgb01(accent)
    fade_out_start = max(24, dur_frames - 14)
    line_path = {
        "c": False,
        "v": [[-w * 0.44, 3], [0, -2], [w * 0.44, 1]],
        "i": [[0, 0], [-w * 0.14, 2], [-w * 0.12, -2]],
        "o": [[w * 0.14, -2], [w * 0.12, 2], [0, 0]],
    }
    return {
        "v": "5.7.4",
        "fr": 30,
        "ip": 0,
        "op": dur_frames,
        "w": w,
        "h": h,
        "nm": "editorial_marker_highlight",
        "ddd": 0,
        "assets": [],
        "layers": [
            {
                "ddd": 0,
                "ind": 1,
                "ty": 4,
                "nm": "MarkerSweep",
                "sr": 1,
                "ks": {
                    "o": {
                        "a": 1,
                        "k": [
                            {"t": 0, "s": [38]},
                            {"t": fade_out_start, "s": [38]},
                            {"t": dur_frames, "s": [0]},
                        ],
                    },
                    "r": {"a": 0, "k": 0},
                    "p": {"a": 0, "k": [w / 2, h / 2, 0]},
                    "a": {"a": 0, "k": [0, 0, 0]},
                    "s": {"a": 0, "k": [100, 100, 100]},
                },
                "ao": 0,
                "shapes": [
                    {
                        "ty": "gr",
                        "it": [
                            {"ind": 0, "ty": "sh", "ks": {"a": 0, "k": line_path}},
                            {
                                "ty": "tm",
                                "s": {"a": 0, "k": 0},
                                "e": {
                                    "a": 1,
                                    "k": [
                                        {"i": {"x": [0.18], "y": [1]}, "o": {"x": [0.32], "y": [0]}, "t": 0, "s": [0]},
                                        {"t": 22, "s": [100]},
                                    ],
                                },
                                "o": {"a": 0, "k": 0},
                                "m": 1,
                            },
                            {"ty": "st", "c": {"a": 0, "k": col}, "o": {"a": 0, "k": 100}, "w": {"a": 0, "k": h * 0.56}, "lc": 1, "lj": 2},
                            {"ty": "tr", "p": {"a": 0, "k": [0, 0]}, "a": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [100, 100]}, "r": {"a": 0, "k": 0}, "o": {"a": 0, "k": 100}},
                        ],
                    }
                ],
                "ip": 0,
                "op": dur_frames,
                "st": 0,
                "bm": 0,
            }
        ],
    }


def make_pointer_arrow(w=360, h=220, dur_frames=90, accent="#EA580C"):
    """Curved editorial callout arrow pointing toward a subject or stat."""
    col = hex_to_rgb01(accent)
    fade_out_start = max(24, dur_frames - 14)
    shaft = {
        "c": False,
        "v": [[-w * 0.36, -h * 0.28], [-w * 0.04, h * 0.08], [w * 0.34, h * 0.20]],
        "i": [[0, 0], [-w * 0.10, -h * 0.14], [-w * 0.12, -h * 0.02]],
        "o": [[w * 0.10, h * 0.16], [w * 0.12, h * 0.08], [0, 0]],
    }
    head = {
        "c": False,
        "v": [[w * 0.22, h * 0.08], [w * 0.35, h * 0.20], [w * 0.20, h * 0.30]],
        "i": [[0, 0], [0, 0], [0, 0]],
        "o": [[0, 0], [0, 0], [0, 0]],
    }
    return {
        "v": "5.7.4",
        "fr": 30,
        "ip": 0,
        "op": dur_frames,
        "w": w,
        "h": h,
        "nm": "editorial_pointer_arrow",
        "ddd": 0,
        "assets": [],
        "layers": [
            {
                "ddd": 0,
                "ind": 1,
                "ty": 4,
                "nm": "ArrowGroup",
                "sr": 1,
                "ks": {
                    "o": {"a": 1, "k": [{"t": 0, "s": [100]}, {"t": fade_out_start, "s": [100]}, {"t": dur_frames, "s": [0]}]},
                    "r": {"a": 0, "k": 0},
                    "p": {"a": 0, "k": [w / 2, h / 2, 0]},
                    "a": {"a": 0, "k": [0, 0, 0]},
                    "s": {"a": 0, "k": [100, 100, 100]},
                },
                "ao": 0,
                "shapes": [
                    {
                        "ty": "gr",
                        "it": [
                            {"ind": 0, "ty": "sh", "ks": {"a": 0, "k": shaft}},
                            {"ind": 1, "ty": "sh", "ks": {"a": 0, "k": head}},
                            {
                                "ty": "tm",
                                "s": {"a": 0, "k": 0},
                                "e": {"a": 1, "k": [{"i": {"x": [0.2], "y": [1]}, "o": {"x": [0.3], "y": [0]}, "t": 0, "s": [0]}, {"t": 20, "s": [100]}]},
                                "o": {"a": 0, "k": 0},
                                "m": 1,
                            },
                            {"ty": "st", "c": {"a": 0, "k": col}, "o": {"a": 0, "k": 100}, "w": {"a": 0, "k": 5.0}, "lc": 2, "lj": 2},
                            {"ty": "tr", "p": {"a": 0, "k": [0, 0]}, "a": {"a": 0, "k": [0, 0]}, "s": {"a": 0, "k": [100, 100]}, "r": {"a": 0, "k": 0}, "o": {"a": 0, "k": 100}},
                        ],
                    }
                ],
                "ip": 0,
                "op": dur_frames,
                "st": 0,
                "bm": 0,
            }
        ],
    }


def _build_preset_json(kind: str, dur_frames: int, accent: str, bg: str) -> dict:
    if kind in ("minimal_lower_third", "lower_third_bar"):
        return make_minimal_lower_third(dur_frames=dur_frames, accent=accent, dark=bg)
    if kind in ("focus_corner_brackets", "corner_brackets"):
        return make_focus_corner_brackets(dur_frames=dur_frames, accent=accent)
    if kind == "handdrawn_underline":
        return make_handdrawn_underline(dur_frames=dur_frames, accent=accent)
    if kind == "handdrawn_circle":
        return make_handdrawn_circle(dur_frames=dur_frames, accent=accent)
    if kind == "marker_highlight":
        return make_marker_highlight(dur_frames=dur_frames, accent=accent)
    if kind == "pointer_arrow":
        return make_pointer_arrow(dur_frames=dur_frames, accent=accent)
    return make_pulse_beacon(dur_frames=dur_frames, accent=accent)


def _infer_kind_from_path(file_path: str, layout: str = "") -> str:
    low = os.path.basename(file_path).lower()
    if "marker" in low or "highlight" in low or layout == "press_evidence_highlight":
        return "marker_highlight"
    if "arrow" in low or "pointer" in low:
        return "pointer_arrow"
    if "bracket" in low or "focus" in low:
        return "focus_corner_brackets"
    if "under" in low:
        return "handdrawn_underline"
    if "circle" in low or "ring" in low:
        return "handdrawn_circle"
    if "pulse" in low or "beacon" in low:
        return "pulse_beacon"
    return "minimal_lower_third"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-dir", help="Batch-generate all lottie_overlay files referenced in storyboard.json")
    ap.add_argument(
        "--kind",
        required=False,
        choices=[
            "minimal_lower_third",
            "lower_third_bar",
            "focus_corner_brackets",
            "corner_brackets",
            "handdrawn_underline",
            "handdrawn_circle",
            "pulse_beacon",
            "marker_highlight",
            "pointer_arrow",
        ],
    )
    ap.add_argument("--out", required=False)
    ap.add_argument("--duration", type=float, default=3.5)
    ap.add_argument("--accent", default="#C84B31")
    ap.add_argument("--bg", default="#0D121A")
    args = ap.parse_args()

    if args.project_dir:
        sb_path = os.path.join(args.project_dir, "storyboard.json")
        if not os.path.isfile(sb_path):
            raise FileNotFoundError(f"storyboard.json not found in {args.project_dir}")
        sb = json.load(open(sb_path, "r", encoding="utf-8"))
        dna = sb.get("style_dna") or {}
        def_accent = dna.get("accent") or args.accent
        def_bg = dna.get("studio_bg") or args.bg
        fps = int(sb.get("fps") or 30)
        built = 0
        for sc in sb.get("scenes", []):
            ov = sc.get("lottie_overlay")
            if not isinstance(ov, dict) or not ov.get("file"):
                continue
            rel_f = ov["file"]
            out_p = rel_f if os.path.isabs(rel_f) else os.path.join(args.project_dir, rel_f)
            if os.path.isfile(out_p) and os.path.getsize(out_p) > 50 and not ov.get("overwrite"):
                continue
            dur_s = float(ov.get("duration") or max(2.2, (sc.get("end_ms", 3500) - sc.get("start_ms", 0)) / 1000.0 - 0.3))
            frames = max(24, int(round(dur_s * fps)))
            kind = ov.get("kind") or _infer_kind_from_path(out_p, str(sc.get("layout", "")))
            accent = ov.get("accent") or ("#FACC15" if kind == "marker_highlight" else def_accent)
            data = _build_preset_json(kind, frames, accent, def_bg)
            os.makedirs(os.path.dirname(os.path.abspath(out_p)), exist_ok=True)
            with open(out_p, "w", encoding="utf-8") as f:
                json.dump(data, f, separators=(",", ":"))
            built += 1
        print(f"[lottie] Batch OK -> generated {built} missing overlay(s) in {args.project_dir}")
        return

    if not args.kind or not args.out:
        ap.error("Provide --project-dir OR both (--kind and --out)")

    frames = max(24, int(round(args.duration * 30)))
    data = _build_preset_json(args.kind, frames, args.accent, args.bg)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))
    print(f"[lottie] OK -> {args.out} ({os.path.getsize(args.out)} bytes, kind={args.kind})")


if __name__ == "__main__":
    main()
