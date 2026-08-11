#!/usr/bin/env python3
"""Deterministically detect which named brands/tools/institutions an
article actually mentions, and resolve each to a real icon asset —
replacing "Claude reads the article and decides which logos matter"
(the step that silently skipped Make.com's logo in an earlier run) with
a keyword lookup against a maintained, extensible dictionary
(assets/known-brands.json).

IMPORTANT — the dictionary lookup only knows what it's been taught. A
brand mentioned for the first time in a new article returns nothing from
`found`, same as the old silent-miss failure mode, just relocated. To
catch that case, this script ALSO runs a cheap heuristic scan for
brand-like names not yet in the dictionary (CamelCase words, ALLCAPS
2-6 letter acronyms, word+domain-suffix patterns, and repeated
capitalized words filtered against a German stopword list) and returns
them separately as `unlisted_candidates` — NOT auto-trusted as a logo
(false positives are likely, especially in German where all nouns
capitalize), but impossible to silently miss. If a real brand shows up
there, add it to known-brands.json before generating covers; don't let
Gemini guess the logo instead.

Usage:
    python3 extract_entities.py --title "..." --content-file draft.md
    -> JSON: {"found": [{"name", "icon_path", "type"}, ...],
              "unlisted_candidates": ["SomeNewTool", ...]}
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).parent.parent
DICT_PATH = SKILL_ROOT / "assets" / "known-brands.json"

# Common capitalized German words that would otherwise false-positive as
# "brand candidates" purely because German capitalizes every noun. Not
# exhaustive — extend if a run keeps flagging the same ordinary word.
GERMAN_STOPWORDS = {
    "der", "die", "das", "und", "oder", "wenn", "dann", "aber", "auch",
    "nicht", "kein", "eine", "einen", "einer", "einem", "dein", "dies",
    "team", "kunde", "kunden", "kundin", "unternehmen", "agentur",
    "agenturen", "beispiel", "ergebnis", "ergebnisse", "kosten", "zeit",
    "tag", "tage", "woche", "monat", "monate", "jahr", "jahre", "prozess",
    "prozesse", "lösung", "lösungen", "problem", "probleme", "frage",
    "fragen", "antwort", "chat", "chats", "daten", "plan", "pläne",
    "tool", "tools", "system", "systeme", "workflow", "workflows",
    "fazit", "achtung", "hinweis", "profi-tipp", "kernbotschaft",
}
CAMEL_CASE_RE = re.compile(r"\b[A-Z][a-z]+[A-Z][A-Za-z]*\b")
ACRONYM_RE = re.compile(r"\b[A-Z]{2,6}\b")
DOMAIN_RE = re.compile(r"\b([A-Z][A-Za-z0-9]+)\.(com|de|ai|io|app)\b")
CAPITALIZED_WORD_RE = re.compile(r"(?<![.!?]\s)(?<!^)\b([A-ZÄÖÜ][a-zäöüß]{2,})\b")
COMMON_ACRONYM_ALLOWLIST = {"DSGVO", "KI", "SEO", "CRM", "API", "AVV", "AI", "EU", "SCC", "ZDR", "FAQ", "CTA", "B2B", "B2C"}


def load_dictionary():
    return json.loads(DICT_PATH.read_text(encoding="utf-8"))


def _ensure_fetched(entry, tool_logos_dir):
    icon_path = tool_logos_dir / entry["icon"]
    if icon_path.exists():
        return str(icon_path)
    fetch_script = SKILL_ROOT / "scripts" / "fetch_tool_icon.py"
    cmd = [sys.executable, str(fetch_script), "--name", entry["fetch_name"], "--out", str(icon_path)]
    if entry.get("fetch_domain"):
        cmd += ["--domain", entry["fetch_domain"]]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not icon_path.exists():
        print(f"WARNING: could not fetch icon for {entry['name']}: {result.stderr.strip()[-300:]}", file=sys.stderr)
        return None
    return str(icon_path)


def extract(text, dictionary):
    text_lower = f" {text.lower()} "
    found = []

    tool_logos_dir = SKILL_ROOT / "assets" / "tool-logos"
    institutional_dir = SKILL_ROOT / "assets" / "institutional-logos"

    for entry in dictionary.get("brands", []):
        if any(kw.lower() in text_lower for kw in entry["keywords"]):
            icon_path = _ensure_fetched(entry, tool_logos_dir)
            if icon_path:
                found.append({"name": entry["name"], "icon_path": icon_path, "type": "tool"})

    for entry in dictionary.get("institutional", []):
        if any(kw.lower() in text_lower for kw in entry["keywords"]):
            icon_path = institutional_dir / entry["icon"]
            if icon_path.exists():
                found.append({"name": entry["name"], "icon_path": str(icon_path), "type": "institutional"})
            else:
                print(f"WARNING: institutional icon missing on disk: {icon_path}", file=sys.stderr)

    return found


def detect_unlisted_candidates(text, dictionary, min_repeats=2):
    """Heuristic-only, deliberately noisy toward over-flagging rather than
    silently missing a real brand. Not a full NER model — a cheap net."""
    already_known_names = {e["name"].lower() for e in dictionary.get("brands", [])} | \
                           {e["name"].lower() for e in dictionary.get("institutional", [])}

    candidates = {}

    for m in CAMEL_CASE_RE.finditer(text):
        candidates.setdefault(m.group(), 0)
        candidates[m.group()] += 10  # strong signal, don't require repeats

    for m in DOMAIN_RE.finditer(text):
        candidates.setdefault(m.group(1), 0)
        candidates[m.group(1)] += 10

    for m in ACRONYM_RE.finditer(text):
        word = m.group()
        if word in COMMON_ACRONYM_ALLOWLIST:
            continue
        candidates.setdefault(word, 0)
        candidates[word] += 1

    for m in CAPITALIZED_WORD_RE.finditer(text):
        word = m.group(1)
        if word.lower() in GERMAN_STOPWORDS:
            continue
        candidates.setdefault(word, 0)
        candidates[word] += 1

    out = []
    for word, score in candidates.items():
        if word.lower() in already_known_names:
            continue
        if score >= 10 or score >= min_repeats:
            out.append(word)
    return sorted(set(out))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--title", default="")
    p.add_argument("--content", default=None)
    p.add_argument("--content-file", default=None)
    args = p.parse_args()

    content = args.content or ""
    if args.content_file:
        content = Path(args.content_file).read_text(encoding="utf-8")

    full_text = f"{args.title} {content}"
    dictionary = load_dictionary()
    found = extract(full_text, dictionary)
    unlisted = detect_unlisted_candidates(full_text, dictionary)
    print(json.dumps({"found": found, "unlisted_candidates": unlisted}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
