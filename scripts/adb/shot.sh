#!/usr/bin/env bash
# One screenshot. Use it to calibrate coordinates or to check what's on screen.
#
#   shot.sh calibrate      -> capture/calibrate.png
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

NAME="${1:-shot}"
require_device
mkdir -p "$OUT_ROOT"

DEST="$OUT_ROOT/$NAME.png"
adb_ exec-out screencap -p > "$DEST"
[[ -s "$DEST" ]] || die "empty screenshot. Is the screen locked?"

read -r WIDTH HEIGHT <<<"$(screen_size)"
echo "$DEST"
echo "${WIDTH}x${HEIGHT}"
