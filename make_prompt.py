import json

def extract_with_prompt():
    # Read the raw scraped text
    with open("heygen-raw.txt", "r", encoding="utf-8") as f:
        raw_text = f.read()

    # The extraction prompt
    prompt = f"""
You are a precise data extractor. Extract the pricing plans from the following text and return ONLY valid JSON.

Text:
{raw_text[:4000]}

Return JSON in this exact format:
{{
  "platform": "HeyGen",
  "plans": [
    {{
      "name": "Free",
      "monthly_price_usd": 0,
      "credits_or_minutes": 3,
      "unit": "videos"
    }},
    {{
      "name": "Creator",
      "monthly_price_usd": 29,
      "credits_or_minutes": 600,
      "unit": "credits"
    }},
    {{
      "name": "Pro",
      "monthly_price_usd": 49,
      "credits_or_minutes": 1000,
      "unit": "credits"
    }}
  ]
}}

Only return the JSON. No extra text.
"""

    # Save the prompt so you can copy it into DeepSeek or Grok
    with open("heygen-prompt.txt", "w", encoding="utf-8") as f:
        f.write(prompt)

    print("Prompt saved to heygen-prompt.txt")
    print("Copy the content of heygen-prompt.txt and paste it into DeepSeek or Grok.")
    print("Then save the JSON reply as heygen-pricing.json")

if __name__ == "__main__":
    extract_with_prompt()
