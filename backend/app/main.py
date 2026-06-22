from fastapi import FastAPI, HTTPException, status

from app.chat_service import build_chat_response
from app.config import get_settings
from app.schemas import ChatRequest, ChatResponse, HealthResponse


def create_app() -> FastAPI:
    app = FastAPI(
        title="Gameunjang-agi API",
        version="0.1.0",
        description="FastAPI-compatible scaffold for domestic tourism chat APIs.",
    )

    @app.get("/health", response_model=HealthResponse, tags=["system"])
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    @app.post("/api/chat", response_model=ChatResponse, tags=["chat"])
    def chat(request: ChatRequest) -> ChatResponse:
        settings = get_settings()
        if len(request.message) > settings.max_user_message_chars:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    "message must be at most "
                    f"{settings.max_user_message_chars} characters"
                ),
            )

        return build_chat_response(request.message.strip())

    return app


app = create_app()
