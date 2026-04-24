from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from ..io.puzpre import load_puzzle, load_puzzle_summary, write_puzpre
from ..models import Puzzle, PuzzleSummary, SolutionCountResult, SolveMode, SolveResult
from .search import backtrack, count_solutions

logger = logging.getLogger(__name__)

SOLVE_MODES: tuple[SolveMode, ...] = ("sto-stone", "sto-sand", "both")
BASE_DIR = Path(__file__).resolve().parents[3]
DEFAULT_PUZZLE_DIR = BASE_DIR.joinpath("puzzles")
DEFAULT_SOLVER_NAME = "StoStoneSolver CLI"


class SolveInterrupted(Exception):
    def __init__(self, puzzle_path: Path, iteration: int, elapsed) -> None:
        self.puzzle_path = puzzle_path
        self.iteration = iteration
        self.elapsed = elapsed
        super().__init__(f"Solve interrupted for {puzzle_path}")


def _now() -> datetime:
    return datetime.now().astimezone()


def _annotate_solution_metadata(
    puzzle: Puzzle,
    mode: SolveMode,
    solved_at: datetime,
    elapsed,
    solver_name: str,
) -> None:
    puzzle.spec.metadata.solver = solver_name
    puzzle.spec.metadata.solve_mode = mode
    puzzle.spec.metadata.solved_at = solved_at.isoformat()
    puzzle.spec.metadata.solved_timezone = solved_at.tzname() or str(solved_at.tzinfo) or "Unknown"
    puzzle.spec.metadata.solve_iterations = str(puzzle.state.constraint_checks)
    puzzle.spec.metadata.solve_elapsed = str(elapsed)
    puzzle.spec.metadata.solve_elapsed_seconds = f"{elapsed.total_seconds():.6f}"


def discover_puzzles(puzzle_dir: Path) -> list[Path]:
    if not puzzle_dir.is_dir():
        raise FileNotFoundError(f"Puzzle directory does not exist: {puzzle_dir}")
    return sorted((path for path in puzzle_dir.glob("*.txt") if path.is_file()), key=lambda path: path.name)


def resolve_puzzle_target(target: str, puzzle_dir: Path) -> Path:
    target_path = Path(target)
    candidates: list[Path] = []

    if target_path.is_absolute() or len(target_path.parts) > 1:
        candidates.append(target_path if target_path.is_absolute() else Path.cwd().joinpath(target_path))
    else:
        candidates.append(puzzle_dir.joinpath(target_path))
        if target_path.suffix == "":
            candidates.append(puzzle_dir.joinpath(f"{target}.txt"))

    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()

    raise FileNotFoundError(f"Puzzle file was not found: {target}")


def _validate_mode(mode: SolveMode) -> None:
    if mode not in SOLVE_MODES:
        raise ValueError(f"Unsupported solve mode: {mode}")


def solve_puzzle(puzzle: Puzzle, mode: SolveMode = "sto-stone") -> SolveResult:
    _validate_mode(mode)
    puzzle.state.constraint_checks = 0
    start_time = _now()
    try:
        solved = backtrack(0, puzzle, mode=mode)
    except KeyboardInterrupt as exc:
        raise SolveInterrupted(
            puzzle.source_path or Path("<unknown puzzle>"),
            puzzle.state.constraint_checks,
            _now() - start_time,
        ) from exc

    finished_at = _now()
    return SolveResult(
        path=puzzle.source_path or Path("<unknown puzzle>"),
        mode=mode,
        solved=solved,
        elapsed=finished_at - start_time,
        puzzle=puzzle,
    )


def count_puzzle_solutions(puzzle: Puzzle, mode: SolveMode = "sto-stone", limit: int = 2) -> SolutionCountResult:
    _validate_mode(mode)
    puzzle.state.constraint_checks = 0
    start_time = _now()
    try:
        solution_count = count_solutions(0, puzzle, mode=mode, limit=limit)
    except KeyboardInterrupt as exc:
        raise SolveInterrupted(
            puzzle.source_path or Path("<unknown puzzle>"),
            puzzle.state.constraint_checks,
            _now() - start_time,
        ) from exc

    finished_at = _now()
    return SolutionCountResult(
        path=puzzle.source_path or Path("<unknown puzzle>"),
        mode=mode,
        solution_count=solution_count,
        search_limit=limit,
        elapsed=finished_at - start_time,
        puzzle=puzzle,
    )


def solve_puzzle_file(
    path: Path | str,
    mode: SolveMode = "sto-stone",
    solutions_dir: Path | None = None,
    solver_name: str = DEFAULT_SOLVER_NAME,
) -> SolveResult:
    ingest_started_at = _now()
    puzzle = load_puzzle(path)
    try:
        result = solve_puzzle(puzzle, mode=mode)
    except SolveInterrupted as exc:
        exc.elapsed = _now() - ingest_started_at
        raise

    solved_at = _now()
    result.elapsed = solved_at - ingest_started_at
    if result.solved:
        _annotate_solution_metadata(puzzle, mode, solved_at, result.elapsed, solver_name)
    if result.solved and solutions_dir is not None:
        result.solution_path = solutions_dir.joinpath(f"{result.path.stem}-solved.txt")
        write_puzpre(result.solution_path, puzzle)
    return result


def count_puzzle_file_solutions(path: Path | str, mode: SolveMode = "sto-stone", limit: int = 2) -> SolutionCountResult:
    ingest_started_at = _now()
    puzzle = load_puzzle(path)
    try:
        result = count_puzzle_solutions(puzzle, mode=mode, limit=limit)
    except SolveInterrupted as exc:
        exc.elapsed = _now() - ingest_started_at
        raise

    result.elapsed = _now() - ingest_started_at
    return result


def summarize_puzzle(path: Path | str) -> PuzzleSummary:
    return load_puzzle_summary(path)
