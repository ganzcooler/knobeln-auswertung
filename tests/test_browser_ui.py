"""Echte Headless-Browser-Tests für die lokale Web-UI."""

from __future__ import annotations

import copy
import socket
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest
import uvicorn
from conftest import FAKE_RESPONSES, FakeLLMClient
from playwright.sync_api import Browser, Page, expect, sync_playwright

from knobeln.application import KnobelnService
from knobeln.store import SQLiteStore
from knobeln.web.app import create_app

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"

pytestmark = pytest.mark.browser


@pytest.fixture(scope="session")
def browser() -> Iterator[Browser]:
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch()
        except Exception as exc:  # noqa: BLE001 - Umgebungsfehler klar melden
            pytest.skip(
                "Chromium konnte nicht gestartet werden. "
                "Bitte `uv run playwright install chromium` und ggf. "
                f"`uv run playwright install-deps chromium` ausführen: {exc}"
            )
        yield browser
        browser.close()


@pytest.fixture
def page(browser: Browser) -> Iterator[Page]:
    context = browser.new_context(viewport={"width": 1280, "height": 900})
    page = context.new_page()
    page.set_default_timeout(15_000)
    yield page
    context.close()


@contextmanager
def live_server(
    tmp_path: Path,
    *,
    responses: dict | None = None,
    with_llm: bool = True,
) -> Iterator[tuple[KnobelnService, str]]:
    service = KnobelnService(
        SQLiteStore(tmp_path / "knobeln.db"),
        llm_client=FakeLLMClient(responses) if with_llm else None,
        scan_dir=tmp_path / "scans",
    )
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    server = uvicorn.Server(
        uvicorn.Config(
            create_app(service),
            host="127.0.0.1",
            port=port,
            log_level="warning",
        )
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 5
    while not server.started and time.monotonic() < deadline:
        time.sleep(0.05)
    if not server.started:
        raise RuntimeError("Testserver ist nicht gestartet.")
    try:
        yield service, f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        thread.join(timeout=5)


def _create_turnier_und_durchgang(page: Page, base_url: str, nummer: int = 1):
    page.goto(f"{base_url}/scannen")
    page.locator("#name-neu").fill("Browser-Turnier")
    page.get_by_role("button", name="Turnier anlegen").click()
    expect(page.get_by_text("Aktuelles Turnier: Browser-Turnier")).to_be_visible()
    if page.locator("#nummer").count():
        page.locator("#nummer").select_option(str(nummer))
        page.get_by_role("button", name="Durchgang anlegen").click()
    expect(page.get_by_role("heading", name=f"Durchgang {nummer}")).to_be_visible()


def _upload(
    page: Page,
    name: str,
    *,
    force: bool = False,
    path: Path | None = None,
    data: bytes | None = None,
):
    if data is not None:
        page.locator("#dateien").set_input_files(
            {"name": name, "mimeType": "image/jpeg", "buffer": data}
        )
    else:
        page.locator("#dateien").set_input_files(str(path or EXAMPLES / name))
    if force:
        page.locator("input[name=force]").check()
    page.get_by_role("button", name="Dateien auswählen").click()


def test_browser_scan_htmx_und_pruefen(page: Page, tmp_path: Path):
    page.set_default_timeout(15_000)
    with live_server(tmp_path) as (_service, url):
        _create_turnier_und_durchgang(page, url, nummer=3)
        _upload(page, "img2.jpg")

        expect(page.get_by_text("fertig", exact=True)).to_be_visible(timeout=15_000)
        page.wait_for_load_state("networkidle")
        page.get_by_role("link", name="Weiter zum Prüfen (1)").click()
        expect(page.get_by_text("Summe stimmt nicht")).to_be_visible()
        expect(page.get_by_text("Zoom umschalten")).to_be_visible()

        page.get_by_role("button", name="Summenabweichung akzeptieren").click()

        expect(page.get_by_text("Gespeichert.")).to_be_visible()
        expect(page.get_by_text("Alles geprüft. Keine offenen Fälle.")).to_be_visible()


def test_browser_manuell_rangliste_und_download(page: Page, tmp_path: Path):
    page.set_default_timeout(15_000)
    with live_server(tmp_path, with_llm=False) as (_service, url):
        _create_turnier_und_durchgang(page, url)

        page.locator("#manuell-nr").fill("1")
        page.locator("#manuell-summe").fill("500")
        page.get_by_role("button", name="Manuell speichern").click()
        expect(page.get_by_text("Manuelles Ergebnis gespeichert.")).to_be_visible()

        page.locator("#manuell-nr").fill("2")
        page.locator("#manuell-summe").fill("500")
        page.get_by_role("button", name="Manuell speichern").click()
        expect(page.get_by_text("Manuelles Ergebnis gespeichert.")).to_be_visible()

        page.locator("nav.tabs").get_by_role("link", name="Rangliste").click()
        expect(page.get_by_text("geteilter Rang").first).to_be_visible()
        expect(page.get_by_text("Aktuelles Turnier: Browser-Turnier")).to_be_visible()

        page.get_by_role("link", name="Vollbild").click()
        expect(page.get_by_role("link", name="Vollbild beenden")).to_be_visible()

        with page.expect_download() as download_info:
            page.get_by_role("link", name="XLSX exportieren").click()
        download = download_info.value
        assert download.suggested_filename.endswith(".xlsx")


def test_browser_hilfe_tastatur_und_turnier_loeschen(page: Page, tmp_path: Path):
    page.set_default_timeout(15_000)
    with live_server(tmp_path, with_llm=False) as (_service, url):
        _create_turnier_und_durchgang(page, url)

        page.get_by_role("button", name="Hilfe").click()
        dialog = page.get_by_role("dialog")
        expect(dialog).to_be_visible()
        expect(dialog.get_by_text("So funktioniert es")).to_be_visible()
        page.keyboard.press("Escape")
        expect(dialog).to_be_hidden()

        page.locator("body").click(position={"x": 5, "y": 5})
        page.keyboard.press("?")
        expect(dialog).to_be_visible()
        page.keyboard.press("Escape")

        page.get_by_role("link", name="Löschen").click()
        expect(page.get_by_text("Wirklich löschen?")).to_be_visible()
        page.get_by_role("link", name="Abbrechen").click()
        expect(page.get_by_text("Aktuelles Turnier: Browser-Turnier")).to_be_visible()


def test_browser_konflikt_ansicht(page: Page, tmp_path: Path):
    responses = copy.deepcopy(FAKE_RESPONSES)
    responses["img1-kopie.jpg"] = copy.deepcopy(FAKE_RESPONSES["img1.jpg"])
    responses["img1-kopie.jpg"]["spieler"][0]["wurf_zeilen"][0]["punkte"] = 100
    responses["img1-kopie.jpg"]["spieler"][0]["wurf_zeilen"][0]["roh"] = "100"
    page.set_default_timeout(15_000)
    with live_server(tmp_path, responses=responses) as (_service, url):
        _create_turnier_und_durchgang(page, url, nummer=2)
        _upload(page, "img1.jpg")
        expect(page.get_by_text("fertig", exact=True)).to_be_visible(timeout=15_000)
        _upload(
            page,
            "img1-kopie.jpg",
            force=True,
            data=(EXAMPLES / "img1.jpg").read_bytes(),
        )
        expect(page.get_by_text("2 von 2 Bögen gelesen")).to_be_visible(timeout=15_000)
        page.wait_for_load_state("networkidle")

        page.locator("nav.tabs").get_by_role("link", name="Prüfen").click()
        page.locator(".queue-item", has_text="Konflikt bei Spieler 41").click()
        expect(page.get_by_text("Diese Erfassung gilt").first).to_be_visible()
        page.get_by_role("button", name="Diese Erfassung gilt").first.click()
        expect(page.get_by_text("Gespeichert.")).to_be_visible()


def test_browser_kompletter_abend_ueber_zwei_durchgaenge(page: Page, tmp_path: Path):
    page.set_default_timeout(20_000)
    with live_server(tmp_path) as (_service, url):
        _create_turnier_und_durchgang(page, url, nummer=2)
        _upload(page, "img1.jpg")
        expect(page.get_by_text("fertig", exact=True)).to_be_visible(timeout=20_000)
        page.wait_for_load_state("networkidle")
        page.get_by_role("button", name="Bogen bestätigen").click()
        expect(page.get_by_text("Bogen bestätigt.")).to_be_visible()

        page.locator("#manuell-nr").fill("99")
        page.locator("#manuell-summe").fill("500")
        page.get_by_role("button", name="Manuell speichern").click()
        expect(page.get_by_text("Manuelles Ergebnis gespeichert.")).to_be_visible()

        page.locator("nav.tabs").get_by_role("link", name="Rangliste").click()
        page.get_by_role("button", name="Durchgang 2 abschließen").click()
        expect(page.get_by_text("Bestätigt").first).to_be_visible()
        expect(page.get_by_role("heading", name="Durchgang 2")).to_be_visible()

        page.locator("nav.tabs").get_by_role("link", name="Scannen").click()
        page.locator("#weiterer-durchgang").select_option("3")
        page.get_by_role("button", name="Durchgang anlegen").click()
        expect(page.get_by_role("heading", name="Durchgang 3")).to_be_visible()

        _upload(page, "img2.jpg")
        expect(page.get_by_text("fertig", exact=True)).to_be_visible(timeout=20_000)
        page.wait_for_load_state("networkidle")
        page.locator("nav.tabs").get_by_role("link", name="Prüfen").click()
        expect(page.get_by_text("Summe stimmt nicht")).to_be_visible()
        page.get_by_role("button", name="Summenabweichung akzeptieren").click()
        expect(page.get_by_text("Gespeichert.")).to_be_visible()

        page.locator("nav.tabs").get_by_role("link", name="Rangliste").click()
        expect(page.get_by_text("Vorläufig").first).to_be_visible()
        page.get_by_role("button", name="Durchgang 3 abschließen").click()
        expect(page.get_by_text("Bestätigt").first).to_be_visible()
        expect(page.get_by_text("985", exact=True).first).to_be_visible()
        expect(page.get_by_text("755", exact=True).first).to_be_visible()
        expect(page.get_by_text("500", exact=True).first).to_be_visible()

        with page.expect_download() as download_info:
            page.get_by_role("link", name="XLSX exportieren").click()
        assert download_info.value.suggested_filename.endswith(".xlsx")


def test_browser_offline_und_wieder_verbunden(page: Page, tmp_path: Path):
    page.set_default_timeout(20_000)
    with live_server(tmp_path, with_llm=False) as (service, url):
        _create_turnier_und_durchgang(page, url, nummer=2)
        _upload(page, "img1.jpg")
        expect(page.get_by_text("warten", exact=True)).to_be_visible()
        expect(
            page.get_by_text("Der Dienst ist gerade nicht erreichbar")
        ).to_be_visible()

        page.locator("#manuell-nr").fill("99")
        page.locator("#manuell-summe").fill("500")
        page.get_by_role("button", name="Manuell speichern").click()
        expect(page.get_by_text("Manuelles Ergebnis gespeichert.")).to_be_visible()
        page.locator("nav.tabs").get_by_role("link", name="Rangliste").click()
        expect(page.get_by_text("500", exact=True).first).to_be_visible()

        page.locator("nav.tabs").get_by_role("link", name="Scannen").click()
        service.llm_client = FakeLLMClient()
        page.get_by_role("button", name="Erneut prüfen").click()
        expect(page.get_by_text("fertig", exact=True)).to_be_visible(timeout=20_000)
        expect(
            page.get_by_text("Der Dienst ist gerade nicht erreichbar")
        ).to_be_hidden()


def test_browser_tablet_layout_und_fokusgroesse(page: Page, tmp_path: Path):
    page.set_default_timeout(15_000)
    page.set_viewport_size({"width": 800, "height": 1000})
    with live_server(tmp_path, with_llm=False) as (_service, url):
        _create_turnier_und_durchgang(page, url)
        page.locator("#manuell-nr").fill("1")
        page.locator("#manuell-summe").fill("500")
        page.get_by_role("button", name="Manuell speichern").click()
        page.locator("nav.tabs").get_by_role("link", name="Prüfen").click()

        hilfe = page.get_by_role("button", name="Hilfe")
        box = hilfe.bounding_box()
        assert box is not None
        assert box["height"] >= 44

        page.locator("nav.tabs").get_by_role("link", name="Rangliste").click()
        expect(page.get_by_role("heading", name="Gesamt")).to_be_visible()
