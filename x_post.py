"""
Posts each new GenCost article to X (runs in the daily workflow, after the article is published).

Uses the X API v2 (pay-per-use) with OAuth 1.0a user keys, stored as GitHub secrets:
  X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET
  (developer.x.com -> your app -> Keys and tokens; the app needs Read and Write). Without them this does nothing.

Cost: X charges $0.015 for a post without a link and $0.20 for a post with a link (Nov 2026).
So by default the post has NO link (about $0.45 a month for one article a day); readers find GenCost
through the link in the X profile. Set the repository variable X_WITH_LINK=1 to add the article link.
Only today's new articles are posted, at most 2 a day. State: data/x-state.json. Log: x-review.txt.

    python x_post.py            # post (needs the secrets)
    python x_post.py --preview  # print the post text, never posts
    python x_post.py --check    # check the keys (reads @bitbooz's own profile, about $0.001), never posts
"""
import base64
import datetime as dt
import hashlib
import hmac
import html
import json
import os
import re
import secrets
import sys
import time
import urllib.parse
from zoneinfo import ZoneInfo

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = "https://getgencost.com"
API = "https://api.x.com/2/tweets"
STATE = os.path.join(HERE, "data", "x-state.json")
LOG = os.path.join(HERE, "x-review.txt")
LIMIT = 280
# Anything X would turn into a link, so a "no link" post never costs the link price by accident
LINKISH = re.compile(r"https?://\S+|\b[\w-]+\.(?:com|net|org|ai|io|co|app|so|dev|video|me)\b\S*", re.I)


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


def post_text(title, desc, url=None):
    desc = re.sub(r"\s+", " ", LINKISH.sub("", desc)).strip()
    title = re.sub(r"\s+", " ", LINKISH.sub("", title)).strip()
    tail = f"\n\n{url}" if url else "\n\nToday's prices on GenCost (link in profile)."
    room = LIMIT - len(tail) - (23 - len(url) if url else 0)  # X counts every link as 23 characters
    text = f"{title}\n\n{desc}"
    if len(text) > room:
        text = text[: room - 1].rsplit(" ", 1)[0].rstrip(",.;:") + "…"
    return text + tail


def oauth_header(method, url, keys):
    """OAuth 1.0a (HMAC-SHA1) header for a JSON request (the JSON body is not part of the signature)."""
    p = {"oauth_consumer_key": keys["api_key"], "oauth_nonce": secrets.token_hex(16),
         "oauth_signature_method": "HMAC-SHA1", "oauth_timestamp": str(int(time.time())),
         "oauth_token": keys["token"], "oauth_version": "1.0"}
    q = lambda s: urllib.parse.quote(str(s), safe="~")
    base = "&".join([method.upper(), q(url), q("&".join(f"{q(k)}={q(v)}" for k, v in sorted(p.items())))])
    key = f"{q(keys['api_secret'])}&{q(keys['token_secret'])}".encode()
    p["oauth_signature"] = base64.b64encode(hmac.new(key, base.encode(), hashlib.sha1).digest()).decode()
    return "OAuth " + ", ".join(f'{q(k)}="{q(v)}"' for k, v in sorted(p.items()))


IMAGE = os.path.join(HERE, "assets", "og-image.png")


def upload_image(keys):
    """Upload the GenCost picture (X API v2 media upload) and return its media id, or None.
    Set the repository variable X_NO_IMAGE=1 to post text only."""
    if os.environ.get("X_NO_IMAGE", "").strip() == "1" or not os.path.exists(IMAGE):
        return None
    url = "https://api.x.com/2/media/upload"
    try:
        r = requests.post(url, timeout=60, headers={"Authorization": oauth_header("POST", url, keys)},
                          files={"media": ("gencost.png", open(IMAGE, "rb"), "image/png")},
                          data={"media_category": "tweet_image", "media_type": "image/png"})
        if r.status_code in (200, 201):
            d = r.json()
            return (d.get("data") or {}).get("id") or d.get("media_id_string")
        log(f"X picture upload failed (posting text only): HTTP {r.status_code} {r.text[:200]}")
    except requests.RequestException as e:
        log(f"X picture upload failed (posting text only): {e}")
    return None


def post(keys, text):
    """Post on X with the GenCost picture when it can be uploaded. Returns the response."""
    body = {"text": text}
    mid = upload_image(keys)
    if mid:
        body["media"] = {"media_ids": [str(mid)]}
    return requests.post(API, json=body, timeout=30,
                         headers={"Authorization": oauth_header("POST", API, keys), "Content-Type": "application/json"})


def main():
    preview = "--preview" in sys.argv
    keys = {"api_key": os.environ.get("X_API_KEY", "").strip(), "api_secret": os.environ.get("X_API_SECRET", "").strip(),
            "token": os.environ.get("X_ACCESS_TOKEN", "").strip(), "token_secret": os.environ.get("X_ACCESS_TOKEN_SECRET", "").strip()}
    with_link = os.environ.get("X_WITH_LINK", "").strip() == "1"
    if "--check" in sys.argv:
        missing = [n for n, k in [("X_API_KEY", "api_key"), ("X_API_SECRET", "api_secret"), ("X_ACCESS_TOKEN", "token"),
                                  ("X_ACCESS_TOKEN_SECRET", "token_secret")] if not keys[k]]
        if missing:
            print("Missing secrets:", ", ".join(missing))
            sys.exit(1)
        print("Access token looks like an OAuth 1.0a token (number-dash-...):", bool(re.fullmatch(r"\d+-\w+", keys["token"])))
        url = "https://api.x.com/2/users/me"
        r = requests.get(url, timeout=30, headers={"Authorization": oauth_header("GET", url, keys)})
        print("X answered:", r.status_code, r.text[:300])
        mid = upload_image(keys)  # uploading a picture is not a post: nothing is published
        print("Picture upload:", "works, media id " + str(mid) if mid else "failed (posts will be text only)")
        sys.exit(0 if r.status_code == 200 else 1)
    if "--hello" in sys.argv:  # one first post by hand (Check X keys workflow, "post" ticked)
        text = ("GenCost is now on X! \U0001F44B\n\nEvery morning we read the official pricing pages of 40+ AI video, image, "
                "voice and music tools, so you can see what they really cost in dollars.\n\nNew price comparisons here every day.")
        r = requests.post(API, json={"text": text}, timeout=30,
                          headers={"Authorization": oauth_header("POST", API, keys), "Content-Type": "application/json"})
        print("X answered:", r.status_code, r.text[:300])
        if r.status_code in (200, 201):
            log(f"Posted the first GenCost post on X: https://x.com/i/status/{r.json()['data']['id']}")
        sys.exit(0 if r.status_code in (200, 201) else 1)
    if not preview and not all(keys.values()):
        print("No X_API_KEY / X_API_SECRET / X_ACCESS_TOKEN / X_ACCESS_TOKEN_SECRET secrets, so nothing was posted to X.")
        return
    try:
        items = json.load(open(os.path.join(HERE, "queue", "queue.json"), encoding="utf-8")).get("items", [])
    except (OSError, ValueError):
        items = []
    try:
        state = json.load(open(STATE, encoding="utf-8"))
    except (OSError, ValueError):
        state = {"about": "Articles posted to X by x_post.py.", "posted": {}}
    today = now().date().isoformat()
    todo = [i for i in items if i.get("published") == today and i["page"] not in state["posted"]
            and os.path.exists(os.path.join(HERE, i["page"]))]
    if "--page" in sys.argv:  # post one chosen article now (the "Post an article" workflow)
        page = sys.argv[sys.argv.index("--page") + 1]
        todo = [{"page": page}] if os.path.exists(os.path.join(HERE, page)) else []
    if preview:
        todo = todo or [i for i in items if re.fullmatch(r"\d{4}-\d{2}-\d{2}", i.get("published") or "")][-1:]
    if not todo:
        print("No new article to post on X today.")
        return
    for item in todo[:2]:
        title, desc = meta(item["page"])
        url = f"{SITE}/{item['page']}" if with_link else None
        text = post_text(title, desc, url)
        if preview:
            print(text, f"\n[{len(text)} characters, {'with' if url else 'no'} link]\n")
            continue
        try:
            r = post(keys, text)
        except requests.RequestException as e:
            log(f"X post failed (network): {e}")
            return
        if r.status_code not in (200, 201):
            log(f"X post failed: HTTP {r.status_code} {r.text[:300]}")
            return
        tid = (r.json().get("data") or {}).get("id", "")
        link = f"https://x.com/i/status/{tid}"
        state["posted"][item["page"]] = {"date": today, "url": link, "with_link": bool(url)}
        log(f"Posted on X ({'with' if url else 'no'} link): {link}  ({item['page']})")
    if not preview:
        with open(STATE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
