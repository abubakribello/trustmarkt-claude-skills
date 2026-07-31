#!/usr/bin/env python3
"""Deterministically pick a real photo from the named pose library
(assets/headshots/real-photos/johannes-<mood>-<pose>-NN.png) to match a
cover concept's intended emotional register — replacing "Claude picks
whichever filename looks right" with a fixed concept->mood-keyword
mapping and a reproducible tie-break (alphabetical), plus a per-article
no-repeat constraint so the 3 covers don't reuse the same photo.

Usage:
    python3 select_pose.py --concept stat_highlight --already-used a.png b.png
    -> prints the chosen photo's absolute path
"""
import argparse
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).parent.parent
POSE_DIR = SKILL_ROOT / "assets" / "headshots" / "real-photos"

# Concept type -> ordered list of mood keywords to try, most-specific first.
# Extend this mapping (not the calling code) when a new concept type is added.
CONCEPT_MOODS = {
    "stat_highlight": ["frowning-serious", "serious", "skeptical"],
    "before_after_split": ["skeptical", "thinking", "serious"],
    "tool_composition": ["serious", "thinking", "confident"],
    "workflow_diagram": ["serious", "confident", "thinking"],
    "network_hologram": ["serious", "thinking", "skeptical"],
}


def select(concept, already_used, pose_dir=POSE_DIR):
    if not pose_dir.exists():
        sys.exit(f"Pose library not found: {pose_dir}")
    candidates = sorted(p.name for p in pose_dir.glob("johannes-*.png"))
    already_used = set(already_used or [])

    moods = CONCEPT_MOODS.get(concept, ["serious"])
    for mood in moods:
        matches = [c for c in candidates if mood in c and c not in already_used]
        if matches:
            return str(pose_dir / matches[0])

    # Nothing unused matched any mood keyword for this concept — fall back
    # to any unused photo at all, rather than failing the whole run.
    unused = [c for c in candidates if c not in already_used]
    if unused:
        return str(pose_dir / unused[0])

    sys.exit(f"No unused pose photos left in {pose_dir} (all {len(candidates)} already used this run).")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--concept", required=True, choices=list(CONCEPT_MOODS.keys()))
    p.add_argument("--already-used", nargs="*", default=[], help="Filenames (not full paths) already picked this run")
    args = p.parse_args()
    print(select(args.concept, args.already_used))


if __name__ == "__main__":
    main()
