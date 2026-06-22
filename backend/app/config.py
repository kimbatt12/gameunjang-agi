import os
from functools import lru_cache

DEFAULT_MAX_USER_MESSAGE_CHARS = 1000


class Settings:
    def __init__(self, max_user_message_chars: int) -> None:
        self.max_user_message_chars = max_user_message_chars


@lru_cache
def get_settings() -> Settings:
    raw_limit = os.getenv("MAX_USER_MESSAGE_CHARS")
    if raw_limit is None:
        return Settings(max_user_message_chars=DEFAULT_MAX_USER_MESSAGE_CHARS)

    try:
        parsed_limit = int(raw_limit)
    except ValueError:
        parsed_limit = DEFAULT_MAX_USER_MESSAGE_CHARS

    return Settings(max_user_message_chars=max(1, parsed_limit))
