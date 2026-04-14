from __future__ import annotations

import argparse
import logging
import pathlib
import sys
from logging.handlers import RotatingFileHandler

from .solver.service import DEFAULT_PUZZLE_DIR, SOLVE_MODES, SolveInterrupted, discover_puzzles, resolve_puzzle_target, solve_puzzle_file, summarize_puzzle

logger = logging.getLogger(__name__)


def resolve_cli_path(path_name: str) -> pathlib.Path:
    path = pathlib.Path(path_name).expanduser()
    if not path.is_absolute():
        path = pathlib.Path.cwd().joinpath(path)
    return path.resolve()


def resolve_puzzle_dir(dir_name: str | None) -> pathlib.Path:
    return DEFAULT_PUZZLE_DIR if dir_name is None else resolve_cli_path(dir_name)


def setup_logging(log_level: str = "INFO", log_file: pathlib.Path | None = None) -> None:
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%m/%d/%Y %H:%M:%S",
        )
    )
    handlers: list[logging.Handler] = [console_handler]

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            filename=log_file,
            mode="a+",
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s - %(levelname)s - %(message)s",
                datefmt="%m/%d/%Y %H:%M:%S",
            )
        )
        handlers.append(file_handler)

    logging.basicConfig(level=getattr(logging, log_level), handlers=handlers, force=True)


def describe_mode(mode: str) -> str:
    return {
        "sto-stone": "Sto-Stone",
        "sto-sand": "Sto-Sand",
        "both": "Sto-Stone (with Sto-Sand check)",
    }[mode]


def collect_solve_targets(puzzles: list[str], solve_all: bool, puzzle_dir: pathlib.Path) -> list[pathlib.Path]:
    if solve_all and puzzles:
        raise ValueError("Choose either explicit puzzles or --all, not both.")
    if solve_all:
        puzzle_paths = discover_puzzles(puzzle_dir)
        if not puzzle_paths:
            raise FileNotFoundError(f"No puzzle files were found in {puzzle_dir}")
        return puzzle_paths
    if not puzzles:
        raise ValueError("Provide at least one puzzle or use --all.")
    return [resolve_puzzle_target(puzzle_name, puzzle_dir) for puzzle_name in puzzles]


def emit_show(puzzle_path: pathlib.Path) -> None:
    summary = summarize_puzzle(puzzle_path)
    print(f"Puzzle: {summary.path}")
    print(f"Size: {summary.rows} x {summary.cols}")
    print(f"Rooms: {summary.rooms}")
    print(f"Numbered rooms: {summary.numbered_rooms}")
    print(f"Pre-shaded cells: {summary.pre_shaded_cells}")
    print(f"Author: {summary.author or 'Unknown'}")
    print(f"Difficulty: {summary.difficulty or 'Unknown'}")


def run_solve(args: argparse.Namespace) -> int:
    puzzle_dir = resolve_puzzle_dir(args.dir)
    puzzle_paths = collect_solve_targets(args.puzzles, args.all, puzzle_dir)
    log_file = resolve_cli_path(args.log_file) if args.log_file else None
    solutions_dir = resolve_cli_path(args.solutions_dir) if args.solutions_dir else None

    setup_logging(args.log_level, log_file)
    solved_count = 0

    for puzzle_path in puzzle_paths:
        logger.info("Solving %s in %s mode", puzzle_path.name, describe_mode(args.mode))
        try:
            result = solve_puzzle_file(puzzle_path, mode=args.mode, solutions_dir=solutions_dir)
        except SolveInterrupted as exc:
            logger.warning(
                "[%s] Solve interrupted by user after %s at last attempted iteration %s",
                exc.puzzle_path,
                exc.elapsed,
                exc.iteration,
            )
            logger.info("Summary: solved %s of %s puzzle(s) before interruption", solved_count, len(puzzle_paths))
            return 130

        if result.solved:
            solved_count += 1
            logger.info("Solved %s in %s", puzzle_path.name, result.elapsed)
            if result.solution_path is not None:
                logger.info("Wrote solution file: %s", result.solution_path)
        else:
            logger.warning("No %s solution found for %s after %s", describe_mode(args.mode), puzzle_path.name, result.elapsed)

    logger.info("Summary: solved %s of %s puzzle(s)", solved_count, len(puzzle_paths))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sto-Stone solver CLI")
    subparsers = parser.add_subparsers(dest="command")

    list_parser = subparsers.add_parser("list", help="List available puzzle files")
    list_parser.add_argument("--dir", help=f"Puzzle directory. Defaults to {DEFAULT_PUZZLE_DIR}")

    show_parser = subparsers.add_parser("show", help="Show metadata for one puzzle file")
    show_parser.add_argument("puzzle", help="Puzzle name or path")
    show_parser.add_argument("--dir", help=f"Puzzle directory. Defaults to {DEFAULT_PUZZLE_DIR}")

    solve_parser = subparsers.add_parser("solve", help="Solve one or more puzzles")
    solve_parser.add_argument("puzzles", nargs="*", help="Puzzle names or paths")
    solve_parser.add_argument("--all", action="store_true", help="Solve every puzzle in the selected directory")
    solve_parser.add_argument("--dir", help=f"Puzzle directory. Defaults to {DEFAULT_PUZZLE_DIR}")
    solve_parser.add_argument("--mode", choices=list(SOLVE_MODES), default="sto-stone", help="Select which solver mode to run")
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
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    try:
        puzzle_dir = resolve_puzzle_dir(getattr(args, "dir", None))

        if args.command == "list":
            for puzzle_path in discover_puzzles(puzzle_dir):
                print(puzzle_path.name)
            return 0

        if args.command == "show":
            emit_show(resolve_puzzle_target(args.puzzle, puzzle_dir))
            return 0

        if args.command == "solve":
            return run_solve(args)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
