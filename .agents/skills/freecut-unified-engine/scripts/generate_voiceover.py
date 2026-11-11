#!/usr/bin/env python3
"""
Standalone Neural Voiceover Generator for FreeCut (v6.1)
========================================================
When a user provides ONLY a written script (.txt) and has no recorded audio,
this tool generates broadcast-clean narration + exact millisecond `words.json`
and `subtitles.srt` 100% standalone with zero mandatory paid APIs!

Supported Engines:
  1. `edge` (DEFAULT — 100% FREE, ZERO API KEY!):
     Uses Microsoft `edge-tts` neural voices (`pt-BR-AntonioNeural`, `pt-BR-FranciscaNeural`,
     `en-US-AndrewMultilingualNeural`, `es-MX-JorgeNeural`, etc.) and captures native
     `WordBoundary` events directly into `words.json`!
  2. `elevenlabs` (Optional if `ELEVENLABS_API_KEY` is in `.env`):
     Calls ElevenLabs `/v1/text-to-speech/{voice_id}/with-timestamps` and converts
     character-level alignment directly into exact `words.json`!
"""
import argparse
import asyncio
import base64
import json
import os
import sys
import requests

DEFAULT_VOICES = {
    "pt": "pt-BR-AntonioNeural",
    "pt-br": "pt-BR-AntonioNeural",
    "en": "en-US-AndrewMultilingualNeural",
    "es": "es-MX-JorgeNeural",
    "fr": "fr-FR-HenriNeural",
    "de": "de-DE-ConradNeural",
}


def load_env_keys(extra_paths=None) -> dict:
    keys = dict(os.environ)
    for p in list(extra_paths or []) + [os.path.join(os.getcwd(), ".env")]:
        if p and os.path.isfile(p):
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        keys.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    return keys


async def _edge_tts_synthesize(text: str, voice: str, rate: str, out_mp3: str) -> list:
    import edge_tts

    communicate = edge_tts.Communicate(text, voice=voice, rate=rate, boundary="WordBoundary")
    words = []
    with open(out_mp3, "wb") as audio_f:
        async for chunk in communicate.stream():
            ctype = chunk.get("type")
            if ctype == "audio":
                audio_f.write(chunk["data"])
            elif ctype == "WordBoundary":
                # edge-tts offset & duration are in 100-nanosecond ticks (1 ms = 10,000 ticks)
                s_ms = int(round(chunk["offset"] / 10000.0))
                dur_ms = max(25, int(round(chunk["duration"] / 10000.0)))
                tok = (chunk.get("text") or "").strip()
                if tok:
                    words.append({
                        "word": tok,
                        "start_ms": s_ms,
                        "end_ms": s_ms + dur_ms,
                        "confidence": 1.0,
                    })
    return words


def synthesize_elevenlabs(text: str, api_key: str, voice_id: str, out_mp3: str) -> list:
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps"
    r = requests.post(
        url,
        headers={"xi-api-key": api_key, "Content-Type": "application/json"},
        json={
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.78},
        },
        timeout=180,
    )
    r.raise_for_status()
    data = r.json()
    audio_bytes = base64.b64decode(data["audio_base64"])
    with open(out_mp3, "wb") as f:
        f.write(audio_bytes)

    align = data.get("alignment") or {}
    chars = align.get("characters") or []
    starts = align.get("character_start_times_seconds") or []
    ends = align.get("character_end_times_seconds") or []

    words = []
    cur_chars = []
    w_start = None
    w_end = None
    for ch, st, en in zip(chars, starts, ends):
        if ch.isspace():
            if cur_chars:
                words.append({
                    "word": "".join(cur_chars),
                    "start_ms": int(round(w_start * 1000)),
                    "end_ms": max(int(round(w_start * 1000)) + 20, int(round(w_end * 1000))),
                    "confidence": 1.0,
                })
                cur_chars = []
                w_start = None
        else:
            if w_start is None:
                w_start = st
            w_end = en
            cur_chars.append(ch)
    if cur_chars and w_start is not None:
        words.append({
            "word": "".join(cur_chars),
            "start_ms": int(round(w_start * 1000)),
            "end_ms": max(int(round(w_start * 1000)) + 20, int(round(w_end * 1000))),
            "confidence": 1.0,
        })
    return words


def main():
    ap = argparse.ArgumentParser(description="Standalone Free Voiceover + Word Alignment Generator")
    ap.add_argument("--script", required=True, help="Path to UTF-8 text script (.txt) or literal text")
    ap.add_argument("--out-dir", required=True, help="Project directory")
    ap.add_argument("--lang", default="pt-BR", help="Language tag (pt-BR, en, es, etc.)")
    ap.add_argument("--voice", default=None, help="Edge-TTS voice name or ElevenLabs voice_id")
    ap.add_argument("--rate", default="+4%", help="Edge-TTS speaking rate (e.g. '+0%%', '+5%%')")
    ap.add_argument("--engine", default="edge", choices=["edge", "elevenlabs"], help="Default: 'edge' (100%% free)")
    args = ap.parse_args()

    text = open(args.script, "r", encoding="utf-8").read().strip() if os.path.isfile(args.script) else args.script.strip()
    if not text:
        sys.exit("[ERROR] Empty script provided.")

    os.makedirs(args.out_dir, exist_ok=True)
    out_mp3 = os.path.join(args.out_dir, "narration.mp3")
    words_path = os.path.join(args.out_dir, "words.json")

    keys = load_env_keys([os.path.join(args.out_dir, ".env")])
    if args.engine == "elevenlabs":
        el_key = keys.get("ELEVENLABS_API_KEY", "").strip()
        if not el_key:
            sys.exit("[ERROR] ELEVENLABS_API_KEY missing in .env")
        voice_id = args.voice or keys.get("ELEVENLABS_VOICE_ID") or "pNInz6obpgDQGcFmaJgB"
        words = synthesize_elevenlabs(text, el_key, voice_id, out_mp3)
    else:
        voice = args.voice or DEFAULT_VOICES.get(args.lang.lower(), DEFAULT_VOICES.get(args.lang.split("-")[0].lower(), "pt-BR-AntonioNeural"))
        words = asyncio.run(_edge_tts_synthesize(text, voice, args.rate, out_mp3))

    # Fallback to local faster-whisper if network/voice omitted boundary events
    if not words:
        from transcribe_audio import transcribe_local_faster_whisper
        words = transcribe_local_faster_whisper(out_mp3, lang=args.lang)

    with open(words_path, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=2)

    from transcribe_audio import write_srt_from_words
    write_srt_from_words(words, os.path.join(args.out_dir, "subtitles.srt"))

    dur = (words[-1]["end_ms"] / 1000.0) if words else 0.0
    print(f"[voiceover] OK ({args.engine}) -> {out_mp3} ({dur:.1f}s, {len(words)} words aligned)")


if __name__ == "__main__":
    main()
