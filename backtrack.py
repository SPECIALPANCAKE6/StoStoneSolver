import time
import domainBuilder
import readPuzzle

def checkBelow(subgrid):
    emptyBelow = [0 for coords in subgrid]
    for idx, (r, c) in enumerate(subgrid):
        for i in range(readPuzzle.rows-r):
            if readPuzzle.state[r+i][c] == -1:
                emptyBelow[idx] += 1
    return emptyBelow

def dropDown(maxDown, subgrid):
    newSubgrid = []
    for (r, c) in subgrid:
        newSubgrid.append((r+maxDown, c))
    return newSubgrid


def backtrack(roomNum):
    global rows, cols, puzzle, weights, layout, rooms, initialState, given, givenRooms, state, finishTime, solved, maxDown

    solved = False

    # if time.time() > finishTime:
    # return print("Unable to find solution.")

    if roomNum >= readPuzzle.rooms:
        colCounter = [ 0 for i in range(readPuzzle.cols)]
        maxDown = [0] * readPuzzle.rooms
        finalCheck = [0] * readPuzzle.rooms
        testDomains = [None] * readPuzzle.rooms

        for r in range(readPuzzle.rows):
            for c in range(readPuzzle.cols):
                if readPuzzle.state[r][c] == ' #':
                    colCounter[c] += 1
        if colCounter.count(colCounter[0]) == len(colCounter) and colCounter[0] == (readPuzzle.rows / 2):
            print("This is a Sto-Sand Solution:")
            readPuzzle.printGrid(readPuzzle.state)
            for room, domain in enumerate(readPuzzle.usedDomains):
                maxDown[room] = min(checkBelow(domain))
                testDomains[room] = dropDown(maxDown[room], domain)
            for domain in readPuzzle.usedDomains:
                domainBuilder.unDraw(domain)
            for room, test in enumerate(testDomains):
                domainBuilder.drawStone(testDomains[room])
            for i in range(readPuzzle.rooms):
                finalCheck[i] = min(checkBelow(testDomains[i]))
            if finalCheck.count(finalCheck[0]) == len(finalCheck) and finalCheck[0] == 0 and ' #' not in readPuzzle.state[int(readPuzzle.rows / 2)-1]:
                solved = True
                return print("Solution found!")
            else:
                print("Sand worked but not Stone!")
                for room, test in enumerate(testDomains):
                    domainBuilder.unDraw(testDomains[room])
                for room in readPuzzle.usedDomains:
                    domainBuilder.drawStone(room)
        return

    if readPuzzle.weights[roomNum] is not None:
        domain = domainBuilder.domainReduce(readPuzzle.allRoomBorders[roomNum], readPuzzle.allRoomDomains[roomNum])
        for subgrid in domain:
            domainBuilder.drawStone(subgrid)
            readPuzzle.usedDomains[roomNum] = subgrid
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
            readPuzzle.usedDomains[roomNum] = subgrid
            backtrack(roomNum + 1)
            if not solved:
                domainBuilder.unDraw(subgrid)
            else:
                return
