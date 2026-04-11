import pathlib
import logging
from datetime import datetime

import backtrack
import readPuzzle

logger = logging.getLogger(__name__)

SOLVE_MODES = ("sto-stone", "sto-sand", "both")
BASE_DIR = pathlib.Path(__file__).resolve().parent
DEFAULT_PUZZLE_DIR = BASE_DIR.joinpath("puzzles")


class SolveInterrupted(Exception):
    """Raised when the user interrupts a solve attempt."""

    def __init__(self, puzzle_path: pathlib.Path, iteration: int, elapsed) -> None:
        self.puzzle_path = puzzle_path
        self.iteration = iteration
        self.elapsed = elapsed
        super().__init__(f"Solve interrupted for {puzzle_path}")


def discover_puzzles(puzzle_dir: pathlib.Path) -> list[pathlib.Path]:
    """Return all puzzle files from `puzzle_dir` sorted by filename."""
    if not puzzle_dir.is_dir():
        raise FileNotFoundError(f"Puzzle directory does not exist: {puzzle_dir}")
    return sorted(
        (path for path in puzzle_dir.glob("*.txt") if path.is_file()),
        key=lambda path: path.name,
    )


def resolve_puzzle_target(target: str, puzzle_dir: pathlib.Path) -> pathlib.Path:
    """Resolve a puzzle name or path into a concrete `.txt` file path."""
    target_path = pathlib.Path(target)
    candidates: list[pathlib.Path] = []

    if target_path.is_absolute() or len(target_path.parts) > 1:
        if target_path.is_absolute():
            candidates.append(target_path)
        else:
            candidates.append(pathlib.Path.cwd().joinpath(target_path))
    else:
        candidates.append(puzzle_dir.joinpath(target_path))
        if target_path.suffix == "":
            candidates.append(puzzle_dir.joinpath(f"{target}.txt"))

    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()

    raise FileNotFoundError(f"Puzzle file was not found: {target}")


def summarize_puzzle(puzzle_path: pathlib.Path) -> dict[str, int | pathlib.Path]:
    """Load puzzle metadata in a UI-friendly shape without solving it."""
    summary = readPuzzle.readPuzzleMetadata(puzzle_path)
    return {
        "path": puzzle_path.resolve(),
        **summary,
    }


def _write_puzpre_grid(file, rows: list[list[int | str]]) -> None:
    """Write one PUZ-PRE grid section with space-separated cells."""
    for row in rows:
        file.write(" ".join(str(cell) for cell in row) + "\n")


def _format_weights(weights: list[tuple[tuple[int, int], int] | None]) -> str:
    """Format room weights for debug logging."""
    lines = [
        f"Room {room}: {val[0]}, {val[1]}"
        for room, val in enumerate(weights)
        if val is not None
    ]
    return "\n".join(lines) if lines else "None"


def output_puzpre(file_name: pathlib.Path, puzzle_dict: dict[str, int | list]) -> None:
    """Write a solved puzzle back out in PUZ-PRE v3 format."""
    file_name.parent.mkdir(parents=True, exist_ok=True)
    with open(file_name, "w+", newline='\n') as file:
        file.write("pzprv3\nstostone\n")
        file.write(str(puzzle_dict['rows']) + "\n")
        file.write(str(puzzle_dict['cols']) + "\n")
        file.write(str(puzzle_dict['rooms']) + "\n")

        _write_puzpre_grid(file, puzzle_dict['layout'])

        weight_lookup = {coord: weight for coord, weight in (val for val in puzzle_dict['weights'] if val is not None)}
        weight_rows = [
            [weight_lookup.get((r, c), ".") for c in range(puzzle_dict['cols'])]
            for r in range(puzzle_dict['rows'])
        ]
        _write_puzpre_grid(file, weight_rows)

        filled_cells = {
            coord
            for stone in puzzle_dict['drawnStones']
            if stone is not None
            for coord in stone
        }
        stone_rows = [
            ["#" if (r, c) in filled_cells else "." for c in range(puzzle_dict['cols'])]
            for r in range(puzzle_dict['rows'])
        ]
        _write_puzpre_grid(file, stone_rows)

        info_section = puzzle_dict.get('infoSection')
        if isinstance(info_section, str) and info_section.strip():
            file.write("\n" + info_section.strip() + "\n")
        else:
            file.write("\ninfo:{\n \"metadata\": {\n  \"author\": \"Addison Allen's Solver\",\n }\n}")


def solve_puzzle(
    puzzle_path: pathlib.Path,
    mode: str = "sto-stone",
    solutions_dir: pathlib.Path | None = None,
) -> dict[str, object]:
    """Solve one puzzle and optionally export the solved PUZ-PRE file."""
    if mode not in SOLVE_MODES:
        raise ValueError(f"Unsupported solve mode: {mode}")

    start_time = datetime.now()
    puzzle_dict = {
        'constraintChecks': 0,
        'puzzlePath': str(puzzle_path.resolve()),
    }
    try:
        puzzle_dict = readPuzzle.readPuzzle(puzzle_path)
        puzzle_dict['puzzlePath'] = str(puzzle_path.resolve())
        puzzle_dict['constraintChecks'] = 0
        logger.debug("Layout:\n%s", readPuzzle.printFormatGrid(puzzle_dict['layout']))
        logger.debug("Weights:\n%s", _format_weights(puzzle_dict['weights']))
        logger.debug("Initial State:\n%s", readPuzzle.printFormatGrid(puzzle_dict['initialState']))
        solved = backtrack.backtrack(0, puzzle_dict, mode=mode)
    except KeyboardInterrupt as exc:
        raise SolveInterrupted(
            puzzle_path.resolve(),
            int(puzzle_dict.get('constraintChecks', 0)),
            datetime.now() - start_time,
        ) from exc
    elapsed = datetime.now() - start_time

    solution_path = None
    if solved and solutions_dir is not None:
        solution_path = solutions_dir.joinpath(f"{puzzle_path.stem}-solved.txt")
        output_puzpre(solution_path, puzzle_dict)

    return {
        "path": puzzle_path.resolve(),
        "mode": mode,
        "solved": solved,
        "elapsed": elapsed,
        "solution_path": solution_path,
    }
