# class để vẽ bản đồ
import constants
from item import Item
from character import Character

class World:
    def __init__(self):
        self.map_tiles = []
        self.obstacle_tiles = []
        self.exit_tile = None
        self.item_list = []
        self.player = None
        self.character_list = []

    def process_data(self, data,tile_list,item_images,mob_animations):
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                image = tile_list[tile]
                image_rect = image.get_rect()
                image_x = x * constants.TILE_SIZE
                image_y = y * constants.TILE_SIZE
                image_rect.center =(image_x,image_y)
                tile_data = [image,image_rect,image_x,image_y]
                # image_rect.x = image_x
                # image_rect.y = image_y

                if tile == 7:
                    self.obstacle_tiles.append(tile_data)
                elif tile == 8:
                    self.exit_tile = tile_data
                # thêm image data vào map_tiles
                elif tile == 9:
                    coin = Item(image_x,image_y,0,item_images[0])
                    self.item_list.append(coin)
                    tile_data[0] = tile_list[0]
                elif tile == 10:
                    potion = Item(image_x,image_y,1,[item_images[1]]) # vì máu chỉnh có 1 ảnh
                    self.item_list.append(potion)
                    tile_data[0] = tile_list[0]
                elif tile == 11:
                    player = Character(image_x,image_y,100,mob_animations,0,False,1)
                    self.player = player
                    tile_data[0] = tile_list[0]
                elif tile >= 12 and tile <= 16:
                    enemy = Character(image_x,image_y,100,mob_animations,tile - 11,False,1)
                    self.character_list.append(enemy)
                    tile_data[0] = tile_list[0] 
                elif tile == 17:
                    enemy = Character(image_x,image_y,100,mob_animations,6,True,2)
                    self.character_list.append(enemy)
                    tile_data[0] = tile_list[0]
                if tile >= 0:
                    self.map_tiles.append(tile_data)

    def update(self,screen_roll):
        for tile in self.map_tiles:
            tile[2] += screen_roll[0]
            tile[3] += screen_roll[1]
            tile[1].center = (tile[2],tile[3])
    
    def draw(self,screen):
        for title in self.map_tiles:
            screen.blit(title[0],title[1])