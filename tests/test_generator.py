from __future__ import annotations

import random

import pytest

from src.stostone.generator import DEFAULT_GENERATOR_NAME, GenerationFailed, build_puzzle_corpus, generate_unique_puzzle
from src.stostone.generator import service as generator_service
from src.stostone.models import GenerationFilters
from src.stostone.generator.presets import (
    difficulty_label_from_score,
    difficulty_presets_for_family,
    difficulty_scale_for_family,
    resolve_generation_controls,
)
from src.stostone.generator.scoring import DIFFICULTY_SCORE_MODEL, score_generation_quality
from src.stostone.solver.service import count_puzzle_solutions


pytestmark = pytest.mark.integration


def _count_given_cells(initial_state: list[list[int | str]]) -> int:
    return sum(cell == " #" for row in initial_state for cell in row)


def test_reveal_policy_maps_define_expected_distribution() -> None:
    assert generator_service.REVEAL_POLICY_MAPS["mostly-empty"] == (
        ("empty", 0.8),
        ("few-cells", 0.15),
        ("full-room", 0.05),
    )
    assert generator_service.REVEAL_POLICY_MAPS["empty"] == (("empty", 1.0),)
    assert generator_service.REVEAL_POLICY_MAPS["few-cells"] == (("few-cells", 1.0),)
    assert generator_service.REVEAL_POLICY_MAPS["full-room"] == (("full-room", 1.0),)


def test_resolve_generation_controls_merges_presets_and_explicit_overrides() -> None:
    filters, reveal_policy, clue_carving = resolve_generation_controls(
        reveal_policy="empty",
        clue_carving=True,
        filters=GenerationFilters(max_given_shaded_cells=1),
        quality_preset="balanced",
        difficulty_preset="easy",
        clue_profile="guided",
    )

    assert reveal_policy == "empty"
    assert clue_carving is True
    assert filters.min_room_balance == 0.3
    assert filters.min_shape_compactness == 0.75
    assert filters.max_room_size_spread == 5
    assert filters.max_difficulty_score == 25.0
    assert filters.max_given_shaded_cells == 1
    assert filters.max_pre_solved_rooms == 2


def test_difficulty_presets_can_use_calibrated_board_family_bands() -> None:
    global_filters, _, _ = resolve_generation_controls(
        reveal_policy="empty",
        clue_carving=True,
        difficulty_preset="easy",
    )
    family_filters, _, _ = resolve_generation_controls(
        reveal_policy="empty",
        clue_carving=True,
        difficulty_preset="easy",
        board_family="6x6-6r",
    )

    eight_by_eight = difficulty_presets_for_family("8x8-8r")
    varied_size = difficulty_presets_for_family("4x6-6r")

    assert global_filters.max_difficulty_score == 25.0
    assert family_filters.max_difficulty_score == 75.0
    assert eight_by_eight["easy"].max_difficulty_score == 50.0
    assert eight_by_eight["medium"].max_difficulty_score == 80.0
    assert eight_by_eight["hard"].max_difficulty_score == 90.0
    assert varied_size["easy"].max_difficulty_score > global_filters.max_difficulty_score
    assert varied_size["medium"].max_difficulty_score <= varied_size["hard"].max_difficulty_score
    assert difficulty_label_from_score(70, None) == "Hard"
    assert difficulty_label_from_score(70, "6x6-6r") == "Easy"
    assert difficulty_label_from_score(76, "8x8-8r") == "Medium"
    assert difficulty_label_from_score(88, "8x8-8r") == "Hard"
    assert difficulty_scale_for_family("8x8-8r") == "calibrated"
    assert difficulty_scale_for_family("4x6-6r") == "heuristic"
    assert difficulty_scale_for_family(None) == "global"


def test_large_board_difficulty_score_keeps_iteration_separation() -> None:
    shared_metrics = {
        "room_balance": 0.6,
        "shape_compactness": 0.75,
        "given_shaded_cells": 0,
        "pre_solved_rooms": 0,
    }
    medium_search = score_generation_quality(solve_iterations=128, rows=8, cols=8, **shared_metrics)
    deeper_search = score_generation_quality(solve_iterations=1000, rows=8, cols=8, **shared_metrics)

    assert deeper_search > medium_search + 15
    assert deeper_search < 100


def test_large_board_witness_search_rejects_expensive_layouts() -> None:
    puzzle = generator_service._build_solution_search_puzzle(8, 8, 8, random.Random(30002))

    reason = generator_service._witness_search_rejection_reason(puzzle)

    assert reason is not None
    assert "exceeds witness-search budget" in reason


def test_large_board_witness_prefilter_rejects_heavy_domain_layouts() -> None:
    puzzle = generator_service._build_solution_search_puzzle(8, 8, 8, random.Random(30051))

    reason = generator_service._witness_search_rejection_reason(puzzle)

    assert reason is not None
    assert "heavy room domains" in reason


def test_large_board_witness_prefilter_keeps_searchable_seeded_layout() -> None:
    rng = random.Random(30000)
    puzzle = None
    for _ in range(15):
        puzzle = generator_service._build_solution_search_puzzle(8, 8, 8, rng)

    assert puzzle is not None
    assert generator_service._witness_search_rejection_reason(puzzle) is None


def test_clone_puzzle_returns_independent_copy(build_puzzle) -> None:
    puzzle = build_puzzle(2, 2, [[0, 0], [0, 0]])
    puzzle.state.grid[0][0] = " #"
    puzzle.state.drawn_stones[0] = [(0, 0)]

    cloned = generator_service._clone_puzzle(puzzle)
    cloned.state.grid[1][1] = " #"
    cloned.state.drawn_stones[0] = [(1, 1)]

    assert puzzle.state.grid == [[" #", -1], [-1, -1]]
    assert puzzle.state.drawn_stones == [[(0, 0)]]


def test_mostly_empty_reveal_policy_distribution_cutoffs() -> None:
    class StubRandom:
        def __init__(self, value: float) -> None:
            self.value = value

        def random(self) -> float:
            return self.value

    assert generator_service._choose_applied_reveal_policy("mostly-empty", StubRandom(0.0)) == "empty"
    assert generator_service._choose_applied_reveal_policy("mostly-empty", StubRandom(0.7999)) == "empty"
    assert generator_service._choose_applied_reveal_policy("mostly-empty", StubRandom(0.8)) == "few-cells"
    assert generator_service._choose_applied_reveal_policy("mostly-empty", StubRandom(0.9499)) == "few-cells"
    assert generator_service._choose_applied_reveal_policy("mostly-empty", StubRandom(0.95)) == "full-room"


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


def test_generate_unique_puzzle_few_cells_policy_reveals_between_one_and_four_cells() -> None:
    result = generate_unique_puzzle(rows=4, cols=4, rooms=4, seed=0, max_attempts=20, reveal_policy="few-cells")
    metadata = result.puzzle.spec.metadata.extra_fields

    assert result.applied_reveal_policy == "few-cells"
    assert 1 <= result.revealed_cell_count <= 4
    assert 1 <= result.revealed_room_count <= result.revealed_cell_count
    assert result.given_shaded_cells == result.revealed_cell_count
    assert result.pre_solved_rooms <= result.revealed_room_count
    assert _count_given_cells(result.puzzle.spec.initial_state) == result.revealed_cell_count
    assert metadata["revealed_cell_count"] == str(result.revealed_cell_count)
    assert metadata["revealed_room_count"] == str(result.revealed_room_count)
    assert count_puzzle_solutions(result.puzzle, limit=2).solution_count == 1


def test_generate_unique_puzzle_preset_metadata_tracks_effective_generation_controls() -> None:
    result = generate_unique_puzzle(
        rows=4,
        cols=4,
        rooms=4,
        seed=1,
        max_attempts=20,
        difficulty_preset="easy",
        clue_profile="guided",
    )
    metadata = result.puzzle.spec.metadata.extra_fields

    assert result.quality is not None
    assert result.difficulty_preset == "easy"
    assert result.clue_profile == "guided"
    assert result.requested_reveal_policy == "few-cells"
    assert result.applied_reveal_policy == "few-cells"
    assert result.quality.difficulty == "Easy"
    assert result.difficulty_family == "4x4-4r"
    assert result.difficulty_scale == "calibrated"
    assert 1 <= result.revealed_cell_count <= 4
    assert metadata["difficulty_preset"] == "easy"
    assert metadata["difficulty_family"] == "4x4-4r"
    assert metadata["difficulty_scale"] == "calibrated"
    assert metadata["clue_profile"] == "guided"
    assert metadata["requested_reveal_policy"] == "few-cells"
    assert count_puzzle_solutions(result.puzzle, limit=2).solution_count == 1


def test_generate_unique_puzzle_records_clue_carving_budget_exhaustion(monkeypatch) -> None:
    call_count = 0

    def exhaust_budget(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return generator_service._BudgetedSolutionCount(
                solution_count=1,
                constraint_checks=3,
                first_solution_iteration=2,
            )
        return None

    monkeypatch.setattr(generator_service, "_count_solutions_with_constraint_budget", exhaust_budget)

    result = generate_unique_puzzle(rows=4, cols=4, rooms=4, seed=0, max_attempts=20, reveal_policy="empty")
    metadata = result.puzzle.spec.metadata.extra_fields

    assert result.clue_carving_checks == 1
    assert result.clue_carving_budget_exhausted is True
    assert result.numbered_rooms == result.numbered_rooms_before_carving
    assert metadata["clue_carving_budget_exhausted"] == "true"
    assert metadata["generator_solve_iteration_source"] == "uniqueness-first-solution"


def test_generate_unique_puzzle_uses_uniqueness_iteration_hint_for_quality(monkeypatch) -> None:
    def no_carving(*args, **kwargs):
        return args[1], 0, False, None

    monkeypatch.setattr(generator_service, "_carve_number_clues", no_carving)

    result = generate_unique_puzzle(
        rows=4,
        cols=4,
        rooms=4,
        seed=0,
        max_attempts=20,
        reveal_policy="empty",
    )
    metadata = result.puzzle.spec.metadata.extra_fields

    assert result.quality is not None
    assert result.quality.solve_iteration_source == "uniqueness-first-solution"
    assert metadata["generator_solve_iteration_source"] == "uniqueness-first-solution"
    assert metadata["generator_solve_iterations"] == str(result.quality.solve_iterations)


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
    assert result.revealed_room_count == 1
    assert result.revealed_cell_count == result.given_shaded_cells
    assert result.given_shaded_cells == _count_given_cells(result.puzzle.spec.initial_state)
    assert metadata.author == DEFAULT_GENERATOR_NAME
    assert metadata.extra_fields["generation_strategy"] == "solution-first"
    assert metadata.extra_fields["generator_seed"] == "0"
    assert metadata.extra_fields["difficulty_score"]
    assert metadata.extra_fields["difficulty_score_model"] == DIFFICULTY_SCORE_MODEL
    assert metadata.extra_fields["requested_reveal_policy"] == "full-room"
    assert metadata.extra_fields["applied_reveal_policy"] == "full-room"
    assert metadata.extra_fields["revealed_cell_count"] == str(result.revealed_cell_count)
    assert metadata.extra_fields["revealed_room_count"] == str(result.revealed_room_count)
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
