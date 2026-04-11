import gridUtils

def connChecker(puzzle: dict, roomNum: int) -> bool:
    """
    Check whether all shaded cells (' #') in a room form a single connected component.

    Args:
        puzzle: The puzzle dictionary containing state, allRoomIndices, etc.
        roomNum: The room index.

    Returns:
        True if all shaded cells in the room are connected, False otherwise.
    """

    state = puzzle['state']
    shaded = [
        cell
        for cell in puzzle['allRoomIndices'][roomNum]
        if state[cell[0]][cell[1]] == ' #'
    ]
    return len(shaded) <= 1 or gridUtils.isConnected(shaded)
