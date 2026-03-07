import re
from typing import Any

NON_LATIN_LANGS = {
    "ar",
    "zh",
    "ja",
    "ko",
    "hi",
    "bn",
    "ta",
    "te",
    "kn",
    "ml",
    "gu",
    "mr",
    "pa",
    "or",
    "si",
    "ne",
    "my",
    "ru",
}

NON_LATIN_CHAR_RE = re.compile(
    r"[\u4E00-\u9FFF"  # CJK Unified Ideographs
    r"\u3040-\u30FF"  # Hiragana + Katakana
    r"\uAC00-\uD7AF"  # Hangul
    r"\u0590-\u05FF"  # Hebrew
    r"\u0600-\u06FF"  # Arabic
    r"\u0900-\u097F"  # Devanagari
    r"\u0980-\u09FF"  # Bengali
    r"\u0B80-\u0BFF"  # Tamil
    r"\u0C00-\u0C7F"  # Telugu
    r"\u0C80-\u0CFF"  # Kannada
    r"\u0D00-\u0D7F"  # Malayalam
    r"]"
)


def has_non_latin_chars(text: str) -> bool:
    """Return True if text contains any non-Latin script characters."""
    return bool(NON_LATIN_CHAR_RE.search(text))


def parse_fasttext_labels(labels: Any, probs: Any) -> list[tuple[str, float]]:
    """Parse fastText prediction output into (lang_code, probability) pairs."""
    labels_list = list(labels) if labels is not None else []
    probs_list = list(probs) if probs is not None else []
    preds: list[tuple[str, float]] = []
    for label, pr in zip(labels_list, probs_list, strict=False):
        if isinstance(label, bytes):
            try:
                label = label.decode("utf-8")
            except Exception:
                label = str(label)
        if isinstance(label, str):
            code = label.replace("__label__", "").strip()
            try:
                pr_val = float(pr)
            except Exception:
                pr_val = 0.0
            preds.append((code, pr_val))
    return preds


def is_blacklisted(
    preds: list[tuple[str, float]], threshold: float = 0.3
) -> tuple[str, float] | None:
    """Return the first blacklisted language prediction above threshold, or None."""
    for code, score in preds:
        if code in NON_LATIN_LANGS and score >= threshold:
            return (code, score)
    return None
