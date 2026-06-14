"""LLM-powered topic normalization (synonyms, abbreviations, plural merging).

Falls back to the heuristic normalizer when no LLM is configured or the call
fails. Output shape matches ``app.indexing.normalizer.normalize_topics``:
``{canonical_label: [variant, ...]}``.
"""
from __future__ import annotations

import json
import logging
import re

from app.indexing.normalizer import normalize_topics as heuristic_normalize
from app.llm.providers import get_chat_model, llm_available

logger = logging.getLogger(__name__)

_NORMALIZE_SYSTEM = (
    "You are an expert indexer who consolidates topic lists for a book index."
)

_NORMALIZE_INSTRUCTIONS = """\
Consolidate the following topics into canonical index entries.

Rules:
- Merge synonyms (e.g. "BFS" and "Breadth First Search" -> "Breadth First Search (BFS)").
- Merge singular/plural forms (e.g. "Binary Tree", "Binary Trees" -> "Binary Trees").
- Merge capitalization/spelling variants.
- Keep distinct concepts separate.

Respond with ONLY a JSON object mapping each canonical label to the list of
original topics it absorbs, e.g.:
{{"Binary Trees": ["Binary Tree", "Binary Trees"], "Breadth First Search (BFS)": ["BFS", "Breadth First Search"]}}

TOPICS:
{topics}
"""


def llm_normalize_topics(topics: list[str]) -> dict[str, list[str]]:
    topics = [t for t in dict.fromkeys(topics) if t and t.strip()]
    if not topics:
        return {}

    if llm_available():
        try:
            return _llm_normalize(topics)
        except Exception as exc:  # pragma: no cover - network/credentials
            logger.warning("LLM normalization failed (%s); using heuristic", exc)

    return heuristic_normalize(topics)


def _llm_normalize(topics: list[str]) -> dict[str, list[str]]:
    from langchain_core.messages import HumanMessage, SystemMessage

    model = get_chat_model()
    prompt = _NORMALIZE_INSTRUCTIONS.format(topics=json.dumps(topics, ensure_ascii=False))
    response = model.invoke(
        [SystemMessage(content=_NORMALIZE_SYSTEM), HumanMessage(content=prompt)]
    )
    raw = response.content if hasattr(response, "content") else str(response)
    mapping = _parse_json_object(raw)
    if not mapping:
        return heuristic_normalize(topics)

    # Guarantee every input topic is represented somewhere.
    covered = {v.lower() for variants in mapping.values() for v in variants}
    for t in topics:
        if t.lower() not in covered:
            mapping.setdefault(t, []).append(t)
    return mapping


def _parse_json_object(raw: str) -> dict[str, list[str]]:
    raw = raw.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL)
    if fence:
        raw = fence.group(1).strip()
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        raw = match.group(0)
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return {
                str(k): [str(x) for x in (v if isinstance(v, list) else [v])]
                for k, v in data.items()
            }
    except json.JSONDecodeError:
        logger.warning("Could not parse LLM normalization JSON: %s", raw[:200])
    return {}
