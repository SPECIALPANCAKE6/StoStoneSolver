import copy

import domainBuilder
import gridUtils

def printGrid(name):
    return print('\n'.join(['\t'.join([str(cell) for cell in row]) for row in name]))

def readPuzzle(inputFile):
    """
    readPuzzle function which reads the file input to find puzzle room layout, room weights, and pre-shaded cells
    :param inputFile:
    :return:
    """
    global rows, cols, weights, layout, rooms, initialState, state, allRoomIndices, allRoomBorders, allRoomDomains, usedDomains
    with open(inputFile, 'r') as file:
        file.readline()
        file.readline()
        rows = int(file.readline())
        cols = int(file.readline())
        rooms = int(file.readline())

        layout = [cols * [""] for i in range(rows)]
        for row in range(rows):
            line = file.readline()
            for col, symbol in enumerate(line.split()):
                layout[row][col] = int(symbol)

        weights = [None] * rooms
        for row in range(rows):
            line = file.readline()
            for col, symbol in enumerate(line.split()):
                if symbol != ".":
                    weights[layout[row][col]] = ((row, col), int(symbol))

        initialState = [cols * [""] for i in range(rows)]
        state = [cols * [""] for i in range(rows)]
        for row in range(rows):
            line = file.readline()
            for col, symbol in enumerate(line.split()):
                if symbol == ".":
                    initialState[row][col] = -1
                    state[row][col] = -1
                else:
                    initialState[row][col] = ' #'
                    state[row][col] = ' #'


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
                currRoomWeight = weights[currRoom][1]
                domain = gridUtils.connectedSubgrids(allRoomIndices[currRoom], currRoomWeight)
                allRoomDomains.append(domain)
            else:
                domain = gridUtils.connectedSubgrids(allRoomIndices[currRoom])
                allRoomDomains.append(domain)

            initialStones = []
            reducedDomain = []
            for (r, c) in allRoomIndices[currRoom]:
                if initialState[r][c] == ' #':
                    initialStones.append((r, c))
            if initialStones:
                for subdomain in allRoomDomains[currRoom]:
                    domainHasGiven = all(coords in subdomain for coords in initialStones)
                    if domainHasGiven:
                        reducedDomain.append(subdomain)
                allRoomDomains[currRoom] = reducedDomain

        for room, roomIdx in enumerate(allRoomIndices):
            borders = gridUtils.borderGen(room, roomIdx)
            allRoomBorders.append(borders)

        usedDomains = [None] * rooms