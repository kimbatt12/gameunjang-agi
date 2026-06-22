from dataclasses import dataclass
from typing import Any

import httpx

TOUR_API_BASE_URL = "https://apis.data.go.kr/B551011/KorService2"


class TourismApiError(RuntimeError):
    """Raised when the Korea Tourism Organization API call fails."""


@dataclass(frozen=True)
class NormalizedTourismItem:
    title: str
    address: str | None
    official_url: str | None
    source_domain: str
    raw_id: str | None = None


class KoreaTourismClient:
    def __init__(
        self,
        *,
        service_key: str,
        timeout_seconds: float = 10.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._service_key = service_key
        self._timeout_seconds = timeout_seconds
        self._client = client

    def get(self, endpoint: str, params: dict[str, str | int]) -> dict[str, Any]:
        request_params: dict[str, str | int] = {
            "serviceKey": self._service_key,
            "MobileOS": "ETC",
            "MobileApp": "gameunjang-agi",
            "_type": "json",
            **params,
        }

        try:
            response = self._request(endpoint, request_params)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise TourismApiError("tourism api request failed") from exc

    def _request(
        self,
        endpoint: str,
        params: dict[str, str | int],
    ) -> httpx.Response:
        path = endpoint if endpoint.startswith("/") else f"/{endpoint}"
        if self._client is not None:
            return self._client.get(path, params=params)

        with httpx.Client(
            base_url=TOUR_API_BASE_URL,
            timeout=self._timeout_seconds,
        ) as client:
            return client.get(path, params=params)


def normalize_tourism_response(
    payload: dict[str, Any],
) -> tuple[NormalizedTourismItem, ...]:
    items = _extract_items(payload)
    return tuple(
        item for raw_item in items if (item := _normalize_item(raw_item)) is not None
    )


def _extract_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    body = payload.get("response", {}).get("body", {})
    raw_items = body.get("items", {}).get("item", [])
    if isinstance(raw_items, dict):
        return [raw_items]
    if isinstance(raw_items, list):
        return [item for item in raw_items if isinstance(item, dict)]
    return []


def _normalize_item(raw_item: dict[str, Any]) -> NormalizedTourismItem | None:
    title = _clean_string(raw_item.get("title"))
    if title is None:
        return None

    official_url = _clean_string(
        raw_item.get("homepage")
        or raw_item.get("eventhomepage")
        or raw_item.get("eventHompage")
    )
    official_url = _extract_url(official_url) if official_url else None

    return NormalizedTourismItem(
        title=title,
        address=_join_address(raw_item),
        official_url=official_url,
        source_domain="visitkorea.or.kr",
        raw_id=_clean_string(raw_item.get("contentid")),
    )


def _join_address(raw_item: dict[str, Any]) -> str | None:
    parts = [
        part
        for value in (raw_item.get("addr1"), raw_item.get("addr2"))
        if (part := _clean_string(value))
    ]
    if not parts:
        return None
    return " ".join(parts)


def _clean_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = " ".join(value.strip().split())
    return cleaned or None


def _extract_url(value: str) -> str | None:
    for token in value.replace('"', " ").replace("'", " ").split():
        if token.startswith(("https://", "http://")):
            return token.rstrip("<>)")
    return value if value.startswith(("https://", "http://")) else None
