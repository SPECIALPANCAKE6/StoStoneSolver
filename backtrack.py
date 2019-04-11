import time
import domainBuilder
import readPuzzle


def backtrack(roomNum):
    global rows, cols, puzzle, weights, layout, rooms, initialState, given, givenRooms, state, finishTime, solved

    solved = False

    # if time.time() > finishTime:
    # return print("Unable to find solution.")

    if roomNum >= readPuzzle.rooms:
        colCounter = []
        for c in range(readPuzzle.cols):
            colCounter.append(0)

        for r in range(readPuzzle.rows):
            for c in range(readPuzzle.cols):
                if readPuzzle.state[r][c] == ' #':
                    colCounter[c] += 1
        if colCounter.count(colCounter[0]) == len(colCounter) and colCounter[0] == readPuzzle.cols / 2:
            solved = True
            return print("Solution found!")
        return

    if readPuzzle.weights[roomNum] is not None:
        domain = domainBuilder.domainReduce(readPuzzle.allRoomBorders[roomNum], readPuzzle.allRoomDomains[roomNum])
        for subgrid in domain:
            domainBuilder.drawStone(subgrid)
            backtrack(roomNum + 1)
            if not solved:
                domainBuilder.unDraw(subgrid)
            else:
                return

    # elif given is None:
    #    # then reduce to only domains that include the given cells and test
    #    for subgrid in readPuzzle.allRoomDomains[roomNum]:
    #        for (r, c) in subgrid:
    #
    #            domain = domainBuilder.domainReduce(readPuzzle.allRoomBorders[roomNum], readPuzzle.allRoomDomains[roomNum])
    #    backtrack(roomNum + 1)

    else:
        domain = domainBuilder.domainReduce(readPuzzle.allRoomBorders[roomNum], readPuzzle.allRoomDomains[roomNum])

        for subgrid in domain:
            domainBuilder.drawStone(subgrid)
            backtrack(roomNum + 1)
            if not solved:
                domainBuilder.unDraw(subgrid)
            else:
                return
