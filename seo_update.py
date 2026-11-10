"""
seo_update.py - keeps the technical SEO of getgencost.com right, every day.

Runs after update_articles.py (auto_update.py starts it). For every page it:
  - adds a canonical link if the page has none (duplicate pages point to the main version)
  - adds a meta description if missing (from the page's lead paragraph)
  - adds Open Graph / Twitter tags so shared links get a title, text and image
  - adds structured data (JSON-LD): WebSite on the home page, Article on articles,
    BreadcrumbList where the page has breadcrumbs
  - marks old project files and test samples as "noindex"
  - points links to duplicate pages at the main page
  - rebuilds sitemap.xml with every page that should be found
  - writes seo-review.txt with anything that still needs a human (broken links, missing h1 ...)

Everything it adds sits between <!-- SEO:START --> and <!-- SEO:END --> in <head>,
so it can be rebuilt each day without ever touching the rest of the page.
Hand-written tags outside that block always win.
"""

import glob
import html
import json
import os
import re
from datetime import datetime

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Europe/Oslo")
except Exception:
    TZ = None

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

SITE = "https://getgencost.com"
OG_IMAGE = SITE + "/assets/og-image.png"
TODAY = datetime.now(TZ).strftime("%Y-%m-%d")

SKIP = {"google202bf6f8b03cfa8a.html"}  # Google verification file: leave exactly as it is

# Old project notes and test copies: reachable, but should not be in Google
NOINDEX = [
    r"^\d\d-.*\.html$",
    r"^GenCost-Comparison-Guide\.html$",
    r"^index-clean\.html$",
    r"^alert-thanks\.html$",
    r"^404\.html$",
    r"^pages/sample-package-youtube-ai-tools\.html$",
    r"^pages/samples/.*-(test|short)\.html$",
    r"^pages/samples/(sample|voice-sample)\.html$",
]

# Older copies of tool pages -> the live page that the site links to
DUPLICATES = {f"pages/{n}.html": f"pages/music/{n}.html" for n in ("aiva", "boomy", "soundraw", "suno", "udio")}
DUPLICATES.update({f"pages/{n}.html": f"pages/voice/{n}.html" for n in ("cartesia", "elevenlabs", "murf", "playht", "speechify")})

# Pages about tools that shut down -> the article about their alternatives
# (_redirects sends visitors there too; these pages are kept out of Google)
MOVED = {
    "pages/sora.html": "pages/best-sora-alternatives-2026.html",
    "pages/playht.html": "pages/best-playht-alternatives-2026.html",
    "pages/voice/playht.html": "pages/best-playht-alternatives-2026.html",
    "pages/playht-vs-elevenlabs-pricing-2026.html": "pages/best-playht-alternatives-2026.html",
    # two Runway vs Kling articles were merged into one
    "pages/runway-vs-kling-pricing-comparison-2026.html": "pages/runway-vs-kling-pricing-2026.html",
}

MONTH = datetime.now(TZ).strftime("%B %Y")
TOOLS = {}


def tool_pages():
    """Tool pages with live prices -> (tool name, category), from data/*.json."""
    out = {}
    for c in ("video", "voice", "music", "image"):
        try:
            with open(f"data/{c}.json", encoding="utf-8") as f:
                for pf in json.load(f).get("platforms", []):
                    page = (pf.get("page") or "").lstrip("/")
                    if page.endswith(".html"):
                        out[page] = (pf["name"], c)
        except Exception:
            pass
    return out


def tool_title(name, cat):
    what = {"video": "Plans & Cost per Clip", "image": "Plans & Cost per Image"}.get(cat, "Plans & Real Cost")
    return f"{name} Pricing ({MONTH}): {what} | GenCost"


def tool_desc(name, cat):
    extra = "the real cost per clip" if cat == "video" else "what you really get"
    return (f"{name} pricing for {MONTH}: every plan in US dollars, monthly and yearly, credits, "
            f"{extra} and hidden costs. Checked every morning.")

# Pages for tools that were just added: kept out of Google until the daily check has read their prices
PENDING = {"pages/d-id.html", "pages/colossyan.html",
           "pages/pictory.html", "pages/veed.html", "pages/nightcafe.html"}

# Two pages had the same title; give the second one its own
TITLE_FIXES = {
    "pages/runway-vs-kling-pricing-comparison-2026.html": (
        "Runway vs Kling Pricing Comparison 2026 | GenCost",
        "Runway vs Kling: Cost per Video and Plans Compared (2026) | GenCost"),
    "pages/best-free-ai-video-tools-2026.html": (
        "Best Free AI Video Tools 2026: Kling, Runway, Pika, Luma Compared | GenCost",
        "Best Free AI Video Tools 2026: Kling, Runway, Pika, Luma | GenCost"),
    "pages/cheapest-ai-music-tools-in-2026.html": (
        "Cheapest AI Music Tools in 2026: Suno vs Udio vs AIVA vs Soundraw | GenCost",
        "Cheapest AI Music Tools 2026: Suno vs Udio vs AIVA | GenCost"),
}

FONTS = ('<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap" rel="stylesheet">\n'
         '<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700&amp;text=GENCOSTExamples&amp;display=swap" rel="stylesheet">')

ARTICLE = re.compile(r"^pages/(?:samples/)?[^/]*(-vs-|cheapest-|best-)[^/]*\.html$")
START, END = "<!-- SEO:START (added by seo_update.py, rebuilt daily) -->", "<!-- SEO:END -->"
BLOCK = re.compile(re.escape("<!-- SEO:START") + r".*?" + re.escape(END) + r"\n?", re.S)


def clean_article(raw, title):
    """Fix leftovers from AI-written articles: a stray ```html line, a second <head> pasted into
    the article, a missing <h1>, ' | GenCost' in the breadcrumb. Returns (new_raw, list_of_fixes)."""
    fixes = []
    m = re.search(r"(<article\b[^>]*>)(.*?)(</article>)", raw, re.S)
    if not m:
        return raw, fixes
    body = m.group(2)
    new = re.sub(r"^[ \t]*```[a-z]*[ \t]*\n", "", body, flags=re.M)
    new = re.sub(r"<!DOCTYPE html>\s*", "", new, flags=re.I)
    new = re.sub(r"<title>.*?</title>\s*", "", new, flags=re.S)
    new = re.sub(r"<meta\b[^>]*>\s*", "", new)
    new = re.sub(r"<link\b[^>]*>\s*", "", new)
    if new != body:
        fixes.append("removed code fence / pasted <head> from the article")
    if not re.search(r"<h1\b", new):
        h = re.sub(r"\s*\|\s*GenCost\s*$", "", title)
        new = f"\n<h1>{html.escape(h)}</h1>\n" + new.lstrip("\n")
        fixes.append("added the missing <h1>")
    out = raw[:m.start(2)] + new + raw[m.end(2):]
    out2 = re.sub(r"(<nav class=\"crumbs\".*?<span>)([^<]*?)\s*\|\s*GenCost(</span>)", r"\1\2\3", out, flags=re.S)
    if out2 != out:
        fixes.append("removed ' | GenCost' from the breadcrumb")
    return out2, fixes


def url_for(path):
    return SITE + "/" if path == "index.html" else f"{SITE}/{path}"


def text_of(fragment):
    t = re.sub(r"<(script|style)\b.*?</\1>", " ", fragment, flags=re.S | re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


def short(t, n=155):
    t = t.strip()
    if len(t) <= n:
        return t
    cut = t[:n].rsplit(" ", 1)[0].rstrip(",;:–-")
    return cut + "…"


def meta(raw, name):
    m = re.search(r'<meta\s+(?:name|property)="' + re.escape(name) + r'"\s+content="([^"]*)"', raw, re.I)
    return html.unescape(m.group(1)) if m else None


def lead_text(raw):
    body = raw.split("<body", 1)[-1]
    body = re.sub(r'<section[^>]*class="live-box".*?</section>', " ", body, flags=re.S)
    for rx in (r'<p class="lead"[^>]*>(.*?)</p>', r"<article\b.*?<p[^>]*>(.*?)</p>", r"<main\b.*?<p[^>]*>(.*?)</p>"):
        m = re.search(rx, body, re.S | re.I)
        if m and len(text_of(m.group(1))) >= 40:
            return text_of(m.group(1))
    for p in re.findall(r"<p[^>]*>(.*?)</p>", body, re.S | re.I):
        if len(text_of(p)) >= 60:
            return text_of(p)
    return None


def crumbs(raw):
    m = re.search(r'<nav class="crumbs"[^>]*>(.*?)</nav>', raw, re.S)
    if not m:
        return []
    items = []
    for a in re.finditer(r'<a href="([^"]+)">(.*?)</a>|<span>(?!/)([^<]+)</span>', m.group(1)):
        if a.group(1):
            href = a.group(1)
            items.append((text_of(a.group(2)), href if href.startswith("http") else SITE + href))
        elif a.group(3) and a.group(3).strip() != "/":
            items.append((a.group(3).strip(), None))
    return items


def last_checked(raw):
    m = re.search(r"Last checked:\s*(\d{4}-\d{2}-\d{2})", raw)
    return m.group(1) if m else None


def data_updated():
    days = []
    for c in ("video", "voice", "music", "image"):
        try:
            with open(f"data/{c}.json", encoding="utf-8") as f:
                days.append((json.load(f).get("updated") or "")[:10])
        except Exception:
            pass
    return max([d for d in days if d] or [TODAY])


def build_block(path, raw, canonical, noindex, desc):
    title = re.search(r"<title>([^<]*)</title>", raw)
    title = html.unescape(title.group(1)).strip() if title else "GenCost"
    lines = [START]
    if noindex:
        lines.append('<meta name="robots" content="noindex, follow">')
    if canonical:
        lines.append(f'<link rel="canonical" href="{html.escape(canonical)}">')
    if desc:
        lines.append(f'<meta name="description" content="{html.escape(desc)}">')
    og_desc = meta(raw, "description") or desc or "AI video, voice and music tool prices in real dollars, checked every morning."
    page_url = canonical or (re.search(r'rel="canonical" href="([^"]+)"', raw) or [None, url_for(path)])[1]
    is_article = bool(ARTICLE.match(path))
    if not meta(raw, "og:title"):
        lines += [
            '<meta property="og:site_name" content="GenCost">',
            f'<meta property="og:type" content="{"article" if is_article else "website"}">',
            f'<meta property="og:title" content="{html.escape(title)}">',
            f'<meta property="og:description" content="{html.escape(og_desc)}">',
            f'<meta property="og:url" content="{html.escape(page_url)}">',
            f'<meta property="og:image" content="{OG_IMAGE}">',
            '<meta property="og:image:width" content="1200">',
            '<meta property="og:image:height" content="630">',
            '<meta name="twitter:card" content="summary_large_image">',
            f'<meta name="twitter:title" content="{html.escape(title)}">',
            f'<meta name="twitter:description" content="{html.escape(og_desc)}">',
            f'<meta name="twitter:image" content="{OG_IMAGE}">',
        ]
    if not noindex and "application/ld+json" not in BLOCK.sub("", raw):
        graph = []
        org = {"@type": "Organization", "@id": SITE + "/#org", "name": "GenCost", "url": SITE + "/"}
        if path == "index.html":
            graph += [org, {"@type": "WebSite", "@id": SITE + "/#website", "name": "GenCost", "url": SITE + "/",
                            "description": og_desc, "publisher": {"@id": SITE + "/#org"}}]
        if is_article:
            h1 = re.search(r"<h1[^>]*>(.*?)</h1>", raw, re.S)
            art = {"@type": "Article", "headline": short(text_of(h1.group(1)) if h1 else title, 110),
                   "description": og_desc, "mainEntityOfPage": page_url, "image": OG_IMAGE,
                   "author": {"@type": "Organization", "name": "GenCost", "url": SITE + "/"},
                   "publisher": {"@type": "Organization", "name": "GenCost", "url": SITE + "/"}}
            when = last_checked(raw)
            if when:
                art["dateModified"] = when
            graph.append(art)
        fq = re.search(r'<section class="card faq" data-auto="faq">(.*?)</section>', raw, re.S)
        if fq:
            pairs = re.findall(r"<h3>(.*?)</h3><p>(.*?)</p>", fq.group(1), re.S)
            if pairs:
                graph.append({"@type": "FAQPage", "mainEntity": [
                    {"@type": "Question", "name": text_of(q), "acceptedAnswer": {"@type": "Answer", "text": text_of(a)}}
                    for q, a in pairs]})
        cr = crumbs(raw)
        if len(cr) >= 2:
            graph.append({"@type": "BreadcrumbList", "itemListElement": [
                dict({"@type": "ListItem", "position": i + 1, "name": n}, **({"item": u} if u else {}))
                for i, (n, u) in enumerate(cr)]})
        if graph:
            lines.append('<script type="application/ld+json">'
                         + json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False).replace("</", "<\\/")
                         + "</script>")
    lines.append(END)
    return "\n".join(lines) + "\n"


def page_title(path):
    try:
        raw = open(path, encoding="utf-8").read()
    except Exception:
        return path
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", raw, re.S)
    if h1 and text_of(h1.group(1)):
        return text_of(h1.group(1))
    t = re.search(r"<title>([^<]*)</title>", raw)
    return re.sub(r"\s*\|\s*GenCost$", "", html.unescape(t.group(1))) if t else path


def write_llms_txt(sitemap):
    """llms.txt: a plain map of the site for AI assistants (see llmstxt.org)."""
    urls = [loc for loc, _, _, _ in sitemap]
    def path_of(u):
        p = u.replace(SITE + "/", "")
        return p or "index.html"
    guides = sorted((page_title(path_of(u)), u) for u in urls if ARTICLE.match(path_of(u)) and "/samples/" not in u)
    tools = sorted((page_title(path_of(u)), u) for u in urls if path_of(u) in TOOLS)
    lines = [
        "# GenCost",
        "",
        "> GenCost compares the prices of AI video, avatar, image, voice and music tools in US dollars. "
        "Every price is read from each tool's official pricing page every morning and checked before it goes live. "
        "Pages also show the real cost of one video clip (from each tool's own credits per clip) and hidden costs "
        "such as watermarks, expiring credits and commercial-use rules.",
        "",
        f"Prices last updated: {data_updated()}. How prices are checked: {SITE}/how-we-verify.html",
        "",
        "## Price lists",
        f"- [AI video, avatar and image tools]({SITE}/): every plan, monthly and yearly, with cost per clip",
        f"- [AI voice tools]({SITE}/voice.html): every plan in US dollars",
        f"- [AI music tools]({SITE}/music.html): every plan in US dollars",
        f"- [AI image generators]({SITE}/image.html): every plan in US dollars",
        f"- [Compare any tools]({SITE}/compare.html): two or three tools side by side",
        f"- [Budget calculator]({SITE}/calculator.html): how many clips a budget buys",
        f"- [Project calculator]({SITE}/project.html): the cheapest plan per tool for a monthly amount of video, voiceover, music and images",
        f"- [Machine-readable prices]({SITE}/data/video.json), [voice]({SITE}/data/voice.json), [music]({SITE}/data/music.json), [image]({SITE}/data/image.json)",
        f"- [MCP server]({SITE}/mcp): remote MCP endpoint (Streamable HTTP, no sign-in) with tools list_tools, get_prices, compare_tools, find_cheapest. How to connect: {SITE}/ai.html",
        "",
        "## Guides",
    ] + [f"- [{t}]({u})" for t, u in guides] + ["", "## Tool pricing pages"] + [f"- [{t}]({u})" for t, u in tools] + [""]
    txt = "\n".join(lines)
    old = open("llms.txt", encoding="utf-8").read() if os.path.exists("llms.txt") else ""
    if txt != old:
        with open("llms.txt", "w", encoding="utf-8", newline="") as f:
            f.write(txt)


def main():
    pages = sorted(p.replace(os.sep, "/") for p in glob.glob("*.html") + glob.glob("pages/**/*.html", recursive=True))
    pages = [p for p in pages if p not in SKIP]
    global TOOLS
    TOOLS = tool_pages()
    existing = set(pages)
    report, changed, sitemap, report_fixed = [], 0, [], []
    counts = {"canonical": 0, "description": 0, "noindex": 0, "links": 0, "titles": 0}
    broken = {}
    updated = data_updated()

    old_lastmod = {}
    if os.path.exists("sitemap.xml"):
        for loc, lm in re.findall(r"<loc>([^<]+)</loc>\s*<lastmod>([^<]+)</lastmod>", open("sitemap.xml", encoding="utf-8-sig").read()):
            old_lastmod[loc] = lm

    for path in pages:
        try:
            with open(path, encoding="utf-8") as f:
                raw = f.read()
        except UnicodeDecodeError:
            # old files saved in another encoding: only add "noindex", byte-for-byte safe
            if any(re.search(rx, path) for rx in NOINDEX):
                with open(path, encoding="latin-1") as f:
                    raw = f.read()
                if START not in raw and "</head>" in raw:
                    with open(path, "w", encoding="latin-1", newline="") as f:
                        f.write(raw.replace("</head>", f'{START}\n<meta name="robots" content="noindex, follow">\n{END}\n</head>', 1))
                    changed += 1
                counts["noindex"] += 1
            else:
                report.append(f"  {path}: not UTF-8, skipped")
            continue
        if not raw.strip():
            report.append(f"  {path}: empty file (delete it on GitHub, or leave it - it is marked noindex)")
            continue
        new = raw

        if path in TOOLS:
            name, cat = TOOLS[path]
            # the "How does it compare?" box at the bottom points to the tool's own category
            word, href = {"video": ("video", "/#platforms"), "voice": ("voice", "/voice.html"),
                          "music": ("music", "/music.html"), "image": ("image", "/image.html")}.get(cat, ("video", "/#platforms"))
            new = re.sub(r'<p>See all \w+ tools side by side in real dollars\.</p></div>\s*<a class="btn btn-primary" href="[^"]*">Compare \w+ tools',
                         f'<p>See all {word} tools side by side in real dollars.</p></div>\n  <a class="btn btn-primary" href="{href}">Compare {word} tools', new, count=1)
            want_t, want_d = tool_title(name, cat), tool_desc(name, cat)
            t0 = re.search(r"<title>[^<]*</title>", new)
            if t0 and t0.group(0) != f"<title>{html.escape(want_t, quote=False)}</title>":
                new = new.replace(t0.group(0), f"<title>{html.escape(want_t, quote=False)}</title>", 1)
                counts["titles"] += 1
            cm = re.search(r'(<nav class="crumbs"[^>]*>.*<span>)([^<]*)(</span></nav>)', new)
            if cm and cm.group(2) != name:
                new = new[:cm.start(2)] + html.escape(name, quote=False) + new[cm.end(2):]
            d0 = re.search(r'<meta name="description" content="[^"]*">', BLOCK.sub("", new))
            want_meta = f'<meta name="description" content="{html.escape(want_d)}">'
            if d0 and d0.group(0) != want_meta:
                new = new.replace(d0.group(0), want_meta, 1)

        if path in TITLE_FIXES:
            a, b = TITLE_FIXES[path]
            if f"<title>{a}</title>" in new:
                new = new.replace(f"<title>{a}</title>", f"<title>{b}</title>")
                counts["titles"] += 1

        if ARTICLE.match(path):
            t0 = re.search(r"<title>([^<]*)</title>", new)
            new, fx = clean_article(new, html.unescape(t0.group(1)) if t0 else "")
            for x in fx:
                report_fixed.append(f"  {path}: {x}")

        # links to old duplicate pages -> the main page
        for dup, main_page in list(DUPLICATES.items()) + list(MOVED.items()):
            for q in ('"', "'"):
                old_href, new_href = f"href={q}/{dup}{q}", f"href={q}/{main_page}{q}"
                if old_href in new:
                    counts["links"] += new.count(old_href)
                    new = new.replace(old_href, new_href)

        # speed: Orbitron is only used for the logo (and one heading), so load just those letters
        # menu: "Image" next to "Music"
        music_li = '<li><a href="/music.html" data-section="/music,/pages/music/">Music</a></li>'
        if 'data-section="/image"' not in new and music_li in new:
            new = new.replace(music_li, music_li + '\n      <li><a href="/image.html" data-section="/image">Image</a></li>', 1)

        # menu: "Calculators" (budget + project calculator)
        new = new.replace('<li><a href="/calculator.html">Calculator</a></li>', '<li><a href="/calculator.html">Calculators</a></li>')
        # the two calculators point to each other
        XLINK_B = ('<div class="box calc-switch"><strong>Planning a whole project?</strong> Videos, voiceover, music and images each month: '
                   '<a href="/project.html">try the project calculator →</a></div>')
        if path == "calculator.html" and "calc-switch" not in new:
            new = re.sub(r'(<h1>How much AI video can I get for my budget\?</h1>\s*<p class="lead">.*?</p>)', lambda m: m.group(1) + "\n" + XLINK_B, new, count=1, flags=re.S)
        # footer: project calculator next to the budget calculator
        if '<li><a href="/project.html">Project calculator</a></li>' not in new and '<li><a href="/calculator.html">Budget calculator</a></li>' in new:
            new = new.replace('<li><a href="/calculator.html">Budget calculator</a></li>',
                              '<li><a href="/calculator.html">Budget calculator</a></li>\n          <li><a href="/project.html">Project calculator</a></li>', 1)
        # footer: "Use GenCost in AI assistants" (the MCP server page)
        if 'href="/ai.html"' not in new and '<li><a href="/about.html">About GenCost</a></li>' in new:
            new = new.replace('<li><a href="/about.html">About GenCost</a></li>',
                              '<li><a href="/ai.html">Use in Claude &amp; ChatGPT</a></li>\n          <li><a href="/about.html">About GenCost</a></li>', 1)
        # footer: link to the About page next to "Order a package"
        if 'href="/about.html"' not in new and '<li><a href="/order.html">Order a package</a></li>' in new:
            new = new.replace('<li><a href="/order.html">Order a package</a></li>',
                              '<li><a href="/about.html">About GenCost</a></li>\n          <li><a href="/order.html">Order a package</a></li>', 1)

        if FONTS not in new:
            new = re.sub(r'<link href="https://fonts\.googleapis\.com/css2\?family=[^"]*Orbitron[^"]*" rel="stylesheet">',
                         FONTS, new, count=1)

        bare = BLOCK.sub("", new)
        noindex = (any(re.search(rx, path) for rx in NOINDEX) or path in MOVED
                   or (path in PENDING and path not in TOOLS))  # new tool page before its first prices
        has_canon = 'rel="canonical"' in bare
        canonical = None
        if not has_canon:
            canonical = url_for(DUPLICATES.get(path, path))
            counts["canonical"] += 1
        desc = None
        if not meta(bare, "description") and not noindex and ARTICLE.match(path):
            h1 = re.search(r"<h1[^>]*>(.*?)</h1>", bare, re.S)
            name = text_of(h1.group(1)) if h1 else ""
            desc = short(f"{name}: today's prices in US dollars, the real cost per clip and which tool "
                         "is cheaper. Checked every morning.") if name else None
            counts["description"] += bool(desc)
        elif not meta(bare, "description") and not noindex:
            lt = lead_text(bare)
            if lt:
                desc = short(lt)
                counts["description"] += 1
            else:
                report.append(f"  {path}: no description and no text to make one from")
        counts["noindex"] += noindex

        block = build_block(path, bare, canonical, noindex, desc)
        if "</head>" in bare:
            new = bare.replace("</head>", block + "</head>", 1)
        else:
            report.append(f"  {path}: no </head>, SEO tags not added")
            new = bare
        if new != raw:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(new)
            changed += 1

        # checks for a human
        if not noindex:
            t = re.search(r"<title>([^<]*)</title>", new)
            if not t or not t.group(1).strip():
                report.append(f"  {path}: no <title>")
            elif len(html.unescape(t.group(1))) > 70:
                report.append(f"  {path}: title is {len(html.unescape(t.group(1)))} characters (Google shows about 60)")
            h1s = len(re.findall(r"<h1\b", new))
            if h1s != 1:
                report.append(f"  {path}: {h1s} <h1> headings (should be exactly 1)")
        for href in re.findall(r'href="(/[^"#?]*)"', new):
            target = href.lstrip("/")
            if not target or target.endswith("/"):
                target += "index.html"
            if not os.path.splitext(target)[1]:
                target += ".html"
            if target not in existing and not os.path.exists(target):
                broken.setdefault(href, set()).add(path)

        # sitemap: pages that should be found, at their canonical address
        canon_now = re.search(r'rel="canonical" href="([^"]+)"', new)
        canon_now = canon_now.group(1) if canon_now else url_for(path)
        if not noindex and path not in DUPLICATES and canon_now == url_for(path):
            live = ("live-price" in new or "live-plans" in new or "GenCost.start" in new or "GC.start" in new
                    or path in ("index.html", "voice.html", "music.html", "compare.html", "calculator.html"))
            lastmod = updated if live else (last_checked(new) or old_lastmod.get(canon_now) or TODAY)
            prio = "1.0" if path == "index.html" else ("0.9" if path.count("/") == 0 else ("0.8" if ARTICLE.match(path) else "0.7"))
            sitemap.append((canon_now, lastmod, "daily" if live else "weekly", prio))

    sitemap.sort(key=lambda x: (-float(x[3]), x[0]))
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lm, cf, pr in sitemap:
        xml.append(f"  <url>\n    <loc>{html.escape(loc)}</loc>\n    <lastmod>{lm}</lastmod>\n    <changefreq>{cf}</changefreq>\n    <priority>{pr}</priority>\n  </url>")
    xml.append("</urlset>\n")
    xml = "\n".join(xml)
    old = open("sitemap.xml", encoding="utf-8-sig").read() if os.path.exists("sitemap.xml") else ""
    if xml != old:
        with open("sitemap.xml", "w", encoding="utf-8", newline="") as f:
            f.write(xml)

    write_llms_txt(sitemap)

    head = [f"SEO check {datetime.now(TZ).strftime('%Y-%m-%d %H:%M')}",
            f"{len(pages)} pages checked, {changed} changed today, {len(sitemap)} in sitemap.xml, {counts['noindex']} marked noindex",
            f"Made by this script: {counts['canonical']} canonical links, {counts['description']} descriptions; today: "
            f"{counts['links']} links moved to the main page, {counts['titles']} titles fixed", ""]
    if broken:
        head.append("Links to pages that don't exist (fix or remove these links):")
        for href, where in sorted(broken.items()):
            head.append(f"  {href}  <- on {len(where)} page(s), e.g. {sorted(where)[0]}")
        head.append("")
    if report_fixed:
        head.append("Fixed today:")
        head += report_fixed
        head.append("")
    head.append("Needs a human:" if report else "Nothing else to fix.")
    with open("seo-review.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(head + report) + "\n")
    print("\n".join(head[:3]))


if __name__ == "__main__":
    main()
