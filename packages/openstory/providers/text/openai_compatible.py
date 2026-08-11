import json

import httpx
from pydantic import ValidationError

from openstory.providers.text.base import T
from openstory.services.json_repair import StructuredOutputError, extract_json_value


class TextGenerationError(RuntimeError):
    pass


class OpenAICompatibleTextProvider:
    def __init__(
        self,
        *,
        client: httpx.AsyncClient,
        base_url: str,
        api_key: str,
        model: str,
    ) -> None:
        self.client = client
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: type[T],
        temperature: float = 0.2,
    ) -> T:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        first_content = await self._complete(messages, temperature)
        try:
            return self._validate(first_content, schema)
        except (StructuredOutputError, ValidationError) as first_error:
            repair_messages = [
                *messages,
                {"role": "assistant", "content": first_content},
                {
                    "role": "user",
                    "content": (
                        "Your previous response failed structured validation. "
                        f"{_diagnostic(first_error)}\n"
                        "Return corrected JSON only. Do not add prose or Markdown fences."
                    ),
                },
            ]

        second_content = await self._complete(repair_messages, temperature)
        try:
            return self._validate(second_content, schema)
        except (StructuredOutputError, ValidationError) as second_error:
            raise TextGenerationError(
                "Text model returned two invalid structured responses: "
                f"{_diagnostic(second_error)}"
            ) from second_error

    async def _complete(
        self,
        messages: list[dict[str, str]],
        temperature: float,
    ) -> str:
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                },
            )
        except httpx.HTTPError as error:
            raise TextGenerationError(
                f"Text generation transport failed: {type(error).__name__}."
            ) from error

        if not response.is_success:
            raise TextGenerationError(
                f"Text generation request failed with HTTP {response.status_code}."
            )
        try:
            payload = response.json()
            content = payload["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as error:
            raise TextGenerationError(
                "Text generation response is missing message content."
            ) from error
        if not isinstance(content, str) or not content.strip():
            raise TextGenerationError(
                "Text generation response is missing message content."
            )
        return content

    @staticmethod
    def _validate(content: str, schema: type[T]) -> T:
        return schema.model_validate(extract_json_value(content))

    async def aclose(self) -> None:
        await self.client.aclose()


def _diagnostic(error: StructuredOutputError | ValidationError) -> str:
    if isinstance(error, StructuredOutputError):
        return f"StructuredOutputError: {error}"
    details = error.errors(
        include_url=False,
        include_context=False,
        include_input=False,
    )
    return f"ValidationError: {json.dumps(details, default=str)[:1_000]}"
