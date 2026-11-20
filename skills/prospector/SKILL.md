---
name: prospector
description: "Use when the coach wants personalized daily outreach to warm people on Instagram: '/prospector', 'prospector setup', 'build today's batch', 'send the approved batch', or when the morning scheduled task fires. Setup turns 10 closed clients into money signals and writes the opener rules. Each morning it ranks warm people hottest to coldest (follows + liked 2+ reels, follows + liked 1, follows, story viewers; likers who don't follow are never messaged), checks their profiles, and writes an approval sheet with a custom opener per lead. After the coach approves, it sends slowly from his Instagram in Chrome and switches the SetDM AI on for every lead it messaged."
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
  waiting.txt      liked + fit, not following yet. Never sent until they follow
  batches/<date>/  likers.json, followers.json, story_viewers.json, sources.json, pull.txt, profiles.json, approval.md, log.csv
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
2. **Money signals.** Ask for Instagram handles of clients he closed in DMs, up to 10. Use what he has:
   - **10 or more:** pull their profiles (workbench, MODE "profiles") and write the signals from what they have in common.
   - **1 to 9:** pull those, then fill the gaps from his answers to the questions below.
   - **None (new coach):** build it from the questions alone, plus his onboarding answers or ICP doc if he has one. Also ask for 3 to 5 people who booked a call or asked for the price, even if they didn't buy, and pull those.

   Questions (skip any his docs already answer): Who's your best client: age, man or woman, where they live, what they do for work? What problem do they come to you with? What do they usually earn, or what tells you they can afford you? Who wastes your time in the DMs?

   Write `signals.md`: strong signals (1 is enough), weak (need 2), and a **Never** list (who he can't help or won't take: wrong gender, wrong country or language, students, under a set age, other coaches). Put the Never words that show up in bios (e.g. "student", "uni", a city he can't serve) into `config.json` `never_bio` so the helper drops them before judging. Keep strong and weak loose: too narrow and it finds nobody. After 2 weeks, rebuild it from the leads who replied and booked (in sent.csv and SetDM).
3. **Opener.** Ask for 3 openers he already sends and likes. Write `opener.md`: first name, one real detail from their profile, one easy question. His spelling and tone, no link, no offer. Every opener reads different, and a second message is never a copy of the first.
4. **Blacklist.** Ask for family, friends, clients and team handles. One per line.
5. **Schedule.** Create a scheduled task in Claude, every day at 07:30 local: "Run /prospector batch". Tell the coach the Mac has to be on and Claude open at that time.
6. Run `/prospector batch` once now so he sees the sheet.

## Batch (every morning)

**Priority, hottest to coldest.** Fill the day's list from the top down:

| Tier | Who |
|---|---|
| T1 | follows him AND liked 2+ of his reels |
| T2 | follows him AND liked 1 reel |
| T3 | follows him (newest followers) |
| T4 | watched his story |
| Never | liked but doesn't follow. Not messaged until they follow. They wait in `waiting.txt` and come back as T1 or T2 the day they show up as a follower. |

1. **Collect the sources** into `batches/<date>/`:
   - `likers.json`: read `pull_workbench.py`, set MODE = "likers", COACH = handle, REELS = 24, pass the whole text to `COMPOSIO_REMOTE_WORKBENCH`, `curl -sL "<url>" -o .../likers.json`. About 3 cents.
   - `followers.json` (his Chrome): open `instagram.com/<handle>/followers/`, scroll the dialog slowly (one scroll every 1.5 to 3 s, max 60), save `[{"username","full_name"}]`. Newest followers come first. These are confirmed followers, no follow check needed.
   - `story_viewers.json` (his Chrome): open his own active story, open "Seen by" / the viewer list, scroll it slowly the same way, save `[{"username","full_name"}]`. No active story or no viewer list on the web: skip it.
2. `prospector.py candidates ~/Prospector/<handle> <date>` merges the sources, drops blacklist, sent, already checked and pages, and writes `pull.txt` in tier order (T1, T2, likers still needing a follow check, T3, T4) plus `sources.json` with each lead's tier.
3. **Profiles.** Same script, MODE = "profiles", HANDLES = the lines of `pull.txt`. About 24 cents for 400. `curl` to `profiles.json`.
4. `prospector.py sheet ~/Prospector/<handle> <date>` drops the obvious no-fits before you judge: pages and business categories, verified, big accounts, private with no bio, minors (age, school or birth year in the bio), coaches, trainers and sellers (OnlyFans, crypto, forex, MLM, promo), bots and follow-for-follow, empty accounts, bios and names mostly in a non-Latin script (Arabic, Persian, Cyrillic, Hindi, Chinese; `latin_only` in config.json, on by default, turn it off for a coach who sells in those languages), the coach's `never_bio` words. It prints the rest in tier order with the count per drop reason.
5. **Judge** each against `signals.md`, including its Never list (wrong gender, wrong country or language, who he can't help). Keep the fits.
6. **Follow check (his Chrome), only for kept leads tagged CHECK FOLLOW.** In `instagram.com/<handle>/followers/`, type the lead's handle in the dialog's search box, wait 2 to 4 s, read the result. Found: `prospector.py log ~/Prospector/<handle> <date> <lead> follows`, they become T1 or T2. Not found: `... not_follower`, they go to `waiting.txt` and are NOT sent. Clear the box, pause 3 to 8 s. Blocks of 30 with a 5 min pause, max 130 checks. Never open their profiles.
7. **Write** `batches/<date>/approval.md`, up to today's `cap`, T1 first, then T2, T3, T4. Never a liker who didn't pass the follow check.

   ```
   | handle | name | tier | signals | why | opener |
   |---|---|---|---|---|---|
   | jake.r | Jake | T1 | founder, travel | liked 3 reels, runs a design studio | ... |
   ```

   Name = real first name from his full name or bio, never the username. No real name: skip the lead. Openers can use the warmth (he follows, he's been watching), never mention that you tracked likes.
8. Tell the coach: "<n> leads ready in approval.md (T1 x, T2 x, T3 x, T4 x). Delete any row you don't want, then type /prospector send."

## Send (after he approves)

1. `prospector.py queue ~/Prospector/<handle> <date>` prints what can go out now under the caps, and who still needs the SetDM toggle.
2. Per lead, in Chrome: `instagram.com/direct/new/`, search the handle, open the chat, type the opener, send, check it shows as sent. `log ... <lead> sent` (or `failed` / `skipped`).
3. **SetDM toggle after every block of up to 15 sends.** SetDM switches its AI off for a chat whenever a message is sent from the Instagram side, so every lead Claude just messaged needs it back on. In setdm.app: check the coach's @handle is on the page, open each lead's conversation, switch its AI toggle on, `log ... <lead> ai_on`. Find the toggle by its label with `find`, never by guessed coordinates. This per-lead toggle is the only AI switch this skill touches, never the workspace switch or Autopilot.
4. Wait as the safety rules say, run `queue` again, repeat until the queue or the cap is done.
5. Report once at the end: sent, failed, AI on, any warning.

Claude never sends follow-ups in the DMs. Once the toggle is on, SetDM runs the conversation.
