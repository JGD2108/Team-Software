import re
import unicodedata


def normalize_report_text(value: str) -> str:
    """Return consistent, readable Spanish text while preserving accents."""
    text = unicodedata.normalize("NFKC", value)
    text = re.sub(r"\s+", " ", text.strip())
    text = re.sub(r"\s+([,.;:])", r"\1", text)
    return text.upper()
