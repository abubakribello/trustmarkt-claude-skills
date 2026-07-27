#!/usr/bin/env python3
"""Fetch a real icon/logo for a tool, company, or institution mentioned in
an article, so it can be passed as a Gemini reference image (or pasted in
deterministically via watermark.py) instead of asking Gemini to invent a
brand mark from a text description alone.

Sources, in order:
  1. Simple Icons CDN (cdn.simpleicons.org) — thousands of tech/software
     brands in their official color, as SVG, converted to PNG here.
  2. Google's favicon service — fallback for companies/institutions not
     on Simple Icons (lower quality, but works for almost any domain).
Note: Clearbit's logo API is NOT reachable from this sandbox (DNS
blocked) — don't rely on it.

Results are cached to --out; re-run is a no-op unless --force is passed,
so a growing library of tools builds up across article runs instead of
re-fetching every time.

Usage:
    python3 fetch_tool_icon.py --name "WhatsApp" --out assets/tool-logos/whatsapp.png
    python3 fetch_tool_icon.py --name "n8n" --out assets/tool-logos/n8n.png
    python3 fetch_tool_icon.py --name "Hetzner" --domain hetzner.com --out assets/tool-logos/hetzner.png

Dependencies: pip install cairosvg pillow --break-system-packages
  (cairosvg needs the native `cairo` library: brew install cairo / apt install libcairo2)
"""
import argparse
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path


def slugify(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


def fetch(url, timeout=10):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, resp.read()


def try_simple_icons(slug):
    try:
        status, data = fetch(f"https://cdn.simpleicons.org/{slug}")
        if status == 200 and data:
            return data
    except urllib.error.HTTPError:
        pass
    except Exception:
        pass
    return None


def try_favicon(domain):
    try:
        status, data = fetch(f"https://www.google.com/s2/favicons?domain={domain}&sz=256")
        if status == 200 and data:
            return data
    except Exception:
        pass
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--name", required=True, help="Tool/company/institution name")
    p.add_argument("--out", required=True, help="Output PNG path")
    p.add_argument("--domain", help="Domain to try for favicon fallback (defaults to <slug>.com)")
    p.add_argument("--force", action="store_true", help="Re-fetch even if --out already exists")
    args = p.parse_args()

    out = Path(args.out)
    if out.exists() and not args.force:
        print(f"Already cached: {out}")
        return

    slug = slugify(args.name)
    svg_data = try_simple_icons(slug)
    if svg_data:
        try:
            import cairosvg
        except ImportError:
            sys.exit("Found icon as SVG but cairosvg isn't installed: pip install cairosvg --break-system-packages")
        out.parent.mkdir(parents=True, exist_ok=True)
        cairosvg.svg2png(bytestring=svg_data, write_to=str(out), output_width=512, output_height=512)
        print(f"Saved {out} (Simple Icons, official brand color)")
        return

    domain = args.domain or f"{slug}.com"
    favicon_data = try_favicon(domain)
    if favicon_data:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(favicon_data)
        print(f"Saved {out} (favicon fallback for {domain} — lower quality, verify it looks right)")
        return

    sys.exit(
        f"No icon found for '{args.name}' (tried Simple Icons slug '{slug}' and favicon for '{domain}'). "
        "Pass --domain to try a different domain, or skip the real-icon step and describe it in the Gemini prompt instead."
    )


if __name__ == "__main__":
    main()
