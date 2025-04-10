import pygame 

class Button():
    def __init__(self,x,y,image):
        self.image = image
        self.rect = image.get_rect()
        self.rect.topleft = (x,y)
    def draw(self,screen):
        action = False
        pos = pygame.mouse.get_pos()
        # kiểm tra xem chuột di chuyển qua nút chưa
        if self.rect.collidepoint(pos):
            # kiểm tra xem nhấn nút chưa
            if pygame.mouse.get_pressed()[0]:
                action = True
        screen.blit(self.image,self.rect)
        return action