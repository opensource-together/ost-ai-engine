import json
import logging
import threading
from dataclasses import dataclass

from dagster import ConfigurableResource
from mistralai import Mistral
from mistralai.models import (
    AssistantMessage,
    SystemMessage,
    ToolMessage,
    UserMessage,
)
from pydantic import PrivateAttr

from src.linker.prompts import PromptTemplate, load_prompt
from src.linker.utils.serialization import clean_llm_json

_LLM_CALL_TIMEOUT_SECONDS = 45
_LLM_CLIENT_TIMEOUT_MS = 30000
_DEFAULT_CONTEXT_CHARS = 8000


class RateLimitError(Exception):
    """Raised on Mistral 429 — callers should back off longer than a normal retry."""


@dataclass(frozen=True)
class ClassificationResult:
    """Structured output of a classify_project call.

    Includes the model and the prompt fingerprint so every persisted
    classification can be attributed to the exact model + prompt text that
    produced it.
    """

    category: str | None
    domain: str | None
    model: str
    prompt_version: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class LLMClassifierResource(ConfigurableResource):
    api_key: str
    model_id: str = "mistral-small-latest"
    context_chars: int = _DEFAULT_CONTEXT_CHARS
    prompt_name: str = "classifier"
    prompt_version: str = "v1"

    _client: Mistral | None = PrivateAttr(default=None)
    _prompt: PromptTemplate | None = PrivateAttr(default=None)

    @property
    def client(self) -> Mistral:
        """Lazy-initialized singleton Mistral client."""
        if self._client is None:
            self._client = Mistral(
                api_key=self.api_key,
                timeout_ms=_LLM_CLIENT_TIMEOUT_MS,
            )
        return self._client

    @property
    def prompt(self) -> PromptTemplate:
        """Lazy-loaded versioned prompt template."""
        if self._prompt is None:
            self._prompt = load_prompt(self.prompt_name, self.prompt_version)
        return self._prompt

    def classify_project(
        self,
        title: str,
        project_context: str,
        categories: list[str],
        domains: list[str],
    ) -> ClassificationResult:
        """Classify a project using its context and valid labels.

        Raises:
            ValueError: If API key is missing or LLM returns empty content.
            RateLimitError: If Mistral returns a 429 — use a longer backoff.
            TimeoutError: If the LLM call exceeds the hard timeout.
            RuntimeError: For API errors or unknown failures.
        """
        if not self.api_key:
            raise ValueError(
                "LLMResource: No MISTRAL_API_KEY found in environment variables."
            )

        client = self.client
        prompt = self.prompt
        truncated_context = (project_context or "")[: self.context_chars]

        system_prompt, user_content = prompt.render(
            categories=", ".join(categories),
            domains=", ".join(domains),
            title=title,
            context=truncated_context,
        )

        result_container: list[ClassificationResult | None] = [None]
        error_container: list[Exception | None] = [None]

        def _call_api() -> None:
            try:
                messages: list[
                    AssistantMessage | SystemMessage | ToolMessage | UserMessage
                ] = [
                    SystemMessage(content=system_prompt),
                    UserMessage(content=user_content),
                ]
                completion = client.chat.complete(
                    model=self.model_id,
                    messages=messages,
                    temperature=0.0,
                    response_format={"type": "json_object"},
                )
                if completion.choices is None or len(completion.choices) == 0:
                    error_container[0] = ValueError("LLM returned no choices")
                    return
                content = completion.choices[0].message.content
                if content is None or content == "":
                    error_container[0] = ValueError("LLM returned empty content")
                    return
                if isinstance(content, list):
                    content_str = "".join(
                        chunk.text if hasattr(chunk, "text") else str(chunk)
                        for chunk in content
                    )
                elif isinstance(content, str):
                    content_str = content
                else:
                    error_container[0] = ValueError(
                        f"LLM returned unexpected content type: {type(content)}"
                    )
                    return
                parsed = json.loads(clean_llm_json(content_str))
                usage = completion.usage
                result_container[0] = ClassificationResult(
                    category=parsed.get("category"),
                    domain=parsed.get("domain"),
                    model=self.model_id,
                    prompt_version=prompt.fingerprint,
                    prompt_tokens=(usage.prompt_tokens if usage else 0) or 0,
                    completion_tokens=(usage.completion_tokens if usage else 0) or 0,
                    total_tokens=(usage.total_tokens if usage else 0) or 0,
                )
            except Exception as e:
                msg = str(e).lower()
                if "429" in msg or "rate limit" in msg or "too many requests" in msg:
                    error_container[0] = RateLimitError(str(e))
                else:
                    error_container[0] = e

        thread = threading.Thread(target=_call_api, daemon=True)
        thread.start()
        thread.join(timeout=_LLM_CALL_TIMEOUT_SECONDS)

        if thread.is_alive():
            logging.error(
                f"Mistral API hard timeout ({_LLM_CALL_TIMEOUT_SECONDS}s) for {title}"
            )
            raise TimeoutError(
                f"Mistral API hard timeout after {_LLM_CALL_TIMEOUT_SECONDS}s "
                f"for project: {title}"
            )

        if error_container[0] is not None:
            logging.error(f"Mistral API Error for {title}: {error_container[0]}")
            if isinstance(error_container[0], RateLimitError):
                raise error_container[0]
            raise RuntimeError(
                f"Mistral API error for {title}: {error_container[0]}"
            ) from error_container[0]

        if result_container[0] is not None:
            return result_container[0]

        raise RuntimeError(
            f"LLM classification failed for {title}: no result and no error"
        )
