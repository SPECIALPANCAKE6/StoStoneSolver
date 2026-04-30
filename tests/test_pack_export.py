from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.stostone.io.puzpre import load_puzzle
from src.stostone.pack_export import PACK_SCHEMA_VERSION, canonical_puzzle_hash, export_pack
from src.stostone.pack_export.service import SourcePuzzleSpec


pytestmark = [pytest.mark.integration, pytest.mark.regression]


def test_canonical_puzzle_hash_ignores_metadata(puzzle_path) -> None:
    first = load_puzzle(puzzle_path("000-001.txt"))
    second = load_puzzle(puzzle_path("000-001.txt"))
    second.spec.metadata.author = "Someone Else"
    second.spec.metadata.extra_fields["generator_seed"] = "999"

    assert canonical_puzzle_hash(first) == canonical_puzzle_hash(second)


def test_export_pack_uses_id_indexed_maps_and_local_mvp_classification(workspace_tmp_dir: Path, puzzle_dir: Path) -> None:
    pack_path = workspace_tmp_dir.joinpath("pack.json")
    result = export_pack(
        output_path=pack_path,
        puzzle_dir=puzzle_dir,
        source_specs=[SourcePuzzleSpec("000-001.txt", category="tutorial", difficulty="Tutorial")],
    )

    assert result.pack_path == pack_path.resolve()
    assert result.build_report_path == pack_path.with_suffix(".build_report.json").resolve()
    assert result.pack["schema_version"] == PACK_SCHEMA_VERSION
    assert result.pack["pack_type"] == "local_mvp"
    assert result.pack["contains_solutions"] is True
    assert result.pack["contains_debug_data"] is False

    puzzles = result.pack["puzzles_by_id"]
    solutions = result.pack["solutions_by_puzzle_id"]
    hints = result.pack["hint_plans_by_puzzle_id"]
    assert isinstance(puzzles, dict)
    assert isinstance(solutions, dict)
    assert isinstance(hints, dict)
    puzzle_id = next(iter(puzzles))
    assert puzzle_id in solutions
    assert puzzle_id in hints
    assert puzzles[puzzle_id]["puzzle_id"] == puzzle_id
    assert puzzles[puzzle_id]["canonical_hash"]
    assert puzzles[puzzle_id]["unique_solution_proof"]["is_unique"] is True
    assert solutions[puzzle_id]["usage_scope"] == "local_mvp_dev_only"
    assert hints[puzzle_id]


def test_export_pack_build_report_records_required_summary_fields(workspace_tmp_dir: Path, puzzle_dir: Path) -> None:
    pack_path = workspace_tmp_dir.joinpath("report-pack.json")
    result = export_pack(
        output_path=pack_path,
        puzzle_dir=puzzle_dir,
        source_specs=[SourcePuzzleSpec("000-001.txt", category="easy", difficulty="Easy")],
    )

    report = json.loads(result.build_report_path.read_text(encoding="utf-8"))
    assert report["schema_version"] == PACK_SCHEMA_VERSION
    assert report["source_puzpre_files"]
    assert report["generated_seeds"] == []
    assert report["generator_options"] == []
    assert report["duplicate_count"] == 0
    assert report["rejected_puzzle_count"] == 0
    assert report["uniqueness_count_results"]
    assert report["difficulty_distribution"]["Easy"] == 1
    assert report["solve_iterations"]["min"] >= 0
    assert "git_commit" in report


def test_pack_schemas_define_coordinate_and_classification_contract(repo_root: Path) -> None:
    pack_schema = json.loads(repo_root.joinpath("shared", "schemas", "PuzzlePack.schema.json").read_text(encoding="utf-8"))
    solution_schema = json.loads(repo_root.joinpath("shared", "schemas", "SolutionDTO.schema.json").read_text(encoding="utf-8"))

    assert "pack_type" in pack_schema["required"]
    assert pack_schema["properties"]["pack_type"]["enum"] == ["local_mvp", "dev", "debug", "public", "competitive"]
    assert "zero-based [row, col]" in solution_schema["description"]
    assert "not valid for competitive" in solution_schema["description"]


def test_cli_export_pack_writes_pack_and_build_report(repo_root: Path, workspace_tmp_dir: Path) -> None:
    pack_path = workspace_tmp_dir.joinpath("cli-pack.json")
    result = subprocess.run(
        [
            sys.executable,
            "Solver.py",
            "export-pack",
            "--puzzles",
            "000-001.txt",
            "--source-category",
            "easy",
            "--out",
            str(pack_path),
        ],
        cwd=repo_root,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Wrote puzzle pack" in result.stdout
    assert pack_path.is_file()
    assert pack_path.with_suffix(".build_report.json").is_file()
