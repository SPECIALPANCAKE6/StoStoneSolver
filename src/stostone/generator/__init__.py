from __future__ import annotations

from pathlib import Path

from ..core.domains import connected_subgrids
from ..core.grid import border_gen
from ..models import Puzzle, PuzzleSpec, PuzzleState, RoomCache
from ..solver.state_ops import reset_state


def derive_room_cache(spec: PuzzleSpec) -> RoomCache:
    all_room_indices: list[list[tuple[int, int]]] = [[] for _ in range(spec.rooms)]
    for r in range(spec.rows):
        for c in range(spec.cols):
            all_room_indices[spec.layout[r][c]].append((r, c))

    all_room_domains: list[list[list[tuple[int, int]]]] = []
    for room_num, room_indices in enumerate(all_room_indices):
        room_weight = spec.weights[room_num][1] if spec.weights[room_num] is not None else None
        domain = connected_subgrids(room_indices, room_weight)
        if domain is None:
            raise ValueError(f"Invalid room {room_num}: cannot generate connected subgrids")
        all_room_domains.append(domain)

    all_room_borders = [border_gen(room_indices, spec.rows, spec.cols) for room_indices in all_room_indices]
    return RoomCache(
        all_room_indices=all_room_indices,
        all_room_borders=all_room_borders,
        all_room_domains=all_room_domains,
    )


def build_puzzle(spec: PuzzleSpec, source_path: Path | None = None) -> Puzzle:
    cache = derive_room_cache(spec)
    state = PuzzleState(
        grid=[row[:] for row in spec.initial_state],
        drawn_stones=[None] * spec.rooms,
        constraint_checks=0,
    )
    return Puzzle(spec=spec, cache=cache, state=state, source_path=source_path.resolve() if source_path else None)


__all__ = [
    "build_puzzle",
    "derive_room_cache",
    "reset_state",
]
