from dataclasses import dataclass

from app.routing.metadata import TourApiMetadata, load_tour_api_metadata_index

REGION_SYNONYMS: dict[str, tuple[str, ...]] = {
    "서울": ("서울", "서울시", "서울특별시"),
    "부산": ("부산", "부산시", "부산광역시"),
    "강릉": ("강릉", "강릉시"),
    "제주": ("제주", "제주도", "제주시", "서귀포"),
    "경주": ("경주", "경주시"),
    "전주": ("전주", "전주시", "한옥마을"),
    "여수": ("여수", "여수시"),
    "속초": ("속초", "속초시"),
}

CATEGORY_SYNONYMS: dict[str, tuple[str, ...]] = {
    "attraction": ("관광", "관광지", "명소", "가볼만", "갈만한", "추천"),
    "indoor": ("실내", "비 오는 날", "비오는날", "박물관", "미술관"),
    "outdoor": ("야외", "해수욕장", "바다", "공원", "둘레길"),
    "festival": ("축제", "행사", "이벤트", "공연", "이번 달", "이번달"),
    "stay": ("숙소", "숙박", "호텔", "펜션", "리조트", "게스트하우스"),
    "restaurant": ("맛집", "음식점", "식당", "먹거리", "카페"),
    "course": ("코스", "일정", "동선", "루트", "당일치기", "1박 2일", "2박 3일"),
    "detail": ("상세", "주소", "홈페이지", "공식", "운영시간", "입장료"),
    "region_code": ("지역코드", "시군구", "지역", "도시"),
    "keyword": ("검색", "키워드", "주변", "근처"),
}

MIN_RELEVANCE_SCORE = 3
DEFAULT_TOP_K = 3


@dataclass(frozen=True)
class RoutedApiCandidate:
    api: TourApiMetadata
    score: int
    matched_regions: tuple[str, ...]
    matched_categories: tuple[str, ...]
    matched_terms: tuple[str, ...]


@dataclass(frozen=True)
class CandidateSelection:
    candidates: tuple[RoutedApiCandidate, ...]
    matched_regions: tuple[str, ...]
    matched_categories: tuple[str, ...]
    is_low_relevance: bool
    reason: str


def select_api_candidates(
    message: str, top_k: int = DEFAULT_TOP_K
) -> CandidateSelection:
    normalized = _normalize(message)
    matched_regions = _matched_regions(normalized)
    matched_categories = _matched_categories(normalized)
    scored_candidates = tuple(
        candidate
        for api in load_tour_api_metadata_index().apis
        if (
            candidate := _score_api(
                api, normalized, matched_regions, matched_categories
            )
        )
        and candidate.score >= MIN_RELEVANCE_SCORE
    )
    candidates = tuple(
        sorted(
            scored_candidates,
            key=lambda item: (-item.score, item.api.priority, item.api.id),
        )[:top_k]
    )

    if not candidates:
        return CandidateSelection(
            candidates=(),
            matched_regions=matched_regions,
            matched_categories=matched_categories,
            is_low_relevance=True,
            reason="low_relevance_no_api_candidate",
        )

    if not matched_regions or not matched_categories:
        return CandidateSelection(
            candidates=candidates,
            matched_regions=matched_regions,
            matched_categories=matched_categories,
            is_low_relevance=True,
            reason="insufficient_region_or_category_signal",
        )

    return CandidateSelection(
        candidates=candidates,
        matched_regions=matched_regions,
        matched_categories=matched_categories,
        is_low_relevance=False,
        reason="api_candidates_selected",
    )


def _score_api(
    api: TourApiMetadata,
    normalized_message: str,
    matched_regions: tuple[str, ...],
    matched_categories: tuple[str, ...],
) -> RoutedApiCandidate | None:
    score = 0
    api_regions = set(api.regions)
    api_categories = set(api.categories)
    candidate_regions = tuple(
        region for region in matched_regions if region in api_regions
    )
    candidate_categories = tuple(
        category for category in matched_categories if category in api_categories
    )
    matched_terms = _matched_terms(
        normalized_message, tuple(api.synonyms) + (api.searchText,)
    )

    score += len(candidate_regions) * 3
    score += len(candidate_categories) * 4
    score += len(matched_terms) * 2
    score += _search_text_score(normalized_message, api.searchText)
    score += _companion_api_score(api.id, matched_regions, matched_categories)

    if score == 0:
        return None

    return RoutedApiCandidate(
        api=api,
        score=score,
        matched_regions=candidate_regions,
        matched_categories=candidate_categories,
        matched_terms=matched_terms,
    )


def _normalize(message: str) -> str:
    return " ".join(message.strip().lower().split())


def _matched_regions(normalized_message: str) -> tuple[str, ...]:
    return tuple(
        region
        for region, synonyms in REGION_SYNONYMS.items()
        if any(synonym.lower() in normalized_message for synonym in synonyms)
    )


def _matched_categories(normalized_message: str) -> tuple[str, ...]:
    return tuple(
        category
        for category, synonyms in CATEGORY_SYNONYMS.items()
        if any(synonym.lower() in normalized_message for synonym in synonyms)
    )


def _matched_terms(normalized_message: str, terms: tuple[str, ...]) -> tuple[str, ...]:
    term_tokens = {
        token.lower()
        for term in terms
        for token in term.split()
        if len(token.strip()) >= 2
    }
    return tuple(sorted(token for token in term_tokens if token in normalized_message))


def _search_text_score(normalized_message: str, search_text: str) -> int:
    query_tokens = {token for token in normalized_message.split() if len(token) >= 2}
    search_tokens = {token.lower() for token in search_text.split() if len(token) >= 2}
    return len(query_tokens & search_tokens)


def _companion_api_score(
    api_id: str,
    matched_regions: tuple[str, ...],
    matched_categories: tuple[str, ...],
) -> int:
    category_set = set(matched_categories)
    if api_id == "detail_common" and category_set & {"attraction", "indoor", "outdoor"}:
        return 7
    if api_id == "area_code" and matched_regions and "festival" in category_set:
        return 5
    if api_id == "search_stay" and "course" in category_set:
        return 5
    if api_id == "restaurant_area" and "course" in category_set:
        return 4
    return 0
