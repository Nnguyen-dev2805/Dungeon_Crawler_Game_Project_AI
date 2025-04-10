import pygame
import constants
import weapon
import math
from collections import deque


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
        self.alive = True
        self.hit = False
        self.last_hit = pygame.time.get_ticks()
        self.last_attack = pygame.time.get_ticks()
        self.stunned = False

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = pygame.Rect(
            0, 0, constants.TILE_SIZE * size, constants.TILE_SIZE * size
        )
        self.rect.center = (x, y)

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
                # kiểm tra xem đang đi về hướng nào
                if dx > 0:
                    self.rect.right = obstacle[1].left  # đẩy lại về mép tường
                if dx < 0:
                    self.rect.left = obstacle[1].right
        # kiểm tra lên xuống
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

    def bfs(self, start, goal, obstacle_tiles):
        # print(f"[BFS] Bot ở {start} đang tìm đường đến {goal}")
        obstacles = set(
            (obstacle[1].x // constants.TILE_SIZE, obstacle[1].y // constants.TILE_SIZE)
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
        # Kiểm tra nếu goal không tồn tại trong parent
        # tưc nhân vật bị bao vây bởi tường
        if goal not in parent:
            return 0, 0  # Không có đường đi
    
        # truy vết đường đi từ goal về start
        path = []
        current = goal
        while current is not None:
            path.append(current)
            current = parent[current]
        path.reverse()
        # nếu có đường đi, trả về bước đầu tiên
        if len(path) > 1:
            next_step = path[1]
            dx = next_step[0] - start[0]
            dy = next_step[1] - start[1]
            return dx, dy
        return 0, 0  # Không có đường đi

    # dùng cho di chuyển quái vật
    def ai(self, player, obstacle_tiles, screen_scroll, fireball_image):
        """
        AI của kẻ thù, sử dụng BFS để tìm đường.
        :param player: Đối tượng người chơi.
        :param obstacle_tiles: Danh sách các chướng ngại vật.
        :param screen_scroll: Dịch chuyển màn hình.
        :param fireball_image: Hình ảnh quả cầu lửa.
        """
        clipped_line = ()

        stun_cooldown = 100

        # ai_dx = 0
        # ai_dy = 0

        fireball = None

        self.rect.x += screen_scroll[0]
        self.rect.y += screen_scroll[1]

        # Vị trí hiện tại của enemy và player
        enemy_pos = (self.rect.centerx // constants.TILE_SIZE, self.rect.centery // constants.TILE_SIZE)
        player_pos = (player.rect.centerx // constants.TILE_SIZE, player.rect.centery // constants.TILE_SIZE)

        # line_of_sight = (
        #     (self.rect.centerx, self.rect.centery),
        #     (player.rect.centerx, player.rect.centery),
        # )

        # for obstacle in obstacle_tiles:
        #     if obstacle[1].clipline(
        #         line_of_sight
        #     ):  # kiểm tra xem đường nhìn có bị chặn bởi chướng ngại vật không
        #         clipped_line = obstacle[1].clipline(
        #             line_of_sight
        #         )  # nếu có thì sẽ nhận giá trị

        # dist = math.sqrt(
        #     ((self.rect.centerx - player.rect.centerx) ** 2)
        #     + ((self.rect.centery - player.rect.centery) ** 2)
        # )

        # if not clipped_line and dist > constants.RANGE:  # nếu không có chướng ngại vật
        #     # kẻ thù ở bên phải người chơi
        #     if self.rect.centerx > player.rect.centerx:
        #         ai_dx = -constants.ENEMY_SPEED
        #     if self.rect.centerx < player.rect.centerx:
        #         ai_dx = constants.ENEMY_SPEED
        #     if self.rect.centery > player.rect.centery:
        #         ai_dy = -constants.ENEMY_SPEED
        #     if self.rect.centery < player.rect.centery:
        #         ai_dy = constants.ENEMY_SPEED
        ai_dx, ai_dy = self.bfs(enemy_pos, player_pos, obstacle_tiles)
        ai_dx *= constants.ENEMY_SPEED
        ai_dy *= constants.ENEMY_SPEED

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

    def update(self):
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

    def update_action(self, new_action):
        # kiểm tra hành động mới có khác với hành động cũ không
        if new_action != self.action:
            self.action = new_action
            # cập nhật lại frame index nếu đang dừng đột nhiên chạy
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def draw(self, screen):
        flipped_image = pygame.transform.flip(self.image, self.flip, False)
        if self.char_type == 0:
            screen.blit(
                self.image,
                (self.rect.x, self.rect.y - constants.SCALE * constants.OFFSET),
            )
        else:
            screen.blit(flipped_image, self.rect)
