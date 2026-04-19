from __future__ import annotations

from ..assembly import assemble_puzzle, derive_room_cache, reset_state


build_puzzle = assemble_puzzle


__all__ = [
    "assemble_puzzle",
    "build_puzzle",
    "derive_room_cache",
    "reset_state",
]
