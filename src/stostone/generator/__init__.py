from __future__ import annotations

from ..assembly import assemble_puzzle, derive_room_cache, reset_state
from .calibration import analyze_calibration_summaries, load_calibration_records, render_markdown_report, write_calibration_reports
from .calibration_corpus import (
    CalibrationCorpusFamilyPlan,
    CalibrationCorpusPlan,
    CalibrationCorpusRunItem,
    CalibrationCorpusRunResult,
    load_calibration_corpus_plan,
    run_calibration_corpus_plan,
)
from .presets import (
    CLUE_PROFILES,
    DIFFICULTY_PRESETS,
    QUALITY_PRESETS,
    SIZE_AWARE_DIFFICULTY_PRESETS,
    board_family_key,
    difficulty_filter_for_preset,
    difficulty_label_from_score,
    difficulty_presets_for_family,
    difficulty_scale_for_family,
    has_size_aware_difficulty,
)
from .scoring import DIFFICULTY_SCORE_MODEL, iteration_difficulty_component, score_generation_quality
from .service import (
    DEFAULT_GENERATOR_NAME,
    DEFAULT_OUTPUT_PREFIX,
    DEFAULT_REVEAL_POLICY,
    REVEAL_POLICY_MAPS,
    REVEAL_POLICIES,
    GenerationFailed,
    build_puzzle_corpus,
    generate_unique_puzzle,
    quality_rejection_reason,
    write_generated_puzzle,
    write_generation_summary,
)


build_puzzle = assemble_puzzle


__all__ = [
    "DEFAULT_GENERATOR_NAME",
    "DEFAULT_OUTPUT_PREFIX",
    "DEFAULT_REVEAL_POLICY",
    "CalibrationCorpusFamilyPlan",
    "CalibrationCorpusPlan",
    "CalibrationCorpusRunItem",
    "CalibrationCorpusRunResult",
    "CLUE_PROFILES",
    "DIFFICULTY_PRESETS",
    "DIFFICULTY_SCORE_MODEL",
    "GenerationFailed",
    "QUALITY_PRESETS",
    "REVEAL_POLICY_MAPS",
    "REVEAL_POLICIES",
    "SIZE_AWARE_DIFFICULTY_PRESETS",
    "analyze_calibration_summaries",
    "assemble_puzzle",
    "board_family_key",
    "build_puzzle_corpus",
    "build_puzzle",
    "derive_room_cache",
    "difficulty_filter_for_preset",
    "difficulty_label_from_score",
    "difficulty_presets_for_family",
    "difficulty_scale_for_family",
    "generate_unique_puzzle",
    "has_size_aware_difficulty",
    "iteration_difficulty_component",
    "load_calibration_corpus_plan",
    "load_calibration_records",
    "quality_rejection_reason",
    "render_markdown_report",
    "reset_state",
    "run_calibration_corpus_plan",
    "score_generation_quality",
    "write_calibration_reports",
    "write_generated_puzzle",
    "write_generation_summary",
]
