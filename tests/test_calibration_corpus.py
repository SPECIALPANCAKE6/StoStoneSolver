from __future__ import annotations

import json
from datetime import timedelta

import pytest

from src.stostone.generator.calibration_corpus import load_calibration_corpus_plan, run_calibration_corpus_plan
from src.stostone.models import GenerationBatchResult


pytestmark = pytest.mark.unit


def _write_summary(path, *, rows: int = 4, cols: int = 4, rooms: int = 4, count: int = 1) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "requested_count": count,
        "generated_count": count,
        "items": [
            {
                "seed": 1,
                "status": "written",
                "signature": f"{rows}x{cols}-{rooms}r-sig",
                "generation": {
                    "rows": rows,
                    "cols": cols,
                    "rooms": rooms,
                    "attempts": 2,
                    "numbered_rooms": 2,
                    "requested_reveal_policy": "empty",
                    "applied_reveal_policy": "empty",
                },
                "quality": {
                    "difficulty_score": 20,
                    "solve_iterations": 8,
                    "room_balance": 0.5,
                    "shape_compactness": 0.8,
                    "room_size_spread": 2,
                    "given_shaded_cells": 0,
                    "pre_solved_rooms": 0,
                },
            }
        ],
    }
    path.write_text(json.dumps(summary), encoding="utf-8")


def test_load_calibration_corpus_plan_resolves_paths_and_defaults(workspace_tmp_dir) -> None:
    plan_path = workspace_tmp_dir.joinpath("calibration", "plan.json")
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        json.dumps(
            {
                "defaults": {
                    "max_attempts": 20,
                    "reveal_policy": "empty",
                    "out_dir": "corpora/{family}",
                    "summary_file": "summaries/{family}.json",
                },
                "families": [
                    {
                        "rows": 4,
                        "cols": 6,
                        "rooms": 6,
                        "count": 10,
                        "seed_start": 200,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    plan = load_calibration_corpus_plan(plan_path)
    family = plan.families[0]

    assert family.name == "4x6-6r"
    assert family.max_attempts == 20
    assert family.reveal_policy == "empty"
    assert family.out_dir == plan_path.parent.joinpath("corpora", "4x6-6r").resolve()
    assert family.summary_path == plan_path.parent.joinpath("summaries", "4x6-6r.json").resolve()


def test_run_calibration_corpus_plan_skips_complete_summary(monkeypatch, workspace_tmp_dir) -> None:
    summary_path = workspace_tmp_dir.joinpath("4x4-summary.json")
    _write_summary(summary_path, count=2)
    plan_path = workspace_tmp_dir.joinpath("plan.json")
    plan_path.write_text(
        json.dumps(
            {
                "families": [
                    {
                        "rows": 4,
                        "cols": 4,
                        "rooms": 4,
                        "count": 2,
                        "seed_start": 0,
                        "summary_file": summary_path.name,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    def fail_if_called(**_kwargs):
        raise AssertionError("complete summaries should be skipped")

    monkeypatch.setattr("src.stostone.generator.calibration_corpus.build_puzzle_corpus", fail_if_called)
    result = run_calibration_corpus_plan(plan_path, markdown_path=workspace_tmp_dir.joinpath("report.md"))

    assert result.completed
    assert result.items[0].status == "skipped"
    assert result.report["record_count"] == 1
    assert result.markdown_path is not None
    assert result.markdown_path.is_file()


def test_run_calibration_corpus_plan_force_regenerates_complete_summary(monkeypatch, workspace_tmp_dir) -> None:
    summary_path = workspace_tmp_dir.joinpath("4x4-summary.json")
    _write_summary(summary_path)
    plan_path = workspace_tmp_dir.joinpath("plan.json")
    plan_path.write_text(
        json.dumps(
            {
                "families": [
                    {
                        "rows": 4,
                        "cols": 4,
                        "rooms": 4,
                        "count": 1,
                        "seed_start": 0,
                        "summary_file": summary_path.name,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    calls = []

    def fake_build_puzzle_corpus(**kwargs):
        calls.append(kwargs)
        _write_summary(kwargs["summary_path"], count=kwargs["count"])
        return GenerationBatchResult(
            requested_count=kwargs["count"],
            generated_count=kwargs["count"],
            seeds_tried=1,
            seed_start=kwargs["seed_start"],
            seed_step=kwargs["seed_step"],
            duplicates_skipped=0,
            quality_rejected=0,
            generation_failures=0,
            output_dir=kwargs["out_dir"],
            elapsed=timedelta(seconds=0),
        )

    monkeypatch.setattr("src.stostone.generator.calibration_corpus.build_puzzle_corpus", fake_build_puzzle_corpus)
    result = run_calibration_corpus_plan(plan_path, force=True)

    assert calls
    assert result.completed
    assert result.items[0].status == "generated"
