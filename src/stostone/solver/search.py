from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from ..models import Coord, Puzzle, SolveMode
from .state_ops import domain_reduce, draw_stone, restore_cells
from .validation import is_sto_sand, is_sto_stone

logger = logging.getLogger(__name__)


class ConstraintCheckLimitReached(RuntimeError):
    pass


@dataclass(slots=True)
class _RoomCandidates:
    room_num: int
    domains: list[list[Coord]]
    delta_sizes: list[int]
    delta_column_counts: list[list[int]]
    min_delta_size: int
    max_delta_size: int
    min_delta_columns: list[int]
    max_delta_columns: list[int]


def _ensure_constraint_budget(puzzle: Puzzle, max_constraint_checks: int | None) -> None:
    if max_constraint_checks is not None and puzzle.state.constraint_checks > max_constraint_checks:
        raise ConstraintCheckLimitReached(f"Constraint-check budget reached: {max_constraint_checks}")


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


def _count_current_columns(puzzle: Puzzle) -> list[int]:
    counts = [0] * puzzle.cols
    for row in puzzle.state.grid:
        for col, cell in enumerate(row):
            if cell == " #":
                counts[col] += 1
    return counts


def _subgrid_delta_columns(subgrid: list[Coord], puzzle: Puzzle) -> tuple[int, list[int]]:
    delta_size = 0
    delta_columns = [0] * puzzle.cols
    for row, col in subgrid:
        if puzzle.state.grid[row][col] != " #":
            delta_size += 1
            delta_columns[col] += 1
    return delta_size, delta_columns


def _build_room_candidates(room_num: int, puzzle: Puzzle) -> _RoomCandidates | None:
    domains = domain_reduce(
        puzzle.cache.all_room_borders[room_num],
        puzzle.cache.all_room_domains[room_num],
        puzzle.state.grid,
    )
    if not domains:
        return None

    delta_sizes: list[int] = []
    delta_column_counts: list[list[int]] = []
    for subgrid in domains:
        delta_size, delta_columns = _subgrid_delta_columns(subgrid, puzzle)
        delta_sizes.append(delta_size)
        delta_column_counts.append(delta_columns)

    return _RoomCandidates(
        room_num=room_num,
        domains=domains,
        delta_sizes=delta_sizes,
        delta_column_counts=delta_column_counts,
        min_delta_size=min(delta_sizes),
        max_delta_size=max(delta_sizes),
        min_delta_columns=[min(columns[col] for columns in delta_column_counts) for col in range(puzzle.cols)],
        max_delta_columns=[max(columns[col] for columns in delta_column_counts) for col in range(puzzle.cols)],
    )


def _remaining_room_candidates(
    remaining_rooms: tuple[int, ...],
    puzzle: Puzzle,
) -> tuple[_RoomCandidates, ...] | None:
    candidates: list[_RoomCandidates] = []
    for room_num in remaining_rooms:
        room_candidates = _build_room_candidates(room_num, puzzle)
        if room_candidates is None:
            return None
        candidates.append(room_candidates)
    return tuple(candidates)


def _passes_forward_checks(
    *,
    shaded_cells: int,
    column_counts: list[int],
    room_candidates: tuple[_RoomCandidates, ...],
    target_cells: int,
    target_per_column: int,
    cols: int,
) -> bool:
    min_remaining_cells = sum(candidates.min_delta_size for candidates in room_candidates)
    max_remaining_cells = sum(candidates.max_delta_size for candidates in room_candidates)
    if shaded_cells + min_remaining_cells > target_cells:
        return False
    if shaded_cells + max_remaining_cells < target_cells:
        return False

    for col in range(cols):
        min_remaining_column = sum(candidates.min_delta_columns[col] for candidates in room_candidates)
        max_remaining_column = sum(candidates.max_delta_columns[col] for candidates in room_candidates)
        if column_counts[col] + min_remaining_column > target_per_column:
            return False
        if column_counts[col] + max_remaining_column < target_per_column:
            return False
    return True


def _count_solutions_mrv(
    remaining_rooms: tuple[int, ...],
    puzzle: Puzzle,
    mode: SolveMode,
    limit: int,
    max_constraint_checks: int | None,
    on_solution: Callable[[int], None] | None,
    shaded_cells: int,
    column_counts: list[int],
) -> int:
    _ensure_constraint_budget(puzzle, max_constraint_checks)
    target_cells = puzzle.rows * puzzle.cols // 2
    target_per_column = puzzle.rows // 2

    if shaded_cells > target_cells or any(count > target_per_column for count in column_counts):
        return 0

    if not remaining_rooms:
        if shaded_cells != target_cells or any(count != target_per_column for count in column_counts):
            return 0
        puzzle.state.constraint_checks += 1
        _ensure_constraint_budget(puzzle, max_constraint_checks)
        solved = _candidate_satisfies_mode(puzzle, mode, restore_state=True)
        if solved and on_solution is not None:
            on_solution(puzzle.state.constraint_checks)
        return int(solved)

    all_candidates = _remaining_room_candidates(remaining_rooms, puzzle)
    if all_candidates is None:
        return 0
    if not _passes_forward_checks(
        shaded_cells=shaded_cells,
        column_counts=column_counts,
        room_candidates=all_candidates,
        target_cells=target_cells,
        target_per_column=target_per_column,
        cols=puzzle.cols,
    ):
        return 0

    best_candidates = min(all_candidates, key=lambda candidates: (len(candidates.domains), candidates.room_num))
    next_remaining = tuple(room_num for room_num in remaining_rooms if room_num != best_candidates.room_num)
    other_candidates = tuple(candidates for candidates in all_candidates if candidates.room_num != best_candidates.room_num)

    solution_count = 0
    for subgrid, delta_size, delta_columns in zip(
        best_candidates.domains,
        best_candidates.delta_sizes,
        best_candidates.delta_column_counts,
    ):
        next_shaded_cells = shaded_cells + delta_size
        next_column_counts = [column_counts[col] + delta_columns[col] for col in range(puzzle.cols)]
        if not _passes_forward_checks(
            shaded_cells=next_shaded_cells,
            column_counts=next_column_counts,
            room_candidates=other_candidates,
            target_cells=target_cells,
            target_per_column=target_per_column,
            cols=puzzle.cols,
        ):
            continue

        draw_stone(subgrid, puzzle.state.grid)
        puzzle.state.drawn_stones[best_candidates.room_num] = subgrid
        try:
            solution_count += _count_solutions_mrv(
                next_remaining,
                puzzle,
                mode,
                limit - solution_count,
                max_constraint_checks,
                on_solution,
                next_shaded_cells,
                next_column_counts,
            )
        finally:
            restore_cells(subgrid, puzzle.state.grid, puzzle.spec.initial_state)
            puzzle.state.drawn_stones[best_candidates.room_num] = None
        if solution_count >= limit:
            return solution_count
    return solution_count


def count_solutions(
    room_num: int,
    puzzle: Puzzle,
    mode: SolveMode = "sto-stone",
    limit: int = 2,
    max_constraint_checks: int | None = None,
    on_solution: Callable[[int], None] | None = None,
) -> int:
    if limit < 1:
        raise ValueError("Solution count limit must be at least 1.")
    if room_num >= puzzle.rooms:
        remaining_rooms: tuple[int, ...] = ()
    else:
        remaining_rooms = tuple(range(room_num, puzzle.rooms))
    column_counts = _count_current_columns(puzzle)
    return _count_solutions_mrv(
        remaining_rooms,
        puzzle,
        mode,
        limit,
        max_constraint_checks,
        on_solution,
        shaded_cells=sum(column_counts),
        column_counts=column_counts,
    )
