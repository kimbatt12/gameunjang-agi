import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.answer_generation import compose_answer
from app.cost_control import CostControlSnapshot, evaluate_cost_controls
from app.external.llm import LLMResponse
from app.external.tourism import NormalizedTourismItem
from app.main import create_app
from app.routing import select_api_candidates
from app.routing.metadata import read_tour_api_metadata_text
from tools.data_refresh import (
    DEFAULT_BACKEND_CURRENT,
    smoke_snapshot,
    validate_snapshot,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_mvp_chat_smoke_answers_mobile_domestic_tourism_question() -> None:
    llm_provider = _ClassificationLLMProvider()
    client = TestClient(create_app(llm_provider=llm_provider))

    response = client.post(
        "/api/chat",
        json={
            "message": "이번 주말에 아이랑 부산에서 갈 만한 실내 관광지 추천해줘",
            "localConversationId": "mobile-smoke-conversation",
            "clientSessionQuestionCount": 1,
            "clientContext": {"timezone": "Asia/Seoul"},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "answer"
    assert payload["isTourismRelated"] is True
    assert payload["answer"]
    assert payload["sourceDomains"]
    assert set(payload) == {
        "type",
        "isTourismRelated",
        "answer",
        "items",
        "sourceDomains",
        "warnings",
    }
    assert len(llm_provider.requests) == 1


def test_mvp_api_candidate_selection_matches_question_intent() -> None:
    festival = select_api_candidates("서울 이번 달 축제 알려줘")
    itinerary = select_api_candidates("강릉 1박 2일 코스 일정 추천")

    assert festival.is_low_relevance is False
    assert festival.candidates[0].api.id == "search_festival"
    assert itinerary.is_low_relevance is False
    assert itinerary.candidates[0].api.id == "tour_course"


def test_mvp_non_tourism_question_returns_scope_guidance_without_sources() -> None:
    client = TestClient(create_app())

    response = client.post("/api/chat", json={"message": "파이썬 코드 리뷰해줘"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "rejection"
    assert payload["isTourismRelated"] is False
    assert "국내 관광 관련 질문" in payload["answer"]
    assert payload["sourceDomains"] == []
    assert payload["warnings"] == []


def test_mvp_itinerary_and_weather_answers_are_limited_to_confirmed_data() -> None:
    selection = select_api_candidates("제주 비 오는 날 1박 2일 코스 일정 추천")

    response = compose_answer(
        message="제주 비 오는 날 1박 2일 코스 일정 추천",
        selection=selection,
        api_items=(
            NormalizedTourismItem(
                title="제주 실내 전시관",
                address="제주",
                official_url=None,
                source_domain="visitkorea.or.kr",
                raw_id="indoor-1",
            ),
            NormalizedTourismItem(
                title="제주 해변 산책로",
                address="제주",
                official_url=None,
                source_domain="visitkorea.or.kr",
                raw_id="outdoor-1",
            ),
        ),
    )

    assert "1일차" in response.answer
    assert "확인된 정보 기준 제공" in response.answer
    assert "질문의 날씨 조건" in response.answer
    assert response.items[0].title == "제주 실내 전시관"
    assert "weather_condition_affects_order" in response.warnings
    assert "weather_api_not_called_using_question_condition" in response.warnings


def test_mvp_source_domains_are_displayed_for_answerable_tourism_scope() -> None:
    response = compose_answer(
        message="부산 실내 관광지 추천",
        selection=select_api_candidates("부산 실내 관광지 추천"),
        api_items=(
            NormalizedTourismItem(
                title="부산시립미술관",
                address="부산 해운대구 APEC로 58",
                official_url="https://art.busan.go.kr",
                source_domain="visitkorea.or.kr",
                raw_id="indoor-1",
            ),
        ),
    )

    assert response.sourceDomains == ["art.busan.go.kr", "visitkorea.or.kr"]
    assert "출처: art.busan.go.kr, visitkorea.or.kr" in response.answer


def test_mvp_data_refresh_has_weekly_manual_triggers_and_success_only_gate() -> None:
    workflow = (REPO_ROOT / ".github/workflows/data-refresh.yml").read_text(
        encoding="utf-8"
    )

    assert "schedule:" in workflow
    assert "workflow_dispatch:" in workflow
    promote_command = "run: python -m tools.data_refresh promote"
    assert workflow.index("run: python -m tools.data_refresh validate-staging") < (
        workflow.index(promote_command)
    )
    assert workflow.index("run: python -m tools.data_refresh smoke-staging") < (
        workflow.index(promote_command)
    )
    assert validate_snapshot(DEFAULT_BACKEND_CURRENT)["rowCount"] >= 8
    assert len(smoke_snapshot(DEFAULT_BACKEND_CURRENT)["cases"]) == 3


def test_mvp_cost_controls_keep_daily_projection_under_monthly_one_dollar() -> None:
    result = evaluate_cost_controls(
        CostControlSnapshot(
            total_queries=1000,
            cache_hits=960,
            llm_call_count=40,
            estimated_cost_per_llm_call_usd=0.0005,
        )
    )

    assert result.ok is True
    assert result.estimated_daily_cost_usd < result.max_daily_budget_usd
    assert result.max_daily_budget_usd == 1 / 30


def test_mvp_metadata_contains_only_placeholder_free_public_domains() -> None:
    metadata_text = read_tour_api_metadata_text()
    metadata = json.loads(metadata_text)

    source_domains = {api["sourceDomain"] for api in metadata["apis"]}

    assert source_domains <= {"data.go.kr", "visitkorea.or.kr"}
    assert "SECRET" not in metadata_text.upper()
    assert "PASSWORD" not in metadata_text.upper()


class _ClassificationLLMProvider:
    name = "classification-llm"

    def __init__(self) -> None:
        self.requests = []

    def complete(self, request):
        self.requests.append(request)
        return LLMResponse(
            text="domestic_tourism",
            provider=self.name,
            model="test-model",
        )
