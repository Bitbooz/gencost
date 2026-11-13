"""
Publishes one queued article a day (runs at the start of the daily GitHub workflow).

queue/queue.json lists the waiting articles in order. Each run:
  - stops if an article was already published today (Norwegian date), or nothing is waiting
  - copies the next article from queue/ to its place in pages/
  - adds its card at the top of the article list on the homepage
  - writes today's date as 'published'
The rest of the daily job then fills in today's prices, the related guides, SEO tags,
the sitemap and the 18 translations, and IndexNow tells Bing about the new page.

To queue more articles: put the finished page in queue/ and add an item to the end of queue.json.
"""
import datetime as dt
import json
import os
import shutil
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(HERE, "queue", "queue.json")
INDEX = os.path.join(HERE, "index.html")
MARK = "<!-- ARTICLES:START (new article cards are added just above ARTICLES:END) -->"


def main():
    today = dt.datetime.now(ZoneInfo("Europe/Oslo")).date().isoformat()
    try:
        with open(QUEUE, encoding="utf-8") as f:
            q = json.load(f)
    except (OSError, ValueError):
        print("No article queue.")
        return
    items = q.get("items", [])
    if any(i.get("published") == today for i in items):
        print("An article was already published today.")
        return
    nxt = next((i for i in items if not i.get("published")), None)
    if not nxt:
        print("The article queue is empty.")
        return
    src, dst = os.path.join(HERE, nxt["file"]), os.path.join(HERE, nxt["page"])
    if not os.path.exists(src):
        print(f"Queued file missing: {nxt['file']} (skipped)")
        nxt["published"] = "missing"
    elif os.path.exists(dst):
        print(f"{nxt['page']} already exists, so it was not overwritten (skipped)")
        nxt["published"] = "exists"
    else:
        shutil.copyfile(src, dst)
        raw = open(INDEX, encoding="utf-8").read()
        href = 'href="/' + nxt["page"] + '"'
        if MARK in raw and href not in raw.split('id="articles"', 1)[-1]:
            raw = raw.replace(MARK, MARK + "\n      " + nxt["card"], 1)
            with open(INDEX, "w", encoding="utf-8", newline="") as f:
                f.write(raw)
        nxt["published"] = today
        print(f"Published {nxt['page']}")
    with open(QUEUE, "w", encoding="utf-8") as f:
        json.dump(q, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
