#!/usr/bin/env python3
"""Orchestrator: assembles one cover image entirely deterministically —
background, icon tiles, headline text, and the real-photo person are all
composited by this script directly (no Gemini call in the default path).
This is the fix for every reliability failure hit in earlier runs:
garbled/misspelled text, wrong-colored logos, text/person layout
collisions, and non-deterministic likeness — none of those failure modes
are reachable anymore because nothing here is AI-regenerated.

The only inputs still requiring judgment (which the calling Claude
session supplies, not this script) are the headline wording and which
concept/entities apply — see select_concept_types.py, extract_entities.py,
select_pose.py, and validate_headline.py for the deterministic scaffolding
around those decisions.

Usage:
    python3 build_cover.py \\
        --headline "35 MIO. €" --subtext "BUSSGELD-RISIKO OHNE AVV" \\
        --icon assets/tool-logos/claude.png --icon assets/institutional-logos/eu-flag.png \\
        --pose assets/headshots/real-photos/johannes-frowning-serious-02.png \\
        --output cover-v1.png
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from render_background import render as render_background
from render_icon_tile import render_tile
from render_text import draw_glow_text
from composite_person import composite as composite_person
from validate_headline import validate as validate_headline

from PIL import Image


def build(headline, subtext, icon_paths, pose_path, output,
          width=1376, height=768, concept=None, person_side="left"):
    """person_side='left' is the default per Johannes's direct feedback on
    6 real A/B pairs (4/6 preferred the tighter, more dominant crop with
    text on the right). This is NOT a reliable per-concept-type rule —
    stat_highlight itself was a 1-1 split across the two sample articles,
    only network_hologram was consistent (2/2) — so don't hardcode side
    by concept type without more data. Override with person_side='right'
    per-cover based on judgment (or future feedback), not a fixed mapping."""
    errors = validate_headline(headline, concept)
    if errors:
        sys.exit("Headline failed validation:\n" + "\n".join(f"  - {e}" for e in errors))

    text_side = "right" if person_side == "left" else "left"

    tmp_bg = Path(output).with_suffix(".bg-tmp.png")
    tmp_full_bg = Path(output).with_suffix(".bg-full-tmp.png")

    render_background(width, height, str(tmp_bg), glow_side=person_side)
    canvas = Image.open(tmp_bg).convert("RGBA")

    text_col_width = int(width * 0.42)
    text_x = 60 if text_side == "left" else width - text_col_width - 60

    if icon_paths:
        tiles = [render_tile(p) for p in icon_paths]
        total_w = sum(t.width for t in tiles) + 24 * (len(tiles) - 1)
        max_h = max(t.height for t in tiles)
        row = Image.new("RGBA", (total_w, max_h), (0, 0, 0, 0))
        x = 0
        for t in tiles:
            row.alpha_composite(t, (x, 0))
            x += t.width + 24
        canvas.alpha_composite(row, (text_x, 70))
        text_start_y = 70 + max_h + 40
    else:
        text_start_y = 340

    box_width = text_col_width - 60
    used_size = draw_glow_text(canvas, headline, text_x, text_start_y, box_width, 90)
    if subtext:
        draw_glow_text(canvas, subtext, text_x, text_start_y + int(used_size * 1.15), box_width, 48, weight=700)

    canvas.convert("RGB").save(tmp_full_bg)
    composite_person(str(tmp_full_bg), pose_path, output, side=person_side)

    tmp_bg.unlink(missing_ok=True)
    tmp_full_bg.unlink(missing_ok=True)
    print(f"Built {output}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--headline", required=True)
    p.add_argument("--subtext", default=None)
    p.add_argument("--icon", action="append", default=[], help="Icon file(s), repeatable")
    p.add_argument("--pose", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--concept", default=None)
    p.add_argument("--person-side", choices=["left", "right"], default="left")
    args = p.parse_args()
    build(args.headline, args.subtext, args.icon, args.pose, args.output,
          concept=args.concept, person_side=args.person_side)


if __name__ == "__main__":
    main()
