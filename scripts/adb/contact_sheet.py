#!/usr/bin/env python3
"""
@file contact_sheet.py
@brief Build a labeled contact sheet from a scroll-capture frame directory.

@details Reviewing 40+ full-resolution screenshots one at a time is slow and
makes scroll overlap/gaps hard to judge. This tiles every frame into a single
image with its frame number burned in, so duplicate tails and missed regions
are obvious at a glance before transcription starts.

@author pokemon-go tooling
@date 2026-09-18
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw

THUMB_W = 260
COLS = 8
PAD = 8
LABEL_H = 22


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: contact_sheet.py <frame-dir> <output.png> [cols]", file=sys.stderr)
        return 2

    frame_dir = Path(sys.argv[1])
    out_path = Path(sys.argv[2])
    cols = int(sys.argv[3]) if len(sys.argv) > 3 else COLS

    frames = sorted(frame_dir.glob("*.png"))
    if not frames:
        print(f"no PNG frames in {frame_dir}", file=sys.stderr)
        return 1

    with Image.open(frames[0]) as probe:
        w, h = probe.size
    thumb_h = int(THUMB_W * h / w)

    rows = (len(frames) + cols - 1) // cols
    sheet_w = cols * THUMB_W + (cols + 1) * PAD
    sheet_h = rows * (thumb_h + LABEL_H + PAD) + PAD
    sheet = Image.new("RGB", (sheet_w, sheet_h), (24, 24, 28))
    draw = ImageDraw.Draw(sheet)

    for idx, frame in enumerate(frames):
        r, c = divmod(idx, cols)
        x = PAD + c * (THUMB_W + PAD)
        y = PAD + r * (thumb_h + LABEL_H + PAD)
        with Image.open(frame) as im:
            im = im.convert("RGB").resize((THUMB_W, thumb_h), Image.LANCZOS)
            sheet.paste(im, (x, y))
        draw.text((x + 4, y + thumb_h + 4), frame.stem, fill=(235, 235, 235))

    sheet.save(out_path)
    print(f"wrote {out_path} ({len(frames)} frames, {cols}x{rows}, {sheet_w}x{sheet_h})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
