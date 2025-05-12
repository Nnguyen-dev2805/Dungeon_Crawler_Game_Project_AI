import pygame
import constants
import weapon
import math
import numpy as np
import random
import heapq
from collections import deque

from collections import deque
from enum import Enum, auto
from item import Item
from algorithms import a_star, bfs, beam_search


class CharacterState(Enum):
    IDLE = auto()
    MOVING = auto()
    STUNNED = auto()
    ATTACKING = auto()
    DEAD = auto()
    FLEEING = auto()

class Direction(Enum):
    NONE = auto()
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    LEFT_UP = auto()
    LEFT_DOWN = auto()
    RIGHT_UP = auto()
    RIGHT_DOWN = auto()

class Enemy:
    def __init__(self, x, y, health, mob_animations, char_type, boss, size):
        self.char_type = char_type
        self.boss = boss
        self.flip = False
        self.frame_index = 0
        self.action = 0
        self.animation_list = mob_animations[char_type]
        self.update_time = pygame.time.get_ticks()
        self.running = False
        self.health = health
        self.max_health = health
        self.alive = True
        self.hit = False
        self.last_hit = pygame.time.get_ticks()
        self.last_attack = pygame.time.get_ticks()
        self.last_path_update = pygame.time.get_ticks()
        self.path = []

        self.target_center = None 
        self.frames_left = 0
        self.direction = Direction.NONE
        self.step_count = 0

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = pygame.Rect(
            0, 0, constants.TILE_SIZE * size, constants.TILE_SIZE * size
        )
        self.rect.center = (x, y)
        self.state = CharacterState.IDLE

        self.diagonal_steps = 16
        self.straight_steps = 12
        self.step_size = 4.0  
        self.remaining_distance = constants.TILE_SIZE * math.sqrt(2) - (self.diagonal_steps * self.step_size)
        self.diagonal_dx = 2 * math.sqrt(2)  
        self.diagonal_dy = 2 * math.sqrt(2)   
        self.final_dx = self.remaining_distance / math.sqrt(2)  
        self.final_dy = self.remaining_distance / math.sqrt(2)  
        self.straight_dx = self.step_size  
        self.straight_dy = self.step_size 
        self.is_fleeing = False

    def move(self, dx, dy, obstacle_tiles):
        self.running = False
        if dx != 0 or dy != 0:
            self.running = True

        if dx > 0:
            self.flip = False
        if dx < 0:
            self.flip = True

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

    def handle_attack(self, player, fireball_image):
        fireball = None
        dist = math.sqrt(
            (self.rect.centerx - player.rect.centerx) ** 2 +
            (self.rect.centery - player.rect.centery) ** 2
        )

        if dist < constants.ATTACK_RANGE and not player.hit:
            player.health -= 0
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

    def handle_movement(self, player, tile_grid, obstacle_tiles,map_width, map_height):
        ai_dx = 0
        ai_dy = 0
        # print(map_height," ",map_width)
        enemy_tile_x = self.rect.centerx // constants.TILE_SIZE
        enemy_tile_y = self.rect.centery // constants.TILE_SIZE
        enemy_pos = (int(enemy_tile_x), int(enemy_tile_y))
        # print(f"Pos: {enemy_pos}, Path: {self.path}")

        player_tile_x = player.rect.centerx // constants.TILE_SIZE
        player_tile_y = player.rect.centery // constants.TILE_SIZE
        player_pos = (int(player_tile_x), int(player_tile_y))

        if self.direction != Direction.NONE:
            if self.direction in [Direction.LEFT_UP, Direction.LEFT_DOWN, Direction.RIGHT_UP, Direction.RIGHT_DOWN]:
                if self.step_count >= self.diagonal_steps:
                    if self.direction == Direction.LEFT_UP:
                        ai_dx = -self.final_dx
                        ai_dy = -self.final_dy
                    elif self.direction == Direction.LEFT_DOWN:
                        ai_dx = -self.final_dx
                        ai_dy = self.final_dy
                    elif self.direction == Direction.RIGHT_UP:
                        ai_dx = self.final_dx
                        ai_dy = -self.final_dy
                    elif self.direction == Direction.RIGHT_DOWN:
                        ai_dx = self.final_dx
                        ai_dy = self.final_dy
                    self.step_count = 0  
                    self.direction = Direction.NONE
                else:
                    if self.direction == Direction.LEFT_UP:
                        ai_dx = -self.diagonal_dx
                        ai_dy = -self.diagonal_dy
                    elif self.direction == Direction.LEFT_DOWN:
                        ai_dx = -self.diagonal_dx
                        ai_dy = self.diagonal_dy
                    elif self.direction == Direction.RIGHT_UP:
                        ai_dx = self.diagonal_dx
                        ai_dy = -self.diagonal_dy
                    elif self.direction == Direction.RIGHT_DOWN:
                        ai_dx = self.diagonal_dx
                        ai_dy = self.diagonal_dy
                    self.step_count += 1
            else:
                if self.step_count < self.straight_steps:
                    if self.direction == Direction.RIGHT:
                        ai_dx = self.straight_dx
                        ai_dy = 0
                    elif self.direction == Direction.LEFT:
                        ai_dx = -self.straight_dx
                        ai_dy = 0
                    elif self.direction == Direction.DOWN:
                        ai_dx = 0
                        ai_dy = self.straight_dy
                    elif self.direction == Direction.UP:
                        ai_dx = 0
                        ai_dy = -self.straight_dy
                    self.step_count += 1
                else:
                    self.step_count = 0
                    self.direction = Direction.NONE

        if self.direction == Direction.NONE:
            # if self.is_fleeing and self.path and enemy_pos == self.path[-1]:
            #     self.direction = Direction.NONE
            #     self.path = deque()
            #     self.is_fleeing = False
            #     self.state = CharacterState.IDLE
            #     print(f"Enemy reached safe position: {enemy_pos}, standing still")
            #     return 0, 0
            if not self.path or (self.path and (enemy_pos[0], enemy_pos[1]) == self.path[-1]):
                # (dx, dy), self.path = a_star(enemy_pos, player_pos, tile_grid, obstacle_tiles, map_width, map_height)
                # (dx, dy), self.path = beam_search(enemy_pos, player_pos, tile_grid, obstacle_tiles, map_width, map_height)
                # (dx, dy) = bfs(enemy_pos, player_pos, tile_grid, obstacle_tiles, map_width, map_height)
                # Kiểm tra máu để quyết định đuổi theo hoặc chạy trốn
                health_threshold = 0.9 * self.max_health  # 30% máu
                if self.health <= health_threshold:
                    print("Enemy is attempting to flee")
                    # Chạy trốn: Tìm điểm an toàn
                    obstacles = set(
                    (int(obstacle[2] / constants.TILE_SIZE), int(obstacle[3] / constants.TILE_SIZE))
                    for obstacle in obstacle_tiles
                    ) 
                    safe_pos = self.find_safe_position(player_pos, tile_grid,obstacles, map_width, map_height,obstacle_tiles)
                    print(f"Player position: {player_pos}")
                    print(f"Safe position: {safe_pos}")
                    if safe_pos:
                        # print(f"Fleeing to safe_pos: {safe_pos}")
                        (dx, dy), self.path = a_star(enemy_pos, safe_pos, tile_grid, obstacle_tiles, map_width, map_height)
                        self.is_fleeing = True
                    else:
                        # print("No safe position, moving randomly")
                        dx, dy, self.path = 0, 0, []  # Không tìm được điểm an toàn
                        self.is_fleeing = False
                else:
                    # Đuổi theo người chơi
                    self.is_fleeing = False
                    # (dx, dy), self.path = a_star(enemy_pos, player_pos, tile_grid, obstacle_tiles, map_width, map_height)
                    (dx, dy), self.path = beam_search(enemy_pos, player_pos, tile_grid, obstacle_tiles, map_width, map_height)
                if not self.path:  
                    # print("No path found, moving randomly")
                    directions = [
                        (0, 1), (1, 0), (0, -1), (-1, 0),
                        (-1, -1), (-1, 1), (1, -1), (1, 1)
                    ]
                    random_direction = random.choice(directions)
                    next_step = (enemy_pos[0] + random_direction[0], enemy_pos[1] + random_direction[1])
                    dx, dy = random_direction
                else:
                    self.path.pop(0)
                    next_step = self.path[0] if self.path else enemy_pos
                    dx = next_step[0] - enemy_pos[0]
                    dy = next_step[1] - enemy_pos[1]

            else:
                self.path.pop(0)
                next_step = self.path[0] if self.path else enemy_pos
                dx = next_step[0] - enemy_pos[0]
                dy = next_step[1] - enemy_pos[1]
                # print(f"Path dx: {dx}, dy: {dy}, next_step: {next_step}")

            obstacles = set(
                (int(obstacle[2] / constants.TILE_SIZE), int(obstacle[3] / constants.TILE_SIZE))
                for obstacle in obstacle_tiles
            )
            if (next_step[0], next_step[1]) in obstacles or next_step[0] < 0 or next_step[0] >= map_width or next_step[1] < 0 or next_step[1] >= map_height:
                self.direction = Direction.NONE
                self.path = []  
                return 0, 0

            if dx > 0 and dy == 0:
                self.direction = Direction.RIGHT
                self.step_count = 0
            elif dx < 0 and dy == 0:
                self.direction = Direction.LEFT
                self.step_count = 0
            elif dx == 0 and dy > 0:
                self.direction = Direction.DOWN
                self.step_count = 0
            elif dx == 0 and dy < 0:
                self.direction = Direction.UP
                self.step_count = 0
            elif dx < 0 and dy < 0:
                self.direction = Direction.LEFT_UP
                self.step_count = 0
            elif dx < 0 and dy > 0:
                self.direction = Direction.LEFT_DOWN
                self.step_count = 0
            elif dx > 0 and dy < 0:
                self.direction = Direction.RIGHT_UP
                self.step_count = 0
            elif dx > 0 and dy > 0:
                self.direction = Direction.RIGHT_DOWN
                self.step_count = 0
            else:
                self.direction = Direction.NONE

            # print(f"Assigned direction: {self.direction}, step_count: {self.step_count}")
        
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
    
    def ai(self, player, tile_graph, tile_grid, obstacle_tiles, screen_scroll, fireball_image, map_width, map_height):
        self.rect.x += screen_scroll[0]
        self.rect.y += screen_scroll[1]
        self.handle_stun()

        if self.state == CharacterState.DEAD or self.state == CharacterState.STUNNED:
            return None

        fireball, dist = self.handle_attack(player, fireball_image)

        if self.state != CharacterState.STUNNED:
            ai_dx, ai_dy = self.handle_movement(player, tile_grid, obstacle_tiles, map_width, map_height)
            # ai_dx, ai_dy = self.handle_movement(player, obstacle_tiles)
            if ai_dx != 0 or ai_dy != 0:
                self.state = CharacterState.MOVING
                self.move(ai_dx, ai_dy, obstacle_tiles)
            else:
                self.state = CharacterState.IDLE

        return fireball

    def update(self, item_group=None, coin_images=None, red_potion=None):
        if self.health <= 0 and self.alive:
            self.health = 0
            self.alive = False
            self.state = CharacterState.DEAD
            if item_group and coin_images and red_potion:
                self.drop_item(item_group, coin_images, red_potion)
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
        if new_action != self.action:
            self.action = new_action
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def drop_item(self, item_group, coin_images, red_potion):
        item_type = random.choice([0, 1])
        if item_type == 0:
            item = Item(self.rect.centerx, self.rect.centery, 0, coin_images)
        else:
            item = Item(self.rect.centerx, self.rect.centery, 1, [red_potion])
        item_group.add(item)

    def draw(self, screen):
        if not self.alive:
            return

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
        screen.blit(flipped_image, self.rect)

        pygame.draw.rect(screen, (255, 0, 0), self.rect, 2)

        if self.path:
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
    def find_safe_position(self, player_pos, tile_grid, obstacles, map_width, map_height, obstacle_tiles, min_distance=3, radius=4):
        """
        Tìm vị trí an toàn xa player_pos nhất, trong bán kính 'radius' và cách ít nhất min_distance ô.
        """
        max_dist = 0
        best_pos = None
        enemy_tile_x = self.rect.centerx // constants.TILE_SIZE
        enemy_tile_y = self.rect.centery // constants.TILE_SIZE
        enemy_pos = (int(enemy_tile_x), int(enemy_tile_y))

        x_start = max(0, player_pos[0] - 5)
        x_end = min(map_width, player_pos[0] + 5)
        y_start = max(0, player_pos[1] - 5)
        y_end = min(map_height, player_pos[1] + 5)
        for x in range(x_start,x_end):
            for y in range(y_start,y_end):
                if (tile_grid[x][y]== -1 or tile_grid[x][y] == 7 ):
                    continue
                # Kiểm tra có phải ô hợp lệ không
                (step_dx, step_dy), path = a_star(enemy_pos, (x, y), tile_grid, obstacle_tiles, map_width, map_height)
                if path is None:
                    continue
                dist = abs(x - player_pos[0]) + abs(y - player_pos[1])
                if dist >= min_distance and dist > max_dist:
                    max_dist = dist
                    best_pos = (x, y)

        if best_pos is None and min_distance > 1:
            return self.find_safe_position(player_pos, tile_grid, obstacles, map_width, map_height, obstacle_tiles, min_distance - 1, radius)
        return best_pos


