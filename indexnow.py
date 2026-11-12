"""
Tells Bing, Yandex, Naver, Seznam and Yep which GenCost pages changed (IndexNow).

Runs in the workflow right after the morning update has been pushed. It looks at the pages the
update changed (the last commit) and only reports pages whose content really changed: a page
whose only change is today's "checked" date and time is left out, so the search engines are not
asked to re-read 2,000 pages every morning. New pages are always reported.

The key file (KEY.txt at the site root) proves to the search engines that the site is ours.
Run by hand: python indexnow.py            (reports what the last commit changed)
             python indexnow.py --dry-run  (only prints the list)
"""
import json
import re
import subprocess
import sys
import time
import urllib.request

SITE = "https://getgencost.com"
HOST = "getgencost.com"
KEY = "c62418c80e416da2b27ee6d3b7e0596d"
ENDPOINT = "https://api.indexnow.org/indexnow"   # shared: passed on to every IndexNow search engine
DATES = re.compile(r"\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}(?::\d{2})?)?|\d{1,2}:\d{2}")


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout


def url_of(path):
    if path == "index.html":
        return SITE + "/"
    if path.endswith("/index.html"):
        return SITE + "/" + path[: -len("index.html")]
    return SITE + "/" + path


def in_sitemap():
    try:
        return set(re.findall(r"<loc>([^<]+)</loc>", open("sitemap.xml", encoding="utf-8").read()))
    except FileNotFoundError:
        return set()


def changed_pages(base="HEAD~1", head="HEAD"):
    out = []
    for line in git("diff", "--name-status", base, head).splitlines():
        parts = line.split("\t")
        status, path = parts[0], parts[-1]
        if not path.endswith(".html") or status.startswith("D"):
            continue
        if status.startswith("A"):
            out.append(path)
            continue
        old = git("show", f"{base}:{path}")
        new = git("show", f"{head}:{path}")
        if DATES.sub("", old) != DATES.sub("", new):
            out.append(path)
    return out


def submit(urls):
    for i in range(0, len(urls), 10000):
        body = json.dumps({"host": HOST, "key": KEY, "keyLocation": f"{SITE}/{KEY}.txt",
                           "urlList": urls[i:i + 10000]}).encode()
        req = urllib.request.Request(ENDPOINT, data=body, method="POST",
                                     headers={"Content-Type": "application/json; charset=utf-8"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                print(f"IndexNow: {len(urls[i:i + 10000])} pages reported, answer {r.status}")
        except Exception as e:   # never stop the workflow because of this
            print(f"IndexNow: could not report ({type(e).__name__}: {e})")


def main():
    listed = in_sitemap()
    urls = [u for u in (url_of(p) for p in changed_pages()) if u in listed]
    if not urls:
        print("IndexNow: no page content changed")
        return
    if "--dry-run" in sys.argv:
        print("\n".join(urls))
        print(f"{len(urls)} pages")
        return
    time.sleep(90)   # give Netlify time to publish the new version first
    submit(urls)


if __name__ == "__main__":
    main()
