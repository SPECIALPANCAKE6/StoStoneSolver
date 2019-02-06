import connChecker
import domainGen
import readPuzzle
import backtrack
import gridUtils


def domainParser(roomNum, conflicts, inDomain):
    # place subgrid from domain
    for subgrid in inDomain:
        # print("Subgrid " + str(subgrid) + " needs to be placed.")
        for (r, c) in subgrid:
            print("place strone at " + str(subgrid))
            for i in range(len(conflicts)):
                (conR, conC) = conflicts[i][1]
                if conflicts[i][2] == (r, c) and readPuzzle.state[conR][conC] == '#':
                    inDomain.remove(subgrid)
                    domain = domainParser(roomNum, conflicts, inDomain)
                    return domain
    return inDomain


def drawStone(subgrid):
    for (r, c) in subgrid:
        readPuzzle.state[r][c] = '#'




def adjChecker(roomNum, currRoomWeight):
    """
    checks each cell in each rooms adjacents and whether they are shaded and in another or the same room
    :param roomNum:
    :param currRoomWeight:
    :return:
    """

    # TODO change this from cell based approach to room based approach to see if the full stone conflicts with any previously placed rooms.
    # TODO think of it in pairs of indices. (conflicting rm num, conflict indx, currRoomIndex) Make use of layout
    global rows, cols, weights, layout, rooms, given, givenRooms
    global finishTime

    drawnWeight = 0
    genRoomWeight = -1
    currRoomSquareIndices = []

    for r in range(readPuzzle.rows):
        for c in range(readPuzzle.cols):
            if readPuzzle.layout[r][c] == roomNum:
                currRoomSquareIndices.append((r, c))

    # domain = domainGen.domainGen(currRoomSquareIndices, currRoomWeight)

    # gen possible conflict locations and domains for room
    conflicts = gridUtils.conflictGen(currRoomSquareIndices)
    if currRoomWeight == 0:
        domain = gridUtils.connectedSubgrids(currRoomSquareIndices)
    else:
        domain = gridUtils.connectedSubgrids(currRoomSquareIndices, currRoomWeight)

    domainNew = domainParser(roomNum, conflicts, domain)
    for subgrid in domainNew:
        drawStone(subgrid)
        backtrack.backtrack(roomNum + 1)



    # if currRoomWeight == 0:
    #     genRoomWeight = len(currRoomSquareIndices)
    #
    # for r in range(readPuzzle.rows):
    #     for c in range(readPuzzle.cols):
    #         if readPuzzle.layout[r][c] == roomNum:
    #             if drawnWeight + 1 <= currRoomWeight or drawnWeight + 1 <= genRoomWeight:
    #                 currUp = r - 1
    #                 currDown = r + 1
    #                 currLeft = c - 1
    #                 currRight = c + 1
    #                 if r == 0 and currLeft < 0:
    #                     if readPuzzle.state[currDown][c] != '#' or readPuzzle.layout[currDown][c] == roomNum:
    #                         if readPuzzle.state[r][currRight] != '#' or readPuzzle.layout[r][currRight] == roomNum:
    #                             readPuzzle.state[r][c] = '#'
    #                             drawnWeight += 1
    #                             if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
    #                                 if currRoomWeight > 1 and connChecker.connChecker(roomNum, currRoomSquareIndices):
    #                                     backtrack.backtrack(roomNum + 1)
    #                                     break
    #                                 backtrack.backtrack(roomNum + 1)
    #                                 break
    #                             continue
    #                 elif r == 0 and currRight >= readPuzzle.cols:
    #                     if readPuzzle.state[currDown][c] != '#' or readPuzzle.layout[currDown][c] == roomNum:
    #                         if readPuzzle.state[r][currLeft] != '#' or readPuzzle.layout[r][currLeft] == roomNum:
    #                             readPuzzle.state[r][c] = '#'
    #                             drawnWeight += 1
    #                             if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
    #                                 if currRoomWeight > 1 and connChecker.connChecker(roomNum, currRoomSquareIndices):
    #                                     backtrack.backtrack(roomNum + 1)
    #                                     break
    #                                 backtrack.backtrack(roomNum + 1)
    #                                 break
    #                             continue
    #                 elif currDown >= readPuzzle.rows and currLeft < 0:
    #                     if readPuzzle.state[currUp][c] != '#' or readPuzzle.layout[currUp][c] == roomNum:
    #                         if readPuzzle.state[r][currRight] != '#' or readPuzzle.layout[r][currRight] == roomNum:
    #                             readPuzzle.state[r][c] = '#'
    #                             drawnWeight += 1
    #                             if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
    #                                 if currRoomWeight > 1 and connChecker.connChecker(roomNum, currRoomSquareIndices):
    #                                     backtrack.backtrack(roomNum + 1)
    #                                     break
    #                                 backtrack.backtrack(roomNum + 1)
    #                                 break
    #                             continue
    #
    #                 elif currDown >= readPuzzle.rows and currRight >= readPuzzle.cols:
    #                     if readPuzzle.state[currUp][c] != '#' or readPuzzle.layout[currUp][c] == roomNum:
    #                         if readPuzzle.state[r][currLeft] != '#' or readPuzzle.layout[r][currLeft] == roomNum:
    #                             readPuzzle.state[r][c] = '#'
    #                             drawnWeight += 1
    #                             if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
    #                                 if currRoomWeight > 1 and connChecker.connChecker(roomNum, currRoomSquareIndices):
    #                                     backtrack.backtrack(roomNum + 1)
    #                                     break
    #                                 backtrack.backtrack(roomNum + 1)
    #                                 break
    #                             continue
    #
    #                 elif r == 0 and currLeft >= 0 and currRight < readPuzzle.cols:
    #                     if readPuzzle.state[currDown][c] != '#' or readPuzzle.layout[currDown][c] == roomNum:
    #                         if readPuzzle.state[r][currLeft] != '#' or readPuzzle.layout[r][currLeft] == roomNum:
    #                             if readPuzzle.state[r][currRight] != '#' or readPuzzle.layout[r][currRight] == roomNum:
    #                                 readPuzzle.state[r][c] = '#'
    #                                 drawnWeight += 1
    #                                 if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
    #                                     if currRoomWeight > 1 and connChecker.connChecker(roomNum,
    #                                                                                       currRoomSquareIndices):
    #                                         backtrack.backtrack(roomNum + 1)
    #                                         break
    #                                     backtrack.backtrack(roomNum + 1)
    #                                     break
    #                                 continue
    #
    #                 elif currDown >= readPuzzle.rows and currLeft >= 0 and currRight < readPuzzle.cols:
    #                     if readPuzzle.state[currUp][c] != '#' or readPuzzle.layout[currUp][c] == roomNum:
    #                         if readPuzzle.state[r][currLeft] != '#' or readPuzzle.layout[r][currLeft] == roomNum:
    #                             if readPuzzle.state[r][currRight] != '#' or readPuzzle.layout[r][currRight] == roomNum:
    #                                 readPuzzle.state[r][c] = '#'
    #                                 drawnWeight += 1
    #                                 if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
    #                                     if currRoomWeight > 1 and connChecker.connChecker(roomNum,
    #                                                                                       currRoomSquareIndices):
    #                                         backtrack.backtrack(roomNum + 1)
    #                                         break
    #                                     backtrack.backtrack(roomNum + 1)
    #                                     break
    #                                 continue
    #
    #                 elif currDown < readPuzzle.rows and currLeft < 0 and currRight < readPuzzle.cols:
    #                     if readPuzzle.state[currUp][c] != '#' or readPuzzle.layout[currUp][c] == roomNum:
    #                         if readPuzzle.state[currDown][c] != '#' or readPuzzle.layout[currDown][c] == roomNum:
    #                             if readPuzzle.state[r][currRight] != '#' or readPuzzle.layout[r][currRight] == roomNum:
    #                                 readPuzzle.state[r][c] = '#'
    #                                 drawnWeight += 1
    #                                 if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
    #                                     if currRoomWeight > 1 and connChecker.connChecker(roomNum,
    #                                                                                       currRoomSquareIndices):
    #                                         backtrack.backtrack(roomNum + 1)
    #                                         break
    #                                     backtrack.backtrack(roomNum + 1)
    #                                     break
    #                                 continue
    #
    #                 elif currDown < readPuzzle.rows and currLeft >= 0 and currRight >= readPuzzle.cols:
    #                     if readPuzzle.state[currUp][c] != '#' or readPuzzle.layout[currUp][c] == roomNum:
    #                         if readPuzzle.state[currDown][c] != '#' or readPuzzle.layout[currDown][c] == roomNum:
    #                             if readPuzzle.state[r][currLeft] != '#' or readPuzzle.layout[r][currLeft] == roomNum:
    #                                 readPuzzle.state[r][c] = '#'
    #                                 drawnWeight += 1
    #                                 if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
    #                                     if currRoomWeight > 1 and connChecker.connChecker(roomNum,
    #                                                                                       currRoomSquareIndices):
    #                                         backtrack.backtrack(roomNum + 1)
    #                                         break
    #                                     backtrack.backtrack(roomNum + 1)
    #                                     break
    #                                 continue
    #
    #                 elif currDown < readPuzzle.rows and currLeft >= 0 and currRight < readPuzzle.cols:
    #                     if readPuzzle.state[currUp][c] != '#' or readPuzzle.layout[currUp][c] == roomNum:
    #                         if readPuzzle.state[currDown][c] != '#' or readPuzzle.layout[currDown][c] == roomNum:
    #                             if readPuzzle.state[r][currLeft] != '#' or readPuzzle.layout[r][currLeft] == roomNum:
    #                                 if readPuzzle.state[r][currRight] != '#' or readPuzzle.layout[r][
    #                                     currRight] == roomNum:
    #                                     readPuzzle.state[r][c] = '#'
    #                                     drawnWeight += 1
    #                                     if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
    #                                         if currRoomWeight > 1 and connChecker.connChecker(roomNum,
    #                                                                                           currRoomSquareIndices):
    #                                             backtrack.backtrack(roomNum + 1)
    #                                             break
    #                                         backtrack.backtrack(roomNum + 1)
    #                                         break
    #                                     continue
    #
    #
    #         elif drawnWeight > 1 and (r, c) > currRoomSquareIndices[-1]:
    #             if connChecker.connChecker(roomNum, currRoomSquareIndices):
    #                 backtrack.backtrack(roomNum + 1)
    #                 break
    #             else:
    #                 print("Room Num " + str(roomNum) + " might be broken...")
    #         elif drawnWeight == 1 and (r, c) > currRoomSquareIndices[-1]:
    #             backtrack.backtrack(roomNum + 1)
    #             break
    #         elif (r, c) > currRoomSquareIndices[-1]:
    #             if drawnWeight < currRoomWeight or drawnWeight < genRoomWeight:
    #                 print("Room Num: " + str(roomNum) + " wasn't solved...")
    #                 break
