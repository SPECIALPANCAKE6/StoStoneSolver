import copy
import queue as Q

import readPuzzle


def connChecker(roomNum, currRoomIndices):
    """
    currently broken... would work if there are two pairs of connected vertices that aren't connected
    :param roomNum:
    :param currRoomIndices:
    :return: True if shaded cells are all connected, false if disconnected
    """

    # TODO change to room based approach. Determine which rooms connect to each other and at what indices. To be used with adjchecker for conflicts.

    global rows, cols, weights, layout, rooms, given, givenRooms, state
    global finishTime

    connected = False
    visited = copy.deepcopy(currRoomIndices)
    for i in range(len(visited)):
        visited[i] = visited[i],  False
    que = Q.Queue()

    for (rR, rC) in currRoomIndices:
        for i in range(len(visited)):
            if (rR, rC) in visited[i]:
                visited[i] = visited[i][0], True
                que.put((rR, rC))
        while not que.empty():
            s = que.get()

            if readPuzzle.state[rR][rC] == '#':
                currUp = rR - 1
                currDown = rR + 1
                currLeft = rC - 1
                currRight = rC + 1
                if (currUp, rC) in currRoomIndices and readPuzzle.state[currUp][rC] == '#':
                    connected = True
                    continue
                elif (currDown, rC) in currRoomIndices and readPuzzle.state[currDown][rC] == '#':
                    connected = True
                    continue
                elif (rR, currLeft) in currRoomIndices and readPuzzle.state[rR][currLeft] == '#':
                    connected = True
                    continue
                elif (rR, currRight) in currRoomIndices and readPuzzle.state[rR][currRight] == '#':
                    connected = True
                    continue
                else:
                    print("Room Num " + str(roomNum) + " might be broken...")
        return connected

    currRoomIndices = []

    for r in range(rows):
        for c in range(cols):
            if layout[r][c] == roomNum:
                currRoomIndices.append((r, c))