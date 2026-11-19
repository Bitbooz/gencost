"""
One-off helper: writes two "extra" news articles about GenCost's new live features (the AI radar and the AI price
exchange), published on 2026-11-20 on top of the 2 daily queued articles. APPENDS them to queue/queue.json.
Numbers are from data/exchange.json on 2026-11-19.
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
    h = re.sub(r'"datePublished":\s*"[^"]*"', '"datePublished": "2026-11-20"', h)
    h = re.sub(r'"dateModified":\s*"[^"]*"', '"dateModified": "2026-11-20"', h)
    return h + "\n" + body.strip() + "\n" + tail.replace(OLD_SLUG, slug)


def faq(qs):
    return "<h2>Questions people ask</h2>\n" + "\n".join(f"<h3>{q}</h3>\n<p>{a}</p>" for q, a in qs)


ARTS = []

# 1. The AI radar
slug = "gencost-ai-radar-watch-ai-assistants-read-prices-live-2026"
ARTS.append((slug, "Live AI radar", "New: the AI radar", "Watch AIs read GenCost live", page(
    slug,
    "The AI Radar: Watch ChatGPT, Claude and Perplexity Read AI Prices Live (2026)",
    "GenCost's new AI radar is a live 3D globe: every light is an AI assistant such as ChatGPT, Claude or Perplexity reading today's AI tool prices on GenCost.",
    "The AI radar",
    """
<h1>The AI Radar: Watch AI Assistants Read GenCost Live</h1>
<div class="box">
<strong>Quick answer</strong><br/>
The <a href="/radar.html">AI radar</a> is a live 3D globe on GenCost. Every glowing line is an AI, such as ChatGPT, Claude, Perplexity or Meta AI, reading GenCost's prices right now, often while answering someone's question. It updates every 15 seconds and stores nothing about people.<br/>
Last checked: 2026-11-20
</div>
<p class="lead">When you ask an AI assistant "what's the cheapest way to make AI videos?", it often fetches a web page to check today's prices. More and more often, that page is GenCost. Now you can watch it happen.</p>
<h2>What you see on the radar</h2>
<ul>
<li><strong>A glowing line</strong> from the AI company's home (for example San Francisco for ChatGPT and Claude, Seattle for Amazon, Moscow for Yandex, Beijing for Baidu) to the region where the page's language is spoken.</li>
<li><strong>Cyan</strong>: an AI reading while answering someone ("a user asked").</li>
<li><strong>Purple</strong>: an AI learning the page for later (crawling).</li>
<li><strong>Pink</strong>: someone's AI asking <a href="/ai.html">GenCost's AI connector</a> directly, for example for the cheapest option.</li>
<li><strong>A line of text</strong> such as "ChatGPT read Kling's prices while answering someone in Portuguese, 12 seconds ago", and a list of the latest visits.</li>
</ul>
<h2>Why GenCost built it</h2>
<p>AI assistants are becoming the place where people compare prices. GenCost is built for them: prices read from each official pricing page every morning, translated into 21 languages, and an <a href="/ai.html">AI connector</a> for ChatGPT, Claude, Cursor and more. The radar makes that invisible traffic visible, so you can see that AI answers about AI prices come from real, checked numbers.</p>
<h2>Honest by design</h2>
<p>The radar shows <strong>which AI</strong> read <strong>which page</strong>, in <strong>which language</strong>. It does not show where any person is: an AI fetches pages from its own servers, so a visitor's country can't be known, and GenCost doesn't guess. Nothing personal is stored: no IP address, no cookie, only the AI's name, the page and the time.</p>
<p>Open it here: <a href="/radar.html">the AI radar</a> · <a href="/live.html">watch this morning's price check</a> · <a href="/exchange.html">the AI price exchange</a></p>
""" + faq([
        ("Is it really live?", "Yes. Each AI visit is recorded the moment it happens, and the radar fetches the latest ones every 15 seconds. At night in Europe and the US it can be quiet for a while."),
        ("Which AI assistants read GenCost?", "Among others ChatGPT, Claude, Perplexity, Meta AI, Amazon, Apple, Google, Bing (Copilot), Yandex, Baidu, ByteDance (Doubao) and Naver."),
        ("Can I make my AI assistant use GenCost?", "Yes. Add GenCost's free AI connector at https://getgencost.com/mcp to Claude, ChatGPT, Cursor, VS Code, Codex, Windsurf or Gemini CLI. The setup for each app is on the AI connector page."),
    ]) + """
<p class="note">GenCost has no affiliate links and no paid placements. Prices are read from each tool's official pricing page every morning.</p>
""")))

# 2. The AI price exchange
slug = "ai-price-exchange-ai-tools-priced-like-shares-2026"
ex = json.load(open(os.path.join(ROOT, "data", "exchange.json"), encoding="utf-8"))
g0, g1 = ex["gcx"][0], ex["gcx"][-1]
drop = [t for t in sorted(ex["tools"], key=lambda t: t["all"]) if t["all"] < 0][:5]
rises = [t for t in ex["tools"] if t["all"] > 0]
day = ex["date"]
movers = "\n".join(f'<tr><td><strong>{t["symbol"]}</strong></td><td><a href="{t["page"]}">{t["name"]}</a></td>'
                   f'<td>${t["price"]:.2f}/mo</td><td>▼ {abs(t["all"]):.1f}%</td></tr>' for t in drop)
cats = {"video": "Video and avatar", "image": "Image", "voice": "Voice", "music": "Music"}
catrows = "\n".join(f'<tr><td>{cats[c]}</td><td>{v[-1]:.1f}</td><td>{(v[-1] - v[0]) / v[0] * 100:+.1f}%</td></tr>'
                    for c, v in ex["categories"].items() if v)
ARTS.append((slug, "AI price exchange", "New: the AI price exchange", "AI tools priced like shares", page(
    slug,
    "The AI Price Exchange: AI Tools Priced Like Shares, With a Daily Index (2026)",
    f"GenCost's AI price exchange shows 50 AI tools like shares, with a daily price index (GCX), sector indices and the biggest price drops. AI tools got {abs((g1 - g0) / g0 * 100):.1f}% cheaper since {ex['since']}.",
    "The AI price exchange",
    f"""
<h1>The AI Price Exchange: AI Tools Priced Like Shares</h1>
<div class="box">
<strong>Quick answer</strong><br/>
The <a href="/exchange.html">AI price exchange</a> shows every AI tool GenCost tracks like a share, with a ticker, charts and a daily index. The GenCost AI Price Index (GCX) started at 1000 on {ex['since']} and stood at <strong>{g1:.1f}</strong> on {day}: AI tools got <strong>{abs((g1 - g0) / g0 * 100):.1f}% cheaper</strong>, and {"no tool raised its price" if not rises else f"{len(rises)} tool(s) raised their price"}.<br/>
Last checked: {day}
</div>
<p class="lead">AI tools change their prices quietly: a yearly discount here, a cheaper plan there. On a normal pricing page you never see the change. On the AI price exchange you do, the same way you see a share go up or down.</p>
<h2>What's on the exchange</h2>
<ul>
<li><strong>A ticker tape</strong> running across the screen, like on Wall Street, with every tool's symbol, price and change.</li>
<li><strong>GCX, the GenCost AI Price Index</strong>: one number for what AI tools cost, starting at 1000.</li>
<li><strong>Sector indices</strong> for video and avatar, image, voice and music.</li>
<li><strong>The biggest price drops and rises</strong>, and <strong>a chart for every tool</strong>.</li>
<li><strong>All 50 "listings"</strong> with 1-day, 7-day and since-start changes. Green ▼ means cheaper, good news for buyers.</li>
</ul>
<h2>The biggest price drops so far</h2>
<div class="table-scroll"><table>
<thead><tr><th>Symbol</th><th>Tool</th><th>Average price</th><th>Since {ex['since']}</th></tr></thead>
<tbody>
{movers}
</tbody></table></div>
<p>"Average price" is the average, over a tool's paid plans, of the cheapest way to pay each month (monthly, or yearly per month when that is cheaper). Most of these drops are bigger yearly discounts.</p>
<h2>Sector indices on {day}</h2>
<div class="table-scroll"><table>
<thead><tr><th>Sector</th><th>Index (start 1000)</th><th>Change</th></tr></thead>
<tbody>
{catrows}
</tbody></table></div>
<h2>How it works</h2>
<p>Every morning GenCost reads the official pricing page of each tool. A new price only counts after it has been seen on two different days, so a misreading or a one-day banner never moves the index. Each tool starts at 100; GCX is the average of all tools, times ten. AI prices don't move every day like shares, so flat lines are real data too. It's not a stock and you can't buy it, but it tells you when it's a good time to buy a plan.</p>
<p>Open it here: <a href="/exchange.html">the AI price exchange</a> · <a href="/compare">compare all plans</a> · <a href="/radar.html">the AI radar</a></p>
""" + faq([
        ("Are AI tools getting cheaper?", f"So far, yes: the GCX index fell from 1000 to {g1:.1f} between {ex['since']} and {day}, mostly through bigger yearly discounts on video and image tools."),
        ("How often is the AI price exchange updated?", "Every morning, after GenCost has read every tool's official pricing page. A new price shows up after it has been confirmed on a second day."),
        ("Can I use the data?", "Yes. The numbers behind the exchange are free to use with credit (CC BY 4.0): getgencost.com/data/exchange.json and the daily dataset on Hugging Face (Bitbooz/ai-tool-prices)."),
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
            f'<h3>{cat}</h3><p>{p_}</p></a></li>')
    items.append({"file": fname, "page": f"pages/{slug}.html", "card": card, "published": "", "extra": True, "publish_on": "2026-11-20"})
json.dump(q, open(qpath, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("queued:", [a[0] for a in ARTS])
