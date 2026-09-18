#!/usr/bin/env bash
# Shared setup for the adb scripts. Source it, don't run it.
set -euo pipefail

ADB="${ADB:-adb}"
DEVICE_ARGS=()
[[ -n "${ANDROID_SERIAL:-}" ]] && DEVICE_ARGS=(-s "$ANDROID_SERIAL")

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT_ROOT="${OUT_ROOT:-$REPO_ROOT/capture}"

die() { echo "error: $*" >&2; exit 1; }
note() { echo "-- $*" >&2; }

adb_() { "$ADB" "${DEVICE_ARGS[@]}" "$@"; }

require_device() {
  command -v "$ADB" >/dev/null 2>&1 \
    || die "adb isn't on PATH. On macOS: brew install --cask android-platform-tools"

  local list
  list="$("$ADB" devices | awk 'NR>1 && NF {print $1, $2}')"
  [[ -n "$list" ]] \
    || die "no device. Plug in over USB, turn on USB debugging, then accept the prompt on the phone."

  if grep -q unauthorized <<<"$list"; then
    die "device is unauthorized. Unlock the phone and tap Allow on the USB debugging prompt."
  fi

  local count
  count="$(wc -l <<<"$list" | tr -d ' ')"
  if [[ "$count" -gt 1 && -z "${ANDROID_SERIAL:-}" ]]; then
    echo "$list" >&2
    die "more than one device. Set ANDROID_SERIAL to the one you want."
  fi
}

# Screen size as "W H". Physical size wins, since an override changes taps.
screen_size() {
  adb_ shell wm size \
    | sed -n 's/.*: *\([0-9]*\)x\([0-9]*\).*/\1 \2/p' \
    | tail -1
}

screen_is_on() {
  adb_ shell dumpsys power | grep -qE 'mWakefulness=Awake|mScreenOn=true'
}

# macOS ships shasum, most Linux ships sha256sum. Take whichever is there.
file_hash() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | cut -d' ' -f1
  else
    sha256sum "$1" | cut -d' ' -f1
  fi
}
