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

{
  echo "url    $URL"
  echo "date   $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "bytes  $(stat -c %s "$OUT")"
  echo "sha256 $(sha256sum "$OUT" | cut -d' ' -f1)"
} > data/gamemaster.stamp

cat data/gamemaster.stamp
