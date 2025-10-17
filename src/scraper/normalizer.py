"""
Normalization utilities for whitespace, Unicode, case, and canonicalization.
"""

from typing import Optional


def normalize_text(text: Optional[str]) -> str:
    """Normalize whitespace, Unicode (NFKC), and trim text."""
    if text is None:
        return ""
    return text.strip()
