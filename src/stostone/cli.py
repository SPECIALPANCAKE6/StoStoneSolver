from __future__ import annotations

import argparse
import logging
import pathlib
import sys
from logging.handlers import RotatingFileHandler

from .engine import engine
from .generator import CLUE_PROFILES, DIFFICULTY_PRESETS, QUALITY_PRESETS, DEFAULT_OUTPUT_PREFIX, DEFAULT_REVEAL_POLICY, REVEAL_POLICIES, GenerationFailed, analyze_calibration_summaries, render_markdown_report, write_calibration_reports, write_generated_puzzle
from .models import GenerationFilters
from .solver.service import DEFAULT_PUZZLE_DIR, SOLVE_MODES, SolveInterrupted, discover_puzzles, resolve_puzzle_target

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
    summary = engine.summarize(puzzle_path)
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
            result = engine.solve(puzzle_path, mode=args.mode, solutions_dir=solutions_dir)
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


def run_generate(args: argparse.Namespace) -> int:
    log_file = resolve_cli_path(args.log_file) if args.log_file else None
    output_path = resolve_cli_path(args.output) if args.output else None
    output_dir = resolve_cli_path(args.out_dir) if args.out_dir else None
    summary_path = resolve_cli_path(args.summary_file) if args.summary_file else None

    setup_logging(args.log_level, log_file)
    logger.info(
        "Generating puzzle corpus: rows=%s cols=%s rooms=%s count=%s mode=%s reveal_policy=%s clue_carving=%s quality_preset=%s difficulty_preset=%s clue_profile=%s",
        args.rows,
        args.cols,
        "auto" if args.rooms is None else args.rooms,
        args.count,
        describe_mode(args.mode),
        args.reveal_policy,
        not args.no_clue_carving,
        args.quality_preset or "none",
        args.difficulty_preset or "none",
        args.clue_profile or "none",
    )

    if args.seed is not None and args.seed_start is not None:
        raise ValueError("Choose either --seed or --seed-start, not both.")
    if output_path is not None and output_dir is not None:
        raise ValueError("Choose either --output or --out-dir, not both.")
    if args.count > 1 and output_path is not None:
        raise ValueError("Batch generation does not support --output. Use --out-dir instead.")

    explicit_filters = GenerationFilters(
        min_room_balance=args.min_room_balance,
        min_shape_compactness=args.min_shape_compactness,
        max_room_size_spread=args.max_room_size_spread,
        max_given_shaded_cells=args.max_given_cells,
        max_pre_solved_rooms=args.max_pre_solved_rooms,
        min_solve_iterations=args.min_solve_iterations,
        max_solve_iterations=args.max_solve_iterations,
        min_difficulty_score=args.min_difficulty_score,
        max_difficulty_score=args.max_difficulty_score,
    )

    try:
        if args.count == 1:
            result = engine.generate(
                rows=args.rows,
                cols=args.cols,
                rooms=args.rooms,
                seed=args.seed if args.seed is not None else args.seed_start,
                max_attempts=args.max_attempts,
                uniqueness_limit=args.uniqueness_limit,
                reveal_policy=args.reveal_policy,
                mode=args.mode,
                clue_carving=not args.no_clue_carving,
                filters=explicit_filters,
                quality_preset=args.quality_preset,
                difficulty_preset=args.difficulty_preset,
                clue_profile=args.clue_profile,
            )
            if result.quality is None:
                raise GenerationFailed("Generated puzzle is missing quality metrics.")

            written_path = write_generated_puzzle(
                result,
                output_path=output_path,
                output_dir=output_dir,
                output_prefix=args.output_prefix,
                overwrite=False,
            )
            logger.info("Generated %s in %s after %s attempt(s)", written_path, result.elapsed, result.attempts)
            logger.info(
                "Difficulty: %s (score %.2f, %s scale %s); solve iterations: %s; room balance: %.3f; compactness: %.3f",
                result.quality.difficulty,
                result.quality.difficulty_score,
                result.difficulty_scale,
                result.difficulty_family,
                result.quality.solve_iterations,
                result.quality.room_balance,
                result.quality.shape_compactness,
            )
            logger.info(
                "Uniqueness: %s solution(s) with limit %s; reveal policy: %s -> %s",
                result.solution_count,
                result.uniqueness_limit,
                result.requested_reveal_policy,
                result.applied_reveal_policy,
            )
            logger.info(
                "Presets: quality=%s difficulty=%s clue_profile=%s",
                result.quality_preset or "none",
                result.difficulty_preset or "none",
                result.clue_profile or "none",
            )
            logger.info(
                "Revealed cells: %s across %s room(s); fully revealed rooms: %s",
                result.revealed_cell_count,
                result.revealed_room_count,
                result.pre_solved_rooms,
            )
            logger.info(
                "Numbered rooms: %s of %s after clue carving (%s uniqueness check(s), budget exhausted: %s)",
                result.numbered_rooms,
                result.numbered_rooms_before_carving,
                result.clue_carving_checks,
                result.clue_carving_budget_exhausted,
            )
            logger.info("Seed: %s", result.seed)
            return 0

        batch_result = engine.generate_corpus(
            count=args.count,
            rows=args.rows,
            cols=args.cols,
            rooms=args.rooms,
            seed_start=args.seed_start if args.seed_start is not None else args.seed,
            seed_step=args.seed_step,
            max_seeds=args.max_seeds,
            out_dir=output_dir,
            output_prefix=args.output_prefix,
            max_attempts=args.max_attempts,
            uniqueness_limit=args.uniqueness_limit,
            reveal_policy=args.reveal_policy,
            mode=args.mode,
            clue_carving=not args.no_clue_carving,
            filters=explicit_filters,
            quality_preset=args.quality_preset,
            difficulty_preset=args.difficulty_preset,
            clue_profile=args.clue_profile,
            allow_duplicates=args.allow_duplicates,
            summary_path=summary_path,
        )
    except GenerationFailed as exc:
        logger.error("Generation failed: %s", exc)
        return 1
    except KeyboardInterrupt:
        logger.warning("Generation interrupted by user")
        return 130

    for item in batch_result.items:
        if item.status == "written" and item.output_path is not None and item.quality is not None:
            logger.info(
                "Wrote %s (seed=%s, revealed=%s cells/%s rooms, numbered_rooms=%s/%s, difficulty=%s, score=%.2f, iterations=%s)",
                item.output_path,
                item.seed,
                item.generation.revealed_cell_count if item.generation is not None else "?",
                item.generation.revealed_room_count if item.generation is not None else "?",
                item.generation.numbered_rooms if item.generation is not None else "?",
                item.generation.numbered_rooms_before_carving if item.generation is not None else "?",
                item.quality.difficulty,
                item.quality.difficulty_score,
                item.quality.solve_iterations,
            )
        elif item.status == "duplicate":
            logger.info("Skipped duplicate puzzle for seed %s", item.seed)
        elif item.status == "rejected-quality":
            logger.info("Rejected seed %s on quality filters: %s", item.seed, item.reason)
        elif item.status == "failed":
            logger.warning("Seed %s failed to generate a unique puzzle: %s", item.seed, item.reason)

    logger.info(
        "Summary: wrote %s of %s requested puzzle(s) after %s seed(s); duplicates=%s quality_rejected=%s generation_failures=%s",
        batch_result.generated_count,
        batch_result.requested_count,
        batch_result.seeds_tried,
        batch_result.duplicates_skipped,
        batch_result.quality_rejected,
        batch_result.generation_failures,
    )
    if batch_result.summary_path is not None:
        logger.info("Wrote summary file: %s", batch_result.summary_path)
    return 0 if batch_result.generated_count == batch_result.requested_count else 1


def run_calibrate(args: argparse.Namespace) -> int:
    summary_paths = [resolve_cli_path(path_name) for path_name in args.summary_json]
    report_path = resolve_cli_path(args.report) if args.report else None
    json_report_path = resolve_cli_path(args.json_report) if args.json_report else None
    report = analyze_calibration_summaries(summary_paths)
    written_report, written_json = write_calibration_reports(
        report,
        markdown_path=report_path,
        json_path=json_report_path,
    )
    if written_report is not None:
        print(f"Wrote calibration report: {written_report}")
    if written_json is not None:
        print(f"Wrote calibration JSON: {written_json}")
    if written_report is None and written_json is None:
        print(render_markdown_report(report), end="")
    return 0


def run_calibrate_corpus(args: argparse.Namespace) -> int:
    log_file = resolve_cli_path(args.log_file) if args.log_file else None
    plan_path = resolve_cli_path(args.plan)
    report_path = resolve_cli_path(args.report) if args.report else None
    json_report_path = resolve_cli_path(args.json_report) if args.json_report else None

    setup_logging(args.log_level, log_file)
    logger.info("Running calibration corpus plan: %s", plan_path)
    result = engine.calibrate_corpus(
        plan_path,
        force=args.force,
        report_path=report_path,
        json_report_path=json_report_path,
    )

    for item in result.items:
        if item.status == "skipped":
            logger.info(
                "Skipped %s: existing summary has %s/%s puzzle(s)",
                item.family,
                item.generated_count,
                item.requested_count,
            )
        elif item.status == "generated":
            logger.info(
                "Generated %s: wrote %s/%s puzzle(s) after %s seed(s)",
                item.family,
                item.generated_count,
                item.requested_count,
                item.seeds_tried,
            )
        elif item.status == "incomplete":
            logger.warning(
                "Incomplete %s: wrote %s/%s puzzle(s) after %s seed(s): %s",
                item.family,
                item.generated_count,
                item.requested_count,
                item.seeds_tried,
                item.reason,
            )
        elif item.status == "failed":
            logger.error("Failed %s: %s", item.family, item.reason)

    logger.info("Calibration records analyzed: %s", result.report["record_count"])
    if result.markdown_path is not None:
        logger.info("Wrote calibration report: %s", result.markdown_path)
    if result.json_path is not None:
        logger.info("Wrote calibration JSON: %s", result.json_path)
    return 0 if result.completed else 1


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

    generate_parser = subparsers.add_parser("generate", help="Generate one or more unique puzzles and write them to disk")
    generate_parser.add_argument("--rows", type=int, default=4, help="Puzzle row count")
    generate_parser.add_argument("--cols", type=int, default=4, help="Puzzle column count")
    generate_parser.add_argument("--rooms", type=int, help="Optional room count. Defaults to a board-derived value.")
    generate_parser.add_argument("--count", type=int, default=1, help="Number of puzzles to generate")
    generate_parser.add_argument("--seed", type=int, help="Optional random seed for reproducible generation")
    generate_parser.add_argument("--seed-start", type=int, help="Optional starting seed for sequential corpus generation")
    generate_parser.add_argument("--seed-step", type=int, default=1, help="Seed increment when generating multiple puzzles")
    generate_parser.add_argument("--max-seeds", type=int, help="Maximum seeds to try before stopping corpus generation")
    generate_parser.add_argument("--max-attempts", type=int, default=256, help="Maximum generation attempts before failing")
    generate_parser.add_argument("--uniqueness-limit", type=int, default=2, help="Maximum solution count searched during uniqueness checks")
    generate_parser.add_argument("--reveal-policy", choices=list(REVEAL_POLICIES), default=DEFAULT_REVEAL_POLICY, help="Initial-state reveal policy")
    generate_parser.add_argument("--quality-preset", choices=list(QUALITY_PRESETS), help="Named structural quality filter preset")
    generate_parser.add_argument("--difficulty-preset", choices=list(DIFFICULTY_PRESETS), help="Named difficulty-score filter preset")
    generate_parser.add_argument("--clue-profile", choices=list(CLUE_PROFILES), help="Named reveal/clue profile preset")
    generate_parser.add_argument("--mode", choices=list(SOLVE_MODES), default="sto-stone", help="Mode used for uniqueness checks")
    generate_parser.add_argument(
        "--output",
        help="Optional output file path. Defaults to puzzles/generated-<rows>x<cols>-<rooms>r-seed<seed>.txt",
    )
    generate_parser.add_argument("--out-dir", help=f"Optional output directory. Defaults to {DEFAULT_PUZZLE_DIR}")
    generate_parser.add_argument("--output-prefix", default=DEFAULT_OUTPUT_PREFIX, help="Filename prefix for generated puzzles")
    generate_parser.add_argument("--summary-file", help="Optional JSON summary path for batch generation")
    generate_parser.add_argument("--allow-duplicates", action="store_true", help="Allow duplicate puzzle signatures in corpus output")
    generate_parser.add_argument("--no-clue-carving", action="store_true", help="Disable greedy numbered-room clue minimization")
    generate_parser.add_argument("--min-room-balance", type=float, help="Reject puzzles below this room-size balance ratio")
    generate_parser.add_argument("--min-shape-compactness", type=float, help="Reject puzzles below this average room compactness")
    generate_parser.add_argument("--max-room-size-spread", type=int, help="Reject puzzles above this room-size spread")
    generate_parser.add_argument("--max-given-cells", type=int, help="Reject puzzles with more than this many given shaded cells")
    generate_parser.add_argument("--max-pre-solved-rooms", type=int, help="Reject puzzles with more than this many pre-solved rooms")
    generate_parser.add_argument("--min-solve-iterations", type=int, help="Reject puzzles below this solve-iteration count")
    generate_parser.add_argument("--max-solve-iterations", type=int, help="Reject puzzles above this solve-iteration count")
    generate_parser.add_argument("--min-difficulty-score", type=float, help="Reject puzzles below this difficulty score")
    generate_parser.add_argument("--max-difficulty-score", type=float, help="Reject puzzles above this difficulty score")
    generate_parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Console logging verbosity",
    )
    generate_parser.add_argument("--log-file", help="Optional log file path")

    calibrate_parser = subparsers.add_parser("calibrate", help="Analyze generated corpus summaries and recommend preset bands")
    calibrate_parser.add_argument("summary_json", nargs="+", help="Generation summary JSON file(s) from the generate command")
    calibrate_parser.add_argument("--report", help="Optional markdown report output path")
    calibrate_parser.add_argument("--json-report", help="Optional machine-readable JSON report output path")

    calibrate_corpus_parser = subparsers.add_parser("calibrate-corpus", help="Generate a planned corpus matrix and calibrate it")
    calibrate_corpus_parser.add_argument("--plan", required=True, help="Calibration corpus plan JSON path")
    calibrate_corpus_parser.add_argument("--force", action="store_true", help="Regenerate families even when their summary already satisfies the requested count")
    calibrate_corpus_parser.add_argument("--report", help="Optional markdown report output path")
    calibrate_corpus_parser.add_argument("--json-report", help="Optional machine-readable JSON report output path")
    calibrate_corpus_parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Console logging verbosity",
    )
    calibrate_corpus_parser.add_argument("--log-file", help="Optional log file path")

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

        if args.command == "generate":
            return run_generate(args)

        if args.command == "calibrate":
            return run_calibrate(args)

        if args.command == "calibrate-corpus":
            return run_calibrate_corpus(args)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
