"""
AI Price Finder by GenCost: today's prices of AI video, image, voice and music tools, in US dollars.

Reads the Bitbooz/ai-tool-prices dataset live (updated every morning by GenCost from each tool's
official pricing page). Also runs as an MCP server, so AI assistants and agents can call the same tools.
Data: GenCost (https://getgencost.com), CC BY 4.0.
"""
import os
import time

import pandas as pd

BASE = os.environ.get("GENCOST_DATA", "https://huggingface.co/datasets/Bitbooz/ai-tool-prices/resolve/main")
SITE = "https://getgencost.com"
CREDIT = f"Prices from GenCost ({SITE}), read from each official pricing page every morning. CC BY 4.0."
_cache = {"t": 0, "prices": None, "clips": None}


def _load():
    """Both CSV files, cached for an hour so the answers are always from today's data."""
    if _cache["prices"] is None or time.time() - _cache["t"] > 3600:
        p = pd.read_csv(f"{BASE}/prices.csv")
        c = pd.read_csv(f"{BASE}/clip-costs.csv")
        for col in ("monthly_price_usd", "yearly_price_usd", "credits_or_minutes"):
            p[col] = pd.to_numeric(p[col], errors="coerce")
        c["seconds"] = pd.to_numeric(c["seconds"], errors="coerce")
        c["credits"] = pd.to_numeric(c["credits"], errors="coerce")
        _cache.update(t=time.time(), prices=p, clips=c)
    return _cache["prices"], _cache["clips"]


def _money(x):
    return "" if pd.isna(x) or x == "" else f"${x:,.2f}"


def _page(row):
    return row.get("gencost_page") or SITE


def cheapest_plans(category: str = "video", limit: int = 10) -> str:
    """List the cheapest paid plans for one category of AI tools, with today's prices in US dollars.

    Args:
        category: "video", "image", "voice" or "music".
        limit: how many plans to show (1-30).

    Returns:
        A Markdown table: tool, plan, price billed monthly, price per month billed yearly, credits or minutes, GenCost page.
    """
    p, _ = _load()
    category = (category or "video").strip().lower()
    d = p[(p["category"] == category) & (p["monthly_price_usd"] > 0)].copy()
    if d.empty:
        return f"No paid plans found for '{category}'. Use video, image, voice or music."
    d["best"] = d[["monthly_price_usd", "yearly_price_usd"]].min(axis=1, skipna=True)
    d = d.sort_values("best").head(max(1, min(int(limit or 10), 30)))
    lines = ["| Tool | Plan | Monthly | Yearly (per month) | Credits / minutes | More |", "|---|---|---|---|---|---|"]
    for _, r in d.iterrows():
        amount = "" if pd.isna(r["credits_or_minutes"]) else f"{r['credits_or_minutes']:,.0f} {r['unit'] if isinstance(r['unit'], str) else ''}"
        offer = f" ({r['offer']})" if isinstance(r["offer"], str) and r["offer"] else ""
        lines.append(f"| {r['tool']} | {r['plan']}{offer} | {_money(r['monthly_price_usd'])} | {_money(r['yearly_price_usd'])} "
                     f"| {amount} | [GenCost]({_page(r)}) |")
    day = p["date"].iloc[0] if len(p) else ""
    return f"**Cheapest {category} plans, {day}**\n\n" + "\n".join(lines) + f"\n\n{CREDIT}"


def tool_prices(tool: str) -> str:
    """Every plan of one AI tool (for example "Runway", "ElevenLabs", "Suno"), with today's prices in US dollars.

    Args:
        tool: the tool's name, or part of it.

    Returns:
        A Markdown table of the tool's plans, the official pricing page and the GenCost page.
    """
    p, _ = _load()
    q = (tool or "").strip().lower()
    d = p[p["tool"].str.lower().str.contains(q, regex=False)] if q else p.iloc[0:0]
    if d.empty:
        return f"'{tool}' is not tracked by GenCost. Tools: " + ", ".join(sorted(p["tool"].unique()))
    out = []
    for name, g in d.groupby("tool"):
        r0 = g.iloc[0]
        out.append(f"### {name} ({r0['category']})\n\n| Plan | Monthly | Yearly (per month) | Credits / minutes |\n|---|---|---|---|")
        for _, r in g.iterrows():
            amount = "" if pd.isna(r["credits_or_minutes"]) else f"{r['credits_or_minutes']:,.0f} {r['unit'] if isinstance(r['unit'], str) else ''}"
            out.append(f"| {r['plan']} | {_money(r['monthly_price_usd'])} | {_money(r['yearly_price_usd'])} | {amount} |")
        out.append(f"\nOfficial pricing: {r0['source']} · More on [GenCost]({_page(r0)})")
    return "\n".join(out) + f"\n\n{CREDIT}"


def clip_cost(model: str = "Kling 4.0", clips: int = 10, seconds: int = 5) -> str:
    """What a number of AI video clips of one model costs on each platform that sells it, cheapest first.

    Uses the credits one clip costs on each platform and that platform's cheapest monthly plan with enough credits.

    Args:
        model: the video model, for example "Kling 4.0", "Seedance 2.5", "Veo", "Ray3.2" or "Gen-4.5". Add a resolution like "Kling 4.0, 1080p" to narrow it.
        clips: how many clips you want to make in a month.
        seconds: length of each clip in seconds.

    Returns:
        A Markdown table: platform, model, credits needed, the plan that covers it and its monthly price.
    """
    p, c = _load()
    q = [w.strip().lower() for w in (model or "").split(",") if w.strip()]
    d = c[c["model"].str.lower().apply(lambda m: all(w in m for w in q))] if q else c.iloc[0:0]
    if d.empty:
        return "No clip costs for that model. Models: " + ", ".join(sorted(c["model"].unique()))
    clips, seconds = max(1, int(clips or 1)), max(1, int(seconds or 5))
    rows = []
    for (tool, m), g in d.groupby(["tool", "model"]):
        exact = g[g["seconds"] == seconds]
        if len(exact):
            per_clip, note = float(exact["credits"].iloc[0]), ""
        else:
            ref = g.iloc[(g["seconds"] - seconds).abs().argsort().iloc[0]]
            per_clip, note = float(ref["credits"]) / float(ref["seconds"]) * seconds, f" (worked out from {int(ref['seconds'])} s)"
        need = per_clip * clips
        plans = p[(p["tool"] == tool) & (p["unit"] == "credits") & (p["monthly_price_usd"] > 0) & (p["credits_or_minutes"] >= need)]
        if len(plans):
            best = plans.sort_values("monthly_price_usd").iloc[0]
            rows.append((float(best["monthly_price_usd"]), tool, m, need, note, f"{best['plan']}", _money(best["monthly_price_usd"]), _page(best)))
        else:
            top = p[(p["tool"] == tool) & (p["unit"] == "credits") & (p["monthly_price_usd"] > 0)]
            page = _page(top.iloc[0]) if len(top) else SITE
            rows.append((float("inf"), tool, m, need, note, "no single monthly plan has enough credits", "–", page))
    rows.sort(key=lambda r: r[0])
    lines = ["| Platform | Model | Credits needed | Cheapest plan that covers it | Monthly price | More |", "|---|---|---|---|---|---|"]
    for _, tool, m, need, note, plan, price, page in rows:
        lines.append(f"| {tool} | {m} | {need:,.0f}{note} | {plan} | {price} | [GenCost]({page}) |")
    return (f"**{clips} clips of {seconds} s, {model}**\n\n" + "\n".join(lines) +
            "\n\nCredits per clip depend on resolution and sound; check each platform's page. " + CREDIT)


if __name__ == "__main__":
    import gradio as gr

    with gr.Blocks(title="AI Price Finder by GenCost") as demo:
        gr.Markdown("# AI Price Finder\nToday's prices of 50 AI video, image, voice and music tools, in US dollars. "
                    f"Read from each official pricing page every morning by [GenCost]({SITE}). "
                    "No affiliate links, no paid placement.\n\n"
                    "AI assistants can use this Space as an **MCP server** (see *Use via API or MCP* at the bottom).")
        with gr.Tab("Cost of video clips"):
            with gr.Row():
                m = gr.Textbox(value="Kling 4.0", label="Video model (e.g. Kling 4.0, Seedance 2.5, Veo, Ray3.2)")
                n = gr.Number(value=10, precision=0, label="Clips a month")
                s = gr.Number(value=5, precision=0, label="Seconds per clip")
            b1, o1 = gr.Button("Find the cheapest", variant="primary"), gr.Markdown()
            b1.click(clip_cost, [m, n, s], o1)
        with gr.Tab("Cheapest plans"):
            with gr.Row():
                cat = gr.Dropdown(["video", "image", "voice", "music"], value="video", label="Category")
                lim = gr.Slider(1, 30, value=10, step=1, label="How many")
            b2, o2 = gr.Button("Show", variant="primary"), gr.Markdown()
            b2.click(cheapest_plans, [cat, lim], o2)
        with gr.Tab("One tool"):
            t = gr.Textbox(value="Runway", label="Tool")
            b3, o3 = gr.Button("Show prices", variant="primary"), gr.Markdown()
            b3.click(tool_prices, [t], o3)
        gr.Markdown(f"Data: [Bitbooz/ai-tool-prices](https://huggingface.co/datasets/Bitbooz/ai-tool-prices), "
                    f"updated every morning. Full comparisons and calculators: [getgencost.com]({SITE}). CC BY 4.0.")
    demo.launch(mcp_server=True)
