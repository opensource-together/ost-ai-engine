import pytest

from src.linker.prompts.registry import load_prompt
from src.linker.resources.llm_classifier_resource import (
    ClassificationResult,
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


class TestClassificationResultHasPromptVersion:
    def test_field_exists(self) -> None:
        """prompt_version is required so every persisted row can be audited."""
        r = ClassificationResult(
            category="A",
            domain="B",
            model="mistral-small-latest",
            prompt_version="classifier@v1-deadbeef",
            prompt_tokens=1,
            completion_tokens=2,
            total_tokens=3,
        )
        assert r.prompt_version == "classifier@v1-deadbeef"


class TestClassifierPromptBinding:
    def test_resource_exposes_prompt_fingerprint(self) -> None:
        """The resource must expose the same fingerprint the registry resolves,
        so asset metadata and persisted rows agree."""
        load_prompt.cache_clear()
        resource = LLMClassifierResource(api_key="dummy")
        expected = load_prompt("classifier", "v1").fingerprint
        assert resource.prompt.fingerprint == expected
