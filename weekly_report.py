"""
Weekly report for Frode, every Monday morning, as a GitHub issue (the GitHub app sends it to his phone).

What it holds (last 7 days):
  - visits by people, pages read by AI, AI connector questions, top assistants (needs the STATS_KEY secret:
    the key from Frode's private dashboard link, https://getgencost.com/api/stats?key=THIS-PART)
  - confirmed price and credit changes
  - articles published, and how many are left in the queue
  - how the daily runs went
The previous week's report issue is closed, so only the newest one stays open.

    python weekly_report.py            # make the issue (in GitHub Actions)
    python weekly_report.py --preview  # print the report only
"""
import datetime as dt
import json
import os
import subprocess
import sys
from zoneinfo import ZoneInfo

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
LABEL = "weekly-report"
CATS = ("video", "image", "voice", "music")


def money(x):
    return f"${x:,.0f}" if float(x).is_integer() else f"${x:,.2f}"


def gh(*args):
    r = subprocess.run(["gh", *args], capture_output=True, text=True)
    if r.returncode:
        print("gh", " ".join(args[:2]), "failed:", r.stderr.strip()[:300])
    return r.stdout.strip()


def counter(key):
    if not key:
        return ["_The counter isn't in this report yet: add your dashboard key as the GitHub secret `STATS_KEY` "
                "(the part after `key=` in your private dashboard link)._"]
    try:
        r = requests.get("https://getgencost.com/api/stats", params={"key": key, "days": 7, "format": "json"}, timeout=60)
        d = r.json()
    except (requests.RequestException, ValueError):
        return ["_The counter couldn't be read this week._"]
    days = d.get("days", [])
    people, ai, mcp = (sum(x.get(k, 0) for x in days) for k in ("people", "ai", "mcp"))
    out = [f"- **{people:,}** visits by people · **{ai:,}** pages read by AI and search robots · **{mcp}** questions to the AI connector"]
    asked = [(n, c) for n, c in d.get("ai_by_assistant", []) if "a user asked" in n]
    if asked:
        out.append("- **AI assistants that used GenCost to answer someone:** " + ", ".join(f"{n.split(' (')[0]} {c}" for n, c in asked))
    top = d.get("ai_by_assistant", [])[:5]
    if top:
        out.append("- **Robots that read the most:** " + ", ".join(f"{n} {c}" for n, c in top))
    src = [(n, c) for n, c in d.get("people_by_source", []) if n != "Direct"][:5]
    if src:
        out.append("- **People came from:** " + ", ".join(f"{n} {c}" for n, c in src) + " (plus Direct, which includes disguised robots)")
    land = d.get("pages_people_landed_on", [])[:3]
    if land:
        out.append("- **Most visited pages:** " + ", ".join(f"`{p}` ({c})" for p, c in land))
    return out


def price_changes(hist, since):
    out, seen = [], set()
    for cat in CATS:
        for tool, plans in (hist.get(cat) or {}).items():
            for plan, rows in plans.items():
                for i in range(1, len(rows)):
                    if rows[i][0] < since:
                        continue
                    for k, how in ((1, "a month"), (2, "paid yearly")):
                        a, b = rows[i - 1][k], rows[i][k]
                        if a and b and abs(b - a) / a >= 0.03 and (tool, how, a, b) not in seen:
                            seen.add((tool, how, a, b))
                            out.append(f"- {rows[i][0]}: **{tool} {plan}** {money(a)} → {money(b)} {how}")
    for k, (a, b) in (hist.get("credit_changes") or {}).items():
        cat, tool, plan, day = k.split("|")
        if day >= since:
            out.append(f"- {day}: **{tool} {plan}** credits {a:,} → {b:,}")
    return sorted(out) or ["- No confirmed price changes this week."]


def runs(since):
    raw = gh("run", "list", "--workflow", "daily-update.yml", "--limit", "30", "--json", "conclusion,createdAt")
    try:
        items = [r for r in json.loads(raw or "[]") if r["createdAt"][:10] >= since]
    except ValueError:
        return "- Couldn't read the daily runs."
    ok = sum(1 for r in items if r.get("conclusion") == "success")
    bad = [r["createdAt"][:10] for r in items if r.get("conclusion") not in ("success", "skipped", None, "")]
    return f"- {ok} daily runs passed" + (f", **{len(bad)} failed** ({', '.join(sorted(set(bad)))})" if bad else ", none failed") + "."


def main():
    today = dt.datetime.now(ZoneInfo("Europe/Oslo")).date()
    since = (today - dt.timedelta(days=7)).isoformat()
    hist = json.load(open(os.path.join(HERE, "data", "history.json"), encoding="utf-8"))
    q = json.load(open(os.path.join(HERE, "queue", "queue.json"), encoding="utf-8"))["items"]
    published = [i for i in q if (i.get("published") or "") >= since and i.get("published", "")[:2] == "20"]
    left = sum(1 for i in q if not i.get("published"))
    tools = sum(len(json.load(open(os.path.join(HERE, "data", f"{c}.json"), encoding="utf-8"))["platforms"]) for c in CATS)
    body = [f"## GenCost week {since} – {today}", "", "### 📊 Visitors and AI"] + counter(os.environ.get("STATS_KEY", "").strip())
    body += ["", "### 💲 Price changes"] + price_changes(hist, since)
    body += ["", "### 📝 Articles",
             f"- Published this week: {len(published)}" + ("".join(f"\n  - [{i['page'].split('/')[-1][:-5]}](https://getgencost.com/{i['page']})" for i in published)),
             f"- Left in the queue: **{left}**" + (" ⚠️ time to write more" if left < 7 else f" (enough until about {(today + dt.timedelta(days=left)).strftime('%-d %B')})"),
             "", "### ⚙️ The machine", runs(since), f"- Tools tracked: {tools}", "",
             "_Made automatically by weekly_report.py. The previous report is closed when this one opens._"]
    text = "\n".join(body)
    if "--preview" in sys.argv:
        print(text)
        return
    gh("label", "create", LABEL, "--color", "0E8A16", "--description", "GenCost's Monday report", "--force")
    old = json.loads(gh("issue", "list", "--state", "open", "--label", LABEL, "--json", "number") or "[]")
    gh("issue", "create", "--title", f"📊 GenCost weekly report, {today:%-d %B}", "--label", LABEL, "--body", text)
    for o in old:
        gh("issue", "close", str(o["number"]), "--comment", "A newer weekly report is open.")
    print(text)


if __name__ == "__main__":
    main()
