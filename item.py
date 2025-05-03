# class để thêm vật phẩm
import pygame

class Item(pygame.sprite.Sprite):
    # thêm biến dummy để tránh đồng tiền trên thanh panel di chuyển
    def __init__(self, x, y,item_type,animation_list,dummy_coin = False):
        pygame.sprite.Sprite.__init__(self)
        self.item_type = item_type # 0: coin , 1: heath potion
        self.animation_list = animation_list
        self.frame_index = 0
        self.update_time = pygame.time.get_ticks()
        self.image = self.animation_list[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.dummy_coin = dummy_coin
        
        # Thêm các thuộc tính cho hiệu ứng rơi
        self.velocity_y = -8  # vận tốc lên
        self.gravity = 0.5     # trọng lực
        self.bounce_speed = 8  # tốc độ nảy
        self.max_bounces = 2    # số lần nảy tối đa
        self.bounce_count = 0   # Đếm số lần đã nảy
        self.original_y = y     # Vị trí y ban đầu
        self.is_falling = True  # Trạng thái đang rơi

    def update(self,screen_scroll,player,coin_fx,heal_fx):
        # Hiệu ứng rơi và nảy
        if not self.dummy_coin and self.bounce_count < self.max_bounces:
            # Áp dụng trọng lực
            self.velocity_y += self.gravity
            self.rect.y += self.velocity_y
            
            # Kiểm tra nảy khi chạm đất
            if self.rect.y >= self.original_y:
                self.rect.y = self.original_y
                if self.is_falling:  # Chỉ nảy khi đang rơi xuống
                    self.velocity_y = -self.bounce_speed
                    self.bounce_count += 1
                    # Giảm tốc độ nảy sau mỗi lần
                    self.bounce_speed *= 0.5
                self.is_falling = False
            else:
                self.is_falling = True

        # định vị lại vị trí của vật phẩm theo thanh cuộn
        if self.dummy_coin == False:
            self.rect.x += screen_scroll[0]
            self.rect.y += screen_scroll[1]

        # kiểm tra xem nhân vật có chạm vào item không
        if self.rect.colliderect(player.rect):
            if self.item_type == 0:
                player.score += 1
                coin_fx.play()
            elif self.item_type == 1:
                player.health += 10 
                if player.health > 100:
                    player.health = 100
                heal_fx.play()
            self.kill()

        animation_cooldown = 150

        self.image = self.animation_list[self.frame_index]

        if pygame.time.get_ticks() - self.update_time >= animation_cooldown:
            self.frame_index += 1
            self.update_time = pygame.time.get_ticks()

        if self.frame_index >= len(self.animation_list):
            self.frame_index = 0
    
    def draw(self,screen):
        screen.blit(self.image,self.rect)