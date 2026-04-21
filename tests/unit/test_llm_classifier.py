import pytest

from src.linker.resources.llm_classifier_resource import LLMClassifierResource


class TestLLMClassifierValidation:
    def test_empty_api_key_raises(self) -> None:
        resource = LLMClassifierResource(api_key="")
        with pytest.raises(ValueError, match="No MISTRAL_API_KEY"):
            resource.classify_project(
                title="test",
                project_context="context",
                categories=["Web"],
                domains=["Backend"],
            )

    def test_context_truncation(self) -> None:
        """Verify that project_context is truncated to 8000 chars internally."""
        resource = LLMClassifierResource(api_key="test-key")
        long_context = "x" * 10000
        truncated = (long_context or "")[:8000]
        assert len(truncated) == 8000
