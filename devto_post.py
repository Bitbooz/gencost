"""
Weekly post on dev.to, made from GenCost's own pages (runs inside the daily GitHub workflow).

Once a week (when 7 days have passed since the last post) it takes the next guide from ROTATION,
turns its lead, quick answer, tables and notes into a dev.to article, adds the price changes
of the last 7 days, and publishes it with a link back to the full guide on getgencost.com.

ONE-TIME SETUP: dev.to -> Settings -> Extensions -> "DEV Community API Keys" -> Generate API key.
Add it in GitHub as a secret named DEVTO_API_KEY. Without the secret this script does nothing.

    python devto_post.py            # post if a week has passed (needs DEVTO_API_KEY)
    python devto_post.py --preview  # only write devto-preview.md, never posts

State: data/devto-state.json (last post date, which guide is next, links to the posts).
Log:   devto-review.txt
"""
import datetime as dt
import json
import os
import re
import sys
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

SITE = "https://getgencost.com"
HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "data", "devto-state.json")
LOG = os.path.join(HERE, "devto-review.txt")
PREVIEW = os.path.join(HERE, "devto-preview.md")
DAYS_BETWEEN = 7
MAX_ROWS = 14

# Guides with real tables, posted in this order, one a week, then from the top again.
# Tags: at most 4, lowercase letters and numbers only (dev.to rule).
ROTATION = [
    ("pages/cheapest-way-to-use-kling-4-0-2026.html", ["ai", "video", "pricing", "kling"]),
    ("pages/cheapest-ai-music-tools-in-2026.html", ["ai", "music", "pricing", "suno"]),
    ("pages/cheapest-ai-voice-tools-in-2026.html", ["ai", "voice", "pricing", "tts"]),
    ("pages/cheapest-way-to-use-seedance-2-5-2026.html", ["ai", "video", "pricing", "seedance"]),
    ("pages/cheapest-ai-image-generators-2026.html", ["ai", "images", "pricing", "midjourney"]),
    ("pages/runway-vs-kling-pricing-2026.html", ["ai", "video", "pricing", "runway"]),
    ("pages/best-elevenlabs-alternatives-2026.html", ["ai", "voice", "pricing", "elevenlabs"]),
    ("pages/cheapest-ai-video-cost-per-second-2026.html", ["ai", "video", "pricing", "api"]),
    ("pages/best-heygen-alternatives-2026.html", ["ai", "video", "pricing", "heygen"]),
    ("pages/suno-vs-udio-pricing-2026.html", ["ai", "music", "pricing", "udio"]),
    ("pages/cheapest-ai-avatar-tools-in-2026.html", ["ai", "video", "pricing", "avatars"]),
    ("pages/cheapest-ai-voice-cloning-tools-2026.html", ["ai", "voice", "pricing", "voicecloning"]),
    ("pages/cheapest-ai-video-tools-in-2026.html", ["ai", "video", "pricing", "tools"]),
]


def today():
    return dt.datetime.now(ZoneInfo("Europe/Oslo")).date()


def load_state():
    try:
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"about": "Weekly dev.to posts made by devto_post.py.", "next": 0, "last_posted": "", "posts": []}


def log(msg):
    line = f"{dt.datetime.now(ZoneInfo('Europe/Oslo')):%Y-%m-%d %H:%M}  {msg}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def md_inline(node):
    """Text of a node, with links kept as Markdown links (site links made absolute)."""
    out = []
    for el in node.descendants:
        if isinstance(el, str):
            if el.parent.name == "a":
                continue
            out.append(str(el))
        elif el.name == "a" and el.get("href"):
            href = el["href"]
            if href.startswith("/"):
                href = SITE + href
            if href.startswith("http"):
                out.append(f"[{clean(el.get_text(' '))}]({href})")
            else:
                out.append(el.get_text(" "))
        elif el.name == "br":
            out.append(" ")
    return clean("".join(out))


def md_table(table):
    rows = []
    for tr in table.find_all("tr"):
        cells = [clean(c.get_text(" ")).replace("|", "/") for c in tr.find_all(["th", "td"])]
        if cells:
            rows.append(cells)
    if len(rows) < 2:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    head, body = rows[0], rows[1:MAX_ROWS + 1]
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * width]
    lines += ["| " + " | ".join(r) + " |" for r in body]
    if len(rows) - 1 > MAX_ROWS:
        lines.append(f"\n*Showing {MAX_ROWS} of {len(rows) - 1} rows. Full table on GenCost.*")
    return "\n".join(lines)


def heading_before(el):
    h = el.find_previous(["h2", "h3"])
    return clean(h.get_text(" ")) if h else ""


def price_changes():
    path = os.path.join(HERE, "price-changes.txt")
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except OSError:
        return []
    return [l.strip() for l in lines if re.match(r"\d{4}-\d{2}-\d{2}\s", l.strip())]


def build(page, tags):
    with open(os.path.join(HERE, page), encoding="utf-8") as f:
        soup = BeautifulSoup(f, "lxml")
    art = soup.find("article") or soup.find("main") or soup.body
    url = f"{SITE}/{page}"
    title = clean(art.find("h1").get_text(" ")) if art.find("h1") else clean(soup.title.string.split("|")[0])
    day = today()
    title = re.sub(r"\s*\(?\b(in )?2026\)?\s*$", "", title).rstrip(" :-")
    title = f"{title} (prices checked {day:%b} {day.day}, {day.year})"
    desc = soup.find("meta", attrs={"name": "description"})
    desc = clean(desc["content"]) if desc and desc.get("content") else ""

    parts = []
    lead = art.find("p", class_="lead")
    if lead:
        parts.append(md_inline(lead))

    box = next((b for b in art.find_all("div", class_="box") if "quick answer" in b.get_text(" ").lower()), None)
    if box:
        txt = md_inline(box)
        txt = re.sub(r"^quick answer[:\s]*", "", txt, flags=re.I)
        parts.append("**Quick answer:** " + txt)

    used = 0
    for table in art.find_all("table"):
        if used == 2:
            break
        md = md_table(table)
        if not md:
            continue
        live = table.find_parent("section", class_="live-box")
        h = "Today's prices" if live else heading_before(table)
        parts.append(f"## {h}\n\n{md}" if h else md)
        # the note right after the table (how the numbers were worked out)
        holder = table.find_parent("div", class_="table-scroll") or table
        nxt = holder.find_next_sibling()
        if not live and nxt is not None and nxt.name == "p" and "note" in (nxt.get("class") or []):
            note = md_inline(nxt)
            parts.append("> " + ("\\" + note if note.startswith("*") else note))
        used += 1
    if not used:
        return None

    changes = price_changes()
    if changes:
        parts.append("## AI tool price changes in the last 7 days\n\n" + "\n".join(f"- {c}" for c in changes[:12]))

    parts.append(f"**Full guide, updated every morning:** [{clean(soup.title.string.split('|')[0])}]({url})")
    parts.append(
        "---\n\n*About this post: [GenCost](" + SITE + "/) reads each tool's official pricing page every "
        "morning and checks every number before it goes live. This weekly summary is generated automatically "
        "from that data, so the numbers match the site on the day it was posted. Prices are in US dollars, "
        "before tax. GenCost uses no affiliate links and takes no payment from the tools it compares.*"
    )
    body = "\n\n".join(p for p in parts if p)
    art = {"title": title[:128], "body_markdown": body, "published": True, "tags": tags[:4]}
    if desc:
        art["description"] = desc[:250]
    return art


def data_is_fresh():
    """Never post old numbers: the price data must be from today or yesterday."""
    try:
        with open(os.path.join(HERE, "data", "video.json"), encoding="utf-8") as f:
            updated = json.load(f).get("updated", "")[:10]
        return (today() - dt.date.fromisoformat(updated)).days <= 1
    except (OSError, ValueError):
        return False


def main():
    preview = "--preview" in sys.argv
    key = os.environ.get("DEVTO_API_KEY", "").strip()
    if not preview and not key:
        print("No DEVTO_API_KEY secret, so no dev.to post. (Add it to turn weekly posts on.)")
        return
    state = load_state()
    last = state.get("last_posted") or ""
    if not preview and last and (today() - dt.date.fromisoformat(last)).days < DAYS_BETWEEN:
        print(f"Last dev.to post was {last}; next one after {DAYS_BETWEEN} days.")
        return
    if not preview and not data_is_fresh():
        log("Skipped: price data is not from today, so nothing was posted.")
        return

    start = state.get("next", 0) % len(ROTATION)
    article = None
    for i in range(len(ROTATION)):
        idx = (start + i) % len(ROTATION)
        page, tags = ROTATION[idx]
        if os.path.exists(os.path.join(HERE, page)):
            article = build(page, tags)
            if article:
                break
    if not article:
        log("Skipped: no guide with a table found.")
        return

    if preview:
        with open(PREVIEW, "w", encoding="utf-8") as f:
            f.write(f"# {article['title']}\n\ntags: {', '.join(article['tags'])}\n\n{article['body_markdown']}\n")
        print(f"Preview written to {PREVIEW} ({page})")
        return

    try:
        r = requests.post("https://dev.to/api/articles", timeout=60,
                          headers={"api-key": key, "Content-Type": "application/json",
                                   "Accept": "application/vnd.forem.api-v1+json",
                                   "User-Agent": "GenCost weekly post (getgencost.com)"},
                          json={"article": article})
    except requests.RequestException as e:
        log(f"dev.to post failed (network): {e}")
        return
    if r.status_code not in (200, 201):
        log(f"dev.to post failed: HTTP {r.status_code} {r.text[:300]}")
        return
    link = r.json().get("url", "")
    state["last_posted"] = today().isoformat()
    state["next"] = (idx + 1) % len(ROTATION)
    state.setdefault("posts", []).append({"date": state["last_posted"], "page": page, "url": link})
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=1, ensure_ascii=False)
    log(f"Posted on dev.to: {link}  (from {page})")


if __name__ == "__main__":
    main()
