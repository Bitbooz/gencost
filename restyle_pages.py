"""
Puts every content page into the shared GenCost design.

    python restyle_pages.py            convert pages still in an old design
    python restyle_pages.py --refresh  also rebuild already-converted pages
                                       (use after changing site_shell.py)
    python restyle_pages.py pages/x.html   convert just these files

What it does to each page:
  * keeps the title, description, canonical link, JSON-LD and all content
  * swaps the old <style>, background and container for the shared design
  * adds the shared menu, breadcrumb, footer and Google Analytics
  * removes old "← Back to GenCost" links and "Created by" lines
    (the menu, breadcrumb and footer replace them)
  * on tool pages, shows live prices from data/*.json, with the old
    hand-written plan list kept as a fallback

Pages it never touches: index.html, voice.html, music.html, calculator.html,
Google verification files, the numbered project notes (01-...html) and any
file that is empty or broken.

Needs: pip install beautifulsoup4   (lxml optional)
"""
import glob
import os
import re
import sys

from bs4 import BeautifulSoup, Comment

try:
    import lxml  # noqa: F401  (faster, more forgiving parser)
    PARSER = "lxml"
except ImportError:
    PARSER = "html.parser"

import site_shell

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

SKIP_FILES = {"index.html", "voice.html", "music.html", "calculator.html", "index-clean.html", "GenCost-Comparison-Guide.html"}
SKIP_PATTERNS = [re.compile(r"^google[0-9a-f]+\.html$"), re.compile(r"^\d\d-.*\.html$")]

EMERGING = {"seedance", "pixverse", "wan", "openart", "fish-audio", "hume", "resemble", "mureka", "stable-audio", "beatoven"}
VOICE_TOOLS = {"elevenlabs", "cartesia", "murf", "playht", "speechify", "descript", "wellsaid", "fliki"}
MUSIC_TOOLS = {"suno", "udio", "soundraw", "aiva", "boomy"}

# Pages that show live prices: page path -> (category, tool name in data/*.json)
LIVE = {}
try:
    import json
    for cat in ("video", "voice", "music"):
        with open(os.path.join("data", f"{cat}.json"), encoding="utf-8") as f:
            for pf in json.load(f).get("platforms", []):
                if pf.get("page", "").startswith("/"):
                    LIVE[pf["page"].lstrip("/")] = (cat, pf["name"])
except FileNotFoundError:
    print("Note: run regenerate_html.py first to enable live prices on tool pages.")

BACK_RE = re.compile(r"^\s*(←|&larr;|<-)|back to", re.I)


def should_skip(path):
    name = os.path.basename(path)
    if path in SKIP_FILES:  # only matches files in the main folder
        return True
    return any(p.match(name) for p in SKIP_PATTERNS)


def section_for(path):
    """Breadcrumb section and page kind for a file path."""
    p = path.replace("\\", "/")
    slug = os.path.basename(p)[:-5]
    if p.startswith("pages/voice/"):
        return [("Voice", "/voice.html")], "tool"
    if p.startswith("pages/music/"):
        return [("Music", "/music.html")], "tool"
    if p.startswith("pages/samples/"):
        return [("Sample packages", "/order.html")], "sample"
    if p.startswith("pages/"):
        if slug == "emerging":
            return [], "util"
        if "-vs-" in slug or slug.startswith(("cheapest-", "best-")):
            return [("Articles", "/#articles")], "article"
        if slug in EMERGING:
            return [("Emerging tools", "/pages/emerging.html")], "tool"
        if slug in VOICE_TOOLS:
            return [("Voice", "/voice.html")], "tool"
        if slug in MUSIC_TOOLS:
            return [("Music", "/music.html")], "tool"
        return [("Video", "/#platforms")], "tool"
    return [], "util"


def nice_h1(h1_text, title):
    """Turn shouty all-caps headings (e.g. CARTESIA) into normal case."""
    t = h1_text.strip()
    if not t.isupper():
        return None
    guess = re.split(r"\s+(?:Pricing|Price|[|–-])\s*", title or "")[0].strip()
    if guess and guess.lower() == t.lower():
        return guess
    return t[:1] + t[1:].lower()


def is_ga_script(tag):
    src = tag.get("src") or ""
    text = tag.string or ""
    return "googletagmanager" in src or "gtag(" in text


def clean_body(soup, title):
    body = soup.body
    # Comments, styles and analytics inside the body
    for c in body.find_all(string=lambda s: isinstance(s, Comment)):
        c.extract()
    for t in body.find_all("style"):
        t.decompose()
    scripts = []
    for t in body.find_all("script"):
        if is_ga_script(t):
            t.decompose()
        else:
            scripts.append(t.extract())
    # Old one-off site headers / footers inside pages
    for t in body.find_all(["header", "footer"]):
        t.decompose()
    # "← Back to ..." links
    for a in body.find_all("a"):
        if BACK_RE.search(a.get_text(" ", strip=True)):
            parent = a.parent
            a.decompose()
            if parent is not None and parent.name in ("p", "div") and not re.sub(r"[\s·|]+", "", parent.get_text()) and not parent.find(["a", "img", "table"]):
                parent.decompose()
    # "Created by Grok & Bitbooz" lines (footer has it)
    for t in body.find_all(["p", "div"]):
        if getattr(t, "decomposed", False):
            continue
        text = t.get_text(" ", strip=True)
        if "Created by" in text and len(text) < 220 and not t.find(["table", "h2", "h3", "ul"]):
            t.decompose()
    # Unwrap old layout wrappers
    for cls in ("overlay", "container", "wrap"):
        for t in body.find_all(class_=cls):
            t.unwrap()
    for t in body.find_all("main"):
        t.unwrap()
    # Old centred text looks odd in the new left-aligned layout
    for t in body.find_all(["p", "div", "h2", "h3"], style=True):
        style = re.sub(r"text-align\s*:\s*center\s*;?", "", t["style"]).strip()
        if style:
            t["style"] = style
        else:
            del t["style"]
    # Tables scroll sideways on phones
    for table in body.find_all("table"):
        parent = table.parent
        classes = parent.get("class", []) if parent else []
        if "table-wrap" in classes or "table-scroll" in classes:
            continue
        wrapper = soup.new_tag("div", attrs={"class": "table-scroll"})
        table.wrap(wrapper)
    # Headings
    h1 = body.find("h1")
    if h1:
        text = h1.get_text(" ", strip=True)
        if text.upper() == "SAMPLE CONTENT PACKAGE":
            h2 = h1.find_next("h2")
            eyebrow = soup.new_tag("span", attrs={"class": "eyebrow"})
            eyebrow.string = "Sample content package"
            if h2:
                h2.name = "h1"
                h1.replace_with(eyebrow)
                h1 = h2
            else:
                h1.string = "Sample content package"
        else:
            fixed = nice_h1(text, title)
            if fixed:
                h1.string = fixed
        # drop old inline gradient / centering on the h1
        if h1.has_attr("style"):
            del h1["style"]
    return scripts, (h1.get_text(" ", strip=True) if h1 else title)


def add_live_prices(soup, path):
    key = path.replace("\\", "/")
    if key not in LIVE:
        return False
    cat, name = LIVE[key]
    plans = soup.body.find_all(class_="plan")
    if not plans:
        # Simple pages list plans as <ul><li>Plan — $x/mo</li></ul>
        for ul in soup.body.find_all("ul"):
            if "$" in ul.get_text():
                plans = [ul]
                break
    if not plans:
        return False
    first = plans[0]
    parent = first.parent
    container = soup.new_tag("div", attrs={"class": "live-plans", "data-cat": cat, "data-tool": name})
    first.insert_before(container)
    for p in plans:
        if p.parent is parent:
            container.append(p.extract())
    # The old "Prices checked: ..." line is replaced by the live one
    for t in container.parent.find_all("p"):
        if "Prices checked" in t.get_text():
            t.decompose()
    return True


def extract_converted(soup):
    """For --refresh: pull content back out of an already converted page."""
    art = soup.find("article", class_="prose")
    scripts = [s for s in soup.body.find_all("script") if not is_ga_script(s) and "gencost.js" not in (s.get("src") or "")]
    return art, scripts


def convert(path, refresh=False):
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        raw = f.read()
    if not raw.strip():
        return "skipped (empty)"
    soup = BeautifulSoup(raw, PARSER)
    if soup.body is None:
        return "skipped (broken HTML, no <body>)"
    converted = "/assets/gencost.css" in raw
    if converted and not refresh:
        return "already done"

    title = soup.title.get_text(strip=True) if soup.title else os.path.basename(path)
    meta = soup.find("meta", attrs={"name": "description"})
    desc = meta.get("content", "") if meta else ""
    extra = []
    for t in soup.head.find_all(["link", "meta", "script"]) if soup.head else []:
        if t.name == "link" and "canonical" in (t.get("rel") or []):
            extra.append(str(t))
        elif t.name == "meta" and (t.get("property", "").startswith("og:") or t.get("name", "").startswith("twitter:") or t.get("name") == "robots"):
            extra.append(str(t))
        elif t.name == "script" and t.get("type") == "application/ld+json":
            extra.append(str(t))

    section, kind = section_for(path)
    if converted:
        art, script_tags = extract_converted(soup)
        if art is None:
            return "skipped (converted page without content)"
        h1 = art.find("h1")
        heading = h1.get_text(" ", strip=True) if h1 else title
        content = art.decode_contents()
        live = bool(art.find(class_="live-plans"))
    else:
        script_tags, heading = clean_body(soup, title)
        live = add_live_prices(soup, path)
        content = soup.body.decode_contents()

    content = re.sub(r"\n\s*\n+", "\n", content).strip()
    crumb_items = [("Home", "/")] + section + [(heading if len(heading) <= 60 else heading[:57] + "…", None)]

    after = ""
    if kind in ("article", "sample"):
        after = site_shell.ORDER_CTA
    elif kind == "tool" and section:
        label, href = section[0]
        what = "emerging tools" if label == "Emerging tools" else f"{label.lower()} tools"
        after = f"""<div class="page-cta">
  <div><h3>How does it compare?</h3><p>See all {what} side by side in real dollars.</p></div>
  <a class="btn btn-primary" href="{href}">Compare {what} <span class="arrow">→</span></a>
</div>"""

    scripts = "\n".join(str(s) for s in script_tags)
    html = site_shell.page(title, desc, content, crumb_items, kind=kind,
                           extra_head="\n".join(extra), after_html=after, scripts=scripts)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return "converted" + (" + live prices" if live else "")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    refresh = "--refresh" in sys.argv
    if args:
        files = args
    else:
        files = sorted(glob.glob("*.html") + glob.glob("pages/**/*.html", recursive=True))
    counts = {}
    for path in files:
        rel = os.path.relpath(path, ROOT).replace("\\", "/")
        if should_skip(rel):
            continue
        result = convert(rel, refresh)
        counts[result.split(" (")[0]] = counts.get(result.split(" (")[0], 0) + 1
        print(f"{rel}: {result}")
    print("\nSummary:", ", ".join(f"{k}: {v}" for k, v in counts.items()))


if __name__ == "__main__":
    main()
