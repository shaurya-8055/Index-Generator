"""LangChain chat-model factory supporting OpenAI, Gemini and Ollama.

If the configured provider is ``fallback`` (or required credentials/packages
are missing) callers should use the heuristic code paths instead. Use
``llm_available()`` to decide.
"""
from __future__ import annotations

import logging

from app.config import settings

logger = logging.getLogger(__name__)

_DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "gemini": "gemini-1.5-flash",
    "ollama": "llama3.1",
}


def llm_available() -> bool:
    """True when a real LLM provider is configured with the needed credentials."""
    provider = settings.llm_provider.lower()
    if provider == "openai":
        return bool(settings.openai_api_key)
    if provider == "gemini":
        return bool(settings.google_api_key)
    if provider == "ollama":
        return True  # local server; availability checked lazily at call time
    return False


def get_chat_model():
    """Instantiate a LangChain chat model for the configured provider.

    Raises ``RuntimeError`` when the provider is ``fallback`` or unsupported.
    """
    provider = settings.llm_provider.lower()
    model = settings.llm_model or _DEFAULT_MODELS.get(provider, "")
    temperature = settings.llm_temperature

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=settings.openai_api_key,
            max_retries=settings.llm_max_retries,
        )
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=settings.google_api_key,
            # Fail fast so we fall back to the heuristic quickly on quota errors
            # instead of retrying with long backoffs on every chunk.
            max_retries=settings.llm_max_retries,
        )
    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=model,
            temperature=temperature,
            base_url=settings.ollama_base_url,
        )

    raise RuntimeError(
        f"No real LLM configured (provider={provider!r}); use the heuristic fallback."
    )
