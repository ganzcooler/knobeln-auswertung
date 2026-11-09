"""FastAPI-App für die lokale Web-UI."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from urllib.parse import quote

from fastapi import (
    BackgroundTasks,
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..application import DuplicateScanError, KnobelnService
from ..domain.wertung import GUELTIGE_PUNKTE

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def create_app(service: KnobelnService) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        service.process_pending_jobs()
        yield

    app = FastAPI(title="Knobeln-Auswertung", lifespan=lifespan)
    app.mount(
        "/static",
        StaticFiles(directory=str(BASE_DIR / "static")),
        name="static",
    )

    def context(request: Request, **extra: Any) -> dict[str, Any]:
        turniere = service.list_turniere()
        current = service.last_opened_turnier()
        if current is None and turniere:
            current = turniere[0]
        durchgaenge = service.list_durchgaenge(current.id) if current else []
        durchgang = service.current_durchgang(current.id) if current else None
        faelle = service.list_prueffaelle(durchgang.id) if durchgang else []
        return {
            "request": request,
            "turniere": turniere,
            "current_turnier": current,
            "durchgaenge": durchgaenge,
            "current_durchgang": durchgang,
            "prueffall_count": len(faelle),
            "connection_status": service.connection_status(),
            "undo_available": service.has_undo(),
            "gueltige_punkte": sorted(GUELTIGE_PUNKTE),
            **extra,
        }

    def scannen_mit_fehler(request: Request, message: str) -> HTMLResponse:
        return TEMPLATES.TemplateResponse(
            request=request,
            name="scannen.html",
            context=context(request, error=message),
            status_code=400,
        )

    def redirect(
        path: str,
        *,
        hinweis: str | None = None,
        fehler: str | None = None,
    ) -> RedirectResponse:
        params: list[str] = []
        if hinweis:
            params.append(f"hinweis={quote(hinweis)}")
        if fehler:
            params.append(f"fehler={quote(fehler)}")
        suffix = f"?{'&'.join(params)}" if params else ""
        return RedirectResponse(f"{path}{suffix}", status_code=303)

    # -- Grundgerüst -----------------------------------------------------

    @app.get("/", include_in_schema=False)
    def index() -> RedirectResponse:
        return RedirectResponse("/scannen", status_code=303)

    @app.get("/scannen", response_class=HTMLResponse)
    def scannen(
        request: Request,
        background_tasks: BackgroundTasks,
        hinweis: str | None = None,
        fehler: str | None = None,
    ) -> HTMLResponse:
        durchgang = context(request)["current_durchgang"]
        bogen_liste = service.list_bogen(durchgang.id) if durchgang else []
        offene_bogen_ids = (
            {
                fall.bogen_id
                for fall in service.list_prueffaelle(durchgang.id)
                if fall.bogen_id is not None
            }
            if durchgang
            else set()
        )
        bogen_warten = sum(1 for bogen in bogen_liste if bogen.job_status == "warten")
        bogen_laeuft = sum(1 for bogen in bogen_liste if bogen.job_status == "laeuft")
        if bogen_warten and service.llm_client is not None:
            background_tasks.add_task(service.process_pending_jobs)
        manual_groups = (
            [
                stored
                for stored in service.list_gruppen(durchgang.id)
                if stored.quelle == "manuell"
            ]
            if durchgang
            else []
        )
        return TEMPLATES.TemplateResponse(
            request=request,
            name="scannen.html",
            context=context(
                request,
                bogen_liste=bogen_liste,
                manual_groups=manual_groups,
                bogen_total=len(bogen_liste),
                bogen_warten=bogen_warten,
                bogen_laeuft=bogen_laeuft,
                bogen_fertig=sum(
                    1
                    for bogen in bogen_liste
                    if bogen.job_status in {"fertig", "bogen_unklar"}
                ),
                offene_bogen_ids=offene_bogen_ids,
                hinweis=hinweis,
                error=fehler,
            ),
        )

    @app.post("/turniere", response_class=HTMLResponse)
    def turnier_anlegen(request: Request, name: str = Form(...)) -> Any:
        try:
            service.create_turnier(name)
        except ValueError as exc:
            return scannen_mit_fehler(request, str(exc))
        return redirect("/scannen", hinweis="Turnier angelegt.")

    @app.post("/turniere/{turnier_id}/oeffnen", response_class=HTMLResponse)
    def turnier_oeffnen(turnier_id: int) -> RedirectResponse:
        service.open_turnier(turnier_id)
        return redirect("/scannen")

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
        return redirect("/scannen", hinweis="Turnier umbenannt.")

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
        return redirect("/scannen", hinweis="Turnier gelöscht.")

    # -- Durchgang -------------------------------------------------------

    @app.post("/durchgang", response_class=HTMLResponse)
    def durchgang_anlegen(
        request: Request,
        nummer: int = Form(...),
    ) -> Any:
        current = service.last_opened_turnier()
        if current is None:
            return scannen_mit_fehler(request, "Bitte zuerst ein Turnier anlegen.")
        try:
            service.create_durchgang(current.id, nummer)
        except ValueError as exc:
            return scannen_mit_fehler(request, str(exc))
        return redirect("/scannen", hinweis="Durchgang angelegt.")

    @app.post("/durchgang/oeffnen", response_class=HTMLResponse)
    def durchgang_oeffnen_form(durchgang_id: int = Form(...)) -> RedirectResponse:
        service.open_durchgang(durchgang_id)
        return redirect("/scannen")

    @app.post("/durchgang/{durchgang_id}/oeffnen", response_class=HTMLResponse)
    def durchgang_oeffnen(durchgang_id: int) -> RedirectResponse:
        service.open_durchgang(durchgang_id)
        return redirect("/scannen")

    # -- Scan-Import -----------------------------------------------------

    @app.post("/bogen/upload", response_class=HTMLResponse)
    async def bogen_upload(
        request: Request,
        background_tasks: BackgroundTasks,
        dateien: list[UploadFile] = File(...),
        force: bool = Form(False),
    ) -> Any:
        current = service.last_opened_turnier()
        durchgang = service.current_durchgang(current.id) if current else None
        if durchgang is None:
            return scannen_mit_fehler(request, "Bitte zuerst einen Durchgang anlegen.")
        fehler: list[str] = []
        importiert = 0
        for datei in dateien:
            if not datei.filename:
                continue
            data = await datei.read()
            try:
                imported = service.import_scan(
                    dateiname=datei.filename,
                    data=data,
                    durchgang_id=durchgang.id,
                    force=force,
                )
                importiert += len(imported)
            except DuplicateScanError:
                fehler.append(
                    f"{datei.filename}: scheint schon im Stapel zu sein. "
                    "Mit „Duplikat behalten“ erneut ablegen."
                )
            except Exception as exc:  # noqa: BLE001 - Uploadfehler inline zeigen
                fehler.append(f"{datei.filename}: {exc}")
        if importiert:
            background_tasks.add_task(service.process_pending_jobs)
        if fehler:
            return redirect("/scannen", fehler=" | ".join(fehler))
        return redirect("/scannen", hinweis=f"{importiert} Bogen importiert.")

    @app.get("/bogen/{bogen_id}/scan")
    def bogen_scan(bogen_id: int) -> FileResponse:
        try:
            path = service.get_scan_path(bogen_id)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return FileResponse(path, media_type="image/jpeg")

    @app.post("/bogen/{bogen_id}/retry", response_class=HTMLResponse)
    def bogen_retry(
        bogen_id: int, background_tasks: BackgroundTasks
    ) -> RedirectResponse:
        service.retry_bogen(bogen_id)
        background_tasks.add_task(service.process_pending_jobs)
        return redirect("/scannen", hinweis="Bogen wird erneut gelesen.")

    @app.post("/bogen/{bogen_id}/bestaetigen", response_class=HTMLResponse)
    def bogen_bestaetigen_route(bogen_id: int) -> RedirectResponse:
        try:
            service.bogen_bestaetigen(bogen_id)
        except (ValueError, LookupError) as exc:
            return redirect("/scannen", fehler=str(exc))
        return redirect("/scannen", hinweis="Bogen bestätigt.")

    # -- Manuelle Ergebnisse --------------------------------------------

    @app.post("/manuell", response_class=HTMLResponse)
    def manuell_erfassen(
        request: Request,
        spieler_nr: str = Form(...),
        spieler_name: str = Form(""),
        summe: int = Form(...),
    ) -> Any:
        current = service.last_opened_turnier()
        durchgang = service.current_durchgang(current.id) if current else None
        if durchgang is None:
            return scannen_mit_fehler(request, "Bitte zuerst einen Durchgang anlegen.")
        try:
            service.create_manual_result(
                durchgang_id=durchgang.id,
                spieler_nr=spieler_nr,
                spieler_name=spieler_name,
                summe=summe,
            )
        except ValueError as exc:
            return scannen_mit_fehler(request, str(exc))
        return redirect("/scannen", hinweis="Manuelles Ergebnis gespeichert.")

    @app.post("/manuell/{gruppe_id}/bearbeiten", response_class=HTMLResponse)
    def manuell_bearbeiten(
        gruppe_id: int,
        summe: int = Form(...),
        spieler_name: str = Form(""),
    ) -> RedirectResponse:
        try:
            service.update_manual_result(
                gruppe_id,
                summe=summe,
                spieler_name=spieler_name,
            )
        except (ValueError, LookupError) as exc:
            return redirect("/scannen", fehler=str(exc))
        return redirect("/scannen", hinweis="Manuelles Ergebnis geändert.")

    # -- Prüfen ----------------------------------------------------------

    @app.get("/pruefen", response_class=HTMLResponse)
    def pruefen(
        request: Request,
        fall: str | None = None,
        art: str | None = None,
        hinweis: str | None = None,
        fehler: str | None = None,
    ) -> HTMLResponse:
        durchgang = context(request)["current_durchgang"]
        if durchgang is None:
            return TEMPLATES.TemplateResponse(
                request=request,
                name="pruefen.html",
                context=context(
                    request,
                    faelle=[],
                    selected=None,
                    bogen=None,
                    groups=[],
                    konflikt=None,
                    konflikt_gruppen=[],
                    art=None,
                    hinweis=hinweis,
                    error=fehler,
                ),
            )
        faelle = service.list_prueffaelle(durchgang.id)
        if art:
            faelle = [fall for fall in faelle if fall.art == art]
        selected = (
            service.get_prueffall(durchgang.id, fall)
            if fall
            else (faelle[0] if faelle else None)
        )
        bogen = None
        groups = []
        konflikt = None
        konflikt_gruppen = []
        if selected is not None:
            if selected.bogen_id is not None:
                bogen = service.get_bogen(selected.bogen_id)
                groups = service.list_gruppen_for_bogen(selected.bogen_id)
            if selected.konflikt_id is not None:
                konflikt = service.get_konflikt(selected.konflikt_id)
                konflikt_gruppen = [
                    service.get_gruppe(konflikt.gruppe_a_id),
                    service.get_gruppe(konflikt.gruppe_b_id),
                ]
        return TEMPLATES.TemplateResponse(
            request=request,
            name="pruefen.html",
            context=context(
                request,
                faelle=faelle,
                selected=selected,
                bogen=bogen,
                groups=groups,
                konflikt=konflikt,
                konflikt_gruppen=konflikt_gruppen,
                art=art,
                hinweis=hinweis,
                error=fehler,
            ),
        )

    @app.post("/pruefen/aktion", response_class=HTMLResponse)
    def pruefen_aktion(
        background_tasks: BackgroundTasks,
        aktion: str = Form(...),
        gruppe_id: int = Form(0),
        wurf_nr: int = Form(0),
        wert: int = Form(0),
        bogen_id: int = Form(0),
        konflikt_id: int = Form(0),
        gewaehlt_gruppe_id: int = Form(0),
        spieler_nr: str = Form(""),
    ) -> RedirectResponse:
        try:
            if aktion == "korrigieren":
                service.korrigiere_wert(gruppe_id, wurf_nr, wert)
            elif aktion == "uebernehmen":
                service.uebernehme_wert(gruppe_id, wurf_nr)
            elif aktion == "unleserlich":
                service.markiere_unleserlich(gruppe_id, wurf_nr)
            elif aktion == "summe_akzeptieren":
                service.summe_akzeptieren(gruppe_id)
            elif aktion == "kopf_korrigieren":
                service.korrigiere_kopf(gruppe_id, spieler_nr)
            elif aktion == "bogen_bestaetigen":
                service.bogen_bestaetigen(bogen_id)
            elif aktion == "konflikt":
                service.konflikt_entscheiden(konflikt_id, gewaehlt_gruppe_id)
            elif aktion == "retry":
                service.retry_bogen(bogen_id)
                background_tasks.add_task(service.process_pending_jobs)
            else:
                raise ValueError("Unbekannte Aktion.")
        except (ValueError, LookupError) as exc:
            return redirect("/pruefen", fehler=str(exc))
        return redirect("/pruefen", hinweis="Gespeichert.")

    @app.post("/pruefen/undo", response_class=HTMLResponse)
    def pruefen_undo() -> RedirectResponse:
        if service.undo_letzte_korrektur():
            return redirect("/pruefen", hinweis="Korrektur rückgängig gemacht.")
        return redirect(
            "/pruefen", fehler="Es gibt keine Korrektur zum Rückgängigmachen."
        )

    # -- Rangliste -------------------------------------------------------

    @app.get("/rangliste", response_class=HTMLResponse)
    def rangliste(
        request: Request,
        vollbild: int = 0,
        hinweis: str | None = None,
        fehler: str | None = None,
    ) -> HTMLResponse:
        current = context(request)["current_turnier"]
        if current is None:
            return TEMPLATES.TemplateResponse(
                request=request,
                name="rangliste.html",
                context=context(
                    request,
                    durchgangsliste=[],
                    gesamt=[],
                    vollbild=bool(vollbild),
                    hinweis=hinweis,
                    error=fehler,
                ),
            )
        durchgangsliste = [
            (durchgang, service.durchgang_rangliste(durchgang.id))
            for durchgang in service.list_durchgaenge(current.id)
        ]
        return TEMPLATES.TemplateResponse(
            request=request,
            name="rangliste.html",
            context=context(
                request,
                durchgangsliste=durchgangsliste,
                gesamt=service.gesamt_rangliste(current.id),
                vollbild=bool(vollbild),
                hinweis=hinweis,
                error=fehler,
            ),
        )

    @app.get("/rangliste/export.xlsx")
    def rangliste_export() -> Response:
        current = service.last_opened_turnier()
        if current is None:
            return redirect("/rangliste", fehler="Kein Turnier ausgewählt.")
        try:
            data = service.export_xlsx(current.id)
        except Exception as exc:  # noqa: BLE001 - Exportfehler sichtbar machen
            return redirect("/rangliste", fehler=f"Export fehlgeschlagen: {exc}")
        filename = f"rangliste-{current.name}.xlsx".replace(" ", "-")
        return Response(
            content=data,
            media_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @app.post("/durchgang/{durchgang_id}/abschliessen", response_class=HTMLResponse)
    def durchgang_abschliessen(durchgang_id: int) -> RedirectResponse:
        try:
            service.close_durchgang(durchgang_id)
        except ValueError as exc:
            return redirect("/rangliste", fehler=str(exc))
        return redirect("/rangliste", hinweis="Durchgang abgeschlossen.")

    @app.post("/durchgang/{durchgang_id}/wieder-oeffnen", response_class=HTMLResponse)
    def durchgang_wieder_oeffnen(durchgang_id: int) -> RedirectResponse:
        service.reopen_durchgang(durchgang_id)
        return redirect("/rangliste", hinweis="Durchgang wieder geöffnet.")

    @app.post("/verbindung/pruefen", response_class=HTMLResponse)
    def verbindung_pruefen(
        background_tasks: BackgroundTasks,
    ) -> RedirectResponse:
        background_tasks.add_task(service.process_pending_jobs)
        return redirect("/scannen", hinweis="Verbindungsstatus aktualisiert.")

    return app
