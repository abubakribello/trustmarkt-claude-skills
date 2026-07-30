---
name: trustmarkt-article-images
description: Generate a full set of German editorial images for a Trustmarkt/Agenturmarkt article — cover variants plus one image per major section — using Gemini image generation, verify each locally, then push verified images to an n8n webhook that uploads them to Google Drive. Use this skill whenever the user asks for article images, thumbnails, covers, section images, or visuals for a Trustmarkt/Agenturmarkt/Expertenmarkt article, or right after an article draft was created and needs its image set.
---

# Trustmarkt Article Images

Generate the complete image set for one article: **3 cover variants** (for comparison, one gets picked manually) plus **one section image per 2–3 H2 sections**, so the article looks visually alive while scrolling — matching the benchmark articles on Agenturmarkt, which average an image every 2–3 sections.

Images cannot be inserted via the Trustmarkt API. Each verified image is pushed to an n8n webhook, which drops it into Google Drive; Johannes inserts them in the web editor before publishing.

Never upload through a Drive MCP/connector tool directly — passing full-resolution image bytes through a tool call means they get serialized into the model's context (~100K+ tokens per image, 600K+ for a full set). The webhook hop keeps image bytes inside the script's own HTTP request, off-context, regardless of whether this skill runs locally or in a cloud routine sandbox.

## Requirements

- `GEMINI_API_KEY` env var (Gemini image model, Nano Banana Pro) + `pip install google-genai pillow --break-system-packages`
- `N8N_IMAGE_WEBHOOK_URL` env var — your self-hosted n8n webhook that accepts an image/manifest and uploads it to Drive. Import `n8n/trustmarkt-article-image-upload.json` (see `n8n/README.md` for setup) and point this at its production URL.
- `N8N_IMAGE_DRIVE_FOLDER_ID` env var — the shared parent Drive folder. Each article run creates its own subfolder inside it first (step 2 below) and uploads everything there. Defaults to `1P0PBdVPtlloCz9ApzvguklnGgvzoTaIq` unless the user names another.

## Workflow

### 1. Get the article

Either the draft `.md` from the article-writer skill (same session), or fetch it: `python ../trustmarkt-article-writer/scripts/trustmarkt_api.py get-article --id <ID> --expand content`. If the article writer produced an image plan, use it; otherwise derive one now.

### 2. Build the image plan

- 1 cover (3 variants, different concepts)
- Section images at the points where a visual actually adds something — a worked calculation, a comparison, a workflow, a checklist. Not a fixed count (not always exactly 2): add one everywhere it earns its place, skip a section entirely if there's nothing worth illustrating there.
- **Skip any section that would just re-render a table/comparison the article already shows as text.** If the article body already has an HTML table for a given comparison, making an image of the same table is redundant — only illustrate content that isn't already presented visually in the text.
- For each: what it shows, which concept type (below), and a German caption (the platform shows captions — benchmarks use them to add context, e.g. "Foto unserer App für Personalmanagement, die real so im Einsatz ist.")

### 3. Generate

**Both covers and section images go through Gemini (`generate_article_image.py`) — always pass real reference images, never generate from a bare text prompt.** This was validated directly by Johannes reviewing real output: a prior all-Pillow-template attempt (a real photo pasted onto a static background) was rejected outright ("that sucks... mainly text and icons"). What actually works, confirmed against three separate test generations, is Gemini recompositing Johannes' real likeness into a photoreal scene, guided by strong reference images — not a flat template, and not a from-scratch AI illustration.

Always pass this reference set for any image featuring Johannes:

```bash
python scripts/generate_article_image.py \
  --prompt "<see prompt structure below>" \
  --refs assets/headshots/Headshot_Johannes_transparent.png \
         assets/headshots/johannes_webcam_angle1.png \
         assets/headshots/johannes_webcam_angle2.png \
         assets/style-refs/50-workflow-ideen-GOLD-STANDARD.png \
  --aspect 16:9 \
  --output workspace/<slug>/cover-v1.png
```

Multiple face references (the studio headshot plus the two webcam-angle stills) measurably improve likeness over a single photo — Gemini triangulates the true bone structure instead of guessing from one angle. `assets/style-refs/50-workflow-ideen-GOLD-STANDARD.png` is the explicit target look Johannes pointed to live as "perfect" — always include it (or `kein-chaos-mit-ai-good.png` / `ki-vs-mensch-good.png` as secondary style anchors) as a composition/lighting reference.

**Logo watermark is optional, not default.** None of the approved benchmark examples carry a corner brand logo — don't add one just to add one. Only include it when there's an actual reason to signal a brand: e.g. the article covers a partnership/integration between two named tools or companies and the image needs to visually pair them. If it's needed: **never ask Gemini to draw the logo text itself** — small brand wordmarks are unreliable (tested: got a generic sparkle icon once, "DigitalShift" missing the X once). Instead generate the scene with an empty corner, then composite the real logo file deterministically:
```bash
python scripts/watermark.py --image workspace/<slug>/cover-v1.png \
  --logo assets/brand/logo-wordmark-white.png --in-place
```

**Prompt structure** (this combination is what produced three clean results in testing — reuse it, only varying pose/headline/concept). Brand specifics are in `assets/brand/DigitalXShift-brand.md` — read it before generating and use its exact values, not the placeholders below from before the brand deck existed:
- Person: chest-up crop only, **never full body** — this was called out explicitly and repeatedly as a hard rule
- Pose/expression: warm, approachable, confident but not severe or corporate-stiff (the brand's own tone profile leans casual/warm/accessible, not cold/corporate) — vary the pose per variant (arms crossed, hand near chin, slight turn) for the 3 cover variants
- Lighting/background: **use a real photographic scene, not an abstract gradient wash** — a flat near-black/navy or navy-to-cyan backdrop was tried across a full batch and came back as direct feedback ("still too blue," "doesn't have to be brand colors"). Put Johannes in an actual place: a real office/studio interior, a co-working space, a city skyline at dusk, an outdoor location — anything that fits the article's tone. `#1cb5e0` stays purely a small-area accent (rim-light on hair/shoulder, diagram lines, badge border, a lamp/screen glow in the scene) — it must never tint or fill the whole frame. Vary the actual setting across the 3 cover variants, not just the overlay concept, so there's a real choice.
- Overlay concept: pick one from the list below, described as translucent/glowing so it reads as tasteful digital compositing, not clutter — tint any glow/lines in the brand accent `#1cb5e0`, used sparingly against the dark background
- Text: **ask Gemini to render it directly** — with this reference set it comes out correctly spelled and legible (unlike earlier attempts without real face/style refs). State the exact text in quotes, require **bold Montserrat-style geometric sans-serif** (the brand's actual typeface — not serif), in a rounded pill-shaped badge with a glowing `#1cb5e0` border
- Always end with: *"Photorealistic, cinematic, high-end editorial photography — must look like a real photograph with tasteful digital compositing, not like an obviously AI-generated illustration."* This sentence is doing real work; keep it.

Generate **3 cover variants** this way (vary pose + headline phrasing + which overlay concept), so there's a real choice to make, not just one shot.

**Every cover variant should carry icons where relevant, not just one of the three — but they don't all need to be flowcharts.** Early runs only put icons on the workflow-diagram variant and left the stat-highlight and hologram variants as photo-plus-text with nothing else. Vary *how* icons show up per concept instead of repeating one style three times — validated patterns, confirmed across three articles:
- **Branch diagram** (workflow variant): the article's real tool icon as a hub, branching to task/outcome icons on glowing lines
- **Icon cluster + stat** (stat variant): the real tool icon paired with one small supporting icon (coin, shield, clock — whatever fits the number) sitting just above the big stat text, not just floating text alone
- **Icon-in-hologram** (hologram variant): the real tool icon glowing at the center of the network visualization instead of plain abstract dots

Rotate these three (or invent a fourth in the same spirit — an icon cluster styled like a tool-composition collage works too) so the set has real variety to choose from, but every variant ends up populated, not just variant 1.

**Only covers use Johannes' face and this portrait format.** Section/inline images are a different job — see below.

### Cover concept types (rotate across the 3 variants, don't repeat one)

1. **Workflow/diagram overlay** — translucent glowing automation flow chart (icons + curved connecting lines) behind the person, like an n8n workflow. The gold-standard reference.
2. **Network/hologram overlay** — person interacting with a glowing data-network visualization, like `kein-chaos-mit-ai-good.png`.
3. **Stat highlight** — a huge glowing number/percentage floating beside the person, plus a smaller supporting line underneath. Validated in testing (`-50% Kosten` / `pro Monat`) — legible at both large and small scale.
4. **Tool composition** — real logos of the specific tools/companies discussed (n8n, Claude, Meta, WhatsApp, Hetzner, etc.) arranged as a system, not a random collage. Fetch the real icon files first (don't rely on Gemini to invent brand marks from a text description alone — same reliability problem as the DigitalXShift wordmark):
   ```bash
   python scripts/fetch_tool_icon.py --name "WhatsApp" --out assets/tool-logos/whatsapp.png
   python scripts/fetch_tool_icon.py --name "n8n" --out assets/tool-logos/n8n.png
   ```
   This caches to `assets/tool-logos/` (checked first, so repeat topics don't re-fetch) via Simple Icons (thousands of tech/software brands) falling back to a favicon lookup for anything else. Pass the fetched file(s) as extra `--refs` so Gemini composites the real shape/colors instead of guessing — icons are simple enough that Gemini reproduces them reliably from a reference image (unlike small wordmark text), and keep each icon's own real color (don't recolor a brand icon cyan). Verify each generated image regardless (see step 4 below); if a specific icon still comes out wrong after a retry, fall back to pasting it in deterministically the same way as the logo watermark (`watermark.py` accepts multiple `--logo` paths for this).

   **Make the diagram illustrate the actual point, not just decorate.** When the article's point is structural (e.g. "one platform, several narrowly-scoped task bots" rather than one general assistant), draw that structure: the real tool icon branching into multiple small distinct bot/agent nodes, each of those connecting onward to its own specific task icon (calendar, order/package, FAQ bubble, etc.) — not just the tool icon connected to two generic decorative icons. Read what the section/article is actually arguing and let the diagram's topology carry that argument.
5. **Before/after split** — chaos vs. system, manual vs. automated.

### Section/inline images — no Johannes, no cover format

Section images illustrate whatever that specific part of the article is explaining — they are **not** smaller covers. Don't force a portrait of Johannes into every one; most sections should not have a person in them at all. Pick whatever actually communicates the section's point:
- A **table or comparison graphic** (e.g. manual vs. AI cost, self-hosted vs. cloud) — rendered as a clean data graphic, not a photo
- A **workflow/process diagram** — icons and arrows showing a flow, no person needed
- A **stat/infographic** — a number or comparison rendered big and clean
- Real tool icons (fetched via `fetch_tool_icon.py`, same as covers) where the section is specifically about those tools

Loosely keep the brand feel (Montserrat text, `#1cb5e0` as an accent color, clean not "AI-illustration"-looking) so the set reads as one family — but the background doesn't need to match the cover's near-black shade exactly. A comparison table on a lighter neutral background, or a diagram that's mostly white space, is fine and often clearer than forcing every section onto the same dark backdrop.

### Style rules

- **Covers only:** a real, recognizable photo of Johannes is the anchor — this is the single biggest gap vs. the benchmark; never fall back to an abstract/faceless cover or a generic AI face. Chest-up crop only, never full body. Include the full headshot+webcam reference set from `assets/headshots/` plus a style ref from `assets/style-refs/`.
- **Sections:** illustrate the specific point being made (diagram/table/infographic/tool icons) — no forced person, no headline badge.
- Background is a real photographic scene/setting (office, co-working space, city skyline, outdoor location — vary it per image), not an abstract gradient wash. `#1cb5e0` is a small-area accent only (rim-light, diagram lines, a glow source within the scene) — a full-canvas navy/blue backdrop read as "too blue" in direct feedback on two separate batches; don't repeat it.
- Brand accent/glow color `#1cb5e0`, headline font Montserrat — see `assets/brand/DigitalXShift-brand.md` for the full brand guide. Consistent within one article's whole set.
- Clean, professional B2B-editorial — no stock-photo cheese (no smiling robots holding phones), no clip-art, no obviously-AI look

### 4. Verify, then push

Nothing gets uploaded before it's checked — the webhook only ever receives images that already passed.

1. View every generated image with the Read tool. Regenerate anything with garbled/broken German text, wrong logos, or visual clutter — max 2 retries each, then flag it and skip pushing it.
2. Create the article's subfolder first, once, and capture the id it returns:
   ```bash
   python scripts/upload_to_n8n.py --webhook-url "$N8N_IMAGE_WEBHOOK_URL" \
     --create-folder --article-slug <slug> --folder-id "$N8N_IMAGE_DRIVE_FOLDER_ID"
   ```
   Prints `FOLDER_ID=<new id>` on success — use that id, not `$N8N_IMAGE_DRIVE_FOLDER_ID`, as `--folder-id` for every call below. If this step fails, stop and report it rather than falling back to the parent folder.
3. Push each verified image, one call per file, into that subfolder:
   ```bash
   python scripts/upload_to_n8n.py --webhook-url "$N8N_IMAGE_WEBHOOK_URL" \
     --file workspace/<slug>/cover-v1.png --article-slug <slug> --filename cover-v1.png \
     --image-type cover --order 1 \
     --caption "<German caption>" --folder-id "<FOLDER_ID from step 2>"
   ```
   Section images: `--image-type section --order N --insert-after-h2 "<the heading text it follows>"`.
4. Build `manifest.md` (filename → insert after which H2 → German caption → one-line concept description for covers) and push it into the same subfolder:
   ```bash
   python scripts/upload_to_n8n.py --webhook-url "$N8N_IMAGE_WEBHOOK_URL" \
     --manifest workspace/<slug>/manifest.md --article-slug <slug> --folder-id "<FOLDER_ID from step 2>"
   ```
5. Report: article slug, the Drive subfolder created, how many images were pushed vs. flagged and skipped, and confirm the webhook accepted each call (a non-2xx response from the script means it did **not** reach Drive — surface that instead of reporting success).

## Attribution

Image generation approach adapted from the YouTube Thumbnail skill built by Tyler Germain (@itstylergermain) at Friday Labs.
