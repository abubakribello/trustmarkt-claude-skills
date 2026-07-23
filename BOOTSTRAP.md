# Bootstrap (put this in your routine / agent prompt)

The routine prompt should contain nothing but this — all real logic lives in this repo so it can be updated centrally:

```
You automate Trustmarkt content. First, fetch the latest instructions:

  git clone --depth 1 https://github.com/abubakribello/trustmarkt-claude-skills.git tm-skills

(or, without git:
  curl -sL https://raw.githubusercontent.com/abubakribello/trustmarkt-claude-skills/main/skills/trustmarkt-article-writer/SKILL.md
  ...and the scripts under the same path.)

Then decide based on the trigger payload:
- Payload has a topic, review, or nothing (scheduled run) -> read and follow
  tm-skills/skills/trustmarkt-article-writer/SKILL.md
- Payload has a YouTube video URL/ID -> same skill, Mode 1b (video as source)
- Payload asks for a case study / Fallstudie or has a review ID for one -> read and follow
  tm-skills/skills/trustmarkt-case-study-writer/SKILL.md

After an article draft is created, the article skill chains into
tm-skills/skills/trustmarkt-article-images/SKILL.md to generate cover + section
images and upload them to Google Drive.

Environment variables: TRUSTMARKT_API_TOKEN (API), GEMINI_API_KEY (images —
if unset, skip images and note it in the report).
Always follow the SKILL.md files from the repo, not from memory — they may have changed.
```

That's it. Never copy the skill content into the routine itself.
