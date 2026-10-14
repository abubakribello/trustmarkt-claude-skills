#!/usr/bin/env python3
"""Parse a trustmarkt-article-images manifest.md into JSON for the draft finalizer.

Usage:
    python3 parse_manifest.py MANIFEST.md [--images-dir ~/Downloads]

Output JSON: {article_id, slug, covers: [{file, label, caption, path, caption_len}],
              sections: [{file, h2, caption, path}], warnings: [...]}

Image files are looked up as <images-dir>/<slug>__<file> first, then <images-dir>/<file>.
Only the table format is supported (Datei | ... | Bildunterschrift). The older bullet-list
manifests have no captions and are rejected.
"""
import argparse
import json
import re
import sys
from pathlib import Path

COVER_CAPTION_MAX = 90


def split_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse_tables(text):
    sections, current, header = {}, None, None
    for line in text.splitlines():
        if line.startswith("## "):
            current, header = line[3:].strip().lower(), None
            sections[current] = []
        elif current and line.strip().startswith("|"):
            cells = split_row(line)
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                continue
            if header is None:
                header = [c.lower() for c in cells]
            else:
                sections[current].append(dict(zip(header, cells)))
    return sections


def pick(row, *needles):
    for key, value in row.items():
        if any(n in key for n in needles):
            return value
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--images-dir", default=str(Path.home() / "Downloads"))
    args = ap.parse_args()

    text = Path(args.manifest).read_text(encoding="utf-8")
    id_m = re.search(r"Artikel-ID:\**\s*`?([A-Za-z0-9]{20})", text)
    slug_m = re.search(r"Slug:\**\s*`?([a-z0-9-]+)", text)
    slug = slug_m.group(1) if slug_m else Path(args.manifest).name.split("__")[0]
    tables = parse_tables(text)
    if not tables:
        sys.exit("No tables found - old bullet-list manifests are not supported; regenerate the manifest.")

    images = Path(args.images_dir).expanduser()
    warnings = []

    def resolve(name):
        for cand in (images / f"{slug}__{name}", images / name):
            if cand.exists():
                return str(cand)
        warnings.append(f"image file not found: {name} (looked in {images})")
        return None

    covers, sections = [], []
    for title, rows in tables.items():
        for row in rows:
            file = pick(row, "datei")
            caption = pick(row, "bildunterschrift", "caption")
            if title.startswith("cover"):
                if len(caption) > COVER_CAPTION_MAX:
                    warnings.append(f"{file}: cover caption is {len(caption)} chars, the editor allows max {COVER_CAPTION_MAX} - needs a shorter version")
                covers.append({"file": file, "label": pick(row, "template", "konzept"), "caption": caption,
                               "caption_len": len(caption), "path": resolve(file)})
            elif title.startswith("section"):
                sections.append({"file": file, "h2": pick(row, "h2"), "caption": caption, "path": resolve(file)})

    if not sections:
        warnings.append("no section rows found")
    print(json.dumps({"article_id": id_m.group(1) if id_m else None, "slug": slug,
                      "covers": covers, "sections": sections, "warnings": warnings},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
