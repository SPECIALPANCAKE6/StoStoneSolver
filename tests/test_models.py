from __future__ import annotations

from pathlib import Path

import pytest

from datetime import timedelta

from src.stostone.models import GenerationBatchItem, GenerationBatchResult, GenerationFilters, GenerationQuality, PuzzleMetadata, PuzzleSummary, SolutionCountResult, metadata_from_legacy_dict


pytestmark = pytest.mark.unit


def test_metadata_from_legacy_dict_maps_known_and_extra_fields() -> None:
    metadata = metadata_from_legacy_dict(
        {
            "author": "Addison Allen",
            "hard": "Hard",
            "comment": "demo",
            "custom_tag": "value",
        }
    )

    assert metadata.author == "Addison Allen"
    assert metadata.difficulty == "Hard"
    assert metadata.comment == "demo"
    assert metadata.extra_fields == {"custom_tag": "value"}
    assert metadata.to_legacy_dict()["custom_tag"] == "value"


def test_puzzle_summary_to_legacy_dict_uses_nested_metadata() -> None:
    summary = PuzzleSummary(
        rows=4,
        cols=4,
        rooms=5,
        numbered_rooms=3,
        pre_shaded_cells=0,
        metadata=PuzzleMetadata(author="Addison Allen", difficulty="Easy"),
        path=Path("puzzles/000-000.txt"),
    )

    legacy = summary.to_legacy_dict()

    assert legacy["author"] == "Addison Allen"
    assert legacy["difficulty"] == "Easy"
    assert legacy["path"] == Path("puzzles/000-000.txt")


def test_puzzle_keeps_mutable_runtime_state(build_puzzle) -> None:
    puzzle = build_puzzle(
        2,
        2,
        [[0, 0], [0, 0]],
        weights=[((0, 0), 2)],
        initial_state=[[-1, -1], [-1, -1]],
        metadata=PuzzleMetadata(author="Pytest"),
    )
    puzzle.source_path = Path("puzzles/000-000.txt").resolve()
    puzzle.state.grid[0][1] = " #"
    puzzle.state.drawn_stones[0] = [(0, 1)]
    puzzle.state.constraint_checks = 7

    assert puzzle.source_path == Path("puzzles/000-000.txt").resolve()
    assert puzzle.state.grid[0][1] == " #"
    assert puzzle.state.drawn_stones == [[(0, 1)]]
    assert puzzle.state.constraint_checks == 7


def test_solution_count_result_exposes_limit_and_uniqueness_flags() -> None:
    result = SolutionCountResult(
        path=Path("puzzles/000-000.txt"),
        mode="sto-stone",
        solution_count=1,
        search_limit=2,
        elapsed=timedelta(milliseconds=5),
    )

    legacy = result.to_legacy_dict()

    assert result.is_unique
    assert not result.limit_reached
    assert legacy["solution_count"] == 1
    assert legacy["is_unique"] is True


def test_generation_quality_and_batch_models_round_trip_to_legacy_dict() -> None:
    quality = GenerationQuality(
        room_size_min=2,
        room_size_max=4,
        room_size_spread=2,
        room_balance=0.5,
        shape_compactness=0.75,
        given_shaded_cells=1,
        pre_solved_rooms=0,
        solve_iterations=42,
        solve_elapsed=timedelta(milliseconds=12),
        difficulty_score=38.5,
        difficulty="Medium",
    )
    filters = GenerationFilters(min_room_balance=0.4, max_solve_iterations=200)
    item = GenerationBatchItem(seed=7, status="written", output_path=Path("puzzles/generated.txt"), quality=quality)
    batch = GenerationBatchResult(
        requested_count=2,
        generated_count=1,
        seeds_tried=1,
        seed_start=7,
        seed_step=1,
        duplicates_skipped=0,
        quality_rejected=0,
        generation_failures=0,
        output_dir=Path("puzzles"),
        elapsed=timedelta(seconds=1),
        items=[item],
    )

    assert quality.to_legacy_dict()["difficulty"] == "Medium"
    assert filters.to_legacy_dict()["min_room_balance"] == 0.4
    assert item.to_legacy_dict()["status"] == "written"
    assert batch.to_legacy_dict()["generated_count"] == 1
