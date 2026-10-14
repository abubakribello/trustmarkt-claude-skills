#!/usr/bin/env python3
"""Verify a finalized Trustmarkt draft through the API (source of truth after saving).

Usage:
    TRUSTMARKT_API_TOKEN=... python3 verify_draft.py --manifest parsed.json \
        [--article-id ID] [--author "Johannes Kofler"] [--category SEO]

`parsed.json` is the output of parse_manifest.py. Exit code 0 = all checks passed.

Checks: status DRAFT, author, category set (and equal to --category if given), one <figure> per
manifest section image, each directly after its H2, alt == figcaption == manifest caption,
and that the article text (including captions) is German. The cover (Vorschaubild) is not
exposed by the API - verify it in the editor after a reload (see SKILL.md).
"""
import argparse
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request

BASE = os.environ.get("TRUSTMARKT_API_BASE", "https://api.trustmarkt.de/v1")
DE = {"der", "die", "das", "und", "ist", "nicht", "du", "dich", "dein", "deine", "mit", "für", "auf", "ein", "eine", "wie", "wenn", "auch", "zu", "den", "von"}
EN = {"the", "and", "is", "not", "you", "your", "with", "for", "on", "a", "an", "how", "if", "also", "to", "of", "this", "that", "are", "it"}


def get(path, params, token):
    url = BASE + path + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def norm(s):
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


VOID = {"img", "br", "hr", "input", "meta", "link", "source", "wbr"}


def top_level_blocks(content):
    """Return a list of top-level blocks as 'image' or 'other' (paragraph, heading, list, table, ...)."""
    from html.parser import HTMLParser

    class P(HTMLParser):
        def __init__(self):
            super().__init__()
            self.depth, self.blocks = 0, []

        def handle_starttag(self, tag, attrs):
            if self.depth == 0:
                cls = dict(attrs).get("class") or ""
                self.blocks.append("image" if "inline-image" in cls else "other")
            if tag not in VOID:
                self.depth += 1

        def handle_endtag(self, tag):
            if tag not in VOID and self.depth > 0:
                self.depth -= 1

    p = P()
    p.feed(content)
    return p.blocks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--article-id")
    ap.add_argument("--author", default="Johannes Kofler")
    ap.add_argument("--category")
    ap.add_argument("--before", help="API JSON of the article saved BEFORE editing (get-article --expand content > before.json); "
                                     "enables the text-unchanged and bold-preserved checks")
    args = ap.parse_args()
    token = os.environ.get("TRUSTMARKT_API_TOKEN") or sys.exit("TRUSTMARKT_API_TOKEN not set")
    m = json.load(open(args.manifest, encoding="utf-8"))
    aid = args.article_id or m["article_id"] or sys.exit("no article id")
    a = get(f"/articles/{aid}", {"expand": "content,author,category"}, token)
    c = a["content"]
    results = []

    def check(name, ok, detail=""):
        results.append((name, bool(ok), detail))

    check("status is DRAFT", a["status"] == "DRAFT", a["status"])
    check(f"author is {args.author}", (a.get("author") or {}).get("name") == args.author, (a.get("author") or {}).get("name"))
    cat = (a.get("category") or {}).get("name")
    check("category set" + (f" to {args.category}" if args.category else ""),
          cat and (not args.category or cat == args.category), cat)

    blocks = top_level_blocks(c)
    before_first = blocks.index("image") if "image" in blocks else None
    if before_first is not None:
        check("first image has >= 3 blocks before it", before_first >= 3, f"{before_first} block(s) before the first image")

    figs = re.findall(r'<div class="inline-image[^"]*">\s*<figure.*?</figure>\s*</div>', c, re.S)
    check("figure count matches manifest", len(figs) == len(m["sections"]), f"{len(figs)} in article / {len(m['sections'])} in manifest")

    for s in m["sections"]:
        pat = re.compile(r"<h2[^>]*>(.*?)</h2>\s*(<div class=\"inline-image[^\"]*\">\s*<figure.*?</figure>\s*</div>)?", re.S)
        found = None
        for h in pat.finditer(c):
            if norm(re.sub("<[^>]+>", "", h.group(1))) == norm(s["h2"]):
                found = h
                break
        if not found:
            check(f"{s['file']}: H2 exists", False, s["h2"])
            continue
        fig = found.group(2)
        check(f"{s['file']}: image directly after H2 '{s['h2'][:40]}'", bool(fig))
        if fig:
            alt = norm(re.search(r'alt="([^"]*)"', fig).group(1)) if 'alt="' in fig else ""
            cap_m = re.search(r"<figcaption>\s*<p>(.*?)</p>", fig, re.S)
            cap = norm(re.sub("<[^>]+>", "", cap_m.group(1))) if cap_m else ""
            want = norm(s["caption"])
            check(f"{s['file']}: caption == manifest", cap == want, cap[:60])
            if a["status"] == "DRAFT":  # after submission the platform replaces alt with its own generated description
                check(f"{s['file']}: alt == caption", alt == cap, alt[:60])

    if args.before:
        old = json.load(open(args.before, encoding="utf-8"))["content"]
        no_fig = lambda h: re.sub(r'<div class="inline-image.*?</figure>\s*</div>', "", h, flags=re.S)
        plain = lambda h: norm(re.sub(r"<[^>]+>", "", re.sub(r"</(p|li|h[1-6]|div|tr|td|th|ul|ol)>", " ", no_fig(h))))
        check("article text unchanged by editing (images excluded)", plain(old) == plain(c))
        for tag_pair, label in ((("strong", "b"), "bold"), (("em", "i"), "italic")):
            count = lambda h: sum(len(re.findall(rf"<{t}[ >]", no_fig(h))) for t in tag_pair)
            # <i class=...> icons inside callouts are not italics
            if label == "italic":
                count = lambda h: len(re.findall(r"<em[ >]", no_fig(h))) + len(re.findall(r"<i>", no_fig(h)))
            check(f"{label} formatting preserved", count(c) >= count(old), f"{count(old)} before / {count(c)} after")

    text = norm(re.sub("<[^>]+>", " ", c)).lower().split()
    de, en = sum(w in DE for w in text), sum(w in EN for w in text)
    check("article is German (not translated)", de > 3 * max(en, 1), f"german words {de} / english words {en}")

    width = max(len(n) for n, _, _ in results)
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}  {detail}")
    sys.exit(0 if all(ok for _, ok, _ in results) else 1)


if __name__ == "__main__":
    main()
