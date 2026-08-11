#!/usr/bin/env python3
"""Core engine for cover AND section-image generation (as of 2026-08-06,
replacing the fully-deterministic Pillow pipeline in build_cover.py as the
default path — see SKILL.md's "Cover & section-image generation" section
for the full story of why).

Each image is ONE Gemini call that composites a real photo of Johannes
together with icons/diagrams/stat-cards/headline text into a single
cohesive, dramatically-lit scene, using one of 7 proven templates (A-G,
documented in SKILL.md). This produces far more visual richness ("wow
factor") than the old flat Pillow layering — validated directly against
Johannes's own reference thumbnails, and preferred by both Johannes and
Abubakri once the face-fidelity issue below was fixed.

The one non-negotiable rule that makes this safe to use: the person's
face is NEVER regenerated. Every prompt in this file carries FACE_LOCK
verbatim, and every call passes a real, unedited photo from
assets/headshots/real-photos/ as a reference image — never an
AI-regenerated pose. An earlier attempt at this (having Gemini regenerate
Johannes in new poses while "preserving the face") produced likeness
drift Johannes flagged directly once compared side-by-side with real
photos — real photos composited by Gemini, not AI-redrawn people, is
what actually holds likeness.

Text and labels are still a real risk (Gemini can misspell/invent extra
items, or recolor a logo) — always view the result and check
spelling/counts/colors before delivering; retry with a more explicit
count/spelling constraint if something's off (see build_g's "EXACTLY
THREE... no more" wording — that fixed a real duplicate-card bug during
development).

Usage: import the seven build_* functions from another script (both for
covers and for section images — same engine, different template pick per
call), or run this file directly for a quick smoke test.
"""
import os
import sys
from pathlib import Path
from PIL import Image
from google import genai
from google.genai import types

ROOT = Path(__file__).parent.parent
REAL_PHOTOS = ROOT / "assets" / "headshots" / "real-photos"

# Verbatim per Johannes's direct instruction (2026-08-05) after the
# AI-regenerated-pose experiment produced faces he didn't like — real,
# unedited photos only, never let Gemini touch the face at all.
FACE_LOCK = (
    "NEVER modify the human reference image expression or features. "
    "Insert the person exactly as shown, unchanged, into the design."
)

MODEL = "gemini-3-pro-image-preview"


def _client():
    return genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def compose(prompt, ref_paths, out_path, aspect="16:9"):
    """Core Gemini call: prompt + reference images -> one composited PNG."""
    refs = [Image.open(p) for p in ref_paths]
    client = _client()
    resp = client.models.generate_content(
        model=MODEL,
        contents=[prompt] + refs,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio=aspect),
        ),
    )
    for part in resp.candidates[0].content.parts:
        if part.inline_data:
            Path(out_path).write_bytes(part.inline_data.data)
            print(f"Saved {out_path}")
            return out_path
    sys.exit(f"No image returned from Gemini for {out_path}")


def _icon_fragment(icon, index_word):
    """icon is either a real logo file path (exact color/shape preserved,
    added as a reference image) or a plain text description (an original
    generic icon Gemini invents — safe for non-brand concepts like a
    clock or a euro-coin stack, since there's no 'correct' logo to get
    wrong). Returns (prompt_fragment, ref_path_or_None)."""
    if isinstance(icon, (str, Path)) and Path(icon).exists():
        return (f"the {index_word} logo shown in its reference image, preserving its "
                f"exact shape and color, do not redesign or recolor it"), Path(icon)
    return f"an original glowing dark 3D icon tile of {icon}", None


# --- A: minimal text + portrait -------------------------------------------

def build_a(photo, headline, output, person_side="right"):
    """Plain question/identity headline, no icons. Safest template — zero
    icon/label fidelity risk. Good as one of the 3 picks almost every time."""
    text_side = "left" if person_side == "right" else "right"
    prompt = (
        f"{FACE_LOCK} Compose this reference image into a dramatic 16:9 dark "
        f"video-cover scene. The person pose and shirt stay as shown. Position "
        f"the person on the {person_side} side of the frame, upper body "
        f"visible. Near-black dark background with a very subtle grid, no "
        f"other graphics, no icons. On the {text_side} side render this exact "
        f"headline in large bold white all-caps letters, spelled exactly, "
        f"perfectly legible: {headline}. Photorealistic, cinematic lighting, "
        f"no colored glow."
    )
    return compose(prompt, [photo], output)


# --- B: two-icon comparison -------------------------------------------

def build_b(photo, headline, left_icon, left_label, right_icon, right_label, output):
    """Two things weighed against each other (e.g. time vs money, tool A vs
    tool B). Pass a real logo file path for a brand, or a text description
    for a generic concept icon."""
    left_frag, left_ref = _icon_fragment(left_icon, "left")
    right_frag, right_ref = _icon_fragment(right_icon, "right")
    refs = [photo] + [r for r in (left_ref, right_ref) if r]
    prompt = (
        f"{FACE_LOCK} Compose these reference images into one single, cohesive, "
        f"dramatic 16:9 dark video-cover scene. The person pose and shirt stay "
        f"as shown. Position the person centered in the frame, upper body "
        f"visible. Render {left_frag} very large and glowing on the LEFT side "
        f"of the frame at head height, and below it small bold white text: "
        f"{left_label}. Render {right_frag} very large and glowing on the "
        f"RIGHT side of the frame at matching size and height, and below it "
        f"small bold white text: {right_label}. Matching dramatic studio "
        f"lighting so all elements look like one integrated scene. Near-black "
        f"dark background, subtle grid. At the very top render this exact "
        f"headline in large bold white all-caps letters, spelled exactly, "
        f"perfectly legible: {headline}. Photorealistic, cinematic."
    )
    return compose(prompt, refs, output)


# --- C: labeled icon orbit -------------------------------------------

def build_c(photo, headline, items, output):
    """items: list of exactly 4 (icon, label) pairs, arranged in an orbit
    with dashed connector lines to a hub above the person's head. Best fit
    for a scoring framework / checklist / multi-factor breakdown."""
    assert len(items) == 4, "build_c needs exactly 4 (icon, label) items"
    positions = ["top-left", "top-right", "lower-left", "lower-right"]
    refs = [photo]
    icon_lines = []
    for (icon, label), pos in zip(items, positions):
        frag, ref = _icon_fragment(icon, pos)
        if ref:
            refs.append(ref)
        icon_lines.append(f"{pos}: {frag}, labeled {label}")
    icons_desc = "; ".join(icon_lines)
    prompt = (
        f"{FACE_LOCK} Compose these reference images into a dramatic 16:9 dark "
        f"video-cover scene. The person pose and shirt stay as shown. Position "
        f"the person in the lower-center of the frame, upper body visible, "
        f"leaving the upper area clear. Render four glowing icon tiles in an "
        f"orbit around a point above the person's head, each connected to a "
        f"shared center hub by a thin glowing dashed cyan line: {icons_desc}. "
        f"All labels bold white all-caps, spelled exactly, perfectly legible. "
        f"At the bottom render this exact headline in large bold white "
        f"all-caps letters, spelled exactly, perfectly legible: {headline}. "
        f"Near-black dark background with subtle grid. Nothing overlapping "
        f"the face or headline. Photorealistic, cinematic lighting."
    )
    return compose(prompt, refs, output)


# --- D: icon halo (scattered, unlabeled) -------------------------------------------

def build_d(photo, headline, icons, output):
    """icons: 3-4 icons scattered organically around the person, no labels,
    no connector lines. Good for 'what's at stake' / ecosystem framing."""
    refs = [photo]
    icon_descs = []
    for i, icon in enumerate(icons):
        frag, ref = _icon_fragment(icon, f"icon {i+1}")
        if ref:
            refs.append(ref)
        icon_descs.append(frag)
    icons_joined = "; ".join(icon_descs)
    prompt = (
        f"{FACE_LOCK} Compose these reference images into a dramatic 16:9 dark "
        f"video-cover scene. The person pose and shirt stays as shown. "
        f"Position the person centered in the frame, upper body visible, "
        f"leaving the lower-left area clear for a headline. Scatter these "
        f"original glowing dark 3D icon tiles (dark glass rounded-square "
        f"tiles with glowing edges, matching style across all of them) "
        f"organically around the person, varied sizes, no connecting lines, "
        f"no labels: {icons_joined}. In the lower-left render this exact "
        f"headline in large bold white all-caps letters, spelled exactly, "
        f"perfectly legible, not overlapped: {headline}. Near-black dark "
        f"background with subtle grid. Photorealistic, cinematic lighting."
    )
    return compose(prompt, refs, output)


# --- E: AI-prompt-box mockup -------------------------------------------

def build_e(photo, headline, prompt_text, output, person_side="left"):
    """Fake chat-input UI (PROMPT label + typed question + send button).
    Fits content framed as 'the question you'd ask an AI advisor'."""
    text_side = "right" if person_side == "left" else "left"
    prompt = (
        f"{FACE_LOCK} Compose this reference image into a dramatic 16:9 dark "
        f"video-cover scene. The person pose and shirt stay as shown. Position "
        f"the person on the {person_side} side of the frame, upper body "
        f"visible. On the {text_side} side, at the top, render this exact "
        f"headline in large bold white all-caps letters, spelled exactly, "
        f"perfectly legible: {headline}. Below the headline, render a dark "
        f"rounded-rectangle chat-input UI box with a thin border: a small "
        f"grey label reading PROMPT in the top-left of the box, and below it "
        f"in white text the exact sentence: {prompt_text}, and a small "
        f"glowing blue circular send button with a white right-pointing "
        f"arrow icon inside it at the right edge of the box, fully contained "
        f"within the box border. Near-black dark background with subtle "
        f"grid. Photorealistic, cinematic lighting."
    )
    return compose(prompt, [photo], output)


# --- F: workflow / process node-flow -------------------------------------------

def build_f(photo, headline, nodes, output):
    """nodes: 3-5 short labels forming a left-to-right pipeline above the
    person's head. Fits any 'step 1 -> step 2 -> ... -> done' content."""
    node_chain = ", then ".join(nodes)
    prompt = (
        f"{FACE_LOCK} Compose this reference image into a dramatic 16:9 dark "
        f"video-cover scene. The person pose and shirt stay as shown. "
        f"Position the person centered in the LOWER part of the frame only, "
        f"so the whole upper half of the frame is free of the person. Above "
        f"the person, render a CLEAR diagram: exactly {len(nodes)} connected "
        f"node boxes forming one obvious left-to-right pipeline flow across "
        f"the upper half of the frame, each a small rounded rectangle with a "
        f"short label inside it, spelled exactly, legible: {node_chain} — in "
        f"that left-to-right order, connected by smooth glowing cyan cable "
        f"lines with a small arrow at each connection. Keep this node row "
        f"well above the person's head with clear vertical gap, not touching "
        f"or overlapping the head or face at all. At the very top of the "
        f"frame render this exact headline in large bold white all-caps "
        f"letters, spelled exactly, perfectly legible: {headline}. "
        f"Near-black dark background. Photorealistic, cinematic lighting."
    )
    return compose(prompt, [photo], output)


# --- G: stat cards -------------------------------------------

def build_g(photo, headline, cards, output, person_side="right"):
    """cards: list of exactly 3 (big_stat, small_label) pairs — real numbers
    beat generic icons here. Leads with proof, not theory; strong closer
    pick alongside A (question) and C or F (method)."""
    assert len(cards) == 3, "build_g needs exactly 3 (stat, label) cards"
    text_side = "left" if person_side == "right" else "right"
    card_desc = ". ".join(
        f"card {i+1} ({pos}) showing large bold text {stat} and below it "
        f"smaller text {label}"
        for i, ((stat, label), pos) in enumerate(zip(cards, ["top", "middle", "bottom"]))
    )
    prompt = (
        f"{FACE_LOCK} Compose this reference image into a dramatic 16:9 dark "
        f"video-cover scene. The person pose and shirt stay as shown. "
        f"Position the person on the {person_side} side of the frame, upper "
        f"body visible, not extreme close-up, leaving the {text_side} "
        f"two-thirds of the frame clear. On the {text_side} side, render "
        f"EXACTLY THREE small bordered dark UI stat cards (rounded "
        f"rectangle, thin border, dark glass panel), stacked vertically, "
        f"clearly separated, not overlapping each other or the person, no "
        f"more than three cards: {card_desc}. All text spelled exactly as "
        f"given, perfectly legible bold white text, the big numbers in a "
        f"bright glowing blue accent color. Between the cards, to their "
        f"{text_side} edge, render this exact headline in large bold white "
        f"all-caps letters, spelled exactly, perfectly legible: {headline}. "
        f"Near-black dark background with subtle grid. Photorealistic, "
        f"cinematic lighting."
    )
    return compose(prompt, [photo], output)


TEMPLATES = {"A": build_a, "B": build_b, "C": build_c, "D": build_d,
             "E": build_e, "F": build_f, "G": build_g}


if __name__ == "__main__":
    # Quick smoke test — template A with the neutral headshot.
    out = ROOT / "workspace" / "smoke-test-A.png"
    build_a(str(REAL_PHOTOS / "johannes-serious-headshot-01.png"),
            "SMOKE TEST", str(out))
    print(f"Smoke test complete: {out}")
