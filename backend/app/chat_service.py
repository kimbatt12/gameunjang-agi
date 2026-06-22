from app.answer_generation import compose_answer
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

    return compose_answer(message=message, selection=selection)


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
