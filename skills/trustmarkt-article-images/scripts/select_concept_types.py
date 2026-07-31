#!/usr/bin/env python3
"""Deterministically pick 3 distinct cover concept types for an article,
by scoring the 5 documented concept types (SKILL.md's "Cover concept
types" list) against simple, auditable signals in the article text —
replacing "Claude reads the article and picks 3 that feel right" with a
scored, reproducible ranking any run will land on consistently.

Signals used (all cheap regex/keyword checks, no NLP model):
  - stat_highlight:    a €/% figure appears in the title or first ~400 chars
  - before_after_split: "vs.", "im Vergleich", "gegenüber", or a contrast
                         framing like "Ungeklärt oder..." in the title
  - tool_composition:   2+ distinct entities were found by extract_entities.py
  - workflow_diagram:   process/step language: "Schritt", "Workflow",
                         numbered list markers, "Prozess"
  - network_hologram:   always given a baseline score as the generic
                         fallback concept, so there's always a 3rd option
                         even for a topic with no other strong signal

Usage:
    python3 select_concept_types.py --title "..." --content-file draft.md --entity-count 2
    -> JSON: ["stat_highlight", "before_after_split", "network_hologram"]
"""
import argparse
import json
import re

CONCEPT_ORDER = ["stat_highlight", "before_after_split", "tool_composition",
                  "workflow_diagram", "network_hologram"]

STAT_RE = re.compile(r"(\d[\d.,]*\s?(%|€|mio\.?|million|milliarden))", re.IGNORECASE)
CONTRAST_RE = re.compile(r"\bvs\.?\b|im vergleich|gegenüber|oder\b.*\?", re.IGNORECASE)
PROCESS_RE = re.compile(r"\bschritt \d|\bworkflow\b|\bprozess\b|\d\.\s+\w+", re.IGNORECASE)


def score(title, content, entity_count):
    head = f"{title} {content[:400]}"
    full = f"{title} {content}"

    scores = {
        "stat_highlight": 2 if STAT_RE.search(head) else (1 if STAT_RE.search(full) else 0),
        "before_after_split": 2 if CONTRAST_RE.search(title) else (1 if CONTRAST_RE.search(full) else 0),
        "tool_composition": min(entity_count, 2),
        "workflow_diagram": 1 if PROCESS_RE.search(full) else 0,
        "network_hologram": 1,  # generic fallback, always available
    }
    return scores


def select_top3(scores):
    ranked = sorted(CONCEPT_ORDER, key=lambda c: (-scores[c], CONCEPT_ORDER.index(c)))
    return ranked[:3]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--title", default="")
    p.add_argument("--content", default=None)
    p.add_argument("--content-file", default=None)
    p.add_argument("--entity-count", type=int, default=0,
                    help="Number of distinct brand/tool entities extract_entities.py found")
    args = p.parse_args()

    content = args.content or ""
    if args.content_file:
        content = open(args.content_file, encoding="utf-8").read()

    scores = score(args.title, content, args.entity_count)
    top3 = select_top3(scores)
    print(json.dumps({"scores": scores, "selected": top3}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
