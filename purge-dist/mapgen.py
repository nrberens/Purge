import libtcodpy as libtcod
import math

import config
import game
import gfx

class Tile:
	#a tile of the config.map and its properties
	def __init__(self, blocked, x, y, block_sight = None):
		self.blocked = blocked
		self.x = x
		self.y = y
		
		#all tiles start unexplored
		self.explored = False

		self.scanned = False

		self.water = False

		self.flared = False
		
		#by default, if a tile is blocked, it also blocks sight
		if block_sight is None: block_sight = blocked
		self.block_sight = block_sight
		
		flag = 0
		self.flag = flag

class Rect:
	#a rectangle on the config.map. used to characterize a room.
	def __init__(self, x, y, w, h):
		self.x1 = x
		self.y1 = y
		self.x2 = x + w
		self.y2 = y + h
	
	def center(self):
		center_x = (self.x1 + self.x2) / 2
		center_y = (self.y1 + self.y2) / 2
		return (center_x, center_y)
	
	def intersect(self, other):
		#returns true if this rectangle intersects with another one
		return (self.x1 <= other.x2 and self.x2 >= other.x1 and
				self.y1 <= other.y2 and self.y2 >= other.y1)

def create_room(room):
	#go through the tiles in the rectangle and make them passable
	for x in range(room.x1 + 1, room.x2):
		for y in range(room.y1 + 1, room.y2):
			config.map[x][y].blocked = False
			config.map[x][y].block_sight = False

def create_h_tunnel(x1, x2, y):
	
	#horizontal tunnel. min() and max() are used in case x1>x2
	for x in range(min(x1, x2), max(x1, x2) + 1):
		config.map[x][y].blocked = False
		config.map[x][y].block_sight = False

def create_v_tunnel(y1, y2, x):
	
	#vertical tunnel
	for y in range(min(y1, y2), max(y1, y2) + 1):
		config.map[x][y].blocked = False
		config.map[x][y].block_sight = False

def make_map():
	
	#the list of config.objects with just the config.player
	config.objects = [config.player]
	config.nodes = []
	config.flares = []
	#fill config.map with blocked tiles
	config.map = [[ Tile(True, x, y)
		for y in range(config.MAP_HEIGHT)	]
			for x in range(config.MAP_WIDTH)]
	
	rooms = []
	num_rooms = 0
	count = 0
	total_count = config.MAP_WIDTH * config.MAP_HEIGHT
	
	for r in range(config.MAX_ROOMS):
		
		#random width and height
		w = libtcod.random_get_int(0, config.ROOM_MIN_SIZE, config.ROOM_MAX_SIZE)
		h = libtcod.random_get_int(0, config.ROOM_MIN_SIZE, config.ROOM_MAX_SIZE)
		#random position without going out of the boundaries of the config.map
		x = libtcod.random_get_int(0, 0, config.MAP_WIDTH - w - 1)
		y = libtcod.random_get_int(0, 0, config.MAP_HEIGHT - h - 1)
		
		#Rect class makes rectangles easier to work with
		new_room = Rect(x, y, w, h)
		
		#run through the other rooms and see if they intersect
		failed = False
		for other_room in rooms:
			if new_room.intersect(other_room):
				failed = True
				break
		
		if not failed:
			#this means there are no intersections, so this room is valid
			
			#"paint" it to the config.map's tiles
			create_room(new_room)
			
			#add some contents to this room, such as monsters
			place_objects(new_room)
			
			#20% change of fungus
			if libtcod.random_get_int(0, 0, 4) < 2:
				place_fungus(new_room)
			
			if libtcod.random_get_int(0, 0, 4) < 1:
				place_pools(new_room)

			#center coordinates of new room, will be useful later
			(new_x, new_y) = new_room.center()
			
			if num_rooms == 0:
				#this is the first room, where the config.player starts
				config.player.x = new_x
				config.player.y = new_y
				
				#add stairs leading to the previous floor
				stairs_component = game.Stairs(direction='up')
				stairs_up = game.Object(new_x, new_y, '<', 'stairs leading up', libtcod.Color(223, 223, 223), stairs=stairs_component)
				config.objects.append(stairs_up)
				#stairs_up.send_to_back()
			else:
				#all rooms after the first:
				#connect it to the previous room with a tunnel
				
				#center coordinates of previous room
				(prev_x, prev_y) = rooms[num_rooms-1].center()
				
				make_door = False
				
				#draw a coin (random number that is either 0 or 1
				
				if libtcod.random_get_int(0, 0, 1) == 1:
					#first move horizontally, then vertically
					create_h_tunnel(prev_x, new_x, prev_y)
					create_v_tunnel(prev_y, new_y, new_x)
					# if new_y > prev_y: #new room below prev room
						# doorx = new_x
						# doory = new_y-(h/2)
					# else:				#new room above room
						# doorx = new_x
						# doory = new_y+(h/2)
					# #check for walls on either side
					# if config.map[doorx+1][doory].blocked and config.map[doorx-1][doory].blocked and not config.map[doorx][doory].blocked:
						# make_door = True
				else:
					#first move vertically, then horizontally
					create_v_tunnel(prev_y, new_y, prev_x)
					create_h_tunnel(prev_x, new_x, new_y)
					# if new_x > prev_x:	#new room to the right
						# doorx = new_x-(w/2)
						# doory = new_y
					# else:				#new room to the libtcod.LEFT
						# doorx = new_x+(w/2)
						# doory = new_y
					# #check for walls on either side
					# if config.map[doorx][doory+1].blocked and config.map[doorx][doory-1].blocked and not config.map[doorx][doory].blocked:
						# make_door = True
				
				#place a door randomly in the hall
				#dice = libtcod.random_get_int(0, 0, 100)
				#if dice < 10:
				# if make_door:
					# door_component = Door()
					# door = game.Object(doorx, doory, '+', 'a closed door', libtcod.Color(223, 223, 223), door=door_component)
					# config.objects.append(door)
					# config.map[doorx][doory].blocked = True
					# config.map[doorx][doory].block_sight = True
			
			#finally, append the new room to the list
			rooms.append(new_room)
			num_rooms += 1


	place_beast(rooms)
			
	place_corpse(rooms)

	place_bombpart(rooms)

	#place stairs in the last room
	failed = True
	while failed:
		stairsx = libtcod.random_get_int(0, new_room.x1+1, new_room.x2-1)
		stairsy = libtcod.random_get_int(0, new_room.y1+1, new_room.y2-1)
		
		if not is_blocked(stairsx, stairsy):
			failed = False
	
	#add stairs to the center of the last generated room leading down
	stairs_component = game.Stairs(direction='down')
	stairs_down = game.Object(new_x, new_y, '>', 'stairs leading down', libtcod.Color(223, 223, 223), stairs=stairs_component)
	config.objects.append(stairs_down)
	#stairs_down.send_to_back()
	
	make_caves(rooms)
	make_rivers()
	place_doors()

def make_caves(rooms):
	#use cellular automata to create cave-like structures in config.map
	
	#single pass
	
	#check tile and all adjacent tiles
	#if it has <=3 walls, make it a floor
	#if it has >=5 walls, make it a wall
	#if 4 walls, it stays the same
	
	#pdb.set_trace()
	
	for room in rooms:
		if libtcod.random_get_int(0, 1, 100) < 50:
			for x in range(room.x1, room.x2):
				#print "x " + str(x)
				for y in range(room.y1, room.y2):
					#print "y " + str(y)
					wall_count = 0
					#print "wall_count reset"
					for r in (-1,0,1):
						for c in (-1,0,1):
							if config.map[x + r][y + c].blocked == True and not(r == 0 and c == 0):
								wall_count += 1
								#print "wall_count " + str(wall_count)
					
					if wall_count <= 3:
						config.map[x][y].blocked = False
						config.map[x][y].block_sight = False
					elif wall_count >= 5:
						config.map[x][y].blocked = True
						config.map[x][y].block_sight = True

def make_rivers():
	starty = libtcod.random_get_int(0, 1, config.MAP_HEIGHT-1)
	startx = 0
		
	#Drunkard's Walk with double weight to move east
	
	x = startx
	y = starty

	while 1 <= x <= config.MAP_WIDTH-1 and 1 <= y <= config.MAP_HEIGHT-1:
		#place water tile
		if not config.map[x][y].water:
			pool_component = Pool(water=True)
			pool_instance = game.Object(x, y, 'w', 'a pool of water', libtcod.Color(52,108,105), pool=pool_component)
			config.objects.append(pool_instance)
			config.map[x][y].blocked = False
			config.map[x][y].block_sight = False
			config.map[x][y].water = True
		
		walk = libtcod.random_get_int(0, 0, 5)
		if walk == 0: #go north
			y -= 1
		elif walk == 1: #go south
			y += 1
		elif walk == 2: #go west
			x -= 1
		else:			#go east, 2x chance
			x += 1

def place_objects(room):
	# #choose random number of monsters
	# num_monsters = libtcod.random_get_int(0, 0, MAX_ROOM_MONSTERS)
	
	#choose random number of items
	# num_items = libtcod.random_get_int(0, 0, config.MAX_ROOM_ITEMS)
	
	# for i in range (num_items):
	# 	#choose random spot for this item
	# 	x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
	# 	y = libtcod.random_get_int(0, room.y1+1, room.y2-1)
		
	# 	#only  place it if tile is not blocked
	# 	if config.map[x][y].blocked == False:
	# 		dice = libtcod.random_get_int(0, 0, 100)
	# 		if dice < 50:
	# 			armor_component = game.Armor(ac=10, c=2, i=2)
	# 			item_component = game.Item(armor=armor_component)
				
	# 			item = game.Object(x, y, '[', 'Leather Armor', libtcod.dark_orange, item = item_component)
	# 		else:
	# 			#create a longsword (10% chance)
	# 			weapon_component = game.Weapon(mindmg=5, maxdmg=8, hitdie=2)
	# 			item_component = game.Item(weapon=weapon_component)
				
	# 			item = game.Object(x, y, ')', 'Longsword', libtcod.light_blue, item = item_component)
			
	# 		config.objects.append(item)
	# 		item.send_to_back() #items appear below other config.objects
	
	#place monoliths
	#choose random spot for this item
	x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
	y = libtcod.random_get_int(0, room.y1+1, room.y2-1)
	
	num_pillars = libtcod.random_get_int(0, 0, config.MAX_ROOM_PILLARS)
	
	for i in range(num_pillars):
		x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
		y = libtcod.random_get_int(0, room.y1+1, room.y2-1) 
	
		if (config.map[x][y].blocked == False):
			config.map[x][y].blocked = True
			config.map[x][y].block_sight = True
	
	#check for unblocked tile
	# if (config.map[x][y].blocked == False):
	# 	monolith_component = Monolith()
	# 	monolith = game.Object(x, y, '!', 'a monolith', libtcod.Color(255, 255, 255))
	# 	config.objects.append(monolith)
	# 	config.map[x][y].blocked = True
	# 	config.map[x][y].block_sight = True

def place_doors():
	#check all tiles for doorway-appropriate layout
	for x in range(config.MAP_WIDTH):
		for y in range(config.MAP_HEIGHT):
			 #check for appropriate door placement:
					#    #              .
					#   .+.    or      #+#
					#    #              .
					#
			if (config.map[x][y].blocked == False \
				and config.map[x-1][y].blocked == False \
				and config.map[x+1][y].blocked == False \
				and config.map[x][y-1].blocked \
				and config.map[x][y+1].blocked) \
				or ( \
				config.map[x][y].blocked == False \
				and config.map[x][y-1].blocked == False \
				and config.map[x][y+1].blocked == False \
				and config.map[x-1][y].blocked \
				and config.map[x+1][y].blocked):
					#random chance of door placement: 2%
					if libtcod.random_get_int(0, 0, 100) < 2:
						door_component = game.Door()
						door = game.Object(x, y, '+', 'a closed door', libtcod.Color(223, 223, 223), door=door_component)
						libtcod.console_put_char_ex(gfx.con, x, y, ' ', libtcod.white, gfx.color_light_ground)
						config.objects.append(door)
						config.map[x][y].blocked = True
						config.map[x][y].block_sight = True

def place_fungus(room):
	#choose a random spot for fungus to spawn
	x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
	y = libtcod.random_get_int(0, room.y1+1, room.y2-1)
	
	for i in range(x-2, x+2):
		for j in range(y-2, y+2):
			if config.map[i][j].blocked == False or config.map[i][j].block_sight == False:
				fungus_component = game.Fungus()
				fung = game.Object(i, j, 'f', 'bioluminescent fungus', libtcod.Color(174,9,13), fungus=fungus_component)
				config.objects.append(fung)
				fung.send_to_back()
	return

def place_pools(room):	
	#choose a random spot for pool to spawn
	x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
	y = libtcod.random_get_int(0, room.y1+1, room.y2-1)

	radius = 4.0
	i = -radius

	while i < radius:
		half_row_width=math.sqrt(radius*radius-i*i)
   		j = - half_row_width
    	
   		while j < half_row_width:
   			if 0 < int(i)+x < config.MAP_WIDTH and 0 < int(j)+y < config.MAP_HEIGHT:
	   			if config.map[int(i)+x][int(j)+y].blocked == False or config.map[int(i)+x][int(j)+y].block_sight == False:
					pool_component = game.Pool(water=True)
					pool_instance = game.Object(int(i)+x, int(j)+y, 'w', 'a pool of water', libtcod.Color(52,108,105), pool=pool_component)
					config.objects.append(pool_instance)
					config.map[int(i)+x][int(j)+y].water = True
					pool_instance.send_to_back()
			j += 1.0
		i += 1.0

def place_beast(rooms):

	#select a room
	r = libtcod.random_get_int(0, 0, len(rooms)-1)

	room = rooms[r]

	#place The Beast
	x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
	y = libtcod.random_get_int(0, room.y1+1, room.y2-1)
	
	if not is_blocked(x, y):
		fighter_component = game.Fighter(plclass='None', ac=0, str=10, dex=10, con=10, int=10, fth=10, per=10, equipweapon=None, 
									equiparmor=None, equipscanner = None, equipheadlamp = None, equiptank=None, equipcamo=None, 
									hitdie = 10, mindmg = 50, maxdmg = 100, hp=10, defense=0, power=3, o2=100, 
									death_function=game.monster_death)
		ai_component = game.Beast()
		config.beast = game.Object(x, y, 'B', 'beast', libtcod.darker_green, blocks = True, fighter = fighter_component, ai = ai_component)
		config.objects.append(config.beast)
		return True
	return False

def place_corpse(rooms):

	#select a room
	r = libtcod.random_get_int(0, 0, len(rooms)-1)
	room = rooms[r]

	#DEBUG: Place corpse in first room
	# room = rooms[0]

	#place a corpse
	x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
	y = libtcod.random_get_int(0, room.y1+1, room.y2-1)
	
	if not is_blocked(x, y):

		dice = libtcod.random_get_int(0, 0, 100)

		if dice < 16:
			item_component = game.Item(tank=True)
			item = game.Object(x, y, 'O', 'oxygen tank', libtcod.light_blue, item = item_component)
		elif 16 <= dice < 32:
			item_component = game.Item(headlamp=True)
			item = game.Object(x, y, 'L', 'headlamp', libtcod.light_blue, item = item_component)
		elif 32 <= dice < 48:
			item_component = game.Item(siphon=True)
			item = game.Object(x, y, 'o', 'oxygen siphon', libtcod.light_blue, item = item_component)
		elif 48 <= dice < 64:
			camo_component = game.RCamo()
			item_component = game.Item(camo=camo_component)
			item = game.Object(x, y, 'c', 'refractive camo', libtcod.light_blue, item = item_component)
			item.name = 'refractive camo (' + str(item.item.camo.charge) + ')'
		elif 64 <= dice < 80:
			flare_component = game.DroppedFlare()
			item_component = game.Item(flare=flare_component)
			item = game.Object(x, y, 'f', 'signal flare', libtcod.light_blue, item = item_component)
		elif dice >= 80:
			node_component = game.ScannerNode()
			item_component = game.Item(node=node_component)
			item = game.Object(x, y, 'o', 'remote scanner node' , libtcod.light_blue, item = item_component)
			item.name = 'remote scanner node (' + str(item.item.node.charges) + ')'

		corpse_component = game.Corpse(item)
		corpse = game.Object(x, y, 's', 'scientist', libtcod.yellow, blocks = False, corpse = corpse_component)
		config.objects.append(corpse)
		corpse.send_to_back()
		return True
	return False

def place_bombpart(rooms):

	# #select a room
	r = libtcod.random_get_int(0, 0, len(rooms)-1)
	room = rooms[r]

	#DEBUG: Place bomb in first room
	# room = rooms[0]

	#place a bombpart
	x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
	y = libtcod.random_get_int(0, room.y1+1, room.y2-1)

	bombpart_component = game.BombPart()
	bombpart = game.Object(x, y, 'b', 'bomb componenent', libtcod.yellow, blocks = False, bombpart = bombpart_component)
	config.objects.append(bombpart)
	bombpart.send_to_back()
				
def is_blocked(x, y):
	#first test the map tile
	if config.map[x][y].blocked:
		return True
	
	for object in config.objects:
		if object.blocks and object.x == x and object.y == y:
			return True