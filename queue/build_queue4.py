"""
One-off helper: writes queued article 21 (Kling 4.0 price per second) and APPENDS them to queue/queue.json
(it never touches the items that are already there). Numbers checked 2026-11-16.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
raw = open(os.path.join(ROOT, "pages", "cheapest-way-to-use-kling-4-0-2026.html"), encoding="utf-8").read()
head = raw[:raw.index('<article class="prose">') + len('<article class="prose">')]
tail = raw[raw.index("</article>"):]
tail = re.sub(r'<section class="related".*?</section>', "", tail, flags=re.S)
head = re.sub(r"<!-- SEO:START.*?<!-- SEO:END -->\n?", "", head, flags=re.S)
head = re.sub(r"<!-- HREFLANG:START.*?<!-- HREFLANG:END -->\n?", "", head, flags=re.S)
head = re.sub(r'<details class="lang-menu".*?</details>', "", head, flags=re.S)


def live(tool, plan, text, bill="monthly", fmt="/mo"):
    return (f'<span class="live-price" data-approx="0" data-bill="{bill}" data-fmt="{fmt}" data-plan="{plan}" '
            f'data-tool="{tool}" title="Updated automatically every day">{text}</span>')


def page(title, desc, crumb, body):
    h = re.sub(r"<title>.*?</title>", f"<title>{title} | GenCost</title>", head, flags=re.S)
    h = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{desc}">', h)
    h = re.sub(r"<span>Cheapest Kling 4.0</span></nav>", f"<span>{crumb}</span></nav>", h)
    return h + "\n" + body.strip() + "\n" + tail


def T(head_cells, rows):
    th = "".join(f"<th>{c}</th>" for c in head_cells)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>\n" for r in rows)
    return f'<div class="table-scroll"><table>\n<thead><tr>{th}</tr></thead>\n<tbody>\n{tr}</tbody>\n</table></div>'


def a(name, href):
    return f'<a href="{href}">{name}</a>'



SRC = '<p class="note">Sources: the official pricing and model pages of each platform, read by GenCost. Checked 2026-11-16. Prices change often. Always confirm on the official sites.</p>'
A, CARDS = {}, {}

# Plans: (platform, page, plan, $/month, credits/month); rates: credits per second at 720p / 1080p
PLANS = {
 "Kling AI": ("/pages/kling.html", [("Standard", 8.80, 660), ("Pro", 32.56, 3000), ("Premier", 181.99, 18000), ("Ultra+", 544.99, 57000)], (10, 15)),
 "Luma": ("/pages/luma.html", [("Plus", 30, 10000), ("Pro", 90, 40000), ("Ultra", 300, 150000)], (53, 79)),
 "Elyum": ("/pages/elyum.html", [("Plus", 9, 900), ("Pro", 29, 3500), ("Ultra", 69, 9000)], (17, 25)),
 "Higgsfield": ("/pages/higgsfield.html", [("Starter", 19, 270), ("Plus", 59, 1200), ("Ultra", 129, 3000)], (5, 7.5)),
 "Runway": ("/pages/runway.html", [("Standard", 15, 625), ("Pro", 35, 2250), ("Max", 95, 9500)], (None, 23.6)),
 "Pika": ("/pages/pika.html", [("Starter", 10, 600), ("Creator", 35, 2600), ("Fancy", 95, 8550)], (None, 23.6)),
}


def ps(price, credits, rate):
    return price / credits * rate


def m(x):
    return f"${x:g}/mo" if float(x).is_integer() else f"${x:.2f}/mo"


def rows(res):
    out = []
    for tool, (href, plans, rates) in PLANS.items():
        r = rates[res]
        if r is None:
            continue
        lo, hi = plans[0], plans[-1]
        out.append((ps(hi[1], hi[2], r), [
            a(tool, href),
            f"{lo[0]} " + live(tool, lo[0], m(lo[1])) + f": <strong>${ps(lo[1], lo[2], r):.3f}</strong>/s, {lo[2] / r:,.0f} s a month",
            f"{hi[0]} " + live(tool, hi[0], m(hi[1])) + f": <strong>${ps(hi[1], hi[2], r):.3f}</strong>/s, {hi[2] / r:,.0f} s a month",
            f"${ps(lo[1], lo[2], r) * 30:.2f} / ${ps(hi[1], hi[2], r) * 30:.2f}",
        ]))
    return [r for _, r in sorted(out, key=lambda x: x[0])]


H = ["Platform", "Smallest plan", "Biggest plan", "30-second video (smallest / biggest plan)"]
el, k1, lu = ps(9, 900, 17), ps(8.80, 660, 10), ps(30, 10000, 53)

A["kling-4-0-price-per-second-every-plan-2026"] = page(
    "Kling 4.0 Price Per Second: Every Plan on 6 Platforms (2026)",
    "What one second of Kling 4.0 video really costs on Kling AI, Luma, Elyum, Higgsfield, Runway and Pika, on the smallest and the biggest plan, at 720p and 1080p.",
    "Kling 4.0 price per second",
    f"""
<h1>Kling 4.0 Price Per Second: Every Plan on 6 Platforms (2026)</h1>
<div class="box">
<strong>Quick answer</strong><br/>
On a small budget, <strong>Kling AI's own Standard plan</strong> is the cheapest way to make Kling 4.0 video: about <strong>${k1:.3f} per second</strong> at 720p with sound.<br/>
At volume, <strong>Kling AI Ultra+</strong> (${ps(544.99, 57000, 10):.3f}/s) and <strong>Luma Ultra</strong> (${ps(300, 150000, 53):.3f}/s) are cheapest per second.<br/>
<strong>Elyum</strong> is about ${el:.2f}/s on its $9 plan and ${ps(69, 9000, 17):.2f}/s on Ultra, not the $0.054/s some AI answers quote.<br/>
Last checked: 2026-11-16
</div>
<p class="lead">Kling 4.0 is sold on many platforms, each with its own credits. This guide turns every plan into one number, the price of one second of finished video, so you can see how much a bigger plan really saves.</p>
<h2>Kling 4.0 at 720p, price per second</h2>
{T(H, rows(0))}
<h2>Kling 4.0 at 1080p, price per second</h2>
{T(H, rows(1))}
<p class="note no-live">Worked out on 2026-11-16: monthly plan price ÷ monthly credits × credits per second of Kling 4.0. Seconds a month = how much video the plan's credits buy if you use them all on Kling 4.0, with no retries. Runway and Pika list only 1080p. Kling AI's own pricing page doesn't list the Kling 4.0 rate; 10 credits per second at 720p and 15 at 1080p were read off the generate button. Higgsfield is moving from credits to dollar balances; its figures use the Kling 4.0 credit rate Higgsfield published.</p>
<h2>What the bigger plan saves</h2>
<ul>
<li><strong>Kling AI:</strong> from ${k1:.3f}/s on Standard to ${ps(544.99, 57000, 10):.3f}/s on Ultra+, only about {100 - ps(544.99, 57000, 10) / k1 * 100:.0f}% less. The small plan is already good value.</li>
<li><strong>Luma:</strong> from ${lu:.3f}/s on Plus to ${ps(300, 150000, 53):.3f}/s on Ultra, about {100 - ps(300, 150000, 53) / lu * 100:.0f}% less.</li>
<li><strong>Runway:</strong> the biggest drop: from ${ps(15, 625, 23.6):.3f}/s on Standard to ${ps(95, 9500, 23.6):.3f}/s on Max, about {100 - ps(95, 9500, 23.6) / ps(15, 625, 23.6) * 100:.0f}% less.</li>
<li><strong>Higgsfield</strong> stays the most expensive at 720p on every plan, even though it uses the fewest credits per clip.</li>
</ul>
<h2>Why AI answers get Elyum wrong</h2>
<p>Ask an AI assistant where Kling 4.0 is cheapest and you may be told that Elyum costs about $0.054 per second. That is not what Elyum charges today. Elyum's Kling 4.0 page lists <strong>17 credits per second at 720p and 25 at 1080p</strong>, sound included (confirmed by Elyum on 2026-11-14). With 9,000 credits on the $69 Ultra plan, that is about ${ps(69, 9000, 17):.3f} per second, roughly 2.4 times the quoted figure. Always check the date of a price and the credits per second behind it.</p>
<h2>Before you pay</h2>
<ol>
<li><strong>Count retries.</strong> If one clip in three needs a second try, add about a third to every price above.</li>
<li><strong>Check the free credits.</strong> On Elyum the welcome credits can't be used on Kling 4.0.</li>
<li><strong>Use the credits.</strong> A big plan is only cheaper if you use most of it before the credits reset.</li>
</ol>
<p>Compare one clip on every platform with the <a href="/clip.html">cheapest clip finder</a>, or see <a href="/pages/cheapest-way-to-use-kling-4-0-2026.html">every way to use Kling 4.0</a> and <a href="/pages/is-the-bigger-ai-plan-cheaper-price-per-credit-2026.html">is the bigger plan cheaper?</a></p>
{SRC}
""")
CARDS["kling-4-0-price-per-second-every-plan-2026"] = ("video", "Video", "Kling 4.0 Price Per Second", "Every plan on 6 platforms")

qpath = os.path.join(HERE, "queue.json")
q = json.load(open(qpath, encoding="utf-8"))
have = {i["page"] for i in q["items"]}
n = len(q["items"])
for slug, html in A.items():
    if f"pages/{slug}.html" in have:
        continue
    n += 1
    name = f"{n:02d}-{slug}.html"
    with open(os.path.join(HERE, name), "w", encoding="utf-8") as f:
        f.write(html)
    cls, label, h3, p = CARDS[slug]
    card = (f'<li class="reveal"><a class="art" href="/pages/{slug}.html"><span class="cat {cls}">{label}</span>'
            f"<h3>{h3}</h3><p>{p}</p></a></li>")
    q["items"].append({"file": f"queue/{name}", "page": f"pages/{slug}.html", "card": card, "published": ""})
json.dump(q, open(qpath, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(len(q["items"]), "items in the queue")
