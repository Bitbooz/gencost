"""
Price alerts: emails the people who asked (the "Get an email when X's price changes" form on each tool page) when
that tool's price changes.

Uses the same confirmed changes as price_news.py (seen on two different days, doubtful ones held back), so an alert
is never sent for a misreading.

    python price_alerts.py            send today's alerts
    python price_alerts.py --preview  show what would be sent, send nothing
    python price_alerts.py --test     send one sample alert to the ALERT_REPLY_TO inbox (the owner's own)

Needs (GitHub secrets): NETLIFY_TOKEN (reads the form sign-ups), RESEND_API_KEY (sends the email),
ALERT_REPLY_TO (the inbox that gets "stop" replies), XAI_API_KEY (optional: the email in the reader's language).
No email address is ever written to the repository: data/alert-state.json only keeps a hash of (sign-up, change)
so nobody gets the same alert twice. Unsubscribe: the reader replies "stop" and the sign-up is deleted in
Netlify -> Forms -> price-alerts.
"""
import hashlib
import json
import os
import re
import sys

import requests

import price_news

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "data", "alert-state.json")
SITE = "https://getgencost.com"
FROM = os.environ.get("ALERT_FROM", "GenCost price alerts <alerts@getgencost.com>")
NETLIFY = "https://api.netlify.com/api/v1"
MAX_PER_RUN = 90  # Resend's free plan sends at most 100 emails a day
LANG_NAMES = {"es": "Spanish", "pt": "Portuguese", "de": "German", "fr": "French", "ar": "Arabic", "he": "Hebrew",
              "it": "Italian", "ja": "Japanese", "ru": "Russian", "zh-tw": "Traditional Chinese", "ko": "Korean",
              "id": "Indonesian", "tr": "Turkish", "hi": "Hindi", "vi": "Vietnamese", "pl": "Polish", "uk": "Ukrainian",
              "zh": "Simplified Chinese", "no": "Norwegian (Bokmål)", "sv": "Swedish",
              "da": "Danish", "fi": "Finnish", "nl": "Dutch", "th": "Thai", "tl": "Filipino", "bn": "Bengali"}


def log(msg):
    print(msg)
    price_news.log("[alerts] " + msg)


def signups(token):
    """Every price-alert sign-up: id, address, tool and the language of the page it came from."""
    h = {"Authorization": f"Bearer {token}", "User-Agent": "GenCost price alerts"}
    sites = requests.get(f"{NETLIFY}/sites?filter=all&per_page=100", headers=h, timeout=30).json()
    site = next((s for s in sites if "getgencost.com" in (s.get("custom_domain") or "") + (s.get("url") or "")), None)
    if not site:
        raise RuntimeError("the getgencost.com site was not found with this Netlify token")
    forms = requests.get(f"{NETLIFY}/sites/{site['id']}/forms", headers=h, timeout=30).json()
    form = next((f for f in forms if f.get("name") == "price-alerts"), None)
    if not form:
        return []
    out, page = [], 1
    while True:
        rows = requests.get(f"{NETLIFY}/forms/{form['id']}/submissions?per_page=100&page={page}", headers=h, timeout=30).json()
        for s in rows:
            d = s.get("data") or {}
            addr, tool = (d.get("email") or s.get("email") or "").strip(), (d.get("tool") or "").strip()
            if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", addr) or not tool or d.get("company"):
                continue
            m = re.match(r"https?://[^/]+/([a-z]{2}(?:-tw)?)/", d.get("referrer") or "")
            lang = m.group(1) if m and m.group(1) in LANG_NAMES else "en"
            out.append({"id": s["id"], "to": addr, "tool": tool, "lang": lang})
        if len(rows) < 100:
            return out
        page += 1


def message(g, hist, url):
    text = price_news.text_for(g, hist).replace("\n\nRead on the official pricing page this morning.", "")
    subject = f"{g['tool']} changed its price"
    body = (f"{text}\n\nGenCost read this on {g['tool']}'s official pricing page and saw it on two different days "
            f"before sending this alert.\n\nToday's prices: {url}\n\n"
            f"You get this because you asked for an email when {g['tool']}'s price changes. "
            f"Reply \"stop\" and you are removed.\n\nGenCost · getgencost.com · no affiliate links, no paid placement")
    return subject, body


def translate(subject, body, lang):
    key = (os.getenv("XAI_API_KEY") or "").strip()
    if lang == "en" or not key:
        return subject, body
    try:
        from openai import OpenAI
        r = OpenAI(api_key=key, base_url="https://api.x.ai/v1", timeout=90).chat.completions.create(
            model="grok-3", temperature=0,
            messages=[{"role": "user", "content":
                       f"Translate this short email into {LANG_NAMES[lang]}. Keep tool names, plan names, prices, numbers, "
                       f"the arrow and URLs exactly as they are. Keep the word \"stop\" in English inside quotes. "
                       f"Answer with JSON only: {{\"subject\": \"...\", \"body\": \"...\"}}\n\n"
                       + json.dumps({"subject": subject, "body": body}, ensure_ascii=False)}])
        out = json.loads(r.choices[0].message.content.strip().removeprefix("```json").removeprefix("```").removesuffix("```"))
        nums = lambda s: sorted(re.findall(r"\d[\d,.]*", s))
        if nums(out["body"]) == nums(body) and SITE in out["body"]:
            return out["subject"], out["body"]
    except Exception as e:  # any problem: send it in English rather than not at all
        print(f"translation to {lang} failed, sending English: {e}")
    return subject, body


def link(p):
    p = p.replace("&", "&amp;").replace("<", "&lt;")
    return re.sub(r"(https://\S+)", r'<a href="\1">\1</a>', p)


def send(key, reply_to, to, subject, body):
    html_body = ('<div style="font-family:system-ui,sans-serif;font-size:15px;line-height:1.55;color:#111">'
                 + "".join(f"<p>{link(p)}</p>" for p in body.split("\n\n")) + "</div>")
    r = requests.post("https://api.resend.com/emails", timeout=30, headers={"Authorization": f"Bearer {key}"},
                      json={"from": FROM, "to": [to], "reply_to": reply_to, "subject": subject, "text": body, "html": html_body,
                            "headers": {"List-Unsubscribe": f"<mailto:{reply_to}?subject=stop>"}})
    return r.status_code in (200, 201), f"HTTP {r.status_code} {r.text[:200]}"


def main():
    preview = "--preview" in sys.argv
    hist = json.load(open(os.path.join(HERE, "data", "history.json"), encoding="utf-8"))
    links = price_news.pages()
    rkey = (os.getenv("RESEND_API_KEY") or "").strip()
    reply_to = (os.getenv("ALERT_REPLY_TO") or "").strip()

    if "--test" in sys.argv:  # one sample alert to the owner's own inbox, with an example price
        g = {"cat": "video", "tool": "D-ID", "plan": "Pro", "ids": ["test"],
             "parts": [{"kind": "price", "how": "a month", "old": 49.0, "new": 39.0}]}
        subject, body = message(g, hist, SITE + links.get(("video", "D-ID"), "/"))
        ok, info = send(rkey, reply_to, reply_to, "[Test] " + subject, body + "\n\n(This is a test alert with an example price.)")
        print("Test alert sent to the ALERT_REPLY_TO inbox." if ok else f"Test alert FAILED: {info}")
        raise SystemExit(0 if ok else 1)

    today = price_news.now().date().isoformat()
    omap = price_news.offers()
    groups = [g for g in price_news.group(price_news.changes(hist, today)) if not price_news.doubtful(g, omap)]
    if not groups:
        print("No confirmed price change today, so no price alerts.")
        return
    token = (os.getenv("NETLIFY_TOKEN") or "").strip()
    if not token or not rkey or not reply_to:
        print("Price alerts are not set up yet (NETLIFY_TOKEN, RESEND_API_KEY and ALERT_REPLY_TO are needed).")
        return
    try:
        state = json.load(open(STATE, encoding="utf-8"))
    except (OSError, ValueError):
        state = {"about": "Hashes of (sign-up, price change) already emailed by price_alerts.py. No email addresses.", "sent": {}}
    people = signups(token)
    sent = failed = 0
    for g in groups:
        url = SITE + links.get((g["cat"], g["tool"]), "/")
        subject, body = message(g, hist, url)
        cache = {}
        for p in people:
            if p["tool"].lower() != g["tool"].lower():
                continue
            mark = hashlib.sha256(f"{p['id']}|{'|'.join(g['ids'])}".encode()).hexdigest()[:20]
            if mark in state["sent"]:
                continue
            if sent + failed >= MAX_PER_RUN:
                log(f"Stopped at {MAX_PER_RUN} alerts today (the email plan's daily limit); the rest go tomorrow.")
                break
            if p["lang"] not in cache:
                cache[p["lang"]] = translate(subject, body, p["lang"])
            s, b = cache[p["lang"]]
            if preview:
                print(f"--- to a {p['lang']} reader of {g['tool']}\n{s}\n\n{b}\n")
                continue
            ok, info = send(rkey, reply_to, p["to"], s, b)
            if ok:
                state["sent"][mark] = today
                sent += 1
            else:
                failed += 1
                log(f"An alert for {g['tool']} could not be sent: {info}")
    if not preview:
        json.dump(state, open(STATE, "w", encoding="utf-8"), indent=1)
        log(f"{today}: {sent} price alert(s) sent for {len(groups)} change(s)" + (f", {failed} failed" if failed else "") + ".")


if __name__ == "__main__":
    main()
