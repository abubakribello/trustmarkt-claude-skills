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

IMPORTANT — registering locally is not enough on its own. A cloud routine
does a fresh `git clone --depth 1` per BOOTSTRAP.md every run; anything this
script writes to the local working copy is lost when that sandbox is torn
down unless it's pushed back to GitHub. So: if a GITHUB_TOKEN env var is
present (a token scoped to just this repo, contents:write), this script
commits and pushes the updated known-brands.json + new icon file straight
back to whatever branch the sandbox is actually on, so every subsequent
routine run — not just this one — picks up the brand via the fast
dictionary path. Without a token, the registration still works for THIS
run (the calling skill gets a valid icon_path either way) but won't persist
past the current sandbox — this degrades the same way fetch_tool_icon.py
degrades when cairo is missing: warn clearly, never crash the actual run
over it.

Idempotent — safe to call even if the brand may already be registered.

Usage:
    python3 register_brand.py --name "Zapier" --domain zapier.com
    python3 register_brand.py --name "Retool"
    -> prints the icon_path to use immediately in this run's build_cover.py call
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).parent.parent
REPO_ROOT = SKILL_ROOT.parent.parent  # skills/trustmarkt-article-images/../.. -> repo root
DICT_PATH = SKILL_ROOT / "assets" / "known-brands.json"
TOOL_LOGOS_DIR = SKILL_ROOT / "assets" / "tool-logos"


def slugify(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _run_git(args, cwd=REPO_ROOT, env=None):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, env=env)


def _sanitize(text, token):
    """Never let the token leak into anything that gets printed — git error
    messages sometimes echo the remote URL verbatim, which would include it."""
    return text.replace(token, "***") if token else text


def push_registration(name, changed_paths):
    """Best-effort. Returns True if pushed, False otherwise — never raises,
    never blocks the caller from getting a usable icon_path for this run."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print(f"NOTE: GITHUB_TOKEN not set — '{name}' is registered for THIS run only. "
              f"It will need rediscovering next time unless this token is configured.",
              file=sys.stderr)
        return False

    remote_result = _run_git(["config", "--get", "remote.origin.url"])
    remote_url = remote_result.stdout.strip()
    m = re.search(r"github\.com[:/]([^/]+)/([^/.]+)", remote_url)
    if not m:
        print(f"NOTE: couldn't parse owner/repo from remote '{remote_url}' — skipping push-back.",
              file=sys.stderr)
        return False
    owner, repo = m.group(1), m.group(2)

    branch_result = _run_git(["rev-parse", "--abbrev-ref", "HEAD"])
    branch = branch_result.stdout.strip()
    if not branch or branch == "HEAD":
        print("NOTE: detached HEAD or unknown branch — skipping push-back.", file=sys.stderr)
        return False

    auth_url = f"https://{token}@github.com/{owner}/{repo}.git"

    _run_git(["add", *[str(p) for p in changed_paths]])
    commit = _run_git(["commit", "-m", f"Register brand: {name} (auto, by trustmarkt-article-images skill)"])
    if commit.returncode != 0 and "nothing to commit" not in commit.stdout:
        print(f"NOTE: commit failed, skipping push-back: {_sanitize(commit.stderr.strip(), token)[-300:]}",
              file=sys.stderr)
        return False

    for attempt in range(2):
        push = _run_git(["push", auth_url, f"HEAD:{branch}"])
        if push.returncode == 0:
            return True
        if attempt == 0:
            # Likely a concurrent registration from another routine run —
            # fetch + rebase once and retry before giving up.
            _run_git(["fetch", auth_url, branch])
            _run_git(["rebase", "FETCH_HEAD"])

    print(f"NOTE: push-back failed after retry — '{name}' is registered for THIS run only: "
          f"{_sanitize(push.stderr.strip(), token)[-300:]}", file=sys.stderr)
    return False


def register(name, domain=None, push=True):
    dictionary = json.loads(DICT_PATH.read_text(encoding="utf-8"))

    for entry in dictionary.get("brands", []):
        if entry["name"].lower() == name.lower():
            icon_path = TOOL_LOGOS_DIR / entry["icon"]
            if icon_path.exists():
                return str(icon_path), False, False  # already registered, nothing to do

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

    pushed = False
    if push:
        pushed = push_registration(name, [DICT_PATH, icon_path])

    return str(icon_path), True, pushed


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--name", required=True, help="Brand/tool name exactly as it should be matched (case-insensitive)")
    p.add_argument("--domain", default=None, help="Domain for the favicon fallback if Simple Icons doesn't have it (defaults to <slug>.com)")
    p.add_argument("--no-push", action="store_true", help="Register locally only, skip the GITHUB_TOKEN push-back")
    args = p.parse_args()

    icon_path, newly_registered, pushed = register(args.name, args.domain, push=not args.no_push)
    if not newly_registered:
        status = "already registered"
    elif pushed:
        status = "newly registered, pushed to GitHub — persists for all future runs"
    else:
        status = "newly registered for THIS run only — not pushed (see stderr)"
    print(f"{icon_path}  ({status})")


if __name__ == "__main__":
    main()
