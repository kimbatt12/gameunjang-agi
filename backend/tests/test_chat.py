from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


def test_chat_accepts_domestic_tourism_question() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/chat",
        json={
            "message": "이번 주말에 아이랑 부산에서 갈 만한 실내 관광지 추천해줘",
            "localConversationId": "local-conversation-1",
            "clientSessionQuestionCount": 1,
            "clientContext": {"timezone": "Asia/Seoul"},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "answer"
    assert payload["isTourismRelated"] is True
    assert payload["answer"]
    assert payload["items"] == []
    assert payload["sourceDomains"] == ["visitkorea.or.kr"]
    assert (
        "확인된 API 항목 데이터가 없어 추천 항목을 제공하지 않습니다"
        in payload["answer"]
    )
    assert "api_data_first_answer" not in payload["warnings"]
    assert "confirmed_api_item_data_unavailable" in payload["warnings"]
    assert "weather_api_not_called_using_question_condition" in payload["warnings"]


def test_chat_rejects_non_tourism_question_without_sources() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/chat",
        json={
            "message": "파이썬 리스트 컴프리헨션을 설명해줘",
            "clientSessionQuestionCount": 1,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "rejection"
    assert payload["isTourismRelated"] is False
    assert "국내 관광 관련 질문" in payload["answer"]
    assert payload["items"] == []
    assert payload["sourceDomains"] == []
    assert payload["warnings"] == ["out_of_scope_no_external_call"]


def test_non_tourism_scope_guidance_skips_external_source_policy() -> None:
    client = TestClient(create_app())

    response = client.post("/api/chat", json={"message": "회사 보고서 요약해줘"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "rejection"
    assert "여행지, 관광지, 축제, 숙소, 음식점, 여행코스" in payload["answer"]
    assert payload["sourceDomains"] == []
    assert payload["warnings"] == ["out_of_scope_no_external_call"]


def test_chat_rejects_message_over_configured_length(monkeypatch) -> None:
    monkeypatch.setenv("MAX_USER_MESSAGE_CHARS", "5")
    get_settings.cache_clear()
    try:
        client = TestClient(create_app())

        response = client.post("/api/chat", json={"message": "부산 관광지 추천"})

        assert response.status_code == 422
        assert "at most 5 characters" in response.json()["detail"]
    finally:
        get_settings.cache_clear()


def test_chat_rejects_raw_message_over_configured_length_after_strip(
    monkeypatch,
) -> None:
    monkeypatch.setenv("MAX_USER_MESSAGE_CHARS", "5")
    get_settings.cache_clear()
    try:
        client = TestClient(create_app())
        message = "     부산"

        response = client.post("/api/chat", json={"message": message})

        assert len(message) > 5
        assert len(message.strip()) <= 5
        assert response.status_code == 422
        assert "at most 5 characters" in response.json()["detail"]
    finally:
        get_settings.cache_clear()


def test_chat_rejects_blank_message() -> None:
    client = TestClient(create_app())

    response = client.post("/api/chat", json={"message": "   "})

    assert response.status_code == 422


def test_chat_response_schema_includes_consistent_fields() -> None:
    client = TestClient(create_app())

    response = client.post("/api/chat", json={"message": "서울 축제 알려줘"})

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {
        "type",
        "isTourismRelated",
        "answer",
        "items",
        "sourceDomains",
        "warnings",
    }
    assert isinstance(payload["answer"], str)
    assert isinstance(payload["items"], list)
    assert isinstance(payload["sourceDomains"], list)
    assert isinstance(payload["warnings"], list)


def test_chat_asks_for_more_info_when_region_is_missing() -> None:
    client = TestClient(create_app())

    response = client.post("/api/chat", json={"message": "국내 축제 알려줘"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "answer"
    assert payload["isTourismRelated"] is True
    assert "국내 지역명" in payload["answer"]
    assert payload["items"] == []
    assert payload["sourceDomains"] == []
    assert payload["warnings"] == [
        "insufficient_region_or_category_signal",
        "no_external_call_due_to_insufficient_information",
    ]


def test_chat_tourism_source_policy_uses_allowed_api_candidate_domain() -> None:
    client = TestClient(create_app())

    response = client.post("/api/chat", json={"message": "서울 축제 알려줘"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["isTourismRelated"] is True
    assert set(payload["sourceDomains"]).issubset({"data.go.kr", "visitkorea.or.kr"})
    assert "선택된 API 후보 도메인:" in payload["answer"]
    assert "confirmed_api_item_data_unavailable" in payload["warnings"]
