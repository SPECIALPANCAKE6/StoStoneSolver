from __future__ import annotations

import pytest

from src.stostone.generator import DEFAULT_GENERATOR_NAME, GenerationFailed, build_puzzle_corpus, generate_unique_puzzle
from src.stostone.models import GenerationFilters
from src.stostone.solver.service import count_puzzle_solutions


pytestmark = pytest.mark.integration


def _count_given_cells(initial_state: list[list[int | str]]) -> int:
    return sum(cell == " #" for row in initial_state for cell in row)


@pytest.mark.regression
def test_generate_unique_puzzle_is_reproducible_for_seed() -> None:
    first = generate_unique_puzzle(rows=4, cols=4, rooms=4, seed=0, max_attempts=20, reveal_policy="empty")
    second = generate_unique_puzzle(rows=4, cols=4, rooms=4, seed=0, max_attempts=20, reveal_policy="empty")

    assert first.seed == 0
    assert first.solution_count == 1
    assert first.applied_reveal_policy == "empty"
    assert first.given_shaded_cells == 0
    assert first.pre_solved_rooms == 0
    assert first.puzzle.spec.layout == second.puzzle.spec.layout
    assert first.puzzle.spec.weights == second.puzzle.spec.weights
    assert first.puzzle.spec.initial_state == second.puzzle.spec.initial_state == [[-1] * 4 for _ in range(4)]

    uniqueness = count_puzzle_solutions(first.puzzle, limit=2)
    assert uniqueness.solution_count == 1


def test_generate_unique_puzzle_single_cell_policy_reveals_exactly_one_cell() -> None:
    result = generate_unique_puzzle(rows=4, cols=4, rooms=4, seed=0, max_attempts=20, reveal_policy="single-cell")

    assert result.applied_reveal_policy == "single-cell"
    assert result.given_shaded_cells == 1
    assert result.pre_solved_rooms == 0
    assert _count_given_cells(result.puzzle.spec.initial_state) == 1
    assert count_puzzle_solutions(result.puzzle, limit=2).solution_count == 1


@pytest.mark.regression
def test_generate_unique_puzzle_carves_numbered_room_clues_by_default() -> None:
    carved = generate_unique_puzzle(rows=4, cols=4, rooms=4, seed=0, max_attempts=20, reveal_policy="empty")
    plain = generate_unique_puzzle(
        rows=4,
        cols=4,
        rooms=4,
        seed=0,
        max_attempts=20,
        reveal_policy="empty",
        clue_carving=False,
    )
    metadata = carved.puzzle.spec.metadata.extra_fields

    assert plain.numbered_rooms == 4
    assert plain.numbered_rooms_before_carving == 4
    assert carved.numbered_rooms == 2
    assert carved.numbered_rooms_before_carving == 4
    assert carved.clue_carving_enabled
    assert carved.clue_carving_checks == 4
    assert metadata["clue_carving_enabled"] == "true"
    assert metadata["numbered_rooms_before_carving"] == "4"
    assert metadata["numbered_rooms"] == "2"
    assert metadata["clue_carving_removed_numbered_rooms"] == "2"
    assert count_puzzle_solutions(carved.puzzle, limit=2).solution_count == 1


def test_generate_unique_puzzle_full_room_policy_tracks_generation_metadata() -> None:
    result = generate_unique_puzzle(rows=4, cols=4, rooms=4, seed=0, max_attempts=20, reveal_policy="full-room")
    metadata = result.puzzle.spec.metadata

    assert result.applied_reveal_policy == "full-room"
    assert result.pre_solved_rooms == 1
    assert result.given_shaded_cells == _count_given_cells(result.puzzle.spec.initial_state)
    assert metadata.author == DEFAULT_GENERATOR_NAME
    assert metadata.extra_fields["generation_strategy"] == "solution-first"
    assert metadata.extra_fields["generator_seed"] == "0"
    assert metadata.extra_fields["difficulty_score"]
    assert metadata.extra_fields["requested_reveal_policy"] == "full-room"
    assert metadata.extra_fields["applied_reveal_policy"] == "full-room"
    assert metadata.extra_fields["solution_count"] == "1"
    assert metadata.difficulty == result.quality.difficulty if result.quality is not None else None
    assert count_puzzle_solutions(result.puzzle, limit=2).solution_count == 1


@pytest.mark.regression
def test_generate_unique_puzzle_handles_seeded_6x6_case_efficiently() -> None:
    result = generate_unique_puzzle(rows=6, cols=6, rooms=6, seed=0, max_attempts=10, reveal_policy="empty")

    assert result.solution_count == 1
    assert result.attempts <= 10
    assert result.puzzle.spec.metadata.extra_fields["generation_strategy"] == "solution-first"
    assert count_puzzle_solutions(result.puzzle, limit=2).solution_count == 1


def test_generate_unique_puzzle_rejects_invalid_generation_args() -> None:
    with pytest.raises(ValueError):
        generate_unique_puzzle(rows=5, cols=4)

    with pytest.raises(ValueError):
        generate_unique_puzzle(rows=4, cols=4, rooms=9)

    with pytest.raises(ValueError):
        generate_unique_puzzle(rows=4, cols=4, reveal_policy="unknown")


def test_generate_unique_puzzle_raises_when_attempt_budget_is_exhausted() -> None:
    with pytest.raises(GenerationFailed):
        generate_unique_puzzle(rows=4, cols=4, rooms=4, seed=0, max_attempts=1, reveal_policy="empty")


@pytest.mark.regression
def test_build_puzzle_corpus_writes_requested_unique_puzzles(workspace_tmp_dir) -> None:
    output_dir = workspace_tmp_dir.joinpath("corpus")
    result = build_puzzle_corpus(
        count=2,
        rows=4,
        cols=4,
        rooms=4,
        seed_start=0,
        max_seeds=10,
        out_dir=output_dir,
        reveal_policy="empty",
    )

    assert result.generated_count == 2
    assert result.requested_count == 2
    assert len(list(output_dir.glob("*.txt"))) == 2
    assert all(item.status == "written" for item in result.items if item.output_path is not None)


@pytest.mark.regression
def test_build_puzzle_corpus_skips_duplicates_against_existing_output(workspace_tmp_dir) -> None:
    output_dir = workspace_tmp_dir.joinpath("corpus")
    first = build_puzzle_corpus(
        count=1,
        rows=4,
        cols=4,
        rooms=4,
        seed_start=0,
        max_seeds=1,
        out_dir=output_dir,
        reveal_policy="empty",
    )
    second = build_puzzle_corpus(
        count=1,
        rows=4,
        cols=4,
        rooms=4,
        seed_start=0,
        max_seeds=2,
        out_dir=output_dir,
        reveal_policy="empty",
    )

    assert first.generated_count == 1
    assert second.generated_count == 1
    assert second.duplicates_skipped >= 1
    assert any(item.status == "duplicate" for item in second.items)


def test_build_puzzle_corpus_applies_quality_filters(workspace_tmp_dir) -> None:
    output_dir = workspace_tmp_dir.joinpath("filtered")
    result = build_puzzle_corpus(
        count=1,
        rows=4,
        cols=4,
        rooms=4,
        seed_start=0,
        max_seeds=3,
        out_dir=output_dir,
        reveal_policy="empty",
        filters=GenerationFilters(min_solve_iterations=500),
    )

    assert result.generated_count == 0
    assert result.quality_rejected >= 1
    assert any(item.status == "rejected-quality" for item in result.items)
