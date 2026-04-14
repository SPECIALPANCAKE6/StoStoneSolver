from __future__ import annotations

import pathlib

from ..io.puzpre import load_puzzle, load_puzzle_summary


def printFormatGrid(name: list[list[int | str]]) -> str:
    return "\n".join(["\t".join([str(cell) for cell in row]) for row in name])


def readPuzzleMetadata(inputFile: pathlib.Path | str) -> dict[str, int | str | None]:
    summary = load_puzzle_summary(inputFile)
    return {
        "rows": summary.rows,
        "cols": summary.cols,
        "rooms": summary.rooms,
        "numbered_rooms": summary.numbered_rooms,
        "pre_shaded_cells": summary.pre_shaded_cells,
        "author": summary.author,
        "difficulty": summary.difficulty,
    }


def readPuzzle(inputFile: pathlib.Path | str) -> dict[str, object]:
    return load_puzzle(inputFile).to_legacy_dict()


__all__ = [
    "printFormatGrid",
    "readPuzzle",
    "readPuzzleMetadata",
]
