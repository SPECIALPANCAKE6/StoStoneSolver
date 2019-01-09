import copy

def readPuzzle(inputFile):
    """
    readPuzzle function which reads the file input to find puzzle room layout, room weights, and pre-shaded cells
    :param inputFile:
    :return:
    """
    global rows, cols, weights, layout, rooms, given, state
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
                    if row + 1 == rows and col + 1 == cols:
                        break
                    continue
                else:
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
        state = copy.deepcopy(given)
