from __future__ import annotations

import json

import pytest

from src.stostone.engine import engine


pytestmark = pytest.mark.integration


def test_engine_load_and_summarize_share_same_puzzle_metadata(puzzle_path) -> None:
    puzzle = engine.load(puzzle_path("000-000.txt"))
    summary = engine.summarize(puzzle_path("000-000.txt"))

    assert puzzle.rows == 4
    assert summary.rooms == puzzle.rooms == 5
    assert summary.author == "Addison Allen"
    assert summary.difficulty == "Easy"


@pytest.mark.regression
def test_engine_solve_and_count_cover_app_facing_solver_api(puzzle_path) -> None:
    solved = engine.solve(puzzle_path("000-000.txt"))
    unique = engine.count(puzzle_path("000-001.txt"), limit=2)

    assert solved.solved
    assert solved.mode == "sto-stone"
    assert solved.puzzle is not None
    assert solved.puzzle.state.constraint_checks > 0

    assert unique.solution_count == 1
    assert unique.is_unique
    assert unique.puzzle is not None
    assert unique.puzzle.state.constraint_checks > 0


@pytest.mark.regression
def test_engine_generate_and_generate_corpus_expose_generation_surface(workspace_tmp_dir) -> None:
    single = engine.generate(rows=4, cols=4, rooms=4, seed=1, max_attempts=20, difficulty_preset="easy", clue_profile="guided")
    summary_path = workspace_tmp_dir.joinpath("engine-corpus-summary.json")
    corpus_dir = workspace_tmp_dir.joinpath("engine-corpus")
    batch = engine.generate_corpus(
        count=2,
        rows=4,
        cols=4,
        rooms=4,
        seed_start=0,
        max_seeds=10,
        reveal_policy="empty",
        out_dir=corpus_dir,
        summary_path=summary_path,
    )

    assert single.solution_count == 1
    assert single.quality is not None
    assert single.puzzle.spec.metadata.difficulty == single.quality.difficulty
    assert single.difficulty_preset == "easy"
    assert single.difficulty_family == "4x4-4r"
    assert single.difficulty_scale == "calibrated"
    assert single.clue_profile == "guided"
    assert single.requested_reveal_policy == "few-cells"

    assert batch.generated_count == 2
    assert batch.requested_count == 2
    assert batch.summary_path == summary_path.resolve()
    assert len(list(corpus_dir.glob("*.txt"))) == 2


def test_engine_calibrate_corpus_exposes_plan_runner(workspace_tmp_dir) -> None:
    summary_path = workspace_tmp_dir.joinpath("4x4-summary.json")
    plan_path = workspace_tmp_dir.joinpath("plan.json")
    report_path = workspace_tmp_dir.joinpath("report.md")
    summary = {
        "requested_count": 1,
        "generated_count": 1,
        "items": [
            {
                "seed": 1,
                "status": "written",
                "signature": "engine-calibration-sig",
                "generation": {
                    "rows": 4,
                    "cols": 4,
                    "rooms": 4,
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
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
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

    result = engine.calibrate_corpus(plan_path, report_path=report_path)

    assert result.completed
    assert result.items[0].status == "skipped"
    assert result.report["record_count"] == 1
    assert report_path.is_file()
