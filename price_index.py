"""
Monthly AI price index: on the 1st of each month, writes an article about last month's price changes,
built only from GenCost's own price history (data/history.json), so every number is a real reading.

  "AI Tool Prices in November 2026: What Changed"
  - which plans got cheaper or more expensive (monthly and yearly price), with dates
  - which plans changed their credits
  - how many tools kept the same prices

The article is put first in the queue (queue/queue.json), so publish_queue.py publishes it the same morning,
with the usual card, feed, translations, Bluesky, X and Short. Runs before publish_queue.py in the daily workflow.
Nothing happens on other days, if last month has no data, or if the article already exists.

    python price_index.py                  # only does something on the 1st
    python price_index.py --month 2026-11  # build that month now (also when it is not the 1st)
    python price_index.py --month 2026-11 --dry-run   # write nothing, print the summary
"""
import datetime as dt
import html
import json
import os
import re
import sys
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
CATS = (("video", "Video"), ("image", "Image"), ("voice", "Voice"), ("music", "Music"))
FREE = re.compile(r"^(free|basic free|starter free)$", re.I)


def money(x):
    return f"${x:,.0f}" if float(x).is_integer() else f"${x:,.2f}"


def month_name(ym):
    return dt.date(int(ym[:4]), int(ym[5:]), 1).strftime("%B %Y")


def collect(hist, ym):
    rows, seen, tools = [], set(), set()
    for cat, _ in CATS:
        for tool, plans in (hist.get(cat) or {}).items():
            tools.add((cat, tool))
            for plan, hist_rows in plans.items():
                if FREE.match(plan):
                    continue
                for i in range(1, len(hist_rows)):
                    day = hist_rows[i][0]
                    if not day.startswith(ym):
                        continue
                    old, new = hist_rows[i - 1], hist_rows[i]
                    for k, how in ((1, "monthly"), (2, "yearly")):
                        a, b = old[k], new[k]
                        if not a or not b or abs(b - a) / a < 0.03:
                            continue
                        key = (tool, how, a, b, day)
                        if key in seen:
                            continue
                        seen.add(key)
                        rows.append({"cat": cat, "tool": tool, "plan": plan, "how": how, "old": a, "new": b, "day": day})
    credits = []
    for k, (a, b) in (hist.get("credit_changes") or {}).items():
        cat, tool, plan, day = k.split("|")
        if day.startswith(ym) and a and b:
            credits.append({"cat": cat, "tool": tool, "plan": plan, "old": a, "new": b, "day": day})
    return rows, credits, tools


def pages():
    out = {}
    for cat, _ in CATS:
        try:
            for p in json.load(open(os.path.join(HERE, "data", f"{cat}.json"), encoding="utf-8"))["platforms"]:
                out[p["name"]] = p.get("page") or ""
        except (OSError, ValueError, KeyError):
            pass
    return out


def shell():
    raw = open(os.path.join(HERE, "pages", "cheapest-way-to-use-kling-4-0-2026.html"), encoding="utf-8").read()
    head = raw[:raw.index('<article class="prose">') + len('<article class="prose">')]
    tail = raw[raw.index("</article>"):]
    tail = re.sub(r'<section class="related".*?</section>', "", tail, flags=re.S)
    for pat in (r"<!-- SEO:START.*?<!-- SEO:END -->\n?", r"<!-- HREFLANG:START.*?<!-- HREFLANG:END -->\n?",
                r'<details class="lang-menu".*?</details>'):
        head = re.sub(pat, "", head, flags=re.S)
    return head, tail


def build(ym, hist):
    rows, credits, tools = collect(hist, ym)
    links = pages()
    tools = {t for t in tools if t[1] in links}  # only tools GenCost still lists
    name = month_name(ym)
    cheaper = [r for r in rows if r["new"] < r["old"]]
    dearer = [r for r in rows if r["new"] > r["old"]]
    changed_tools = {r["tool"] for r in rows} | {c["tool"] for c in credits}
    same = len(tools) - len(changed_tools)
    a = lambda t: f'<a href="{links.get(t, "")}">{html.escape(t)}</a>' if links.get(t) else html.escape(t)

    def pct(r):
        return (r["new"] - r["old"]) / r["old"] * 100

    if rows or credits:
        bits = []
        if cheaper:
            b = min(cheaper, key=pct)
            bits.append(f"<strong>{len(cheaper)}</strong> plan price{'s' if len(cheaper) != 1 else ''} went down; the biggest cut was "
                        f"<strong>{html.escape(b['tool'])} {html.escape(b['plan'])}</strong>, {money(b['old'])} → {money(b['new'])} "
                        f"({'paid yearly' if b['how'] == 'yearly' else 'a month'}, {pct(b):.0f}%)")
        if dearer:
            bits.append(f"<strong>{len(dearer)}</strong> went up")
        if credits:
            bits.append(f"<strong>{len(credits)}</strong> plan{'s' if len(credits) != 1 else ''} changed how many credits you get")
        answer = (f"In {name}, " + "; ".join(bits) + f".<br/>\nThe other <strong>{same}</strong> of the {len(tools)} AI tools "
                  f"GenCost tracks kept the same prices all month.")
    else:
        answer = f"No AI tool GenCost tracks changed its price in {name}: all {len(tools)} kept the same plans and prices."

    def table(items):
        out = []
        cr_plans = {(c["tool"], c["plan"]) for c in credits}
        for r in sorted(items, key=pct):
            note = " *" if (r["tool"], r["plan"]) in cr_plans else ""
            out.append(f"<tr><td>{a(r['tool'])}</td><td>{html.escape(r['plan'])}{note}</td><td>{'Paid yearly (per month)' if r['how'] == 'yearly' else 'Monthly'}</td>"
                       f"<td>{money(r['old'])}</td><td><strong>{money(r['new'])}</strong></td><td>{pct(r):+.0f}%</td><td>{r['day']}</td></tr>")
        return ('<div class="table-scroll"><table>\n<thead><tr><th>Tool</th><th>Plan</th><th>Billing</th><th>Before</th><th>After</th>'
                '<th>Change</th><th>Confirmed</th></tr></thead>\n<tbody>\n' + "\n".join(out) + "\n</tbody>\n</table></div>")

    body = [f"<h1>AI Tool Prices in {name}: What Changed</h1>",
            f'<div class="box">\n<strong>Quick answer</strong><br/>\n{answer}<br/>\nBased on GenCost\'s daily readings in {name}.\n</div>',
            f'<p class="lead">GenCost reads the official pricing page of every tool it tracks every morning. A new price only counts when it '
            f'has been read on two separate days. This is the list of every confirmed change in {name}'
            + (f' (readings since {dt.date.fromisoformat(hist["since"]).strftime("%-d %B")})' if hist.get("since", "")[:7] == ym else "") + '.</p>']
    if cheaper:
        body += [f"<h2>Cheaper in {name}</h2>", table(cheaper)]
        if any((r["tool"], r["plan"]) in {(c["tool"], c["plan"]) for c in credits} for r in cheaper):
            body.append("<p class=\"note\">* This plan also changed its credits, so a lower price does not always mean more for your money. See the credit changes below.</p>")
    if dearer:
        body += [f"<h2>More expensive in {name}</h2>", table(dearer)]
    if credits:
        cr = []
        for c in sorted(credits, key=lambda c: c["day"]):
            cr.append(f"<tr><td>{a(c['tool'])}</td><td>{html.escape(c['plan'])}</td><td>{c['old']:,.0f}</td>"
                      f"<td><strong>{c['new']:,.0f}</strong></td><td>{(c['new'] - c['old']) / c['old'] * 100:+.0f}%</td><td>{c['day']}</td></tr>")
        body += [f"<h2>Credit changes in {name}</h2>",
                 "<p>A plan can keep its price and still give you more or less. These plans changed the number of credits a month:</p>",
                 '<div class="table-scroll"><table>\n<thead><tr><th>Tool</th><th>Plan</th><th>Credits before</th><th>Credits after</th>'
                 "<th>Change</th><th>Confirmed</th></tr></thead>\n<tbody>\n" + "\n".join(cr) + "\n</tbody>\n</table></div>"]
    by_cat = []
    for cat, label in CATS:
        n = sum(1 for (c, _) in tools if c == cat)
        ch = len({r["tool"] for r in rows + credits if r["cat"] == cat})
        if n:
            by_cat.append(f"<li><strong>{label}:</strong> {ch} of {n} tools changed something</li>")
    body += [f"<h2>{name} by category</h2>", "<ul>" + "".join(by_cat) + "</ul>",
             "<h2>How this list is made</h2>",
             "<p>Every price here is a reading from the tool's official pricing page, in US dollars before tax. Discounts that last only "
             "for the first month are not counted as price changes, and a change under 3% is left out. Free plans are left out.</p>",
             '<p>See today\'s prices on every <a href="/compare.html">comparison table</a>, or find the cheapest single clip with the '
             '<a href="/clip.html">clip finder</a>.</p>',
             f'<p class="note">Source: GenCost\'s daily readings of the official pricing pages, {name}.</p>']
    title = f"AI Tool Prices in {name}: What Changed"
    first = re.sub(r"<[^>]+>", "", answer).split(";")[0].split(".<br/>")[0]
    desc = html.escape(f"Every confirmed AI tool price change in {name}, from GenCost's daily readings of the official pricing pages. " + first + ".")[:300]
    head, tail = shell()
    h = re.sub(r"<title>.*?</title>", f"<title>{title} | GenCost</title>", head, flags=re.S)
    h = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{desc}">', h)
    h = re.sub(r"<span>[^<]*</span></nav>", f"<span>Price index {name}</span></nav>", h, count=1)
    page = h + "\n" + "\n".join(body) + "\n" + tail
    summary = f"{len(cheaper)} cheaper, {len(dearer)} dearer, {len(credits)} credit changes, {same} of {len(tools)} tools unchanged"
    return page, summary, len(rows) + len(credits)


def main():
    today = dt.datetime.now(ZoneInfo("Europe/Oslo")).date()
    if "--month" in sys.argv:
        ym = sys.argv[sys.argv.index("--month") + 1]
    elif today.day == 1:
        ym = (today - dt.timedelta(days=1)).strftime("%Y-%m")
    else:
        print("Not the 1st of the month, so no price index today.")
        return
    hist = json.load(open(os.path.join(HERE, "data", "history.json"), encoding="utf-8"))
    if hist.get("since", "9999") > f"{ym}-31":
        print(f"No price history for {ym}.")
        return
    slug = f"ai-tool-prices-{month_name(ym).lower().replace(' ', '-')}-what-changed"
    page, summary, n = build(ym, hist)
    print(f"Price index {ym}: {summary}")
    if "--dry-run" in sys.argv:
        return
    qpath = os.path.join(HERE, "queue", "queue.json")
    q = json.load(open(qpath, encoding="utf-8"))
    if any(i["page"] == f"pages/{slug}.html" for i in q["items"]) or os.path.exists(os.path.join(HERE, "pages", f"{slug}.html")):
        print("The price index for this month already exists.")
        return
    fname = f"queue/index-{ym}-{slug}.html"
    with open(os.path.join(HERE, fname), "w", encoding="utf-8") as f:
        f.write(page)
    card = (f'<li class="reveal"><a class="art" href="/pages/{slug}.html"><span class="cat guide">Price index</span>'
            f"<h3>AI prices in {month_name(ym)}</h3><p>Every confirmed price change</p></a></li>")
    item = {"file": fname, "page": f"pages/{slug}.html", "card": card, "published": ""}
    idx = next((k for k, i in enumerate(q["items"]) if not i.get("published")), len(q["items"]))
    q["items"].insert(idx, item)  # next in line, so it goes live this morning
    json.dump(q, open(qpath, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"Queued as the next article: {fname}")


if __name__ == "__main__":
    main()
