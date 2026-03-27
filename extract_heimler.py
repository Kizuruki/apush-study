"""
extract_heimler.py — Processes Heimler Review Guide PDFs from notes/heimler/
and outputs src/data/heimler_notes.json

Usage:
    python extract_heimler.py
    python extract_heimler.py --resume

Requirements:
    pip install openai pdfplumber
"""

import json, os, re, time, argparse
from pathlib import Path
import pdfplumber
from openai import OpenAI

PDF_DIR = Path("notes/heimler")
OUTPUT  = Path("src/data/heimler_notes.json")
RAW_OUTPUT = Path("src/data/heimler_raw.json")

# Map known Heimler section titles → CED topic IDs
SECTION_TO_TOPICS = {
    "native american": ["1.2"],
    "here come the europeans": ["1.3", "1.5"],
    "columbian exchange": ["1.4", "1.6"],
    "cultural interactions": ["1.4", "1.6"],
    "act i": ["3.2", "3.3", "3.4"],
    "act ii": ["3.5", "3.6", "3.7", "3.8", "3.9"],
    "act iii": ["3.10", "3.11"],
    "world power": ["4.2"],
    "modern economy": ["4.5"],
    "modern democracy": ["4.7", "4.8"],
    "modern society": ["4.6", "4.10", "4.11"],
    "singular": ["4.13"],
    "westward migration": ["6.3"],
    "american industrialization": ["6.5", "6.6"],
    "labor in the gilded": ["6.7", "6.8"],
    "government": ["6.11", "6.12"],
    "imperialism": ["7.2"],
    "spanish-american": ["7.3"],
    "progressive era": ["7.4"],
    "world war i": ["7.5", "7.6"],
    "roaring": ["7.7", "7.8"],
    "great depression": ["7.9", "7.10"],
    "mobilization": ["7.12"],
    "fighting ww": ["7.13"],
    "reagan": ["9.2"],
    "cold war": ["9.3"],
    "changing economy": ["9.4"],
    "migration and immigration": ["9.5"],
    "challenges": ["9.6"],
}

def extract_text(pdf_path):
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t: pages.append(t)
    return "\n".join(pages)

def map_to_topics(section_title):
    sl = section_title.lower()
    for key, topics in SECTION_TO_TOPICS.items():
        if key in sl:
            return topics
    return []

def summarize_section(client, section_title, content, topic_ids):
    prompt = f"""You are extracting AP US History study notes from a Heimler Review Guide.

SECTION: "{section_title}"
CED TOPICS: {', '.join(topic_ids)}
CONTENT:
{content[:2000]}

Extract concise study notes (150-300 words) focusing on:
- Key events and their causes/effects
- Important people and significance
- AP exam connections
- Specific examples and dates

Write as bullet points. Be specific and historically accurate."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}],
        max_tokens=400,
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        return

    if not PDF_DIR.exists():
        print(f"❌ {PDF_DIR} directory not found")
        print(f"   Create it and add your Heimler PDFs")
        return

    pdfs = list(PDF_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"❌ No PDFs found in {PDF_DIR}")
        return

    client = OpenAI(api_key=api_key)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    raw_heimler = {}
    if args.resume and RAW_OUTPUT.exists():
        with open(RAW_OUTPUT) as f:
            raw_heimler = json.load(f)
    existing = {}
    if args.resume and OUTPUT.exists():
        with open(OUTPUT) as f:
            existing = json.load(f)
        print(f"📂 Resuming — {len(existing)} topics already done")

    notes = dict(existing)

    print(f"\n{'='*55}")
    print(f"  Heimler PDF Extractor — {len(pdfs)} PDFs")
    print(f"{'='*55}\n")

    for pdf_path in sorted(pdfs):
        print(f"\n  Processing: {pdf_path.name}")
        try:
            text = extract_text(pdf_path)
            lines = text.split('\n')
            sections = {}
            current_section = None
            current_lines = []

            for line in lines:
                l = line.strip()
                if not l or '©' in l or 'HEIMLER' in l: continue
                # Section header detection
                if re.match(r'^ANSWERS\s+[A-Z]', l) or (l.isupper() and len(l) > 5 and l != 'ANSWERS'):
                    if current_section and current_lines:
                        sections[current_section] = '\n'.join(current_lines)
                    current_section = l.replace('ANSWERS ', '').title()
                    current_lines = []
                else:
                    if current_section:
                        current_lines.append(l)

            if current_section and current_lines:
                sections[current_section] = '\n'.join(current_lines)

            for sec_title, content in sections.items():
                topic_ids = map_to_topics(sec_title)
                if not topic_ids: continue

                for tid in topic_ids:
                    raw_heimler[tid] = content  # save raw PDF-extracted text
                    with open(RAW_OUTPUT, "w", encoding="utf-8") as f:
                        json.dump(raw_heimler, f, indent=2, ensure_ascii=False)
                    if args.resume and tid in notes: continue
                    print(f"    → Topic {tid} from '{sec_title}'")
                    try:
                        note = summarize_section(client, sec_title, content, topic_ids)
                        notes[tid] = note
                        with open(OUTPUT, "w", encoding="utf-8") as f:
                            json.dump(notes, f, indent=2, ensure_ascii=False)
                        time.sleep(0.8)
                    except Exception as e:
                        print(f"       ⚠ Error: {e}")

        except Exception as e:
            print(f"    ❌ Failed to process: {e}")

    print(f"\n{'='*55}")
    print(f"  ✅ Done! {len(notes)} topics have notes")
    print(f"  Output: {OUTPUT}")
    print(f"{'='*55}\n")

if __name__ == "__main__":
    main()
