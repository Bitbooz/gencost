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

MONEY = r"[~≈]?\s?\$\d[\d,]*(?:\.\d{1,2})?(?:\s?/\s?(?:mo|month))?"


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
        if getattr(p, "get", None) and ("live-box" in (p.get("class") or []) or "live-price" in (p.get("class") or [])):
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
        for tr in rows[1:]:
            cells = tr.find_all(["td", "th"])
            if not cells:
                continue
            label = cells[0].get_text(" ", strip=True)
            tool = matcher.tool_in(label) or context_tool
            if not tool:
                continue
            pc = price_col
            if pc is None:
                pc = next((i for i, c in enumerate(cells) if re.search(r"\$\d", c.get_text())), None)
            if pc is None or pc >= len(cells) or cells[pc].find(class_="live-price"):
                continue
            cell_text = cells[pc].get_text(" ", strip=True)
            plan = find_plan(tool, label) or find_plan(tool, cell_text)
            if not plan:
                continue
            bill = "yearly" if re.search(r"year|annual", cell_text, re.I) else "monthly"
            if live_value(tool, plan["name"], bill)[0] is None:
                continue
            for node in cells[pc].find_all(string=True):
                mm = re.search(MONEY, str(node))
                if mm:
                    mark_text(soup, node, tool, plan, mm, bill)
                    marked += 1
                    break
            # credits and cost-per-clip columns follow the price
            if credit_col is not None and credit_col < len(cells):
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
            new = f"~${price / credits * int(kind[3:]):.2f}"
        else:
            continue
        if c.get_text(strip=True) != new:
            c.string = new
            changed += 1
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
    marked = mark_tables(soup, art, matcher) + mark_lines(soup, art, matcher)

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


def main():
    tools, updated = load_tools()
    if not tools:
        print("No price data found (run regenerate_html.py first).")
        return
    matcher = Matcher(tools)
    lines = [f"Article prices updated {datetime.now().strftime('%Y-%m-%d %H:%M')} (price data from {updated})\n"]
    for path in ARTICLES:
        r = process(path, tools, matcher, updated)
        if r is None:
            continue
        marked, changed, names, report = r
        live = BeautifulSoup(open(path, encoding="utf-8").read(), PARSER).find_all(class_="live-price")
        lines.append(f"{path}: {len(live)} live prices ({marked} new, {changed} changed today) · box: {', '.join(names) or 'none'}")
        lines += report
        print(lines[-1 - len(report)])
    with open("article-review.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
