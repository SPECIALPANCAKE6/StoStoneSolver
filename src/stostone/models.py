from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Literal

Coord = tuple[int, int]
Border = tuple[Coord, Coord]
WeightEntry = tuple[Coord, int] | None
Cell = int | str
CellGrid = list[list[Cell]]
LayoutGrid = list[list[int]]
Stone = list[Coord] | None
SolveMode = Literal["sto-stone", "sto-sand", "both"]
GenerationItemStatus = Literal["written", "duplicate", "rejected-quality", "failed"]


@dataclass(slots=True)
class PuzzleMetadata:
    author: str | None = None
    difficulty: str | None = None
    comment: str | None = None
    solver: str | None = None
    solve_mode: str | None = None
    solved_at: str | None = None
    solved_timezone: str | None = None
    solve_iterations: str | None = None
    solve_elapsed: str | None = None
    solve_elapsed_seconds: str | None = None
    extra_fields: dict[str, str] = field(default_factory=dict)

    def to_legacy_dict(self) -> dict[str, str | None]:
        data: dict[str, str | None] = {}
        for key in (
            "author",
            "difficulty",
            "comment",
            "solver",
            "solve_mode",
            "solved_at",
            "solved_timezone",
            "solve_iterations",
            "solve_elapsed",
            "solve_elapsed_seconds",
        ):
            value = getattr(self, key)
            if value is not None:
                data[key] = value

        for key, value in self.extra_fields.items():
            if key not in data and value is not None:
                data[key] = value

        return data


@dataclass(slots=True)
class PuzzleSummary:
    rows: int
    cols: int
    rooms: int
    numbered_rooms: int
    pre_shaded_cells: int
    metadata: PuzzleMetadata
    path: Path | None = None

    @property
    def author(self) -> str | None:
        return self.metadata.author

    @property
    def difficulty(self) -> str | None:
        return self.metadata.difficulty

    def to_legacy_dict(self) -> dict[str, int | str | Path | None]:
        return {
            "path": self.path,
            "rows": self.rows,
            "cols": self.cols,
            "rooms": self.rooms,
            "numbered_rooms": self.numbered_rooms,
            "pre_shaded_cells": self.pre_shaded_cells,
            "author": self.author,
            "difficulty": self.difficulty,
        }


@dataclass(slots=True)
class PuzzleSpec:
    rows: int
    cols: int
    rooms: int
    layout: LayoutGrid
    weights: list[WeightEntry]
    initial_state: CellGrid
    info_section: str | None = None
    metadata: PuzzleMetadata = field(default_factory=PuzzleMetadata)


@dataclass(slots=True)
class RoomCache:
    all_room_indices: list[list[Coord]]
    all_room_borders: list[list[Border]]
    all_room_domains: list[list[list[Coord]]]


@dataclass(slots=True)
class PuzzleState:
    grid: CellGrid
    drawn_stones: list[Stone]
    constraint_checks: int = 0


@dataclass(slots=True)
class Puzzle:
    spec: PuzzleSpec
    cache: RoomCache
    state: PuzzleState
    source_path: Path | None = None

    @property
    def rows(self) -> int:
        return self.spec.rows

    @property
    def cols(self) -> int:
        return self.spec.cols

    @property
    def rooms(self) -> int:
        return self.spec.rooms


@dataclass(slots=True)
class SolveResult:
    path: Path
    mode: SolveMode
    solved: bool
    elapsed: timedelta
    solution_path: Path | None = None
    puzzle: Puzzle | None = None

    def to_legacy_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "mode": self.mode,
            "solved": self.solved,
            "elapsed": self.elapsed,
            "solution_path": self.solution_path,
        }


@dataclass(slots=True)
class SolutionCountResult:
    path: Path
    mode: SolveMode
    solution_count: int
    search_limit: int
    elapsed: timedelta
    puzzle: Puzzle | None = None

    @property
    def limit_reached(self) -> bool:
        return self.solution_count >= self.search_limit

    @property
    def is_unique(self) -> bool:
        return self.solution_count == 1 and self.search_limit >= 2

    def to_legacy_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "mode": self.mode,
            "solution_count": self.solution_count,
            "search_limit": self.search_limit,
            "limit_reached": self.limit_reached,
            "is_unique": self.is_unique,
            "elapsed": self.elapsed,
        }


@dataclass(slots=True)
class GenerationResult:
    puzzle: Puzzle
    seed: int
    attempts: int
    uniqueness_limit: int
    elapsed: timedelta
    quality_preset: str | None
    difficulty_preset: str | None
    difficulty_family: str
    difficulty_scale: str
    clue_profile: str | None
    requested_reveal_policy: str
    applied_reveal_policy: str
    revealed_cell_count: int
    revealed_room_count: int
    given_shaded_cells: int
    pre_solved_rooms: int
    numbered_rooms: int
    numbered_rooms_before_carving: int
    clue_carving_enabled: bool = True
    clue_carving_checks: int = 0
    clue_carving_budget_exhausted: bool = False
    solution_count: int = 1
    quality: GenerationQuality | None = None

    @property
    def is_unique(self) -> bool:
        return self.solution_count == 1

    def to_legacy_dict(self) -> dict[str, object]:
        return {
            "seed": self.seed,
            "attempts": self.attempts,
            "uniqueness_limit": self.uniqueness_limit,
            "elapsed": self.elapsed,
            "rows": self.puzzle.rows,
            "cols": self.puzzle.cols,
            "rooms": self.puzzle.rooms,
            "quality_preset": self.quality_preset,
            "difficulty_preset": self.difficulty_preset,
            "difficulty_family": self.difficulty_family,
            "difficulty_scale": self.difficulty_scale,
            "clue_profile": self.clue_profile,
            "requested_reveal_policy": self.requested_reveal_policy,
            "applied_reveal_policy": self.applied_reveal_policy,
            "revealed_cell_count": self.revealed_cell_count,
            "revealed_room_count": self.revealed_room_count,
            "given_shaded_cells": self.given_shaded_cells,
            "pre_solved_rooms": self.pre_solved_rooms,
            "numbered_rooms": self.numbered_rooms,
            "numbered_rooms_before_carving": self.numbered_rooms_before_carving,
            "clue_carving_enabled": self.clue_carving_enabled,
            "clue_carving_checks": self.clue_carving_checks,
            "clue_carving_budget_exhausted": self.clue_carving_budget_exhausted,
            "solution_count": self.solution_count,
            "is_unique": self.is_unique,
            "quality": None if self.quality is None else self.quality.to_legacy_dict(),
        }


@dataclass(slots=True)
class GenerationQuality:
    room_size_min: int
    room_size_max: int
    room_size_spread: int
    room_balance: float
    shape_compactness: float
    given_shaded_cells: int
    pre_solved_rooms: int
    solve_iterations: int
    solve_elapsed: timedelta
    difficulty_score: float
    difficulty: str
    difficulty_score_model: str = "unknown"
    solve_iteration_source: str = "solver"

    def to_legacy_dict(self) -> dict[str, object]:
        return {
            "room_size_min": self.room_size_min,
            "room_size_max": self.room_size_max,
            "room_size_spread": self.room_size_spread,
            "room_balance": self.room_balance,
            "shape_compactness": self.shape_compactness,
            "given_shaded_cells": self.given_shaded_cells,
            "pre_solved_rooms": self.pre_solved_rooms,
            "solve_iterations": self.solve_iterations,
            "solve_elapsed": self.solve_elapsed,
            "difficulty_score": self.difficulty_score,
            "difficulty": self.difficulty,
            "difficulty_score_model": self.difficulty_score_model,
            "solve_iteration_source": self.solve_iteration_source,
        }


@dataclass(slots=True)
class GenerationFilters:
    min_room_balance: float | None = None
    min_shape_compactness: float | None = None
    max_room_size_spread: int | None = None
    max_given_shaded_cells: int | None = None
    max_pre_solved_rooms: int | None = None
    min_solve_iterations: int | None = None
    max_solve_iterations: int | None = None
    min_difficulty_score: float | None = None
    max_difficulty_score: float | None = None

    def to_legacy_dict(self) -> dict[str, object]:
        return {
            "min_room_balance": self.min_room_balance,
            "min_shape_compactness": self.min_shape_compactness,
            "max_room_size_spread": self.max_room_size_spread,
            "max_given_shaded_cells": self.max_given_shaded_cells,
            "max_pre_solved_rooms": self.max_pre_solved_rooms,
            "min_solve_iterations": self.min_solve_iterations,
            "max_solve_iterations": self.max_solve_iterations,
            "min_difficulty_score": self.min_difficulty_score,
            "max_difficulty_score": self.max_difficulty_score,
        }


@dataclass(slots=True)
class GenerationBatchItem:
    seed: int
    status: GenerationItemStatus
    output_path: Path | None = None
    signature: str | None = None
    reason: str | None = None
    generation: GenerationResult | None = None
    quality: GenerationQuality | None = None

    def to_legacy_dict(self) -> dict[str, object]:
        return {
            "seed": self.seed,
            "status": self.status,
            "output_path": None if self.output_path is None else str(self.output_path),
            "signature": self.signature,
            "reason": self.reason,
            "generation": None if self.generation is None else self.generation.to_legacy_dict(),
            "quality": None if self.quality is None else self.quality.to_legacy_dict(),
        }


@dataclass(slots=True)
class GenerationBatchResult:
    requested_count: int
    generated_count: int
    seeds_tried: int
    seed_start: int
    seed_step: int
    duplicates_skipped: int
    quality_rejected: int
    generation_failures: int
    output_dir: Path
    elapsed: timedelta
    items: list[GenerationBatchItem] = field(default_factory=list)
    summary_path: Path | None = None

    def to_legacy_dict(self) -> dict[str, object]:
        return {
            "requested_count": self.requested_count,
            "generated_count": self.generated_count,
            "seeds_tried": self.seeds_tried,
            "seed_start": self.seed_start,
            "seed_step": self.seed_step,
            "duplicates_skipped": self.duplicates_skipped,
            "quality_rejected": self.quality_rejected,
            "generation_failures": self.generation_failures,
            "output_dir": str(self.output_dir),
            "elapsed": self.elapsed,
            "summary_path": None if self.summary_path is None else str(self.summary_path),
            "items": [item.to_legacy_dict() for item in self.items],
        }


def metadata_from_legacy_dict(metadata: PuzzleMetadata | dict[str, object] | None) -> PuzzleMetadata:
    if isinstance(metadata, PuzzleMetadata):
        return metadata
    if isinstance(metadata, dict):
        known_keys = {
            "author",
            "difficulty",
            "hard",
            "comment",
            "solver",
            "solve_mode",
            "solved_at",
            "solved_timezone",
            "solve_iterations",
            "solve_elapsed",
            "solve_elapsed_seconds",
        }
        return PuzzleMetadata(
            author=metadata.get("author"),  # type: ignore[arg-type]
            difficulty=(metadata.get("difficulty") or metadata.get("hard")),  # type: ignore[arg-type]
            comment=metadata.get("comment"),  # type: ignore[arg-type]
            solver=metadata.get("solver"),  # type: ignore[arg-type]
            solve_mode=metadata.get("solve_mode"),  # type: ignore[arg-type]
            solved_at=metadata.get("solved_at"),  # type: ignore[arg-type]
            solved_timezone=metadata.get("solved_timezone"),  # type: ignore[arg-type]
            solve_iterations=metadata.get("solve_iterations"),  # type: ignore[arg-type]
            solve_elapsed=metadata.get("solve_elapsed"),  # type: ignore[arg-type]
            solve_elapsed_seconds=metadata.get("solve_elapsed_seconds"),  # type: ignore[arg-type]
            extra_fields={
                str(key): str(value)
                for key, value in metadata.items()
                if key not in known_keys and value is not None
            },
        )
    return PuzzleMetadata()
