import readPuzzle


def domainReduce(borders, domain):
    # place subgrid from domain

    reducedDomain = []

    if borders:
        for subgrid in domain:
            conflict = False
            for (r, c) in subgrid:
                for i in range(len(borders)):
                    (conR, conC) = borders[i][0]
                    if borders[i][1] == (r, c) and readPuzzle.state[conR][conC] == ' #':
                        conflict = True
                        break
                if conflict:
                    break
            if not conflict:
                reducedDomain.append(subgrid)
        return reducedDomain
    else:
        return domain


def drawStone(subgrid):
    for (r, c) in subgrid:
        readPuzzle.state[r][c] = ' #'


def unDraw(subgrid):
    for (r, c) in subgrid:
        readPuzzle.state[r][c] = -1


#def domainBuilder(roomNum, origDomain, borders, indices):
#    """
#    gens borders for current room, and then generates rooms domain based on borders
#    :param roomNum:
#    :param currRoomWeight:
#    :return: domain: Fully parsed domain for currRoom
#    """
#
#    global rows, cols, weights, layout, rooms, given, givenRooms
#    global finishTime
#
#    # currRoomSquareIndices = []
#    #
#    # for r in range(readPuzzle.rows):
#    #     for c in range(readPuzzle.cols):
#    #         if readPuzzle.layout[r][c] == roomNum:
#    #             currRoomSquareIndices.append((r, c))
#
#    # borders = gridUtils.borderGen(roomNum, currRoomSquareIndices) # gen possible border locations and domains for room
#    # if currRoomWeight == 0:
#    #     domain = gridUtils.connectedSubgrids(readPuzzle.allRoomIndices[roomNum])
#    # else:
#    #     domain = gridUtils.connectedSubgrids(readPuzzle.allRoomIndices[roomNum], currRoomWeight)
#
#    domain = domainReduce(borders, origDomain)
#    return domain
#
#    # if currRoomWeight == 0:
#    #     genRoomWeight = len(currRoomSquareIndices)
#    #
#    # for r in range(readPuzzle.rows):
#    #     for c in range(readPuzzle.cols):
#    #         if readPuzzle.layout[r][c] == roomNum:
#    #             if drawnWeight + 1 <= currRoomWeight or drawnWeight + 1 <= genRoomWeight:
#    #                 currUp = r - 1
#    #                 currDown = r + 1
#    #                 currLeft = c - 1
#    #                 currRight = c + 1
#    #                 if r == 0 and currLeft < 0:
#    #                     if readPuzzle.state[currDown][c] != '#' or readPuzzle.layout[currDown][c] == roomNum:
#    #                         if readPuzzle.state[r][currRight] != '#' or readPuzzle.layout[r][currRight] == roomNum:
#    #                             readPuzzle.state[r][c] = '#'
#    #                             drawnWeight += 1
#    #                             if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
#    #                                 if currRoomWeight > 1 and connChecker.connChecker(roomNum, currRoomSquareIndices):
#    #                                     backtrack.backtrack(roomNum + 1)
#    #                                     break
#    #                                 backtrack.backtrack(roomNum + 1)
#    #                                 break
#    #                             continue
#    #                 elif r == 0 and currRight >= readPuzzle.cols:
#    #                     if readPuzzle.state[currDown][c] != '#' or readPuzzle.layout[currDown][c] == roomNum:
#    #                         if readPuzzle.state[r][currLeft] != '#' or readPuzzle.layout[r][currLeft] == roomNum:
#    #                             readPuzzle.state[r][c] = '#'
#    #                             drawnWeight += 1
#    #                             if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
#    #                                 if currRoomWeight > 1 and connChecker.connChecker(roomNum, currRoomSquareIndices):
#    #                                     backtrack.backtrack(roomNum + 1)
#    #                                     break
#    #                                 backtrack.backtrack(roomNum + 1)
#    #                                 break
#    #                             continue
#    #                 elif currDown >= readPuzzle.rows and currLeft < 0:
#    #                     if readPuzzle.state[currUp][c] != '#' or readPuzzle.layout[currUp][c] == roomNum:
#    #                         if readPuzzle.state[r][currRight] != '#' or readPuzzle.layout[r][currRight] == roomNum:
#    #                             readPuzzle.state[r][c] = '#'
#    #                             drawnWeight += 1
#    #                             if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
#    #                                 if currRoomWeight > 1 and connChecker.connChecker(roomNum, currRoomSquareIndices):
#    #                                     backtrack.backtrack(roomNum + 1)
#    #                                     break
#    #                                 backtrack.backtrack(roomNum + 1)
#    #                                 break
#    #                             continue
#    #
#    #                 elif currDown >= readPuzzle.rows and currRight >= readPuzzle.cols:
#    #                     if readPuzzle.state[currUp][c] != '#' or readPuzzle.layout[currUp][c] == roomNum:
#    #                         if readPuzzle.state[r][currLeft] != '#' or readPuzzle.layout[r][currLeft] == roomNum:
#    #                             readPuzzle.state[r][c] = '#'
#    #                             drawnWeight += 1
#    #                             if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
#    #                                 if currRoomWeight > 1 and connChecker.connChecker(roomNum, currRoomSquareIndices):
#    #                                     backtrack.backtrack(roomNum + 1)
#    #                                     break
#    #                                 backtrack.backtrack(roomNum + 1)
#    #                                 break
#    #                             continue
#    #
#    #                 elif r == 0 and currLeft >= 0 and currRight < readPuzzle.cols:
#    #                     if readPuzzle.state[currDown][c] != '#' or readPuzzle.layout[currDown][c] == roomNum:
#    #                         if readPuzzle.state[r][currLeft] != '#' or readPuzzle.layout[r][currLeft] == roomNum:
#    #                             if readPuzzle.state[r][currRight] != '#' or readPuzzle.layout[r][currRight] == roomNum:
#    #                                 readPuzzle.state[r][c] = '#'
#    #                                 drawnWeight += 1
#    #                                 if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
#    #                                     if currRoomWeight > 1 and connChecker.connChecker(roomNum,
#    #                                                                                       currRoomSquareIndices):
#    #                                         backtrack.backtrack(roomNum + 1)
#    #                                         break
#    #                                     backtrack.backtrack(roomNum + 1)
#    #                                     break
#    #                                 continue
#    #
#    #                 elif currDown >= readPuzzle.rows and currLeft >= 0 and currRight < readPuzzle.cols:
#    #                     if readPuzzle.state[currUp][c] != '#' or readPuzzle.layout[currUp][c] == roomNum:
#    #                         if readPuzzle.state[r][currLeft] != '#' or readPuzzle.layout[r][currLeft] == roomNum:
#    #                             if readPuzzle.state[r][currRight] != '#' or readPuzzle.layout[r][currRight] == roomNum:
#    #                                 readPuzzle.state[r][c] = '#'
#    #                                 drawnWeight += 1
#    #                                 if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
#    #                                     if currRoomWeight > 1 and connChecker.connChecker(roomNum,
#    #                                                                                       currRoomSquareIndices):
#    #                                         backtrack.backtrack(roomNum + 1)
#    #                                         break
#    #                                     backtrack.backtrack(roomNum + 1)
#    #                                     break
#    #                                 continue
#    #
#    #                 elif currDown < readPuzzle.rows and currLeft < 0 and currRight < readPuzzle.cols:
#    #                     if readPuzzle.state[currUp][c] != '#' or readPuzzle.layout[currUp][c] == roomNum:
#    #                         if readPuzzle.state[currDown][c] != '#' or readPuzzle.layout[currDown][c] == roomNum:
#    #                             if readPuzzle.state[r][currRight] != '#' or readPuzzle.layout[r][currRight] == roomNum:
#    #                                 readPuzzle.state[r][c] = '#'
#    #                                 drawnWeight += 1
#    #                                 if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
#    #                                     if currRoomWeight > 1 and connChecker.connChecker(roomNum,
#    #                                                                                       currRoomSquareIndices):
#    #                                         backtrack.backtrack(roomNum + 1)
#    #                                         break
#    #                                     backtrack.backtrack(roomNum + 1)
#    #                                     break
#    #                                 continue
#    #
#    #                 elif currDown < readPuzzle.rows and currLeft >= 0 and currRight >= readPuzzle.cols:
#    #                     if readPuzzle.state[currUp][c] != '#' or readPuzzle.layout[currUp][c] == roomNum:
#    #                         if readPuzzle.state[currDown][c] != '#' or readPuzzle.layout[currDown][c] == roomNum:
#    #                             if readPuzzle.state[r][currLeft] != '#' or readPuzzle.layout[r][currLeft] == roomNum:
#    #                                 readPuzzle.state[r][c] = '#'
#    #                                 drawnWeight += 1
#    #                                 if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
#    #                                     if currRoomWeight > 1 and connChecker.connChecker(roomNum,
#    #                                                                                       currRoomSquareIndices):
#    #                                         backtrack.backtrack(roomNum + 1)
#    #                                         break
#    #                                     backtrack.backtrack(roomNum + 1)
#    #                                     break
#    #                                 continue
#    #
#    #                 elif currDown < readPuzzle.rows and currLeft >= 0 and currRight < readPuzzle.cols:
#    #                     if readPuzzle.state[currUp][c] != '#' or readPuzzle.layout[currUp][c] == roomNum:
#    #                         if readPuzzle.state[currDown][c] != '#' or readPuzzle.layout[currDown][c] == roomNum:
#    #                             if readPuzzle.state[r][currLeft] != '#' or readPuzzle.layout[r][currLeft] == roomNum:
#    #                                 if readPuzzle.state[r][currRight] != '#' or readPuzzle.layout[r][
#    #                                     currRight] == roomNum:
#    #                                     readPuzzle.state[r][c] = '#'
#    #                                     drawnWeight += 1
#    #                                     if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
#    #                                         if currRoomWeight > 1 and connChecker.connChecker(roomNum,
#    #                                                                                           currRoomSquareIndices):
#    #                                             backtrack.backtrack(roomNum + 1)
#    #                                             break
#    #                                         backtrack.backtrack(roomNum + 1)
#    #                                         break
#    #                                     continue
#    #
#    #
#    #         elif drawnWeight > 1 and (r, c) > currRoomSquareIndices[-1]:
#    #             if connChecker.connChecker(roomNum, currRoomSquareIndices):
#    #                 backtrack.backtrack(roomNum + 1)
#    #                 break
#    #             else:
#    #                 print("Room Num " + str(roomNum) + " might be broken...")
#    #         elif drawnWeight == 1 and (r, c) > currRoomSquareIndices[-1]:
#    #             backtrack.backtrack(roomNum + 1)
#    #             break
#    #         elif (r, c) > currRoomSquareIndices[-1]:
#    #             if drawnWeight < currRoomWeight or drawnWeight < genRoomWeight:
#    #                 print("Room Num: " + str(roomNum) + " wasn't solved...")
#    #                 break
