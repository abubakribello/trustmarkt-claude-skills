---
name: trustmarkt-draft-finalizer
description: Finalize a Trustmarkt/Agenturmarkt article DRAFT in the web editor (app.trustmarkt.de) - insert all section images under their H2s with captions, set the cover (Vorschaubild) and its caption, choose the category, switch the author to Johannes Kofler, and save as draft (never publish). Use this skill whenever the user asks to add images to a draft, finish/finalise a draft, upload the cover or section images, set category/author, or says "do the manifest" for an article that already exists as a draft - typically right after trustmarkt-article-images has produced the images and manifest.
---

# Trustmarkt Draft Finalizer

The Trustmarkt API cannot handle images, covers, category or author changes in the editor flow, so this skill does them in the **real Chrome** (Claude in Chrome extension), where the user is logged in to app.trustmarkt.de. Source of truth for what to insert is the article's `manifest.md` (from `trustmarkt-article-images`). Result: a saved **DRAFT** that the user reviews and submits themselves.

**Never click "Artikel veröffentlichen".** Finalizing ends at "Entwurf sichern". Submitting is the user's decision.

## Inputs

| Needed | From | If missing |
|---|---|---|
| Manifest `.md` + the image files | Usually `~/Downloads/<slug>__manifest.md` and `<slug>__section-N.png` / `__cover-vN.png` (a Drive download). `file_upload` can read `~/Downloads` and `~/Documents` | Ask where they are |
| Cover variant (v1/v2/v3) | The user - picking the cover is Johannes's call | Ask. Never choose silently for a real run |
| Category | The user's words. List: Automatisierung, Branding, Buchhaltung, Business, Compliance, Content Marketing, E-Commerce, Finanzen, Kommunikation, Marketing, News, Personalführung, Personalmanagement, Ratgeber, Recruiting, SEO, Social Media, Technologie & KI, Vertrieb | Ask (suggest the closest by topic) |
| Author | Default **Johannes Kofler** (drafts are created under Abubakri) | - |

Needs: Claude in Chrome connected to a Chrome profile that is logged in to Trustmarkt (`list_connected_browsers` must not be empty), and `TRUSTMARKT_API_TOKEN` for verification. Load the chrome tools in one ToolSearch call (see the chrome-browser skill) plus `browser_batch`, `file_upload`, `find`, `javascript_tool`.

## Hard rules

1. **Language guard first, every time.** Chrome auto-translate rewrites the editor DOM into English and saving then stores English text (this is what got six articles rejected). Run `__tm.guard()`; it must return `lang: "de"` and no `translated` class. If not: stop, ask the user to turn off translation for app.trustmarkt.de ("Never translate this site") and reload. Never edit or save in a translated tab.
2. **Text must be final before images.** `update-article` (API) replaces the whole content and wipes inserted images. Do not call it after images are in.
3. **An image goes in the block directly after its H2 heading** ("Einfügen nach H2"), not after the following paragraph.
4. **Caption = figcaption AND alt** (one field) while the article is a DRAFT. Use the manifest caption character for character, including the final period. (After the article is submitted the platform replaces the alt with its own generated description, so alt == caption only holds for drafts.)
5. **Cover caption max 90 characters** (inclusive; exactly 90 is fine) - the editor refuses to save longer ones ("Maximal 90 Zeichen."). Manifest cover captions are often longer (up to 132 so far). The only allowed fix is a faithful shortening that keeps the meaning (no new claims, no dropped numbers), applied only to the chosen cover and listed in the report as original vs. shortened (with both lengths) - or leave the cover caption empty and say so, if the user prefers. `parse_manifest.py` warns about over-limit captions; `__tm.coverCaption()` refuses them.
5b. **The first image needs at least 3 blocks before it** (2+ intro paragraphs plus the first H2 heading, counted as editor blocks). `__tm.bildAfterH2()` refuses to place a first image earlier and `verify_draft.py` fails the draft if it happens. If a manifest anchors section-1 to an H2 that is too early, stop and tell the user - do not move the image elsewhere on your own.
6. Never use a native file dialog (Claude cannot see or operate it; computer use cannot control Claude's own window). Use the input-capture hook + `file_upload`.
7. Keep each `javascript_tool` call short (<25 s). Poll long waits in separate calls. Use refs/DOM, not screen coordinates: the window size changes between screenshots, so coordinates drift.
8. One draft at a time. Do not run two editors on the same draft.
9. Check every step's result before the next one. If it does not match, stop and report instead of retrying blindly (max 2 attempts per step).
10. **Saving through the editor silently strips bold.** Editor.js's sanitizer drops `<strong>` (there is no bold tool in this editor), so any `**bold**` written via the API vanishes on the first editor save (6 bold passages lost in the first real run). Before every save run `__tm.preserveFormatting()` (turns `<strong>`→`<b>`, which survives), and verify with `verify_draft.py --before`. Links and `<i>` icons are not affected.

## Workflow

### 1. Prepare
**Get the images on disk** (skip if they are already in a readable folder such as the local `trustmarkt-article-images/workspace/<slug>/`). From Drive, without pushing bytes through the model: find the file ids with the Drive connector (`search_files`: `title contains '<slug>' and mimeType contains 'image/'`), then in the **Chrome** tab navigate to `https://drive.google.com/uc?export=download&id=<fileId>` for each file - it downloads to `~/Downloads` under its Drive name (`<slug>__section-1.png` ...). Check each size against `fileSize` from the search result. Never use the connector's `download_file_content` for images (base64 through the model's context, ~100K+ tokens each). Needs a Chrome profile signed in to a Google account that can open the Drive folder. Drive files can be JPEG data named `.png`; the editor accepts it.
```bash
python3 scripts/parse_manifest.py ~/Downloads/<slug>__manifest.md > /tmp/parsed.json
curl -s -H "Authorization: Bearer $TRUSTMARKT_API_TOKEN" "https://api.trustmarkt.de/v1/articles/<id>?expand=content" > /tmp/before.json   # snapshot BEFORE editing
```
Output lists covers, section rows (file, H2, caption, resolved path) and `warnings` (missing files, cover caption >90). Resolve warnings with the user before touching the editor. Old bullet-list manifests are rejected (no captions) - regenerate them.

### 2. Open the draft
`tabs_context_mcp` -> new tab (or the user's draft tab if they ask) -> `navigate` to `https://app.trustmarkt.de/artikel/<articleId>`. The user must already be logged in; never sign in. Load `scripts/editor_helpers.js` once per page load (paste as one `javascript_tool` call), then `__tm.guard()`.

### 3. Section images - repeat per row, in manifest order
1. `__tm.installHook()` (once per page load; reload removes it).
2. `await __tm.bildAfterH2("<H2 text>")` -> `{captured: true}`. Throws if the H2 is missing or already has an image after it - then stop and tell the user.
3. `find` "hidden file input appended to body, not the Vorschaubild one" -> ref -> `file_upload` with the image path.
4. The Pintura crop editor opens **slowly** (30-90 s on this heavy page: it slides in, shows a blank canvas, then the image). A Fertig click before it is ready is lost - the block then stays in `image-tool--uploading` and the editor stays open. So: wait ~30 s, take a small screenshot, click `__tm.clickFertig()` once when the editor chrome (X top-left, yellow Fertig top-right) is crisp.
5. Poll `__tm.filled()` every ~10 s until the block flips from `uploading` to `filled` (1-4 minutes; the screenshot shows a faint "Bild wird verarbeitet…" spinner meanwhile). If it is still `uploading` after ~2 min and a screenshot shows the editor open and idle (no spinner), the first click was lost: click Fertig once more. Do not touch the page otherwise. After `filled`, the editor needs another ~20-30 s to slide away - the caption call works already.
6. `await __tm.captionAfterH2("<H2 text>", "<caption>")` -> `ok: true`.

### 4. Cover (Vorschaubild)
1. `find` the file input labelled "Vorschaubild ändern" (persistent input, no hook needed) -> `file_upload` the chosen cover.
2. Pintura opens as above: `clickFertig()` once, poll until the editor closes (screenshot shows the page again; the thumbnail card shows the image). Do not click other things meanwhile - a click lands on the overlay.
3. `await __tm.coverCaption("<caption <= 90 chars>")`.

### 5. Category and author
`await __tm.pick("<Category>")` and `await __tm.pick("Johannes Kofler")`. Options are read from the DOM; exactly one match is required.

### 6. Save as draft
Run the guard again (`__tm.guard().ok`), then `__tm.preserveFormatting()` (Hard rule 10), then `__tm.saveDraft()`, wait ~10 s, then `__tm.validationErrors()` must be empty (otherwise fix and click again; an old error can linger one render). A toast is not reliable - verify through the API instead.

### 7. Verify (source of truth)
```bash
TRUSTMARKT_API_TOKEN=... python3 scripts/verify_draft.py --manifest /tmp/parsed.json --category "<Category>" --before /tmp/before.json
```
Must exit 0: status DRAFT, author Johannes Kofler, category set, first image has >= 3 blocks before it, one figure per manifest section directly after its H2, caption == manifest == alt, article text unchanged by editing, bold/italic count not reduced, article text German. If "bold formatting preserved" fails, the formatting step was skipped - fix in the editor (`preserveFormatting()` then save again), not through `update-article` (that wipes the images). Then **reload the editor tab** and confirm: Vorschaubild `<img>` is a permanent URL (`.../thumbnails/thumbnail/...`, not `livewire-tmp`), the cover caption is still there, `__tm.guard().ok` is true. (The API does not expose the cover.)

### 8. Report
Article id/title, which cover variant, category, author, images inserted, verify result, anything skipped (e.g. cover caption shortened - say exactly what was changed), and a reminder that the user has to review and submit the draft themselves. Close tabs you opened.

## Gotchas learned in the dry run
- Editor = Editor.js blocks + Pintura image editor on a Livewire page. Block menu (the six dots next to a block): Nach oben / Löschen (needs a second "Sicher?" click) / Nach unten - useful to fix a misplaced image.
- The Bild block's `<input type=file>` exists only for an instant; the hook in `editor_helpers.js` appends it to `<body>` so `find`/`file_upload` can reach it. Uploads go to S3 immediately (before saving) - an abandoned block leaves an unreferenced file, harmless.
- Typing into the category dropdown search does not work through key events; selecting the `.bc-option` element does.
- A frame ghost of the crop editor (blank white screen with faint text) means it is still processing, not hung.
- Do not use `Artikel veröffentlichen` even though it turns green once the draft is complete.

## Failure handling
- Not logged in / login page: stop, ask the user to log in in that Chrome profile.
- `guard().ok` false: see Hard rule 1.
- Extension not connected: tell the user; the fallback is the hybrid way - Claude does placement, captions, category, author and save in the built-in browser, the user picks each file in the dialog.
- Save fails with a validation message: read it, fix the field (most likely cover caption length), save again once.
- Verify fails: report the failing checks verbatim; do not "fix" by republishing through the API.
