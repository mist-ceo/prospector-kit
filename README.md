# Prospector Kit

`/prospector` finds people who liked your reels and follow you, writes a personal opener for each, and after you approve the list sends them from your Instagram and hands the chat to your SetDM AI.

It runs on YOUR computer, in YOUR Chrome, because Instagram already trusts that device and network. Never set it up on someone else's computer, a server or a VPN.

## Install (once, about 20 minutes)

1. **Claude:** install the Claude desktop app (claude.com/download), sign in, open the **Code** tab.
2. **Chrome:** install the **Claude in Chrome** extension from the Chrome Web Store, sign in with the same Claude account. In that Chrome, stay logged into instagram.com as your coaching account and into setdm.app with your workspace selected. Keep using this Chrome for Instagram as normal.
3. **Composio (reads likers and profiles, about $8 a month):** make your own account at composio.dev. Connect the GetAnyAPI app there and add a payment method if it asks (every lookup costs a fraction of a cent). Copy your Composio MCP link and add it in the Claude app under Settings, Connectors, Add custom connector. Use your own Composio account only, never someone else's: it can reach every app connected to it.
4. **GitHub:** make a free GitHub account and accept the invite to `prospector-kit` (check your email). Copy the repo link from the invite page, then paste this into the Code tab with your link at the end:

   > Clone this private GitHub repo into my home folder and run its setup.sh. If GitHub asks me to log in, walk me through it. The repo:

5. **Check:** type `/prospector check`. It tells you anything that's missing.
6. **Setup:** type `/prospector setup`. Have ready: 10 Instagram handles of clients you closed in DMs, 3 openers you already send and like, and the handles of family, friends and clients it must never message. It also schedules the daily run at 07:30.

## Every day

Your Mac on, Claude open. The day's list lands in `~/Prospector/<your handle>/batches/<date>/approval.md`. Delete any row you don't want, type `/prospector send`, and leave the Instagram tab it's using alone while it sends. It ramps up on its own: 50 a day the first week, 75 the second, then about 100 (5 to 6 hours of slow sending spread through the day). If Instagram ever shows a warning it stops and drops back to 50.

## Updates

Paste this into the Code tab now and then: "Run setup.sh in my prospector-kit folder." It pulls the latest version.
