"""
Posts each new GenCost article to Bluesky (runs in the daily workflow, after the article is published).

Uses Bluesky's open API (AT Protocol) directly, with an App Password:
  GitHub secrets BSKY_HANDLE (e.g. getgencost.bsky.social) and BSKY_APP_PASSWORD
  (Bluesky -> Settings -> Privacy and security -> App passwords). Without them this does nothing.

It posts the articles from queue/queue.json that were published today and are not posted yet,
with a link card (title, description, GenCost image). State: data/bluesky-state.json. Log: bluesky-review.txt.

    python bluesky_post.py            # post (needs the secrets)
    python bluesky_post.py --preview  # print the post text, never posts
"""
import datetime as dt
import html
import json
import os
import re
import sys
from zoneinfo import ZoneInfo

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = "https://getgencost.com"
API = "https://bsky.social/xrpc"
STATE = os.path.join(HERE, "data", "bluesky-state.json")
LOG = os.path.join(HERE, "bluesky-review.txt")
IMAGE = os.path.join(HERE, "assets", "og-image.png")


def now():
    return dt.datetime.now(ZoneInfo("Europe/Oslo"))


def log(msg):
    line = f"{now():%Y-%m-%d %H:%M}  {msg}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def meta(page):
    raw = open(os.path.join(HERE, page), encoding="utf-8").read()
    t = re.search(r"<title>(.*?)</title>", raw, re.S)
    d = re.search(r'<meta name="description" content="([^"]*)"', raw)
    title = html.unescape(t.group(1)).split(" | GenCost")[0].strip() if t else page
    return title, html.unescape(d.group(1)) if d else ""


def post_text(title, desc, url):
    text = f"{title}\n\n{desc}"
    tail = f"\n\n{url}"
    if len(text) + len(tail) > 290:  # Bluesky allows 300 characters
        text = text[: 290 - len(tail) - 1].rsplit(" ", 1)[0] + "…"
    return text + tail


def facets(text, url):
    b = text.encode("utf-8")
    start = b.rfind(url.encode("utf-8"))
    return [{"index": {"byteStart": start, "byteEnd": start + len(url.encode("utf-8"))},
             "features": [{"$type": "app.bsky.richtext.facet#link", "uri": url}]}]


def main():
    preview = "--preview" in sys.argv
    handle = os.environ.get("BSKY_HANDLE", "").strip().lstrip("@")
    password = os.environ.get("BSKY_APP_PASSWORD", "").strip()
    if not preview and not (handle and password):
        print("No BSKY_HANDLE / BSKY_APP_PASSWORD secrets, so nothing was posted to Bluesky.")
        return
    try:
        items = json.load(open(os.path.join(HERE, "queue", "queue.json"), encoding="utf-8")).get("items", [])
    except (OSError, ValueError):
        items = []
    try:
        state = json.load(open(STATE, encoding="utf-8"))
    except (OSError, ValueError):
        state = {"about": "Articles posted to Bluesky by bluesky_post.py.", "posted": {}}
    today = now().date().isoformat()
    todo = [i for i in items if i.get("published") == today and i["page"] not in state["posted"]
            and os.path.exists(os.path.join(HERE, i["page"]))]
    if preview:
        todo = todo or [i for i in items if re.fullmatch(r"\d{4}-\d{2}-\d{2}", i.get("published") or "")][-1:]
    if not todo:
        print("No new article to post on Bluesky today.")
        return
    session = None
    for item in todo[:2]:
        title, desc = meta(item["page"])
        url = f"{SITE}/{item['page']}"
        text = post_text(title, desc, url)
        if preview:
            print(text)
            continue
        try:
            if session is None:
                r = requests.post(f"{API}/com.atproto.server.createSession", timeout=30,
                                  json={"identifier": handle, "password": password})
                if r.status_code != 200:
                    log(f"Bluesky login failed: HTTP {r.status_code} {r.text[:200]}")
                    return
                session = r.json()
            auth = {"Authorization": f"Bearer {session['accessJwt']}"}
            embed = {"$type": "app.bsky.embed.external",
                     "external": {"uri": url, "title": title[:300], "description": desc[:300]}}
            if os.path.exists(IMAGE):
                up = requests.post(f"{API}/com.atproto.repo.uploadBlob", timeout=60, data=open(IMAGE, "rb").read(),
                                   headers={**auth, "Content-Type": "image/png"})
                if up.status_code == 200:
                    embed["external"]["thumb"] = up.json()["blob"]
            record = {"$type": "app.bsky.feed.post", "text": text, "facets": facets(text, url), "embed": embed,
                      "langs": ["en"], "createdAt": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")}
            r = requests.post(f"{API}/com.atproto.repo.createRecord", timeout=30, headers=auth,
                              json={"repo": session["did"], "collection": "app.bsky.feed.post", "record": record})
        except requests.RequestException as e:
            log(f"Bluesky post failed (network): {e}")
            return
        if r.status_code != 200:
            log(f"Bluesky post failed: HTTP {r.status_code} {r.text[:200]}")
            return
        rkey = r.json().get("uri", "").rsplit("/", 1)[-1]
        link = f"https://bsky.app/profile/{handle}/post/{rkey}"
        state["posted"][item["page"]] = {"date": today, "url": link}
        log(f"Posted on Bluesky: {link}  ({item['page']})")
    if not preview:
        with open(STATE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
