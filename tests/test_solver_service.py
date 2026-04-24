from __future__ import annotations

from pathlib import Path

import pytest

from src.stostone.io.puzpre import load_puzzle
from src.stostone.solver import service


pytestmark = pytest.mark.integration


def test_discover_puzzles_requires_existing_directory(workspace_tmp_dir: Path) -> None:
    with pytest.raises(FileNotFoundError):
        service.discover_puzzles(workspace_tmp_dir.joinpath("missing"))


def test_resolve_puzzle_target_accepts_name_without_extension(puzzle_dir: Path) -> None:
    resolved = service.resolve_puzzle_target("000-000", puzzle_dir)
    assert resolved.name == "000-000.txt"


def test_solve_puzzle_rejects_unknown_mode(puzzle_path) -> None:
    puzzle = load_puzzle(puzzle_path("000-000.txt"))

    with pytest.raises(ValueError):
        service.solve_puzzle(puzzle, mode="invalid")  # type: ignore[arg-type]


def test_count_puzzle_solutions_rejects_invalid_limit(build_puzzle) -> None:
    puzzle = build_puzzle(2, 1, [[0], [0]])

    with pytest.raises(ValueError):
        service.count_puzzle_solutions(puzzle, limit=0)


@pytest.mark.regression
def test_solve_puzzle_file_solves_known_puzzle_and_writes_output(puzzle_path, solutions_dir: Path) -> None:
    result = service.solve_puzzle_file(
        puzzle_path("000-000.txt"),
        solutions_dir=solutions_dir,
        solver_name="pytest suite",
    )

    assert result.solved
    assert result.solution_path == solutions_dir.joinpath("000-000-solved.txt")
    assert result.solution_path.is_file()
    assert result.puzzle is not None
    assert result.puzzle.spec.metadata.solver == "pytest suite"
    assert result.puzzle.spec.metadata.solve_mode == "sto-stone"
    assert int(result.puzzle.spec.metadata.solve_iterations or "0") > 0


@pytest.mark.regression
@pytest.mark.slow
def test_solve_puzzle_file_solves_001_001_regression(puzzle_path) -> None:
    result = service.solve_puzzle_file(puzzle_path("001-001.txt"))

    assert result.solved
    assert result.puzzle is not None
    assert result.puzzle.state.constraint_checks > 0


def test_solve_puzzle_supports_both_mode(puzzle_path) -> None:
    puzzle = load_puzzle(puzzle_path("000-000.txt"))
    result = service.solve_puzzle(puzzle, mode="both")

    assert result.solved
    assert result.mode == "both"


@pytest.mark.regression
def test_count_puzzle_file_solutions_proves_known_puzzle_is_unique(puzzle_path) -> None:
    result = service.count_puzzle_file_solutions(puzzle_path("000-001.txt"), limit=2)

    assert result.solution_count == 1
    assert result.search_limit == 2
    assert result.is_unique
    assert not result.limit_reached
    assert result.puzzle is not None
    assert result.puzzle.state.constraint_checks > 0


def test_count_puzzle_solutions_stops_at_limit_and_restores_state(build_puzzle) -> None:
    limited_puzzle = build_puzzle(4, 1, [[0], [0], [0], [0]])
    full_puzzle = build_puzzle(4, 1, [[0], [0], [0], [0]])

    limited = service.count_puzzle_solutions(limited_puzzle, mode="sto-stone", limit=2)
    full = service.count_puzzle_solutions(full_puzzle, mode="sto-stone", limit=5)

    assert limited.solution_count == 2
    assert limited.limit_reached
    assert not limited.is_unique
    assert full.solution_count == 3
    assert full_puzzle.state.constraint_checks > limited_puzzle.state.constraint_checks
    assert limited_puzzle.state.grid == limited_puzzle.spec.initial_state
    assert limited_puzzle.state.drawn_stones == [None]
    assert full_puzzle.state.grid == full_puzzle.spec.initial_state
    assert full_puzzle.state.drawn_stones == [None]


def test_count_puzzle_solutions_reports_zero_when_unsolved(build_puzzle) -> None:
    puzzle = build_puzzle(2, 1, [[0], [0]], weights=[((0, 0), 2)])

    result = service.count_puzzle_solutions(puzzle, mode="sto-stone", limit=2)

    assert result.solution_count == 0
    assert not result.limit_reached
    assert not result.is_unique


def test_solve_puzzle_wraps_keyboard_interrupt(build_puzzle, monkeypatch) -> None:
    puzzle = build_puzzle(2, 2, [[0, 0], [0, 0]])
    puzzle.source_path = Path("puzzles/sample.txt").resolve()

    def raise_interrupt(*_args, **_kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(service, "backtrack", raise_interrupt)

    with pytest.raises(service.SolveInterrupted) as excinfo:
        service.solve_puzzle(puzzle)

    assert excinfo.value.puzzle_path == puzzle.source_path
