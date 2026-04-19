from __future__ import annotations

import pytest

from src.stostone.solver.validation import can_stone_drop, fills_bottom_half, get_below, is_sto_sand, is_sto_stone


pytestmark = pytest.mark.unit


def test_is_sto_sand_uses_column_counts_only(build_puzzle) -> None:
    puzzle = build_puzzle(4, 2, [[0, 0], [0, 0], [0, 0], [0, 0]])
    puzzle.state.grid = [[" #", -1], [-1, " #"], [" #", -1], [-1, " #"]]

    assert is_sto_sand(puzzle)

    puzzle.state.grid[0][0] = -1

    assert not is_sto_sand(puzzle)


def test_get_below_and_can_stone_drop_require_all_destinations_open() -> None:
    stone = [(0, 0), (1, 0)]
    below = get_below(stone, 4)
    state = [[" #"], [" #"], [-1], [-1]]

    assert below == [(1, 0), (2, 0)]
    assert can_stone_drop(below, state, set(stone))

    state[2][0] = " #"

    assert not can_stone_drop(below, state, set(stone))


def test_is_sto_stone_restores_original_state_after_failed_drop(build_puzzle) -> None:
    puzzle = build_puzzle(4, 2, [[0, 0], [0, 0], [0, 0], [0, 0]])
    puzzle.state.grid[0][0] = " #"
    puzzle.state.drawn_stones[0] = [(0, 0)]

    assert not is_sto_stone(puzzle)
    assert puzzle.state.grid == [[" #", -1], [-1, -1], [-1, -1], [-1, -1]]


def test_is_sto_stone_drops_rigid_shape_into_bottom_half(build_puzzle) -> None:
    puzzle = build_puzzle(4, 2, [[0, 0], [0, 0], [0, 0], [0, 0]])
    top_block = [(0, 0), (0, 1), (1, 0), (1, 1)]

    for r, c in top_block:
        puzzle.state.grid[r][c] = " #"
    puzzle.state.drawn_stones[0] = top_block

    assert is_sto_stone(puzzle)
    assert fills_bottom_half(puzzle)
    assert puzzle.state.grid == [[-1, -1], [-1, -1], [" #", " #"], [" #", " #"]]
