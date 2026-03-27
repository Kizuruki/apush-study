#!/usr/bin/env python3
"""
extract_fiveable_raw.py
-----------------------
Walks notes/fiveable/ for topic_* folders, extracts clean text from
each index.html, and writes src/data/fiveable_raw.json.

Folder naming expected:
  notes/fiveable/topic_1_2/index.html  -> key "1.2"
  notes/fiveable/topic_3_10/index.html -> key "3.10"
  notes/fiveable/overview_1/           -> skipped (not a topic)

Run from your repo root:
  python extract_fiveable_raw.py
"""

import os
import json
import re
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Installing beautifulsoup4...")
    os.system("pip install beautifulsoup4 -q")
    from bs4 import BeautifulSoup


FIVEABLE_DIR = Path("notes/fiveable")
OUTPUT_PATH  = Path("src/data/fiveable_raw.json")

STRIP_TAGS = [
    "script", "style", "nav", "footer", "header", "aside",
    "noscript", "iframe", "svg", "button", "form", "input",
]

CLUTTER_PATTERNS = [
    "paywall", "modal", "cookie", "banner", "popup", "ad-",
    "advertisement", "social", "share", "signup", "login",
    "sidebar", "breadcrumb", "navbar", "footer", "header",
    "related", "recommend",
]


def is_clutter(tag):
    if not hasattr(tag, "attrs") or tag.attrs is None:
        return False

    for attr in ("class", "id"):
        val = tag.get(attr)

        if attr == "class":
            if isinstance(val, list):
                val = " ".join(val)
            elif val is None:
                val = ""
        else:
            val = val or ""

        if any(p in val.lower() for p in CLUTTER_PATTERNS):
            return True

    return False


def extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all(STRIP_TAGS):
        tag.decompose()

    for tag in soup.find_all(True):
        if not hasattr(tag, "name"):
            continue
        if is_clutter(tag):
            tag.decompose()

    body = (
        soup.find("main")
        or soup.find("article")
        or soup.find(id=re.compile(r"content|main|body", re.I))
        or soup.find(class_=re.compile(r"content|main|body|guide", re.I))
        or soup.body
    )

    if not body:
        return ""

    lines = []
    for elem in body.descendants:
        if elem.name in ("h1","h2","h3","h4","h5","h6"):
            text = elem.get_text(" ", strip=True)
            if text:
                lines.append(f"\n## {text}\n")
        elif elem.name in ("p", "li", "dt", "dd", "td", "th", "blockquote"):
            text = elem.get_text(" ", strip=True)
            if text and len(text) > 20:
                lines.append(text)

    raw = "\n".join(lines)
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    cleaned = "\n".join(
        line for line in raw.splitlines()
        if len(line.strip()) > 1
    )

    return cleaned.strip()


def folder_to_topic_id(folder_name: str):
    """topic_1_2 -> '1.2',  topic_3_10 -> '3.10',  anything else -> None"""
    m = re.fullmatch(r"topic_(\d+)_(\d+)", folder_name)
    if not m:
        return None
    return f"{m.group(1)}.{m.group(2)}"


def main():
    if not FIVEABLE_DIR.exists():
        print(f"ERROR: {FIVEABLE_DIR} not found. Run from your repo root.")
        return

    result = {}
    folders = sorted(FIVEABLE_DIR.iterdir())

    for folder in folders:
        if not folder.is_dir():
            continue

        topic_id = folder_to_topic_id(folder.name)
        if topic_id is None:
            print(f"  Skipping {folder.name}")
            continue

        index_html = folder / "index.html"
        if not index_html.exists():
            print(f"  MISSING index.html in {folder.name}")
            continue

        html = index_html.read_text(encoding="utf-8", errors="replace")
        text = extract_text(html)

        if len(text) < 100:
            print(f"  WARNING: very short text for {topic_id} ({len(text)} chars)")
        else:
            print(f"  OK  {topic_id:6s}  {len(text):,} chars  ({folder.name})")

        result[topic_id] = text

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"\nWrote {len(result)} topics to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
