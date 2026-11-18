"""
Deletes GenCost's own posts on X and Bluesky, e.g. a price news post that turned out wrong.

    python delete_posts.py --x 2122932139079647666 --bsky 3n2kurm2q7f2l
Run through GitHub Actions -> Delete posts (it has the secrets).
"""
import argparse
import os

import requests

import bluesky_post
import x_post

ap = argparse.ArgumentParser()
ap.add_argument("--x", default="", help="X post ids, comma separated")
ap.add_argument("--bsky", default="", help="Bluesky post ids (the last part of the post link), comma separated")
a = ap.parse_args()

keys = {"api_key": os.environ.get("X_API_KEY", "").strip(), "api_secret": os.environ.get("X_API_SECRET", "").strip(),
        "token": os.environ.get("X_ACCESS_TOKEN", "").strip(), "token_secret": os.environ.get("X_ACCESS_TOKEN_SECRET", "").strip()}
failed = 0
for pid in filter(None, (s.strip() for s in a.x.split(","))):
    url = f"https://api.x.com/2/tweets/{pid}"
    r = requests.delete(url, timeout=30, headers={"Authorization": x_post.oauth_header("DELETE", url, keys)})
    ok = r.status_code == 200 and r.json().get("data", {}).get("deleted")
    print(f"X {pid}: {'deleted' if ok else f'FAILED HTTP {r.status_code} {r.text[:200]}'}")
    failed += not ok

rkeys = [s.strip() for s in a.bsky.split(",") if s.strip()]
if rkeys:
    s = requests.post(f"{bluesky_post.API}/com.atproto.server.createSession", timeout=30,
                      json={"identifier": os.environ["BSKY_HANDLE"].strip().lstrip("@"),
                            "password": os.environ["BSKY_APP_PASSWORD"].strip()}).json()
    for rk in rkeys:
        r = requests.post(f"{bluesky_post.API}/com.atproto.repo.deleteRecord", timeout=30,
                          headers={"Authorization": f"Bearer {s['accessJwt']}"},
                          json={"repo": s["did"], "collection": "app.bsky.feed.post", "rkey": rk})
        print(f"Bluesky {rk}: {'deleted' if r.status_code == 200 else f'FAILED HTTP {r.status_code} {r.text[:200]}'}")
        failed += r.status_code != 200
raise SystemExit(1 if failed else 0)
