#!/usr/bin/env bash
# Walk the box in Pokemon GO and let Calcy read each one.
#
#   calcy_scan.sh --button 980,1750 --count 80
#
# There are no default coordinates. Calcy's floating button sits wherever
# you dragged it, and a wrong tap opens something else. Get the real
# position first:
#
#   1. Open one Pokemon so the Calcy button is visible.
#   2. scripts/adb/shot.sh calibrate
#   3. Read the button's pixel position off that screenshot and pass it.
#
# The loop is: tap Calcy, wait for the read, swipe left to the next
# Pokemon. Calcy stores every read in its History, and pull_calcy_csv.sh
# exports the lot.
#
# Leave the phone alone while this runs. A stray touch desyncs it.
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

BUTTON=""
COUNT=50
SCAN_MS=2600      # Calcy needs a beat to read the arc and the stats
SWIPE_MS=400

while [[ $# -gt 0 ]]; do
  case "$1" in
    --button)  BUTTON="$2"; shift 2 ;;
    --count)   COUNT="$2"; shift 2 ;;
    --scan-ms) SCAN_MS="$2"; shift 2 ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) die "unknown option $1" ;;
  esac
done

[[ "$BUTTON" =~ ^[0-9]+,[0-9]+$ ]] \
  || die "--button needs X,Y in pixels. See the calibration steps at the top of this file."

require_device
screen_is_on || die "screen is off. Wake and unlock the phone first."

BX="${BUTTON%,*}"
BY="${BUTTON#*,}"
read -r WIDTH HEIGHT <<<"$(screen_size)"
MID_Y=$(( HEIGHT / 2 ))
RIGHT_X=$(( WIDTH * 85 / 100 ))
LEFT_X=$(( WIDTH * 15 / 100 ))
SCAN_S=$(awk -v ms="$SCAN_MS" 'BEGIN{printf "%.2f", ms/1000}')

note "scanning $COUNT Pokemon, tapping Calcy at $BX,$BY"
note "stop with ctrl-c. Calcy keeps everything it already read."

for i in $(seq 1 "$COUNT"); do
  adb_ shell input tap "$BX" "$BY"
  sleep "$SCAN_S"
  # Swipe right to left moves to the next Pokemon on the detail screen.
  adb_ shell input swipe "$RIGHT_X" "$MID_Y" "$LEFT_X" "$MID_Y" "$SWIPE_MS"
  sleep 0.7
  printf '\r  %d/%d' "$i" "$COUNT" >&2
done
echo >&2

note "done. Export from Calcy History, then run pull_calcy_csv.sh"
