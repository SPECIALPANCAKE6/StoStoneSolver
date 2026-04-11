import gridUtils


def domainGen(currRoomIndices, currRoomWeight = None):
    """Legacy compatibility wrapper for room-domain generation.

    The active solver now builds domains through ``gridUtils.connectedSubgrids``.
    Keep this thin wrapper so any older imports follow the same implementation
    instead of the stale prototype that depended on module globals.
    """
    return gridUtils.connectedSubgrids(currRoomIndices, currRoomWeight)
