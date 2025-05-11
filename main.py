import pygame
import csv
import constants
import math
from pygame import mixer
from player import Player
from enemy import Enemy
from weapon import Weapon
from item import Item
from world import World
from button import Button

mixer.init()
pygame.init()

screen = pygame.display.set_mode((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
pygame.display.set_caption("Dungeon Crawler")

# biến FPS
clock = pygame.time.Clock()

# biến xác định level
level = 12

start_game = False
pause_game = False
level_complete = False
start_intro = False

# biến cho thanh cuộn màn hình
screen_scroll = [0,0] # cuộn x và cuộn y

# biến di chuyển
moving_right = False
moving_left = False
moving_up = False
moving_down = False

# font chữ
font = pygame.font.Font("assets/fonts/AtariClassic.ttf",20)

# hàm scale ảnh
def scale_img(image, scale):
    width = int(image.get_width() * scale)
    height = int(image.get_height() * scale)
    return pygame.transform.scale(image, (width, height))

# tải âm thanh
pygame.mixer.music.load('assets/audio/music.wav')
pygame.mixer.music.set_volume(0.3) # âm lượng nhạc nền
# pygame.mixer.music.play(-1,0.0,5000) # lặp lại nhạc nền
shot_fx = pygame.mixer.Sound('assets/audio/arrow_shot.mp3')
shot_fx.set_volume(0.5) # âm lượng âm thanh bắn
hit_fx = pygame.mixer.Sound('assets/audio/arrow_hit.wav')
hit_fx.set_volume(0.5) # âm lượng âm thanh bắn
coin_fx = pygame.mixer.Sound('assets/audio/coin.wav')
coin_fx.set_volume(0.5) # âm lượng âm thanh bắn
heal_fx = pygame.mixer.Sound('assets/audio/heal.wav')
heal_fx.set_volume(0.5) # âm lượng âm thanh bắn

# load button
start_img = scale_img(pygame.image.load('assets/images/buttons/button_start.png').convert_alpha(),constants.BUTTON_SCALE)
exit_img = scale_img(pygame.image.load('assets/images/buttons/button_exit.png').convert_alpha(),constants.BUTTON_SCALE)
restart_img = scale_img(pygame.image.load('assets/images/buttons/button_restart.png').convert_alpha(),constants.BUTTON_SCALE)
resume_img = scale_img(pygame.image.load('assets/images/buttons/button_resume.png').convert_alpha(),constants.BUTTON_SCALE)

# load máu
heart_empty = scale_img(pygame.image.load('assets/images/items/heart_empty.png').convert_alpha(),constants.ITEM_SCALE)
heart_half = scale_img(pygame.image.load('assets/images/items/heart_half.png').convert_alpha(),constants.ITEM_SCALE)
heart_full = scale_img(pygame.image.load('assets/images/items/heart_full.png').convert_alpha(),constants.ITEM_SCALE)

# load tiền
coin_images = []
for x in range(4):
    img = pygame.image.load(f'assets/images/items/coin_f{x}.png').convert_alpha()
    img = scale_img(img,constants.ITEM_SCALE)
    coin_images.append(img)

# load máu
red_potion = scale_img(pygame.image.load('assets/images/items/potion_red.png').convert_alpha(),constants.POTION_SCALE)

item_images = []
item_images.append(coin_images)
item_images.append(red_potion)

# load vũ khí
bow_image = scale_img(pygame.image.load('assets/images/weapons/bow.png').convert_alpha(),constants.WEAPON_SCALE)
arrow_image = scale_img(pygame.image.load('assets/images/weapons/arrow.png').convert_alpha(),constants.WEAPON_SCALE)
fireball_image = scale_img(pygame.image.load('assets/images/weapons/fireball.png').convert_alpha(),constants.FIREBALL_SCALE)

# tải bản đồ
tile_list = []
for x in range(constants.TILE_TYPES):
    img = pygame.image.load(f'assets/images/tiles/{x}.png').convert_alpha()
    img = pygame.transform.scale(img, (constants.TILE_SIZE, constants.TILE_SIZE))
    tile_list.append(img)

# load ảnh nhân vật
mob_animations = []
mob_types = ["elf", "imp", "skeleton", "goblin", "muddy", "tiny_zombie", "big_demon"]
animation_types = ["idle", "run"]
for mob in mob_types:
    animation_list = []
    for aninmation in animation_types:
        temp_list = []
        for i in range(4):
            img = pygame.image.load(f'assets/images/characters/{mob}/{aninmation}/{i}.png').convert_alpha()
            img = scale_img(img, constants.SCALE)
            temp_list.append(img)
        animation_list.append(temp_list)
    mob_animations.append(animation_list)

# hàm vẽ chữ lên màn hình
def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

# hàm hiển thị thông tin game
def draw_info():
    # vẽ khu vực hiển thị thông tin
    pygame.draw.rect(screen,constants.PANEL,(0,0,constants.SCREEN_WIDTH,50))
    pygame.draw.line(screen,constants.WHITE,(0,50),(constants.SCREEN_WIDTH,50))
    # hiển thị máu người chơi
    half_hearts_drawn = False
    for i in range(5):
        if player.health >= ((i+1)*20):
            screen.blit(heart_full,((10 + i * 50),0)) # padding trái 10, khoảng cách giữa các máu 50
        elif (player.health % 20 > 0) and half_hearts_drawn == False:
            screen.blit(heart_half,((10 + i * 50),0))
            half_hearts_drawn = True
        else:
            screen.blit(heart_empty,((10 + i * 50),0))
    # hiển thị level
    draw_text("LEVEL: " +str(level),font,constants.WHITE,constants.SCREEN_WIDTH/2,15)
    
    # hiển thị điểm
    draw_text(f'X{player.score}',font,constants.WHITE,constants.SCREEN_WIDTH - 100,15)



# hàm tạo lưới
def draw_grid():
    for x in range(30):
        pygame.draw.line(screen,constants.WHITE,(x * constants.TILE_SIZE,0),(x * constants.TILE_SIZE,constants.SCREEN_HEIGHT))
        pygame.draw.line(screen,constants.WHITE,(0,x * constants.TILE_SIZE),(constants.SCREEN_WIDTH,x * constants.TILE_SIZE))

# hàm reset level
def reset_level():
    for group in [damage_text_group, arrow_group, item_group, fireball_group]:
        group.empty()
    data =[] 
    for row in range(constants.ROWS):
        r = [-1] * constants.COLS
        data.append(r)
    return data


# class hiển thị damage
class DamageText(pygame.sprite.Sprite):
    def __init__(self, x, y, damage,color):
        pygame.sprite.Sprite.__init__(self)
        self.image = font.render(damage, True, color)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.counter = 0
    def update(self):
        # đặt lại vị trí theo thanh cuộn
        self.rect.x += screen_scroll[0]
        self.rect.y += screen_scroll[1]

        self.rect.y -= 1
        # xóa sau một vài giây
        self.counter += 1
        if self.counter > 30:
            self.kill()

# làm mờ màng hình tạo hiểu ứng chuyển màn
class ScreenFade():
    def __init__(self,direction,color,speed):
        self.direction = direction
        self.color = color
        self.speed = speed
        self.fade_counter = 0
    def fade(self):
        fade_complete = False
        self.fade_counter += self.speed
        if self.direction == 1:
            pygame.draw.rect(screen,self.color,(0 - self.fade_counter,0,constants.SCREEN_WIDTH//2,constants.SCREEN_HEIGHT)) # di chuyển từ trung tâm sang trái
            pygame.draw.rect(screen,self.color,(constants.SCREEN_WIDTH//2 + self.fade_counter,0,constants.SCREEN_WIDTH,constants.SCREEN_HEIGHT)) # từ trung tâm sang phải
            pygame.draw.rect(screen,self.color,(0,0 - self.fade_counter,constants.SCREEN_WIDTH,constants.SCREEN_HEIGHT//2)) # từ trung tâm lên trên
            pygame.draw.rect(screen,self.color,(0,constants.SCREEN_HEIGHT//2 + self.fade_counter,constants.SCREEN_WIDTH,constants.SCREEN_HEIGHT))
        if self.direction == 2: # theo chiều dọc
            pygame.draw.rect(screen,self.color,(0,0,constants.SCREEN_WIDTH,0 + self.fade_counter))
        if self.fade_counter >= constants.SCREEN_WIDTH:
            fade_complete = True
        return fade_complete
world_data =[]

for row in range(constants.ROWS):
    r = [-1] * constants.COLS
    world_data.append(r)

# đọc file csv
with open(f'levels/level{level}_data.csv',newline='') as csvfile:
    reader = csv.reader(csvfile,delimiter=',')
    for x,row in enumerate(reader):
        for y,tile in enumerate(row):
            world_data[x][y] = int(tile) 

world = World()
world.process_data(world_data,tile_list,item_images,mob_animations)

map_width = len(world_data[0])
map_height = len(world_data)

# tạo nhân vật
player = world.player

# tạo vũ khí
bow = Weapon(bow_image,arrow_image)

# nhận dữ liệu từ world data
enemy_list = world.character_list

damage_text_group = pygame.sprite.Group()   
arrow_group = pygame.sprite.Group()
item_group = pygame.sprite.Group()
fireball_group = pygame.sprite.Group()

score_coin = Item(constants.SCREEN_WIDTH - 115,23,0,coin_images,True)
item_group.add(score_coin)

# thêm vật phẩm vào từ file dữ liệu
for item in world.item_list:
    item_group.add(item)

# tạo hiệu ứng mờ
intro_fade = ScreenFade(1,constants.BLACK,4)
death_fade = ScreenFade(2,constants.PINK,4)

# tạo nút bấm
start_button = Button(constants.SCREEN_WIDTH//2 - 145,constants.SCREEN_HEIGHT//2 - 150,start_img)
exit_button = Button(constants.SCREEN_WIDTH//2 - 110,constants.SCREEN_HEIGHT//2 + 50,exit_img)
restart_button = Button(constants.SCREEN_WIDTH//2 - 175,constants.SCREEN_HEIGHT//2 - 50,restart_img)
resume_button = Button(constants.SCREEN_WIDTH//2 - 175,constants.SCREEN_HEIGHT//2 - 150,resume_img)

run = True
while run:
    #  điều khiển tốc độ khung hình
    clock.tick(constants.FPS)

    if start_game == False:
        screen.fill(constants.MENU_BG)
        if start_button.draw(screen):
            start_game = True
            start_intro = False
            # start_intro = True
        if exit_button.draw(screen):
            run = False
    else:
        if pause_game == True:
            screen.fill(constants.MENU_BG)
            if resume_button.draw(screen):
                pause_game = False 
            if exit_button.draw(screen):
                run = False
        else:
            screen.fill(constants.BG)

            # draw_grid()

            if player.alive == True:

                dx = 0 
                dy = 0
                if moving_right:
                    dx = constants.SPEED
                if moving_left:
                    dx = -constants.SPEED
                if moving_up:
                    dy = -constants.SPEED
                if moving_down:
                    dy = constants.SPEED

                # di chuyển nhân vật
                screen_scroll,level_complete= player.move(dx, dy,world.obstacle_tiles,world.exit_tile)

                # update các đối tượng trong game
                world.update(screen_scroll)

                # cập nhật quái vật
                for enemy in enemy_list:
                    if enemy.alive:
                        fireball = enemy.ai(player,world.weighted_tile_grid,world.tile_grid,world.obstacle_tiles,screen_scroll,fireball_image,map_width, map_height)
                        if fireball:
                            fireball_group.add(fireball)
                    enemy.update(item_group, coin_images, red_potion)

                # cập nhật nhân vật
                player.update()

                # cập nhật vũ khí
                arrow = bow.update(player)
                if arrow:
                    arrow_group.add(arrow)
                    shot_fx.play()
                for arrow in arrow_group:
                    damage,damage_pos = arrow.update(screen_scroll,world.obstacle_tiles,enemy_list)
                    if damage:
                        damage_text = DamageText(damage_pos.centerx,damage_pos.centery,str(damage),constants.RED)
                        damage_text_group.add(damage_text)
                        hit_fx.play()
                
                damage_text_group.update()
                fireball_group.update(screen_scroll,player)
                item_group.update(screen_scroll,player,coin_fx,heal_fx)

            world.draw(screen)

            # vẽ nhân vật
            player.draw(screen)

            # vẽ quái vật
            for enemy in enemy_list:
                enemy.draw(screen)

            # vẽ vũ khí
            bow.draw(screen)
            for arrow in arrow_group:
                arrow.draw(screen)

            for fireball in fireball_group:
                fireball.draw(screen)

            # vẽ damage
            damage_text_group.draw(screen)

            # vẽ item
            item_group.draw(screen)

            # hiển thị thông tin game
            draw_info() 

            # vẽ lại đề đè lên panel thông tin
            score_coin.draw(screen) # phải thêm phương thức draw vì nếu không thêm thì draw chỉ áp dụng cho Group
            
            if level_complete:
                start_intro = True
                level += 1
                world_data = reset_level()
                with open(f'levels/level{level}_data.csv',newline='') as csvfile:
                    reader = csv.reader(csvfile,delimiter=',')
                    for x,row in enumerate(reader):
                        for y,tile in enumerate(row):
                            world_data[x][y] = int(tile) 
                world = World()
                world.process_data(world_data,tile_list,item_images,mob_animations)
                # ghi đè lại các thông tin mới lên thông tin cũ
                temp_hp = player.health
                temp_score = player.score
                player = world.player
                player.health = temp_hp
                player.score = temp_score
                enemy_list = world.character_list
                score_coin = Item(constants.SCREEN_WIDTH - 115,23,0,coin_images,True)
                item_group.add(score_coin)
                for item in world.item_list:
                    item_group.add(item)
            
            # vẽ hiệu ứng mờ
            if start_intro == True:
                if intro_fade.fade():
                    start_intro = False
                    intro_fade.fade_counter = 0
            
            # vẽ hiệu ứng chết
            if player.alive == False:
                if death_fade.fade():
                    if restart_button.draw(screen):
                        death_fade.fade_counter = 0
                        start_intro = True
                        world_data = reset_level()
                        with open(f'levels/level{level}_data.csv',newline='') as csvfile:
                            reader = csv.reader(csvfile,delimiter=',')
                            for x,row in enumerate(reader):
                                for y,tile in enumerate(row):
                                    world_data[x][y] = int(tile) 
                        world = World()
                        world.process_data(world_data,tile_list,item_images,mob_animations)
                        # ghi đè lại các thông tin mới lên thông tin cũ
                        temp_score = player.score
                        player = world.player
                        player.score = temp_score
                        enemy_list = world.character_list
                        score_coin = Item(constants.SCREEN_WIDTH - 115,23,0,coin_images,True)
                        item_group.add(score_coin)
                        for item in world.item_list:
                            item_group.add(item)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        # khi nhấn nút di chuyển
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                moving_right = True
            if event.key == pygame.K_LEFT:
                moving_left = True
            if event.key == pygame.K_UP :
                moving_up = True
            if event.key == pygame.K_DOWN:
                moving_down = True
            if event.key == pygame.K_ESCAPE:
                pause_game = True
        # khi thả nút di chuyển
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_RIGHT:
                moving_right = False
            if event.key == pygame.K_LEFT:
                moving_left = False
            if event.key == pygame.K_UP:
                moving_up = False
            if event.key == pygame.K_DOWN:
                moving_down = False
    pygame.display.update()

pygame.quit()
