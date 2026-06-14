"""Document parsing: turn uploaded files into a {page_number: text} map."""

from .loader import SUPPORTED_EXTENSIONS, ParsedDocument, load_document

__all__ = ["load_document", "ParsedDocument", "SUPPORTED_EXTENSIONS"]
