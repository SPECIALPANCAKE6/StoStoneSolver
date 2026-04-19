from __future__ import annotations

import pytest

from src.stostone.core.domain_gen import domainGen
from src.stostone.core.domains import connected_subgrids
from src.stostone.core.grid import border_gen, grid_bfs, grid_neighbors, is_connected
from src.stostone.core.grid_utils import borderGen, connectedSubgrids, gridBFS, gridNeighbors, isConnected
from src.stostone.solver.state_ops import reset_state


pytestmark = pytest.mark.unit


def test_grid_neighbors_respects_bounds_and_legacy_wrapper() -> None:
    assert grid_neighbors((0, 0), 2, 2) == [(1, 0), (0, 1)]
    assert set(gridNeighbors((1, 1))) == {(0, 1), (2, 1), (1, 0), (1, 2)}


def test_border_gen_returns_outside_to_room_pairs() -> None:
    coords = [(0, 0), (0, 1)]

    borders = border_gen(coords, 2, 3)

    assert ((1, 0), (0, 0)) in borders
    assert ((1, 1), (0, 1)) in borders
    assert ((0, 2), (0, 1)) in borders
    assert ((0, 1), (0, 0)) not in borders
    assert borders == borderGen(coords, 2, 3)


def test_connected_helpers_only_return_connected_subgrids() -> None:
    coords = [(0, 0), (0, 1), (1, 1)]

    subgrids = connected_subgrids(coords, 2)

    assert subgrids is not None
    assert [(0, 0), (0, 1)] in subgrids
    assert [(0, 1), (1, 1)] in subgrids
    assert [(0, 0), (1, 1)] not in subgrids
    assert connectedSubgrids(coords, 2) == subgrids
    assert domainGen(coords, 2) == subgrids
    assert grid_bfs(coords) is not None
    assert len(grid_bfs(coords) or []) == 3
    assert is_connected(coords)
    assert gridBFS([]) is None
    assert not isConnected([(0, 0), (1, 1)])


def test_reset_state_restores_initial_grid_and_tracking(build_puzzle) -> None:
    puzzle = build_puzzle(
        2,
        2,
        [[0, 1], [0, 1]],
        weights=[((0, 0), 1), None],
        initial_state=[[" #", -1], [-1, -1]],
    )

    assert puzzle.cache.all_room_indices == [[(0, 0), (1, 0)], [(0, 1), (1, 1)]]
    assert puzzle.cache.all_room_domains[0] == [[(0, 0)], [(1, 0)]]

    puzzle.state.grid[1][1] = " #"
    puzzle.state.drawn_stones[1] = [(1, 1)]
    puzzle.state.constraint_checks = 3

    reset_state(puzzle)

    assert puzzle.state.grid == puzzle.spec.initial_state
    assert puzzle.state.drawn_stones == [None, None]
    assert puzzle.state.constraint_checks == 0
