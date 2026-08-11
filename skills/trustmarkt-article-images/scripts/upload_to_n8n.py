#!/usr/bin/env python3
"""Push article images to an n8n webhook, which handles Google Drive.
Runs after the local self-check/regen loop in SKILL.md — only images
that already passed verification should be sent here.

Three calls per article, in order:
  1. --create-folder   once, to create a subfolder for this article
                        inside the shared parent folder; prints the new
                        folder's id so the caller can reuse it below
  2. --file             once per verified image, using the folder id
                        from step 1 as --folder-id
  3. --manifest         once, same folder id

No third-party dependencies (stdlib only), so this works in any sandbox
without a pip install step.

Usage:
    # 1. create the per-article folder (parent = shared drive folder)
    python3 upload_to_n8n.py --webhook-url "$N8N_IMAGE_WEBHOOK_URL" \
        --create-folder --article-slug <slug> \
        --folder-id "$N8N_IMAGE_DRIVE_FOLDER_ID"
    # -> prints "FOLDER_ID=<new id>" on success; capture it and use as
    #    --folder-id for every call below instead of the parent id

    # 2. image, once per verified file
    python3 upload_to_n8n.py --webhook-url "$N8N_IMAGE_WEBHOOK_URL" \
        --file workspace/<slug>/cover-v1.png \
        --article-slug <slug> --filename cover-v1.png \
        --image-type cover --order 1 \
        --caption "Mini-SaaS statt Chaos: ein Prompt, eine App." \
        --folder-id "<new id from step 1>"

    # 3. manifest (plain markdown, no binary)
    python3 upload_to_n8n.py --webhook-url "$N8N_IMAGE_WEBHOOK_URL" \
        --manifest workspace/<slug>/manifest.md \
        --article-slug <slug> --folder-id "<new id from step 1>"

Environment: N8N_IMAGE_WEBHOOK_URL, N8N_IMAGE_DRIVE_FOLDER_ID (both can
also be passed as flags).

Webhook contract (multipart/form-data):
  type            "create_folder" | "image" | "manifest"
  folder_id       create_folder: parent folder id to create the article
                   subfolder inside. image/manifest: the target folder
                   to upload into (normally the subfolder id returned
                   by a prior create_folder call)
  article_slug    create_folder: name of the subfolder to create
  filename        target filename in Drive (image mode only)
  image_type      "cover" | "section" (image mode only)
  order           int, position within its group (image mode only)
  insert_after_h2 heading text this section image follows (section only)
  caption         German caption text
  markdown        manifest content (manifest mode only)
  image           binary file part (image mode only)

Response (JSON): {"ok": true, "id": "<drive id>", "name": "<drive name>"}
  create_folder: id/name are the new subfolder's.
  image/manifest: id/name are the uploaded file's.
"""
import argparse
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
import uuid


def build_multipart(fields, file_field=None, file_path=None):
    boundary = uuid.uuid4().hex
    parts = []
    for name, value in fields.items():
        if value is None:
            continue
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()
        )
    if file_field and file_path:
        ctype = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
        with open(file_path, "rb") as f:
            data = f.read()
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{file_field}"; '
            f'filename="{os.path.basename(file_path)}"\r\nContent-Type: {ctype}\r\n\r\n'.encode()
            + data
            + b"\r\n"
        )
    parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(parts)
    return body, f"multipart/form-data; boundary={boundary}"


def post(webhook_url, body, content_type):
    req = urllib.request.Request(webhook_url, data=body, method="POST", headers={
        "Content-Type": content_type,
        "Content-Length": str(len(body)),
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, resp.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--webhook-url", default=os.environ.get("N8N_IMAGE_WEBHOOK_URL"))
    p.add_argument("--folder-id", default=os.environ.get("N8N_IMAGE_DRIVE_FOLDER_ID"))
    p.add_argument("--article-slug", required=True)
    p.add_argument("--caption", default="")

    p.add_argument("--file", help="Verified image file to upload")
    p.add_argument("--filename", help="Target filename in Drive (image mode)")
    p.add_argument("--image-type", choices=["cover", "section"])
    p.add_argument("--order", type=int)
    p.add_argument("--insert-after-h2", default=None)

    p.add_argument("--manifest", help="manifest.md path to send instead of an image")
    p.add_argument("--create-folder", action="store_true",
                    help="Create a subfolder named --article-slug inside --folder-id (the parent); prints FOLDER_ID=<new id>")
    args = p.parse_args()

    if not args.webhook_url:
        sys.exit("No webhook URL: pass --webhook-url or set N8N_IMAGE_WEBHOOK_URL.")
    if not args.folder_id:
        sys.exit("No Drive folder id: pass --folder-id or set N8N_IMAGE_DRIVE_FOLDER_ID.")
    modes = [bool(args.file), bool(args.manifest), args.create_folder]
    if sum(modes) != 1:
        sys.exit("Pass exactly one of --create-folder, --file (verified image), or --manifest.")

    fields = {
        "folder_id": args.folder_id,
        "article_slug": args.article_slug,
        "caption": args.caption,
    }

    if args.create_folder:
        fields["type"] = "create_folder"
        body, content_type = build_multipart(fields)
        label = f"folder for {args.article_slug}"
    elif args.manifest:
        if not os.path.exists(args.manifest):
            sys.exit(f"Manifest not found: {args.manifest}")
        fields["type"] = "manifest"
        with open(args.manifest, "r", encoding="utf-8") as f:
            fields["markdown"] = f.read()
        body, content_type = build_multipart(fields)
        label = args.manifest
    else:
        if not os.path.exists(args.file):
            sys.exit(f"Image not found: {args.file}")
        if not args.filename or not args.image_type:
            sys.exit("--filename and --image-type are required in image mode.")
        fields["type"] = "image"
        fields["filename"] = args.filename
        fields["image_type"] = args.image_type
        fields["order"] = args.order
        fields["insert_after_h2"] = args.insert_after_h2
        body, content_type = build_multipart(fields, file_field="image", file_path=args.file)
        label = args.filename

    status, text = post(args.webhook_url, body, content_type)
    if not (200 <= status < 300):
        sys.exit(f"Webhook returned {status}: {text[:500]}")

    print(f"OK ({status}): {label} -> {args.webhook_url}")
    if args.create_folder:
        try:
            new_id = json.loads(text)["id"]
        except (json.JSONDecodeError, KeyError):
            sys.exit(f"create_folder succeeded but response had no usable id: {text[:500]}")
        print(f"FOLDER_ID={new_id}")


if __name__ == "__main__":
    main()
