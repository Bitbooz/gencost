"""
Publishes PER_DAY queued articles a day (runs at the start of the daily GitHub workflow).

queue/queue.json lists the waiting articles in order. Each run:
  - stops when PER_DAY articles were already published today (Norwegian date), or nothing is waiting
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
PER_DAY = 2  # articles a day (more pages for AI search to index; 2026-11-19)
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
    # Extra articles (e.g. news about a new GenCost feature): published on their own day, on top of PER_DAY.
    for x in items:
        if x.get("extra") and not x.get("published") and x.get("publish_on", "9999") <= today:
            src, dst = os.path.join(HERE, x["file"]), os.path.join(HERE, x["page"])
            if os.path.exists(src) and not os.path.exists(dst):
                shutil.copyfile(src, dst)
                raw = open(INDEX, encoding="utf-8").read()
                if MARK in raw and ('href="/' + x["page"] + '"') not in raw.split('id="articles"', 1)[-1]:
                    with open(INDEX, "w", encoding="utf-8", newline="") as f:
                        f.write(raw.replace(MARK, MARK + "\n      " + x["card"], 1))
                x["published"] = today
                print(f"Published extra article {x['page']}")
            else:
                x["published"] = "missing" if not os.path.exists(src) else "exists"
    done = sum(1 for i in items if i.get("published") == today and not i.get("extra"))
    if done >= PER_DAY:
        print(f"{done} article(s) already published today.")
    while done < PER_DAY:
        nxt = next((i for i in items if not i.get("published") and not i.get("extra")), None)
        if not nxt:
            print("The article queue is empty.")
            break
        src, dst = os.path.join(HERE, nxt["file"]), os.path.join(HERE, nxt["page"])
        if not os.path.exists(src):
            print(f"Queued file missing: {nxt['file']} (skipped)")
            nxt["published"] = "missing"
            continue
        if os.path.exists(dst):
            print(f"{nxt['page']} already exists, so it was not overwritten (skipped)")
            nxt["published"] = "exists"
            continue
        shutil.copyfile(src, dst)
        raw = open(INDEX, encoding="utf-8").read()
        href = 'href="/' + nxt["page"] + '"'
        if MARK in raw and href not in raw.split('id="articles"', 1)[-1]:
            raw = raw.replace(MARK, MARK + "\n      " + nxt["card"], 1)
            with open(INDEX, "w", encoding="utf-8", newline="") as f:
                f.write(raw)
        nxt["published"] = today
        done += 1
        print(f"Published {nxt['page']}")
    with open(QUEUE, "w", encoding="utf-8") as f:
        json.dump(q, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
