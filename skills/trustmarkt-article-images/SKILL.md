---
name: trustmarkt-article-images
description: Generate a full set of German editorial images for a Trustmarkt/Agenturmarkt article — 3 cover variants (a real, unedited photo of Johannes composited by Gemini into a designed scene via one of 7 proven templates) plus 3 section images (illustrative diagrams/tables/infographics, no person). Use this skill whenever the user asks for article images, thumbnails, covers, section images, or visuals for a Trustmarkt/Agenturmarkt/Expertenmarkt article, or right after an article draft was created and needs its image set.
---

# Trustmarkt Article Images

Generate the complete image set for one article: **3 cover variants** (for comparison, one gets picked manually) plus **3 section images**, so the article looks visually alive while scrolling — matching the benchmark articles on Agenturmarkt, which average an image every 2–3 sections.

Images cannot be inserted via the Trustmarkt API. Each verified image is pushed to an n8n webhook, which drops it into Google Drive; Johannes inserts them in the web editor before publishing.

Never upload through a Drive MCP/connector tool directly — passing full-resolution image bytes through a tool call means they get serialized into the model's context (~100K+ tokens per image, 600K+ for a full set). The webhook hop keeps image bytes inside the script's own HTTP request, off-context, regardless of whether this skill runs locally or in a cloud routine sandbox.

## Cover generation: one Gemini call per cover, real photo + template (as of 2026-08-06)

**This replaces the deterministic Pillow pipeline (`build_cover.py` + `render_background.py`/`render_text.py`/`render_icon_tile.py`/`composite_person.py`) for covers only.** Those scripts are gone (not kept as a fallback — see below). `scripts/compose_cover.py` is the only cover path now.

**Section images are a different job and are unaffected by this — see "Section images" further down.** They never involved likeness, so there was never a reliability reason to change them; they still go through `generate_article_image.py` with no person in frame, exactly as before.

**If `GEMINI_API_KEY` isn't available, stop and report that — do not fall back to the deterministic pipeline.** A flatter, less "wow" cover set was worse than the current one by direct comparison (see below); producing no images and saying why is better than silently shipping the worse version. This is a deliberate choice, not an oversight.

**Why the switch:** the deterministic pipeline was itself a fix for an even earlier all-AI approach that failed on likeness/logo/layout reliability (see git history / the section below this one for that story) — but once text/logos/layout were locked down deterministically, the result read as visually flat next to Johannes's real reference thumbnails ("a million steps backward" on the flat multi-icon layouts specifically). The fix that actually worked: let Gemini composite the WHOLE scene in one call — real photo + icons/diagrams/stat-cards/headline all together, with matching lighting — instead of Pillow-pasting flat layers on top of each other. Validated across two full articles' worth of variants (all 7 templates, twice), both Johannes and Abubakri preferred every result over the deterministic version.

**The one non-negotiable rule that makes this safe:** the face is NEVER regenerated. `scripts/compose_cover.py`'s `FACE_LOCK` constant goes into every prompt verbatim, and every call passes a real, unedited photo from `assets/headshots/real-photos/` as a reference image — **never** an AI-regenerated pose. This was learned the hard way mid-development: an attempt at generating *new poses* of Johannes (via Gemini, "same face, different gesture") produced likeness drift he flagged directly once compared side-by-side with real photos of him smiling. Real photos composited around by Gemini hold likeness; asking Gemini to redraw him does not — no amount of "preserve exactly" prompt wording fixed that, only using real, unedited source photos did.

Text, icon counts, and logo colors are still a real per-call risk (Gemini can misspell, invent an extra card, or recolor a logo) — **always view every generated image with the Read tool and check spelling/counts/colors before delivering.** Retry with a more explicit constraint if something's off (`build_g`'s "EXACTLY THREE... no more" wording is the fix for a real duplicate-card bug hit during development — same pattern applies to any count/spelling miss).

### The 7 templates

| # | Template | Function (`compose_cover.py`) | Fits content that... |
|---|---|---|---|
| A | Logo(s) above the headline + portrait | `build_a(photo, headline, output, icons)` — `icons` = one logo or a list | Is a plain question/identity headline. Simplest layout — no orbit/scatter framework to get wrong. Carries the article's prominent content brand(s) as a slightly haloed row above the text (one for a single-tool piece, two when it pairs a product with an institution like ChatGPT + EU flag). |
| B | Two-icon comparison | `build_b(photo, headline, left_icon, left_label, right_icon, right_label, output)` | Weighs two things against each other (time vs money, tool A vs tool B). |
| C | Labeled icon orbit | `build_c(photo, headline, items, output)` — `items` = exactly 4 `(icon, label)` pairs | Is a scoring framework / checklist / 4-factor breakdown. |
| D | Icon halo (scattered) | `build_d(photo, headline, icons, output)` — `icons` = 3-4 items, no labels | Is "what's at stake" / an ecosystem/ingredients framing. |
| E | AI-prompt-box mockup | `build_e(photo, headline, prompt_text, output, icon)` | Frames the content as "the question you'd ask an AI advisor." |
| F | Workflow / process flow | `build_f(photo, headline, nodes, output, icon)` — `nodes` = 3-5 short labels | Is any step-1-to-step-N process or pipeline. |
| G | Stat cards | `build_g(photo, headline, cards, output, icon)` — `cards` = exactly 3 `(stat, label)` pairs | Has 3 concrete real numbers/case studies. Leads with proof, not theory. |

**Every template renders at least one relevant icon now — there is no icon-less variant.** For B/C/D that's inherent to the template (multiple icons). For A/E/F/G, the icon argument is required: A renders the article's prominent content brand(s) — one or several, whatever the piece actually features — as a slightly haloed logo row above the headline (don't force a fixed count; put the logos the content is about), E places it inside the prompt-box mockup, F places it inside whichever single node it actually represents, G places it once above the stat cards. On A, each logo gets a slight halo so it lifts off the dark background, but the halo goes *around* the logo — it must never recolor the mark itself (a "bright glow" over "preserve exact colors" is what tints a logo the wrong color).

Each `icon` (all templates) is either a **real logo file path** from `assets/tool-logos/` (exact color/shape preserved, passed as a reference image — use for actual named brands) or a **plain text description** (Gemini invents an original icon — safe for generic concepts like "a stack of gold euro coins," since there's no real logo to get wrong). **If the article is AI-themed but never names a specific product**, `extract_entities.py`'s `found` list will contain a `"generic_ai_fallback": true` Claude entry (see step 2 below) — use that logo as the icon rather than a text description, so the "AI" concept has a real, recognizable mark instead of an invented one.

**Picking 3 of 7 per cover set** is a judgment call, not a lookup — same spirit as headline-writing below. A pattern that's worked well twice so far: one **A** (question/identity, the safe always-works anchor), one **mechanism** template (**C** or **F** — the actual method/framework/process the article delivers), one **proof** template (**G** — real numbers/case studies, if the article has them). Don't force B, D, or E where the content doesn't naturally fit one of them — a forced metaphor reads worse than a plain A.

**This supersedes `assets/brand/DigitalXShift-brand.md`'s background-style guidance for covers/sections specifically** — the brand guide's color (`#1cb5e0`) and typeface (Montserrat) values still apply as accent/label choices where you write literal text into a prompt, just not its "flat gradient wash" background guidance.

## Feedback From 2026-08-03 Review — read before generating

Johannes reviewed a batch of thumbnails across all three thumbnail skills — this one, `youtube-thumbnails-merged`, and `instagram-shorts-thumbnails` (all three share the same `composite_person.py`/`render_background.py`/`render_text.py` lineage). What's now baked in or confirmed:

- **Yellow/orange glow bug — fixed.** Every render was picking up an unwanted warm yellow-orange rim glow no matter what the concept called for. Root cause: `glow_color=(255, 205, 110)` was hardcoded as the *default* in `render_background.py`, `composite_person.py`, and `render_text.py`, and nothing ever overrode it. Fixed to a cool blue `(80, 150, 255)` in all three, plus the skin-tone warmth shift in `composite_person.py` step 4 flipped from warm to cool to match. If a cover ever looks yellow again, check those three files' defaults first.
- **Icons: real and recognizable only, big or none.** This skill already only uses real fetched logos (never AI-drawn), which is correct — keep it that way. Additionally: a viewer should recognize the tool at a glance, so cap at 2 per cover as already documented. (This note originally continued with "...an icon-less fallback is a better choice than forcing a weak one in" — that no longer applies: every current template requires at least one icon, real or Gemini-invented concept icon, see "The 7 templates" above and the generic-AI-fallback in step 2 below.)
- **Version control.** The `cover-v<N>.png` numbering in the workflow already supports this — keep using it, and additionally copy the reviewer-picked cover into a dated `approved/` subfolder before generating further variants, so a later iteration can never overwrite the one that already got picked.
- **Don't assume the same template works across YouTube / Instagram-Shorts / article covers** — they have real structural differences (e.g. this skill's own left/right person-side conventions differ from the other two). Get one format to a genuinely good state first, then deliberately adapt elements to the others, rather than porting a template wholesale.
- **Text must stay legible — enforced now.** `render_text.py`'s auto-fit floor was raised from 20px to 40px and now prints a warning if a headline is long enough to hit it; if you see that warning, shorten the headline rather than trust the shrink.

## Requirements

**Required for both covers (`compose_cover.py`) and section images (`generate_article_image.py`) — there is no fallback path for covers:**
- `GEMINI_API_KEY` env var (Gemini image model, `gemini-3-pro-image-preview`) + `pip install google-genai pillow`. If this isn't set, stop and tell the user rather than generating covers a worse way — this restriction is specific to covers (see "Cover generation" above); it was never true of section images, which have no deterministic alternative to fall back to in the first place.

**Always required for delivery:**
- `N8N_IMAGE_WEBHOOK_URL` env var — your self-hosted n8n webhook that accepts an image/manifest and uploads it to Drive. Import `n8n/trustmarkt-article-image-upload.json` (see `n8n/README.md` for setup) and point this at its production URL.
- `N8N_IMAGE_DRIVE_FOLDER_ID` env var — the shared parent Drive folder. Each article run creates its own subfolder inside it first and uploads everything there. Defaults to `1P0PBdVPtlloCz9ApzvguklnGgvzoTaIq` unless the user names another.

**Recommended for cloud routines specifically:**
- `GITHUB_TOKEN` env var — a token scoped to just this repo (`contents: write` is enough) so `register_brand.py` can push a newly-discovered brand's icon back to GitHub. Without it, a new brand still works for the run that discovers it, but the registration is lost when that sandbox is torn down (every routine run does a fresh shallow clone per `BOOTSTRAP.md` — nothing persists across runs unless it's pushed back). With it, every brand only ever needs discovering once, by whichever run happens to encounter it first.

## Workflow

### 1. Get the article

Either the draft `.md` from the article-writer skill (same session), or fetch it: `python ../trustmarkt-article-writer/scripts/trustmarkt_api.py get-article --id <ID> --expand content`.

### 2. Which brands does the article name? (needed for every cover template now — see step 3)

```bash
python scripts/extract_entities.py --title "<article title>" --content-file draft.md
# -> JSON {"found": [{name, icon_path, type, [generic_ai_fallback]}, ...], "unlisted_candidates": [...]}
```

**If no real brand/tool was found at all and the article is AI-themed** (mentions "AI"/"KI"/"künstliche Intelligenz" without ever naming a specific product), `found` will contain one extra entry: `{"name": "Claude", "icon_path": "assets/tool-logos/claude.png", "type": "tool", "generic_ai_fallback": true}`. Use that as the `icon` for whichever template you're building instead of a plain-text "AI" description — a real, recognizable logo beats an invented generic one. This fallback is skipped automatically the moment any real tool is found, since a specific brand is always the better, more relevant pick.

**`known-brands.json` is a self-growing cache, not a list you're expected to hand-maintain** — this skill gets packaged and distributed, so nobody downstream will remember to manually edit a JSON file when a new tool comes up. `unlisted_candidates` (a regex heuristic) is a supplementary hint only. **The reliable mechanism is this required step:**

Independently read the article yourself and list every named tool/brand/company mentioned. For every brand on your list that is **not** already in `found`'s names:

```bash
python scripts/register_brand.py --name "<Brand Name>" --domain <its domain if known>
# -> fetches its icon AND permanently appends it to known-brands.json.
# Idempotent — safe to call even if it might already be registered.
```

This makes the dictionary grow automatically through normal use: the first article to mention a given brand is the only one that ever needs this extra step for it.

### 3. Generate the 3 covers

Pick 3 of the 7 templates per the guidance above (question/identity + mechanism + proof is the pattern that's worked twice). For each:

1. **Pick a real photo** from `assets/headshots/real-photos/` matching the cover's tone — filenames are the interface (`serious`, `smiling`, `excited-presenting`, `mindblown`, etc.). Never use an AI-regenerated pose.
2. **Write the headline yourself** (and any icon labels/stat-card text) — the one step that genuinely needs understanding, not a lookup. Distill the article's real hook/number/argument into ALL-CAPS German, exact spelling, don't invent a stat that isn't in the article.
3. **Pick the icon(s)** every template needs: an `icon_path` from step 2's `found` list (including the `generic_ai_fallback` Claude entry, if that's what's present) wherever the concept names a real brand or is AI-themed with no specific product, otherwise a plain text description of the concept.
4. **Call the matching `build_*` function** from `scripts/compose_cover.py`:

```bash
python3 -c "
from scripts.compose_cover import build_a
build_a(
    'assets/headshots/real-photos/johannes-serious-headshot-01.png',
    'IST CHATGPT DSGVO-KONFORM?',
    'workspace/<slug>/cover-v1.png',
    icons=['assets/tool-logos/openai.png', 'assets/institutional-logos/eu-flag.png'],
)
"
```

(`icons` takes one logo or a list — pass the article's prominent content brand(s); a single-tool piece passes one, a piece pairing a product with an institution passes both. Swap `build_a` and its args for whichever of the 7 templates fits — see the table above for each function's signature; the icon argument is required on A/E/F/G, B/C/D take their icons as part of `left_icon`/`right_icon`/`items`/`icons`.)

5. **View the result with the Read tool immediately.** Check: spelling of every piece of text, icon colors match the real brand (if a real logo was referenced), correct item count (no invented extra card/icon), nothing overlapping the face or headline. If something's off, retry with a tighter constraint in the prompt (edit the relevant `build_*` function's prompt string, or just call `compose()` directly with a hand-written prompt for a one-off fix) rather than shipping a flawed result.

### 4. Generate the 3 section images — a different job, no person, unchanged from before

**Trustmarkt editor image rules — placement is validated, plan around it:** every image needs a **valid caption** (a non-empty, meaningful German Bildunterschrift — never blank, never a placeholder), and there must be **at least three text paragraphs between any two images**. The cover counts as the article's first image, so the first section image needs three paragraphs of body text after the intro/cover before it, and each subsequent section image needs three more paragraphs after the previous one. In practice: don't place a section image right after another with only a heading or a single paragraph between them — space them across H2 sections that actually carry three-plus paragraphs, and drop an image rather than crowd two together. This is why the default is ~3 section images across a 1,000–1,600-word article, not one per H2.

Section images illustrate whatever that specific part of the article is explaining — they are **not** smaller covers, they don't use `compose_cover.py`, and they never feature Johannes:

```bash
python scripts/generate_article_image.py \
  --prompt "<description of the diagram/table/infographic>" \
  --refs <fetched tool icons if relevant> \
  --aspect 16:9 \
  --output workspace/<slug>/section-1.png
```

- A **table or comparison graphic** (e.g. manual vs. AI cost, self-hosted vs. cloud) — rendered as a clean data graphic, not a photo
- A **workflow/process diagram** — icons and arrows showing a flow, no person needed
- A **stat/infographic** — a number or comparison rendered big and clean
- Real tool icons (fetched via `fetch_tool_icon.py`, same dictionary as covers) where the section is specifically about those tools
- **No person, no headline badge, ever.** Skip any section that would just re-render a table/comparison the article already shows as text.
- Loosely keep the brand feel (Montserrat, `#1cb5e0` accent) so the set reads as one family, but the background doesn't need to match the covers' dark style exactly — a comparison table on a lighter neutral background is fine and often clearer.
- **Should read as human-made, not AI-generated.** `generate_article_image.py` now appends a style suffix pushing away from common AI-image tells (glow/gradient-mesh, glossy-3D, decorative sparkles/particles, melted or too-symmetrical icons) toward real editorial-design conventions (flat vector icons, restrained 2-3 color palette, grid alignment, deliberate asymmetry/negative space) — this applies automatically, no extra flag needed. Still worth a deliberate glance on every result: if it reads as "AI slop" at a glance, regenerate with a tighter prompt (e.g. spell out "flat vector, no glow" for that specific image) rather than shipping it.
- **View every generated section image with the Read tool. Regenerate anything with garbled/broken German text, wrong logos, or visual clutter — max 2 retries each, then flag it and skip pushing it.**

### 5. Verify, then push

Nothing gets uploaded before it's checked — the webhook only ever receives images that already passed.

1. **Covers:** view each with the Read tool per step 3.4's checklist (spelling, icon colors/counts, nothing overlapping the face/headline). **Section images:** full visual check per step 4 above (garbled text, wrong logos, clutter — max 2 retries, then flag and skip). Both are Gemini-generated now, so both need a real check — nothing is "guaranteed by construction."
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
     --caption "<German caption>" --folder-id "<FOLDER_ID from step 5.2>"
   ```
   Section images: `--image-type section --order N --insert-after-h2 "<the heading text it follows>"`. **`--caption` is mandatory and must be a real German caption** — Trustmarkt's editor rejects an image without a valid caption, so never push with a blank or placeholder one. Confirm the chosen `--insert-after-h2` anchors leave ≥3 text paragraphs between consecutive images (see the placement rule in step 4) before pushing.
4. Build `manifest.md` (filename → insert after which H2 → German caption → one-line concept description for covers) and push it into the same subfolder:
   ```bash
   python scripts/upload_to_n8n.py --webhook-url "$N8N_IMAGE_WEBHOOK_URL" \
     --manifest workspace/<slug>/manifest.md --article-slug <slug> --folder-id "<FOLDER_ID from step 5.2>"
   ```
5. Report: article slug, the Drive subfolder created, how many images were pushed vs. flagged and skipped, and confirm the webhook accepted each call (a non-2xx response from the script means it did **not** reach Drive — surface that instead of reporting success).

## Asset library reference

- `scripts/compose_cover.py` — the cover engine: `FACE_LOCK`, the `compose()` Gemini helper, and all 7 `build_*` template functions. Read "Cover generation" above for the full story. **Covers only** — see `generate_article_image.py` for section images.
- `scripts/generate_article_image.py` — the section-image generator: a free-form Gemini call per section (table/diagram/infographic prompt + optional icon refs), no person, no template system. Unchanged by the cover rework.
- `assets/known-brands.json` — the entity dictionary `extract_entities.py` matches against. **Self-growing, not hand-maintained**: `register_brand.py` appends to it automatically the first time a new brand is registered (see step 2a) — don't edit it by hand as routine maintenance; that doesn't scale once this skill is distributed to people who aren't its maintainer.
- `assets/tool-logos/` — cached real brand icons, fetched via `fetch_tool_icon.py` (Simple Icons CDN when the environment has system `cairo`, falling back automatically — not as an error — to Google's favicon service when it doesn't; this is expected behavior in most cloud sandboxes, not a degraded state to fix).
- `assets/institutional-logos/eu-flag.png` — geometrically exact EU flag (12 gold stars, official blue), generated once by a small deterministic script, not AI-drawn, for any DSGVO/GDPR/EU-AI-Act-themed cover. Extend this folder + `known-brands.json`'s `institutional` list for other recurring institutional symbols.
- `assets/headshots/real-photos/johannes-<mood>-<pose>-NN.png` — the real photo library `compose_cover.py` picks from. Filenames are the only interface — name new photos with an accurate mood keyword (`serious`, `smiling`, `excited-presenting`, `mindblown`, etc.) so they're discoverable. **Never add an AI-regenerated pose here — real, unedited photos only** (see "Cover & section-image generation" above for why this is a hard rule, not a preference).
- `assets/fonts/Montserrat-Variable.ttf` — the real brand typeface, bundled in-repo so text rendering never depends on whatever fonts happen to be installed in a given sandbox.

## Attribution

Section-image generation (`generate_article_image.py`) adapted from the YouTube Thumbnail skill built by Tyler Germain (@itstylergermain) at Friday Labs. Cover generation used to share that lineage too, before `compose_cover.py` superseded it for covers specifically.
