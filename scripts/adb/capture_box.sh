#!/usr/bin/env bash
# Screenshot the whole Pokemon list.
#
# Open Pokemon GO, tap the Pokeball, tap Pokemon, and set the sort to
# Number. Scroll to the very top. Then run this.
#
# Sort by Number, not CP. Number puts every copy of a species together, so
# duplicates are obvious in the frames and the transfer list writes itself.
#
# 325 Pokemon is about 27 frames at 12 per screen. --steps has headroom and
# the run stops early once the list stops moving.
HERE="$(dirname "${BASH_SOURCE[0]}")"
exec "$HERE/scroll_capture.sh" --name box --steps 45 "$@"
