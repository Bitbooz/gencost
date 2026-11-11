"""
Builds the Spanish version of GenCost under /es/.

Every page in sitemap.xml gets a Spanish copy at /es/<same path>. Runs every morning after
seo_update.py, so the Spanish pages always carry today's prices.

How it translates:
- Text is translated in blocks (a paragraph, a table cell, a heading ...), so sentences stay whole.
- Numbers and prices are replaced by [[0]], [[1]] ... before translating, so a price change never
  needs a new translation, and Grok can never change a price.
- Inline tags (links, bold, live prices) are replaced by <t0>...</t0> and put back afterwards,
  with their original attributes.
- Every translation is stored in data/i18n/es.json and reused. Grok (XAI_API_KEY) is only asked
  for text it has not translated before. Without a key, the stored translations are used.
- A page is only published in Spanish when at least MIN_COVERAGE of its text is translated.
- Text that the page's JavaScript writes (price tables, calculators) is collected with a headless
  browser and translated too; assets/i18n.js swaps it in on the Spanish pages.

Run: python translate_site.py            (normal daily run)
     python translate_site.py --no-browser   (skip collecting JavaScript text)
"""
import html
import json
import os
import re
import sys
import threading
import time
from collections import Counter
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from bs4 import BeautifulSoup, NavigableString, Comment

SITE = "https://getgencost.com"
LANG = "es"
OUT = "es"
CACHE_FILE = os.path.join("data", "i18n", "es.json")
UI_FILE = os.path.join("data", "i18n", "es-ui.json")
MIN_COVERAGE = 0.9
MAX_BATCHES = 150          # Grok calls per run at most (the first run translates the most)
BATCH_CHARS = 7000
BATCH_ITEMS = 40
WORKERS = 6               # Grok calls at the same time
MODEL = "grok-3"
API_KEY = (os.getenv("XAI_API_KEY") or "").strip()

INLINE = {"a", "abbr", "b", "br", "cite", "del", "em", "i", "img", "ins", "kbd", "mark", "q", "s",
          "small", "span", "strong", "sub", "sup", "time", "u", "wbr", "input"}
VOID = {"br", "img", "wbr", "input"}
SKIP = {"script", "style", "noscript", "textarea", "pre", "code", "svg", "template", "iframe", "head"}
ATTRS = ("title", "alt", "placeholder", "aria-label")
NUM = re.compile(r"[$€£]?\d(?:[\d,.]*\d)?")
TOKEN = re.compile(r"\[\[(\d+)\]\]")
LETTERS = re.compile(r"[A-Za-z]{2}")
NOT_TRANSLATED_PREFIXES = ("/data/", "/assets/", "/embed.js", "/mcp", "/es/")


# ---------- small helpers ----------

def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=0, sort_keys=True)
    os.replace(tmp, path)


def mask(text, nums):
    """Replace numbers by [[n]] and remember them in nums (shared across one unit)."""
    def rep(m):
        nums.append(m.group(0))
        return f"[[{len(nums) - 1}]]"
    return NUM.sub(rep, text)


def unmask(text, nums):
    return TOKEN.sub(lambda m: nums[int(m.group(1))] if int(m.group(1)) < len(nums) else "", text)


def norm(text):
    return re.sub(r"\s+", " ", text)


def skipped(el):
    if el.name in SKIP:
        return True
    cls = el.get("class") or []
    return "notranslate" in cls or "logo" in cls or el.get("translate") == "no" or "lang-switch" in cls


def has_block(el):
    for d in el.descendants:
        if getattr(d, "name", None) and (d.name not in INLINE or d.name in SKIP):
            return True
    return False


# ---------- units: one block of text with its inline tags ----------

class Unit:
    """A block's contents as 'Hello <t0>[[0]]/mo</t0> world', plus what is needed to rebuild it."""

    def __init__(self, node, is_text=False):
        self.node, self.is_text = node, is_text
        self.nums, self.shells = [], []
        if is_text:
            raw = str(node)
            self.lead = raw[:len(raw) - len(raw.lstrip())]
            self.trail = raw[len(raw.rstrip()):]
            self.key = html.escape(mask(norm(raw).strip(), self.nums), quote=False)
        else:
            self.key = self._ser(node).strip()
            self.key = re.sub(r"\s+", " ", self.key)

    def _ser(self, el):
        out = []
        for c in el.children:
            if isinstance(c, Comment):
                continue
            if isinstance(c, NavigableString):
                out.append(html.escape(mask(norm(str(c)), self.nums), quote=False))
            elif c.name in VOID:
                i = len(self.shells)
                self.shells.append(c)
                out.append(f"<t{i}/>")
            else:
                i = len(self.shells)
                self.shells.append(c)
                out.append(f"<t{i}>" + self._ser(c) + f"</t{i}>")
        return "".join(out)

    def worth(self):
        return bool(LETTERS.search(TOKEN.sub("", re.sub(r"</?t\d+/?>", "", self.key))))

    def apply(self, soup, translated):
        """Put the translation in place. False if it does not fit (then the English stays)."""
        if self.is_text:
            if re.search(r"</?t\d+", translated) or set(TOKEN.findall(translated)) - {str(i) for i in range(len(self.nums))}:
                return False
            self.node.replace_with(NavigableString(self.lead + html.unescape(unmask(translated, self.nums)) + self.trail))
            return True
        nodes = self._build(soup, translated)
        if nodes is None:
            return False
        self.node.clear()
        for n in nodes:
            self.node.append(n)
        return True

    def _build(self, soup, s):
        parts = re.split(r"(<t\d+/>|<t\d+>|</t\d+>)", s)
        root = soup.new_tag("div")
        stack = [(None, root)]
        used = set()
        valid = {str(i) for i in range(len(self.nums))}
        for p in parts:
            if not p:
                continue
            m = re.fullmatch(r"<t(\d+)(/?)>", p)
            e = re.fullmatch(r"</t(\d+)>", p)
            if m:
                i = int(m.group(1))
                if i >= len(self.shells) or i in used:
                    return None
                used.add(i)
                shell = self.shells[i]
                new = soup.new_tag(shell.name, attrs=dict(shell.attrs))
                stack[-1][1].append(new)
                if m.group(2) != "/":
                    if shell.name in VOID:
                        return None
                    stack.append((i, new))
                elif shell.name not in VOID:
                    return None
            elif e:
                if stack[-1][0] != int(e.group(1)):
                    return None
                stack.pop()
            else:
                if set(TOKEN.findall(p)) - valid:
                    return None
                stack[-1][1].append(NavigableString(html.unescape(unmask(p, self.nums))))
        if len(stack) != 1 or used != set(range(len(self.shells))):
            return None
        return list(root.contents)


def collect_units(body):
    units = []

    def walk(el):
        if skipped(el):
            return
        if not has_block(el):
            u = Unit(el)
            if u.worth():
                units.append(u)
            return
        for c in list(el.children):
            if isinstance(c, Comment):
                continue
            if isinstance(c, NavigableString):
                if LETTERS.search(str(c)):
                    u = Unit(c, is_text=True)
                    if u.worth():
                        units.append(u)
            elif c.name:
                if c.name in INLINE and not has_block(c) and not skipped(c):
                    u = Unit(c)
                    if u.worth():
                        units.append(u)
                else:
                    walk(c)
    walk(body)
    return units


class AttrUnit:
    def __init__(self, el, attr):
        self.el, self.attr, self.nums = el, attr, []
        self.key = html.escape(mask(norm(el.get(attr, "")).strip(), self.nums), quote=False)

    def worth(self):
        return bool(LETTERS.search(TOKEN.sub("", self.key)))

    def apply(self, soup, translated):
        if re.search(r"</?t\d+", translated):
            return False
        self.el[self.attr] = html.unescape(unmask(translated, self.nums))
        return True


def collect_attr_units(soup):
    units = []
    for el in soup.find_all(True):
        if el.name in ("script", "style", "textarea"):
            continue
        for a in ATTRS:
            if el.get(a):
                units.append(AttrUnit(el, a))
        if el.name == "input" and el.get("type") in ("submit", "button") and el.get("value"):
            units.append(AttrUnit(el, "value"))
    for m in soup.find_all("meta"):
        if (m.get("name") in ("description", "twitter:title", "twitter:description")
                or m.get("property") in ("og:title", "og:description")) and m.get("content"):
            units.append(AttrUnit(m, "content"))
    return [u for u in units if u.worth()]


# ---------- Grok ----------

PROMPT = """You translate the website GenCost (an independent price comparison of AI video, image, voice and music tools) from English to Spanish.
Write neutral Latin American Spanish that also reads naturally in Spain. Use "tú". Keep it short, clear and natural, like a good human translator.
Strict rules:
- Keep every tag like <t0>...</t0> or <t3/> exactly as written (same numbers), around the matching words. Do not add or remove tags.
- Keep every token like [[0]] exactly as written. They stand for numbers and prices.
- Do not translate names of tools, companies, models or plans (GenCost, Runway, Kling AI, HeyGen, Gen-4.5, Standard, Pro, Creator, Free ...). "credits" -> "créditos".
- "/mo" -> "/mes", "per month" -> "al mes", "billed yearly"/"paid yearly" -> "pago anual".
- Return ONLY a JSON object that maps each id to its translation, nothing else.

Snippets (JSON, id -> English):
"""


def grok_translate(items):
    """items: {id: english}. Returns {id: spanish} (possibly partial)."""
    from openai import OpenAI
    client = OpenAI(api_key=API_KEY, base_url="https://api.x.ai/v1", timeout=180)
    r = client.chat.completions.create(
        model=MODEL, temperature=0,
        messages=[{"role": "user", "content": PROMPT + json.dumps(items, ensure_ascii=False)}])
    text = r.choices[0].message.content.strip()
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    out = json.loads(text)
    return {k: v for k, v in out.items() if k in items and isinstance(v, str) and v.strip()}


def fits(src, dst):
    """The translation keeps the same tags and tokens as the English."""
    tags = lambda s: sorted(re.findall(r"</?t\d+/?>", s))
    toks = lambda s: sorted(TOKEN.findall(s))
    return tags(src) == tags(dst) and toks(src) == toks(dst)


def translate_missing(keys, cache, translator, report):
    todo = [k for k in dict.fromkeys(keys) if k not in cache]
    if not todo:
        return 0
    if translator is None:
        report.append(f"{len(todo)} texts not translated yet (no XAI_API_KEY)")
        return 0
    batches, cur, size = [], [], 0
    for k in todo:
        if cur and (size + len(k) > BATCH_CHARS or len(cur) >= BATCH_ITEMS):
            batches.append(cur)
            cur, size = [], 0
        cur.append(k)
        size += len(k)
    if cur:
        batches.append(cur)
    def one(batch):
        items = {str(i): k for i, k in enumerate(batch)}
        for attempt in range(3):
            try:
                return items, translator(items), None
            except Exception as e:
                err = f"{type(e).__name__}: {str(e)[:120]}"
                time.sleep(3 + 5 * attempt)
        return items, {}, err

    done = 0
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for n, (items, got, err) in enumerate(pool.map(one, batches[:MAX_BATCHES])):
            if err:
                report.append(f"batch {n + 1}: {err}")
            for i, k in items.items():
                v = got.get(i)
                if v and fits(k, v):
                    cache[k] = v
                    done += 1
                elif v:
                    report.append(f"translation did not keep the tags or numbers, kept English: {k[:70]}")
            if n % 10 == 9:
                save_json(CACHE_FILE, cache)
    save_json(CACHE_FILE, cache)
    if len(batches) > MAX_BATCHES:
        report.append(f"{len(batches) - MAX_BATCHES} batches left for the next run")
    return done


# ---------- pages ----------

def sitemap_pages():
    try:
        xml = open("sitemap.xml", encoding="utf-8").read()
    except FileNotFoundError:
        return []
    out = []
    for loc in re.findall(r"<loc>([^<]+)</loc>", xml):
        if not loc.startswith(SITE) or "/es/" in loc:
            continue
        path = loc[len(SITE):] or "/"
        f = "index.html" if path == "/" else path.lstrip("/")
        if not f.endswith(".html"):
            f += ".html"
        if os.path.exists(f):
            out.append((path if path != "/" else "/", f))
    return out


def es_path(path):
    return "/es/" if path in ("/", "/index.html") else "/es" + path


def es_file(f):
    return os.path.join(OUT, f)


def url_path(href):
    """'/pages/x.html#a' -> ('/pages/x.html', '#a'); None for external or not translatable."""
    if href.startswith(SITE):
        href = href[len(SITE):] or "/"
    if not href.startswith("/") or href.startswith("//") or href.startswith(NOT_TRANSLATED_PREFIXES):
        return None
    m = re.match(r"([^#?]*)(.*)", href)
    return m.group(1) or "/", m.group(2)


def to_es(href, translated):
    up = url_path(href)
    if not up:
        return href
    p, rest = up
    key = "/" if p in ("/", "/index.html") else p
    if key in translated or (key + ".html") in translated:
        return es_path(p) + rest
    return href


def set_lang_switch(soup, href, label, lang):
    right = soup.select_one("nav.top .nav-right")
    if not right:
        return
    for old in right.select("a.lang-switch"):
        old.decompose()
    a = soup.new_tag("a", attrs={"class": "lang-switch", "href": href, "hreflang": lang, "lang": lang,
                                 "title": "Español" if lang == "es" else "English"})
    a.string = label
    right.insert(0, a)


HREF_START, HREF_END = "<!-- HREFLANG:START -->", "<!-- HREFLANG:END -->"


def hreflang_block(path):
    en = SITE + ("/" if path == "/" else path)
    es = SITE + es_path(path)
    return (f'{HREF_START}\n<link rel="alternate" hreflang="en" href="{en}">\n'
            f'<link rel="alternate" hreflang="es" href="{es}">\n'
            f'<link rel="alternate" hreflang="x-default" href="{en}">\n{HREF_END}\n')


def put_hreflang(raw, path):
    raw = re.sub(re.escape(HREF_START) + r".*?" + re.escape(HREF_END) + r"\n?", "", raw, flags=re.S)
    return raw.replace("</head>", hreflang_block(path) + "</head>", 1)


def drop_hreflang(raw):
    return re.sub(re.escape(HREF_START) + r".*?" + re.escape(HREF_END) + r"\n?", "", raw, flags=re.S)


def translate_jsonld(soup, cache, keys_only, translated):
    """FAQ and article texts in structured data, and links to the Spanish pages."""
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(s.string or "")
        except Exception:
            continue

        def walk(o):
            if isinstance(o, dict):
                for k, v in list(o.items()):
                    if isinstance(v, str) and k in ("name", "text", "headline", "description") and o.get("@type") != "Organization":
                        nums = []
                        key = html.escape(mask(norm(v).strip(), nums), quote=False)
                        if LETTERS.search(TOKEN.sub("", key)):
                            keys_only.append(key)
                            if key in cache and not re.search(r"</?t\d+", cache[key]):
                                o[k] = html.unescape(unmask(cache[key], nums))
                    elif isinstance(v, str) and k in ("item", "mainEntityOfPage", "url") and v.startswith(SITE):
                        o[k] = SITE + to_es(v, translated)
                    else:
                        walk(v)
            elif isinstance(o, list):
                for x in o:
                    walk(x)
        walk(data)
        if keys_only is not None:
            s.string = json.dumps(data, ensure_ascii=False)


def build_page(path, f, cache, translated, keys):
    """Returns (spanish html or None, coverage). Adds every text key it needs to keys."""
    raw = open(f, encoding="utf-8").read()
    soup = BeautifulSoup(drop_hreflang(raw), "html.parser")
    body = soup.body
    if body is None:
        return None, 0
    units = collect_units(body)
    if soup.title and soup.title.string and LETTERS.search(soup.title.string):
        units.append(Unit(soup.title.string, is_text=True))
    units += collect_attr_units(soup)
    total = ok = 0
    for u in units:
        keys.append(u.key)
        w = len(u.key)
        total += w
        tr = cache.get(u.key)
        if tr and u.apply(soup, tr):
            ok += w
    jsonld_keys = []
    translate_jsonld(soup, cache, jsonld_keys, translated)
    keys.extend(jsonld_keys)
    coverage = ok / total if total else 1
    # language, links, address
    if soup.html:
        soup.html["lang"] = LANG
    for a in soup.find_all(["a", "form", "link"]):
        attr = "action" if a.name == "form" else "href"
        if a.get(attr) and not (a.name == "link" and a.get("rel") and a.get("rel")[0] in ("canonical", "alternate", "stylesheet", "icon", "preconnect", "manifest")):
            a[attr] = to_es(a[attr], translated)
    for a in soup.select("a[data-section]"):
        a["data-section"] = ",".join("/es" + s if s.startswith("/") else s for s in a["data-section"].split(","))
    can = soup.find("link", rel="canonical")
    if can:
        can["href"] = SITE + es_path(path)
    og = soup.find("meta", property="og:url")
    if og:
        og["content"] = SITE + es_path(path)
    set_lang_switch(soup, path if path != "/" else "/", "EN", "en")
    if not soup.find("script", src="/assets/i18n.js") and soup.head:
        soup.head.append(soup.new_tag("script", attrs={"defer": "", "src": "/assets/i18n.js"}))
    out = str(soup).replace("</head>", hreflang_block(path) + "</head>", 1)
    return out, coverage


# ---------- text written by JavaScript ----------

COLLECT_JS = r"""() => {
  const NUM = /[$€£]?\d(?:[\d,.]*\d)?/g, out = [];
  const skip = (el) => el.closest('script,style,textarea,pre,code,svg,.notranslate,.logo,.lang-switch,[translate=no]');
  const add = (s) => {
    s = (s || '').replace(/\s+/g, ' ').trim();
    let n = 0; const k = s.replace(NUM, () => '[[' + (n++) + ']]');
    if (/[A-Za-z]{2}/.test(k.replace(/\[\[\d+\]\]/g, ''))) out.push(k);
  };
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let t; while ((t = w.nextNode())) { if (!skip(t.parentElement)) add(t.nodeValue); }
  document.querySelectorAll('[placeholder],[title],[aria-label]').forEach((el) => {
    if (skip(el)) return; ['placeholder', 'title', 'aria-label'].forEach((a) => el.getAttribute(a) && add(el.getAttribute(a)));
  });
  return out;
}"""


def static_text_keys(f):
    """Text-node keys of the page before any JavaScript runs (what the browser would show)."""
    soup = BeautifulSoup(open(f, encoding="utf-8").read(), "html.parser")
    out = Counter()
    if soup.body:
        for t in soup.body.find_all(string=True):
            if isinstance(t, Comment) or (t.parent and any(p.name in SKIP for p in [t.parent, *t.parents] if p.name)):
                continue
            k = mask(norm(str(t)).strip(), [])
            if LETTERS.search(TOKEN.sub("", k)):
                out[k] += 1
        for el in soup.find_all(True):
            for a in ATTRS:
                if el.get(a):
                    out[mask(norm(el[a]).strip(), [])] += 1
    return out


def collect_runtime(pages, report):
    """Open each page in a headless browser and keep the text that only JavaScript writes."""
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        report.append("Playwright missing: text written by JavaScript was not collected")
        return None
    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self, *a, **k):
            pass
    handler = partial(Quiet, directory=os.getcwd())
    srv = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    found = set()
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page()
            pg.route(re.compile(r"^https?://(?!127\.0\.0\.1)"), lambda r: r.abort())
            for path, f in pages:
                try:
                    pg.goto(f"http://127.0.0.1:{port}/{f}", wait_until="networkidle", timeout=20000)
                    pg.wait_for_timeout(300)
                    seen = Counter(pg.evaluate(COLLECT_JS))
                    static = static_text_keys(f)
                    found |= {k for k, n in seen.items() if n > static.get(k, 0)}  # written by JavaScript
                except Exception as e:
                    report.append(f"browser: {f}: {type(e).__name__}")
            b.close()
    finally:
        srv.shutdown()
    return found


# ---------- sitemap ----------

def add_to_sitemap(paths):
    try:
        xml = open("sitemap.xml", encoding="utf-8").read()
    except FileNotFoundError:
        return
    xml = re.sub(r"\s*<url>\s*<loc>" + re.escape(SITE) + r"/es/.*?</url>", "", xml, flags=re.S)
    today = time.strftime("%Y-%m-%d")
    extra = "".join(f"\n  <url>\n    <loc>{SITE}{es_path(p)}</loc>\n    <lastmod>{today}</lastmod>\n"
                    f"    <changefreq>daily</changefreq>\n    <priority>0.6</priority>\n  </url>" for p in paths)
    xml = xml.replace("</urlset>", extra.lstrip("\n") + "\n</urlset>" if extra else "</urlset>")
    with open("sitemap.xml", "w", encoding="utf-8") as fh:
        fh.write(xml)


# ---------- main ----------

def main(translator="grok", browser=True):
    report = []
    cache = load_json(CACHE_FILE, {})
    if translator == "grok":
        translator = grok_translate if API_KEY else None
    pages = sitemap_pages()
    if not pages:
        print("No pages in sitemap.xml")
        return
    all_paths = {p for p, _ in pages}

    # 1. what needs translating: page text, then text written by JavaScript
    keys = []
    for path, f in pages:
        build_page(path, f, cache, all_paths, keys)
    runtime = collect_runtime(pages, report) if browser else None
    ui_old = load_json(UI_FILE, {}).get("ui", {})
    ui_keys = sorted(runtime) if runtime is not None else sorted(ui_old)
    translate_missing(keys + ui_keys, cache, translator, report)

    # 2. which pages are translated well enough to publish
    built, done = {}, set()
    for path, f in pages:
        out, cov = build_page(path, f, cache, all_paths, [])
        if out and cov >= MIN_COVERAGE:
            built[path] = (f, out)
            done.add(path)
        elif out:
            report.append(f"{f}: only {cov:.0%} translated, not published in Spanish yet")
    # links only point to Spanish pages that exist; build again with the final list
    for path in list(built):
        f = built[path][0]
        out, _ = build_page(path, f, cache, done, [])
        os.makedirs(os.path.dirname(es_file(f)) or ".", exist_ok=True)
        with open(es_file(f), "w", encoding="utf-8") as fh:
            fh.write(out)
    # remove Spanish pages whose English page is gone or no longer good enough
    keep = {os.path.normpath(es_file(built[p][0])) for p in built}
    for root, _, files in os.walk(OUT):
        for name in files:
            fp = os.path.normpath(os.path.join(root, name))
            if fp.endswith(".html") and fp not in keep:
                os.remove(fp)

    # 3. English pages: link to the Spanish page and say it exists
    for path, f in pages:
        raw = open(f, encoding="utf-8").read()
        if path in done:
            new = put_hreflang(raw, path)
            new = re.sub(r'<a class="lang-switch"[^>]*>[^<]*</a>\s*', "", new)
            link = f'<a class="lang-switch" href="{es_path(path)}" hreflang="es" lang="es" title="Español">ES</a>'
            m = re.search(r'(<div class="nav-right">)(\s*)', new)
            if m:
                new = new[:m.end()] + link + m.group(2) + new[m.end():]
        else:
            new = drop_hreflang(raw)
            new = re.sub(r'<a class="lang-switch"[^>]*>[^<]*</a>\s*', "", new)
        if new != raw:
            with open(f, "w", encoding="utf-8") as fh:
                fh.write(new)

    # 4. dictionary for assets/i18n.js, and the sitemap
    ui = {k: cache[k] for k in ui_keys if k in cache and not re.search(r"</?t\d+", cache[k])}
    pages_list = sorted({p for p in done} | {p.removesuffix(".html") for p in done if p.endswith(".html")} | ({"/index.html"} if "/" in done else set()))
    save_json(UI_FILE, {"about": "Spanish texts for words that the page JavaScript writes (used by /assets/i18n.js), and the pages that exist in Spanish.",
                        "ui": ui, "pages": pages_list})
    add_to_sitemap(sorted(done))

    with open("translate-review.txt", "w", encoding="utf-8") as fh:
        fh.write(f"{time.strftime('%Y-%m-%d %H:%M')}  Spanish pages: {len(done)} of {len(pages)}, "
                 f"stored translations: {len(cache)}, JavaScript texts: {len(ui)}/{len(ui_keys)}\n")
        for line in report:
            fh.write("  - " + line + "\n")
    print(f"Spanish site: {len(done)}/{len(pages)} pages, {len(cache)} stored translations, "
          f"{len(ui)}/{len(ui_keys)} JavaScript texts" + (f", {len(report)} notes in translate-review.txt" if report else ""))


if __name__ == "__main__":
    main(browser="--no-browser" not in sys.argv)
