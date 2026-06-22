from app.guard import is_domestic_tourism_question
from app.routing import CandidateSelection, select_api_candidates
from app.schemas import ChatResponse

SCOPE_GUIDANCE = (
    "이 서비스는 국내 관광 관련 질문에만 답변할 수 있습니다. "
    "여행지, 관광지, 축제, 숙소, 음식점, 여행코스와 관련된 질문을 입력해 주세요."
)


def build_chat_response(message: str) -> ChatResponse:
    guard_result = is_domestic_tourism_question(message)

    if not guard_result.is_tourism_related:
        return ChatResponse(
            type="rejection",
            isTourismRelated=False,
            answer=SCOPE_GUIDANCE,
            items=[],
            sourceDomains=[],
            warnings=["out_of_scope_no_external_call"],
        )

    selection = select_api_candidates(message)
    if selection.is_low_relevance:
        return _build_insufficient_information_response(selection)

    candidate_names = ", ".join(
        candidate.api.name for candidate in selection.candidates
    )

    return ChatResponse(
        type="answer",
        isTourismRelated=True,
        answer=(
            "국내 관광 질문으로 확인되어 한국관광공사 API 후보를 선택했습니다. "
            f"우선 후보: {candidate_names}. "
            "현재 단계에서는 외부 API나 LLM을 호출하지 않고 후보 라우팅만 수행합니다."
        ),
        items=[],
        sourceDomains=_source_domains(selection),
        warnings=["external_provider_not_configured", "tour_api_candidates_selected"],
    )


def _build_insufficient_information_response(
    selection: CandidateSelection,
) -> ChatResponse:
    detail = (
        "지역명과 관광 유형(예: 관광지, 축제, 숙소, 맛집, 코스)을 함께 알려 주세요."
    )
    if selection.matched_regions and not selection.matched_categories:
        detail = "관광 유형(예: 관광지, 축제, 숙소, 맛집, 코스)을 함께 알려 주세요."
    elif selection.matched_categories and not selection.matched_regions:
        detail = "국내 지역명(예: 서울, 부산, 강릉, 제주)을 함께 알려 주세요."

    answer = (
        "질문이 국내 관광 범위에는 해당하지만 API 후보를 고르기에는 "
        f"정보가 부족합니다. {detail}"
    )

    return ChatResponse(
        type="answer",
        isTourismRelated=True,
        answer=answer,
        items=[],
        sourceDomains=[],
        warnings=[selection.reason, "no_external_call_due_to_insufficient_information"],
    )


def _source_domains(selection: CandidateSelection) -> list[str]:
    return sorted({candidate.api.sourceDomain for candidate in selection.candidates})
