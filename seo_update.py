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
}

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
    for c in ("video", "voice", "music"):
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


def main():
    pages = sorted(p.replace(os.sep, "/") for p in glob.glob("*.html") + glob.glob("pages/**/*.html", recursive=True))
    pages = [p for p in pages if p not in SKIP]
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

        bare = BLOCK.sub("", new)
        noindex = any(re.search(rx, path) for rx in NOINDEX) or path in MOVED
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
