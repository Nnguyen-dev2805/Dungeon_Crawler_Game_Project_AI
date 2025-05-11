# class để vẽ bản đồ
import constants
from item import Item
from player import Player
from enemy import Enemy
import pygame

class World:
    def __init__(self):
        self.map_tiles = []
        self.obstacle_tiles = []
        self.exit_tile = None
        self.item_list = []
        self.player = None
        self.character_list = []
        self.tile_graph = None
        self.tile_grid = None
        self.weighted_tile_grid = None
    
    def process_data(self, data,tile_list,item_images,mob_animations):
        map_width = len(data[0])
        map_height = len(data)
        self.tile_graph = TileGraph(map_width, map_height)
        self.tile_grid = TileGrid(map_width, map_height)
        self.weighted_tile_grid = WeightedTileGrid(map_width, map_height)
        
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                image = tile_list[tile]
                image_rect = image.get_rect()
                image_x = x * constants.TILE_SIZE
                image_y = y * constants.TILE_SIZE
                # image_x = x * constants.TILE_SIZE + constants.TILE_SIZE / 2
                # image_y = y * constants.TILE_SIZE + constants.TILE_SIZE / 2
                image_rect.center =(image_x,image_y)
                tile_data = [image,image_rect,image_x,image_y]
                if tile == 7:
                    self.obstacle_tiles.append(tile_data)
                elif tile == 8:
                    self.exit_tile = tile_data
                elif tile == 9:
                    coin = Item(image_x,image_y,0,item_images[0])
                    self.item_list.append(coin)
                    tile_data[0] = tile_list[0]
                elif tile == 10:
                    potion = Item(image_x,image_y,1,[item_images[1]])
                    self.item_list.append(potion)
                    tile_data[0] = tile_list[0]
                elif tile == 11:
                    player = Player(image_x,image_y,100,mob_animations,1)
                    self.player = player
                    tile_data[0] = tile_list[0]
                elif tile >= 12 and tile <= 16:
                    enemy = Enemy(image_x,image_y,100,mob_animations,tile - 11,False,1)
                    self.character_list.append(enemy)
                    tile_data[0] = tile_list[0] 
                elif tile == 17:
                    enemy = Enemy(image_x,image_y,100,mob_animations,6,True,2)
                    self.character_list.append(enemy)
                    tile_data[0] = tile_list[0]
                if tile >= 0:
                    self.map_tiles.append(tile_data)

        dungeon_dict = {(x, y): {"tile_id": tile} for y, row in enumerate(data) for x, tile in enumerate(row)}
        self.tile_graph.get_dungeon_edges(dungeon_dict, wall_tile_id=7)
        self.tile_grid.getwalls(self.obstacle_tiles)
        self.weighted_tile_grid.getwalls(self.obstacle_tiles)
    

    def update(self,screen_roll):
        for tile in self.map_tiles:
            tile[2] += screen_roll[0]
            tile[3] += screen_roll[1]
            tile[1].center = (tile[2],tile[3])
    
    def draw(self,screen):
        
        for tile in self.map_tiles:
            screen.blit(tile[0],tile[1])
            # pygame.draw.rect(screen, (255, 0, 0), tile[1], 2)

        for tile in self.obstacle_tiles:
            pygame.draw.rect(screen, (255, 0, 0), tile[1], 2)
class TileGraph:
    """
    Đồ thị vô hướng với các nút là ô 
    Các cạnh là các đường đi giữa các ô không phải là tường liền kề
    """
    def __init__(self,map_width,map_height):
        self.edges = {}
        self.map_width = map_width
        self.map_height = map_height
        for col in range(map_width):
            for row in range(map_height):
                self.edges[(col,row)] = [] # chứa các node làm key(col,row) làm key và list các node láng giềng làm value
    
    def get_dungeon_edges(self,dungeon,wall_tile_id):
        """
        Xây dựng đồ thị từ bản đồ dungeon.
        Args:
            dungeon: 2D array hoặc dictionary đại diện cho bản đồ.
            wall_tile_id: ID đại diện cho ô tường.
        Độ phức tạp thời gian là O(2|E|)
        """
        for col in range(self.map_width):
            for row in range(self.map_height):
                curr_tile = dungeon[(col,row)]
                if curr_tile["tile_id"] != wall_tile_id:
                    # kiểm tra ô bên phải
                    if col + 1 < self.map_width and dungeon[(col+1,row)]["tile_id"] != wall_tile_id:
                        self.edges[(col,row)].append((col+1,row))
                        self.edges[(col+1,row)].append((col,row))
                    # Kiểm tra ô bên dưới
                    if row + 1 < self.map_height and dungeon[(col, row + 1)]["tile_id"] != wall_tile_id:
                        self.edges[(col, row)].append((col, row + 1))
                        self.edges[(col, row + 1)].append((col, row))
    
    def neighbors(self,index):
        """
        Lấy danh sách các ô láng giềng của một ô.
        Args:
            index: Tọa độ của ô (x, y).
        Returns:
            List các ô láng giềng.
        """
        return self.edges.get(index, []) # trả về list các ô có thể kết nối được

class TileGrid:
    """
    Lớp đồ thị dựa trên lưới để biểu diễn các ô, dùng cho BFS.
    Args:
        width (int): chiều rộng bản đồ
        height (int): chiều cao bản đồ
    """
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.walls = []

    def getwalls(self, obstacle_tiles):
        """
        Lấy danh sách tọa độ các ô tường từ obstacle_tiles.
        Time Complexity: O(|V|)
        Args:
            obstacle_tiles: List các ô tường từ World.obstacle_tiles
        """
        for tile in obstacle_tiles:
            col = tile[2] // constants.TILE_SIZE
            row = tile[3] // constants.TILE_SIZE
            self.walls.append((col, row))

    def constrained(self, index):
        (x, y) = index
        return 0 <= x < self.width and 0 <= y < self.height

    def notwall(self, index):
        return index not in self.walls

    def neighbors(self, index):
        (x, y) = index
        results = [(x + 1, y), (x, y - 1), (x - 1, y), (x, y + 1)]
        if (x + y) % 2 == 0:
            results.reverse()
        results = [r for r in results if self.constrained(r) and self.notwall(r)]
        return results

class WeightedTileGrid(TileGrid):
    """
    Lớp đồ thị dựa trên lưới có trọng số, kế thừa từ TileGrid.
    Dùng cho các thuật toán tìm đường có trọng số như Dijkstra.
    """
    def __init__(self, width, height):
        super().__init__(width, height)
        self.weights = {}

    def cost(self, start, end):
        """
        Trả về chi phí di chuyển từ start đến end. Mặc định là 1.
        """
        return self.weights.get(end, 1)