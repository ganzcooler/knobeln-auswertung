"""FastAPI-App für die lokale Web-UI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..application import KnobelnService

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def create_app(service: KnobelnService) -> FastAPI:
    app = FastAPI(title="Knobeln-Auswertung")
    app.mount(
        "/static",
        StaticFiles(directory=str(BASE_DIR / "static")),
        name="static",
    )

    def context(request: Request, **extra: Any) -> dict[str, Any]:
        current = service.last_opened_turnier()
        return {
            "request": request,
            "turniere": service.list_turniere(),
            "current_turnier": current,
            **extra,
        }

    def scannen_mit_fehler(request: Request, message: str) -> HTMLResponse:
        return TEMPLATES.TemplateResponse(
            request=request,
            name="scannen.html",
            context=context(request, error=message),
            status_code=400,
        )

    @app.get("/", include_in_schema=False)
    def index() -> RedirectResponse:
        return RedirectResponse("/scannen", status_code=303)

    @app.get("/scannen", response_class=HTMLResponse)
    def scannen(request: Request) -> HTMLResponse:
        return TEMPLATES.TemplateResponse(
            request=request,
            name="scannen.html",
            context=context(request),
        )

    @app.post("/turniere", response_class=HTMLResponse)
    def turnier_anlegen(request: Request, name: str = Form(...)) -> Any:
        try:
            service.create_turnier(name)
        except ValueError as exc:
            return scannen_mit_fehler(request, str(exc))
        return RedirectResponse("/scannen", status_code=303)

    @app.post("/turniere/{turnier_id}/oeffnen", response_class=HTMLResponse)
    def turnier_oeffnen(turnier_id: int) -> RedirectResponse:
        service.open_turnier(turnier_id)
        return RedirectResponse("/scannen", status_code=303)

    @app.post("/turniere/{turnier_id}/umbenennen", response_class=HTMLResponse)
    def turnier_umbenennen(
        request: Request,
        turnier_id: int,
        name: str = Form(...),
    ) -> Any:
        try:
            service.rename_turnier(turnier_id, name)
        except ValueError as exc:
            return scannen_mit_fehler(request, str(exc))
        return RedirectResponse("/scannen", status_code=303)

    @app.get("/turniere/{turnier_id}/loeschen", response_class=HTMLResponse)
    def turnier_loeschen_bestaetigen(
        request: Request,
        turnier_id: int,
    ) -> HTMLResponse:
        turnier = service.get_turnier(turnier_id)
        return TEMPLATES.TemplateResponse(
            request=request,
            name="turnier_loeschen.html",
            context=context(request, turnier=turnier),
        )

    @app.post("/turniere/{turnier_id}/loeschen", response_class=HTMLResponse)
    def turnier_loeschen(turnier_id: int) -> RedirectResponse:
        service.delete_turnier(turnier_id)
        return RedirectResponse("/scannen", status_code=303)

    return app
