from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..models import GenerationFilters
from .presets import CLUE_PROFILES, QUALITY_PRESETS, difficulty_presets_for_family
from .scoring import DIFFICULTY_SCORE_MODEL, score_generation_quality

CALIBRATION_METRICS: tuple[str, ...] = (
    "difficulty_score",
    "solve_iterations",
    "room_balance",
    "shape_compactness",
    "room_size_spread",
    "given_shaded_cells",
    "pre_solved_rooms",
    "numbered_rooms",
    "attempts",
)
PERCENTILES: tuple[int, ...] = (0, 25, 50, 60, 75, 85, 100)


@dataclass(slots=True, frozen=True)
class CalibrationRecord:
    source_path: str
    family: str
    signature: str
    status: str
    seed: int | None
    quality_preset: str | None
    difficulty_preset: str | None
    clue_profile: str | None
    requested_reveal_policy: str | None
    applied_reveal_policy: str | None
    difficulty_score: float
    solve_iterations: int
    room_balance: float
    shape_compactness: float
    room_size_spread: int
    given_shaded_cells: int
    pre_solved_rooms: int
    numbered_rooms: int
    attempts: int

    def metric(self, name: str) -> float:
        return float(getattr(self, name))


def _as_int(value: Any) -> int:
    return int(value)


def _as_float(value: Any) -> float:
    return float(value)


def _summary_family(summary: dict[str, Any]) -> str | None:
    rows = summary.get("rows")
    cols = summary.get("cols")
    rooms = summary.get("rooms")
    if rows is None or cols is None or rooms is None:
        return None
    return f"{rows}x{cols}-{rooms}r"


def _path_family(path_name: str | None) -> str | None:
    if not path_name:
        return None
    match = re.search(r"(?P<rows>\d+)x(?P<cols>\d+)-(?P<rooms>\d+)r", path_name)
    if match is None:
        return None
    return f"{match.group('rows')}x{match.group('cols')}-{match.group('rooms')}r"


def _item_family(summary: dict[str, Any], generation: dict[str, Any]) -> str | None:
    rows = generation.get("rows")
    cols = generation.get("cols")
    rooms = generation.get("rooms")
    if rows is not None and cols is not None and rooms is not None:
        return f"{rows}x{cols}-{rooms}r"
    return _summary_family(summary)


def _family_dimensions(family: str) -> tuple[int, int, int] | None:
    match = re.fullmatch(r"(?P<rows>\d+)x(?P<cols>\d+)-(?P<rooms>\d+)r", family)
    if match is None:
        return None
    return int(match.group("rows")), int(match.group("cols")), int(match.group("rooms"))


def _difficulty_score_for_record(family: str, quality: dict[str, Any]) -> float:
    stored_score = _as_float(quality["difficulty_score"])
    if quality.get("difficulty_score_model") == DIFFICULTY_SCORE_MODEL:
        return stored_score

    dimensions = _family_dimensions(family)
    if dimensions is None:
        return stored_score

    rows, cols, _ = dimensions
    return score_generation_quality(
        solve_iterations=_as_int(quality["solve_iterations"]),
        rows=rows,
        cols=cols,
        room_balance=_as_float(quality["room_balance"]),
        shape_compactness=_as_float(quality["shape_compactness"]),
        given_shaded_cells=_as_int(quality["given_shaded_cells"]),
        pre_solved_rooms=_as_int(quality["pre_solved_rooms"]),
    )


def _build_record(summary: dict[str, Any], item: dict[str, Any], source_path: Path) -> CalibrationRecord | None:
    if item.get("status") == "failed":
        return None
    generation = item.get("generation")
    quality = item.get("quality")
    signature = item.get("signature")
    if not isinstance(generation, dict) or not isinstance(quality, dict) or not signature:
        return None

    family = _item_family(summary, generation) or _path_family(item.get("output_path"))
    if family is None:
        return None

    try:
        return CalibrationRecord(
            source_path=str(source_path),
            family=family,
            signature=str(signature),
            status=str(item.get("status", "unknown")),
            seed=None if item.get("seed") is None else _as_int(item["seed"]),
            quality_preset=generation.get("quality_preset"),
            difficulty_preset=generation.get("difficulty_preset"),
            clue_profile=generation.get("clue_profile"),
            requested_reveal_policy=generation.get("requested_reveal_policy"),
            applied_reveal_policy=generation.get("applied_reveal_policy"),
            difficulty_score=_difficulty_score_for_record(family, quality),
            solve_iterations=_as_int(quality["solve_iterations"]),
            room_balance=_as_float(quality["room_balance"]),
            shape_compactness=_as_float(quality["shape_compactness"]),
            room_size_spread=_as_int(quality["room_size_spread"]),
            given_shaded_cells=_as_int(quality["given_shaded_cells"]),
            pre_solved_rooms=_as_int(quality["pre_solved_rooms"]),
            numbered_rooms=_as_int(generation["numbered_rooms"]),
            attempts=_as_int(generation["attempts"]),
        )
    except (KeyError, TypeError, ValueError):
        return None


def load_calibration_records(summary_paths: list[Path | str]) -> list[CalibrationRecord]:
    records_by_signature: dict[str, CalibrationRecord] = {}
    for summary_path in summary_paths:
        path = Path(summary_path)
        with open(path, "r", encoding="utf-8") as file:
            summary = json.load(file)
        for item in summary.get("items", []):
            if not isinstance(item, dict):
                continue
            record = _build_record(summary, item, path)
            if record is not None and record.signature not in records_by_signature:
                records_by_signature[record.signature] = record
    return list(records_by_signature.values())


def percentile(values: list[float], percentile_value: float) -> float:
    if not values:
        raise ValueError("Cannot calculate a percentile from an empty value list.")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * (percentile_value / 100.0)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] + ((ordered[upper] - ordered[lower]) * weight)


def round_to_nearest(value: float, increment: float) -> float:
    if increment <= 0:
        raise ValueError("Increment must be positive.")
    return math.floor((value / increment) + 0.5) * increment


def _filter_matches(record: CalibrationRecord, filters: GenerationFilters) -> bool:
    if filters.min_room_balance is not None and record.room_balance < filters.min_room_balance:
        return False
    if filters.min_shape_compactness is not None and record.shape_compactness < filters.min_shape_compactness:
        return False
    if filters.max_room_size_spread is not None and record.room_size_spread > filters.max_room_size_spread:
        return False
    if filters.max_given_shaded_cells is not None and record.given_shaded_cells > filters.max_given_shaded_cells:
        return False
    if filters.max_pre_solved_rooms is not None and record.pre_solved_rooms > filters.max_pre_solved_rooms:
        return False
    if filters.min_solve_iterations is not None and record.solve_iterations < filters.min_solve_iterations:
        return False
    if filters.max_solve_iterations is not None and record.solve_iterations > filters.max_solve_iterations:
        return False
    if filters.min_difficulty_score is not None and record.difficulty_score < filters.min_difficulty_score:
        return False
    if filters.max_difficulty_score is not None and record.difficulty_score > filters.max_difficulty_score:
        return False
    return True


def _clue_profile_matches(record: CalibrationRecord, profile_name: str) -> bool:
    if profile_name == "minimal":
        return record.given_shaded_cells == 0 and record.pre_solved_rooms == 0
    if profile_name == "varied":
        profile = CLUE_PROFILES[profile_name]
        return (
            record.given_shaded_cells <= (profile.max_given_shaded_cells or 0)
            and record.pre_solved_rooms <= (profile.max_pre_solved_rooms or 0)
            and record.applied_reveal_policy in {"empty", "few-cells", "full-room"}
        )
    if profile_name == "guided":
        return 1 <= record.given_shaded_cells <= 4 and record.applied_reveal_policy == "few-cells"
    if profile_name == "room-reveal":
        return record.pre_solved_rooms == 1 and record.applied_reveal_policy == "full-room"
    return False


def _rate(matches: int, total: int) -> float:
    return 0.0 if total == 0 else matches / total


def _metric_percentiles(records: list[CalibrationRecord]) -> dict[str, dict[str, float]]:
    return {
        metric: {
            f"p{percentile_value}": percentile([record.metric(metric) for record in records], percentile_value)
            for percentile_value in PERCENTILES
        }
        for metric in CALIBRATION_METRICS
    }


def _current_difficulty_cutoffs(board_family: str | None = None) -> dict[str, float]:
    difficulty_presets = difficulty_presets_for_family(board_family)
    return {
        "easy_max": difficulty_presets["easy"].max_difficulty_score or 25.0,
        "medium_max": difficulty_presets["medium"].max_difficulty_score or 50.0,
        "hard_max": difficulty_presets["hard"].max_difficulty_score or 75.0,
    }


def _keep_or_recommend(current: float, recommended: float, tolerance: float) -> float:
    return current if abs(current - recommended) <= tolerance else recommended


def _difficulty_recommendations(percentiles: dict[str, dict[str, float]], board_family: str | None = None) -> dict[str, float]:
    current = _current_difficulty_cutoffs(board_family)
    score_percentiles = percentiles["difficulty_score"]
    easy_max = _keep_or_recommend(current["easy_max"], round_to_nearest(score_percentiles["p25"], 5.0), 5.0)
    medium_max = _keep_or_recommend(current["medium_max"], round_to_nearest(score_percentiles["p60"], 5.0), 5.0)
    hard_max = _keep_or_recommend(current["hard_max"], round_to_nearest(score_percentiles["p85"], 5.0), 5.0)
    medium_max = max(easy_max, medium_max)
    hard_max = max(medium_max, hard_max)
    return {
        "easy_max": easy_max,
        "medium_min": easy_max,
        "medium_max": medium_max,
        "hard_min": medium_max,
        "hard_max": hard_max,
        "expert_min": hard_max,
    }


def _quality_recommendations(percentiles: dict[str, dict[str, float]]) -> dict[str, dict[str, float | int]]:
    return {
        "balanced": {
            "min_room_balance": round(round_to_nearest(percentiles["room_balance"]["p25"], 0.05), 2),
            "min_shape_compactness": round(round_to_nearest(percentiles["shape_compactness"]["p25"], 0.05), 2),
            "max_room_size_spread": int(round(percentiles["room_size_spread"]["p75"])),
        },
        "strict": {
            "min_room_balance": round(round_to_nearest(percentiles["room_balance"]["p50"], 0.05), 2),
            "min_shape_compactness": round(round_to_nearest(percentiles["shape_compactness"]["p50"], 0.05), 2),
            "max_room_size_spread": int(round(percentiles["room_size_spread"]["p50"])),
        },
    }


def _hit_rates(records: list[CalibrationRecord], board_family: str | None = None) -> dict[str, dict[str, float]]:
    total = len(records)
    difficulty_presets = difficulty_presets_for_family(board_family)
    quality_rates = {
        name: _rate(sum(_filter_matches(record, filters) for record in records), total)
        for name, filters in QUALITY_PRESETS.items()
    }
    difficulty_rates = {
        name: _rate(sum(_filter_matches(record, filters) for record in records), total)
        for name, filters in difficulty_presets.items()
    }
    clue_rates = {
        name: _rate(sum(_clue_profile_matches(record, name) for record in records), total)
        for name in CLUE_PROFILES
    }
    return {
        "quality": quality_rates,
        "difficulty": difficulty_rates,
        "clue_profiles": clue_rates,
    }


def _family_report(records: list[CalibrationRecord], board_family: str | None = None) -> dict[str, Any]:
    metric_percentiles = _metric_percentiles(records)
    applied_counts: dict[str, int] = {}
    for record in records:
        policy = record.applied_reveal_policy or "unknown"
        applied_counts[policy] = applied_counts.get(policy, 0) + 1
    return {
        "record_count": len(records),
        "percentiles": metric_percentiles,
        "hit_rates": _hit_rates(records, board_family),
        "applied_reveal_policy_counts": dict(sorted(applied_counts.items())),
        "recommendations": {
            "difficulty": _difficulty_recommendations(metric_percentiles, board_family),
            "quality": _quality_recommendations(metric_percentiles),
        },
    }


def analyze_calibration_records(records: list[CalibrationRecord]) -> dict[str, Any]:
    if not records:
        raise ValueError("No usable calibration records were found.")

    families: dict[str, list[CalibrationRecord]] = {}
    for record in records:
        families.setdefault(record.family, []).append(record)

    overall = _family_report(records)
    family_reports = {
        family: _family_report(family_records, family)
        for family, family_records in sorted(families.items())
    }
    return {
        "record_count": len(records),
        "difficulty_score_model": DIFFICULTY_SCORE_MODEL,
        "families": family_reports,
        "overall": overall,
    }


def analyze_calibration_summaries(summary_paths: list[Path | str]) -> dict[str, Any]:
    return analyze_calibration_records(load_calibration_records(summary_paths))


def _format_number(value: float | int) -> str:
    if isinstance(value, int) or float(value).is_integer():
        return str(int(value))
    return f"{value:.3f}".rstrip("0").rstrip(".")


def render_markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# Sto-Stone Generator Calibration Report",
        "",
        f"Records analyzed: {report['record_count']}",
        f"Difficulty score model: {report.get('difficulty_score_model', 'unknown')}",
        "",
        "## Overall Recommendations",
        "",
        _render_recommendations(report["overall"]["recommendations"]),
        "",
    ]
    for family, family_report in report["families"].items():
        lines.extend(
            [
                f"## {family}",
                "",
                f"Records: {family_report['record_count']}",
                "",
                "### Metric Percentiles",
                "",
                _render_percentile_table(family_report["percentiles"]),
                "",
                "### Current Preset Hit Rates",
                "",
                _render_hit_rate_table(family_report["hit_rates"]),
                "",
                "### Applied Reveal Policies",
                "",
                _render_count_table(family_report["applied_reveal_policy_counts"]),
                "",
                "### Family Recommendations",
                "",
                _render_recommendations(family_report["recommendations"]),
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _render_percentile_table(percentiles: dict[str, dict[str, float]]) -> str:
    headers = ["metric", *(f"p{value}" for value in PERCENTILES)]
    rows = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for metric in CALIBRATION_METRICS:
        values = percentiles[metric]
        rows.append("| " + " | ".join([metric, *(_format_number(values[f"p{value}"]) for value in PERCENTILES)]) + " |")
    return "\n".join(rows)


def _render_hit_rate_table(hit_rates: dict[str, dict[str, float]]) -> str:
    rows = ["| preset_type | preset | hit_rate |", "| --- | --- | --- |"]
    for preset_type, rates in hit_rates.items():
        for preset, rate in rates.items():
            rows.append(f"| {preset_type} | {preset} | {rate:.1%} |")
    return "\n".join(rows)


def _render_count_table(counts: dict[str, int]) -> str:
    rows = ["| value | count |", "| --- | --- |"]
    for value, count in counts.items():
        rows.append(f"| {value} | {count} |")
    return "\n".join(rows)


def _render_recommendations(recommendations: dict[str, Any]) -> str:
    difficulty = recommendations["difficulty"]
    quality = recommendations["quality"]
    return "\n".join(
        [
            "- Difficulty: "
            f"easy <= {_format_number(difficulty['easy_max'])}, "
            f"medium {_format_number(difficulty['medium_min'])}-{_format_number(difficulty['medium_max'])}, "
            f"hard {_format_number(difficulty['hard_min'])}-{_format_number(difficulty['hard_max'])}, "
            f"expert > {_format_number(difficulty['expert_min'])}",
            "- Quality balanced: "
            f"room_balance >= {_format_number(quality['balanced']['min_room_balance'])}, "
            f"shape_compactness >= {_format_number(quality['balanced']['min_shape_compactness'])}, "
            f"room_size_spread <= {quality['balanced']['max_room_size_spread']}",
            "- Quality strict: "
            f"room_balance >= {_format_number(quality['strict']['min_room_balance'])}, "
            f"shape_compactness >= {_format_number(quality['strict']['min_shape_compactness'])}, "
            f"room_size_spread <= {quality['strict']['max_room_size_spread']}",
        ]
    )


def write_calibration_reports(
    report: dict[str, Any],
    *,
    markdown_path: Path | str | None = None,
    json_path: Path | str | None = None,
) -> tuple[Path | None, Path | None]:
    written_markdown = None
    written_json = None
    if markdown_path is not None:
        written_markdown = Path(markdown_path)
        written_markdown.parent.mkdir(parents=True, exist_ok=True)
        written_markdown.write_text(render_markdown_report(report), encoding="utf-8", newline="\n")
        written_markdown = written_markdown.resolve()
    if json_path is not None:
        written_json = Path(json_path)
        written_json.parent.mkdir(parents=True, exist_ok=True)
        with open(written_json, "w", encoding="utf-8", newline="\n") as file:
            json.dump(report, file, indent=2, sort_keys=True)
        written_json = written_json.resolve()
    return written_markdown, written_json


__all__ = [
    "CALIBRATION_METRICS",
    "CalibrationRecord",
    "PERCENTILES",
    "analyze_calibration_records",
    "analyze_calibration_summaries",
    "load_calibration_records",
    "percentile",
    "render_markdown_report",
    "round_to_nearest",
    "write_calibration_reports",
]
