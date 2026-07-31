---
name: trustmarkt-article-images
description: Generate a full set of German editorial images for a Trustmarkt/Agenturmarkt article — cover variants (built deterministically, no AI regeneration of the face/text/logos) plus one image per major section (Gemini-generated) — verify each locally, then push verified images to an n8n webhook that uploads them to Google Drive. Use this skill whenever the user asks for article images, thumbnails, covers, section images, or visuals for a Trustmarkt/Agenturmarkt/Expertenmarkt article, or right after an article draft was created and needs its image set.
---

# Trustmarkt Article Images

Generate the complete image set for one article: **3 cover variants** (for comparison, one gets picked manually) plus **one section image per 2–3 H2 sections**, so the article looks visually alive while scrolling — matching the benchmark articles on Agenturmarkt, which average an image every 2–3 sections.

Images cannot be inserted via the Trustmarkt API. Each verified image is pushed to an n8n webhook, which drops it into Google Drive; Johannes inserts them in the web editor before publishing.

Never upload through a Drive MCP/connector tool directly — passing full-resolution image bytes through a tool call means they get serialized into the model's context (~100K+ tokens per image, 600K+ for a full set). The webhook hop keeps image bytes inside the script's own HTTP request, off-context, regardless of whether this skill runs locally or in a cloud routine sandbox.

## Cover generation is deterministic, not AI-regenerated (as of 2026-07-31)

**This replaces the earlier "Gemini recomposites Johannes into a photoreal scene" approach for covers.** That approach was validated once against real feedback, then hit three separate, reproducible reliability failures in actual unattended production use:

1. **Inconsistent likeness.** Gemini re-synthesizes the face from scratch every call — even byte-identical prompt + identical reference images produced two visibly different faces on back-to-back runs. There is no way to prompt this away; it's how the model works.
2. **Wrong logo colors / missing logos entirely.** A live run silently omitted Make.com's logo from an "n8n vs. Make" cover (nobody told Gemini to draw it), and on retries the Claude AI icon's reference orange background got stripped to plain white/cyan.
3. **Text/person layout collisions.** Asking Gemini to "leave the right 50% empty" for the person, or "keep text left of 42%," was **not reliably obeyed** — it took three regeneration passes on a single cover to get one collision-free result, and that was still fixed by trial and error, not a guarantee.

None of these are reachable anymore. **Covers are now assembled entirely by deterministic scripts — no Gemini call in the default cover path at all:**

- The **background** (dark grid + warm rim-light glow) is drawn programmatically — `scripts/render_background.py`.
- **Text** is rendered with the real bundled Montserrat font (`assets/fonts/Montserrat-Variable.ttf`) — `scripts/render_text.py`. Correct spelling is guaranteed by construction; it's never AI-drawn.
- **Brand/institutional icons** are real fetched/generated assets composited as glossy tiles — `scripts/render_icon_tile.py`. Colors are always exactly right because nothing is redrawn.
- **The person** is Johannes' real, unedited photo, picked from a named pose library and composited with a feathered edge + matching rim-light glow — `scripts/composite_person.py`. This *is* his exact face, always, because it's not a regeneration.

The visual result is intentionally the bold "YouTube-thumbnail" look (near-black grid background, huge glow headline text, glossy 3D icon tiles, dramatic pose) rather than the earlier soft photographic-scene direction — that was a deliberate, explicit pivot requested after reviewing real high-performing thumbnail benchmarks, not an accident. **This supersedes `assets/brand/DigitalXShift-brand.md`'s "use a real photographic scene, not a gradient wash" guidance for covers specifically** — the brand guide's color (`#1cb5e0`) and typeface (Montserrat) values still apply, just not its background-style guidance.

Section/inline images are unaffected by this change — they still go through Gemini per the existing workflow below, since they never involved likeness, brand-logo, or fixed-layout risk in the first place.

## Requirements

**For covers:** just Pillow (already required) — no `GEMINI_API_KEY` needed. (A possible future enhancement — a small bounded Gemini call for a decorative circuit/hologram flourish — is not built; see "Cover concept types" below.)

**For section/inline images:**
- `GEMINI_API_KEY` env var (Gemini image model, Nano Banana Pro) + `pip install google-genai pillow`

**Always required for delivery:**
- `N8N_IMAGE_WEBHOOK_URL` env var — your self-hosted n8n webhook that accepts an image/manifest and uploads it to Drive. Import `n8n/trustmarkt-article-image-upload.json` (see `n8n/README.md` for setup) and point this at its production URL.
- `N8N_IMAGE_DRIVE_FOLDER_ID` env var — the shared parent Drive folder. Each article run creates its own subfolder inside it first and uploads everything there. Defaults to `1P0PBdVPtlloCz9ApzvguklnGgvzoTaIq` unless the user names another.

**Recommended for cloud routines specifically:**
- `GITHUB_TOKEN` env var — a token scoped to just this repo (`contents: write` is enough) so `register_brand.py` can push a newly-discovered brand's icon back to GitHub. Without it, a new brand still works for the run that discovers it, but the registration is lost when that sandbox is torn down (every routine run does a fresh shallow clone per `BOOTSTRAP.md` — nothing persists across runs unless it's pushed back). With it, every brand only ever needs discovering once, by whichever run happens to encounter it first.

## Workflow

### 1. Get the article

Either the draft `.md` from the article-writer skill (same session), or fetch it: `python ../trustmarkt-article-writer/scripts/trustmarkt_api.py get-article --id <ID> --expand content`.

### 2. Generate the 3 covers — run this exact sequence, per article, no manual concept-brainstorming

```bash
# 2a. Which brands/institutions does the article actually name?
python scripts/extract_entities.py --title "<article title>" --content-file draft.md
# -> JSON {"found": [{name, icon_path, type}, ...], "unlisted_candidates": [...]}
```

**`known-brands.json` is a self-growing cache, not a list you're expected to hand-maintain** — this skill gets packaged and distributed, so nobody downstream will remember to manually edit a JSON file when a new tool comes up. `unlisted_candidates` (a regex heuristic) is a supplementary hint only — it demonstrably misses cases (e.g. a brand mentioned only at the start of a sentence, since German capitalizes every noun and a naive capitalized-word scan would otherwise be mostly false positives). **The reliable mechanism is this required step:**

Independently read the article yourself and list every named tool/brand/company mentioned — this is something you're already good at and are doing anyway while reading the article in step 1. For every brand on your list that is **not** already in `found`'s names:

```bash
python scripts/register_brand.py --name "<Brand Name>" --domain <its domain if known>
# -> fetches its icon AND permanently appends it to known-brands.json.
# Idempotent — safe to call even if it might already be registered.
# Every future article mentioning this brand will now find it via the fast
# dictionary lookup in extract_entities.py, with no manual step needed again.
```

This makes the dictionary grow automatically through normal use: the first article to mention a given brand is the only one that ever needs this extra step for it.

```bash
# 2b. Which 3 of the 5 concept types fit this article? (scored heuristic:
#     €/% figures -> stat_highlight, "vs."/contrast framing -> before_after_split,
#     2+ entities -> tool_composition, process language -> workflow_diagram,
#     network_hologram is always the generic fallback)
python scripts/select_concept_types.py --title "<article title>" --content-file draft.md --entity-count <len(found) from 2a>
# -> {"selected": ["<type1>", "<type2>", "<type3>"]}
```

For each of the 3 selected concept types:

```bash
# 2c. Pick a pose matching this concept's mood, excluding poses already used
#     this run (pass every filename picked so far in --already-used)
python scripts/select_pose.py --concept <type> --already-used <prior picks>
# -> absolute path to a real johannes-<mood>-<pose>-NN.png

# 2d. Write the headline yourself — this is the one step that genuinely needs
#     understanding, not a lookup. Distill the article's core hook/number/
#     argument into ALL-CAPS German, <= 6 words, <= 40 characters. For
#     stat_highlight it MUST contain a real €/% figure from the article —
#     never invent one. Then validate before building anything:
python scripts/validate_headline.py --text "<YOUR HEADLINE>" --concept <type>
# Non-zero exit = fix the headline and re-check. Do not proceed until it passes.

# 2e. Build the actual cover — this is the only step that writes pixels
python scripts/build_cover.py \
  --headline "<validated headline>" --subtext "<optional smaller second line>" \
  --concept <type> \
  --icon <icon_path from 2a, repeat --icon per entity, cap at 2 icons per cover> \
  --pose <path from 2c> \
  --person-side left \
  --output workspace/<slug>/cover-v<N>.png
```

**`--person-side` default is `left`** (person anchored left, big/dominant close crop, text+icons on the right) — per Johannes's direct feedback on 6 real A/B pairs, 4/6 preferred this over the original `right` layout (person right, text+icons left, more headroom). **This is a global default, not a per-concept-type rule** — the data doesn't support one; `stat_highlight` itself was a 1-1 split across the two sample articles. Use judgment (or accumulated feedback) to override with `--person-side right` for an individual cover if it reads better that way; don't hardcode it by concept type without more evidence than 1-2 samples per type.

**Known limitation, not yet automated:** `build_cover.py` doesn't (yet) programmatically detect a text/person overlap — it happened three times during development with different poses/text lengths before landing on safe defaults, and the mirrored `left` layout was specifically re-verified for face-clipping (Johannes flagged "face is lost" on 2 of the 4 old A/B pairs that used this tighter crop). After building, view the result with the Read tool; if the person's silhouette overlaps the headline text or their head is cut off, rebuild with `--inset-frac` raised (keeps more of the person visible inside the frame — try 0.85–0.95) or lowered (crops tighter — try 0.60–0.80), and/or `--height-frac` lowered (shrinks the person — try 0.85–0.95). This is the one manual check left in an otherwise fully scripted pipeline.

### 3. Section/inline images — unchanged, still Gemini, no Johannes

Section images illustrate whatever that specific part of the article is explaining — they are **not** smaller covers, and this is a genuinely different job from cover generation, so it keeps using Gemini directly:

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
- No forced person, no headline badge. Skip any section that would just re-render a table/comparison the article already shows as text.
- Loosely keep the brand feel (Montserrat, `#1cb5e0` accent) so the set reads as one family, but the background doesn't need to match the covers' dark grid exactly — a comparison table on a lighter neutral background is fine and often clearer.
- **View every generated section image with the Read tool. Regenerate anything with garbled/broken German text, wrong logos, or visual clutter — max 2 retries each, then flag it and skip pushing it.** (This check still applies here — section images are still Gemini-generated and can still fail this way; covers can't anymore.)

### Cover concept types

The 5 types `select_concept_types.py` scores and picks 3 from. All 5 currently share the same visual template (background + icon row + headline text + person) — they differ in **which icons get shown, how the headline is framed, and which pose is selected**, not in a distinct AI-generated diagram/hologram graphic. An earlier version of this skill described a glowing circuit-diagram or network-hologram flourish behind the icons; that's not implemented in the deterministic pipeline yet (would mean reintroducing a small, bounded Gemini call for just that decorative element, cropped/masked so it can't collide with anything else). Ask before adding it back if a cover set feels visually flat — for now the plain version is the deliberately-chosen default.

1. **`stat_highlight`** — a big number/percentage as the headline (`"35 MIO. €"` + subtext), triggered by a €/% figure appearing early in the article.
2. **`before_after_split`** — a contrast-framed headline (`"UNGEKLÄRT ODER DSGVO-KONFORM?"`), triggered by "vs."/comparison language.
3. **`tool_composition`** — triggered when 2+ named entities are found; typically gets 2 icons side by side with a bold "VS" or similar.
4. **`workflow_diagram`** — triggered by process/step language in the article.
5. **`network_hologram`** — the generic fallback, always scored, guarantees there's always a valid 3rd pick.

### 4. Verify, then push

Nothing gets uploaded before it's checked — the webhook only ever receives images that already passed.

1. **Covers:** view each with the Read tool, checking only for the text/person overlap described in step 2 (everything else — spelling, logo colors, likeness — is guaranteed by construction and doesn't need re-checking). **Section images:** full visual check per step 3 above (garbled text, wrong logos, clutter — max 2 retries, then flag and skip).
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

## Asset library reference

- `assets/known-brands.json` — the entity dictionary `extract_entities.py` matches against. **Self-growing, not hand-maintained**: `register_brand.py` appends to it automatically the first time a new brand is registered (see step 2a) — don't edit it by hand as routine maintenance; that doesn't scale once this skill is distributed to people who aren't its maintainer.
- `assets/tool-logos/` — cached real brand icons, fetched via `fetch_tool_icon.py` (Simple Icons CDN when the environment has system `cairo`, falling back automatically — not as an error — to Google's favicon service when it doesn't; this is expected behavior in most cloud sandboxes, not a degraded state to fix).
- `assets/institutional-logos/eu-flag.png` — geometrically exact EU flag (12 gold stars, official blue), generated once by a small deterministic script, not AI-drawn, for any DSGVO/GDPR/EU-AI-Act-themed cover. Extend this folder + `known-brands.json`'s `institutional` list for other recurring institutional symbols.
- `assets/headshots/real-photos/johannes-<mood>-<pose>-NN.png` — the real photo library `select_pose.py` picks from (already-transparent PNGs). Filenames are the only interface — name new photos with an accurate mood keyword (`serious`, `frowning`, `skeptical`, `thinking`, `smiling`, etc.) so they're discoverable; `select_pose.py`'s `CONCEPT_MOODS` mapping decides which moods each concept type prefers.
- `assets/fonts/Montserrat-Variable.ttf` — the real brand typeface, bundled in-repo so text rendering never depends on whatever fonts happen to be installed in a given sandbox.

## Attribution

Image generation approach (for section/inline images, and originally for covers before the deterministic rewrite) adapted from the YouTube Thumbnail skill built by Tyler Germain (@itstylergermain) at Friday Labs.
