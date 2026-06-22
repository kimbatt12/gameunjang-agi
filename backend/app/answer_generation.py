import re
from dataclasses import dataclass
from urllib.parse import urlparse

from app.external.tourism import NormalizedTourismItem
from app.external.weather import WeatherResult
from app.routing import CandidateSelection
from app.schemas import ChatItem, ChatResponse

UNKNOWN_CONFIRMED_VALUE = "확인된 정보 없음"
API_ITEM_BASIS_LABEL = "API 제공 항목"
DEFAULT_MAX_ITEMS = 5
STRONG_WIND_SPEED_MPS = 14.0


@dataclass(frozen=True)
class RecommendationSeed:
    title: str
    category: str
    address: str | None = None
    official_url: str | None = None


ADVERSE_WEATHER_PATTERNS = tuple(
    re.compile(pattern)
    for pattern in (
        r"(?<![0-9A-Za-z가-힣])비(?:가|는)?\s*"
        r"(?:오(?:는)?\s*날|오는날|오고|오면|온다|와|내리|올)",
        r"우천",
        r"호우",
        r"장마",
        r"폭우",
        r"(?<![0-9A-Za-z가-힣])눈(?:이|은)?\s*"
        r"(?:오(?:는)?\s*날|오는날|오고|오면|온다|와|내리|올)",
        r"폭설",
        r"대설",
        r"폭염",
        r"한파",
        r"강풍",
    )
)
WEATHER_REQUIRED_TERMS = (
    "비 오는 날",
    "비오는날",
    "우천",
    "호우",
    "장마",
    "폭우",
    "눈 오는 날",
    "눈오는날",
    "폭설",
    "대설",
    "폭염",
    "한파",
    "강풍",
    "날씨",
    "예보",
    "주말",
    "일정",
    "코스",
)
OUTDOOR_CATEGORY_TERMS = (
    "등산",
    "산책로",
    "산림",
    "해수욕장",
    "공원",
    "둘레길",
    "해변",
    "자연휴양림",
    "수목원",
    "캠핑장",
)
REGION_NAME_MOUNTAIN_FALSE_POSITIVES = frozenset({"부산", "울산"})
MOUNTAIN_TITLE_TOKEN_PATTERN = re.compile(
    r"(?<![0-9A-Za-z가-힣])([가-힣]+산)(?=$|[^0-9A-Za-z가-힣])"
)


def compose_answer(
    *,
    message: str,
    selection: CandidateSelection,
    api_items: tuple[NormalizedTourismItem, ...] = (),
    weather: WeatherResult | None = None,
) -> ChatResponse:
    weather_context = _weather_context(message, weather)
    items = _build_items(selection, api_items, weather_context["adverse"])
    source_domains = _source_domains(selection, api_items, weather, items)
    warnings = _warnings(selection, items, weather_context, weather)
    answer = _answer_text(
        selection=selection,
        items=items,
        source_domains=source_domains,
        is_itinerary=_is_itinerary(selection),
        weather_summary=weather_context["summary"],
    )

    return ChatResponse(
        type="answer",
        isTourismRelated=True,
        answer=answer,
        items=items,
        sourceDomains=source_domains,
        warnings=warnings,
    )


def _build_items(
    selection: CandidateSelection,
    api_items: tuple[NormalizedTourismItem, ...],
    adverse_weather: bool,
) -> list[ChatItem]:
    if api_items:
        seeds = tuple(
            RecommendationSeed(
                title=item.title,
                category=_category_from_item(item, selection),
                address=item.address,
                official_url=item.official_url,
            )
            for item in api_items
        )
    else:
        return []

    sorted_seeds = [
        seed
        for _, seed in sorted(
            enumerate(seeds),
            key=lambda indexed_seed: (
                _weather_rank(indexed_seed[1].category, adverse_weather),
                indexed_seed[0],
            ),
        )
    ]
    return [
        ChatItem(
            title=seed.title,
            reason=_reason(seed.category, adverse_weather, bool(seed.official_url)),
            address=seed.address,
            openingHours=UNKNOWN_CONFIRMED_VALUE,
            price=UNKNOWN_CONFIRMED_VALUE,
            officialUrl=seed.official_url,
            mapUrl=None,
        )
        for seed in sorted_seeds[:DEFAULT_MAX_ITEMS]
    ]


def _answer_text(
    *,
    selection: CandidateSelection,
    items: list[ChatItem],
    source_domains: list[str],
    is_itinerary: bool,
    weather_summary: str | None,
) -> str:
    region = selection.matched_regions[0] if selection.matched_regions else "국내"
    basis = _basis_text(has_items=bool(items))
    weather_line = f"\n날씨 고려: {weather_summary}" if weather_summary else ""
    source_line = _source_line(source_domains, has_items=bool(items))

    if not items:
        return (
            f"{region} 관광 API 후보는 선택했지만, 확인된 API 항목 데이터가 없어 "
            f"추천 항목을 제공하지 않습니다. {basis}{weather_line}{source_line}"
        )

    if is_itinerary:
        day_plan = _itinerary_lines(items)
        return (
            f"{region} 일정 추천입니다. "
            f"{basis}{weather_line}\n\n{day_plan}{source_line}"
        )

    item_titles = ", ".join(item.title for item in items)
    return f"{region} 추천 항목: {item_titles}. {basis}{weather_line}{source_line}"


def _basis_text(*, has_items: bool) -> str:
    if has_items:
        return (
            "정규화된 API 항목 데이터와 항목별 공식 링크가 있는 경우에만 "
            "공식 링크를 표시했습니다. "
            f"미확인 값은 '{UNKNOWN_CONFIRMED_VALUE}'로 표시합니다."
        )
    return (
        "정규화된 API 항목 데이터가 확인되지 않았습니다. "
        "따라서 임의 추천, 운영시간, 가격, 공식 링크 근거를 생성하지 않습니다."
    )


def _source_line(source_domains: list[str], *, has_items: bool) -> str:
    if not source_domains:
        return ""
    label = "출처" if has_items else "선택된 API 후보 도메인"
    return f"\n{label}: {', '.join(source_domains)}"


def _itinerary_lines(items: list[ChatItem]) -> str:
    morning = items[0].title if len(items) >= 1 else "확인된 관광 후보 없음"
    lunch = items[1].title if len(items) >= 2 else "확인된 음식점 정보 없음"
    afternoon = items[2].title if len(items) >= 3 else morning
    lodging = items[3].title if len(items) >= 4 else "확인된 숙박 정보 없음"
    return "\n".join(
        (
            "1일차",
            f"- 오전: {morning}",
            f"- 점심: {lunch}",
            f"- 오후: {afternoon}",
            "- 저녁: 확인된 정보 기준 제공",
            f"- 숙박: {lodging}",
            "",
            "2일차",
            f"- 오전: {afternoon}",
            f"- 점심: {lunch}",
            "- 오후: 확인된 정보 기준 제공",
        )
    )


def _reason(category: str, adverse_weather: bool, has_official_url: bool) -> str:
    weather_reason = (
        "악천후 조건에서 실내 우선 추천"
        if adverse_weather and category == "indoor"
        else None
    )
    link_reason = (
        "API 제공 공식 링크 확인" if has_official_url else API_ITEM_BASIS_LABEL
    )
    return " · ".join(part for part in (weather_reason, link_reason) if part)


def _weather_context(
    message: str,
    weather: WeatherResult | None,
) -> dict[str, str | bool | None]:
    inferred_adverse = _message_has_adverse_weather_condition(message)
    requires_weather = inferred_adverse or any(
        term in message for term in WEATHER_REQUIRED_TERMS
    )
    if weather and weather.available and weather.forecasts:
        forecast_adverse = _forecast_has_adverse_weather(weather)
        adverse = inferred_adverse or forecast_adverse
        summary_parts = []
        if inferred_adverse:
            summary_parts.append("질문의 날씨 조건을 반영해 실내 항목을 우선했습니다.")
        summary_parts.append(
            "기상청 단기예보 기준 악천후 가능성 반영"
            if forecast_adverse
            else "기상청 단기예보 기준 강수/강풍 지표 없음"
        )
        summary = " ".join(summary_parts)
        return {"required": requires_weather, "adverse": adverse, "summary": summary}
    if weather and weather.available and not weather.forecasts:
        return {
            "required": requires_weather,
            "adverse": inferred_adverse,
            "summary": "기상청 단기예보 항목이 없어 날씨 근거를 확인하지 못했습니다.",
        }
    if inferred_adverse:
        return {
            "required": requires_weather,
            "adverse": True,
            "summary": "질문의 날씨 조건을 반영해 실내 항목을 우선했습니다.",
        }
    return {"required": requires_weather, "adverse": False, "summary": None}


def _message_has_adverse_weather_condition(message: str) -> bool:
    normalized = " ".join(message.strip().split())
    return any(pattern.search(normalized) for pattern in ADVERSE_WEATHER_PATTERNS)


def _forecast_has_adverse_weather(weather: WeatherResult) -> bool:
    adverse_pty_values = {"1", "2", "3", "4", "5", "6", "7"}
    return any(
        (forecast.category == "PTY" and forecast.value in adverse_pty_values)
        or (
            forecast.category == "WSD"
            and _parse_wind_speed(forecast.value) >= STRONG_WIND_SPEED_MPS
        )
        for forecast in weather.forecasts
    )


def _parse_wind_speed(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        return 0.0


def _source_domains(
    selection: CandidateSelection,
    api_items: tuple[NormalizedTourismItem, ...],
    weather: WeatherResult | None,
    items: list[ChatItem],
) -> list[str]:
    if not items:
        domains = {candidate.api.sourceDomain for candidate in selection.candidates}
    else:
        displayed_titles = {item.title for item in items}
        domains = {
            item.source_domain for item in api_items if item.title in displayed_titles
        }
    domains.update(
        domain
        for item in items
        if item.officialUrl and (domain := _domain_from_url(item.officialUrl))
    )
    if weather and weather.available and weather.source_domain:
        domains.add(weather.source_domain)
    return sorted(domains)


def _warnings(
    selection: CandidateSelection,
    items: list[ChatItem],
    weather_context: dict[str, str | bool | None],
    weather: WeatherResult | None,
) -> list[str]:
    warnings = []
    if items:
        warnings.extend(["api_data_first_answer", "unconfirmed_values_marked"])
    if _is_itinerary(selection):
        warnings.append("itinerary_format_applied")
    if weather_context["adverse"]:
        warnings.append("weather_condition_affects_order")
    if weather_context["required"] and not weather:
        warnings.append("weather_api_not_called_using_question_condition")
    if weather and weather.available and not weather.forecasts:
        warnings.append("weather_forecast_data_unavailable")
    if weather:
        warnings.extend(weather.warnings)
    if not items:
        warnings.append("no_recommended_items_from_confirmed_data")
        warnings.append("confirmed_api_item_data_unavailable")
    return warnings


def _is_itinerary(selection: CandidateSelection) -> bool:
    return "course" in selection.matched_categories


def _category_from_selection(selection: CandidateSelection) -> str:
    for category in ("indoor", "outdoor", "restaurant", "stay", "festival", "course"):
        if category in selection.matched_categories:
            return category
    return "attraction"


def _category_from_item(
    item: NormalizedTourismItem,
    selection: CandidateSelection,
) -> str:
    searchable = f"{item.title} {item.address or ''}"
    if any(term in searchable for term in ("실내", "박물관", "미술관", "전시관")):
        return "indoor"
    if any(term in searchable for term in OUTDOOR_CATEGORY_TERMS) or _is_mountain_title(
        item.title
    ):
        return "outdoor"
    if any(term in searchable for term in ("식당", "음식점", "맛집", "카페")):
        return "restaurant"
    if any(term in searchable for term in ("호텔", "숙소", "숙박", "펜션")):
        return "stay"
    return _category_from_selection(selection)


def _is_mountain_title(title: str) -> bool:
    return any(
        token not in REGION_NAME_MOUNTAIN_FALSE_POSITIVES
        for token in MOUNTAIN_TITLE_TOKEN_PATTERN.findall(title)
    )


def _weather_rank(category: str, adverse_weather: bool) -> int:
    if not adverse_weather:
        return 0
    if category == "indoor":
        return 0
    if category in {"restaurant", "stay"}:
        return 1
    return 2


def _domain_from_url(url: str) -> str | None:
    parsed = urlparse(url)
    return parsed.netloc.lower() or None
