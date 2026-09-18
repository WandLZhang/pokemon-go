#!/usr/bin/env python3
"""
@file transcribe.py
@brief Transcribe Pokemon GO scroll-capture screenshots into structured JSON.

@details The capture scripts produce a sequence of overlapping screenshots of
a scrolling list (item bag or Pokemon box). Reading those by hand is slow and
error prone, and the overlap means the same row appears in several frames. We
send every frame to Gemini in one multimodal request so the model can see the
whole sequence at once and reconcile the overlap itself, rather than us trying
to stitch rows with brittle heuristics.

Uses Vertex AI with application default credentials.

@author pokemon-go tooling
@date 2026-09-18
"""

import argparse
import json
import sys
from pathlib import Path

from google import genai
from google.genai import types

MODEL = "gemini-2.5-flash"
PROJECT = "wz-mobile-coding"
LOCATION = "global"

BAG_PROMPT = """These are sequential, overlapping screenshots of the Pokemon GO
item bag in list view, scrolling from the top of the list to the bottom.

Transcribe every distinct item into JSON. Rules:
- The frames OVERLAP. The same item appears in multiple frames. Report each
  item exactly ONCE.
- The count is the "xN" badge on the lower-left of the item's icon.
- If an item's count badge is cut off at the edge of one frame, look for the
  same item in the adjacent frame where it is fully visible.
- Some items legitimately have NO count badge (e.g. Stickers, Scrapbook,
  Camera, Explorer Gadget, Incubator with an infinity symbol). Use null for
  those.
- Preserve the section headers exactly as shown (MEDICINE, POKE BALLS,
  BERRIES, GIFTS, TRAINER BOOSTS, OTHER ITEMS, PASSES, LURES, KEY ITEMS, TMS,
  EVOLUTION ITEMS, etc.) and record which section each item is under.
- Keep the items in the same order they appear in the list.

Return ONLY valid JSON, no markdown fences, in this exact shape:
{
  "reported_total": <the number left of the slash in the header>,
  "capacity": <the number right of the slash>,
  "items": [
    {"name": "...", "count": <int or null>, "section": "..."}
  ]
}
"""

BOX_PROMPT = """These are sequential, overlapping screenshots of the Pokemon GO
Pokemon storage list, scrolling from the top to the bottom.

Transcribe every distinct Pokemon into JSON. Rules:
- The frames OVERLAP. The same Pokemon appears in multiple frames. Report each
  entry exactly ONCE, in list order.
- For each Pokemon record: name, CP, and any visible markers (shiny, lucky,
  shadow, purified, favorite, buddy, mega, background/costume, traded).
- If a nickname is shown instead of the species name, record it as given.

Return ONLY valid JSON, no markdown fences, in this exact shape:
{
  "pokemon": [
    {"name": "...", "cp": <int or null>, "markers": ["..."]}
  ]
}
"""


def load_frames(frame_dir: Path) -> list[Path]:
    """
    @brief Collect the PNG frames of a capture run in scroll order.

    @param frame_dir Directory written by scroll_capture.sh.

    @return Sorted list of frame paths.
    """
    frames = sorted(frame_dir.glob("*.png"))
    if not frames:
        raise SystemExit(f"no PNG frames in {frame_dir}")
    return frames


def transcribe(frames: list[Path], prompt: str, model: str = MODEL) -> dict:
    """
    @brief Send all frames to Gemini in one request and parse the JSON reply.

    @details Sending the whole sequence at once (rather than frame by frame)
    is what lets the model dedupe the scroll overlap and recover counts that
    are clipped at a frame boundary.

    @param frames Ordered frame paths.
    @param prompt Task instructions describing the expected JSON shape.
    @param model Model identifier to use.

    @return Parsed JSON object from the model.
    """
    client = genai.Client(vertexai=True, project=PROJECT, location=LOCATION)

    parts = [types.Part.from_text(text=prompt)]
    for f in frames:
        parts.append(types.Part.from_text(text=f"--- {f.name} ---"))
        parts.append(
            types.Part.from_bytes(data=f.read_bytes(), mime_type="image/png")
        )

    print(f"sending {len(frames)} frames to {model}...", file=sys.stderr)
    resp = client.models.generate_content(
        model=model,
        contents=[types.Content(role="user", parts=parts)],
        config=types.GenerateContentConfig(
            temperature=0,
            response_mime_type="application/json",
        ),
    )

    raw = resp.text or ""
    # Log the full payload so a bad parse can always be diagnosed.
    print(f"--- model response ({len(raw)} chars) ---", file=sys.stderr)
    print(raw, file=sys.stderr)
    print("--- end model response ---", file=sys.stderr)

    return json.loads(raw)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("frame_dir", type=Path)
    ap.add_argument("--kind", choices=["bag", "box"], required=True)
    ap.add_argument("--out", type=Path, help="write JSON here instead of stdout")
    ap.add_argument("--model", default=MODEL, help="model to use (default: %(default)s)")
    args = ap.parse_args()

    frames = load_frames(args.frame_dir)
    prompt = BAG_PROMPT if args.kind == "bag" else BOX_PROMPT
    data = transcribe(frames, prompt, model=args.model)

    text = json.dumps(data, indent=2, ensure_ascii=False)
    if args.out:
        args.out.write_text(text + "\n")
        print(f"wrote {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
