#!/usr/bin/env python3
"""Deterministically render bold glowing headline text onto an image —
no AI call. This is the fix for the "garbled/misspelled German text"
failure mode: since Gemini never touches the text, correct spelling is
guaranteed by construction, and exact position is guaranteed too (no more
text/person layout collisions from a prompt instruction Gemini ignored).

Uses the real Montserrat font (assets/fonts/Montserrat-Variable.ttf) per
the brand guide — set to a bold weight via the variable-font weight axis.

Usage:
    python3 render_text.py --image cover.png --text "35 MIO. €" \\
        --subtext "BUSSGELD-RISIKO OHNE AVV" --box-x 60 --box-y 380 \\
        --box-width 700 --in-place
"""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT_PATH = str(Path(__file__).parent.parent / "assets" / "fonts" / "Montserrat-Variable.ttf")


def _load_font(size, weight=800):
    font = ImageFont.truetype(FONT_PATH, size)
    try:
        font.set_variation_by_axes([weight])
    except Exception:
        pass
    return font


def _fit_font_size(draw, text, max_width, start_size, weight, min_size=20):
    size = start_size
    while size > min_size:
        font = _load_font(size, weight)
        w = draw.textbbox((0, 0), text, font=font)[2]
        if w <= max_width:
            return font, size
        size -= 2
    return _load_font(min_size, weight), min_size


def draw_glow_text(base, text, box_x, box_y, box_width, size,
                    weight=800, fill=(255, 255, 255), glow_color=(255, 205, 110),
                    glow_radius=10, glow_passes=2):
    """Mutates `base` in place. `base` must be an RGBA image."""
    assert base.mode == "RGBA", "draw_glow_text requires an RGBA base image"
    draw = ImageDraw.Draw(base)
    font, fitted_size = _fit_font_size(draw, text, box_width, size, weight)

    glow_layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_layer)
    for _ in range(glow_passes):
        gd.text((box_x, box_y), text, font=font, fill=glow_color + (255,))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=glow_radius))
    base.alpha_composite(glow_layer)

    draw = ImageDraw.Draw(base)
    draw.text((box_x, box_y), text, font=font, fill=fill)
    return fitted_size


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--image", required=True)
    p.add_argument("--text", required=True, help="Main headline (upper line)")
    p.add_argument("--subtext", default=None, help="Optional smaller second line")
    p.add_argument("--box-x", type=int, required=True)
    p.add_argument("--box-y", type=int, required=True)
    p.add_argument("--box-width", type=int, required=True)
    p.add_argument("--main-size", type=int, default=90)
    p.add_argument("--sub-size", type=int, default=48)
    p.add_argument("--output", default=None)
    p.add_argument("--in-place", action="store_true")
    args = p.parse_args()

    img = Image.open(args.image).convert("RGBA")
    used_size = draw_glow_text(img, args.text, args.box_x, args.box_y, args.box_width, args.main_size)
    if args.subtext:
        sub_y = args.box_y + int(used_size * 1.15)
        draw_glow_text(img, args.subtext, args.box_x, sub_y, args.box_width, args.sub_size, weight=700)

    out = Path(args.output) if args.output else Path(args.image)
    img.convert("RGB").save(out)
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
