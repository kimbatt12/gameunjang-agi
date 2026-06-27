import json
from functools import lru_cache
from importlib import resources
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

METADATA_RESOURCE = "data/current/tour_api_metadata.json"
SCHEMA_RESOURCE = "data/schemas/tour_api_metadata.schema.json"


class TourApiMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    name: str
    description: str
    endpoint: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9]*$")
    method: Literal["GET"]
    requiredParams: list[str]
    optionalParams: list[str]
    responseFields: list[str]
    categories: list[str]
    regions: list[str]
    synonyms: list[str]
    examples: list[str]
    sourceDomain: Literal["data.go.kr", "visitkorea.or.kr"]
    lastCheckedAt: str
    searchText: str
    priority: int = Field(ge=1)


class TourApiMetadataIndex(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schemaVersion: Literal["1.0.0"]
    generatedAt: str
    apis: list[TourApiMetadata]


@lru_cache
def load_tour_api_metadata_index() -> TourApiMetadataIndex:
    payload = json.loads(read_tour_api_metadata_text())

    return TourApiMetadataIndex.model_validate(payload)


def read_tour_api_metadata_text() -> str:
    return _read_routing_resource(METADATA_RESOURCE)


def read_tour_api_metadata_schema_text() -> str:
    return _read_routing_resource(SCHEMA_RESOURCE)


def _read_routing_resource(relative_path: str) -> str:
    return (
        resources.files(__package__).joinpath(relative_path).read_text(encoding="utf-8")
    )
