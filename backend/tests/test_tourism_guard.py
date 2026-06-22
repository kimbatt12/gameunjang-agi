from app.guard import is_domestic_tourism_question


def test_guard_accepts_domestic_location_with_tourism_intent() -> None:
    result = is_domestic_tourism_question("강릉 2박 3일 여행 코스 짜줘")

    assert result.is_tourism_related is True
    assert result.reason == "domestic_location_and_tourism_intent"


def test_guard_rejects_location_without_tourism_intent() -> None:
    result = is_domestic_tourism_question("서울 시장 선거 결과 알려줘")

    assert result.is_tourism_related is False


def test_guard_rejects_foreign_travel() -> None:
    result = is_domestic_tourism_question("오사카 맛집 추천해줘")

    assert result.is_tourism_related is False
    assert result.reason == "foreign_travel_out_of_scope"


def test_guard_rejects_foreign_travel_with_domestic_departure() -> None:
    result = is_domestic_tourism_question("서울 출발 오사카 맛집 추천해줘")

    assert result.is_tourism_related is False
    assert result.reason == "foreign_travel_out_of_scope"
