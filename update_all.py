import requests
from bs4 import BeautifulSoup

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
    "hailuo": "https://hailuoai.video/pricing",
    "ltx": "https://ltx.studio/pricing",
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def scrape_platform(name, url):
    try:
        print(f"Scraping {name}...")
        response = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        
        filename = f"{name}-raw.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"  Saved {filename}")
        return True
    except Exception as e:
        print(f"  Failed {name}: {e}")
        return False

if __name__ == "__main__":
    print("Starting full scrape...\n")
    success = 0
    for name, url in platforms.items():
        if scrape_platform(name, url):
            success += 1
    print(f"\nDone. {success}/{len(platforms)} platforms scraped.")
