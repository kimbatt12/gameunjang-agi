from app.guard import is_domestic_tourism_question
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

    return ChatResponse(
        type="answer",
        isTourismRelated=True,
        answer=(
            "국내 관광 관련 질문으로 확인되었습니다. "
            "현재 단계에서는 외부 API나 LLM을 호출하지 않고, "
            "후속 마일스톤에서 한국관광공사 공공데이터 기반 추천을 연결할 예정입니다."
        ),
        items=[],
        sourceDomains=["data.go.kr", "visitkorea.or.kr"],
        warnings=["external_provider_not_configured"],
    )
