from __future__ import annotations

from .state_ops import domain_reduce, draw_stone, restore_cells


def domainReduce(borders, domain, state):
    return domain_reduce(borders, domain, state)


def drawStone(subgrid, state) -> None:
    draw_stone(subgrid, state)


def unDraw(subgrid, state, initialState=None) -> None:
    restore_cells(subgrid, state, initialState)


__all__ = [
    "domainReduce",
    "drawStone",
    "unDraw",
]
