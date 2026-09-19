#!/usr/bin/env bash
# Pull the current PokeMiners game master and record what we got.
# The JSON itself stays out of git; data/gamemaster.stamp pins the version.
set -euo pipefail

cd "$(dirname "$0")"
mkdir -p data

URL="https://raw.githubusercontent.com/PokeMiners/game_masters/master/latest/latest.json"
OUT="data/gamemaster.json"

echo "fetching $URL"
curl -fsS -o "$OUT.tmp" "$URL"
mv "$OUT.tmp" "$OUT"

# stat -c and sha256sum are GNU. macOS has neither, and both run after the
# download succeeds, so the old version left you with the JSON and no stamp.
if command -v sha256sum >/dev/null 2>&1; then
  HASH="$(sha256sum "$OUT" | cut -d' ' -f1)"
else
  HASH="$(shasum -a 256 "$OUT" | cut -d' ' -f1)"
fi

{
  echo "url    $URL"
  echo "date   $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "bytes  $(wc -c < "$OUT" | tr -d ' ')"
  echo "sha256 $HASH"
} > data/gamemaster.stamp

cat data/gamemaster.stamp
