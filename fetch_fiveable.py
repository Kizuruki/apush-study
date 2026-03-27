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
RAW_OUTPUT = Path("src/data/fiveable_raw.json")

UNIT_OVERVIEW_URLS = {
  "overview_1": "https://fiveable.me/apush/unit-1/review/study-guide/436xVWPsHDmbH6vqPhXi",
  "overview_2": "https://fiveable.me/apush/unit-2/review/study-guide/MrhwF2OP3DVLQwTIh2wZ",
  "overview_3": "https://fiveable.me/apush/unit-3/review/study-guide/2EzLHuxQ3b4WEIPrx5zM",
  "overview_4": "https://fiveable.me/apush/unit-4/review/study-guide/oLc9021gUMSDADySvXfR",
  "overview_5": "https://fiveable.me/apush/unit-5/review/study-guide/6Upoqbpo7BMFKQIPNAn8",
  "overview_6": "https://fiveable.me/apush/unit-6/review/study-guide/XZscSKd7WFiyvpD3Z61j",
  "overview_7": "https://fiveable.me/apush/unit-7/review/study-guide/Z8yz2hLUNbkRC9OthYsd",
  "overview_8": "https://fiveable.me/apush/unit-8/review/study-guide/ucf1FJzgrQryddtK97hv",
  "overview_9": "https://fiveable.me/apush/unit-9/review/study-guide/hJRgla5LVpNJN2iR3e9e",
}

OVERVIEW_OUTPUT = Path("src/data/unit_overviews.json")

FIVEABLE_URLS = {
# Causation / Comparison / Continuity
  "1.7":  "https://fiveable.me/apush/unit-1/causation-period-1/study-guide/DAGaYjTWpcEa9xMRdb86",
  "2.8":  "https://fiveable.me/apush/unit-2/comparison-period-2/study-guide/osbWaPWHbIDMpvo1PPjH",
  "3.13": "https://fiveable.me/apush/unit-3/continuity-change-period-3/study-guide/51uENnieSL7EhfHYtqyR",
  "4.14": "https://fiveable.me/apush/unit-4/causation-period-4/study-guide/of2JSOwgAxbow5qUxTmx",
  "5.12": "https://fiveable.me/apush/unit-5/comparison-period-5/study-guide/F4PJCNduTfAlJJKn5VEj",
  "6.14": "https://fiveable.me/apush/unit-6/continuity-change-period-6/study-guide/YxG0RLR92x6i03ihmLj2",
  "7.15": "https://fiveable.me/apush/unit-7/comparison-period-7/study-guide/AsdMiXS56cxJRb0VbaQ6",
  "8.15": "https://fiveable.me/apush/unit-8/continuity-change-period-8/study-guide/CrQUvMS5z0WkJfj1qPfG",
  "9.7":  "https://fiveable.me/apush/unit-9/causation-period-9/study-guide/9F58jAjqrlXeUuHFNrtT",

  # Other missing topics
  "3.11": "https://fiveable.me/apush/unit-3/developing-an-american-identity/study-guide/MEaybcl53Ms0Y37023ML",
  "3.12": "https://fiveable.me/apush/unit-3/movement-early-republic/study-guide/eoL3MkhdlT5xBQVMW6jW",
  "4.4":  "https://fiveable.me/apush/unit-4/america-on-world-stage-1800-1848/study-guide/DhM9tP7aAONxSWn0sGpD",
  "4.9":  "https://fiveable.me/apush/unit-4/development-an-american-culture/study-guide/EZrhIocFWQsxZVyZIHAv",
  "4.12": "https://fiveable.me/apush/unit-4/african-americans-early-republic/study-guide/7xeQjlCwTvWKuWJNS9VY",
  "5.5":  "https://fiveable.me/apush/unit-5/sectional-conflict-before-civil-war/study-guide/Klx3eOhZBS11qtWKIvH2",
  "6.2":  "https://fiveable.me/apush/unit-6/westward-expansion-economic-development-1865-1898/study-guide/IyGGrUeyJLooDzn8Y5OT",
  "6.9":  "https://fiveable.me/apush/unit-6/responses-immigration-1865-1898/study-guide/X4fx724j5MTe7HVMX20x",
  "6.10": "https://fiveable.me/apush/unit-6/development-middle-class-1865-1898/study-guide/mLXszg6nCgdwD1wDrnAt",
  "6.13": "https://fiveable.me/apush/unit-6/politics-gilded-age/study-guide/8nIh2AsuMR3xXcKSZRaq",
  "7.11": "https://fiveable.me/apush/unit-7/interwar-foreign-policy/study-guide/byiVnNajkchodwAk3EJm",
  "7.14": "https://fiveable.me/apush/unit-7/postwar-diplomacy/study-guide/xMjx3s8J0K11zGx6sHBP",
  "8.5":  "https://fiveable.me/apush/unit-8/culture-after-1945/study-guide/HuEqGJLM5NGTvsEdDilu",
  "8.7":  "https://fiveable.me/apush/unit-8/america-as-world-power/study-guide/CJrU270W97IiyhqgLyQH",
  "8.12": "https://fiveable.me/apush/unit-8/youth-culture-1960s/study-guide/RaRE6JHkpeGMR7exEexk",
  "8.13": "https://fiveable.me/apush/unit-8/environment-natural-resources-1968-1980/study-guide/0t0VXJnMCn7QKI5gwV6X",
  "1.1": "https://fiveable.me/apush/unit-1/context-european-encounters-americas/study-guide/PrHNVmAM1cykKvSebMuS",
  "2.1": "https://fiveable.me/apush/unit-2/context-european-colonization-north-america/study-guide/2cwnnkpNtrJCQUVKbbvh",
  "3.1": "https://fiveable.me/apush/unit-3/context-american-independence/study-guide/9iJasxNtHYt2SBpTnTfL",
  "4.1": "https://fiveable.me/apush/unit-4/context-early-american-democracy/study-guide/l50VQC2Ghh7MS0mDKX46",
  "5.1": "https://fiveable.me/apush/unit-5/contextualizing-period-5/study-guide/4IjDIqCCZ4MNbXQ9gqev",
  "6.1": "https://fiveable.me/apush/unit-6/context-industrialization-gilded-age/study-guide/xj5s6yDrmKT7LxrUWvl2",
  "7.1": "https://fiveable.me/apush/unit-7/context-20th-century-global-conflicts/study-guide/4AKsCOPpRLPL2usRPyD6",
  "8.1": "https://fiveable.me/apush/unit-8/context-us-as-global-leader/study-guide/gQBcPKrfySmr9qtQziHd",
  "9.1": "https://fiveable.me/apush/unit-9/context-present-day-america/study-guide/HnIdvKcPqLuFXlxLt0ok",
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
    raw_notes = {}
    if args.resume and RAW_OUTPUT.exists():
        with open(RAW_OUTPUT) as f:
            raw_notes = json.load(f)
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
            raw_notes[topic_id] = raw  # save original scraped text
            with open(RAW_OUTPUT, "w", encoding="utf-8") as f:
                json.dump(raw_notes, f, indent=2, ensure_ascii=False)
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
    # ── Unit overviews ──────────────────────────────────────
    print(f"\n  Fetching unit overviews...")
    existing_overviews = {}
    if args.resume and OVERVIEW_OUTPUT.exists():
        with open(OVERVIEW_OUTPUT) as f:
            existing_overviews = json.load(f)

    overviews = dict(existing_overviews)

    for key, url in UNIT_OVERVIEW_URLS.items():
        if args.resume and key in overviews:
            print(f"    {key} — skipped")
            continue
        print(f"    {key} — fetching...")
        try:
            html = fetch_page(url)
            raw = clean_html(html)
            prompt = f"""You are summarizing an AP US History unit overview from Fiveable.

RAW TEXT:
{raw[:3000]}

Write a concise unit overview (150-250 words) covering:
- The time period and major themes
- 3-4 most important developments
- Key historical significance for the AP exam
- Big-picture continuities and changes

Write as flowing prose, not bullet points."""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role":"user","content":prompt}],
                max_tokens=350,
                temperature=0.3,
            )
            overviews[key] = response.choices[0].message.content.strip()
            with open(OVERVIEW_OUTPUT, "w", encoding="utf-8") as f:
                json.dump(overviews, f, indent=2, ensure_ascii=False)
            print(f"         ✓")
            time.sleep(1.2)
        except Exception as e:
            print(f"         ⚠ Error: {e}")

if __name__ == "__main__":
    main()
