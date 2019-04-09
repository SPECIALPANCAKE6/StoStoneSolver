import copy

import domainBuilder
import gridUtils


def readPuzzle(inputFile):
    """
    readPuzzle function which reads the file input to find puzzle room layout, room weights, and pre-shaded cells
    :param inputFile:
    :return:
    """
    global rows, cols, weights, layout, rooms, given, givenRooms, state, allRoomIndices, allRoomBorders, allRoomDomains
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

        #weights = {}
        #for row, line in enumerate(file):
        #    for col, symbol in enumerate(line.split()):
        #        if symbol == ".":
        #            if row + 1 == rows and col + 1 == cols:
        #                break
        #            continue
        #        else:
        #            weights.update({layout[row][col]: (row, col, int(symbol))})
        #            if row + 1 == rows and col + 1 == cols:
        #                break
        #    else:
        #        continue
        #    break

        #weights = {}
        #for row in range(rows):
        #    line = file.readline()
        #    for col, symbol in enumerate(line.split()):
        #        if symbol != ".":
        #            weights.update({layout[row][col]: (row, col, int(symbol))})

        weights = [None] * rooms
        for row in range(rows):
            line = file.readline()
            for col, symbol in enumerate(line.split()):
                if symbol != ".":
                    weights[layout[row][col]] = (row, col, int(symbol))

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

        # TODO: allow for any cell to possible be given at init, not just the full room
        givenRooms = {}
        for i in weights:
            for r in range(rows):
                for c in range(cols):
                    if layout[r][c] == i and given[r][c] == '#' \
                            and i in weights:
                        givenRooms.update({i : weights[i]})
                        del weights[i]

        # givenRooms should be replaced with initialState
        # TODO: initialState will be passed to the domain generator code
        initialState = [cols * [""] for i in range(rows)]
        for row in range(rows):
            line = file.readline()
            for col, symbol in enumerate(line.split()):
                if symbol == ".":
                    initialState[row][col] = -1
                else:
                    initialState[row][col] = "#"

        allRoomIndices = []
        allRoomDomains = []
        allRoomBorders = []

        for currRoom in range(rooms):
            currRoomSquareIndices = []
            for r in range(rows):
                for c in range(cols):
                    if layout[r][c] == currRoom:
                        currRoomSquareIndices.append((r, c))
            allRoomIndices.append(currRoomSquareIndices)

            if weights[currRoom] != None:
                currRoomWeight = weights[currRoom][2]
                domain = gridUtils.connectedSubgrids(allRoomIndices[currRoom], currRoomWeight)
                allRoomDomains.append(domain)
            else:
                domain = gridUtils.connectedSubgrids(allRoomIndices[currRoom])
                allRoomDomains.append(domain)

        for room, roomIdx in enumerate(allRoomIndices):
            borders = gridUtils.borderGen(room, roomIdx)
            allRoomBorders.append(borders)
