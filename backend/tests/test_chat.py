from fastapi.testclient import TestClient

from app.config import get_settings
from app.external.llm import LLMProviderError, LLMResponse
from app.external.weather import WeatherResult
from app.main import create_app
from app.routing import CandidateSelection, RoutedApiCandidate
from app.routing.metadata import load_tour_api_metadata_index


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
    llm_provider = _SequenceLLMProvider(["domestic_tourism"])
    client = TestClient(create_app(llm_provider=llm_provider))

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
    assert llm_provider.requests == []


def test_chat_rejects_foreign_travel_question_without_llm_recheck() -> None:
    llm_provider = _SequenceLLMProvider(["domestic_tourism"])
    client = TestClient(create_app(llm_provider=llm_provider))

    response = client.post(
        "/api/chat",
        json={"message": "오사카 2박 3일 여행 코스 추천해줘"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "rejection"
    assert payload["isTourismRelated"] is False
    assert payload["items"] == []
    assert payload["sourceDomains"] == []
    assert payload["warnings"] == ["out_of_scope_no_external_call"]
    assert llm_provider.requests == []


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


def test_chat_answerable_tourism_question_uses_tourism_api_and_llm() -> None:
    tourism_client = _RecordingTourismClient(
        {
            "response": {
                "body": {
                    "items": {
                        "item": [
                            {
                                "contentid": "gn-course-1",
                                "title": "강릉 바다 커피거리 코스",
                                "addr1": "강원특별자치도 강릉시 창해로",
                                "homepage": (
                                    '<a href="https://www.visitkorea.or.kr">공식</a>'
                                ),
                            },
                            {
                                "contentid": "gn-course-2",
                                "title": "오죽헌 역사 산책 코스",
                                "addr1": "강원특별자치도 강릉시 율곡로3139번길 24",
                            },
                        ]
                    }
                }
            }
        }
    )
    llm_provider = _RecordingLLMProvider()
    client = TestClient(
        create_app(tourism_client=tourism_client, llm_provider=llm_provider)
    )

    response = client.post("/api/chat", json={"message": "강릉 2박 3일 코스"})

    assert response.status_code == 200
    payload = response.json()
    assert tourism_client.calls
    endpoint, params = tourism_client.calls[0]
    assert endpoint == "areaBasedList2"
    assert params["areaCode"] == "32"
    assert params["sigunguCode"] == "1"
    assert params["contentTypeId"] == "25"
    assert payload["items"][0]["title"] == "강릉 바다 커피거리 코스"
    assert payload["items"][0]["officialUrl"] == "https://www.visitkorea.or.kr"
    assert "confirmed_api_item_data_unavailable" not in payload["warnings"]
    assert "api_data_first_answer" in payload["warnings"]
    assert "llm_composed_answer" in payload["warnings"]
    assert payload["answer"] == "LLM composed answer using 강릉 바다 커피거리 코스"
    assert llm_provider.requests
    prompt = llm_provider.requests[0].messages[-1].content
    assert "강릉 바다 커피거리 코스" in prompt
    assert "오죽헌 역사 산책 코스" in prompt


def test_guard_accepted_tourism_question_skips_llm_scope_recheck() -> None:
    tourism_client = _RecordingTourismClient({"response": {"body": {"items": {}}}})
    llm_provider = _SequenceLLMProvider(["true"])
    client = TestClient(
        create_app(tourism_client=tourism_client, llm_provider=llm_provider)
    )

    response = client.post("/api/chat", json={"message": "강릉 2박 3일 코스"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "answer"
    assert payload["isTourismRelated"] is True
    assert tourism_client.calls
    assert llm_provider.requests == []
    assert "llm_scope_recheck_accepted" not in payload["warnings"]


def test_guard_rejected_llm_scope_recheck_can_continue_to_answer_flow() -> None:
    tourism_client = _RecordingTourismClient(
        {
            "response": {
                "body": {
                    "items": {
                        "item": [
                            {
                                "contentid": "jj-keyword-1",
                                "title": "전주 한옥마을 산책",
                                "addr1": "전북특별자치도 전주시 완산구",
                            }
                        ]
                    }
                }
            }
        }
    )
    llm_provider = _SequenceLLMProvider(
        ["domestic_tourism", "LLM composed answer using 전주 한옥마을 산책"]
    )
    client = TestClient(
        create_app(tourism_client=tourism_client, llm_provider=llm_provider)
    )

    response = client.post("/api/chat", json={"message": "한옥마을 주변"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "answer"
    assert payload["isTourismRelated"] is True
    assert tourism_client.calls
    assert len(llm_provider.requests) == 2
    assert payload["answer"] == "LLM composed answer using 전주 한옥마을 산책"
    assert "llm_scope_recheck_accepted" in payload["warnings"]
    assert "out_of_scope_no_external_call" not in payload["warnings"]


def test_ambiguous_guard_rejected_llm_scope_recheck_keeps_out_of_scope_rejection() -> (
    None
):
    tourism_client = _RecordingTourismClient({"response": {"body": {"items": {}}}})
    llm_provider = _SequenceLLMProvider(["not_domestic_tourism"])
    client = TestClient(
        create_app(tourism_client=tourism_client, llm_provider=llm_provider)
    )

    response = client.post("/api/chat", json={"message": "한옥마을 주변"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "rejection"
    assert payload["isTourismRelated"] is False
    assert payload["warnings"] == ["out_of_scope_after_llm_scope_recheck"]
    assert tourism_client.calls == []
    assert len(llm_provider.requests) == 1


def test_ambiguous_guard_rejection_without_llm_provider_keeps_no_external_call_warning(
    monkeypatch,
) -> None:
    monkeypatch.delenv("UPSTAGE_API_KEY", raising=False)
    monkeypatch.delenv("UPSTAGE_MODEL", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    get_settings.cache_clear()
    try:
        tourism_client = _RecordingTourismClient({"response": {"body": {"items": {}}}})
        client = TestClient(create_app(tourism_client=tourism_client))

        response = client.post("/api/chat", json={"message": "한옥마을 주변"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["type"] == "rejection"
        assert payload["isTourismRelated"] is False
        assert payload["warnings"] == ["out_of_scope_no_external_call"]
        assert tourism_client.calls == []
    finally:
        get_settings.cache_clear()


def test_guard_rejected_llm_scope_recheck_failure_fails_closed() -> None:
    tourism_client = _RecordingTourismClient({"response": {"body": {"items": {}}}})
    llm_provider = _SequenceLLMProvider([LLMProviderError("classifier failed")])
    client = TestClient(
        create_app(tourism_client=tourism_client, llm_provider=llm_provider)
    )

    response = client.post("/api/chat", json={"message": "한옥마을 주변"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "rejection"
    assert payload["isTourismRelated"] is False
    assert payload["warnings"] == [
        "out_of_scope_after_llm_scope_recheck",
        "llm_scope_recheck_unavailable",
    ]
    assert tourism_client.calls == []
    assert len(llm_provider.requests) == 1


def test_guard_rejected_llm_scope_recheck_malformed_output_fails_closed() -> None:
    tourism_client = _RecordingTourismClient({"response": {"body": {"items": {}}}})
    llm_provider = _SequenceLLMProvider(["maybe"])
    client = TestClient(
        create_app(tourism_client=tourism_client, llm_provider=llm_provider)
    )

    response = client.post("/api/chat", json={"message": "한옥마을 주변"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "rejection"
    assert payload["isTourismRelated"] is False
    assert payload["warnings"] == [
        "out_of_scope_after_llm_scope_recheck",
        "llm_scope_recheck_unavailable",
    ]
    assert tourism_client.calls == []
    assert len(llm_provider.requests) == 1


def test_chat_weather_question_calls_weather_api_when_injected() -> None:
    tourism_client = _RecordingTourismClient(
        {
            "response": {
                "body": {
                    "items": {
                        "item": [
                            {
                                "contentid": "busan-indoor-1",
                                "title": "부산 실내 전시관",
                                "addr1": "부산광역시 해운대구",
                            }
                        ]
                    }
                }
            }
        }
    )
    weather_client = _RecordingWeatherClient(
        WeatherResult(
            available=False,
            forecasts=(),
            source_domain=None,
            warnings=("weather_api_unavailable",),
        )
    )
    client = TestClient(
        create_app(tourism_client=tourism_client, weather_client=weather_client)
    )

    response = client.post("/api/chat", json={"message": "부산 비 오는 날 실내 관광지"})

    assert response.status_code == 200
    payload = response.json()
    assert weather_client.calls
    params = weather_client.calls[0]
    assert params["nx"] == 98
    assert params["ny"] == 76
    assert "weather_api_unavailable" in payload["warnings"]
    assert "weather_api_not_called_using_question_condition" not in payload["warnings"]


def test_chat_weather_question_uses_tour_api_service_key_for_default_weather_client(
    monkeypatch,
) -> None:
    tourism_client = _RecordingTourismClient(
        {
            "response": {
                "body": {
                    "items": {
                        "item": [
                            {
                                "contentid": "busan-indoor-1",
                                "title": "부산 실내 전시관",
                                "addr1": "부산광역시 해운대구",
                            }
                        ]
                    }
                }
            }
        }
    )
    created_clients: list[_RecordingDefaultWeatherClient] = []

    def recording_weather_client(
        *,
        service_key: str,
    ) -> _RecordingDefaultWeatherClient:
        client = _RecordingDefaultWeatherClient(service_key)
        created_clients.append(client)
        return client

    monkeypatch.setenv("TOUR_API_SERVICE_KEY", "placeholder-tour-key")
    monkeypatch.delenv("KMA_API_KEY", raising=False)
    monkeypatch.setattr("app.chat_service.KoreaWeatherClient", recording_weather_client)
    get_settings.cache_clear()
    try:
        client = TestClient(create_app(tourism_client=tourism_client))

        response = client.post(
            "/api/chat", json={"message": "부산 비 오는 날 실내 관광지"}
        )

        assert response.status_code == 200
        payload = response.json()
        assert [client.service_key for client in created_clients] == [
            "placeholder-tour-key"
        ]
        assert created_clients[0].calls
        assert "weather_api_unavailable" in payload["warnings"]
        assert (
            "weather_api_not_called_using_question_condition" not in payload["warnings"]
        )
    finally:
        get_settings.cache_clear()


def test_fetch_tourism_items_skips_candidate_with_unresolved_required_param() -> None:
    from app.chat_service import _fetch_tourism_items

    apis = {api.id: api for api in load_tour_api_metadata_index().apis}
    selection = CandidateSelection(
        candidates=(
            RoutedApiCandidate(
                api=apis["detail_common"],
                score=20,
                matched_regions=(),
                matched_categories=("detail",),
                matched_terms=("공식", "운영시간"),
            ),
            RoutedApiCandidate(
                api=apis["area_based_list"],
                score=10,
                matched_regions=("경주",),
                matched_categories=("attraction",),
                matched_terms=("관광지",),
            ),
        ),
        matched_regions=("경주",),
        matched_categories=("detail", "attraction"),
        is_low_relevance=False,
        reason="api_candidates_selected",
    )
    tourism_client = _RecordingTourismClient(
        {
            "response": {
                "body": {"items": {"item": [{"contentid": "1", "title": "불국사"}]}}
            }
        }
    )

    items, warnings = _fetch_tourism_items(
        selection=selection,
        tourism_client=tourism_client,
    )

    assert warnings == []
    assert items[0].title == "불국사"
    assert tourism_client.calls == [
        (
            "areaBasedList2",
            {
                "numOfRows": 10,
                "pageNo": 1,
                "arrange": "A",
                "areaCode": "35",
                "sigunguCode": "2",
            },
        )
    ]
    assert "contentId" not in tourism_client.calls[0][1]


def test_fetch_tourism_items_skips_keyword_candidate_without_matched_region() -> None:
    from app.chat_service import _fetch_tourism_items

    apis = {api.id: api for api in load_tour_api_metadata_index().apis}
    selection = CandidateSelection(
        candidates=(
            RoutedApiCandidate(
                api=apis["search_keyword"],
                score=10,
                matched_regions=(),
                matched_categories=("keyword",),
                matched_terms=("검색",),
            ),
        ),
        matched_regions=(),
        matched_categories=("keyword",),
        is_low_relevance=False,
        reason="api_candidates_selected",
    )
    tourism_client = _RecordingTourismClient({"response": {"body": {"items": {}}}})

    items, warnings = _fetch_tourism_items(
        selection=selection,
        tourism_client=tourism_client,
    )

    assert items == ()
    assert warnings == []
    assert tourism_client.calls == []


class _RecordingTourismClient:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload
        self.calls: list[tuple[str, dict[str, str | int]]] = []

    def get(self, endpoint: str, params: dict[str, str | int]) -> dict[str, object]:
        self.calls.append((endpoint, params))
        return self._payload


class _RecordingLLMProvider:
    name = "recording-llm"

    def __init__(self) -> None:
        self.requests = []

    def complete(self, request):
        self.requests.append(request)
        return LLMResponse(
            text="LLM composed answer using 강릉 바다 커피거리 코스",
            provider=self.name,
            model="test-model",
        )


class _SequenceLLMProvider:
    name = "sequence-llm"

    def __init__(self, responses) -> None:
        self._responses = list(responses)
        self.requests = []

    def complete(self, request):
        self.requests.append(request)
        response = self._responses.pop(0)
        if isinstance(response, LLMProviderError):
            raise response
        return LLMResponse(text=response, provider=self.name, model="test-model")


class _RecordingWeatherClient:
    def __init__(self, result: WeatherResult) -> None:
        self._result = result
        self.calls: list[dict[str, str | int]] = []

    def get_vilage_forecast(self, params: dict[str, str | int]) -> WeatherResult:
        self.calls.append(params)
        return self._result


class _RecordingDefaultWeatherClient:
    def __init__(self, service_key: str) -> None:
        self.service_key = service_key
        self.calls: list[dict[str, str | int]] = []

    def get_vilage_forecast(self, params: dict[str, str | int]) -> WeatherResult:
        self.calls.append(params)
        return WeatherResult(
            available=False,
            forecasts=(),
            source_domain=None,
            warnings=("weather_api_unavailable",),
        )
