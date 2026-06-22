from dataclasses import dataclass
from typing import Protocol

import httpx


class LLMProviderError(RuntimeError):
    """Raised when an LLM provider cannot produce a response."""


@dataclass(frozen=True)
class LLMMessage:
    role: str
    content: str


@dataclass(frozen=True)
class LLMRequest:
    messages: tuple[LLMMessage, ...]
    max_tokens: int
    temperature: float = 0.2


@dataclass(frozen=True)
class LLMResponse:
    text: str
    provider: str
    model: str
    warnings: tuple[str, ...] = ()


class LLMProvider(Protocol):
    name: str

    def complete(self, request: LLMRequest) -> LLMResponse:
        """Return a single text completion for the request."""


class ChatCompletionsProvider:
    name: str

    def __init__(
        self,
        *,
        name: str,
        api_key: str,
        model: str,
        base_url: str,
        timeout_seconds: float = 10.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.name = name
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._client = client

    def complete(self, request: LLMRequest) -> LLMResponse:
        payload = {
            "model": self._model,
            "messages": [
                {"role": message.role, "content": message.content}
                for message in request.messages
            ],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }
        headers = {"Authorization": f"Bearer {self._api_key}"}

        try:
            response = self._post(payload, headers)
            response.raise_for_status()
            text = _extract_chat_completion_text(response.json())
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError(f"{self.name} provider failed") from exc

        if not text:
            raise LLMProviderError(f"{self.name} provider returned empty content")

        return LLMResponse(text=text, provider=self.name, model=self._model)

    def _post(
        self,
        payload: dict[str, object],
        headers: dict[str, str],
    ) -> httpx.Response:
        if self._client is not None:
            return self._client.post("/chat/completions", json=payload, headers=headers)

        with httpx.Client(
            base_url=self._base_url,
            timeout=self._timeout_seconds,
        ) as client:
            return client.post("/chat/completions", json=payload, headers=headers)


class UpstageProvider(ChatCompletionsProvider):
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout_seconds: float = 10.0,
        client: httpx.Client | None = None,
    ) -> None:
        super().__init__(
            name="upstage",
            api_key=api_key,
            model=model,
            base_url="https://api.upstage.ai/v1/solar",
            timeout_seconds=timeout_seconds,
            client=client,
        )


class OpenRouterProvider(ChatCompletionsProvider):
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout_seconds: float = 10.0,
        client: httpx.Client | None = None,
    ) -> None:
        super().__init__(
            name="openrouter",
            api_key=api_key,
            model=model,
            base_url="https://openrouter.ai/api/v1",
            timeout_seconds=timeout_seconds,
            client=client,
        )


class FallbackLLMProvider:
    name = "fallback"

    def __init__(self, primary: LLMProvider, fallback: LLMProvider) -> None:
        self._primary = primary
        self._fallback = fallback

    def complete(self, request: LLMRequest) -> LLMResponse:
        try:
            return self._primary.complete(request)
        except LLMProviderError:
            fallback_response = self._fallback.complete(request)
            return LLMResponse(
                text=fallback_response.text,
                provider=fallback_response.provider,
                model=fallback_response.model,
                warnings=(
                    *fallback_response.warnings,
                    f"llm_provider_fallback_from_{self._primary.name}",
                ),
            )


def _extract_chat_completion_text(payload: dict[str, object]) -> str:
    choices = payload["choices"]
    if not isinstance(choices, list):
        raise TypeError("choices must be a list")

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise TypeError("choice must be an object")

    message = first_choice["message"]
    if not isinstance(message, dict):
        raise TypeError("message must be an object")

    content = message["content"]
    if not isinstance(content, str):
        raise TypeError("content must be a string")

    return content.strip()
