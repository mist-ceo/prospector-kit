#!/usr/bin/env python3
"""/prospector bookkeeping. Claude does the browser work and the judging; this keeps the lists honest.

  prospector.py init <dir> <coach_handle>
  prospector.py candidates <dir> <date> [--limit 400]   likers/followers/story_viewers -> pull.txt, tiered hottest first
  prospector.py sheet <dir> <date>                      profiles.json -> compact list to judge
  prospector.py cap <dir> <date>                        today's daily limit (ramp 50, 75, 100)
  prospector.py queue <dir> <date>                      approved rows not sent yet + what the caps allow
  prospector.py log <dir> <date> <handle> <sent|failed|skipped|ai_on|follows|not_follower|warning> [note]
"""
import csv, json, re, sys
from datetime import datetime
from pathlib import Path

DEFAULT_CONFIG = {"coach_handle": "", "setdm_workspace": "", "daily_cap": 100, "hourly_cap": 20,
                  "never_bio": [], "latin_only": True,
                  "ramp": [[0, 50], [7, 75], [14, 100]],
                  "max_followers": 20000, "min_followers": 0}
PAGE_WORDS = re.compile(r"(shop|store|official|brand|boutique|apparel|clothing|supps|supplement|nutrition|"
                        r"agency|media|magazine|news|daily|memes|coach|trainer|"
                        r"realestate|crypto|forex|_ig$|promo|deals|giveaway)", re.I)
MINOR = re.compile(r"(\b1[0-7] ?(y/?o|yrs?|years? old)\b|\bclass of 20(2[6-9]|3\d)\b|\bu1[0-8]\b|\bunder ?1[0-8]\b|"
                   r"high ?school|middle school|\bgrade (9|1[0-2])\b|\b(born|b\.|bday|birthday)\W.{0,20}?20(0[6-9]|1\d)\b|🎂.{0,20}?20(0[6-9]|1\d)\b|\b20(0[6-9]|1\d) ?🎂)", re.I)
SELLER = re.compile(r"(\bcoach(ing)?\b|personal trainer|\btrainer\b|\bpt\b|online training|\bdm (me )?for\b|onlyfans|"
                    r"\bof\b ?link|\bcrypto\b|\bforex\b|\bday ?trad|\bpromo|\bcollabs?\b|\bambassador\b|\bugc\b|"
                    r"\bmlm\b|\bherbalife\b|\bcashapp\b)", re.I)
BUSINESS_CATS = re.compile(r"(shop|store|brand|product|company|business|agency|media|news|magazine|"
                           r"gym|fitness|coach|trainer|nutrition|restaurant|real estate)", re.I)


def non_latin(text):
    """True when most letters are outside the Latin alphabet (Arabic, Persian, Cyrillic, Devanagari, CJK...)."""
    letters = [ch for ch in text if ch.isalpha()]
    if len(letters) < 4:
        return False
    latin = sum(ch.isascii() or "\u00c0" <= ch <= "\u024f" for ch in letters)
    return latin / len(letters) < 0.5


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


def cap_today(d, date):
    """Ramp by days since the first send: 50, then 75 after a week, then daily_cap (100) after two.
    Any warning in the last 14 days drops it back to the first step."""
    c = cfg(d)
    p = d / "sent.csv"
    rows = list(csv.DictReader(p.open())) if p.exists() else []
    sends = sorted(r["date"] for r in rows if r["status"] == "sent")
    day = datetime.fromisoformat(date)
    recent_warn = any(r["status"] == "warning" and (day - datetime.fromisoformat(r["date"])).days < 14 for r in rows)
    if not sends or recent_warn:
        return min(c["ramp"][0][1], c["daily_cap"])
    age = (day - datetime.fromisoformat(sends[0])).days
    step = max(v for days, v in c["ramp"] if age >= days)
    return min(step, c["daily_cap"])


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


def load_list(path):
    if not path.exists():
        return []
    x = json.loads(path.read_text())
    if isinstance(x, dict):
        sys.exit(f"{path.name} is an error: {x}")
    return x


def known_follows(d):
    p = d / "sent.csv"
    return {r["handle"] for r in csv.DictReader(p.open()) if r["status"] == "follows"} if p.exists() else set()


TIER_ORDER = {"T1": 0, "T2": 1, "check2": 2, "check1": 3, "T3": 4, "T4": 5}
TIER_TEXT = {"T1": "T1 follows + liked 2+", "T2": "T2 follows + liked 1", "T3": "T3 follows",
             "T4": "T4 story viewer", "check2": "liked 2+, CHECK FOLLOW", "check1": "liked 1, CHECK FOLLOW"}


def tier(follows, liked, story):
    if follows:
        return "T1" if liked >= 2 else "T2" if liked == 1 else "T3"
    if liked:
        return "check2" if liked >= 2 else "check1"     # never sent unless the follow check finds them
    return "T4" if story else None


def candidates(d, date, limit):
    """Merge today's sources (likers.json from the API, followers.json and story_viewers.json from his Chrome),
    tier them hottest to coldest, write pull.txt in that order and sources.json with each lead's tier."""
    b = d / "batches" / date
    likers = load_list(b / "likers.json")
    followers = load_list(b / "followers.json")
    story = load_list(b / "story_viewers.json")
    if not (likers or followers or story):
        sys.exit("no sources: need likers.json, followers.json or story_viewers.json in " + str(b))
    norm = lambda x: (x.get("username") or "").strip().lstrip("@").lower()
    fol = {norm(x) for x in followers} | known_follows(d)
    seen_story = {norm(x) for x in story}
    liked = {norm(x): len(x.get("liked") or []) for x in likers}
    names = {norm(x): x.get("full_name") or "" for x in likers + followers + story}
    waiting = handles(d / "waiting.txt")          # fit, liked, didn't follow yet
    block = handles(d / "blacklist.txt") | sent_handles(d)
    seen = handles(d / "seen.txt")
    coach = cfg(d)["coach_handle"].lower()
    rows, dropped = [], {"known": 0, "page": 0, "liked, not following": 0}
    for u in set(names):
        if not u or u == coach or u in block:
            dropped["known"] += u in block
            continue
        if u in seen and not (u in waiting and u in fol):   # a waiting liker who now follows comes back
            dropped["known"] += 1
            continue
        if PAGE_WORDS.search(u) or PAGE_WORDS.search(names[u]):
            dropped["page"] += 1
            continue
        t = tier(u in fol, liked.get(u, 0), u in seen_story)
        if u in waiting and u not in fol:
            dropped["liked, not following"] += 1
            continue
        if t:
            rows.append((TIER_ORDER[t], -liked.get(u, 0), u, t))
    rows.sort()
    rows = rows[:limit]
    (b / "pull.txt").write_text("".join(r[2] + "\n" for r in rows))
    src = {r[2]: {"tier": r[3], "liked": liked.get(r[2], 0), "follows": r[2] in fol, "story": r[2] in seen_story} for r in rows}
    (b / "sources.json").write_text(json.dumps(src, indent=1))
    with (d / "seen.txt").open("a") as f:
        f.write("".join(r[2] + "\n" for r in rows))
    count = {}
    for r in rows:
        count[r[3]] = count.get(r[3], 0) + 1
    print(f"{len(rows)} to pull (about ${len(rows) * 0.0006:.2f}) | " + ", ".join(f"{TIER_TEXT[k]}: {v}" for k, v in sorted(count.items(), key=lambda x: TIER_ORDER[x[0]])))
    print(f"dropped {dropped} | {b / 'pull.txt'}")


def sheet(d, date):
    c = cfg(d)
    b = d / "batches" / date
    prof = json.loads((b / "profiles.json").read_text())
    src = json.loads((b / "sources.json").read_text()) if (b / "sources.json").exists() else {}
    never = re.compile("|".join(c["never_bio"]), re.I) if c["never_bio"] else None
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
        elif MINOR.search(p.get("biography") or ""):
            why = "minor"
        elif SELLER.search(p.get("biography") or ""):
            why = "coach or seller"
        elif (p.get("following_count") or 0) >= 3000 and fc < 300:
            why = "bot or follow-for-follow"
        elif not p.get("media_count") and not (p.get("biography") or "").strip() and not (p.get("full_name") or "").strip():
            why = "empty account"
        elif c["latin_only"] and non_latin(f"{p.get('biography') or ''} {p.get('full_name') or ''}"):
            why = "non-English script"
        elif never and never.search(f"{p.get('biography') or ''} {p.get('full_name') or ''}"):
            why = "coach's never list"
        if why:
            drop[why] = drop.get(why, 0) + 1
            continue
        keep.append(p)
    keep.sort(key=lambda p: (TIER_ORDER.get((src.get(p["username"]) or {}).get("tier"), 9), -((src.get(p["username"]) or {}).get("liked") or 0)))
    for p in keep:
        bio = (p.get("biography") or "").replace("\n", " / ")
        lk = TIER_TEXT.get((src.get(p["username"]) or {}).get("tier"), "?") + " | "
        print(f"@{p['username']} | {lk}{p.get('full_name') or '-'} | {p.get('follower_count')}f | "
              f"{'private' if p.get('is_private') else 'public'} | {bio[:220]} | {' '.join(p.get('bio_links') or [])[:80]}")
    print(f"\n{len(keep)} to judge | dropped {drop}")


def approved(d, date):
    p = d / "batches" / date / "approval.md"
    rows = []
    for line in p.read_text().splitlines():
        cells = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(cells) >= 5 and cells[0] not in ("handle", "") and not set(cells[0]) <= set("-:"):
            rows.append({"handle": cells[0].lstrip("@").lower(), "name": cells[1], "opener": cells[-1]})
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
    cap = cap_today(d, date)
    room = max(0, min(cap - sent_today, c["hourly_cap"] - sent_hour))
    print(f"approved left {len(q)} | sent today {sent_today}/{cap} | this hour {sent_hour}/{c['hourly_cap']} | can send now {room}")
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
    if status == "not_follower":
        with (d / "waiting.txt").open("a") as f:
            f.write(handle + "\n")
    print("logged", handle, status)


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    cmd, d = a[0], Path(a[1])
    if cmd == "init":
        init(d, a[2])
    elif cmd == "candidates":
        lim = int(a[a.index("--limit") + 1]) if "--limit" in a else 400
        candidates(d, a[2], lim)
    elif cmd == "sheet":
        sheet(d, a[2])
    elif cmd == "cap":
        print(cap_today(d, a[2]))
    elif cmd == "queue":
        queue(d, a[2])
    elif cmd == "log":
        log(d, a[2], a[3], a[4], " ".join(a[5:]))
    else:
        sys.exit(__doc__)
