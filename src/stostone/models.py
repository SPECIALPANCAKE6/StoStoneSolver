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

    def to_legacy_dict(self) -> dict[str, object]:
        legacy = {
            "rows": self.spec.rows,
            "cols": self.spec.cols,
            "rooms": self.spec.rooms,
            "layout": self.spec.layout,
            "weights": self.spec.weights,
            "initialState": self.spec.initial_state,
            "state": self.state.grid,
            "allRoomIndices": self.cache.all_room_indices,
            "allRoomBorders": self.cache.all_room_borders,
            "allRoomDomains": self.cache.all_room_domains,
            "drawnStones": self.state.drawn_stones,
            "infoSection": self.spec.info_section,
            "metadata": self.spec.metadata.to_legacy_dict(),
            "constraintChecks": self.state.constraint_checks,
        }
        if self.source_path is not None:
            legacy["puzzlePath"] = str(self.source_path)
        return legacy


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


def legacy_dict_to_puzzle(puzzle_dict: dict[str, object]) -> Puzzle:
    spec = PuzzleSpec(
        rows=puzzle_dict["rows"],  # type: ignore[arg-type]
        cols=puzzle_dict["cols"],  # type: ignore[arg-type]
        rooms=puzzle_dict["rooms"],  # type: ignore[arg-type]
        layout=puzzle_dict["layout"],  # type: ignore[arg-type]
        weights=puzzle_dict["weights"],  # type: ignore[arg-type]
        initial_state=puzzle_dict["initialState"],  # type: ignore[arg-type]
        info_section=puzzle_dict.get("infoSection"),  # type: ignore[arg-type]
        metadata=metadata_from_legacy_dict(puzzle_dict.get("metadata")),  # type: ignore[arg-type]
    )
    cache = RoomCache(
        all_room_indices=puzzle_dict["allRoomIndices"],  # type: ignore[arg-type]
        all_room_borders=puzzle_dict["allRoomBorders"],  # type: ignore[arg-type]
        all_room_domains=puzzle_dict["allRoomDomains"],  # type: ignore[arg-type]
    )
    state = PuzzleState(
        grid=puzzle_dict["state"],  # type: ignore[arg-type]
        drawn_stones=puzzle_dict["drawnStones"],  # type: ignore[arg-type]
        constraint_checks=int(puzzle_dict.get("constraintChecks", 0)),
    )
    source_path = puzzle_dict.get("puzzlePath")
    return Puzzle(
        spec=spec,
        cache=cache,
        state=state,
        source_path=Path(source_path).resolve() if isinstance(source_path, str) else None,
    )


def sync_legacy_dict(puzzle_dict: dict[str, object], puzzle: Puzzle) -> dict[str, object]:
    puzzle_dict.clear()
    puzzle_dict.update(puzzle.to_legacy_dict())
    return puzzle_dict
