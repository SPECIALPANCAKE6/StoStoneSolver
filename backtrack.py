import adjChecker
import readPuzzle

givenRooms = {}

def backtrack(roomNum):
    global rows, cols, puzzle, weights, layout, rooms, given, givenRooms, state
    #global finishTime

    #if time.time() > finishTime:
    #    return

    if roomNum == 0:
        #state = copy.deepcopy(readPuzzle.given)
        for i in list(readPuzzle.weights.keys()):
            for r in range(readPuzzle.rows):
                for c in range(readPuzzle.cols):
                    if readPuzzle.layout[r][c] == i and readPuzzle.given[r][c] == '#' \
                            and i in list(readPuzzle.weights.keys()):
                        givenRooms.update({i : readPuzzle.weights[i]})
                        del readPuzzle.weights[i]

    if roomNum in readPuzzle.weights.keys():
        currRoomWeight = readPuzzle.weights[roomNum][2]
        adjChecker.adjChecker(roomNum, currRoomWeight)

    elif roomNum in list(givenRooms.keys()):
        backtrack(roomNum+1)

    else:
        adjChecker.adjChecker(roomNum, 0)

