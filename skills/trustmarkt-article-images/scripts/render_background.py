#!/usr/bin/env python3
"""Deterministically render the cover's dark grid + rim-light-glow background.
No AI call, no external dependency beyond Pillow — guaranteed identical
structure every run, and nothing for a person/text/icon to ever collide
with by surprise, because it is drawn to an exact, known spec.

Usage:
    python3 render_background.py --output bg.png --width 1376 --height 768
"""
import argparse
import math
from PIL import Image, ImageDraw


def render(width, height, output,
           base_color=(15, 16, 20), grid_color=(255, 255, 255),
           grid_alpha=14, grid_spacing=48,
           glow_side="left", glow_color=(255, 205, 110),
           glow_radius_frac=0.55, glow_strength=190):
    glow_center_frac = (0.10, 0.45) if glow_side == "left" else (0.90, 0.45)
    img = Image.new("RGB", (width, height), base_color)

    # Grid overlay
    grid = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid)
    for x in range(0, width, grid_spacing):
        gd.line([(x, 0), (x, height)], fill=grid_color + (grid_alpha,), width=1)
    for y in range(0, height, grid_spacing):
        gd.line([(0, y), (width, y)], fill=grid_color + (grid_alpha,), width=1)
    img = Image.alpha_composite(img.convert("RGBA"), grid)

    # Radial glow (right side, matching where the person will be composited)
    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gpx, gpy = int(width * glow_center_frac[0]), int(height * glow_center_frac[1])
    max_r = int(width * glow_radius_frac)
    glow_px = glow.load()
    # Downsample for speed: render at 1/4 res then upscale
    small_w, small_h = max(1, width // 4), max(1, height // 4)
    small = Image.new("RGBA", (small_w, small_h), (0, 0, 0, 0))
    sp = small.load()
    for sy in range(small_h):
        for sx in range(small_w):
            x, y = sx * 4, sy * 4
            d = math.hypot(x - gpx, y - gpy)
            t = max(0.0, 1.0 - d / max_r)
            a = int(glow_strength * (t ** 1.6))
            if a > 0:
                sp[sx, sy] = glow_color + (a,)
    glow = small.resize((width, height), Image.BILINEAR)
    img = Image.alpha_composite(img, glow)

    img.convert("RGB").save(output)
    print(f"Saved {output} ({width}x{height})")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    p.add_argument("--width", type=int, default=1376)
    p.add_argument("--height", type=int, default=768)
    p.add_argument("--glow-side", choices=["left", "right"], default="left")
    args = p.parse_args()
    render(args.width, args.height, args.output, glow_side=args.glow_side)


if __name__ == "__main__":
    main()
