---
name: trustmarkt-article-images
description: Generate a full set of German editorial images for a Trustmarkt/Agenturmarkt article — cover variants plus one image per major section — using Gemini image generation, then upload them to Google Drive for manual insertion. Use this skill whenever the user asks for article images, thumbnails, covers, section images, or visuals for a Trustmarkt/Agenturmarkt/Expertenmarkt article, or right after an article draft was created and needs its image set.
---

# Trustmarkt Article Images

Generate the complete image set for one article: **3 cover variants** (for comparison, one gets picked manually) plus **one section image per 2–3 H2 sections**, so the article looks visually alive while scrolling — matching the benchmark articles on Agenturmarkt, which average an image every 2–3 sections.

Images cannot be inserted via the Trustmarkt API. The output goes to Google Drive; Johannes inserts them in the web editor before publishing.

## Requirements

- `GEMINI_API_KEY` env var (Gemini image model, Nano Banana Pro)
- `pip install google-genai pillow --break-system-packages` (once per environment)
- Google Drive access (connector) for upload — target folder ID `1P0PBdVPtlloCz9ApzvguklnGgvzoTaIq` unless the user names another

## Workflow

### 1. Get the article

Either the draft `.md` from the article-writer skill (same session), or fetch it: `python ../trustmarkt-article-writer/scripts/trustmarkt_api.py get-article --id <ID> --expand content`. If the article writer produced an image plan, use it; otherwise derive one now.

### 2. Build the image plan

- 1 cover (3 variants, different concepts)
- 1 section image after every 2nd–3rd H2, at the points where a visual proves or illustrates something: a worked calculation, a comparison, a workflow, a tool
- For each: what it shows, which concept type (below), and a German caption (the platform shows captions — benchmarks use them to add context, e.g. "Foto unserer App für Personalmanagement, die real so im Einsatz ist.")

### 3. Generate

```bash
python scripts/generate_article_image.py \
  --prompt "<detailed German-text-overlay prompt>" \
  --refs assets/style-refs/01_was-passiert-wirklich.jpg assets/tool-logos/claude.png \
  --aspect 16:9 \
  --output workspace/<slug>/cover-v1.png
```

Covers 16:9. Section images 16:9 or 3:2. Always pass 1–2 style refs from `assets/style-refs/` so the set looks coherent; add tool logos from `assets/tool-logos/` when the section is about that tool.

### Concept types (rotate across the set, don't repeat one)

1. **Editorial statement** — clean background, short bold German phrase (3–6 words) as the visual anchor ("Mini-SaaS statt Chaos", "Dein Engpass, nicht dein Tool"). Benchmark covers look exactly like this.
2. **Tool composition** — logos/icons of the tools discussed (n8n, Claude, Meta, WhatsApp) arranged as a system/flow diagram, not a random collage
3. **Stat highlight** — the article's strongest number, huge ("−50 % Softwarekosten", "36.400 € vs. 4.000 €")
4. **Workflow/diagram look** — stylized process visualization (trigger → logic → output) for automation sections
5. **Before/after split** — chaos vs. system, manual vs. automated

### Style rules

- German text only in images, short (max ~6 words), spelled correctly — verify by viewing the generated image with the Read tool; regenerate if the text is garbled (AI image text often is)
- Consistent palette within one article's set (pick per article: the blue-editorial reference style is the safe default)
- Clean, professional B2B-editorial — no stock-photo cheese, no clip-art, no faces unless the user explicitly wants the headshot style
- View every image after generating; regenerate anything with broken text, wrong logos, or visual clutter (max 2 retries each, then flag it)

### 4. Deliver

1. Upload all images to the Drive folder, inside a subfolder named after the article slug
2. Add `manifest.md` next to them: table of filename → insert after which H2 → German caption → (for covers) one-line concept description so the best variant is easy to pick
3. Report: link to the Drive folder, image count, and anything flagged for regeneration

## Attribution

Image generation approach adapted from the YouTube Thumbnail skill built by Tyler Germain (@itstylergermain) at Friday Labs.
