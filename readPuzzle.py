import copy
import gridUtils


def readPuzzle(inputFile):
    """
    readPuzzle function which reads the file input to find puzzle room layout, room weights, and pre-shaded cells
    :param inputFile:
    :return:
    """
    global rows, cols, weights, layout, rooms, given, givenRooms, state, allRoomIndices, allRoomConflicts
    with open(inputFile, 'r') as file:
        file.readline()
        file.readline()
        rows = int(file.readline())
        cols = int(file.readline())
        rooms = int(file.readline())

        layout = [cols * [""] for i in range(rows)]
        for row, line in enumerate(file):
            for col, symbol in enumerate(line.split()):
                layout[row][col] = int(symbol)
                if row + 1 == rows and col + 1 == cols:
                    break
            else:
                continue
            break

        weights = {}
        for row, line in enumerate(file):
            for col, symbol in enumerate(line.split()):
                if symbol == ".":
                    if row + 1 == rows and col + 1 == cols:
                        break
                    continue
                else:
                    weights.update({layout[row][col]: (row, col, int(symbol))})
                    if row + 1 == rows and col + 1 == cols:
                        break
            else:
                continue
            break

        given = [cols * [""] for i in range(rows)]
        for row, line in enumerate(file):
            for col, symbol in enumerate(line.split()):
                if symbol == ".":
                    given[row][col] = -1
                    if row + 1 == rows and col + 1 == cols:
                        break
                    continue
                else:
                    given[row][col] = symbol
                    if row + 1 == rows and col + 1 == cols:
                        break
            else:
                continue
            break
        state = copy.deepcopy(given)

        givenRooms = {}
        for i in list(weights.keys()):
            for r in range(rows):
                for c in range(cols):
                    if layout[r][c] == i and given[r][c] == '#' \
                            and i in list(weights.keys()):
                        givenRooms.update({i : weights[i]})
                        del weights[i]

        allRoomIndices = []
        allRoomConflicts = []

        for currRoom in range(rooms):
            currRoomSquareIndices = []
            for r in range(rows):
                for c in range(cols):
                    if layout[r][c] == currRoom:
                        currRoomSquareIndices.append((r, c))
            allRoomIndices.append(currRoomSquareIndices)

        for room, roomIdx in enumerate(allRoomIndices):
            conflicts = gridUtils.conflictGen(room, roomIdx)
            allRoomConflicts.append(conflicts)
