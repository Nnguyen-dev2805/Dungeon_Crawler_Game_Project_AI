import constants
import math
import heapq
from collections import deque

def a_star(start, goal, tile_grid, obstacle_tiles):
    obstacles = set(
        (int(obstacle[2] / constants.TILE_SIZE), int(obstacle[3] / constants.TILE_SIZE))
        for obstacle in obstacle_tiles
    )

    open_set = [(0, start)]
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}
    visited = set()
    path = []

    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

    while open_set:
        current_f, current = heapq.heappop(open_set)
        if current == goal:
            return reconstruct_path(came_from, current, start)
        if current in visited:
            continue
        visited.add(current)
        for direction in directions:
            neighbor = (current[0] + direction[0], current[1] + direction[1])
            if (neighbor[0] < 0 or neighbor[1] < 0 or neighbor in obstacles):
                continue
            tentative_g_score = g_score[current] + 1
            if tentative_g_score < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))
    return (0, 0), path

def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def reconstruct_path(came_from, current, start):
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    if len(path) > 1:
        next_step = path[1]
        dx = next_step[0] - start[0]
        dy = next_step[1] - start[1]
        return (dx, dy), path
    return (0, 0), path

def bfs(start, goal, tile_grid, obstacle_tiles):
    obstacles = set(
        (int(obstacle[2] / constants.TILE_SIZE), int(obstacle[3] / constants.TILE_SIZE))
        for obstacle in obstacle_tiles
    )

    queue = deque([start])
    visited = set()
    visited.add(start)
    parent = {start: None}

    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

    while queue:
        current = queue.popleft()
        if current == goal:
            break
        for direction in directions:
            neighbor = (current[0] + direction[0], current[1] + direction[1])
            if (
                neighbor not in visited
                and neighbor not in obstacles
                and neighbor[0] >= 0
                and neighbor[1] >= 0
            ):
                queue.append(neighbor)
                visited.add(neighbor)
                parent[neighbor] = current
    if goal not in parent:
        return 0, 0

    path = []
    current = goal
    while current is not None:
        path.append(current)
        current = parent[current]
    path.reverse()
    if len(path) > 1:
        next_step = path[1]
        dx = next_step[0] - start[0]
        dy = next_step[1] - start[1]
        return dx, dy
    return 0, 0

def BFS(graph, start, goal):
    tosearch = deque([start])
    visited = {start: None}

    while tosearch:
        node = tosearch.popleft()
        if node == goal:
            break
        for neighbor in graph.neighbors(node):
            if neighbor not in visited:
                tosearch.append(neighbor)
                visited[neighbor] = node

    return visited

def getPath(pathdict, start, goal):
    if goal not in pathdict:
        return []
    currenttile = goal
    path = []
    while currenttile != start:
        path.append(currenttile)
        currenttile = pathdict[currenttile]
    path.append(start)
    path.reverse()
    return path