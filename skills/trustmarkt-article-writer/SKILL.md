---
name: trustmarkt-article-writer
description: Write and publish German SEO articles to Trustmarkt (trustmarkt.de / Agenturmarkt.de / Expertenmarkt.de) via the Trustmarkt REST API, including scheduled topic discovery — researching questions the target group searches for (e.g. "Lohnt sich n8n für Agenturen", "Ist Claude datenschutzkonform") and systematically covering them over time. Use this skill whenever the user asks to create, draft, write, or publish an article, blog post, Magazin-Artikel, or SEO content on Trustmarkt, Agenturmarkt, or Expertenmarkt — including scheduled daily/weekly runs with no explicit topic, and external triggers via webhook/n8n/routine with a topic or review payload. Also use it to list or update existing Trustmarkt articles.
---

# Trustmarkt Article Writer

Create German-language articles on the company's Trustmarkt profile via the REST API. Articles are created as drafts (`DRAFT` status), then go through Trustmarkt's review flow (`SUBMITTED` → `APPROVED`/`REJECTED`). The API cannot publish directly — creating a clean, complete draft is the goal.

## Authentication

All calls need a Bearer token. Resolution order:

1. `TRUSTMARKT_API_TOKEN` environment variable
2. A `--token` argument passed to the helper script
3. If neither exists, ask the user for their token (generated in the Trustmarkt dashboard under API settings). Never hardcode tokens into files.

Base URL: `https://api.trustmarkt.de/v1`

## Two modes

**Mode 1 — Explicit topic:** the user or trigger payload names a topic or review. Follow the workflow below directly.

**Mode 1b — YouTube video as source:** the trigger payload contains a YouTube URL/ID (e.g. a new video was published on the company channel). Fetch the transcript first:

```bash
pip install youtube-transcript-api --break-system-packages   # once per environment
python scripts/youtube_transcript.py "<url-or-id>" --out transcript.txt
```

Then treat the video as **inspiration, not a script**: extract the core question the video answers, its key arguments, concrete numbers/examples, and 1–2 quotable statements. Write a standalone SEO article that fully answers that question for someone who never watches the video — reframe the video's topic as a search query the target group would type (see patterns below) and use that as the title. Link the video once in the article ("Im Video ausführlich erklärt: [Titel](URL)") — links are API-safe, embeds/images are not. If no transcript exists, use the video title as topic seed and research the topic via web search instead; note this in the report.

Before writing, still check `list-articles` — if the video's topic is already covered, write a complementary angle instead of a duplicate.

**Mode 2 — Topic discovery (scheduled daily/weekly runs, no topic given):** the goal is to systematically cover, over many runs, the questions the target group actually searches for. Do this before the writing workflow:

1. **Load coverage.** Fetch ALL existing article titles (paginate `list-articles` until `meta.last_page`). These are the covered topics.
2. **Generate candidates.** Combine two sources:
   - *Pattern grid:* expand the question patterns below with current tools/services relevant to the audience (agencies, experts, coaches, consultants — and their clients).
   - *Live research:* web-search for what the target group is currently asking (German queries; check "People also ask"-style phrasings, Reddit/Foren, current tool news). Fresh, news-driven questions rank faster than evergreen ones everyone has covered.
3. **Pick ONE topic** not yet covered (compare against existing titles semantically, not just string match). Prefer: high search intent, clear buying relevance, currently trending, and specific over generic — "Lohnt sich n8n für Agenturen" beats "Was ist Automatisierung".
4. Then write it via the workflow below. Report which topic was chosen and why, plus 2–3 runner-up topics so the backlog is visible.

### Question patterns of the target group

Expand these with concrete tools/branches (X = tool/service, Y = audience segment):

- Lohnt sich X? / Lohnt sich X für Y? (Lohnt sich n8n für Agenturen?)
- Ist X datenschutzkonform / DSGVO-konform? (Ist Claude datenschutzkonform?)
- X vs. Z: Was ist besser für Y?
- Was kostet X? / Was kostet eine gute Y-Agentur?
- Wie finde ich eine seriöse Y-Agentur / einen guten Coach?
- X Erfahrungen / X Test / X Alternativen
- Wie viel kostet [Leistung] wirklich? Woran erkennt man Qualität bei [Leistung]?

## Workflow

1. **Gather context first.** Before writing, pull real company data so the article is grounded, not generic:
   ```bash
   python scripts/trustmarkt_api.py me                     # company profile, name, category
   python scripts/trustmarkt_api.py list-reviews           # recent customer reviews
   python scripts/trustmarkt_api.py list-articles          # existing articles (avoid duplicate topics, match tone)
   python scripts/trustmarkt_api.py list-case-studies      # case studies to reference/link
   ```
   If the trigger payload (webhook/n8n) already contains a topic or review, use it as the seed but still check existing articles to avoid duplicating a topic.

2. **Draft the article in German** following the content rules below. Write the draft to a local `.md` file first so the user can inspect it and so failed API calls lose nothing.

3. **Create the draft on Trustmarkt:**
   ```bash
   python scripts/trustmarkt_api.py create-article --title "..." --content-file draft.md
   ```
   The script validates constraints before sending. On success it prints the article ID, slug, and status.

4. **Report back** with the article ID, title, word count, and a reminder that images must be added in the Trustmarkt web editor and the article submitted for review there.

To revise an existing draft: `python scripts/trustmarkt_api.py update-article --id <ID> --title "..." --content-file draft.md`. Only `DRAFT` or `REJECTED` articles can be updated — the API returns 422 otherwise.

## Content rules (German)

Write in professional German with **Sie-Form**. Target audience: businesses researching agencies, experts, coaches and consultants — the article should build trust and demonstrate expertise, not sell aggressively.

- Length: aim for 800–1,500 words unless the user asks otherwise
- Structure: short intro paragraph (no H1 — the title is the H1), then H2 sections, H3/H4 subsections where useful
- SEO: work the main keyword into the title, the first paragraph, and at least two H2s naturally; answer the search intent directly
- End with a short practical conclusion ("Fazit")
- Concrete beats abstract: use numbers, examples, and steps. If reviews/case studies were fetched, reference real outcomes (anonymized unless public)

### Hard API constraints (validated by the script)

- Title: 10–90 characters
- Content: Markdown, max 50,000 characters
- Supported Markdown ONLY: `##`/`###`/`####` headings, **bold**, _italic_, [links](https://example.com), lists, `---` dividers. GFM tables and `:::faq` / `:::callout` directives are accepted on update and generally render, but keep them optional
- Raw HTML is stripped server-side — never use HTML tags
- No images via API (add them later in the web editor); mention this in your final report
- Max 50 articles may sit in DRAFT/SUBMITTED/REJECTED at once — if creation fails with 422 mentioning the limit, list articles and tell the user which drafts to publish or delete

### Example title/structure

Titel: `Website-Relaunch: 7 Fehler, die Agenturen ihre Kunden kosten`

```markdown
Ein Website-Relaunch entscheidet oft über Sichtbarkeit und Umsatz. …

## Fehler 1: Kein Redirect-Konzept

…

## Fehler 2: …

---

## Fazit

…
```

## Error handling

- `401` → token invalid/missing: ask the user for a fresh token
- `422` → print the `errors` object verbatim; usually a length violation or the 50-draft limit
- `429` → wait 30s and retry once; if it persists, report and stop
- Never retry blindly more than once; report failures with the exact API message
