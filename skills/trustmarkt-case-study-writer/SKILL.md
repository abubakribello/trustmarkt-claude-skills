---
name: trustmarkt-case-study-writer
description: Generate complete German case studies (Fallstudien) for Trustmarkt (trustmarkt.de / Agenturmarkt.de / Expertenmarkt.de), structured exactly to Trustmarkt's case study schema and based on real customer reviews pulled via the Trustmarkt REST API. Use this skill whenever the user asks to create, draft, or write a case study, Fallstudie, customer success story, or Referenz for Trustmarkt — including when triggered externally via webhook/n8n/routine with a review ID or customer name. Also use it to list or read existing Trustmarkt case studies.
---

# Trustmarkt Case Study Writer

Generate ready-to-paste German case studies matching Trustmarkt's exact case study structure.

**Important limitation:** The Trustmarkt API has **no create/store endpoint for case studies** (read-only: `GET /case-studies`). This skill therefore produces a complete, field-by-field content package that maps 1:1 to the fields in Trustmarkt's case study editor. The user pastes it into the web app (or feeds it to Trustmarkt's built-in AI case study tool). If Trustmarkt ships a `POST /case-studies` endpoint later, switch to posting directly.

## Authentication

Same as the article writer: `TRUSTMARKT_API_TOKEN` env var, `--token` flag, or ask the user. Base URL `https://api.trustmarkt.de/v1`. Never hardcode tokens.

## Workflow

1. **Gather source material via the API:**
   ```bash
   python scripts/trustmarkt_api.py me
   python scripts/trustmarkt_api.py list-reviews                       # find the review to build on
   python scripts/trustmarkt_api.py get-review --id <ID>              # full review content
   python scripts/trustmarkt_api.py list-case-studies --expand review # existing studies: tone + avoid duplicates
   python scripts/trustmarkt_api.py get-case-study --id <ID> --expand "review, content"  # study an existing one as a style reference
   ```
   A case study linked to a verified review is far more credible — if the trigger payload contains a review ID, build around that review. Otherwise pick the strongest recent review (high rating, concrete detail) and confirm the choice with the user if working interactively.

   If the user supplies extra material (project notes, KPIs, a transcript), that takes priority over inferred content. **Never invent metrics.** If no real numbers exist, ask for them or write qualitative results.

2. **Generate the content package** using the exact template below. Write it to `fallstudie-<kunde>.md`.

3. **Deliver** the file plus a short note listing what still happens in the web app: linking the verified review, uploading media/video, and publishing.

## Content package template

Fill every field. German, Sie-Form, konkret statt werblich. This maps 1:1 to Trustmarkt's `CaseStudyResource` fields:

```markdown
# Fallstudie: [Kundenname]

## Basisdaten
- **Titel** (max ~90 Zeichen, ergebnisorientiert): Wie [Kunde] mit [Leistung] [Ergebnis] erreichte
- **Anzeigetitel** (Kurzversion für Listen): …
- **Kunde**: [Name]
- **Kunden-Website**: [URL]
- **Branche**: [aus IndustryResource wählen, z. B. E-Commerce]
- **Zeitraum**: [start_date] – [end_date]
- **Verknüpfte Bewertung**: [Review-ID, falls vorhanden]

## Zusammenfassung (summary)
[2–3 Sätze: Ausgangslage → Maßnahme → Ergebnis. Wird in Listen/Previews angezeigt.]

## Kennzahlen (metrics)
- **Titel der Sektion**: z. B. "Die Ergebnisse in Zahlen"
- **Kennzahlen-Zusammenfassung**: [3–4 konkrete KPIs, z. B. "+30 % Umsatz, −20 % Absprungrate, 15 % mehr Traffic"]

## Herausforderung (problems)
- **Titel**: z. B. "Die Ausgangslage bei [Kunde]"
- **Inhalt**: [2–4 Absätze: konkrete Probleme, warum bisherige Ansätze scheiterten]

## Ziele (goals)
- **Titel**: z. B. "Die Ziele von [Kunde]"
- **Inhalt**: [1–3 Absätze: messbare Ziele, Prioritäten]

## Lösung & Ergebnisse (results)
- **Titel**: z. B. "Die Lösung und Ergebnisse"
- **Inhalt**: [3–5 Absätze: Vorgehen Schritt für Schritt, dann Ergebnisse mit Zahlen; ggf. Kundenzitat aus der Bewertung]

## Call-to-Action (cta)
- **Titel**: z. B. "Ähnliche Ergebnisse erzielen?"
- **Text**: [1–2 Sätze, Kontaktaufforderung]

## Über uns (about_section_text)
[1–2 Sätze über das eigene Unternehmen, aus dem me-Profil abgeleitet]
```

Quality bar: a reader should finish knowing exactly what was done, for whom, and with what measurable outcome. Quotes only verbatim from the actual review — never fabricated.

## Error handling

- `401` → ask for a fresh token
- `429` → wait 30s, retry once, then report
- Review not found → list reviews and ask which to use
