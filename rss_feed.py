"""
Writes feed.xml: an RSS feed of GenCost's new articles (runs in the daily workflow, after publish_queue.py).

Zapier (or any RSS reader) watches https://getgencost.com/feed.xml and shares each new article,
for example on the GenCost Facebook page. The feed lists the articles published from the queue,
newest first, with title, description and date read from each page.
"""
import datetime as dt
import html
import json
import os
import re
from email.utils import format_datetime
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = "https://getgencost.com"


def meta(page):
    raw = open(os.path.join(HERE, page), encoding="utf-8").read()
    title = re.search(r"<title>(.*?)</title>", raw, re.S)
    desc = re.search(r'<meta name="description" content="([^"]*)"', raw)
    title = html.unescape(title.group(1)).split(" | GenCost")[0].strip() if title else page
    return title, html.unescape(desc.group(1)) if desc else ""


def main():
    try:
        items = json.load(open(os.path.join(HERE, "queue", "queue.json"), encoding="utf-8")).get("items", [])
    except (OSError, ValueError):
        items = []
    done = [i for i in items if re.fullmatch(r"\d{4}-\d{2}-\d{2}", i.get("published") or "")
            and os.path.exists(os.path.join(HERE, i["page"]))]
    done.sort(key=lambda i: i["published"], reverse=True)
    entries = []
    for i in done[:30]:
        title, desc = meta(i["page"])
        when = dt.datetime.fromisoformat(i["published"] + "T07:00:00").replace(tzinfo=ZoneInfo("Europe/Oslo"))
        url = f"{SITE}/{i['page']}"
        entries.append(f"""  <item>
    <title>{html.escape(title)}</title>
    <link>{url}</link>
    <guid isPermaLink="true">{url}</guid>
    <pubDate>{format_datetime(when)}</pubDate>
    <description>{html.escape(desc)}</description>
  </item>""")
    now = format_datetime(dt.datetime.now(ZoneInfo("Europe/Oslo")))
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>GenCost: AI tool prices</title>
  <link>{SITE}/</link>
  <atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml"/>
  <description>New guides on what AI video, image, voice and music tools really cost, from GenCost's daily price checks.</description>
  <language>en</language>
  <lastBuildDate>{now}</lastBuildDate>
{chr(10).join(entries)}
</channel>
</rss>
"""
    with open(os.path.join(HERE, "feed.xml"), "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"feed.xml: {len(entries)} articles")


if __name__ == "__main__":
    main()
