from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str


class ClientContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timezone: str | None = Field(default=None, max_length=80)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1)
    localConversationId: str | None = Field(default=None, max_length=120)
    clientSessionQuestionCount: int | None = Field(default=None, ge=0)
    clientContext: ClientContext | None = None

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message must not be blank")
        return value


class ChatItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    reason: str | None = None
    address: str | None = None
    openingHours: str | None = None
    price: str | None = None
    officialUrl: str | None = None
    mapUrl: str | None = None


class ChatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["answer", "rejection", "limit_exceeded"]
    isTourismRelated: bool | None
    answer: str
    items: list[ChatItem]
    sourceDomains: list[str]
    warnings: list[str]
