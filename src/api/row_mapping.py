"""Normalize SQLAlchemy mapping rows for FastAPI/Pydantic (UUID → str)."""

from typing import Any
from uuid import UUID

from sqlalchemy.engine import Result


def mapping_rows(result: Result[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in result.mappings().all():
        d = dict(row)
        for key, val in list(d.items()):
            if isinstance(val, UUID):
                d[key] = str(val)
        rows.append(d)
    return rows


def mapping_row_first(result: Result[Any]) -> dict[str, Any] | None:
    row = result.mappings().first()
    if row is None:
        return None
    d = dict(row)
    for key, val in list(d.items()):
        if isinstance(val, UUID):
            d[key] = str(val)
    return d
