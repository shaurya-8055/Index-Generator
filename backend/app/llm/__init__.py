"""LLM integration layer (LangChain) with a dependency-free fallback."""

from .extractor import extract_topics
from .normalizer_llm import llm_normalize_topics
from .providers import get_chat_model, llm_available

__all__ = [
    "get_chat_model",
    "llm_available",
    "extract_topics",
    "llm_normalize_topics",
]
