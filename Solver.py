# import libs for measurement of time
import sys
import glob
import time
import copy
import queue as Q
import connChecker
import adjChecker
import domainGen


# globals for reading in the puzzle
global rows
global cols
global puzzle
global weights
global layout
global rooms
global given
global givenRooms
global finishTime

global state


def readPuzzle(inputFile):
    """
    readPuzzle function which reads the file input to find puzzle room layout, room weights, and pre-shaded cells
    :param inputFile:
    :return:
    """
    global rows, cols, puzzle, weights, layout, rooms, given
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
                    #weights[row][col] = -1
                    if row + 1 == rows and col + 1 == cols:
                        break
                    continue
                else:
                    #weights[row][col] = int(symbol)
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


#def connChecker(roomNum, currRoomIndices):
#    """
#    currently broken... would work if there are two pairs of connected vertices that aren't connected
#    :param roomNum:
#    :param currRoomIndices:
#    :return: True if shaded cells are all connected, false if disconnected
#    """
#    global rows, cols, puzzle, weights, layout, rooms, given, givenRooms, state
#    global finishTime
#
#    connected = False
#    visited = copy.deepcopy(currRoomIndices)
#    for i in range(len(visited)):
#        visited[i] = visited[i],  False
#    que = Q.Queue()
#
#    for (rR, rC) in currRoomIndices:
#        for i in range(len(visited)):
#            if (rR, rC) in visited[i]:
#                visited[i] = visited[i][0], True
#                que.put((rR, rC))
#        while not que.empty():
#            s = que.get()
#
#            if state[rR][rC] == '#':
#                currUp = rR - 1
#                currDown = rR + 1
#                currLeft = rC - 1
#                currRight = rC + 1
#                if (currUp, rC) in currRoomIndices and state[currUp][rC] == '#':
#                    connected = True
#                    continue
#                elif (currDown, rC) in currRoomIndices and state[currDown][rC] == '#':
#                    connected = True
#                    continue
#                elif (rR, currLeft) in currRoomIndices and state[rR][currLeft] == '#':
#                    connected = True
#                    continue
#                elif (rR, currRight) in currRoomIndices and state[rR][currRight] == '#':
#                    connected = True
#                    continue
#                else:
#                    print("Room Num " + str(roomNum) + " might be broken...")
#        return connected


#def adjChecker(roomNum, currRoomWeight):
#    """
#    checks each cell in each rooms adjacents and whether they are shaded and in another or the same room
#    :param roomNum:
#    :param currRoomWeight:
#    :return:
#    """
#    global rows, cols, puzzle, weights, layout, rooms, given, givenRooms, state
#    global finishTime
#
#    drawnWeight = 0
#    genRoomWeight = -1
#    currRoomIndices = []
#
#    for r in range(rows):
#        for c in range(cols):
#            if layout[r][c] == roomNum:
#                currRoomIndices.append((r, c))
#
#    if currRoomWeight == 0:
#        genRoomWeight = len(currRoomIndices)
#
#    for r in range(rows):
#        for c in range(cols):
#            if layout[r][c] == roomNum:
#                if drawnWeight+1 <= currRoomWeight or drawnWeight+1 <= genRoomWeight:
#                    currUp = r-1
#                    currDown = r+1
#                    currLeft = c-1
#                    currRight = c+1
#                    if r == 0 and currLeft < 0:
#                        if state[currDown][c] != '#' or layout[currDown][c] == roomNum:
#                            if state[r][currRight] != '#' or layout[r][currRight] == roomNum:
#                                state[r][c] = '#'
#                                drawnWeight += 1
#                                if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
#                                    if currRoomWeight > 1 and connChecker.connChecker(roomNum, currRoomIndices):
#                                        backtrack(roomNum + 1)
#                                        break
#                                    backtrack(roomNum + 1)
#                                    break
#                                continue
#                    elif r == 0 and currRight >= cols:
#                        if state[currDown][c] != '#' or layout[currDown][c] == roomNum:
#                            if state[r][currLeft] != '#' or layout[r][currLeft] == roomNum:
#                                state[r][c] = '#'
#                                drawnWeight += 1
#                                if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
#                                    if currRoomWeight > 1 and connChecker.connChecker(roomNum, currRoomIndices):
#                                        backtrack(roomNum + 1)
#                                        break
#                                    backtrack(roomNum + 1)
#                                    break
#                                continue
#                    elif currDown >= rows and currLeft < 0:
#                        if state[currUp][c] != '#' or layout[currUp][c] == roomNum:
#                            if state[r][currRight] != '#' or layout[r][currRight] == roomNum:
#                                state[r][c] = '#'
#                                drawnWeight += 1
#                                if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
#                                    if currRoomWeight > 1 and connChecker.connChecker(roomNum, currRoomIndices):
#                                        backtrack(roomNum + 1)
#                                        break
#                                    backtrack(roomNum + 1)
#                                    break
#                                continue
#
#                    elif currDown >= rows and currRight >= cols:
#                        if state[currUp][c] != '#' or layout[currUp][c] == roomNum:
#                            if state[r][currLeft] != '#' or layout[r][currLeft] == roomNum:
#                                state[r][c] = '#'
#                                drawnWeight += 1
#                                if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
#                                    if currRoomWeight > 1 and connChecker.connChecker(roomNum, currRoomIndices):
#                                        backtrack(roomNum + 1)
#                                        break
#                                    backtrack(roomNum + 1)
#                                    break
#                                continue
#
#                    elif r == 0 and currLeft >= 0 and currRight < cols:
#                        if state[currDown][c] != '#' or layout[currDown][c] == roomNum:
#                                if state[r][currLeft] != '#' or layout[r][currLeft] == roomNum:
#                                    if state[r][currRight] != '#' or layout[r][currRight] == roomNum:
#                                        state[r][c] = '#'
#                                        drawnWeight += 1
#                                        if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
#                                            if currRoomWeight > 1 and connChecker.connChecker(roomNum, currRoomIndices):
#                                                backtrack(roomNum+1)
#                                                break
#                                            backtrack(roomNum + 1)
#                                            break
#                                        continue
#
#                    elif currDown >= rows and currLeft >= 0 and currRight < cols:
#                        if state[currUp][c] != '#' or layout[currUp][c] == roomNum:
#                            if state[r][currLeft] != '#' or layout[r][currLeft] == roomNum:
#                                if state[r][currRight] != '#' or layout[r][currRight] == roomNum:
#                                        state[r][c] = '#'
#                                        drawnWeight += 1
#                                        if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
#                                            if currRoomWeight > 1 and connChecker.connChecker(roomNum, currRoomIndices):
#                                                backtrack(roomNum+1)
#                                                break
#                                            backtrack(roomNum + 1)
#                                            break
#                                        continue
#
#                    elif currDown < rows and currLeft < 0 and currRight < cols:
#                        if state[currUp][c] != '#' or layout[currUp][c] == roomNum:
#                            if state[currDown][c] != '#' or layout[currDown][c] == roomNum:
#                                if state[r][currRight] != '#' or layout[r][currRight] == roomNum:
#                                        state[r][c] = '#'
#                                        drawnWeight += 1
#                                        if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
#                                            if currRoomWeight > 1 and connChecker.connChecker(roomNum, currRoomIndices):
#                                                backtrack(roomNum+1)
#                                                break
#                                            backtrack(roomNum + 1)
#                                            break
#                                        continue
#
#                    elif currDown < rows and currLeft >= 0 and currRight >= cols:
#                        if state[currUp][c] != '#' or layout[currUp][c] == roomNum:
#                            if state[currDown][c] != '#' or layout[currDown][c] == roomNum:
#                                if state[r][currLeft] != '#' or layout[r][currLeft] == roomNum:
#                                        state[r][c] = '#'
#                                        drawnWeight += 1
#                                        if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
#                                            if currRoomWeight > 1 and connChecker.connChecker(roomNum, currRoomIndices):
#                                                backtrack(roomNum+1)
#                                                break
#                                            backtrack(roomNum + 1)
#                                            break
#                                        continue
#
#                    elif currDown < rows and currLeft >= 0 and currRight < cols:
#                        if state[currUp][c] != '#' or layout[currUp][c] == roomNum:
#                            if state[currDown][c] != '#' or layout[currDown][c] == roomNum:
#                                if state[r][currLeft] != '#' or layout[r][currLeft] == roomNum:
#                                    if state[r][currRight] != '#' or layout[r][currRight] == roomNum:
#                                        state[r][c] = '#'
#                                        drawnWeight += 1
#                                        if drawnWeight == currRoomWeight or drawnWeight == genRoomWeight:
#                                            if currRoomWeight > 1 and connChecker.connChecker(roomNum, currRoomIndices):
#                                                backtrack(roomNum+1)
#                                                break
#                                            backtrack(roomNum + 1)
#                                            break
#                                        continue
#
#            elif drawnWeight > 1 and (r, c) > currRoomIndices[-1]:
#                if connChecker.connChecker(roomNum, currRoomIndices):
#                    backtrack(roomNum + 1)
#                    break
#                else:
#                    print("Room Num " + str(roomNum) + " might be broken...")
#            elif drawnWeight == 1 and (r, c) > currRoomIndices[-1]:
#                backtrack(roomNum + 1)
#                break
#            elif (r, c) > currRoomIndices[-1]:
#                if drawnWeight < currRoomWeight or drawnWeight < genRoomWeight:
#                    print("Room Num: " + str(roomNum) + " wasn't solved...")
#                    break


def backtrack(roomNum):
    global rows, cols, puzzle, weights, layout, rooms, given, givenRooms, state
    global finishTime

    if time.time() > finishTime:
        return

    if roomNum == 0:
        state = copy.deepcopy(given)
        for i in list(weights.keys()):
            for r in range(rows):
                for c in range(cols):
                    if layout[r][c] == i and given[r][c] == '#' and i in list(weights.keys()):
                        givenRooms.update({i : weights[i]})
                        del weights[i]

    if roomNum in weights.keys():
        currRoomWeight = weights[roomNum][2]
        adjChecker.adjChecker(roomNum, currRoomWeight)

    elif roomNum in list(givenRooms.keys()):
        backtrack(roomNum+1)

    else:
        adjChecker(roomNum, 0)


if __name__ == "__main__":
    global finishTime
    totalSolved = 0
    totalUnsolved = 0
    fileNames = glob.glob("puzzles/*.txt")
    for fileName in fileNames:
        readPuzzle(fileName)
        print(fileName)
        print("Layout:")
        for line in layout:
            print(line)
            # cells marked by room number
        print("Weights:")
        for key in weights.keys():
            print(key, ':' , weights[key])
            # formatted room : (x, y, weight)
        print("Given:")
        for line in given:
            print(line)
            # given stones are #, -1 means empty
        givenRooms = {}
        startTime = time.time()
        finishTime = startTime + 10000000
        backtrack(0)
        endTime = time.time()
        print(endTime - startTime)
        print("")
