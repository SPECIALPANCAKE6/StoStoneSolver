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
def test_cli_generate_accepts_preset_flags(repo_root: Path, workspace_tmp_dir: Path) -> None:
    output_path = workspace_tmp_dir.joinpath("guided-easy.txt")
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
        "1",
        "--max-attempts",
        "20",
        "--difficulty-preset",
        "easy",
        "--clue-profile",
        "guided",
        "--output",
        str(output_path),
    )

    assert result.returncode == 0
    assert "Presets: quality=none difficulty=easy clue_profile=guided" in result.stdout

    puzzle = load_puzzle(output_path)
    assert puzzle.spec.metadata.extra_fields["difficulty_preset"] == "easy"
    assert puzzle.spec.metadata.extra_fields["difficulty_family"] == "4x4-4r"
    assert puzzle.spec.metadata.extra_fields["difficulty_scale"] == "calibrated"
    assert puzzle.spec.metadata.extra_fields["clue_profile"] == "guided"
    assert puzzle.spec.metadata.extra_fields["requested_reveal_policy"] == "few-cells"
    assert puzzle.spec.metadata.difficulty == "Easy"


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
    written_items = [item for item in summary["items"] if item["status"] == "written"]
    assert written_items
    assert "revealed_cell_count" in written_items[0]["generation"]
    assert "revealed_room_count" in written_items[0]["generation"]


@pytest.mark.regression
def test_cli_calibrate_writes_markdown_and_json_reports(repo_root: Path, workspace_tmp_dir: Path) -> None:
    summary_path = workspace_tmp_dir.joinpath("synthetic-summary.json")
    report_path = workspace_tmp_dir.joinpath("calibration-report.md")
    json_report_path = workspace_tmp_dir.joinpath("calibration-report.json")
    summary = {
        "items": [
            {
                "seed": 1,
                "status": "written",
                "signature": "sig-1",
                "generation": {
                    "rows": 4,
                    "cols": 4,
                    "rooms": 4,
                    "attempts": 2,
                    "numbered_rooms": 2,
                    "requested_reveal_policy": "empty",
                    "applied_reveal_policy": "empty",
                },
                "quality": {
                    "difficulty_score": 20,
                    "solve_iterations": 8,
                    "room_balance": 0.5,
                    "shape_compactness": 0.8,
                    "room_size_spread": 2,
                    "given_shaded_cells": 0,
                    "pre_solved_rooms": 0,
                },
            }
        ]
    }
    summary_path.write_text(json.dumps(summary), encoding="utf-8")

    result = run_cli(
        repo_root,
        "calibrate",
        str(summary_path),
        "--report",
        str(report_path),
        "--json-report",
        str(json_report_path),
    )

    assert result.returncode == 0
    assert "Wrote calibration report" in result.stdout
    assert report_path.is_file()
    assert json_report_path.is_file()
    assert "Sto-Stone Generator Calibration Report" in report_path.read_text(encoding="utf-8")

    report = json.loads(json_report_path.read_text(encoding="utf-8"))
    assert report["record_count"] == 1
    assert report["families"]["4x4-4r"]["record_count"] == 1


@pytest.mark.regression
def test_cli_calibrate_corpus_runs_plan_and_writes_combined_report(repo_root: Path, workspace_tmp_dir: Path) -> None:
    plan_path = workspace_tmp_dir.joinpath("calibration", "plan.json")
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    report_path = workspace_tmp_dir.joinpath("calibration", "report.md")
    json_report_path = workspace_tmp_dir.joinpath("calibration", "report.json")
    summary_path = plan_path.parent.joinpath("summaries", "4x4-4r.json")
    plan_path.write_text(
        json.dumps(
            {
                "families": [
                    {
                        "rows": 4,
                        "cols": 4,
                        "rooms": 4,
                        "count": 1,
                        "seed_start": 0,
                        "max_seeds": 5,
                        "max_attempts": 20,
                        "reveal_policy": "empty",
                        "out_dir": "corpus/4x4-4r",
                        "summary_file": "summaries/4x4-4r.json",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    result = run_cli(
        repo_root,
        "calibrate-corpus",
        "--plan",
        str(plan_path),
        "--report",
        str(report_path),
        "--json-report",
        str(json_report_path),
    )

    assert result.returncode == 0
    assert "Generated 4x4-4r" in result.stdout
    assert summary_path.is_file()
    assert report_path.is_file()
    assert json_report_path.is_file()

    report = json.loads(json_report_path.read_text(encoding="utf-8"))
    assert report["record_count"] == 1
    assert report["families"]["4x4-4r"]["record_count"] == 1


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
