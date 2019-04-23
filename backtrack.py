import time
import domainBuilder
import readPuzzle


def getBelow(subgrid):
    cellsBelow = [None for coords in subgrid]
    for idx, (r, c) in enumerate(subgrid):
        if r + 1 < readPuzzle.rows:
            cellsBelow[idx] = (r + 1, c)
    return cellsBelow


def checkBelow(subgrid):
    emptyBelow = [False for coords in subgrid]
    if None not in subgrid:
        for idx, (r, c) in enumerate(subgrid):
            if readPuzzle.state[r][c] == -1:
                emptyBelow[idx] = True
    return emptyBelow


def dropDown(roomNum, subgrid):
    domainBuilder.unDraw(lastPlaced[roomNum])
    domainBuilder.drawStone(subgrid)


# TODO: find below positions for each room and check if empty, if so move stone down. while loop that runs while theres at least one stone that can move down

def backtrack(roomNum):
    global rows, cols, puzzle, weights, layout, rooms, initialState, given, givenRooms, state, finishTime, solved, maxDown, lastPlaced

    solved = False

    # if time.time() > finishTime:
    # return print("Unable to find solution.")

    if roomNum >= readPuzzle.rooms:
        colCounter = [0 for i in range(readPuzzle.cols)]
        maxDown = [0] * readPuzzle.rooms
        finalCheck = [0] * readPuzzle.rooms
        lastPlaced = [subgrid for subgrid in readPuzzle.usedSubgrids]

        for r in range(readPuzzle.rows):
            for c in range(readPuzzle.cols):
                if readPuzzle.state[r][c] == ' #':
                    colCounter[c] += 1
        if colCounter.count(colCounter[0]) == len(colCounter) and colCounter[0] == (readPuzzle.rows / 2):
            print("This is a Sto-Sand Solution:")
            readPuzzle.printGrid(readPuzzle.state)
            belows = []
            emptyBelow = []
            for subgrid in readPuzzle.usedSubgrids:
                belows.append(getBelow(subgrid))
            for room in belows:
                emptyBelow.append(checkBelow(room))
            while (True in empty for empty in emptyBelow):
                for idx, empty in enumerate(emptyBelow):
                    if None not in belows[idx] and True in emptyBelow[idx]:
                        dropDown(idx, belows[idx])
                        lastPlaced[idx] = belows[idx]
                        belows[idx] = getBelow(belows[idx])
                        emptyBelow[idx] = checkBelow(belows[idx])
            if (True not in empty for empty in emptyBelow):
                solved = True
                return print("Solution found!")
            else:
                print("Sand worked but not Stone!")
                for room, subgrid in enumerate(lastPlaced):
                    domainBuilder.unDraw(lastPlaced[room])
                for room in readPuzzle.usedSubgrids:
                    domainBuilder.drawStone(room)

            #    maxDown[room] = min(checkBelow(subgrid))
            #    testDomains[room] = dropDown(maxDown[room], subgrid)
            # for domain in readPuzzle.usedSubgrids:
            #    domainBuilder.unDraw(domain)
            # for room, test in enumerate(testDomains):
            #    domainBuilder.drawStone(testDomains[room])
            # for i in range(readPuzzle.rooms):
            #    finalCheck[i] = min(checkBelow(testDomains[i]))
            # if finalCheck.count(finalCheck[0]) == len(finalCheck) and finalCheck[0] == 0 and ' #' not in readPuzzle.state[int(readPuzzle.rows / 2)-1]:
            #
            # else:
            #    print("Sand worked but not Stone!")
            #    for room, test in enumerate(testDomains):
            #        domainBuilder.unDraw(testDomains[room])
            #    for room in readPuzzle.usedSubgrids:
            #        domainBuilder.drawStone(room)
        return

    if readPuzzle.weights[roomNum] is not None:
        domain = domainBuilder.domainReduce(readPuzzle.allRoomBorders[roomNum], readPuzzle.allRoomDomains[roomNum])
        for subgrid in domain:
            domainBuilder.drawStone(subgrid)
            readPuzzle.usedSubgrids[roomNum] = subgrid
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
            readPuzzle.usedSubgrids[roomNum] = subgrid
            backtrack(roomNum + 1)
            if not solved:
                domainBuilder.unDraw(subgrid)
            else:
                return
