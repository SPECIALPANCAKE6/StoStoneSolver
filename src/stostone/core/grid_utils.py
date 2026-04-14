from __future__ import annotations

from .domains import connected_subgrids
from .grid import border_gen, grid_bfs, grid_neighbors, is_connected, random_coords


def gridNeighbors(coord, rows=None, cols=None):
    return grid_neighbors(coord, rows, cols)


def borderGen(coords, rows: int, cols: int):
    return border_gen(coords, rows, cols)


def gridBFS(coords):
    return grid_bfs(coords)


def isConnected(coords):
    return is_connected(coords)


def connectedSubgrids(coords, numSquares=None):
    return connected_subgrids(coords, numSquares)


def randomCoords(rows: int, cols: int, num: int):
    return random_coords(rows, cols, num)


__all__ = [
    "borderGen",
    "connectedSubgrids",
    "gridBFS",
    "gridNeighbors",
    "isConnected",
    "randomCoords",
]
