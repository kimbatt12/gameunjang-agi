from fastapi import FastAPI

from app.schemas import HealthResponse


def create_app() -> FastAPI:
    app = FastAPI(
        title="Gameunjang-agi API",
        version="0.1.0",
        description="FastAPI-compatible scaffold for domestic tourism chat APIs.",
    )

    @app.get("/health", response_model=HealthResponse, tags=["system"])
    def health() -> HealthResponse:
        return HealthResponse(status="ok")

    return app


app = create_app()
