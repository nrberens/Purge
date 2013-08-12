#O R B I T A L
#a game by Nathaniel Berens
#based on code by Jotaf
#powered by libtcod

#implement magic system
	#how to learn spells?
	#spell card allows player to choose spells
	#press button to cast equipped spell
	#uses up mana reserves
	#mana potions restore mana?
#mini player card expands into full player card
#mini target card under the player card
#mouse interaction:
	#right-click brings up context menu, all available actions on that tile
	
#0.12 - Added Cave Generation and O2 - 8/7/13


import libtcodpy as libtcod
import math
import textwrap
import shelve
import pdb
import random

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50

MAP_WIDTH = 80
MAP_HEIGHT = 36

BAR_WIDTH = 18

PANEL_HEIGHT = 7
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT

MSG_X = BAR_WIDTH + 2
MSG_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 2
MSG_HEIGHT = PANEL_HEIGHT - 1

INVENTORY_WIDTH = 50

LIMIT_FPS = 20

ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30
NUM_FLOORS = 10

#COLOR PALETTES

#Dark Horizon
# color_dark_wall = libtcod.Color(32,40,61)
# color_light_wall = libtcod.Color(122,60,45)
# color_dark_ground = libtcod.Color(19,26,42)
# color_light_ground = libtcod.Color(127,51,28)

#Extra Soft (Black and Gray)
# color_dark_wall = libtcod.Color(12,12,13)
# color_light_wall = libtcod.Color(37,37,38)
# color_dark_ground = libtcod.Color(1,1,1)
# color_light_ground = libtcod.Color(24,25,26)

#2046
# color_dark_wall = libtcod.Color(102,33,18)
# color_light_wall = libtcod.Color(192,98,2)
# color_dark_ground = libtcod.Color(44,9,13)
# color_light_ground = libtcod.Color(102,33,18)

#Bloodlust
color_dark_wall = libtcod.Color(26,13,22)
color_light_wall = libtcod.Color(121,9,0)
color_dark_ground = libtcod.Color(10,7,2)
color_light_ground = libtcod.Color(67,8,14)
panel_color = libtcod.Color(26,13,22)

#Tutorial
# color_dark_wall = libtcod.Color(0, 0, 100)
# color_light_wall = libtcod.Color(130, 110, 50)
# color_dark_ground = libtcod.Color(50, 50, 150)
# color_light_ground = libtcod.Color(200, 180, 50)

FOV_ALGO = 0 #default FOV algorithm
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 7

MAX_ROOM_MONSTERS = 3
MAX_ROOM_ITEMS = 2

HEAL_AMOUNT = 30
LIGHTNING_RANGE = 5
LIGHTNING_DAMAGE = 20
CONFUSE_NUM_TURNS = 10
CONFUSE_RANGE = 8
FIREBALL_RADIUS = 3
FIREBALL_DAMAGE = 12

class Tile:
	#a tile of the map and its properties
	def __init__(self, blocked, x, y, block_sight = None):
		self.blocked = blocked
		self.x = x
		self.y = y

		#all tiles start unexplored
		self.explored = False

		#by default, if a tile is blocked, it also blocks sight
		if block_sight is None: block_sight = blocked
		self.block_sight = block_sight
		
		flag = 0
		self.flag = flag

class Rect:
	#a rectangle on the map. used to characterize a room.
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

class Object:
	#this is a generic object: the player, a monster, an item, the stairs...
	#it's always represented by a character on screen.
	def __init__(self, x, y, char, name, color, floor=0, blocks=False, stats=None, fighter=None, ai=None, item=None, stairs=None, door=None, fungus=None):
		self.name = name
		self.blocks = blocks
		self.x = x
		self.y = y
		self.char = char
		self.color = color
		self.floor = floor
		floor = current_floor

		self.stats = stats
		if self.stats: #let the stats component know who owns it
			self.stats.owner = self

		self.fighter = fighter
		if self.fighter: #let the fighter component know who owns it
			self.fighter.owner = self

		self.ai = ai
		if self.ai: #let the AI component know who owns it
			self.ai.owner = self

		self.item = item
		if self.item: #let the item component know who owns it
			self.item.owner = self

		self.stairs = stairs
		if self.stairs: #let the stairs component know who owns it
			self.stairs.owner = self

		self.door = door
		if self.door: #let the stairs component know who owns it
			self.door.owner = self

		self.fungus = fungus
		if self.fungus:
			self.fungus.owner = self

	def move(self, dx, dy):
		#check if destination tile is blocked
		if not map[self.x + dx][self.y + dy].blocked:
			self.x += dx
			self.y += dy

	def move_towards(self, target_x, target_y):
		#vector from this object to the target, and distance
		dx = target_x - self.x
		dy = target_y - self.y
		distance = math.sqrt(dx ** 2 + dy ** 2)

		#normalize it length 1 (preserving direction), then round it and convert to integer so the movement is restricted to the map grid
		dx = int(round(dx / distance))
		dy = int(round(dy / distance))
		self.move(dx, dy)

	def distance_to(self, other):
		#return the distance to another object
		dx = other.x - self.x
		dy = other.y - self.y
		return math.sqrt(dx ** 2 + dy ** 2)

	def distance(self, x, y):
		#return the distance to some coordinates
		return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

	def send_to_back(self):
		#makes this object be drawn first, so all others appear above it if they're in the same tile
		global objects
		objects.remove(self)
		objects.insert(0, self)

	def draw(self):
		if libtcod.map_is_in_fov(fov_map, self.x, self.y):
			#set the color and then draw the character that represents this object at its position
			libtcod.console_set_default_foreground(con, self.color)
			libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)

	def clear(self):
		#erase the character that represents this object
		if libtcod.map_is_in_fov(fov_map, self.x, self.y):
			libtcod.console_put_char_ex(con, self.x, self.y, ' ', libtcod.white, color_light_ground)

class Stats:
	#statistics for the player character
	def __init__(self, plclass, ac, str, dex, con, int, fth, per, equipweapon, equiparmor, hitdie, mindmg, maxdmg):
		self.plclass = plclass
		self.ac = ac
		self.str = str
		self.dex = dex
		self.con = con
		self.int = int
		self.fth = fth
		self.per = per
		self.equipweapon = equipweapon
		self.equiparmor = equiparmor
		self.hitdie = hitdie
		self.mindmg = mindmg
		self.maxdmg = maxdmg

	def buff_stats(self, ac, s, d, c, i, f, p):
		self.ac += ac
		self.str += s
		self.dex += d
		self.con += c
		self.int += i
		self.fth += f
		self.per += p


	def debuff_stats(self, ac, s, d, c, i, f, p):
		self.ac -= ac
		self.str -= s
		self.dex -= d
		self.con -= c
		self.int -= i
		self.fth -= f
		self.per -= p

class Fighter:
	#stats for any PC or NPC object
	def __init__(self, plclass, ac, str, dex, con, int, fth, per, equipweapon, equiparmor, hitdie, mindmg, maxdmg, hp, power, defense, o2, death_function=None):
		self.plclass = plclass
		self.ac = ac
		self.str = str
		self.dex = dex
		self.con = con
		self.int = int
		self.fth = fth
		self.per = per
		self.equipweapon = equipweapon
		self.equiparmor = equiparmor
		self.hitdie = hitdie
		self.mindmg = mindmg
		self.maxdmg = maxdmg

		self.max_hp = hp
		self.hp = hp
		self.power = power
		self.defense = defense
		self.o2 = o2
		self.death_function = death_function

	def buff_stats(self, ac, s, d, c, i, f, p):
		self.ac += ac
		self.str += s
		self.dex += d
		self.con += c
		self.int += i
		self.fth += f
		self.per += p


	def debuff_stats(self, ac, s, d, c, i, f, p):
		self.ac -= ac
		self.str -= s
		self.dex -= d
		self.con -= c
		self.int -= i
		self.fth -= f
		self.per -= p

	def take_damage(self, damage):
		#apply damage if possible
		if damage > 0:
			self.hp -= damage
		#check for death. if there's a death function, call it
		if self.hp <= 0:
			function = self.death_function
			if function is not None:
				function(self.owner)
			
	def manage_oxygen(self, oxygen):
		#each turn reduce oxygen by 1
		self.o2 += oxygen
		
		#check for suffocation
		if self.o2 <= 0:
			function = self.death_function
			if function is not None:
				function(self.owner)
				
	#where to call?

	def attack(self, target):

		if	self.owner==player:
			#if player, use player attack stats
			hitdie = self.hitdie
			mindmg = self.mindmg
			maxdmg = self.maxdmg
		else:
			#not player, use filler stats
			hitdie = 2
			mindmg = 1
			maxdmg = 5

		if libtcod.random_get_int(0,1,20) > hitdie:
			#hit!
			message('hit!')
			#determine damage
			damage = libtcod.random_get_int(0, mindmg, maxdmg) - target.fighter.defense
		else:
			#miss!
			message('miss!')
			damage = 0

		if damage > 0:
			#make the target take some damage
			message(self.owner.name.capitalize() + ' attacks ' + target.name + ' for ' + str(damage) + ' hit points.')
			target.fighter.take_damage(damage)
		else:
			message(self.owner.name.capitalize() + ' attacks ' + target.name + ' but it has no effect!')

	def heal(self, amount):
		#heal by the given amount, without going over the maximum
		self.hp += amount
		if self.hp > self.max_hp:
			self.hp = self.max_hp

class BasicMonster:
	#AI for a basic monster.
	def take_turn(self):
		#a basic monster takes its turn. if you can see it, it can see you
		monster = self.owner
		if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):

			#move towards player if far away
			if monster.distance_to(player) >= 2:
				monster.move_towards(player.x, player.y)

			#close enough, attack! (if the player is still alive.)
			elif player.fighter.hp > 0:
				monster.fighter.attack(player)

class ConfusedMonster:
	#AI for a temporarily confused monster (reverts to previous AI after spell runs out)
	def __init__(self, old_ai, num_turns=CONFUSE_NUM_TURNS):
		self.old_ai = old_ai
		self.num_turns = num_turns

	def take_turn(self):
		if self.num_turns > 0: #still confused
			#move in a random direction
			self.owner.move(libtcod.random_get_int(0,-1,1), libtcod.random_get_int(0,-1,1))
			self.num_turns -= 1
		else: #no longer confused, restore the previous AI
			self.owner.ai = self.old_ai
			message('The ' + self.owner.name + ' is no longer confused!', libtcod.red)

class Item:
	#an item that can be picked up and used.
	def __init__(self, use_function=None, equipped=False, armor=None, weapon=None):
		self.use_function = use_function
		self.equipped = equipped
		self.armor = armor
		self.weapon = weapon

	def pick_up(self):
		#add the player's inventory and remove from the map
		if len(inventory) >= 26:
			message('Your inventory is full - cannot pick up ' + self.owner.name + '.', libtcod.red)
		else:
			inventory.append(self.owner)
			objects.remove(self.owner)
			message('You picked up a ' + self.owner.name + '!', libtcod.green)

	def use(self):
		#just call the "use_function" if it is defined
		if self.use_function is None:
			message('The ' + self.owner.name + ' cannot be used.')
		else:
			if self.use_function() != 'cancelled':
				inventory.remove(self.owner) #destroy after use, unless it was cancelled for some reason

	def drop(self):
		#add to the map and remove from the player's inventory. also, place it at the player's coordinates.
		objects.append(self.owner)
		inventory.remove(self.owner)
		self.owner.x = player.x
		self.owner.y = player.y
		message('You dropped a ' + self.owner.name + '.', libtcod.yellow)

	def equip_armor(self):

		if not self.equipped:
			remove_armor()
			self.equipped = True
			self.owner.name = self.owner.name + ' (worn)'
			player.fighter.equiparmor = self.owner
			player.fighter.buff_stats(self.armor.ac, self.armor.s, self.armor.d, self.armor.c, self.armor.i, self.armor.f, self.armor.p)
		else:
			self.equipped = False
			self.owner.name = self.owner.name.replace(' (worn)', '')
			player.fighter.equiparmor = birthdaysuit
			player.fighter.debuff_stats(self.armor.ac, self.armor.s, self.armor.d, self.armor.c, self.armor.i, self.armor.f, self.armor.p)

	def equip_weapon(self):

		#check for equipped weapons

		if not self.equipped:
			remove_weapons()
			self.equipped = True
			self.owner.name = self.owner.name + ' (wielded)'
			player.fighter.equipweapon = self.owner
			player.fighter.hitdie = self.weapon.hitdie
			player.fighter.mindmg = self.weapon.mindmg
			player.fighter.maxdmg = self.weapon.maxdmg
		else:
			self.equipped = False
			self.owner.name = self.owner.name.replace(' (wielded)', '')
			player.fighter.equipweapon = barehands
			player.fighter.hitdie = 0
			player.fighter.mindmg = 0
			player.fighter.maxdmg = 0

class Armor:
	def __init__(self, ac=0, s=0, d=0, c=0, i=0, f=0, p=0):
		self.ac = ac
		self.s = s
		self.d = d
		self.c = c
		self.i = i
		self.f = f
		self.p = p

class Weapon:
	def __init__(self, mindmg=0, maxdmg=0, hitdie=0):
		self.mindmg = mindmg
		self.maxdmg = maxdmg
		self.hitdie = hitdie

class Stairs:
	#stairs that go up or down a floor

	def __init__(self, direction=None):
		self.direction = direction

class Door:
	#doors that open, close, and can be locked
	def __init__(self, open=False, locked=False):
		self.open = open
		self.locked = locked

	def open_door(self):
		global map, fov_recompute
		self.open = True
		message('You open the door.', libtcod.white)
		self.owner.char = '/'
		map[self.owner.x][self.owner.y].blocked = False
		map[self.owner.x][self.owner.y].block_sight = False
		self.owner.name = 'An open door'
		self.owner.send_to_back()
		fov_recompute = True
		render_all()

	def close_door(self):
		global map, fov_recompute
		self.open = False
		message('You close the door.', libtcod.white)
		self.owner.char = '+'
		map[self.owner.x][self.owner.y].blocked = True
		map[self.owner.x][self.owner.y].block_sight = True
		self.owner.name = 'A closed door'
		fov_recompute = True
		render_all()

class Monolith:
	#monoliths that give a one-time upgrade
	def __init__(self, used=False):
		self.used = used
		
	def use_monolith(self):
		return

class Fungus:
	#bioluminescent fungus that refills oxygen
	def __init__(self):
		return

def create_room(room):
	global map
	#go through the tiles in the rectangle and make them passable
	for x in range(room.x1 + 1, room.x2):
		for y in range(room.y1 + 1, room.y2):
			map[x][y].blocked = False
			map[x][y].block_sight = False

def create_h_tunnel(x1, x2, y):
	global map
	#horizontal tunnel. min() and max() are used in case x1>x2
	for x in range(min(x1, x2), max(x1, x2) + 1):
		map[x][y].blocked = False
		map[x][y].block_sight = False

def create_v_tunnel(y1, y2, x):
	global map
	#vertical tunnel
	for y in range(min(y1, y2), max(y1, y2) + 1):
		map[x][y].blocked = False
		map[x][y].block_sight = False

def make_map():
	global map, objects, floors
	
	#the list of objects with just the player
	objects = [player]

	#fill map with blocked tiles
	map = [[ Tile(True, x, y)
		for y in range(MAP_HEIGHT)	]
			for x in range(MAP_WIDTH)]

	rooms = []
	num_rooms = 0
	count = 0
	total_count = MAP_WIDTH * MAP_HEIGHT

	for r in range(MAX_ROOMS):

		#random width and height
		w = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
		h = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
		#random position without going out of the boundaries of the map
		x = libtcod.random_get_int(0, 0, MAP_WIDTH - w - 1)
		y = libtcod.random_get_int(0, 0, MAP_HEIGHT - h - 1)

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

			#"paint" it to the map's tiles
			create_room(new_room)

			#add some contents to this room, such as monsters
			place_objects(new_room)

			#20% change of fungus
			# if libtcod.random_get_int(0, 0, 4) < 1:
			# 	place_fungus(new_room)

			place_fungus(new_room)

			#center coordinates of new room, will be useful later
			(new_x, new_y) = new_room.center()

			if num_rooms == 0:
				#this is the first room, where the player starts
				player.x = new_x
				player.y = new_y

				#add stairs leading to the previous floor
				stairs_component = Stairs(direction='up')
				stairs_up = Object(new_x, new_y, '<', 'stairs leading up', libtcod.Color(223, 223, 223), stairs=stairs_component)
				objects.append(stairs_up)
				stairs_up.send_to_back()
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
					# if map[doorx+1][doory].blocked and map[doorx-1][doory].blocked and not map[doorx][doory].blocked:
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
					# if map[doorx][doory+1].blocked and map[doorx][doory-1].blocked and not map[doorx][doory].blocked:
						# make_door = True

				#place a door randomly in the hall
				#dice = libtcod.random_get_int(0, 0, 100)
				#if dice < 10:
				# if make_door:
					# door_component = Door()
					# door = Object(doorx, doory, '+', 'a closed door', libtcod.Color(223, 223, 223), door=door_component)
					# objects.append(door)
					# map[doorx][doory].blocked = True
					# map[doorx][doory].block_sight = True

			#finally, append the new room to the list
			rooms.append(new_room)
			num_rooms += 1

	#place stairs in the last room
	failed = True
	while failed:
		stairsx = libtcod.random_get_int(0, new_room.x1+1, new_room.x2-1)
		stairsy = libtcod.random_get_int(0, new_room.y1+1, new_room.y2-1)

		if not is_blocked(stairsx, stairsy):
			failed = False

	#add stairs to the center of the last generated room leading down
	stairs_component = Stairs(direction='down')
	stairs_down = Object(new_x, new_y, '>', 'stairs leading down', libtcod.Color(223, 223, 223), stairs=stairs_component)
	objects.append(stairs_down)
	stairs_down.send_to_back()
	
	#add cave sections
	make_caves(rooms)
	place_doors()

	#flood fill to check for continuity
	x = libtcod.random_get_int(0, 0, MAP_WIDTH-1)
	y = libtcod.random_get_int(0, 0, MAP_HEIGHT-1)
	
	#pdb.set_trace()
	#(x, y, count)

def make_caves(rooms):
	#use cellular automata to create cave-like structures in map
	
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
							if map[x + r][y + c].blocked == True and not(r == 0 and c == 0):
								wall_count += 1
								#print "wall_count " + str(wall_count)
					
					if wall_count <= 3:
						map[x][y].blocked = False
						map[x][y].block_sight = False
					elif wall_count >= 5:
						map[x][y].blocked = True
						map[x][y].block_sight = True
	
def flood_fill(x, y, count): #iterative
	
	pdb.set_trace()
	
	# 1. Set Q to the empty queue.
	Q = []
	
	# 2. If the color of node is not equal to target-color, return.
	if map[x][y].blocked:
		return
		
	# 3. Add node to Q.
	Q.append(map[x][y]) #appends tile at x,y
	
	# 4. For each element N of Q:
	for n in Q:
	# 5.    If the color of N is equal to target-color:
		if n.blocked == False and n.flag != 1:
	# 6.        Set w and e equal to N.
			w = n
			wx = n.x
			e = n
			ex = n.x
	# 7.        Move w to the west until the color of the node to the west of w no longer matches target-color.
		for i in range(x, 0, -1):
			wx = i
			if map[i][y].blocked == True or map[i][y].flag == 1:
				break
	# 8.		Move e to the east until the color of the node to the east of e no longer matches target-color.
		for i in range(x, MAP_WIDTH, 1):
			ex = i
			if map[ex][y].blocked == True or map[ex][y].flag == 1:
				break
	# 9.       For each node n between w and e:			
		for i in range(wx, ex, 1):
	# 10.           Set the color of n to replacement-color.
			map[i][y].flag = 1
	# 11.           If the color of the node to the north of n is target-color, add that node to Q.
		if map[i][n.y-1].blocked == False and map[i][n.y-1].flag != 1:
			Q.append(map[i][n.y-1])
	# 12.           If the color of the node to the south of n is target-color, add that node to Q.				
		if map[i][n.y+1].blocked == False and map[i][n.y+1].flag != 1:
			Q.append(map[i][n.y+1])
	# 13. Continue looping until Q is exhausted.
	# 14. Return.
	return
					
def all_rooms_are_filled(): #check if map is contiguous
	#pdb.set_trace()
	for x in range(MAP_WIDTH):
		for y in range(MAP_HEIGHT):
			if map[x][y].blocked == False and map[x][y].flag != 1:
				#print y
				return False
	return True

def place_objects(room):
	# #choose random number of monsters
	# num_monsters = libtcod.random_get_int(0, 0, MAX_ROOM_MONSTERS)

	# for i in range(num_monsters):
	# #choose random spot for this monster
		# x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
		# y = libtcod.random_get_int(0, room.y1+1, room.y2-1)

		# #only place it if the tile is not blocked
		# if not is_blocked(x, y):
			# if libtcod.random_get_int(0, 0, 100) < 80: #80% chance of getting an orc
				# #create an orc
				# fighter_component = Fighter(plclass='None', ac=0, str=10, dex=10, con=10, int=10, fth=10, per=10, equipweapon=None, equiparmor=None, hitdie = 0, mindmg = 0, maxdmg = 0, hp=10, defense=0, power=3, o2=100, death_function=monster_death)
				# ai_component = BasicMonster()

				# monster = Object(x, y, 'o', 'orc', libtcod.desaturated_green, blocks=True, fighter=fighter_component, ai=ai_component)
			# else:
				# #create a troll
				# fighter_component = Fighter(plclass='None', ac=0, str=10, dex=10, con=10, int=10, fth=10, per=10, equipweapon=None, equiparmor=None, hitdie = 0, mindmg = 0, maxdmg = 0, hp=16, defense=1, power=4, o2=100 death_function=monster_death)
				# ai_component = BasicMonster()

				# monster = Object(x, y, 'T', 'troll', libtcod.darker_green, blocks = True, fighter=fighter_component, ai=ai_component)

			# objects.append(monster)

	#choose random number of items
	num_items = libtcod.random_get_int(0, 0, MAX_ROOM_ITEMS)

	for i in range (num_items):
		#choose random spot for this item
		x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
		y = libtcod.random_get_int(0, room.y1+1, room.y2-1)

		#only  place it if tile is not blocked
		if map[x][y].blocked == False:
			dice = libtcod.random_get_int(0, 0, 100)
			# if dice < 50:
				# #create a healing potion
				# item_component = Item(use_function=cast_heal)
				# item = Object(x, y, '!', 'healing potion', libtcod.violet, item=item_component)
			# elif dice < 50 + 10:
				# #create a lightning bolt scroll (10% chance)
				# item_component = Item(use_function=cast_lightning)

				# item = Object(x, y, '#', 'scroll of lightning bolt', libtcod.light_yellow, item = item_component)
			# elif dice < 50+10+10:
				# #create a fireball scroll (10% chance)
				# item_component = Item(use_function=cast_fireball)

				# item = Object(x, y, '#', 'scroll of fireball', libtcod.light_yellow, item=item_component)
			# elif dice < 50+10+10+10:
				# #create a confuse scroll (10% chance)
				# item_component = Item(use_function=cast_confuse)

				# item = Object(x, y, '#', 'scroll of confusion', libtcod.light_yellow, item = item_component)
			# elif dice < 50+10+10+10+10+10:
				# #create some leather armor (10% chance)
			if dice < 50:
				armor_component = Armor(ac=10, c=2, i=2)
				item_component = Item(armor=armor_component)

				item = Object(x, y, '[', 'Leather Armor', libtcod.dark_orange, item = item_component)
			else:
				#create a longsword (10% chance)
				weapon_component = Weapon(mindmg=5, maxdmg=8, hitdie=2)
				item_component = Item(weapon=weapon_component)

				item = Object(x, y, ')', 'Longsword', libtcod.light_blue, item = item_component)

			objects.append(item)
			item.send_to_back() #items appear below other objects

	#place monoliths
	#choose random spot for this item
	x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
	y = libtcod.random_get_int(0, room.y1+1, room.y2-1)
	
	#check for unblocked tile
	if (map[x][y].blocked == False):
		monolith_component = Monolith()
		monolith = Object(x, y, '!', 'a monolith', libtcod.Color(255, 255, 255))
		objects.append(monolith)
		map[x][y].blocked = True
		map[x][y].block_sight = True

def place_doors():
	global map, objects
	#check all tiles for doorway-appropriate layout
	for x in range(MAP_WIDTH):
		for y in range(MAP_HEIGHT):
			 #check for appropriate door placement:
					#    #              .
					#   .+.    or      #+#
					#    #              .
					#
			if (map[x][y].blocked == False \
				and map[x-1][y].blocked == False \
				and map[x+1][y].blocked == False \
				and map[x][y-1].blocked \
				and map[x][y+1].blocked) \
				or ( \
				map[x][y].blocked == False \
				and map[x][y-1].blocked == False \
				and map[x][y+1].blocked == False \
				and map[x-1][y].blocked \
				and map[x+1][y].blocked):
					#random chance of door placement: 2%
					if libtcod.random_get_int(0, 0, 100) < 2:
						door_component = Door()
						door = Object(x, y, '+', 'a closed door', libtcod.Color(223, 223, 223), door=door_component)
						libtcod.console_put_char_ex(con, x, y, ' ', libtcod.white, color_light_ground)
						objects.append(door)
						map[x][y].blocked = True
						map[x][y].block_sight = True

def place_fungus(room):
	#choose a random spot for fungus to spawn
	x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
	y = libtcod.random_get_int(0, room.y1+1, room.y2-1)

	for i in range(x-3, x+3):
		for j in range(y-3, y+3):
			if map[x][y].blocked == False:
				fungus_component = Fungus()
				fung = Object(i, j, libtcod.CHAR_YEN, 'bioluminescent fungus', libtcod.Color(121,9,0), fungus=fungus_component)
				objects.append(fung)
	return	

def is_blocked(x, y):
	#first test the map tile
	if map[x][y].blocked:
		return True

	for object in objects:
		if object.blocks and object.x == x and object.y == y:
			return True

def closest_monster(max_range):
	#find closest enemy, up to a maximum range, and in teh player's FOV
	closest_enemy = None
	closest_dist = max_range + 1 #start with (slightly more than maximum range)

	for object in objects:
		if object.fighter and not object == player and libtcod.map_is_in_fov(fov_map, object.x, object.y):
			#calculate the distance between this object and the player
			dist = player.distance_to(object)
			if dist < closest_dist: #it's closer, so remember it
				closest_enemy = object
				closest_dist = dist
	return closest_enemy

def handle_keys():																							#handle keyboard commands
	global playerx, playery
	global fov_recompute
	global current_floor
	global objects
	
	global key;

	#other functions
	if key.vk == libtcod.KEY_ENTER and key.lalt:
		#Alt+Enter: toggle fullscreen
		libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

	elif key.vk == libtcod.KEY_ESCAPE:
		#Escape: exit game
		return 'exit'

	#movement keys
	if game_state == 'playing':

		if key.vk == libtcod.KEY_UP:
			player_move_or_attack(0, -1)

		elif key.vk == libtcod.KEY_DOWN:
			player_move_or_attack(0, 1)

		elif key.vk == libtcod.KEY_LEFT:
			player_move_or_attack(-1, 0)

		elif key.vk == libtcod.KEY_RIGHT:
			player_move_or_attack(1, 0)
		else:
			#test for other keys
			key_char = chr(key.c)

			if key_char == 'g':
				#pick up an item
				for object in objects: #look for an item in the player's tile
					if object.x == player.x and object.y == player.y and object.item:
						object.item.pick_up()
						break

			if key_char == 'i':
				#show the inventory
				chosen_item = inventory_menu('Press the key next to an item to use it, or any other to cancel.\n')
				if chosen_item is not None:
					if chosen_item.armor:
						chosen_item.equip_armor()
					elif chosen_item.weapon:
						chosen_item.equip_weapon()
					else:
						chosen_item.use()

			if key_char == 'd':
				#show the inventory; if an item is selected, drop it
				chosen_item = inventory_menu('Press the key next to an item to (d)rop it, or any other to cancel.\n')
				if chosen_item is not None:
					chosen_item.drop()

			if key_char == 'c':
				#show the player card until player presses 'c' or 'esc'
				player_card()

			if key_char == 'o':
				#search for adjacent doors and open/close them
				for object in objects:
					if object.door and object.x <= player.x+1 and object.x >= player.x-1 and object.y <= player.y+1 and object.y >= player.y-1:
						if object.door.open:
							object.door.close_door()
						else:
							object.door.open_door()
				# #prompt for direction and open door
				# open_dir = open_menu()
				# if open_dir == 'North':
					# for object in objects:
						# if object.door and object.x == player.x and object.y == (player.y-1):
							# if object.door.open:
								# object.door.close_door()
							# else:
								# object.door.open_door()
							# break
				# elif open_dir == 'South':
					# for object in objects:
						# if object.door and object.x == player.x and object.y == (player.y+1):
							# if object.door.open:
								# object.door.close_door()
							# else:
								# object.door.open_door()
							# break
				# elif open_dir == 'East':
					# for object in objects:
						# if object.door and object.x == (player.x+1) and object.y == player.y:
							# if object.door.open:
								# object.door.close_door()
							# else:
								# object.door.open_door()
							# break
				# elif open_dir == 'West':
					# for object in objects:
						# if object.door and object.x == (player.x-1) and object.y == player.y:
							# if object.door.open:
								# object.door.close_door()
							# else:
								# object.door.open_door()
							# break


			#ascending
			if key_char == ',' or key_char == '<':
				#move up a floor
				#check if on staircase
				for object in objects:
					if object.stairs and player.x == object.x and player.y == object.y:
						#player is on stairs
						if object.stairs.direction == "up":
							if current_floor==0:
								message('There is no escape.', libtcod.red)
							else:
								#there's a floor above, so let him ascend
								go_to_floor(current_floor-1)
								break
						elif object.stairs.direction == "down":
							#player is on downward stairs
							message('These stairs lead down!', libtcod.red)
							break

			#descending
			if key_char == '.' or key_char == '>':
				#move down a floor
				#check if on staircase
				for object in objects:
					if object.stairs and player.x == object.x and player.y == object.y:
						#player is on stairs
						if object.stairs.direction == "down":
								go_to_floor(current_floor+1)
								break
						elif object.stairs.direction == "up":
							#player is on downward stairs
							message('These stairs lead up!', libtcod.red)
							break

			return 'didnt-take-turn'

#def get_key(key):
	##return either libtcod code or character that was pressed
	#if key.vk == libtcod.KEY_CHAR:
		#return chr(key.c)
	#else:
		#return key.vk

def handle_time():
	#pdb.set_trace()
	#player.fighter.manage_oxygen(-1)
	return

def go_to_floor(dest):
	global floors, map, objects, current_floor

	if dest > (len(floors)-1):
		#floor has not been generated yet, so generate it
		make_map()
	else:
		#floor has been generated
		map = floors[dest][0]
		objects = floors[dest][1]

		if dest < current_floor:
			#ascending
			for object in objects:
				if object.stairs and object.stairs.direction == "down":
					#find location of stairs_down from destination floor and place player there
					player.x = object.x
					player.y = object.y
					break
		elif dest > current_floor:
			#descending
			for object in objects:
				if object.stairs and object.stairs.direction == "up":
					#find location of stairs_down from destination floor and place player there
					player.x = object.x
					player.y = object.y
					break
		else:
			message('Something\'s kinda weird.', libtcod.red)

	current_floor = dest

	initialize_fov()

def get_names_under_mouse():
	global mouse

	#return a string with the names of all objects under the mouse
	(x, y) = (mouse.cx, mouse.cy)

	#create a list with the names of all objects at the mouse's coordinates and in FOV
	names = [obj.name for obj in objects
		if obj.x == x and obj.y == y and libtcod.map_is_in_fov(fov_map, obj.x, obj.y)]

	names = ', '.join(names)  #join the names, separated by commas
	return names.capitalize()

def target_tile(max_range=None):
	global key, mouse
	#return the position of a tile libtcod.LEFT-clicked in player's FOV (optionally in a range), or (None, None) if right-clicked.
	while True:
		#render the screen. this erases the inventory and shows the names of objects under the mouse.
		render_all()
		libtcod.console_flush()

		key = libtcod.console_check_for_keypress()
		mouse = libtcod.mouse_get_status() #get mouse position and click status
		(x, y) = (mouse.cx, mouse.cy)

		if (mouse.lbutton_pressed and libtcod.map_is_in_fov(fov_map, x, y) and
			(max_range is None or player.distance(x, y) <= max_range)):
			return (x, y)

		if mouse.rbutton_pressed or key.vk == libtcod.KEY_ESCAPE:
			return (None, None) #cancel if the player right-clicked or pressed escape

def target_monster(max_range=None):
	#returns a clicked monster inside FOV up to a range, or None if right-clicked
	while True:
		(x,y) = target_tile(max_range)
		if x is None: #player cancelled
			return None

		#return the first clicked-monster, otherwise continue looping
		for obj in objects:
			if obj.x == x and obj.y == y and obj.fighter and obj != player:
				return obj

def player_move_or_attack(dx, dy):
	global fov_recompute

	#the coordinates the player is moving to/attacking
	x = player.x + dx
	y = player.y + dy

	#try to find an attackable object there
	target = None
	for object in objects:
		if object.fighter and object.x == x and object.y == y:
			target = object
			break

	#attack if target found, move otherwise
	if target is not None:
		player.fighter.attack(target)
	else:
		player.move(dx, dy)
		fov_recompute = True

def player_death(player):
	#the game ended!
	global game_state
	message('You died!', libtcod.red)
	game_state = 'dead'

	#for added effect, transform the player into a corpse!
	player.char = '%'
	player.color = libtcod.dark_red

def monster_death(monster):
	#transform it into a nasty corpse! it doesn't block, can't be attacked, and doesn't move
	message(monster.name.capitalize() + ' is dead!', libtcod.orange)
	monster.char = '%'
	monster.color = libtcod.dark_red
	monster.blocks = False
	monster.fighter = None
	monster.ai = None
	monster.name = 'remains of ' + monster.name
	monster.send_to_back()

def cast_heal():
	#heal the player
	if player.fighter.hp == player.fighter.max_hp:
		message('You are already at full health.', libtcod.red)
		return 'cancelled'

	message('Your wounds start to feel better!', libtcod.light_violet)
	player.fighter.heal(HEAL_AMOUNT)

def cast_lightning():
	#find closest enemy (inside a maximum range) and damage it
	monster = closest_monster(LIGHTNING_RANGE)
	if monster is None: #no enemy found within maximum rnage
		message('No enemy is close enough to strike.', libtcod.red)
		return 'cancelled'

	#zap it!
	message('A lightning bolt strikes the ' + monster.name + ' with a loud thunder! The damage is '
		+ str(LIGHTNING_DAMAGE) + ' hit points ', libtcod.light_blue)
	monster.fighter.take_damage(LIGHTNING_DAMAGE)

def cast_confuse():
	#ask the player for a monster to confuse
	message('libtcod.LEFT-click an enemy to confuse it, or right-click to cancel.', libtcod.light_cyan)
	monster = target_monster(CONFUSE_RANGE)

	if monster is None: return 'cancelled'

	#replace the monster's AI with "confused" AI; after some turns it restores old AI
	old_ai = monster.ai
	monster.ai = ConfusedMonster(old_ai)
	monster.ai.owner = monster #tell the new component who owns it
	message('The eyes of the ' + monster.name + ' look vacant as he starts to stumble around!', libtcod.light_green)

def cast_fireball():
	#ask the player for a target tile to throw a fireball at
	message('libtcod.LEFT-click a target tile for the fireball, or right-click to cancel.', libtcod.light_cyan)
	(x, y) = target_tile()
	if x is None: return 'cancelled'
	message('The fireball explodes, burning everything within ' + str(FIREBALL_RADIUS) + ' tiles!', libtcod.orange)

	for obj in objects:  #damage every fighter in range, including the player
		if obj.distance(x, y) <= FIREBALL_RADIUS and obj.fighter:
			message('The ' + obj.name + ' gets burned for ' + str(FIREBALL_DAMAGE) + ' hit points.', libtcod.orange)
			obj.fighter.take_damage(FIREBALL_DAMAGE)

def remove_armor():
	global inventory
	#check for equipped armor and remove it
	for i in inventory:
		if i.item.armor and i.item.equipped:
			i.item.equipped = False
			i.name = i.name.replace(' (worn)', '')

def remove_weapons():
	global inventory
	#check for equipped weapons and remove it
	for i in inventory:
		if i.item.weapon and i.item.equipped:
			i.item.equipped = False
			i.name = i.name.replace(' (wielded)', '')

def message(new_msg, color = libtcod.white):
	#split the message if necessary, among multiple lines
	new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)

	for line in new_msg_lines:
		#if the buffer is full, remove the first line to make room for the new one
		if len(game_msgs) == MSG_HEIGHT:
			del game_msgs[0]

		#add the new line as a tuple, with the text and the color
		game_msgs.append( (line, color) )

def menu(header, options, width):
	if len(options) > 26: raise ValueError('Cannot have a menu with more than 26 options.')

	#calculate the total height for the header (after auto-wrap) and one line per option
	header_height = libtcod.console_get_height_rect(con, 0, 0, width, SCREEN_HEIGHT, header)
	height = len(options) + header_height

	#create an off-screen console that represents the menu's window
	window = libtcod.console_new(width, height)

	#print the header, with auto-wrap
	libtcod.console_set_default_foreground(window, libtcod.white)
	libtcod.console_print_rect_ex(window, 0, 0, width, height, libtcod.BKGND_NONE, libtcod.LEFT, header)

	#print all the options
	y = header_height
	letter_index = ord('a')
	for option_text in options:
		text = '(' + chr(letter_index) + ') ' + option_text
		libtcod.console_print_ex(window, 0, y, libtcod.BKGND_NONE, libtcod.LEFT, text)
		y += 1
		letter_index += 1

	#blit the contents of "window" to the root console
	x = SCREEN_WIDTH/2 - width/2
	y = SCREEN_HEIGHT/2 - height/2
	libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)

	#present the root console to the player and wait for a key-press
	libtcod.console_flush()
	key = libtcod.console_wait_for_keypress(True)

	if key.vk == libtcod.KEY_ENTER and key.lalt:  #(special case) Alt+Enter: toggle fullscreen
		libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

	#convert the ASCII code to an index; if it corresponds to an option, return it
	index = key.c - ord('a')
	if index >= 0 and index < len(options): return index
	return None

def inventory_menu(header):
	#show a menu with each item of the inventory as an option
	if len(inventory) == 0:
		options = ['Inventory is empty.']
	else:
		options = [item.name for item in inventory]

	index = menu(header, options, INVENTORY_WIDTH)

	#if an item was chosen, return it
	if index is None or len(inventory) == 0: return None
	return inventory[index].item

def open_menu():
	#show a menu with the cardinal directions
	open_dir = libtcod.console_wait_for_keypress(True)

	if open_dir.vk == libtcod.KEY_UP:
		return 'North'
	elif open_dir.vk == libtcod.KEY_DOWN:
		return 'South'
	elif open_dir.vk == libtcod.KEY_RIGHT:
		return 'East'
	elif open_dir.vk == libtcod.KEYleft:
		return 'West'

def msgbox(text, width=50):
	menu(text, [], width)  #use menu() as a sort of "message box"

def player_card():
	#create an off-screen console that represents the card's window
	window = libtcod.console_new(20, 20)

	#print player stats
	libtcod.console_set_default_foreground(window, libtcod.white)
	libtcod.console_print_ex(window, 1, 1, libtcod.BKGND_NONE, libtcod.LEFT, 'STR:' + str(player.fighter.str))
	libtcod.console_print_ex(window, 1, 2, libtcod.BKGND_NONE, libtcod.LEFT, 'DEX:' + str(player.fighter.dex))
	libtcod.console_print_ex(window, 1, 3, libtcod.BKGND_NONE, libtcod.LEFT, 'CON:' + str(player.fighter.con))
	libtcod.console_print_ex(window, 1, 4, libtcod.BKGND_NONE, libtcod.LEFT, 'INT:' + str(player.fighter.int))
	libtcod.console_print_ex(window, 1, 5, libtcod.BKGND_NONE, libtcod.LEFT, 'FTH:' + str(player.fighter.fth))
	libtcod.console_print_ex(window, 1, 6, libtcod.BKGND_NONE, libtcod.LEFT, 'PER:' + str(player.fighter.per))

	libtcod.console_print_ex(window, 1, 9, libtcod.BKGND_NONE, libtcod.LEFT, 'Encumbrance: ')

	#blit the contents of "window" to the root console
	libtcod.console_blit(window, 0, 0, 20, 20, 0, 1, 7, 1.0, 0.7)

	#present the root console to the player and wait for a key-press
	libtcod.console_flush()
	key = libtcod.console_wait_for_keypress(True)

	if key.vk == libtcod.KEY_ENTER and key.lalt:  #(special case) Alt+Enter: toggle fullscreen
		libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

	return None

def render_bar(x, y, total_width, name, value, maximum, bar_color, back_color):
	#render a bar (HP, experience, etc.) first calculate the width of the bar
	bar_width = int(float(value) / maximum * total_width)

	#render the background first
	libtcod.console_set_default_background(top_panel, back_color)
	libtcod.console_rect(top_panel, x, y, total_width, 1, False)

	#now render the bar on top
	libtcod.console_set_default_background(top_panel, bar_color)
	if bar_width > 0:
		libtcod.console_rect(top_panel, x, y, bar_width, 1, False)

	#finally, some centered text with the values
	libtcod.console_set_default_foreground(top_panel, libtcod.white)
	libtcod.console_print(top_panel, x + total_width / 2, y, name +
							': ' + str(value) + '/' + str(maximum))

def render_all():
	global fov_map, color_dark_wall, color_light_wall
	global color_dark_ground, color_light_ground
	global fov_recompute

	if fov_recompute:
		#recompute FOV if needed (the player moved or something)
		fov_recompute = False
		libtcod.map_compute_fov(fov_map, player.x, player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)

		#go through all tiles, and set their background color
		for y in range(MAP_HEIGHT):
			for x in range(MAP_WIDTH):
				visible = libtcod.map_is_in_fov(fov_map, x, y)
				wall = map[x][y].block_sight
				if not visible:
					#if it's not visible right now, the player can only see it if it's explored
					if map[x][y].explored:
						if wall:
							libtcod.console_set_char_background(con, x, y, color_dark_wall, libtcod.BKGND_SET)
						else:
							libtcod.console_set_char_background(con, x, y, color_dark_ground, libtcod.BKGND_SET)
				else:
					#it's visible
					if wall:
						libtcod.console_set_char_background(con, x, y, color_light_wall, libtcod.BKGND_SET )
					else:
						libtcod.console_set_char_background(con, x, y, color_light_ground, libtcod.BKGND_SET )
					#since it's visible, explore it
					map[x][y].explored = True

	#draw all objects
	for object in objects:
		if object != player:
			if (object.stairs or object.door) and map[object.x][object.y].explored:
				libtcod.console_set_default_foreground(con, object.color)
				libtcod.console_put_char(con, object.x, object.y, object.char, libtcod.BKGND_NONE)
			else:
				object.draw()
	player.draw()

	#blit 'con' to '0'
	libtcod.console_blit(con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0, PANEL_HEIGHT)

	#prepare to render the GUI panels
	libtcod.console_set_default_background(top_panel, panel_color)
	libtcod.console_set_default_background(bottom_panel, panel_color)
	libtcod.console_clear(top_panel)
	libtcod.console_clear(bottom_panel)

	#print the game messages, one line at a time
	y = 1
	for (line, color) in game_msgs:
		libtcod.console_set_default_foreground(bottom_panel, color)
		libtcod.console_print_ex(bottom_panel, MSG_X, y, libtcod.BKGND_NONE, libtcod.LEFT, line)
		y += 1

	#show the player's stats
	libtcod.console_print_ex(top_panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT, player.name + ' the ' + player.fighter.plclass)
	render_bar(1, 1, BAR_WIDTH, 'HP', player.fighter.hp, player.fighter.max_hp, libtcod.light_red, libtcod.darker_red)
	render_bar(1, 2, BAR_WIDTH, '02', player.fighter.o2, 100, libtcod.light_blue, libtcod.darker_blue)
	render_bar(1, 3, BAR_WIDTH, 'Level', 100, 100, libtcod.light_green, libtcod.darker_green)
	libtcod.console_print_ex(top_panel, 1, 2, libtcod.BKGND_NONE, libtcod.LEFT, get_names_under_mouse())

	#show the currently equipped weapon's stats
	# new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)
	libtcod.console_print_ex(top_panel, 20, 0, libtcod.BKGND_NONE, libtcod.LEFT, player.fighter.equipweapon.name[:-9])
	libtcod.console_print_ex(top_panel, 20, 1, libtcod.BKGND_NONE, libtcod.LEFT, 'Hit %: ' + str((20-player.fighter.hitdie)*5))
	libtcod.console_print_ex(top_panel, 20, 2, libtcod.BKGND_NONE, libtcod.LEFT, 'Damage: ' + str(player.fighter.mindmg) + ' - ' + str(player.fighter.maxdmg))

	#show the currently equipped armor's stats
	libtcod.console_print_ex(top_panel, 40, 0, libtcod.BKGND_NONE, libtcod.LEFT, player.fighter.equiparmor.name[:-7])
	libtcod.console_print_ex(top_panel, 40, 1, libtcod.BKGND_NONE, libtcod.LEFT, 'AC: ' + str(player.fighter.ac))

	#show the currently equipped spell (not implemented yet)
	libtcod.console_print_ex(top_panel, 60, 0, libtcod.BKGND_NONE, libtcod.LEFT, 'Fireball')

	#show current target's stats

	#display names of objects under the mouse
	libtcod.console_set_default_foreground(bottom_panel, libtcod.light_gray)
	libtcod.console_print_ex(bottom_panel, 1, 2, libtcod.BKGND_NONE, libtcod.LEFT, 'Current floor: ' + str(current_floor))

	#blit the contents of "panel" to the root console
	libtcod.console_blit(top_panel, 0, 0, SCREEN_WIDTH, PANEL_HEIGHT, 0, 0, 0)
	libtcod.console_blit(bottom_panel, 0, 0, SCREEN_WIDTH, PANEL_HEIGHT, 0, 0, PANEL_Y)

def new_game():
	global player, inventory, game_msgs, game_state, current_floor, floors, birthdaysuit, barehands
	
	#create the dungeon floor list
	floors = []
	current_floor = 0

	#create object representing the player
	armor_component = Armor(ac=0)
	item_component = Item(armor=armor_component)
	birthdaysuit = Object(0, 0, '[', 'Birthday Suit (worn)', libtcod.dark_orange, item = item_component)

	weapon_component = Weapon(mindmg=1, maxdmg=3, hitdie=2)
	item_component = Item(weapon=weapon_component)
	barehands = Object(0, 0, ')', 'Bare hands (wielded)', libtcod.light_blue, item = item_component)

	fighter_component = Fighter(plclass='Astronaut', ac=0, str=10, dex=10, con=10, int=10, fth=10, per=10, equipweapon=barehands, equiparmor=birthdaysuit, hitdie = 0, mindmg = 0, maxdmg = 0, hp=500, defense=2, power=5, o2=100, death_function=player_death)
	player = Object(0, 0, '@', 'Dwayne', libtcod.white, blocks=True, fighter=fighter_component)
	
	#while True:
		#make_map()
		# pdb.set_trace()
		#if all_rooms_are_filled():
			#break
	
	make_map()
		
	floors.append([map, objects])
			
	initialize_fov()

	#create inventory
	inventory = []

	#create the list of game messages and their colors, starts empty
	game_msgs = []

	game_state = 'playing'

	#a warm welcoming message!
	message('As you enter, you hear a disembodied voice whisper: "There is no escape here, ' + player.fighter.plclass + ', not even death."', libtcod.red)

def initialize_fov():
	global fov_recompute, fov_map

	fov_recompute = True

	#create FOV map
	fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
	for y in range(MAP_HEIGHT):
		for x in range(MAP_WIDTH):
			libtcod.map_set_properties(fov_map, x, y, not map[x][y].block_sight, not map[x][y].blocked)

	libtcod.console_clear(con)  #unexplored areas start black (which is the default background color)

def play_game():
	global key, mouse
	
	player_action = None
	
	key = libtcod.Key()
	mouse = libtcod.Mouse()

	while not libtcod.console_is_window_closed():																#MAIN LOOP
		libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE,key,mouse)
		render_all()

		#flush console to screen
		libtcod.console_flush()

		#clear object positions
		for object in objects:
			object.clear()

		player_action = handle_keys()

		if player_action == 'exit':
			save_game()
			break

		#let monsters take their turn
		if game_state == 'playing' and player_action != 'didnt-take-turn':
			handle_time()
			for object in objects:
				if object.ai:
					object.ai.take_turn()

def save_game():
	#open a new empty shelve (possibly overwriting an old one) to write the game data
	file = shelve.open('savegame', 'n')
	file['map'] = map
	file['objects'] = objects
	file['player_index'] = objects.index(player)  #index of player in objects list
	file['floors'] = floors
	file['inventory'] = inventory
	file['game_msgs'] = game_msgs
	file['game_state'] = game_state
	file.close()

def load_game():
	#open the previously saved shelve and load the game data
	global map, objects, player, inventory, game_msgs, game_state

	file = shelve.open('savegame', 'r')
	map = file['map']
	objects = file['objects']
	player = objects[file['player_index']]  #get index of player in objects list and access it
	floors = file['floors']
	inventory = file['inventory']
	game_msgs = file['game_msgs']
	game_state = file['game_state']
	file.close()

	initialize_fov()

def main_menu():
	img = libtcod.image_load('menu_background1.png')

	while not  libtcod.console_is_window_closed():
		#show the background image, at twice the regular console resolution
		libtcod.image_blit_2x(img, 0, 0, 0)

		#show the game's title, and some credits!
		libtcod.console_set_default_foreground(0, libtcod.black)
		libtcod.console_print(0, SCREEN_WIDTH/2, SCREEN_HEIGHT/2-4, 'O R B I T A L')
		libtcod.console_set_default_foreground(0, libtcod.white)
		libtcod.console_print(0, SCREEN_WIDTH/2, SCREEN_HEIGHT-2, 'By Nathaniel Berens')

		#show options and wait for the player's choice
		choice = menu(' ', ['Play a new game', 'Continue last game', 'Quit'], 24)

		if choice == 0: #new game
			new_game()
			play_game()
		elif choice == 1: #load last game
			try:
				load_game()
			except:
				msgbox('\n No saved game to load. \n', 24)
				continue
			play_game()
		elif choice == 2: #quit
			break


#INITIALIZATION AND MAIN LOOP
#------------------------------------------------------------#
#libtcod.console_set_custom_font('arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD) 	#init custom font
libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'PURGATORIO', False)								  	#init console
con = libtcod.console_new(MAP_WIDTH, MAP_HEIGHT)														#init off-screen console
top_panel = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)												#init top panel
bottom_panel = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)											#init bottom panel
libtcod.sys_set_fps(LIMIT_FPS)																			#limit fps
libtcod.console_set_alignment(0, libtcod.CENTER)																		#set console alignment

main_menu()
