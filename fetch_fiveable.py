"""
fetch_fiveable.py — Fetches Fiveable study guide pages and extracts
structured notes into src/data/fiveable_notes.json

Usage:
    python fetch_fiveable.py           # fetch all topics
    python fetch_fiveable.py --resume  # skip already-fetched topics

Requirements:
    pip install openai requests beautifulsoup4
"""

import json, os, re, time, argparse
from pathlib import Path
from openai import OpenAI

FIVEABLE_URLS = {
  "1.2":"https://fiveable.me/apush/unit-1/native-american-societies-before-european-contact/study-guide/WSdp3WwC8fc4Hcds2um6",
  "1.3":"https://fiveable.me/apush/unit-1/european-exploration-americas/study-guide/4Xo0Z9vsVo97AfHCtNzM",
  "1.4":"https://fiveable.me/apush/unit-1/columbian-exchange-spanish-exploration-conquest/study-guide/adQt4h0vtMjRyzXDZN8e",
  "1.5":"https://fiveable.me/apush/unit-1/labor-slavery-caste-spanish-colonial-system/study-guide/YNYW7aq8cgcgywTr8aob",
  "1.6":"https://fiveable.me/apush/unit-1/cultural-interactions-between-europeans-native-americans-africans/study-guide/xKdK0605epqUHu2tUwYM",
  "2.2":"https://fiveable.me/apush/unit-2/european-colonization-north-america/study-guide/bOqbTIQvhKy42VNcnRMs",
  "2.3":"https://fiveable.me/apush/unit-2/regions-british-colonies/study-guide/43BTTQADqqAwsWbjpJ5G",
  "2.4":"https://fiveable.me/apush/unit-2/transatlantic-trade/study-guide/UcqUNsSk8bGifGh838TY",
  "2.5":"https://fiveable.me/apush/unit-2/interactions-between-american-indians-europeans/study-guide/chUDbGx9XSPajryeDxcv",
  "2.6":"https://fiveable.me/apush/unit-2/slavery-british-colonies/study-guide/h2ezjfgaQaItQZybcxyf",
  "2.7":"https://fiveable.me/apush/unit-2/colonial-society-culture/study-guide/Lko98iWbbumC8ceFevkv",
  "3.2":"https://fiveable.me/apush/unit-3/seven-years-war-french-indian-war/study-guide/Xiy5IbXj54SmSbIyUazE",
  "3.3":"https://fiveable.me/apush/unit-3/taxation-without-representation/study-guide/RjW4aBcZHoaG4ABJrvIk",
  "3.4":"https://fiveable.me/apush/unit-3/philosophical-foundations-american-revolution/study-guide/1tqf5yAhHDgdepsUL6GT",
  "3.5":"https://fiveable.me/apush/unit-3/american-revolution/study-guide/qmZACCrcWZjV1YajNd9d",
  "3.6":"https://fiveable.me/apush/unit-3/influence-revolutionary-ideals/study-guide/DaZjTIBFYrpHgheRa9sC",
  "3.7":"https://fiveable.me/apush/unit-3/articles-confederation/study-guide/bllK78POE3keG1TCHNXI",
  "3.8":"https://fiveable.me/apush/unit-3/constitutional-convention-debates-over-ratification/study-guide/OVohv8ZoyPEaJ0Ut9yUa",
  "3.9":"https://fiveable.me/apush/unit-3/constitution/study-guide/GFXLutGBoLM4MszJCxWq",
  "3.10":"https://fiveable.me/apush/unit-3/shaping-new-republic/study-guide/jDcJK92nIldkFTb5QJpZ",
  "4.2":"https://fiveable.me/apush/unit-4/rise-political-parties-era-jefferson/study-guide/jBptoMVxCR4JxRknAlm7",
  "4.3":"https://fiveable.me/apush/unit-4/politics-regional-interests-1800-1848/study-guide/1TQCI0h8ONg84TKhEywv",
  "4.5":"https://fiveable.me/apush/unit-4/market-revolution-industrialization/study-guide/XB7wtlsHuzKyN4rtUORe",
  "4.6":"https://fiveable.me/apush/unit-4/market-revolution-society-culture/study-guide/utkUPzxiRypzIvTXl779",
  "4.7":"https://fiveable.me/apush/unit-4/expanding-democracy-1800-1848/study-guide/yvZqvo6sEMe2gvvM03AB",
  "4.8":"https://fiveable.me/apush/unit-4/jackson-federal-power/study-guide/VnevAqqtpZVuKzRpBf4O",
  "4.10":"https://fiveable.me/apush/unit-4/second-great-awakening/study-guide/tR4UP1gR5yZZRsp6w0v9",
  "4.11":"https://fiveable.me/apush/unit-4/an-age-reform-1800-1848/study-guide/pq1BOhhhmXUke0J5WXkS",
  "4.13":"https://fiveable.me/apush/unit-4/society-south-early-republic/study-guide/zhWn5XFSD8f6Lh2VoX4c",
  "5.2":"https://fiveable.me/apush/unit-5/manifest-destiny/study-guide/QCAKf0AWBCPTgZHZtUPD",
  "5.3":"https://fiveable.me/apush/unit-5/mexican-american-war/study-guide/NMqiBxahosm76SKTghut",
  "5.4":"https://fiveable.me/apush/unit-5/compromise-1850/study-guide/SD3f1WJu48SnOd8v1RAm",
  "5.6":"https://fiveable.me/apush/unit-5/failure-compromise/study-guide/Pc8cAsWACsNLhZIwOHf3",
  "5.7":"https://fiveable.me/apush/unit-5/election-1860-secession/study-guide/6wnMakCgnFOoTG2IEnSa",
  "5.8":"https://fiveable.me/apush/unit-5/military-conflict-civil-war/study-guide/d9NgoNY74uuvfh4RmD6l",
  "5.9":"https://fiveable.me/apush/unit-5/government-policies-during-civil-war/study-guide/rI7StngOCC4D0qsmkDvV",
  "5.10":"https://fiveable.me/apush/unit-5/reconstruction/study-guide/DiWHCM2v4Drc73iIcfDS",
  "5.11":"https://fiveable.me/apush/unit-5/failures-reconstruction/study-guide/v760MdiOJXB3TCLYZBZ5",
  "6.3":"https://fiveable.me/apush/unit-6/westward-expansion-social-cultural-development-1865-1898/study-guide/tjZEnBbepPcpcbtaF5eA",
  "6.4":"https://fiveable.me/apush/unit-6/new-south-1865-1898/study-guide/OB83CdTZrgzJYVjQ0xCX",
  "6.5":"https://fiveable.me/apush/unit-6/technological-innovation-1865-1898/study-guide/UbJ4g3jWethQISe6Yzal",
  "6.6":"https://fiveable.me/apush/unit-6/rise-industrial-capitalism-1865-1898/study-guide/KgfyIEY4fiMV5yk7Ng0X",
  "6.7":"https://fiveable.me/apush/unit-6/labor-gilded-age-1865-1898/study-guide/S5kLZj55mM4PK2a8a80A",
  "6.8":"https://fiveable.me/apush/unit-6/immigration-migration-gilded-age-1865-1898/study-guide/tFUqkhIaH3BOei1JuxAM",
  "6.11":"https://fiveable.me/apush/unit-6/reform-gilded-age/study-guide/c8AtStJnup2hvLeHcZcC",
  "6.12":"https://fiveable.me/apush/unit-6/controversies-over-role-government-gilded-age/study-guide/CU4ireSXmjF3ZkbKgQYd",
  "7.2":"https://fiveable.me/apush/unit-7/imperialism-debates/study-guide/XQhEsqd89b8yG7yqh4dK",
  "7.3":"https://fiveable.me/apush/unit-7/spanish-american-war/study-guide/oTnk4443gyjW9WwKdPbK",
  "7.4":"https://fiveable.me/apush/unit-7/progressives/study-guide/a9XjRguda7a0EHsXEXDz",
  "7.5":"https://fiveable.me/apush/unit-7/world-war-i-military-diplomacy/study-guide/4wZDa2Pak8FfrKeucUqt",
  "7.6":"https://fiveable.me/apush/unit-7/world-war-i-home-front/study-guide/z3zU0aD0liS5u8BPkQOX",
  "7.7":"https://fiveable.me/apush/unit-7/1920s-innovations-communication-technology/study-guide/KM5LZjLDw8GP7jySCER1",
  "7.8":"https://fiveable.me/apush/unit-7/1920s-cultural-political-controversies/study-guide/LXAypu3iPW64jHg87JFH",
  "7.9":"https://fiveable.me/apush/unit-7/great-depression/study-guide/hI7MOeaEZFK45NrnWkxr",
  "7.10":"https://fiveable.me/apush/unit-7/new-deal/study-guide/O8bvpnFSbBfiQMHlcl4D",
  "7.12":"https://fiveable.me/apush/unit-7/world-war-ii-mobilization/study-guide/5YjYcPKLKi9eIBZzNaXs",
  "7.13":"https://fiveable.me/apush/unit-7/world-war-ii-military/study-guide/3giKnoeivLFf1jQamalK",
  "8.2":"https://fiveable.me/apush/unit-8/cold-war-1945-1980/study-guide/vLoggG1eZuSCQnMwTaE5",
  "8.3":"https://fiveable.me/apush/unit-8/red-scare/study-guide/DO0e4A4aiTYvyrkA5oje",
  "8.4":"https://fiveable.me/apush/unit-8/economy-after-1945/study-guide/houeOTJKnK56RUnHRRD7",
  "8.6":"https://fiveable.me/apush/unit-8/early-steps-civil-rights-movement-1940s-1950s/study-guide/bLUUfoR5Lt4D1FcR5EOB",
  "8.8":"https://fiveable.me/apush/unit-8/vietnam-war/study-guide/vGcbjSr85W3AwiZZEH7T",
  "8.9":"https://fiveable.me/apush/unit-8/great-society/study-guide/5lE2fsg4BsckTqmDNJqx",
  "8.10":"https://fiveable.me/apush/unit-8/african-american-civil-rights-movement-1960s/study-guide/yInAfvUol9DCb9fB2Eer",
  "8.11":"https://fiveable.me/apush/unit-8/expansion-civil-rights-movement/study-guide/4JIzz1rguSts5wCf7Odr",
  "8.14":"https://fiveable.me/apush/unit-8/society-transition/study-guide/XwxV2oK2ulyRH0YxkAZd",
  "9.2":"https://fiveable.me/apush/unit-9/reagan-conservatism/study-guide/bhzREq69MW1ktHbBP8hg",
  "9.3":"https://fiveable.me/apush/unit-9/end-cold-war/study-guide/jSK48CxJEPXM0bpeuKEg",
  "9.4":"https://fiveable.me/apush/unit-9/a-changing-economy-1980-present/study-guide/NPJrmemKFxqdAtJVbR6e",
  "9.5":"https://fiveable.me/apush/unit-9/migration-immigration-1990s-2000s/study-guide/h48Rw9Wyn6SOzLUA4mF6",
  "9.6":"https://fiveable.me/apush/unit-9/challenges-21st-century/study-guide/EXLLVyYPLInl4kY1shVW",
}

OUTPUT = Path("src/data/fiveable_notes.json")

def fetch_page(url):
    import requests
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    return r.text

def clean_html(html):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    # Remove nav, script, style, footer
    for tag in soup(["nav","script","style","footer","header","aside"]):
        tag.decompose()
    # Get main content text
    main = soup.find("main") or soup.find("article") or soup.body
    if not main:
        return soup.get_text()
    text = main.get_text(separator="\n")
    # Clean up
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    # Remove Fiveable UI boilerplate
    skip = ["practice questions","cheatsheet","print guide","report error",
            "more resources","upgrade","free diagnostic","Fiveable"]
    lines = [l for l in lines if not any(s.lower() in l.lower() for s in skip)]
    return "\n".join(lines[:120])  # cap at ~120 lines

def extract_notes(client, topic_id, raw_text):
    prompt = f"""You are extracting AP US History study notes for Topic {topic_id} from a Fiveable study guide.

RAW TEXT:
{raw_text[:3000]}

Extract the most important historical content as concise study notes. Focus on:
- Key events, dates, and their significance
- Cause-and-effect relationships
- Important people and their roles
- AP exam-relevant connections

Return plain text study notes (not JSON), 200-400 words, organized with bullet points.
Do NOT include: website navigation, ads, unrelated links, or promotional content."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an AP US History expert extracting concise study notes."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        print("   Windows: $env:OPENAI_API_KEY='sk-...'")
        print("   Mac/Linux: export OPENAI_API_KEY='sk-...'")
        return

    client = OpenAI(api_key=api_key)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    # Load existing
    existing = {}
    if args.resume and OUTPUT.exists():
        with open(OUTPUT) as f:
            existing = json.load(f)
        print(f"📂 Resuming — {len(existing)} topics already done")

    notes = dict(existing)
    total = len(FIVEABLE_URLS)
    processed = 0
    errors = 0

    print(f"\n{'='*55}")
    print(f"  Fiveable Notes Extractor — {total} topics")
    print(f"  Estimated cost: ~${total * 0.002:.2f} (gpt-4o-mini)")
    print(f"{'='*55}\n")

    for i, (topic_id, url) in enumerate(FIVEABLE_URLS.items(), 1):
        if args.resume and topic_id in notes:
            print(f"  [{i}/{total}] {topic_id} — skipped (already done)")
            continue

        print(f"  [{i}/{total}] {topic_id} — fetching...")
        try:
            html = fetch_page(url)
            raw = clean_html(html)
            note = extract_notes(client, topic_id, raw)
            notes[topic_id] = note
            processed += 1
            # Save after each
            with open(OUTPUT, "w", encoding="utf-8") as f:
                json.dump(notes, f, indent=2, ensure_ascii=False)
            print(f"         ✓ {len(note)} chars")
            time.sleep(1.2)  # rate limit
        except Exception as e:
            print(f"         ⚠ Error: {e}")
            errors += 1
            time.sleep(2)

    print(f"\n{'='*55}")
    print(f"  ✅ Done! {processed} processed, {errors} errors")
    print(f"  Output: {OUTPUT}")
    print(f"{'='*55}\n")

if __name__ == "__main__":
    main()
