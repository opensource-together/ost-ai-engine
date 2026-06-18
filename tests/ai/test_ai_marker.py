"""Placeholder for real AI/LLM integration tests (RUN_AI_TESTS=1)."""

import pytest


@pytest.mark.ai
class TestAiMarker:
    def test_ai_suite_requires_explicit_opt_in(self) -> None:
        """Skipped in CI unless RUN_AI_TESTS=1 is set."""
        pytest.skip("Add real LLM/API tests here when needed.")
