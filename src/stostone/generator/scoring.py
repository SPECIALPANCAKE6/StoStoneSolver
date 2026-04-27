from __future__ import annotations

import math

DIFFICULTY_SCORE_MODEL = "solver-log-area-v2"
LARGE_BOARD_SCORE_AREA = 64


def iteration_difficulty_component(*, solve_iterations: int, rows: int, cols: int) -> float:
    if solve_iterations < 0:
        raise ValueError("Solve iterations must not be negative.")

    board_area = rows * cols
    if board_area >= LARGE_BOARD_SCORE_AREA:
        return min(90.0, math.log2(solve_iterations + 1) * 8.0)
    return min(70.0, math.log2(solve_iterations + 1) * 10.0)


def score_generation_quality(
    *,
    solve_iterations: int,
    rows: int,
    cols: int,
    room_balance: float,
    shape_compactness: float,
    given_shaded_cells: int,
    pre_solved_rooms: int,
) -> float:
    iteration_component = iteration_difficulty_component(
        solve_iterations=solve_iterations,
        rows=rows,
        cols=cols,
    )
    imbalance_bonus = (1.0 - room_balance) * 15.0
    irregularity_bonus = (1.0 - shape_compactness) * 15.0
    clue_penalty = given_shaded_cells * 8.0 + pre_solved_rooms * 12.0
    return max(0.0, min(100.0, iteration_component + imbalance_bonus + irregularity_bonus - clue_penalty))


__all__ = [
    "DIFFICULTY_SCORE_MODEL",
    "LARGE_BOARD_SCORE_AREA",
    "iteration_difficulty_component",
    "score_generation_quality",
]
