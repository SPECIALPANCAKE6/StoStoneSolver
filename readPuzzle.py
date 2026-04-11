import pathlib
import gridUtils
import logging

logger = logging.getLogger(__name__)


def printFormatGrid(name: list[list[str]]) -> str:
    """
        printFormatGrid function which formats the grid for logging purposes

        Args:
            name (list[list[str]]): The grid to be formatted, represented as a list of lists of strings.

        Returns:
            str: A string representation of the grid, formatted for logging.
    """
    return '\n'.join(['\t'.join([str(cell) for cell in row]) for row in name])


def _readPuzzleSections(file) -> tuple[
    int,
    int,
    int,
    list[list[int]],
    list[tuple[tuple[int, int], int] | None],
    list[list[int | str]],
]:
    """Read the PUZ-PRE sections shared by metadata and full puzzle loading."""
    file.readline()
    file.readline()
    rows = int(file.readline())
    cols = int(file.readline())
    rooms = int(file.readline())

    layout = [[int(symbol) for symbol in file.readline().strip().split()] for _ in range(rows)]

    weights: list[tuple[tuple[int, int], int] | None] = [None] * rooms
    for row in range(rows):
        for col, weight in enumerate(file.readline().strip().split()):
            if weight != ".":
                weights[layout[row][col]] = ((row, col), int(weight))

    initialState = [[-1 if cell == "." else ' #' for cell in file.readline().strip().split()] for _ in range(rows)]
    return rows, cols, rooms, layout, weights, initialState


def readPuzzleMetadata(inputFile: pathlib.Path | str) -> dict[str, int]:
    """Load only the puzzle metadata needed by the lightweight CLI commands."""
    with open(inputFile, 'r') as file:
        rows, cols, rooms, _, weights, initialState = _readPuzzleSections(file)

    return {
        "rows": rows,
        "cols": cols,
        "rooms": rooms,
        "numbered_rooms": sum(weight is not None for weight in weights),
        "pre_shaded_cells": sum(cell == ' #' for row in initialState for cell in row),
    }


def readPuzzle(inputFile: pathlib.Path | str) -> dict:
    """
    readPuzzle function which reads the file input to find puzzle room layout, room weights, and pre-shaded cells.
    It also generates the initial state of the puzzle, the list of room indices, the list of room borders, and the list of room domains.

    Args:
        inputFile (pathlib.Path): The path to the input puzzle file.

    Returns:
        dict[str, int | list]: A dictionary containing the following keys and their corresponding values:
            - "rows" (int): The number of rows in the puzzle grid.
            - "cols" (int): The number of columns in the puzzle grid.
            - "weights" (list[tuple[tuple[int, int], int] | None]): A list of tuples containing the room index, coordinates, and weight for each room that has a weight. Rooms without weights will have a value of None.
            - "layout" (list[list[int]]): A 2D list representing the layout of the puzzle grid, where each cell contains the room index it belongs to.
            - "rooms" (int): The number of rooms in the puzzle.
            - "initialState" (list[list[int | str]]): A 2D list representing the initial state of the puzzle grid, where each cell is either -1 (indicating a unshaded cell) or ' #' (indicating a pre-shaded cell).
            - "state" (list[list[int | str]]): A 2D list representing the current state of the puzzle grid, initialized to the same values as "initialState".
            - "allRoomIndices" (list[list[tuple[int, int]]]): A list of lists, where each inner list contains the coordinates of the cells belonging to a specific room.
            - "allRoomBorders" (list[list[tuple[tuple[int, int], tuple[int, int]]]]): A list of lists, where each inner list contains the coordinates of the border cells for a specific room.
            - "allRoomDomains" (list[list[list[tuple[int, int]]]]): A list of lists, where each inner list contains the possible configurations of shaded cells for a specific room, based on the room's weight and the pre-shaded cells.
            - "drawnStones" (list[None | tuple[int, int] | list[tuple[int, int]]]): A list initialized with None values, which will later be used to keep track of the drawn stones for each room in the solution.
    """

    with open(inputFile, 'r') as file:
        rows, cols, rooms, layout, weights, initialState = _readPuzzleSections(file)
        state = [row[:] for row in initialState]

        # allRoomIndices: A list of lists, where each inner list contains the coordinates of the cells belonging to a specific room.
        allRoomIndices: list[list[tuple[int, int]]] = [[] for _ in range(rooms)]
        for r in range(rows):
            for c in range(cols):
                allRoomIndices[layout[r][c]].append((r, c))

        allRoomDomains: list[list[list[tuple[int, int]]]] = []
        allRoomBorders = []

        for currRoom in range(rooms):
            currRoomIndices = allRoomIndices[currRoom]

            if weights[currRoom] is not None:
                currRoomWeight = weights[currRoom][1] # type: ignore
                domain = gridUtils.connectedSubgrids(currRoomIndices, currRoomWeight)
            else:
                domain = gridUtils.connectedSubgrids(currRoomIndices)

            if domain is None:
                raise ValueError(f"Invalid room {currRoom}: cannot generate connected subgrids")
            allRoomDomains.append(domain)

            # collect any pre-shaded cells in this room as a set for efficient lookup
            initialStones = {(r, c) for (r, c) in currRoomIndices if initialState[r][c] == ' #'}

            # if there are pre-shaded cells, filter the domain to only subgrids that contain all of them
            if initialStones:
                reducedDomain = [
                    subdomain for subdomain in allRoomDomains[currRoom]
                    if initialStones.issubset(subdomain)  # O(k) check
                ]
                allRoomDomains[currRoom] = reducedDomain

        for room, roomIdx in enumerate(allRoomIndices):
            borders = gridUtils.borderGen(roomIdx, rows, cols)
            allRoomBorders.append(borders)

        # drawnStones: A list (the play grid) initialized with None values. FOR FUTURE USE
        drawnStones = [None] * rooms

    return {
        "rows": rows,
        "cols": cols,
        "weights": weights,
        "layout": layout,
        "rooms": rooms,
        "initialState": initialState,
        "state": state,
        "allRoomIndices": allRoomIndices,
        "allRoomBorders": allRoomBorders,
        "allRoomDomains": allRoomDomains,
        "drawnStones": drawnStones
    }
