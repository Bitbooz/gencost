"""
One-off helper: an "extra" article answering "How much does Krea AI cost?", published on 2026-11-22
on top of the 2 daily queued articles. APPENDS it to queue/queue.json.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
raw = open(os.path.join(ROOT, "pages", "gencost-ai-connector-and-hugging-face-price-finder-2026.html"), encoding="utf-8").read()
head = raw[:raw.index('<article class="prose">') + len('<article class="prose">')]
tail = raw[raw.index("</article>"):]
tail = re.sub(r'<section class="related".*?</section>', "", tail, flags=re.S)
head = re.sub(r"<!-- SEO:START.*?<!-- SEO:END -->\n?", "", head, flags=re.S)
head = re.sub(r"<!-- HREFLANG:START.*?<!-- HREFLANG:END -->\n?", "", head, flags=re.S)
head = re.sub(r'<details class="lang-menu".*?</details>', "", head, flags=re.S)
OLD_SLUG = "gencost-ai-connector-and-hugging-face-price-finder-2026"


def live(tool, plan, text, bill="monthly", fmt="/mo"):
    return (f'<span class="live-price" data-approx="0" data-bill="{bill}" data-fmt="{fmt}" data-plan="{plan}" '
            f'data-tool="{tool}" title="Updated automatically every day">{text}</span>')


def page(slug, title, desc, crumb, body):
    h = head.replace(OLD_SLUG, slug)
    h = re.sub(r"<title>.*?</title>", f"<title>{title} | GenCost</title>", h, flags=re.S)
    for prop in ("description", "og:description", "twitter:description"):
        h = re.sub(rf'(<meta (?:name|property)="{prop}" content=")[^"]*"', lambda m: m.group(1) + desc + '"', h)
    for prop in ("og:title", "twitter:title"):
        h = re.sub(rf'(<meta (?:name|property)="{prop}" content=")[^"]*"', lambda m: m.group(1) + title + '"', h)
    h = re.sub(r"<span>AI connector and Price Finder</span></nav>", f"<span>{crumb}</span></nav>", h)
    h = re.sub(r'"datePublished":\s*"[^"]*"', '"datePublished": "2026-11-22"', h)
    h = re.sub(r'"dateModified":\s*"[^"]*"', '"dateModified": "2026-11-22"', h)
    return h + "\n" + body.strip() + "\n" + tail.replace(OLD_SLUG, slug)


def faq(qs):
    return "<h2>Questions people ask</h2>\n" + "\n".join(f"<h3>{q}</h3>\n<p>{a}</p>" for q, a in qs)


ARTS = []
slug = "how-much-does-krea-ai-cost-2026"
K = "Krea"
ARTS.append((slug, "How much does Krea AI cost?", "Plans and the price of one video", "How much does Krea cost?", page(
    slug,
    "How Much Does Krea AI Cost? Plans and the Price of One Video (2026)",
    "Krea costs $0 (100 units a day) or $9 a month for Basic. One 5-second Kling 2.5 video costs about $0.47 on Basic; Seedance 2.5 about $1.80. All plans, checked daily.",
    "How much does Krea cost?",
    f"""
<h1>How Much Does Krea AI Cost?</h1>
<div class="box">
<strong>Quick answer</strong><br/>
Krea has a free plan with 100 compute units a day and paid plans from {live(K, "Basic", "$9/mo")} (Basic, 5,000 units a month). On Basic, one 5-second Kling 2.5 video costs about $0.47, and one 5-second Seedance 2.5 video at 720p about $1.80.<br/>
Last checked: 2026-11-22
</div>
<p class="lead">Krea puts many AI video and image models in one subscription: Kling, Seedance, Veo, Wan, LTX and Krea's own image model. You pay with "compute units", and each model uses a different number of them, so the plan price alone doesn't tell you what a video costs. Here's the real price.</p>
<h2>Krea plans</h2>
<div class="table-scroll"><table>
<thead><tr><th>Plan</th><th>Paid monthly</th><th>Paid yearly (per month)</th><th>Compute units</th></tr></thead>
<tbody>
<tr><td>Free</td><td>$0</td><td>$0</td><td>100 a day</td></tr>
<tr><td>Basic</td><td>{live(K, "Basic", "$9/mo")}</td><td>{live(K, "Basic", "$5/mo", bill="yearly")}</td><td>5,000 a month</td></tr>
<tr><td>Pro</td><td>{live(K, "Pro", "$35/mo")}</td><td>{live(K, "Pro", "$21/mo", bill="yearly")}</td><td>20,000 a month</td></tr>
<tr><td>Max</td><td>{live(K, "Max", "$105/mo")}</td><td>{live(K, "Max", "$63/mo", bill="yearly")}</td><td>60,000 a month</td></tr>
</tbody>
</table></div>
<p class="note">Prices in this table update automatically every morning from <a href="https://www.krea.ai/pricing" rel="nofollow">Krea's pricing page</a>.</p>
<h2>What one video costs on Krea Basic</h2>
<div class="table-scroll"><table>
<thead><tr><th>Model</th><th>Clip</th><th>Units per clip</th><th>Videos on Basic</th><th>Price per video</th></tr></thead>
<tbody>
<tr><td>Kling 3.0, standard, no sound</td><td>3 seconds</td><td>about 192</td><td>about 26</td><td>about $0.35</td></tr>
<tr><td>Kling 2.5</td><td>5 seconds</td><td>about 263</td><td>about 19</td><td>about $0.47</td></tr>
<tr><td>LTX-2.5 Fast, 720p</td><td>6 seconds</td><td>about 417</td><td>about 12</td><td>about $0.75</td></tr>
<tr><td>Seedance 2.5, 720p</td><td>5 seconds</td><td>about 1,000</td><td>about 5</td><td>about $1.80</td></tr>
</tbody>
</table></div>
<p class="note">Worked out from Krea's own table of videos per plan: $9 for 5,000 units = $0.0018 per unit. Krea's table is approximate, so these are too.</p>
<h2>Is Krea a good deal?</h2>
<ul>
<li><strong>Yes, if you want many models in one place.</strong> One plan covers Kling, Seedance, Veo, Wan and image models, so you don't need several subscriptions.</li>
<li><strong>For one model only, the maker can be cheaper.</strong> If you only use Kling, compare with <a href="/pages/kling.html">Kling's own plans</a>; for Seedance, see <a href="/pages/cheapest-way-to-use-seedance-2-5-2026.html">the cheapest way to use Seedance 2.5</a>.</li>
<li><strong>Yearly billing saves a lot.</strong> Basic paid yearly is {live(K, "Basic", "$5/mo", bill="yearly")} instead of {live(K, "Basic", "$9/mo")}, so every video above costs about 45% less.</li>
</ul>
<h2>Watch out</h2>
<ul>
<li><strong>The free plan has no commercial license.</strong> You need a paid plan to use the videos for clients or ads.</li>
<li><strong>100 free units a day is less than one Kling 2.5 video</strong> (about 263 units). The free plan is for images and trying things out.</li>
<li><strong>Units don't roll over.</strong> Monthly units are lost at the end of the month, and extra units you buy expire after 90 days.</li>
<li><strong>Retries cost the same as keepers.</strong> If you need three tries per video, multiply the price by three.</li>
</ul>
<p>Want the full cost of a project, with voice and music? Try <a href="/estimate.html">Price my video</a>, or compare all tools on the <a href="/pages/krea.html">Krea page</a> and in the <a href="/clip.html">cheapest clip finder</a>.</p>
""" + faq([
        ("Is Krea free?", "Yes, Krea has a free plan with 100 compute units a day, but no commercial license. Paid plans start with Basic at $9 a month, or $5 a month paid yearly."),
        ("How many videos do you get with Krea Basic?", "About 19 five-second Kling 2.5 videos, or about 5 five-second Seedance 2.5 videos at 720p, from Basic's 5,000 compute units a month."),
        ("Do Krea compute units roll over?", "No. Monthly units are lost at the end of each month, and units you buy on top expire after 90 days."),
    ]) + """
<p class="note">Sources: Krea's official pricing page and its table of videos per plan, checked 2026-11-22. GenCost has no affiliate links and no paid placements. Prices change often; always confirm on the official site.</p>
""")))

qpath = os.path.join(HERE, "queue.json")
q = json.load(open(qpath, encoding="utf-8"))
items = q["items"] if isinstance(q, dict) else q
for slug, h3, cat, p_, html in ARTS:
    fname = f"queue/news-{slug}.html"
    open(os.path.join(ROOT, fname), "w", encoding="utf-8").write(html)
    if any(i.get("page") == f"pages/{slug}.html" for i in items):
        continue
    card = (f'<li class="reveal"><a class="art" href="/pages/{slug}.html"><span class="cat guide">News</span>'
            f'<h3>{h3}</h3><p>{cat}</p></a></li>')
    items.append({"file": fname, "page": f"pages/{slug}.html", "card": card, "published": "", "extra": True, "publish_on": "2026-11-22"})
json.dump(q, open(qpath, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("queued:", [a[0] for a in ARTS])
