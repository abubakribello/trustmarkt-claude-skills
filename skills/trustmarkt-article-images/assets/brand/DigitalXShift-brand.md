# DigitalXShift brand guide (extracted from client brand deck)

Source: brand guideline slides supplied directly by the client (pasted inline, not saved as files — transcribed here as text/hex values so the skill doesn't depend on having the original image). If a real logo export (PNG/SVG) becomes available, add it to this folder and reference it from `SKILL.md`.

## Colors

- **Gradient** (primary background/accent, diagonal dark-to-bright): `#000046` → `#1cb5e0`
- **Dunkel blau** (dark blue, solid): `#000046`
- **Black**: `#000000`
- **White**: `#ffffff`

Use `#1cb5e0` as the glow/accent color (badge borders, highlighted headline words, stat callouts) — this replaces the earlier generic teal placeholder (`#29D8F0`) used before the brand deck was supplied. Use the `#000046` → `#1cb5e0` diagonal gradient for backgrounds instead of a flat charcoal/black studio background, where it doesn't fight the photo subject.

## Typography

- **Montserrat** — the brand's only functional typeface, used for both headline/display and paragraph text. Ask Gemini for "bold Montserrat-style geometric sans-serif" headline text, not serif.
- Two script/signature fonts ("Smooth Fantasy", and a custom "Shift" script) appear only in the logo lockup itself (the stylized "Shift" wordmark tail) — decorative, not for body or headline text. Don't use script fonts for article headlines.

## Logo

Wordmark: "DIGITALX" in bold Montserrat (navy-to-cyan gradient matching the brand gradient) + "Shift" in a flowing script tail, plus a standalone icon (two parallel diagonal stripes forming a stylized "Z"/lightning-bolt shape) seen in the brand deck but not yet supplied as a separate file.

Two real logo files are now in this folder:
- `logo-wordmark-color.png` — full gradient-color wordmark, transparent background. Use on light/white sections of a composition.
- `logo-wordmark-white.png` — solid white wordmark, transparent background (near-invisible until placed on a dark background). Use on the dark-gradient background that's the default for covers/sections.

Pass the appropriate one as an extra `--refs` entry when generating, and instruct Gemini to place it small in a bottom corner as a subtle watermark (matching how the benchmark examples carry a small brand mark) — never large, never covering the subject or headline badge.

## Brand tone (from the "Branding Style" slider slide)

Leans clearly toward: **Warm** (not cold), **Progressive** (not nostalgic), **Accessible** (not overly serious), **Casual** (not corporate), **Simple** (not complex). Slightly casual-leaning on the formal/casual axis too.

Apply this to pose/expression choices: approachable and warm rather than stiff/corporate, confident but not severe, clean/uncluttered compositions rather than dense/busy ones.
