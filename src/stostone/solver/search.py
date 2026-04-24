from __future__ import annotations

import logging

from ..models import Puzzle, SolveMode
from .state_ops import domain_reduce, draw_stone, restore_cells
from .validation import is_sto_sand, is_sto_stone

logger = logging.getLogger(__name__)


def _candidate_satisfies_mode(puzzle: Puzzle, mode: SolveMode, *, restore_state: bool = False) -> bool:
    iteration = puzzle.state.constraint_checks
    sto_sand = is_sto_sand(puzzle)
    if mode == "sto-sand":
        if sto_sand:
            logger.info("[%s] Sto-Sand check passed at iteration %s", puzzle.source_path or "<unknown puzzle>", iteration)
        return sto_sand
    if sto_sand:
        logger.info("[%s] Sto-Sand check passed at iteration %s", puzzle.source_path or "<unknown puzzle>", iteration)
    if not sto_sand:
        return False

    if not restore_state:
        return is_sto_stone(puzzle)

    original_state = [row[:] for row in puzzle.state.grid]
    try:
        return is_sto_stone(puzzle)
    finally:
        puzzle.state.grid[:] = original_state


def backtrack(room_num: int, puzzle: Puzzle, mode: SolveMode = "sto-stone") -> bool:
    if room_num >= puzzle.rooms:
        puzzle.state.constraint_checks += 1
        return _candidate_satisfies_mode(puzzle, mode)

    reduced_domain = domain_reduce(
        puzzle.cache.all_room_borders[room_num],
        puzzle.cache.all_room_domains[room_num],
        puzzle.state.grid,
    )
    for subgrid in reduced_domain:
        draw_stone(subgrid, puzzle.state.grid)
        puzzle.state.drawn_stones[room_num] = subgrid
        if backtrack(room_num + 1, puzzle, mode):
            return True
        restore_cells(subgrid, puzzle.state.grid, puzzle.spec.initial_state)
        puzzle.state.drawn_stones[room_num] = None
    return False


def count_solutions(room_num: int, puzzle: Puzzle, mode: SolveMode = "sto-stone", limit: int = 2) -> int:
    if limit < 1:
        raise ValueError("Solution count limit must be at least 1.")

    if room_num >= puzzle.rooms:
        puzzle.state.constraint_checks += 1
        return int(_candidate_satisfies_mode(puzzle, mode, restore_state=True))

    solution_count = 0
    reduced_domain = domain_reduce(
        puzzle.cache.all_room_borders[room_num],
        puzzle.cache.all_room_domains[room_num],
        puzzle.state.grid,
    )
    for subgrid in reduced_domain:
        draw_stone(subgrid, puzzle.state.grid)
        puzzle.state.drawn_stones[room_num] = subgrid
        solution_count += count_solutions(room_num + 1, puzzle, mode=mode, limit=limit - solution_count)
        restore_cells(subgrid, puzzle.state.grid, puzzle.spec.initial_state)
        puzzle.state.drawn_stones[room_num] = None
        if solution_count >= limit:
            return solution_count
    return solution_count
