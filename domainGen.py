import readPuzzle


def dfs(currRoomIndices, start = None, goal = None, visited = None):
    if start is None:
        start = currRoomIndices[0]

    if goal is None:
        goal = currRoomIndices[-1]

    if visited is None:
        visited = set()

    visited.add(start)
    for j in currRoomIndices:
        if j not in visited:
            dfs(currRoomIndices, j, goal, visited)

    return visited






def domainGen(currRoomIndices, currRoomWeight = None):
    #for each v ∈ Adj[u] do
    #process
    #edge(u, v) if desired
    #if state[v] = “undiscovered” then
    #p[v] = u
    #DFS(G, v)
    #state[u] = “processed”

    visited = []
    paths = []
   
    for (rR, rC) in currRoomIndices:
        if (rR, rC) not in visited:
            visited.append((rR,rC))
        else:
            continue
        if len(visited) == currRoomWeight:
            return visited
        for n in range(rR - 1, rR + 2):
            for m in range(rC - 1, rC + 2):
                if not (n == rR and m == rC) and n > -1 and m > -1 and n < readPuzzle.rows and m < readPuzzle.cols:
                    if (n, m) in currRoomIndices and (n, m) not in visited:
                        visited.append((n, m))

        paths = paths.append(visited)
        visited = []

                        #continue
   
    return print("Domain Gen")

    #dfs(currRoomIndices)
