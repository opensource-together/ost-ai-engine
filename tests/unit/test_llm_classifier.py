import pytest

from src.linker.resources.llm_classifier_resource import (
    LLMClassifierResource,
    RateLimitError,
)


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


class TestRateLimitError:
    def test_rate_limit_is_distinguishable(self) -> None:
        """RateLimitError is its own exception type so callers can back off longer."""
        err = RateLimitError("429 Too Many Requests")
        assert isinstance(err, Exception)
        assert "429" in str(err)
