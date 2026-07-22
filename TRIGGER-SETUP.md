# Triggering the Trustmarkt Skills from Outside Claude

Two skills, pulled live from this repo (see `BOOTSTRAP.md`):

- **trustmarkt-article-writer** — fetches company context via the Trustmarkt API, writes a German article, creates it as a draft via `POST /articles`
- **trustmarkt-case-study-writer** — pulls a review via the API, generates a complete German case study content package matching Trustmarkt's schema (no store endpoint exists, so final creation happens in the web app)

Both need `TRUSTMARKT_API_TOKEN` (dashboard → API settings). Below are the two external trigger routes.

---

## Option A: n8n webhook → Claude API (recommended)

Fits the existing Trustmarkt ↔ n8n integration. Trustmarkt's official n8n Trigger Node fires on platform events (e.g. new review).

**Flow:** Trustmarkt Trigger Node (or Webhook node) → HTTP Request node → Anthropic Messages API → article lands in Trustmarkt as draft.

HTTP Request node configuration:

```
POST https://api.anthropic.com/v1/messages
Headers:
  x-api-key: {{ANTHROPIC_API_KEY}}
  anthropic-version: 2023-06-01
  content-type: application/json
Body:
{
  "model": "claude-sonnet-5",
  "max_tokens": 8000,
  "messages": [{
    "role": "user",
    "content": "Neue Bewertung eingegangen: {{ $json.review }}. Schreibe daraus einen Trustmarkt-Artikel / eine Fallstudie gemäß Skill."
  }]
}
```

For the article flow to actually POST to Trustmarkt, run the skill in an execution environment (Claude Code / Agent SDK / cloud routine — see Option B) rather than the plain Messages API, since the skill needs code execution. Alternative pure-n8n variant: let the Messages API return the finished Markdown, then add one more n8n HTTP Request node that does the `POST https://api.trustmarkt.de/v1/articles` itself with `{"title": ..., "content": ...}` and the Trustmarkt Bearer token. That keeps everything inside n8n.

## Option B: Claude Code cloud routine (webhook-triggered)

Claude Code routines run Claude with full tool access in the cloud, triggered by schedule or incoming webhook — the skill runs end-to-end including the API POST.

1. Install both skills into the Claude Code environment (Settings → Capabilities → Skills, or drop the folders into `.claude/skills/`).
2. Set `TRUSTMARKT_API_TOKEN` as an environment secret.
3. Create a routine at claude.ai/code/scheduled (or via `/routines` in Claude Code) with a webhook trigger and a prompt like:
   > "Payload enthält Topic oder Review-ID. Nutze trustmarkt-article-writer bzw. trustmarkt-case-study-writer, erstelle den Inhalt und lege Artikel als Draft über die API an. Fallstudien-Content als Datei ausgeben."
4. Point the Trustmarkt webhook (dashboard → Integrationen → Webhooks) or an n8n workflow at the routine's webhook URL.

**Scheduled variant:** same routine on a cron (e.g. weekly): "Prüfe neue Bewertungen der letzten 7 Tage und erstelle daraus einen Artikel-Draft." Or for topic discovery: "Führe einen Topic-Discovery-Lauf aus" (daily/weekly — the skill picks one uncovered SEO question per run).

## Option C: New YouTube video → article

Goal: every new video on the channel becomes source material for an article draft.

**Detecting a new video (n8n, no OAuth needed):** use the **RSS Feed Trigger** node with the channel feed:

```
https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID
```

(Find CHANNEL_ID on the channel page → source/share. Alternatively use n8n's YouTube Trigger node with Google OAuth.) The feed item gives you the video URL and title.

**Flow:** RSS Trigger → (optional filter, e.g. skip Shorts) → webhook call to the Claude Code routine (Option B) with payload `{"video_url": "...", "title": "..."}`.

**What the skill does with it (Mode 1b, built in):** installs `youtube-transcript-api`, pulls the video transcript via `scripts/youtube_transcript.py`, extracts the core question + key points + quotes, and writes a standalone SEO article answering that question — with one link back to the video. If the video has no captions, it falls back to using the title as topic seed plus web research. Duplicate topics are detected against existing articles first.

**Pure-n8n variant:** an n8n community node (e.g. a transcript node or an HTTP call to a transcript service) can fetch the transcript, which you then pass in the prompt to the Anthropic Messages API and POST the returned Markdown to `POST /v1/articles` yourself — same pattern as the Option A fallback.

---

## Constraints to remember

- Articles: created as **DRAFT**; review/publishing + images happen in the Trustmarkt web app. Max 50 drafts at once. Title 10–90 chars, Markdown only (H2–H4, bold, italic, links, lists, dividers), 50k char limit.
- Case studies: **no POST endpoint** — the skill outputs a paste-ready package for the web editor / Trustmarkt's AI tool. If Trustmarkt adds `POST /case-studies`, the skill's script can be extended in minutes.
