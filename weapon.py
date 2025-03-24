# Class Tạo vũ khí cho người chơi
import pygame
import math
import constants
import random

class Weapon():
    def __init__(self,image,arrow_image):
        self.original_image = image
        self.angle = 0
        self.arrow_image = arrow_image
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect()
        self.fired = False # kiểm tra xem đã bắn chưa
        self.last_shot = pygame.time.get_ticks() # không có người chơi Spam

    def update(self,player):
        shot_cooldown = 300 # bắn sau 300ms

        self.rect.center = player.rect.center

        arrow = None

        pos = pygame.mouse.get_pos()
        # tính toán vị trí chuột so với tâm của vũ khí
        x_dist = pos[0] - player.rect.centerx
        y_dist = -(pos[1] - player.rect.centery) # nếu ra kết quả âm cho biết chuột ở dưới tâm
        self.angle = math.degrees(math.atan2(y_dist, x_dist))

        # bắn mũi tên
        if pygame.mouse.get_pressed()[0] and self.fired == False and (pygame.time.get_ticks() - self.last_shot >= shot_cooldown):
            arrow = Arrow(self.arrow_image,player.rect.centerx,player.rect.centery,self.angle)
            self.fired = True
            self.last_shot = pygame.time.get_ticks()
        # reset bắn
        if pygame.mouse.get_pressed()[0] == False:
            self.fired = False
        return arrow
   
    def draw(self,screen):
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        screen.blit(self.image, ((self.rect.centerx - self.image.get_width() // 2), (self.rect.centery - self.image.get_height() // 2)))

class Arrow(pygame.sprite.Sprite):
    def __init__(self,image, x, y, angle):
        pygame.sprite.Sprite.__init__(self)
        self.original_image = image
        self.angle = angle
        self.image = pygame.transform.rotate(self.original_image, angle - 90) # vì hình ảnh ban đầu đã quay 90 độ do Sprite
        self.rect = self.image.get_rect()
        self.rect.center = (x,y)
        # tính toán tốc độ theo trục x và y dựa vào góc bắn
        self.dx = math.cos(math.radians(angle)) * constants.ARROW_SPEED
        self.dy = -(math.sin(math.radians(angle)) * constants.ARROW_SPEED)
    
    def update(self,screen_scroll,enemy_list):
        damage = 0
        damage_pos = None

        # định vị lại tốc độ 
        self.rect.x += screen_scroll[0] + self.dx
        self.rect.y += screen_scroll[1] + self.dy

        # kiểm tra xem cung ra khỏi m   àn hình hay chưa
        if self.rect.right < 0 or self.rect.left > constants.SCREEN_WIDTH or self.rect.bottom < 0 or self.rect.top > constants.SCREEN_HEIGHT:
            self.kill() # hàm trong Sprite để xóa đối tượng khỏi Group
        # kiểm tra va chạm với quái vật
        for enemy in enemy_list:
            if enemy.rect.colliderect(self.rect) and enemy.alive:
                damage = 10 + random.randint(-5,5)
                damage_pos = enemy.rect
                enemy.health -= damage
                self.kill()
                break   
        return damage,damage_pos
        
    def draw(self, screen):
        screen.blit(self.image, ((self.rect.centerx - self.image.get_width() // 2), (self.rect.centery - self.image.get_height() // 2)))