import requests
from bs4 import BeautifulSoup
import json

def get_heygen_pricing():
    url = "https://www.heygen.com/pricing"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Get clean text from the page
    text = soup.get_text(separator="\n", strip=True)
    
    # Save raw text (so you can see what was scraped)
    with open("heygen-raw.txt", "w", encoding="utf-8") as f:
        f.write(text)
    
    print("Raw pricing page saved to heygen-raw.txt")
    print("\n--- First 1500 characters ---")
    print(text[:1500])
    
    # Placeholder for AI extraction
    # Later we will send this text to DeepSeek/Grok
    print("\nNext step: Send the text to an AI to extract clean JSON.")

if __name__ == "__main__":
    get_heygen_pricing()
