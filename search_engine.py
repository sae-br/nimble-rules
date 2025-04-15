import os
import json
import re
from rapidfuzz import fuzz, process
from markupsafe import Markup

# Load chunks from all JSON files in /output
def load_all_chunks(folder="output"):
    all_chunks = []
    for filename in os.listdir(folder):
        if filename.endswith(".json"):
            with open(os.path.join(folder, filename), "r", encoding="utf-8") as f:
                chunks = json.load(f)
                all_chunks.extend(chunks)
    return all_chunks

# Normalize spelling and typos
def normalize_query(term):
    replacements = {
        "armour": "armor",
        "colour": "color",
        "favour": "favor",
        "honour": "honor",
        "centre": "center",
        "innitiative": "initiative",
    }
    return replacements.get(term.lower(), term)

# Prioritize source order
def get_source_priority(source):
    source = source.lower()
    if "corerules" in source:
        return 0
    elif "heroes" in source:
        return 1
    elif "gmguide" in source:
        return 2
    return 3

# Extract a short snippet around the keyword and highlight the exact match

def extract_snippet(text, query, context_chars=150):
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    match = pattern.search(text)

    if not match:
        snippet = text[:context_chars * 2]
    else:
        start = max(match.start() - context_chars, 0)
        end = match.end() + context_chars
        snippet = text[start:end]

    return snippet.strip(), pattern

# Relevance score for keyword placement

def score_chunk(chunk, query):
    text = chunk["text"].lower()
    query_lower = query.lower()
    heading_score = 5 if query_lower in text.split("\n")[0] else 0
    frequency_score = text.count(query_lower)
    return heading_score + frequency_score

# Keyword search

def keyword_search_web(query, chunks, limit=10):
    query = normalize_query(query)
    results = []
    for chunk in chunks:
        if query.lower() in chunk["text"].lower():
            score = score_chunk(chunk, query)
            results.append((chunk, score))

    if not results:
        return []

    sorted_results = sorted(
        results,
        key=lambda item: (-item[1], get_source_priority(item[0]["source"]))
    )

    formatted = []
    for chunk, score in sorted_results[:limit]:
        snippet, pattern = extract_snippet(chunk["text"], query)
        highlighted = pattern.sub(
            lambda m: f'<span style="background-color:goldenrod">{m.group(0)}</span>',
            snippet
        )
        formatted.append({
            "source": chunk["source"],
            "page": chunk["page"],
            "score": score,
            "text": chunk["text"],
            "highlighted_text": Markup(highlighted)
        })
    return formatted

# Fuzzy search fallback

def fuzzy_search_web(query, chunks, limit=5, min_score=20):
    query_normalized = normalize_query(query)
    raw_results = process.extract(
        query_normalized,
        [chunk["text"] for chunk in chunks],
        scorer=fuzz.token_sort_ratio,
        limit=50
    )

    results = []
    for match_text, fuzz_score, idx in raw_results:
        if fuzz_score < min_score:
            continue

        chunk = chunks[idx]
        score = score_chunk(chunk, query_normalized)
        results.append((chunk, fuzz_score, score))

    sorted_results = sorted(
        results,
        key=lambda item: (-item[2], get_source_priority(item[0]["source"]), -item[1])
    )

    formatted = []
    for chunk, fuzz_score, score in sorted_results[:limit]:
        snippet, pattern = extract_snippet(chunk["text"], query_normalized)
        highlighted = pattern.sub(
            lambda m: f'<span style="background-color:goldenrod">{m.group(0)}</span>',
            snippet
        )
        formatted.append({
            "source": chunk["source"],
            "page": chunk["page"],
            "score": score,
            "text": chunk["text"],
            "highlighted_text": Markup(highlighted)
        })
    return formatted