#!/bin/bash
# Installs or updates the Prospector Kit. Safe to rerun.
cd "$(dirname "$0")" || exit 1

ok() { printf "  ok   %s\n" "$1"; }
miss() { printf "  MISSING  %s\n" "$1"; MISSING=1; }

echo "Updating"
git pull -q --rebase origin main 2>/dev/null && ok "latest version" || echo "  (couldn't pull, using what's here)"

echo "Checking tools"
command -v git >/dev/null && ok git || miss "git"
command -v python3 >/dev/null && ok python3 || miss "python3 (run: xcode-select --install)"
command -v curl >/dev/null && ok curl || miss "curl"
command -v claude >/dev/null || [ -d "/Applications/Claude.app" ] && ok "Claude" || miss "Claude desktop app (claude.com/download)"
[ -d "/Applications/Google Chrome.app" ] || command -v google-chrome >/dev/null && ok "Google Chrome" || miss "Google Chrome"

echo "Installing the skill"
mkdir -p "$HOME/.claude/skills" "$HOME/Prospector"
for d in skills/*/; do
  n=$(basename "$d")
  [ -f "$d/SKILL.md" ] || continue
  rm -rf "$HOME/.claude/skills/$n" && cp -R "$d" "$HOME/.claude/skills/$n" && ok "/$n"
done
ok "your work folder: ~/Prospector"

[ -n "$MISSING" ] && echo "Install what's MISSING, then rerun." || echo "Done. Type /prospector check in Claude to start."
