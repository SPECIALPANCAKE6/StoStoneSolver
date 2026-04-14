from __future__ import annotations

from ..core.grid import is_connected
from ..models import Puzzle, legacy_dict_to_puzzle


def room_is_connected(puzzle: Puzzle, room_num: int) -> bool:
    shaded = [
        cell
        for cell in puzzle.cache.all_room_indices[room_num]
        if puzzle.state.grid[cell[0]][cell[1]] == " #"
    ]
    return len(shaded) <= 1 or is_connected(shaded)


def connChecker(puzzle: Puzzle | dict[str, object], roomNum: int) -> bool:
    if isinstance(puzzle, dict):
        return room_is_connected(legacy_dict_to_puzzle(puzzle), roomNum)
    return room_is_connected(puzzle, roomNum)


__all__ = [
    "connChecker",
    "room_is_connected",
]
