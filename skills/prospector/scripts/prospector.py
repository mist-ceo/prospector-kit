#!/usr/bin/env python3
"""/prospector bookkeeping. Claude does the browser work and the judging; this keeps the lists honest.

  prospector.py init <dir> <coach_handle>
  prospector.py candidates <dir> <date> [--limit 200]   likers.json or followers.json -> pull.txt (dedupe + drop pages)
  prospector.py sheet <dir> <date>                      profiles.json -> compact list to judge
  prospector.py queue <dir> <date>                      approved rows not sent yet + what the caps allow
  prospector.py log <dir> <date> <handle> <sent|failed|skipped|ai_on|follows|not_follower|warning> [note]
"""
import csv, json, re, sys
from datetime import datetime
from pathlib import Path

DEFAULT_CONFIG = {"coach_handle": "", "setdm_workspace": "", "daily_cap": 30, "hourly_cap": 20,
                  "max_followers": 20000, "min_followers": 0}
PAGE_WORDS = re.compile(r"(shop|store|official|brand|boutique|apparel|clothing|supps|supplement|nutrition|"
                        r"agency|media|magazine|news|daily|memes|coach|trainer|"
                        r"realestate|crypto|forex|_ig$|promo|deals|giveaway)", re.I)
BUSINESS_CATS = re.compile(r"(shop|store|brand|product|company|business|agency|media|news|magazine|"
                           r"gym|fitness|coach|trainer|nutrition|restaurant|real estate)", re.I)


def handles(path):
    p = Path(path)
    if not p.exists():
        return set()
    return {l.strip().lstrip("@").lower() for l in p.read_text().splitlines() if l.strip() and not l.startswith("#")}


def sent_handles(d):
    p = d / "sent.csv"
    if not p.exists():
        return set()
    return {r["handle"] for r in csv.DictReader(p.open()) if r.get("status") == "sent"}


def cfg(d):
    return {**DEFAULT_CONFIG, **json.loads((d / "config.json").read_text())}


def init(d, coach):
    d.mkdir(parents=True, exist_ok=True)
    (d / "batches").mkdir(exist_ok=True)
    if not (d / "config.json").exists():
        (d / "config.json").write_text(json.dumps({**DEFAULT_CONFIG, "coach_handle": coach.lstrip("@")}, indent=2))
    for f, txt in [("blacklist.txt", "# family, friends, clients, team. One handle per line.\n"),
                   ("seen.txt", ""), ("signals.md", "# Money signals\n\n## Strong (1 is enough)\n\n## Weak (need 2)\n\n## Never\n"),
                   ("opener.md", "# Opener rules\n\n## Coach's real openers\n\n## Rules\n- First name, one real detail from the profile, one easy question.\n- No link, no offer, no voice note. Every opener reads different.\n")]:
        if not (d / f).exists():
            (d / f).write_text(txt)
    if not (d / "sent.csv").exists():
        (d / "sent.csv").write_text("time,date,handle,status,note\n")
    print("ready:", d)


def candidates(d, date, limit):
    b = d / "batches" / date
    src = b / "likers.json" if (b / "likers.json").exists() else b / "followers.json"
    fol = json.loads(src.read_text())
    if isinstance(fol, dict):
        sys.exit(f"{src.name} is an error: {fol}")
    fol.sort(key=lambda f: -len(f.get("liked") or []))
    block = handles(d / "blacklist.txt") | sent_handles(d) | handles(d / "seen.txt")
    coach = cfg(d)["coach_handle"].lower()
    out, dropped = [], {"known": 0, "page": 0}
    for f in fol:
        u = (f.get("username") or "").strip().lstrip("@").lower()
        if not u or u == coach or u in out:
            continue
        if u in block:
            dropped["known"] += 1
            continue
        if PAGE_WORDS.search(u) or PAGE_WORDS.search(f.get("full_name") or ""):
            dropped["page"] += 1
            continue
        out.append(u)
        if len(out) >= limit:
            break
    (b / "pull.txt").write_text("\n".join(out) + "\n")
    with (d / "seen.txt").open("a") as s:
        s.write("".join(u + "\n" for u in out))
    print(f"from {src.name}: {len(out)} to pull (about ${len(out) * 0.0006:.2f}) | dropped known {dropped['known']}, pages {dropped['page']} | {b/'pull.txt'}")


def sheet(d, date):
    c = cfg(d)
    b = d / "batches" / date
    prof = json.loads((b / "profiles.json").read_text())
    liked = {}
    if (b / "likers.json").exists():
        liked = {x["username"]: len(x.get("liked") or []) for x in json.loads((b / "likers.json").read_text())}
    keep, drop = [], {}
    for h, p in prof.items():
        why = None
        fc = p.get("follower_count") or 0
        cat = f"{p.get('category') or ''} {p.get('category_name') or ''}"
        if p.get("error"):
            why = "error"
        elif p.get("is_verified"):
            why = "verified"
        elif fc > c["max_followers"] or fc < c["min_followers"]:
            why = "followers"
        elif BUSINESS_CATS.search(cat):
            why = "business"
        elif p.get("is_private") and not (p.get("biography") or "").strip():
            why = "private, no bio"
        if why:
            drop[why] = drop.get(why, 0) + 1
            continue
        keep.append(p)
    for p in keep:
        bio = (p.get("biography") or "").replace("\n", " / ")
        lk = f"liked {liked[p['username']]} | " if p["username"] in liked else ""
        print(f"@{p['username']} | {lk}{p.get('full_name') or '-'} | {p.get('follower_count')}f | "
              f"{'private' if p.get('is_private') else 'public'} | {bio[:220]} | {' '.join(p.get('bio_links') or [])[:80]}")
    print(f"\n{len(keep)} to judge | dropped {drop}")


def approved(d, date):
    p = d / "batches" / date / "approval.md"
    rows = []
    for line in p.read_text().splitlines():
        cells = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(cells) >= 5 and cells[0] not in ("handle", "") and not set(cells[0]) <= set("-:"):
            rows.append({"handle": cells[0].lstrip("@").lower(), "name": cells[1], "opener": cells[4]})
    return rows


def today_log(d, date):
    p = d / "batches" / date / "log.csv"
    return list(csv.DictReader(p.open())) if p.exists() else []


def queue(d, date):
    c = cfg(d)
    block = handles(d / "blacklist.txt")
    sent = sent_handles(d)
    log = today_log(d, date)
    done = {r["handle"] for r in log if r["status"] in ("sent", "failed", "skipped")}
    sent_today = sum(r["status"] == "sent" for r in log)
    hour_ago = datetime.now().timestamp() - 3600
    sent_hour = sum(r["status"] == "sent" and datetime.fromisoformat(r["time"]).timestamp() > hour_ago for r in log)
    if any(r["status"] == "warning" for r in log):
        print("STOP: a warning was logged today. No sends for 48 h.")
        return
    nf = {r["handle"] for r in log if r["status"] == "not_follower"}
    q = [r for r in approved(d, date) if r["handle"] not in done | sent | block | nf]
    need_ai = [r["handle"] for r in log if r["status"] == "sent"
               and r["handle"] not in {x["handle"] for x in log if x["status"] == "ai_on"}]
    room = max(0, min(c["daily_cap"] - sent_today, c["hourly_cap"] - sent_hour))
    print(f"approved left {len(q)} | sent today {sent_today}/{c['daily_cap']} | this hour {sent_hour}/{c['hourly_cap']} | can send now {room}")
    print("AI toggle still off for:", ", ".join(need_ai) or "none")
    for r in q[:room]:
        print(f"@{r['handle']} | {r['opener']}")


def log(d, date, handle, status, note=""):
    now = datetime.now().isoformat(timespec="seconds")
    handle = handle.lstrip("@").lower()
    b = d / "batches" / date
    b.mkdir(parents=True, exist_ok=True)
    for p in (b / "log.csv", d / "sent.csv"):
        new = not p.exists()
        with p.open("a", newline="") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["time", "date", "handle", "status", "note"])
            w.writerow([now, date, handle, status, note])
    print("logged", handle, status)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    cmd, d = a[0], Path(a[1])
    if cmd == "init":
        init(d, a[2])
    elif cmd == "candidates":
        lim = int(a[a.index("--limit") + 1]) if "--limit" in a else 200
        candidates(d, a[2], lim)
    elif cmd == "sheet":
        sheet(d, a[2])
    elif cmd == "queue":
        queue(d, a[2])
    elif cmd == "log":
        log(d, a[2], a[3], a[4], " ".join(a[5:]))
    else:
        sys.exit(__doc__)
