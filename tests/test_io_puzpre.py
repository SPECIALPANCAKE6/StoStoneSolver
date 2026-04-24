from __future__ import annotations

import pytest

from src.stostone.io.puzpre import load_puzzle, load_puzzle_summary, write_puzpre
from src.stostone.models import PuzzleMetadata


pytestmark = pytest.mark.integration


def test_load_puzzle_summary_reads_known_counts_and_metadata(puzzle_path) -> None:
    summary = load_puzzle_summary(puzzle_path("000-000.txt"))

    assert summary.rows == 4
    assert summary.cols == 4
    assert summary.rooms == 5
    assert summary.numbered_rooms == 3
    assert summary.pre_shaded_cells == 0
    assert summary.author == "Addison Allen"
    assert summary.difficulty == "Easy"


def test_load_puzzle_filters_domains_to_pre_shaded_cells(puzzle_path) -> None:
    puzzle = load_puzzle(puzzle_path("001-000-1.txt"))

    rooms_with_givens = {
        room_num: {(r, c) for (r, c) in room if puzzle.spec.initial_state[r][c] == " #"}
        for room_num, room in enumerate(puzzle.cache.all_room_indices)
    }
    rooms_with_givens = {room_num: givens for room_num, givens in rooms_with_givens.items() if givens}

    assert rooms_with_givens
    for room_num, givens in rooms_with_givens.items():
        assert all(givens.issubset(set(domain)) for domain in puzzle.cache.all_room_domains[room_num])


def test_write_puzpre_round_trips_drawn_stones_and_metadata(build_puzzle, workspace_tmp_dir) -> None:
    puzzle = build_puzzle(
        2,
        2,
        [[0, 0], [0, 0]],
        initial_state=[[-1, -1], [-1, -1]],
        info_section="info:{}",
        metadata=PuzzleMetadata(author="Pytest"),
    )
    puzzle.spec.metadata.extra_fields["label"] = "roundtrip"
    puzzle.state.drawn_stones[0] = [(0, 0), (1, 0)]

    output_path = workspace_tmp_dir.joinpath("roundtrip.txt")
    write_puzpre(output_path, puzzle)
    reloaded = load_puzzle(output_path)

    assert output_path.is_file()
    assert reloaded.spec.metadata.author == "Pytest"
    assert reloaded.spec.metadata.extra_fields["label"] == "roundtrip"
    assert reloaded.spec.initial_state[0][0] == " #"
    assert reloaded.spec.initial_state[1][0] == " #"


def test_write_puzpre_round_trips_unsolved_initial_state_givens(build_puzzle, workspace_tmp_dir) -> None:
    puzzle = build_puzzle(
        2,
        2,
        [[0, 0], [0, 0]],
        initial_state=[[" #", -1], [-1, -1]],
        info_section="info:{}",
        metadata=PuzzleMetadata(author="Pytest"),
    )

    output_path = workspace_tmp_dir.joinpath("unsolved-givens.txt")
    write_puzpre(output_path, puzzle)
    reloaded = load_puzzle(output_path)

    assert output_path.is_file()
    assert reloaded.spec.initial_state[0][0] == " #"
    assert reloaded.spec.initial_state[0][1] == -1
