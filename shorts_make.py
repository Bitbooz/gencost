"""
Makes a YouTube Short (1080x1920, about 20 seconds, no sound) from each new GenCost article,
and tells Frode where to download it (runs in the daily workflow, after the article is published).

Slides: the article's title, one slide per line of its "Quick answer" box, and an end card.
Rendered with Playwright (same browser the price reader uses) and joined with ffmpeg.

Where the video goes (only if HF_TOKEN is set):
  https://huggingface.co/datasets/Bitbooz/gencost-shorts  ->  YYYY-MM-DD.mp4 and YYYY-MM-DD.txt (title + description)
and a comment on the GitHub issue "Today's YouTube Short" with the download link and the text to paste,
so it arrives as an email / phone notification. Upload it from the YouTube app and add music there.

Automatic upload: shorts.xml (an RSS feed of the latest Shorts, each with the video as an enclosure) is updated in the
same Hugging Face repo. Zapier watches it ("RSS by Zapier: New item in feed" -> "YouTube: Upload video", using the
enclosure URL as the file, the item title as the title and the item description as the description). Zapier's
YouTube app is audited by Google, so the videos can be public; our own Google project would be locked to private.
  Feed: https://huggingface.co/datasets/Bitbooz/gencost-shorts/resolve/main/shorts.xml

    python shorts_make.py                  # today's article (needs HF_TOKEN to upload; GH_TOKEN for the issue)
    python shorts_make.py --local PAGE     # only make shorts-out/short.mp4 from pages/PAGE.html
"""
import datetime as dt
import html
import json
import os
import re
import shutil
import subprocess
import sys
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "shorts-out")
SITE = "https://getgencost.com"
REPO = "Bitbooz/gencost-shorts"
ISSUE_TITLE = "Today's YouTube Short"
LABEL = "short"
SLIDE_SECONDS, FADE = 3.2, 0.35

CSS = """
*{box-sizing:border-box;margin:0}
body{width:1080px;height:1920px;background:#07070c;font-family:Inter,"Noto Sans",Arial,sans-serif;color:#ececf3;overflow:hidden;position:relative}
.g1{position:absolute;width:1300px;height:1300px;border-radius:50%;background:radial-gradient(circle,rgba(0,212,255,.20),transparent 65%);top:-520px;left:-380px}
.g2{position:absolute;width:1300px;height:1300px;border-radius:50%;background:radial-gradient(circle,rgba(123,104,238,.26),transparent 65%);bottom:-560px;right:-420px}
.grid{position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px);background-size:60px 60px;mask-image:radial-gradient(ellipse at center,#000 30%,transparent 75%)}
.top{position:absolute;top:150px;left:0;right:0;text-align:center;font-weight:700;letter-spacing:.32em;font-size:34px;color:#00d4ff}
.c{position:absolute;left:90px;right:90px;top:50%;transform:translateY(-50%)}
h1{font-size:92px;line-height:1.06;font-weight:800;letter-spacing:-.02em}
h1 span{background:linear-gradient(90deg,#00d4ff,#7b68ee);-webkit-background-clip:text;color:transparent}
.label{font-size:44px;font-weight:700;color:#a3a3b9;margin-bottom:30px;text-transform:uppercase;letter-spacing:.06em}
.big{font-size:74px;line-height:1.16;font-weight:700}
.big strong{background:linear-gradient(90deg,#00d4ff,#7b68ee);-webkit-background-clip:text;color:transparent}
.money{color:#4ade80}
.sub{font-size:40px;color:#a3a3b9;margin-top:40px}
.pill{display:inline-block;font-size:38px;font-weight:600;padding:16px 30px;border-radius:999px;color:#4ade80;border:2px solid rgba(74,222,128,.4);background:rgba(74,222,128,.08);margin-top:50px}
.n{position:absolute;bottom:170px;left:0;right:0;text-align:center;font-size:36px;color:#7d7d95}
.url{font-size:88px;font-weight:800;margin-top:30px}
"""


def today():
    return dt.datetime.now(ZoneInfo("Europe/Oslo")).date()


def read_article(page):
    raw = open(os.path.join(HERE, page), encoding="utf-8").read()
    t = re.search(r"<h1>(.*?)</h1>", raw, re.S)
    title = html.unescape(re.sub(r"<[^>]+>", "", t.group(1))).strip() if t else page
    box = re.search(r'<div class="box">\s*<strong>Quick answer</strong>(.*?)</div>', raw, re.S)
    lines = []
    for part in re.split(r"<br\s*/?>", box.group(1) if box else ""):
        part = part.strip()
        text = html.unescape(re.sub(r"<[^>]+>", "", part)).strip()
        if not text or text.lower().startswith("last checked"):
            continue
        lines.append(part)
    d = re.search(r'<meta name="description" content="([^"]*)"', raw)
    return title, lines[:5], html.unescape(d.group(1)) if d else ""


def slide_html(body):
    return (f'<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>'
            f'<div class="grid"></div><div class="g1"></div><div class="g2"></div>{body}</body></html>')


def money(s):
    return re.sub(r"(\$\d[\d,]*(?:\.\d+)?)", r'<span class="money">\1</span>', s)


def durations(title, lines):
    """Seconds per slide: long enough to read (about 14 characters a second), never under 3."""
    plain = lambda h: re.sub(r"<[^>]+>", "", h)
    return [4.0] + [max(3.0, min(7.0, 1.2 + len(plain(l)) / 14)) for l in lines] + [3.5]


def slides(title, lines, day):
    words = title.split(" (")[0]
    head = words.rsplit(" ", 2)
    t = f'{" ".join(head[:-2])} <span>{" ".join(head[-2:])}</span>' if len(head) > 2 else f"<span>{words}</span>"
    out = [slide_html(f'<div class="top">GENCOST</div><div class="c"><h1>{t}</h1>'
                      f'<div class="pill">● Prices checked {day:%b} {day.day}, {day.year}</div></div>')]
    for i, part in enumerate(lines, 1):
        if ":" in re.sub(r"<[^>]+>", "", part):
            label, rest = part.split(":", 1)
            label = re.sub(r"<[^>]+>", "", label)
        else:
            label, rest = "", part
        out.append(slide_html(f'<div class="top">GENCOST</div><div class="c"><div class="label">{label}</div>'
                              f'<div class="big">{money(rest.strip())}</div></div><div class="n">{i} / {len(lines)}</div>'))
    out.append(slide_html('<div class="top">GENCOST</div><div class="c" style="text-align:center">'
                          '<div class="label">Every tool, every plan, updated daily</div><div class="url"><span class="money">getgencost.com</span></div>'
                          '<div class="sub">No affiliate links · no paid rankings</div></div>'))
    return out


def render(pages, folder):
    from playwright.sync_api import sync_playwright
    os.makedirs(folder, exist_ok=True)
    files = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1920})
        for i, h in enumerate(pages):
            pg.set_content(h, wait_until="load")
            pg.wait_for_timeout(250)
            f = os.path.join(folder, f"s{i:02d}.png")
            pg.screenshot(path=f)
            files.append(f)
        b.close()
    return files


def to_video(images, path, durations):
    args, n = ["ffmpeg", "-y", "-loglevel", "error"], len(images)
    for img in images:
        args += ["-i", img]  # one still image; zoompan below turns it into secs*30 frames
    parts = []
    for i in range(n):
        secs = durations[i]
        parts.append(f"[{i}:v]scale=1080:1920,format=yuv420p,zoompan=z='min(zoom+0.0006,1.04)':d={int(secs * 30)}:s=1080x1920:fps=30,"
                     f"fade=t=in:st=0:d={FADE},fade=t=out:st={secs - FADE}:d={FADE}[v{i}]")
    graph = ";".join(parts) + ";" + "".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[out]"
    args += ["-filter_complex", graph, "-map", "[out]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
             "-pix_fmt", "yuv420p", "-movflags", "+faststart", path]
    subprocess.run(args, check=True)


def caption(title, desc, page):
    url = f"{SITE}/{page}"
    short_title = title.split(" (")[0]
    if len(short_title) > 90:
        short_title = short_title[:87] + "…"
    text = (f"{desc}\n\nFull comparison, updated every morning: {url}\n\n"
            "GenCost checks the official pricing pages of 40+ AI tools every day. No affiliate links.\n\n"
            "#AI #AItools #AIvideo #Shorts")
    return f"{short_title} #shorts", text


def shorts_feed(api, newest):
    """RSS of the 15 newest Shorts in the Hugging Face repo, for Zapier's automatic YouTube upload."""
    from email.utils import format_datetime
    from xml.sax.saxutils import escape
    names = sorted({f[:-4] for f in api.list_repo_files(REPO, repo_type="dataset")
                    if re.fullmatch(r"\d{4}-\d{2}-\d{2}\.mp4", f)} | {newest}, reverse=True)[:15]
    items = []
    for n in names:
        try:
            path = os.path.join(OUT, f"{n}.txt")
            if not os.path.exists(path):
                from huggingface_hub import hf_hub_download
                path = hf_hub_download(REPO, f"{n}.txt", repo_type="dataset", token=api.token)
            txt = open(path, encoding="utf-8").read()
        except Exception:
            continue
        m = re.search(r"TITLE:\n(.*?)\n\nDESCRIPTION:\n(.*)", txt, re.S)
        if not m:
            continue
        url = f"https://huggingface.co/datasets/{REPO}/resolve/main/{n}.mp4"
        when = format_datetime(dt.datetime.fromisoformat(n + "T07:00:00+00:00"))
        items.append(f"<item><title>{escape(m.group(1).strip())}</title><link>{url}</link><guid isPermaLink=\"false\">gencost-short-{n}</guid>"
                     f"<pubDate>{when}</pubDate><description>{escape(m.group(2).strip())}</description>"
                     f"<enclosure url=\"{url}\" type=\"video/mp4\" length=\"{os.path.getsize(os.path.join(OUT, n + '.mp4')) if os.path.exists(os.path.join(OUT, n + '.mp4')) else 0}\"/></item>")
    rss = ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>GenCost YouTube Shorts</title>'
           f"<link>{SITE}</link><description>Daily GenCost Shorts, for automatic upload to YouTube.</description>"
           + "".join(items) + "</channel></rss>\n")
    open(os.path.join(OUT, "shorts.xml"), "w", encoding="utf-8").write(rss)
    api.upload_file(path_or_fileobj=os.path.join(OUT, "shorts.xml"), path_in_repo="shorts.xml", repo_id=REPO,
                    repo_type="dataset", commit_message=f"Shorts feed {newest}")


def gh(*args):
    r = subprocess.run(["gh", *args], capture_output=True, text=True)
    if r.returncode:
        print("gh failed:", r.stderr.strip()[:200])
    return r.stdout.strip()


def main():
    if "--local" in sys.argv:
        page = f"pages/{sys.argv[sys.argv.index('--local') + 1]}.html"
        title, lines, desc = read_article(page)
        work = os.path.join(OUT, "frames")
        imgs = render(slides(title, lines, today()), work)
        to_video(imgs, os.path.join(OUT, "short.mp4"), durations(title, lines))
        t, d = caption(title, desc, page)
        open(os.path.join(OUT, "short.txt"), "w", encoding="utf-8").write(f"TITLE:\n{t}\n\nDESCRIPTION:\n{d}\n")
        print("made", os.path.join(OUT, "short.mp4"))
        return
    token = os.environ.get("HF_TOKEN", "").strip()
    if not token:
        print("No HF_TOKEN, so no Short was made.")
        return
    day = today()
    try:
        items = json.load(open(os.path.join(HERE, "queue", "queue.json"), encoding="utf-8")).get("items", [])
    except (OSError, ValueError):
        items = []
    item = next((i for i in items if i.get("published") == day.isoformat()), None)
    if not item:
        print("No new article today, so no Short.")
        return
    title, lines, desc = read_article(item["page"])
    if not lines:
        print("The article has no Quick answer box, so no Short.")
        return
    shutil.rmtree(OUT, ignore_errors=True)
    imgs = render(slides(title, lines, day), os.path.join(OUT, "frames"))
    name = day.isoformat()
    video = os.path.join(OUT, f"{name}.mp4")
    to_video(imgs, video, durations(title, lines))
    t, d = caption(title, desc, item["page"])
    with open(os.path.join(OUT, f"{name}.txt"), "w", encoding="utf-8") as f:
        f.write(f"TITLE:\n{t}\n\nDESCRIPTION:\n{d}\n")
    try:
        from huggingface_hub import HfApi
        api = HfApi(token=token)
        api.create_repo(REPO, repo_type="dataset", exist_ok=True)
        for fn in (f"{name}.mp4", f"{name}.txt"):
            api.upload_file(path_or_fileobj=os.path.join(OUT, fn), path_in_repo=fn, repo_id=REPO, repo_type="dataset",
                            commit_message=f"Short {name}")
        try:
            shorts_feed(api, name)
        except Exception as e:  # the Short itself is uploaded; only the automatic-upload feed failed
            print(f"Shorts feed failed: {e}")
    except Exception as e:
        print(f"Short upload failed: {e}")
        with open(os.path.join(HERE, "hf-review.txt"), "a", encoding="utf-8") as f:
            f.write(f"{name}  Short upload failed: {str(e)[:300]}\n")
        return
    link = f"https://huggingface.co/datasets/{REPO}/resolve/main/{name}.mp4?download=true"
    body = (f"@Bitbooz today's YouTube Short is ready.\n\n**Download:** {link}\n\n"
            f"**Title** (paste in YouTube):\n```\n{t}\n```\n**Description:**\n```\n{d}\n```\n"
            "In the YouTube app: + → Short → upload the video → add music from YouTube's library → paste title and description → Upload.")
    gh("label", "create", LABEL, "--color", "0E8A16", "--description", "Daily YouTube Short", "--force")
    found = json.loads(gh("issue", "list", "--state", "open", "--label", LABEL, "--json", "number") or "[]")
    if found:
        gh("issue", "comment", str(found[0]["number"]), "--body", body)
    else:
        gh("issue", "create", "--title", ISSUE_TITLE, "--label", LABEL, "--body", body)
    print("Short ready:", link)


if __name__ == "__main__":
    main()
