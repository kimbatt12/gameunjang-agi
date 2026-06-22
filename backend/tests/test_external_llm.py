import httpx

from app.external.llm import (
    FallbackLLMProvider,
    LLMMessage,
    LLMProviderError,
    LLMRequest,
    OpenRouterProvider,
    UpstageProvider,
)


def test_upstage_provider_returns_successful_completion() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/solar/chat/completions"
        assert request.headers["authorization"] == "Bearer placeholder-upstage-key"
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "부산 실내 관광지입니다."}}]},
        )

    provider = UpstageProvider(
        api_key="placeholder-upstage-key",
        model="placeholder-upstage-model",
        client=httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url="https://api.upstage.ai/v1/solar",
        ),
    )

    response = provider.complete(_request())

    assert response.text == "부산 실내 관광지입니다."
    assert response.provider == "upstage"
    assert response.model == "placeholder-upstage-model"
    assert response.warnings == ()


def test_openrouter_provider_is_used_as_fallback_after_primary_failure() -> None:
    primary = _FailingProvider("upstage")

    def fallback_handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "fallback answer"}}]},
        )

    fallback = OpenRouterProvider(
        api_key="placeholder-openrouter-key",
        model="placeholder-openrouter-model",
        client=httpx.Client(
            transport=httpx.MockTransport(fallback_handler),
            base_url="https://openrouter.ai/api/v1",
        ),
    )
    provider = FallbackLLMProvider(primary=primary, fallback=fallback)

    response = provider.complete(_request())

    assert response.text == "fallback answer"
    assert response.provider == "openrouter"
    assert response.warnings == ("llm_provider_fallback_from_upstage",)


def test_provider_timeout_raises_provider_error() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out")

    provider = UpstageProvider(
        api_key="placeholder-upstage-key",
        model="placeholder-upstage-model",
        client=httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url="https://api.upstage.ai/v1/solar",
        ),
    )

    try:
        provider.complete(_request())
    except LLMProviderError as exc:
        assert "upstage provider failed" in str(exc)
    else:
        raise AssertionError("expected LLMProviderError")


class _FailingProvider:
    def __init__(self, name: str) -> None:
        self.name = name

    def complete(self, request: LLMRequest):
        raise LLMProviderError("primary failed")


def _request() -> LLMRequest:
    return LLMRequest(
        messages=(LLMMessage(role="user", content="부산 관광지 추천"),),
        max_tokens=128,
    )
