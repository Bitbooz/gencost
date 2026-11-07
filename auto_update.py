"""
GenCost price updater.

For every tool below it:
  1. downloads the official pricing page and saves the text as <name>-raw.txt
  2. asks Grok (xAI API) to turn that text into plans and prices
  3. CHECKS the result: every paid price must actually appear on the page.
     If a price can't be found (the AI misread or made it up), the old prices
     are kept and the problem is written to price-review.txt
  4. saves the prices in the right place:
        video / avatar / image tools  ->  <name>-pricing.json   (main folder)
        voice tools                   ->  voice/<name>-pricing.json
        music tools                   ->  music/<name>-pricing.json
  5. runs regenerate_html.py so the website data (data/*.json) is rebuilt

Needs the XAI_API_KEY environment variable (on GitHub: a repository secret).
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime

try:  # Norwegian time, also on GitHub's servers (which run on UTC)
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Europe/Oslo")
except Exception:
    TZ = None

import requests
from bs4 import BeautifulSoup

FOLDER = os.path.dirname(os.path.abspath(__file__))
os.chdir(FOLDER)

API_KEY = (os.getenv("XAI_API_KEY") or "").strip()
MODEL = "grok-3"

VIDEO = {
    "hailuo": "https://hailuoai.video/pricing",
    "veo": "https://deepmind.google/technologies/veo/",
    "sora": "https://openai.com/sora",
    "vidu": "https://www.vidu.studio/pricing",
    "krea": "https://www.krea.ai/pricing",
    "heygen": "https://www.heygen.com/pricing",
    "higgsfield": "https://higgsfield.ai/pricing",
    "runway": "https://runwayml.com/pricing",
    "kling": "https://klingai.com/pricing",
    "synthesia": "https://www.synthesia.io/pricing",
    "pika": "https://pika.art/pricing",
    "luma": "https://lumalabs.ai/pricing",
    "viggle": "https://viggle.ai/pricing",
    "invideo": "https://invideo.io/pricing",
    "capcut": "https://www.capcut.com/pricing",
    "ltx": "https://ltx.studio/pricing",
}
VOICE = {
    "elevenlabs": "https://elevenlabs.io/pricing",
    "murf": "https://murf.ai/pricing",
    "cartesia": "https://cartesia.ai/pricing",
    "speechify": "https://speechify.com/pricing",
    "descript": "https://www.descript.com/pricing",
}
MUSIC = {
    "suno": "https://suno.com/pricing",
    "udio": "https://www.udio.com/pricing",
    "soundraw": "https://soundraw.io/pricing",
    "aiva": "https://www.aiva.ai/pricing",
    "boomy": "https://boomy.com/pricing",
}

# Used only when a tool has NO saved prices at all and extraction fails.
FALLBACK = {
    "higgsfield": {
        "platform": "Higgsfield",
        "plans": [
            {"name": "Starter", "monthly_price_usd": 19, "credits_or_minutes": 270, "unit": "credits"},
            {"name": "Plus", "monthly_price_usd": 59, "credits_or_minutes": 1200, "unit": "credits"},
            {"name": "Ultra", "monthly_price_usd": 129, "credits_or_minutes": 3000, "unit": "credits"},
        ],
    },
    "kling": {
        "platform": "Kling AI",
        "plans": [
            {"name": "Standard", "monthly_price_usd": 10, "credits_or_minutes": 660, "unit": "credits"},
            {"name": "Pro", "monthly_price_usd": 37, "credits_or_minutes": 3000, "unit": "credits"},
            {"name": "Premier", "monthly_price_usd": 92, "credits_or_minutes": 8000, "unit": "credits"},
        ],
    },
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}
REVIEW_FILE = "price-review.txt"


def json_path(name):
    if name in VOICE:
        return os.path.join("voice", f"{name}-pricing.json")
    if name in MUSIC:
        return os.path.join("music", f"{name}-pricing.json")
    return f"{name}-pricing.json"


def load_existing(path):
    try:
        with open(path, encoding="utf-8-sig") as f:
            d = json.load(f)
        return d if d.get("plans") else None
    except Exception:
        return None


def extract_pricing(platform_name, raw_text):
    prompt = f"""Extract the main individual subscription plans AND any special offers from this text.

Rules:
- Ignore Enterprise / Contact sales plans
- Use the MONTHLY price in US dollars exactly as written on the page (e.g. "USD 19.99" -> 19.99)
- If only a yearly price is shown, divide it by 12 and say so in "offer"
- If there is a yearly discount, mention it in "offer"
- Look for phrases like "2 months free", "save X%", "limited time", "bonus credits"
- Never invent prices. Only use numbers that appear in the text.
- Never use null

Platform: {platform_name}

Text:
{raw_text[:8000]}

Return ONLY valid JSON:
{{
  "platform": "{platform_name}",
  "plans": [
    {{
      "name": "Creator",
      "monthly_price_usd": 29,
      "credits_or_minutes": 600,
      "unit": "credits",
      "offer": "2 months free on yearly"
    }}
  ]
}}

Only JSON. No extra text."""
    from openai import OpenAI
    client = OpenAI(api_key=API_KEY, base_url="https://api.x.ai/v1")
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return response.choices[0].message.content


def price_on_page(price, text):
    """True if this price (or, for yearly-derived prices, price x 12) is written in the page text."""
    def found(value):
        value = round(float(value), 2)
        if value == int(value):
            pattern = rf"(?<![\d.,]){int(value)}(?:[.,]00?)?(?![\d])"
        else:
            whole, cents = f"{value:.2f}".split(".")
            cents_alt = cents.rstrip("0") or "0"
            pattern = rf"(?<![\d]){whole}[.,](?:{cents}|{cents_alt})(?![\d])"
        return re.search(pattern, text) is not None
    return found(price) or found(price * 12)


def check(data, text):
    """Returns a list of problems. Empty list = looks right."""
    problems = []
    plans = data.get("plans")
    if not isinstance(plans, list) or not plans:
        return ["no plans found"]
    for p in plans:
        price = p.get("monthly_price_usd")
        if not isinstance(price, (int, float)):
            problems.append(f"{p.get('name')}: price is not a number ({price!r})")
            continue
        if price < 0 or price > 2000:
            problems.append(f"{p.get('name')}: unrealistic price ${price}")
        elif price > 0 and not price_on_page(price, text):
            problems.append(f"{p.get('name')}: ${price} does not appear on the pricing page")
    return problems


def review(name, url, problems):
    stamp = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
    with open(REVIEW_FILE, "a", encoding="utf-8") as f:  # one run's problems
        f.write(f"{stamp}  {name}  ({url})\n")
        for pr in problems:
            f.write(f"    - {pr}\n")
        f.write("    -> kept the previous prices\n\n")


def process_platform(name, url):
    print(f"Processing {name}...")
    path = json_path(name)
    try:
        r = requests.get(url, headers=HEADERS, timeout=25)
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        with open(f"{name}-raw.txt", "w", encoding="utf-8") as f:
            f.write(text)
        if len(text) < 200:
            review(name, url, [f"pricing page returned almost no text (HTTP {r.status_code})"])
            print("  Page had no usable text - kept old prices")
            return False

        reply = extract_pricing(name, text)
        reply = reply.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(reply)
    except Exception as e:
        review(name, url, [f"error: {e}"])
        print(f"  Failed {name}: {e} - kept old prices")
        return False

    problems = check(data, text)
    if problems:
        review(name, url, problems)
        print(f"  Not saved, prices could not be confirmed: {problems}")
        return False

    old = load_existing(path)
    data["platform"] = (old or {}).get("platform") or data.get("platform") or name
    data["source"] = url
    data["last_checked"] = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    changed = not old or old.get("plans") != data["plans"]
    print(f"  Saved {path}" + (" (prices changed)" if changed else " (no change)"))
    return True


if __name__ == "__main__":
    if not API_KEY:
        print("XAI_API_KEY is not set. Add it as an environment variable (or GitHub secret) and run again.")
        sys.exit(1)

    if os.path.exists(REVIEW_FILE):
        os.remove(REVIEW_FILE)  # the file always describes the latest run
    print("Starting price update...\n")
    everything = {**VIDEO, **VOICE, **MUSIC}
    success = sum(process_platform(n, u) for n, u in everything.items())
    print(f"\nDone. {success}/{len(everything)} tools confirmed and saved.")

    for name, data in FALLBACK.items():
        if not load_existing(json_path(name)):
            with open(json_path(name), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"Used fallback prices for {name} (no saved prices existed)")

    if os.path.exists(REVIEW_FILE):
        print(f"Some tools need a look: see {REVIEW_FILE}")
    else:
        with open(REVIEW_FILE, "w", encoding="utf-8") as f:
            f.write(f"{datetime.now(TZ).strftime('%Y-%m-%d %H:%M')}  All tools were checked and confirmed. Nothing to review.\n")

    subprocess.run([sys.executable, "regenerate_html.py"], check=False)
