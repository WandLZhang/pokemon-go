#!/usr/bin/env bash
# Screenshot a scrolling list, one frame per swipe.
#
#   scroll_capture.sh --name box --steps 30
#
# Swipes are slow on purpose. A fast swipe flings the list and skips rows,
# and the overlap between frames is what lets you stitch without a gap.
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

NAME="capture"
STEPS=30
FROM_FRAC=0.78     # swipe starts here, as a fraction of screen height
TO_FRAC=0.34       # and ends here. The gap is how far the list moves
SWIPE_MS=700       # slow enough not to fling
SETTLE_MS=900      # wait for the list to stop before the next frame

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name)    NAME="$2"; shift 2 ;;
    --steps)   STEPS="$2"; shift 2 ;;
    --from)    FROM_FRAC="$2"; shift 2 ;;
    --to)      TO_FRAC="$2"; shift 2 ;;
    --swipe-ms)  SWIPE_MS="$2"; shift 2 ;;
    --settle-ms) SETTLE_MS="$2"; shift 2 ;;
    -h|--help) sed -n '2,10p' "$0"; exit 0 ;;
    *) die "unknown option $1" ;;
  esac
done

require_device
screen_is_on || die "screen is off. Wake and unlock the phone first."

read -r WIDTH HEIGHT <<<"$(screen_size)"
X=$(( WIDTH / 2 ))
Y_FROM=$(awk -v h="$HEIGHT" -v f="$FROM_FRAC" 'BEGIN{printf "%d", h*f}')
Y_TO=$(awk -v h="$HEIGHT" -v f="$TO_FRAC" 'BEGIN{printf "%d", h*f}')
SETTLE_S=$(awk -v ms="$SETTLE_MS" 'BEGIN{printf "%.2f", ms/1000}')

DEST="$OUT_ROOT/$NAME"
mkdir -p "$DEST"
note "${WIDTH}x${HEIGHT}, swiping $X,$Y_FROM -> $X,$Y_TO, $STEPS frames into $DEST"

PREV_SUM=""
for i in $(seq -f "%03g" 1 "$STEPS"); do
  FRAME="$DEST/$NAME-$i.png"
  adb_ exec-out screencap -p > "$FRAME"

  [[ -s "$FRAME" ]] || die "empty screenshot at frame $i. Is the screen locked?"

  # Two identical frames means the list stopped moving, so we're at the end.
  SUM="$(file_hash "$FRAME")"
  if [[ "$SUM" == "$PREV_SUM" ]]; then
    rm -f "$FRAME"
    note "frame $i matches the one before it. Bottom of the list, stopping."
    break
  fi
  PREV_SUM="$SUM"

  echo "$FRAME"
  adb_ shell input swipe "$X" "$Y_FROM" "$X" "$Y_TO" "$SWIPE_MS"
  sleep "$SETTLE_S"
done

COUNT="$(find "$DEST" -name "$NAME-*.png" | wc -l | tr -d ' ')"
note "$COUNT frames in $DEST"
