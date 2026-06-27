import pytest

from app.answer_generation import _is_mountain_title, compose_answer
from app.external.tourism import NormalizedTourismItem
from app.external.weather import (
    NormalizedWeatherForecast,
    WeatherResult,
)
from app.routing import select_api_candidates


def _busan_api_items() -> tuple[NormalizedTourismItem, ...]:
    return (
        NormalizedTourismItem(
            title="해운대해수욕장",
            address="부산 해운대구 우동",
            official_url=None,
            source_domain="visitkorea.or.kr",
            raw_id="outdoor-1",
        ),
        NormalizedTourismItem(
            title="부산시립미술관",
            address="부산 해운대구 APEC로 58",
            official_url="https://art.busan.go.kr",
            source_domain="visitkorea.or.kr",
            raw_id="indoor-1",
        ),
    )


def test_answer_snapshot_marks_sources_and_unconfirmed_values() -> None:
    selection = select_api_candidates("부산 실내 관광지 추천")
    api_items = (
        NormalizedTourismItem(
            title="부산시립미술관",
            address="부산 해운대구 APEC로 58",
            official_url="https://art.busan.go.kr",
            source_domain="visitkorea.or.kr",
            raw_id="12345",
        ),
    )

    response = compose_answer(
        message="부산 실내 관광지 추천",
        selection=selection,
        api_items=api_items,
    )

    assert response.model_dump() == {
        "type": "answer",
        "isTourismRelated": True,
        "answer": (
            "부산 추천 항목: 부산시립미술관. "
            "정규화된 API 항목 데이터와 항목별 공식 링크가 있는 경우에만 "
            "공식 링크를 표시했습니다. "
            "미확인 값은 '확인된 정보 없음'로 표시합니다.\n"
            "출처: art.busan.go.kr, visitkorea.or.kr"
        ),
        "items": [
            {
                "title": "부산시립미술관",
                "reason": "API 제공 공식 링크 확인",
                "address": "부산 해운대구 APEC로 58",
                "openingHours": "확인된 정보 없음",
                "price": "확인된 정보 없음",
                "officialUrl": "https://art.busan.go.kr",
                "mapUrl": None,
            }
        ],
        "sourceDomains": ["art.busan.go.kr", "visitkorea.or.kr"],
        "warnings": ["api_data_first_answer", "unconfirmed_values_marked"],
    }


def test_itinerary_snapshot_uses_day_part_format_and_sources() -> None:
    selection = select_api_candidates("강릉 1박 2일 코스 일정 추천")
    api_items = (
        NormalizedTourismItem(
            title="강릉시립미술관",
            address="강릉",
            official_url=None,
            source_domain="visitkorea.or.kr",
            raw_id="indoor-1",
        ),
    )

    response = compose_answer(
        message="강릉 1박 2일 코스 일정 추천",
        selection=selection,
        api_items=api_items,
    )

    assert "1일차\n- 오전:" in response.answer
    assert "\n- 점심:" in response.answer
    assert "\n- 숙박:" in response.answer
    assert "\n\n2일차\n- 오전:" in response.answer
    assert "확인된 정보 기준 제공" in response.answer
    assert response.sourceDomains == ["visitkorea.or.kr"]
    assert "itinerary_format_applied" in response.warnings
    assert response.items[0].title == "강릉시립미술관"


def test_weather_api_result_influences_order_warnings_and_source_domain() -> None:
    selection = select_api_candidates("부산 주말 관광지 추천")
    weather = WeatherResult(
        available=True,
        forecasts=(
            NormalizedWeatherForecast(
                category="PTY",
                value="1",
                forecast_date="20260622",
                forecast_time="1500",
            ),
        ),
        source_domain="data.go.kr",
        warnings=(),
    )

    response = compose_answer(
        message="부산 주말 관광지 추천",
        selection=selection,
        api_items=_busan_api_items(),
        weather=weather,
    )

    assert response.items[0].title == "부산시립미술관"
    assert (
        response.items[0].reason
        == "악천후 조건에서 실내 우선 추천 · API 제공 공식 링크 확인"
    )
    assert response.sourceDomains == [
        "art.busan.go.kr",
        "data.go.kr",
        "visitkorea.or.kr",
    ]
    assert "weather_condition_affects_order" in response.warnings
    assert "기상청 단기예보 기준 악천후 가능성 반영" in response.answer


def test_mild_wind_weather_does_not_warn_or_reorder_items() -> None:
    selection = select_api_candidates("부산 주말 관광지 추천")
    weather = WeatherResult(
        available=True,
        forecasts=(
            NormalizedWeatherForecast(
                category="WSD",
                value="4.2",
                forecast_date="20260622",
                forecast_time="1500",
            ),
        ),
        source_domain="data.go.kr",
        warnings=(),
    )

    response = compose_answer(
        message="부산 주말 관광지 추천",
        selection=selection,
        api_items=_busan_api_items(),
        weather=weather,
    )

    assert [item.title for item in response.items] == [
        "해운대해수욕장",
        "부산시립미술관",
    ]
    assert "weather_condition_affects_order" not in response.warnings
    assert "기상청 단기예보 기준 강수/강풍 지표 없음" in response.answer


def test_non_weather_words_containing_bi_do_not_trigger_weather_ordering() -> None:
    selection = select_api_candidates("부산 가성비 관광지 추천")

    for message in (
        "부산 가성비 관광지 추천",
        "부산 여행 비용 관광지 추천",
        "부산 여행 준비 관광지 추천",
        "부산 숙박비와 교통비와 관광지 추천",
    ):
        response = compose_answer(
            message=message,
            selection=selection,
            api_items=_busan_api_items(),
        )

        assert [item.title for item in response.items] == [
            "해운대해수욕장",
            "부산시립미술관",
        ]
        assert "weather_condition_affects_order" not in response.warnings
        assert "날씨 고려:" not in response.answer


def test_korean_adverse_weather_phrases_trigger_weather_ordering() -> None:
    selection = select_api_candidates("제주 비 오는 날 갈만한 관광지 추천")

    for message in (
        "제주 비가 오는 날 갈만한 관광지 추천",
        "제주 비 오는 날 갈만한 관광지 추천",
        "제주 눈이 오는 날 갈만한 관광지 추천",
        "제주 눈 오는 날 갈만한 관광지 추천",
        "제주 우천 갈만한 관광지 추천",
        "제주 호우 갈만한 관광지 추천",
        "제주 장마 갈만한 관광지 추천",
        "제주 폭우 갈만한 관광지 추천",
        "제주 폭설 갈만한 관광지 추천",
        "제주 대설 갈만한 관광지 추천",
        "제주 폭염 갈만한 관광지 추천",
        "제주 한파 갈만한 관광지 추천",
        "제주 강풍 갈만한 관광지 추천",
    ):
        response = compose_answer(
            message=message,
            selection=selection,
            api_items=(
                NormalizedTourismItem(
                    title="제주 해변 산책로",
                    address="제주",
                    official_url=None,
                    source_domain="visitkorea.or.kr",
                    raw_id="outdoor-1",
                ),
                NormalizedTourismItem(
                    title="제주 실내 전시관",
                    address="제주",
                    official_url=None,
                    source_domain="visitkorea.or.kr",
                    raw_id="indoor-1",
                ),
            ),
        )

        assert response.items[0].title == "제주 실내 전시관"
        assert "weather_condition_affects_order" in response.warnings
        assert "weather_api_not_called_using_question_condition" in response.warnings


def test_empty_weather_forecasts_are_unknown_not_clear_weather() -> None:
    selection = select_api_candidates("부산 주말 관광지 추천")
    weather = WeatherResult(
        available=True,
        forecasts=(),
        source_domain="data.go.kr",
        warnings=(),
    )

    response = compose_answer(
        message="부산 주말 관광지 추천",
        selection=selection,
        api_items=_busan_api_items(),
        weather=weather,
    )

    assert [item.title for item in response.items] == [
        "해운대해수욕장",
        "부산시립미술관",
    ]
    assert "기상청 단기예보 기준 강수/강풍 지표 없음" not in response.answer
    assert (
        "기상청 단기예보 항목이 없어 날씨 근거를 확인하지 못했습니다" in response.answer
    )
    assert "weather_condition_affects_order" not in response.warnings
    assert "weather_forecast_data_unavailable" in response.warnings
    assert "data.go.kr" in response.sourceDomains


def test_strong_wind_weather_warns_and_reorders_items() -> None:
    selection = select_api_candidates("부산 주말 관광지 추천")
    weather = WeatherResult(
        available=True,
        forecasts=(
            NormalizedWeatherForecast(
                category="WSD",
                value="14.0",
                forecast_date="20260622",
                forecast_time="1500",
            ),
        ),
        source_domain="data.go.kr",
        warnings=(),
    )

    response = compose_answer(
        message="부산 주말 관광지 추천",
        selection=selection,
        api_items=_busan_api_items(),
        weather=weather,
    )

    assert [item.title for item in response.items] == [
        "부산시립미술관",
        "해운대해수욕장",
    ]
    assert "weather_condition_affects_order" in response.warnings
    assert "기상청 단기예보 기준 악천후 가능성 반영" in response.answer


def test_busan_restaurant_item_is_not_demoted_as_outdoor_in_bad_weather() -> None:
    selection = select_api_candidates("부산 비 오는 날 맛집 추천")

    response = compose_answer(
        message="부산 비 오는 날 맛집 추천",
        selection=selection,
        api_items=(
            NormalizedTourismItem(
                title="해운대해수욕장",
                address="부산 해운대구 우동",
                official_url=None,
                source_domain="visitkorea.or.kr",
                raw_id="outdoor-1",
            ),
            NormalizedTourismItem(
                title="부산맛집",
                address="부산 중구 중앙대로",
                official_url=None,
                source_domain="visitkorea.or.kr",
                raw_id="restaurant-1",
            ),
        ),
    )

    assert [item.title for item in response.items] == ["부산맛집", "해운대해수욕장"]
    assert "weather_condition_affects_order" in response.warnings


def test_busan_hotel_item_is_not_demoted_as_outdoor_in_bad_weather() -> None:
    selection = select_api_candidates("부산 비 오는 날 호텔 추천")

    response = compose_answer(
        message="부산 비 오는 날 호텔 추천",
        selection=selection,
        api_items=(
            NormalizedTourismItem(
                title="해운대해수욕장",
                address="부산 해운대구 우동",
                official_url=None,
                source_domain="visitkorea.or.kr",
                raw_id="outdoor-1",
            ),
            NormalizedTourismItem(
                title="부산호텔",
                address="부산 중구 중앙대로",
                official_url=None,
                source_domain="visitkorea.or.kr",
                raw_id="stay-1",
            ),
        ),
    )

    assert [item.title for item in response.items] == ["부산호텔", "해운대해수욕장"]
    assert "weather_condition_affects_order" in response.warnings


@pytest.mark.parametrize(
    ("title", "is_mountain"),
    (
        ("한라산", True),
        ("한라산 백록담", True),
        ("설악산", True),
        ("설악산 케이블카", True),
        ("북한산", True),
        ("부산", False),
        ("부산 맛집", False),
        ("울산", False),
        ("울산 호텔", False),
    ),
)
def test_mountain_title_helper_excludes_region_name_false_positives(
    title: str, is_mountain: bool
) -> None:
    assert _is_mountain_title(title) is is_mountain


@pytest.mark.parametrize(
    ("message", "mountain_title", "preferred_title"),
    (
        ("제주 비 오는 날 실내 관광지 추천", "한라산", "제주 실내 전시관"),
        ("제주 비 오는 날 실내 관광지 추천", "한라산 백록담", "제주 실내 전시관"),
        ("속초 비 오는 날 맛집 추천", "설악산", "속초맛집"),
        ("속초 비 오는 날 맛집 추천", "설악산 케이블카", "속초맛집"),
        ("서울 비 오는 날 호텔 추천", "북한산", "서울호텔"),
    ),
)
def test_mountain_titles_are_demoted_behind_bad_weather_friendly_categories(
    message: str, mountain_title: str, preferred_title: str
) -> None:
    selection = select_api_candidates(message)

    response = compose_answer(
        message=message,
        selection=selection,
        api_items=(
            NormalizedTourismItem(
                title=mountain_title,
                address=None,
                official_url=None,
                source_domain="visitkorea.or.kr",
                raw_id="mountain-1",
            ),
            NormalizedTourismItem(
                title=preferred_title,
                address=None,
                official_url=None,
                source_domain="visitkorea.or.kr",
                raw_id="weather-friendly-1",
            ),
        ),
    )

    assert [item.title for item in response.items] == [preferred_title, mountain_title]
    assert "weather_condition_affects_order" in response.warnings


def test_ulsan_hotel_item_is_not_demoted_as_outdoor_in_bad_weather() -> None:
    selection = select_api_candidates("울산 비 오는 날 호텔 추천")

    response = compose_answer(
        message="울산 비 오는 날 호텔 추천",
        selection=selection,
        api_items=(
            NormalizedTourismItem(
                title="간절곶 해변 산책로",
                address="울산 울주군 서생면",
                official_url=None,
                source_domain="visitkorea.or.kr",
                raw_id="outdoor-1",
            ),
            NormalizedTourismItem(
                title="울산호텔",
                address="울산 남구 삼산동",
                official_url=None,
                source_domain="visitkorea.or.kr",
                raw_id="stay-1",
            ),
        ),
    )

    assert [item.title for item in response.items] == ["울산호텔", "간절곶 해변 산책로"]
    assert "weather_condition_affects_order" in response.warnings


def test_question_weather_condition_influences_order_without_weather_api() -> None:
    selection = select_api_candidates("제주 비 오는 날 갈만한 관광지 추천")

    response = compose_answer(
        message="제주 비 오는 날 갈만한 관광지 추천",
        selection=selection,
        api_items=(
            NormalizedTourismItem(
                title="제주 해변 산책로",
                address="제주",
                official_url=None,
                source_domain="visitkorea.or.kr",
                raw_id="outdoor-1",
            ),
            NormalizedTourismItem(
                title="제주 실내 전시관",
                address="제주",
                official_url=None,
                source_domain="visitkorea.or.kr",
                raw_id="indoor-1",
            ),
        ),
    )

    assert response.items[0].title == "제주 실내 전시관"
    assert "weather_condition_affects_order" in response.warnings
    assert "weather_api_not_called_using_question_condition" in response.warnings
    assert "질문의 날씨 조건" in response.answer


def test_question_condition_with_clear_kma_forecast_uses_distinct_summary() -> None:
    selection = select_api_candidates("제주 비 오는 날 갈만한 관광지 추천")
    weather = WeatherResult(
        available=True,
        forecasts=(
            NormalizedWeatherForecast(
                category="PTY",
                value="0",
                forecast_date="20260622",
                forecast_time="1500",
            ),
        ),
        source_domain="data.go.kr",
        warnings=(),
    )

    response = compose_answer(
        message="제주 비 오는 날 갈만한 관광지 추천",
        selection=selection,
        api_items=(
            NormalizedTourismItem(
                title="제주 해변 산책로",
                address="제주",
                official_url=None,
                source_domain="visitkorea.or.kr",
                raw_id="outdoor-1",
            ),
            NormalizedTourismItem(
                title="제주 실내 전시관",
                address="제주",
                official_url=None,
                source_domain="visitkorea.or.kr",
                raw_id="indoor-1",
            ),
        ),
        weather=weather,
    )

    assert response.items[0].title == "제주 실내 전시관"
    assert "weather_condition_affects_order" in response.warnings
    assert "질문의 날씨 조건을 반영" in response.answer
    assert "기상청 단기예보 기준 강수/강풍 지표 없음" in response.answer
    assert "기상청 단기예보 기준 악천후 가능성 반영" not in response.answer


def test_insufficient_information_case_keeps_no_sources_or_items() -> None:
    from app.chat_service import build_chat_response

    response = build_chat_response("국내 축제 알려줘")

    assert response.items == []
    assert response.sourceDomains == []
    assert response.warnings == []
    assert "국내 지역명" in response.answer


def test_empty_api_items_do_not_create_recommendations_or_official_claims() -> None:
    selection = select_api_candidates("부산 관광지 추천")

    response = compose_answer(message="부산 관광지 추천", selection=selection)

    assert response.items == []
    assert response.sourceDomains == ["visitkorea.or.kr"]
    assert (
        "확인된 API 항목 데이터가 없어 추천 항목을 제공하지 않습니다" in response.answer
    )
    assert "임의 추천" in response.answer
    assert "선택된 API 후보 도메인: visitkorea.or.kr" in response.answer
    assert "출처:" not in response.answer
    assert "api_data_first_answer" not in response.warnings
    assert "confirmed_api_item_data_unavailable" in response.warnings


def test_source_domains_with_items_exclude_routing_candidate_domains() -> None:
    selection = select_api_candidates("서울 축제 지역코드 추천")
    api_items = (
        NormalizedTourismItem(
            title="서울빛초롱축제",
            address="서울 종로구",
            official_url="https://stolantern.com",
            source_domain="visitkorea.or.kr",
            raw_id="festival-1",
        ),
    )

    response = compose_answer(
        message="서울 축제 지역코드 추천",
        selection=selection,
        api_items=api_items,
    )

    assert "data.go.kr" in {
        candidate.api.sourceDomain for candidate in selection.candidates
    }
    assert response.items
    assert response.sourceDomains == ["stolantern.com", "visitkorea.or.kr"]
    assert "data.go.kr" not in response.answer
