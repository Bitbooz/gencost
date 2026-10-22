import requests
from bs4 import BeautifulSoup
import json
from openai import OpenAI

API_KEY = "YOUR_API_KEY_HERE"

client = OpenAI(api_key=API_KEY, base_url="https://api.x.ai/v1")

platforms = {
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

headers = {"User-Agent": "Mozilla/5.0"}

def extract_pricing(platform_name, raw_text):
    prompt = f"""Extract the main individual subscription plans AND any special offers from this text.

Rules:
- Ignore Enterprise / Contact sales plans
- Prefer monthly prices
- If there is a yearly discount, mention it in "offer"
- Look for phrases like "2 months free", "save X%", "limited time", "bonus credits"
- Never use null

Platform: {platform_name}

Text:
{raw_text[:6000]}

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

    try:
        response = client.chat.completions.create(
            model="grok-3",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"  AI error: {e}")
        return None

def process_platform(name, url):
    print(f"Processing {name}...")
    try:
        r = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text(separator="\n", strip=True)

        json_text = extract_pricing(name, text)
        if not json_text:
            return False

        json_text = json_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(json_text)

        filename = f"{name}-pricing.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"  Saved {filename}")
        return True
    except Exception as e:
        print(f"  Failed {name}: {e}")
        return False

if __name__ == "__main__":
    print("Starting update with offers...\n")
    success = 0
    for name, url in platforms.items():
        if process_platform(name, url):
            success += 1
    print(f"\nDone. {success}/{len(platforms)} platforms updated.")


# Force good data for platforms that often fail extraction
import json
with open("higgsfield-pricing.json", "w", encoding="utf-8") as f:
    json.dump({
        "platform": "Higgsfield",
        "plans": [
            {"name": "Starter", "monthly_price_usd": 19, "credits_or_minutes": 270, "unit": "credits"},
            {"name": "Plus", "monthly_price_usd": 59, "credits_or_minutes": 1200, "unit": "credits"},
            {"name": "Ultra", "monthly_price_usd": 129, "credits_or_minutes": 3000, "unit": "credits"}
        ]
    }, f, indent=2)

with open("kling-pricing.json", "w", encoding="utf-8") as f:
    json.dump({
        "platform": "Kling AI",
        "plans": [
            {"name": "Standard", "monthly_price_usd": 10, "credits_or_minutes": 660, "unit": "credits"},
            {"name": "Pro", "monthly_price_usd": 37, "credits_or_minutes": 3000, "unit": "credits"},
            {"name": "Premier", "monthly_price_usd": 92, "credits_or_minutes": 8000, "unit": "credits"}
        ]
    }, f, indent=2)
print("Forced good data for Higgsfield and Kling AI")

import subprocess
subprocess.run(["python", "regenerate_html.py"])
