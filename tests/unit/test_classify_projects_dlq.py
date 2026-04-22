"""DLQ resilience tests for the classifier asset.

The DLQ is a monitoring-only table. A failed insert (e.g. Postgres
ForeignKeyViolation during the gap between classification and sync) must
NOT abort the classifier's batch — otherwise every successful classification
in the run is lost. These tests pin that contract.
"""

from unittest.mock import MagicMock, patch

import psycopg2
import pytest

from src.linker.assets.classification.core_match__classify_projects import (
    _persist_failures,
)


@pytest.fixture
def logger() -> MagicMock:
    return MagicMock()


def _cursor_cm(cursor: MagicMock) -> MagicMock:
    """Return a MagicMock that behaves like `get_db_cursor(commit=...)`."""
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=cursor)
    cm.__exit__ = MagicMock(return_value=False)
    return cm


class TestPersistFailures:
    def test_all_succeed_returns_full_count(self, logger: MagicMock) -> None:
        cur = MagicMock()
        with patch(
            "src.linker.assets.classification.core_match__classify_projects.get_db_cursor",
            return_value=_cursor_cm(cur),
        ):
            count = _persist_failures(
                [("id1", "err1"), ("id2", "err2"), ("id3", "err3")],
                logger,
            )
        assert count == 3
        logger.warning.assert_not_called()

    def test_fk_violation_on_one_does_not_abort_batch(self, logger: MagicMock) -> None:
        """A single FK violation must not poison the whole DLQ write."""
        cur_ok = MagicMock()
        cur_bad = MagicMock()
        cur_bad.execute.side_effect = psycopg2.errors.ForeignKeyViolation(
            'insert or update on table "project_classification_failure" '
            "violates foreign key constraint "
            '"project_classification_failure_projectId_fkey"'
        )
        cur_ok2 = MagicMock()

        cursors = iter([_cursor_cm(cur_ok), _cursor_cm(cur_bad), _cursor_cm(cur_ok2)])
        with patch(
            "src.linker.assets.classification.core_match__classify_projects.get_db_cursor",
            side_effect=lambda *a, **kw: next(cursors),
        ):
            count = _persist_failures(
                [("ok1", "err"), ("bad", "err"), ("ok2", "err")],
                logger,
            )

        assert count == 2
        assert logger.warning.call_count == 1
        (msg,), _ = logger.warning.call_args
        assert "bad" in msg

    def test_every_write_uses_isolated_transaction(self, logger: MagicMock) -> None:
        """Each DLQ row is written in its own commit so one failure can't
        abort siblings inside the same transaction."""
        call_kwargs: list[dict] = []

        def fake_cursor(*args, **kwargs) -> MagicMock:
            call_kwargs.append(kwargs)
            return _cursor_cm(MagicMock())

        with patch(
            "src.linker.assets.classification.core_match__classify_projects.get_db_cursor",
            side_effect=fake_cursor,
        ):
            _persist_failures([("a", "e"), ("b", "e")], logger)

        assert len(call_kwargs) == 2
        for kw in call_kwargs:
            assert kw.get("commit") is True

    def test_empty_list_is_noop(self, logger: MagicMock) -> None:
        with patch(
            "src.linker.assets.classification.core_match__classify_projects.get_db_cursor"
        ) as cur_mock:
            count = _persist_failures([], logger)
        assert count == 0
        cur_mock.assert_not_called()
