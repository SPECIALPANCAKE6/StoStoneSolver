from __future__ import annotations

import logging

from ..models import Coord, Puzzle
from .state_ops import draw_stone, restore_cells

logger = logging.getLogger(__name__)


def is_sto_sand(puzzle: Puzzle) -> bool:
    col_counter = [0] * puzzle.cols
    for r in range(puzzle.rows):
        for c in range(puzzle.cols):
            if puzzle.state.grid[r][c] == " #":
                col_counter[c] += 1
    return all(count == puzzle.rows // 2 for count in col_counter)


def fills_bottom_half(puzzle: Puzzle) -> bool:
    half = puzzle.rows // 2
    return all(puzzle.state.grid[r][c] != " #" for r in range(half) for c in range(puzzle.cols)) and all(
        puzzle.state.grid[r][c] == " #" for r in range(half, puzzle.rows) for c in range(puzzle.cols)
    )


def get_below(stone: list[Coord], rows: int) -> list[Coord | None]:
    cells_below: list[Coord | None] = [None] * len(stone)
    for index, (r, c) in enumerate(stone):
        if r + 1 < rows:
            cells_below[index] = (r + 1, c)
    return cells_below


def can_stone_drop(
    subgrid: list[Coord | None],
    state: list[list[int | str]],
    current_stone: set[Coord],
) -> bool:
    for cell in subgrid:
        if cell is None:
            return False
        if cell not in current_stone and state[cell[0]][cell[1]] != -1:
            return False
    return True


def drop_down(previous_stone: list[Coord], stone: list[Coord], state: list[list[int | str]]) -> None:
    restore_cells(previous_stone, state)
    draw_stone(stone, state)


def is_sto_stone(puzzle: Puzzle) -> bool:
    last_placed = [stone[:] if stone is not None else None for stone in puzzle.state.drawn_stones]
    logger.debug("Dropping stones")

    moved = True
    while moved:
        moved = False
        for index, stone in enumerate(last_placed):
            if stone is None:
                continue
            below = get_below(stone, puzzle.rows)
            if can_stone_drop(below, puzzle.state.grid, set(stone)):
                next_position = [cell for cell in below if cell is not None]
                drop_down(stone, next_position, puzzle.state.grid)
                last_placed[index] = next_position
                moved = True

    if fills_bottom_half(puzzle):
        logger.info("[%s] Sto-Stone check passed", puzzle.source_path or "<unknown puzzle>")
        return True

    logger.debug("[%s] Failed Sto-Stone check after dropping stones", puzzle.source_path or "<unknown puzzle>")
    for room, original_stone in enumerate(puzzle.state.drawn_stones):
        dropped_stone = last_placed[room]
        if dropped_stone is not None:
            restore_cells(dropped_stone, puzzle.state.grid)
        if original_stone is not None:
            draw_stone(original_stone, puzzle.state.grid)
    return False

