from __future__ import annotations


def normalize_name(value: str) -> str:
    lowered = value.strip().lower()
    cleaned = lowered.replace(".", "").replace("'", "").replace("-", " ")
    return " ".join(cleaned.split())
