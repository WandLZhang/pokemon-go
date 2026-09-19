#!/usr/bin/env bash
# Screenshot the whole Pokemon list.
#
# Open Pokemon GO, tap the Pokeball, tap Pokemon, and set the sort to
# Number. Scroll to the very top. Then run this.
#
# Sort by Number, not CP. Number puts every copy of a species together, so
# duplicates are obvious in the frames and the transfer list writes itself.
#
# Overlap matters more than speed here. Each card renders CP above the
# sprite and the name below it, so a row sitting at the top or bottom edge
# loses one of the two. The first run advanced about five rows per frame
# against five visible, which left no overlap and dropped a row per frame.
#
# 0.70 to 0.48 moves roughly 1.6 rows against 5.5 visible, so every row
# lands mid-screen in some frame with both its CP and its name. That costs
# more frames. Take the frames.
HERE="$(dirname "${BASH_SOURCE[0]}")"
exec "$HERE/scroll_capture.sh" --name box --steps 120 \
  --from 0.70 --to 0.48 --swipe-ms 1200 --settle-ms 1200 "$@"
