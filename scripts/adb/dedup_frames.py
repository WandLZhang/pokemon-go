#!/usr/bin/env python3
"""
@file dedup_frames.py
@brief Identify duplicate/redundant frames in a scroll-capture sequence.

@details scroll_capture.sh stops when two consecutive screenshots are byte
identical. That check is unreliable on a live device because the status bar
(clock, battery, signal) changes between every frame, so the run scrolls
forever at the bottom of the list. This tool compares only the scrollable
content region of each frame, letting us find the true last unique frame
after the fact.

@author pokemon-go tooling
@date 2026-09-18
"""

import sys
from pathlib import Path

from PIL import Image, ImageChops

# Crop box excludes the status bar (top) and the floating nav buttons (bottom),
# keeping only the scrolling list content that actually distinguishes frames.
CROP_TOP_FRAC = 0.18
CROP_BOTTOM_FRAC = 0.90


def content_signature(path: Path) -> bytes:
    """
    @brief Return a comparable byte signature for a frame's content region.

    @param path Path to a PNG screenshot.

    @return Raw RGB bytes of the cropped, downscaled content region.
    """
    with Image.open(path) as im:
        im = im.convert("RGB")
        w, h = im.size
        box = (0, int(h * CROP_TOP_FRAC), w, int(h * CROP_BOTTOM_FRAC))
        # Downscale to absorb 1-2px scroll jitter and antialiasing noise.
        crop = im.crop(box).resize((160, 320), Image.BILINEAR)
        return crop.tobytes()


def diff_score(a: Path, b: Path) -> float:
    """
    @brief Mean absolute per-channel difference between two frames' content.

    @param a First frame path.
    @param b Second frame path.

    @return Mean absolute difference in 0-255 units; near 0 means identical.
    """
    with Image.open(a) as ia, Image.open(b) as ib:
        ia = ia.convert("RGB")
        ib = ib.convert("RGB")
        w, h = ia.size
        box = (0, int(h * CROP_TOP_FRAC), w, int(h * CROP_BOTTOM_FRAC))
        ca = ia.crop(box).resize((160, 320), Image.BILINEAR)
        cb = ib.crop(box).resize((160, 320), Image.BILINEAR)
        d = ImageChops.difference(ca, cb)
        hist = d.histogram()
        total = 0
        count = 0
        for channel in range(3):
            for value in range(256):
                n = hist[channel * 256 + value]
                total += value * n
                count += n
        return total / count if count else 0.0


def main() -> int:
    if len(sys.argv) < 2:
        print(
            "usage: dedup_frames.py <frame-dir> [threshold]\n"
            "       dedup_frames.py <frame-a.png> <frame-b.png>",
            file=sys.stderr,
        )
        return 2

    # Pair mode: scroll_capture.sh calls this per frame to decide when the list
    # stopped moving. Printing just the score keeps the shell side a one-liner.
    if len(sys.argv) == 3 and Path(sys.argv[1]).is_file() and Path(sys.argv[2]).is_file():
        print(f"{diff_score(Path(sys.argv[1]), Path(sys.argv[2])):.4f}")
        return 0

    frame_dir = Path(sys.argv[1])
    threshold = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0

    frames = sorted(frame_dir.glob("*.png"))
    if not frames:
        print(f"no PNG frames in {frame_dir}", file=sys.stderr)
        return 1

    print(f"{len(frames)} frames in {frame_dir}")
    print(f"threshold={threshold} (mean abs content diff)\n")

    last_unique = frames[0]
    unique = [frames[0]]
    for prev, cur in zip(frames, frames[1:]):
        score = diff_score(prev, cur)
        flag = "DUP " if score < threshold else "    "
        print(f"{flag}{prev.name} -> {cur.name}  diff={score:.3f}")
        if score >= threshold:
            unique.append(cur)
            last_unique = cur

    print(f"\nunique frames: {len(unique)}")
    print(f"last unique frame: {last_unique.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
