from __future__ import annotations

import pytest

from src.stostone.solver.domain_builder import domainReduce, drawStone, unDraw
from src.stostone.solver.state_ops import domain_reduce, draw_stone, reset_state, restore_cells


pytestmark = pytest.mark.unit


def test_domain_reduce_rejects_border_conflicts() -> None:
    state = [[-1, -1], [" #", -1]]
    borders = [((1, 0), (0, 0))]
    domain = [[(0, 0)], [(0, 1)]]

    reduced = domain_reduce(borders, domain, state)

    assert reduced == [[(0, 1)]]
    assert domainReduce(borders, domain, state) == reduced


def test_draw_and_restore_cells_respect_initial_state() -> None:
    initial_state = [[" #", -1], [-1, -1]]
    state = [[-1, -1], [-1, -1]]

    draw_stone([(0, 0), (1, 1)], state)
    drawStone([(0, 1)], state)
    restore_cells([(0, 0), (1, 1)], state, initial_state)
    unDraw([(0, 1)], state, initial_state)

    assert state == initial_state


def test_reset_state_clears_runtime_mutation(build_puzzle) -> None:
    puzzle = build_puzzle(2, 2, [[0, 0], [0, 0]])
    puzzle.state.grid[0][0] = " #"
    puzzle.state.drawn_stones[0] = [(0, 0)]
    puzzle.state.constraint_checks = 9

    reset_state(puzzle)

    assert puzzle.state.grid == puzzle.spec.initial_state
    assert puzzle.state.drawn_stones == [None]
    assert puzzle.state.constraint_checks == 0
