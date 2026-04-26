from __future__ import annotations

import hashlib
import json
import math
import random
from collections import Counter
from copy import deepcopy
from datetime import datetime
from pathlib import Path

from ..assembly import apply_initial_state_constraints, assemble_puzzle
from ..core.grid import grid_neighbors
from ..io.puzpre import load_puzzle, write_puzpre
from ..models import (
    GenerationBatchItem,
    GenerationBatchResult,
    GenerationFilters,
    GenerationQuality,
    GenerationResult,
    Puzzle,
    PuzzleMetadata,
    PuzzleSpec,
    SolveMode,
    WeightEntry,
    legacy_dict_to_puzzle,
)
from ..solver.service import DEFAULT_PUZZLE_DIR, SOLVE_MODES, count_puzzle_solutions, solve_puzzle
from ..solver.state_ops import domain_reduce, draw_stone, restore_cells
from ..solver.validation import is_sto_stone

DEFAULT_GENERATOR_NAME = "StoStoneSolver Generator"
DEFAULT_REVEAL_POLICY = "mostly-empty"
DEFAULT_OUTPUT_PREFIX = "generated"
REVEAL_POLICIES: tuple[str, ...] = ("mostly-empty", "empty", "single-cell", "full-room")


class GenerationFailed(RuntimeError):
    pass


def _now() -> datetime:
    return datetime.now().astimezone()


def _empty_state(rows: int, cols: int) -> list[list[int]]:
    return [[-1 for _ in range(cols)] for _ in range(rows)]


def _normalize_generation_args(
    rows: int,
    cols: int,
    rooms: int | None,
    max_attempts: int,
    uniqueness_limit: int,
    reveal_policy: str,
    mode: SolveMode,
) -> int:
    if rows <= 0 or cols <= 0:
        raise ValueError("Rows and columns must be positive integers.")
    if rows % 2 != 0:
        raise ValueError("Sto-Stone generation requires an even row count.")
    if max_attempts < 1:
        raise ValueError("Max attempts must be at least 1.")
    if uniqueness_limit < 2:
        raise ValueError("Uniqueness limit must be at least 2.")
    if reveal_policy not in REVEAL_POLICIES:
        raise ValueError(f"Unsupported reveal policy: {reveal_policy}")
    if mode not in SOLVE_MODES:
        raise ValueError(f"Unsupported solve mode: {mode}")

    half_area = rows * cols // 2
    normalized_rooms = min(cols, half_area) if rooms is None else rooms
    if normalized_rooms < 1 or normalized_rooms > half_area:
        raise ValueError("Room count must be between 1 and half the board area.")
    return normalized_rooms


def _normalize_batch_args(
    count: int,
    seed_step: int,
    max_seeds: int | None,
    out_dir: Path | str | None,
    output_prefix: str,
) -> tuple[int, Path]:
    if count < 1:
        raise ValueError("Count must be at least 1.")
    if seed_step < 1:
        raise ValueError("Seed step must be at least 1.")
    if max_seeds is not None and max_seeds < count:
        raise ValueError("Max seeds must be at least the requested count.")
    if not output_prefix:
        raise ValueError("Output prefix must not be empty.")

    output_dir = DEFAULT_PUZZLE_DIR if out_dir is None else Path(out_dir)
    if output_dir.exists() and not output_dir.is_dir():
        raise ValueError("Output directory path must refer to a directory.")
    return (count * 20 if max_seeds is None else max_seeds), output_dir


def _generate_connected_layout(
    rows: int,
    cols: int,
    rooms: int,
    rng: random.Random,
) -> tuple[list[list[int]], list[list[tuple[int, int]]]]:
    cells = [(r, c) for r in range(rows) for c in range(cols)]
    seeds = rng.sample(cells, rooms)
    layout = [[-1 for _ in range(cols)] for _ in range(rows)]
    room_cells: list[list[tuple[int, int]]] = [[] for _ in range(rooms)]
    frontiers = [set() for _ in range(rooms)]
    unassigned = set(cells)

    for room_num, seed in enumerate(seeds):
        r, c = seed
        layout[r][c] = room_num
        room_cells[room_num].append(seed)
        unassigned.remove(seed)

    for room_num, seed in enumerate(seeds):
        for neighbor in grid_neighbors(seed, rows, cols):
            if neighbor in unassigned:
                frontiers[room_num].add(neighbor)

    while unassigned:
        candidate_rooms = sorted(
            (room_num for room_num, frontier in enumerate(frontiers) if frontier),
            key=lambda room_num: (len(room_cells[room_num]), room_num),
        )
        if not candidate_rooms:
            raise GenerationFailed("Room layout growth stalled before all cells were assigned.")

        room_num = rng.choice(candidate_rooms[: min(3, len(candidate_rooms))])
        room_coord_set = set(room_cells[room_num])
        seed_row, seed_col = seeds[room_num]
        cell = min(
            frontiers[room_num],
            key=lambda coord: (
                -sum(neighbor in room_coord_set for neighbor in grid_neighbors(coord, rows, cols)),
                abs(coord[0] - seed_row) + abs(coord[1] - seed_col),
                coord[0],
                coord[1],
            ),
        )

        r, c = cell
        layout[r][c] = room_num
        room_cells[room_num].append(cell)
        unassigned.remove(cell)

        for frontier in frontiers:
            frontier.discard(cell)
        for neighbor in grid_neighbors(cell, rows, cols):
            if neighbor in unassigned:
                frontiers[room_num].add(neighbor)

    return layout, room_cells


def _build_weight_entries(
    room_cells: list[list[tuple[int, int]]],
    weight_values: list[int],
    rng: random.Random,
) -> list[WeightEntry]:
    return [(rng.choice(tuple(room_coords)), weight_values[room_num]) for room_num, room_coords in enumerate(room_cells)]


def _copy_weights(weights: list[WeightEntry]) -> list[WeightEntry]:
    return [None if weight is None else ((weight[0][0], weight[0][1]), weight[1]) for weight in weights]


def _count_given_cells(initial_state: list[list[int | str]]) -> int:
    return sum(cell == " #" for row in initial_state for cell in row)


def _count_numbered_rooms(weights: list[WeightEntry]) -> int:
    return sum(weight is not None for weight in weights)


def _choose_applied_reveal_policy(requested_policy: str, rng: random.Random) -> str:
    if requested_policy != DEFAULT_REVEAL_POLICY:
        return requested_policy

    roll = rng.random()
    if roll < 0.8:
        return "empty"
    if roll < 0.95:
        return "single-cell"
    return "full-room"


def _build_initial_state(
    rows: int,
    cols: int,
    drawn_stones: list[list[tuple[int, int]] | None],
    requested_reveal_policy: str,
    rng: random.Random,
) -> tuple[list[list[int | str]], str, int, int]:
    initial_state: list[list[int | str]] = _empty_state(rows, cols)
    room_stones = [stone for stone in drawn_stones if stone]
    applied_reveal_policy = _choose_applied_reveal_policy(requested_reveal_policy, rng)

    if not room_stones or applied_reveal_policy == "empty":
        return initial_state, "empty", 0, 0

    if applied_reveal_policy == "single-cell":
        stone = rng.choice(room_stones)
        coord = rng.choice(stone)
        initial_state[coord[0]][coord[1]] = " #"
        return initial_state, "single-cell", 1, 0

    if applied_reveal_policy == "full-room":
        stone = rng.choice(room_stones)
        for r, c in stone:
            initial_state[r][c] = " #"
        return initial_state, "full-room", len(stone), 1

    raise ValueError(f"Unsupported applied reveal policy: {applied_reveal_policy}")


def _build_generation_metadata(
    *,
    generator_name: str,
    seed: int,
    generated_at: datetime,
    attempts: int,
    elapsed,
    requested_reveal_policy: str,
    applied_reveal_policy: str,
    given_shaded_cells: int,
    pre_solved_rooms: int,
    uniqueness_limit: int,
    solution_count: int,
    rows: int,
    cols: int,
    rooms: int,
    numbered_rooms: int,
    numbered_rooms_before_carving: int,
    clue_carving_enabled: bool,
    clue_carving_checks: int,
) -> PuzzleMetadata:
    return PuzzleMetadata(
        author=generator_name,
        extra_fields={
            "generator": generator_name,
            "generation_strategy": "solution-first",
            "layout_strategy": "balanced-frontier",
            "generator_seed": str(seed),
            "generated_at": generated_at.isoformat(),
            "generated_timezone": generated_at.tzname() or str(generated_at.tzinfo) or "Unknown",
            "generation_attempts": str(attempts),
            "generation_elapsed": str(elapsed),
            "generation_elapsed_seconds": f"{elapsed.total_seconds():.6f}",
            "requested_reveal_policy": requested_reveal_policy,
            "applied_reveal_policy": applied_reveal_policy,
            "given_shaded_cells": str(given_shaded_cells),
            "pre_solved_rooms": str(pre_solved_rooms),
            "uniqueness_limit": str(uniqueness_limit),
            "solution_count": str(solution_count),
            "rows": str(rows),
            "cols": str(cols),
            "rooms": str(rooms),
            "numbered_rooms": str(numbered_rooms),
            "numbered_rooms_before_carving": str(numbered_rooms_before_carving),
            "clue_carving_enabled": str(clue_carving_enabled).lower(),
            "clue_carving_strategy": "greedy-number-removal" if clue_carving_enabled else "disabled",
            "clue_carving_checks": str(clue_carving_checks),
            "clue_carving_removed_numbered_rooms": str(numbered_rooms_before_carving - numbered_rooms),
        },
    )


def _build_solution_search_puzzle(rows: int, cols: int, rooms: int, rng: random.Random) -> Puzzle:
    layout, _ = _generate_connected_layout(rows, cols, rooms, rng)
    spec = PuzzleSpec(
        rows=rows,
        cols=cols,
        rooms=rooms,
        layout=layout,
        weights=[None] * rooms,
        initial_state=_empty_state(rows, cols),
        metadata=PuzzleMetadata(),
    )
    return assemble_puzzle(spec)


def _count_subgrid_columns(subgrid: list[tuple[int, int]], cols: int) -> list[int]:
    counts = [0] * cols
    for _, col in subgrid:
        counts[col] += 1
    return counts


def _state_satisfies_mode(puzzle: Puzzle, mode: SolveMode) -> bool:
    if mode == "sto-sand":
        return True

    original_state = [row[:] for row in puzzle.state.grid]
    try:
        return is_sto_stone(puzzle)
    finally:
        puzzle.state.grid[:] = original_state


def _candidate_order_key(
    room_num: int,
    subgrid: list[tuple[int, int]],
    subgrid_columns: list[int],
    column_counts: list[int],
    target_per_column: int,
    size_frequencies: list[Counter[int]],
) -> tuple[int, int, int, int]:
    pressure_gain = sum((target_per_column - column_counts[col]) * subgrid_columns[col] for col in range(len(column_counts)))
    row_values = [coord[0] for coord in subgrid]
    col_values = [coord[1] for coord in subgrid]
    span = (max(row_values) - min(row_values)) + (max(col_values) - min(col_values))
    return (
        size_frequencies[room_num][len(subgrid)],
        -pressure_gain,
        span,
        -len(subgrid),
    )


def _find_solution_witness(puzzle: Puzzle, mode: SolveMode) -> list[list[tuple[int, int]]] | None:
    half_area = puzzle.rows * puzzle.cols // 2
    target_per_column = puzzle.rows // 2
    room_capacities = [len(room_indices) for room_indices in puzzle.cache.all_room_indices]
    room_column_capacities = [
        _count_subgrid_columns(room_indices, puzzle.cols) for room_indices in puzzle.cache.all_room_indices
    ]
    size_frequencies = [
        Counter(len(subgrid) for subgrid in room_domains) for room_domains in puzzle.cache.all_room_domains
    ]
    column_counts = [0] * puzzle.cols
    remaining_rooms = set(range(puzzle.rooms))

    def feasible_candidates(
        room_num: int,
        active_rooms: set[int],
        shaded_cells: int,
    ) -> list[tuple[list[tuple[int, int]], list[int]]]:
        reduced_domain = domain_reduce(
            puzzle.cache.all_room_borders[room_num],
            puzzle.cache.all_room_domains[room_num],
            puzzle.state.grid,
        )
        other_rooms = active_rooms - {room_num}
        min_remaining_cells = len(other_rooms)
        max_remaining_cells = sum(room_capacities[other_room] for other_room in other_rooms)
        remaining_column_capacity = [
            sum(room_column_capacities[other_room][col] for other_room in other_rooms)
            for col in range(puzzle.cols)
        ]

        candidates: list[tuple[list[tuple[int, int]], list[int]]] = []
        for subgrid in reduced_domain:
            subgrid_size = len(subgrid)
            remaining_area = half_area - shaded_cells - subgrid_size
            if remaining_area < min_remaining_cells or remaining_area > max_remaining_cells:
                continue

            subgrid_columns = _count_subgrid_columns(subgrid, puzzle.cols)
            if any(column_counts[col] + subgrid_columns[col] > target_per_column for col in range(puzzle.cols)):
                continue
            if any(
                column_counts[col] + subgrid_columns[col] + remaining_column_capacity[col] < target_per_column
                for col in range(puzzle.cols)
            ):
                continue

            candidates.append((subgrid, subgrid_columns))

        candidates.sort(
            key=lambda item: _candidate_order_key(
                room_num,
                item[0],
                item[1],
                column_counts,
                target_per_column,
                size_frequencies,
            )
        )
        return candidates

    def search(shaded_cells: int) -> bool:
        if not remaining_rooms:
            if shaded_cells != half_area or any(count != target_per_column for count in column_counts):
                return False
            return _state_satisfies_mode(puzzle, mode)

        best_room: int | None = None
        best_candidates: list[tuple[list[tuple[int, int]], list[int]]] | None = None
        for room_num in sorted(remaining_rooms):
            candidates = feasible_candidates(room_num, remaining_rooms, shaded_cells)
            if not candidates:
                return False
            if best_candidates is None or len(candidates) < len(best_candidates):
                best_room = room_num
                best_candidates = candidates

        assert best_room is not None
        assert best_candidates is not None

        remaining_rooms.remove(best_room)
        for subgrid, subgrid_columns in best_candidates:
            draw_stone(subgrid, puzzle.state.grid)
            puzzle.state.drawn_stones[best_room] = subgrid
            for col, count in enumerate(subgrid_columns):
                column_counts[col] += count

            if search(shaded_cells + len(subgrid)):
                remaining_rooms.add(best_room)
                return True

            for col, count in enumerate(subgrid_columns):
                column_counts[col] -= count
            restore_cells(subgrid, puzzle.state.grid, puzzle.spec.initial_state)
            puzzle.state.drawn_stones[best_room] = None

        remaining_rooms.add(best_room)
        return False

    if not search(0):
        return None

    ordered_witness: list[list[tuple[int, int]]] = []
    for room_num in range(puzzle.rooms):
        stone = puzzle.state.drawn_stones[room_num]
        if stone is None:
            raise GenerationFailed("Constructive generation produced an incomplete witness.")
        ordered_witness.append(stone[:])
    return ordered_witness


def _build_weighted_candidate_puzzle(
    solution_search_puzzle: Puzzle,
    witness: list[list[tuple[int, int]]],
    rng: random.Random,
) -> Puzzle:
    weight_values = [len(stone) for stone in witness]
    spec = PuzzleSpec(
        rows=solution_search_puzzle.rows,
        cols=solution_search_puzzle.cols,
        rooms=solution_search_puzzle.rooms,
        layout=[row[:] for row in solution_search_puzzle.spec.layout],
        weights=_build_weight_entries(solution_search_puzzle.cache.all_room_indices, weight_values, rng),
        initial_state=_empty_state(solution_search_puzzle.rows, solution_search_puzzle.cols),
        metadata=PuzzleMetadata(),
    )
    return assemble_puzzle(spec)


def _assemble_generated_puzzle(
    template_puzzle: Puzzle,
    weights: list[WeightEntry],
    initial_state: list[list[int | str]],
    metadata: PuzzleMetadata | None = None,
) -> Puzzle:
    return apply_initial_state_constraints(
        assemble_puzzle(
            PuzzleSpec(
                rows=template_puzzle.rows,
                cols=template_puzzle.cols,
                rooms=template_puzzle.rooms,
                layout=[row[:] for row in template_puzzle.spec.layout],
                weights=_copy_weights(weights),
                initial_state=[row[:] for row in initial_state],
                metadata=PuzzleMetadata() if metadata is None else metadata,
            )
        )
    )


def _carve_number_clues(
    template_puzzle: Puzzle,
    weights: list[WeightEntry],
    initial_state: list[list[int | str]],
    *,
    mode: SolveMode,
    uniqueness_limit: int,
    rng: random.Random,
) -> tuple[list[WeightEntry], int]:
    current_weights = _copy_weights(weights)
    room_order = list(range(template_puzzle.rooms))
    rng.shuffle(room_order)
    carving_checks = 0

    for room_num in room_order:
        if current_weights[room_num] is None:
            continue

        trial_weights = _copy_weights(current_weights)
        trial_weights[room_num] = None
        carving_checks += 1
        count_result = count_puzzle_solutions(
            _assemble_generated_puzzle(template_puzzle, trial_weights, initial_state),
            mode=mode,
            limit=uniqueness_limit,
        )
        if count_result.solution_count == 1:
            current_weights = trial_weights

    return current_weights, carving_checks


def _clone_puzzle(puzzle: Puzzle) -> Puzzle:
    return legacy_dict_to_puzzle(deepcopy(puzzle.to_legacy_dict()))


def _room_shape_compactness(room_indices: list[tuple[int, int]]) -> float:
    rows = [coord[0] for coord in room_indices]
    cols = [coord[1] for coord in room_indices]
    bounding_area = (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)
    return len(room_indices) / bounding_area


def _difficulty_from_score(score: float) -> str:
    if score < 25:
        return "Easy"
    if score < 50:
        return "Medium"
    if score < 75:
        return "Hard"
    return "Expert"


def _score_generation_quality(
    *,
    solve_iterations: int,
    room_balance: float,
    shape_compactness: float,
    given_shaded_cells: int,
    pre_solved_rooms: int,
) -> float:
    iteration_component = min(70.0, math.log2(solve_iterations + 1) * 10.0)
    imbalance_bonus = (1.0 - room_balance) * 15.0
    irregularity_bonus = (1.0 - shape_compactness) * 15.0
    clue_penalty = given_shaded_cells * 8.0 + pre_solved_rooms * 12.0
    return max(0.0, min(100.0, iteration_component + imbalance_bonus + irregularity_bonus - clue_penalty))


def _build_generation_quality(result: GenerationResult, mode: SolveMode) -> GenerationQuality:
    room_sizes = [len(room_indices) for room_indices in result.puzzle.cache.all_room_indices]
    room_size_min = min(room_sizes)
    room_size_max = max(room_sizes)
    room_size_spread = room_size_max - room_size_min
    room_balance = room_size_min / room_size_max
    shape_compactness = sum(_room_shape_compactness(room_indices) for room_indices in result.puzzle.cache.all_room_indices) / len(
        result.puzzle.cache.all_room_indices
    )

    solve_result = solve_puzzle(_clone_puzzle(result.puzzle), mode=mode)
    if not solve_result.solved or solve_result.puzzle is None:
        raise GenerationFailed("Generated puzzle could not be re-solved for quality scoring.")

    solve_iterations = solve_result.puzzle.state.constraint_checks
    difficulty_score = _score_generation_quality(
        solve_iterations=solve_iterations,
        room_balance=room_balance,
        shape_compactness=shape_compactness,
        given_shaded_cells=result.given_shaded_cells,
        pre_solved_rooms=result.pre_solved_rooms,
    )
    return GenerationQuality(
        room_size_min=room_size_min,
        room_size_max=room_size_max,
        room_size_spread=room_size_spread,
        room_balance=room_balance,
        shape_compactness=shape_compactness,
        given_shaded_cells=result.given_shaded_cells,
        pre_solved_rooms=result.pre_solved_rooms,
        solve_iterations=solve_iterations,
        solve_elapsed=solve_result.elapsed,
        difficulty_score=difficulty_score,
        difficulty=_difficulty_from_score(difficulty_score),
    )


def _annotate_quality_metadata(result: GenerationResult) -> None:
    quality = result.quality
    if quality is None:
        return

    result.puzzle.spec.metadata.difficulty = quality.difficulty
    result.puzzle.spec.metadata.extra_fields.update(
        {
            "room_size_min": str(quality.room_size_min),
            "room_size_max": str(quality.room_size_max),
            "room_size_spread": str(quality.room_size_spread),
            "room_balance": f"{quality.room_balance:.6f}",
            "shape_compactness": f"{quality.shape_compactness:.6f}",
            "generator_solve_iterations": str(quality.solve_iterations),
            "generator_solve_elapsed": str(quality.solve_elapsed),
            "generator_solve_elapsed_seconds": f"{quality.solve_elapsed.total_seconds():.6f}",
            "difficulty_score": f"{quality.difficulty_score:.6f}",
            "difficulty_label": quality.difficulty,
        }
    )


def quality_rejection_reason(quality: GenerationQuality, filters: GenerationFilters) -> str | None:
    reasons: list[str] = []
    if filters.min_room_balance is not None and quality.room_balance < filters.min_room_balance:
        reasons.append(f"room balance {quality.room_balance:.3f} < {filters.min_room_balance:.3f}")
    if filters.min_shape_compactness is not None and quality.shape_compactness < filters.min_shape_compactness:
        reasons.append(f"shape compactness {quality.shape_compactness:.3f} < {filters.min_shape_compactness:.3f}")
    if filters.max_room_size_spread is not None and quality.room_size_spread > filters.max_room_size_spread:
        reasons.append(f"room size spread {quality.room_size_spread} > {filters.max_room_size_spread}")
    if filters.max_given_shaded_cells is not None and quality.given_shaded_cells > filters.max_given_shaded_cells:
        reasons.append(f"given shaded cells {quality.given_shaded_cells} > {filters.max_given_shaded_cells}")
    if filters.max_pre_solved_rooms is not None and quality.pre_solved_rooms > filters.max_pre_solved_rooms:
        reasons.append(f"pre-solved rooms {quality.pre_solved_rooms} > {filters.max_pre_solved_rooms}")
    if filters.min_solve_iterations is not None and quality.solve_iterations < filters.min_solve_iterations:
        reasons.append(f"solve iterations {quality.solve_iterations} < {filters.min_solve_iterations}")
    if filters.max_solve_iterations is not None and quality.solve_iterations > filters.max_solve_iterations:
        reasons.append(f"solve iterations {quality.solve_iterations} > {filters.max_solve_iterations}")
    if filters.min_difficulty_score is not None and quality.difficulty_score < filters.min_difficulty_score:
        reasons.append(f"difficulty score {quality.difficulty_score:.2f} < {filters.min_difficulty_score:.2f}")
    if filters.max_difficulty_score is not None and quality.difficulty_score > filters.max_difficulty_score:
        reasons.append(f"difficulty score {quality.difficulty_score:.2f} > {filters.max_difficulty_score:.2f}")
    return "; ".join(reasons) or None


def _canonical_puzzle_signature(puzzle: Puzzle) -> str:
    room_map: dict[int, int] = {}
    next_room = 0
    normalized_layout: list[list[int]] = []
    for row in puzzle.spec.layout:
        normalized_row: list[int] = []
        for room_num in row:
            if room_num not in room_map:
                room_map[room_num] = next_room
                next_room += 1
            normalized_row.append(room_map[room_num])
        normalized_layout.append(normalized_row)

    weight_values = [0] * puzzle.rooms
    for room_num, weight_entry in enumerate(puzzle.spec.weights):
        weight_values[room_map[room_num]] = 0 if weight_entry is None else weight_entry[1]

    initial_state = [[1 if cell == " #" else 0 for cell in row] for row in puzzle.spec.initial_state]
    payload = {
        "layout": normalized_layout,
        "weights": weight_values,
        "initial_state": initial_state,
    }
    return hashlib.sha256(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")).hexdigest()


def _load_existing_signatures(output_dir: Path) -> set[str]:
    signatures: set[str] = set()
    if not output_dir.exists():
        return signatures

    for puzzle_path in sorted(output_dir.glob("*.txt")):
        try:
            signatures.add(_canonical_puzzle_signature(load_puzzle(puzzle_path)))
        except Exception:
            continue
    return signatures


def _default_output_path(output_dir: Path, prefix: str, puzzle: Puzzle, seed: int) -> Path:
    return output_dir.joinpath(f"{prefix}-{puzzle.rows}x{puzzle.cols}-{puzzle.rooms}r-seed{seed}.txt")


def _next_available_output_path(path: Path) -> Path:
    if not path.exists():
        return path

    index = 1
    while True:
        candidate = path.with_name(f"{path.stem}-{index}{path.suffix}")
        if not candidate.exists():
            return candidate
        index += 1


def write_generated_puzzle(
    result: GenerationResult,
    *,
    output_path: Path | str | None = None,
    output_dir: Path | str | None = None,
    output_prefix: str = DEFAULT_OUTPUT_PREFIX,
    overwrite: bool = False,
) -> Path:
    if output_path is not None and output_dir is not None:
        raise ValueError("Choose either an explicit output path or an output directory, not both.")

    if output_path is not None:
        target_path = Path(output_path)
    else:
        target_dir = DEFAULT_PUZZLE_DIR if output_dir is None else Path(output_dir)
        target_path = _default_output_path(target_dir, output_prefix, result.puzzle, result.seed)

    if target_path.exists() and target_path.is_dir():
        raise ValueError("Output path must be a file path, not a directory.")

    final_path = target_path if overwrite else _next_available_output_path(target_path)
    write_puzpre(final_path, result.puzzle)
    return final_path.resolve()


def write_generation_summary(path: Path | str, batch_result: GenerationBatchResult) -> Path:
    summary_path = Path(path)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w", encoding="utf-8", newline="\n") as file:
        json.dump(batch_result.to_legacy_dict(), file, indent=2, default=str)
    return summary_path.resolve()


def generate_unique_puzzle(
    *,
    rows: int = 4,
    cols: int = 4,
    rooms: int | None = None,
    seed: int | None = None,
    max_attempts: int = 256,
    uniqueness_limit: int = 2,
    reveal_policy: str = DEFAULT_REVEAL_POLICY,
    mode: SolveMode = "sto-stone",
    generator_name: str = DEFAULT_GENERATOR_NAME,
    clue_carving: bool = True,
) -> GenerationResult:
    normalized_rooms = _normalize_generation_args(rows, cols, rooms, max_attempts, uniqueness_limit, reveal_policy, mode)
    normalized_seed = random.SystemRandom().randrange(0, 2**63) if seed is None else seed
    rng = random.Random(normalized_seed)
    started_at = _now()

    for attempt in range(1, max_attempts + 1):
        solution_search_puzzle = _build_solution_search_puzzle(rows, cols, normalized_rooms, rng)
        witness = _find_solution_witness(solution_search_puzzle, mode)
        if witness is None:
            continue

        candidate = _build_weighted_candidate_puzzle(solution_search_puzzle, witness, rng)
        count_result = count_puzzle_solutions(candidate, mode=mode, limit=uniqueness_limit)
        if count_result.solution_count != 1:
            continue

        initial_state, applied_reveal_policy, given_shaded_cells, pre_solved_rooms = _build_initial_state(
            rows,
            cols,
            witness,
            reveal_policy,
            rng,
        )
        numbered_rooms_before_carving = _count_numbered_rooms(candidate.spec.weights)
        carved_weights = _copy_weights(candidate.spec.weights)
        clue_carving_checks = 0
        if clue_carving:
            carved_weights, clue_carving_checks = _carve_number_clues(
                candidate,
                candidate.spec.weights,
                initial_state,
                mode=mode,
                uniqueness_limit=uniqueness_limit,
                rng=rng,
            )

        final_numbered_rooms = _count_numbered_rooms(carved_weights)
        final_given_shaded_cells = given_shaded_cells
        final_pre_solved_rooms = pre_solved_rooms
        generated_at = _now()
        elapsed = generated_at - started_at
        metadata = _build_generation_metadata(
            generator_name=generator_name,
            seed=normalized_seed,
            generated_at=generated_at,
            attempts=attempt,
            elapsed=elapsed,
            requested_reveal_policy=reveal_policy,
            applied_reveal_policy=applied_reveal_policy,
            given_shaded_cells=final_given_shaded_cells,
            pre_solved_rooms=final_pre_solved_rooms,
            uniqueness_limit=uniqueness_limit,
            solution_count=count_result.solution_count,
            rows=rows,
            cols=cols,
            rooms=normalized_rooms,
            numbered_rooms=final_numbered_rooms,
            numbered_rooms_before_carving=numbered_rooms_before_carving,
            clue_carving_enabled=clue_carving,
            clue_carving_checks=clue_carving_checks,
        )
        generated_puzzle = _assemble_generated_puzzle(candidate, carved_weights, initial_state, metadata)
        result = GenerationResult(
            puzzle=generated_puzzle,
            seed=normalized_seed,
            attempts=attempt,
            uniqueness_limit=uniqueness_limit,
            elapsed=elapsed,
            requested_reveal_policy=reveal_policy,
            applied_reveal_policy=applied_reveal_policy,
            given_shaded_cells=final_given_shaded_cells,
            pre_solved_rooms=final_pre_solved_rooms,
            numbered_rooms=final_numbered_rooms,
            numbered_rooms_before_carving=numbered_rooms_before_carving,
            clue_carving_enabled=clue_carving,
            clue_carving_checks=clue_carving_checks,
            solution_count=count_result.solution_count,
        )
        result.quality = _build_generation_quality(result, mode)
        _annotate_quality_metadata(result)
        return result

    raise GenerationFailed(
        f"Unable to generate a unique {rows}x{cols} puzzle with {normalized_rooms} rooms after {max_attempts} attempts."
    )


def build_puzzle_corpus(
    *,
    count: int,
    rows: int = 4,
    cols: int = 4,
    rooms: int | None = None,
    seed_start: int | None = None,
    seed_step: int = 1,
    max_seeds: int | None = None,
    out_dir: Path | str | None = None,
    output_prefix: str = DEFAULT_OUTPUT_PREFIX,
    max_attempts: int = 256,
    uniqueness_limit: int = 2,
    reveal_policy: str = DEFAULT_REVEAL_POLICY,
    mode: SolveMode = "sto-stone",
    generator_name: str = DEFAULT_GENERATOR_NAME,
    clue_carving: bool = True,
    filters: GenerationFilters | None = None,
    allow_duplicates: bool = False,
    summary_path: Path | str | None = None,
) -> GenerationBatchResult:
    normalized_rooms = _normalize_generation_args(rows, cols, rooms, max_attempts, uniqueness_limit, reveal_policy, mode)
    max_seed_attempts, output_dir = _normalize_batch_args(count, seed_step, max_seeds, out_dir, output_prefix)
    filters = GenerationFilters() if filters is None else filters
    normalized_seed_start = random.SystemRandom().randrange(0, 2**63) if seed_start is None else seed_start
    output_dir.mkdir(parents=True, exist_ok=True)

    seen_signatures = set() if allow_duplicates else _load_existing_signatures(output_dir)
    items: list[GenerationBatchItem] = []
    generated_count = 0
    duplicates_skipped = 0
    quality_rejected = 0
    generation_failures = 0
    started_at = _now()

    for seed_index in range(max_seed_attempts):
        seed = normalized_seed_start + (seed_index * seed_step)
        try:
            result = generate_unique_puzzle(
                rows=rows,
                cols=cols,
                rooms=normalized_rooms,
                seed=seed,
                max_attempts=max_attempts,
                uniqueness_limit=uniqueness_limit,
                reveal_policy=reveal_policy,
                mode=mode,
                generator_name=generator_name,
                clue_carving=clue_carving,
            )
        except GenerationFailed as exc:
            generation_failures += 1
            items.append(GenerationBatchItem(seed=seed, status="failed", reason=str(exc)))
            continue

        if result.quality is None:
            raise GenerationFailed("Generated puzzle is missing quality metrics.")

        signature = _canonical_puzzle_signature(result.puzzle)
        if not allow_duplicates and signature in seen_signatures:
            duplicates_skipped += 1
            items.append(
                GenerationBatchItem(
                    seed=seed,
                    status="duplicate",
                    signature=signature,
                    generation=result,
                    quality=result.quality,
                    reason="Duplicate puzzle signature already present in corpus.",
                )
            )
            continue

        rejection_reason = quality_rejection_reason(result.quality, filters)
        if rejection_reason is not None:
            quality_rejected += 1
            items.append(
                GenerationBatchItem(
                    seed=seed,
                    status="rejected-quality",
                    signature=signature,
                    generation=result,
                    quality=result.quality,
                    reason=rejection_reason,
                )
            )
            continue

        seen_signatures.add(signature)
        output_path = write_generated_puzzle(
            result,
            output_dir=output_dir,
            output_prefix=output_prefix,
            overwrite=False,
        )
        generated_count += 1
        items.append(
            GenerationBatchItem(
                seed=seed,
                status="written",
                output_path=output_path,
                signature=signature,
                generation=result,
                quality=result.quality,
            )
        )
        if generated_count >= count:
            break

    batch_result = GenerationBatchResult(
        requested_count=count,
        generated_count=generated_count,
        seeds_tried=min(max_seed_attempts, len(items)),
        seed_start=normalized_seed_start,
        seed_step=seed_step,
        duplicates_skipped=duplicates_skipped,
        quality_rejected=quality_rejected,
        generation_failures=generation_failures,
        output_dir=output_dir.resolve(),
        elapsed=_now() - started_at,
        items=items,
    )
    if summary_path is not None:
        batch_result.summary_path = write_generation_summary(summary_path, batch_result)
    return batch_result
