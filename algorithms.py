import constants
import math
import heapq
from collections import deque
from constants import Direction

def a_star(start, goal, tile_grid, obstacle_tiles,map_width, map_height,attack = True):
    if attack:
        obstacles = set(
            (int(obstacle[2] / constants.TILE_SIZE), int(obstacle[3] / constants.TILE_SIZE))
            for obstacle in obstacle_tiles
        )
    else:
        obstacles = obstacle_tiles

    print(f"KAKAKAKA: {obstacles}")
    open_set = [(0, start)]
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}
    visited = set()
    path = []

    directions = [
        (0, 1), (1, 0), (0, -1), (-1, 0), 
        # (-1, -1), (-1, 1), (1, -1), (1, 1)  
    ]

    while open_set:
        current_f, current = heapq.heappop(open_set)
        if current == goal:
            print("KKAKAKAKAKAKKA")
            return reconstruct_path(came_from, current, start)
        if current in visited:
            continue
        visited.add(current)
        for direction in directions:
            dx, dy = direction
            neighbor = (current[0] + dx, current[1] + dy)
            if (neighbor[0] < 0 or neighbor[0] >= map_width + 1 or
                neighbor[1] < 0 or neighbor[1] >= map_height + 1 or
                neighbor in obstacles):
                print(f"kakaka {neighbor}")
                continue

            # can_move_diagonally = True
            # if dx != 0 and dy != 0:  
            #     if dx == 1 and dy == 1:  # RIGHT_DOWN
            #         right_tile = (current[0] + 1, current[1])  # Ô bên phải của current
            #         below_tile = (current[0], current[1] + 1)  # Ô phía dưới của current
            #         if (right_tile[0] < map_width and right_tile in obstacles) or \
            #            (below_tile[1] < map_height and below_tile in obstacles):
            #             can_move_diagonally = False
            #     elif dx == -1 and dy == 1:  # LEFT_DOWN
            #         left_tile = (current[0] - 1, current[1])   # Ô bên trái của current
            #         below_tile = (current[0], current[1] + 1)  # Ô phía dưới của current
            #         if (left_tile[0] >= 0 and left_tile in obstacles) or \
            #            (below_tile[1] < map_height and below_tile in obstacles):
            #             can_move_diagonally = False
            #     elif dx == 1 and dy == -1:  # RIGHT_UP
            #         right_tile = (current[0] + 1, current[1])  # Ô bên phải của current
            #         above_tile = (current[0], current[1] - 1)  # Ô phía trên của current
            #         if (right_tile[0] < map_width and right_tile in obstacles) or \
            #            (above_tile[1] >= 0 and above_tile in obstacles):
            #             can_move_diagonally = False
            #     elif dx == -1 and dy == -1:  # LEFT_UP
            #         left_tile = (current[0] - 1, current[1])   # Ô bên trái của current
            #         above_tile = (current[0], current[1] - 1)  # Ô phía trên của current
            #         if (left_tile[0] >= 0 and left_tile in obstacles) or \
            #            (above_tile[1] >= 0 and above_tile in obstacles):
            #             can_move_diagonally = False

            # if not can_move_diagonally:
            #     continue

            # Chi phí di chuyển: 1 cho hướng chính, sqrt(2) cho hướng chéo
            # cost = 1 if direction in [(0, 1), (1, 0), (0, -1), (-1, 0)] else math.sqrt(2)
            cost = 1 if direction in [(0, 1), (1, 0), (0, -1), (-1, 0)] else 1.1
            tentative_g_score = g_score[current] + cost
            if tentative_g_score < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))
    print(f"DEBUG BLABLA {came_from}")
    return (0, 0), path


def heuristic(a, b):
    # return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def reconstruct_path(came_from, current, start):
    print(f"TOI O DAY {came_from}")
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

# def get_path_a_star(start, goal,tile_grid, obstacle_tiles,map_width, map_height):
#     (dx, dy),path = a_star(start, goal, tile_grid,obstacle_tiles,map_width,map_height)
#     print(f"DEBUG: Full path from A*: {path}")
#     if not path or len(path) < 2:
#         return start  
#     return path[1]  

# lấy danh sách hướng đi áp dụng cho việc tuần tra
def get_path_a_star(start, goal, tile_grid, obstacle_tiles, map_width, map_height):
    # obstacle_tiles ở đây là set chứa các vị trí là tường theo file CSV
    (dx, dy), path = a_star(start, goal, tile_grid, obstacle_tiles, map_width, map_height,False)
    print(f"DEBUG: Full path from A*: {path}")
    directions = []
    for i in range(len(path) - 1):
        current = path[i]
        next_pos = path[i + 1]
        dx = next_pos[0] - current[0]
        dy = next_pos[1] - current[1]
        if dx > 0 and dy == 0:
            directions.append(Direction.RIGHT)
        elif dx < 0 and dy == 0:
            directions.append(Direction.LEFT)
        elif dx == 0 and dy > 0:
            directions.append(Direction.DOWN)
        elif dx == 0 and dy < 0:
            directions.append(Direction.UP)
        elif dx < 0 and dy < 0:
            directions.append(Direction.LEFT_UP)
        elif dx < 0 and dy > 0:
            directions.append(Direction.LEFT_DOWN)
        elif dx > 0 and dy < 0:
            directions.append(Direction.RIGHT_UP)
        elif dx > 0 and dy > 0:
            directions.append(Direction.RIGHT_DOWN)
    return directions  # Ví dụ: [DOWN, DOWN]
# BFS

def bfs(start, goal, tile_grid, obstacle_tiles, map_width, map_height):
    obstacles = set(
        (int(obstacle[2] / constants.TILE_SIZE), int(obstacle[3] / constants.TILE_SIZE))
        for obstacle in obstacle_tiles
    )

    queue = deque([start])
    visited = {start: None}  # Dictionary để lưu cha của mỗi node
    parent = {start: None}   # Theo dõi đường đi

    directions = [
        (0, 1), (1, 0), (0, -1), (-1, 0)  # 4 hướng chính
    ]

    while queue:
        current = queue.popleft()
        if current == goal:
            break
        for dx, dy in directions:
            neighbor = (current[0] + dx, current[1] + dy)
            if (0 <= neighbor[0] < map_width and
                0 <= neighbor[1] < map_height and
                neighbor not in obstacles and
                neighbor not in visited):
                queue.append(neighbor)
                visited[neighbor] = current
                parent[neighbor] = current  # Lưu cha để tái tạo đường đi

    # Tái tạo đường đi và tính hướng di chuyển
    if goal not in parent:
        return (0, 0), []  # Không tìm thấy đường đi

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
        return (dx, dy), path
    return (0, 0), path

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

#Local search :  beam search

# def beam_search(start, goal, tile_grid, obstacle_tiles, map_width, map_height):
#     obstacles = set(
#         (int(obstacle[2] / constants.TILE_SIZE), int(obstacle[3] / constants.TILE_SIZE))
#         for obstacle in obstacle_tiles
#     )

#     # Khởi tạo beam với heap
#     Beam = [(heuristic(start, goal), start, [start])]  # (heuristic, current, path)
#     visited = set([start])
#     beam_width = 3  # Có thể điều chỉnh

#     directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # 4 hướng chính

#     while Beam:
#         # Tạo các node con
#         children = []
#         for h, current, actions in Beam:
#             h, current, actions = heapq.heappop(Beam)

#             if current == goal:
#                 if actions:
#                     next_step = actions[0]
#                     dx = next_step[0] - start[0]
#                     dy = next_step[1] - start[1]
#                     return (dx, dy), actions
#                 return (0, 0), []

#             visited.add(current)

#             for dx, dy in directions:
#                 neighbor = (current[0] + dx, current[1] + dy)
                
#                 # Kiểm tra biên và chướng ngại vật
#                 if (neighbor[0] < 0 or neighbor[0] >= map_width or
#                     neighbor[1] < 0 or neighbor[1] >= map_height or
#                     neighbor in obstacles or neighbor in visited):
#                     continue
#                 new_actions = actions + [neighbor]
#                 h_score = heuristic(neighbor, goal)
#                 children.append((h_score, neighbor, new_actions))

#         # Thêm các node con vào Beam, giữ kích thước không vượt quá beam_width
#         for child in children:
#             heapq.heappush(Beam, child)
#         # Giữ lại beam_width node tốt nhất
#         Beam = heapq.nsmallest(beam_width, Beam)

#     return (0, 0), []  # Không tìm thấy đường đi


def beam_search(start, goal, tile_grid, obstacle_tiles, map_width, map_height):
    # Tạo tập chướng ngại vật
    obstacles = set(
        (int(obstacle[2] / constants.TILE_SIZE), int(obstacle[3] / constants.TILE_SIZE))
        for obstacle in obstacle_tiles
    )

    # Kiểm tra trường hợp đặc biệt
    if start == goal:
        return (0, 0), [start]

    # Khởi tạo beam với cấp độ đầu tiên
    current_level = [(heuristic(start, goal), start, [start])]  # (heuristic, current, path)
    visited = set([start])  # Lưu các ô đã thăm
    beam_width = 3  # Có thể điều chỉnh
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # 4 hướng chính

    while current_level:
        # Tạo tất cả trạng thái con cho cấp độ hiện tại
        next_level = []
        for h, current, actions in current_level:
            if current == goal:
                if len(actions) > 1:
                    next_step = actions[1]
                    dx = next_step[0] - start[0]
                    dy = next_step[1] - start[1]
                    return (dx, dy), actions
                return (0, 0), []

            # Tạo các node con
            for dx, dy in directions:
                neighbor = (current[0] + dx, current[1] + dy)
                # Kiểm tra biên, chướng ngại vật, và visited
                if (neighbor[0] < 0 or neighbor[0] >= map_width or
                    neighbor[1] < 0 or neighbor[1] >= map_height or
                    neighbor in obstacles or
                    neighbor in visited):
                    continue

                new_actions = actions + [neighbor]
                h_score = heuristic(neighbor, goal)
                next_level.append((h_score, neighbor, new_actions))
                visited.add(neighbor)  # Đánh dấu ô đã thăm

        # Chọn beam_width trạng thái tốt nhất cho cấp độ tiếp theo
        next_level = heapq.nsmallest(beam_width, next_level, key=lambda x: x[0])
        current_level = next_level

    return (0, 0), []  # Không tìm thấy đường đi

def backtracking_search(start, goal, tile_grid, obstacle_tiles, map_width, map_height, max_depth=50):
    """
    Tìm đường đi từ start đến goal bằng thuật toán backtracking.
    Args:
        start: Tuple (x, y) - Vị trí bắt đầu.
        goal: Tuple (x, y) - Vị trí mục tiêu.
        tile_grid: Ma trận bản đồ.
        obstacle_tiles: Danh sách chướng ngại vật.
        map_width, map_height: Kích thước bản đồ.
        max_depth: Giới hạn độ sâu đệ quy để tránh tràn stack.
    Returns:
        Tuple ((dx, dy), path): Hướng di chuyển tiếp theo và đường đi.
    """
    obstacles = set(
        (int(obstacle[2] / constants.TILE_SIZE), int(obstacle[3] / constants.TILE_SIZE))
        for obstacle in obstacle_tiles
    )

    directions = [
        (0, 1), (1, 0), (0, -1), (-1, 0)  # 4 hướng chính
        # Có thể thêm hướng chéo nếu cần: (-1, -1), (-1, 1), (1, -1), (1, 1)
    ]

    visited = set()

    def is_valid_move(pos):
        x, y = pos
        return (
            0 <= x < map_width and
            0 <= y < map_height and
            pos not in obstacles and
            pos not in visited
        )

    def backtrack(current, path, depth):
        if depth > max_depth:
            return None
        if current == goal:
            return path

        visited.add(current)
        for dx, dy in directions:
            next_pos = (current[0] + dx, current[1] + dy)
            if is_valid_move(next_pos):
                result = backtrack(next_pos, path + [next_pos], depth + 1)
                if result is not None:
                    return result
        visited.remove(current)  # Quay lui: bỏ đánh dấu ô đã thăm
        return None

    # Gọi hàm backtrack
    path = backtrack(start, [start], 0)
    if path and len(path) > 1:
        next_step = path[1]
        dx = next_step[0] - start[0]
        dy = next_step[1] - start[1]
        return (dx, dy), path
    return (0, 0), []