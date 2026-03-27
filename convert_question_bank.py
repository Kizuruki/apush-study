"""
convert_question_bank.py — Converts apush_questions.json into the
question_bank.json format expected by app.js

Run: python convert_question_bank.py
"""

import json
from pathlib import Path

# Same map as extract_heimler.py
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

def section_to_topic_ids(section_title):
    sl = section_title.lower()
    for key, topics in SECTION_TO_TOPICS.items():
        if key in sl:
            return topics
    return []

def build_explanation(q):
    correct = q["correct"]
    lines = []
    for letter, text in q["explanations"].items():
        lines.append(f"{letter}: {text}")
    return "\n".join(lines)

with open("apush_questions.json") as f:
    questions = json.load(f)

bank = {}
skipped = 0

for q in questions:
    topic_ids = section_to_topic_ids(q.get("topic", ""))
    if not topic_ids:
        skipped += 1
        continue

    converted = {
        "question": q["question"],
        "choices": [
            {"letter": k, "text": v}
            for k, v in q["choices"].items()
        ],
        "correct": q["correct"],
        "skill": "Causation",
        "explanation": build_explanation(q),
        "theme_connection": "",
        "essay_angle": "",
        "source": "heimler_mcq",
        "noteguide_context": q.get("noteguide_context", {})
    }

    for tid in topic_ids:
        if tid not in bank:
            bank[tid] = []
        bank[tid].append(converted)

output = Path("src/data/question_bank.json")
output.parent.mkdir(parents=True, exist_ok=True)
with open(output, "w", encoding="utf-8") as f:
    json.dump(bank, f, indent=2, ensure_ascii=False)

total = sum(len(v) for v in bank.values())
print(f"✅ Done — {total} questions across {len(bank)} topics ({skipped} skipped, no topic match)")
print(f"Output: {output}")
