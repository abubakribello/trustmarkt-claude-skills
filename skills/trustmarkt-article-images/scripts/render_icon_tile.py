#!/usr/bin/env python3
"""Deterministically render a real fetched icon (from fetch_tool_icon.py,
or the EU-flag generator) as a glossy rounded-square 3D app-icon tile —
no AI call, so the brand's real colors/shape are always exactly preserved
(this is what "wrong logo color" bugs were coming from: asking Gemini to
redraw a reference icon instead of just compositing it).

Usage:
    python3 render_icon_tile.py --icon assets/tool-logos/claude.png --output tile.png
    # place several tiles in a row:
    python3 render_icon_tile.py --icon a.png --icon b.png --output row.png --gap 20
"""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageOps


def _rounded_mask(size, radius):
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), (size[0] - 1, size[1] - 1)], radius=radius, fill=255)
    return mask


def render_tile(icon_path, tile_size=220, corner_radius=36, padding_frac=0.06,
                 bg_color=(28, 30, 36), shadow_alpha=140, shadow_blur=14, shadow_offset=(0, 8)):
    icon = Image.open(icon_path).convert("RGBA")
    # Fit icon inside the tile with a thin padding, preserving aspect ratio —
    # small padding_frac so the real logo fills the tile (a wide flat margin
    # around a small icon read as an odd grey "cap" rather than an app icon).
    pad = int(tile_size * padding_frac)
    inner = tile_size - pad * 2
    icon.thumbnail((inner, inner), Image.LANCZOS)

    tile = Image.new("RGBA", (tile_size, tile_size), bg_color + (255,))
    mask = _rounded_mask((tile_size, tile_size), corner_radius)
    # subtle gloss: lighter gradient band across the top third
    gloss = Image.new("RGBA", (tile_size, tile_size), (0, 0, 0, 0))
    gd = ImageDraw.Draw(gloss)
    gd.rectangle([(0, 0), (tile_size, tile_size // 3)], fill=(255, 255, 255, 35))
    tile = Image.alpha_composite(tile, gloss)
    tile.putalpha(mask)

    ix = (tile_size - icon.width) // 2
    iy = (tile_size - icon.height) // 2
    tile.alpha_composite(icon, (ix, iy))

    canvas_pad = shadow_blur * 3
    canvas = Image.new("RGBA", (tile_size + canvas_pad * 2, tile_size + canvas_pad * 2), (0, 0, 0, 0))
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sx = canvas_pad + shadow_offset[0]
    sy = canvas_pad + shadow_offset[1]
    sd.rounded_rectangle([(sx, sy), (sx + tile_size, sy + tile_size)], radius=corner_radius,
                          fill=(0, 0, 0, shadow_alpha))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=shadow_blur))
    canvas.alpha_composite(shadow)
    canvas.alpha_composite(tile, (canvas_pad, canvas_pad))
    return canvas


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--icon", action="append", required=True, help="Icon file(s), repeatable for a row")
    p.add_argument("--output", required=True)
    p.add_argument("--tile-size", type=int, default=220)
    p.add_argument("--gap", type=int, default=24)
    args = p.parse_args()

    tiles = [render_tile(icon, tile_size=args.tile_size) for icon in args.icon]
    total_w = sum(t.width for t in tiles) + args.gap * (len(tiles) - 1)
    max_h = max(t.height for t in tiles)
    row = Image.new("RGBA", (total_w, max_h), (0, 0, 0, 0))
    x = 0
    for t in tiles:
        row.alpha_composite(t, (x, (max_h - t.height) // 2))
        x += t.width + args.gap

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    row.save(out)
    print(f"Saved {out} ({row.size[0]}x{row.size[1]}, {len(tiles)} tile(s))")


if __name__ == "__main__":
    main()
