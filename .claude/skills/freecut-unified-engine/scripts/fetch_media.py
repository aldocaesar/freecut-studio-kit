"""
fetch_media.py — Exact Multi-Source Documentary Media Hunter & Visual Contact-Sheet Validator (v5).
Built cleanly on top of vcy-AGOSTO's visual_asset_agent (100% zero FREECUT-card inheritance):
  - Specific Entities (`specific: true`):
      * STRICTLY BLOCKS generic stock (Pexels / Pixabay) so wrong generic people/objects never enter.
      * Specific Videos: YouTube / Shorts excerpt via `yt-dlp --download-sections` (normalized 1080p30, -g 30, muted).
      * Specific Images: Bing Images (murl JSON) + DuckDuckGo Images (vqd) + Yandex Images + Google News RSS Article Scraper (`og:image` / `<figcaption>`) + Wikimedia Commons + TMDB Official 1080p/4K Stills.
  - Ambient / Conceptual B-Roll (`specific: false`):
      * Pexels HD Video/Photo API -> Pixabay Video/Photo API -> Openverse API.
  - Validation & Human-Grade Framing:
      * Metadata surgical ranker + RapidOCR anti-watermark & label boost + 64-bit dHash anti-duplication.
      * Downloads Top-4 candidates per specific scene and builds `media/contact_sheet.jpg` for Vision inspection.
      * Supports instant candidate swap (`--select S02=3 S05=2`) and generates `media/backdrops/{sid}_blur.jpg`
        for portrait/square real photos so heads/labels are NEVER chopped by forced 16:9 cropping.
"""
import argparse
import concurrent.futures
import hashlib
import html as html_lib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.parse

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)
import _runtime_env  # noqa: E402
_runtime_env.init()

import requests
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

try:
    from bs4 import BeautifulSoup
except Exception:
    BeautifulSoup = None

try:
    from rapidocr_onnxruntime import RapidOCR
    _OCR_ENGINE = RapidOCR()
except Exception:
    _OCR_ENGINE = None

BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)
WIKI_HEADERS = {
    "User-Agent": "OpenBotFreeCutStudio/5.0 (Documentary Editorial Pipeline; local@openbot.ai)"
}
WEB_HEADERS = {
    "User-Agent": BROWSER_UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}

STOPWORDS = {
    "can", "in", "on", "at", "for", "with", "the", "a", "an", "by", "from", "to", "and", "or", "of",
    "de", "da", "do", "das", "dos", "em", "no", "na", "um", "uma", "com", "para", "por", "foto", "image",
    "official", "real", "hd", "4k", "photo", "picture",
}
WATERMARKS = (
    "shutterstock", "gettyimages", "getty images", "alamy", "istockphoto", "istock",
    "dreamstime", "123rf", "depositphotos", "vecteezy", "watermark", "stock photo",
)
IGNORED_URL_PARTS = (
    "logo", "icon", "avatar", "badge", "tracker", "pixel", "banner_ad", "sprite",
    "spinner", "placeholder", "loading", "thumb_default", ".svg", ".gif",
    "shutterstock", "gettyimages", "alamy", "istockphoto", "dreamstime", "123rf", "depositphotos",
    "lh3.googleusercontent.com/j6_cofbogxh",
)

USED_URLS = set()
USED_DHASHES = []
STATE_LOCK = threading.Lock()
DDG_LOCK = threading.Lock()
_LAST_DDG_TS = 0.0
_ZERO_KEY_AMBIENT_VIDEOS = [0]
_ZERO_KEY_AMBIENT_CAP = [4]


def load_env_keys(extra_paths=None) -> dict:
    keys = {
        "PEXELS_API_KEY": os.environ.get("PEXELS_API_KEY", "").strip(),
        "PIXABAY_API_KEY": os.environ.get("PIXABAY_API_KEY", "").strip(),
        "TMDB_API_KEY": os.environ.get("TMDB_API_KEY", "").strip(),
    }
    search_paths = list(extra_paths or []) + [
        os.path.join(os.getcwd(), ".env"),
    ]
    appdata = os.environ.get("APPDATA") or os.path.expanduser("~/.config")
    vault_dirs = [
        os.path.join(appdata, "OpenBot", "agent-api-keys", ".vault"),
    ]
    for vd in vault_dirs:
        if os.path.isdir(vd):
            for k in list(keys.keys()):
                kp = os.path.join(vd, k)
                if not keys[k] and os.path.isfile(kp):
                    try:
                        keys[k] = open(kp, "r", encoding="utf-8").read().strip()
                    except Exception:
                        pass
    for path in search_paths:
        if path and os.path.isfile(path):
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip().strip('"').strip("'")
                        if k in keys and not keys[k] and v:
                            keys[k] = v
    return keys


def compute_dhash(im: Image.Image) -> int:
    gray = im.convert("L").resize((9, 8), Image.Resampling.BILINEAR)
    px = list(gray.getdata())
    bits = 0
    for row in range(8):
        offset = row * 9
        for col in range(8):
            bits = (bits << 1) | (1 if px[offset + col] > px[offset + col + 1] else 0)
    return bits


def hamming_dist(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def register_unique_media(url: str, dhash_val=None) -> bool:
    with STATE_LOCK:
        if url in USED_URLS:
            return False
        if dhash_val is not None:
            for existing in USED_DHASHES:
                if hamming_dist(dhash_val, existing) <= 6:
                    return False
            USED_DHASHES.append(dhash_val)
        USED_URLS.add(url)
        return True


def _norm(txt: str) -> str:
    return re.sub(r"[^a-z0-9\u00c0-\u017f\s]", " ", (txt or "").lower()).strip()


def rank_candidate(cand: dict, query: str, strict: bool = True, must_match: list = None, exclude_terms: list = None) -> float:
    score = 40.0
    url = cand.get("url", "")
    url_low = url.lower()
    if any(bad in url_low for bad in IGNORED_URL_PARTS):
        cand["score"] = -100.0
        return -100.0

    q_words = [w for w in _norm(query).split() if len(w) > 2 and w not in STOPWORDS]
    meta_blob = _norm(f"{cand.get('title', '')} {cand.get('caption', '')} {cand.get('page_url', '')} {url}")
    title_slug = _norm(f"{cand.get('title', '')} {os.path.basename(urllib.parse.urlparse(url).path)}")

    primary = q_words[:2]
    all_primary = all(w in meta_blob for w in primary) if primary else True
    has_primary = any(w in meta_blob for w in primary) if primary else True
    if strict and primary:
        if all_primary:
            score += 32.0
        elif has_primary:
            score -= 10.0
        else:
            score -= 50.0
    elif has_primary:
        score += 24.0

    if must_match:
        for tok in must_match:
            if tok.lower() in meta_blob:
                score += 22.0
            else:
                score -= 16.0
    if exclude_terms:
        for tok in exclude_terms:
            if tok.lower() in meta_blob:
                score -= 65.0

    # Penalize Cyrillic / CIS marketplace spam from Yandex when query has no Slavic/Cyrillic context
    q_low = query.lower()
    if not re.search(r"[\u0400-\u04ff]", q_low) and not any(
        k in q_low for k in ("russia", "moscow", "ukraine", "kyiv", "belarus", "minsk")
    ):
        raw_blob = f"{cand.get('title', '')} {cand.get('caption', '')} {url_low}"
        if re.search(r"[\u0400-\u04ff]", raw_blob) or any(
            dom in url_low for dom in (".ru/", ".ua/", ".by/", "ozone.ru", "sbermegamarket", "wildberries", "rozetka")
        ):
            score -= 60.0

    if q_words:
        matched = sum(1 for w in q_words if w in meta_blob)
        score += (matched / float(len(q_words))) * 26.0
    if all_primary and any(w in title_slug for w in primary):
        score += 12.0

    w, h = int(cand.get("width") or 0), int(cand.get("height") or 0)
    if w >= 1280 or h >= 900:
        score += 14.0
    elif w >= 800 or h >= 600:
        score += 8.0
    elif 0 < w < 450:
        score -= 30.0

    src = cand.get("source", "")
    if "wikimedia" in src and has_primary:
        score += 10.0
    elif "tmdb" in src:
        score += 12.0
    elif "news" in src and has_primary:
        score += 9.0
    elif not strict and src in ("pixabay_photo", "pexels_photo") and has_primary:
        score += 12.0

    cand["score"] = round(score, 2)
    return score


# ── Multi-Source Searchers (vcy-AGOSTO ported & hardened) ─────────────────

def search_bing_images(query: str, limit: int = 14) -> list:
    out = []
    try:
        url = f"https://www.bing.com/images/search?q={urllib.parse.quote(query)}&form=HDRSC2&first=1"
        r = requests.get(url, headers=WEB_HEADERS, timeout=9)
        if not r.ok:
            return out
        blocks = re.findall(r'm="(\{[^"]+\})"', r.text)
        for raw in blocks[:limit * 2]:
            try:
                data = json.loads(html_lib.unescape(raw))
                img_url = data.get("murl", "")
                if not img_url or not img_url.startswith("http"):
                    continue
                out.append({
                    "url": img_url,
                    "title": data.get("t", "") or data.get("desc", ""),
                    "caption": data.get("desc", ""),
                    "page_url": data.get("purl", ""),
                    "source": "bing_images",
                    "width": 0,
                    "height": 0,
                })
                if len(out) >= limit:
                    break
            except Exception:
                continue
    except Exception:
        pass
    return out


def search_duckduckgo_images(query: str, limit: int = 12) -> list:
    global _LAST_DDG_TS
    out = []
    try:
        with DDG_LOCK:
            wait = 1.4 - (time.time() - _LAST_DDG_TS)
            if wait > 0:
                time.sleep(wait)
            s = requests.Session()
            home = f"https://duckduckgo.com/?q={urllib.parse.quote(query)}&iax=images&ia=images"
            r1 = s.get(home, headers=WEB_HEADERS, timeout=8)
            _LAST_DDG_TS = time.time()
            m = re.search(r"vqd=([a-zA-Z0-9_-]+)", r1.text) or re.search(r'"vqd"\s*:\s*"([^"]+)"', r1.text)
            if not m:
                return out
            vqd = m.group(1)
            time.sleep(0.6)
            r2 = s.get(
                "https://duckduckgo.com/i.js",
                params={"l": "wt-wt", "o": "json", "q": query, "vqd": vqd, "f": ",,,", "p": "1"},
                headers={**WEB_HEADERS, "Referer": "https://duckduckgo.com/", "Accept": "application/json"},
                timeout=8,
            )
            _LAST_DDG_TS = time.time()
            if not r2.ok:
                return out
            for item in r2.json().get("results", [])[:limit]:
                u = item.get("image", "")
                if u and u.startswith("http"):
                    out.append({
                        "url": u,
                        "title": item.get("title", ""),
                        "caption": item.get("title", ""),
                        "page_url": item.get("url", ""),
                        "source": f"duckduckgo ({item.get('source', '')})",
                        "width": int(item.get("width") or 0),
                        "height": int(item.get("height") or 0),
                    })
    except Exception:
        pass
    return out


def search_yandex_images(query: str, limit: int = 12) -> list:
    out = []
    try:
        url = f"https://yandex.com/images/search?text={urllib.parse.quote(query)}"
        r = requests.get(url, headers=WEB_HEADERS, timeout=8)
        if not r.ok or "showcaptcha" in r.text.lower():
            return out
        hrefs = re.findall(r"&quot;img_href&quot;:&quot;(https?://[^&]+)&quot;", r.text)
        descs = re.findall(r"&quot;description&quot;:&quot;([^&]+)&quot;", r.text)
        for idx, raw_u in enumerate(hrefs[:limit]):
            clean_u = urllib.parse.unquote(raw_u.replace(r"\/", "/"))
            if "yandex" in clean_u or "yastatic" in clean_u:
                continue
            ttl = descs[idx] if idx < len(descs) else os.path.basename(urllib.parse.urlparse(clean_u).path)
            out.append({
                "url": clean_u,
                "title": ttl,
                "caption": ttl,
                "page_url": "",
                "source": "yandex",
                "width": 0,
                "height": 0,
            })
    except Exception:
        pass
    return out


def search_news_images(query: str, limit: int = 8) -> list:
    """Scrapes real editorial press article OpenGraph photos via Bing News RSS (direct article URLs)."""
    if BeautifulSoup is None:
        return []
    out = []
    try:
        rss = f"https://www.bing.com/news/search?q={urllib.parse.quote(query)}&format=rss"
        r = requests.get(rss, headers=WEB_HEADERS, timeout=7)
        if not r.ok:
            return out
        soup = BeautifulSoup(r.text, "xml")
        items = soup.find_all("item")[: max(limit, 6)]

        def _fetch_art(it):
            link = it.link.text.strip() if it.link and it.link.text else ""
            art_title = it.title.text.strip() if it.title and it.title.text else ""
            if not link:
                return None
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(link).query)
            real_url = qs.get("url", [link])[0]
            try:
                pr = requests.get(real_url, headers=WEB_HEADERS, timeout=5, allow_redirects=True)
                if not pr.ok:
                    return None
                ps = BeautifulSoup(pr.text, "html.parser")
                og = ps.find("meta", property="og:image") or ps.find("meta", attrs={"name": "twitter:image"})
                img_u = (og.get("content", "").strip() if og else "")
                if img_u and img_u.startswith("http") and "j6_cofbogxh" not in img_u.lower():
                    return {
                        "url": img_u,
                        "title": art_title,
                        "caption": art_title,
                        "page_url": pr.url,
                        "source": "news_article",
                        "width": 1200,
                        "height": 675,
                    }
            except Exception:
                return None
            return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
            for hit in ex.map(_fetch_art, items):
                if hit:
                    out.append(hit)
                    if len(out) >= limit:
                        break
    except Exception:
        pass
    return out


def search_browser_images_playwright(query: str, limit: int = 10) -> list:
    """Headless Playwright Chromium fallback when HTTP scrapers get <4 good hits or JS rendering is required."""
    out = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(user_agent=BROWSER_UA, viewport={"width": 1366, "height": 900})
            page = ctx.new_page()
            url = f"https://www.bing.com/images/search?q={urllib.parse.quote(query)}&qft=+filterui:imagesize-large&form=IRFLTR"
            page.goto(url, wait_until="domcontentloaded", timeout=14000)
            page.wait_for_timeout(850)
            items = page.evaluate("""() => {
                const res = [];
                document.querySelectorAll('a.iusc').forEach(a => {
                    try {
                        const m = JSON.parse(a.getAttribute('m') || '{}');
                        if (m.murl && m.murl.startsWith('http')) {
                            res.push({ url: m.murl, title: m.t || m.desc || '', page_url: m.purl || '' });
                        }
                    } catch {}
                });
                return res;
            }""")
            browser.close()
            for it in (items or [])[:limit]:
                out.append({
                    "url": it["url"],
                    "title": it.get("title", ""),
                    "caption": it.get("title", ""),
                    "page_url": it.get("page_url", ""),
                    "source": "playwright_browser",
                    "width": 1280,
                    "height": 720,
                })
    except Exception:
        pass
    return out


def search_wikimedia_images(query: str, limit: int = 10) -> list:
    out = []
    try:
        r = requests.get(
            "https://commons.wikimedia.org/w/api.php",
            headers=WIKI_HEADERS,
            params={
                "action": "query",
                "generator": "search",
                "gsrnamespace": 6,
                "gsrsearch": f"{query} filetype:bitmap",
                "gsrlimit": limit,
                "prop": "imageinfo",
                "iiprop": "url|size|mime|extmetadata",
                "iiurlwidth": 1920,
                "format": "json",
            },
            timeout=8,
        )
        if not r.ok:
            return out
        pages = r.json().get("query", {}).get("pages", {})
        for _, pg in sorted(pages.items(), key=lambda kv: kv[1].get("index", 99)):
            infos = pg.get("imageinfo", [])
            if not infos:
                continue
            ii = infos[0]
            mime = ii.get("mime", "")
            if not any(m in mime for m in ("jpeg", "png", "webp")):
                continue
            w, h = int(ii.get("width", 0)), int(ii.get("height", 0))
            if w < 500 or h < 360:
                continue
            u = ii.get("thumburl") or ii.get("url", "")
            ttl = pg.get("title", "").replace("File:", "")
            out.append({
                "url": u,
                "title": ttl,
                "caption": ttl,
                "page_url": ii.get("descriptionurl", ""),
                "source": "wikimedia",
                "width": w,
                "height": h,
            })
    except Exception:
        pass
    return out


def search_tmdb_images(query: str, api_key: str, universe: str = "", limit: int = 8) -> list:
    if not api_key:
        return []
    out = []
    headers = {"Accept": "application/json", "User-Agent": WIKI_HEADERS["User-Agent"]}
    params = {"query": query or universe, "include_adult": "false", "language": "en-US"}
    if api_key.startswith("ey") or len(api_key) > 40:
        headers["Authorization"] = f"Bearer {api_key}"
    else:
        params["api_key"] = api_key
    try:
        r = requests.get("https://api.themoviedb.org/3/search/multi", params=params, headers=headers, timeout=8)
        if not r.ok:
            return out
        for ent in r.json().get("results", [])[:2]:
            mtype = ent.get("media_type")
            eid = ent.get("id")
            if mtype not in ("movie", "tv") or not eid:
                continue
            ttl = ent.get("title") or ent.get("name") or query
            if ent.get("backdrop_path"):
                bp = ent["backdrop_path"].lstrip("/")
                out.append({
                    "url": f"https://image.tmdb.org/t/p/original/{bp}",
                    "title": f"{ttl} Official Backdrop",
                    "caption": ent.get("overview", "")[:120],
                    "page_url": f"https://www.themoviedb.org/{mtype}/{eid}",
                    "source": "tmdb",
                    "width": 1920,
                    "height": 1080,
                })
    except Exception:
        pass
    return out


def search_openverse_images(query: str, limit: int = 8) -> list:
    out = []
    try:
        r = requests.get(
            "https://api.openverse.org/v1/images/",
            params={"q": query, "page_size": limit},
            headers=WIKI_HEADERS,
            timeout=8,
        )
        if r.ok:
            for res in r.json().get("results", [])[:limit]:
                u = res.get("url", "")
                if u.startswith("http"):
                    out.append({
                        "url": u,
                        "title": res.get("title", ""),
                        "caption": res.get("title", ""),
                        "page_url": res.get("foreign_landing_url", ""),
                        "source": "openverse",
                        "width": int(res.get("width") or 0),
                        "height": int(res.get("height") or 0),
                    })
    except Exception:
        pass
    return out


def _orientation_for_aspect(aspect_ratio: str) -> str:
    if aspect_ratio in ("9:16", "4:5"):
        return "portrait"
    if aspect_ratio == "1:1":
        return "square"
    return "landscape"


_PIXABAY_FLUFF_WORDS = {
    "cinematic", "footage", "shot", "shots", "background", "aesthetic", "dramatic",
    "slow", "motion", "view", "scene", "4k", "hd", "broll", "high", "resolution",
    "photography", "lighting", "editorial", "modern", "luxury", "wide", "angle",
    "closeup", "close", "up", "establish", "establishing", "atmospheric", "moody",
}


def _pixabay_queries(query: str) -> list:
    """
    Pixabay REST API enforces:
      1) `q` max length <= 100 chars (returns HTTP 400 if longer!).
      2) Strict boolean AND matching across creator tags (5-7 word LLM prompts
         often return 0 hits until distilled to 2-3 core nouns).
    Returns [trimmed_full_query, compact_2_to_3_keyword_fallback].
    """
    clean = re.sub(r"[^\w\s\u00c0-\u017f-]", " ", query or "")
    clean = " ".join(clean.split())
    if len(clean) > 95:
        clean = clean[:95].rsplit(" ", 1)[0].strip()
    out = [clean] if clean else []
    core = [
        w for w in clean.split()
        if len(w) > 2 and w.lower() not in STOPWORDS and w.lower() not in _PIXABAY_FLUFF_WORDS
    ]
    if len(core) >= 2:
        short3 = " ".join(core[:3])[:95]
        short2 = " ".join(core[:2])[:95]
        for cand_q in (short3, short2):
            if cand_q and cand_q.lower() not in {x.lower() for x in out}:
                out.append(cand_q)
    return out or ["abstract"]


def search_stock_images(query: str, keys: dict, aspect_ratio: str = "16:9") -> list:
    out = []
    orient = _orientation_for_aspect(aspect_ratio)
    if keys.get("PIXABAY_API_KEY"):
        seen_pb = set()
        for pb_q in _pixabay_queries(query):
            try:
                r = requests.get(
                    "https://pixabay.com/api/",
                    params={
                        "key": keys["PIXABAY_API_KEY"],
                        "q": pb_q,
                        "image_type": "photo",
                        "orientation": "vertical" if orient == "portrait" else "horizontal",
                        "min_width": 1000,
                        "safesearch": "true",
                        "per_page": 15,
                    },
                    timeout=8,
                )
                if r.ok:
                    for hit in r.json().get("hits", []):
                        u = hit.get("fullHDURL") or hit.get("largeImageURL") or hit.get("webformatURL", "")
                        if u and u not in seen_pb:
                            seen_pb.add(u)
                            out.append({
                                "url": u,
                                "title": hit.get("tags", query),
                                "caption": hit.get("tags", query),
                                "page_url": hit.get("pageURL", ""),
                                "source": "pixabay_photo",
                                "width": int(hit.get("imageWidth") or 1920),
                                "height": int(hit.get("imageHeight") or 1080),
                            })
                if len(seen_pb) >= 4:
                    break
            except Exception:
                pass
    if keys.get("PEXELS_API_KEY"):
        try:
            r = requests.get(
                "https://api.pexels.com/v1/search",
                headers={"Authorization": keys["PEXELS_API_KEY"]},
                params={"query": query, "per_page": 10, "orientation": orient},
                timeout=8,
            )
            if r.ok:
                for ph in r.json().get("photos", []):
                    src = ph.get("src", {})
                    u = src.get("large2x") or src.get("large") or src.get("original", "")
                    if u:
                        out.append({
                            "url": u,
                            "title": ph.get("alt", query),
                            "caption": ph.get("alt", query),
                            "page_url": ph.get("url", ""),
                            "source": "pexels_photo",
                            "width": int(ph.get("width") or 1920),
                            "height": int(ph.get("height") or 1080),
                        })
        except Exception:
            pass
    return out


# ── Video Fetchers (Stock HD + YouTube Specific Excerpt via yt-dlp) ───────

def probe_video_duration_s(video_path: str) -> float:
    """Returns exact MP4 duration in seconds via ffprobe (0.0 on error)."""
    if not os.path.isfile(video_path):
        return 0.0
    try:
        res = subprocess.run(
            [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", video_path,
            ],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return float((res.stdout or "0").strip() or 0.0)
    except Exception:
        return 0.0


def normalize_video_for_freecut(raw_mp4: str, out_mp4: str, target_dur_s: float, aspect_ratio: str = "16:9") -> bool:
    """Normalizes any video to silent target aspect @ 30fps, -g 30 keyframe-aligned H.264 for buttery FreeCut scrubbing."""
    try:
        os.makedirs(os.path.dirname(out_mp4), exist_ok=True)
        tw, th = ASPECT_DIMS.get(aspect_ratio, (1920, 1080))
        cmd = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", raw_mp4,
            "-t", f"{max(6.5, target_dur_s + 2.5):.2f}",
            "-map_metadata", "-1",
            "-an",
            "-vf", f"scale={tw}:{th}:force_original_aspect_ratio=increase,crop={tw}:{th},fps=30,format=yuv420p",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
            "-r", "30", "-g", "30", "-keyint_min", "30", "-sc_threshold", "0",
            "-movflags", "+faststart",
            out_mp4,
        ]
        subprocess.run(cmd, stdin=subprocess.DEVNULL, check=True, timeout=65)
        return os.path.isfile(out_mp4) and os.path.getsize(out_mp4) > 15000
    except Exception:
        return False


def extract_video_preview_frames(video_path: str, sid: str, project_dir: str, dur_s: float) -> list:
    """Extracts 3 keyframe thumbnails (15%, 50%, 85%) from a downloaded video so Vision QA checks video clips too."""
    cand_dir = os.path.join(project_dir, "media", "candidates")
    os.makedirs(cand_dir, exist_ok=True)
    thumbs = []
    for idx, frac in enumerate((0.15, 0.50, 0.85), 1):
        ts = max(0.2, round(dur_s * frac, 2))
        out_jpg = os.path.join(cand_dir, f"{sid}_vid_f{idx}.jpg")
        try:
            subprocess.run(
                ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{ts:.2f}", "-i", video_path, "-frames:v", "1", "-q:v", "3", out_jpg],
                check=True,
                timeout=12,
            )
            if os.path.isfile(out_jpg) and os.path.getsize(out_jpg) > 1000:
                thumbs.append({"cand_idx": idx, "path": out_jpg, "label": f"FRAME {int(frac*100)}%"})
        except Exception:
            pass
    return thumbs


def fetch_specific_youtube_clip(query: str, raw_mp4: str, out_mp4: str, dur_s: float, aspect_ratio: str = "16:9") -> str:
    """Downloads ONLY a clean ~10s section from YouTube via yt-dlp for specific people/events/products."""
    if shutil.which("yt-dlp") is None:
        return ""
    try:
        os.makedirs(os.path.dirname(raw_mp4), exist_ok=True)
        if os.path.exists(raw_mp4):
            os.remove(raw_mp4)
        end_sec = int(max(12, min(22, round(dur_s + 8))))
        cmd = [
            "yt-dlp",
            f"ytsearch1:{query}",
            "-f", "bestvideo[height<=1080][ext=mp4]/best[height<=1080][ext=mp4]/best",
            "--download-sections", f"*00:04-00:{end_sec:02d}",
            "--match-filter", "duration >= 10 & duration <= 900",
            "--no-playlist",
            "--quiet",
            "-o", raw_mp4,
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        if res.returncode == 0 and os.path.isfile(raw_mp4) and os.path.getsize(raw_mp4) > 15000:
            if normalize_video_for_freecut(raw_mp4, out_mp4, dur_s, aspect_ratio=aspect_ratio):
                return f"ytsearch1:{query}"
    except Exception:
        pass
    return ""


def fetch_ambient_stock_video(query: str, keys: dict, raw_mp4: str, out_mp4: str, dur_s: float, aspect_ratio: str = "16:9") -> str:
    urls = []
    orient = _orientation_for_aspect(aspect_ratio)
    target_w = ASPECT_DIMS.get(aspect_ratio, (1920, 1080))[0]
    min_pref_dur = max(5.5, min(14.0, dur_s + 0.8))
    if keys.get("PIXABAY_API_KEY"):
        seen_pb_v = set()
        for pb_q in _pixabay_queries(query):
            try:
                r = requests.get(
                    "https://pixabay.com/api/videos/",
                    params={
                        "key": keys["PIXABAY_API_KEY"],
                        "q": pb_q,
                        "safesearch": "true",
                        "per_page": 20,
                    },
                    timeout=9,
                )
                if r.ok:
                    raw_hits = [h for h in r.json().get("hits", []) if float(h.get("duration") or 0) >= 3.8]

                    def _pb_sort_key(h):
                        vmap = h.get("videos") or {}
                        ref = vmap.get("large") or vmap.get("medium") or {}
                        vw = int(ref.get("width") or 1920)
                        vh = int(ref.get("height") or 1080)
                        orient_ok = (vh >= vw) if orient == "portrait" else (vw >= vh)
                        hdur = float(h.get("duration") or 0)
                        return (
                            0 if orient_ok else 1,
                            0 if hdur >= min_pref_dur else 1,
                            -min(20.0, hdur),
                        )

                    for hit in sorted(raw_hits, key=_pb_sort_key):
                        vmap = hit.get("videos") or {}
                        tiers = []
                        for tname in ("large", "medium", "small"):
                            td = vmap.get(tname) or {}
                            tu = td.get("url") or ""
                            tw = int(td.get("width") or 0)
                            th = int(td.get("height") or 0)
                            if tu and 720 <= max(tw, th, 720) <= 2560:
                                tiers.append((abs((tw or target_w) - target_w), tu))
                        if not tiers:
                            for tname in ("large", "medium"):
                                tu = (vmap.get(tname) or {}).get("url") or ""
                                if tu:
                                    tiers.append((0, tu))
                                    break
                        tiers.sort(key=lambda x: x[0])
                        if tiers and tiers[0][1] not in seen_pb_v:
                            seen_pb_v.add(tiers[0][1])
                            urls.append(("pixabay_video", tiers[0][1]))
                if len(seen_pb_v) >= 4:
                    break
            except Exception:
                pass
    if keys.get("PEXELS_API_KEY"):
        try:
            r = requests.get(
                "https://api.pexels.com/videos/search",
                headers={"Authorization": keys["PEXELS_API_KEY"]},
                params={"query": query, "per_page": 14, "orientation": orient},
                timeout=9,
            )
            if r.ok:
                vids = r.json().get("videos", [])
                # Sort so clips >= min_pref_dur come first (prevents 5s clips in 12s beats!)
                vids_sorted = sorted(
                    vids,
                    key=lambda v: (0 if float(v.get("duration") or 0) >= min_pref_dur else 1, -min(20.0, float(v.get("duration") or 0))),
                )
                for vid in vids_sorted:
                    if float(vid.get("duration") or 0) < 3.8:
                        continue
                    vfs = sorted(
                        [vf for vf in vid.get("video_files", []) if 720 <= max(vf.get("width", 0), vf.get("height", 0)) <= 2560],
                        key=lambda x: abs(x.get("width", target_w) - target_w),
                    ) or vid.get("video_files", [])
                    for vf in vfs[:1]:
                        if vf.get("link"):
                            urls.append(("pexels_video", vf["link"]))
        except Exception:
            pass

    for src_tag, u in urls:
        if not register_unique_media(u):
            continue
        try:
            os.makedirs(os.path.dirname(raw_mp4), exist_ok=True)
            with requests.get(u, headers=WEB_HEADERS, stream=True, timeout=20) as resp:
                if not resp.ok:
                    continue
                with open(raw_mp4, "wb") as f:
                    for chunk in resp.iter_content(65536):
                        if chunk:
                            f.write(chunk)
            if normalize_video_for_freecut(raw_mp4, out_mp4, dur_s, aspect_ratio=aspect_ratio):
                return f"{src_tag}:{u}"
        except Exception:
            continue

    # Zero-key free B-roll fallback when neither Pexels nor Pixabay key is configured:
    # Cap yt-dlp ambient clips per run so zero-API machines never stall on 20+ YouTube downloads,
    # letting remaining ambient scenes fall through instantaneously to scraped HD Ken Burns photos!
    if not keys.get("PEXELS_API_KEY") and not keys.get("PIXABAY_API_KEY"):
        with STATE_LOCK:
            used_yt = _ZERO_KEY_AMBIENT_VIDEOS[0]
            if used_yt < _ZERO_KEY_AMBIENT_CAP[0]:
                _ZERO_KEY_AMBIENT_VIDEOS[0] = used_yt + 1
                allow_yt = True
            else:
                allow_yt = False
        if allow_yt:
            return fetch_specific_youtube_clip(f"{query} 4k b-roll footage no talking", raw_mp4, out_mp4, dur_s, aspect_ratio=aspect_ratio)
    return ""


# ── Image Processing, Subject Cutout (rembg) & Web Print Capture (v6.0) ───

ASPECT_DIMS = {
    "16:9": (1920, 1080),
    "9:16": (1080, 1920),
    "4:5": (1080, 1350),
    "1:1": (1080, 1080),
}

_REMBG_SESSION = None
_REMBG_FAILED = False


def _measure_white_border_ratio(im: Image.Image) -> float:
    """Measures fraction of outer 8% perimeter pixels that are studio-white (>=242)."""
    rgb = im.convert("RGB").resize((120, 120), Image.Resampling.BILINEAR)
    px = rgb.load()
    border = 0
    white = 0
    for y in range(120):
        for x in range(120):
            if x < 10 or x >= 110 or y < 10 or y >= 110:
                border += 1
                r, g, b = px[x, y]
                if r >= 242 and g >= 242 and b >= 242:
                    white += 1
    return white / max(1, border)


def build_subject_cutout(src_img_path: str, sid: str, project_dir: str) -> str:
    """
    Extracts a clean RGBA transparent cutout (`media/cutouts/{sid}_cutout.png`)
    using `rembg` (u2net) when available, or a clean corner-seeded studio background
    alpha matte fallback. Auto-crops excess transparent padding!
    """
    global _REMBG_SESSION, _REMBG_FAILED
    cut_dir = os.path.join(project_dir, "media", "cutouts")
    os.makedirs(cut_dir, exist_ok=True)
    out_png = os.path.join(cut_dir, f"{sid}_cutout.png")

    rgba = None
    if not _REMBG_FAILED:
        try:
            from rembg import new_session, remove
            if _REMBG_SESSION is None:
                _REMBG_SESSION = new_session("u2net")
            with Image.open(src_img_path) as raw:
                inp = ImageOps.exif_transpose(raw).convert("RGBA")
                if max(inp.size) > 1400:
                    sc = 1400.0 / max(inp.size)
                    inp = inp.resize((int(inp.width * sc), int(inp.height * sc)), Image.Resampling.LANCZOS)
                rgba = remove(inp, session=_REMBG_SESSION)
        except Exception:
            _REMBG_FAILED = True

    if rgba is None:
        # Clean studio-background flood matte fallback
        with Image.open(src_img_path) as raw:
            im = ImageOps.exif_transpose(raw).convert("RGBA")
            if max(im.size) > 1400:
                sc = 1400.0 / max(im.size)
                im = im.resize((int(im.width * sc), int(im.height * sc)), Image.Resampling.LANCZOS)
            px = im.load()
            w, h = im.size
            # Sample corner background color
            corners = [px[0, 0][:3], px[w - 1, 0][:3], px[0, h - 1][:3], px[w - 1, h - 1][:3]]
            bg_r = sum(c[0] for c in corners) // 4
            bg_g = sum(c[1] for c in corners) // 4
            bg_b = sum(c[2] for c in corners) // 4
            visited = bytearray(w * h)
            stack = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
            tol = 34
            while stack:
                cx, cy = stack.pop()
                idx = cy * w + cx
                if visited[idx]:
                    continue
                r, g, b, a = px[cx, cy]
                if abs(r - bg_r) <= tol and abs(g - bg_g) <= tol and abs(b - bg_b) <= tol:
                    visited[idx] = 1
                    px[cx, cy] = (r, g, b, 0)
                    if cx > 0:
                        stack.append((cx - 1, cy))
                    if cx + 1 < w:
                        stack.append((cx + 1, cy))
                    if cy > 0:
                        stack.append((cx, cy - 1))
                    if cy + 1 < h:
                        stack.append((cx, cy + 1))
            rgba = im

    # Tight bounding-box crop with 12px breathing pad
    bbox = rgba.getbbox()
    if bbox:
        pad = 12
        x0 = max(0, bbox[0] - pad)
        y0 = max(0, bbox[1] - pad)
        x1 = min(rgba.width, bbox[2] + pad)
        y1 = min(rgba.height, bbox[3] + pad)
        rgba = rgba.crop((x0, y0, x1, y1))

    rgba.save(out_png, "PNG")
    return out_png


def capture_web_print(url: str, sid: str, project_dir: str) -> str:
    """Captures a clean editorial press/article evidence print via headless Playwright."""
    prints_dir = os.path.join(project_dir, "media", "prints")
    os.makedirs(prints_dir, exist_ok=True)
    out_png = os.path.join(prints_dir, f"{sid}_print.png")
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(viewport={"width": 1280, "height": 820}, device_scale_factor=1.5)
            page = ctx.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=18000)
            page.wait_for_timeout(900)
            # Strip common cookie/consent overlays cleanly
            page.evaluate("""() => {
                const sel = ['[id*="cookie"]', '[class*="cookie"]', '[id*="consent"]', '[class*="consent"]', '[class*="popup"]', 'header nav'];
                for (const s of sel) document.querySelectorAll(s).forEach(el => { if (el.offsetHeight < 360) el.style.display = 'none'; });
            }""")
            page.screenshot(path=out_png, clip={"x": 80, "y": 40, "width": 1120, "height": 680})
            browser.close()
        if os.path.isfile(out_png) and os.path.getsize(out_png) > 8000:
            return out_png
    except Exception:
        pass
    return ""


def build_editorial_assets(src_img_path: str, sid: str, project_dir: str, aspect_ratio: str = "16:9", make_cutout: bool = False):
    """
    Saves clean human-editor versions of every verified image:
      1. `media/images/{sid}.jpg`: Full-integrity graded original.
      2. `media/images/{sid}_bleed.jpg` (+ `_16x9.jpg` alias): Smart top-weighted full-bleed cover matching `aspect_ratio`.
      3. `media/backdrops/{sid}_plate.jpg`: Darkened, heavily blurred atmospheric plate derived from the photo's own palette.
      4. `media/cutouts/{sid}_cutout.png`: Optional RGBA transparent cutout for `parallax_cutout_stage` / `aroll_yap_overlay`.
    """
    img_dir = os.path.join(project_dir, "media", "images")
    bg_dir = os.path.join(project_dir, "media", "backdrops")
    os.makedirs(img_dir, exist_ok=True)
    os.makedirs(bg_dir, exist_ok=True)
    target_wh = ASPECT_DIMS.get(aspect_ratio, (1920, 1080))

    with Image.open(src_img_path) as raw:
        im = ImageOps.exif_transpose(raw).convert("RGB")
        w, h = im.size
        if max(w, h) > 2200:
            scale = 2200.0 / max(w, h)
            im = im.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)

        graded = ImageEnhance.Contrast(im).enhance(1.05)
        main_jpg = os.path.join(img_dir, f"{sid}.jpg")
        graded.save(main_jpg, "JPEG", quality=94)

        bleed = ImageOps.fit(graded, target_wh, Image.Resampling.LANCZOS, centering=(0.5, 0.35))
        bleed_jpg = os.path.join(img_dir, f"{sid}_16x9.jpg")
        bleed.save(bleed_jpg, "JPEG", quality=93)

        plate = ImageOps.fit(graded, target_wh, Image.Resampling.BILINEAR)
        plate = plate.filter(ImageFilter.GaussianBlur(radius=42))
        plate = ImageEnhance.Brightness(plate).enhance(0.26)
        plate = ImageEnhance.Color(plate).enhance(0.75)
        plate_jpg = os.path.join(bg_dir, f"{sid}_plate.jpg")
        plate.save(plate_jpg, "JPEG", quality=90)

        cutout_png = build_subject_cutout(main_jpg, sid, project_dir) if make_cutout else ""
        return main_jpg, bleed_jpg, plate_jpg, graded.size, cutout_png


def ocr_check_image(img_path: str, query: str, exclude_terms: list = None) -> tuple:
    """Returns (ok_valid: bool, bonus: float, detected_snippet: str)."""
    if _OCR_ENGINE is None:
        return True, 0.0, ""
    try:
        res, _ = _OCR_ENGINE(img_path)
        if not res:
            return True, 0.0, ""
        txt = " ".join(item[1] for item in res if len(item) > 1 and item[1]).strip()
        low = txt.lower()
        for wm in WATERMARKS:
            if wm in low:
                return False, -80.0, f"WATERMARK:{wm}"
        # Reject Cyrillic product labels when query is non-Slavic (prevents Yandex CIS bottle leaks)
        q_low = (query or "").lower()
        if not re.search(r"[\u0400-\u04ff]", q_low) and not any(
            k in q_low for k in ("russia", "moscow", "ukraine", "kyiv", "belarus", "cyrillic", "russo")
        ):
            if len(re.findall(r"[\u0400-\u04ff]", txt)) >= 3:
                return False, -100.0, f"CYRILLIC_LABEL:{txt[:40]}"
        # Reject wrong product flavors/variants printed directly on packaging
        for bad_tok in (exclude_terms or []):
            bt = str(bad_tok).strip().lower()
            if len(bt) >= 4 and re.search(rf"\b{re.escape(bt)}\b", low):
                return False, -95.0, f"EXCLUDED_OCR:{bt}"
        q_words = [w for w in _norm(query).split() if len(w) > 2 and w not in STOPWORDS]
        hits = sum(1 for w in q_words if w in low)
        return True, hits * 15.0, txt[:80]
    except Exception:
        return True, 0.0, ""


def gather_image_candidates(
    queries: list,
    specific: bool,
    mode: str,
    universe: str,
    keys: dict,
    must_match: list = None,
    exclude_terms: list = None,
    seed_urls: list = None,
    aspect_ratio: str = "16:9",
) -> list:
    pool = []
    seen = set()
    for su in (seed_urls or []):
        if isinstance(su, str) and su.startswith("http") and su not in seen:
            seen.add(su)
            pool.append({
                "url": su,
                "title": queries[0] if queries else "Verified Entity Seed",
                "caption": queries[0] if queries else "",
                "page_url": su,
                "source": "verified_seed",
                "width": 1600,
                "height": 1600,
                "score": 135.0,
                "matched_query": queries[0] if queries else "",
            })
    for q in queries:
        if mode == "pop":
            tasks = [
                lambda q=q: search_tmdb_images(q, keys.get("TMDB_API_KEY", ""), universe=universe),
                lambda q=q: search_bing_images(q, limit=12),
                lambda q=q: search_news_images(q, limit=6),
                lambda q=q: search_yandex_images(q, limit=10),
                lambda q=q: search_wikimedia_images(q, limit=8),
            ]
        elif specific:
            tasks = [
                lambda q=q: search_bing_images(q, limit=14),
                lambda q=q: search_news_images(q, limit=6),
                lambda q=q: search_wikimedia_images(q, limit=10),
                lambda q=q: search_yandex_images(q, limit=10),
                lambda q=q: search_tmdb_images(q, keys.get("TMDB_API_KEY", ""), universe=universe),
            ]
        else:
            has_stock_api = bool(keys.get("PEXELS_API_KEY") or keys.get("PIXABAY_API_KEY"))
            if has_stock_api:
                tasks = [
                    lambda q=q: search_stock_images(q, keys, aspect_ratio=aspect_ratio),
                    lambda q=q: search_wikimedia_images(q, limit=8),
                    lambda q=q: search_openverse_images(q, limit=8),
                ]
            else:
                # Zero-API Virgin PC Mode: scrape crisp high-resolution editorial/ambient photography in parallel!
                tasks = [
                    lambda q=q: search_bing_images(f"{q} high resolution photography", limit=14),
                    lambda q=q: search_wikimedia_images(q, limit=10),
                    lambda q=q: search_openverse_images(q, limit=10),
                    lambda q=q: search_yandex_images(q, limit=8),
                ]

        batches = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(tasks)) as ex:
            for fut in concurrent.futures.as_completed([ex.submit(fn) for fn in tasks]):
                try:
                    batches.append(fut.result() or [])
                except Exception:
                    pass

        for batch in batches:
            for c in batch:
                u = c.get("url", "")
                if u and u not in seen:
                    seen.add(u)
                    sc = rank_candidate(c, q, strict=specific, must_match=must_match, exclude_terms=exclude_terms)
                    if sc > -20:
                        c["matched_query"] = q
                        pool.append(c)

        # Headless Playwright browser fallback if HTTP scrapers returned fewer than 4 strong candidates
        if len([c for c in pool if c.get("score", 0) >= 52]) < 4:
            for c in search_browser_images_playwright(q, limit=10):
                u = c.get("url", "")
                if u and u not in seen:
                    seen.add(u)
                    sc = rank_candidate(c, q, strict=specific, must_match=must_match, exclude_terms=exclude_terms)
                    if sc > -20:
                        c["matched_query"] = q
                        pool.append(c)

        if len([c for c in pool if c.get("score", 0) >= 75]) >= 8:
            break

    pool.sort(key=lambda x: x.get("score", 0), reverse=True)
    return pool


def download_and_validate_candidates(
    sid: str,
    pool: list,
    project_dir: str,
    query_ref: str,
    max_keep: int = 4,
    penalize_white_bg: bool = False,
    must_match: list = None,
    exclude_terms: list = None,
) -> list:
    cand_dir = os.path.join(project_dir, "media", "candidates")
    os.makedirs(cand_dir, exist_ok=True)
    kept = []
    must_toks = [t.lower() for t in (must_match or []) if t]
    excl_toks = [t.lower() for t in (exclude_terms or []) if t]

    for cand in pool[:24]:
        u = cand["url"]
        try:
            hdrs = dict(WEB_HEADERS)
            if cand.get("page_url"):
                hdrs["Referer"] = cand["page_url"]
            r = requests.get(u, headers=hdrs, timeout=11)
            if r.status_code == 403 and "Referer" in hdrs:
                hdrs.pop("Referer", None)
                r = requests.get(u, headers=hdrs, timeout=9)
            if not r.ok or len(r.content) < 6500:
                continue
            im = Image.open(io.BytesIO(r.content))
            im.verify()
            im = Image.open(io.BytesIO(r.content))
            im = ImageOps.exif_transpose(im).convert("RGB")
            w, h = im.size
            if w < 460 or h < 320:
                continue
            ar = w / float(h)
            if ar > 3.2 or ar < 0.35:
                continue

            dh = compute_dhash(im)
            idx = len(kept) + 1
            c_path = os.path.join(cand_dir, f"{sid}_cand{idx}.jpg")
            im.save(c_path, "JPEG", quality=93)

            ok_wm, ocr_bonus, ocr_txt = ocr_check_image(c_path, query_ref, exclude_terms=excl_toks)
            if not ok_wm:
                os.remove(c_path)
                continue

            white_ratio = _measure_white_border_ratio(im)
            white_penalty = -28.0 if (penalize_white_bg and white_ratio > 0.55) else 0.0

            meta_blob = f"{cand.get('title', '')} {u} {ocr_txt}".lower()
            anchor_bonus = sum(18.0 for tok in must_toks if tok in meta_blob)
            excl_penalty = sum(-45.0 for tok in excl_toks if tok in meta_blob)

            if idx == 1:
                if not register_unique_media(u, dh):
                    os.remove(c_path)
                    continue

            kept.append({
                "cand_idx": idx,
                "path": c_path,
                "url": u,
                "source": cand.get("source", ""),
                "title": cand.get("title", "")[:90],
                "width": w,
                "height": h,
                "white_border_ratio": round(white_ratio, 3),
                "score": round(cand.get("score", 0) + ocr_bonus + anchor_bonus + excl_penalty + white_penalty, 1),
                "ocr_snippet": ocr_txt,
            })
            if len(kept) >= max_keep:
                break
        except Exception:
            continue

    kept.sort(key=lambda x: x["score"], reverse=True)
    final_kept = []
    for new_i, item in enumerate(kept, 1):
        tmp_p = os.path.join(cand_dir, f"{sid}_sorted_{new_i}.jpg")
        shutil.copy2(item["path"], tmp_p)
        item["tmp_p"] = tmp_p
    for new_i, item in enumerate(kept, 1):
        final_p = os.path.join(cand_dir, f"{sid}_cand{new_i}.jpg")
        shutil.move(item.pop("tmp_p"), final_p)
        item["cand_idx"] = new_i
        item["path"] = final_p
        final_kept.append(item)
    return final_kept


def _load_cross_platform_fonts():
    font_sets = [
        (r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\segoeui.ttf", r"C:\Windows\Fonts\consolab.ttf"),
        ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Menlo.ttc"),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"),
    ]
    for fb, fr, fm in font_sets:
        if os.path.isfile(fb):
            try:
                return ImageFont.truetype(fb, 22), ImageFont.truetype(fr, 15), ImageFont.truetype(fm, 15)
            except Exception:
                pass
    d = ImageFont.load_default()
    return d, d, d


def render_contact_sheet(results: list, out_jpg: str, batch_size: int = 8):
    """
    Generates crisp, high-resolution visual QA contact sheet batches covering ALL visual scenes:
      - Specific Images (`#1 SELECTED` .. `#4`)
      - Ambient / Pexels Images (`#1 SELECTED` .. `#3`)
      - Videos (`3` extracted frames at 15%, 50%, 85% of clip)
      - Web Press Prints (`1` captured screenshot)
      - Missing scenes (bright red alert row so Vision QA re-queries immediately)
    Paginates into batches of `batch_size` rows (`contact_sheet.jpg`, `contact_sheet_batch_2.jpg`, ...)
    so thumbnails stay sharp and readable for Vision models even on 20-30 scene edits.
    """
    vis_rows = [
        r for r in results
        if r.get("actual_type") not in ("text_only", "motion_only", "none")
    ]
    if not vis_rows:
        return ""

    row_h = 250
    col_w = 340
    left_w = 360
    W = left_w + col_w * 4 + 30
    f_hdr, f_sub, f_tag = _load_cross_platform_fonts()
    os.makedirs(os.path.dirname(out_jpg), exist_ok=True)

    # Remove stale extra batch files from older runs
    base_dir = os.path.dirname(out_jpg)
    for old_f in os.listdir(base_dir):
        if old_f.startswith("contact_sheet_batch_") and old_f.endswith(".jpg"):
            try:
                os.remove(os.path.join(base_dir, old_f))
            except Exception:
                pass

    total_batches = max(1, (len(vis_rows) + batch_size - 1) // batch_size)
    written_sheets = []

    for b_idx in range(total_batches):
        chunk = vis_rows[b_idx * batch_size : (b_idx + 1) * batch_size]
        H = 74 + len(chunk) * row_h + 20
        sheet = Image.new("RGB", (W, H), (15, 17, 22))
        draw = ImageDraw.Draw(sheet)

        hdr = f"VISUAL MEDIA QA GRID — BATCH {b_idx + 1}/{total_batches} (VERIFY EVERY ROW: --select SXX=N OR REWRITE QUERY + --scene SXX)"
        draw.text((24, 20), hdr, fill=(242, 244, 248), font=f_hdr)

        for r_idx, row in enumerate(chunk):
            y0 = 74 + r_idx * row_h
            draw.line([(20, y0 - 8), (W - 20, y0 - 8)], fill=(42, 46, 56), width=1)
            sid = row["scene_id"]
            atype = row.get("actual_type", "image")
            spec_tag = "SPECIFIC" if row.get("specific") else "AMBIENT/STOCK"
            selected = row.get("selected_cand", 1)
            q_label = (row.get("queries") or [""])[0][:36]
            narr = (row.get("narration") or "")[:102]

            badge_color = (56, 189, 248) if row.get("specific") else (167, 139, 250)
            if not row.get("ok"):
                badge_color = (248, 113, 113)
            draw.text((24, y0 + 8), f"{sid} [{atype.upper()} • {spec_tag}]", fill=badge_color, font=f_hdr)
            draw.text((24, y0 + 42), f"Query: {q_label}", fill=(210, 216, 226), font=f_sub)
            for li in range(0, len(narr), 36):
                draw.text((24, y0 + 72 + (li // 36) * 20), narr[li:li + 36], fill=(148, 156, 172), font=f_sub)

            thumb_box = (col_w - 20, row_h - 54)
            if not row.get("ok"):
                x0 = left_w
                draw.rectangle([x0, y0 + 4, x0 + col_w * 2, y0 + 4 + thumb_box[1]], fill=(65, 18, 22), outline=(239, 68, 68), width=3)
                draw.text((x0 + 20, y0 + 70), "MISSING MEDIA — REWRITE QUERY & RE-RUN --scene " + sid, fill=(254, 202, 202), font=f_hdr)
                continue

            if atype == "video":
                vframes = row.get("video_frames") or []
                for vf in vframes[:3]:
                    ci = vf["cand_idx"]
                    x0 = left_w + (ci - 1) * col_w
                    try:
                        with Image.open(vf["path"]) as cim:
                            th = ImageOps.contain(cim.convert("RGB"), thumb_box, Image.Resampling.LANCZOS)
                        bg_cell = Image.new("RGB", thumb_box, (26, 29, 36))
                        bg_cell.paste(th, ((thumb_box[0] - th.width) // 2, (thumb_box[1] - th.height) // 2))
                        sheet.paste(bg_cell, (x0, y0 + 4))
                    except Exception:
                        pass
                    draw.rectangle([x0, y0 + 4, x0 + thumb_box[0], y0 + 4 + thumb_box[1]], outline=(34, 197, 94), width=3)
                    lbl = vf.get("label", f"FRAME {ci}")
                    draw.rectangle([x0 + 6, y0 + 10, x0 + 118, y0 + 34], fill=(34, 197, 94))
                    draw.text((x0 + 12, y0 + 13), lbl, fill=(10, 12, 15), font=f_tag)
                    draw.text((x0 + 2, y0 + row_h - 42), f"VIDEO | {str(row.get('url',''))[:28]}", fill=(185, 192, 205), font=f_tag)
                continue

            if atype == "web_print" and row.get("path"):
                x0 = left_w
                try:
                    with Image.open(row["path"]) as cim:
                        th = ImageOps.contain(cim.convert("RGB"), thumb_box, Image.Resampling.LANCZOS)
                    bg_cell = Image.new("RGB", thumb_box, (26, 29, 36))
                    bg_cell.paste(th, ((thumb_box[0] - th.width) // 2, (thumb_box[1] - th.height) // 2))
                    sheet.paste(bg_cell, (x0, y0 + 4))
                except Exception:
                    pass
                draw.rectangle([x0, y0 + 4, x0 + thumb_box[0], y0 + 4 + thumb_box[1]], outline=(34, 197, 94), width=4)
                draw.rectangle([x0 + 6, y0 + 10, x0 + 136, y0 + 34], fill=(34, 197, 94))
                draw.text((x0 + 12, y0 + 13), "WEB PRINT", fill=(10, 12, 15), font=f_tag)
                continue

            for c in (row.get("candidates") or [])[:4]:
                ci = c["cand_idx"]
                x0 = left_w + (ci - 1) * col_w
                try:
                    with Image.open(c["path"]) as cim:
                        th = ImageOps.contain(cim.convert("RGB"), thumb_box, Image.Resampling.LANCZOS)
                    bg_cell = Image.new("RGB", thumb_box, (26, 29, 36))
                    bg_cell.paste(th, ((thumb_box[0] - th.width) // 2, (thumb_box[1] - th.height) // 2))
                    sheet.paste(bg_cell, (x0, y0 + 4))
                except Exception:
                    pass

                is_sel = (ci == selected)
                b_col = (34, 197, 94) if is_sel else (75, 85, 99)
                draw.rectangle([x0, y0 + 4, x0 + thumb_box[0], y0 + 4 + thumb_box[1]], outline=b_col, width=4 if is_sel else 1)
                badge_txt = f"#{ci} SELECTED" if is_sel else f"#{ci}"
                draw.rectangle([x0 + 6, y0 + 10, x0 + (128 if is_sel else 42), y0 + 34], fill=b_col)
                draw.text((x0 + 12, y0 + 13), badge_txt, fill=(10, 12, 15) if is_sel else (245, 245, 245), font=f_tag)
                meta_line = f"{c['width']}x{c['height']} | {c['source'][:18]}"
                draw.text((x0 + 2, y0 + row_h - 42), meta_line, fill=(185, 192, 205), font=f_tag)

        target_p = out_jpg if b_idx == 0 else os.path.join(base_dir, f"contact_sheet_batch_{b_idx + 1}.jpg")
        sheet.save(target_p, "JPEG", quality=90)
        written_sheets.append(target_p)

    return written_sheets


def _scene_wants_cutout(scene: dict, layout_style: str) -> bool:
    media_cfg = scene.get("media") if isinstance(scene.get("media"), dict) else {}
    if scene.get("cutout") or media_cfg.get("cutout"):
        return True
    return layout_style in ("parallax_cutout_stage", "aroll_yap_overlay", "cutout_stage", "subject_cutout")


def process_scene(scene: dict, project_dir: str, keys: dict, aspect_ratio: str = "16:9") -> dict:
    sid = scene["id"]
    stype = scene.get("type", "SCENE")
    layout_style = (scene.get("layout") or scene.get("scene_type") or scene.get("layout_style") or "full_bleed_ken_burns").lower()
    dur_s = max(3.5, (scene["end_ms"] - scene["start_ms"]) / 1000.0)
    media_cfg = scene.get("media") if isinstance(scene.get("media"), dict) else {}

    queries = (
        media_cfg.get("queries")
        or scene.get("queries")
        or ([media_cfg["query"]] if media_cfg.get("query") else [])
        or ([scene["query"]] if scene.get("query") else [])
    )
    evidence_url = media_cfg.get("evidence_url") or scene.get("evidence_url") or ""
    source_type = media_cfg.get("source_type") or scene.get("media_type") or "image"

    # 0. Real Web / Press Print Evidence capture
    if (source_type == "web_print" or layout_style == "press_evidence_highlight") and evidence_url:
        prt = capture_web_print(evidence_url, sid, project_dir)
        if prt:
            main_jpg, bleed_jpg, plate_jpg, wh, cut_png = build_editorial_assets(
                prt, sid, project_dir, aspect_ratio=aspect_ratio, make_cutout=False
            )
            return {
                "scene_id": sid,
                "ok": True,
                "actual_type": "web_print",
                "specific": True,
                "queries": queries or [evidence_url],
                "narration": scene.get("narration", ""),
                "path": prt,
                "bleed_path": bleed_jpg,
                "plate_path": plate_jpg,
                "width": wh[0],
                "height": wh[1],
                "url": evidence_url,
                "source": "web_print",
                "candidates": [],
            }

    if layout_style in ("kinetic_statement", "text_only") and not queries:
        return {"scene_id": sid, "ok": True, "actual_type": "text_only", "specific": False}

    if (stype == "MOTION_SCENE" or layout_style in ("motion_scene", "motion")) and not queries:
        return {"scene_id": sid, "ok": True, "actual_type": "motion_only", "specific": False}

    if not queries:
        return {"scene_id": sid, "ok": True, "actual_type": "none", "specific": False}

    specific = bool(media_cfg.get("specific", scene.get("specific", False)))
    mode = media_cfg.get("mode", scene.get("mode", "default"))
    universe = media_cfg.get("universe", scene.get("universe", ""))
    must_match = media_cfg.get("must_match") or scene.get("must_match") or []
    exclude_terms = media_cfg.get("exclude_terms") or scene.get("exclude_terms") or []
    seed_urls = media_cfg.get("seed_urls") or scene.get("seed_urls") or []
    wants_cutout = _scene_wants_cutout(scene, layout_style)

    raw_dir = os.path.join(project_dir, "media", "raw")
    vid_dir = os.path.join(project_dir, "media", "videos")
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(vid_dir, exist_ok=True)

    # 1. Video path (if requested) — v7.0 Zero-Freeze + Multi-Shot B-Roll (`{sid}_b2.mp4` / `{sid}_b3.mp4`)
    if source_type == "video":
        out_mp4 = os.path.join(vid_dir, f"{sid}.mp4")
        raw_mp4 = os.path.join(raw_dir, f"{sid}_raw.mp4")
        for q_idx, q in enumerate(queries):
            src_hit = (
                fetch_specific_youtube_clip(q, raw_mp4, out_mp4, dur_s, aspect_ratio=aspect_ratio)
                if specific
                else fetch_ambient_stock_video(q, keys, raw_mp4, out_mp4, dur_s, aspect_ratio=aspect_ratio)
            )
            if src_hit:
                d1 = probe_video_duration_s(out_mp4)
                extra_clips = []
                # Whenever beat > 5.8s or primary clip is shorter than beat, fetch distinct secondary B-roll angle(s)
                need_b2 = (dur_s > 5.8) or (d1 < dur_s + 0.25)
                if need_b2:
                    alt_queries = queries[q_idx + 1 :] + queries[: q_idx + 1]
                    b2_out = os.path.join(vid_dir, f"{sid}_b2.mp4")
                    b2_raw = os.path.join(raw_dir, f"{sid}_b2_raw.mp4")
                    sub_target = max(5.5, dur_s * 0.6)
                    for aq in alt_queries:
                        b2_hit = (
                            fetch_specific_youtube_clip(f"{aq} detail", b2_raw, b2_out, sub_target, aspect_ratio=aspect_ratio)
                            if specific
                            else fetch_ambient_stock_video(aq, keys, b2_raw, b2_out, sub_target, aspect_ratio=aspect_ratio)
                        )
                        if b2_hit and os.path.isfile(b2_out):
                            extra_clips.append(b2_out)
                            break
                d_sum = d1 + sum(probe_video_duration_s(p) for p in extra_clips)
                if dur_s > 11.2 or d_sum < dur_s + 0.25:
                    alt_queries = list(reversed(queries))
                    b3_out = os.path.join(vid_dir, f"{sid}_b3.mp4")
                    b3_raw = os.path.join(raw_dir, f"{sid}_b3_raw.mp4")
                    sub_target = max(5.0, dur_s * 0.45)
                    for aq in alt_queries:
                        b3_hit = (
                            fetch_specific_youtube_clip(f"{aq} closeup", b3_raw, b3_out, sub_target, aspect_ratio=aspect_ratio)
                            if specific
                            else fetch_ambient_stock_video(aq, keys, b3_raw, b3_out, sub_target, aspect_ratio=aspect_ratio)
                        )
                        if b3_hit and os.path.isfile(b3_out):
                            extra_clips.append(b3_out)
                            break

                vframes = extract_video_preview_frames(out_mp4, sid, project_dir, min(dur_s, max(1.0, d1)))
                return {
                    "scene_id": sid,
                    "ok": True,
                    "actual_type": "video",
                    "specific": specific,
                    "queries": queries,
                    "narration": scene.get("narration", ""),
                    "path": out_mp4,
                    "secondary_videos": extra_clips,
                    "duration_s": round(d1, 2),
                    "url": src_hit,
                    "source": src_hit.split(":", 1)[0] if ":" in src_hit else "video",
                    "video_frames": vframes,
                }

    # 2. Multi-source image discovery + Top-4/Top-3 candidate pool validation
    pool = gather_image_candidates(
        queries,
        specific=specific,
        mode=mode,
        universe=universe,
        keys=keys,
        must_match=must_match,
        exclude_terms=exclude_terms,
        seed_urls=seed_urls,
        aspect_ratio=aspect_ratio,
    )
    kept = download_and_validate_candidates(
        sid,
        pool,
        project_dir,
        query_ref=queries[0],
        max_keep=4 if specific else 3,
        penalize_white_bg=(layout_style == "full_bleed_ken_burns" and not wants_cutout),
        must_match=must_match,
        exclude_terms=exclude_terms,
    )

    if kept:
        main_jpg, bleed_jpg, plate_jpg, wh, cutout_png = build_editorial_assets(
            kept[0]["path"], sid, project_dir, aspect_ratio=aspect_ratio, make_cutout=wants_cutout
        )
        return {
            "scene_id": sid,
            "ok": True,
            "actual_type": "image",
            "specific": specific,
            "queries": queries,
            "narration": scene.get("narration", ""),
            "selected_cand": 1,
            "path": main_jpg,
            "bleed_path": bleed_jpg,
            "plate_path": plate_jpg,
            "cutout_path": cutout_png,
            "width": wh[0],
            "height": wh[1],
            "url": kept[0]["url"],
            "source": kept[0]["source"],
            "candidates": kept,
        }

    return {
        "scene_id": sid,
        "ok": False,
        "actual_type": "missing_verified_entity",
        "specific": specific,
        "queries": queries,
        "narration": scene.get("narration", ""),
        "candidates": [],
    }


def apply_manual_selections(project_dir: str, selections: list):
    report_path = os.path.join(project_dir, "media", "download_report.json")
    sb_path = os.path.join(project_dir, "storyboard.json")
    sb = json.load(open(sb_path, "r", encoding="utf-8")) if os.path.isfile(sb_path) else {}
    aspect_ratio = str(sb.get("aspect_ratio") or "16:9")
    scenes_by_id = {sc["id"]: sc for sc in sb.get("scenes", [])}
    report = json.load(open(report_path, "r", encoding="utf-8"))
    by_id = {r["scene_id"]: r for r in report}

    for item in selections:
        if "=" not in item:
            continue
        sid, num_s = item.split("=", 1)
        sid = sid.strip()
        c_idx = int(num_s.strip())
        row = by_id.get(sid)
        if not row or not row.get("candidates"):
            print(f"[select] Scene {sid} has no candidate pool.")
            continue
        chosen = next((c for c in row["candidates"] if c["cand_idx"] == c_idx), None)
        if not chosen or not os.path.isfile(chosen["path"]):
            print(f"[select] Candidate #{c_idx} not found for {sid}.")
            continue
        sc = scenes_by_id.get(sid, {})
        lstyle = (sc.get("layout") or sc.get("scene_type") or "").lower()
        wants_cut = _scene_wants_cutout(sc, lstyle) or bool(row.get("cutout_path"))
        main_jpg, bleed_jpg, plate_jpg, wh, cutout_png = build_editorial_assets(
            chosen["path"], sid, project_dir, aspect_ratio=aspect_ratio, make_cutout=wants_cut
        )
        row["selected_cand"] = c_idx
        row["path"] = main_jpg
        row["bleed_path"] = bleed_jpg
        row["plate_path"] = plate_jpg
        if cutout_png:
            row["cutout_path"] = cutout_png
        row["width"], row["height"] = wh
        row["url"] = chosen["url"]
        row["source"] = chosen["source"]
        print(f"[select] Swapped {sid} -> Candidate #{c_idx} ({chosen['source']}, {wh[0]}x{wh[1]})")

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    sheet_path = os.path.join(project_dir, "media", "contact_sheet.jpg")
    sheets = render_contact_sheet(report, sheet_path)
    print(f"[select] Updated contact sheet batch(es): {', '.join(sheets) if isinstance(sheets, list) else sheets}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-dir", required=True)
    ap.add_argument("--select", nargs="*", help="Swap specific candidate(s), e.g. --select S02=2 S05=3")
    ap.add_argument("--scene", nargs="*", help="Re-hunt only specific scene ID(s), e.g. --scene S02")
    ap.add_argument("--cutout", nargs="*", help="Force RGBA subject cutout extraction for specific scene ID(s), e.g. --cutout S02 S05")
    ap.add_argument("--zero-key-video-cap", type=int, default=4, help="Max ambient YouTube B-roll downloads when running without Pexels/Pixabay keys (remaining ambient scenes use scraped HD photos)")
    args = ap.parse_args()
    _ZERO_KEY_AMBIENT_CAP[0] = max(0, int(args.zero_key_video_cap))

    if args.cutout:
        report_path = os.path.join(args.project_dir, "media", "download_report.json")
        report = json.load(open(report_path, "r", encoding="utf-8")) if os.path.isfile(report_path) else []
        by_id = {r["scene_id"]: r for r in report}
        for sid in args.cutout:
            src = os.path.join(args.project_dir, "media", "images", f"{sid}.jpg")
            if os.path.isfile(src):
                cut_p = build_subject_cutout(src, sid, args.project_dir)
                if sid in by_id:
                    by_id[sid]["cutout_path"] = cut_p
                print(f"[cutout] OK -> {cut_p}")
        if report:
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
        if not args.select and not args.scene:
            return

    if args.select:
        apply_manual_selections(args.project_dir, args.select)
        return

    sb = json.load(open(os.path.join(args.project_dir, "storyboard.json"), "r", encoding="utf-8"))
    aspect_ratio = str(sb.get("aspect_ratio") or "16:9")
    keys = load_env_keys([os.path.join(args.project_dir, ".env")])
    scenes = sb.get("scenes", [])
    report_path = os.path.join(args.project_dir, "media", "download_report.json")
    existing_by_id = {}
    if args.scene and os.path.isfile(report_path):
        for r in json.load(open(report_path, "r", encoding="utf-8")):
            existing_by_id[r["scene_id"]] = r

    target_ids = set(args.scene) if args.scene else {sc["id"] for sc in scenes}
    target_scenes = [sc for sc in scenes if sc["id"] in target_ids]

    print(f"[fetch_media v6] Hunting verified media for {len(target_scenes)} scene(s) ({aspect_ratio}, Zero Card Vices)...")
    results_map = dict(existing_by_id)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
        futs = {ex.submit(process_scene, sc, args.project_dir, keys, aspect_ratio): sc["id"] for sc in target_scenes}
        for fut in concurrent.futures.as_completed(futs):
            sid = futs[fut]
            res = fut.result()
            results_map[sid] = res
            print(f"  [{'OK' if res.get('ok') else 'MISS'}] {sid} -> {res.get('actual_type')} ({res.get('source', res.get('url', ''))[:45]})")

    ordered = [results_map[sc["id"]] for sc in scenes if sc["id"] in results_map]
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(ordered, f, ensure_ascii=False, indent=2)

    sheet_path = os.path.join(args.project_dir, "media", "contact_sheet.jpg")
    built_sheets = render_contact_sheet(ordered, sheet_path)
    if built_sheets:
        for sp in (built_sheets if isinstance(built_sheets, list) else [built_sheets]):
            print(f"[fetch_media v6] Contact sheet batch ready for Vision QA: {sp}")


if __name__ == "__main__":
    main()
