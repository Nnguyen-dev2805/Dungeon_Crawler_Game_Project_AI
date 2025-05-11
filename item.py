# class để thêm vật phẩm
import pygame
import random

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
        
        # Drop animation properties
        self.is_dropping = not dummy_coin  # Only drop animation for non-dummy items
        self.drop_start_y = y - 30  # Start 50 pixels above final position
        self.drop_speed = 3
        self.rect.y = self.drop_start_y

    def update(self,screen_scroll,player,coin_fx,heal_fx):
        # Handle drop animation
        if self.is_dropping:
            target_y = self.drop_start_y + 30  # Final position
            if self.rect.y < target_y:
                self.rect.y += self.drop_speed
            else:
                self.is_dropping = False
                self.rect.y = target_y

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