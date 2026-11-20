"""GetAnyAPI pulls for /prospector (Composio, billed per call). Runs INSIDE COMPOSIO_REMOTE_WORKBENCH.

Set MODE and the inputs in the first lines, pass the whole file as code_to_execute. It prints one s3 url.

MODE = "likers":   likers of the coach's newest REELS reels (about $0.001 per reel, up to about 1,000 likers each).
                   curl -sL "<url>" -o ~/Prospector/<handle>/batches/<date>/likers.json
MODE = "profiles": one profile per handle in HANDLES (about $0.0006 each, 200 = $0.12).
                   curl -sL "<url>" -o ~/Prospector/<handle>/batches/<date>/profiles.json

GetAnyAPI follower search can't confirm a follow on big accounts (it returns the newest followers instead),
so the follow check happens in the coach's Chrome. See SKILL.md.
"""
MODE = "likers"       # "likers" or "profiles"
COACH = ""            # coach handle, no @ (likers mode)
REELS = 12            # how many of the newest reels to read likers from
HANDLES = []          # profiles mode, from batches/<date>/pull.txt

import json, time, uuid
from concurrent.futures import ThreadPoolExecutor


def call(slug, args, tries=2):
    err = None
    for a in range(tries):
        r, e = run_composio_tool(slug, {**args, "idempotency_key": f"{slug}-{uuid.uuid4().hex[:12]}"})
        out = ((r or {}).get("data") or {}).get("output") or {}
        if out.get("data"):
            return out["data"], None
        err = str(e or r)[:200]
        time.sleep(3)
    return None, err


def likers():
    d, err = call("GETANYAPI_INSTAGRAM_USER_REELS", {"handle": COACH, "max_cost_usd": "0.02", "response_max_items": REELS})
    reels = [r.get("shortcode") for r in (d or {}).get("reels", [])[:REELS] if r.get("shortcode")]
    if not reels:
        return {"error": err or "no reels"}

    def one(code):
        x, e = call("GETANYAPI_INSTAGRAM_POST_LIKERS", {"url": f"https://www.instagram.com/reel/{code}/", "max_cost_usd": "0.05"})
        return code, (x or {}).get("likers", []), e

    seen = {}
    with ThreadPoolExecutor(4) as ex:
        for code, ls, e in ex.map(one, reels):
            for l in ls:
                u = (l.get("username") or "").lower()
                if not u or l.get("verified"):
                    continue
                s = seen.setdefault(u, {"username": u, "full_name": l.get("displayName") or "",
                                        "private": l.get("private"), "liked": []})
                s["liked"].append(code)
    out = sorted(seen.values(), key=lambda s: -len(s["liked"]))
    print("reels", len(reels), "| unique likers", len(out), "| liked 2+:", sum(len(s["liked"]) > 1 for s in out))
    return out


def profiles():
    def one(h):
        p, e = call("GETANYAPI_GET_INSTAGRAM_PROFILE", {"handle": h, "max_cost_usd": "0.01"})
        if not p:
            return h, {"username": h, "error": e}
        return h, {"username": p.get("handle") or h, "full_name": p.get("displayName"), "biography": p.get("bio") or "",
                   "follower_count": p.get("followers"), "following_count": p.get("following"),
                   "media_count": p.get("posts"), "is_private": p.get("private"), "is_verified": p.get("verified"),
                   "is_business_account": p.get("isBusiness"), "category": p.get("category"),
                   "bio_links": [b.get("url") if isinstance(b, dict) else b for b in (p.get("bioLinks") or [])]}

    with ThreadPoolExecutor(6) as ex:
        res = dict(ex.map(one, [h.strip().lstrip("@").lower() for h in HANDLES if h.strip()]))
    bad = [h for h, v in res.items() if v.get("error")]
    print("pulled", len(res) - len(bad), "of", len(res), "| failed:", bad[:20])
    return res


res = likers() if MODE == "likers" else profiles()
path = f"/tmp/prospector-{MODE}.json"
json.dump(res, open(path, "w"))
up = upload_local_file(path)
up = up[0] if isinstance(up, tuple) else up
print("URL", up.get("s3_url"))
