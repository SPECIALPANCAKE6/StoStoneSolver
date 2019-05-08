import domainBuilder
import readPuzzle


def isStoSand(state):
    colCounter = [0 for i in range(readPuzzle.cols)]
    for r in range(readPuzzle.rows):
        for c in range(readPuzzle.cols):
            if state[r][c] == ' #':
                colCounter[c] += 1
    if all(count == readPuzzle.rows / 2 for count in colCounter):
        return True
    return False


def getBelow(stone):
    cellsBelow = [None for coords in stone]
    for idx, (r, c) in enumerate(stone):
        if r + 1 < readPuzzle.rows:
            cellsBelow[idx] = (r + 1, c)
    return cellsBelow


def canStoneDrop(roomNum, subgrid):
    if None not in subgrid:
        for idx, (r, c) in enumerate(subgrid):
            if readPuzzle.state[r][c] == -1 and (r, c) not in lastPlaced[roomNum]:
                return True
    return False


def dropDown(roomNum, stone):
    domainBuilder.unDraw(lastPlaced[roomNum])
    domainBuilder.drawStone(stone)


def isStoStone():
    belows = []
    emptyBelow = []
    for subgrid in readPuzzle.drawnStones:
        belows.append(getBelow(subgrid))
    for room in belows:
        emptyBelow.append(canStoneDrop(belows.index(room), room))
    while True in emptyBelow:
        for idx, below in enumerate(belows):
            if canStoneDrop(idx, below):
                dropDown(idx, below)
                lastPlaced[idx] = below
                belows[idx] = getBelow(below)
                emptyBelow[idx] = canStoneDrop(idx, belows[idx])
    if isStoSand(readPuzzle.state):
        print("Sto-Stone Solution found!")
        readPuzzle.printGrid(readPuzzle.state)
        return True
    else:
        for room, stone in enumerate(readPuzzle.drawnStones):
            domainBuilder.unDraw(lastPlaced[room])
            domainBuilder.drawStone(stone)
        print("Not a Sto-Stone Solution...")
        return False


def backtrack(roomNum):
    global solved, lastPlaced

    solved = False

    # if time.time() > finishTime:
    # return print("Unable to find solution.")

    if roomNum >= readPuzzle.rooms:
        lastPlaced = [subgrid for subgrid in readPuzzle.drawnStones]

        if isStoSand(readPuzzle.state):
            print("This is a Sto-Sand Solution:")
            readPuzzle.printGrid(readPuzzle.state)
            solved = isStoStone()
            #    maxDown[room] = min(canStoneDrop(subgrid))
            #    testDomains[room] = dropDown(maxDown[room], subgrid)
            # for domain in readPuzzle.usedSubgrids:
            #    domainBuilder.unDraw(domain)
            # for room, test in enumerate(testDomains):
            #    domainBuilder.drawStone(testDomains[room])
            # for i in range(readPuzzle.rooms):
            #    finalCheck[i] = min(canStoneDrop(testDomains[i]))
            #if finalCheck.count(finalCheck[0]) == len(finalCheck) and finalCheck[0] == 0 and ' #' not in readPuzzle.state[int(readPuzzle.rows / 2)-1]:
            #    solved = True
            #    return print("Solution found!")
            #else:
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
            readPuzzle.drawnStones[roomNum] = subgrid
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
            readPuzzle.drawnStones[roomNum] = subgrid
            backtrack(roomNum + 1)
            if not solved:
                domainBuilder.unDraw(subgrid)
            else:
                return
