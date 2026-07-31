#!/usr/bin/env python3
"""Generate an article image via Gemini (Nano Banana Pro).

Adapted from the YouTube Thumbnail skill by Tyler Germain (Friday Labs)
for Trustmarkt/Agenturmarkt article images: no headshot requirement,
configurable aspect ratio, optional style/logo reference images.

Usage:
    python3 generate_article_image.py \
        --prompt "Editorial cover, bold German text 'Mini-SaaS statt Chaos', ..." \
        --refs style-ref.jpg claude-logo.png \
        --aspect 16:9 \
        --output cover-v1.png

Environment: GEMINI_API_KEY must be set.
Dependencies: pip install google-genai pillow --break-system-packages
"""
import argparse
import os
import sys
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--prompt", required=True, help="Detailed image prompt")
    p.add_argument("--refs", nargs="*", default=[], help="Style/logo reference image paths")
    p.add_argument("--aspect", default="16:9", choices=["16:9", "3:2", "4:3", "1:1"], help="Aspect ratio")
    p.add_argument("--output", required=True, help="Output PNG path")
    p.add_argument("--model", default="gemini-3-pro-image-preview")
    args = p.parse_args()

    if not os.environ.get("GEMINI_API_KEY"):
        sys.exit("GEMINI_API_KEY is not set.")

    try:
        from google import genai
        from google.genai import types
        from PIL import Image
    except ImportError as e:
        sys.exit(f"Missing dependency ({e}). Run: pip install google-genai pillow --break-system-packages")

    contents = []
    for ref in args.refs:
        rp = Path(ref)
        if not rp.exists():
            sys.exit(f"Reference image not found: {ref}")
        try:
            contents.append(Image.open(rp))
        except Exception as e:
            sys.exit(f"Not a readable image: {ref} ({e})")

    style_suffix = (
        "\n\nStyle requirements: clean professional B2B editorial illustration for a German "
        "business magazine article. Any text in the image must be in correct German, short "
        "(max 6 words), large and legible. Consistent modern palette, generous negative space, "
        "no watermarks, no stock-photo look, no clip-art."
    )
    contents.append(args.prompt + style_suffix)

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    resp = client.models.generate_content(
        model=args.model,
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio=args.aspect),
        ),
    )

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    for part in resp.candidates[0].content.parts:
        if getattr(part, "inline_data", None) and part.inline_data.data:
            out.write_bytes(part.inline_data.data)
            print(f"Saved {out} ({out.stat().st_size} bytes, {args.aspect})")
            return
    sys.exit("No image returned. Response: " + str(resp)[:500])


if __name__ == "__main__":
    main()
