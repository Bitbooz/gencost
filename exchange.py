"""
Writes data/exchange.json for "The AI price exchange" (/exchange.html): every tool GenCost tracks shown like a share.

- A tool's "price" = the average, over its paid plans, of the cheapest way to pay per month (monthly, or yearly per
  month when that is cheaper). Only confirmed prices: data/history.json adds a row after two readings on two days.
- Each tool also gets an index (100 = its price on the first day GenCost tracked it), so tools can be compared.
- The GenCost AI Price Index (GCX) = the average tool index x 10, so it starts at 1000. One index per category too.
Run after regenerate_html.py (auto_update.py does it). It only reads data files; it can't change a price.
"""
import json
import os
import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
CATS = ("video", "image", "voice", "music")
SYMBOLS = {"Higgsfield": "HIGGS", "PixVerse": "PIXV", "OpenArt": "OART", "InVideo": "INVD", "Dreamina": "DRMA", "Runway": "RNWY",
           "Kling AI": "KLNG", "Pika": "PIKA", "Luma": "LUMA", "Midjourney": "MJ", "ElevenLabs": "ELVN", "Suno": "SUNO",
           "Udio": "UDIO", "HeyGen": "HEYG", "Synthesia": "SYNT", "Captions": "CAPT", "CapCut": "CAPC", "Pictory": "PICT",
           "Leonardo": "LEON", "Ideogram": "IDEO", "Google Veo": "VEO", "Hailuo AI": "HAIL", "Vidu": "VIDU", "Viggle": "VIGL",
           "Krea": "KREA", "Wan": "WAN", "MiniMax Audio": "MMAX", "D-ID": "DID", "Murf": "MURF", "Adobe Firefly": "FFLY"}


def load(rel):
    with open(os.path.join(HERE, rel), encoding="utf-8-sig") as f:
        return json.load(f)


def best(monthly, yearly):
    vals = [v for v in (monthly, yearly) if v and v > 0]
    return min(vals) if vals else None


def symbol(name, used):
    s = SYMBOLS.get(name) or re.sub(r"[^A-Z0-9]", "", name.upper())[:4] or "TOOL"
    base, n = s, 2
    while s in used:
        s, n = f"{base[:3]}{n}", n + 1
    used.add(s)
    return s


def main():
    hist = load("data/history.json")
    start = date.fromisoformat(hist.get("since", "2026-11-08"))
    today = datetime.now(ZoneInfo("Europe/Oslo")).date()
    days = [(start + timedelta(d)).isoformat() for d in range((today - start).days + 1)]
    used, tools = set(), []
    for cat in CATS:
        for p in load(f"data/{cat}.json").get("platforms", []):
            name = p["name"]
            plans = [pl.get("name") for pl in p.get("plans") or [] if best(pl.get("monthly_price_usd"), pl.get("yearly_price_usd"))]
            rows_by_plan = {pl: (hist.get(cat, {}).get(name) or {}).get(pl) or [] for pl in plans}
            if not plans:
                continue
            series = []
            for d in days:
                vals = []
                for pl in plans:
                    rows = rows_by_plan[pl]
                    cur = None
                    for r in rows:              # the last confirmed price on or before this day
                        if r[0] <= d:
                            cur = best(r[1], r[2] if len(r) > 2 else None)
                    if cur is None and rows:    # a plan GenCost started tracking later: its first price
                        cur = best(rows[0][1], rows[0][2] if len(rows[0]) > 2 else None)
                    if cur is None:             # no history at all: today's price
                        pl_now = next(x for x in p["plans"] if x.get("name") == pl)
                        cur = best(pl_now.get("monthly_price_usd"), pl_now.get("yearly_price_usd"))
                    vals.append(cur)
                series.append(round(sum(vals) / len(vals), 2))
            first = series[0] or 1
            pct = lambda a, b: round((b - a) / a * 100, 1) if a else 0.0
            tools.append({
                "symbol": symbol(name, used), "name": name, "cat": cat, "page": p.get("page") or "/", "plans": len(plans),
                "price": series[-1], "series": series, "index": [round(v / first * 100, 2) for v in series],
                "d1": pct(series[-2], series[-1]) if len(series) > 1 else 0.0,
                "d7": pct(series[max(0, len(series) - 8)], series[-1]), "all": pct(series[0], series[-1]),
            })
    def idx(group):
        return [round(sum(t["index"][i] for t in group) / len(group) * 10, 1) for i in range(len(days))] if group else []
    out = {
        "about": "The AI price exchange. Written by exchange.py from confirmed prices (data/history.json). Not a stock: you can't buy it.",
        "date": today.isoformat(), "since": start.isoformat(), "days": days,
        "gcx": idx(tools), "categories": {c: idx([t for t in tools if t["cat"] == c]) for c in CATS},
        "tools": sorted(tools, key=lambda t: t["symbol"]),
    }
    with open(os.path.join(HERE, "data", "exchange.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    movers = sorted(tools, key=lambda t: t["all"])
    print(f"exchange: {len(tools)} tools, GCX {out['gcx'][0]} -> {out['gcx'][-1]}; biggest drop {movers[0]['symbol']} {movers[0]['all']}%")


if __name__ == "__main__":
    main()
