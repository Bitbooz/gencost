"""
Tells Frode when the daily run needs a look, as a GitHub issue (the GitHub app sends a phone notification).

Runs as the last step of the daily workflow. It collects only real problems:
  - the workflow itself failed
  - a tool's prices could not be confirmed, so the old prices were kept (price-review.txt)
  - the weekly dev.to post failed (devto-review.txt)
  - a queued article could not be published (queue/queue.json)
If there are problems: one open issue labelled 'needs-look' gets them (a new issue, or a comment on the open one).
If everything went fine and an issue is open, it is closed with a short note.

Uses the GitHub CLI (gh) with the workflow's own token; no extra secret is needed.
"""
import datetime as dt
import json
import os
import re
import subprocess
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
TODAY = dt.datetime.now(ZoneInfo("Europe/Oslo")).date().isoformat()
LABEL = "needs-look"
TITLE = "GenCost: something needs a look"


def read(name):
    try:
        return open(os.path.join(HERE, name), encoding="utf-8").read()
    except OSError:
        return ""


def problems():
    out = []
    if os.environ.get("JOB_STATUS", "success") != "success":
        out.append(f"**The daily update failed** before it finished. Log: {os.environ.get('RUN_URL', '')}")
    kept = []
    for block in re.split(r"\n\s*\n", read("price-review.txt")):
        if "kept the previous prices" in block:
            head = block.strip().splitlines()[0]
            why = [l.strip(" -") for l in block.splitlines()[1:] if l.strip().startswith("- ")][:3]
            kept.append(f"- {head.split('  ', 1)[-1].strip()}: " + "; ".join(why))
    if kept:
        out.append("**Prices could not be confirmed** for these tools, so their old prices were kept:\n" + "\n".join(kept[:15]))
    dev = [l for l in read("devto-review.txt").splitlines() if l.startswith(TODAY) and "failed" in l]
    if dev:
        out.append("**The weekly dev.to post failed:**\n" + "\n".join(f"- {l[18:]}" for l in dev[-3:]))
    try:
        q = json.load(open(os.path.join(HERE, "queue", "queue.json"), encoding="utf-8"))
        bad = [i["page"] for i in q.get("items", []) if i.get("published") in ("missing", "exists")]
        left = sum(1 for i in q.get("items", []) if not i.get("published"))
        if bad:
            out.append("**Queued articles that were skipped:** " + ", ".join(bad))
        if left == 0 and any(i.get("published") == TODAY for i in q.get("items", [])):
            out.append("**The article queue is now empty.** Today's article was the last one; add more to keep one a day.")
    except (OSError, ValueError):
        pass
    return out


def gh(*args):
    r = subprocess.run(["gh", *args], capture_output=True, text=True)
    if r.returncode:
        print("gh", " ".join(args[:2]), "failed:", r.stderr.strip()[:300])
    return r.stdout.strip()


def main():
    found = problems()
    gh("label", "create", LABEL, "--color", "D93F0B", "--description", "The daily run needs a look", "--force")
    open_issues = json.loads(gh("issue", "list", "--state", "open", "--label", LABEL, "--json", "number") or "[]")
    number = str(open_issues[0]["number"]) if open_issues else None
    if found:
        body = f"@Bitbooz daily run {TODAY} ({os.environ.get('RUN_URL', '')}):\n\n" + "\n\n".join(found)
        if number:
            gh("issue", "comment", number, "--body", body)
        else:
            gh("issue", "create", "--title", TITLE, "--label", LABEL, "--body", body)
        print("Reported:", len(found), "problem(s)")
    elif number:
        gh("issue", "close", number, "--comment", f"The daily run on {TODAY} went fine, so this is closed.")
        print("All good; closed the open issue.")
    else:
        print("All good; nothing to report.")


if __name__ == "__main__":
    main()
