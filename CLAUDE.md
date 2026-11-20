# CLAUDE.md: Prospector Kit

**Read this file first, every time.** This kit runs daily warm outreach for a coach: it finds people who liked his reels and follow him, writes a personal opener for each, and after he approves the list sends them from his own Instagram in Chrome and hands each chat to SetDM. It is read and run only: updates come from setup.sh, so never edit the files in this folder.

## What's here

| Path | What |
|---|---|
| `skills/prospector/` | The `/prospector` skill and its two scripts |
| `setup.sh` | Installs and updates the skill. Rerun it any time to get the latest version |

The coach's own work never goes in this folder. It lives in `~/Prospector/<handle>/`.

## Rules (non-negotiable)

1. **Nothing goes out on Instagram without the coach's approval.** Only rows he left in that day's approval.md get sent.
2. **Only this computer, only his Chrome.** Never log his Instagram in anywhere else, never use a VPN, server or cloud browser.
3. **Never type a password or a code.** Every login and every "was this you" is the coach's.
4. **SetDM:** the only AI switch this kit touches is the per-chat toggle, for leads it just messaged from an approved batch. Never the workspace switch, never Autopilot. Check the coach's @handle is on the page before every click in SetDM.
5. **Stop on any Instagram warning** and tell the coach. No sends for 48 h after one.
6. **No em dashes.** Commas, periods, colons or line breaks.
7. **Don't make anything up.** Names come from the lead's profile, openers follow the coach's own rules in opener.md.
