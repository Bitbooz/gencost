"""
Builds the price data the website reads.

This script NO LONGER writes index.html, voice.html or music.html.
Those pages now have a fixed design and load their prices from:

    data/video.json   (from the *-pricing.json files in this folder)
    data/voice.json   (from voice/*-pricing.json)
    data/music.json   (from music/*-pricing.json)

So you can run it as often as you like without touching the design.
It keeps the same name so auto_update.py and the .bat files keep working.

The "updated" date only changes when a price actually changes.
"""
import glob
import json
import os
from datetime import datetime

try:  # show times in Norwegian time, also when GitHub (UTC) runs the update
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Europe/Oslo")
except Exception:
    TZ = None

folder = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(folder, "data")
os.makedirs(data_dir, exist_ok=True)

# ---------- Video / avatar / image tools (files in the main folder) ----------
VIDEO_FILES = [
    "heygen-pricing.json", "higgsfield-pricing.json", "runway-pricing.json",
    "kling-pricing.json", "synthesia-pricing.json", "pika-pricing.json",
    "luma-pricing.json", "viggle-pricing.json", "invideo-pricing.json",
    "capcut-pricing.json", "ltx-pricing.json", "hailuo-pricing.json",
    "veo-pricing.json", "sora-pricing.json",
    "vidu-pricing.json", "krea-pricing.json",
    "midjourney-pricing.json", "leonardo-pricing.json", "ideogram-pricing.json",
]

# keyword in platform/file name -> (display name, page)
VIDEO_NAMES = [
    ("heygen", "HeyGen", "/pages/heygen.html"),
    ("higgs", "Higgsfield", "/pages/higgsfield.html"),
    ("runway", "Runway", "/pages/runway.html"),
    ("kling", "Kling AI", "/pages/kling.html"),
    ("synth", "Synthesia", "/pages/synthesia.html"),
    ("pika", "Pika", "/pages/pika.html"),
    ("luma", "Luma", "/pages/luma.html"),
    ("viggle", "Viggle", "/pages/viggle.html"),
    ("invideo", "InVideo", "/pages/invideo.html"),
    ("capcut", "CapCut", "/pages/capcut.html"),
    ("ltx", "LTX Studio", "/pages/ltx.html"),
    ("hailuo", "Hailuo AI", "/pages/hailuo.html"),
    ("veo", "Google Veo", "/pages/veo.html"),
    ("sora", "Sora", "/pages/sora.html"),
    ("vidu", "Vidu", "/pages/vidu.html"),
    ("krea", "Krea", "/pages/krea.html"),
    ("midjourney", "Midjourney", "/pages/midjourney.html"),
    ("leonardo", "Leonardo", "/pages/leonardo.html"),
    ("ideogram", "Ideogram", "/pages/ideogram.html"),
]

VOICE_NAMES = [
    ("eleven", "ElevenLabs", "/pages/voice/elevenlabs.html"),
    ("murf", "Murf AI", "/pages/voice/murf.html"),
    ("cartesia", "Cartesia", "/pages/voice/cartesia.html"),
    ("speechify", "Speechify", "/pages/voice/speechify.html"),
    ("descript", "Descript", "/pages/voice/descript.html"),
    ("playht", "PlayHT", "/pages/voice/playht.html"),
    ("play.ht", "PlayHT", "/pages/voice/playht.html"),
    ("wellsaid", "WellSaid Labs", "/pages/voice/wellsaid.html"),
    ("fliki", "Fliki", "/pages/voice/fliki.html"),
]

MUSIC_NAMES = [
    ("suno", "Suno", "/pages/music/suno.html"),
    ("udio", "Udio", "/pages/music/udio.html"),
    ("soundraw", "Soundraw", "/pages/music/soundraw.html"),
    ("aiva", "AIVA", "/pages/music/aiva.html"),
    ("boomy", "Boomy", "/pages/music/boomy.html"),
]


def load(path):
    try:
        with open(path, encoding="utf-8-sig") as f:
            d = json.load(f)
        return d if isinstance(d, dict) and d.get("plans") else None
    except Exception as e:
        print(f"  Skipped {os.path.basename(path)}: {e}")
        return None


def build(category, paths, names):
    platforms = []
    for path in paths:
        d = load(path)
        if not d:
            continue
        key = (str(d.get("platform") or "") + " " + os.path.basename(path)).lower()
        name, page = None, "#"
        for kw, n, p in names:
            if kw in key:
                name, page = n, p
                break
        if not name:
            name = str(d.get("platform") or os.path.basename(path).replace("-pricing.json", "")).title()
        platforms.append({
            "name": name,
            "page": page,
            "source": d.get("source") or d.get("source_url") or "",
            "checked": d.get("last_checked") or d.get("checked") or "",
            "plans": d["plans"],
        })
    order = [n for _, n, _ in names]
    platforms.sort(key=lambda p: (order.index(p["name"]) if p["name"] in order else 999, p["name"]))

    out_path = os.path.join(data_dir, f"{category}.json")
    now = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
    updated = now
    # Keep the old date if nothing changed, so "updated" means "prices changed"
    if os.path.exists(out_path):
        try:
            with open(out_path, encoding="utf-8") as f:
                old = json.load(f)
            strip = lambda ps: [{k: v for k, v in p.items() if k != "checked"} for p in ps]
            if old.get("updated") and strip(old.get("platforms", [])) == strip(platforms):
                updated = old["updated"]
        except Exception:
            pass
    # Tools the updater could not read keep "checked": "" -> the site says "Entered by hand"
    data = {"category": category, "updated": updated, "platforms": platforms}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print(f"data/{category}.json: {len(platforms)} tools, updated {updated}")


build("video", [os.path.join(folder, f) for f in VIDEO_FILES], VIDEO_NAMES)
build("voice", sorted(glob.glob(os.path.join(folder, "voice", "*-pricing.json"))), VOICE_NAMES)
build("music", sorted(glob.glob(os.path.join(folder, "music", "*-pricing.json"))), MUSIC_NAMES)
