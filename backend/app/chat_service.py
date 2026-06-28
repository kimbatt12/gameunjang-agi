import json
import logging
from datetime import UTC, datetime
from typing import Protocol

from app.answer_generation import compose_answer, requires_weather_api
from app.config import Settings, get_settings
from app.external.llm import (
    FallbackLLMProvider,
    LLMMessage,
    LLMProvider,
    LLMProviderError,
    LLMRequest,
    OpenRouterProvider,
    UpstageProvider,
)
from app.external.tourism import (
    KoreaTourismClient,
    NormalizedTourismItem,
    TourismApiError,
    normalize_tourism_response,
)
from app.external.weather import KoreaWeatherClient, WeatherResult
from app.guard import ScopeClassification
from app.routing import CandidateSelection, RoutedApiCandidate, select_api_candidates
from app.schemas import ChatResponse

SCOPE_GUIDANCE = (
    "이 서비스는 국내 관광 관련 질문에만 답변할 수 있습니다. "
    "여행지, 관광지, 축제, 숙소, 음식점, 여행코스와 관련된 질문을 입력해 주세요."
)

COMMON_TOURISM_REQUIRED_PARAMS = frozenset(
    {"serviceKey", "MobileOS", "MobileApp", "_type"}
)
REGION_API_CODES: dict[str, tuple[str, str | None]] = {
    "서울": ("1", None),
    "부산": ("6", None),
    "강릉": ("32", "1"),
    "제주": ("39", None),
    "경주": ("35", "2"),
    "전주": ("37", "12"),
    "여수": ("38", "13"),
    "속초": ("32", "5"),
}
REGION_WEATHER_GRIDS: dict[str, tuple[int, int]] = {
    "서울": (60, 127),
    "부산": (98, 76),
    "강릉": (92, 131),
    "제주": (52, 38),
    "경주": (100, 91),
    "전주": (63, 89),
    "여수": (73, 66),
    "속초": (87, 141),
}

logger = logging.getLogger(__name__)

SUPPORTED_SCOPE_LABELS = frozenset({"domestic_tourism", "out_of_scope"})
KOREAN_LABEL_SUFFIXES = ("입니다", "이에요", "예요")


class TourismClient(Protocol):
    def get(self, endpoint: str, params: dict[str, str | int]) -> dict[str, object]:
        """Return a Korea Tourism API JSON payload."""


class WeatherClient(Protocol):
    def get_vilage_forecast(self, params: dict[str, str | int]) -> WeatherResult:
        """Return a normalized KMA village forecast result."""


def build_chat_response(
    message: str,
    *,
    tourism_client: TourismClient | None = None,
    weather_client: WeatherClient | None = None,
    llm_provider: LLMProvider | None = None,
) -> ChatResponse:
    response = _build_chat_response_with_internal_warnings(
        message,
        tourism_client=tourism_client,
        weather_client=weather_client,
        llm_provider=llm_provider,
    )
    return _finalize_chat_response(response)


def _build_chat_response_with_internal_warnings(
    message: str,
    *,
    tourism_client: TourismClient | None = None,
    weather_client: WeatherClient | None = None,
    llm_provider: LLMProvider | None = None,
) -> ChatResponse:
    settings: Settings | None = None
    llm = llm_provider
    warnings: list[str] = []

    settings = get_settings()
    llm = llm_provider or _default_llm_provider(settings)
    scope = _classify_scope_with_llm(message=message, llm_provider=llm)
    if not scope.is_tourism_related:
        return _build_out_of_scope_response(warnings=[scope.reason])
    warnings.append("llm_scope_classified_domestic_tourism")

    selection = select_api_candidates(message, default_missing_signals=True)
    selection = _select_api_routes_with_llm(
        message=message,
        selection=selection,
        llm_provider=llm,
    )
    if selection.is_low_relevance:
        response = _build_insufficient_information_response(selection)
        response.warnings.extend(warnings)
        return response

    tourism = tourism_client or _default_tourism_client(settings)
    weather = weather_client or _default_weather_client(settings)
    llm = llm or _default_llm_provider(settings)

    api_items, integration_warnings = _fetch_tourism_items(
        selection=selection,
        tourism_client=tourism,
    )
    weather_result = _fetch_weather(
        message=message,
        selection=selection,
        weather_client=weather,
    )
    response = compose_answer(
        message=message,
        selection=selection,
        api_items=api_items,
        weather=weather_result,
    )
    response.warnings.extend(warnings)
    response.warnings.extend(integration_warnings)
    return _compose_with_llm(
        message=message,
        response=response,
        api_items=api_items,
        llm_provider=llm,
    )


def _finalize_chat_response(response: ChatResponse) -> ChatResponse:
    internal_warnings = list(response.warnings)
    logger.info(
        "chat response produced",
        extra={
            "response_type": response.type,
            "warnings": internal_warnings,
            "warning_count": len(internal_warnings),
        },
    )
    return response.model_copy(update={"warnings": []})


def _build_out_of_scope_response(*, warnings: list[str]) -> ChatResponse:
    return ChatResponse(
        type="rejection",
        isTourismRelated=False,
        answer=SCOPE_GUIDANCE,
        items=[],
        sourceDomains=[],
        warnings=warnings,
    )


def _classify_scope_with_llm(
    *,
    message: str,
    llm_provider: LLMProvider | None,
) -> ScopeClassification:
    if llm_provider is None:
        return ScopeClassification(
            label="out_of_scope",
            reason="llm_scope_classification_provider_missing",
        )

    try:
        llm_response = llm_provider.complete(
            LLMRequest(
                messages=(
                    LLMMessage(
                        role="system",
                        content=(
                            "사용자 질문이 국내 관광 질문인지 분류하세요. "
                            "반드시 domestic_tourism 또는 out_of_scope 중 "
                            "하나의 라벨만 답하세요. 자연스러운 한국어 표현과 "
                            "짧은 구어체도 고려하세요. 국내 여행, 관광, 장소, "
                            "명소, 음식, 숙소, 축제, 산책, 스키장, 여행 코스, "
                            "갈 만한 곳을 묻는 질문이면 domestic_tourism입니다. "
                            "예: 부산 축제 알려줘 -> domestic_tourism, "
                            "전주 맛집 추천 -> domestic_tourism, "
                            "제주 숙소 알려줘 -> domestic_tourism, "
                            "강릉 1박 2일 루트 짜줘 -> domestic_tourism. "
                            "해외 여행이나 관광과 무관한 질문은 out_of_scope입니다."
                        ),
                    ),
                    LLMMessage(role="user", content=message),
                ),
                max_tokens=8,
                temperature=0,
            )
        )
    except LLMProviderError:
        return ScopeClassification(
            label="out_of_scope",
            reason="llm_scope_classification_failed",
        )

    classification = _parse_scope_label(llm_response.text)
    if classification == "domestic_tourism":
        return ScopeClassification(label="domestic_tourism")
    if classification == "out_of_scope":
        return ScopeClassification(
            label="out_of_scope",
            reason="llm_scope_classified_out_of_scope",
        )
    return ScopeClassification(
        label="out_of_scope",
        reason="llm_scope_classification_malformed",
    )


def _parse_scope_label(text: str) -> str | None:
    normalized = _strip_markdown_code_fence(text.strip())
    json_label = _parse_scope_label_json(normalized)
    if json_label is not None:
        return json_label
    return _parse_scope_label_plain(normalized)


def _parse_scope_label_json(text: str) -> str | None:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    if isinstance(payload, str):
        return _parse_scope_label_plain(payload)
    if isinstance(payload, dict):
        label = payload.get("label")
        if isinstance(label, str):
            return _parse_scope_label_plain(label)
    return None


def _parse_scope_label_plain(text: str) -> str | None:
    normalized = text.strip().lower().strip("` \n\t.,:;!?'\"")
    if normalized in SUPPORTED_SCOPE_LABELS:
        return normalized
    for label in SUPPORTED_SCOPE_LABELS:
        if any(normalized == f"{label}{suffix}" for suffix in KOREAN_LABEL_SUFFIXES):
            return label
    return None


def _strip_markdown_code_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```") or not stripped.endswith("```"):
        return stripped
    lines = stripped.splitlines()
    if len(lines) < 3:
        return stripped
    return "\n".join(lines[1:-1]).strip()


def _select_api_routes_with_llm(
    *,
    message: str,
    selection: CandidateSelection,
    llm_provider: LLMProvider | None,
) -> CandidateSelection:
    if llm_provider is None or not selection.candidates:
        return selection

    prompt = _api_route_prompt(message=message, selection=selection)
    try:
        llm_response = llm_provider.complete(
            LLMRequest(
                messages=(
                    LLMMessage(
                        role="system",
                        content=(
                            "Choose the best Korea Tourism API route candidates. "
                            'Return only strict JSON: {"ids":["candidate_id"]}. '
                            "Use only IDs from the api route candidates list."
                        ),
                    ),
                    LLMMessage(role="user", content=prompt),
                ),
                max_tokens=80,
                temperature=0,
            )
        )
    except LLMProviderError:
        return selection
    except IndexError:
        return selection

    selected_ids = _parse_route_candidate_ids(llm_response.text)
    candidate_by_id = {
        candidate.api.id: candidate for candidate in selection.candidates
    }
    selected_candidates = tuple(
        candidate_by_id[candidate_id]
        for candidate_id in selected_ids
        if candidate_id in candidate_by_id
    )
    if not selected_candidates:
        return selection

    selected_id_set = {candidate.api.id for candidate in selected_candidates}
    remaining_candidates = tuple(
        candidate
        for candidate in selection.candidates
        if candidate.api.id not in selected_id_set
    )
    return CandidateSelection(
        candidates=selected_candidates + remaining_candidates,
        matched_regions=selection.matched_regions,
        matched_categories=selection.matched_categories,
        is_low_relevance=selection.is_low_relevance,
        reason=selection.reason,
    )


def _api_route_prompt(*, message: str, selection: CandidateSelection) -> str:
    candidate_lines = []
    for candidate in selection.candidates:
        api = candidate.api
        region_hint = (
            ",".join(candidate.matched_regions)
            if candidate.matched_regions
            else "nationwide-capable"
        )
        category_hint = ",".join(api.categories[:4])
        candidate_lines.append(
            f"{api.id}|{api.endpoint}|priority={api.priority}|"
            f"categories={category_hint}|regions={region_hint}|"
            f"summary={api.description}|search={api.searchText}"
        )
    return (
        f"question={message}\n"
        f"detected_regions={','.join(selection.matched_regions) or 'nationwide'}\n"
        f"detected_categories={','.join(selection.matched_categories) or 'none'}\n"
        "api route candidates:\n" + "\n".join(candidate_lines)
    )


def _parse_route_candidate_ids(text: str) -> tuple[str, ...]:
    stripped = text.strip()
    if not stripped:
        return ()

    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        cleaned = stripped.strip("` \n\t.,;:'\"")
        return (cleaned,) if _is_candidate_id(cleaned) else ()

    if isinstance(payload, str):
        return (payload,) if _is_candidate_id(payload) else ()
    if isinstance(payload, list):
        return tuple(
            item for item in payload if isinstance(item, str) and _is_candidate_id(item)
        )
    if isinstance(payload, dict):
        for key in ("ids", "candidate_ids", "api_ids"):
            value = payload.get(key)
            if isinstance(value, list):
                return tuple(
                    item
                    for item in value
                    if isinstance(item, str) and _is_candidate_id(item)
                )
        for key in ("id", "candidate_id", "api_id"):
            value = payload.get(key)
            if isinstance(value, str) and _is_candidate_id(value):
                return (value,)
    return ()


def _is_candidate_id(value: str) -> bool:
    return bool(value) and all(
        character.islower() or character.isdigit() or character == "_"
        for character in value
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


def _fetch_tourism_items(
    *,
    selection: CandidateSelection,
    tourism_client: TourismClient | None,
) -> tuple[tuple[NormalizedTourismItem, ...], list[str]]:
    if tourism_client is None or not selection.candidates:
        return (), []

    candidate, params = _first_callable_candidate(selection)
    if candidate is None or params is None:
        return (), []

    try:
        payload = tourism_client.get(
            candidate.api.endpoint,
            params,
        )
    except TourismApiError:
        return (), ["tourism_api_unavailable"]

    return normalize_tourism_response(payload), []


def _first_callable_candidate(
    selection: CandidateSelection,
) -> tuple[RoutedApiCandidate | None, dict[str, str | int] | None]:
    for candidate in selection.candidates:
        params = _tourism_params(selection=selection, candidate=candidate)
        if params is not None:
            return candidate, params
    return None, None


def _tourism_params(
    *,
    selection: CandidateSelection,
    candidate: RoutedApiCandidate,
) -> dict[str, str | int] | None:
    params: dict[str, str | int] = {"numOfRows": 10, "pageNo": 1, "arrange": "A"}
    for required_param in candidate.api.requiredParams:
        if required_param in COMMON_TOURISM_REQUIRED_PARAMS:
            continue
        if "=" in required_param:
            key, value = required_param.split("=", maxsplit=1)
            params[key] = value
            continue
        if required_param == "keyword" and selection.matched_regions:
            params["keyword"] = selection.matched_regions[0]
            continue
        if required_param == "eventStartDate":
            params["eventStartDate"] = datetime.now(UTC).strftime("%Y%m%d")
            continue
        return None

    if selection.matched_regions:
        area_code, sigungu_code = REGION_API_CODES.get(
            selection.matched_regions[0],
            (None, None),
        )
        if area_code:
            params["areaCode"] = area_code
        if sigungu_code:
            params["sigunguCode"] = sigungu_code

    return params


def _fetch_weather(
    *,
    message: str,
    selection: CandidateSelection,
    weather_client: WeatherClient | None,
) -> WeatherResult | None:
    if weather_client is None or not requires_weather_api(message):
        return None
    if not selection.matched_regions:
        return None
    grid = REGION_WEATHER_GRIDS.get(selection.matched_regions[0])
    if grid is None:
        return None

    nx, ny = grid
    return weather_client.get_vilage_forecast(
        {
            "base_date": datetime.now(UTC).strftime("%Y%m%d"),
            "base_time": "0500",
            "nx": nx,
            "ny": ny,
        }
    )


def _compose_with_llm(
    *,
    message: str,
    response: ChatResponse,
    api_items: tuple[NormalizedTourismItem, ...],
    llm_provider: LLMProvider | None,
) -> ChatResponse:
    if llm_provider is None or not api_items:
        return response

    prompt = _llm_prompt(message=message, response=response, api_items=api_items)
    try:
        llm_response = llm_provider.complete(
            LLMRequest(
                messages=(
                    LLMMessage(
                        role="system",
                        content=(
                            "정규화된 공식 관광 API 항목만 근거로 "
                            "한국어 답변을 작성하세요. "
                            "확인되지 않은 운영시간, 가격, 링크는 만들지 마세요."
                        ),
                    ),
                    LLMMessage(role="user", content=prompt),
                ),
                max_tokens=700,
            )
        )
    except LLMProviderError:
        response.warnings.append("llm_provider_unavailable")
        return response

    response.answer = llm_response.text
    response.warnings.extend(llm_response.warnings)
    response.warnings.append("llm_composed_answer")
    return response


def _llm_prompt(
    *,
    message: str,
    response: ChatResponse,
    api_items: tuple[NormalizedTourismItem, ...],
) -> str:
    item_lines = "\n".join(
        f"- {item.title} | 주소: {item.address or '확인된 정보 없음'} | "
        f"공식 링크: {item.official_url or '확인된 정보 없음'}"
        for item in api_items
    )
    return (
        f"사용자 질문: {message}\n"
        f"compose_answer 초안: {response.answer}\n"
        "정규화된 관광 API 항목:\n"
        f"{item_lines}"
    )


def _default_tourism_client(settings: Settings) -> KoreaTourismClient | None:
    if settings.tour_api_service_key is None:
        return None
    return KoreaTourismClient(service_key=settings.tour_api_service_key)


def _default_weather_client(settings: Settings) -> KoreaWeatherClient | None:
    if settings.tour_api_service_key is None:
        return None
    return KoreaWeatherClient(service_key=settings.tour_api_service_key)


def _default_llm_provider(settings: Settings) -> LLMProvider | None:
    upstage = None
    if settings.upstage_api_key and settings.upstage_model:
        upstage = UpstageProvider(
            api_key=settings.upstage_api_key,
            model=settings.upstage_model,
        )
    openrouter = None
    if settings.openrouter_api_key and settings.openrouter_model:
        openrouter = OpenRouterProvider(
            api_key=settings.openrouter_api_key,
            model=settings.openrouter_model,
        )
    if upstage and openrouter:
        return FallbackLLMProvider(primary=upstage, fallback=openrouter)
    return upstage or openrouter
