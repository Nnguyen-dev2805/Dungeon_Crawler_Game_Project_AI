# import pygame
# import constants
# import weapon
# import math
# import numpy as np
# import random
# import heapq

# from collections import deque
# from enum import Enum, auto
# from item import Item
# from algorithms import a_star, bfs
# from qlearning import QLearn  # Import lớp QLearn


# class CharacterState(Enum):
#     IDLE = auto()
#     MOVING = auto()
#     STUNNED = auto()
#     ATTACKING = auto()
#     DEAD = auto()

# class Direction(Enum):
#     NONE = auto()
#     UP = auto()
#     DOWN = auto()
#     LEFT = auto()
#     RIGHT = auto()
#     LEFT_UP = auto()
#     LEFT_DOWN = auto()
#     RIGHT_UP = auto()
#     RIGHT_DOWN = auto()

# class Enemy:
#     def __init__(self, x, y, health, mob_animations, char_type, boss, size, map_width, map_height):
#         self.char_type = char_type
#         self.boss = boss
#         self.flip = False
#         self.frame_index = 0
#         self.action = 0
#         self.animation_list = mob_animations[char_type]
#         self.update_time = pygame.time.get_ticks()
#         self.running = False
#         self.health = health
#         self.max_health = health
#         self.alive = True
#         self.hit = False
#         self.last_hit = pygame.time.get_ticks()
#         self.last_attack = pygame.time.get_ticks()
#         self.last_path_update = pygame.time.get_ticks()
#         self.path = []

#         self.actions = list(range(9))  # 0: NONE, 1: UP, 2: DOWN, 3: LEFT, 4: RIGHT, 5: LEFT_UP, 6: LEFT_DOWN, 7: RIGHT_UP, 8: RIGHT_DOWN
#         # self.qlearn = QLearn(actions=self.actions, alpha=0.1, gamma=0.9, epsilon=0.1)
#         self.qlearn = QLearn(actions=self.actions, alpha=0.2, gamma=0.9, epsilon=0.3)
#         self.last_state = None
#         self.last_action = None

#         self.target_center = None 
#         self.frames_left = 0
#         self.direction = Direction.NONE
#         self.step_count = 0

#         self.image = self.animation_list[self.action][self.frame_index]
#         self.rect = pygame.Rect(
#             0, 0, constants.TILE_SIZE * size, constants.TILE_SIZE * size
#         )
#         self.rect.center = (x, y)
#         self.state = CharacterState.IDLE

#         self.diagonal_steps = 16
#         self.straight_steps = 12
#         self.step_size = 4.0  
#         self.remaining_distance = constants.TILE_SIZE * math.sqrt(2) - (self.diagonal_steps * self.step_size)
#         self.diagonal_dx = 2 * math.sqrt(2)  
#         self.diagonal_dy = 2 * math.sqrt(2) 
#         self.final_dx = self.remaining_distance / math.sqrt(2)  
#         self.final_dy = self.remaining_distance / math.sqrt(2)  
#         self.straight_dx = self.step_size  
#         self.straight_dy = self.step_size 

#         # self.search_belief_map = [[0 for _ in range(map_height)] 
#         #                          for _ in range(map_width)]
#         self.search_belief_map = {}  # từ điển lưu trạng thái niềm tin
#         self.visited_positions = set()  # lưu trữ các vị trí đã đi qua
#         self.lost_player_timer = 0
#         self.lost_player_timeout = 600  # thời gian tối đa mất dấu người chơi
#         self.player_search_trigger = False
#         self.fov_radius = 4  # bán kính quan sát 

#         self.last_belief_update = pygame.time.get_ticks()  # thêm biến thời gian cập nhật
#         self.actual_map_width = map_width  # kích thước thực tế sử dụng
#         self.actual_map_height = map_height

#         self.current_best_pos = None  # Lưu best_pos hiện tại
#         self.delay_timer = 0  # Timer để trì hoãn gọi best_pos mới
#         self.delay_duration = 500  # Delay 500ms trước khi gọi best_pos mới

#     def move(self, dx, dy, obstacle_tiles):
#         self.running = False
#         if dx != 0 or dy != 0:
#             self.running = True

#         if dx > 0:
#             self.flip = False
#         if dx < 0:
#             self.flip = True

#         self.rect.x += dx
#         for obstacle in obstacle_tiles:
#             if obstacle[1].colliderect(self.rect):
#                 if dx > 0:
#                     self.rect.right = obstacle[1].left
#                 if dx < 0:
#                     self.rect.left = obstacle[1].right
        
#         self.rect.y += dy
#         for obstacle in obstacle_tiles:
#             if obstacle[1].colliderect(self.rect):
#                 if dy > 0:
#                     self.rect.bottom = obstacle[1].top
#                 if dy < 0:
#                     self.rect.top = obstacle[1].bottom

#     def get_map_pos(self):
#         return (self.rect.centerx // constants.TILE_SIZE, self.rect.centery // constants.TILE_SIZE)

#     def get_obstacle_positions(self,obstacle_tiles):
#         return set((int(obstacle[2] / constants.TILE_SIZE), int(obstacle[3] / constants.TILE_SIZE)) 
#                    for obstacle in obstacle_tiles)

#     def ray_cast_player(self, player,obstacle_tiles):
#         line_of_sight = ((self.rect.centerx, self.rect.centery), (player.rect.centerx, player.rect.centery))
#         for obstacle in obstacle_tiles:
#             if obstacle[1].clipline(line_of_sight):
#                 return False
#         return True

#     def calculate_state(self, player, obstacle_tiles):
#         """
#         Calculate the state based on relative position to player and obstacles.
#         State is a tuple: (relative_x, relative_y, health_status, player_visible)
#         """
#         enemy_pos = self.get_map_pos()
#         player_pos = (player.rect.centerx // constants.TILE_SIZE, player.rect.centery // constants.TILE_SIZE)
        
#         # Tính khoảng cách tương đối
#         relative_x = player_pos[0] - enemy_pos[0]
#         relative_y = player_pos[1] - enemy_pos[1]
        
#         # Giới hạn khoảng cách để giảm không gian trạng thái
#         relative_x = max(-5, min(5, relative_x))
#         relative_y = max(-5, min(5, relative_y))
        
#         # Trạng thái sức khỏe: 0 (dưới 25%), 1 (25-50%), 2 (trên 50%)
#         health_status = 0 if self.health < self.max_health * 0.25 else 1 if self.health < self.max_health * 0.5 else 2
        
#         # Kiểm tra người chơi có trong tầm nhìn không
#         player_visible = 1 if self.ray_cast_player(player, obstacle_tiles) else 0
        
#         return (relative_x, relative_y, health_status, player_visible)

#     def get_reward(self, player, obstacle_tiles):
#         """
#         Calculate reward based on current situation.
#         - Positive reward for getting closer to player or attacking.
#         - Negative reward for low health or being too far.
#         - Bonus for hiding when low health.
#         """
#         reward = 0
#         dist = math.sqrt(
#             (self.rect.centerx - player.rect.centerx) ** 2 +
#             (self.rect.centery - player.rect.centery) ** 2
#         )
        
#         # Phần thưởng khi gần người chơi
#         if dist < constants.ATTACK_RANGE:
#             reward += 100  # Có thể tấn công
#         elif dist < constants.TILE_SIZE * 5:
#             reward += 20  # Đang tiến gần
#         else:
#             reward -= 10  # Quá xa
            
#         # Phạt nếu máu thấp
#         if self.health < self.max_health * 0.25:
#             reward -= 20
#             # Thưởng nếu đang ở vị trí an toàn (xa người chơi và có chướng ngại vật)
#             if dist > constants.TILE_SIZE * 5 and self.ray_cast_player(player, obstacle_tiles) == False:
#                 reward += 30
                
#         # Phạt nếu bị tấn công
#         if self.hit:
#             reward -= 50
            
#         return reward

#     def handle_attack(self, player, fireball_image):
#         fireball = None
#         dist = math.sqrt(
#             (self.rect.centerx - player.rect.centerx) ** 2 +
#             (self.rect.centery - player.rect.centery) ** 2
#         )

#         if dist < constants.ATTACK_RANGE and not player.hit:
#             player.health -= 10
#             player.hit = True
#             player.last_hit = pygame.time.get_ticks()

#         fireball_cooldown = 700
#         if self.boss and dist < 500:
#             if (pygame.time.get_ticks() - self.last_attack) > fireball_cooldown:
#                 fireball = weapon.Fireball(
#                     fireball_image,
#                     self.rect.centerx,
#                     self.rect.centery,
#                     player.rect.centerx,
#                     player.rect.centery,
#                 )
#                 self.last_attack = pygame.time.get_ticks()

#         return fireball, dist

#     def handle_stun(self):
#         stun_cooldown = 100
#         current_time = pygame.time.get_ticks()
#         if self.hit:
#             self.hit = False
#             self.last_hit = current_time
#             self.state = CharacterState.STUNNED
#             self.running = False
#             self.update_action(0)
#             self.direction = Direction.NONE
#             self.distance_moved = 0
#         if self.state == CharacterState.STUNNED:
#             if current_time - self.last_hit > stun_cooldown:
#                 self.state = CharacterState.IDLE

#     def update_search_belief_map(self, player,obstacle_tiles):
#         check_see = self.ray_cast_player(player,obstacle_tiles)
#         player_pos = (player.rect.centerx // constants.TILE_SIZE, player.rect.centery // constants.TILE_SIZE)
#         enemy_pos = self.get_map_pos()
#         obstacles = self.get_obstacle_positions(obstacle_tiles)
#         if check_see:
#             for x in range(max(0, player_pos[0] - 2 * self.fov_radius), min(self.actual_map_width, player_pos[0] + 2 * self.fov_radius)):
#                 for y in range(max(0, player_pos[1] - 2 * self.fov_radius), min(self.actual_map_height, player_pos[1] + 2 * self.fov_radius)):
#                     if (x, y) not in obstacles:
#                         self.search_belief_map[(x, y)] = 0  
#                         self.search_belief_map[(x, y)] = min(10, self.search_belief_map.get((x, y), 0) + 5)
            
#             for x in range(max(0, player_pos[0] - self.fov_radius), min(self.actual_map_width, player_pos[0] + self.fov_radius)):
#                 for y in range(max(0, player_pos[1] - self.fov_radius), min(self.actual_map_height, player_pos[1] + self.fov_radius)):
#                     if (x, y) not in obstacles:
#                         self.search_belief_map[(x, y)] = min(10, self.search_belief_map.get((x, y), 0) + 5)

#         else:
#             fov_radius = 2
#             for x in range(max(0, enemy_pos[0] - fov_radius), min(self.actual_map_width, enemy_pos[0] + fov_radius)):
#                 for y in range(max(0, enemy_pos[1] - fov_radius), min(self.actual_map_height, enemy_pos[1] + fov_radius)):
#                     # if (x, y) not in obstacles:
#                     #     self.search_belief_map[(x, y)] = 0
#                     if (x, y) not in obstacles and (x, y) not in self.visited_positions:
#                         self.search_belief_map[(x, y)] = max(0, self.search_belief_map.get((x, y), 0))  # giữ niềm tin hiện tại
#                     if random.random() < 0.1:  # thêm ngẫu nhiên niềm tin nhỏ
#                         self.search_belief_map[(x, y)] = min(3, self.search_belief_map.get((x, y), 0) + 1)

#     def decay_search_belief_map(self,obstacle_tiles):
#         decay_rate = 0.01
#         obstacles = self.get_obstacle_positions(obstacle_tiles)
#         keys_to_remove = []
#         for (x, y), belief in list(self.search_belief_map.items()):
#             if (x, y) not in obstacles:
#                 new_belief = max(0, belief - decay_rate)
#                 if new_belief > 0:
#                     self.search_belief_map[(x, y)] = new_belief
#                 else:
#                     keys_to_remove.append((x, y))
#         # xóa nhưng thằng niềm tin bằng 0
#         for key in keys_to_remove:
#             del self.search_belief_map[key]

#     def find_patroltarget_belief_map(self,obstacle_tiles,tile_grid):
#         best_score = -float("inf")
#         best_pos = None
#         obstacles = self.get_obstacle_positions(obstacle_tiles)
#         enemy_pos = self.get_map_pos()
#         max_belief = max((belief for (x, y), belief in self.search_belief_map.items() 
#                      if (x, y) not in obstacles), default=0)
#         max_distance = math.sqrt(self.actual_map_width**2 + self.actual_map_height**2)
#         search_radius = 10
#         for (x, y), belief in self.search_belief_map.items():
#             if abs(x - enemy_pos[0]) > search_radius or abs(y - enemy_pos[1]) > search_radius:
#                 continue
#             if (x, y) in obstacles or x >= len(tile_grid[0]) or y >= len(tile_grid) or tile_grid[y][x] == -1:
#                 continue
#             dist = math.sqrt((x - enemy_pos[0])**2 + (y - enemy_pos[1])**2)
#             # if max_belief == 0:
#             #     score = -dist / max_distance * 0.05
#             # else:
#             score = belief / max_belief * 0.95 - dist / max_distance * 0.05

#             # giảm điểm số nếu vị trí đã đi qua
#             if (x, y) in self.visited_positions:
#                 score -= 0.5 
#             if score > best_score:
#                 best_score = score
#                 best_pos = (x, y)

#         if not best_pos:
#             # valid_positions = [(x, y) for x in range(max(0, enemy_pos[0] - search_radius), min(self.actual_map_width, enemy_pos[0] + search_radius))
#             #               for y in range(max(0, enemy_pos[1] - search_radius), min(self.actual_map_height, enemy_pos[1] + search_radius))
#             #               if (x, y) not in obstacles and (x, y) != enemy_pos]
#             valid_positions = [
#                 (x, y)
#                 for x in range(max(0, enemy_pos[0] - search_radius), min(self.actual_map_width, enemy_pos[0] + search_radius))
#                 for y in range(max(0, enemy_pos[1] - search_radius), min(self.actual_map_height, enemy_pos[1] + search_radius))
#                 if (x, y) not in obstacles
#                 and x < len(tile_grid[0]) and y < len(tile_grid)
#                 and tile_grid[y][x] != -1
#                 and (x, y) != enemy_pos
#             ]
#             # ưu tiên các vị trí chưa đi qua
#             unvisited_positions = [pos for pos in valid_positions if pos not in self.visited_positions]
#             if unvisited_positions:
#                 best_pos = random.choice(unvisited_positions)
#             elif valid_positions:
#                 best_pos = random.choice(valid_positions)
#             else:
#                 best_pos = enemy_pos

#         print(f"DEBUG: Patrol target position = {best_pos}")
#         return best_pos

#     def handle_movement(self, player, tile_grid, obstacle_tiles,map_width, map_height):
#         ai_dx = 0
#         ai_dy = 0

#         enemy_tile_x = self.rect.centerx // constants.TILE_SIZE
#         enemy_tile_y = self.rect.centery // constants.TILE_SIZE
#         enemy_pos = (int(enemy_tile_x), int(enemy_tile_y))

#         self.visited_positions.add(enemy_pos)  # đánh dấu vị trí đã đi qua

#         player_tile_x = player.rect.centerx // constants.TILE_SIZE
#         player_tile_y = player.rect.centery // constants.TILE_SIZE
#         player_pos = (int(player_tile_x), int(player_tile_y))
        

#         self.update_search_belief_map(player,obstacle_tiles)
#         self.decay_search_belief_map(obstacle_tiles)

#         if self.direction != Direction.NONE:
#             if self.direction in [Direction.LEFT_UP, Direction.LEFT_DOWN, Direction.RIGHT_UP, Direction.RIGHT_DOWN]:
#                 if self.step_count >= self.diagonal_steps:
#                     if self.direction == Direction.LEFT_UP:
#                         ai_dx = -self.final_dx
#                         ai_dy = -self.final_dy
#                     elif self.direction == Direction.LEFT_DOWN:
#                         ai_dx = -self.final_dx
#                         ai_dy = self.final_dy
#                     elif self.direction == Direction.RIGHT_UP:
#                         ai_dx = self.final_dx
#                         ai_dy = -self.final_dy
#                     elif self.direction == Direction.RIGHT_DOWN:
#                         ai_dx = self.final_dx
#                         ai_dy = self.final_dy
#                     self.step_count = 0  
#                     self.direction = Direction.NONE
#                 else:
#                     if self.direction == Direction.LEFT_UP:
#                         ai_dx = -self.diagonal_dx
#                         ai_dy = -self.diagonal_dy
#                     elif self.direction == Direction.LEFT_DOWN:
#                         ai_dx = -self.diagonal_dx
#                         ai_dy = self.diagonal_dy
#                     elif self.direction == Direction.RIGHT_UP:
#                         ai_dx = self.diagonal_dx
#                         ai_dy = -self.diagonal_dy
#                     elif self.direction == Direction.RIGHT_DOWN:
#                         ai_dx = self.diagonal_dx
#                         ai_dy = self.diagonal_dy
#                     self.step_count += 1
#             else:
#                 if self.step_count < self.straight_steps:
#                     if self.direction == Direction.RIGHT:
#                         ai_dx = self.straight_dx
#                         ai_dy = 0
#                     elif self.direction == Direction.LEFT:
#                         ai_dx = -self.straight_dx
#                         ai_dy = 0
#                     elif self.direction == Direction.DOWN:
#                         ai_dx = 0
#                         ai_dy = self.straight_dy
#                     elif self.direction == Direction.UP:
#                         ai_dx = 0
#                         ai_dy = -self.straight_dy
#                     self.step_count += 1
#                 else:
#                     self.step_count = 0
#                     self.direction = Direction.NONE

#         if self.direction == Direction.NONE:
#             current_time = pygame.time.get_ticks()
#             if not self.path or (self.path and (enemy_pos[0], enemy_pos[1]) == self.path[-1]):
#                 best_pos = self.find_patroltarget_belief_map(obstacle_tiles,tile_grid)
#                 if best_pos and 0 <= best_pos[0] < map_width and 0 <= best_pos[1] < map_height and best_pos not in self.get_obstacle_positions(obstacle_tiles):
#                     # print(f"DEBUG: Calculating path from {enemy_pos} to {best_pos}")  
#                     next_step = best_pos
#                     (dx, dy), self.path = a_star(enemy_pos, best_pos, tile_grid, obstacle_tiles, map_width, map_height)
#                     if self.path:
#                         next_step = self.path[0] if self.path else enemy_pos
#                         dx = next_step[0] - enemy_pos[0]
#                         dy = next_step[1] - enemy_pos[1]
#                         # print(f"DEBUG: Path found, length = {len(self.path)}")
#                     else:
#                         print("ahahhaahhahahhaha")
#                         directions = [
#                             (0, 1), (1, 0), (0, -1), (-1, 0),
#                             (-1, -1), (-1, 1), (1, -1), (1, 1)
#                         ]
#                         random_direction = random.choice(directions)
#                         next_step = (enemy_pos[0] + random_direction[0], enemy_pos[1] + random_direction[1])
#                         dx = random_direction[0]
#                         dy = random_direction[1]
#                 else:
#                     print("DEBUG: Invalid best_pos, using random direction")
#                     directions = [
#                         (0, 1), (1, 0), (0, -1), (-1, 0),
#                         (-1, -1), (-1, 1), (1, -1), (1, 1)
#                     ]
#                     random_direction = random.choice(directions)
#                     next_step = (enemy_pos[0] + random_direction[0], enemy_pos[1] + random_direction[1])
#                     dx = random_direction[0]
#                     dy = random_direction[1]

#             else:
#                 # # Tiếp tục di chuyển theo path hiện tại
#                 # if self.path:
#                 #     self.path.pop(0)
#                 #     if self.path:
#                 #         next_step = self.path[0]
#                 #         dx = next_step[0] - enemy_pos[0]
#                 #         dy = next_step[1] - enemy_pos[1]
#                 #         # print(f"DEBUG: Following path to {next_step}")
#                 #     else:
#                 #         print("DEBUG: Path completed, recalculating")
#                 #         return self.handle_movement(player, tile_grid, obstacle_tiles, map_width, map_height)
#                 # else:
#                 #     print("DEBUG: LALALALLALALAL")
#                 #     directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]
#                 #     random_direction = random.choice(directions)
#                 #     next_step = (enemy_pos[0] + random_direction[0], enemy_pos[1] + random_direction[1])
#                 #     dx = random_direction[0]
#                 #     dy = random_direction[1]
#                 self.path.pop(0)
#                 next_step = self.path[0] if self.path else enemy_pos
#                 dx = next_step[0] - enemy_pos[0]
#                 dy = next_step[1] - enemy_pos[1]

#             obstacles = set(
#                 (int(obstacle[2] / constants.TILE_SIZE), int(obstacle[3] / constants.TILE_SIZE))
#                 for obstacle in obstacle_tiles
#             )

#             if (next_step[0], next_step[1]) in obstacles or next_step[0] < 0 or next_step[0] >= map_width or next_step[1] < 0 or next_step[1] >= map_height:
#                 self.direction = Direction.NONE
#                 self.path = []
#                 return 0, 0

#             if dx > 0 and dy == 0:
#                 self.direction = Direction.RIGHT
#                 self.step_count = 0
#             elif dx < 0 and dy == 0:
#                 self.direction = Direction.LEFT
#                 self.step_count = 0
#             elif dx == 0 and dy > 0:
#                 self.direction = Direction.DOWN
#                 self.step_count = 0
#             elif dx == 0 and dy < 0:
#                 self.direction = Direction.UP
#                 self.step_count = 0
#             elif dx < 0 and dy < 0:
#                 self.direction = Direction.LEFT_UP
#                 self.step_count = 0
#             elif dx < 0 and dy > 0:
#                 self.direction = Direction.LEFT_DOWN
#                 self.step_count = 0
#             elif dx > 0 and dy < 0:
#                 self.direction = Direction.RIGHT_UP
#                 self.step_count = 0
#             elif dx > 0 and dy > 0:
#                 self.direction = Direction.RIGHT_DOWN
#                 self.step_count = 0
#             else:
#                 self.direction = Direction.NONE
        
#         return ai_dx, ai_dy

#     # def handle_movement(self, player, tile_grid, obstacle_tiles, map_width, map_height):
#     #     """
#     #     Use Q-learning to choose movement direction.
#     #     """
#     #     # Tính trạng thái hiện tại
#     #     state = self.calculate_state(player, obstacle_tiles)
#     #     reward = self.get_reward(player, obstacle_tiles)
        
#     #     # Cập nhật Q-value cho trạng thái và hành động trước đó
#     #     if self.last_state is not None and self.last_action is not None:
#     #         self.qlearn.learn(self.last_state, self.last_action, state, reward)
        
#     #     # Chọn hành động mới
#     #     action = self.qlearn.choose_action(state)
#     #     self.last_state = state
#     #     self.last_action = action

#     #     print(f"State: {state}, Reward: {reward}, Action: {action}")
        
#     #     # Ánh xạ hành động sang hướng di chuyển
#     #     direction_map = {
#     #         0: Direction.NONE,
#     #         1: Direction.UP,
#     #         2: Direction.DOWN,
#     #         3: Direction.LEFT,
#     #         4: Direction.RIGHT,
#     #         5: Direction.LEFT_UP,
#     #         6: Direction.LEFT_DOWN,
#     #         7: Direction.RIGHT_UP,
#     #         8: Direction.RIGHT_DOWN
#     #     }
#     #     self.direction = direction_map[action]
        
#     #     ai_dx, ai_dy = 0, 0
#     #     if self.direction != Direction.NONE:
#     #         if self.direction in [Direction.LEFT_UP, Direction.LEFT_DOWN, Direction.RIGHT_UP, Direction.RIGHT_DOWN]:
#     #             if self.step_count >= self.diagonal_steps:
#     #                 if self.direction == Direction.LEFT_UP:
#     #                     ai_dx = -self.final_dx
#     #                     ai_dy = -self.final_dy
#     #                 elif self.direction == Direction.LEFT_DOWN:
#     #                     ai_dx = -self.final_dx
#     #                     ai_dy = self.final_dy
#     #                 elif self.direction == Direction.RIGHT_UP:
#     #                     ai_dx = self.final_dx
#     #                     ai_dy = -self.final_dy
#     #                 elif self.direction == Direction.RIGHT_DOWN:
#     #                     ai_dx = self.final_dx
#     #                     ai_dy = self.final_dy
#     #                 self.step_count = 0  
#     #                 self.direction = Direction.NONE
#     #             else:
#     #                 if self.direction == Direction.LEFT_UP:
#     #                     ai_dx = -self.diagonal_dx
#     #                     ai_dy = -self.diagonal_dy
#     #                 elif self.direction == Direction.LEFT_DOWN:
#     #                     ai_dx = -self.diagonal_dx
#     #                     ai_dy = self.diagonal_dy
#     #                 elif self.direction == Direction.RIGHT_UP:
#     #                     ai_dx = self.diagonal_dx
#     #                     ai_dy = -self.diagonal_dy
#     #                 elif self.direction == Direction.RIGHT_DOWN:
#     #                     ai_dx = self.diagonal_dx
#     #                     ai_dy = self.diagonal_dy
#     #                 self.step_count += 1
#     #         else:
#     #             if self.step_count < self.straight_steps:
#     #                 if self.direction == Direction.RIGHT:
#     #                     ai_dx = self.straight_dx
#     #                     ai_dy = 0
#     #                 elif self.direction == Direction.LEFT:
#     #                     ai_dx = -self.straight_dx
#     #                     ai_dy = 0
#     #                 elif self.direction == Direction.DOWN:
#     #                     ai_dx = 0
#     #                     ai_dy = self.straight_dy
#     #                 elif self.direction == Direction.UP:
#     #                     ai_dx = 0
#     #                     ai_dy = -self.straight_dy
#     #                 self.step_count += 1
#     #             else:
#     #                 self.step_count = 0
#     #                 self.direction = Direction.NONE
        
#     #     return ai_dx, ai_dy

    
#     def ai(self, player, tile_graph, tile_grid, obstacle_tiles, screen_scroll, fireball_image, map_width, map_height):
#         self.rect.x += screen_scroll[0]
#         self.rect.y += screen_scroll[1]
#         self.handle_stun()

#         if self.state == CharacterState.DEAD or self.state == CharacterState.STUNNED:
#             return None

#         fireball, dist = self.handle_attack(player, fireball_image)

#         if self.state != CharacterState.STUNNED:
#             ai_dx, ai_dy = self.handle_movement(player, tile_grid, obstacle_tiles, map_width, map_height)
#             if ai_dx != 0 or ai_dy != 0:
#                 self.state = CharacterState.MOVING
#                 self.move(ai_dx, ai_dy, obstacle_tiles)
#             else:
#                 self.state = CharacterState.IDLE

#         return fireball

#     def update(self, item_group=None, coin_images=None, red_potion=None):
#         if self.health <= 0 and self.alive:
#             self.health = 0
#             self.alive = False
#             self.state = CharacterState.DEAD
#             if item_group and coin_images and red_potion:
#                 self.drop_item(item_group, coin_images, red_potion)
#         if self.running:
#             self.update_action(1)
#         else:
#             self.update_action(0)
#         aninmation_cooldown = 70
#         self.image = self.animation_list[self.action][self.frame_index]
#         if pygame.time.get_ticks() - self.update_time > aninmation_cooldown:
#             self.update_time = pygame.time.get_ticks()
#             self.frame_index += 1
#         if self.frame_index >= len(self.animation_list[self.action]):
#             self.frame_index = 0

#     def update_action(self, new_action):
#         if new_action != self.action:
#             self.action = new_action
#             self.frame_index = 0
#             self.update_time = pygame.time.get_ticks()

#     def drop_item(self, item_group, coin_images, red_potion):
#         item_type = random.choice([0, 1])
#         if item_type == 0:
#             item = Item(self.rect.centerx, self.rect.centery, 0, coin_images)
#         else:
#             item = Item(self.rect.centerx, self.rect.centery, 1, [red_potion])
#         item_group.add(item)

#     def draw(self, screen):
#         if not self.alive:
#             return

#         health_bar_width = 40
#         health_bar_height = 4
#         health_ratio = self.health / self.max_health
#         pygame.draw.rect(screen, (255, 0, 0), 
#                         (self.rect.centerx - health_bar_width//2, 
#                          self.rect.top - 10, 
#                          health_bar_width, 
#                          health_bar_height))
#         pygame.draw.rect(screen, (0, 255, 0), 
#                         (self.rect.centerx - health_bar_width//2, 
#                          self.rect.top - 10, 
#                          health_bar_width * health_ratio, 
#                          health_bar_height))

#         flipped_image = pygame.transform.flip(self.image, self.flip, False)
#         screen.blit(flipped_image, self.rect)

#         pygame.draw.rect(screen, (255, 0, 0), self.rect, 2)

#         if self.path:
#             for i in range(len(self.path) - 1):
#                 start_pos = (
#                     self.path[i][0] * constants.TILE_SIZE + constants.TILE_SIZE // 2,
#                     self.path[i][1] * constants.TILE_SIZE + constants.TILE_SIZE // 2
#                 )
#                 end_pos = (
#                     self.path[i + 1][0] * constants.TILE_SIZE + constants.TILE_SIZE // 2,
#                     self.path[i + 1][1] * constants.TILE_SIZE + constants.TILE_SIZE // 2
#                 )
#                 pygame.draw.line(screen, (0, 0, 255), start_pos, end_pos, 1)
#                 pygame.draw.circle(screen, (0, 0, 255), start_pos, 1)

#         enemy_tile_x = self.rect.centerx // constants.TILE_SIZE
#         enemy_tile_y = self.rect.centery // constants.TILE_SIZE
#         tile_center = (
#             enemy_tile_x * constants.TILE_SIZE + constants.TILE_SIZE / 2,
#             enemy_tile_y * constants.TILE_SIZE + constants.TILE_SIZE / 2
#         )
#         pygame.draw.circle(screen, (0, 255, 0), tile_center, 3)
#         pygame.draw.circle(screen, (255, 255, 0), self.rect.center, 3)
#         if self.state == CharacterState.STUNNED:
#             pygame.draw.circle(screen, (255, 0, 0), 
#                                (self.rect.centerx, self.rect.top - 15), 3)

#     def can_attack(self):
#         return pygame.time.get_ticks() - self.last_attack > self.attack_cooldown

#     def update_state(self):
#         if self.state == CharacterState.IDLE:
#             self.update_action(0)
#         elif self.state == CharacterState.MOVING:
#             self.update_action(1)
#         elif self.state == CharacterState.ATTACKING:
#             self.update_action(2)

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
from qlearning import QLearn  # Import lớp QLearn

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
    LEFT_UP = auto()
    LEFT_DOWN = auto()
    RIGHT_UP = auto()
    RIGHT_DOWN = auto()

class Enemy:
    def __init__(self, x, y, health, mob_animations, char_type, boss, size, map_width, map_height):
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

        self.actions = list(range(9))  # 0: NONE, 1: UP, 2: DOWN, 3: LEFT, 4: RIGHT, 5: LEFT_UP, 6: LEFT_DOWN, 7: RIGHT_UP, 8: RIGHT_DOWN
        self.qlearn = QLearn(actions=self.actions, alpha=0.2, gamma=0.9, epsilon=0.3)
        self.last_state = None
        self.last_action = None

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

        self.search_belief_map = {}  # từ điển lưu trạng thái niềm tin
        self.visited_positions = set()  # lưu trữ các vị trí đã đi qua
        self.lost_player_timer = 0
        self.lost_player_timeout = 600  # thời gian tối đa mất dấu người chơi
        self.player_search_trigger = False
        self.fov_radius = 4  # bán kính quan sát 

        self.last_belief_update = pygame.time.get_ticks()  # thêm biến thời gian cập nhật
        self.actual_map_width = map_width  # kích thước thực tế sử dụng
        self.actual_map_height = map_height

        self.current_best_pos = None  # Lưu best_pos hiện tại
        self.delay_timer = 0  # Timer để trì hoãn gọi best_pos mới
        self.delay_duration = 500  # Delay 500ms trước khi gọi best_pos mới

        # Biến hỗ trợ DEBUG
        self.debug_best_pos = None  # Lưu vị trí best_pos
        self.debug_waiting_for_space = False  # Trạng thái chờ nhấn phím cách
        self.position_printed = False  # Cờ kiểm soát việc in vị trí

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

    def get_map_pos(self):
        return (self.rect.centerx // constants.TILE_SIZE, self.rect.centery // constants.TILE_SIZE)

    def get_obstacle_positions(self, obstacle_tiles):
        return set((int(obstacle[2] / constants.TILE_SIZE), int(obstacle[3] / constants.TILE_SIZE)) 
                   for obstacle in obstacle_tiles)

    def ray_cast_player(self, player, obstacle_tiles):
        line_of_sight = ((self.rect.centerx, self.rect.centery), (player.rect.centerx, player.rect.centery))
        for obstacle in obstacle_tiles:
            if obstacle[1].clipline(line_of_sight):
                return False
        return True

    def calculate_state(self, player, obstacle_tiles):
        enemy_pos = self.get_map_pos()
        player_pos = (player.rect.centerx // constants.TILE_SIZE, player.rect.centery // constants.TILE_SIZE)
        relative_x = player_pos[0] - enemy_pos[0]
        relative_y = player_pos[1] - enemy_pos[1]
        relative_x = max(-5, min(5, relative_x))
        relative_y = max(-5, min(5, relative_y))
        health_status = 0 if self.health < self.max_health * 0.25 else 1 if self.health < self.max_health * 0.5 else 2
        player_visible = 1 if self.ray_cast_player(player, obstacle_tiles) else 0
        return (relative_x, relative_y, health_status, player_visible)

    def get_reward(self, player, obstacle_tiles):
        reward = 0
        dist = math.sqrt(
            (self.rect.centerx - player.rect.centerx) ** 2 +
            (self.rect.centery - player.rect.centery) ** 2
        )
        if dist < constants.ATTACK_RANGE:
            reward += 100
        elif dist < constants.TILE_SIZE * 5:
            reward += 20
        else:
            reward -= 10
        if self.health < self.max_health * 0.25:
            reward -= 20
            if dist > constants.TILE_SIZE * 5 and self.ray_cast_player(player, obstacle_tiles) == False:
                reward += 30
        if self.hit:
            reward -= 50
        return reward

    def handle_attack(self, player, fireball_image):
        fireball = None
        dist = math.sqrt(
            (self.rect.centerx - player.rect.centerx) ** 2 +
            (self.rect.centery - player.rect.centery) ** 2
        )

        if dist < constants.ATTACK_RANGE and not player.hit:
            # player.health -= 10
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

    def update_search_belief_map(self, player, obstacle_tiles):
        check_see = self.ray_cast_player(player, obstacle_tiles)
        player_pos = (player.rect.centerx // constants.TILE_SIZE, player.rect.centery // constants.TILE_SIZE)
        enemy_pos = self.get_map_pos()
        obstacles = self.get_obstacle_positions(obstacle_tiles)
        if check_see:
            for x in range(max(0, player_pos[0] - 2 * self.fov_radius), min(self.actual_map_width, player_pos[0] + 2 * self.fov_radius)):
                for y in range(max(0, player_pos[1] - 2 * self.fov_radius), min(self.actual_map_height, player_pos[1] + 2 * self.fov_radius)):
                    if (x, y) not in obstacles:
                        self.search_belief_map[(x, y)] = 0  
                        self.search_belief_map[(x, y)] = min(10, self.search_belief_map.get((x, y), 0) + 5)
            
            for x in range(max(0, player_pos[0] - self.fov_radius), min(self.actual_map_width, player_pos[0] + self.fov_radius)):
                for y in range(max(0, player_pos[1] - self.fov_radius), min(self.actual_map_height, player_pos[1] + self.fov_radius)):
                    if (x, y) not in obstacles:
                        self.search_belief_map[(x, y)] = min(10, self.search_belief_map.get((x, y), 0) + 5)

        else:
            fov_radius = 2
            for x in range(max(0, enemy_pos[0] - fov_radius), min(self.actual_map_width, enemy_pos[0] + fov_radius)):
                for y in range(max(0, enemy_pos[1] - fov_radius), min(self.actual_map_height, enemy_pos[1] + fov_radius)):
                    if (x, y) not in obstacles and (x, y) not in self.visited_positions:
                        self.search_belief_map[(x, y)] = max(0, self.search_belief_map.get((x, y), 0))
                    # if random.random() < 0.1:
                    #     self.search_belief_map[(x, y)] = min(3, self.search_belief_map.get((x, y), 0) + 1)

    def decay_search_belief_map(self, obstacle_tiles):
        decay_rate = 0.01
        obstacles = self.get_obstacle_positions(obstacle_tiles)
        keys_to_remove = []
        for (x, y), belief in list(self.search_belief_map.items()):
            if (x, y) not in obstacles:
                new_belief = max(0, belief - decay_rate)
                if new_belief > 0:
                    self.search_belief_map[(x, y)] = new_belief
                else:
                    keys_to_remove.append((x, y))
        for key in keys_to_remove:
            del self.search_belief_map[key]

    def find_patroltarget_belief_map(self, obstacle_tiles, tile_grid):
        best_score = -float("inf")
        best_pos = None
        obstacles = self.get_obstacle_positions(obstacle_tiles)
        enemy_pos = self.get_map_pos()
        max_belief = max((belief for (x, y), belief in self.search_belief_map.items() 
                     if (x, y) not in obstacles), default=0)
        max_distance = math.sqrt(self.actual_map_width**2 + self.actual_map_height**2)
        search_radius = 10
        for (x, y), belief in self.search_belief_map.items():
            if abs(x - enemy_pos[0]) > search_radius or abs(y - enemy_pos[1]) > search_radius:
                continue
            if (x, y) in obstacles or x >= len(tile_grid[0]) or y >= len(tile_grid) or tile_grid[y][x] == -1:
                continue
            dist = math.sqrt((x - enemy_pos[0])**2 + (y - enemy_pos[1])**2)
            score = belief / max_belief * 0.95 - dist / max_distance * 0.05

            if (x, y) in self.visited_positions:
                score -= 0.5 
            if score > best_score:
                best_score = score
                best_pos = (x, y)

        if not best_pos:
            valid_positions = [
                (x, y)
                for x in range(max(0, enemy_pos[0] - search_radius), min(self.actual_map_width, enemy_pos[0] + search_radius))
                for y in range(max(0, enemy_pos[1] - search_radius), min(self.actual_map_height, enemy_pos[1] + search_radius))
                if (x, y) not in obstacles
                and x < len(tile_grid[0]) and y < len(tile_grid)
                and tile_grid[y][x] != -1
                and (x, y) != enemy_pos
            ]
            unvisited_positions = [pos for pos in valid_positions if pos not in self.visited_positions]
            if unvisited_positions:
                best_pos = random.choice(unvisited_positions)
            elif valid_positions:
                best_pos = random.choice(valid_positions)
            else:
                best_pos = enemy_pos

        print(f"DEBUG: Patrol target position = {best_pos}")
        # Lưu best_pos để in vị trí
        self.debug_best_pos = best_pos
        # In bảng niềm tin
        self.print_belief_map()
        # Kích hoạt trạng thái chờ nhấn phím cách và đặt cờ in vị trí
        self.debug_waiting_for_space = True
        self.position_printed = False

        return best_pos

    def handle_movement(self, player, tile_grid, obstacle_tiles, map_width, map_height):
        ai_dx = 0
        ai_dy = 0

        enemy_tile_x = self.rect.centerx // constants.TILE_SIZE
        enemy_tile_y = self.rect.centery // constants.TILE_SIZE
        enemy_pos = (int(enemy_tile_x), int(enemy_tile_y))

        self.visited_positions.add(enemy_pos)

        player_tile_x = player.rect.centerx // constants.TILE_SIZE
        player_tile_y = player.rect.centery // constants.TILE_SIZE
        player_pos = (int(player_tile_x), int(player_tile_y))
        
        self.update_search_belief_map(player, obstacle_tiles)
        self.decay_search_belief_map(obstacle_tiles)

        # Nếu đang chờ nhấn phím cách, không tiếp tục xử lý
        if self.debug_waiting_for_space:
            return 0, 0

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
            current_time = pygame.time.get_ticks()
            if not self.path or (self.path and (enemy_pos[0], enemy_pos[1]) == self.path[-1]):
                best_pos = self.find_patroltarget_belief_map(obstacle_tiles, tile_grid)
                if best_pos and 0 <= best_pos[0] < map_width and 0 <= best_pos[1] < map_height and best_pos not in self.get_obstacle_positions(obstacle_tiles):
                    next_step = best_pos
                    (dx, dy), self.path = a_star(enemy_pos, best_pos, tile_grid, obstacle_tiles, map_width, map_height)
                    if self.path:
                        next_step = self.path[0] if self.path else enemy_pos
                        dx = next_step[0] - enemy_pos[0]
                        dy = next_step[1] - enemy_pos[1]
                    else:
                        print("ahahhaahhahahhaha")
                        directions = [
                            (0, 1), (1, 0), (0, -1), (-1, 0),
                            (-1, -1), (-1, 1), (1, -1), (1, 1)
                        ]
                        random_direction = random.choice(directions)
                        next_step = (enemy_pos[0] + random_direction[0], enemy_pos[1] + random_direction[1])
                        dx = random_direction[0]
                        dy = random_direction[1]
                else:
                    print("DEBUG: Invalid best_pos, using random direction")
                    directions = [
                        (0, 1), (1, 0), (0, -1), (-1, 0),
                        (-1, -1), (-1, 1), (1, -1), (1, 1)
                    ]
                    random_direction = random.choice(directions)
                    next_step = (enemy_pos[0] + random_direction[0], enemy_pos[1] + random_direction[1])
                    dx = random_direction[0]
                    dy = random_direction[1]

            else:
                if self.path:
                    self.path.pop(0)
                    if self.path:
                        next_step = self.path[0]
                        dx = next_step[0] - enemy_pos[0]
                        dy = next_step[1] - enemy_pos[1]
                    else:
                        print("DEBUG: Path completed, recalculating")
                        return self.handle_movement(player, tile_grid, obstacle_tiles, map_width, map_height)
                else:
                    print("DEBUG: LALALALLALALAL")
                    directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]
                    random_direction = random.choice(directions)
                    next_step = (enemy_pos[0] + random_direction[0], enemy_pos[1] + random_direction[1])
                    dx = random_direction[0]
                    dy = random_direction[1]

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
        
        return ai_dx, ai_dy

    def check_debug_input(self):
        """Kiểm tra xem người dùng có nhấn phím cách để tiếp tục và in vị trí."""
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if self.debug_waiting_for_space:
                    self.debug_waiting_for_space = False
                    if self.debug_best_pos and not self.position_printed:
                        enemy_pos = self.get_map_pos()
                        print(f"DEBUG: Enemy position = {enemy_pos}, Target position = {self.debug_best_pos}")
                        self.position_printed = True
                    return True
        return False

    def ai(self, player, tile_graph, tile_grid, obstacle_tiles, screen_scroll, fireball_image, map_width, map_height):
        self.rect.x += screen_scroll[0]
        self.rect.y += screen_scroll[1]
        self.handle_stun()

        if self.state == CharacterState.DEAD or self.state == CharacterState.STUNNED:
            return None

        fireball, dist = self.handle_attack(player, fireball_image)

        if self.state != CharacterState.STUNNED:
            ai_dx, ai_dy = self.handle_movement(player, tile_grid, obstacle_tiles, map_width, map_height)
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
        animation_cooldown = 70
        self.image = self.animation_list[self.action][self.frame_index]
        if pygame.time.get_ticks() - self.update_time > animation_cooldown:
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

    def print_belief_map(self):
        """In từ điển search_belief_map dưới dạng bảng dễ nhìn với vị trí ô và giá trị niềm tin."""
        if not self.search_belief_map:
            print("DEBUG: Search Belief Map is empty.")
            return

        # Tìm phạm vi x và y
        x_coords = [pos[0] for pos in self.search_belief_map.keys()]
        y_coords = [pos[1] for pos in self.search_belief_map.keys()]
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)

        # In tiêu đề
        header = "     " + " ".join(f"{x:2d}" for x in range(min_x, max_x + 1))
        print(header)
        print("-----" + "---" * (max_x - min_x + 1))

        # In từng hàng
        for y in range(min_y, max_y + 1):
            row = f"{y:2d} | "
            for x in range(min_x, max_x + 1):
                belief = self.search_belief_map.get((x, y), 0)
                row += f"{belief:5.1f} "
            print(row)
