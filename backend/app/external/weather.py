from dataclasses import dataclass
from typing import Any

import httpx

KMA_API_BASE_URL = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0"


@dataclass(frozen=True)
class NormalizedWeatherForecast:
    category: str
    value: str
    forecast_date: str
    forecast_time: str


@dataclass(frozen=True)
class WeatherResult:
    available: bool
    forecasts: tuple[NormalizedWeatherForecast, ...]
    source_domain: str | None
    warnings: tuple[str, ...]


class KoreaWeatherClient:
    def __init__(
        self,
        *,
        service_key: str,
        timeout_seconds: float = 5.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._service_key = service_key
        self._timeout_seconds = timeout_seconds
        self._client = client

    def get_vilage_forecast(self, params: dict[str, str | int]) -> WeatherResult:
        request_params: dict[str, str | int] = {
            "serviceKey": self._service_key,
            "dataType": "JSON",
            **params,
        }
        try:
            response = self._request("/getVilageFcst", request_params)
            response.raise_for_status()
            forecasts = normalize_weather_response(response.json())
        except (
            httpx.HTTPError,
            ValueError,
            TypeError,
        ):
            return WeatherResult(
                available=False,
                forecasts=(),
                source_domain=None,
                warnings=("weather_api_unavailable",),
            )

        return WeatherResult(
            available=True,
            forecasts=forecasts,
            source_domain="data.go.kr",
            warnings=(),
        )

    def _request(
        self,
        endpoint: str,
        params: dict[str, str | int],
    ) -> httpx.Response:
        if self._client is not None:
            return self._client.get(endpoint, params=params)

        with httpx.Client(
            base_url=KMA_API_BASE_URL,
            timeout=self._timeout_seconds,
        ) as client:
            return client.get(endpoint, params=params)


def normalize_weather_response(
    payload: dict[str, Any],
) -> tuple[NormalizedWeatherForecast, ...]:
    raw_items = (
        payload.get("response", {}).get("body", {}).get("items", {}).get("item", [])
    )
    if isinstance(raw_items, dict):
        raw_items = [raw_items]
    if not isinstance(raw_items, list):
        return ()

    forecasts: list[NormalizedWeatherForecast] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        category = item.get("category")
        value = item.get("fcstValue")
        forecast_date = item.get("fcstDate")
        forecast_time = item.get("fcstTime")
        required_parts = (category, value, forecast_date, forecast_time)
        if all(isinstance(part, str) and part for part in required_parts):
            forecasts.append(
                NormalizedWeatherForecast(
                    category=category,
                    value=value,
                    forecast_date=forecast_date,
                    forecast_time=forecast_time,
                )
            )

    return tuple(forecasts)
