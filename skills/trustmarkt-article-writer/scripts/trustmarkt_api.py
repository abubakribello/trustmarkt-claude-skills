#!/usr/bin/env python3
"""Trustmarkt API helper (https://api.trustmarkt.de/v1).

Auth: TRUSTMARKT_API_TOKEN env var or --token.

Commands:
  me                                       Authenticated user + company
  list-articles [--search X] [--page N]    List company articles
  get-article --id ID [--expand content]   Show one article
  create-article --title T (--content-file F | --content S)
                 [--author-id A] [--category-id C] [--thumbnail-alt ALT]
  update-article --id ID [--title T] [--content-file F | --content S] ...
  list-reviews [--page N]                  List company reviews
  get-review --id ID                       Show one review
  list-case-studies [--search X] [--page N]
  get-case-study --id ID [--expand "review, content"]
  list-inquiries [--page N]
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = os.environ.get("TRUSTMARKT_API_BASE", "https://api.trustmarkt.de/v1")

MD_LINK_RE = re.compile(r"\[[^\]]+\]\((https?://[^\s)]+)\)")


def request(method, path, token, params=None, body=None, retry_429=True):
    url = BASE + path
    if params:
        url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        payload = e.read().decode(errors="replace")
        if e.code == 429 and retry_429:
            sys.stderr.write("429 rate limited - waiting 30s, retrying once...\n")
            time.sleep(30)
            return request(method, path, token, params, body, retry_429=False)
        try:
            payload = json.dumps(json.loads(payload), indent=2, ensure_ascii=False)
        except (json.JSONDecodeError, ValueError):
            pass
        sys.exit(f"HTTP {e.code} {method} {path}\n{payload}")
    except urllib.error.URLError as e:
        sys.exit(f"Network error: {e.reason}")


def check_directive_fences(content):
    """Container directives (:::callout, :::faq, ...) must be closed with a bare
    ':::' line. An unclosed block is NOT rejected by the API - it silently ships
    and renders as literal ':::callout ...' text instead of a styled box, which
    is only visible after the article is rendered. Catch it here instead.

    Convention (remark-directive): a line whose stripped form is ':::<name>...'
    opens a block; a line that is exactly ':::' closes the innermost open block.
    """
    errors = []
    open_stack = []  # (line_number, directive_line)
    for lineno, line in enumerate(content.splitlines(), 1):
        s = line.strip()
        if s == ":::":
            if open_stack:
                open_stack.pop()
            else:
                errors.append(f"line {lineno}: a closing ':::' has no matching open directive above it")
        elif s.startswith(":::") and len(s) > 3:
            open_stack.append((lineno, s))
    for lineno, directive in open_stack:
        name = directive[3:].split()[0] if len(directive) > 3 else ""
        errors.append(
            f"line {lineno}: directive '{directive}' is never closed - add a line "
            f"containing only ':::' after its body (an unclosed :::{name} renders "
            f"as literal text, not a styled block)"
        )
    return errors


def validate_article(title, content):
    errors = []
    if title is not None and not (10 <= len(title) <= 90):
        errors.append(f"title must be 10-90 chars (got {len(title)})")
    if content is not None:
        if len(content) > 50000:
            errors.append(f"content max 50000 chars (got {len(content)})")
        if "<" in content and ">" in content:
            if re.search(r"<[a-zA-Z][^>]*>", content):
                errors.append("content appears to contain HTML tags - they will be stripped; use Markdown only")
        if content.lstrip().startswith("# "):
            errors.append("content starts with an H1 - the title is the H1; start with intro text and use ## sections")
        if "![" in content:
            errors.append("images are not supported via API - remove image Markdown, add images in the web editor")
        link_urls = MD_LINK_RE.findall(content)
        counts = {}
        for u in link_urls:
            counts[u] = counts.get(u, 0) + 1
        dupes = [u for u, c in counts.items() if c > 1]
        if dupes:
            details = ", ".join(f"{u} (used {counts[u]}x)" for u in dupes)
            errors.append(f"the same link URL is used more than once: {details} - each link in the article must point to a different URL")
        errors.extend(check_directive_fences(content))
    if errors:
        sys.exit("Validation failed:\n- " + "\n- ".join(errors))


def read_content(args):
    if getattr(args, "content_file", None):
        with open(args.content_file, encoding="utf-8") as f:
            return f.read()
    return getattr(args, "content", None)


def out(data):
    print(json.dumps(data, indent=2, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--token", default=os.environ.get("TRUSTMARKT_API_TOKEN"))
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("me")

    def paged(name):
        s = sub.add_parser(name)
        s.add_argument("--page", type=int)
        s.add_argument("--per-page", type=int)
        s.add_argument("--search")
        s.add_argument("--expand")
        return s

    paged("list-articles")
    paged("list-reviews")
    paged("list-case-studies")
    paged("list-inquiries")

    for name in ("get-article", "get-review", "get-case-study"):
        s = sub.add_parser(name)
        s.add_argument("--id", required=True)
        s.add_argument("--expand")

    ca = sub.add_parser("create-article")
    ca.add_argument("--title", required=True)
    ca.add_argument("--content")
    ca.add_argument("--content-file")
    ca.add_argument("--author-id")
    ca.add_argument("--category-id")
    ca.add_argument("--thumbnail-alt")

    ua = sub.add_parser("update-article")
    ua.add_argument("--id", required=True)
    ua.add_argument("--title")
    ua.add_argument("--content")
    ua.add_argument("--content-file")
    ua.add_argument("--author-id")
    ua.add_argument("--category-id")
    ua.add_argument("--thumbnail-alt")

    args = p.parse_args()
    if not args.token:
        sys.exit("No token. Set TRUSTMARKT_API_TOKEN or pass --token.")
    t = args.token

    if args.cmd == "me":
        out(request("GET", "/me", t))
    elif args.cmd in ("list-articles", "list-reviews", "list-case-studies", "list-inquiries"):
        path = "/" + args.cmd.replace("list-", "")
        out(request("GET", path, t, params={
            "page": args.page, "per_page": args.per_page,
            "search": args.search, "expand": args.expand}))
    elif args.cmd in ("get-article", "get-review", "get-case-study"):
        res = args.cmd.replace("get-", "")
        plural = {"article": "articles", "review": "reviews", "case-study": "case-studies"}[res]
        out(request("GET", f"/{plural}/{args.id}", t, params={"expand": args.expand}))
    elif args.cmd == "create-article":
        content = read_content(args)
        validate_article(args.title, content)
        body = {"title": args.title}
        for key, val in (("content", content), ("author_id", args.author_id),
                         ("category_id", args.category_id), ("thumbnail_alt", args.thumbnail_alt)):
            if val is not None:
                body[key] = val
        result = request("POST", "/articles", t, body=body)
        out(result)
        sys.stderr.write(f"\nCreated article id={result.get('id')} status={result.get('status')} slug={result.get('slug')}\n"
                         "Note: add images and submit for review in the Trustmarkt web editor.\n")
    elif args.cmd == "update-article":
        content = read_content(args)
        validate_article(args.title, content)
        body = {}
        for key, val in (("title", args.title), ("content", content), ("author_id", args.author_id),
                         ("category_id", args.category_id), ("thumbnail_alt", args.thumbnail_alt)):
            if val is not None:
                body[key] = val
        if not body:
            sys.exit("Nothing to update - pass --title and/or --content(-file).")
        out(request("PUT", f"/articles/{args.id}", t, body=body))


if __name__ == "__main__":
    main()
