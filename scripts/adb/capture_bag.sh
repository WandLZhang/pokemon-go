#!/usr/bin/env bash
# Screenshot the whole item bag.
#
# Open Pokemon GO, tap the Pokeball, tap Items, scroll to the top, then run
# this. Use the list view, not the grid, because the grid hides the counts
# behind the icons.
#
# The bag is shorter than the box, and the rows are taller, so this takes a
# smaller bite per swipe than capture_box.sh.
HERE="$(dirname "${BASH_SOURCE[0]}")"
exec "$HERE/scroll_capture.sh" --name bag --steps 25 --from 0.80 --to 0.40 "$@"
