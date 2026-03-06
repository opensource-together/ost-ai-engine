import datetime
import uuid
from typing import Any


def make_serializable(obj: Any) -> Any:
    """Convert datetime, date, and UUID objects to JSON-serializable strings."""
    if isinstance(obj, datetime.datetime | datetime.date):
        return obj.isoformat()
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_serializable(v) for v in obj]
    return obj


def clean_llm_json(raw: str) -> str:
    """Strip markdown code fences from LLM JSON responses."""
    return raw.replace("```json", "").replace("```", "").strip()
