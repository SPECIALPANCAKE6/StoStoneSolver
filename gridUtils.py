import random
import itertools
import iterators
import readPuzzle


def borderGen(coords):
    borders = []
    for coord in coords:
        neighbors = [neighbor for neighbor in gridNeighbors(coord, readPuzzle.rows, readPuzzle.cols)
                     if neighbor not in coords]
        borders += (((r, c), coord) for (r, c) in neighbors)
    return borders

# connectedSubgrids
# input: coords is a list of (row, col) co-ordinates defining the individual squares of a connected grid region.
# output: subgrids is a list of lists containing each connected subgrid of the original grid region.
# Note: This routine is not efficient.  It runs in O(n 2^n)-time where n is the number of squares in the input.
def connectedSubgrids(coords, numSquares = None):
    # Handle bad inputs.
    if numSquares != None and len(coords) < numSquares:
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
    if numSquares == None:
        binaries = itertools.product([0,1], repeat=n)
    else:
        binaries = iterators.stcombos(n-numSquares, numSquares)

    # Check each binary string incidence vector.
    for binary in binaries:
        # Create the subgrid described by the incidence vector.
        subgrid = [coord for i, coord in enumerate(coords) if binary[i] == 1]

        # Skip over the empty subgrid case (ie all zeros case).
        if len(subgrid) == 0: continue

        # If the subgrid is connected, then add it to the output list.
        if isConnected(subgrid):
            subgrids.append(subgrid)

    # Return the valid subgrids.
    return subgrids


# gridNeighbors
# input:
# output:
def gridNeighbors(coord, rows = None, cols = None):
    r = coord[0]
    c = coord[1]
    neighbors = []

    if r > 0: neighbors.append((r-1, c))
    if rows == None or r < rows-1: neighbors.append((r+1, c))
    if c > 0: neighbors.append((r, c-1))
    if cols == None or c < cols-1: neighbors.append((r, c+1))

    return neighbors


# isConnected
# input:
# output:
def isConnected(coords):
    found = gridBFS(coords)
    return found != None and len(found) == len(coords)

# gridBFS
# input:
# output:
def gridBFS(coords):
    found = []
    if len(coords) == 0: return

    todo = [coords[0]]

    while len(todo) > 0:
        current = todo.pop(0)

        neighbors = gridNeighbors(current)

        discovered = [neighbor for neighbor in neighbors
            if neighbor in coords and neighbor not in found and neighbor not in todo]
        todo = todo + discovered

        found.append(current)

    return found


# randomCoords
# input:
# output:
# For testing purposes.
def randomCoords(rows, cols, num):
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

    # gen possible border cells/rooms
    borders = borderGen(grid)


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
