from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest

from src.stostone.assembly import assemble_puzzle
from src.stostone.models import PuzzleMetadata, PuzzleSpec


REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def puzzle_dir(repo_root: Path) -> Path:
    return repo_root.joinpath("puzzles")


@pytest.fixture
def puzzle_path(puzzle_dir: Path):
    def _path(name: str) -> Path:
        return puzzle_dir.joinpath(name)

    return _path


@pytest.fixture
def workspace_tmp_dir(repo_root: Path, request: pytest.FixtureRequest) -> Path:
    base_dir = repo_root.joinpath("test-output", "pytest")
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "-", request.node.nodeid)
    work_dir = base_dir.joinpath(safe_name)
    if work_dir.exists():
        shutil.rmtree(work_dir, ignore_errors=True)
    work_dir.mkdir(parents=True, exist_ok=True)
    return work_dir


@pytest.fixture
def solutions_dir(workspace_tmp_dir: Path) -> Path:
    return workspace_tmp_dir.joinpath("solutions")


@pytest.fixture
def build_puzzle():
    def _build(
        rows: int,
        cols: int,
        layout: list[list[int]],
        weights: list[tuple[tuple[int, int], int] | None] | None = None,
        initial_state: list[list[int | str]] | None = None,
        *,
        info_section: str | None = None,
        metadata: PuzzleMetadata | None = None,
    ):
        rooms = max(cell for row in layout for cell in row) + 1
        return assemble_puzzle(
            PuzzleSpec(
                rows=rows,
                cols=cols,
                rooms=rooms,
                layout=layout,
                weights=[None] * rooms if weights is None else weights,
                initial_state=[[-1 for _ in range(cols)] for _ in range(rows)] if initial_state is None else initial_state,
                info_section=info_section,
                metadata=PuzzleMetadata() if metadata is None else metadata,
            )
        )

    return _build
