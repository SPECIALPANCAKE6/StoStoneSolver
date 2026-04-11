from collections import deque

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
    currRoomIndices = puzzle['allRoomIndices'][roomNum]
    # Convert to set for O(1) membership checks
    room_cells = set(currRoomIndices)

    # Find all shaded cells in this room
    shaded = [cell for cell in currRoomIndices if state[cell[0]][cell[1]] == ' #']

    # If there are no shaded cells or only one, they're trivially connected
    if len(shaded) <= 1:
        return True

    # BFS from the first shaded cell to see if we can reach all others
    visited = {shaded[0]}
    queue = deque([shaded[0]])

    while queue:
        r, c = queue.popleft()
        # Check all 4 neighbors
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if (nr, nc) in room_cells and (nr, nc) not in visited:
                if state[nr][nc] == ' #':
                    visited.add((nr, nc))
                    queue.append((nr, nc))

    # All shaded cells are connected if we visited all of them
    return len(visited) == len(shaded)