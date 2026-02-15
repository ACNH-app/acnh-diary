from __future__ import annotations
import unicodedata


def normalize_name(value: str) -> str:
    lowered = value.strip().lower()
    lowered = "".join(
        ch for ch in unicodedata.normalize("NFKD", lowered) if not unicodedata.combining(ch)
    )
    cleaned = lowered.replace(".", "").replace("'", "").replace("-", " ")
    return " ".join(cleaned.split())
