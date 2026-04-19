from __future__ import annotations

from pathlib import Path

import pytest

from src.stostone.models import PuzzleMetadata, PuzzleSummary, legacy_dict_to_puzzle, metadata_from_legacy_dict, sync_legacy_dict


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


def test_legacy_puzzle_round_trip_preserves_state_and_source(build_puzzle) -> None:
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

    legacy = puzzle.to_legacy_dict()
    restored = legacy_dict_to_puzzle(legacy)

    assert restored.source_path == puzzle.source_path
    assert restored.state.grid == puzzle.state.grid
    assert restored.state.drawn_stones == puzzle.state.drawn_stones
    assert restored.state.constraint_checks == 7

    synced = {"stale": True}
    sync_legacy_dict(synced, restored)

    assert "stale" not in synced
    assert synced["constraintChecks"] == 7
    assert synced["metadata"]["author"] == "Pytest"
