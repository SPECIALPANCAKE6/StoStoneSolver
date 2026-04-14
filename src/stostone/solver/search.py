from __future__ import annotations

import logging

from ..models import Puzzle, SolveMode
from .state_ops import domain_reduce, draw_stone, restore_cells
from .validation import is_sto_sand, is_sto_stone

logger = logging.getLogger(__name__)


def backtrack(room_num: int, puzzle: Puzzle, mode: SolveMode = "sto-stone") -> bool:
    if room_num >= puzzle.rooms:
        puzzle.state.constraint_checks += 1
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
        return is_sto_stone(puzzle)

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

