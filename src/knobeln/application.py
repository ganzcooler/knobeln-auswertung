"""Anwendungskern für Turniere, Scans, Prüffälle und Ranglisten."""

from __future__ import annotations

import io
import uuid
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path

from openpyxl import Workbook

from .domain.models import BogenRef, Gruppe
from .domain.scan import Bogen, Durchgang, Konflikt, StoredGruppe
from .domain.turnier import Turnier
from .domain.wertung import GUELTIGE_PUNKTE, ist_gueltige_summe
from .io.input_scanner import bogen_id_for
from .io.pdf import image_to_jpeg, pdf_page_count, render_pdf_page
from .llm.client import LLMClient, LLMError, LLMJSONError, LLMLengthError
from .llm.mapping import build_neue_bogen
from .store import SQLiteStore


class DuplicateScanError(RuntimeError):
    def __init__(self, bogen: Bogen) -> None:
        super().__init__("Dieser Bogen scheint schon im Stapel zu sein.")
        self.bogen = bogen


@dataclass(frozen=True)
class Prueffall:
    id: str
    art: str
    schweregrad: int
    titel: str
    detail: str
    bogen_id: int | None = None
    gruppe_id: int | None = None
    wurf_nr: int | None = None
    konflikt_id: int | None = None


@dataclass(frozen=True)
class RanglistenZeile:
    rang: int
    spieler_nr: str
    spieler_name: str
    summe: int
    quelle: str
    status: str
    geteilter_rang: bool = False


class KnobelnService:
    def __init__(
        self,
        store: SQLiteStore,
        *,
        llm_client: LLMClient | None = None,
        scan_dir: Path | str = Path("data/scans"),
        connection_check: Callable[[], bool] | None = None,
        max_cost: float | None = None,
    ) -> None:
        self.store = store
        self.llm_client = llm_client
        self.scan_dir = Path(scan_dir)
        self.scan_dir.mkdir(parents=True, exist_ok=True)
        self.connection_check = connection_check
        self.max_cost = max_cost

    # -- Turnier und Durchgang ------------------------------------------

    def create_turnier(self, name: str) -> Turnier:
        clean_name = self._require_name(name)
        turnier = self.store.create_turnier(clean_name)
        self.store.set_last_opened(turnier.id)
        return turnier

    def list_turniere(self) -> list[Turnier]:
        return self.store.list_turniere()

    def get_turnier(self, turnier_id: int) -> Turnier:
        turnier = self.store.get_turnier(turnier_id)
        if turnier is None:
            raise LookupError(f"Turnier {turnier_id} nicht gefunden.")
        return turnier

    def rename_turnier(self, turnier_id: int, name: str) -> Turnier:
        self.get_turnier(turnier_id)
        clean_name = self._require_name(name)
        self.store.rename_turnier(turnier_id, clean_name)
        return Turnier(id=turnier_id, name=clean_name)

    def open_turnier(self, turnier_id: int) -> Turnier:
        turnier = self.get_turnier(turnier_id)
        self.store.set_last_opened(turnier_id)
        return turnier

    def last_opened_turnier(self) -> Turnier | None:
        turnier_id = self.store.get_last_opened_id()
        if turnier_id is None:
            return None
        return self.store.get_turnier(turnier_id)

    def delete_turnier(self, turnier_id: int) -> None:
        self.get_turnier(turnier_id)
        self.store.backup()
        self.store.delete_turnier(turnier_id)
        if self.store.get_last_opened_id() == turnier_id:
            self.store.clear_last_opened()

    def create_durchgang(self, turnier_id: int, nummer: int) -> Durchgang:
        self.get_turnier(turnier_id)
        if not 1 <= nummer <= 5:
            raise ValueError("Die Durchgangsnummer muss zwischen 1 und 5 liegen.")
        if self.store.get_durchgang_by_nummer(turnier_id, nummer) is not None:
            raise ValueError("Diesen Durchgang gibt es schon.")
        durchgang = self.store.create_durchgang(turnier_id, nummer)
        self.store.set_last_opened(turnier_id)
        self.store.set_last_opened_durchgang(durchgang.id)
        return durchgang

    def list_durchgaenge(self, turnier_id: int) -> list[Durchgang]:
        return self.store.list_durchgaenge(turnier_id)

    def get_durchgang(self, durchgang_id: int) -> Durchgang:
        durchgang = self.store.get_durchgang(durchgang_id)
        if durchgang is None:
            raise LookupError(f"Durchgang {durchgang_id} nicht gefunden.")
        return durchgang

    def open_durchgang(self, durchgang_id: int) -> Durchgang:
        durchgang = self.get_durchgang(durchgang_id)
        self.store.set_last_opened(durchgang.turnier_id)
        self.store.set_last_opened_durchgang(durchgang.id)
        return durchgang

    def current_durchgang(self, turnier_id: int) -> Durchgang | None:
        durchgang_id = self.store.get_last_opened_durchgang_id()
        if durchgang_id is not None:
            durchgang = self.store.get_durchgang(durchgang_id)
            if durchgang is not None and durchgang.turnier_id == turnier_id:
                return durchgang
        durchgaenge = self.store.list_durchgaenge(turnier_id)
        return durchgaenge[0] if durchgaenge else None

    def ensure_import_context(self, turnier_name: str, nummer: int = 1) -> Durchgang:
        turnier = next(
            (t for t in self.store.list_turniere() if t.name == turnier_name),
            None,
        )
        if turnier is None:
            turnier = self.create_turnier(turnier_name)
        durchgang = self.store.get_durchgang_by_nummer(turnier.id, nummer)
        if durchgang is None:
            durchgang = self.create_durchgang(turnier.id, nummer)
        return durchgang

    # -- Scan-Import und Extraktion ------------------------------------

    def import_scan(
        self,
        *,
        dateiname: str,
        data: bytes,
        durchgang_id: int,
        force: bool = False,
    ) -> list[Bogen]:
        durchgang = self._require_open_durchgang(durchgang_id)
        suffix = Path(dateiname).suffix.lower()
        if suffix not in {".jpg", ".jpeg", ".png", ".pdf"}:
            raise ValueError("Bitte JPG, PNG oder PDF ablegen.")

        pages: list[tuple[int, str, bytes]] = []
        if suffix == ".pdf":
            for page in range(1, pdf_page_count(data) + 1):
                pages.append(
                    (page, bogen_id_for(data, page), render_pdf_page(data, page))
                )
        else:
            pages.append((1, bogen_id_for(data, 1), image_to_jpeg(data)))

        for _page, bogen_id, _image in pages:
            existing = self.store.find_bogen_by_bogen_id(durchgang_id, bogen_id)
            if existing is not None and not force:
                raise DuplicateScanError(existing)

        result: list[Bogen] = []
        for page, bogen_id, image in pages:
            existing = self.store.find_bogen_by_bogen_id(durchgang_id, bogen_id)
            if existing is not None:
                bogen_id = f"{bogen_id}-kopie-{uuid.uuid4().hex[:6]}"
            path = self.scan_dir / f"{bogen_id}.jpg"
            path.write_bytes(image)
            result.append(
                self.store.create_bogen(
                    durchgang_id=durchgang.id,
                    dateiname=dateiname,
                    archiv_pfad=str(path),
                    seite=page,
                    bogen_id=bogen_id,
                )
            )
        return result

    def process_pending_jobs(self) -> int:
        if self.llm_client is None:
            return 0
        processed = 0
        spent = 0.0
        for job in self.store.list_pending_jobs():
            if self.max_cost is not None and spent > self.max_cost:
                break
            bogen = self.store.get_bogen(job.bogen_id)
            if bogen is None:
                continue
            durchgang = self.store.get_durchgang(bogen.durchgang_id)
            if durchgang is None:
                continue
            self.store.update_job(bogen.id, status="laeuft")
            self.store.set_bogen_status(bogen.id, "laeuft")
            try:
                image_bytes = Path(bogen.archiv_pfad).read_bytes()
                result = self.llm_client.extract_bogen(
                    bogen_id=bogen.bogen_id,
                    quelle=bogen.dateiname,
                    image_bytes=image_bytes,
                    mime_type="image/jpeg",
                )
                self._store_extraction(bogen, durchgang, result)
                self.store.update_job(
                    bogen.id,
                    status="fertig",
                    prompt_tokens=result.prompt_tokens,
                    completion_tokens=result.completion_tokens,
                    cost_usd=result.cost_usd,
                )
                spent += result.cost_usd
                processed += 1
            except (LLMJSONError, LLMLengthError) as exc:
                self.store.update_job(bogen.id, status="fehler", fehler=str(exc))
                self.store.set_bogen_status(bogen.id, "fehler")
            except LLMError as exc:
                self.store.update_job(bogen.id, status="warten", fehler=str(exc))
                self.store.set_bogen_status(bogen.id, "warten")
            except Exception as exc:  # noqa: BLE001 - Jobfehler sichtbar machen
                self.store.update_job(bogen.id, status="fehler", fehler=str(exc))
                self.store.set_bogen_status(bogen.id, "fehler")
        return processed

    def _store_extraction(self, bogen: Bogen, durchgang: Durchgang, result) -> None:
        neue = build_neue_bogen(
            result.bogen,
            ref=BogenRef(
                bogen_id=bogen.bogen_id,
                quelle=bogen.dateiname,
                seite=bogen.seite,
            ),
        )
        self.store.delete_groups_for_bogen(bogen.id)
        if neue.bogen_unklar:
            placeholder = Gruppe(
                ref=BogenRef(
                    bogen_id=bogen.bogen_id,
                    quelle=bogen.dateiname,
                    seite=bogen.seite,
                ),
                position=0,
                durchgang_nr=durchgang.nummer,
                spieler_nr="",
                spieler_name="",
                placeholder=True,
            )
            placeholder.recompute()
            self.store.save_gruppe(
                durchgang_id=durchgang.id,
                bogen_id=bogen.id,
                gruppe=placeholder,
                quelle="scan",
            )
            self.store.set_bogen_status(bogen.id, "bogen_unklar")
            return

        for gruppe in neue.spieler:
            if neue.durchgang_nr is not None and neue.durchgang_nr != durchgang.nummer:
                gruppe.zusatz_status.add("durchgang_unklar")
                gruppe.zusatz_warnungen.append(
                    f"Bogen nennt Durchgang {neue.durchgang_nr}; abgelegt in "
                    f"Durchgang {durchgang.nummer}."
                )
            gruppe.durchgang_nr = durchgang.nummer
            gruppe.recompute()
            self._register_scan_group(durchgang.id, bogen.id, gruppe)
        self.store.set_bogen_status(bogen.id, "fertig")

    def retry_bogen(self, bogen_id: int) -> None:
        self.store.retry_job(bogen_id)

    def list_bogen(self, durchgang_id: int) -> list[Bogen]:
        return self.store.list_bogen(durchgang_id)

    def get_bogen(self, bogen_id: int) -> Bogen:
        bogen = self.store.get_bogen(bogen_id)
        if bogen is None:
            raise LookupError(f"Bogen {bogen_id} nicht gefunden.")
        return bogen

    def get_scan_path(self, bogen_id: int) -> Path:
        return Path(self.get_bogen(bogen_id).archiv_pfad)

    def list_gruppen(self, durchgang_id: int) -> list[StoredGruppe]:
        return self.store.list_gruppen(durchgang_id)

    def list_gruppen_for_bogen(self, bogen_id: int) -> list[StoredGruppe]:
        return self.store.list_gruppen_for_bogen(bogen_id)

    def get_gruppe(self, gruppe_id: int) -> StoredGruppe:
        stored = self.store.get_gruppe(gruppe_id)
        if stored is None:
            raise LookupError(f"Gruppe {gruppe_id} nicht gefunden.")
        return stored

    def get_konflikt(self, konflikt_id: int) -> Konflikt:
        konflikt = self.store.get_konflikt(konflikt_id)
        if konflikt is None:
            raise LookupError(f"Konflikt {konflikt_id} nicht gefunden.")
        return konflikt

    # -- Gruppen und Konflikte -----------------------------------------

    def _register_scan_group(
        self, durchgang_id: int, bogen_id: int, gruppe: Gruppe
    ) -> int:
        active = [
            stored
            for stored in self.store.find_gruppen_for_player(
                durchgang_id, gruppe.spieler_nr
            )
            if stored.ergebnis_status == "aktiv"
        ]
        if not active:
            return self.store.save_gruppe(
                durchgang_id=durchgang_id,
                bogen_id=bogen_id,
                gruppe=gruppe,
                quelle="scan",
            )
        existing = active[0]
        if self._same_result(existing, gruppe):
            return existing.id
        new_id = self.store.save_gruppe(
            durchgang_id=durchgang_id,
            bogen_id=bogen_id,
            gruppe=gruppe,
            quelle="scan",
            ergebnis_status="konflikt",
        )
        self._create_conflict(existing, new_id)
        return new_id

    def create_manual_result(
        self,
        *,
        durchgang_id: int,
        spieler_nr: str,
        spieler_name: str,
        summe: int,
    ) -> StoredGruppe:
        durchgang = self._require_open_durchgang(durchgang_id)
        clean_nr = spieler_nr.strip()
        if not clean_nr:
            raise ValueError("Die Spieler-Nr. fehlt.")
        if not ist_gueltige_summe(summe):
            raise ValueError(
                "Die Summe muss zwischen 0 und 2400 liegen und durch 5 teilbar sein."
            )
        manual = Gruppe(
            ref=BogenRef(bogen_id="", quelle="manuell", seite=1),
            position=0,
            durchgang_nr=durchgang.nummer,
            spieler_nr=clean_nr,
            spieler_name=spieler_name.strip(),
            punkte=[None] * 12,
            punkte_roh=[""] * 12,
            summe_bogen=summe,
            summe_bogen_roh=str(summe),
            geprueft=True,
            statuses={"ok", "geprueft"},
        )
        active = [
            stored
            for stored in self.store.find_gruppen_for_player(durchgang_id, clean_nr)
            if stored.ergebnis_status == "aktiv"
        ]
        if any(stored.quelle != "manuell" for stored in active):
            raise ValueError(
                "Für diesen Spieler gibt es schon ein gescanntes Ergebnis. "
                "Bitte den Bogen prüfen."
            )
        if active and self._same_result(active[0], manual):
            return active[0]
        status = "aktiv" if not active else "konflikt"
        manual_id = self.store.save_gruppe(
            durchgang_id=durchgang_id,
            bogen_id=None,
            gruppe=manual,
            quelle="manuell",
            ergebnis_status=status,
        )
        if active:
            self._create_conflict(active[0], manual_id)
        stored = self.store.get_gruppe(manual_id)
        if stored is None:
            raise RuntimeError("Manuelles Ergebnis konnte nicht gespeichert werden.")
        return stored

    def _create_conflict(self, existing: StoredGruppe, new_id: int) -> Konflikt:
        new = self.store.get_gruppe(new_id)
        if new is None:
            raise RuntimeError("Konfliktgruppe nicht gefunden.")
        detail = self._diff_detail(existing, new)
        konflikt = self.store.create_konflikt(
            durchgang_id=existing.durchgang_id,
            spieler_nr=existing.gruppe.spieler_nr,
            gruppe_a_id=existing.id,
            gruppe_b_id=new.id,
        )
        for stored in (existing, new):
            stored.ergebnis_status = "konflikt"
            stored.konflikt_id = konflikt.id
            stored.gruppe.konflikt = True
            stored.gruppe.konflikt_art = "daten"
            stored.gruppe.konflikt_detail = detail
            self.store.update_gruppe(stored)
        return konflikt

    def konflikt_entscheiden(self, konflikt_id: int, gruppe_id: int) -> None:
        konflikt = self.store.get_konflikt(konflikt_id)
        if konflikt is None:
            raise LookupError("Konflikt nicht gefunden.")
        if gruppe_id not in {konflikt.gruppe_a_id, konflikt.gruppe_b_id}:
            raise ValueError("Diese Erfassung gehört nicht zum Konflikt.")
        for stored_id in (konflikt.gruppe_a_id, konflikt.gruppe_b_id):
            status = "aktiv" if stored_id == gruppe_id else "verworfen"
            self.store.set_gruppe_ergebnis_status(stored_id, status, konflikt_id=None)
        self.store.update_konflikt(
            konflikt_id, status="entschieden", gewaehlt_gruppe_id=gruppe_id
        )

    # -- Prüffälle und Entscheidungen ----------------------------------

    def list_prueffaelle(self, durchgang_id: int) -> list[Prueffall]:
        faelle: list[Prueffall] = []
        for konflikt in self.store.list_offene_konflikte(durchgang_id):
            faelle.append(
                Prueffall(
                    id=f"k{konflikt.id}",
                    art="konflikt",
                    schweregrad=4,
                    titel=f"Konflikt bei Spieler {konflikt.spieler_nr}",
                    detail="Zwei Erfassungen mit unterschiedlichen Ergebnissen.",
                    konflikt_id=konflikt.id,
                )
            )
        for stored in self.store.list_gruppen(durchgang_id):
            if stored.quelle == "manuell" or stored.ergebnis_status == "verworfen":
                continue
            if stored.gruppe.geprueft:
                continue
            statuses = stored.gruppe.statuses - {"ok", "geprueft"}
            if not statuses:
                continue
            gruppe = stored.gruppe
            if "bogen_unklar" in statuses:
                faelle.append(
                    Prueffall(
                        id=f"g{stored.id}-bogen",
                        art="bogen_unklar",
                        schweregrad=6,
                        titel="Bogen unklar",
                        detail=gruppe.warnung_text
                        or "Bogen konnte nicht gelesen werden.",
                        bogen_id=stored.bogen_id,
                        gruppe_id=stored.id,
                    )
                )
                continue
            if "durchgang_unklar" in statuses or "spieler_unklar" in statuses:
                faelle.append(
                    Prueffall(
                        id=f"g{stored.id}-kopf",
                        art="kopfzeile",
                        schweregrad=5,
                        titel="Kopfzeile unklar",
                        detail=gruppe.warnung_text,
                        bogen_id=stored.bogen_id,
                        gruppe_id=stored.id,
                    )
                )
            for index, punkt in enumerate(gruppe.punkte):
                wurf_nr = index + 1
                kommentar = gruppe.kommentare[index]
                if kommentar.startswith(
                    (
                        "Korrigiert:",
                        "Als unleserlich markiert.",
                        "Vorschlag übernommen.",
                    )
                ):
                    continue
                if punkt is None:
                    art = (
                        "wert_fehlt"
                        if not gruppe.punkte_roh[index].strip()
                        else "wert_ungueltig"
                    )
                    faelle.append(
                        Prueffall(
                            id=f"g{stored.id}-w{wurf_nr}-{art}",
                            art=art,
                            schweregrad=3 if art == "wert_fehlt" else 2,
                            titel=(
                                "Fehlender Wert"
                                if art == "wert_fehlt"
                                else "Unzulässiger Wert"
                            ),
                            detail=(
                                f"Spieler {gruppe.spieler_nr or '?'}, Wurf {wurf_nr}: "
                                f"{gruppe.punkte_roh[index] or 'leer'}"
                            ),
                            bogen_id=stored.bogen_id,
                            gruppe_id=stored.id,
                            wurf_nr=wurf_nr,
                        )
                    )
                elif gruppe.korrekturen[index]:
                    faelle.append(
                        Prueffall(
                            id=f"g{stored.id}-w{wurf_nr}-korrektur",
                            art="wert_korrigiert",
                            schweregrad=3,
                            titel="Unklare Ziffer",
                            detail=f"Wurf {wurf_nr}: {gruppe.korrekturen[index]}",
                            bogen_id=stored.bogen_id,
                            gruppe_id=stored.id,
                            wurf_nr=wurf_nr,
                        )
                    )
                elif gruppe.llm_hinweise[index]:
                    faelle.append(
                        Prueffall(
                            id=f"g{stored.id}-w{wurf_nr}-hinweis",
                            art="unklare_ziffer",
                            schweregrad=3,
                            titel="Unklare Ziffer",
                            detail=f"Wurf {wurf_nr}: {gruppe.llm_hinweise[index]}",
                            bogen_id=stored.bogen_id,
                            gruppe_id=stored.id,
                            wurf_nr=wurf_nr,
                        )
                    )
            if "summe_abweichung" in statuses:
                faelle.append(
                    Prueffall(
                        id=f"g{stored.id}-summe",
                        art="summe",
                        schweregrad=1,
                        titel="Summe stimmt nicht",
                        detail=(
                            f"Spieler {gruppe.spieler_nr or '?'}: "
                            f"{gruppe.summe_bogen} geschrieben, "
                            f"{gruppe.summe_berechnet} berechnet "
                            f"(Delta {gruppe.delta:+d})."
                            if gruppe.summe_bogen is not None
                            and gruppe.summe_berechnet is not None
                            and gruppe.delta is not None
                            else gruppe.warnung_text
                        ),
                        bogen_id=stored.bogen_id,
                        gruppe_id=stored.id,
                    )
                )
        return sorted(faelle, key=lambda fall: (fall.schweregrad, fall.id))

    def get_prueffall(self, durchgang_id: int, fall_id: str) -> Prueffall | None:
        return next(
            (
                fall
                for fall in self.list_prueffaelle(durchgang_id)
                if fall.id == fall_id
            ),
            None,
        )

    def korrigiere_wert(self, gruppe_id: int, wurf_nr: int, punkte: int) -> None:
        stored = self._require_scan_group(gruppe_id)
        if not 1 <= wurf_nr <= 12:
            raise ValueError("Wurf-Nr. muss zwischen 1 und 12 liegen.")
        if punkte not in GUELTIGE_PUNKTE:
            raise ValueError("Dieser Wert steht nicht in der Wertung.")
        index = wurf_nr - 1
        self._remember_undo(stored, index)
        alt = stored.gruppe.punkte[index]
        stored.gruppe.punkte[index] = punkte
        if alt != punkte:
            roh = stored.gruppe.punkte_roh[index] or "leer"
            self._append_kommentar(stored, index, f"Korrigiert: {roh} -> {punkte}")
        stored.gruppe.korrekturen[index] = None
        stored.gruppe.llm_hinweise[index] = None
        stored.gruppe.recompute()
        self.store.update_gruppe(stored)

    def uebernehme_wert(self, gruppe_id: int, wurf_nr: int) -> None:
        stored = self._require_scan_group(gruppe_id)
        index = wurf_nr - 1
        if stored.gruppe.punkte[index] is None:
            raise ValueError("Es gibt keinen gültigen Vorschlag zum Übernehmen.")
        self._remember_undo(stored, index)
        stored.gruppe.korrekturen[index] = None
        stored.gruppe.llm_hinweise[index] = None
        self._append_kommentar(stored, index, "Vorschlag übernommen.")
        stored.gruppe.recompute()
        self.store.update_gruppe(stored)

    def markiere_unleserlich(self, gruppe_id: int, wurf_nr: int) -> None:
        stored = self._require_scan_group(gruppe_id)
        index = wurf_nr - 1
        self._remember_undo(stored, index)
        stored.gruppe.punkte[index] = None
        stored.gruppe.korrekturen[index] = None
        stored.gruppe.llm_hinweise[index] = None
        self._append_kommentar(stored, index, "Als unleserlich markiert.")
        stored.gruppe.recompute()
        self.store.update_gruppe(stored)

    def update_manual_result(
        self,
        gruppe_id: int,
        *,
        summe: int,
        spieler_name: str,
    ) -> StoredGruppe:
        stored = self.get_gruppe(gruppe_id)
        if stored.quelle != "manuell":
            raise ValueError("Nur manuelle Ergebnisse können hier bearbeitet werden.")
        if stored.ergebnis_status != "aktiv" or stored.konflikt_id is not None:
            raise ValueError(
                "Diese Erfassung ist Teil eines offenen Konflikts und kann hier "
                "nicht bearbeitet werden."
            )
        durchgang = self.get_durchgang(stored.durchgang_id)
        if durchgang.status == "abgeschlossen":
            raise ValueError("Dieser Durchgang ist abgeschlossen.")
        if not ist_gueltige_summe(summe):
            raise ValueError(
                "Die Summe muss zwischen 0 und 2400 liegen und durch 5 teilbar sein."
            )
        stored.gruppe.summe_bogen = summe
        stored.gruppe.summe_bogen_roh = str(summe)
        stored.gruppe.spieler_name = spieler_name.strip()
        stored.gruppe.statuses = {"ok", "geprueft"}
        self.store.update_gruppe(stored)
        return stored

    def has_undo(self) -> bool:
        return self.store.get_undo() is not None

    def undo_letzte_korrektur(self) -> bool:
        data = self.store.get_undo()
        if data is None:
            return False
        try:
            stored = self.store.get_gruppe(int(str(data["gruppe_id"])))
            wurf_nr = int(str(data["wurf_nr"]))
        except (KeyError, TypeError, ValueError):
            self.store.clear_undo()
            return False
        if stored is None or not 1 <= wurf_nr <= 12:
            self.store.clear_undo()
            return False
        index = wurf_nr - 1
        stored.gruppe.punkte[index] = _optional_int(data.get("punkt"))
        stored.gruppe.kommentare[index] = str(data.get("kommentar") or "")
        stored.gruppe.korrekturen[index] = _optional_str(data.get("korrektur"))
        stored.gruppe.llm_hinweise[index] = _optional_str(data.get("hinweis"))
        stored.gruppe.recompute()
        self.store.update_gruppe(stored)
        self.store.clear_undo()
        return True

    @staticmethod
    def _append_kommentar(stored: StoredGruppe, index: int, note: str) -> None:
        vorhanden = stored.gruppe.kommentare[index].strip()
        stored.gruppe.kommentare[index] = f"{vorhanden} | {note}" if vorhanden else note

    def _remember_undo(self, stored: StoredGruppe, index: int) -> None:
        self.store.set_undo(
            {
                "gruppe_id": stored.id,
                "wurf_nr": index + 1,
                "punkt": stored.gruppe.punkte[index],
                "kommentar": stored.gruppe.kommentare[index],
                "korrektur": stored.gruppe.korrekturen[index],
                "hinweis": stored.gruppe.llm_hinweise[index],
            }
        )

    def summe_akzeptieren(self, gruppe_id: int) -> None:
        stored = self._require_scan_group(gruppe_id)
        stored.gruppe.geprueft = True
        stored.gruppe.recompute()
        self.store.update_gruppe(stored)

    def bogen_bestaetigen(self, bogen_id: int) -> None:
        groups = self.store.list_gruppen_for_bogen(bogen_id)
        if not groups:
            raise LookupError("Bogen nicht gefunden.")
        durchgang_id = groups[0].durchgang_id
        gruppen_ids = {stored.id for stored in groups}
        blocker = [
            fall
            for fall in self.list_prueffaelle(durchgang_id)
            if fall.bogen_id == bogen_id
        ]
        for konflikt in self.store.list_offene_konflikte(durchgang_id):
            if {konflikt.gruppe_a_id, konflikt.gruppe_b_id} & gruppen_ids:
                blocker.append(
                    Prueffall(
                        id=f"k{konflikt.id}",
                        art="konflikt",
                        schweregrad=4,
                        titel=f"Konflikt bei Spieler {konflikt.spieler_nr}",
                        detail="Zuerst den Konflikt entscheiden.",
                        konflikt_id=konflikt.id,
                    )
                )
        if blocker:
            raise ValueError(
                f"Es sind noch {len(blocker)} Prüffälle auf diesem Bogen offen."
            )
        for stored in groups:
            stored.gruppe.geprueft = True
            stored.gruppe.recompute()
            self.store.update_gruppe(stored)

    def close_durchgang(self, durchgang_id: int) -> None:
        offen = self.list_prueffaelle(durchgang_id)
        if offen:
            raise ValueError(
                "Durchgang kann nicht abgeschlossen werden: "
                f"{len(offen)} offene Prüffälle."
            )
        self.store.set_durchgang_status(durchgang_id, "abgeschlossen")

    def reopen_durchgang(self, durchgang_id: int) -> None:
        self.store.backup()
        self.store.set_durchgang_status(durchgang_id, "offen")

    # -- Rangliste und Export ------------------------------------------

    def durchgang_rangliste(self, durchgang_id: int) -> list[RanglistenZeile]:
        durchgang = self.get_durchgang(durchgang_id)
        rows = self._rangliste_rows(
            [
                stored
                for stored in self.store.list_gruppen(durchgang_id)
                if stored.ergebnis_status == "aktiv"
            ]
        )
        status = "bestätigt" if durchgang.status == "abgeschlossen" else "vorläufig"
        return [
            RanglistenZeile(
                rang=row.rang,
                spieler_nr=row.spieler_nr,
                spieler_name=row.spieler_name,
                summe=row.summe,
                quelle=row.quelle,
                status=status,
                geteilter_rang=row.geteilter_rang,
            )
            for row in rows
        ]

    def gesamt_rangliste(self, turnier_id: int) -> list[RanglistenZeile]:
        durchgaenge = self.store.list_durchgaenge(turnier_id)
        gruppen = [
            stored
            for stored in self.store.list_gruppen_for_turnier(turnier_id)
            if stored.ergebnis_status == "aktiv"
        ]
        sums: dict[str, int] = {}
        names: dict[str, str] = {}
        quellen: dict[str, set[str]] = {}
        for stored in gruppen:
            wert = self._result_sum(stored)
            if wert is None:
                continue
            key = stored.gruppe.spieler_nr
            sums[key] = sums.get(key, 0) + wert
            if stored.gruppe.spieler_name and key not in names:
                names[key] = stored.gruppe.spieler_name
            quellen.setdefault(key, set()).add(
                "manuell" if stored.quelle == "manuell" else "gescannt"
            )
        status = (
            "bestätigt"
            if durchgaenge and all(d.status == "abgeschlossen" for d in durchgaenge)
            else "vorläufig"
        )
        rows = sorted(sums.items(), key=lambda item: (-item[1], item[0]))
        result: list[RanglistenZeile] = []
        previous_sum: int | None = None
        previous_rank = 0
        for index, (spieler_nr, summe) in enumerate(rows, start=1):
            rang = previous_rank if summe == previous_sum else index
            quelle_set = quellen.get(spieler_nr, set())
            result.append(
                RanglistenZeile(
                    rang=rang,
                    spieler_nr=spieler_nr,
                    spieler_name=names.get(spieler_nr, ""),
                    summe=summe,
                    quelle=(
                        "gemischt"
                        if len(quelle_set) > 1
                        else next(iter(quelle_set), "gescannt")
                    ),
                    status=status,
                )
            )
            previous_sum = summe
            previous_rank = rang
        return self._mark_ties(result)

    def _rangliste_rows(self, gruppen: list[StoredGruppe]) -> list[RanglistenZeile]:
        values: dict[str, tuple[int, str, str]] = {}
        for stored in gruppen:
            wert = self._result_sum(stored)
            if wert is None:
                continue
            key = stored.gruppe.spieler_nr
            if key not in values:
                values[key] = (
                    wert,
                    stored.gruppe.spieler_name,
                    "manuell" if stored.quelle == "manuell" else "gescannt",
                )
        rows = sorted(values.items(), key=lambda item: (-item[1][0], item[0]))
        result: list[RanglistenZeile] = []
        previous_sum: int | None = None
        previous_rank = 0
        for index, (spieler_nr, (summe, name, quelle)) in enumerate(rows, start=1):
            rang = previous_rank if summe == previous_sum else index
            result.append(
                RanglistenZeile(
                    rang=rang,
                    spieler_nr=spieler_nr,
                    spieler_name=name,
                    summe=summe,
                    quelle=quelle,
                    status="",
                )
            )
            previous_sum = summe
            previous_rank = rang
        return self._mark_ties(result)

    @staticmethod
    def _mark_ties(rows: list[RanglistenZeile]) -> list[RanglistenZeile]:
        zaehler: dict[int, int] = {}
        for row in rows:
            zaehler[row.summe] = zaehler.get(row.summe, 0) + 1
        return [
            replace(row, geteilter_rang=zaehler[row.summe] > 1)
            if zaehler[row.summe] > 1
            else row
            for row in rows
        ]

    def export_xlsx(self, turnier_id: int) -> bytes:
        self.get_turnier(turnier_id)
        workbook = Workbook()
        default_sheet = workbook.active
        if default_sheet is not None:
            workbook.remove(default_sheet)
        for durchgang in self.store.list_durchgaenge(turnier_id):
            worksheet = workbook.create_sheet(f"Durchgang {durchgang.nummer}")
            self._write_rangliste(worksheet, self.durchgang_rangliste(durchgang.id))
        gesamt = workbook.create_sheet("Gesamt")
        self._write_rangliste(gesamt, self.gesamt_rangliste(turnier_id))
        stream = io.BytesIO()
        workbook.save(stream)
        workbook.close()
        return stream.getvalue()

    @staticmethod
    def _write_rangliste(worksheet, rows: list[RanglistenZeile]) -> None:
        worksheet.append(["Rang", "Spieler-Nr.", "Name", "Summe", "Quelle", "Status"])
        for row in rows:
            worksheet.append(
                [
                    row.rang,
                    row.spieler_nr,
                    row.spieler_name,
                    row.summe,
                    row.quelle,
                    row.status,
                ]
            )

    # -- Verbindung und Hilfen -----------------------------------------

    def connection_status(self) -> str:
        if self.connection_check is not None:
            return "erreichbar" if self.connection_check() else "nicht erreichbar"
        return "erreichbar" if self.llm_client is not None else "nicht erreichbar"

    def _require_open_durchgang(self, durchgang_id: int) -> Durchgang:
        durchgang = self.get_durchgang(durchgang_id)
        if durchgang.status == "abgeschlossen":
            raise ValueError("Dieser Durchgang ist abgeschlossen.")
        return durchgang

    def _require_scan_group(self, gruppe_id: int) -> StoredGruppe:
        stored = self.store.get_gruppe(gruppe_id)
        if stored is None:
            raise LookupError("Gruppe nicht gefunden.")
        if stored.quelle == "manuell":
            raise ValueError(
                "Manuelle Ergebnisse werden nicht über die Prüfansicht bearbeitet."
            )
        return stored

    @staticmethod
    def _result_sum(stored: StoredGruppe) -> int | None:
        if stored.quelle == "manuell":
            return stored.gruppe.summe_bogen
        if all(
            punkt is not None and punkt in GUELTIGE_PUNKTE
            for punkt in stored.gruppe.punkte
        ):
            return sum(punkt for punkt in stored.gruppe.punkte if punkt is not None)
        return None

    def _same_result(self, existing: StoredGruppe, incoming: Gruppe) -> bool:
        existing_sum = self._result_sum(existing)
        incoming_sum = (
            sum(punkt for punkt in incoming.punkte if punkt is not None)
            if all(
                punkt is not None and punkt in GUELTIGE_PUNKTE
                for punkt in incoming.punkte
            )
            else incoming.summe_bogen
        )
        return existing_sum is not None and existing_sum == incoming_sum

    @staticmethod
    def _diff_detail(existing: StoredGruppe, new: StoredGruppe) -> str:
        parts: list[str] = []
        for index, (alt, neu) in enumerate(
            zip(existing.gruppe.punkte, new.gruppe.punkte, strict=True), start=1
        ):
            if alt != neu:
                parts.append(
                    f"W{index:02d}: bestehend {alt if alt is not None else 'leer'}, "
                    f"neu {neu if neu is not None else 'leer'}"
                )
        if existing.gruppe.summe_bogen != new.gruppe.summe_bogen:
            alt_summe = existing.gruppe.summe_bogen
            neu_summe = new.gruppe.summe_bogen
            parts.append(
                "Summe: bestehend "
                f"{alt_summe if alt_summe is not None else 'leer'}, "
                "neu "
                f"{neu_summe if neu_summe is not None else 'leer'}"
            )
        return "; ".join(parts) or "abweichende Werte"

    @staticmethod
    def _require_name(name: str) -> str:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Der Turniername darf nicht leer sein.")
        return clean_name


def _optional_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _optional_str(value: object) -> str | None:
    if value is None or value == "":
        return None
    return str(value)
