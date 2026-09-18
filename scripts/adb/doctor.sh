#!/usr/bin/env bash
# Preflight. Run this first and fix whatever it complains about.
source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

require_device

read -r WIDTH HEIGHT <<<"$(screen_size)"
MODEL="$(adb_ shell getprop ro.product.model | tr -d '\r')"
RELEASE="$(adb_ shell getprop ro.build.version.release | tr -d '\r')"

echo "device       $MODEL, Android $RELEASE"
echo "screen       ${WIDTH}x${HEIGHT}"

if screen_is_on; then
  echo "screen state on"
else
  echo "screen state OFF. Wake and unlock the phone, or every capture is black."
fi

FOREGROUND="$(adb_ shell dumpsys activity activities \
  | sed -n 's/.*mResumedActivity.*{[^ ]* [^ ]* \([^ /]*\)\/.*/\1/p' | head -1)"
echo "foreground   ${FOREGROUND:-unknown}"

for PKG in com.nianticlabs.pokemongo tesmath.calcy; do
  if adb_ shell pm list packages | tr -d '\r' | grep -qx "package:$PKG"; then
    echo "installed    $PKG"
  else
    echo "MISSING      $PKG"
  fi
done

# A dimmer distorts color and breaks every Calcy scan. It's the most common
# cause of a failed read.
DIM="$(adb_ shell settings get secure reduce_bright_colors_activated 2>/dev/null | tr -d '\r')"
[[ "$DIM" == "1" ]] && echo "WARNING      Extra Dim is on. Turn it off or Calcy scans fail."

echo
echo "capture dir  $OUT_ROOT"
