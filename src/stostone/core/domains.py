from __future__ import annotations

import itertools

from ..models import Coord
from .grid import is_connected


def connected_subgrids(coords: list[Coord], num_squares: int | None = None) -> list[list[Coord]] | None:
    if num_squares is not None and len(coords) < num_squares:
        return None
    if not is_connected(coords):
        return None

    subgrids: list[list[Coord]] = []
    n = len(coords)

    if num_squares is None:
        candidate_indices = (
            [index for index, included in enumerate(binary) if included]
            for binary in itertools.product([0, 1], repeat=n)
        )
    else:
        candidate_indices = itertools.combinations(range(n), num_squares)

    for indices in candidate_indices:
        index_set = set(indices)
        if num_squares is None and not index_set:
            continue
        subgrid = [coord for index, coord in enumerate(coords) if index in index_set]
        if is_connected(subgrid):
            subgrids.append(subgrid)

    return subgrids
