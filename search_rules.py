import json
import os
import re
from rapidfuzz import fuzz, process
from rich import print

# Load all rule chunks from the output folder
def load_all_chunks(folder="output"):
    all_chunks = []
    for filename in os.listdir(folder):
        if filename.endswith(".json"):
            with open(os.path.join(folder, filename), "r", encoding="utf-8") as f:
                chunks = json.load(f)
                all_chunks.extend(chunks)
    print(f"📚 Loaded {len(all_chunks)} total chunks from {folder}")
    return all_chunks

# Normalize UK/US spelling and known typos
def normalize_query(term):
    replacements = {
        "armour": "armor",
        "colour": "color",
        "favour": "favor",
        "honour": "honor",
        "centre": "center",
    }
    return replacements.get(term.lower(), term)

# Keyword search with heading/frequency scoring and source priority
def keyword_search(query, chunks, limit=10):
    query_lower = query.lower()
    matches = []

    for chunk in chunks:
        text = chunk["text"]
        lower_text = text.lower()

        if query_lower in lower_text:
            frequency_score = lower_text.count(query_lower)
            first_line = lower_text.split("\n")[0]
            heading_score = 5 if query_lower in first_line else 0
            total_score = heading_score + frequency_score
            matches.append((chunk, total_score))

    if not matches:
        print("😕 No keyword matches found.")
        return False

    print(f"🔍 [bold green]Found {len(matches)} keyword match(es)[/bold green]:\n")

    def sort_key(item):
        chunk, score = item
        source = chunk["source"].lower()
        if "corerules" in source:
            source_priority = 0
        elif "heroes" in source:
            source_priority = 1
        elif "gmguide" in source:
            source_priority = 2
        else:
            source_priority = 3
        return (-score, source_priority)

    sorted_matches = sorted(matches, key=sort_key)

    for chunk, score in sorted_matches[:limit]:
        print(f"[bold cyan]{chunk['source']}[/bold cyan], page [bold green]{chunk['page']}[/bold green] — Relevance score: {score}")
        print(chunk["text"])
        print("[dim]" + "-" * 80 + "[/dim]")

    return True

# Fallback: improved fuzzy match with heading/frequency/source scoring
def fuzzy_search(query, chunks, limit=5, min_score=20):
    query_normalized = normalize_query(query)
    print("🤔 No keyword hits — trying fuzzy match...\n")

    raw_results = process.extract(
        query_normalized,
        [chunk["text"] for chunk in chunks],
        scorer=fuzz.token_sort_ratio,
        limit=50  # grab more for smarter scoring
    )

    scored_results = []
    for match_text, fuzz_score, idx in raw_results:
        if fuzz_score < min_score:
            continue

        chunk = chunks[idx]
        text_lower = chunk["text"].lower()
        query_lower = query_normalized.lower()
        first_line = text_lower.split("\n")[0]

        heading_score = 5 if query_lower in first_line else 0
        frequency_score = text_lower.count(query_lower)
        total_score = heading_score + frequency_score

        source = chunk["source"].lower()
        if "corerules" in source:
            source_priority = 0
        elif "heroes" in source:
            source_priority = 1
        elif "gmguide" in source:
            source_priority = 2
        else:
            source_priority = 3

        scored_results.append((chunk, fuzz_score, total_score, source_priority))

    if not scored_results:
        print("😕 No relevant matches found.")
        return

    sorted_results = sorted(
        scored_results,
        key=lambda item: (-item[2], item[3], -item[1])  # relevance desc, source asc, fuzz desc
    )

    for chunk, fuzz_score, total_score, _ in sorted_results[:limit]:
        print(f"[bold cyan]{chunk['source']}[/bold cyan], page [bold green]{chunk['page']}[/bold green] — Fuzzy: {fuzz_score:.1f}%, Relevance: {total_score}")
        print(chunk["text"])
        print("[dim]" + "-" * 80 + "[/dim]")

# Entry point
def main():
    chunks = load_all_chunks()

    while True:
        query = input("\n🔎 Enter a rules question (or 'q' to quit): ").strip()
        if query.lower() in ("q", "quit", "exit"):
            print("👋 Goodbye!")
            break

        found = keyword_search(normalize_query(query), chunks, limit=5)
        if not found:
            fuzzy_search(query, chunks, limit=5)

if __name__ == "__main__":
    main()
