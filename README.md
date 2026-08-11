# Trustmarkt Claude Skills

Central source of truth for the Trustmarkt automation skills. Claude routines and other people's Claude setups pull the **latest** version of these instructions at runtime — update this repo, and every consumer gets the change on their next run without touching their routine config.

## Structure

```
BOOTSTRAP.md                                  <- the ONLY thing a routine needs (stable, tiny)
TRIGGER-SETUP.md                              <- how to wire external triggers (n8n, webhooks, RSS, cron)
skills/
  trustmarkt-article-writer/
    SKILL.md                                  <- full instructions: German SEO articles via POST /articles
    scripts/trustmarkt_api.py                 <- Trustmarkt REST API helper (validates constraints)
    scripts/youtube_transcript.py             <- transcript fetcher for video-triggered articles
  trustmarkt-case-study-writer/
    SKILL.md                                  <- full instructions: German case studies (no store endpoint -> paste-ready package)
    scripts/trustmarkt_api.py
```

## How consumers use this repo

A routine's prompt stays minimal — see `BOOTSTRAP.md`. It clones this repo (or fetches the raw files), reads the relevant `SKILL.md`, and follows it for the incoming payload.

## Secrets

No secrets live in this repo. Each environment sets:

- `TRUSTMARKT_API_TOKEN` — from the Trustmarkt dashboard (API settings)

## Updating

Edit the `SKILL.md` files / scripts here and commit to `main`. All routines pick up the change on their next run. For breaking changes, note them in the commit message; consumers always run latest `main`.
