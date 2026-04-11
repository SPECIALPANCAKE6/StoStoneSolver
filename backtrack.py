import domainBuilder

# the backtracking module no longer relies on global puzzle state stored in
# readPuzzle; instead every function takes a puzzleDict that was returned by
# readPuzzle.readPuzzle.  This keeps the solver reentrant and removes hidden
# dependencies.


def isStoSand(puzzleDict: dict[str, int | list]) -> bool:
    """
    Sto-Sand check applied to a puzzle dictionary.  Uses only the passed state and
    dimensions instead of reading globals.
    """
    rows = puzzleDict['rows']
    cols = puzzleDict['cols']
    state = puzzleDict['state']

    colCounter = [0] * cols
    for r in range(rows):
        for c in range(cols):
            if state[r][c] == ' #':
                colCounter[c] += 1
    # rows is integer; ensure the half is integrally compared
    half = rows // 2
    return all(count == half for count in colCounter)


def fillsBottomHalf(puzzleDict: dict[str, int | list]) -> bool:
    """Return True when the current board is exactly the bottom half filled.

    Sto-Stone's final rigid-drop state must occupy every cell in the bottom
    half of the grid and leave every cell in the top half empty.
    """
    rows = puzzleDict['rows']
    cols = puzzleDict['cols']
    state = puzzleDict['state']
    half = rows // 2

    return all(state[r][c] != ' #' for r in range(half) for c in range(cols)) and \
        all(state[r][c] == ' #' for r in range(half, rows) for c in range(cols))


def getBelow(stone: list[tuple[int,int]], rows: int) -> list[tuple[int,int] | None]:
    """Return the coordinates directly below each cell in a stone.
    Cells that would fall off the bottom edge are replaced with None.
    """
    cellsBelow = [None] * len(stone)
    for idx, (r, c) in enumerate(stone):
        if r + 1 < rows:
            cellsBelow[idx] = (r + 1, c)
    return cellsBelow


def canStoneDrop(roomNum: int, subgrid: list[tuple[int,int] | None],
                 puzzleDict: dict[str, int | list]) -> bool:
    """Return True if the stone described by `subgrid` can drop one row.

    subgrid is the output of `getBelow`; entries may be None when the stone
    is at the bottom of the board.  roomNum is only needed for consulting
    the previously placed stones from the last successful configuration.
    """
    state = puzzleDict['state']
    current_stone = set(puzzleDict['lastPlaced'][roomNum] or [])

    for cell in subgrid:
        if cell is None:
            return False
        if cell not in current_stone and state[cell[0]][cell[1]] != -1:
            return False
    return True


def dropDown(roomNum: int, stone: list[tuple[int,int]],
             puzzleDict: dict[str, int | list]) -> None:
    """Move the last placed stone for roomNum out and replace with `stone`.

    This function mutates `puzzleDict['state']` via domainBuilder helpers.
    """
    state = puzzleDict['state']
    domainBuilder.unDraw(puzzleDict['lastPlaced'][roomNum], state)
    domainBuilder.drawStone(stone, state)


def isStoStone(puzzleDict: dict[str, int | list]) -> bool:
    """Perform the Sto-Stone drop test on the current puzzle dictionary.

    This function simulates gravity for the stones stored in
    `puzzleDict['drawnStones']`.  It modifies the state as it drops stones and
    uses `puzzleDict['lastPlaced']` to remember the previous configuration so
    it can restore it at the end if the test fails.
    """
    rows = puzzleDict['rows']
    state = puzzleDict['state']
    drawn = puzzleDict['drawnStones']
    lastPlaced = puzzleDict['lastPlaced']
    belows = [getBelow(stone, rows) for stone in drawn]
    emptyBelow = [canStoneDrop(i, belows[i], puzzleDict) for i in range(len(belows))]

    while any(emptyBelow):
        for idx, below in enumerate(belows):
            if emptyBelow[idx]:
                dropDown(idx, below, puzzleDict)
                lastPlaced[idx] = below
                belows[idx] = getBelow(below, rows)
                emptyBelow[idx] = canStoneDrop(idx, belows[idx], puzzleDict)

    if fillsBottomHalf(puzzleDict):
        return True

    # restore original stones
    for room, stone in enumerate(drawn):
        domainBuilder.unDraw(lastPlaced[room], state)
        domainBuilder.drawStone(stone, state)
    return False


def backtrack(roomNum: int, puzzleDict: dict[str, int | list],
              mode: str = "sto-stone") -> bool:
    """Recursive backtracking search using an explicit puzzle dictionary.

    Returns True as soon as a solution matching `mode` is discovered; otherwise
    False. The puzzleDict is mutated in place (stones drawn/undrawn) but
    restored before the call returns to its caller.
    """
    rooms = puzzleDict['rooms']

    # allocate lastPlaced list on first call
    if 'lastPlaced' not in puzzleDict:
        puzzleDict['lastPlaced'] = [None] * rooms

    if roomNum >= rooms:
        # all rooms assigned; check the requested drop rules
        puzzleDict['lastPlaced'] = list(puzzleDict['drawnStones'])
        sto_sand = isStoSand(puzzleDict)
        if mode == "sto-sand":
            return sto_sand
        if not sto_sand:
            return False
        return isStoStone(puzzleDict)

    state = puzzleDict['state']
    domain = domainBuilder.domainReduce(
        puzzleDict['allRoomBorders'][roomNum],
        puzzleDict['allRoomDomains'][roomNum],
        state
    )
    for subgrid in domain:
        domainBuilder.drawStone(subgrid, state)
        puzzleDict['drawnStones'][roomNum] = subgrid
        if backtrack(roomNum + 1, puzzleDict, mode):
            return True
        domainBuilder.unDraw(subgrid, state, puzzleDict['initialState'])
        puzzleDict['drawnStones'][roomNum] = None
    return False
