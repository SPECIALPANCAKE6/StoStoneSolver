from __future__ import annotations

import pytest

from src.stostone.engine import engine


pytestmark = pytest.mark.integration


def test_engine_load_and_summarize_share_same_puzzle_metadata(puzzle_path) -> None:
    puzzle = engine.load(puzzle_path("000-000.txt"))
    summary = engine.summarize(puzzle_path("000-000.txt"))

    assert puzzle.rows == 4
    assert summary.rooms == puzzle.rooms == 5
    assert summary.author == "Addison Allen"
    assert summary.difficulty == "Easy"


@pytest.mark.regression
def test_engine_solve_and_count_cover_app_facing_solver_api(puzzle_path) -> None:
    solved = engine.solve(puzzle_path("000-000.txt"))
    unique = engine.count(puzzle_path("000-001.txt"), limit=2)

    assert solved.solved
    assert solved.mode == "sto-stone"
    assert solved.puzzle is not None
    assert solved.puzzle.state.constraint_checks > 0

    assert unique.solution_count == 1
    assert unique.is_unique
    assert unique.puzzle is not None
    assert unique.puzzle.state.constraint_checks > 0


@pytest.mark.regression
def test_engine_generate_and_generate_corpus_expose_generation_surface(workspace_tmp_dir) -> None:
    single = engine.generate(rows=4, cols=4, rooms=4, seed=0, max_attempts=20, reveal_policy="empty")
    summary_path = workspace_tmp_dir.joinpath("engine-corpus-summary.json")
    corpus_dir = workspace_tmp_dir.joinpath("engine-corpus")
    batch = engine.generate_corpus(
        count=2,
        rows=4,
        cols=4,
        rooms=4,
        seed_start=0,
        max_seeds=10,
        reveal_policy="empty",
        out_dir=corpus_dir,
        summary_path=summary_path,
    )

    assert single.solution_count == 1
    assert single.quality is not None
    assert single.puzzle.spec.metadata.difficulty == single.quality.difficulty

    assert batch.generated_count == 2
    assert batch.requested_count == 2
    assert batch.summary_path == summary_path.resolve()
    assert len(list(corpus_dir.glob("*.txt"))) == 2
