# n8n workflow: Trustmarkt Article Image Upload

Receives one call per HTTP request from `scripts/upload_to_n8n.py` — create a folder, upload an image, or upload the manifest — and does the corresponding Google Drive operation. `scripts/upload_to_n8n.py`'s docstring has the full field contract.

## Import

1. n8n → Workflows → Import from File → `trustmarkt-article-image-upload.json`.
2. Open all three Google Drive nodes ("Create Article Folder", "Upload Image to Drive", "Upload Manifest to Drive") and select your Google Drive OAuth2 credential (the placeholder `REPLACE_WITH_YOUR_CREDENTIAL_ID` won't resolve on its own).
3. Activate the workflow. Copy its production webhook URL (Webhook node → the `https://<your-domain>/webhook/trustmarkt-article-image` shown after activation) into `N8N_IMAGE_WEBHOOK_URL` wherever the skill runs.
4. Set `N8N_IMAGE_DRIVE_FOLDER_ID` to the shared parent Drive folder new article subfolders get created inside.
5. Test in order: `--create-folder` first (confirm a real subfolder appears in Drive and the script prints `FOLDER_ID=...`), then `--file`/`--manifest` using that returned id, before wiring it into a real article run.

## Current behavior

Each article run creates one subfolder (named after `article_slug`) inside the shared parent folder, then uploads every image plus `manifest.md` into that subfolder. The routine (the skill/script) is responsible for creating the folder first and reusing its id for every subsequent call in that run — the workflow itself doesn't search for or reuse an existing subfolder, so re-running `--create-folder` for the same slug creates a second folder rather than reusing the first one. Not an issue for normal single-pass article runs; worth knowing if you retry a failed run.

## Why a webhook instead of Claude uploading to Drive directly

Passing full-resolution image bytes through a Drive MCP/connector tool call means the bytes get serialized into the model's own context — roughly 100K+ tokens per image, 600K+ for a full article's set. Routing through this webhook keeps the bytes inside `upload_to_n8n.py`'s own HTTP request instead, which costs nothing in model context regardless of whether the skill runs locally or in a cloud routine sandbox with no shared filesystem.
