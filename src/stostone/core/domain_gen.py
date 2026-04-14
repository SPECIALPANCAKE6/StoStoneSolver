from __future__ import annotations

from .domains import connected_subgrids


def domainGen(currRoomIndices, currRoomWeight = None):
    return connected_subgrids(currRoomIndices, currRoomWeight)


__all__ = ["domainGen"]
