"""
Keeps the prices in GenCost's articles up to date.

Runs every day after the price update (auto_update.py calls it), and can be
run by hand:   python update_articles.py

For every article (pages/*-vs-*.html, pages/cheapest-*.html, pages/best-*.html) it:
  1. puts a "Today's prices" box at the top, built from data/*.json
  2. finds prices in tables and in short lines like "Kling Standard ~$10/mo"
     and marks them (<span class="live-price" ...>) the first time it sees them
  3. writes today's price into every marked price, plus credits and
     cost-per-clip columns next to it
  4. updates "Last checked:" dates

Prices are written into the page itself, so visitors AND Google see them.
Longer sentences in the article text are left as written.
A summary of what it did goes to article-review.txt.
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

from bs4 import BeautifulSoup, NavigableString

try:
    import lxml  # noqa: F401
    PARSER = "lxml"
except ImportError:
    PARSER = "html.parser"

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

ARTICLES = sorted(set(glob.glob("pages/*-vs-*.html") + glob.glob("pages/cheapest-*.html") + glob.glob("pages/best-*.html")))

# Other ways articles write tool names
EXTRA_ALIASES = {
    "Kling AI": ["Kling"],
    "Pika": ["Pika Labs", "Pika Art"],
    "Luma": ["Luma Dream Machine", "Luma AI", "Dream Machine"],
    "Runway": ["Runway ML", "RunwayML"],
    "Google Veo": ["Veo"],
    "Hailuo AI": ["MiniMax Hailuo", "Hailuo"],
    "LTX Studio": ["LTX"],
    "ElevenLabs": ["Eleven Labs"],
    "PlayHT": ["Play.ht", "Play HT"],
    "Murf AI": ["Murf.ai", "Murf"],
    "WellSaid Labs": ["WellSaid"],
    "InVideo": ["InVideo AI", "invideo"],
}

# Tools that have shut down: articles that mention them get a short note with a link
GONE = {
    "Sora": ("was shut down by OpenAI in 2026", "/pages/best-sora-alternatives-2026.html"),
    "PlayHT": ("shut down on 31 December 2025", "/pages/best-playht-alternatives-2026.html"),
}

MONEY = r"[~≈]?\s?\$\d[\d,]*(?:\.\d{1,2})?(?:\s?/\s?(?:mo|month))?"
# In tables a price can be a range like "$10–12/mo"; it becomes one live price
MONEY_RANGE = r"[~≈]?\s?\$\d[\d,]*(?:\.\d{1,2})?(?:\s?[–-]\s?\$?\d[\d,]*(?:\.\d{1,2})?)?(?:\s?/\s?(?:mo|month))?"
FREE_NAMES = re.compile(r"^(free|basic|trial|starter|hobby)\b", re.I)


def load_tools():
    tools, updated = {}, ""
    for cat in ("video", "voice", "music"):
        try:
            with open(os.path.join("data", f"{cat}.json"), encoding="utf-8") as f:
                d = json.load(f)
        except FileNotFoundError:
            continue
        updated = max(updated, d.get("updated") or "")
        for pf in d.get("platforms", []):
            tools[pf["name"]] = dict(pf, category=cat)
    return tools, updated


def num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def money(v):
    return f"${int(v)}" if float(v).is_integer() else f"${v:.2f}"


def find_plan(tool, text):
    """The plan of this tool whose name appears in text (longest name wins)."""
    for p in sorted(tool["plans"], key=lambda p: -len(p["name"])):
        if re.search(r"(?<![\w])" + re.escape(p["name"]) + r"(?![\w])", text, re.I):
            return p
    return None


class Matcher:
    def __init__(self, tools):
        self.tools = tools
        pairs = []
        for name in tools:
            for a in [name] + EXTRA_ALIASES.get(name, []) + ([name[:-3]] if name.endswith(" AI") else []):
                pairs.append((a, name))
        pairs.sort(key=lambda x: -len(x[0]))
        self.pairs = pairs
        self.rx = re.compile(r"(?<![\w])(" + "|".join(re.escape(a) for a, _ in pairs) + r")(?![\w])", re.I)
        self.lookup = {a.lower(): n for a, n in pairs}

    def tool_in(self, text):
        m = self.rx.search(text or "")
        return self.tools[self.lookup[m.group(1).lower()]] if m else None

    def tools_in(self, text):
        seen = []
        for m in self.rx.finditer(text or ""):
            n = self.lookup[m.group(1).lower()]
            if n not in seen:
                seen.append(n)
        return seen


def live_value(tool, plan, bill):
    """The price to show for this plan, or None if it has no price."""
    p = next((x for x in tool["plans"] if x["name"] == plan), None)
    if not p:
        return None, None
    m, y = num(p.get("monthly_price_usd")) or 0, num(p.get("yearly_price_usd"))
    price = y if bill == "yearly" and y else m
    return (price if price > 0 else None), p


def cheapest_paid(tool, need_clips=False):
    """Cheapest plan with a price (and credits, if clip costs are needed)."""
    pc = (tool.get("clips") or {}).get("plan_credits") or {}
    only = (tool.get("clips") or {}).get("only_plans")
    ps = [p for p in tool["plans"] if (num(p.get("monthly_price_usd")) or 0) > 0
          and (not need_clips or (num(p.get("credits_or_minutes")) or num(pc.get(p["name"])) or 0) > 0)
          and (not need_clips or not only or p["name"] in only)]
    return min(ps, key=lambda p: p["monthly_price_usd"]) if ps else None


def free_plan(tool):
    return next((p for p in tool["plans"] if FREE_NAMES.match(p["name"]) and not (num(p.get("monthly_price_usd")) or 0)), None)


def clip_cost(tool, plan, secs, bill="monthly"):
    """(usd, credits, scaled) for one clip of `secs` seconds, from data/clip-costs.json. None if unknown."""
    info = tool.get("clips") or {}
    clips = {int(k): v for k, v in (info.get("clips") or {}).items()}
    price, p = live_value(tool, plan["name"], bill) if plan else (None, None)
    credits = num((p or {}).get("credits_or_minutes")) or num((info.get("plan_credits") or {}).get(plan["name"] if plan else ""))
    if not clips or not price or not credits:
        return None
    if info.get("only_plans") and plan["name"] not in info["only_plans"]:
        return None
    if secs in clips:
        cr, scaled = clips[secs], False
    else:
        near = min(clips, key=lambda k: abs(k - secs))
        cr, scaled = clips[near] / near * secs, True
    return price / credits * cr, cr, scaled


def fmt_price(price, suffix, approx):
    return ("~" if approx else "") + money(price) + suffix


def span_for(soup, tool, plan, bill, suffix, approx):
    s = soup.new_tag("span", attrs={"class": "live-price", "data-tool": tool["name"], "data-plan": plan,
                                   "data-bill": bill, "data-fmt": suffix, "data-approx": "1" if approx else "0",
                                   "title": "Updated automatically every day"})
    return s


def mark_text(soup, node, tool, plan, money_match, bill):
    """Replace the money text in a text node with a live-price span."""
    text = str(node)
    token = money_match.group(0)
    suffix = "/mo" if re.search(r"/\s?(mo|month)", token) else ""
    approx = token.strip().startswith(("~", "≈"))
    span = span_for(soup, tool, plan["name"], bill, suffix, approx)
    span.string = token.strip()
    before, after = text[:money_match.start()], text[money_match.end():]
    if before.endswith(" ") and token.startswith(" "):
        before = before[:-1]
    new = [NavigableString(before), span, NavigableString(after)]
    node.replace_with(*[n for n in new if not (isinstance(n, NavigableString) and str(n) == "")])
    return span


def in_live(node):
    for p in node.parents:
        if getattr(p, "get", None) and any(c in (p.get("class") or []) for c in ("live-box", "live-price", "est-basis")):
            return True
    return False


def mark_tables(soup, art, matcher):
    marked = 0
    for table in art.find_all("table"):
        if in_live(table):
            continue
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue
        head = [c.get_text(" ", strip=True).lower() for c in rows[0].find_all(["th", "td"])]
        price_col = next((i for i, h in enumerate(head) if "price" in h or "cheapest" in h or h in ("cost", "monthly")), None)
        credit_col = next((i for i, h in enumerate(head) if "credit" in h), None)
        est_cols = {i: int(h[:-1]) for i, h in enumerate(head) if re.fullmatch(r"\d+s", h)}
        context_tool = None  # the tool this table is about: nearest heading above that names one
        for heading in table.find_all_previous(["h2", "h3"], limit=4):
            context_tool = matcher.tool_in(heading.get_text(" ", strip=True))
            if context_tool:
                break
        cheapest_col = price_col is not None and "cheapest" in head[price_col]
        free_col = next((i for i, h in enumerate(head) if "free" in h and ("credit" in h or "limit" in h)), None)
        for tr in rows[1:]:
            cells = tr.find_all(["td", "th"])
            if not cells:
                continue
            label = cells[0].get_text(" ", strip=True)
            tool = matcher.tool_in(label) or context_tool
            if not tool:
                continue
            # free-tier credits ("One-time 125 credits") follow the tool's free plan
            if free_col is not None and free_col < len(cells) and not cells[free_col].find(attrs={"data-live": True}):
                fp = free_plan(tool)
                fc = num((fp or {}).get("credits_or_minutes"))
                if fp and fc and fc > 0:
                    for node in cells[free_col].find_all(string=True):
                        nm = re.search(r"(?<![\d~$.])(\d[\d,]*)(?=\s*credits?\b)", str(node), re.I)
                        if nm and "/day" not in str(node)[nm.end():nm.end() + 14].replace(" ", ""):
                            t = str(node)
                            sp = soup.new_tag("span", attrs={"data-live": "credits", "data-tool": tool["name"], "data-plan": fp["name"],
                                                             "title": "Updated automatically every day"})
                            sp.string = nm.group(1)
                            node.replace_with(*[x for x in (NavigableString(t[:nm.start()]), sp, NavigableString(t[nm.end():])) if str(x)])
                            marked += 1
                            break
            pc = price_col
            if pc is None:
                pc = next((i for i, c in enumerate(cells) if re.search(r"\$\d", c.get_text())), None)
            if pc is None or pc >= len(cells) or cells[pc].find(class_="live-price"):
                continue
            cell_text = cells[pc].get_text(" ", strip=True)
            others = " | ".join(c.get_text(" ", strip=True) for i, c in enumerate(cells[1:], 1) if i != pc)
            plan_cell = next((cells[i].get_text(" ", strip=True) for i, h in enumerate(head) if h == "plan" and i < len(cells)), "")
            plan = (find_plan(tool, label) or find_plan(tool, plan_cell) or find_plan(tool, cell_text)
                    or find_plan(tool, others))
            if not plan and cheapest_col:
                plan = cheapest_paid(tool)
            if not plan:
                continue
            row_text = label + " " + cell_text + " " + (cells[1].get_text(" ", strip=True) if len(cells) > 1 else "")
            bill = "yearly" if re.search(r"year|annual", row_text, re.I) else "monthly"
            if live_value(tool, plan["name"], bill)[0] is None:
                continue
            for node in cells[pc].find_all(string=True):
                mm = re.search(MONEY_RANGE, str(node))
                if mm:
                    mark_text(soup, node, tool, plan, mm, bill)
                    marked += 1
                    break
            # credits and cost-per-clip columns follow the price
            if credit_col is not None and credit_col < len(cells) and credit_col != free_col:
                c = cells[credit_col]
                if re.fullmatch(r"[\d,.]+[kK]?", c.get_text(strip=True)):
                    c["data-live"] = "credits"
                    c["data-tool"], c["data-plan"] = tool["name"], plan["name"]
            for i, secs in est_cols.items():
                if i < len(cells):
                    c = cells[i]
                    if re.fullmatch(r"[~≈]?\$[\d.]+", c.get_text(strip=True)):
                        c["data-live"] = f"est{secs}"
                        c["data-tool"], c["data-plan"], c["data-bill"] = tool["name"], plan["name"], bill
    return marked


def mark_lines(soup, art, matcher):
    """Short phrases like 'Kling Standard ~$10/mo' or 'Runway Pro: $28/mo' anywhere in the text."""
    marked = 0
    for node in list(art.find_all(string=True)):
        if in_live(node) or node.find_parent("table") or node.find_parent(["script", "style"]):
            continue
        text = str(node)
        if "$" not in text:
            continue
        for tm in matcher.rx.finditer(text):
            tool = matcher.tools[matcher.lookup[tm.group(1).lower()]]
            rest = text[tm.end():tm.end() + 60]
            for p in sorted(tool["plans"], key=lambda p: -len(p["name"])):
                pm = re.match(r"\s+" + re.escape(p["name"]) + r"(?:\s+plan)?\s*(?:is|at|costs?|for|:|—|–|-|≈|=)?\s*(" + MONEY + r")", rest, re.I)
                if pm:
                    bill = "yearly" if re.search(r"billed yearly|annual", text[tm.end():tm.end() + 120], re.I) else "monthly"
                    if live_value(tool, p["name"], bill)[0] is None:
                        break
                    start = tm.end() + pm.start(1)
                    mm = re.compile(MONEY).match(text, start)
                    # only monthly plan prices ("$10/mo", "$10/month", "$10 per month"), never totals like "≈ $1.50"
                    per_month = mm and (re.search(r"/\s?(mo|month)", mm.group(0)) or re.match(r"\s*(per|a|/)\s*month", text[mm.end():mm.end() + 12], re.I))
                    if mm and per_month:
                        mark_text(soup, node, tool, p, mm, bill)
                        marked += 1
                    break
            else:
                continue
            break  # node was replaced; any further phrases in it are picked up next run
    return marked


def refresh(art, tools, report):
    changed = 0
    for s in art.find_all(class_="live-price"):
        if "live-est" in (s.get("class") or []):
            continue  # example totals, see refresh_examples
        tool = tools.get(s.get("data-tool"))
        if not tool:
            report.append(f"    - {s.get('data-tool')} {s.get('data-plan')}: tool no longer in the price data, left as is")
            continue
        price, _ = live_value(tool, s.get("data-plan"), s.get("data-bill", "monthly"))
        if price is None:
            report.append(f"    - {tool['name']} {s.get('data-plan')}: plan not found in today's prices, left as is")
            continue
        new = fmt_price(price, s.get("data-fmt", ""), False)
        if s.get_text() != new:
            s.string = new
            changed += 1
    for c in art.find_all(attrs={"data-live": True}):
        tool = tools.get(c.get("data-tool"))
        if not tool:
            continue
        price, p = live_value(tool, c.get("data-plan"), c.get("data-bill", "monthly"))
        credits = num((p or {}).get("credits_or_minutes"))
        kind = c["data-live"]
        if kind == "credits" and credits:
            new = f"{credits:,}"
        elif kind.startswith("est") and price and credits:
            cc = clip_cost(tool, p, int(kind[3:]), c.get("data-bill", "monthly"))
            if not cc:
                continue
            new = f"~${cc[0]:.2f}"
        else:
            continue
        if c.get_text(strip=True) != new:
            c.string = new
            changed += 1
    changed += refresh_examples(art, tools, report)
    return changed


EXAMPLE = re.compile(r"(\d+)\s?[×x]\s?(\d+)-second")


def mark_examples(soup, art, matcher):
    """'20 × 10-second videos: Kling ≈ $3.00 | Hailuo ≈ $2.80' -> live totals from real clip costs."""
    marked = 0
    for node in list(art.find_all(string=EXAMPLE)):
        if in_live(node):
            continue
        m = EXAMPLE.search(str(node))
        block = node.find_parent(["div", "p", "li"]) or node.parent
        block["data-example-n"], block["data-example-secs"] = m.group(1), m.group(2)
        while True:  # one span per pass, until no more "Tool ≈ $X" is left in the block
            found = False
            for t in list(block.find_all(string=True)):
                if in_live(t):
                    continue
                text = str(t)
                em = EXAMPLE.search(text)
                for tm in matcher.rx.finditer(text, em.end() if em else 0):
                    tool = matcher.tools[matcher.lookup[tm.group(1).lower()]]
                    if not tool.get("clips"):
                        continue
                    pm = re.match(r"(\s+[\w+ ]{1,20}?)?\s*[≈~]\s*(\$\d[\d,]*(?:\.\d{1,2})?)", text[tm.end():])
                    if not pm:
                        continue
                    plan = find_plan(tool, pm.group(1) or "")
                    a, b = tm.end() + pm.start(2), tm.end() + pm.end(2)
                    sp = soup.new_tag("span", attrs={"class": "live-price live-est", "data-tool": tool["name"],
                                                     "data-plan": plan["name"] if plan else "", "title": "Updated automatically every day"})
                    sp.string = text[a:b]
                    t.replace_with(*[x for x in (NavigableString(text[:a]), sp, NavigableString(text[b:])) if str(x)])
                    marked += 1
                    found = True
                    break
                if found:
                    break
            if not found:
                break
    return marked


def refresh_examples(art, tools, report):
    changed = 0
    for block in art.find_all(attrs={"data-example-n": True}):
        n, secs = int(block["data-example-n"]), int(block["data-example-secs"])
        basis, totals = [], []
        for sp in block.find_all(class_="live-est"):
            tool = tools.get(sp.get("data-tool"))
            if not tool:
                continue
            plan = next((p for p in tool["plans"] if p["name"] == sp.get("data-plan")), None) if sp.get("data-plan") else cheapest_paid(tool, True)
            cc = clip_cost(tool, plan, secs) if plan else None
            if not cc:
                report.append(f"    - example {tool['name']}: no clip cost, left as is")
                continue
            usd, cr, scaled = cc
            new = f"${usd * n:,.2f}"
            if sp.get_text() != new:
                sp.string = new
                changed += 1
            totals.append((usd * n, tool["name"]))
            info = tool["clips"]
            have = num(plan.get("credits_or_minutes")) or num((info.get("plan_credits") or {}).get(plan["name"])) or 0
            fits = int(have // cr) if cr else 0
            extra = f"; the plan covers about {fits} such clips a month" if fits < n else ""
            basis.append(f"{tool['name']} {plan['name']} {money(live_value(tool, plan['name'], 'monthly')[0])}/mo, "
                         f"{info.get('model')}: {cr:g} credits per {secs}s{' (scaled)' if scaled else ''}{extra}")
        if not basis:
            continue
        if len(totals) > 1:
            totals.sort()
            report.append(f"    - example {n} x {secs}s: " + ", ".join(f"{t} ${v:,.2f}" for v, t in totals)
                          + f" -> cheapest today: {totals[0][1]} (check the verdict text agrees)")
        text = "Today's prices and each tool's real credits per clip: " + " · ".join(basis) + "."
        old = block.find(class_="est-basis")
        if old:
            if old.get_text() != text:
                old.string = text
        else:
            soup = BeautifulSoup("", PARSER)
            br, small = soup.new_tag("br"), soup.new_tag("small", attrs={"class": "est-basis"})
            small.string = text
            block.append(br)
            block.append(small)
    return changed


def live_box(soup, names, tools, updated):
    names = names[:6]
    rows = []
    for n in names:
        t = tools[n]
        paid = [p for p in t["plans"] if (num(p.get("monthly_price_usd")) or 0) > 0]
        if len(names) > 2:
            paid = sorted(paid, key=lambda p: p["monthly_price_usd"])[:1]
        for p in paid:
            y = num(p.get("yearly_price_usd"))
            credits = num(p.get("credits_or_minutes"))
            rows.append(
                f"<tr><td><a href=\"{html.escape(t.get('page', '#'))}\">{html.escape(n)}</a></td>"
                f"<td>{html.escape(p['name'])}</td>"
                f"<td class=\"num\">{money(p['monthly_price_usd'])}</td>"
                f"<td class=\"num\">{money(y) if y and y < p['monthly_price_usd'] else '–'}</td>"
                f"<td class=\"num\">{f'{credits:,}' + ' ' + html.escape(str(p.get('unit') or '')) if credits else '–'}</td></tr>")
    if not rows:
        return None
    ids = ",".join(re.sub(r"[^a-z0-9]+", "-", n.lower()).strip("-") for n in names)
    checked = [tools[n].get("checked") for n in names if tools[n].get("checked")]
    when = max(checked) if checked else updated
    what = "Every paid plan" if len(names) <= 2 else "Cheapest paid plan per tool"
    box = f"""<section class="live-box" aria-label="Today's prices">
<div class="live-box-head"><h2>Today's prices</h2><span class="live-note"><span class="dot"></span>Checked automatically · {html.escape(when)}</span></div>
<div class="table-scroll"><table>
<thead><tr><th>Tool</th><th>Plan</th><th>Paid monthly</th><th>Paid yearly</th><th>Includes</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table></div>
<p class="note">{what}, in US dollars, read from each tool's official pricing page. Prices in tables below update too; some figures in the running text were written when this article was published.
<a href="/compare.html?tools={ids}">Compare these tools side by side →</a></p>
</section>"""
    return BeautifulSoup(box, PARSER).find("section")


def process(path, tools, matcher, updated):
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    soup = BeautifulSoup(raw, PARSER)
    art = soup.find("article", class_="prose")
    if not art:
        return None
    report = []
    marked = mark_tables(soup, art, matcher) + mark_examples(soup, art, matcher) + mark_lines(soup, art, matcher)

    # Which tools is this article about? Title first, then the most-mentioned names.
    h1 = art.find("h1")
    title_tools = matcher.tools_in((h1.get_text(" ") if h1 else "") + " " + os.path.basename(path).replace("-", " "))
    counts = {}
    for n in matcher.tools_in(art.get_text(" ")):
        counts[n] = len(re.findall(r"(?<![\w])" + re.escape(n.split()[0]) + r"(?![\w])", art.get_text(" "), re.I))
    others = [n for n, c in sorted(counts.items(), key=lambda x: -x[1]) if c >= 3 and n not in title_tools]
    names = title_tools if len(title_tools) >= 2 else (title_tools + others)

    old_box = art.find("section", class_="live-box")
    box = live_box(soup, names, tools, updated) if names else None
    if old_box and box:
        old_box.replace_with(box)
    elif box:
        anchor = h1.find_next_sibling("p") if h1 else None
        (anchor or h1 or art.contents[0]).insert_after(box)

    for gone in GONE:  # table rows and whole sections about a shut-down tool
        rx = re.compile(r"^\s*" + re.escape(gone) + r"\b", re.I)
        for tr in art.find_all("tr"):
            first = tr.find(["td", "th"])
            if first and rx.match(first.get_text(" ", strip=True)) and not in_live(tr):
                tr.decompose()
                report.append(f"    - removed a {gone} table row")
        while True:
            h = next((x for x in art.find_all(["h2", "h3"]) if x.get_text(" ", strip=True).lower() == gone.lower()), None)
            if not h:
                break
            sec = h.find_parent("section")
            if sec and sec.find(["h2", "h3"]) is h and "live-box" not in (sec.get("class") or []):
                sec.decompose()
            else:
                for sib in list(h.find_next_siblings()):
                    if sib.name in ("h2", "h3"):
                        break
                    sib.decompose()
                h.decompose()
            report.append(f"    - removed the {gone} section")

    for gone, (when, link) in GONE.items():
        if (art.find(class_="gone-note", attrs={"data-gone": gone}) or os.path.basename(path) == os.path.basename(link)
                or art.find("a", href=link)):
            continue  # already noted, or the article already points readers to the alternatives
        if re.search(r"(?<![\w])" + re.escape(gone) + r"(?![\w])", art.get_text(" "), re.I):
            note = BeautifulSoup(f'<p class="gone-note" data-gone="{gone}"><strong>Update:</strong> {gone} {when}, so it is no longer in '
                                 f'our price lists. See the <a href="{link}">cheapest {gone} alternatives</a>.</p>', PARSER).find("p")
            anchor = art.find("section", class_="live-box") or art.find("h1")
            if anchor:
                anchor.insert_after(note)
            else:
                art.insert(0, note)
            report.append(f"    - added a note that {gone} has shut down")

    changed = refresh(art, tools, report)

    for node in art.find_all(string=re.compile(r"Last checked:\s*\d{4}-\d{2}-\d{2}")):
        node.replace_with(re.sub(r"Last checked:\s*\d{4}-\d{2}-\d{2}", f"Last checked: {updated[:10]}", str(node)))

    # Write back only the <article> part; the rest of the page stays byte-for-byte the same
    m = re.search(r"<article\b[^>]*>.*</article>", raw, re.S)
    if not m:
        return None
    new = raw[:m.start()] + str(art) + raw[m.end():]
    if new != raw:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new)
    return marked, changed, names, report


# Old sentences on other pages that are no longer true; replaced wherever they are found
NOTE_FIXES = {
    # Sora and PlayHT have shut down (2026-11-07): new article cards, no PlayHT in teaser texts
    "index.html": [
        ('<li class="reveal"><a class="art" href="/pages/playht-vs-elevenlabs-pricing-2026.html"><span class="cat voice">Voice</span><h3>PlayHT vs ElevenLabs Pricing 2026</h3><p>Voice tools comparison</p></a></li>',
         '<li class="reveal"><a class="art" href="/pages/best-playht-alternatives-2026.html"><span class="cat voice">Voice</span><h3>PlayHT Is Shut Down: Cheapest Alternatives</h3><p>Cartesia vs ElevenLabs vs Murf</p></a></li>'),
        ('<li class="reveal"><a class="art" href="/pages/cheapest-ai-video-tools-in-2026.html"><span class="cat video">Video</span><h3>Cheapest AI Video Tools in 2026</h3><p>Kling vs Runway vs Pika vs Luma</p></a></li>',
         '<li class="reveal"><a class="art" href="/pages/best-sora-alternatives-2026.html"><span class="cat video">Video</span><h3>Sora Is Shut Down: Cheapest Alternatives</h3><p>Veo vs Kling vs Runway, cost per clip</p></a></li>\n'
         '      <li class="reveal"><a class="art" href="/pages/cheapest-ai-video-tools-in-2026.html"><span class="cat video">Video</span><h3>Cheapest AI Video Tools in 2026</h3><p>Kling vs Runway vs Pika vs Luma</p></a></li>'),
        ('<li class="reveal"><a class="art" href="/pages/best-sora-alternatives-2026.html"><span class="cat video">Video</span><h3>Sora Is Shut Down: Cheapest Alternatives</h3><p>Veo vs Kling vs Runway, cost per clip</p></a></li>',
         '<li class="reveal"><a class="art" href="/pages/best-sora-alternatives-2026.html"><span class="cat video">Video</span><h3>Sora Is Shut Down: Cheapest Alternatives</h3><p>Veo vs Kling vs Runway, cost per clip</p></a></li>\n      <li class="reveal"><a class="art" href="/pages/cheapest-way-to-use-seedance-2-5-2026.html"><span class="cat video">Video</span><h3>Where Is Seedance 2.5 Cheapest?</h3><p>CapCut vs Higgsfield vs Luma vs Pika</p></a></li>'),
        ('<li class="reveal"><a class="art" href="/pages/cheapest-way-to-use-seedance-2-5-2026.html"><span class="cat video">Video</span><h3>Where Is Seedance 2.5 Cheapest?</h3><p>CapCut vs Higgsfield vs Luma vs Pika</p></a></li>',
         '<li class="reveal"><a class="art" href="/pages/cheapest-way-to-use-seedance-2-5-2026.html"><span class="cat video">Video</span><h3>Where Is Seedance 2.5 Cheapest?</h3><p>CapCut vs Higgsfield vs Luma vs Pika</p></a></li>\n      <li class="reveal"><a class="art" href="/pages/kling-vs-veo-pricing-2026.html"><span class="cat video">Video</span><h3>Kling vs Veo Pricing 2026</h3><p>Plans and real cost per video</p></a></li>\n      <li class="reveal"><a class="art" href="/pages/cheapest-ai-video-cost-per-second-2026.html"><span class="cat video">Video</span><h3>AI Video Cost per Second</h3><p>11 tools, real cost per clip</p></a></li>'),
        ('<li class="reveal"><a class="art" href="/pages/best-playht-alternatives-2026.html"><span class="cat voice">Voice</span><h3>PlayHT Is Shut Down: Cheapest Alternatives</h3><p>Cartesia vs ElevenLabs vs Murf</p></a></li>',
         '<li class="reveal"><a class="art" href="/pages/best-playht-alternatives-2026.html"><span class="cat voice">Voice</span><h3>PlayHT Is Shut Down: Cheapest Alternatives</h3><p>Cartesia vs ElevenLabs vs Murf</p></a></li>\n      <li class="reveal"><a class="art" href="/pages/best-elevenlabs-alternatives-2026.html"><span class="cat voice">Voice</span><h3>Cheaper ElevenLabs Alternatives</h3><p>Real cost per hour of speech</p></a></li>'),
        ("ElevenLabs, PlayHT, Cartesia and more", "ElevenLabs, Cartesia, Murf and more"),
        ("Clip estimates assume one credit per second of video, which differs between tools.",
         "Clip costs use each tool's own credits per clip for the model named (hover to see it). Tools without a known clip cost show none."),
    ],
    "voice.html": [
        ('<li class="reveal"><a class="art" href="/pages/best-playht-alternatives-2026.html"><span class="cat voice">Voice</span><h3>PlayHT Is Shut Down: Cheapest Alternatives</h3><p>Cartesia vs ElevenLabs vs Murf</p></a></li>',
         '<li class="reveal"><a class="art" href="/pages/best-playht-alternatives-2026.html"><span class="cat voice">Voice</span><h3>PlayHT Is Shut Down: Cheapest Alternatives</h3><p>Cartesia vs ElevenLabs vs Murf</p></a></li>\n      <li class="reveal"><a class="art" href="/pages/best-elevenlabs-alternatives-2026.html"><span class="cat voice">Voice</span><h3>Cheaper ElevenLabs Alternatives</h3><p>Real cost per hour of speech</p></a></li>'),
        ('<li class="reveal"><a class="art" href="/pages/playht-vs-elevenlabs-pricing-2026.html"><span class="cat voice">Voice</span><h3>PlayHT vs ElevenLabs Pricing 2026</h3><p>Voice tools comparison</p></a></li>',
         '<li class="reveal"><a class="art" href="/pages/best-playht-alternatives-2026.html"><span class="cat voice">Voice</span><h3>PlayHT Is Shut Down: Cheapest Alternatives</h3><p>Cartesia vs ElevenLabs vs Murf</p></a></li>'),
        ("ElevenLabs, PlayHT, Cartesia and more", "ElevenLabs, Cartesia, Murf and more"),
        ("Compare ElevenLabs, Cartesia, PlayHT, Murf,", "Compare ElevenLabs, Cartesia, Murf,"),
    ],
    "changelog.html": [
        ('<div class="entry">\n<div class="date">2026-10-29</div>',
         '<div class="entry">\n<div class="date">2026-11-07</div>\n<p>Removed Sora and PlayHT, which have both shut down, and added guides to their cheapest alternatives. '
         'Added the real cost per video clip, "Watch out" notes on hidden costs for 26 tools, and live prices inside articles.</p>\n</div>\n'
         '<div class="entry">\n<div class="date">2026-10-29</div>'),
    ],
    # Veo's real price is $19.99 (it was misread as $8.99), so Vidu is cheaper per clip than Veo
    "pages/best-sora-alternatives-2026.html": [
        ("Cheapest per clip: <strong>Google Veo</strong> (in Google Flow, part of Google AI Pro) and <strong>Vidu</strong>.",
         "Cheapest per clip: <strong>Vidu</strong> and <strong>Google Veo</strong> (in Google Flow, part of Google AI Pro)."),
        ("<h3>Google Veo: cheapest per clip, closest to Sora</h3>", "<h3>Google Veo: closest to Sora, and cheap per clip</h3>"),
        ("Per clip it is the cheapest option in this list, and the plan", "Per clip it is one of the cheapest options in this list, and the plan"),
    ],
    # PlayHT has shut down: old voice articles no longer recommend it
    "pages/cheapest-ai-voice-tools-in-2026.html": [
        ("<strong>Cartesia's free tier</strong> and <strong>PlayHT's free plan</strong> are the cheapest realistic options. For paid plans scaling beyond hobby use, <strong>ElevenLabs' Creator tier ($22/mo)</strong> remains the best value-per-minute for quality voice cloning, while <strong>PlayHT</strong> wins on raw character volume per dollar at higher tiers.",
         "<strong>Cartesia's free tier</strong> and <strong>ElevenLabs' free plan</strong> are the cheapest realistic options. For paid plans, <strong>Cartesia Pro ($5/mo)</strong> gives the most speech per dollar, while <strong>ElevenLabs' Creator tier ($22/mo)</strong> is the best pick for quality voice cloning."),
        ("Murf is the most expensive per-minute option of the four,", "Murf is the most expensive per-minute option here,"),
    ],
    "pages/cheapest-ai-voice-cloning-tools-2026.html": [
        (" PlayHT sits in the middle — competitive on paper but weaker voice cloning fidelity for the price.", ""),
        ("A cost breakdown of ElevenLabs, Cartesia, and PlayHT voice cloning pricing in 2026", "A cost breakdown of ElevenLabs and Cartesia voice cloning pricing in 2026"),
    ],
    # two Runway vs Kling articles were merged into one
    "index.html#merge": [
        ('      <li class="reveal"><a class="art" href="/pages/runway-vs-kling-pricing-comparison-2026.html"><span class="cat video">Video</span><h3>Runway vs Kling: Full Pricing Comparison</h3><p>Plans, credits and cost per clip in depth</p></a></li>\n', ""),
    ],
    # a right arrow that was saved with the wrong encoding when the articles were first written
    "pages/*.html": [("←’", "→")],
    # with real credits per clip Pika is cheaper than Luma at every clip length
    # with real credits per clip (Kling 3.0 vs Hailuo H3) Kling is cheaper on small plans, Hailuo on the biggest
    "pages/kling-vs-hailuo-pricing-2026.html": [("Very close in price. Hailuo can be slightly better value on higher plans.",
                                               "Kling is cheaper per clip on the smaller plans. On the biggest plans Hailuo works out cheaper per clip.")],
    "pages/pika-vs-luma-pricing-2026.html": [("Best for short clips: Luma<br/>", "Best for short clips: Pika<br/>"),
                                              ("Best for volume: Luma<br/>", "Best for volume: Pika<br/>")],
}


def fix_notes():
    """Small one-time text fixes. Safe to run every day: once fixed, nothing matches any more."""
    for pattern, pairs in NOTE_FIXES.items():
        for path in sorted(glob.glob(pattern.split("#")[0])):
            try:
                with open(path, encoding="utf-8") as f:
                    raw = f.read()
            except (FileNotFoundError, UnicodeDecodeError):
                continue
            new = raw
            for a, b in pairs:
                if a in new and (not b or b not in new):
                    new = new.replace(a, b)
            if new != raw:
                with open(path, "w", encoding="utf-8", newline="") as f:
                    f.write(new)
                print(f"{path}: text fixed")


# Articles that now redirect elsewhere: never suggested as related reading
MOVED_ARTICLES = {"pages/playht-vs-elevenlabs-pricing-2026.html", "pages/runway-vs-kling-pricing-comparison-2026.html"}


def article_info(path):
    raw = open(path, encoding="utf-8").read()
    soup = BeautifulSoup(raw, PARSER)
    art = soup.find("article", class_="prose")
    h1 = art.find("h1") if art else None
    t = soup.find("title")
    title = h1.get_text(" ", strip=True) if h1 else re.sub(r"\s*\|\s*GenCost$", "", t.get_text() if t else path)
    return title


def write_article(path, raw, art):
    m = re.search(r"<article\b[^>]*>.*</article>", raw, re.S)
    if not m:
        return False
    new = raw[:m.start()] + str(art) + raw[m.end():]
    if new != raw:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new)
        return True
    return False


def related_html(items, heading, extra=""):
    lis = "".join(f'<li><a href="/{html.escape(p)}">{html.escape(t)}</a></li>' for p, t in items)
    return BeautifulSoup(f'<section class="related" data-auto="related"><h2>{heading}</h2><ul>{lis}</ul>{extra}</section>', PARSER).find("section")


def put_related(art, section):
    old = art.find("section", attrs={"data-auto": "related"})
    if old:
        old.extract()
    art.append(section)  # always last, after the FAQ


def plan_line(tool, p):
    price = num(p.get("monthly_price_usd")) or 0
    bits = [f"{money(price)}/mo" if price else "Free"]
    cr = num(p.get("credits_or_minutes"))
    if cr:
        bits.append(f"{cr:,} {p.get('unit') or ''}".strip())
    lens = sorted(int(k) for k in ((tool.get("clips") or {}).get("clips") or {}))
    if lens and price:
        secs = 10 if 10 in lens else lens[-1]
        cc = clip_cost(tool, p, secs)
        if cc:
            bits.append(f"{secs}s clip ≈ ${cc[0]:.2f}")
    return f'<div class="plan"><strong>{html.escape(p["name"])}</strong>: {html.escape(" · ".join(bits))}</div>'


def load_tool_info():
    try:
        with open(os.path.join("data", "tool-info.json"), encoding="utf-8") as f:
            return json.load(f).get("tools", {})
    except Exception:
        return {}


def cents(v):
    return money(round(v, 2))


def faq_items(name, tool, info):
    """Questions and answers for a tool page, built from today's prices (so they are never out of date)."""
    qa = []
    paid = sorted([p for p in tool["plans"] if (num(p.get("monthly_price_usd")) or 0) > 0], key=lambda p: p["monthly_price_usd"])
    checked = (tool.get("checked") or "")[:10]
    if paid:
        lo, hi = paid[0], paid[-1]
        y = num(lo.get("yearly_price_usd"))
        a = f"The cheapest paid {name} plan is {lo['name']} at {cents(lo['monthly_price_usd'])} a month"
        a += f" ({cents(y)} a month if you pay yearly)." if y and y < lo["monthly_price_usd"] else "."
        if hi is not lo:
            a += f" The biggest plan we track is {hi['name']} at {cents(hi['monthly_price_usd'])} a month."
        a += f" Prices checked {checked}." if checked else " These prices are entered by hand, so confirm them on the official site."
        qa.append((f"How much does {name} cost?", a))
    free = free_plan(tool)
    if free or info.get("free"):
        a = ""
        if free:
            cr = num(free.get("credits_or_minutes"))
            a = f"Yes. The {free['name']} plan costs $0" + (f" and includes {cr:,} {free.get('unit') or ''}".rstrip() + "." if cr else ".")
        if info.get("free"):
            a = (a + " " if a else "") + info["free"]
        qa.append((f"Does {name} have a free plan?", a.strip()))
    clips = tool.get("clips") or {}
    lens = sorted(int(k) for k in (clips.get("clips") or {}))
    if lens:
        secs = 10 if 10 in lens else lens[-1]
        best = None
        for p in paid:
            cc = clip_cost(tool, p, secs)
            if cc:
                best = (p, cc)
                break
        if best:
            p, (usd, cr, scaled) = best
            qa.append((f"How much does one video clip cost on {name}?",
                       f"On the {p['name']} plan, one {secs}-second clip with {clips.get('model')} costs about ${usd:.2f}"
                       f" ({cr:g} credits). We work this out from {name}'s own credits per clip and today's plan price;"
                       " higher resolutions and premium models cost more."
                       f" If you usually need 3 tries for every clip you keep, plan for about ${usd * 3:.2f} per kept clip."))
    hidden = (tool.get("hidden") or {}).get("items") or []
    if hidden:
        qa.append((f"Are there hidden costs with {name}?", " ".join(h.rstrip(".") + "." for h in hidden)))
    return qa


INFO = load_tool_info()


def load_history():
    try:
        with open(os.path.join("data", "history.json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


HISTORY = load_history()


def tool_history(name, cat):
    return (HISTORY.get(cat) or {}).get(name) or {}


def price_changes(days=None):
    """All price changes as (date, category, tool, plan, old_monthly, new_monthly, old_yearly, new_yearly)."""
    out = []
    for cat in ("video", "voice", "music"):
        for tool, plans in (HISTORY.get(cat) or {}).items():
            for plan, rows in plans.items():
                for a, b in zip(rows, rows[1:]):
                    out.append((b[0], cat, tool, plan, a[1], b[1], a[2], b[2]))
    out.sort(reverse=True)
    if days:
        cutoff = (datetime.now(TZ) - __import__("datetime").timedelta(days=days)).strftime("%Y-%m-%d")
        out = [c for c in out if c[0] >= cutoff]
    return out


def change_text(c):
    day, cat, tool, plan, om, nm, oy, ny = c
    bits = []
    if om != nm:
        bits.append(f"{money(om) if om else 'free'} → {money(nm) if nm else 'free'} a month")
    if oy != ny and (oy or ny):
        bits.append(f"paid yearly {money(oy) if oy else '–'} → {money(ny) if ny else '–'}")
    return f"{tool} {plan}: " + ", ".join(bits) if bits else ""


def history_svg(plans):
    """A small step chart of each paid plan's monthly price over time."""
    series = [(n, r) for n, r in plans.items() if len(r) >= 2 and r[-1][1] > 0][:4]  # plans whose price changed
    days = sorted({row[0] for _, r in series for row in r})
    if len(days) < 2:
        return ""
    d0 = datetime.strptime(days[0], "%Y-%m-%d")
    last = datetime.now(TZ).replace(tzinfo=None) if TZ else datetime.now()
    span = max((last - d0).days, 1)
    top = (max(row[1] for _, r in series for row in r) or 1) * 1.15
    W, H, L, B = 640, 180, 56, 26
    x = lambda d: L + (W - L - 10) * ((datetime.strptime(d, "%Y-%m-%d") - d0).days / span)
    y = lambda v: 10 + (H - B - 10) * (1 - v / top)
    colors = ["#00d4ff", "#9d8ff5", "#3ddc97", "#ff8fb1"]
    paths, legend = [], []
    for i, (name, rows) in enumerate(series):
        pts, prev = [], None
        for d, m, _ in rows:
            if prev is not None:
                pts.append(f"{x(d):.1f},{y(prev):.1f}")
            pts.append(f"{x(d):.1f},{y(m):.1f}")
            prev = m
        pts.append(f"{W - 10:.1f},{y(prev):.1f}")
        paths.append(f'<polyline fill="none" stroke="{colors[i]}" stroke-width="2.5" points="{" ".join(pts)}"/>')
        legend.append(f'<span class="ph-key"><i style="background:{colors[i]}"></i>{html.escape(name)} {money(rows[-1][1])}</span>')
    axis = (f'<text x="{L - 8}" y="{y(top / 1.15) + 4:.1f}" text-anchor="end">{money(round(top / 1.15, 2))}</text>'
            f'<text x="{L - 8}" y="{y(0) + 4:.1f}" text-anchor="end">$0</text>'
            f'<text x="{L}" y="{H - 6}">{days[0]}</text><text x="{W - 10}" y="{H - 6}" text-anchor="end">today</text>'
            f'<line x1="{L}" y1="{y(0):.1f}" x2="{W - 10}" y2="{y(0):.1f}" class="ph-axis"/>')
    return (f'<svg class="ph-chart" viewBox="0 0 {W} {H}" role="img" aria-label="Monthly price of each plan over time">'
            f'{axis}{"".join(paths)}</svg><div class="ph-legend">{"".join(legend)}</div>')


def history_section(name, cat):
    plans = tool_history(name, cat)
    since = HISTORY.get("since", "")
    changes = [c for c in price_changes() if c[2] == name and c[1] == cat]
    chart = history_svg(plans)
    if changes:
        items = "".join(f"<li><b>{c[0]}</b> {html.escape(change_text(c)[len(name) + 1:])}</li>" for c in changes[:6] if change_text(c))
        body = f"{chart}<h3>Price changes</h3><ul>{items}</ul>"
    else:
        body = f"<p>No price changes since GenCost started recording {html.escape(name)}'s prices on {since}. Every change will show up here, with the date.</p>"
    return BeautifulSoup(f'<section class="card price-history" data-auto="history"><h2>{html.escape(name)} price history</h2>{body}</section>', PARSER).find("section")


def alert_form(name):
    return BeautifulSoup(f"""<section class="card alert-box" data-auto="alert">
<h2>Get an email when {html.escape(name)}'s price changes</h2>
<form name="price-alerts" method="POST" action="/alert-thanks.html" data-netlify="true" netlify-honeypot="company">
<input type="hidden" name="form-name" value="price-alerts"><input type="hidden" name="tool" value="{html.escape(name)}">
<p class="hp"><label>Company <input name="company" tabindex="-1" autocomplete="off"></label></p>
<div class="alert-row"><label class="sr" for="alert-email">Email</label><input id="alert-email" type="email" name="email" placeholder="you@example.com" required>
<button class="btn btn-primary" type="submit">Notify me</button></div>
</form>
<p class="note">Only used to tell you about price changes. Reply "stop" to any email and you are removed. See the <a href="/about.html#privacy">privacy note</a>.</p>
</section>""", PARSER).find("section")


def put_auto(art, section, key, before=None):
    old = art.find("section", attrs={"data-auto": key})
    if old:
        if str(old) != str(section):
            old.replace_with(section)
        return
    anchor = art.find("section", attrs={"data-auto": before}) if before else None
    if anchor:
        anchor.insert_before(section)
    else:
        art.append(section)


def update_changelog(report):
    """changelog.html gets an automatic list of the last 60 days of price changes; price-changes.txt the last 7."""
    week = [change_text(c) and f"{c[0]}  {change_text(c)}" for c in price_changes(7)]
    with open("price-changes.txt", "w", encoding="utf-8") as f:
        f.write(f"Price changes in the last 7 days (for the price alert email), made {datetime.now(TZ).strftime('%Y-%m-%d')}\n\n"
                + ("\n".join(w for w in week if w) or "No price changes this week.") + "\n")
    if not os.path.exists("changelog.html"):
        return
    raw = open("changelog.html", encoding="utf-8").read()
    soup = BeautifulSoup(raw, PARSER)
    art = soup.find("article", class_="prose")
    if not art:
        return
    recent = [c for c in price_changes(60) if change_text(c)]
    since = HISTORY.get("since", "")
    if recent:
        items = "".join(f"<li><b>{c[0]}</b> {html.escape(change_text(c))}</li>" for c in recent[:80])
        body = f"<ul>{items}</ul>"
    else:
        body = f"<p>No price changes yet since automatic recording started on {since}.</p>"
    sec = BeautifulSoup(f'<section class="price-log" data-auto="price-log"><h2>Automatic price changes</h2>'
                        f'<p class="note">Every change found by the daily check, newest first. Recorded since {since}.</p>{body}</section>', PARSER).find("section")
    old = art.find("section", attrs={"data-auto": "price-log"})
    if old:
        if str(old) != str(sec):
            old.replace_with(sec)
    else:
        h1 = art.find("h1")
        nxt = h1.find_next_sibling("p") if h1 else None
        (nxt or h1).insert_after(sec)
    if write_article("changelog.html", raw, art):
        report.append("changelog.html: price log updated")


def link_pages(tools, names_by_article, report):
    """'Related guides' on every article and tool page, and today's plans as the no-JavaScript fallback."""
    live = {p: n for p, n in names_by_article.items() if p not in MOVED_ARTICLES}
    titles = {p: article_info(p) for p in live}
    changed = 0
    for path, names in live.items():
        scored = []
        for other, onames in live.items():
            if other == path:
                continue
            overlap = len(set(names) & set(onames))
            if overlap:
                scored.append((-overlap, other))
        items = [(o, titles[o]) for _, o in sorted(scored)[:4]]
        if not items:
            continue
        raw = open(path, encoding="utf-8").read()
        soup = BeautifulSoup(raw, PARSER)
        art = soup.find("article", class_="prose")
        if not art:
            continue
        put_related(art, related_html(items, "Related guides"))
        changed += write_article(path, raw, art)
    for name, tool in tools.items():
        page = (tool.get("page") or "").lstrip("/")
        if not page.endswith(".html") or not os.path.exists(page):
            continue
        raw = open(page, encoding="utf-8").read()
        soup = BeautifulSoup(raw, PARSER)
        art = soup.find("article", class_="prose")
        if not art:
            continue
        info = INFO.get(name, {})
        h1 = art.find("h1")
        if h1 and h1.get_text(" ", strip=True) != f"{name} Pricing":
            h1.string = f"{name} Pricing"
        for p_old in art.find_all("p"):
            if p_old.get_text(" ", strip=True) == "See approx. cost per 10s in the plans below.":
                p_old.decompose()  # left over from the old design; voice and music have no 10s cost
        if info:
            for card in art.find_all("div", class_="card"):
                h2 = card.find("h2")
                if h2 and h2.get_text(strip=True) in ("Free tier", "Notes") and len(card.get_text(" ", strip=True)) < 200:
                    card.decompose()
            parts = [f"<h2>About {html.escape(name)}</h2><p>{html.escape(info.get('about', ''))}</p>"]
            if info.get("best_for"):
                parts.append(f"<h3>Who it's for</h3><p>{html.escape(info['best_for'])}</p>")
            if info.get("free"):
                parts.append(f"<h3>Free plan</h3><p>{html.escape(info['free'])}</p>")
            if info.get("credits"):
                parts.append(f"<h3>How the credits work</h3><p>{html.escape(info['credits'])}</p>")
            about = BeautifulSoup(f'<section class="card" data-auto="about">{"".join(parts)}</section>', PARSER).find("section")
            old_about = art.find("section", attrs={"data-auto": "about"})
            if old_about:
                if str(old_about) != str(about):
                    old_about.replace_with(about)
            else:
                plans_card = art.find(class_="live-plans")
                anchor = plans_card.find_parent("div", class_="card") if plans_card else None
                (anchor or art.find("h1")).insert_after(about)
        if not art.find(class_="live-plans"):
            for box in art.find_all("div", class_="box"):
                if box.find("p", class_="price"):
                    box.decompose()  # the old hand-written price box
            card = BeautifulSoup(f'<div class="card"><h2>Plans</h2><div class="live-plans" data-cat="{tool["category"]}" data-tool="{html.escape(name)}"></div></div>', PARSER).find("div")
            h1x = art.find("h1")
            sub = h1x.find_next_sibling("p") if h1x else None
            (sub or h1x).insert_after(card)
        qa = faq_items(name, tool, info)
        if qa:
            body = "".join(f"<h3>{html.escape(q)}</h3><p>{html.escape(a)}</p>" for q, a in qa)
            faq = BeautifulSoup(f'<section class="card faq" data-auto="faq"><h2>{html.escape(name)} pricing FAQ</h2>{body}</section>', PARSER).find("section")
            old_faq = art.find("section", attrs={"data-auto": "faq"})
            if old_faq:
                if str(old_faq) != str(faq):
                    old_faq.replace_with(faq)
            else:
                art.append(faq)
        box = art.find(class_="live-plans")
        if box and tool.get("plans"):
            fresh = BeautifulSoup("".join(plan_line(tool, p) for p in tool["plans"]), PARSER)
            body = fresh.body or fresh
            if box.decode_contents() != body.decode_contents():
                box.clear()
                for el in list(body.children):
                    box.append(el)
        put_auto(art, history_section(name, tool["category"]), "history", before="faq")
        put_auto(art, alert_form(name), "alert", before="faq")
        about = [p for p, n in live.items() if name in n]
        about.sort(key=lambda p: (len(live[p]), p))
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        extra = f'<p><a href="/compare.html?tools={slug}">Compare {html.escape(name)} with other tools →</a></p>'
        if about:
            put_related(art, related_html([(p, titles[p]) for p in about[:6]], f"Guides that compare {html.escape(name)}", extra))
        else:
            put_related(art, BeautifulSoup(f'<section class="related" data-auto="related">{extra}</section>', PARSER).find("section"))
        changed += write_article(page, raw, art)
    report.append(f"Related guides and tool-page fallbacks: {changed} pages updated")


def main():
    fix_notes()
    tools, updated = load_tools()
    if not tools:
        print("No price data found (run regenerate_html.py first).")
        return
    matcher = Matcher(tools)
    names_by_article = {}
    lines = [f"Article prices updated {datetime.now(TZ).strftime('%Y-%m-%d %H:%M')} (price data from {updated})\n"]
    for path in ARTICLES:
        r = process(path, tools, matcher, updated)
        if r is None:
            continue
        marked, changed, names, report = r
        names_by_article[path] = names
        live = BeautifulSoup(open(path, encoding="utf-8").read(), PARSER).find_all(class_="live-price")
        lines.append(f"{path}: {len(live)} live prices ({marked} new, {changed} changed today) · box: {', '.join(names) or 'none'}")
        lines += report
        print(lines[-1 - len(report)])
    link_pages(tools, names_by_article, lines)
    update_changelog(lines)
    with open("article-review.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
