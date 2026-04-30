from __future__ import annotations

import hashlib
import json
import subprocess
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Literal

from ..generator import GenerationFailed, generate_unique_puzzle
from ..io.puzpre import load_puzzle
from ..models import GenerationResult, Puzzle, SolveMode
from ..solver.service import count_puzzle_solutions, resolve_puzzle_target
from ..solver.state_ops import domain_reduce, draw_stone, restore_cells
from ..solver.validation import is_sto_sand, is_sto_stone

PACK_SCHEMA_VERSION = "1.0.0"
RULESET = "sto-stone"
RULESET_VERSION = "1.0"
SOLUTION_USAGE_SCOPE = "local_mvp_dev_only"
PackType = Literal["local_mvp", "dev", "debug", "public", "competitive"]


@dataclass(frozen=True, slots=True)
class SourcePuzzleSpec:
    path: str
    category: str = "library"
    difficulty: str | None = None
    title: str | None = None
    tutorial_message: str | None = None


@dataclass(frozen=True, slots=True)
class GeneratedPuzzleSpec:
    count: int
    category: str
    rows: int
    cols: int
    rooms: int
    seed_start: int
    difficulty_preset: str | None = None
    reveal_policy: str = "empty"
    max_attempts: int = 32
    max_seeds: int = 128


@dataclass(frozen=True, slots=True)
class PackExportResult:
    pack_path: Path
    build_report_path: Path
    pack: dict[str, object]
    build_report: dict[str, object]


STARTER_SOURCE_PUZZLES: tuple[SourcePuzzleSpec, ...] = (
    SourcePuzzleSpec(
        "000-001.txt",
        category="tutorial",
        difficulty="Tutorial",
        title="First Stone",
        tutorial_message="Shade a connected shape inside each numbered room, then check how the stones fall.",
    ),
    SourcePuzzleSpec(
        "000-002.txt",
        category="tutorial",
        difficulty="Tutorial",
        title="Room Counts",
        tutorial_message="Use room numbers as exact shaded-cell counts before testing the full drop.",
    ),
    SourcePuzzleSpec(
        "162-001.txt",
        category="tutorial",
        difficulty="Tutorial",
        title="No Touching Across Rooms",
        tutorial_message="Shaded cells may touch inside a room, but they cannot touch across a room border.",
    ),
    SourcePuzzleSpec("162-002.txt", category="easy", difficulty="Easy", title="Small Steps"),
    SourcePuzzleSpec("MG-001-001.txt", category="easy", difficulty="Easy", title="Mind Games Easy"),
    SourcePuzzleSpec("001-001.txt", category="medium", difficulty="Medium", title="Tall Drop"),
    SourcePuzzleSpec("YP-001.txt", category="medium", difficulty="Medium", title="Yellow Medium"),
    SourcePuzzleSpec("162-004-corrected.txt", category="medium", difficulty="Medium", title="Corrected Rooms"),
    SourcePuzzleSpec("162-005.txt", category="medium", difficulty="Medium", title="Middle Weight"),
    SourcePuzzleSpec("162-006.txt", category="medium", difficulty="Medium", title="Steady Descent"),
)

STARTER_GENERATED_PUZZLES: tuple[GeneratedPuzzleSpec, ...] = (
    GeneratedPuzzleSpec(
        count=3,
        category="easy",
        rows=4,
        cols=4,
        rooms=4,
        seed_start=200,
        difficulty_preset="easy",
        reveal_policy="empty",
        max_attempts=20,
        max_seeds=20,
    ),
    GeneratedPuzzleSpec(
        count=1,
        category="showcase",
        rows=6,
        cols=6,
        rooms=6,
        seed_start=702,
        difficulty_preset="hard",
        reveal_policy="empty",
        max_attempts=32,
        max_seeds=8,
    ),
)


def _json_dumps_canonical(payload: dict[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _room_map(layout: list[list[int]]) -> dict[int, int]:
    mapping: dict[int, int] = {}
    next_room = 0
    for row in layout:
        for room_id in row:
            if room_id not in mapping:
                mapping[room_id] = next_room
                next_room += 1
    return mapping


def _normalized_layout(puzzle: Puzzle, mapping: dict[int, int]) -> list[list[int]]:
    return [[mapping[room_id] for room_id in row] for row in puzzle.spec.layout]


def _normalized_weights(puzzle: Puzzle, mapping: dict[int, int]) -> list[dict[str, object]]:
    weights: list[dict[str, object]] = []
    for original_room_id, weight_entry in enumerate(puzzle.spec.weights):
        if weight_entry is None:
            continue
        (row, col), value = weight_entry
        weights.append(
            {
                "room_id": mapping[original_room_id],
                "cell": [row, col],
                "value": value,
            }
        )
    return sorted(weights, key=lambda item: (int(item["room_id"]), item["cell"][0], item["cell"][1]))


def _initial_state_coords(puzzle: Puzzle) -> list[list[int]]:
    coords = [
        [row, col]
        for row, cells in enumerate(puzzle.spec.initial_state)
        for col, cell in enumerate(cells)
        if cell == " #"
    ]
    return sorted(coords)


def canonical_puzzle_payload(puzzle: Puzzle) -> dict[str, object]:
    mapping = _room_map(puzzle.spec.layout)
    return {
        "ruleset": RULESET,
        "ruleset_version": RULESET_VERSION,
        "rows": puzzle.rows,
        "cols": puzzle.cols,
        "rooms": len(mapping),
        "layout": _normalized_layout(puzzle, mapping),
        "weights": _normalized_weights(puzzle, mapping),
        "initial_state": _initial_state_coords(puzzle),
    }


def canonical_puzzle_hash(puzzle: Puzzle) -> str:
    return hashlib.sha256(_json_dumps_canonical(canonical_puzzle_payload(puzzle)).encode("utf-8")).hexdigest()


def puzzle_id_for_hash(canonical_hash: str) -> str:
    return f"puz_{canonical_hash[:16]}"


def _metadata_dict(puzzle: Puzzle) -> dict[str, str | None]:
    return puzzle.spec.metadata.to_legacy_dict()


def _difficulty_for(
    puzzle: Puzzle,
    *,
    override: str | None,
    generation: GenerationResult | None,
) -> dict[str, object]:
    if generation is not None and generation.quality is not None:
        return {
            "label": generation.quality.difficulty,
            "score": generation.quality.difficulty_score,
            "scale": generation.difficulty_scale,
            "family": generation.difficulty_family,
            "solve_iterations": generation.quality.solve_iterations,
        }
    label = override or puzzle.spec.metadata.difficulty or "Unrated"
    return {
        "label": label,
        "score": None,
        "scale": "source-label",
        "family": f"{puzzle.rows}x{puzzle.cols}-{puzzle.rooms}r",
        "solve_iterations": None,
    }


def _source_metadata(
    *,
    puzzle: Puzzle,
    source_path: Path | None,
    generation: GenerationResult | None,
) -> dict[str, object]:
    metadata = _metadata_dict(puzzle)
    if generation is not None:
        return {
            "kind": "generated",
            "path": None,
            "generator_seed": generation.seed,
            "generator": metadata.get("generator"),
            "generation_strategy": metadata.get("generation_strategy"),
            "requested_reveal_policy": generation.requested_reveal_policy,
            "applied_reveal_policy": generation.applied_reveal_policy,
        }
    return {
        "kind": "puzpre",
        "path": None if source_path is None else str(source_path),
        "author": puzzle.spec.metadata.author,
        "comment": puzzle.spec.metadata.comment,
    }


def _normalized_room_stones(puzzle: Puzzle) -> dict[str, list[list[int]]]:
    stones: dict[str, list[list[int]]] = {}
    for room_id, stone in enumerate(puzzle.state.drawn_stones):
        if stone is None:
            continue
        stones[str(room_id)] = sorted([[row, col] for row, col in stone])
    return stones


def _all_shaded_from_stones(stones_by_room_id: dict[str, list[list[int]]]) -> list[list[int]]:
    shaded = {tuple(cell) for stone in stones_by_room_id.values() for cell in stone}
    return [list(cell) for cell in sorted(shaded)]


def _simulate_drop(rows: int, stones_by_room_id: dict[str, list[list[int]]]) -> dict[str, list[list[int]]]:
    stones = {room_id: [tuple(cell) for cell in cells] for room_id, cells in stones_by_room_id.items()}

    def occupied_without(room_id: str) -> set[tuple[int, int]]:
        return {cell for other_room, cells in stones.items() if other_room != room_id for cell in cells}

    moved = True
    while moved:
        moved = False
        for room_id in sorted(stones, key=lambda value: int(value)):
            stone = stones[room_id]
            below = [(row + 1, col) for row, col in stone]
            if any(row >= rows for row, _ in below):
                continue
            blocked = occupied_without(room_id)
            if any(cell in blocked for cell in below):
                continue
            stones[room_id] = below
            moved = True

    return {room_id: [list(cell) for cell in sorted(cells)] for room_id, cells in stones.items()}


def _find_solution_stones(puzzle: Puzzle) -> tuple[dict[str, list[list[int]]], int]:
    working = deepcopy(puzzle)
    working.state.constraint_checks = 0

    def search(remaining_rooms: tuple[int, ...]) -> dict[str, list[list[int]]] | None:
        if not remaining_rooms:
            working.state.constraint_checks += 1
            if not is_sto_sand(working):
                return None
            original_grid = [row[:] for row in working.state.grid]
            original_stones = _normalized_room_stones(working)
            try:
                if is_sto_stone(working):
                    return original_stones
            finally:
                working.state.grid[:] = original_grid
            return None

        room_domains: list[tuple[int, list[list[tuple[int, int]]]]] = []
        for room_id in remaining_rooms:
            domains = domain_reduce(
                working.cache.all_room_borders[room_id],
                working.cache.all_room_domains[room_id],
                working.state.grid,
            )
            if not domains:
                return None
            room_domains.append((room_id, domains))

        room_id, domains = min(room_domains, key=lambda item: (len(item[1]), item[0]))
        next_remaining = tuple(candidate for candidate in remaining_rooms if candidate != room_id)
        for subgrid in domains:
            draw_stone(subgrid, working.state.grid)
            working.state.drawn_stones[room_id] = subgrid
            try:
                solution = search(next_remaining)
                if solution is not None:
                    return solution
            finally:
                restore_cells(subgrid, working.state.grid, working.spec.initial_state)
                working.state.drawn_stones[room_id] = None
        return None

    stones = search(tuple(range(working.rooms)))
    if stones is None:
        raise ValueError("Puzzle has no Sto-Stone solution.")
    return stones, working.state.constraint_checks


def _solve_for_solution(puzzle: Puzzle) -> tuple[dict[str, object], int]:
    stones_by_room_id, constraint_checks = _find_solution_stones(puzzle)
    shaded_cells = _all_shaded_from_stones(stones_by_room_id)
    final_stones_by_room_id = _simulate_drop(puzzle.rows, stones_by_room_id)
    final_filled_cells = _all_shaded_from_stones(final_stones_by_room_id)
    solution_id = "sol_" + hashlib.sha256(
        _json_dumps_canonical({"shaded_cells": shaded_cells, "stones_by_room_id": stones_by_room_id}).encode("utf-8")
    ).hexdigest()[:16]
    return (
        {
            "schema_version": PACK_SCHEMA_VERSION,
            "puzzle_id": "",
            "solution_id": solution_id,
            "usage_scope": SOLUTION_USAGE_SCOPE,
            "shaded_cells": shaded_cells,
            "stones_by_room_id": stones_by_room_id,
            "drop_preview": {
                "start_stones_by_room_id": stones_by_room_id,
                "final_stones_by_room_id": final_stones_by_room_id,
                "final_filled_cells": final_filled_cells,
            },
        },
        constraint_checks,
    )


def _first_weighted_room(puzzle: Puzzle) -> tuple[int, int] | None:
    for room_id, weight_entry in enumerate(puzzle.spec.weights):
        if weight_entry is not None:
            return room_id, weight_entry[1]
    return None


def _build_hint_plan(
    *,
    puzzle: Puzzle,
    solution: dict[str, object] | None,
    category: str,
    tutorial_message: str | None,
    allow_solution_hints: bool,
) -> list[dict[str, object]]:
    hints: list[dict[str, object]] = []
    if category == "tutorial" and tutorial_message:
        hints.append({"kind": "tutorial", "message": tutorial_message})

    weighted_room = _first_weighted_room(puzzle)
    if weighted_room is not None:
        room_id, value = weighted_room
        hints.append(
            {
                "kind": "room_focus",
                "room_id": room_id,
                "message": f"Room {room_id + 1} must contain exactly {value} shaded cell(s).",
            }
        )

    if allow_solution_hints and solution is not None:
        givens = {tuple(cell) for cell in _initial_state_coords(puzzle)}
        for cell in solution["shaded_cells"]:  # type: ignore[index]
            cell_tuple = tuple(cell)
            if cell_tuple not in givens:
                hints.append(
                    {
                        "kind": "reveal_cell",
                        "cell": cell,
                        "message": f"Cell [{cell[0]}, {cell[1]}] is part of the solution.",
                    }
                )
                break
        hints.append(
            {
                "kind": "drop_preview",
                "message": "Preview the rigid stone fall to see whether the bottom half fills cleanly.",
            }
        )

    if not hints:
        hints.append({"kind": "room_focus", "message": "Start with a numbered room and keep its shaded cells connected."})
    return hints


def _puzzle_to_dto(
    *,
    puzzle: Puzzle,
    puzzle_id: str,
    canonical_hash: str,
    source_path: Path | None,
    category: str,
    title: str | None,
    difficulty: dict[str, object],
    generation: GenerationResult | None,
    uniqueness: dict[str, object],
    tutorial_message: str | None,
) -> dict[str, object]:
    mapping = _room_map(puzzle.spec.layout)
    dto: dict[str, object] = {
        "schema_version": PACK_SCHEMA_VERSION,
        "puzzle_id": puzzle_id,
        "canonical_hash": canonical_hash,
        "ruleset": RULESET,
        "ruleset_version": RULESET_VERSION,
        "rows": puzzle.rows,
        "cols": puzzle.cols,
        "rooms": len(mapping),
        "layout": _normalized_layout(puzzle, mapping),
        "weights": _normalized_weights(puzzle, mapping),
        "initial_state": _initial_state_coords(puzzle),
        "difficulty": difficulty,
        "category": category,
        "title": title or puzzle_id,
        "source": _source_metadata(puzzle=puzzle, source_path=source_path, generation=generation),
        "metadata": _metadata_dict(puzzle),
        "unique_solution_proof": uniqueness,
    }
    if tutorial_message:
        dto["tutorial"] = {"message": tutorial_message}
    return dto


def _git_commit(base_dir: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=base_dir,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _source_specs_for_starter() -> list[SourcePuzzleSpec]:
    return list(STARTER_SOURCE_PUZZLES)


def _generated_specs_for_starter() -> list[GeneratedPuzzleSpec]:
    return list(STARTER_GENERATED_PUZZLES)


def _iter_generated_puzzles(spec: GeneratedPuzzleSpec) -> tuple[list[tuple[Puzzle, GenerationResult]], list[int], int]:
    accepted: list[tuple[Puzzle, GenerationResult]] = []
    generated_seeds: list[int] = []
    rejected = 0
    seed = spec.seed_start
    seeds_tried = 0
    while len(accepted) < spec.count and seeds_tried < spec.max_seeds:
        try:
            result = generate_unique_puzzle(
                rows=spec.rows,
                cols=spec.cols,
                rooms=spec.rooms,
                seed=seed,
                max_attempts=spec.max_attempts,
                reveal_policy=spec.reveal_policy,
                difficulty_preset=spec.difficulty_preset,
            )
        except GenerationFailed:
            rejected += 1
        else:
            accepted.append((result.puzzle, result))
            generated_seeds.append(seed)
        seed += 1
        seeds_tried += 1
    if len(accepted) < spec.count:
        raise GenerationFailed(f"Generated {len(accepted)} of {spec.count} requested {spec.category} puzzle(s).")
    return accepted, generated_seeds, rejected


def export_pack(
    *,
    output_path: Path | str,
    pack_id: str = "starter_pack",
    title: str = "StoStone Starter Pack",
    description: str = "Local MVP starter puzzles for the StoStone Godot app.",
    pack_type: PackType = "local_mvp",
    puzzle_dir: Path | str | None = None,
    source_specs: list[SourcePuzzleSpec] | None = None,
    generated_specs: list[GeneratedPuzzleSpec] | None = None,
    starter: bool = False,
    mode: SolveMode = "sto-stone",
) -> PackExportResult:
    if mode != "sto-stone":
        raise ValueError("Godot MVP pack export currently supports only Sto-Stone mode.")
    if pack_type in ("public", "competitive"):
        contains_solutions = False
        contains_debug_data = False
    else:
        contains_solutions = True
        contains_debug_data = pack_type == "debug"

    output = Path(output_path)
    base_dir = Path(__file__).resolve().parents[3]
    resolved_puzzle_dir = base_dir.joinpath("puzzles") if puzzle_dir is None else Path(puzzle_dir)
    sources = list(source_specs or [])
    generators = list(generated_specs or [])
    if starter:
        sources = _source_specs_for_starter() + sources
        generators = _generated_specs_for_starter() + generators
    if not sources and not generators:
        raise ValueError("Provide at least one source puzzle, generated puzzle spec, or --starter.")

    puzzles_by_id: dict[str, object] = {}
    solutions_by_puzzle_id: dict[str, object] = {}
    hint_plans_by_puzzle_id: dict[str, object] = {}
    categories: dict[str, int] = {}
    uniqueness_results: dict[str, object] = {}
    solve_iterations: list[int] = []
    source_files: list[str] = []
    generated_seeds: list[int] = []
    rejected_count = 0
    duplicate_count = 0
    item_reports: list[dict[str, object]] = []

    def add_puzzle(
        *,
        puzzle: Puzzle,
        source_path: Path | None,
        category: str,
        difficulty_override: str | None,
        title_override: str | None,
        tutorial_message: str | None,
        generation: GenerationResult | None,
    ) -> None:
        nonlocal duplicate_count, rejected_count
        digest = canonical_puzzle_hash(puzzle)
        puzzle_id = puzzle_id_for_hash(digest)
        if puzzle_id in puzzles_by_id:
            duplicate_count += 1
            return

        count_result = count_puzzle_solutions(deepcopy(puzzle), mode=mode, limit=2)
        uniqueness = {
            "mode": mode,
            "solution_count": count_result.solution_count,
            "search_limit": count_result.search_limit,
            "is_unique": count_result.is_unique,
            "constraint_checks": count_result.puzzle.state.constraint_checks if count_result.puzzle is not None else 0,
            "elapsed_seconds": count_result.elapsed.total_seconds(),
        }
        if not count_result.is_unique:
            rejected_count += 1
            return

        solution, solve_checks = _solve_for_solution(puzzle)
        solve_iterations.append(solve_checks)
        solution["puzzle_id"] = puzzle_id
        difficulty = _difficulty_for(puzzle, override=difficulty_override, generation=generation)
        dto = _puzzle_to_dto(
            puzzle=puzzle,
            puzzle_id=puzzle_id,
            canonical_hash=digest,
            source_path=source_path,
            category=category,
            title=title_override,
            difficulty=difficulty,
            generation=generation,
            uniqueness=uniqueness,
            tutorial_message=tutorial_message,
        )

        puzzles_by_id[puzzle_id] = dto
        if contains_solutions:
            solutions_by_puzzle_id[puzzle_id] = solution
        hint_plans_by_puzzle_id[puzzle_id] = _build_hint_plan(
            puzzle=puzzle,
            solution=solution if contains_solutions else None,
            category=category,
            tutorial_message=tutorial_message,
            allow_solution_hints=contains_solutions,
        )
        categories[category] = categories.get(category, 0) + 1
        uniqueness_results[puzzle_id] = uniqueness
        item_reports.append(
            {
                "puzzle_id": puzzle_id,
                "title": dto["title"],
                "category": category,
                "difficulty": difficulty["label"],
                "source": dto["source"],
                "canonical_hash": digest,
                "solve_iterations": solve_checks,
                "uniqueness": uniqueness,
            }
        )

    for source in sources:
        path = resolve_puzzle_target(source.path, resolved_puzzle_dir)
        source_files.append(str(path))
        add_puzzle(
            puzzle=load_puzzle(path),
            source_path=path,
            category=source.category,
            difficulty_override=source.difficulty,
            title_override=source.title,
            tutorial_message=source.tutorial_message,
            generation=None,
        )

    generator_options: list[dict[str, object]] = []
    for generator in generators:
        generator_options.append(
            {
                "count": generator.count,
                "category": generator.category,
                "rows": generator.rows,
                "cols": generator.cols,
                "rooms": generator.rooms,
                "seed_start": generator.seed_start,
                "difficulty_preset": generator.difficulty_preset,
                "reveal_policy": generator.reveal_policy,
                "max_attempts": generator.max_attempts,
                "max_seeds": generator.max_seeds,
            }
        )
        generated, seeds, rejected = _iter_generated_puzzles(generator)
        generated_seeds.extend(seeds)
        rejected_count += rejected
        for puzzle, generation in generated:
            add_puzzle(
                puzzle=puzzle,
                source_path=None,
                category=generator.category,
                difficulty_override=None,
                title_override=f"Generated {generator.category.title()} {generation.seed}",
                tutorial_message=None,
                generation=generation,
            )

    difficulty_distribution: dict[str, int] = {}
    for puzzle in puzzles_by_id.values():
        difficulty = puzzle["difficulty"]["label"]  # type: ignore[index]
        difficulty_distribution[difficulty] = difficulty_distribution.get(difficulty, 0) + 1

    pack = {
        "schema_version": PACK_SCHEMA_VERSION,
        "pack_id": pack_id,
        "pack_type": pack_type,
        "contains_solutions": contains_solutions,
        "contains_debug_data": contains_debug_data,
        "manifest": {
            "title": title,
            "description": description,
            "puzzle_count": len(puzzles_by_id),
            "categories": categories,
            "schema_major": int(PACK_SCHEMA_VERSION.split(".", 1)[0]),
            "solution_data_notice": "SolutionDTO data is local-MVP/dev convenience data only and is not valid for competitive, paid, rewarded, or server-authoritative modes.",
        },
        "puzzles_by_id": puzzles_by_id,
        "solutions_by_puzzle_id": solutions_by_puzzle_id,
        "hint_plans_by_puzzle_id": hint_plans_by_puzzle_id,
    }

    exported_at = datetime.now().astimezone().isoformat()
    iteration_summary = {
        "min": min(solve_iterations) if solve_iterations else None,
        "max": max(solve_iterations) if solve_iterations else None,
        "average": mean(solve_iterations) if solve_iterations else None,
    }
    build_report = {
        "schema_version": PACK_SCHEMA_VERSION,
        "pack_id": pack_id,
        "pack_type": pack_type,
        "export_timestamp": exported_at,
        "git_commit": _git_commit(base_dir),
        "source_puzpre_files": source_files,
        "generated_seeds": generated_seeds,
        "generator_options": generator_options,
        "rejected_puzzle_count": rejected_count,
        "duplicate_count": duplicate_count,
        "uniqueness_count_results": uniqueness_results,
        "difficulty_distribution": difficulty_distribution,
        "solve_iterations": iteration_summary,
        "items": item_reports,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(pack, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    report_path = output.with_suffix(".build_report.json")
    report_path.write_text(json.dumps(build_report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return PackExportResult(
        pack_path=output.resolve(),
        build_report_path=report_path.resolve(),
        pack=pack,
        build_report=build_report,
    )
