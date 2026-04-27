from __future__ import annotations

from pathlib import Path

from .generator.calibration_corpus import CalibrationCorpusRunResult, run_calibration_corpus_plan
from .generator.service import DEFAULT_GENERATOR_NAME, DEFAULT_OUTPUT_PREFIX, DEFAULT_REVEAL_POLICY, build_puzzle_corpus, generate_unique_puzzle
from .io.puzpre import load_puzzle, load_puzzle_summary
from .models import GenerationBatchResult, GenerationFilters, GenerationResult, Puzzle, PuzzleSummary, SolutionCountResult, SolveMode, SolveResult
from .solver.service import DEFAULT_SOLVER_NAME, count_puzzle_file_solutions, count_puzzle_solutions, solve_puzzle, solve_puzzle_file


class StoStoneEngine:
    def load(self, path: Path | str) -> Puzzle:
        return load_puzzle(path)

    def summarize(self, path: Path | str) -> PuzzleSummary:
        return load_puzzle_summary(path)

    def solve(
        self,
        target: Puzzle | Path | str,
        *,
        mode: SolveMode = "sto-stone",
        solutions_dir: Path | None = None,
        solver_name: str = DEFAULT_SOLVER_NAME,
    ) -> SolveResult:
        if isinstance(target, Puzzle):
            return solve_puzzle(target, mode=mode)
        return solve_puzzle_file(target, mode=mode, solutions_dir=solutions_dir, solver_name=solver_name)

    def count(
        self,
        target: Puzzle | Path | str,
        *,
        mode: SolveMode = "sto-stone",
        limit: int = 2,
    ) -> SolutionCountResult:
        if isinstance(target, Puzzle):
            return count_puzzle_solutions(target, mode=mode, limit=limit)
        return count_puzzle_file_solutions(target, mode=mode, limit=limit)

    def generate(
        self,
        *,
        rows: int = 4,
        cols: int = 4,
        rooms: int | None = None,
        seed: int | None = None,
        max_attempts: int = 256,
        uniqueness_limit: int = 2,
        reveal_policy: str = DEFAULT_REVEAL_POLICY,
        mode: SolveMode = "sto-stone",
        generator_name: str = DEFAULT_GENERATOR_NAME,
        clue_carving: bool = True,
        filters: GenerationFilters | None = None,
        quality_preset: str | None = None,
        difficulty_preset: str | None = None,
        clue_profile: str | None = None,
    ) -> GenerationResult:
        return generate_unique_puzzle(
            rows=rows,
            cols=cols,
            rooms=rooms,
            seed=seed,
            max_attempts=max_attempts,
            uniqueness_limit=uniqueness_limit,
            reveal_policy=reveal_policy,
            mode=mode,
            generator_name=generator_name,
            clue_carving=clue_carving,
            filters=filters,
            quality_preset=quality_preset,
            difficulty_preset=difficulty_preset,
            clue_profile=clue_profile,
        )

    def generate_corpus(
        self,
        *,
        count: int,
        rows: int = 4,
        cols: int = 4,
        rooms: int | None = None,
        seed_start: int | None = None,
        seed_step: int = 1,
        max_seeds: int | None = None,
        out_dir: Path | str | None = None,
        output_prefix: str = DEFAULT_OUTPUT_PREFIX,
        max_attempts: int = 256,
        uniqueness_limit: int = 2,
        reveal_policy: str = DEFAULT_REVEAL_POLICY,
        mode: SolveMode = "sto-stone",
        generator_name: str = DEFAULT_GENERATOR_NAME,
        clue_carving: bool = True,
        filters: GenerationFilters | None = None,
        quality_preset: str | None = None,
        difficulty_preset: str | None = None,
        clue_profile: str | None = None,
        allow_duplicates: bool = False,
        summary_path: Path | str | None = None,
    ) -> GenerationBatchResult:
        return build_puzzle_corpus(
            count=count,
            rows=rows,
            cols=cols,
            rooms=rooms,
            seed_start=seed_start,
            seed_step=seed_step,
            max_seeds=max_seeds,
            out_dir=out_dir,
            output_prefix=output_prefix,
            max_attempts=max_attempts,
            uniqueness_limit=uniqueness_limit,
            reveal_policy=reveal_policy,
            mode=mode,
            generator_name=generator_name,
            clue_carving=clue_carving,
            filters=filters,
            quality_preset=quality_preset,
            difficulty_preset=difficulty_preset,
            clue_profile=clue_profile,
            allow_duplicates=allow_duplicates,
            summary_path=summary_path,
        )

    def calibrate_corpus(
        self,
        plan_path: Path | str,
        *,
        force: bool = False,
        report_path: Path | str | None = None,
        json_report_path: Path | str | None = None,
    ) -> CalibrationCorpusRunResult:
        return run_calibration_corpus_plan(
            plan_path,
            force=force,
            markdown_path=report_path,
            json_path=json_report_path,
        )


engine = StoStoneEngine()


__all__ = ["StoStoneEngine", "engine"]
