import random
import itertools
import iterators
from collections import deque


def gridNeighbors(coord: tuple[int, int], rows = None, cols = None):
    """
        This function generates the neighboring coordinates of a given coordinate on the grid.
        The neighboring coordinates are defined as the coordinates that are adjacent to the given coordinate in the four cardinal directions (up, down, left, right)
        and are within the bounds of the grid if specified.

        Args:
            coord (tuple[int, int]): A tuple containing the coordinates (row, col) of a cell on in a room.
            rows (int | None): An optional parameter specifying the number of rows in the grid. If None, no upper bound is applied to the row index.
            cols (int | None): An optional parameter specifying the number of columns in the grid. If None, no upper bound is applied to the column index.

        Returns:
            list[tuple[int, int]]: A list of tuples, where each tuple contains the coordinates of a neighboring cell that is adjacent to the given coordinate
            and within the bounds of the grid if specified.
    """

    r = coord[0]
    c = coord[1]
    neighbors = []

    if r > 0: neighbors.append((r-1, c))
    if rows is None or r < rows-1: neighbors.append((r+1, c))
    if c > 0: neighbors.append((r, c-1))
    if cols is None or c < cols-1: neighbors.append((r, c+1))

    return neighbors


def borderGen(coords, rows: int, cols: int) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    """
        This function generates the border cells of a given set of coordinates.
        The border cells are defined as the cells that are adjacent to the given coordinates but not included in the room itself.

        Args:
            coords (list[tuple[int, int]]): A list of tuples, where each tuple contains the coordinates (row, col) of a cell in a room.
            rows (int): total number of rows in the puzzle grid (used to prevent neighbors outside bounds).
            cols (int): total number of columns in the puzzle grid.

        Returns:
            list[tuple[tuple[int, int], tuple[int, int]]]: A list of tuples, where each tuple contains the coordinates of a border cell and the adjacent coordinate from the original room that it borders.
    """

    # convert to set for O(1) membership tests, since we may check many neighbors
    coord_set = set(coords)
    borders = []
    for coord in coords:
        raw_neighbors = gridNeighbors(coord, rows, cols)
        # only keep those not in the room itself
        neighbors = [n for n in raw_neighbors if n not in coord_set]
        # record the outside cell along with the border cell it touches
        borders += (((r, c), coord) for (r, c) in neighbors)
    return borders


def gridBFS(coords: list[tuple[int, int]]) -> list[tuple[int, int]] | None:
    """
        This function performs a breadth-first search (BFS) on a given set of coordinates to find all connected cells.
        The BFS starts from the first coordinate in the list and explores all neighboring cells that are part of the room (i.e., cells that are in the input list of coordinates).
        The function returns a list of all connected cells in the room, or None if the input is empty.

        Args:
            coords (list[tuple[int, int]]): A list of tuples, where each tuple contains the coordinates (row, col) of a cell in a room.
                The BFS will be performed on this set of coordinates to find all connected cells.

        Returns:
            list[tuple[int, int]] | None: A list of tuples, where each tuple contains the coordinates of a cell that is connected to the starting coordinate through neighboring cells in the input list.
                If the input list is empty, None is returned.
    """

    if not coords:
        return None

    found = []
    todo = deque([coords[0]])
    coord_set = set(coords)  # allow O(1) membership tests

    while todo:
        current = todo.popleft()
        neighbors = gridNeighbors(current)
        # discover new neighbors that are part of the original set but not yet seen
        for neighbor in neighbors:
            if neighbor in coord_set and neighbor not in found and neighbor not in todo:
                todo.append(neighbor)
        found.append(current)

    return found


def isConnected(coords: list[tuple[int, int]]) -> bool:
    """
        This function checks if a given set of coordinates forms a connected region on the grid.
        A region is considered connected if there is a path between any two cells in the room that only passes through cells in the room.

        Args:
            coords (list[tuple[int, int]]): A list of tuples, where each tuple contains the coordinates (row, col) of a cell in the room.

        Returns:
            bool: True if the coordinates form a connected region, False otherwise.
    """

    found = gridBFS(coords)
    return found is not None and len(found) == len(coords)


def connectedSubgrids(coords: list[tuple[int, int]], numSquares: int | None = None) -> list[list[tuple[int, int]]] | None:
    """
        This function generates all connected subgrids of a given room.
        It can also generate connected subgrids with a specified number of squares to be filled.
        Note: This routine is not efficient. It runs in O(n 2^n)-time where n is the number of squares in the input.

        Args:
            coords (list[tuple[int, int]]): A list of tuples, where each tuple contains the coordinates (row, col) of a cell in a given room.
            numSquares (int | None): An optional parameter specifying the number of squares required to be filled in the connected subgrids to be generated.
                If None, all connected subgrids will be generated.

        Returns:
            list[list[tuple[int, int]]] | None: A list of lists, where each inner list contains the coordinates of the cells in a connected subgrid of the original room.
                If numSquares is specified and there are not enough squares to fill, None is returned.
    """

    # Handle bad inputs.
    if numSquares is not None and len(coords) < numSquares:
        return None
    if isConnected(coords) == False:
        return None

    # Number of squares in the grid.
    n = len(coords)

    # Initialize the output.
    subgrids = []

    # An iterable for all binary strings of length n (with numSquares 1s).
    # Each binary string will be used as an incidence vector for the subgrids.
    # For example, (1,1,0,1) would represent the inclusion of squares 0,1,3.
    if numSquares is None:
        binaries = itertools.product([0,1], repeat=n)
    else:
        binaries = iterators.stcombos(n-numSquares, numSquares)

    # Check each binary string incidence vector.
    for binary in binaries:
        # Create the subgrid described by the incidence vector.
        subgrid = [coord for i, coord in enumerate(coords) if binary[i] == 1]

        # Skip over the empty subgrid case (ie all zeros case).
        # Only occurs when numSquares is None (using itertools.product).
        if numSquares is None and len(subgrid) == 0:
            continue

        # If the subgrid is connected, then add it to the output list.
        if isConnected(subgrid):
            subgrids.append(subgrid)

    # Return the valid subgrids.
    return subgrids


def randomCoords(rows: int, cols: int, num: int) -> list[tuple[int, int]] | None:
    """
        This function generates a specified number of random coordinates within the bounds of a grid defined by the number of rows and columns.
        The function ensures that the generated coordinates are unique and do not exceed the total number of cells in the grid.

        Args:
            rows (int): The number of rows in the grid.
            cols (int): The number of columns in the grid.
            num (int): The number of random coordinates to generate.

        Returns:
            list[tuple[int, int]] | None: A list of tuples, where each tuple contains the coordinates (row, col) of a randomly generated cell within the grid.
                If the number of requested coordinates exceeds the total number of cells in the grid, None is returned.
    """

    if num > rows*cols:
        return None

    coords = []
    while len(coords) < num:
        r = random.randint(0, rows-1)
        c = random.randint(0, cols-1)
        coord = (r, c)
        if coord not in coords:
            coords.append(coord)

    return coords


if __name__ == "__main__":
    # Sample grid.
    grid = [(0,0), (0,1), (0,2), (1,0), (1,1), (1,2)]


    # Print the grid.
    print("Original grid squares")
    print(grid)

    # gen possible border rows/cols (supply explicit grid dimensions)
    maxr = max(r for r,c in grid) + 1
    maxc = max(c for r,c in grid) + 1
    borders = borderGen(grid, maxr, maxc)


    # Sample subgrids.
    subgrids = connectedSubgrids(grid)

    # Print each subgrid.
    print("\nConnected subgrids")
    for subgrid in subgrids:
        print(subgrid)

    # Sample subgrids.with specified number of squares.
    subgrids = connectedSubgrids(grid, 3)

    # Print each subgrid.
    print("\nConnected subgrids with a specified number of squares")
    for subgrid in subgrids:
        print(subgrid)
