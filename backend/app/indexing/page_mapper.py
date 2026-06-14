"""Map normalized topics to the pages on which they appear.

A topic matches a page if any of its variants appears as a whole-word
(case-insensitive) substring of that page's text. Page lists are deduplicated
and sorted.
"""
from __future__ import annotations

import re

from app.indexing.text_utils import clean_whitespace


def map_topics_to_pages(
    normalized: dict[str, list[str]],
    pages: dict[int, str],
) -> dict[str, list[int]]:
    """Return ``{canonical_topic: [sorted, unique, page, numbers]}``."""
    # Pre-lowercase page text once for performance.
    lowered = {n: clean_whitespace(text.lower()) for n, text in pages.items()}

    result: dict[str, list[int]] = {}
    for canonical, variants in normalized.items():
        patterns = [_compile_variant(v) for v in variants if v.strip()]
        hits: set[int] = set()
        for page_no, text in lowered.items():
            if not text:
                continue
            if any(p.search(text) for p in patterns):
                hits.add(page_no)
        if hits:
            result[canonical] = sorted(hits)
    return result


def _compile_variant(variant: str) -> re.Pattern[str]:
    # Match the variant text on whole-word boundaries; tolerate flexible
    # internal whitespace ("graph algorithms" matches "graph  algorithms").
    parts = re.escape(clean_whitespace(variant.lower())).replace(r"\ ", r"\s+")
    return re.compile(rf"\b{parts}\b")
