"""Service layer: orchestrates the workflow and persistence."""

from .index_service import generate_index_for_document, search_index

__all__ = ["generate_index_for_document", "search_index"]
