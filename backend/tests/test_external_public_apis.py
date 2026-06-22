import json
from pathlib import Path

import httpx

from app.external.tourism import KoreaTourismClient, normalize_tourism_response
from app.external.weather import KoreaWeatherClient, normalize_weather_response

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_tourism_client_normalizes_fixture_schema() -> None:
    payload = _load_fixture("tourism_area_based_list.json")

    items = normalize_tourism_response(payload)

    assert len(items) == 2
    assert items[0].title == "부산시립미술관"
    assert items[0].address == "부산 해운대구 APEC로 58 (우동)"
    assert items[0].official_url == "https://art.busan.go.kr"
    assert items[0].source_domain == "visitkorea.or.kr"
    assert items[1].official_url is None


def test_tourism_client_calls_public_api_with_placeholder_key() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/B551011/KorService2/areaBasedList2"
        assert request.url.params["serviceKey"] == "placeholder-tour-key"
        assert request.url.params["_type"] == "json"
        return httpx.Response(200, json=_load_fixture("tourism_area_based_list.json"))

    client = KoreaTourismClient(
        service_key="placeholder-tour-key",
        client=httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url="https://apis.data.go.kr/B551011/KorService2",
        ),
    )

    payload = client.get("areaBasedList2", {"areaCode": "6"})

    assert normalize_tourism_response(payload)[0].title == "부산시립미술관"


def test_weather_client_normalizes_fixture_schema() -> None:
    payload = _load_fixture("weather_vilage_forecast.json")

    forecasts = normalize_weather_response(payload)

    assert len(forecasts) == 2
    assert forecasts[0].category == "TMP"
    assert forecasts[0].value == "22"
    assert forecasts[0].forecast_date == "20260622"
    assert forecasts[0].forecast_time == "1500"


def test_weather_client_degrades_gracefully_on_timeout() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out")

    client = KoreaWeatherClient(
        service_key="placeholder-kma-key",
        client=httpx.Client(
            transport=httpx.MockTransport(handler),
            base_url="https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0",
        ),
    )

    result = client.get_vilage_forecast(
        {"base_date": "20260622", "base_time": "0500", "nx": 98, "ny": 76}
    )

    assert result.available is False
    assert result.forecasts == ()
    assert result.source_domain is None
    assert result.warnings == ("weather_api_unavailable",)


def _load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))
