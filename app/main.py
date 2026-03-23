"""FastAPI application entrypoint."""

from fastapi import FastAPI

from app.api.routes import router as api_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="CareerCopilot-SkillMemory",
        version="0.1.0",
        description="Single-user career-finding agent backend for interview demo.",
    )
    app.include_router(api_router)
    return app


app = create_app()
