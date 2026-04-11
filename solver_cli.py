import argparse
import logging
import pathlib
import sys
from logging.handlers import RotatingFileHandler

import solver_runner

logger = logging.getLogger(__name__)


def resolve_cli_path(path_name: str) -> pathlib.Path:
    """Resolve CLI-supplied paths relative to the current working directory."""
    path = pathlib.Path(path_name).expanduser()
    if not path.is_absolute():
        path = pathlib.Path.cwd().joinpath(path)
    return path.resolve()


def resolve_puzzle_dir(dir_name: str | None) -> pathlib.Path:
    """Return the puzzle directory selected by the user or the repo default."""
    return solver_runner.DEFAULT_PUZZLE_DIR if dir_name is None else resolve_cli_path(dir_name)


def setup_logging(log_level: str = "INFO", log_file: pathlib.Path | None = None) -> None:
    """Configure console logging and optionally a rotating log file."""
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    handlers: list[logging.Handler] = [console_handler]

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            filename=log_file,
            mode='a+',
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8',
        )
        file_handler.setFormatter(
            logging.Formatter(
                fmt='%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%m/%d/%Y %H:%M:%S',
            )
        )
        handlers.append(file_handler)

    logging.basicConfig(level=getattr(logging, log_level), handlers=handlers, force=True)


def describe_mode(mode: str) -> str:
    """Return a human-readable label for the selected solve mode."""
    return {
        "sto-stone": "Sto-Stone",
        "sto-sand": "Sto-Sand",
        "both": "Sto-Stone (with Sto-Sand check)",
    }[mode]


def collect_solve_targets(puzzles: list[str], solve_all: bool, puzzle_dir: pathlib.Path) -> list[pathlib.Path]:
    """Resolve the user's solve target selection into concrete puzzle paths."""
    if solve_all and puzzles:
        raise ValueError("Choose either explicit puzzles or --all, not both.")
    if solve_all:
        puzzle_paths = solver_runner.discover_puzzles(puzzle_dir)
        if not puzzle_paths:
            raise FileNotFoundError(f"No puzzle files were found in {puzzle_dir}")
        return puzzle_paths
    if not puzzles:
        raise ValueError("Provide at least one puzzle or use --all.")
    return [solver_runner.resolve_puzzle_target(puzzle_name, puzzle_dir) for puzzle_name in puzzles]


def emit_show(puzzle_path: pathlib.Path) -> None:
    """Print a compact metadata summary for a single puzzle file."""
    summary = solver_runner.summarize_puzzle(puzzle_path)
    print(f"Puzzle: {summary['path']}")
    print(f"Size: {summary['rows']} x {summary['cols']}")
    print(f"Rooms: {summary['rooms']}")
    print(f"Numbered rooms: {summary['numbered_rooms']}")
    print(f"Pre-shaded cells: {summary['pre_shaded_cells']}")


def run_solve(args: argparse.Namespace) -> int:
    """Solve the requested puzzles and print a concise summary to stdout."""
    puzzle_dir = resolve_puzzle_dir(args.dir)
    puzzle_paths = collect_solve_targets(args.puzzles, args.all, puzzle_dir)
    log_file = resolve_cli_path(args.log_file) if args.log_file else None
    solutions_dir = resolve_cli_path(args.solutions_dir) if args.solutions_dir else None

    setup_logging(args.log_level, log_file)
    solved_count = 0

    for puzzle_path in puzzle_paths:
        logger.info(f"Solving {puzzle_path.name} in {describe_mode(args.mode)} mode")
        result = solver_runner.solve_puzzle(puzzle_path, mode=args.mode, solutions_dir=solutions_dir)
        if result['solved']:
            solved_count += 1
            logger.info(f"Solved {puzzle_path.name} in {result['elapsed']}")
            if result['solution_path'] is not None:
                logger.info(f"Wrote solution file: {result['solution_path']}")
            if args.mode == "both":
                logger.info("The reported solution satisfies the Sto-Sand check along the Sto-Stone search path.")
        else:
            logger.warning(
                f"No {describe_mode(args.mode)} solution found for {puzzle_path.name} after {result['elapsed']}"
            )

    logger.info(f"Summary: solved {solved_count} of {len(puzzle_paths)} puzzle(s)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser for the solver CLI."""
    parser = argparse.ArgumentParser(description="Sto-Stone solver CLI")
    subparsers = parser.add_subparsers(dest="command")

    list_parser = subparsers.add_parser("list", help="List available puzzle files")
    list_parser.add_argument("--dir", help=f"Puzzle directory. Defaults to {solver_runner.DEFAULT_PUZZLE_DIR}")

    show_parser = subparsers.add_parser("show", help="Show metadata for one puzzle file")
    show_parser.add_argument("puzzle", help="Puzzle name or path")
    show_parser.add_argument("--dir", help=f"Puzzle directory. Defaults to {solver_runner.DEFAULT_PUZZLE_DIR}")

    solve_parser = subparsers.add_parser("solve", help="Solve one or more puzzles")
    solve_parser.add_argument("puzzles", nargs="*", help="Puzzle names or paths")
    solve_parser.add_argument("--all", action="store_true", help="Solve every puzzle in the selected directory")
    solve_parser.add_argument("--dir", help=f"Puzzle directory. Defaults to {solver_runner.DEFAULT_PUZZLE_DIR}")
    solve_parser.add_argument(
        "--mode",
        choices=list(solver_runner.SOLVE_MODES),
        default="sto-stone",
        help="Select which solver mode to run",
    )
    solve_parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Console logging verbosity",
    )
    solve_parser.add_argument("--log-file", help="Optional log file path")
    solve_parser.add_argument("--solutions-dir", help="Optional output directory for solved puzzle files")

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    try:
        puzzle_dir = resolve_puzzle_dir(getattr(args, "dir", None))

        if args.command == "list":
            for puzzle_path in solver_runner.discover_puzzles(puzzle_dir):
                print(puzzle_path.name)
            return 0

        if args.command == "show":
            emit_show(solver_runner.resolve_puzzle_target(args.puzzle, puzzle_dir))
            return 0

        if args.command == "solve":
            return run_solve(args)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    parser.print_help()
    return 0
