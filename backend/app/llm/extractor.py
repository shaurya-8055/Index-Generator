"""Topic extraction.

Two strategies:

* ``_llm_extract`` — prompts a LangChain chat model to extract index-worthy
  topics from a chunk of text and returns a ``List[str]``.
* ``_heuristic_extract`` — a dependency-free fallback using noun-phrase-ish
  n-gram frequency analysis so the app produces a real index without any
  API key.

``extract_topics`` picks the right strategy based on configuration.
"""
from __future__ import annotations

import json
import logging
import re
from collections import Counter

from app.indexing.text_utils import (
    STOP_WORDS,
    normalize_topic_label,
    tokenize,
)
from app.llm.providers import get_chat_model, llm_available

logger = logging.getLogger(__name__)

_EXTRACTION_SYSTEM = (
    "You are an expert technical indexer who builds book-style indexes. "
    "Extract the important, index-worthy topics, concepts, terms and named "
    "entities from the provided text."
)

_EXTRACTION_INSTRUCTIONS = """\
Extract index-worthy topics from the text below.

Rules:
- Return concepts, technical terms, named entities and key subjects.
- Remove stop words and generic filler.
- Normalize capitalization (Title Case; keep acronyms like BFS, API).
- Avoid duplicates and near-duplicates.
- Ignore extremely common / generic words.
- Prefer 1-3 word noun phrases.

Respond with ONLY a JSON array of strings, e.g. ["Arrays", "Graph Algorithms", "BFS"].

TEXT:
{text}
"""


def extract_topics(text: str, *, max_topics: int = 40) -> list[str]:
    """Extract a list of normalized topic labels from a chunk of text."""
    if not text or not text.strip():
        return []

    if llm_available():
        try:
            return _llm_extract(text, max_topics=max_topics)
        except Exception as exc:  # pragma: no cover - network/credentials
            logger.warning("LLM extraction failed (%s); using heuristic fallback", exc)

    return _heuristic_extract(text, max_topics=max_topics)


# --------------------------------------------------------------------------- #
# LLM strategy
# --------------------------------------------------------------------------- #
def _llm_extract(text: str, *, max_topics: int) -> list[str]:
    from langchain_core.messages import HumanMessage, SystemMessage

    model = get_chat_model()
    prompt = _EXTRACTION_INSTRUCTIONS.format(text=text[:12000])
    response = model.invoke(
        [SystemMessage(content=_EXTRACTION_SYSTEM), HumanMessage(content=prompt)]
    )
    raw = response.content if hasattr(response, "content") else str(response)
    topics = _parse_json_array(raw)
    cleaned = _dedupe_preserving_order(
        normalize_topic_label(t) for t in topics if t and t.strip()
    )
    return cleaned[:max_topics]


def _parse_json_array(raw: str) -> list[str]:
    raw = raw.strip()
    # Strip markdown code fences if present.
    fence = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL)
    if fence:
        raw = fence.group(1).strip()
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if match:
        raw = match.group(0)
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [str(x) for x in data]
    except json.JSONDecodeError:
        logger.warning("Could not parse LLM JSON output; got: %s", raw[:200])
    return []


# --------------------------------------------------------------------------- #
# Heuristic fallback strategy
# --------------------------------------------------------------------------- #
def _heuristic_extract(text: str, *, max_topics: int) -> list[str]:
    """Frequency-based n-gram extraction (no external dependencies)."""
    tokens = tokenize(text)
    if not tokens:
        return []

    unigrams = Counter(tokens)
    bigrams = Counter(_ngrams(tokens, 2))
    trigrams = Counter(_ngrams(tokens, 3))

    candidates: Counter[str] = Counter()

    # Multi-word phrases are usually better index entries; weight them up.
    for phrase, count in trigrams.items():
        if count >= 2:
            candidates[phrase] += count * 3
    for phrase, count in bigrams.items():
        if count >= 2:
            candidates[phrase] += count * 2
    for word, count in unigrams.items():
        if count >= 2 and len(word) > 3:
            candidates[word] += count

    if not candidates:  # short text: fall back to most frequent unigrams
        candidates.update({w: c for w, c in unigrams.items() if len(w) > 3})

    ranked = [phrase for phrase, _ in candidates.most_common(max_topics * 3)]
    ranked = _suppress_subsumed_unigrams(ranked)
    labels = _dedupe_preserving_order(normalize_topic_label(p) for p in ranked)
    return labels[:max_topics]


def _suppress_subsumed_unigrams(ranked: list[str]) -> list[str]:
    """Drop single-word candidates that already appear inside a multi-word
    phrase (e.g. keep "Binary Trees" but drop the bare "Binary")."""
    phrase_words = {
        w for phrase in ranked if " " in phrase for w in phrase.split()
    }
    return [p for p in ranked if " " in p or p not in phrase_words]


def _ngrams(tokens: list[str], n: int) -> list[str]:
    grams = []
    for i in range(len(tokens) - n + 1):
        window = tokens[i : i + n]
        # Skip phrases that start or end with a stop word remnant.
        if window[0] in STOP_WORDS or window[-1] in STOP_WORDS:
            continue
        grams.append(" ".join(window))
    return grams


def _dedupe_preserving_order(items) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item.lower()
        if key and key not in seen:
            seen.add(key)
            out.append(item)
    return out
