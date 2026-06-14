"""Dependency-free text utilities shared by extraction and mapping."""
from __future__ import annotations

import re

# A compact English stop-word list — enough to filter index noise without
# pulling in a heavyweight NLP dependency.
STOP_WORDS: frozenset[str] = frozenset(
    """
    a an the and or but if then else when while for of to in on at by with from into
    over under again further once here there all any both each few more most other some
    such no nor not only own same so than too very can will just should now is are was
    were be been being have has had do does did doing this that these those it its it's
    as about above below up down out off again i you he she we they them his her their our
    your my me him us also which who whom whose what where why how between within without
    upon per via etc eg ie vs
    """.split()
)

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9'\-]*")
_MULTISPACE_RE = re.compile(r"\s+")

# Acronyms / initialisms that should keep their casing.
_KNOWN_ACRONYMS = {
    "bfs", "dfs", "api", "http", "https", "sql", "html", "css", "json", "xml",
    "ai", "ml", "nlp", "ocr", "cpu", "gpu", "io", "url", "uri", "tcp", "udp",
    "rest", "crud", "orm", "jwt", "ui", "ux", "id", "os", "db",
}


def clean_whitespace(text: str) -> str:
    return _MULTISPACE_RE.sub(" ", text).strip()


def tokenize(text: str) -> list[str]:
    """Return lowercase word tokens, excluding stop words and single chars."""
    tokens = _WORD_RE.findall(text.lower())
    return [t for t in tokens if len(t) > 1 and t not in STOP_WORDS]


def normalize_topic_label(topic: str) -> str:
    """Normalize a topic's display label: trim, collapse spaces, title-case
    while preserving known acronyms."""
    topic = clean_whitespace(topic)
    if not topic:
        return ""

    words = topic.split(" ")
    result: list[str] = []
    for word in words:
        # Preserve parenthetical acronyms like "(BFS)".
        bare = word.strip("()").lower()
        if bare in _KNOWN_ACRONYMS:
            result.append(word.replace(bare, bare.upper()))
        elif word.isupper() and len(word) <= 5:
            result.append(word)  # already an acronym
        else:
            result.append(word[:1].upper() + word[1:].lower() if word else word)
    return " ".join(result)


def topic_key(topic: str) -> str:
    """A normalized matching key for dedup / synonym comparison."""
    return clean_whitespace(topic.lower()).rstrip("s")
