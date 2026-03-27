"""
convert_question_bank.py — Converts apush_questions.json into question_bank.json
keyed by unit number ("unit_1", "unit_2", etc.)

Run: python convert_question_bank.py
"""

import json
from pathlib import Path

def build_explanation(q):
    lines = []
    for letter, text in q["explanations"].items():
        lines.append(f"{letter}: {text}")
    return "\n".join(lines)

with open("apush_questions.json", encoding="utf-8") as f:
    questions = json.load(f)

bank = {}

for q in questions:
    unit = q.get("unit")
    if not unit:
        continue
    key = f"unit_{unit}"
    if key not in bank:
        bank[key] = []
    bank[key].append({
        "question": q["question"],
        "choices": [{"letter": k, "text": v} for k, v in q["choices"].items()],
        "correct": q["correct"],
        "skill": "Causation",
        "explanation": build_explanation(q),
        "theme_connection": "",
        "essay_angle": "",
        "source": "heimler_mcq",
        "noteguide_context": q.get("noteguide_context", {})
    })

output = Path("src/data/question_bank.json")
output.parent.mkdir(parents=True, exist_ok=True)
with open(output, "w", encoding="utf-8") as f:
    json.dump(bank, f, indent=2, ensure_ascii=False)

total = sum(len(v) for v in bank.values())
print(f"✅ Done — {total} questions across {len(bank)} units")
for key in sorted(bank.keys()):
    print(f"  {key}: {len(bank[key])} questions")
