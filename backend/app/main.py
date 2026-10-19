from fastapi import FastAPI

from app.api.routes import router
from app.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="Kids English Speaking Demo")
    app.state.settings = settings
    app.include_router(router)
    return app


app = create_app()