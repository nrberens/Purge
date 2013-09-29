#MAP SIZE
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 40
NUM_FLOORS = 10

#ROOM SPAWN LIMITS
MAX_ROOM_ITEMS = 2
MAX_ROOM_PILLARS = 1

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50

MAP_WIDTH = 80
MAP_HEIGHT = 36

BAR_WIDTH = 18

#PANEL
PANEL_HEIGHT = 7
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT

#MESSAGE BAR
MSG_X = BAR_WIDTH + 2
MSG_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 2
MSG_HEIGHT = PANEL_HEIGHT - 1

#FPS
LIMIT_FPS = 20

#FOV
FOV_ALGO = 0 #default FOV algorithm
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 7
BEAST_SIGHT_RADIUS = 10
NODE_SIGHT_RADIUS = 5
FLARE_RADIUS = 5

#INVENTORY
INVENTORY_WIDTH = 50
TOTAL_BOMB_PARTS = 5

#GLOBAL DEFINTIONS
global objects, player, beast
global inventory
global map, floors, current_floor
global fov_map, beast_fov_map, fov_recompute, fov_radius, beast_fov_radius
global nodes, flares
global game_msgs, game_state
global max_o2, bomb_parts_collected
global turns

max_o2 = 200
bomb_parts_collected = 0