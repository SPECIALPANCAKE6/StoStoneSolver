from __future__ import annotations

from ..assembly import assemble_puzzle, derive_room_cache, reset_state
from .service import (
    DEFAULT_GENERATOR_NAME,
    DEFAULT_OUTPUT_PREFIX,
    DEFAULT_REVEAL_POLICY,
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
    "GenerationFailed",
    "REVEAL_POLICIES",
    "assemble_puzzle",
    "build_puzzle_corpus",
    "build_puzzle",
    "derive_room_cache",
    "generate_unique_puzzle",
    "quality_rejection_reason",
    "reset_state",
    "write_generated_puzzle",
    "write_generation_summary",
]
