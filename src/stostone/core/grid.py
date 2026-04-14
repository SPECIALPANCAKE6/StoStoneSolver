from __future__ import annotations

import random
from collections import deque

from ..models import Border, Coord


def grid_neighbors(coord: Coord, rows: int | None = None, cols: int | None = None) -> list[Coord]:
    r, c = coord
    neighbors: list[Coord] = []

    if r > 0:
        neighbors.append((r - 1, c))
    if rows is None or r < rows - 1:
        neighbors.append((r + 1, c))
    if c > 0:
        neighbors.append((r, c - 1))
    if cols is None or c < cols - 1:
        neighbors.append((r, c + 1))

    return neighbors


def border_gen(coords: list[Coord], rows: int, cols: int) -> list[Border]:
    coord_set = set(coords)
    borders: list[Border] = []
    for coord in coords:
        for neighbor in grid_neighbors(coord, rows, cols):
            if neighbor not in coord_set:
                borders.append((neighbor, coord))
    return borders


def grid_bfs(coords: list[Coord]) -> list[Coord] | None:
    if not coords:
        return None

    found: list[Coord] = []
    todo = deque([coords[0]])
    coord_set = set(coords)

    while todo:
        current = todo.popleft()
        for neighbor in grid_neighbors(current):
            if neighbor in coord_set and neighbor not in found and neighbor not in todo:
                todo.append(neighbor)
        found.append(current)

    return found


def is_connected(coords: list[Coord]) -> bool:
    found = grid_bfs(coords)
    return found is not None and len(found) == len(coords)


def random_coords(rows: int, cols: int, num: int) -> list[Coord] | None:
    if num > rows * cols:
        return None

    coords: list[Coord] = []
    while len(coords) < num:
        coord = (random.randint(0, rows - 1), random.randint(0, cols - 1))
        if coord not in coords:
            coords.append(coord)
    return coords

