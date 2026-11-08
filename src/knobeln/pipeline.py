"""Orchestrierung: Eingang -> LLM -> Validierung -> Merge -> CSV -> Aufräumen."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

from .config import Config
from .domain.merge import merge_gruppen
from .domain.models import BogenRef, Gruppe
from .domain.validation import apply_identity_checks, gruppen_nach_bogen, offene_gruppen
from .io.cleanup import (
    CleanupReport,
    FileResult,
    execute_actions,
    plan_actions,
)
from .io.csv_store import CSV_COLUMNS, CSVWriteError, load_groups, write_groups
from .io.input_scanner import (
    InputFile,
    bogen_ids_for,
    scan_input,
)
from .io.pdf import image_to_jpeg, render_pdf_page
from .llm.client import LLMClient
from .llm.mapping import build_neue_bogen


class PipelineError(RuntimeError):
    pass


@dataclass
class FileCost:
    quelle: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    cost_usd: float = 0.0
    cached: bool = False


@dataclass
class RunSummary:
    files_total: int = 0
    files_processed: int = 0
    files_skipped: int = 0
    pages_processed: int = 0
    new_groups: int = 0
    duplicates: int = 0
    conflicts: int = 0
    open_groups: int = 0
    unreadable: int = 0
    deleted: int = 0
    moved: int = 0
    kept: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    cost_usd: float = 0.0
    cache_hits: int = 0
    technical_errors: int = 0
    unsupported: int = 0
    cleanup_failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    file_costs: list[FileCost] = field(default_factory=list)

    @property
    def needs_attention(self) -> bool:
        return bool(
            self.open_groups
            or self.technical_errors
            or self.unsupported
            or self.cleanup_failures
        )

    @property
    def exit_code(self) -> int:
        return 2 if self.needs_attention else 0


class Pipeline:
    def __init__(
        self,
        config: Config,
        client: LLMClient,
        *,
        log: Callable[[str], None] | None = None,
    ) -> None:
        self.config = config
        self.client = client
        self.log = log or (lambda _msg: None)
        self.summary = RunSummary()

    def run(self) -> RunSummary:
        self._prepare()
        if self.config.reset:
            existing_groups, fieldnames = [], list(CSV_COLUMNS)
        else:
            existing_groups, fieldnames = load_groups(self.config.output_csv)
        scan = scan_input(self.config.input_dir)
        self.summary.files_total = len(scan.files)

        if self.config.verbose:
            for path in scan.hidden:
                self.log(f"ignoriert (versteckt): {path}")
            for path in scan.unsupported:
                self.log(f"nicht unterstützt: {path}")

        known_bogen_ids = {gruppe.bogen_id for gruppe in existing_groups}
        processed_this_run: set[str] = set()
        incoming: list[Gruppe] = []
        file_results: list[FileResult] = []

        for input_file in scan.files:
            file_result, new_groups = self._process_file(
                input_file,
                known_bogen_ids=known_bogen_ids,
                processed_this_run=processed_this_run,
            )
            file_results.append(file_result)
            incoming.extend(new_groups)

        for path in scan.unsupported:
            relative = path.relative_to(self.config.input_dir)
            file_results.append(
                FileResult(
                    path=path,
                    relative=relative,
                    bogen_ids=[],
                    unsupported=True,
                    error="nicht unterstützt",
                )
            )
            self.summary.unsupported += 1
            self.summary.warnings.append(f"Nicht unterstützte Datei: {relative}")

        merge_result = merge_gruppen(existing_groups, incoming)
        groups = merge_result.gruppen
        apply_identity_checks(groups)
        self.summary.new_groups = merge_result.neue_gruppen
        self.summary.duplicates = merge_result.duplikate
        self.summary.conflicts = merge_result.konflikte
        self.summary.open_groups = len(offene_gruppen(groups))
        for detail in merge_result.details:
            self.summary.warnings.append(f"Konflikt: {detail}")

        if not self.config.dry_run:
            try:
                write_groups(
                    self.config.output_csv,
                    groups,
                    fieldnames,
                    backup=self.config.backup,
                )
            except CSVWriteError as exc:
                raise PipelineError(str(exc)) from exc

        for file_result in file_results:
            if file_result.unsupported or file_result.technical_error:
                continue
            if any(
                bogen_id in merge_result.conflict_bogen_ids
                for bogen_id in file_result.bogen_ids
            ):
                file_result.force_review = True
            file_result.bogen_ids = [
                merge_result.duplicate_bogen_ids.get(bogen_id, bogen_id)
                for bogen_id in file_result.bogen_ids
            ]

        groups_by_bogen = gruppen_nach_bogen(groups)
        actions = plan_actions(
            file_results,
            groups_by_bogen,
            keep_input=self.config.keep_input,
        )
        if self.config.dry_run:
            self.summary.deleted = sum(1 for a in actions if a.action == "delete")
            self.summary.moved = sum(1 for a in actions if a.action == "review")
            self.summary.kept = sum(1 for a in actions if a.action == "keep")
        else:
            report = execute_actions(actions, self.config.review_dir)
            self._apply_cleanup_report(report)

        return self.summary

    # ------------------------------------------------------------------

    def _prepare(self) -> None:
        self.config.input_dir.mkdir(parents=True, exist_ok=True)
        try:
            if self.config.review_dir.resolve().is_relative_to(
                self.config.input_dir.resolve()
            ):
                raise PipelineError(
                    "Der Review-Ordner darf nicht innerhalb des Eingangs liegen."
                )
        except OSError:
            pass
        if self.config.reset and self.config.output_csv.exists():
            if not self.config.dry_run:
                stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                backup = self.config.output_csv.with_name(
                    f"{self.config.output_csv.stem}.{stamp}.bak"
                    f"{self.config.output_csv.suffix}"
                )
                try:
                    self.config.output_csv.rename(backup)
                except OSError as exc:
                    raise PipelineError(
                        f"Alte CSV konnte nicht archiviert werden: {exc}"
                    ) from exc
                self.log(f"Alte CSV archiviert: {backup}")

    def _process_file(
        self,
        input_file: InputFile,
        *,
        known_bogen_ids: set[str],
        processed_this_run: set[str],
    ) -> tuple[FileResult, list[Gruppe]]:
        result = FileResult(
            path=input_file.path,
            relative=input_file.relative,
            bogen_ids=[],
        )
        groups: list[Gruppe] = []
        file_cost = FileCost(quelle=str(input_file.relative))

        try:
            data = input_file.path.read_bytes()
        except OSError as exc:
            result.technical_error = True
            result.error = f"Datei nicht lesbar: {exc}"
            self.summary.technical_errors += 1
            self.summary.warnings.append(f"{input_file.relative}: {result.error}")
            return self._finish(result, groups, file_cost)

        try:
            bogen_ids = bogen_ids_for(input_file, data)
        except Exception as exc:
            result.technical_error = True
            result.error = f"PDF/Datei nicht lesbar: {exc}"
            self.summary.technical_errors += 1
            self.summary.warnings.append(f"{input_file.relative}: {result.error}")
            return self._finish(result, groups, file_cost)

        result.bogen_ids = bogen_ids

        if input_file.kind == "image":
            bogen_id = bogen_ids[0]
            if self._should_skip(
                bogen_id,
                known_bogen_ids=known_bogen_ids,
                processed_this_run=processed_this_run,
            ):
                self.summary.files_skipped += 1
                self.log(f"übersprungen (bekannt): {input_file.relative}")
                return self._finish(result, groups, file_cost)
            try:
                image_bytes = image_to_jpeg(data)
            except Exception as exc:
                result.technical_error = True
                result.error = f"Bild nicht lesbar: {exc}"
                self.summary.technical_errors += 1
                self.summary.warnings.append(f"{input_file.relative}: {result.error}")
                return self._finish(result, groups, file_cost)
            new_groups = self._process_page(
                input_file,
                page=1,
                bogen_id=bogen_id,
                image_bytes=image_bytes,
                result=result,
                file_cost=file_cost,
            )
            if new_groups is None:
                return self._finish(result, groups, file_cost)
            groups.extend(new_groups)
            processed_this_run.add(bogen_id)
            self.summary.files_processed += 1
            return self._finish(result, groups, file_cost)

        # PDF: Seite für Seite, damit eine kaputte Seite die anderen nicht blockiert.
        new_page_count = 0
        for page, bogen_id in enumerate(bogen_ids, start=1):
            if self._should_skip(
                bogen_id,
                known_bogen_ids=known_bogen_ids,
                processed_this_run=processed_this_run,
            ):
                continue
            try:
                image_bytes = render_pdf_page(data, page)
            except Exception as exc:
                result.technical_error = True
                result.error = f"PDF-Seite {page} nicht renderbar: {exc}"
                self.summary.technical_errors += 1
                self.summary.warnings.append(
                    f"{input_file.relative} S.{page}: {result.error}"
                )
                continue
            new_groups = self._process_page(
                input_file,
                page=page,
                bogen_id=bogen_id,
                image_bytes=image_bytes,
                result=result,
                file_cost=file_cost,
            )
            if new_groups is None:
                continue
            groups.extend(new_groups)
            processed_this_run.add(bogen_id)
            new_page_count += 1

        if new_page_count:
            self.summary.files_processed += 1
        else:
            self.summary.files_skipped += 1
        return self._finish(result, groups, file_cost)

    def _should_skip(
        self,
        bogen_id: str,
        *,
        known_bogen_ids: set[str],
        processed_this_run: set[str],
    ) -> bool:
        return (
            bogen_id in known_bogen_ids and not self.config.reprocess
        ) or bogen_id in processed_this_run

    def _process_page(
        self,
        input_file: InputFile,
        *,
        page: int,
        bogen_id: str,
        image_bytes: bytes,
        result: FileResult,
        file_cost: FileCost,
    ) -> list[Gruppe] | None:
        new_groups = self._extract(
            input_file,
            page=page,
            bogen_id=bogen_id,
            image_bytes=image_bytes,
            file_cost=file_cost,
        )
        if new_groups is None:
            result.technical_error = True
            result.error = f"LLM-Aufruf Seite {page} fehlgeschlagen"
            return None
        return new_groups

    def _finish(
        self,
        result: FileResult,
        groups: list[Gruppe],
        file_cost: FileCost,
    ) -> tuple[FileResult, list[Gruppe]]:
        if file_cost.prompt_tokens or file_cost.completion_tokens or file_cost.cached:
            self.summary.file_costs.append(file_cost)
        return result, groups

    def _extract(
        self,
        input_file: InputFile,
        *,
        page: int,
        bogen_id: str,
        image_bytes: bytes,
        file_cost: FileCost,
    ) -> list[Gruppe] | None:
        self.log(f"lese: {input_file.relative} (Seite {page})")
        try:
            llm_result = self.client.extract_bogen(
                bogen_id=bogen_id,
                quelle=str(input_file.relative),
                image_bytes=image_bytes,
                mime_type="image/jpeg",
            )
        except Exception as exc:  # noqa: BLE001 - klare Meldung nach oben
            self.summary.technical_errors += 1
            self.summary.warnings.append(f"{input_file.relative} S.{page}: {exc}")
            return None

        self.summary.pages_processed += 1
        if llm_result.cached:
            self.summary.cache_hits += 1
            file_cost.cached = True
        else:
            self.summary.prompt_tokens += llm_result.prompt_tokens
            self.summary.completion_tokens += llm_result.completion_tokens
            self.summary.reasoning_tokens += llm_result.reasoning_tokens
            self.summary.cost_usd += llm_result.cost_usd
            file_cost.prompt_tokens += llm_result.prompt_tokens
            file_cost.completion_tokens += llm_result.completion_tokens
            file_cost.reasoning_tokens += llm_result.reasoning_tokens
            file_cost.cost_usd += llm_result.cost_usd
            if (
                self.config.max_cost is not None
                and self.summary.cost_usd > self.config.max_cost
            ):
                raise PipelineError(
                    "Kostenlimit überschritten: "
                    f"${self.summary.cost_usd:.4f} > "
                    f"${self.config.max_cost:.4f}."
                )

        ref = BogenRef(
            bogen_id=bogen_id,
            quelle=str(input_file.relative),
            seite=page,
        )
        neue_bogen = build_neue_bogen(llm_result.bogen, ref=ref)
        if neue_bogen.bogen_unklar:
            placeholder = Gruppe(
                ref=ref,
                position=0,
                durchgang_nr=neue_bogen.durchgang_nr,
                spieler_nr="",
                spieler_name="",
                placeholder=True,
            )
            placeholder.recompute()
            self.summary.unreadable += 1
            return [placeholder]

        return neue_bogen.spieler

    def _apply_cleanup_report(self, report: CleanupReport) -> None:
        self.summary.deleted += report.deleted
        self.summary.moved += report.moved
        self.summary.kept += report.kept
        self.summary.cleanup_failures.extend(report.failures)
        for failure in report.failures:
            self.summary.warnings.append(f"Aufräumen fehlgeschlagen: {failure}")
