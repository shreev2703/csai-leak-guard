#!/bin/sh
# One-line setup for the CSAI Leak Guard game (Mac / Linux). Paste into Terminal:
#
#   curl -LsSf https://raw.githubusercontent.com/shreev2703/csai-leak-guard/main/install.sh | sh
#
# It installs uv (which installs Python for you), downloads the game into
# ~/csai-leak-guard, and starts it. Paste the same line again any time to restart.
# It never overwrites your filter.py.
set -e
GITHUB_USER="shreev2703"
REPO_ZIP="${LEAKGUARD_ZIP:-https://github.com/$GITHUB_USER/csai-leak-guard/archive/refs/heads/main.zip}"
DEST="${LEAKGUARD_DEST:-$HOME/csai-leak-guard}"
export PATH="$HOME/.local/bin:$PATH"

if ! command -v uv >/dev/null 2>&1; then
  echo "==> Installing uv (one time, about 10 seconds)..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

if [ -f "$DEST/leakguard.py" ]; then
  echo "==> Found the game in $DEST (keeping your changes)"
else
  echo "==> Downloading the game into $DEST ..."
  TMP="$(mktemp -d)"
  curl -LsSf "$REPO_ZIP" -o "$TMP/game.zip"
  unzip -q "$TMP/game.zip" -d "$TMP/x"
  mkdir -p "$DEST"
  cp -R "$TMP"/x/*/. "$DEST"/
  rm -rf "$TMP"
fi

cd "$DEST"
echo "==> Starting Leak Guard. Your browser will open in a moment."
echo "    (If it doesn't, open the link printed below.)"
if [ -n "$CI" ]; then
  uv run leakguard.py --check
else
  uv run leakguard.py < /dev/tty
fi
