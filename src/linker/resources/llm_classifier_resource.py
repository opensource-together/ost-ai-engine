import json
import logging
import threading

import httpx
from dagster import ConfigurableResource
from openai import OpenAI
from pydantic import PrivateAttr

_LLM_CALL_TIMEOUT_SECONDS = 45


class LLMClassifierResource(ConfigurableResource):
    api_key: str
    model_id: str = "mistralai/mistral-small-3.2-24b-instruct"

    _client: OpenAI | None = PrivateAttr(default=None)

    @property
    def client(self) -> OpenAI:
        """Lazy-initialized singleton OpenAI client."""
        if self._client is None:
            self._client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.api_key,
                timeout=httpx.Timeout(30.0, connect=10.0, read=20.0, write=10.0),
                max_retries=1,
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
                "LLMResource: No OPENROUTER_API_KEY found in environment variables."
            )

        client = self.client

        # Truncate context to keep it snappy and cheap
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
                completion = client.chat.completions.create(
                    model=self.model_id,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    temperature=0.0,
                    response_format={"type": "json_object"},
                )
                content = completion.choices[0].message.content
                if content is None:
                    error_container[0] = ValueError("LLM returned empty content")
                    return
                clean_json = content.replace("```json", "").replace("```", "").strip()
                result_container[0] = json.loads(clean_json)
            except Exception as e:
                error_container[0] = e

        thread = threading.Thread(target=_call_api, daemon=True)
        thread.start()
        thread.join(timeout=_LLM_CALL_TIMEOUT_SECONDS)

        if thread.is_alive():
            logging.error(
                "OpenRouter API hard timeout "
                f"({_LLM_CALL_TIMEOUT_SECONDS}s) for {title}"
            )
            raise TimeoutError(
                f"OpenRouter API hard timeout after {_LLM_CALL_TIMEOUT_SECONDS}s "
                f"for project: {title}"
            )

        if error_container[0] is not None:
            logging.error(f"OpenRouter API Error for {title}: {error_container[0]}")
            raise RuntimeError(
                f"OpenRouter API error for {title}: {error_container[0]}"
            ) from error_container[0]

        if result_container[0] is not None:
            return result_container[0]

        raise RuntimeError(
            f"LLM classification failed for {title}: no result and no error"
        )
