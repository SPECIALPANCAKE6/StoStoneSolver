from __future__ import annotations

from pathlib import Path

from ..io.puzpre import write_puzpre
from ..models import PuzzleSummary, SolutionCountResult, SolveResult, legacy_dict_to_puzzle
from ..solver.service import DEFAULT_PUZZLE_DIR, SOLVE_MODES, SolveInterrupted, count_puzzle_file_solutions as _count_puzzle_file_solutions, discover_puzzles, resolve_puzzle_target, solve_puzzle_file, summarize_puzzle as _summarize_puzzle


def summarize_puzzle(puzzle_path: Path) -> dict[str, int | Path | str | None]:
    summary: PuzzleSummary = _summarize_puzzle(puzzle_path)
    return summary.to_legacy_dict()


def output_puzpre(file_name: Path, puzzle_dict: dict[str, object]) -> None:
    write_puzpre(file_name, legacy_dict_to_puzzle(puzzle_dict))


def solve_puzzle(
    puzzle_path: Path,
    mode: str = "sto-stone",
    solutions_dir: Path | None = None,
) -> dict[str, object]:
    result: SolveResult = solve_puzzle_file(puzzle_path, mode=mode, solutions_dir=solutions_dir)  # type: ignore[arg-type]
    return result.to_legacy_dict()


def count_puzzle_solutions(
    puzzle_path: Path,
    mode: str = "sto-stone",
    limit: int = 2,
) -> dict[str, object]:
    result: SolutionCountResult = _count_puzzle_file_solutions(puzzle_path, mode=mode, limit=limit)  # type: ignore[arg-type]
    return result.to_legacy_dict()


__all__ = [
    "DEFAULT_PUZZLE_DIR",
    "SOLVE_MODES",
    "SolveInterrupted",
    "count_puzzle_solutions",
    "discover_puzzles",
    "output_puzpre",
    "resolve_puzzle_target",
    "solve_puzzle",
    "summarize_puzzle",
]
