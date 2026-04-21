import json
import logging
import threading

from dagster import ConfigurableResource
from mistralai import Mistral
from mistralai.models import (
    AssistantMessage,
    SystemMessage,
    ToolMessage,
    UserMessage,
)
from pydantic import PrivateAttr

from src.linker.utils.serialization import clean_llm_json

_LLM_CALL_TIMEOUT_SECONDS = 45
_LLM_CLIENT_TIMEOUT_MS = 30000


class LLMClassifierResource(ConfigurableResource):
    api_key: str
    model_id: str = "mistral-small-latest"

    _client: Mistral | None = PrivateAttr(default=None)

    @property
    def client(self) -> Mistral:
        """Lazy-initialized singleton Mistral client."""
        if self._client is None:
            self._client = Mistral(
                api_key=self.api_key,
                timeout_ms=_LLM_CLIENT_TIMEOUT_MS,
            )
        return self._client

    def classify_project(
        self,
        title: str,
        project_context: str,
        categories: list[str],
        domains: list[str],
    ) -> dict:
        """Classify a project using its context and valid labels.

        Takes a project in context (title, description, topics, readme)
        and the list of valid categories/domains from OST.
        Returns a Dict with the classification.

        Raises:
            ValueError: If API key is missing or LLM returns empty content.
            TimeoutError: If the LLM call exceeds the hard timeout.
            RuntimeError: For API errors or unknown failures.
        """
        if not self.api_key:
            raise ValueError(
                "LLMResource: No MISTRAL_API_KEY found in environment variables."
            )

        client = self.client

        truncated_context = (project_context or "")[:8000]

        cats_str = ", ".join(categories)
        doms_str = ", ".join(domains)

        system_prompt = (
            "You are an expert technical classifier. "
            "Analyze the GitHub project context "
            "(Title, Description, Topics, Readme) "
            "and classify it.\n"
            f"1. Assign the single most relevant Category from: [{cats_str}]\n"
            f"2. Assign the single most relevant Domain from: [{doms_str}]\n"
            "If unsure, pick the closest match or null.\n"
            "Response format: JSON ONLY, no markdown, no explanation.\n"
            'Example: {"category": "Framework", "domain": "Web Development"}'
        )

        user_content = f"Title: {title}\n\nProject Context:\n{truncated_context}"

        result_container: list[dict[str, object] | None] = [None]
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
                result_container[0] = json.loads(clean_llm_json(content_str))
            except Exception as e:
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
            raise RuntimeError(
                f"Mistral API error for {title}: {error_container[0]}"
            ) from error_container[0]

        if result_container[0] is not None:
            return result_container[0]

        raise RuntimeError(
            f"LLM classification failed for {title}: no result and no error"
        )
