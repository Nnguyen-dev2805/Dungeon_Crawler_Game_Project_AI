import pygame
import csv
import constants
from character import Character
from weapon import Weapon
from item import Item
from world import World

pygame.init()

screen = pygame.display.set_mode((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
pygame.display.set_caption("Dungeon Crawler")

# biến FPS
clock = pygame.time.Clock()

# biến xác định level
level = 1

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

# hàm tạo lưới
def draw_grid():
    for x in range(30):
        pygame.draw.line(screen,constants.WHITE,(x * constants.TILE_SIZE,0),(x * constants.TILE_SIZE,constants.SCREEN_HEIGHT))
        pygame.draw.line(screen,constants.WHITE,(0,x * constants.TILE_SIZE),(constants.SCREEN_WIDTH,x * constants.TILE_SIZE))

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

# tạo nhân vật
player = world.player

# tạo vũ khí
bow = Weapon(bow_image,arrow_image)

# nhận dữ liệu từ world data
enemy_list = world.character_list

damage_text_group = pygame.sprite.Group()   
arrow_group = pygame.sprite.Group()
item_group = pygame.sprite.Group()

score_coin = Item(constants.SCREEN_WIDTH - 115,23,0,coin_images,True)
item_group.add(score_coin)

# thêm vật phẩm vào từ file dữ liệu
for item in world.item_list:
    item_group.add(item)

run = True
while run:
    #  điều khiển tốc độ khung hình
    clock.tick(constants.FPS)

    screen.fill(constants.BG)

    # draw_grid()

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
    screen_scroll = player.move(dx, dy,world.obstacle_tiles)

    # update các đối tượng trong game
    world.update(screen_scroll)

    # cập nhật quái vật
    for enemy in enemy_list:
        enemy.ai(screen_scroll)
        enemy.update()

    # cập nhật nhân vật
    player.update()

    # cập nhật vũ khí
    arrow = bow.update(player)
    if arrow:
        arrow_group.add(arrow)
    for arrow in arrow_group:
        damage,damage_pos = arrow.update(screen_scroll,enemy_list)
        if damage:
            damage_text = DamageText(damage_pos.centerx,damage_pos.centery,str(damage),constants.RED)
            damage_text_group.add(damage_text)
    
    damage_text_group.update()
    item_group.update(screen_scroll,player)

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

    # vẽ damage
    damage_text_group.draw(screen)

    # vẽ item
    item_group.draw(screen)

    # hiển thị thông tin game
    draw_info() 

    # vẽ lại đề đè lên panel thông tin
    score_coin.draw(screen) # phải thêm phương thức draw vì nếu không thêm thì draw chỉ áp dụng cho Group
    

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
