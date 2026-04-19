from __future__ import annotations

from pathlib import Path

import pytest

from src.stostone.compat import printFormatGrid, readPuzzle, readPuzzleMetadata
from src.stostone.compat.backtrack import backtrack, isStoSand, isStoStone
from src.stostone.compat.solver_runner import output_puzpre


pytestmark = pytest.mark.integration


def test_read_puzzle_metadata_matches_known_summary(puzzle_path) -> None:
    metadata = readPuzzleMetadata(puzzle_path("000-000.txt"))

    assert metadata["rows"] == 4
    assert metadata["cols"] == 4
    assert metadata["rooms"] == 5
    assert metadata["numbered_rooms"] == 3
    assert metadata["author"] == "Addison Allen"
    assert metadata["difficulty"] == "Easy"


def test_read_puzzle_returns_legacy_shape(puzzle_path) -> None:
    puzzle = readPuzzle(puzzle_path("000-000.txt"))

    for key in (
        "rows",
        "cols",
        "rooms",
        "layout",
        "weights",
        "initialState",
        "state",
        "allRoomIndices",
        "allRoomBorders",
        "allRoomDomains",
        "drawnStones",
    ):
        assert key in puzzle

    assert puzzle["rows"] == 4
    assert puzzle["drawnStones"] == [None] * puzzle["rooms"]


@pytest.mark.regression
def test_backtrack_wrapper_solves_and_updates_legacy_dict(puzzle_path) -> None:
    puzzle = readPuzzle(puzzle_path("000-000.txt"))

    assert backtrack(0, puzzle)
    assert all(stone is not None for stone in puzzle["drawnStones"])
    assert isStoSand(puzzle)
    assert puzzle["state"] == [[-1, -1, -1, -1], [-1, -1, -1, -1], [" #", " #", " #", " #"], [" #", " #", " #", " #"]]


def test_output_puzpre_writes_file_from_legacy_dict(puzzle_path, workspace_tmp_dir: Path) -> None:
    puzzle = readPuzzle(puzzle_path("000-000.txt"))
    assert backtrack(0, puzzle)

    output_path = workspace_tmp_dir.joinpath("legacy-output.txt")
    output_puzpre(output_path, puzzle)

    assert output_path.is_file()
    assert " #" in printFormatGrid(puzzle["state"])
