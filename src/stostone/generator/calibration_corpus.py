from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..models import GenerationBatchResult, GenerationFilters, SolveMode
from .calibration import analyze_calibration_summaries, write_calibration_reports
from .presets import board_family_key
from .service import (
    DEFAULT_GENERATOR_NAME,
    DEFAULT_OUTPUT_PREFIX,
    DEFAULT_REVEAL_POLICY,
    GenerationFailed,
    build_puzzle_corpus,
)

FILTER_KEYS: tuple[str, ...] = (
    "min_room_balance",
    "min_shape_compactness",
    "max_room_size_spread",
    "max_given_shaded_cells",
    "max_pre_solved_rooms",
    "min_solve_iterations",
    "max_solve_iterations",
    "min_difficulty_score",
    "max_difficulty_score",
)


@dataclass(slots=True, frozen=True)
class CalibrationCorpusFamilyPlan:
    name: str
    rows: int
    cols: int
    rooms: int
    count: int
    seed_start: int
    out_dir: Path
    summary_path: Path
    seed_step: int = 1
    max_seeds: int | None = None
    output_prefix: str = DEFAULT_OUTPUT_PREFIX
    max_attempts: int = 256
    uniqueness_limit: int = 2
    reveal_policy: str = DEFAULT_REVEAL_POLICY
    mode: SolveMode = "sto-stone"
    generator_name: str = DEFAULT_GENERATOR_NAME
    clue_carving: bool = True
    filters: GenerationFilters | None = None
    quality_preset: str | None = None
    difficulty_preset: str | None = None
    clue_profile: str | None = None
    allow_duplicates: bool = False


@dataclass(slots=True, frozen=True)
class CalibrationCorpusPlan:
    path: Path
    families: tuple[CalibrationCorpusFamilyPlan, ...]


@dataclass(slots=True, frozen=True)
class CalibrationCorpusRunItem:
    family: str
    status: str
    summary_path: Path
    requested_count: int
    generated_count: int | None = None
    seeds_tried: int | None = None
    reason: str | None = None
    batch_result: GenerationBatchResult | None = None


@dataclass(slots=True, frozen=True)
class CalibrationCorpusRunResult:
    plan: CalibrationCorpusPlan
    items: tuple[CalibrationCorpusRunItem, ...]
    report: dict[str, Any]
    markdown_path: Path | None = None
    json_path: Path | None = None

    @property
    def completed(self) -> bool:
        return all(item.status in {"generated", "skipped"} for item in self.items)


def _required_int(data: dict[str, Any], key: str, family_index: int) -> int:
    if key not in data:
        raise ValueError(f"Family #{family_index} is missing required field '{key}'.")
    return int(data[key])


def _optional_int(data: dict[str, Any], key: str) -> int | None:
    return None if data.get(key) is None else int(data[key])


def _resolve_plan_path(value: str | Path, base_dir: Path, family_name: str) -> Path:
    path = Path(str(value).format(family=family_name, name=family_name))
    if not path.is_absolute():
        path = base_dir.joinpath(path)
    return path.resolve()


def _parse_filters(data: dict[str, Any]) -> GenerationFilters | None:
    filters_data = data.get("filters")
    if filters_data is None:
        return None
    if not isinstance(filters_data, dict):
        raise ValueError("Plan 'filters' must be an object when provided.")

    unexpected = sorted(set(filters_data) - set(FILTER_KEYS))
    if unexpected:
        raise ValueError(f"Unsupported filter field(s): {', '.join(unexpected)}")

    return GenerationFilters(**{key: filters_data[key] for key in FILTER_KEYS if key in filters_data})


def _load_family_plan(
    raw_family: dict[str, Any],
    defaults: dict[str, Any],
    base_dir: Path,
    family_index: int,
) -> CalibrationCorpusFamilyPlan:
    data = {**defaults, **raw_family}
    rows = _required_int(data, "rows", family_index)
    cols = _required_int(data, "cols", family_index)
    rooms = _required_int(data, "rooms", family_index)
    count = _required_int(data, "count", family_index)
    seed_start = _required_int(data, "seed_start", family_index)
    name = str(data.get("name") or board_family_key(rows, cols, rooms))

    out_dir = _resolve_plan_path(data.get("out_dir", "{family}"), base_dir, name)
    summary_path = _resolve_plan_path(data.get("summary_file", "{family}-summary.json"), base_dir, name)

    return CalibrationCorpusFamilyPlan(
        name=name,
        rows=rows,
        cols=cols,
        rooms=rooms,
        count=count,
        seed_start=seed_start,
        seed_step=int(data.get("seed_step", 1)),
        max_seeds=_optional_int(data, "max_seeds"),
        out_dir=out_dir,
        output_prefix=str(data.get("output_prefix", DEFAULT_OUTPUT_PREFIX)),
        summary_path=summary_path,
        max_attempts=int(data.get("max_attempts", 256)),
        uniqueness_limit=int(data.get("uniqueness_limit", 2)),
        reveal_policy=str(data.get("reveal_policy", DEFAULT_REVEAL_POLICY)),
        mode=data.get("mode", "sto-stone"),
        generator_name=str(data.get("generator_name", DEFAULT_GENERATOR_NAME)),
        clue_carving=bool(data.get("clue_carving", True)),
        filters=_parse_filters(data),
        quality_preset=data.get("quality_preset"),
        difficulty_preset=data.get("difficulty_preset"),
        clue_profile=data.get("clue_profile"),
        allow_duplicates=bool(data.get("allow_duplicates", False)),
    )


def load_calibration_corpus_plan(plan_path: Path | str) -> CalibrationCorpusPlan:
    path = Path(plan_path).resolve()
    with open(path, "r", encoding="utf-8") as file:
        payload = json.load(file)

    defaults = payload.get("defaults", {})
    families = payload.get("families")
    if not isinstance(defaults, dict):
        raise ValueError("Calibration corpus plan 'defaults' must be an object when provided.")
    if not isinstance(families, list) or not families:
        raise ValueError("Calibration corpus plan must include a non-empty 'families' list.")
    if any(not isinstance(raw_family, dict) for raw_family in families):
        raise ValueError("Every calibration corpus family entry must be an object.")

    return CalibrationCorpusPlan(
        path=path,
        families=tuple(
            _load_family_plan(raw_family, defaults, path.parent, index + 1)
            for index, raw_family in enumerate(families)
        ),
    )


def _summary_generated_count(summary_path: Path) -> int | None:
    if not summary_path.is_file():
        return None
    try:
        with open(summary_path, "r", encoding="utf-8") as file:
            summary = json.load(file)
    except (OSError, json.JSONDecodeError):
        return None
    try:
        return int(summary.get("generated_count", 0))
    except (TypeError, ValueError):
        return None


def _run_family(family: CalibrationCorpusFamilyPlan, force: bool) -> CalibrationCorpusRunItem:
    generated_count = _summary_generated_count(family.summary_path)
    if not force and generated_count is not None and generated_count >= family.count:
        return CalibrationCorpusRunItem(
            family=family.name,
            status="skipped",
            summary_path=family.summary_path,
            requested_count=family.count,
            generated_count=generated_count,
            reason="Summary already satisfies requested count.",
        )

    try:
        batch_result = build_puzzle_corpus(
            count=family.count,
            rows=family.rows,
            cols=family.cols,
            rooms=family.rooms,
            seed_start=family.seed_start,
            seed_step=family.seed_step,
            max_seeds=family.max_seeds,
            out_dir=family.out_dir,
            output_prefix=family.output_prefix,
            max_attempts=family.max_attempts,
            uniqueness_limit=family.uniqueness_limit,
            reveal_policy=family.reveal_policy,
            mode=family.mode,
            generator_name=family.generator_name,
            clue_carving=family.clue_carving,
            filters=family.filters,
            quality_preset=family.quality_preset,
            difficulty_preset=family.difficulty_preset,
            clue_profile=family.clue_profile,
            allow_duplicates=family.allow_duplicates,
            summary_path=family.summary_path,
        )
    except GenerationFailed as exc:
        return CalibrationCorpusRunItem(
            family=family.name,
            status="failed",
            summary_path=family.summary_path,
            requested_count=family.count,
            reason=str(exc),
        )

    status = "generated" if batch_result.generated_count >= family.count else "incomplete"
    return CalibrationCorpusRunItem(
        family=family.name,
        status=status,
        summary_path=family.summary_path,
        requested_count=family.count,
        generated_count=batch_result.generated_count,
        seeds_tried=batch_result.seeds_tried,
        reason=None if status == "generated" else "Generated fewer puzzles than requested.",
        batch_result=batch_result,
    )


def run_calibration_corpus_plan(
    plan_path: Path | str,
    *,
    force: bool = False,
    markdown_path: Path | str | None = None,
    json_path: Path | str | None = None,
) -> CalibrationCorpusRunResult:
    plan = load_calibration_corpus_plan(plan_path)
    items = tuple(_run_family(family, force) for family in plan.families)
    summary_paths = [
        item.summary_path
        for item in items
        if item.status in {"generated", "skipped", "incomplete"} and item.summary_path.is_file()
    ]
    if not summary_paths:
        raise ValueError("No calibration summary files were available after running the corpus plan.")

    report = analyze_calibration_summaries(summary_paths)
    written_markdown, written_json = write_calibration_reports(
        report,
        markdown_path=markdown_path,
        json_path=json_path,
    )
    return CalibrationCorpusRunResult(
        plan=plan,
        items=items,
        report=report,
        markdown_path=written_markdown,
        json_path=written_json,
    )


__all__ = [
    "CalibrationCorpusFamilyPlan",
    "CalibrationCorpusPlan",
    "CalibrationCorpusRunItem",
    "CalibrationCorpusRunResult",
    "load_calibration_corpus_plan",
    "run_calibration_corpus_plan",
]
