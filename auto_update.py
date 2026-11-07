"""
GenCost price updater.

For every tool below it:
  1. downloads the official pricing page and saves the text as <name>-raw.txt
     (if that fails or the prices can't be confirmed, it opens the page in a
      real browser so prices loaded by JavaScript are visible too)
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

try:  # real browser for pages that need JavaScript (pip install playwright)
    from playwright.sync_api import sync_playwright
    BROWSER_OK = True
except Exception:
    BROWSER_OK = False

FOLDER = os.path.dirname(os.path.abspath(__file__))
os.chdir(FOLDER)

API_KEY = (os.getenv("XAI_API_KEY") or "").strip()
MODEL = "grok-3"

VIDEO = {
    # A list = several addresses to try, in order, until one gives confirmed prices
    "hailuo": ["https://hailuoai.video/pricing", "https://hailuoai.video/subscribe"],
    "veo": "https://one.google.com/about/google-ai-plans/",  # Veo is sold through Google AI plans
    "sora": "https://openai.com/sora",
    "vidu": ["https://www.vidu.com/pricing", "https://www.vidu.studio/pricing"],
    "krea": "https://www.krea.ai/pricing",
    "heygen": "https://www.heygen.com/pricing",
    "higgsfield": "https://higgsfield.ai/pricing",
    "runway": "https://runwayml.com/pricing",
    "kling": ["https://app.klingai.com/global/membership/membership-plan", "https://klingai.com/global/membership/membership-plan", "https://klingai.com/pricing"],
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

# Buttons or tabs the browser should click before reading, per tool
# (e.g. Murf opens on its "API" tab; the normal plans are under "Studio").
# Pages with a Monthly / Yearly switch where only one is shown at a time:
# the browser reads the page once per tab and gives the AI both.
TABS = {
    "kling": ["Monthly", "Yearly"],
}

CLICKS = {
    "murf": ["Studio"],
    "hailuo": ["From", "Upgrade", "Subscribe", "Pricing"],
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
- Prices in US dollars exactly as written on the page (e.g. "USD 19.99" -> 19.99)
- "monthly_price_usd" = the price per month when you pay MONTH BY MONTH, i.e. what you
  actually pay every month after any first-month deal. Never use a crossed-out "was" price.
  Example: "$6.99 / 1st mo  $10  Then $8.8/month" -> monthly_price_usd 8.8, offer "$6.99 first month"
- "yearly_price_usd" = the price PER MONTH when you pay for a whole year upfront
  (if the page shows "$144 billed yearly", use 12). Use 0 if there is no yearly option.
- Many pages show the yearly price first or by default. Read carefully which number is which.
- The text may contain sections like "[Monthly tab]" and "[Yearly tab]": take the monthly price
  from the Monthly section and the yearly price from the Yearly section.
- If the page only shows the yearly-billing price for a plan, put it in BOTH fields
  and write "monthly price not shown" in "offer"
- "offer": only special offers for THIS plan (e.g. "first month $9", "bonus credits"),
  max 80 characters. Do not repeat the yearly discount there. Use "" if none.
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
      "yearly_price_usd": 24,
      "credits_or_minutes": 600,
      "unit": "credits",
      "offer": ""
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


NUMBER_RE = re.compile(r"(?<![\d.,])(\d{1,3}(?:,\d{3})+|\d+)(?:[.,](\d{1,2}))?(?![\d])")


def price_on_page(price, text):
    """True if this price is written on the page, or is a yearly total on the page divided by 12
    (e.g. "$139/year" -> 11.58 a month, allowing for rounding to the cent)."""
    value = round(float(price), 2)
    for m in NUMBER_RE.finditer(text):
        n = float(m.group(1).replace(",", "") + ("." + m.group(2) if m.group(2) else ""))
        if abs(n - value) < 0.005:
            return True
        # yearly total / 12: only for numbers written as money ("$139", "USD 139", "139 USD")
        if n >= 24 and abs(n / 12 - value) <= 0.01:
            before, after = text[max(0, m.start() - 5):m.start()], text[m.end():m.end() + 5]
            if re.search(r"[$€£]|USD", before) or re.search(r"USD|\$", after):
                return True
    return False


def check(data, text):
    """Returns (problems, notes). Problems = do not save. Notes = saved, but something was left out."""
    problems, notes = [], []
    plans = data.get("plans")
    if not isinstance(plans, list) or not plans:
        return ["no plans found"], notes
    for p in plans:
        price = p.get("monthly_price_usd")
        if not isinstance(price, (int, float)):
            problems.append(f"{p.get('name')}: price is not a number ({price!r})")
            continue
        if price < 0 or price > 2000:
            problems.append(f"{p.get('name')}: unrealistic price ${price}")
        elif price > 0 and not price_on_page(price, text):
            problems.append(f"{p.get('name')}: ${price} does not appear on the pricing page")
        # Yearly price: optional. A wrong one is dropped instead of blocking the tool.
        yearly = p.get("yearly_price_usd")
        if yearly in (None, 0, "", "0"):
            p.pop("yearly_price_usd", None)
        elif not isinstance(yearly, (int, float)) or yearly < 0 or (price and yearly > price) or not price_on_page(yearly, text):
            notes.append(f"{p.get('name')}: yearly price {yearly!r} could not be confirmed, left out")
            p.pop("yearly_price_usd", None)
    return problems, notes


def review(name, url, problems, outcome="kept the previous prices"):
    stamp = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
    with open(REVIEW_FILE, "a", encoding="utf-8") as f:  # one run's problems
        f.write(f"{stamp}  {name}  ({url})\n")
        for pr in problems:
            f.write(f"    - {pr}\n")
        f.write(f"    -> {outcome}\n\n")


_pw = None
_browser = None


def click_first_visible(page, label):
    """Click the first visible button / tab / link with this text. True if something was clicked."""
    for loc in (page.get_by_role("button", name=label, exact=True),
                page.get_by_role("tab", name=label, exact=True),
                page.get_by_text(label, exact=True),
                page.get_by_role("button", name=re.compile(re.escape(label)))):
        try:
            for el in loc.all()[:8]:
                if el.is_visible():
                    el.click(timeout=3000)
                    page.wait_for_timeout(2000)
                    return True
        except Exception:
            pass
    return False


def browser_text(url, clicks=(), tabs=()):
    """Open the page in a real (headless) Chrome, let JavaScript load the prices, return the visible text."""
    global _pw, _browser
    if _browser is None:
        _pw = sync_playwright().start()
        _browser = _pw.chromium.launch()
    ctx = _browser.new_context(user_agent=HEADERS["User-Agent"], locale="en-US", viewport={"width": 1366, "height": 900})
    page = ctx.new_page()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        # Close cookie / consent popups that cover the page
        for label in ("Accept all", "Accept All", "Accept", "I agree", "Agree", "Allow all", "Got it", "OK"):
            try:
                btn = page.get_by_role("button", name=label, exact=True)
                if btn.count():
                    btn.first.click(timeout=2000)
                    page.wait_for_timeout(800)
                    break
            except Exception:
                pass
        for label in clicks:  # open the right tab / price popup
            if click_first_visible(page, label):
                break
        for _ in range(4):  # scroll so lazy-loaded price tables appear
            page.mouse.wheel(0, 2500)
            page.wait_for_timeout(700)
        page.wait_for_timeout(1500)
        if not tabs:
            return page.inner_text("body")
        parts = []
        for label in tabs:
            if click_first_visible(page, label):
                parts.append(f"[{label} tab]\n" + page.inner_text("body"))
        return "\n\n".join(parts) if parts else page.inner_text("body")
    finally:
        ctx.close()


def close_browser():
    global _pw, _browser
    try:
        if _browser:
            _browser.close()
        if _pw:
            _pw.stop()
    except Exception:
        pass


def extract_and_check(name, text):
    """Returns (data, problems, notes)."""
    if len(text) < 200:
        return None, ["page had almost no text"], []
    try:
        reply = extract_pricing(name, text)
        reply = reply.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(reply)
    except Exception as e:
        return None, [f"error: {e}"], []
    problems, notes = check(data, text)
    return data, problems, notes


def read_one(name, url):
    """Try one address: quick download, then a real browser. Returns (data, problems, notes, text, method)."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=25)
        text = BeautifulSoup(r.text, "html.parser").get_text(separator="\n", strip=True)
        status = r.status_code
    except Exception as e:
        text, status = "", f"error: {str(e)[:120]}"
    if len(text) < 200:
        data, problems, notes = None, [f"pricing page returned almost no text (HTTP {status})"], []
    elif name in TABS and BROWSER_OK:
        data, problems, notes = None, ["needs the browser to open both tabs"], []
    else:
        data, problems, notes = extract_and_check(name, text)
    method = "download"

    if problems and BROWSER_OK:
        try:
            btext = browser_text(url, CLICKS.get(name, ()), TABS.get(name, ()))
        except Exception as e:
            btext = ""
            problems.append(f"browser could not open the page: {str(e).splitlines()[0][:150]}")
        if len(btext) >= 200:
            bdata, bproblems, bnotes = extract_and_check(name, btext)
            if not bproblems:
                return bdata, [], bnotes, btext, "browser"
            problems = [f"download: {p}" for p in problems] + [f"browser: {p}" for p in bproblems]
        elif btext:
            problems.append("browser also got almost no text")
        if len(btext) > len(text):
            text = btext  # keep what the browser saw, so <name>-raw.txt shows the problem
    return data, problems, notes, text, method


def process_platform(name, urls):
    print(f"Processing {name}...")
    path = json_path(name)
    urls = [urls] if isinstance(urls, str) else list(urls)
    all_problems, best_text = [], ""
    data = None
    for url in urls:
        data, problems, notes, text, method = read_one(name, url)
        if len(text) > len(best_text):
            best_text = text
        if not problems:
            best_text = text
            break
        all_problems += [f"{p}" if len(urls) == 1 else f"[{url}] {p}" for p in problems]
    else:
        problems = all_problems
    url = urls[0] if problems else url
    text = best_text

    with open(f"{name}-raw.txt", "w", encoding="utf-8") as f:
        f.write(text)

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
    if notes:
        review(name, url, notes, outcome="saved the monthly prices")
    changed = not old or old.get("plans") != data["plans"]
    print(f"  Saved {path} via {method}" + (" (prices changed)" if changed else " (no change)"))
    return True


if __name__ == "__main__":
    if not API_KEY:
        print("XAI_API_KEY is not set. Add it as an environment variable (or GitHub secret) and run again.")
        sys.exit(1)

    if os.path.exists(REVIEW_FILE):
        os.remove(REVIEW_FILE)  # the file always describes the latest run
    print("Starting price update...\n")
    everything = {**VIDEO, **VOICE, **MUSIC}
    if not BROWSER_OK:
        print("(Playwright not installed: pages that need JavaScript can't be read. pip install playwright)")
    try:
        success = sum(process_platform(n, u) for n, u in everything.items())
    finally:
        close_browser()
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
