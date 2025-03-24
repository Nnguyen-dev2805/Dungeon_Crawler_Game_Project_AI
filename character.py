import pygame
import constants
import math


class Character:
    def __init__(self, x, y, health, mob_animations, char_type,boss,size):
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
        self.stunned = False

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = pygame.Rect(0, 0, constants.TILE_SIZE* size, constants.TILE_SIZE * size)
        self.rect.center = (x, y)

    def move(self, dx, dy,obstacle_tiles):
        screen_scroll = [0,0]

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
                    self.rect.right = obstacle[1].left # đẩy lại về mép tường
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
            # di chuyển sang trái hoặc phải
            if self.rect.right > (constants.SCREEN_WIDTH - constants.SCROLL_THRESH):
                screen_scroll[0] = (constants.SCREEN_WIDTH - constants.SCROLL_THRESH) - self.rect.right
                self.rect.right = (constants.SCREEN_WIDTH - constants.SCROLL_THRESH)
            if self.rect.left < constants.SCROLL_THRESH:
                screen_scroll[0] = constants.SCROLL_THRESH - self.rect.left
                self.rect.left = constants.SCROLL_THRESH
            # di chuyển lên trên hoặc xuống
            if self.rect.bottom > (constants.SCREEN_HEIGHT - constants.SCROLL_THRESH):
                screen_scroll[1] = (constants.SCREEN_HEIGHT - constants.SCROLL_THRESH) - self.rect.bottom
                self.rect.bottom = (constants.SCREEN_HEIGHT - constants.SCROLL_THRESH)
            if self.rect.top < constants.SCROLL_THRESH:
                screen_scroll[1] = constants.SCROLL_THRESH - self.rect.top
                self.rect.top = constants.SCROLL_THRESH

        return screen_scroll

    # dùng cho di chuyển quái vật
    def ai(self,player,obstacle_tiles,screen_scroll):
        clipped_line = ()
        
        stun_cooldown = 100

        ai_dx = 0
        ai_dy = 0

        self.rect.x += screen_scroll[0]
        self.rect.y += screen_scroll[1]

        line_of_sight =((self.rect.centerx,self.rect.centery),(player.rect.centerx,player.rect.centery))

        for obstacle in obstacle_tiles:
            if obstacle[1].clipline(line_of_sight): # kiểm tra xem đường nhìn có bị chặn bởi chướng ngại vật không
                clipped_line = obstacle[1].clipline(line_of_sight) # nếu có thì sẽ nhận giá trị
        
        dist = math.sqrt(((self.rect.centerx - player.rect.centerx)**2)+((self.rect.centery - player.rect.centery)**2))

        if not clipped_line and dist > constants.RANGE: # nếu không có chướng ngại vật
            # kẻ thù ở bên phải người chơi
            if self.rect.centerx > player.rect.centerx:
                ai_dx = -constants.ENEMY_SPEED
            if self.rect.centerx < player.rect.centerx:
                ai_dx = constants.ENEMY_SPEED
            if self.rect.centery > player.rect.centery:
                ai_dy = -constants.ENEMY_SPEED
            if self.rect.centery < player.rect.centery:
                ai_dy = constants.ENEMY_SPEED
        if self.alive:
            if not self.stunned:
                self.move(ai_dx,ai_dy,obstacle_tiles)

                # attck player
                if dist < constants.ATTACK_RANGE and player.hit == False:
                    player.health -= 10
                    player.hit = True
                    player.last_hit = pygame.time.get_ticks()

            # check if hit
            if self.hit == True:
                self.hit = False
                self.last_hit = pygame.time.get_ticks()
                self.stunned = True
                self.running = False
                self.update_action(0)
            
            if (pygame.time.get_ticks() - self.last_hit)> stun_cooldown:
                self.stunned = False


    def update(self):
        # kiểm tra xem nhân vật còn sống không
        if self.health <= 0:
            self.health = 0
            self.alive = False  

        # cập nhật thời gian nhận sát thương
        hit_cooldown = 1000
        if self.char_type == 0:
            if self.hit == True and (pygame.time.get_ticks() - self.last_hit > hit_cooldown):
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
        pygame.draw.rect(screen, constants.RED, self.rect, 1)
