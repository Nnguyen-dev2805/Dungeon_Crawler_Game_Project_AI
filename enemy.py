import pygame
import constants
import weapon
import math
import numpy as np
import random
import heapq

from collections import deque
from enum import Enum, auto
from item import Item
from algorithms import a_star, bfs


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
        self.distance_moved = 0

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = pygame.Rect(
            0, 0, constants.TILE_SIZE * size, constants.TILE_SIZE * size
        )
        self.rect.center = (x, y)
        self.state = CharacterState.IDLE

    def move(self, dx, dy, obstacle_tiles):
        self.running = False
        if dx != 0 or dy != 0:
            self.running = True

        if dx > 0:
            self.flip = False
        if dx < 0:
            self.flip = True

        if dx != 0 and dy != 0:
            dx = dx * (math.sqrt(2) / 2)
            dy = dy * (math.sqrt(2) / 2)

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
            (dx, dy), self.path = a_star(enemy_pos, player_pos, tile_grid, obstacle_tiles) # sử dụng thuật toán
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

    def bfs(self, start, goal, tile_grid, obstacle_tiles):
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