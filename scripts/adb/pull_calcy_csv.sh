#!/usr/bin/env bash
# Find the Calcy IV CSV export on the device and pull it.
#
# Calcy writes it from History, in the three-dot menu, through the Android
# share sheet. That means you pick the folder, so this checks the usual
# ones. Pass a path to skip the search.
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

require_device
mkdir -p "$OUT_ROOT"

if [[ $# -ge 1 ]]; then
  REMOTE="$1"
else
  SEARCH_DIRS=(
    /sdcard/Download
    /sdcard/Documents
    /sdcard/Android/data/tesmath.calcy/files
    /sdcard/CalcyIV
    /sdcard
  )
  note "looking for a Calcy CSV in: ${SEARCH_DIRS[*]}"
  # Android ships toybox find, which has -maxdepth and -iname but not
  # reliably -newermt. Keep the expression to what toybox definitely has.
  REMOTE="$(adb_ shell "find ${SEARCH_DIRS[*]} -maxdepth 2 -iname '*.csv' \
      2>/dev/null | head -40" | tr -d '\r' | grep -i -m1 \
      -E 'calcy|pokemon|scan' || true)"

  if [[ -z "$REMOTE" ]]; then
    echo "No CSV with calcy, pokemon or scan in the name. Everything found:" >&2
    adb_ shell "find ${SEARCH_DIRS[*]} -maxdepth 2 -iname '*.csv' 2>/dev/null" \
      | tr -d '\r' >&2
    die "pass the path as an argument, or re-export and note the folder the save dialog shows."
  fi
fi

LOCAL="$OUT_ROOT/box.csv"
note "pulling $REMOTE"
adb_ pull "$REMOTE" "$LOCAL" >/dev/null

[[ -s "$LOCAL" ]] || die "pulled an empty file from $REMOTE"

ROWS=$(( $(wc -l < "$LOCAL") - 1 ))
echo "$LOCAL"
echo "header: $(head -1 "$LOCAL")"
echo "$ROWS data rows"
