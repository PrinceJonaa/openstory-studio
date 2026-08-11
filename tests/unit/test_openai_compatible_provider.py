import json

import httpx
import pytest
from openstory.domain.canon import CanonExtractionResponse
from openstory.providers.text.openai_compatible import (
    OpenAICompatibleTextProvider,
    TextGenerationError,
)


def valid_response(content: str) -> httpx.Response:
    return httpx.Response(
        200,
        json={"choices": [{"message": {"content": content}}]},
    )


@pytest.mark.asyncio
async def test_provider_validates_chat_completion_json() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer local"
        body = json.loads(request.content)
        assert body["model"] == "local-model"
        assert body["temperature"] == 0.2
        assert body["messages"] == [
            {"role": "system", "content": "archivist"},
            {"role": "user", "content": "source"},
        ]
        assert "tools" not in body
        assert "response_format" not in body
        return valid_response(
            '{"entities":[],"facts":[],"unresolved_references":[]}'
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = OpenAICompatibleTextProvider(
            client=client,
            base_url="http://local.test/v1",
            api_key="local",
            model="local-model",
        )
        result = await provider.generate_structured(
            system_prompt="archivist",
            user_prompt="source",
            schema=CanonExtractionResponse,
        )

    assert result.entities == []


@pytest.mark.asyncio
async def test_provider_repairs_one_invalid_json_response() -> None:
    requests: list[dict[str, object]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(json.loads(request.content))
        if len(requests) == 1:
            return valid_response("not json")
        return valid_response(
            '```json\n{"entities":[],"facts":[],"unresolved_references":[]}\n```'
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = OpenAICompatibleTextProvider(
            client=client,
            base_url="http://local.test/v1/",
            api_key="local",
            model="local-model",
        )
        result = await provider.generate_structured(
            system_prompt="archivist",
            user_prompt="source",
            schema=CanonExtractionResponse,
        )

    assert result.facts == []
    assert len(requests) == 2
    repair_messages = requests[1]["messages"]
    assert isinstance(repair_messages, list)
    assert "Return corrected JSON only" in repair_messages[-1]["content"]
    assert "StructuredOutputError" in repair_messages[-1]["content"]


@pytest.mark.asyncio
async def test_provider_repairs_one_schema_validation_failure() -> None:
    calls = 0

    async def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return valid_response(
                '{"entities":[],"facts":[],"unresolved_references":[],"invented":true}'
            )
        return valid_response(
            '{"entities":[],"facts":[],"unresolved_references":[]}'
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await OpenAICompatibleTextProvider(
            client=client,
            base_url="http://local.test/v1",
            api_key="local",
            model="local-model",
        ).generate_structured(
            system_prompt="archivist",
            user_prompt="source",
            schema=CanonExtractionResponse,
        )

    assert result.entities == []
    assert calls == 2


@pytest.mark.asyncio
async def test_provider_stops_after_two_invalid_structured_responses() -> None:
    calls = 0

    async def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return valid_response("still not json")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = OpenAICompatibleTextProvider(
            client=client,
            base_url="http://local.test/v1",
            api_key="local",
            model="local-model",
        )
        with pytest.raises(TextGenerationError, match="two invalid structured responses"):
            await provider.generate_structured(
                system_prompt="archivist",
                user_prompt="source",
                schema=CanonExtractionResponse,
            )

    assert calls == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("response", "message"),
    [
        (httpx.Response(401, json={"error": "unauthorized"}), "HTTP 401"),
        (httpx.Response(200, json={"choices": []}), "missing message content"),
    ],
)
async def test_provider_does_not_retry_http_or_envelope_failures(
    response: httpx.Response,
    message: str,
) -> None:
    calls = 0

    async def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return response

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = OpenAICompatibleTextProvider(
            client=client,
            base_url="http://local.test/v1",
            api_key="local",
            model="local-model",
        )
        with pytest.raises(TextGenerationError, match=message):
            await provider.generate_structured(
                system_prompt="archivist",
                user_prompt="source",
                schema=CanonExtractionResponse,
            )

    assert calls == 1


def test_build_text_provider_selects_mock_and_rejects_unknown_names() -> None:
    from openstory.providers.text.mock import MockTextProvider
    from openstory_api.dependencies import (
        Settings,
        TextProviderConfigurationError,
        build_text_provider,
    )

    assert isinstance(build_text_provider(Settings(text_provider="mock")), MockTextProvider)
    with pytest.raises(TextProviderConfigurationError, match="Unknown text provider"):
        build_text_provider(Settings(text_provider="mystery"))
