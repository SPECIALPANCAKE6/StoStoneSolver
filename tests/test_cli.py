from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


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
