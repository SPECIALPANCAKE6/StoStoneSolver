from __future__ import annotations

from ..models import legacy_dict_to_puzzle, sync_legacy_dict
from ..solver.search import backtrack as _backtrack
from ..solver.state_ops import draw_stone as _draw_stone
from ..solver.state_ops import restore_cells as _restore_cells
from ..solver.validation import can_stone_drop, drop_down, fills_bottom_half, get_below, is_sto_sand, is_sto_stone


def isStoSand(puzzleDict: dict[str, object]) -> bool:
    return is_sto_sand(legacy_dict_to_puzzle(puzzleDict))


def fillsBottomHalf(puzzleDict: dict[str, object]) -> bool:
    return fills_bottom_half(legacy_dict_to_puzzle(puzzleDict))


def getBelow(stone, rows):
    return get_below(stone, rows)


def canStoneDrop(subgrid, state, current_stone) -> bool:
    return can_stone_drop(subgrid, state, current_stone)


def isStoStone(puzzleDict: dict[str, object]) -> bool:
    puzzle = legacy_dict_to_puzzle(puzzleDict)
    solved = is_sto_stone(puzzle)
    sync_legacy_dict(puzzleDict, puzzle)
    return solved


def backtrack(roomNum: int, puzzleDict: dict[str, object], mode: str = "sto-stone") -> bool:
    puzzle = legacy_dict_to_puzzle(puzzleDict)
    solved = _backtrack(roomNum, puzzle, mode=mode)  # type: ignore[arg-type]
    sync_legacy_dict(puzzleDict, puzzle)
    return solved


def dropDown(previous_stone, stone, state) -> None:
    drop_down(previous_stone, stone, state)


def drawStone(subgrid, state) -> None:
    _draw_stone(subgrid, state)


def unDraw(subgrid, state, initialState=None) -> None:
    _restore_cells(subgrid, state, initialState)


__all__ = [
    "backtrack",
    "canStoneDrop",
    "drawStone",
    "dropDown",
    "fillsBottomHalf",
    "getBelow",
    "isStoSand",
    "isStoStone",
    "unDraw",
]
