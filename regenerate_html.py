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
    "pixverse-pricing.json", "hedra-pricing.json", "did-pricing.json",
    "colossyan-pricing.json", "opusclip-pricing.json", "captions-pricing.json",
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
    ("pixverse", "PixVerse", "/pages/pixverse.html"),
    ("hedra", "Hedra", "/pages/hedra.html"),
    ("did-pricing", "D-ID", "/pages/d-id.html"),
    ("colossyan", "Colossyan", "/pages/colossyan.html"),
    ("opusclip", "OpusClip", "/pages/opusclip.html"),
    ("captions", "Captions", "/pages/captions.html"),
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
    ("hume", "Hume", "/pages/hume.html"),
    ("resemble", "Resemble AI", "/pages/resemble.html"),
    ("fishaudio", "Fish Audio", "/pages/fish-audio.html"),
]

MUSIC_NAMES = [
    ("suno", "Suno", "/pages/music/suno.html"),
    ("udio", "Udio", "/pages/music/udio.html"),
    ("soundraw", "Soundraw", "/pages/music/soundraw.html"),
    ("aiva", "AIVA", "/pages/music/aiva.html"),
    ("boomy", "Boomy", "/pages/music/boomy.html"),
    ("beatoven", "Beatoven", "/pages/beatoven.html"),
    ("stableaudio", "Stable Audio", "/pages/stable-audio.html"),
    ("mureka", "Mureka", "/pages/mureka.html"),
]


def load(path):
    try:
        with open(path, encoding="utf-8-sig") as f:
            d = json.load(f)
        return d if isinstance(d, dict) and d.get("plans") else None
    except Exception as e:
        print(f"  Skipped {os.path.basename(path)}: {e}")
        return None


def load_clip_costs():
    """data/clip-costs.json (kept by hand): credits per video clip for each tool."""
    try:
        with open(os.path.join(data_dir, "clip-costs.json"), encoding="utf-8-sig") as f:
            return json.load(f).get("tools", {})
    except Exception as e:
        print(f"  No clip costs: {e}")
        return {}


def load_hidden_costs():
    """data/hidden-costs.json (kept by hand): watermarks, expiring credits, commercial-use rules."""
    try:
        with open(os.path.join(data_dir, "hidden-costs.json"), encoding="utf-8-sig") as f:
            return json.load(f).get("tools", {})
    except Exception as e:
        print(f"  No hidden costs: {e}")
        return {}


# Tools that have shut down: kept out of the price lists (their old files stay for history)
DISCONTINUED = {"Sora", "PlayHT"}
# Not shown: Resemble AI's pricing page is for deepfake detection, not for voices
HIDDEN_TOOLS = {"Resemble AI"}


def record_history(category, platforms, day):
    """data/history.json: every plan's price per day, saved only when it changes.
    Only prices read fresh from the official page in this run count (a tool that could not be read keeps
    old prices, which are not a new reading). A new price must be read in two separate runs before it
    counts as a change, so a one-off misread never shows up as a price change or in a price alert."""
    path = os.path.join(data_dir, "history.json")
    try:
        with open(path, encoding="utf-8") as f:
            hist = json.load(f)
    except Exception:
        hist = {}
    if hist.get("version") != 3:
        # start again: earlier rows could hold reading errors; each tool starts at its next fresh reading
        hist = {"about": "Price per plan over time: [date, monthly, yearly]. A row is added only when a new price "
                         "has been read in two separate daily checks.",
                "version": 3, "since": day, "video": {}, "voice": {}, "music": {}, "pending": {}, "readings": {}}
    cat = hist.setdefault(category, {})
    pending = hist.setdefault("pending", {})
    readings = hist.setdefault("readings", {})
    for pf in platforms:
        checked = pf.get("checked")
        rkey = f"{category}|{pf['name']}"
        if not checked or readings.get(rkey) == checked:
            continue  # not checked against the official page, or no new reading since last time
        readings[rkey] = checked
        tool = cat.setdefault(pf["name"], {})
        for p in pf["plans"]:
            m = p.get("monthly_price_usd")
            y = p.get("yearly_price_usd") or 0
            if not isinstance(m, (int, float)) or isinstance(m, bool):
                continue
            rows = tool.setdefault(p["name"], [])
            m = round(float(m), 2)
            y = round(float(y), 2) if isinstance(y, (int, float)) else 0
            if not rows:
                rows.append([day, m, y])
                continue
            if not y and rows[-1][2]:
                y = rows[-1][2]  # a yearly price that could not be confirmed today is not a change
            if y and not rows[-1][2] and m == rows[-1][1]:
                rows[-1][2] = y  # a yearly price found for the first time is not a change either
                continue
            key = f"{category}|{pf['name']}|{p['name']}"
            if rows[-1][1:] == [m, y]:
                pending.pop(key, None)
                continue
            seen = pending.get(key)
            if seen and seen["value"] == [m, y] and seen["reading"] != checked:
                rows.append([day, m, y])  # read the same new price twice: a real change
                pending.pop(key, None)
            else:
                pending[key] = {"value": [m, y], "reading": checked, "first_seen": day}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(hist, f, indent=1, ensure_ascii=False)


def build(category, paths, names):
    clip_costs = load_clip_costs() if category == "video" else {}
    hidden = load_hidden_costs()
    platforms = []
    for path in paths:
        d = load(path)
        if not d:
            continue
        key = (str(d.get("platform") or "") + " " + os.path.basename(path)).lower()
        name, page = None, "#"
        stem = os.path.basename(path).lower().replace("-pricing.json", "")
        # exact file name first ("stableaudio" must not be read as "udio"), then the old keyword match
        for kw, n, p in names:
            if kw.replace("-pricing", "") == stem:
                name, page = n, p
                break
        if not name:
            for kw, n, p in names:
                if kw in key:
                    name, page = n, p
                    break
        if not name:
            name = str(d.get("platform") or os.path.basename(path).replace("-pricing.json", "")).title()
        if name in DISCONTINUED or name in HIDDEN_TOOLS:
            continue
        for p in d["plans"]:  # "TEAM" -> "Team"
            if isinstance(p.get("name"), str) and p["name"].isupper() and len(p["name"]) > 3:
                p["name"] = p["name"].title()
        platforms.append({
            "name": name,
            "page": page,
            "source": d.get("source") or d.get("source_url") or "",
            "checked": d.get("last_checked") or d.get("checked") or "",
            "plans": d["plans"],
        })
        if name in clip_costs:
            platforms[-1]["clips"] = clip_costs[name]
        if name in hidden:
            platforms[-1]["hidden"] = hidden[name]
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
            strip = lambda ps: [{k: v for k, v in p.items() if k not in ("checked", "clips", "hidden")} for p in ps]
            if old.get("updated") and strip(old.get("platforms", [])) == strip(platforms):
                updated = old["updated"]
        except Exception:
            pass
    record_history(category, platforms, now[:10])
    # Tools the updater could not read keep "checked": "" -> the site says "Entered by hand"
    data = {"category": category, "updated": updated, "platforms": platforms}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    print(f"data/{category}.json: {len(platforms)} tools, updated {updated}")


build("video", [os.path.join(folder, f) for f in VIDEO_FILES], VIDEO_NAMES)
build("voice", sorted(glob.glob(os.path.join(folder, "voice", "*-pricing.json"))), VOICE_NAMES)
build("music", sorted(glob.glob(os.path.join(folder, "music", "*-pricing.json"))), MUSIC_NAMES)
