#!/usr/bin/env python3
"""Gate the one genuinely creative input in this pipeline (the headline
text, which needs real summarization and can't be reduced to a keyword
rule) with hard, deterministic checks — so a bad headline fails loudly
before rendering instead of silently shipping.

Usage:
    python3 validate_headline.py --text "35 MIO. €" --concept stat_highlight
    Exit code 0 = valid. Non-zero + message on stderr = invalid, fix and retry.
"""
import argparse
import re
import sys

MAX_WORDS = 6
MAX_CHARS = 40
HAS_DIGIT_RE = re.compile(r"\d")
HAS_CURRENCY_OR_PCT_RE = re.compile(r"%|€")
GERMAN_HINT_RE = re.compile(r"[äöüßÄÖÜ]|ß|CHECK|KONFORM|GÜNSTIG|RECHNET|RISIKO|KOSTEN", re.IGNORECASE)


def validate(text, concept):
    errors = []
    words = text.split()
    if len(words) > MAX_WORDS:
        errors.append(f"too many words ({len(words)} > {MAX_WORDS}): '{text}'")
    if len(text) > MAX_CHARS:
        errors.append(f"too long ({len(text)} chars > {MAX_CHARS}): '{text}'")
    if concept == "stat_highlight" and not (HAS_DIGIT_RE.search(text) and HAS_CURRENCY_OR_PCT_RE.search(text)):
        errors.append(f"concept is stat_highlight but no €/% figure found in: '{text}'")
    if not text.isupper():
        errors.append(f"headline should be ALL CAPS for the display-text style: '{text}'")
    return errors


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--text", required=True)
    p.add_argument("--concept", default=None)
    args = p.parse_args()

    errors = validate(args.text, args.concept)
    if errors:
        for e in errors:
            print(f"INVALID: {e}", file=sys.stderr)
        sys.exit(1)
    print("OK")


if __name__ == "__main__":
    main()
