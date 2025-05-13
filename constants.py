# Lưu các biến hằng số của game

FPS = 60  # tốc độ khung hình
# SCREEN_WIDTH = 800
# SCREEN_HEIGHT = 600
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
SCALE = 3 # tỉ lệ cho hình ảnh trong game
WEAPON_SCALE = 1.5 # tỉ lệ cho vũ khí
FIREBALL_SCALE = 1 # tỉ lệ cho quả cầu lửa
ITEM_SCALE = 3 # tỉ lệ cho item
POTION_SCALE = 2 # tỉ lệ cho bình máu
BUTTON_SCALE = 1 # tỉ lệ cho nút bấm
SPEED = 5
FIREBALL_SPEED = 4 
ARROW_SPEED = 10 # tốc độ của mũi tên
ENEMY_SPEED = 4
OFFSET = 12 # điều chỉnh khoảng cách giữa nhân vật và vũ khí
TILE_SIZE = 16 * SCALE
TILE_TYPES = 18 # số loại tile
# ROWS = 150
# COLS = 150
ROWS = 150
COLS = 150
SCROLL_THRESH = 200
RANGE = 50
ATTACK_RANGE = 60


WHITE = (255, 255, 255)
PINK =(235,65,54)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BG = (40, 25, 25)
MENU_BG = (130, 0, 0) # màu nền của menu
PANEL = (50, 50, 50) # màu nền của panel


# constants.py
MINIMAP_TILE_SIZE = 4  # Kích thước mỗi ô trong minimap (4x4 pixel)
MINIMAP_POS_X = 10     # Vị trí X của minimap (góc trái dưới)
MINIMAP_POS_Y = 10     # Vị trí Y (góc trái dưới, sẽ điều chỉnh dựa trên map_height)
# MINIMAP_WIDTH và MINIMAP_HEIGHT sẽ được tính động dựa trên map_width và map_height
MINIMAP_WALL_COLOR = (100, 100, 100)  # Màu tường
MINIMAP_FLOOR_COLOR = (50, 50, 50)    # Màu sàn
MINIMAP_PLAYER_COLOR = (0, 255, 0)    # Màu người chơi (xanh lá)
MINIMAP_ENEMY_COLOR = (255, 0, 0)     # Màu enemy (đỏ)
MINIMAP_EXIT_COLOR = (0, 0, 255)      # Màu lối ra (xanh dương)


from enum import Enum, auto

class Direction(Enum):
    NONE = auto()
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    LEFT_UP = auto()
    LEFT_DOWN = auto()
    RIGHT_UP = auto()
    RIGHT_DOWN = auto()