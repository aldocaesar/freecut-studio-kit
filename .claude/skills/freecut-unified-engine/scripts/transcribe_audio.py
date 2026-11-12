#!/usr/bin/env python3
"""
Universal Word-Level Audio & Video Transcriber for FreeCut (v6.1)
=================================================================
100% standalone — ZERO external private services or mandatory paid APIs!

Accepts ANY audio (.mp3, .wav, .m4a, .ogg, .flac) OR video (.mp4, .mov, .mkv, .webm)
and produces exact millisecond word-level alignment (`words.json` + `subtitles.srt`).

Engine Priority (`--engine auto` default):
  1. `--from-srt <file.srt>` : Instant zero-cost alignment from an existing SRT file.
  2. `groq` (`GROQ_API_KEY`) : Optional ultra-fast cloud Whisper (`whisper-large-v3-turbo`, free tier available).
  3. `assemblyai` (`ASSEMBLYAI_API_KEY`) : Optional cloud AssemblyAI Universal-2 word timestamps.
  4. `local` (`faster-whisper`): 100% FREE, offline, zero API key! Uses GPU CUDA if cuBLAS is available,
     with automatic crash-proof fallback to multi-core CPU (`int8`) on Windows/macOS/Linux.
"""
import argparse
import ctypes
import json
import os
import re
import subprocess
import sys
import tempfile
import time

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)
import _runtime_env  # noqa: E402
_runtime_env.init()

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
import requests

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}
VOICE_MEMO_EXTS = {".opus", ".oga", ".ogg", ".aac", ".amr", ".3gp", ".wma", ".caf", ".flac"}


def load_env_keys(extra_paths=None) -> dict:
    keys = dict(os.environ)
    candidates = list(extra_paths or []) + [
        os.path.join(os.getcwd(), ".env"),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".env")),
    ]
    for p in candidates:
        if p and os.path.isfile(p):
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        keys.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    return keys


def ensure_audio_file(input_path: str, out_dir: str) -> str:
    """Extract/normalize video or voice-note formats (.opus/.ogg/.aac/etc.) to crisp 44.1kHz WAV for both Whisper & FreeCut."""
    ext = os.path.splitext(input_path)[1].lower()
    if ext not in VIDEO_EXTS and ext not in VOICE_MEMO_EXTS:
        return input_path
    os.makedirs(out_dir, exist_ok=True)
    wav_out = os.path.join(out_dir, "extracted_audio.wav")
    cmd = [
        "ffmpeg", "-nostdin", "-y", "-i", input_path,
        "-vn", "-ar", "44100", "-c:a", "pcm_s16le",
        wav_out,
    ]
    res = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True)
    if res.returncode != 0 or not os.path.isfile(wav_out):
        raise RuntimeError(f"FFmpeg audio extraction failed: {res.stderr[-400:]}")
    kind = "video" if ext in VIDEO_EXTS else f"audio ({ext})"
    print(f"[transcribe] Normalized {kind} to 44.1kHz WAV -> {wav_out}")
    return wav_out


def _ts_to_ms(ts: str) -> int:
    ts = ts.strip().replace(".", ",")
    hms, ms = ts.split(",")
    h, m, s = [int(x) for x in hms.split(":")]
    return ((h * 3600 + m * 60 + s) * 1000) + int(ms[:3].ljust(3, "0"))


def _ms_to_srt_ts(ms: int) -> str:
    ms = max(0, int(ms))
    h = ms // 3600000
    ms %= 3600000
    m = ms // 60000
    ms %= 60000
    s = ms // 1000
    rem = ms % 1000
    return f"{h:02d}:{m:02d}:{s:02d},{rem:03d}"


def parse_srt_to_words(srt_path: str) -> list:
    raw = open(srt_path, "r", encoding="utf-8-sig", errors="ignore").read()
    blocks = re.split(r"\n\s*\n", raw.strip())
    words = []
    for b in blocks:
        lines = [ln.strip() for ln in b.strip().splitlines() if ln.strip()]
        if len(lines) < 2:
            continue
        ts_line = lines[1] if "-->" in lines[1] else (lines[0] if "-->" in lines[0] else None)
        if not ts_line:
            continue
        txt_start = 2 if ts_line == lines[1] else 1
        text = " ".join(lines[txt_start:]).strip()
        text = re.sub(r"<[^>]+>", "", text).strip()
        if not text:
            continue
        p0, p1 = [x.strip() for x in ts_line.split("-->")[:2]]
        s_ms, e_ms = _ts_to_ms(p0), _ts_to_ms(p1)
        tokens = text.split()
        dur = max(1, e_ms - s_ms)
        total_chars = max(1, sum(len(t) for t in tokens))
        cur = s_ms
        for idx, tok in enumerate(tokens):
            share = int(round(dur * (len(tok) / total_chars)))
            w_end = e_ms if idx == len(tokens) - 1 else min(e_ms, cur + max(20, share))
            words.append({
                "word": tok,
                "start_ms": cur,
                "end_ms": max(cur + 15, w_end),
                "confidence": 1.0,
            })
            cur = w_end
    return words


def write_srt_from_words(words: list, srt_path: str, max_words_per_cue: int = 5):
    if not words:
        return
    cues = []
    buf = []
    for w in words:
        buf.append(w)
        tok = w["word"]
        gap_break = len(buf) >= 2 and (w["start_ms"] - buf[-2]["end_ms"] > 450)
        if gap_break and len(buf) > 1:
            last = buf.pop()
            cues.append(buf)
            buf = [last]
            continue
        if len(buf) >= max_words_per_cue or tok.endswith((".", "!", "?", ":", ";")):
            cues.append(buf)
            buf = []
    if buf:
        cues.append(buf)

    lines = []
    for idx, chunk in enumerate(cues, 1):
        s_ms = chunk[0]["start_ms"]
        e_ms = max(s_ms + 120, chunk[-1]["end_ms"])
        txt = " ".join(x["word"] for x in chunk)
        lines.append(f"{idx}\n{_ms_to_srt_ts(s_ms)} --> {_ms_to_srt_ts(e_ms)}\n{txt}\n")
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def write_compact_words(words: list, compact_path: str, window_ms: int = 8000):
    """Writes a token-lean word-timestamp digest (~75 lines for a 10-min video vs 6,000 lines in words.json)."""
    if not words:
        return
    lines = [
        "# Compact Word-Timestamp Index (word@start_s) — Read THIS file instead of words.json or raw audio!"
    ]
    chunk = []
    win_start = words[0]["start_ms"]
    for w in words:
        chunk.append(w)
        tok = str(w.get("word", ""))
        elapsed = w["end_ms"] - win_start
        if elapsed >= window_ms or (elapsed >= 4500 and tok.endswith((".", "!", "?", ";"))):
            s0 = chunk[0]["start_ms"]
            e0 = chunk[-1]["end_ms"]
            body = " ".join(f"{x['word']}@{x['start_ms']/1000.0:.2f}" for x in chunk)
            lines.append(f"[{s0}ms..{e0}ms] {body}")
            chunk = []
            win_start = e0
    if chunk:
        s0 = chunk[0]["start_ms"]
        e0 = chunk[-1]["end_ms"]
        body = " ".join(f"{x['word']}@{x['start_ms']/1000.0:.2f}" for x in chunk)
        lines.append(f"[{s0}ms..{e0}ms] {body}")
    with open(compact_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _prepare_windows_cuda_dlls() -> bool:
    """Register pip-installed NVIDIA cuBLAS/cuDNN DLL folders on Windows and verify cublas loads."""
    if os.name != "nt":
        return True
    site_dirs = [p for p in sys.path if "site-packages" in p.lower() and os.path.isdir(p)]
    rel_candidates = [
        os.path.join("nvidia", "cublas", "bin"),
        os.path.join("nvidia", "cudnn", "bin"),
        os.path.join("torch", "lib"),
    ]
    for sd in site_dirs:
        for rel in rel_candidates:
            dll_dir = os.path.join(sd, rel)
            if os.path.isdir(dll_dir):
                try:
                    os.add_dll_directory(dll_dir)
                except Exception:
                    pass
                os.environ["PATH"] = dll_dir + os.pathsep + os.environ.get("PATH", "")
    for dll_name in ("cublas64_12.dll", "cublas64_11.dll"):
        try:
            ctypes.WinDLL(dll_name)
            return True
        except OSError:
            continue
    return False


def _run_whisper_pass(
    WhisperModel,
    audio_path: str,
    model_size: str,
    device: str,
    compute_type: str,
    lang_arg: str | None,
    initial_prompt: str | None,
) -> tuple[list, str]:
    kwargs = {"device": device, "compute_type": compute_type}
    if device == "cpu":
        kwargs["cpu_threads"] = max(2, min(12, os.cpu_count() or 4))
    print(f"[transcribe] Local FREE faster-whisper (model='{model_size}', device='{device}', compute='{compute_type}')...")
    model = WhisperModel(model_size, **kwargs)
    segments_gen, info = model.transcribe(
        audio_path,
        language=lang_arg,
        initial_prompt=initial_prompt or None,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 280},
    )
    # Materialize generator inside try-block so lazy CUDA DLL errors are caught cleanly
    segments = list(segments_gen)
    words = []
    for seg in segments:
        if getattr(seg, "words", None):
            for w in seg.words:
                tok = (w.word or "").strip()
                if not tok:
                    continue
                s_ms = int(round(w.start * 1000))
                e_ms = max(s_ms + 20, int(round(w.end * 1000)))
                words.append({
                    "word": tok,
                    "start_ms": s_ms,
                    "end_ms": e_ms,
                    "confidence": round(float(getattr(w, "probability", 0.95)), 4),
                })
        else:
            toks = (seg.text or "").strip().split()
            if not toks:
                continue
            s_ms = int(round(seg.start * 1000))
            e_ms = max(s_ms + 50, int(round(seg.end * 1000)))
            step = max(20, (e_ms - s_ms) // len(toks))
            for idx, tok in enumerate(toks):
                ws = s_ms + idx * step
                we = e_ms if idx == len(toks) - 1 else ws + step
                words.append({"word": tok, "start_ms": ws, "end_ms": we, "confidence": 0.9})
    detected = getattr(info, "language", lang_arg or "auto")
    return words, detected


def transcribe_local_faster_whisper(
    audio_path: str,
    lang: str = "auto",
    model_size: str = "small",
    initial_prompt: str | None = None,
) -> list:
    """100% FREE local word-level transcription via faster-whisper (zero API key, auto CUDA->CPU fallback)."""
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "faster-whisper is not installed. Run the installer (`install.ps1` / `install.sh`) "
            "or `pip install faster-whisper`."
        ) from exc

    lang_arg = None if (not lang or lang.lower() == "auto") else lang.split("-")[0].lower()
    try_cuda = False
    try:
        import ctranslate2
        if ctranslate2.get_cuda_device_count() > 0 and _prepare_windows_cuda_dlls():
            try_cuda = True
    except Exception:
        try_cuda = False

    if try_cuda:
        try:
            words, detected = _run_whisper_pass(
                WhisperModel, audio_path, model_size, "cuda", "float16", lang_arg, initial_prompt
            )
            print(f"[transcribe] faster-whisper (CUDA) detected language='{detected}', aligned {len(words)} words.")
            return words
        except Exception as cuda_exc:
            print(f"[transcribe] CUDA runtime unavailable ({cuda_exc}); falling back automatically to CPU int8...")

    words, detected = _run_whisper_pass(
        WhisperModel, audio_path, model_size, "cpu", "int8", lang_arg, initial_prompt
    )
    print(f"[transcribe] faster-whisper (CPU int8) detected language='{detected}', aligned {len(words)} words.")
    return words


def transcribe_groq(audio_path: str, api_key: str, lang: str = "auto", initial_prompt: str | None = None) -> list:
    """Optional ultra-fast cloud Whisper via Groq API (`whisper-large-v3-turbo`)."""
    print("[transcribe] Uploading audio to Groq Whisper (`whisper-large-v3-turbo`)...")
    # Compress large files or uncompressed WAVs > 8MB to lightweight mono 64kbps mp3 (stays well under Groq 25MB cap)
    send_path = audio_path
    tmp_mp3 = None
    ext = os.path.splitext(audio_path)[1].lower()
    fsize = os.path.getsize(audio_path)
    if fsize > 18 * 1024 * 1024 or (ext == ".wav" and fsize > 8 * 1024 * 1024):
        fd, tmp_mp3 = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        subprocess.run(
            ["ffmpeg", "-nostdin", "-y", "-i", audio_path, "-vn", "-ac", "1", "-ar", "16000", "-b:a", "64k", tmp_mp3],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=True,
        )
        send_path = tmp_mp3

    try:
        data = {
            "model": "whisper-large-v3-turbo",
            "response_format": "verbose_json",
            "timestamp_granularities[]": "word",
        }
        if lang and lang.lower() != "auto":
            data["language"] = lang.split("-")[0].lower()
        if initial_prompt:
            data["prompt"] = initial_prompt[:800]

        with open(send_path, "rb") as f:
            r = requests.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {api_key}"},
                data=data,
                files={"file": (os.path.basename(send_path), f)},
                timeout=180,
            )
        r.raise_for_status()
        payload = r.json()
        words = []
        for w in payload.get("words", []):
            tok = (w.get("word") or "").strip()
            if not tok:
                continue
            s_ms = int(round(float(w["start"]) * 1000))
            e_ms = max(s_ms + 20, int(round(float(w["end"]) * 1000)))
            words.append({"word": tok, "start_ms": s_ms, "end_ms": e_ms, "confidence": 0.98})
        return words
    finally:
        if tmp_mp3 and os.path.isfile(tmp_mp3):
            try:
                os.remove(tmp_mp3)
            except OSError:
                pass


def transcribe_assemblyai(audio_path: str, api_key: str, lang: str = "auto") -> list:
    """Optional cloud AssemblyAI Universal-2 word-level transcription."""
    headers = {"authorization": api_key}
    print("[transcribe] Uploading audio to AssemblyAI...")
    with open(audio_path, "rb") as f:
        r_up = requests.post("https://api.assemblyai.com/v2/upload", headers=headers, data=f, timeout=300)
    r_up.raise_for_status()
    upload_url = r_up.json()["upload_url"]

    payload = {"audio_url": upload_url, "speech_models": ["universal-2"]}
    if not lang or lang.lower() == "auto":
        payload["language_detection"] = True
    else:
        payload["language_code"] = lang.split("-")[0].lower()

    r_tx = requests.post(
        "https://api.assemblyai.com/v2/transcript",
        headers={**headers, "content-type": "application/json"},
        json=payload,
        timeout=60,
    )
    r_tx.raise_for_status()
    tx_id = r_tx.json()["id"]

    poll_url = f"https://api.assemblyai.com/v2/transcript/{tx_id}"
    while True:
        res = requests.get(poll_url, headers=headers, timeout=30).json()
        status = res.get("status")
        if status == "completed":
            break
        if status == "error":
            raise RuntimeError(f"AssemblyAI Error: {res.get('error')}")
        time.sleep(2.5)

    return [
        {
            "word": w["text"],
            "start_ms": int(w["start"]),
            "end_ms": int(w["end"]),
            "confidence": round(float(w.get("confidence", 1.0)), 4),
        }
        for w in res.get("words", [])
    ]


def main():
    ap = argparse.ArgumentParser(description="Universal FreeCut Word-Level Transcriber (Free Local Default)")
    ap.add_argument("--audio", required=True, help="Input audio (.mp3/.wav/.m4a) OR video (.mp4/.mov)")
    ap.add_argument("--out-dir", required=True, help="Project output folder")
    ap.add_argument("--lang", default="auto", help="Language code (pt, en, es, or auto)")
    ap.add_argument("--from-srt", default=None, help="Optional existing word/phrase .srt file (instant, zero compute)")
    ap.add_argument(
        "--engine",
        default="auto",
        choices=["auto", "local", "groq", "assemblyai"],
        help="Transcription engine: 'local' (100%% free faster-whisper), 'groq', 'assemblyai', or 'auto' (prefers local unless cloud key set or falls back to local)",
    )
    ap.add_argument(
        "--whisper-model",
        default="small",
        help="Local faster-whisper model size ('tiny', 'base', 'small', 'medium', 'large-v3-turbo'). Default: 'small'",
    )
    ap.add_argument(
        "--prompt",
        default=None,
        help="Optional proper-noun / topic hint to boost Whisper spelling accuracy (e.g. 'Kigali, Ruanda, Fanta Citron')",
    )
    args = ap.parse_args()

    if not os.path.isfile(args.audio):
        sys.exit(f"[ERROR] Input file not found: {args.audio}")

    os.makedirs(args.out_dir, exist_ok=True)
    words_path = os.path.join(args.out_dir, "words.json")
    srt_out_path = os.path.join(args.out_dir, "subtitles.srt")
    compact_path = os.path.join(args.out_dir, "words_compact.txt")

    # 1. Instant SRT path
    if args.from_srt and os.path.isfile(args.from_srt):
        words = parse_srt_to_words(args.from_srt)
        with open(words_path, "w", encoding="utf-8") as f:
            json.dump(words, f, ensure_ascii=False, indent=2)
        if os.path.abspath(args.from_srt) != os.path.abspath(srt_out_path):
            write_srt_from_words(words, srt_out_path)
        write_compact_words(words, compact_path)
        dur = (words[-1]["end_ms"] / 1000.0) if words else 0.0
        print(f"[transcribe] OK (SRT) -> {len(words)} words ({dur:.1f}s) saved to {compact_path} + {words_path}")
        return

    # Ensure clean audio if video was provided
    audio_file = ensure_audio_file(args.audio, args.out_dir)
    keys = load_env_keys([os.path.join(args.out_dir, ".env")])

    groq_key = keys.get("GROQ_API_KEY", "").strip()
    aai_key = keys.get("ASSEMBLYAI_API_KEY", "").strip()

    words = None
    engine_used = None

    if args.engine == "local":
        words = transcribe_local_faster_whisper(
            audio_file, lang=args.lang, model_size=args.whisper_model, initial_prompt=args.prompt
        )
        engine_used = f"local:faster-whisper({args.whisper_model})"
    elif args.engine == "groq":
        if not groq_key:
            sys.exit("[ERROR] --engine groq requested, but GROQ_API_KEY is not set.")
        words = transcribe_groq(audio_file, groq_key, lang=args.lang, initial_prompt=args.prompt)
        engine_used = "cloud:groq"
    elif args.engine == "assemblyai":
        if not aai_key:
            sys.exit("[ERROR] --engine assemblyai requested, but ASSEMBLYAI_API_KEY is not set.")
        words = transcribe_assemblyai(audio_file, aai_key, lang=args.lang)
        engine_used = "cloud:assemblyai"
    else:
        # AUTO mode: Try fast cloud if user explicitly configured a key; otherwise 100% FREE local faster-whisper!
        if groq_key:
            try:
                words = transcribe_groq(audio_file, groq_key, lang=args.lang, initial_prompt=args.prompt)
                if words:
                    engine_used = "cloud:groq"
            except Exception as e:
                print(f"[transcribe] Groq failed ({e}), falling back to FREE local faster-whisper...")
        if not words and aai_key:
            try:
                words = transcribe_assemblyai(audio_file, aai_key, lang=args.lang)
                if words:
                    engine_used = "cloud:assemblyai"
            except Exception as e:
                print(f"[transcribe] AssemblyAI failed ({e}), falling back to FREE local faster-whisper...")
        if not words:
            words = transcribe_local_faster_whisper(
                audio_file, lang=args.lang, model_size=args.whisper_model, initial_prompt=args.prompt
            )
            engine_used = f"local:faster-whisper({args.whisper_model})"

    with open(words_path, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False, indent=2)
    write_srt_from_words(words, srt_out_path)
    write_compact_words(words, compact_path)

    dur = (words[-1]["end_ms"] / 1000.0) if words else 0.0
    print(f"[transcribe] OK [{engine_used}] -> {len(words)} words ({dur:.1f}s) | {compact_path} + {srt_out_path}")


if __name__ == "__main__":
    main()
