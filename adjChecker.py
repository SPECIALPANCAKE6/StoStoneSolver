import connChecker
import Solver


def adjChecker(roomNum, currRoomWeight):
    """
    checks each cell in each rooms adjacents and whether they are shaded and in another or the same room
    :param roomNum:
    :param currRoomWeight:
    :return:
    """
    global rows, cols, puzzle, weights, layout, rooms, given, givenRooms, state
    global finishTime

    drawnWeight = 0
    genRoomWeight = -1
    currRoomSquareIndices = []

    for r in range(rows):
        for c in range(cols):
            if layout[r][c] == roomNum:
                currRoomSquareIndices.append((r, c))

    if currRoomWeight == 0:
        genRoomWeight = len(currRoomSquareIndices)

    for r in range(rows):
        for c in range(cols):
            if layout[r][c] == roomNum:
                if drawnWeight+1 <= currRoomWeight or drawnWeight+1 <= genRoomWeight:
                    currUp = r-1
                    currDown = r+1
                    currLeft = c-1
                    currRight = c+1
                    if r == 0 and currLeft < 0:
                        if state[currDown][c] != '#' or layout[currDown][c] == roomNum:
                            if state[r][currRight] != '#' or layout[r][currRight] == roomNum:
                                state[r][c] = '#'
                                drawnWeight += 1
                                if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
                                    if currRoomWeight > 1 and connChecker.connChecker(roomNum, currRoomSquareIndices):
                                        backtrack(roomNum + 1)
                                        break
                                    backtrack(roomNum + 1)
                                    break
                                continue
                    elif r == 0 and currRight >= cols:
                        if state[currDown][c] != '#' or layout[currDown][c] == roomNum:
                            if state[r][currLeft] != '#' or layout[r][currLeft] == roomNum:
                                state[r][c] = '#'
                                drawnWeight += 1
                                if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
                                    if currRoomWeight > 1 and connChecker.connChecker(roomNum, currRoomSquareIndices):
                                        backtrack(roomNum + 1)
                                        break
                                    backtrack(roomNum + 1)
                                    break
                                continue
                    elif currDown >= rows and currLeft < 0:
                        if state[currUp][c] != '#' or layout[currUp][c] == roomNum:
                            if state[r][currRight] != '#' or layout[r][currRight] == roomNum:
                                state[r][c] = '#'
                                drawnWeight += 1
                                if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
                                    if currRoomWeight > 1 and connChecker.connChecker(roomNum, currRoomSquareIndices):
                                        backtrack(roomNum + 1)
                                        break
                                    backtrack(roomNum + 1)
                                    break
                                continue

                    elif currDown >= rows and currRight >= cols:
                        if state[currUp][c] != '#' or layout[currUp][c] == roomNum:
                            if state[r][currLeft] != '#' or layout[r][currLeft] == roomNum:
                                state[r][c] = '#'
                                drawnWeight += 1
                                if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
                                    if currRoomWeight > 1 and connChecker.connChecker(roomNum, currRoomSquareIndices):
                                        backtrack(roomNum + 1)
                                        break
                                    backtrack(roomNum + 1)
                                    break
                                continue

                    elif r == 0 and currLeft >= 0 and currRight < cols:
                        if state[currDown][c] != '#' or layout[currDown][c] == roomNum:
                                if state[r][currLeft] != '#' or layout[r][currLeft] == roomNum:
                                    if state[r][currRight] != '#' or layout[r][currRight] == roomNum:
                                        state[r][c] = '#'
                                        drawnWeight += 1
                                        if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
                                            if currRoomWeight > 1 and connChecker.connChecker(roomNum, currRoomSquareIndices):
                                                backtrack(roomNum+1)
                                                break
                                            backtrack(roomNum + 1)
                                            break
                                        continue

                    elif currDown >= rows and currLeft >= 0 and currRight < cols:
                        if state[currUp][c] != '#' or layout[currUp][c] == roomNum:
                            if state[r][currLeft] != '#' or layout[r][currLeft] == roomNum:
                                if state[r][currRight] != '#' or layout[r][currRight] == roomNum:
                                        state[r][c] = '#'
                                        drawnWeight += 1
                                        if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
                                            if currRoomWeight > 1 and connChecker.connChecker(roomNum, currRoomSquareIndices):
                                                backtrack(roomNum+1)
                                                break
                                            backtrack(roomNum + 1)
                                            break
                                        continue

                    elif currDown < rows and currLeft < 0 and currRight < cols:
                        if state[currUp][c] != '#' or layout[currUp][c] == roomNum:
                            if state[currDown][c] != '#' or layout[currDown][c] == roomNum:
                                if state[r][currRight] != '#' or layout[r][currRight] == roomNum:
                                        state[r][c] = '#'
                                        drawnWeight += 1
                                        if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
                                            if currRoomWeight > 1 and connChecker.connChecker(roomNum, currRoomSquareIndices):
                                                backtrack(roomNum+1)
                                                break
                                            backtrack(roomNum + 1)
                                            break
                                        continue

                    elif currDown < rows and currLeft >= 0 and currRight >= cols:
                        if state[currUp][c] != '#' or layout[currUp][c] == roomNum:
                            if state[currDown][c] != '#' or layout[currDown][c] == roomNum:
                                if state[r][currLeft] != '#' or layout[r][currLeft] == roomNum:
                                        state[r][c] = '#'
                                        drawnWeight += 1
                                        if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
                                            if currRoomWeight > 1 and connChecker.connChecker(roomNum, currRoomSquareIndices):
                                                backtrack(roomNum+1)
                                                break
                                            backtrack(roomNum + 1)
                                            break
                                        continue

                    elif currDown < rows and currLeft >= 0 and currRight < cols:
                        if state[currUp][c] != '#' or layout[currUp][c] == roomNum:
                            if state[currDown][c] != '#' or layout[currDown][c] == roomNum:
                                if state[r][currLeft] != '#' or layout[r][currLeft] == roomNum:
                                    if state[r][currRight] != '#' or layout[r][currRight] == roomNum:
                                        state[r][c] = '#'
                                        drawnWeight += 1
                                        if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
                                            if currRoomWeight > 1 and connChecker.connChecker(roomNum, currRoomSquareIndices):
                                                backtrack(roomNum+1)
                                                break
                                            backtrack(roomNum + 1)
                                            break
                                        continue

            elif drawnWeight > 1 and (r, c) > currRoomSquareIndices[-1]:
                if connChecker.connChecker(roomNum, currRoomSquareIndices):
                    backtrack(roomNum + 1)
                    break
                else:
                    print("Room Num " + str(roomNum) + " might be broken...")
            elif drawnWeight == 1 and (r, c) > currRoomSquareIndices[-1]:
                backtrack(roomNum + 1)
                break
            elif (r, c) > currRoomSquareIndices[-1]:
                if drawnWeight < currRoomWeight or drawnWeight < genRoomWeight:
                    print("Room Num: " + str(roomNum) + " wasn't solved...")
                    break