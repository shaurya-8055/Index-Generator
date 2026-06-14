"""Heuristic topic normalization: merge singular/plural and casing variants.

Produces a mapping of ``canonical_label -> [original variants...]`` so that
page mapping can attribute every variant to a single index entry.
"""
from __future__ import annotations

from collections import defaultdict

from app.indexing.text_utils import normalize_topic_label, topic_key


def normalize_topics(topics: list[str]) -> dict[str, list[str]]:
    """Merge near-duplicate topics into canonical labels.

    Returns ``{canonical: [variant, ...]}``. The canonical label is the
    longest / most descriptive variant in each group.
    """
    groups: dict[str, list[str]] = defaultdict(list)
    for topic in topics:
        label = normalize_topic_label(topic)
        if not label:
            continue
        groups[topic_key(label)].append(label)

    canonical: dict[str, list[str]] = {}
    for variants in groups.values():
        unique_variants = _dedupe(variants)
        best = _pick_canonical(unique_variants)
        canonical[best] = unique_variants
    return dict(sorted(canonical.items(), key=lambda kv: kv[0].lower()))


def _pick_canonical(variants: list[str]) -> str:
    """Prefer the plural form when present, otherwise the longest variant."""
    plural = [v for v in variants if v.lower().endswith("s")]
    pool = plural or variants
    return max(pool, key=lambda v: (len(v), v))


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item.lower() not in seen:
            seen.add(item.lower())
            out.append(item)
    return out
