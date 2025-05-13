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
from algorithms import a_star, bfs,get_path_a_star,beam_search,backtracking_search
from qlearning import QLearn 
from constants import Direction
class CharacterState(Enum):
    IDLE = auto()
    MOVING = auto()
    STUNNED = auto()
    ATTACKING = auto()
    DEAD = auto()
    FLEELING = auto()
    PATROLLING = auto()

class Enemy:
    def __init__(self, x, y, health, mob_animations, char_type, boss, size, map_width, map_height,tile_grid,enemy_pos,wall_positions,attack_algorithm):
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
        self.enemy_pos_csv = enemy_pos
        self.tile_grid = tile_grid  # Mảng 2D từ file CSV
        self.wall_positions = wall_positions # lưu các vị trí tường
        self.patrol_cooldown = 0  # Đếm thời gian chờ giữa các lần gọi handle_patrol
        self.patrol_cooldown_duration = 1  # Số frame chờ giữa các lần gọi (ví dụ: 2 frame)

        self.current_target_tile = None # lưu vị trí hiện tại của enemy
        self.actions = [1, 2, 3, 4]  # 1: UP, 2: DOWN, 3: LEFT, 4: RIGHT
        self.qlearn = QLearn(actions=self.actions, alpha=0.2, gamma=0.9, epsilon=0.3)
        self.last_state = None
        # self.last_action = None
        self.last_action = 1  # Khởi tạo hành động mặc định là UP
        self.last_positions = []  # Lưu trữ lịch sử vị trí để tránh lặp lại

        self.target_center = None 
        self.frames_left = 0
        self.direction = Direction.NONE
        self.step_count = 0
        self.directions_queue = []  # Hàng đợi lưu danh sách hướng từ A*

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = pygame.Rect(
            0, 0, constants.TILE_SIZE * size, constants.TILE_SIZE * size
        )
        self.rect.center = (x, y)
        self.state = CharacterState.IDLE
        self.player_search_trigger = False  # xác định chế độ đang thực hiện


        # ------ DÙNG CHO VIỆC DI CHUYỂN ------

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

        # ------ DÙNG CHO NIỀM TIN ------
        
        # self.search_belief_map = [[1 for _ in range(map_width)] for _ in range(map_height)]
        self.search_belief_map = [[1 for _ in range(map_height)] for _ in range(map_width)]
        # self.search_belief_map = {}  # từ điển lưu trạng thái niềm tin
        self.visited_positions = set()
        self.lost_player_timer = 0
        self.lost_player_timeout = 600

        self.fov_radius = 4

        self.last_belief_update = pygame.time.get_ticks()  # thêm biến thời gian cập nhật
        self.map_width = map_width  # kích thước thực tế sử dụng
        self.map_height = map_height

        self.current_best_pos = None  # Lưu best_pos hiện tại
        self.delay_timer = 0  # Timer để trì hoãn gọi best_pos mới
        self.delay_duration = 500  # Delay 500ms trước khi gọi best_pos mới

        self.patrol_style = "belief"  # Mặc định là tuần tra theo niềm tin, có thể thay bằng qlearning belief
        self.cover_bonus = 50  # Phần thưởng cho các vị trí gần tường
        self.repeat_penalty_base = 20  # Tăng hình phạt lặp lại vị trí
        self.exploration_bonus = 10  # Thưởng khi khám phá vị trí mới

        # Vẽ hình tròn tấn công
        self.radius = 200 #phạm vi tấn công 200 pixel
        self.draw_detection_circle = True
        self.attack_algorithm = attack_algorithm

        self.flee_start_time = None
        self.heal_cooldown = 2000  # 2 giây (2000ms)

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
        # đang dùng là dùng theo pixel
        line_of_sight = ((self.rect.centerx, self.rect.centery), (player.rect.centerx, player.rect.centery))
        for obstacle in obstacle_tiles:
            if obstacle[1].clipline(line_of_sight):
                return False
        return True

    def get_next_pos(self, pos, action):
        x, y = pos
        if action == 1:  # UP
            return (x, y - 1)
        elif action == 2:  # DOWN
            return (x, y + 1)
        elif action == 3:  # LEFT
            return (x - 1, y)
        elif action == 4:  # RIGHT
            return (x + 1, y)
        return pos

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
    
    def handle_attack(self, player, fireball_image,obstacle_tiles):
        fireball = None
        dist = math.sqrt(
            (self.rect.centerx - player.rect.centerx) ** 2 +
            (self.rect.centery - player.rect.centery) ** 2
        )
        if dist < self.radius or self.ray_cast_player(player, obstacle_tiles):
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
        if self.draw_detection_circle:
            pygame.draw.circle(screen, (255, 255, 0), self.rect.center, self.radius, 1)
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
    

    # HÀM DI CHUYỂN THEO TỪNG Ô
    def move_to_next_tile(self, next_tile, obstacle_tiles, map_width, map_height):
        ai_dx, ai_dy = 0, 0
        enemy_pos = self.get_map_pos()

        if isinstance(next_tile, (list, tuple)) and isinstance(next_tile[0], (list, tuple)):
            next_tile = next_tile[0]

        # nếu không có hướng di chuyển hoặc đã hoàn thành các bước di chuyển
        if self.direction == Direction.NONE or (self.step_count >= self.straight_steps):
            dx = next_tile[0] - enemy_pos[0]
            dy = next_tile[1] - enemy_pos[1]

            # xác định hướng di chuyển dựa trên dx, dy
            if dx > 0 and dy == 0:
                self.direction = Direction.RIGHT
            elif dx < 0 and dy == 0:
                self.direction = Direction.LEFT
            elif dx == 0 and dy > 0:
                self.direction = Direction.DOWN
            elif dx == 0 and dy < 0:
                self.direction = Direction.UP
            elif dx < 0 and dy < 0:
                self.direction = Direction.LEFT_UP
            elif dx < 0 and dy > 0:
                self.direction = Direction.LEFT_DOWN
            elif dx > 0 and dy < 0:
                self.direction = Direction.RIGHT_UP
            elif dx > 0 and dy > 0:
                self.direction = Direction.RIGHT_DOWN
            else:
                self.direction = Direction.NONE

            # kiểm tra va chạm với chướng ngại vật hoặc ngoài biên map
            obstacles = self.get_obstacle_positions(obstacle_tiles)
            if (next_tile[0], next_tile[1]) in obstacles or \
            next_tile[0] < 0 or next_tile[0] >= map_width or \
            next_tile[1] < 0 or next_tile[1] >= map_height:
                self.direction = Direction.NONE
                return 0, 0

            self.step_count = 0  

        # thực hiện di chuyển theo hướng đã chọn
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

        return ai_dx, ai_dy

# ----------------------- HÀM XỬ LÝ VIỆC TUẦN TRA SỬ DỤNG Q-LEARNING -----------------------

    def calculate_state(self, player, obstacle_tiles, map_width, map_height):
        # chưa fix PIXEL
        enemy_pos = self.get_map_pos()
        player_pos = (player.rect.centerx // constants.TILE_SIZE, player.rect.centery // constants.TILE_SIZE)
        # enemy_pos = self.enemy_pos_csv
        # player_pos = player.player_pos_csv
        
        # Lưu trữ toàn bộ khoảng cách tương đối
        relative_x = player_pos[0] - enemy_pos[0]
        relative_y = player_pos[1] - enemy_pos[1]
        
        health_status = 0 if self.health < self.max_health * 0.25 else 1 if self.health < self.max_health * 0.5 else 2
        player_visible = 1 if self.ray_cast_player(player, obstacle_tiles) else 0
        
        obstacles = self.get_obstacle_positions(obstacle_tiles)
        valid_directions = [action for action in self.actions 
                           if self.get_next_pos(enemy_pos, action) not in obstacles 
                           and 0 <= self.get_next_pos(enemy_pos, action)[0] < map_width 
                           and 0 <= self.get_next_pos(enemy_pos, action)[1] < map_height]
        
        # Thêm thông tin về số ô tường liền kề (góc nấp)
        cover_count = sum(1 for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)] 
                         if (enemy_pos[0] + dx, enemy_pos[1] + dy) in self.wall_positions)
        
        # Thêm niềm tin từ search_belief_map vào trạng thái
        belief_value = self.search_belief_map[enemy_pos[0]][enemy_pos[1]]
        belief_category = 0 if belief_value < 2 else 1 if belief_value < 5 else 2  # Phân loại niềm tin
        
        return (relative_x, relative_y, player_visible, tuple(valid_directions), cover_count, belief_category)

    def get_reward(self, player, obstacle_tiles, old_pos, new_pos):
        reward = 0
        dist = math.sqrt((self.rect.centerx - player.rect.centerx) ** 2 + (self.rect.centery - player.rect.centery) ** 2)
        old_dist = math.sqrt((old_pos[0] * constants.TILE_SIZE - player.rect.centerx) ** 2 + (old_pos[1] * constants.TILE_SIZE - player.rect.centery) ** 2)

        # Thưởng nếu tiến gần người chơi
        if dist < old_dist:
            reward += (old_dist - dist) * 5
        else:
            reward -= (dist - old_dist) * 3  # Phạt nếu đi xa người chơi

        # Thưởng nếu nhìn thấy người chơi
        if self.ray_cast_player(player, obstacle_tiles):
            reward += 100

        # Thưởng nếu ở khu vực có niềm tin cao
        belief_value = self.search_belief_map[new_pos[0]][new_pos[1]]
        reward += belief_value * 10

        # Thưởng nếu ở gần tường (góc nấp)
        new_cover_count = sum(1 for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)] 
                            if (new_pos[0] + dx, new_pos[1] + dy) in self.wall_positions)
        reward += new_cover_count * self.cover_bonus

        # Phạt nếu lặp lại vị trí
        if new_pos in self.last_positions:
            idx = self.last_positions.index(new_pos)
            repeat_penalty = self.repeat_penalty_base * (len(self.last_positions) - idx) / len(self.last_positions)
            reward -= repeat_penalty
        else:
            reward += self.exploration_bonus  # Thưởng khi khám phá vị trí mới

        # Phạt nếu bị tấn công
        if self.hit:
            reward -= 50

        return reward

    def handle_patrol_qlearning(self, player, tile_grid, obstacle_tiles, map_width, map_height):
        print("ĐANG DÙNG Q-LEARNING ĐỂ TUẦN TRA")
        ai_dx, ai_dy = 0, 0
        enemy_pos = self.enemy_pos_csv

        if self.direction == Direction.NONE or self.step_count >= self.straight_steps:
            state = self.calculate_state(player, obstacle_tiles, map_width, map_height)
            old_pos = enemy_pos
            valid_directions = list(state[3])  # Lấy valid_directions từ trạng thái
            
            action = self.qlearn.choose_action(state, valid_directions)
            
            direction_map = {1: Direction.UP, 2: Direction.DOWN, 3: Direction.LEFT, 4: Direction.RIGHT}
            self.direction = direction_map[action]
            next_pos = self.get_next_pos(enemy_pos, action)
            
            obstacles = self.get_obstacle_positions(obstacle_tiles)
            if next_pos in obstacles or next_pos[0] < 0 or next_pos[0] >= map_width or next_pos[1] < 0 or next_pos[1] >= map_height:
                reward = -20
                self.direction = Direction.NONE
            else:
                self.step_count = 0

        if self.direction != Direction.NONE:
            if self.step_count < self.straight_steps:
                if self.direction == Direction.RIGHT: ai_dx = self.straight_dx
                elif self.direction == Direction.LEFT: ai_dx = -self.straight_dx
                elif self.direction == Direction.DOWN: ai_dy = self.straight_dy
                elif self.direction == Direction.UP: ai_dy = -self.straight_dy
                self.step_count += 1
            else:
                new_pos = self.get_next_pos(enemy_pos, self.last_action)
                state = self.calculate_state(player, obstacle_tiles, map_width, map_height)
                reward = self.get_reward(player, obstacle_tiles, old_pos, new_pos)
                self.last_positions.append(new_pos)
                if len(self.last_positions) > 10: self.last_positions.pop(0)
                if self.last_state is not None and self.last_action is not None:
                    self.qlearn.learn(self.last_state, self.last_action, state, reward)
                self.last_state = state
                self.last_action = action
                print(f"State: {state}, Reward: {reward}, Action: {action}")
                self.step_count = 0
                self.direction = Direction.NONE
                self.enemy_pos_csv = new_pos
                # Cập nhật visited_positions để đồng bộ với belief map
                self.visited_positions.add(new_pos)
                if len(self.visited_positions) > 20:
                    self.visited_positions.pop()

        return ai_dx, ai_dy
    
# ----------------------- HÀM XỬ LÝ VIỆC TẤN CÔNG HAY BỎ CHẠY-----------------------    

    def decide_behavior(self, dist):
        # safe_distance = 5 * constants.TILE_SIZE
        # # Chạy trốn nếu máu dưới 25% hoặc quá gần người chơi
        # if self.health < self.max_health * 0.25 or dist <= safe_distance:
        #     return "flee"
        # return "attack"
    
        safe_distance = 5 * constants.TILE_SIZE
        # Chạy trốn nếu máu dưới 60%, tấn công nếu trên 60% hoặc dưới 25% và khoảng cách nhỏ
        if self.health < self.max_health * 0.60:
            if self.health < self.max_health * 0.25 and dist <= safe_distance:
                return "attack"  # Liều mạng tấn công
            return "flee"  # Ưu tiên chạy trốn nếu máu thấp
        return "attack"

    def handle_flee(self, player, tile_grid, obstacle_tiles, map_width, map_height):
        """
        Xử lý việc chạy trốn và tìm vị trí nấp để hồi máu.
        Sử dụng A* để tìm đường đến vị trí an toàn với logic di chuyển giống handle_movement_attack.
        Hồi máu sau 2 giây khi đang chạy trốn.
        """
        # Khởi tạo thời gian chạy trốn nếu chưa có
        if self.flee_start_time is None:
            self.flee_start_time = pygame.time.get_ticks()

        safe_spot = self.find_safe_spot(player, tile_grid, obstacle_tiles, map_width, map_height)
        enemy_pos = self.get_map_pos()
        player_pos = player.get_map_pos()

        ai_dx = 0
        ai_dy = 0

        dist = math.sqrt(
            (self.rect.centerx - player.rect.centerx) ** 2 +
            (self.rect.centery - player.rect.centery) ** 2
        )

        # Hồi máu sau 2 giây khi đang chạy trốn
        current_time = pygame.time.get_ticks()
        if current_time - self.flee_start_time >= self.heal_cooldown and self.health < self.max_health:
            self.health = min(self.max_health, self.health + 10)
            print(f"Enemy healed to {self.health} while fleeing")
            self.flee_start_time = current_time  # Reset thời gian để hồi máu tiếp sau 2 giây nữa

        # Kiểm tra nếu đã đến vị trí nấp và hồi máu thêm nếu cần
        if enemy_pos == safe_spot and self.health < self.max_health:
            self.health = min(self.max_health, self.health + 10)
            print(f"Enemy healed to {self.health} at {safe_spot}")
            self.flee_start_time = current_time  # Reset thời gian khi đến safe spot

        # Nếu ngoài tầm phát hiện và không thấy người chơi, dừng lại
        if dist > self.radius and not self.ray_cast_player(player, obstacle_tiles):
            self.state = CharacterState.IDLE
            self.direction = Direction.NONE
            self.path = []
            self.flee_start_time = None  # Reset thời gian chạy trốn
            return 0, 0

        if self.direction != Direction.NONE:
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
                self.update_enemy_pos_csv(self.direction)
                self.direction = Direction.NONE

        if self.direction == Direction.NONE:
            if not self.path or (self.path and enemy_pos == self.path[-1]):
                print(f"Fleeing to safe spot using A*: {safe_spot}")
                (dx, dy), self.path = a_star(enemy_pos, safe_spot, tile_grid, obstacle_tiles, map_width, map_height, True)
                print(f"DEBUG PATH (Flee): {self.path}")
                if not self.path:
                    print("No path found, moving randomly")
                    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
                    random_direction = random.choice(directions)
                    next_step = (enemy_pos[0] + random_direction[0], enemy_pos[1] + random_direction[1])
                    dx, dy = random_direction
                else:
                    self.path.pop(0)
                    next_step = self.path[0] if self.path else enemy_pos
                    dx = next_step[0] - enemy_pos[0]
                    dy = next_step[1] - enemy_pos[1]
                    print(f"Next step (Flee): dx={dx}, dy={dy}")
            else:
                self.path.pop(0)
                next_step = self.path[0] if self.path else enemy_pos
                dx = next_step[0] - enemy_pos[0]
                dy = next_step[1] - enemy_pos[1]

            obstacles = self.get_obstacle_positions(obstacle_tiles)
            if (next_step[0], next_step[1]) in obstacles or next_step[0] < 0 or next_step[0] >= map_width or next_step[1] < 0 or next_step[1] >= map_height:
                self.direction = Direction.NONE
                self.path = []
                self.flee_start_time = None  # Reset thời gian chạy trốn
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
            else:
                self.direction = Direction.NONE

        return ai_dx, ai_dy
    
    
# ----------------------- HÀM XỬ LÝ VIỆC TUẦN TRA SỬ DỤNG THUẬT NIỀM TIN -----------------------

    def update_search_belief_map(self, player, obstacle_tiles):
        check_see = self.ray_cast_player(player, obstacle_tiles)
        player_pos = (player.rect.centerx // constants.TILE_SIZE, player.rect.centery // constants.TILE_SIZE)
        enemy_pos = self.enemy_pos_csv
        if check_see:
            self.lost_player_timer = 0  # reset timer khi thấy người chơi
            for x in range(self.map_width):
                    for y in range(self.map_height):
                        if (x, y) in self.wall_positions:
                            continue
                        self.search_belief_map[x][y] = 0

            for x in range(max(0, player_pos[0] - 2 * self.fov_radius), min(self.map_width, player_pos[0] + 2 * self.fov_radius)):
                for y in range(max(0, player_pos[1] - 2 * self.fov_radius), min(self.map_height, player_pos[1] + 2 * self.fov_radius)):
                    if (x, y) in self.wall_positions:
                        continue
                    # self.search_belief_map[x][y] = min(10.0, self.search_belief_map[x][y] + 5)
                    self.search_belief_map[x][y] +=5
            
            for x in range(max(0, player_pos[0] - self.fov_radius), min(self.map_width, player_pos[0] + self.fov_radius)):
                for y in range(max(0, player_pos[1] - self.fov_radius), min(self.map_height, player_pos[1] + self.fov_radius)):
                    if (x, y) in self.wall_positions:
                        continue
                    # self.search_belief_map[x][y] = min(10.0, self.search_belief_map[x][y] + 5)
                    self.search_belief_map[x][y] +=5
        else:
            self.lost_player_timer += 1  # tăng timer khi mất dấu người chơi
            fov_radius = 2
            for x in range(max(0, enemy_pos[0] - fov_radius), min(self.map_width, enemy_pos[0] + fov_radius)):
                for y in range(max(0, enemy_pos[1] - fov_radius), min(self.map_height, enemy_pos[1] + fov_radius)):
                    if (x, y) in self.wall_positions:
                        continue
                    self.search_belief_map[x][y] = 0
                    # self.search_belief_map[x][y] = max(0, self.search_belief_map[x][y], 0)
                    # if random.random() < 0.1:
                    #     self.search_belief_map[x][y] = min(3, self.search_belief_map[x][y], 0) + 1
            
            if self.lost_player_timer > self.lost_player_timeout // 2:  # Sau 300 frame
                for x in range(self.map_width):
                    for y in range(self.map_height):
                        if (x, y) not in self.wall_positions and (x, y) not in self.visited_positions:
                            # self.search_belief_map[x][y] = max(0, self.search_belief_map[x][y], 0)
                        # if random.random() < 0.1:
                        #     self.search_belief_map[x][y] = min(3, self.search_belief_map[x][y], 0) + 1
                            self.search_belief_map[x][y] = max(0.0, self.search_belief_map[x][y] + 0.01)  # Tăng nhẹ niềm tin ở vùng chưa đi

        # print("DEBUG: Belief Map:")
        # for i in range(self.map_width):
        #     print(f"Row {i}: {' '.join(f'{self.search_belief_map[i][j]:2.1f}' for j in range(self.map_height))}")
        
                    

    def decay_search_belief_map(self, obstacle_tiles):
        for x in range(self.map_width):
                for y in range(self.map_height):
                        self.search_belief_map[x][y] = self.search_belief_map[x][y] + 0.01
                        # self.search_belief_map[x][y] = self.search_belief_map[x][y] - 0.01

    def find_patroltarget_belief_map(self):
        best_score = -float("inf")
        best_pos = None
        enemy_pos = self.enemy_pos_csv
        max_belief = max(self.search_belief_map[x][y] 
                 for x in range(self.map_width) 
                 for y in range(self.map_height) 
                 if (x, y) not in self.wall_positions)

        max_distance = math.sqrt(self.map_width**2 + self.map_height**2)
        for x in range(self.map_width):
            for y in range(self.map_height):
                if (x,y) in self.wall_positions:
                    continue
                belief = self.search_belief_map[x][y]
                dist=math.sqrt((x-enemy_pos[0])**2 + (y-enemy_pos[1])**2)
                # Đếm số ô tường liền kề làm góc nấp
                # cover_count = sum(1 for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)] 
                #                 if (x + dx, y + dy) in self.wall_positions)
                # tính điểm: ưu tiên những điểm xa npc và có niềm tin cao
                score= belief/max_belief * 0.95 - dist/max_distance*0.05

                # score = (belief / max_belief * 0.95) - (dist / max_distance * 0.05) + (cover_count * 0.1)           
                if (x, y) in self.visited_positions:
                    score -= 0.5  # Phạt nếu đã đi qua
                # if (x, y) in self.visited_positions:
                #     visit_count = sum(1 for pos in self.visited_positions if pos == (x, y))  # Đếm số lần đã đi qua
                #     score -= 1.0 * visit_count  # Phạt mạnh hơn dựa trên số lần
                if score > best_score:
                    best_score = score
                    best_pos = (x, y)
                    
        # print(f"Diem to nhat: {best_score}, vi tri: {best_pos}, belief: {self.search_belief_map[best_pos[0]][best_pos[1]]}")
        if not best_pos or best_score < 0: # Nếu không tìm được vị trí tốt, chọn ngẫu nhiên          
            print("Di ngau nhien")
            valid_positions = [(x, y) for x in range(self.map_width) for y in range(self.map_height)
                            if (x, y) not in self.wall_positions and (x, y) != enemy_pos]
            if valid_positions:
                best_pos = random.choice(valid_positions)
            else:
                best_pos = enemy_pos
        print(f"NEW POS: {best_pos}")
        return best_pos

    def handle_patrol_belief(self, player, tile_grid, obstacle_tiles, map_width, map_height, screen_scroll, world):
        ai_dx, ai_dy = 0, 0
        enemy_pos = self.enemy_pos_csv
        print(f"Player đang ở: {player.get_map_pos()}")
        print(f"Enemy đang ở (CSV): {enemy_pos}")

        if self.patrol_cooldown > 0:
            self.patrol_cooldown -= 1
            return ai_dx, ai_dy
        
        # nếu còn hướng để di chuyển
        if self.direction != Direction.NONE:
            ai_dx, ai_dy = self.apply_direction()
            if ai_dx != 0 or ai_dy != 0:
                self.move(ai_dx, ai_dy, obstacle_tiles)
                self.visited_positions.add(enemy_pos)
                if len(self.visited_positions) > 50:  # giới hạn số vị trí đã đi qua
                    self.visited_positions.pop() # xóa vị trí cũ nhất
            self.patrol_cooldown = self.patrol_cooldown_duration  # Reset cooldown
            return ai_dx, ai_dy

        # path rỗng và hướng rỗng đi tìm vị trí tuần tra mới
        best_pos = self.find_patroltarget_belief_map()
        print(f"DEBUG Enemy: Tìm vị trí tuần tra mới: {best_pos}")
        self.directions_queue = get_path_a_star(enemy_pos, best_pos, tile_grid, self.wall_positions, map_width, map_height)
        # print(f"DEBUG Enemy: Danh sách hướng từ A*: {self.directions_queue}")
        
        # có path thì đi tìm hướng đi tiếp theo
        if self.directions_queue:
            self.direction = self.directions_queue.pop(0)
        else:
            self.direction = Direction.NONE
        self.patrol_cooldown = self.patrol_cooldown_duration
        return ai_dx, ai_dy

# ----------------------- HÀM XỬ LÝ VIỆC DI CHUYỂN GIỮA VỊ TRÍ DỮ LIỆU VÀ VỊ TRÍ PIXEL -----------------------
   
    def apply_direction(self):
        ai_dx, ai_dy = 0, 0
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
            self.update_enemy_pos_csv(self.direction)
            if self.directions_queue:
                self.direction = self.directions_queue.pop(0)
            else:
                self.direction = Direction.NONE
        return ai_dx, ai_dy

    def update_enemy_pos_csv(self, direction):
        x, y = self.enemy_pos_csv
        if direction == Direction.RIGHT:
            self.enemy_pos_csv = (x + 1, y)
        elif direction == Direction.LEFT:
            self.enemy_pos_csv = (x - 1, y)
        elif direction == Direction.DOWN:
            self.enemy_pos_csv = (x, y + 1)
        elif direction == Direction.UP:
            self.enemy_pos_csv = (x, y - 1)

# ----------------------- HÀM XỬ LÝ AI -----------------------

    def ai(self, player, tile_graph, tile_grid, obstacle_tiles, screen_scroll, fireball_image, map_width, map_height, world):
        self.rect.x += screen_scroll[0]
        self.rect.y += screen_scroll[1]
        self.handle_stun()

        if self.state == CharacterState.DEAD or self.state == CharacterState.STUNNED:
            return None

        self.update_search_belief_map(player, obstacle_tiles)
        fireball, dist = self.handle_attack(player, fireball_image,obstacle_tiles)

        if self.ray_cast_player(player, obstacle_tiles):
            self.player_search_trigger = True
            behavior = self.decide_behavior(dist)
            if behavior == "attack":
                self.state = CharacterState.ATTACKING if dist < constants.ATTACK_RANGE else CharacterState.MOVING
                # Sử dụng A* để đuổi người chơi khi nhìn thấy
                ai_dx, ai_dy = self.handle_movement_attack(player, tile_grid, obstacle_tiles, map_width, map_height)
                if ai_dx != 0 or ai_dy != 0:
                    self.move(ai_dx, ai_dy, obstacle_tiles)
            elif behavior == "flee":
                self.state = CharacterState.FLEELING
                ai_dx, ai_dy = self.handle_flee(player, tile_grid, obstacle_tiles, map_width, map_height)
                if ai_dx != 0 or ai_dy != 0:
                    self.move(ai_dx, ai_dy, obstacle_tiles)
        else:
            self.player_search_trigger = False
            self.state = CharacterState.PATROLLING
            self.decay_search_belief_map(obstacle_tiles)
            if self.patrol_style == "belief":
                ai_dx, ai_dy = self.handle_patrol_belief(player, tile_grid, obstacle_tiles, map_width, map_height, screen_scroll, world)
            elif self.patrol_style == "qlearning":
                ai_dx, ai_dy = self.handle_patrol_qlearning(player, tile_grid, obstacle_tiles, map_width, map_height)
            if ai_dx != 0 or ai_dy != 0:
                self.move(ai_dx, ai_dy, obstacle_tiles)
        return fireball
    


# ----------------------- HÀM XỬ LÝ TẤN CÔNG BẰNG THUẬT BFS,A*,BEAM SEARCH,BACKTRACK -----------------------

    def handle_movement_attack(self, player, tile_grid, obstacle_tiles,map_width, map_height):
        print("ATTACKKK")
        ai_dx = 0
        ai_dy = 0

        enemy_tile_x = self.rect.centerx // constants.TILE_SIZE
        enemy_tile_y = self.rect.centery // constants.TILE_SIZE
        enemy_pos = (int(enemy_tile_x), int(enemy_tile_y))

        # print(f"DEBUG ENEMY: {enemy_pos}")

        player_tile_x = player.rect.centerx // constants.TILE_SIZE
        player_tile_y = player.rect.centery // constants.TILE_SIZE
        player_pos = (int(player_tile_x), int(player_tile_y))
        dist = math.sqrt(
            (self.rect.centerx - player.rect.centerx) ** 2 +
            (self.rect.centery - player.rect.centery) ** 2
        )
        # Kiểm tra nếu người chơi ngoài vòng phát hiện và không được nhìn thấy
        if dist > self.radius and not self.ray_cast_player(player, obstacle_tiles):
            self.state = CharacterState.IDLE
            self.direction = Direction.NONE
            self.path = []
            return 0, 0

        if self.direction != Direction.NONE:
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
                self.update_enemy_pos_csv(self.direction)
                self.direction = Direction.NONE

        if self.direction == Direction.NONE:
            if not self.path or (self.path and (enemy_pos[0], enemy_pos[1]) == self.path[-1]):
                print(f"Using configured algorithm: {self.attack_algorithm}")
                if self.attack_algorithm == "a_star":
                    (dx, dy), self.path = a_star(enemy_pos, player_pos, tile_grid, obstacle_tiles, map_width, map_height, True)
                elif self.attack_algorithm == "bfs":
                    (dx, dy), self.path = bfs(enemy_pos, player_pos, tile_grid, obstacle_tiles, map_width, map_height)
                elif self.attack_algorithm == "beam_search":
                    (dx, dy), self.path = beam_search(enemy_pos, player_pos, tile_grid, obstacle_tiles, map_width, map_height)
                elif self.attack_algorithm == "backtracking":
                    (dx, dy), self.path = backtracking_search(enemy_pos, player_pos, tile_grid, obstacle_tiles, map_width, map_height)

                print(f"DEBUG PATH ({self.attack_algorithm}): {self.path}")
                if not self.path:
                    print("No path found, moving randomly")
                    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
                    random_direction = random.choice(directions)
                    next_step = (enemy_pos[0] + random_direction[0], enemy_pos[1] + random_direction[1])
                    dx, dy = random_direction
                else:
                    self.path.pop(0)
                    next_step = self.path[0] if self.path else enemy_pos
                    dx = next_step[0] - enemy_pos[0]
                    dy = next_step[1] - enemy_pos[1]
                    print(f"Next step ({self.attack_algorithm}): dx={dx}, dy={dy}")

            else:
                self.path.pop(0)
                next_step = self.path[0] if self.path else enemy_pos
                dx = next_step[0] - enemy_pos[0]
                dy = next_step[1] - enemy_pos[1]

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
            else:
                self.direction = Direction.NONE
        
        return ai_dx, ai_dy
    

# ----------------------- HÀM XỬ LÝ TRỐN -----------------------
    def find_safe_spot(self, player, tile_grid, obstacle_tiles, map_width, map_height):
        """
        Tìm vị trí nấp xa người chơi nhất và khuất tầm nhìn (gần tường).
        Sử dụng A* với heuristic ưu tiên khoảng cách xa và độ che chắn.
        """
        player_pos = player.get_map_pos()
        enemy_pos = self.get_map_pos()

        # Tạo danh sách các vị trí tiềm năng (gần tường và không nhìn thấy trực tiếp)
        potential_spots = []
        for x in range(map_width):
            for y in range(map_height):
                if (x, y) not in self.get_obstacle_positions(obstacle_tiles):
                    # Ưu tiên vị trí gần tường (ít nhất 1 ô tường liền kề)
                    cover_count = sum(1 for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]
                                    if (x + dx, y + dy) in self.wall_positions)
                    if cover_count > 0 and not self.ray_cast_player_from(player, (x * constants.TILE_SIZE, y * constants.TILE_SIZE), obstacle_tiles):
                        dist = math.hypot(x - player_pos[0], y - player_pos[1])
                        potential_spots.append(((x, y), dist + cover_count * 10))  # Ưu tiên xa và che chắn

        if not potential_spots:
            # Nếu không tìm thấy vị trí nấp, chọn vị trí xa nhất ngẫu nhiên
            valid_positions = [(x, y) for x in range(map_width) for y in range(map_height)
                             if (x, y) not in self.wall_positions and (x, y) != enemy_pos]
            if valid_positions:
                return max(valid_positions, key=lambda pos: math.hypot(pos[0] - player_pos[0], pos[1] - player_pos[1]))
            return enemy_pos

        # Chọn vị trí xa nhất và có che chắn tốt nhất
        best_spot = max(potential_spots, key=lambda x: x[1])[0]
        return best_spot
    
    def ray_cast_player_from(self, player, target_pos, obstacle_tiles):
        """
        Kiểm tra xem có đường thẳng nhìn thấy từ target_pos đến người chơi không.
        """
        line_of_sight = (target_pos, (player.rect.centerx, player.rect.centery))
        for obstacle in obstacle_tiles:
            if obstacle[1].clipline(line_of_sight):
                return False
        return True