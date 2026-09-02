from unittest.mock import MagicMock, patch

from src.linker.assets.classification.core_match__classify_projects import (
    _count_status,
    _estimated_cost_usd,
    _persist_usage,
)


class TestEstimatedCost:
    def test_zero_tokens_is_zero(self) -> None:
        assert _estimated_cost_usd(0, 0) == 0.0

    def test_one_million_input_tokens(self) -> None:
        assert _estimated_cost_usd(1_000_000, 0) == 0.2


class TestCountStatus:
    def test_counts_402_in_error_text(self) -> None:
        failures = [
            ("a", "RuntimeError: Mistral API error: Status 402 insufficient_quota"),
            ("b", "RateLimitError: 429 Too Many Requests"),
        ]
        assert _count_status(failures, "402") == 1
        assert _count_status(failures, "429") == 1


class TestPersistUsage:
    def test_inserts_usage_row(self) -> None:
        cur = MagicMock()
        cm = MagicMock()
        cm.__enter__.return_value = cur
        cm.__exit__.return_value = False

        with patch(
            "src.linker.assets.classification.core_match__classify_projects.get_db_cursor",
            return_value=cm,
        ):
            _persist_usage(
                MagicMock(),
                model="mistral-small-latest",
                prompt_tokens=10,
                completion_tokens=5,
                estimated_cost_usd=0.001,
                requests=3,
                http_402=1,
                http_429=0,
            )

        sql = cur.execute.call_args[0][0]
        params = cur.execute.call_args[0][1]
        assert "match.llm_usage" in sql
        assert params == ("mistral-small-latest", 10, 5, 0.001, 3, 1, 0)

    def test_skips_empty_usage(self) -> None:
        with patch(
            "src.linker.assets.classification.core_match__classify_projects.get_db_cursor"
        ) as mock_get_db:
            _persist_usage(
                MagicMock(),
                model="mistral-small-latest",
                prompt_tokens=0,
                completion_tokens=0,
                estimated_cost_usd=0.0,
                requests=0,
                http_402=0,
                http_429=0,
            )
        mock_get_db.assert_not_called()
