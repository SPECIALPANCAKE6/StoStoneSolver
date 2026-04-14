from __future__ import annotations

from ..models import Border, CellGrid, Coord, Puzzle


def domain_reduce(
    borders: list[Border],
    domain: list[list[Coord]],
    state: CellGrid,
) -> list[list[Coord]]:
    if not borders:
        return domain

    reduced_domain: list[list[Coord]] = []
    for subgrid in domain:
        conflict = False
        for room_cell in subgrid:
            for outside_cell, border_cell in borders:
                if room_cell == border_cell and state[outside_cell[0]][outside_cell[1]] == " #":
                    conflict = True
                    break
            if conflict:
                break
        if not conflict:
            reduced_domain.append(subgrid)
    return reduced_domain


def draw_stone(subgrid: list[Coord], state: CellGrid) -> None:
    for r, c in subgrid:
        state[r][c] = " #"


def restore_cells(
    subgrid: list[Coord],
    state: CellGrid,
    initial_state: CellGrid | None = None,
) -> None:
    for r, c in subgrid:
        state[r][c] = -1 if initial_state is None else initial_state[r][c]


def reset_state(puzzle: Puzzle) -> None:
    puzzle.state.grid[:] = [row[:] for row in puzzle.spec.initial_state]
    puzzle.state.drawn_stones[:] = [None] * puzzle.spec.rooms
    puzzle.state.constraint_checks = 0

