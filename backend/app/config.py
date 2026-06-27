import os
from functools import lru_cache

DEFAULT_MAX_USER_MESSAGE_CHARS = 1000


class Settings:
    def __init__(
        self,
        *,
        max_user_message_chars: int,
        tour_api_service_key: str | None,
        kma_api_key: str | None,
        upstage_api_key: str | None,
        upstage_model: str | None,
        openrouter_api_key: str | None,
        openrouter_model: str | None,
    ) -> None:
        self.max_user_message_chars = max_user_message_chars
        self.tour_api_service_key = tour_api_service_key
        self.kma_api_key = kma_api_key
        self.upstage_api_key = upstage_api_key
        self.upstage_model = upstage_model
        self.openrouter_api_key = openrouter_api_key
        self.openrouter_model = openrouter_model


@lru_cache
def get_settings() -> Settings:
    raw_limit = os.getenv("MAX_USER_MESSAGE_CHARS")
    parsed_limit = DEFAULT_MAX_USER_MESSAGE_CHARS
    if raw_limit is not None:
        try:
            parsed_limit = int(raw_limit)
        except ValueError:
            parsed_limit = DEFAULT_MAX_USER_MESSAGE_CHARS

    return Settings(
        max_user_message_chars=max(1, parsed_limit),
        tour_api_service_key=_optional_env("TOUR_API_SERVICE_KEY"),
        kma_api_key=_optional_env("KMA_API_KEY"),
        upstage_api_key=_optional_env("UPSTAGE_API_KEY"),
        upstage_model=_optional_env("UPSTAGE_MODEL"),
        openrouter_api_key=_optional_env("OPENROUTER_API_KEY"),
        openrouter_model=_optional_env("OPENROUTER_MODEL"),
    )


def _optional_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None
