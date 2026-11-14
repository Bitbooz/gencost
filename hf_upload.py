"""
Uploads GenCost's daily prices to Hugging Face as an open dataset (runs in the daily GitHub workflow).

Dataset: https://huggingface.co/datasets/Bitbooz/ai-tool-prices
Each run writes, from data/*.json and data/clip-costs.json:
  prices.csv                 today's plans of every tool (one row per plan)
  clip-costs.csv             credits per clip for the models GenCost tracks
  daily/YYYY-MM-DD.csv       a copy of prices.csv for that day (the history builds up day by day)
  README.md                  the dataset card
ONE-TIME SETUP: a Hugging Face "Write" token as the GitHub secret HF_TOKEN. Without it this does nothing.

    python hf_upload.py           # upload (needs HF_TOKEN)
    python hf_upload.py --local   # only write the files to hf-dataset/ (no upload)
"""
import csv
import datetime as dt
import json
import os
import sys
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "hf-dataset")
REPO = "Bitbooz/ai-tool-prices"
SITE = "https://getgencost.com"
CATS = ["video", "image", "voice", "music"]

CARD = """---
license: cc-by-4.0
pretty_name: GenCost AI Tool Prices (daily)
language:
- en
tags:
- pricing
- ai-tools
- generative-ai
- text-to-video
- text-to-image
- text-to-speech
- music-generation
size_categories:
- n<1K
configs:
- config_name: prices
  data_files: prices.csv
- config_name: clip_costs
  data_files: clip-costs.csv
---

# AI tool prices, checked every morning

Daily subscription prices of {tools} AI video, avatar, image, voice and music tools, in US dollars,
from [GenCost]({site}). Every morning GenCost reads each tool's official pricing page, checks the
numbers, and only publishes a price change after it has been seen on two different days.

Last updated: **{today}**.

## Files

| File | What it is |
|---|---|
| `prices.csv` | Today's plans: one row per plan, with monthly and yearly price, credits and source page |
| `clip-costs.csv` | Credits one clip uses, per tool and model (for example Kling 4.0 at 720p) |
| `daily/YYYY-MM-DD.csv` | A copy of `prices.csv` for each day, so you can follow prices over time |

## Columns in `prices.csv`

`date`, `category` (video, image, voice, music), `tool`, `plan`, `monthly_price_usd` (billed monthly),
`yearly_price_usd` (per month, billed yearly; empty if the tool shows none), `credits_or_minutes`, `unit`,
`offer`, `source` (official pricing page), `gencost_page`.

## Notes

- Prices are before tax and can differ by country.
- Credits per clip depend on model, resolution, length and sound; see `clip-costs.csv` and the note on each tool's GenCost page.
- Free plans are listed with a price of 0.

## Use and citation

Free to use with credit: **GenCost ({site})**, CC BY 4.0. Human-readable comparisons, calculators and
an MCP server for AI assistants: {site}/ai.html. No affiliate links; tools do not pay to be listed.
"""


def today():
    return dt.datetime.now(ZoneInfo("Europe/Oslo")).date().isoformat()


def build():
    os.makedirs(os.path.join(OUT, "daily"), exist_ok=True)
    day = today()
    rows, tools = [], set()
    for cat in CATS:
        try:
            data = json.load(open(os.path.join(HERE, "data", f"{cat}.json"), encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for p in data.get("platforms", []):
            tools.add(p["name"])
            page = p.get("page") or ""
            for pl in p.get("plans", []):
                if pl.get("pending"):
                    continue
                rows.append({
                    "date": day, "category": cat, "tool": p["name"], "plan": pl.get("name", ""),
                    "monthly_price_usd": pl.get("monthly_price_usd", ""), "yearly_price_usd": pl.get("yearly_price_usd") or "",
                    "credits_or_minutes": pl.get("credits_or_minutes") or "", "unit": pl.get("unit") or "",
                    "offer": pl.get("offer") or "", "source": p.get("source") or "",
                    "gencost_page": (SITE + page) if page.startswith("/") else page,
                })
    cols = list(rows[0].keys())
    for path in ("prices.csv", f"daily/{day}.csv"):
        with open(os.path.join(OUT, path), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
    clips = json.load(open(os.path.join(HERE, "data", "clip-costs.json"), encoding="utf-8")).get("tools", {})
    with open(os.path.join(OUT, "clip-costs.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["tool", "model", "seconds", "credits", "official_source", "source", "checked"])
        for tool, c in sorted(clips.items()):
            for o in c.get("options") or [{"model": c.get("model"), "clips": c.get("clips", {})}]:
                for secs, cr in sorted((o.get("clips") or {}).items(), key=lambda x: float(x[0])):
                    w.writerow([tool, o.get("model", ""), secs, cr, "yes" if c.get("official") else "no",
                                c.get("source", ""), c.get("checked", "")])
    with open(os.path.join(OUT, "README.md"), "w", encoding="utf-8") as f:
        f.write(CARD.format(tools=len(tools), site=SITE, today=day))
    return day, len(rows), len(tools)


def main():
    local = "--local" in sys.argv
    token = os.environ.get("HF_TOKEN", "").strip()
    if not local and not token:
        print("No HF_TOKEN secret, so nothing was uploaded to Hugging Face.")
        return
    day, n, t = build()
    print(f"Dataset files written: {n} plans from {t} tools ({day})")
    if local:
        return
    try:
        from huggingface_hub import HfApi
        api = HfApi(token=token)
        api.create_repo(REPO, repo_type="dataset", exist_ok=True)
        api.upload_folder(folder_path=OUT, repo_id=REPO, repo_type="dataset",
                          commit_message=f"Prices {day}")
        print(f"Uploaded to https://huggingface.co/datasets/{REPO}")
    except Exception as e:  # never break the daily run
        print(f"Hugging Face upload failed: {e}")
        with open(os.path.join(HERE, "hf-review.txt"), "a", encoding="utf-8") as f:
            f.write(f"{day}  Hugging Face upload failed: {str(e)[:300]}\n")


if __name__ == "__main__":
    main()
