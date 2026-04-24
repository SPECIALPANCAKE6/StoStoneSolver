from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.stostone import DEFAULT_GENERATOR_NAME, count_puzzle_solutions, load_puzzle, load_puzzle_summary


pytestmark = [pytest.mark.cli, pytest.mark.integration]


def run_cli(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "Solver.py", *args],
        cwd=repo_root,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_list_displays_known_puzzle(repo_root: Path) -> None:
    result = run_cli(repo_root, "list")

    assert result.returncode == 0
    assert "000-000.txt" in result.stdout


def test_cli_show_prints_metadata(repo_root: Path) -> None:
    result = run_cli(repo_root, "show", "000-000")

    assert result.returncode == 0
    assert "Rooms: 5" in result.stdout
    assert "Author: Addison Allen" in result.stdout
    assert "Difficulty: Easy" in result.stdout


@pytest.mark.regression
def test_cli_generate_writes_unique_puzzle_file(repo_root: Path) -> None:
    seed = next(
        candidate
        for candidate in range(1000)
        if not repo_root.joinpath("puzzles", f"generated-4x4-4r-seed{candidate}.txt").exists()
    )
    output_path = repo_root.joinpath("puzzles", f"generated-4x4-4r-seed{seed}.txt")

    try:
        result = run_cli(
            repo_root,
            "generate",
            "--rows",
            "4",
            "--cols",
            "4",
            "--rooms",
            "4",
            "--seed",
            str(seed),
            "--max-attempts",
            "20",
            "--reveal-policy",
            "empty",
        )

        assert result.returncode == 0
        assert output_path.is_file()
        assert output_path.name.startswith("generated-")
        assert "Generated" in result.stdout
        assert f"Seed: {seed}" in result.stdout

        puzzle = load_puzzle(output_path)
        assert puzzle.spec.metadata.author == DEFAULT_GENERATOR_NAME
        assert puzzle.spec.metadata.extra_fields["generator_seed"] == str(seed)
        assert puzzle.spec.metadata.extra_fields["requested_reveal_policy"] == "empty"
        assert count_puzzle_solutions(puzzle, limit=2).solution_count == 1
    finally:
        if output_path.exists():
            output_path.unlink()


@pytest.mark.regression
def test_cli_generate_supports_disabling_clue_carving(repo_root: Path, workspace_tmp_dir: Path) -> None:
    output_path = workspace_tmp_dir.joinpath("uncarved.txt")
    result = run_cli(
        repo_root,
        "generate",
        "--rows",
        "4",
        "--cols",
        "4",
        "--rooms",
        "4",
        "--seed",
        "0",
        "--max-attempts",
        "20",
        "--reveal-policy",
        "empty",
        "--output",
        str(output_path),
        "--no-clue-carving",
    )

    assert result.returncode == 0
    summary = load_puzzle_summary(output_path)
    assert summary.numbered_rooms == 4
    assert "Numbered rooms: 4 of 4" in result.stdout


@pytest.mark.regression
def test_cli_generate_batch_writes_corpus_and_summary(repo_root: Path, workspace_tmp_dir: Path) -> None:
    output_dir = workspace_tmp_dir.joinpath("corpus")
    summary_path = workspace_tmp_dir.joinpath("generation-summary.json")

    result = run_cli(
        repo_root,
        "generate",
        "--rows",
        "4",
        "--cols",
        "4",
        "--rooms",
        "4",
        "--count",
        "2",
        "--seed-start",
        "0",
        "--max-seeds",
        "10",
        "--reveal-policy",
        "empty",
        "--out-dir",
        str(output_dir),
        "--summary-file",
        str(summary_path),
    )

    assert result.returncode == 0
    assert len(list(output_dir.glob("*.txt"))) == 2
    assert summary_path.is_file()
    assert "Summary: wrote 2 of 2 requested puzzle(s)" in result.stdout

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["generated_count"] == 2
    assert summary["requested_count"] == 2
    assert len(summary["items"]) >= 2


@pytest.mark.regression
def test_cli_solve_writes_solution_file(repo_root: Path, workspace_tmp_dir: Path) -> None:
    solutions_dir = workspace_tmp_dir.joinpath("solutions")
    result = run_cli(repo_root, "solve", "000-000.txt", "--solutions-dir", str(solutions_dir))

    assert result.returncode == 0
    assert "Solved 000-000.txt" in result.stdout
    assert solutions_dir.joinpath("000-000-solved.txt").is_file()


def test_cli_reports_missing_puzzle_as_usage_error(repo_root: Path) -> None:
    result = run_cli(repo_root, "solve", "missing-puzzle.txt")

    assert result.returncode == 2
    assert "error:" in result.stderr
