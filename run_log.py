"""
Writes data/run-log.json: what this morning's price check did, tool by tool, for the "Watch GenCost check prices"
page (live.html). Run after regenerate_html.py (it needs today's history.json).

It only reads files the run already wrote, so it can't change a price:
- data/{video,image,voice,music}.json   'checked' time of each tool (today = read from the official page)
- price-review.txt                      tools that could not be read today (old prices kept), and their time
- data/history.json                     confirmed price changes today, and new prices waiting for a second reading
- queue/queue.json                      the article published today
"""
import json
import os
import re
from datetime import datetime
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
TZ = ZoneInfo("Europe/Oslo")
CATS = ("video", "image", "voice", "music")


def load(rel, default):
    try:
        with open(os.path.join(HERE, rel), encoding="utf-8-sig") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def slug(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def review_times():
    """slug -> (time, short reason) for tools that couldn't be read today."""
    out, cur = {}, None
    try:
        text = open(os.path.join(HERE, "price-review.txt"), encoding="utf-8").read()
    except OSError:
        return out
    for block in text.split("\n\n"):
        m = re.match(r"(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2})\s+(\S+)", block.strip())
        if m and "kept the previous prices" in block:
            out[slug(m.group(3))] = (m.group(1), m.group(2))
    return out


def build(day=None):
    day = day or datetime.now(TZ).strftime("%Y-%m-%d")
    hist = load("data/history.json", {})
    pending = hist.get("pending", {})
    kept = {k: v for k, v in review_times().items() if v[0] == day}
    tools = []
    for cat in CATS:
        for p in load(f"data/{cat}.json", {}).get("platforms", []):
            name, checked = p["name"], p.get("checked") or ""
            t = {"name": name, "cat": cat, "page": p.get("page") or "/", "changes": [], "waiting": 0}
            k = next((v for s, v in kept.items() if slug(name).startswith(s) or s.startswith(slug(name))), None)
            if checked.startswith(day):
                t.update(time=checked[11:16], status="ok")
            elif k:
                t.update(time=k[1], status="kept", note="The page couldn't be read today, so yesterday's prices were kept")
            else:
                t.update(time="", status="manual", note="This tool blocks automatic reading; its prices are checked by hand")
            for plan, rows in (hist.get(cat, {}).get(name) or {}).items():
                if len(rows) > 1 and rows[-1][0] == day and rows[-1][1] != rows[-2][1]:
                    old, new = rows[-2][1], rows[-1][1]
                    if old and abs(new - old) / old > 0.5:
                        t["note"] = "A big price change was seen; it's being checked by hand before it's shown"
                        continue  # same rule as price_news.py: more often a misreading or a sale than a real change
                    t["changes"].append({"plan": plan, "old": old, "new": new})
            t["waiting"] = sum(1 for key, v in pending.items()
                               if key.startswith(f"{cat}|{name}|") and v.get("first_seen") == day)
            if t["changes"]:
                t["status"] = "changed"
            tools.append(t)
    tools.sort(key=lambda t: (t["time"] == "", t["time"]))
    times = [t["time"] for t in tools if t["time"]]

    q = load("queue/queue.json", [])
    items = q if isinstance(q, list) else q.get("items", [])
    articles = []
    for it in items:
        if it.get("published") == day:
            h3 = re.search(r"<h3>(.*?)</h3>", it.get("card", ""))
            articles.append({"title": re.sub(r"<[^>]+>", "", h3.group(1)) if h3 else it["page"], "url": "/" + it["page"]})

    count = lambda s: sum(1 for t in tools if t["status"] == s)
    return {
        "about": "What GenCost's morning price check did today. Written by run_log.py; shown on /live.html.",
        "date": day, "started": min(times) if times else "", "finished": max(times) if times else "",
        "totals": {"tools": len(tools), "read": count("ok") + count("changed"), "changed": count("changed"),
                   "kept": count("kept"), "manual": count("manual"),
                   "waiting": sum(t["waiting"] for t in tools)},
        "articles": articles,
        "tools": tools,
    }


if __name__ == "__main__":
    log = build()
    with open(os.path.join(HERE, "data", "run-log.json"), "w", encoding="utf-8") as f:
        json.dump(log, f, indent=1, ensure_ascii=False)
    print(f"run-log: {log['totals']} ({log['started']}–{log['finished']})")
