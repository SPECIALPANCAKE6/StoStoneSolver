from __future__ import annotations

import json

import pytest

from src.stostone.generator.calibration import (
    analyze_calibration_records,
    load_calibration_records,
    percentile,
    render_markdown_report,
    round_to_nearest,
)
from src.stostone.generator.scoring import DIFFICULTY_SCORE_MODEL, score_generation_quality


pytestmark = pytest.mark.unit


def _summary_item(
    *,
    signature: str,
    difficulty_score: float,
    rows: int = 4,
    cols: int = 4,
    rooms: int = 4,
    room_balance: float = 0.5,
    shape_compactness: float = 0.8,
    room_size_spread: int = 3,
    given_shaded_cells: int = 0,
    pre_solved_rooms: int = 0,
    applied_reveal_policy: str = "empty",
    status: str = "written",
    score_model: str | None = DIFFICULTY_SCORE_MODEL,
) -> dict[str, object]:
    quality: dict[str, object] = {
        "difficulty_score": difficulty_score,
        "solve_iterations": int(difficulty_score) + 1,
        "room_balance": room_balance,
        "shape_compactness": shape_compactness,
        "room_size_spread": room_size_spread,
        "given_shaded_cells": given_shaded_cells,
        "pre_solved_rooms": pre_solved_rooms,
    }
    if score_model is not None:
        quality["difficulty_score_model"] = score_model

    return {
        "seed": 1,
        "status": status,
        "signature": signature,
        "generation": {
            "rows": rows,
            "cols": cols,
            "rooms": rooms,
            "attempts": 2,
            "numbered_rooms": 2,
            "requested_reveal_policy": applied_reveal_policy,
            "applied_reveal_policy": applied_reveal_policy,
        },
        "quality": quality,
    }


def test_load_calibration_records_dedupes_signatures_and_skips_unusable_items(workspace_tmp_dir) -> None:
    summary_path = workspace_tmp_dir.joinpath("summary.json")
    summary = {
        "items": [
            _summary_item(signature="same", difficulty_score=10),
            _summary_item(signature="same", difficulty_score=90),
            {"status": "failed", "signature": "failed"},
            {"status": "written", "signature": "missing-quality", "generation": {"rows": 4, "cols": 4, "rooms": 4}},
            _summary_item(signature="rejected", difficulty_score=30, status="rejected-quality"),
        ]
    }
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    records = load_calibration_records([summary_path])

    assert [record.signature for record in records] == ["same", "rejected"]
    assert records[0].difficulty_score == 10
    assert records[1].status == "rejected-quality"


def test_load_calibration_records_rescores_legacy_summary_items(workspace_tmp_dir) -> None:
    summary_path = workspace_tmp_dir.joinpath("summary.json")
    summary = {
        "items": [
            _summary_item(
                signature="legacy-score",
                difficulty_score=10,
                rows=8,
                cols=8,
                rooms=8,
                score_model=None,
            )
        ]
    }
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    [record] = load_calibration_records([summary_path])
    expected_score = score_generation_quality(
        solve_iterations=11,
        rows=8,
        cols=8,
        room_balance=0.5,
        shape_compactness=0.8,
        given_shaded_cells=0,
        pre_solved_rooms=0,
    )

    assert record.difficulty_score == pytest.approx(expected_score)
    assert record.difficulty_score != 10


def test_percentile_and_rounding_helpers_are_deterministic() -> None:
    assert percentile([10, 20, 30, 40], 25) == 17.5
    assert percentile([10, 20, 30, 40], 50) == 25
    assert round_to_nearest(17.5, 5) == 20
    assert round_to_nearest(0.73, 0.05) == pytest.approx(0.75)


def test_analyze_calibration_records_recommends_deterministic_preset_bands(workspace_tmp_dir) -> None:
    summary_path = workspace_tmp_dir.joinpath("summary.json")
    summary = {
        "items": [
            _summary_item(signature="a", difficulty_score=10, room_balance=0.2, shape_compactness=0.7, room_size_spread=5),
            _summary_item(signature="b", difficulty_score=20, room_balance=0.3, shape_compactness=0.75, room_size_spread=4),
            _summary_item(signature="c", difficulty_score=30, room_balance=0.4, shape_compactness=0.8, room_size_spread=3),
            _summary_item(signature="d", difficulty_score=40, room_balance=0.5, shape_compactness=0.85, room_size_spread=2),
            _summary_item(signature="e", difficulty_score=80, room_balance=0.6, shape_compactness=0.9, room_size_spread=1),
        ]
    }
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    records = load_calibration_records([summary_path])

    report = analyze_calibration_records(records)
    recommendations = report["overall"]["recommendations"]

    assert report["record_count"] == 5
    assert report["difficulty_score_model"] == DIFFICULTY_SCORE_MODEL
    assert report["families"]["4x4-4r"]["record_count"] == 5
    assert recommendations["difficulty"]["easy_max"] == 25.0
    assert recommendations["difficulty"]["medium_max"] == 35.0
    assert recommendations["difficulty"]["hard_max"] == 55.0
    assert recommendations["quality"]["balanced"]["min_room_balance"] == 0.3
    assert recommendations["quality"]["strict"]["min_shape_compactness"] == 0.8

    markdown = render_markdown_report(report)
    assert "# Sto-Stone Generator Calibration Report" in markdown
    assert "## 4x4-4r" in markdown
    assert "| difficulty_score |" in markdown


def test_calibration_hit_rates_use_size_aware_family_difficulty_presets(workspace_tmp_dir) -> None:
    summary_path = workspace_tmp_dir.joinpath("summary.json")
    summary = {
        "items": [
            _summary_item(signature="global-hard-family-easy", difficulty_score=70, rows=6, cols=6, rooms=6)
        ]
    }
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    records = load_calibration_records([summary_path])

    report = analyze_calibration_records(records)

    assert report["overall"]["hit_rates"]["difficulty"]["easy"] == 0.0
    assert report["families"]["6x6-6r"]["hit_rates"]["difficulty"]["easy"] == 1.0


def test_difficulty_recommendations_do_not_invert_adjacent_bands(workspace_tmp_dir) -> None:
    summary_path = workspace_tmp_dir.joinpath("summary.json")
    summary = {
        "items": [
            _summary_item(signature=f"sig-{index}", difficulty_score=score, rows=4, cols=6, rooms=6)
            for index, score in enumerate([60, 65, 80, 80, 80])
        ]
    }
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    report = analyze_calibration_records(load_calibration_records([summary_path]))
    difficulty = report["families"]["4x6-6r"]["recommendations"]["difficulty"]

    assert difficulty["easy_max"] <= difficulty["medium_max"]
    assert difficulty["medium_max"] <= difficulty["hard_max"]
