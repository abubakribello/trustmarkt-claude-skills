#!/usr/bin/env python3
"""Fetch a brand's icon AND permanently register it in known-brands.json —
turning the dictionary into a self-growing cache instead of a hand-maintained
list. This matters because this skill is packaged and distributed (pushed to
GitHub for others to run); nobody downstream is going to remember to hand-edit
a JSON file every time an article mentions a tool that hasn't come up before.

The reliable detector for "does this article mention a brand we don't know
about yet" is NOT a regex heuristic (extract_entities.py's unlisted_candidates
is a supplementary, imperfect safety net — it demonstrably misses cases, e.g.
a brand only ever mentioned at the start of a sentence). It's the Claude
session reading the article, which is what SKILL.md requires as a mandatory
step. This script is what that step calls the FIRST time a given brand shows
up; every subsequent article mentioning the same brand hits the fast
dictionary lookup in extract_entities.py instead and never needs this again.

Idempotent — safe to call even if the brand may already be registered.

Usage:
    python3 register_brand.py --name "Zapier" --domain zapier.com
    python3 register_brand.py --name "Retool"
    -> prints the icon_path to use immediately in this run's build_cover.py call
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).parent.parent
DICT_PATH = SKILL_ROOT / "assets" / "known-brands.json"
TOOL_LOGOS_DIR = SKILL_ROOT / "assets" / "tool-logos"


def slugify(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


def register(name, domain=None):
    dictionary = json.loads(DICT_PATH.read_text(encoding="utf-8"))

    for entry in dictionary.get("brands", []):
        if entry["name"].lower() == name.lower():
            icon_path = TOOL_LOGOS_DIR / entry["icon"]
            if icon_path.exists():
                return str(icon_path), False  # already registered, nothing to do

    slug = slugify(name)
    icon_filename = f"{slug}.png"
    icon_path = TOOL_LOGOS_DIR / icon_filename

    fetch_script = SKILL_ROOT / "scripts" / "fetch_tool_icon.py"
    cmd = [sys.executable, str(fetch_script), "--name", name, "--out", str(icon_path)]
    if domain:
        cmd += ["--domain", domain]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not icon_path.exists():
        sys.exit(f"Could not fetch an icon for '{name}': {result.stderr.strip()[-500:]}\n"
                  f"This brand cannot be auto-registered — either it has no discoverable "
                  f"favicon/Simple-Icons entry, or the domain guess was wrong. Pass --domain "
                  f"explicitly, or fall back to describing it in the cover prompt without a logo.")

    entry = {
        "name": name,
        "keywords": [name.lower()],
        "icon": icon_filename,
        "fetch_name": name,
        "type": "tool",
    }
    if domain:
        entry["fetch_domain"] = domain

    already = [e for e in dictionary.get("brands", []) if e["name"].lower() == name.lower()]
    if not already:
        dictionary.setdefault("brands", []).append(entry)
        DICT_PATH.write_text(json.dumps(dictionary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return str(icon_path), True


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--name", required=True, help="Brand/tool name exactly as it should be matched (case-insensitive)")
    p.add_argument("--domain", default=None, help="Domain for the favicon fallback if Simple Icons doesn't have it (defaults to <slug>.com)")
    args = p.parse_args()

    icon_path, newly_registered = register(args.name, args.domain)
    status = "newly registered" if newly_registered else "already registered"
    print(f"{icon_path}  ({status})")


if __name__ == "__main__":
    main()
