from dataclasses import dataclass

DOMESTIC_LOCATION_KEYWORDS = frozenset(
    {
        "한국",
        "국내",
        "서울",
        "부산",
        "대구",
        "인천",
        "광주",
        "대전",
        "울산",
        "세종",
        "경기",
        "강원",
        "충북",
        "충청북도",
        "충남",
        "충청남도",
        "전북",
        "전라북도",
        "전남",
        "전라남도",
        "경북",
        "경상북도",
        "경남",
        "경상남도",
        "제주",
        "강릉",
        "속초",
        "전주",
        "경주",
        "여수",
        "통영",
        "춘천",
        "목포",
        "안동",
        "수원",
        "가평",
    }
)

TOURISM_INTENT_KEYWORDS = frozenset(
    {
        "여행",
        "관광",
        "관광지",
        "명소",
        "가볼만",
        "갈 만한",
        "갈만한",
        "코스",
        "일정",
        "축제",
        "행사",
        "숙소",
        "숙박",
        "호텔",
        "펜션",
        "맛집",
        "음식점",
        "카페",
        "실내",
        "야외",
        "박물관",
        "미술관",
        "해수욕장",
        "공원",
        "둘레길",
        "운영시간",
        "입장료",
        "주소",
        "공식 링크",
        "추천",
    }
)

FOREIGN_LOCATION_KEYWORDS = frozenset(
    {
        "일본",
        "도쿄",
        "오사카",
        "중국",
        "상하이",
        "대만",
        "태국",
        "방콕",
        "베트남",
        "다낭",
        "미국",
        "뉴욕",
        "유럽",
        "프랑스",
        "파리",
        "스페인",
    }
)

NON_TOURISM_KEYWORDS = frozenset(
    {
        "코딩",
        "파이썬",
        "주식",
        "투자",
        "정치",
        "선거",
        "연예",
        "아이돌",
        "수학",
        "번역",
        "레시피",
        "법률",
        "의학",
    }
)


@dataclass(frozen=True)
class GuardResult:
    is_tourism_related: bool
    matched_keywords: tuple[str, ...]
    reason: str


def is_domestic_tourism_question(message: str) -> GuardResult:
    normalized = _normalize(message)
    matched_foreign = _matched_keywords(normalized, FOREIGN_LOCATION_KEYWORDS)
    matched_locations = _matched_keywords(normalized, DOMESTIC_LOCATION_KEYWORDS)
    matched_intents = _matched_keywords(normalized, TOURISM_INTENT_KEYWORDS)
    matched_non_tourism = _matched_keywords(normalized, NON_TOURISM_KEYWORDS)

    if matched_foreign and (matched_intents or not matched_locations):
        return GuardResult(
            is_tourism_related=False,
            matched_keywords=matched_foreign,
            reason="foreign_travel_out_of_scope",
        )

    if matched_non_tourism and not matched_intents:
        return GuardResult(
            is_tourism_related=False,
            matched_keywords=matched_non_tourism,
            reason="non_tourism_topic",
        )

    if matched_locations and matched_intents:
        return GuardResult(
            is_tourism_related=True,
            matched_keywords=tuple(sorted({*matched_locations, *matched_intents})),
            reason="domestic_location_and_tourism_intent",
        )

    if "국내" in normalized and matched_intents:
        return GuardResult(
            is_tourism_related=True,
            matched_keywords=tuple(sorted({"국내", *matched_intents})),
            reason="domestic_scope_and_tourism_intent",
        )

    return GuardResult(
        is_tourism_related=False,
        matched_keywords=tuple(sorted({*matched_locations, *matched_intents})),
        reason="insufficient_domestic_tourism_signal",
    )


def _normalize(message: str) -> str:
    return " ".join(message.strip().lower().split())


def _matched_keywords(message: str, keywords: frozenset[str]) -> tuple[str, ...]:
    return tuple(sorted(keyword for keyword in keywords if keyword.lower() in message))
