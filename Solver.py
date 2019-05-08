# import libs for measurement of time
import glob
import time
import os
import shutil

import readPuzzle
import backtrack


def outputPUZPRE(fileName):
    fileName = fileName.replace(".", "-solved.")
    fileName = fileName.replace("puzzles", "solutions")
    with open(fileName, "w+") as file:
        file.write("puzprv3\nstostone\n")
        file.write(str(readPuzzle.rows) + "\n")
        file.write(str(readPuzzle.cols) + "\n")
        file.write(str(readPuzzle.rooms) + "\n")

        for i in readPuzzle.layout:
            row = '\n'.join([' '.join([str(cell) for cell in i])])
            file.write("%s\n" % row)

        for r in range(readPuzzle.rows):
            row = ["."] * readPuzzle.cols
            for c in range(readPuzzle.cols):
                for idx, val in enumerate(readPuzzle.weights):
                    if val and (r, c) in val:
                        row[c] = (str(val[1]))
            row = '\n'.join([' '.join([str(cell) for cell in row])])
            file.write("%s\n" %row)

        for r in range(readPuzzle.rows):
            row = ["."] * readPuzzle.cols
            row = '\n'.join([' '.join([str(cell) for cell in row])])
            file.write("%s\n" % row)

        file.write("\ninfo:{\n \"metadata\": {\n  \"author\": \"Addison Allen's Solver\",\n }\n}")


fileNames = glob.glob("puzzles\\YP-002.txt")
currDir = os.getcwd()
try:
    shutil.rmtree("%s\\solutions" % currDir)
    os.mkdir("%s\\solutions" % currDir)
except OSError:
    os.mkdir("%s\\solutions" % currDir)

print("Initialization Time: " + str(time.time()))
for fileName in fileNames:
    readPuzzle.readPuzzle(fileName)
    print(fileName)
    print("Layout:")
    # cells marked by room number
    readPuzzle.printGrid(readPuzzle.layout)
    print("Weights:")
    # formatted room : (x, y), weight
    for room, val in enumerate(readPuzzle.weights):
        if val is not None:
            print(room, ':' , val[0], ',', val[1])
    print("Initial State:")
    # given stones are #, -1 means empty
    readPuzzle.printGrid(readPuzzle.initialState)
    startTime = time.time()
    print(fileName + " started at " + str(startTime))
    finishTime = startTime + 1000000
    backtrack.backtrack(0)
    endTime = time.time()
    elapsedTime = endTime - startTime
    print("Finish Time: " + str(endTime) + "\nElapsed Time: " + str(elapsedTime))
    print("")
    outputPUZPRE(fileName)

#def readPuzzle(inputFile):
#    """
#    readPuzzle function which reads the file input to find puzzle room layout, room weights, and pre-shaded cells
#    :param inputFile:
#    :return:
#    """
#    global rows, cols, weights, layout, rooms, given
#    with open(inputFile, 'r') as file:
#        file.readline()
#        file.readline()
#        rows = int(file.readline())
#        cols = int(file.readline())
#        rooms = int(file.readline())
#
#        layout = [cols * [""] for i in range(rows)]
#        for row, line in enumerate(file):
#            for col, symbol in enumerate(line.split()):
#                layout[row][col] = int(symbol)
#                if row + 1 == rows and col + 1 == cols:
#                    break
#            else:
#                continue
#            break
#
#        weights = {}
#        for row, line in enumerate(file):
#            for col, symbol in enumerate(line.split()):
#                if symbol == ".":
#                    if row + 1 == rows and col + 1 == cols:
#                        break
#                    continue
#                else:
#                    weights.update({layout[row][col]: (row, col, int(symbol))})
#                    if row + 1 == rows and col + 1 == cols:
#                        break
#            else:
#                continue
#            break
#
#        given = [cols * [""] for i in range(rows)]
#        for row, line in enumerate(file):
#            for col, symbol in enumerate(line.split()):
#                if symbol == ".":
#                    given[row][col] = -1
#                    if row + 1 == rows and col + 1 == cols:
#                        break
#                    continue
#                else:
#                    given[row][col] = symbol
#                    if row + 1 == rows and col + 1 == cols:
#                        break
#            else:
#                continue
#            break
#
#
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


#def domainBuilder(roomNum, currRoomWeight):
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
#
#
#def backtrack(roomNum):
#    global rows, cols, puzzle, weights, layout, rooms, given, givenRooms, state
#    global finishTime
#
#    if time.time() > finishTime:
#        return
#
#    if roomNum == 0:
#        state = copy.deepcopy(readPuzzle.given)
#        for i in list(readPuzzle.weights.keys()):
#            for r in range(readPuzzle.rows):
#                for c in range(readPuzzle.cols):
#                    if readPuzzle.layout[r][c] == i and readPuzzle.given[r][c] == '#' \
#                            and i in list(readPuzzle.weights.keys()):
#                        givenRooms.update({i : readPuzzle.weights[i]})
#                        del readPuzzle.weights[i]
#
#    if roomNum in readPuzzle.weights.keys():
#        currRoomWeight = readPuzzle.weights[roomNum][2]
#        domainBuilder.domainBuilder(roomNum, currRoomWeight)
#
#    elif roomNum in list(givenRooms.keys()):
#        backtrack(roomNum+1)
#
#    else:
#        domainBuilder(roomNum, 0)