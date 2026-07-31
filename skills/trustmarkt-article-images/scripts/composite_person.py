#!/usr/bin/env python3
"""Composite a real, unedited photo of the subject onto an AI-generated
background — instead of asking Gemini to regenerate the face from scratch.

Why: Gemini re-synthesizes a face every single call, even with identical
reference images and prompt — it's fundamentally non-deterministic, so
"exact, always-correct likeness" cannot be guaranteed by prompting alone.
This script guarantees it by never regenerating the face at all: it takes
a real photo (already cut out, transparent background) and composites it
deterministically, with a feathered edge and a rim-light glow matched to
the background's light direction so it reads as one integrated image
rather than an obvious cutout.

Pick the source --person photo to match the cover's intended mood (a
"serious"/"frowning"/"skeptical"/"thinking" pose for high-drama covers, a
"smiling" one for warmer covers) — see assets/headshots/real-photos/ for
the named library.

Usage:
    python3 composite_person.py --background bg.png --person photo.png --output cover.png
"""
import argparse
from PIL import Image, ImageFilter, ImageEnhance, ImageChops


def composite(background_path, person_path, output_path,
              crop_frac=0.62, height_frac=0.97, inset_frac=0.85,
              side="left", feather_radius=6, glow_radius=6, glow_strength=0.95,
              glow_color=(255, 205, 110)):
    """side='left' (new default, matches Johannes's 4/6 preference for the
    tighter/closer/more-dominant crop) anchors the person to the left edge
    with text/icons expected on the right; side='right' is the original
    layout (person right, text/icons left) for the cases that still tested
    better that way (see build_cover.py's per-concept --person-side)."""
    bg = Image.open(background_path).convert("RGBA")
    person = Image.open(person_path).convert("RGBA")

    # 1. Crop to head + shoulders only (cuts off well above the waist) —
    #    reference thumbnails are head-and-shoulders, not full chest-up.
    pw, ph = person.size
    person = person.crop((0, 0, pw, int(ph * crop_frac)))

    # 2. Feather the alpha edge: blur the alpha channel, then keep the
    #    more-transparent of original vs. blurred so the solid interior
    #    stays fully opaque and only the boundary softens. Avoids the
    #    hard, obviously-pasted-in cutout line.
    r, g, b, a = person.split()
    a_blurred = a.filter(ImageFilter.GaussianBlur(radius=feather_radius))
    a_final = ImageChops.darker(a, a_blurred)
    person = Image.merge("RGBA", (r, g, b, a_final))

    # 3. Scale to fill most of the frame height, position on the right.
    target_h = int(bg.height * height_frac)
    scale = target_h / person.height
    person = person.resize((int(person.width * scale), target_h), Image.LANCZOS)

    # 4. Slight warmth/contrast match so the real photo's studio lighting
    #    doesn't look flat against the generated scene's rim light.
    person = ImageEnhance.Contrast(person).enhance(1.06)
    r, g, b, a = person.split()
    r = r.point(lambda i: min(255, int(i * 1.05)))
    b = b.point(lambda i: max(0, int(i * 0.97)))
    person = Image.merge("RGBA", (r, g, b, a))

    bw, bh = bg.size
    if side == "right":
        px = bw - int(person.width * inset_frac)
    else:
        px = int(person.width * inset_frac) - person.width
    py = bh - person.height

    # 5. Rim-light glow: an edge band (dilated alpha minus original alpha),
    #    blurred and tinted to match the background's warm light source,
    #    composited behind the person so the silhouette edge picks up a
    #    believable glow instead of a flat dark outline.
    alpha_mask = person.split()[-1]
    dilated = alpha_mask.filter(ImageFilter.MaxFilter(9))
    edge_band = ImageChops.subtract(dilated, alpha_mask)
    edge_band = edge_band.filter(ImageFilter.GaussianBlur(radius=glow_radius))
    glow_layer = Image.new("RGBA", person.size, glow_color + (0,))
    glow_layer.putalpha(edge_band.point(lambda i: int(i * glow_strength)))

    canvas = bg.copy()
    canvas.alpha_composite(glow_layer, (px, py))
    canvas.alpha_composite(person, (px, py))
    canvas.convert("RGB").save(output_path)
    print(f"Saved {output_path} ({canvas.size[0]}x{canvas.size[1]})")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--background", required=True, help="AI-generated background PNG (empty space reserved for the person)")
    p.add_argument("--person", required=True, help="Real photo of the subject, transparent background, matching pose/mood")
    p.add_argument("--output", required=True)
    p.add_argument("--crop-frac", type=float, default=0.62, help="Fraction of photo height to keep (head+shoulders)")
    p.add_argument("--height-frac", type=float, default=0.97, help="Person height as a fraction of background height")
    p.add_argument("--inset-frac", type=float, default=0.85, help="Fraction of person width kept visible inside the frame (rest is cropped off the outer edge)")
    p.add_argument("--side", choices=["left", "right"], default="left", help="Which edge the person is anchored to; text/icons go on the other side")
    args = p.parse_args()
    composite(args.background, args.person, args.output,
               crop_frac=args.crop_frac, height_frac=args.height_frac,
               inset_frac=args.inset_frac, side=args.side)


if __name__ == "__main__":
    main()
