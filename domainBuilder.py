
# Domain operations are pure helpers that work only on an explicitly
# supplied state grid; no module globals are used.

def domainReduce(borders: list[tuple[tuple[int,int], tuple[int,int]]],
                 domain: list[list[tuple[int,int]]],
                 state: list[list[int | str]]) -> list[list[tuple[int,int]]]:
    """Filter a room domain by the current board state and a set of borders.

    A domain entry is discarded if any of its cells coincide with a border
    position that is already shaded (' #').  ``state`` is mutated by other
    parts of the solver; it is passed in here so that this module remains
    stateless.
    """

    if not borders:
        # nothing to constrain
        return domain

    reducedDomain: list[list[tuple[int,int]]] = []
    for subgrid in domain:
        conflict = False
        for (r, c) in subgrid:
            for outside_cell, room_cell in borders:
                if (r, c) == room_cell and state[outside_cell[0]][outside_cell[1]] == ' #':
                    conflict = True
                    break
            if conflict:
                break
        if not conflict:
            reducedDomain.append(subgrid)
    return reducedDomain


def drawStone(subgrid: list[tuple[int,int]],
              state: list[list[int | str]]) -> None:
    """Mark every coordinate in ``subgrid`` as shaded in ``state``."""
    for (r, c) in subgrid:
        state[r][c] = ' #'


def unDraw(subgrid: list[tuple[int,int]],
           state: list[list[int | str]],
           initialState: list[list[int | str]] | None = None) -> None:
    """Erase or restore every coordinate in ``subgrid`` from ``state``.

    When ``initialState`` is supplied, cells are restored to their original
    puzzle values so pre-shaded givens survive backtracking cleanup.
    """
    for (r, c) in subgrid:
        state[r][c] = -1 if initialState is None else initialState[r][c]