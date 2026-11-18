"""
Posts real price news: when a tool's price or credits changed and the change was confirmed today
(read on two separate days, see regenerate_html.record_history), post it on X and Bluesky.

Example:
  📉 Higgsfield Ultra got cheaper: $99 → $65 a month when paid yearly.
  Read on the official pricing page this morning.

X: no link ($0.015 a post). Bluesky: with a link card to the tool's GenCost page (free).
At most 2 news posts a day; changes on free plans, missing readings (0) and changes under 3% are skipped.
Uses the same secrets as x_post.py and bluesky_post.py; without them it does nothing.
State: data/price-news-state.json. Log: price-news-review.txt.

    python price_news.py            # post today's news
    python price_news.py --preview  # print what would be posted (uses the latest changes if none today)
"""
import datetime as dt
import json
import os
import re
import sys
from zoneinfo import ZoneInfo

import requests

import bluesky_post
import x_post

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = "https://getgencost.com"
STATE = os.path.join(HERE, "data", "price-news-state.json")
LOG = os.path.join(HERE, "price-news-review.txt")
FREE = re.compile(r"^(free|basic free|starter free)$", re.I)
MAX_POSTS = 2


def now():
    return dt.datetime.now(ZoneInfo("Europe/Oslo"))


def log(msg):
    line = f"{now():%Y-%m-%d %H:%M}  {msg}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def money(x):
    return f"${x:,.0f}" if float(x).is_integer() else f"${x:,.2f}"


def pages():
    out = {}
    for cat in ("video", "image", "voice", "music"):
        try:
            for p in json.load(open(os.path.join(HERE, "data", f"{cat}.json"), encoding="utf-8"))["platforms"]:
                out[(cat, p["name"])] = p.get("page") or ""
        except (OSError, ValueError, KeyError):
            pass
    return out


def changes(hist, day):
    """Confirmed changes recorded on `day`: price rows and credit changes. Newest first, deduplicated."""
    out, seen = [], set()
    for cat in ("video", "image", "voice", "music"):
        for tool, plans in (hist.get(cat) or {}).items():
            for plan, rows in plans.items():
                if FREE.match(plan) or len(rows) < 2 or rows[-1][0] != day:
                    continue
                old, new = rows[-2], rows[-1]
                for i, how in ((1, "a month"), (2, "a month when paid yearly")):
                    a, b = old[i], new[i]
                    if not a or not b or abs(b - a) / a < 0.03:
                        continue
                    key = (tool, how, a, b)
                    if key in seen:  # the same plan listed twice under two names (e.g. "Basic" and "Basic Plan")
                        continue
                    seen.add(key)
                    out.append({"cat": cat, "tool": tool, "plan": plan, "kind": "price", "how": how, "old": a, "new": b,
                                "id": f"{cat}|{tool}|{plan}|{how}|{day}"})
    for k, (a, b) in (hist.get("credit_changes") or {}).items():
        cat, tool, plan, d = k.split("|")
        if d == day and a and b and abs(b - a) / a >= 0.03:
            out.append({"cat": cat, "tool": tool, "plan": plan, "kind": "credits", "old": a, "new": b, "id": k})
    # Price changes first, the biggest change in percent first
    out.sort(key=lambda c: (c["kind"] != "price", -abs(c["new"] - c["old"]) / c["old"]))
    return out


def group(items):
    """One post per plan: its monthly and yearly price change and any credit change on the same day."""
    out = {}
    for c in items:
        g = out.setdefault((c["cat"], c["tool"], c["plan"]), {"cat": c["cat"], "tool": c["tool"], "plan": c["plan"], "parts": [], "ids": []})
        g["parts"].append(c)
        g["ids"].append(c["id"])
    return list(out.values())


def offers():
    """(cat, tool, plan) -> the plan's offer note, e.g. "monthly price not shown"."""
    out = {}
    for cat in ("video", "image", "voice", "music"):
        try:
            for p in json.load(open(os.path.join(HERE, "data", f"{cat}.json"), encoding="utf-8"))["platforms"]:
                for pl in p.get("plans") or []:
                    out[(cat, p["name"], pl.get("name", ""))] = (pl.get("offer") or "").lower()
        except (OSError, ValueError, KeyError):
            pass
    return out


def doubtful(g, offer_map):
    """Reason not to post a change automatically, or None. Wrong news is worse than no news."""
    if "not shown" in offer_map.get((g["cat"], g["tool"], g["plan"]), ""):
        return "the monthly price isn't shown on the page, so the comparison may mix monthly and yearly"
    price = [c for c in g["parts"] if c["kind"] == "price"]
    cred = next((c for c in g["parts"] if c["kind"] == "credits"), None)
    if any(abs(c["new"] - c["old"]) / c["old"] > 0.5 for c in price):
        return "the price moved more than 50%, which is more often a misreading or a sale than a real change"
    if price and cred:
        lead = next((c for c in price if c["how"] == "a month"), price[0])
        po, pn = lead["old"] / cred["old"], lead["new"] / cred["new"]
        if abs(pn - po) / po < 0.1:
            return "price and credits moved together (same price per credit), probably renamed plans"
    return None


def text_for(g, hist):
    name = f"{g['tool']} {g['plan']}"
    price = [c for c in g["parts"] if c["kind"] == "price"]
    cred = next((c for c in g["parts"] if c["kind"] == "credits"), None)
    month = next((c for c in price if c["how"] == "a month"), None)
    lead = month or (price[0] if price else None)
    if lead and cred:
        po, pn = lead["old"] / cred["old"], lead["new"] / cred["new"]
        verdict = ("so each credit costs about the same" if abs(pn - po) / po < 0.1 else
                   "so each credit is cheaper" if pn < po else "so each credit costs more")
        text = (f"🔄 {name} changed: {money(lead['old'])} → {money(lead['new'])} {lead['how']}, "
                f"with {cred['new']:,.0f} credits instead of {cred['old']:,.0f}, {verdict}.")
    elif lead:
        down = lead["new"] < lead["old"]
        pct = abs(lead["new"] - lead["old"]) / lead["old"] * 100
        text = (f"📉 {name} got cheaper: {money(lead['old'])} → {money(lead['new'])} {lead['how']} (−{pct:.0f}%)." if down else
                f"📈 {name} costs more now: {money(lead['old'])} → {money(lead['new'])} {lead['how']} (+{pct:.0f}%).")
        other = next((c for c in price if c is not lead), None)
        if other:
            text += f" Paid yearly: {money(other['old'])} → {money(other['new'])} a month."
        cr = (hist.get("credits") or {}).get(f"{g['cat']}|{g['tool']}|{g['plan']}")
        if cr and month:
            text += f" The plan includes {cr:,} credits a month."
    else:
        more = cred["new"] > cred["old"]
        text = f"{'📦' if more else '⚠️'} {name} now gives {cred['new']:,.0f} credits a month instead of {cred['old']:,.0f}, at the same price."
    return text + "\n\nRead on the official pricing page this morning."


def main():
    preview = "--preview" in sys.argv
    try:
        hist = json.load(open(os.path.join(HERE, "data", "history.json"), encoding="utf-8"))
    except (OSError, ValueError):
        print("No data/history.json")
        return
    try:
        state = json.load(open(STATE, encoding="utf-8"))
    except (OSError, ValueError):
        state = {"about": "Price changes posted by price_news.py.", "posted": {}}
    today = now().date().isoformat()
    todo = [c for c in changes(hist, today) if c["id"] not in state["posted"]]
    if preview and not todo:  # show the latest days with a change instead
        days = sorted({r[0] for cat in ("video", "image", "voice", "music") for plans in (hist.get(cat) or {}).values()
                       for rows in plans.values() for r in rows[1:]} | {k.rsplit("|", 1)[1] for k in hist.get("credit_changes") or {}})
        for d in reversed(days[-3:]):
            todo += changes(hist, d)
    if not todo:
        print("No confirmed price change today, so no price news.")
        return
    links = pages()
    xkeys = {"api_key": os.environ.get("X_API_KEY", "").strip(), "api_secret": os.environ.get("X_API_SECRET", "").strip(),
             "token": os.environ.get("X_ACCESS_TOKEN", "").strip(), "token_secret": os.environ.get("X_ACCESS_TOKEN_SECRET", "").strip()}
    handle = os.environ.get("BSKY_HANDLE", "").strip().lstrip("@")
    password = os.environ.get("BSKY_APP_PASSWORD", "").strip()
    session = None
    omap, ok = offers(), []
    for g in group(todo):
        why = doubtful(g, omap)
        if why:
            log(f"Not posted, needs a human look ({why}): {text_for(g, hist).splitlines()[0]}")
        else:
            ok.append(g)
    for c in ok[:MAX_POSTS if not preview else 6]:
        text = text_for(c, hist)
        url = SITE + links.get((c["cat"], c["tool"]), "")
        if preview:
            print(text, f"\n[Bluesky link: {url}]\n")
            continue
        done = {}
        if all(xkeys.values()):
            try:
                r = x_post.post(xkeys, text)
                if r.status_code in (200, 201):
                    done["x"] = f"https://x.com/i/status/{r.json()['data']['id']}"
                else:
                    log(f"X news post failed: HTTP {r.status_code} {r.text[:200]}")
            except requests.RequestException as e:
                log(f"X news post failed (network): {e}")
        if handle and password:
            try:
                if session is None:
                    r = requests.post(f"{bluesky_post.API}/com.atproto.server.createSession", timeout=30,
                                      json={"identifier": handle, "password": password})
                    session = r.json() if r.status_code == 200 else False
                if session:
                    btext = text.replace("this morning.", "this morning:") + f"\n{url}"
                    if os.path.exists(bluesky_post.IMAGE):  # the GenCost picture on the link card, like the article posts
                        up = requests.post(f"{bluesky_post.API}/com.atproto.repo.uploadBlob", timeout=60,
                                           data=open(bluesky_post.IMAGE, "rb").read(),
                                           headers={"Authorization": f"Bearer {session['accessJwt']}", "Content-Type": "image/png"})
                        if up.status_code == 200:
                            card_thumb = up.json()["blob"]
                        else:
                            card_thumb = None
                    else:
                        card_thumb = None
                    record = {"$type": "app.bsky.feed.post", "text": btext, "facets": bluesky_post.facets(btext, url),
                              "embed": {"$type": "app.bsky.embed.external",
                                        "external": {"uri": url, "title": f"{c['tool']} pricing today | GenCost",
                                                     "description": "Every plan in US dollars, read from the official pricing page every morning.",
                                                     **({"thumb": card_thumb} if card_thumb else {})}},
                              "langs": ["en"], "createdAt": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")}
                    r = requests.post(f"{bluesky_post.API}/com.atproto.repo.createRecord", timeout=30,
                                      headers={"Authorization": f"Bearer {session['accessJwt']}"},
                                      json={"repo": session["did"], "collection": "app.bsky.feed.post", "record": record})
                    if r.status_code == 200:
                        done["bluesky"] = f"https://bsky.app/profile/{handle}/post/{r.json()['uri'].rsplit('/', 1)[-1]}"
                    else:
                        log(f"Bluesky news post failed: HTTP {r.status_code} {r.text[:200]}")
            except requests.RequestException as e:
                log(f"Bluesky news post failed (network): {e}")
        if done:
            for i in c["ids"]:
                state["posted"][i] = {"date": today, **done}
            log(f"Price news posted: {text.splitlines()[0]}  {done}")
    if not preview:
        with open(STATE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
