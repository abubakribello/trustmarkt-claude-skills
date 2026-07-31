#!/usr/bin/env python3
"""Composite real logo/icon files onto a generated image as a small
watermark or icon row. Deterministic Pillow paste, not AI-drawn — this is
the reliable fallback for brand marks Gemini gets wrong (tested: missed
a letter in a wordmark, substituted a generic icon once). Accepts one
logo (classic corner watermark) or several (placed as a row, e.g. a
"tool composition" icon strip) in one call.

Usage:
    # single brand watermark
    python3 watermark.py --image workspace/<slug>/cover-v1.png \
        --logo assets/brand/logo-wordmark-white.png --in-place

    # multiple tool icons as a row
    python3 watermark.py --image workspace/<slug>/section-1.png \
        --logo assets/tool-logos/whatsapp.png assets/tool-logos/n8n.png \
        --corner top-right --in-place
"""
import argparse
from pathlib import Path

from PIL import Image


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--image", required=True)
    p.add_argument("--logo", required=True, nargs="+", help="One or more logo/icon files")
    p.add_argument("--width-pct", type=float, default=0.12, help="Each icon's width as fraction of image width")
    p.add_argument("--margin-pct", type=float, default=0.03, help="Margin from edges as fraction of image width")
    p.add_argument("--gap-pct", type=float, default=0.015, help="Gap between icons as fraction of image width (multi-icon only)")
    p.add_argument("--corner", default="bottom-right", choices=["bottom-right", "bottom-left", "top-right", "top-left"])
    p.add_argument("--output", help="Defaults to overwriting --image")
    p.add_argument("--in-place", action="store_true")
    args = p.parse_args()

    base = Image.open(args.image).convert("RGBA")
    w, h = base.size
    icon_w = int(w * args.width_pct)
    gap = int(w * args.gap_pct)
    margin = int(w * args.margin_pct)

    icons = []
    for path in args.logo:
        icon = Image.open(path).convert("RGBA")
        scale = icon_w / icon.width
        icon = icon.resize((icon_w, int(icon.height * scale)), Image.LANCZOS)
        icons.append(icon)

    total_w = sum(icon.width for icon in icons) + gap * (len(icons) - 1)
    max_h = max(icon.height for icon in icons)

    is_right = "right" in args.corner
    is_bottom = "bottom" in args.corner
    x = (w - total_w - margin) if is_right else margin
    y = (h - max_h - margin) if is_bottom else margin

    for icon in icons:
        base.paste(icon, (x, y + (max_h - icon.height) // 2), icon)
        x += icon.width + gap

    out = Path(args.output) if args.output else Path(args.image)
    base.convert("RGB").save(out, "PNG")
    print(f"Watermarked {out} with {len(icons)} icon(s)")


if __name__ == "__main__":
    main()
