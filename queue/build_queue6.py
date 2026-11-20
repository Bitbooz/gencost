"""
One-off helper: an "extra" article about the free GenCost price box (embed.js) and "Price my video",
published on 2026-11-21 on top of the 2 daily queued articles. APPENDS it to queue/queue.json.
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


def page(slug, title, desc, crumb, body):
    h = head.replace(OLD_SLUG, slug)
    h = re.sub(r"<title>.*?</title>", f"<title>{title} | GenCost</title>", h, flags=re.S)
    for prop in ("description", "og:description", "twitter:description"):
        h = re.sub(rf'(<meta (?:name|property)="{prop}" content=")[^"]*"', lambda m: m.group(1) + desc + '"', h)
    for prop in ("og:title", "twitter:title"):
        h = re.sub(rf'(<meta (?:name|property)="{prop}" content=")[^"]*"', lambda m: m.group(1) + title + '"', h)
    h = re.sub(r"<span>AI connector and Price Finder</span></nav>", f"<span>{crumb}</span></nav>", h)
    h = re.sub(r'"datePublished":\s*"[^"]*"', '"datePublished": "2026-11-21"', h)
    h = re.sub(r'"dateModified":\s*"[^"]*"', '"dateModified": "2026-11-21"', h)
    return h + "\n" + body.strip() + "\n" + tail.replace(OLD_SLUG, slug)


def faq(qs):
    return "<h2>Questions people ask</h2>\n" + "\n".join(f"<h3>{q}</h3>\n<p>{a}</p>" for q, a in qs)


ARTS = []
slug = "free-ai-price-box-for-your-website-2026"
ARTS.append((slug, "Free AI price box", "For bloggers and YouTubers", "Free price box for your site", page(
    slug,
    "Free AI Tool Price Box for Your Website or Blog (Updates Every Day) | 2026",
    "Add a free, self-updating price box for Runway, Kling, ElevenLabs, Suno or any of 50 AI tools to your blog or website. Copy two lines of code; prices update every morning.",
    "Free price box for your site",
    """
<h1>Free AI Tool Price Box for Your Website or Blog</h1>
<div class="box">
<strong>Quick answer</strong><br/>
You can add a free price box for any of the 50 AI tools GenCost tracks to your own website or blog. Copy two lines of code from the bottom of any tool page on GenCost; the box shows today's plans and prices and updates by itself every morning. No sign-up, no key, no tracking.<br/>
Last checked: 2026-11-21
</div>
<p class="lead">Writing about Runway, Kling, ElevenLabs or Suno? AI prices change often, so a price you typed into an article last month may already be wrong. The GenCost price box keeps it right for you.</p>
<h2>How to add it (1 minute)</h2>
<ol>
<li>Open the GenCost page of the tool you write about, for example <a href="/pages/runway.html">Runway</a>, <a href="/pages/kling.html">Kling</a> or <a href="/pages/voice/elevenlabs.html">ElevenLabs</a>.</li>
<li>Scroll to the bottom, to <strong>"Add this price box to your site"</strong>, and copy the code.</li>
<li>Paste it into your page or post where the box should appear (in WordPress: a "Custom HTML" block).</li>
</ol>
<p>The code looks like this:</p>
<pre><code>&lt;div class="gencost-prices" data-tool="Runway" data-cat="video"&gt;
  &lt;a href="https://getgencost.com/pages/runway.html"&gt;Runway pricing&lt;/a&gt; by GenCost
&lt;/div&gt;
&lt;script src="https://getgencost.com/embed.js" async&gt;&lt;/script&gt;</code></pre>
<p>For a dark website, add <code>data-theme="dark"</code> to the first line.</p>
<h2>What the box shows</h2>
<ul>
<li>Every plan of the tool, with the monthly price and the price when paid yearly.</li>
<li>Credits or minutes per plan.</li>
<li>The date the prices were checked, and a link to the full comparison on GenCost.</li>
</ul>
<h2>Why it's free</h2>
<p>GenCost reads every tool's official pricing page each morning and wants those numbers to be used. The box links back to GenCost, which is all we ask. There are no ads, no affiliate links and no cookies in the box.</p>
<h2>New too: price a whole video</h2>
<p>Planning a project instead of a single tool? <a href="/estimate.html">Price my video</a> turns an idea like "a 30-second ad with voice-over and music" into a cost on every platform: clips, credits, the cheapest plan, plus voice and music.</p>
""" + faq([
        ("Does the price box slow down my site?", "No. The script loads after your page (async), and the prices are one small file that browsers cache."),
        ("Which tools can I show?", "Any of the 50 AI video, image, voice and music tools on GenCost, for example Runway, Kling, Pika, Higgsfield, Midjourney, ElevenLabs and Suno. The code is on each tool's page."),
        ("Can AI assistants use the same prices?", "Yes. GenCost also has a free AI connector (MCP) for Claude, ChatGPT, Cursor and more, and an open dataset on Hugging Face."),
    ]) + """
<p class="note">GenCost has no affiliate links and no paid placements. Prices are read from each tool's official pricing page every morning.</p>
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
    items.append({"file": fname, "page": f"pages/{slug}.html", "card": card, "published": "", "extra": True, "publish_on": "2026-11-21"})
json.dump(q, open(qpath, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("queued:", [a[0] for a in ARTS])
