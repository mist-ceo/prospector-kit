---
name: prospector
description: "Use when the coach wants personalized daily outreach to warm people on Instagram: '/prospector', 'prospector setup', 'build today's batch', 'send the approved batch', or when the morning scheduled task fires. Setup turns 10 closed clients into money signals and writes the opener rules. Each morning it pulls people who liked the coach's recent reels (GetAnyAPI through Composio), checks their profiles, confirms they follow the coach in his own Chrome, and writes an approval sheet with a custom opener per lead. After the coach approves, it sends slowly from his Instagram in Chrome and switches the SetDM AI on for every lead it messaged."
---

# Prospector

`/prospector setup` · `/prospector batch` · `/prospector send` · `/prospector check`

Read `CLAUDE.md` in the kit folder first.

Work folder: `~/Prospector/<handle>/`. Helper: `python3 ~/.claude/skills/prospector/scripts/prospector.py`. Workbench script: `~/.claude/skills/prospector/scripts/pull_workbench.py`.

```
~/Prospector/<handle>/
  config.json      daily cap, hourly cap, follower ceiling, coach handle
  signals.md       money signals from the coach's closed clients
  opener.md        opener rules + 3 real openers in his own words
  blacklist.txt    family, friends, clients, team. Never messaged.
  sent.csv         every handle ever messaged (never messaged twice)
  seen.txt         every handle already checked (never paid for twice)
  batches/<date>/  likers.json, pull.txt, profiles.json, approval.md, log.csv
```

## Instagram safety (read before any send)

1. **Only this computer, only this Chrome.** It runs in the Chrome the coach already uses for Instagram, on his normal home or phone network. Never on a server, a cloud browser, a VPN or a second Chrome profile.
2. **No passwords, no Instagram API keys.** Claude only uses a session the coach logged into himself. If Instagram asks for a login, a code or "was this you", stop and hand it to the coach.
3. **No bots, no private API.** Chrome is the only send path. GetAnyAPI reads likers and profiles, so the coach's account only sends and runs the follow check.
4. **Pace:** max `hourly_cap` (20) per hour, random 90 to 300 s between sends, a 10 to 20 min break every 15. Daily limit ramps to about 100: 50 a day in week 1, 75 in week 2, then 100 (`prospector.py cap` gives today's number). Any Instagram warning drops it back to 50 for 14 days. 100 a day takes about 5 to 6 hours of sending, spread through the day.
5. **Type like a person:** open the DM, type the opener (don't paste), send. No links, no pitch, no voice notes in the opener.
6. **Stop on any warning.** "Try again later", "We restrict certain activity", an action block, a checkpoint, or 3 failed sends in a row: stop, `log ... <handle> warning`, tell the coach, no sends for 48 h (the helper enforces it).
7. **Never message** anyone in `blacklist.txt` or `sent.csv`, a verified account, a business or brand page, another coach, or anyone who looks under 21.

## /prospector check (run first, and whenever something fails)

Check each one and say in one line what's missing:
- Chrome extension connected, Instagram open and logged in as the coach (his @handle on the page).
- setdm.app open and logged in, the coach's workspace selected.
- Composio connected in Claude, GetAnyAPI active there (`COMPOSIO_SEARCH_TOOLS` for "instagram post likers getanyapi" shows an active connection).
- `~/Prospector/<handle>/` exists with signals.md, opener.md, blacklist.txt filled in.

## Setup (once)

1. `prospector.py init ~/Prospector/<handle> <handle>`.
2. **Money signals.** Ask the coach for 10 Instagram handles of clients he closed in DMs. Pull their profiles (workbench, MODE "profiles"). Write `signals.md`: what those 10 have in common that shows on a profile (country, language, job title, age look, travel, family, gym photos, the problem he solves). Strong signals (1 is enough), weak (need 2), never. Keep it loose: too narrow and it finds nobody.
3. **Opener.** Ask for 3 openers he already sends and likes. Write `opener.md`: first name, one real detail from their profile, one easy question. His spelling and tone, no link, no offer. Every opener reads different, and a second message is never a copy of the first.
4. **Blacklist.** Ask for family, friends, clients and team handles. One per line.
5. **Schedule.** Create a scheduled task in Claude, every day at 07:30 local: "Run /prospector batch". Tell the coach the Mac has to be on and Claude open at that time.
6. Run `/prospector batch` once now so he sees the sheet.

## Batch (every morning)

Source: people who liked his recent reels AND follow him. Following means the DM lands in his Primary inbox and they already know him.

1. **Likers.** Read `pull_workbench.py`, set MODE = "likers", COACH = handle, REELS = 12 (raise to 24 if yesterday's batch came up short of the cap), pass the whole text to `COMPOSIO_REMOTE_WORKBENCH`. About 1.5 cents. `curl -sL "<url>" -o ~/Prospector/<handle>/batches/<date>/likers.json`. People who liked 2+ reels come first. If it fails or he has under 5 reels: open `instagram.com/<handle>/followers/` in Chrome, scroll the list slowly (one scroll every 1.5 to 3 s, max 40), save `followers.json` as `[{"username","full_name"}]`.
2. `prospector.py candidates ~/Prospector/<handle> <date> --limit 400` writes `pull.txt`.
3. **Profiles.** Same script, MODE = "profiles", HANDLES = the lines of `pull.txt`. About 24 cents for 400. `curl` to `profiles.json`.
4. `prospector.py sheet ~/Prospector/<handle> <date>` prints the profiles worth judging.
5. **Judge** each against `signals.md`. Drop anyone who looks under 21, coaches, pages, bots, and anyone outside who he coaches. Keep the hits, best first, up to today's `cap` plus 20%.
6. **Follow check (Chrome, keepers only).** Open `instagram.com/<handle>/followers/`, type a keeper's handle in the dialog's search box, wait 2 to 4 s, read the result. Found: `prospector.py log ~/Prospector/<handle> <date> <lead> follows`. Not found: `... not_follower`, drop them. Clear the box, pause 3 to 8 s, next. Max 130 checks, in blocks of 30 with a 5 min pause. Never open their profiles.
7. **Write** `batches/<date>/approval.md`, followers only, up to today's `cap`:

   ```
   | handle | name | signals | why | opener |
   |---|---|---|---|---|
   | jake.r | Jake | founder, travel | runs a design studio, posts from 4 countries | ... |
   ```

   Name = real first name from his full name or bio, never the username. No real name: skip the lead.
8. Tell the coach: "<n> leads ready in approval.md. Delete any row you don't want, then type /prospector send."

## Send (after he approves)

1. `prospector.py queue ~/Prospector/<handle> <date>` prints what can go out now under the caps, and who still needs the SetDM toggle.
2. Per lead, in Chrome: `instagram.com/direct/new/`, search the handle, open the chat, type the opener, send, check it shows as sent. `log ... <lead> sent` (or `failed` / `skipped`).
3. **SetDM toggle after every block of up to 15 sends.** SetDM switches its AI off for a chat whenever a message is sent from the Instagram side, so every lead Claude just messaged needs it back on. In setdm.app: check the coach's @handle is on the page, open each lead's conversation, switch its AI toggle on, `log ... <lead> ai_on`. Find the toggle by its label with `find`, never by guessed coordinates. This per-lead toggle is the only AI switch this skill touches, never the workspace switch or Autopilot.
4. Wait as the safety rules say, run `queue` again, repeat until the queue or the cap is done.
5. Report once at the end: sent, failed, AI on, any warning.

Claude never sends follow-ups in the DMs. Once the toggle is on, SetDM runs the conversation.
