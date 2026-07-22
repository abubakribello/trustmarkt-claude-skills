#!/usr/bin/env python3
"""Fetch title + transcript for a YouTube video, for use as article source material.

Usage:
  python youtube_transcript.py <video-url-or-id> [--lang de en] [--out transcript.txt]

Requires: pip install youtube-transcript-api --break-system-packages
"""
import argparse
import json
import re
import sys
import urllib.request


def video_id(url_or_id):
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url_or_id):
        return url_or_id
    m = re.search(r"(?:v=|youtu\.be/|shorts/|embed/)([A-Za-z0-9_-]{11})", url_or_id)
    if not m:
        sys.exit(f"Could not extract a video ID from: {url_or_id}")
    return m.group(1)


def fetch_title(vid):
    try:
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json"
        with urllib.request.urlopen(url, timeout=15) as r:
            return json.loads(r.read().decode()).get("title", "")
    except Exception:
        return ""


def main():
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("--lang", nargs="+", default=["de", "en"])
    p.add_argument("--out")
    args = p.parse_args()

    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        sys.exit("Missing dependency. Run: pip install youtube-transcript-api --break-system-packages")

    vid = video_id(args.video)
    title = fetch_title(vid)

    try:
        api = YouTubeTranscriptApi()
        transcript = api.fetch(vid, languages=args.lang)
        segments = list(transcript)
    except Exception:
        # Older API versions
        try:
            segments = YouTubeTranscriptApi.get_transcript(vid, languages=args.lang)
        except Exception as e:
            sys.exit(f"No transcript available for {vid} ({e}). "
                     "Fall back to: video title/description as topic seed, or ask the user for key points.")

    def text(seg):
        return seg.text if hasattr(seg, "text") else seg.get("text", "")

    full = " ".join(text(s).replace("\n", " ").strip() for s in segments if text(s).strip())
    output = f"TITLE: {title}\nVIDEO_ID: {vid}\nURL: https://www.youtube.com/watch?v={vid}\n\nTRANSCRIPT:\n{full}\n"

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Saved {len(full)} chars to {args.out}")
    else:
        print(output)


if __name__ == "__main__":
    main()
