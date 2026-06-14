"""Index construction: extraction support, page mapping, formatting."""

from .formatter import format_index, format_index_text
from .page_mapper import map_topics_to_pages
from .normalizer import normalize_topics

__all__ = [
    "map_topics_to_pages",
    "normalize_topics",
    "format_index",
    "format_index_text",
]
