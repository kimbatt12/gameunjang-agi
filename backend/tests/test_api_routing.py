import json

from jsonschema import Draft202012Validator

from app.routing import select_api_candidates
from app.routing.metadata import (
    TourApiMetadataIndex,
    read_tour_api_metadata_schema_text,
    read_tour_api_metadata_text,
)


def test_tour_api_metadata_matches_declared_schema_shape() -> None:
    schema = json.loads(read_tour_api_metadata_schema_text())
    payload = json.loads(read_tour_api_metadata_text())

    Draft202012Validator.check_schema(schema)
    Draft202012Validator(
        schema,
        format_checker=Draft202012Validator.FORMAT_CHECKER,
    ).validate(payload)

    assert schema["title"] == "Korea Tourism Organization API Metadata Index"
    assert set(schema["required"]) == {"schemaVersion", "generatedAt", "apis"}
    assert set(schema["$defs"]["apiMetadata"]["required"]) <= set(
        schema["$defs"]["apiMetadata"]["properties"]
    )

    metadata = TourApiMetadataIndex.model_validate(payload)
    assert metadata.schemaVersion == "1.0.0"
    assert {api.id for api in metadata.apis} >= {
        "area_based_list",
        "search_keyword",
        "detail_common",
        "search_festival",
        "search_stay",
        "restaurant_area",
        "tour_course",
        "area_code",
    }


def test_routes_region_and_indoor_category_to_area_based_list() -> None:
    selection = select_api_candidates("부산 실내 관광지 추천")

    assert selection.is_low_relevance is False
    assert selection.matched_regions == ("부산",)
    assert "indoor" in selection.matched_categories
    assert [candidate.api.id for candidate in selection.candidates][:3] == [
        "area_based_list",
        "search_keyword",
        "detail_common",
    ]


def test_routes_festival_synonym_to_festival_and_area_code() -> None:
    selection = select_api_candidates("이번 달 서울 행사 뭐 있어?")

    assert selection.is_low_relevance is False
    assert selection.matched_regions == ("서울",)
    candidate_ids = [candidate.api.id for candidate in selection.candidates]
    assert candidate_ids[0] == "search_festival"
    assert "area_code" in candidate_ids


def test_routes_itinerary_synonym_to_course_related_candidates() -> None:
    selection = select_api_candidates("강릉 2박 3일 코스 짜줘")

    assert selection.is_low_relevance is False
    candidate_ids = [candidate.api.id for candidate in selection.candidates]
    assert candidate_ids[0] == "tour_course"
    assert "search_stay" in candidate_ids


def test_low_relevance_policy_when_region_is_missing() -> None:
    selection = select_api_candidates("축제 알려줘")

    assert selection.is_low_relevance is True
    assert selection.reason == "insufficient_region_or_category_signal"
    assert selection.matched_regions == ()
    assert selection.matched_categories == ("festival",)
