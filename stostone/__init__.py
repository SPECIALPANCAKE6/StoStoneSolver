from pathlib import Path

_SRC_PACKAGE = Path(__file__).resolve().parent.parent.joinpath("src", "stostone")
if _SRC_PACKAGE.is_dir():
    __path__.append(str(_SRC_PACKAGE))

from .generator import build_puzzle, derive_room_cache, reset_state
from .io.puzpre import load_puzzle, load_puzzle_summary, write_puzpre
from .models import Puzzle, PuzzleMetadata, PuzzleSpec, PuzzleState, PuzzleSummary, RoomCache, SolveMode, SolveResult
from .solver.service import DEFAULT_PUZZLE_DIR, SOLVE_MODES, SolveInterrupted, discover_puzzles, resolve_puzzle_target, solve_puzzle, solve_puzzle_file

__all__ = [
    "DEFAULT_PUZZLE_DIR",
    "SOLVE_MODES",
    "SolveInterrupted",
    "SolveMode",
    "PuzzleMetadata",
    "PuzzleSummary",
    "PuzzleSpec",
    "RoomCache",
    "PuzzleState",
    "Puzzle",
    "SolveResult",
    "build_puzzle",
    "derive_room_cache",
    "reset_state",
    "load_puzzle",
    "load_puzzle_summary",
    "write_puzpre",
    "discover_puzzles",
    "resolve_puzzle_target",
    "solve_puzzle",
    "solve_puzzle_file",
]

