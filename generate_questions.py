"""
generate_questions.py — Pre-generates questions for all topics and saves
to src/data/question_bank.json

Usage:
    python generate_questions.py
    python generate_questions.py --topic 3.5
    python generate_questions.py --resume
    python generate_questions.py --per-topic 5

Requirements: pip install openai
"""

import json, os, re, time, argparse, random
from pathlib import Path
from openai import OpenAI

UNITS_FILE    = Path("src/data/units.json")
FIVEABLE_RAW  = Path("src/data/fiveable_raw.json")
HEIMLER_RAW   = Path("src/data/heimler_raw.json")
OUTPUT        = Path("src/data/question_bank.json")

def chunk_notes(text, chunk_size=600):
    """Split notes into chunks and return one randomly selected chunk."""
    paragraphs = [p.strip() for p in text.split('\n') if len(p.strip()) > 40]
    if not paragraphs:
        return text[:chunk_size]
    chunks = []
    current = []
    length = 0
    for p in paragraphs:
        current.append(p)
        length += len(p)
        if length >= chunk_size:
            chunks.append('\n'.join(current))
            current = []
            length = 0
    if current:
        chunks.append('\n'.join(current))
    return random.choice(chunks) if chunks else text[:chunk_size]

def generate_questions_for_topic(client, unit, topic, raw_notes, count=3):
    chunk = chunk_notes(raw_notes, chunk_size=700)

    prompt = f"""You are an expert AP US History exam writer.

UNIT: {unit['period']} ({unit['years']}) — {unit['sub']}
TOPIC: {topic['id']} "{topic['title']}"
AP THEME: {topic.get('themeLabel', '')}

SOURCE NOTES (base your questions ONLY on this content):
{chunk}

Generate exactly {count} AP-style multiple choice questions based on the content above.

RULES:
- ALL 4 choices must be historically accurate facts
- Wrong choices are wrong because they answer a DIFFERENT question (wrong cause, wrong effect, wrong connection), NOT because the information is false
- Question types: Causation / Effect / Connection / Significance / Context — vary them
- Each question must be about a DIFFERENT aspect of the notes

Return ONLY valid JSON, no markdown:
{{
  "questions": [
    {{
      "question": "2-3 sentences of context then the question",
      "choices": [
        {{"letter":"A","text":"historically accurate, 1 sentence"}},
        {{"letter":"B","text":"historically accurate, 1 sentence"}},
        {{"letter":"C","text":"historically accurate, 1 sentence"}},
        {{"letter":"D","text":"historically accurate, 1 sentence"}}
      ],
      "correct": "B",
      "skill": "Causation",
      "explanation": "Why correct is right, and why each wrong choice is historically true but doesn't answer THIS question.",
      "theme_connection": "1 sentence connecting to {topic.get('themeLabel', '')}",
      "essay_angle": "One AP essay angle (LEQ/SAQ/DBQ)",
      "source_chunk": "{chunk[:80].replace(chr(10),' ')}..."
    }}
  ]
}}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}],
        max_tokens=2000,
        temperature=0.7,
    )
    text = response.choices[0].message.content.strip()
    text = re.sub(r'```json\n?|\n?```', '', text).strip()
    return json.loads(text)['questions']

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume",    action="store_true")
    parser.add_argument("--topic",     type=str, help="Generate only for one topic ID e.g. 3.5")
    parser.add_argument("--per-topic", type=int, default=5, help="Questions per topic (default 5)")
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set"); return

    client = OpenAI(api_key=api_key)

    with open(UNITS_FILE, encoding="utf-8") as f:
        units_data = json.load(f)

    fiveable_raw = {}
    heimler_raw  = {}
    if FIVEABLE_RAW.exists():
        with open(FIVEABLE_RAW, encoding="utf-8") as f:
            fiveable_raw = json.load(f)

    if HEIMLER_RAW.exists():
        with open(HEIMLER_RAW, encoding="utf-8") as f:
            heimler_raw = json.load(f)

    existing = {}
    if args.resume and OUTPUT.exists():
        with open(OUTPUT, encoding="utf-8") as f:
            existing = json.load(f)

    bank = dict(existing)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    for unit in units_data['units']:
        for topic in unit['topics']:
            tid = topic['id']
            if args.topic and tid != args.topic:
                continue
            raw = heimler_raw.get(tid) or fiveable_raw.get(tid)
            if not raw:
                print(f"  ⚠ No raw notes for {tid} — skipping")
                continue
            existing_count = len(bank.get(tid, []))
            needed = args.per_topic - existing_count
            if args.resume and needed <= 0:
                print(f"  {tid} — already has {existing_count} questions, skipping")
                continue
            print(f"  Generating {needed} questions for {tid} '{topic['title']}'...")
            try:
                qs = generate_questions_for_topic(client, unit, topic, raw, count=min(needed, 5))
                if tid not in bank:
                    bank[tid] = []
                bank[tid].extend(qs)
                with open(OUTPUT, "w", encoding="utf-8") as f:
                    json.dump(bank, f, indent=2, ensure_ascii=False)
                print(f"    ✓ {len(qs)} questions added (total: {len(bank[tid])})")
                time.sleep(1.0)
            except Exception as e:
                print(f"    ⚠ Error: {e}")
                time.sleep(2)

    total = sum(len(v) for v in bank.values())
    print(f"\n✅ Done — {total} total questions across {len(bank)} topics")
    print(f"Output: {OUTPUT}")

if __name__ == "__main__":
    main()
