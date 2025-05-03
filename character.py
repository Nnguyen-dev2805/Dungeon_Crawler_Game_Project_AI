import pygame
import constants
import weapon
import math
import numpy as np
from collections import deque
from enum import Enum, auto
from item import Item
import random
import heapq

class CharacterState(Enum):
    IDLE = auto()
    MOVING = auto()
    STUNNED = auto()
    ATTACKING = auto()
    DEAD = auto()

class Direction(Enum):
    NONE = auto()
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()

class Character:
    def __init__(self, x, y, health, mob_animations, char_type, boss, size):
        self.char_type = char_type
        self.boss = boss
        self.score = 0
        self.flip = False  # hướng nhân vật
        self.frame_index = 0
        self.action = 0  # 0: đứng yên, 1: di chuyển
        self.animation_list = mob_animations[char_type]
        self.update_time = pygame.time.get_ticks()  # thời gian cập nhật ảnh
        self.running = False
        self.health = health
        self.max_health = health
        self.alive = True
        self.hit = False
        self.last_hit = pygame.time.get_ticks()
        self.last_attack = pygame.time.get_ticks()
        self.last_path_update = pygame.time.get_ticks()
        self.stunned = False

        self.target_center = None 
        self.frames_left = 0
        self.direction = None 
        self.distance_moved = 0

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = pygame.Rect(
            0, 0, constants.TILE_SIZE * size, constants.TILE_SIZE * size
        )
        self.rect.center = (x, y)
        self.state = CharacterState.IDLE

    def move(self, dx, dy, obstacle_tiles, exit_tile=None):
        screen_scroll = [0, 0]

        level_complete = False

        self.running = False
        # xác định hướng di chuyển
        if dx != 0 or dy != 0:
            self.running = True

        # xác định hướng của nhân v
        if dx > 0:
            self.flip = False
        if dx < 0:
            self.flip = True

        # vận tốc theo đường chéo = vận tốc theo trục x * căn 2 / 2
        if dx != 0 and dy != 0:
            dx = dx * (math.sqrt(2) / 2)
            dy = dy * (math.sqrt(2) / 2)
        
        # kiểm tra xem có đụng độ với tường không
        self.rect.x += dx
        for obstacle in obstacle_tiles:
            if obstacle[1].colliderect(self.rect):
                if dx > 0:
                    self.rect.right = obstacle[1].left
                if dx < 0:
                    self.rect.left = obstacle[1].right
        
        self.rect.y += dy
        for obstacle in obstacle_tiles:
            if obstacle[1].colliderect(self.rect):
                if dy > 0:
                    self.rect.bottom = obstacle[1].top
                if dy < 0:
                    self.rect.top = obstacle[1].bottom

        # màn hình chỉ di chuyển với người chơi
        if self.char_type == 0:
            # kiểm tra xem có chạm vào cửa exit không
            if exit_tile[1].colliderect(self.rect):
                # kiểm tra xem người chơi có thực sự ở tâm ô exit chưa
                exit_dist = math.sqrt(
                    (
                        (self.rect.centerx - exit_tile[1].centerx) ** 2
                        + (self.rect.centery - exit_tile[1].centery) ** 2
                    )
                )
                if exit_dist < 20:
                    level_complete = True
            # di chuyển sang trái hoặc phải
            if self.rect.right > (constants.SCREEN_WIDTH - constants.SCROLL_THRESH):
                screen_scroll[0] = (
                    constants.SCREEN_WIDTH - constants.SCROLL_THRESH
                ) - self.rect.right
                self.rect.right = constants.SCREEN_WIDTH - constants.SCROLL_THRESH
            if self.rect.left < constants.SCROLL_THRESH:
                screen_scroll[0] = constants.SCROLL_THRESH - self.rect.left
                self.rect.left = constants.SCROLL_THRESH
            # di chuyển lên trên hoặc xuống
            if self.rect.bottom > (constants.SCREEN_HEIGHT - constants.SCROLL_THRESH):
                screen_scroll[1] = (
                    constants.SCREEN_HEIGHT - constants.SCROLL_THRESH
                ) - self.rect.bottom
                self.rect.bottom = constants.SCREEN_HEIGHT - constants.SCROLL_THRESH
            if self.rect.top < constants.SCROLL_THRESH:
                screen_scroll[1] = constants.SCROLL_THRESH - self.rect.top
                self.rect.top = constants.SCROLL_THRESH

        return screen_scroll, level_complete

    def handle_attack(self, player, fireball_image):
        fireball = None
        dist = math.sqrt(
            (self.rect.centerx - player.rect.centerx) ** 2 +
            (self.rect.centery - player.rect.centery) ** 2
        )

        if dist < constants.ATTACK_RANGE and not player.hit:
            player.health -= 10
            player.hit = True
            player.last_hit = pygame.time.get_ticks()

        fireball_cooldown = 700
        if self.boss and dist < 500:
            if (pygame.time.get_ticks() - self.last_attack) > fireball_cooldown:
                fireball = weapon.Fireball(
                    fireball_image,
                    self.rect.centerx,
                    self.rect.centery,
                    player.rect.centerx,
                    player.rect.centery,
                )
                self.last_attack = pygame.time.get_ticks()

        return fireball, dist

    def handle_movement(self, player, tile_grid, obstacle_tiles):
        ai_dx = 0
        ai_dy = 0

        enemy_tile_x = self.rect.centerx // constants.TILE_SIZE
        enemy_tile_y = self.rect.centery // constants.TILE_SIZE
        enemy_pos = (int(enemy_tile_x), int(enemy_tile_y))

        player_tile_x = player.rect.centerx // constants.TILE_SIZE
        player_tile_y = player.rect.centery // constants.TILE_SIZE
        player_pos = (int(player_tile_x), int(player_tile_y))

        if self.distance_moved >= constants.TILE_SIZE:
            self.direction = Direction.NONE
            self.distance_moved = 0

        current_time = pygame.time.get_ticks()
        if self.direction == Direction.NONE or current_time - self.last_path_update > 300:
            dx, dy = self.a_star(enemy_pos, player_pos, tile_grid, obstacle_tiles)
            self.last_path_update = current_time
            
            if dx == 0 and dy == 0:
                directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
                random_direction = random.choice(directions)
                next_step = (enemy_pos[0] + random_direction[0], enemy_pos[1] + random_direction[1])
            else:
                next_step = (enemy_pos[0] + dx, enemy_pos[1] + dy)

            obstacles = set(
                (int(obstacle[2] / constants.TILE_SIZE), int(obstacle[3] / constants.TILE_SIZE))
                for obstacle in obstacle_tiles
            )
            if next_step in obstacles:
                return 0, 0

            if next_step[0] > enemy_pos[0]:
                self.direction = Direction.RIGHT
            elif next_step[0] < enemy_pos[0]:
                self.direction = Direction.LEFT
            elif next_step[1] > enemy_pos[1]:
                self.direction = Direction.DOWN
            elif next_step[1] < enemy_pos[1]:
                self.direction = Direction.UP
            else:
                self.direction = Direction.NONE
            self.distance_moved = 0

        if self.direction != Direction.NONE:
            if self.direction == Direction.RIGHT:
                ai_dx = constants.ENEMY_SPEED
            elif self.direction == Direction.LEFT:
                ai_dx = -constants.ENEMY_SPEED
            elif self.direction == Direction.DOWN:
                ai_dy = constants.ENEMY_SPEED
            elif self.direction == Direction.UP:
                ai_dy = -constants.ENEMY_SPEED

            self.distance_moved += constants.ENEMY_SPEED

        return ai_dx, ai_dy
    
    def handle_stun(self):
        stun_cooldown = 100
        current_time = pygame.time.get_ticks()
        if self.hit:
            self.hit = False
            self.last_hit = current_time
            self.state = CharacterState.STUNNED
            self.running = False
            self.update_action(0)
            self.direction = Direction.NONE
            self.distance_moved = 0
        if self.state == CharacterState.STUNNED:
            if current_time - self.last_hit > stun_cooldown:
                self.state = CharacterState.IDLE
    
    def ai(self, player, tile_graph, tile_grid, obstacle_tiles, screen_scroll, fireball_image):
        self.rect.x += screen_scroll[0]
        self.rect.y += screen_scroll[1]
        self.handle_stun()

        if self.state == CharacterState.DEAD or self.state == CharacterState.STUNNED:
            return None

        fireball, dist = self.handle_attack(player, fireball_image)

        if self.state != CharacterState.STUNNED:
            ai_dx, ai_dy = self.handle_movement(player, tile_grid, obstacle_tiles)
            if ai_dx != 0 or ai_dy != 0:
                self.state = CharacterState.MOVING
                self.move(ai_dx, ai_dy, obstacle_tiles)
            else:
                self.state = CharacterState.IDLE

        return fireball

    def bfs(self, start, goal, tile_grid,obstacle_tiles):
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

    # def ai(self, player, tile_graph,tile_grid, obstacle_tiles, screen_scroll, fireball_image):

        stun_cooldown = 100

        ai_dx = 0
        ai_dy = 0

        fireball = None

        self.rect.x += screen_scroll[0]
        self.rect.y += screen_scroll[1]

        enemy_tile_x = self.rect.centerx // constants.TILE_SIZE
        enemy_tile_y = self.rect.centery // constants.TILE_SIZE
        enemy_pos = (int(enemy_tile_x), int(enemy_tile_y))

        player_tile_x = player.rect.centerx // constants.TILE_SIZE
        player_tile_y = player.rect.centery // constants.TILE_SIZE
        player_pos = (int(player_tile_x), int(player_tile_y))

        tile_center = (
            (enemy_tile_x * constants.TILE_SIZE + constants.TILE_SIZE / 2) + screen_scroll[0],
            (enemy_tile_y * constants.TILE_SIZE + constants.TILE_SIZE / 2) + screen_scroll[1]
        )


        if self.distance_moved >= constants.TILE_SIZE:
            self.direction = None
            self.distance_moved = 0

        if self.direction is None:
            dx, dy = self.bfs(enemy_pos, player_pos, tile_grid, obstacle_tiles)
            next_step = (enemy_pos[0] + dx, enemy_pos[1] + dy)

            obstacles = set(
                (int(obstacle[2] / constants.TILE_SIZE), int(obstacle[3] / constants.TILE_SIZE))
                for obstacle in obstacle_tiles
            )
            if next_step in obstacles:
                print(f"[AI] Ô tiếp theo {next_step} là tường, không di chuyển")
                return fireball

            if next_step[0] > enemy_pos[0]:
                self.direction = "right"
            elif next_step[0] < enemy_pos[0]:
                self.direction = "left"
            elif next_step[1] > enemy_pos[1]:
                self.direction = "down"
            elif next_step[1] < enemy_pos[1]:
                self.direction = "up"
            else:
                self.direction = None
            self.distance_moved = 0
            print(f"[AI] Hướng di chuyển: {self.direction}")

        if self.direction is not None:
            if self.direction == "right":
                ai_dx = constants.ENEMY_SPEED
            elif self.direction == "left":
                ai_dx = -constants.ENEMY_SPEED
            elif self.direction == "down":
                ai_dy = constants.ENEMY_SPEED
            elif self.direction == "up":
                ai_dy = -constants.ENEMY_SPEED

            self.distance_moved += constants.ENEMY_SPEED
            print(f"[AI] Đã di chuyển: {self.distance_moved}/{constants.TILE_SIZE} pixel")
        
        dist = math.sqrt(((self.rect.centerx - player.rect.centerx) ** 2) + ((self.rect.centery - player.rect.centery) ** 2))
        if self.alive:
            if not self.stunned:
                self.move(ai_dx, ai_dy, obstacle_tiles)

                # attck player
                if dist < constants.ATTACK_RANGE and player.hit == False:
                    player.health -= 10
                    player.hit = True
                    player.last_hit = pygame.time.get_ticks()

                # thời gian hồi chiêu quả cầu lửa
                fireball_cooldown = 700
                if self.boss:
                    if dist < 500:
                        if (
                            pygame.time.get_ticks() - self.last_attack
                        ) > fireball_cooldown:
                            fireball = weapon.Fireball(
                                fireball_image,
                                self.rect.centerx,
                                self.rect.centery,
                                player.rect.centerx,
                                player.rect.centery,
                            )
                            self.last_attack = pygame.time.get_ticks()
            # check if hit
            if self.hit == True:
                self.hit = False
                self.last_hit = pygame.time.get_ticks()
                self.stunned = True
                self.running = False
                self.update_action(0)

            if (pygame.time.get_ticks() - self.last_hit) > stun_cooldown:
                self.stunned = False
        return fireball

    # def update(self):
        # kiểm tra xem nhân vật còn sống không
        if self.health <= 0:
            self.health = 0
            self.alive = False

        # cập nhật thời gian nhận sát thương
        hit_cooldown = 1000
        if self.char_type == 0:
            if self.hit == True and (
                pygame.time.get_ticks() - self.last_hit > hit_cooldown
            ):
                self.hit = False

        # cập nhật hành động
        if self.running:
            self.update_action(1)
        else:
            self.update_action(0)

        aninmation_cooldown = 70  # thời gian cập nhật ảnh
        self.image = self.animation_list[self.action][self.frame_index]
        # kiểm tra thời gian cập nhật ảnh
        if pygame.time.get_ticks() - self.update_time > aninmation_cooldown:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        if self.frame_index >= len(self.animation_list[self.action]):
            self.frame_index = 0

    def update(self, item_group=None, coin_images=None, red_potion=None):
        if self.health <= 0 and self.alive:
            self.health = 0
            self.alive = False
            self.state = CharacterState.DEAD
            if self.char_type != 0 and item_group and coin_images and red_potion:
                self.drop_item(item_group, coin_images, red_potion)
        hit_cooldown = 1000
        if self.char_type == 0:
            if self.hit and (pygame.time.get_ticks() - self.last_hit > hit_cooldown):
                self.hit = False
        if self.running:
            self.update_action(1)
        else:
            self.update_action(0)
        aninmation_cooldown = 70
        self.image = self.animation_list[self.action][self.frame_index]
        if pygame.time.get_ticks() - self.update_time > aninmation_cooldown:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        if self.frame_index >= len(self.animation_list[self.action]):
            self.frame_index = 0

    def update_action(self, new_action):
        # kiểm tra hành động mới có khác với hành động cũ không
        if new_action != self.action:
            self.action = new_action
            # cập nhật lại frame index nếu đang dừng đột nhiên chạy
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def drop_item(self, item_group, coin_images, red_potion):
        item_type = random.choice([0, 1])
        if item_type == 0:
            item = Item(self.rect.centerx, self.rect.centery, 0, coin_images)
        else:
            item = Item(self.rect.centerx, self.rect.centery, 1, [red_potion])
        item_group.add(item)

    # def draw(self, screen):
    #     pygame.draw.rect(screen, (255, 0, 0), self.rect, 2)
    #     flipped_image = pygame.transform.flip(self.image, self.flip, False)
    #     if self.char_type == 0:
    #         screen.blit(
    #             self.image,
    #             (self.rect.x, self.rect.y - constants.SCALE * constants.OFFSET),
    #         )
    #     else:
    #         screen.blit(flipped_image, self.rect)
    #     if self.char_type != 0:
    #         enemy_tile_x = self.rect.centerx // constants.TILE_SIZE
    #         enemy_tile_y = self.rect.centery // constants.TILE_SIZE
    #         tile_center = (
    #             enemy_tile_x * constants.TILE_SIZE + constants.TILE_SIZE / 2,
    #             enemy_tile_y * constants.TILE_SIZE + constants.TILE_SIZE / 2
    #         )
    #         pygame.draw.circle(screen, (0, 255, 0), tile_center, 3)  
    #         pygame.draw.circle(screen, (255, 255, 0), self.rect.center, 3)
    #         # if self.target_center is not None:
    #         #     pygame.draw.circle(screen, (255, 0, 0), self.target_center, 3)  # Màu đỏ

    def draw(self, screen):
        if not self.alive:
            return

        if self.char_type != 0:
            health_bar_width = 40
            health_bar_height = 4
            health_ratio = self.health / self.max_health
            pygame.draw.rect(screen, (255, 0, 0), 
                            (self.rect.centerx - health_bar_width//2, 
                             self.rect.top - 10, 
                             health_bar_width, 
                             health_bar_height))
            pygame.draw.rect(screen, (0, 255, 0), 
                            (self.rect.centerx - health_bar_width//2, 
                             self.rect.top - 10, 
                             health_bar_width * health_ratio, 
                             health_bar_height))

        flipped_image = pygame.transform.flip(self.image, self.flip, False)
        if self.char_type == 0:
            screen.blit(
                self.image,
                (self.rect.x, self.rect.y - constants.SCALE * constants.OFFSET),
            )
        else:
            screen.blit(flipped_image, self.rect)

        if self.char_type != 0 and self.path:
            for i in range(len(self.path) - 1):
                start_pos = (
                    self.path[i][0] * constants.TILE_SIZE + constants.TILE_SIZE // 2,
                    self.path[i][1] * constants.TILE_SIZE + constants.TILE_SIZE // 2
                )
                end_pos = (
                    self.path[i + 1][0] * constants.TILE_SIZE + constants.TILE_SIZE // 2,
                    self.path[i + 1][1] * constants.TILE_SIZE + constants.TILE_SIZE // 2
                )
                pygame.draw.line(screen, (0, 0, 255), start_pos, end_pos, 1)
                pygame.draw.circle(screen, (0, 0, 255), start_pos, 1)

        if self.char_type != 0:
            enemy_tile_x = self.rect.centerx // constants.TILE_SIZE
            enemy_tile_y = self.rect.centery // constants.TILE_SIZE
            tile_center = (
                enemy_tile_x * constants.TILE_SIZE + constants.TILE_SIZE / 2,
                enemy_tile_y * constants.TILE_SIZE + constants.TILE_SIZE / 2
            )
            pygame.draw.circle(screen, (0, 255, 0), tile_center, 3)
            pygame.draw.circle(screen, (255, 255, 0), self.rect.center, 3)
            if self.state == CharacterState.STUNNED:
                pygame.draw.circle(screen, (255, 0, 0), 
                                (self.rect.centerx, self.rect.top - 15), 3)
    def can_attack(self):
        return pygame.time.get_ticks() - self.last_attack > self.attack_cooldown

    def update_state(self):
        if self.state == CharacterState.IDLE:
            self.update_action(0)
        elif self.state == CharacterState.MOVING:
            self.update_action(1)
        elif self.state == CharacterState.ATTACKING:
            self.update_action(2)

    def a_star(self, start, goal, tile_grid, obstacle_tiles):
        obstacles = set(
            (int(obstacle[2] / constants.TILE_SIZE), int(obstacle[3] / constants.TILE_SIZE))
            for obstacle in obstacle_tiles
        )

        open_set = [(0, start)]
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self.heuristic(start, goal)}
        visited = set()

        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

        while open_set:
            current_f, current = heapq.heappop(open_set)
            if current == goal:
                return self.reconstruct_path(came_from, current, start)
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
                    f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        self.path = []
        return 0, 0

    def heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def reconstruct_path(self, came_from, current, start):
        self.path = [current]
        while current in came_from:
            current = came_from[current]
            self.path.append(current)
        self.path.reverse()
        if len(self.path) > 1:
            next_step = self.path[1]
            dx = next_step[0] - start[0]
            dy = next_step[1] - start[1]
            return dx, dy
        return 0, 0
    
def BFS(graph,start,goal):
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

def getPath(pathdict,start,goal):
    if goal not in pathdict:
        return []
    currenttile = goal
    path = [pathdict]
    while currenttile != start:
        currenttile = pathdict[currenttile]
        path.append(currenttile)
    path.reverse()
    return path