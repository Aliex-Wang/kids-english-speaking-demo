from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.routes import router
from app.config import Settings, get_settings
from app.services import Services, build_services

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def create_app(
    settings: Settings | None = None,
    services: Services | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="Kids English Speaking Demo")
    if services is None:
        services = build_services(settings, templates)
    app.state.services = services
    app.state.settings = settings
    app.mount(
        "/static",
        StaticFiles(directory=BASE_DIR / "static", check_dir=False),
        name="static",
    )
    app.include_router(router)
    return app


app = create_app()
