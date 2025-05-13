import pygame
import constants
import weapon
import math
from enum import Enum, auto


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

class Player:
    def __init__(self, x, y, health, mob_animations, size,player_pos):
        self.char_type = 0 
        self.score = 0
        self.flip = False
        self.frame_index = 0
        self.action = 0
        self.animation_list = mob_animations[self.char_type]
        self.update_time = pygame.time.get_ticks()
        self.running = False
        self.health = health
        self.max_health = health
        self.alive = True
        self.hit = False
        self.last_hit = pygame.time.get_ticks()
        self.state = CharacterState.IDLE
        self.player_pos_csv = player_pos

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = pygame.Rect(
            0, 0, constants.TILE_SIZE * size, constants.TILE_SIZE * size
        )
        self.rect.center = (x, y)

    def move(self, dx, dy, obstacle_tiles, exit_tile=None):
        screen_scroll = [0, 0]
        level_complete = False

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

        if exit_tile and exit_tile[1].colliderect(self.rect):
            exit_dist = math.sqrt(
                ((self.rect.centerx - exit_tile[1].centerx) ** 2 +
                 (self.rect.centery - exit_tile[1].centery) ** 2)
            )
            if exit_dist < 20:
                level_complete = True
        if self.rect.right > (constants.SCREEN_WIDTH - constants.SCROLL_THRESH):
            screen_scroll[0] = (constants.SCREEN_WIDTH - constants.SCROLL_THRESH) - self.rect.right
            self.rect.right = constants.SCREEN_WIDTH - constants.SCROLL_THRESH
        if self.rect.left < constants.SCROLL_THRESH:
            screen_scroll[0] = constants.SCROLL_THRESH - self.rect.left
            self.rect.left = constants.SCROLL_THRESH
        if self.rect.bottom > (constants.SCREEN_HEIGHT - constants.SCROLL_THRESH):
            screen_scroll[1] = (constants.SCREEN_HEIGHT - constants.SCROLL_THRESH) - self.rect.bottom
            self.rect.bottom = constants.SCREEN_HEIGHT - constants.SCROLL_THRESH
        if self.rect.top < constants.SCROLL_THRESH:
            screen_scroll[1] = constants.SCROLL_THRESH - self.rect.top
            self.rect.top = constants.SCROLL_THRESH

        # print(f"CCCCCCCCCCCCCCCCCCCCCCCC {screen_scroll}")
        return screen_scroll, level_complete

    def update(self):
        if self.health <= 0 and self.alive:
            self.health = 0
            self.alive = False
            self.state = CharacterState.DEAD
        hit_cooldown = 1000
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
        if new_action != self.action:
            self.action = new_action
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def draw(self, screen):
        if not self.alive:
            return
        screen.blit(
            self.image,
            (self.rect.x, self.rect.y - constants.SCALE * constants.OFFSET),
        )

    def get_map_pos(self):
        return (self.rect.centerx // constants.TILE_SIZE, self.rect.centery // constants.TILE_SIZE)

