import libtcodpy as libtcod
import math
import pdb

import config
import gfx
import mapgen #we don't like this, can we break circular import?

class Object:
	#this is a generic object: the config.player, a monster, an item, the stairs...
	#it's always represented by a character on screen.
	def __init__(self, x, y, char, name, color, floor=0, blocks=False, stats=None, fighter=None, ai=None, item=None, 
				corpse=None, node=None, flare=None, stairs=None, door=None, fungus=None, pool=None, bombpart=None):
		self.name = name
		self.blocks = blocks
		self.x = x
		self.y = y
		self.char = char
		self.color = color
		self.floor = config.current_floor
		
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

		self.corpse = corpse
		if self.corpse: #let the corpse component know who owns it
			self.corpse.owner = self

		self.node = node
		if self.node:
			self.node.owner = self

		self.flare = flare
		if self.flare:
			self.flare.owner = self
		
		self.stairs = stairs
		if self.stairs: #let the stairs component know who owns it
			self.stairs.owner = self
		
		self.door = door
		if self.door: #let the door component know who owns it
			self.door.owner = self
		
		self.fungus = fungus
		if self.fungus:
			self.fungus.owner = self
		
		self.pool = pool
		if self.pool:
			self.pool.owner = self

		self.bombpart = bombpart
		if self.bombpart:
			self.bombpart.owner = self
	
	def move(self, dx, dy):
		
		if self == config.beast:
			if config.map[config.beast.x + dx][config.beast.y + dy].water: 
				return
			
			#not working
			if config.map[config.beast.x + dx][config.beast.y + dy].flared:
				return

		#check if destination tile is blocked		
		if not config.map[self.x + dx][self.y + dy].blocked:
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
		config.objects.remove(self)
		config.objects.insert(0, self)
	
	def draw(self):

		for n in config.nodes:
			if libtcod.map_is_in_fov(n.node.fov_map, self.x, self.y):
				libtcod.console_set_default_foreground(gfx.con, self.color)
				libtcod.console_put_char(gfx.con, self.x, self.y, self.char, libtcod.BKGND_NONE)

		if libtcod.map_is_in_fov(config.fov_map, self.x, self.y):
			#set the color and then draw the character that represents this object at its position
			libtcod.console_set_default_foreground(gfx.con, self.color)
			libtcod.console_put_char(gfx.con, self.x, self.y, self.char, libtcod.BKGND_NONE)
		#DEBUG: Show all config.objects
		# libtcod.console_set_default_foreground(gfx.con, self.color)
		# libtcod.console_put_char(gfx.con, self.x, self.y, self.char, libtcod.BKGND_NONE)
	
	def clear(self):
		#erase the character that represents this object
		if libtcod.map_is_in_fov(config.fov_map, self.x, self.y):
			#libtcod.console_put_char_ex(con, self.x, self.y, ' ', libtcod.white, color_light_ground)
			libtcod.console_put_char(gfx.con, self.x, self.y, ' ')

class Stats:
	#statistics for the config.player character
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
	def __init__(self, plclass, ac, str, dex, con, int, fth, per, equipweapon, 
				equiparmor, equipscanner, equipheadlamp, equiptank, equipcamo, hitdie, 
				mindmg, maxdmg, hp, power, defense, o2, death_function=None):

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
		self.equipscanner = equipscanner
		self.equipheadlamp = equipheadlamp
		self.equiptank = equiptank
		self.equipcamo = equipcamo
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
				# function(self.owner)
				function()
	
	def manage_oxygen(self, oxygen):
		#each turn reduce oxygen by 1
		self.o2 += oxygen
		
		#check for suffocation
		if self.o2 <= 0:
			# function = self.death_function
			# if function is not None:
			# 	function()
			self.take_damage(15);
	
	def attack(self, target):
		
		#if config.player, use config.player attack stats
		hitdie = self.hitdie
		mindmg = self.mindmg
		maxdmg = self.maxdmg
		
		if libtcod.random_get_int(0,1,20) > hitdie:
			#hit!
			gfx.message('hit!')
			#determine damage
			damage = libtcod.random_get_int(0, mindmg, maxdmg) - target.fighter.defense
		else:
			#miss!
			gfx.message('miss!')
			damage = 0
		
		if damage > 0:
			#make the target take some damage
			gfx.message(self.owner.name.capitalize() + ' attacks ' + target.name + ' for ' + str(damage) + ' hit points.')
			target.fighter.take_damage(damage)
		else:
			gfx.message(self.owner.name.capitalize() + ' attacks ' + target.name + ' but it has no effect!')
	
	def heal(self, amount):
		#heal by the given amount, without going over the maximum
		self.hp += amount
		if self.hp > self.max_hp:
			self.hp = self.max_hp

	def is_camouflaged(self):
		#pdb.set_trace()
		for i in config.inventory:
			if i.item.camo and i.item.equipped:
				return True
		
		return False				

class BasicMonster:
	#AI for a basic monster.
	def take_turn(self):
		#a basic monster takes its turn. if you can see it, it can see you
		monster = self.owner
		if libtcod.map_is_in_fov(config.fov_map, monster.x, monster.y):
			
			#move towards config.player if far away
			if monster.distance_to(config.player) >= 2:
				monster.move_towards(config.player.x, config.player.y)
			
			#close enough, attack! (if the config.player is still alive.)
			elif config.player.fighter.hp > 0:
				monster.fighter.attack(config.player)

class Beast:
	#AI for The Beast
	def take_turn(self):
		config.beast = self.owner

		#config.Player is in config.beast's FOV
		if libtcod.map_is_in_fov(config.beast_fov_map, config.player.x, config.player.y) and not config.player.fighter.is_camouflaged():
			#move towards config.player if far away
			if config.beast.distance_to(config.player) >= 2:
				config.beast.move_towards(config.player.x, config.player.y)
			#close enough to attack
			# elif config.player.fighter.hp > 0:
				#config.beast.fighter.attack(config.player)
		#move randomly
		else:
			move = libtcod.random_get_int(0, 0, 3)
			
			if move == 0: #move up
					config.beast.move(0, -1)
			elif move == 1: #move down
					config.beast.move(0, 1)
			elif move == 2: #move left
					config.beast.move(-1, 0)
			else: 	#move right
					config.beast.move(1, 0)
				
class Item:
	#an item that can be picked up and used.
	def __init__(self, use_function=None, equipped=False, armor=None, weapon=None, scanner=None, headlamp=False, 
					tank=False, siphon=False, node=None, camo=None, flare=None, bomb=None):
		self.use_function = use_function
		self.equipped = equipped
		self.armor = armor
		self.weapon = weapon
		self.scanner = scanner
		self.headlamp = headlamp
		self.tank = tank
		self.siphon = siphon
		self.node = node
		self.camo = camo
		self.flare = flare
		self.bomb = bomb

	def pick_up(self):
		#add the config.player's config.inventory and remove from the map

		if len(config.inventory) >= 26:
			gfx.message('Your config.inventory is full - cannot pick up ' + self.owner.name + '.', libtcod.red)
		else:
			config.inventory.append(self.owner)
			config.objects.remove(self.owner)
			gfx.message('You picked up a ' + self.owner.name + '!', libtcod.green)
	
	def use(self):
		#just call the "use_function" if it is defined
		if self.use_function is None:
			gfx.message('The ' + self.owner.name + ' cannot be used.')
		else:
			if self.use_function() != 'cancelled':
				config.inventory.remove(self.owner) #destroy after use, unless it was cancelled for some reason
	
	def drop(self):
		#add to the map and remove from the config.player's config.inventory. also, place it at the config.player's coordinates.
		config.objects.append(self.owner)
		config.inventory.remove(self.owner)
		self.owner.x = config.player.x
		self.owner.y = config.player.y
		gfx.message('You dropped a ' + self.owner.name + '.', libtcod.yellow)
	
	def equip_armor(self):
		
		if not self.equipped:
			remove_armor()
			self.equipped = True
			self.owner.name = self.owner.name + ' (worn)'
			config.player.fighter.equiparmor = self.owner
			config.player.fighter.buff_stats(self.armor.ac, self.armor.s, self.armor.d, self.armor.c, self.armor.i, self.armor.f, self.armor.p)
		else:
			self.equipped = False
			self.owner.name = self.owner.name.replace(' (worn)', '')
			config.player.fighter.equiparmor = birthdaysuit
			config.player.fighter.debuff_stats(self.armor.ac, self.armor.s, self.armor.d, self.armor.c, self.armor.i, self.armor.f, self.armor.p)
	
	def equip_weapon(self):
		
		#check for equipped weapons
		
		if not self.equipped:
			remove_weapons()
			self.equipped = True
			self.owner.name = self.owner.name + ' (wielded)'
			config.player.fighter.equipweapon = self.owner
			config.player.fighter.hitdie = self.weapon.hitdie
			config.player.fighter.mindmg = self.weapon.mindmg
			config.player.fighter.maxdmg = self.weapon.maxdmg
		else:
			self.equipped = False
			self.owner.name = self.owner.name.replace(' (wielded)', '')
			config.player.fighter.equipweapon = barehands
			config.player.fighter.hitdie = 0
			config.player.fighter.mindmg = 0
			config.player.fighter.maxdmg = 0
	
	def equip_scanner(self):
		#check for equipped scanner
		
		if not self.equipped:
			self.remove_scanners()
			self.equipped = True
			self.owner.name = self.owner.name + ' (equipped)'
			config.player.fighter.equipscanner = self.owner
		else:
			self.remove_scanners()

	def remove_scanners(self):
		#check for equipped weapons and remove it
		for i in config.inventory:
			if i.item.scanner and i.item.equipped:
				i.item.equipped = False
				i.name = i.name.replace(' (equipped)', '')

	def equip_headlamp(self):
		#check for equipped headlamp

		if not self.equipped:
			self.remove_headlamps()
			self.equipped = True
			self.owner.name = self.owner.name + ' (equipped)'
			config.player.fighter.equipheadlamp = self.owner
			config.fov_radius = config.TORCH_RADIUS + 5
			config.beast_fov_radius = config.BEAST_SIGHT_RADIUS + 2
			gfx.render_all()
		else:
			# self.equipped = False
			# self.owner.name = self.owner.name.replace(' (equipped)', '')
			# config.player.fighter.equipheadlamp = None
			self.remove_headlamps()

	def remove_headlamps(self):
		#check for equipped headlamps and remove them
		for i in config.inventory:
			if i.item.headlamp and i.item.equipped:
				i.item.equipped = False
				i.name = i.name.replace(' (equipped)', '')
				config.fov_radius = config.TORCH_RADIUS
				config.beast_fov_radius = config.BEAST_SIGHT_RADIUS
				gfx.render_all()

	def equip_tank(self):
		#check for equipped headlamp

		if not self.equipped:
			self.remove_tanks()
			self.equipped = True
			self.owner.name = self.owner.name + ' (equipped)'
			config.player.fighter.equiptank = self.owner
			config.max_o2 = config.max_o2 * 2
		else:
			self.remove_tanks()

	def remove_tanks(self):
		#check for equipped headlamps and remove them
		for i in config.inventory:
			if i.item.tank and i.item.equipped:
				i.item.equipped = False
				i.name = i.name.replace(' (equipped)', '')

	def equip_camo(self):
		if not self.equipped:
			self.remove_camo()
			self.equipped = True
			self.owner.name = self.owner.name + ' (equipped)'
			config.player.fighter.equipcamo = self.owner
			config.player.color = libtcod.gray
		else:
			self.remove_camo()

	def remove_camo(self):
		#check for equipped headlamps and remove them
		for i in config.inventory:
			if i.item.camo and i.item.equipped:
				i.item.equipped = False
				i.name = i.name.replace(' (equipped)', '')
				config.player.color = libtcod.white

	def plant_node(self):
		#drop a node and remove a charge
		#if last charge, remove and destroy item
		
		node_component = PlantedNode()
		planted_node = Object(config.player.x, config.player.y, 'n', 'deployed scanner node', libtcod.light_blue, node = node_component)

		config.objects.append(planted_node)
		config.nodes.append(planted_node)
		
		self.node.charges -= 1
		self.owner.name = 'remote scanner nodes (' + str(self.node.charges) + ')'

		if self.node.charges == 0:
			config.inventory.remove(self.owner)

		gfx.render_all()

	def drop_flare(self):

		flare_component = DroppedFlare()
		dropped_flare = Object(config.player.x, config.player.y, 'f', 'lit signal flare', libtcod.light_blue, flare = flare_component)

		config.objects.append(dropped_flare)
		config.flares.append(dropped_flare)
		config.inventory.remove(self.owner)

		gfx.render_all()

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

class Scanner:
	def __init__(self):
		return
	
	def ping(self, scanner_primed):
		#show all explored map tiles, stairs, and doors
		#flag each tile as 'scanned' for one turn
		#have gfx.render_all() display scanned tiles
		for x in range(config.MAP_WIDTH):
			for y in range(config.MAP_HEIGHT):
				if config.map[x][y].explored and scanner_primed == True:
					config.map[x][y].scanned = True
				elif config.map[x][y].explored and scanner_primed == False:
					config.map[x][y].scanned = False	

class ScannerNode:
	def __init__(self):
		self.charges = 3

class PlantedNode:
	def __init__(self):
		#create new fov_map for area around planted node
		#add to array of nodes, have render_all cycle through all nodes
		self.fov_map = libtcod.map_new(config.MAP_WIDTH, config.MAP_HEIGHT)
		for y in range(config.MAP_HEIGHT):
			for x in range(config.MAP_WIDTH):
				libtcod.map_set_properties(self.fov_map, x, y, not config.map[x][y].block_sight, not config.map[x][y].blocked)

class RCamo:
	def __init__(self):
		self.charge = 20

class DroppedFlare:
	def __init__(self):
		self.lifespan = 50
		self.radius = config.FLARE_RADIUS

		self.fov_map = libtcod.map_new(config.MAP_WIDTH, config.MAP_HEIGHT)
		for y in range(config.MAP_HEIGHT):
			for x in range(config.MAP_WIDTH):
				libtcod.map_set_properties(self.fov_map, x, y, not config.map[x][y].block_sight, not config.map[x][y].blocked)

	def clear_flare(self):

		self.owner.clear()
		config.flares.remove(self.owner)

		for y in range(config.MAP_HEIGHT):
			for x in range(config.MAP_WIDTH):
				if libtcod.map_is_in_fov(self.fov_map, x, y):
						config.map[x][y].flared = False

class Corpse:
	#a fellow science team member that carries a usable item
	def __init__(self, item=None):
		self.item = item
	
	def pick_up(self):
		#add the config.player's config.inventory and remove from the map
		if self.item == None:
			gfx.message('You comb over the body and find nothing of use.', libtcod.yellow)
		else:
			if self.item.item.siphon:
				gfx.message('You\'ve siphoned oxygen off of the corpse!')
				config.player.fighter.o2 = config.max_o2
				self.item = None
			else:
				if len(config.inventory) >= 26:
					gfx.message('Your config.inventory is full - cannot pick up ' + self.item.name + '.', libtcod.red)
				else:
					config.inventory.append(self.item)
					gfx.message('You picked up a ' + self.item.name + '!', libtcod.green)
					self.item = None

class BombPart:
	def __init__(self):
		return

	def pick_up(self):
		config.bomb_parts_collected += 1
		config.objects.remove(self.owner)

		if config.bomb_parts_collected < 5:
			gfx.message("You pick up a bomb component. (" + str(config.TOTAL_BOMB_PARTS - config.bomb_parts_collected) + " remaining)")	#add num_remaining
		elif config.bomb_parts_collected == 5:
			bomb_component = Bomb()
			item_component = Item(bomb=bomb_component)
			bomb = Object(config.player.x, config.player.y, 'B', 'armed nuclear bomb', libtcod.yellow, item = item_component)
			config.inventory.append(bomb)
			gfx.message("You have all the bomb components. Place the bomb on the final floor.")

class Bomb:
	def __init__(self):
		return

	def plant_bomb(self):
		
		#for now, just win game
		#eventually, allow player to try to escape... show bomb timer
		return

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
		
		self.open = True
		gfx.message('You open the door.', libtcod.white)
		self.owner.char = '/'
		config.map[self.owner.x][self.owner.y].blocked = False
		config.map[self.owner.x][self.owner.y].block_sight = False
		self.owner.name = 'An open door'
		self.owner.send_to_back()
		config.fov_recompute = True
		gfx.render_all()
	
	def close_door(self):
		
		self.open = False
		gfx.message('You close the door.', libtcod.white)
		self.owner.char = '+'
		config.map[self.owner.x][self.owner.y].blocked = True
		config.map[self.owner.x][self.owner.y].block_sight = True
		self.owner.name = 'A closed door'
		config.fov_recompute = True
		gfx.render_all()

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
		
class Pool:
	#pool of water, blood, or lava
	def __init__(self, water=None, blood=None, lava=None):
		self.water = water
		self.blood = blood
		self.lava = lava
		return

def closest_monster(max_range):
	#find closest enemy, up to a maximum range, and in the config.player's FOV
	closest_enemy = None
	closest_dist = max_range + 1 #start with (slightly more than maximum range)
	
	for object in config.objects:
		if object.fighter and not object == config.player and libtcod.map_is_in_fov(config.fov_map, object.x, object.y):
			#calculate the distance between this object and the config.player
			dist = config.player.distance_to(object)
			if dist < closest_dist: #it's closer, so remember it
				closest_enemy = object
				closest_dist = dist
	return closest_enemy

def handle_keys(key):	#handle keyboard commands
	global playerx, playery

	#other functions
	if key.vk == libtcod.KEY_ENTER and key.lalt:
		#Alt+Enter: toggle fullscreen
		libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
	
	elif key.vk == libtcod.KEY_ESCAPE:
		#Escape: exit game
		return 'exit'
	
	#movement keys
	if config.game_state == 'playing':
		
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
				for object in config.objects: #look for an item in the config.player's tile
					if object.x == config.player.x and object.y == config.player.y:
						if object.item:
							object.item.pick_up()
						elif object.corpse:
							object.corpse.pick_up()
						elif object.bombpart:
							object.bombpart.pick_up()
						break
			
			if key_char == 'i':
				#show the config.inventory
				chosen_item = gfx.inventory_menu('Press the key next to an item to use it, or any other to cancel.\n')
				if chosen_item is not None:
					if chosen_item.armor:
						chosen_item.equip_armor()
					elif chosen_item.weapon:
						chosen_item.equip_weapon()
					elif chosen_item.tank:
						chosen_item.equip_tank()
					elif chosen_item.headlamp:
						chosen_item.equip_headlamp()
					elif chosen_item.camo:
						chosen_item.equip_camo()
					elif chosen_item.node:
						chosen_item.plant_node()
					elif chosen_item.flare:
						chosen_item.drop_flare()
					elif chosen_item.bomb:
						chosen_item.bomb.plant_bomb()
						return 'win'
			
			if key_char == 'd':
				#show the config.inventory; if an item is selected, drop it
				chosen_item = gfx.inventory_menu('Press the key next to an item to (d)rop it, or any other to cancel.\n')
				if chosen_item is not None:
					chosen_item.drop()
			
			if key_char == 'c':
				#show the config.player card until config.player presses 'c' or 'esc'
				gfx.player_card()
			
			if key_char == 'o':
				#search for adjacent doors and open/close them
				for object in config.objects:
					if object.door and object.x <= config.player.x+1 and object.x >= config.player.x-1 and object.y <= config.player.y+1 and object.y >= config.player.y-1:
						if object.door.open:
							object.door.close_door()
						else:
							object.door.open_door()
			
			if key_char == 'p':
				#ping map using scanner
				for i in config.inventory:
					if i.item.scanner and i.item.equipped:
						i.item.scanner.ping(True)
						gfx.message('You pinged the map.', libtcod.white)
						config.fov_recompute = True
						gfx.render_all()
						i.item.scanner.ping(False)
				
			#ascending
			if key_char == ',' or key_char == '<':
				#move up a floor
				#check if on staircase
				for object in config.objects:
					if object.stairs and config.player.x == object.x and config.player.y == object.y:
						#config.player is on stairs
						if object.stairs.direction == "up":
							if config.current_floor==0:
								gfx.message('There is no escape.', libtcod.red)
							else:
								#there's a floor above, so let him ascend
								go_to_floor(config.current_floor-1)
								break
						elif object.stairs.direction == "down":
							#config.player is on downward stairs
							gfx.message('These stairs lead down!', libtcod.red)
							break
			
			#descending
			if key_char == '.' or key_char == '>':
				#move down a floor
				#check if on staircase
				for object in config.objects:
					if object.stairs and config.player.x == object.x and config.player.y == object.y:
						#config.player is on stairs
						if object.stairs.direction == "down":
								go_to_floor(config.current_floor+1)
								break
						elif object.stairs.direction == "up":
							#config.player is on downward stairs
							gfx.message('These stairs lead up!', libtcod.red)
							break
			
			return 'didnt-take-turn'

def handle_time():
	#pdb.set_trace()
	config.turns += 1

	if config.player.fighter.is_camouflaged():
		for i in config.inventory:
			if i.item.camo and i.item.equipped:
				if i.item.camo.charge <= 0:
					remove_camo()
					config.inventory.remove(i)
					config.player.color = libtcod.white
				else:
					i.item.camo.charge -= 1
					i.name = 'refractive camo (' + str(i.item.camo.charge) + ')'

	for f in config.flares:
		if f.flare.lifespan <= 0:
			f.flare.clear_flare()
		else:
			f.flare.lifespan -= 1

	on_fungus = False
	
	for object in config.objects:
		if object.x == config.player.x and object.y == config.player.y and object.fungus:
			on_fungus = True
			if config.player.fighter.o2 < config.max_o2:
				config.player.fighter.manage_oxygen(20)
	
	if on_fungus == False:
		if config.player.fighter.o2 > 0:
			config.player.fighter.manage_oxygen(-1)

	#sound_proximity()

def sound_proximity():
	#detect sound emanating Objects nearby

	for object in config.objects:
		if object == config.beast and config.beast.distance_to(config.player) < 16:
			gfx.message("You hear scraping footsteps and a rumbling growl.", libtcod.blue)
		elif object.stairs and object.distance_to(config.player) < 10:
			gfx.message("You hear a faint gust of wind.", libtcod.blue)
		elif object.pool and object.distance_to(config.player) < 8:
			gfx.message("You hear the sloshing of gentle waves nearby.", libtcod.blue)

def go_to_floor(dest):

	#pdb.set_trace()
	
	if dest > (len(config.floors)-1):
		#floor has not been generated yet, so generate it
		#store previous floor
		config.floors[config.current_floor][0] = config.map
		config.floors[config.current_floor][1] = config.objects
		config.floors[config.current_floor][2] = config.nodes
		config.floors[config.current_floor][3] = config.flares
		mapgen.make_map()
		config.floors.append([config.map, config.objects, config.nodes, config.flares])
	else:
		#floor has been generated
		config.map = config.floors[dest][0]
		config.objects = config.floors[dest][1]
		config.nodes = config.floors[dest][2]
		config.flares = config.floors[dest][3]
		
		if dest < config.current_floor:
			#ascending
			for object in config.objects:
				if object.stairs and object.stairs.direction == "down":
					#find location of stairs_down from destination floor and place config.player there
					config.player.x = object.x
					config.player.y = object.y
					break
		elif dest > config.current_floor:
			#descending
			for object in config.objects:
				if object.stairs and object.stairs.direction == "up":
					#find location of stairs_down from destination floor and place config.player there
					config.player.x = object.x
					config.player.y = object.y
					break
		else:
			gfx.message('Something\'s kinda weird.', libtcod.red)
	
	config.current_floor = dest
	
	gfx.initialize_fov()

def get_names_under_mouse():
	global mouse
	
	#return a string with the names of all config.objects under the mouse
	(x, y) = (mouse.cx, mouse.cy)
	
	#create a list with the names of all config.objects at the mouse's coordinates and in FOV
	names = [obj.name for obj in config.objects
		if obj.x == x and obj.y == y and libtcod.map_is_in_fov(config.fov_map, obj.x, obj.y)]
	
	names = ', '.join(names)  #join the names, separated by commas
	return names.capitalize()

def target_tile(max_range=None):
	global key, mouse
	#return the position of a tile libtcod.LEFT-clicked in config.player's FOV (optionally in a range), or (None, None) if right-clicked.
	while True:
		#render the screen. this erases the config.inventory and shows the names of config.objects under the mouse.
		gfx.render_all()
		libtcod.console_flush()
		
		key = libtcod.console_check_for_keypress()
		mouse = libtcod.mouse_get_status() #get mouse position and click status
		(x, y) = (mouse.cx, mouse.cy)
		
		if (mouse.lbutton_pressed and libtcod.map_is_in_fov(config.fov_map, x, y) and
			(max_range is None or config.player.distance(x, y) <= max_range)):
			return (x, y)
		
		if mouse.rbutton_pressed or key.vk == libtcod.KEY_ESCAPE:
			return (None, None) #cancel if the config.player right-clicked or pressed escape

def target_monster(max_range=None):
	#returns a clicked monster inside FOV up to a range, or None if right-clicked
	while True:
		(x,y) = target_tile(max_range)
		if x is None: #config.player cancelled
			return None
		
		#return the first clicked-monster, otherwise continue looping
		for obj in config.objects:
			if obj.x == x and obj.y == y and obj.fighter and obj != config.player:
				return obj

def player_move_or_attack(dx, dy):
	
	#the coordinates the config.player is moving to/attacking
	x = config.player.x + dx
	y = config.player.y + dy
	
	#try to find an attackable object there
	target = None
	for object in config.objects:
		if object.fighter and object.x == x and object.y == y:
			target = object
			break
	
	#attack if target found, move otherwise
	if target is not None:
		config.player.fighter.attack(target)
	else:
		config.player.move(dx, dy)
		config.fov_recompute = True

def player_death():
	#the game ended!
	gfx.message('You died!', libtcod.red)
	config.game_state = 'dead'
	
	#for added effect, transform the config.player into a corpse!
	config.player.char = '%'
	config.player.color = libtcod.dark_red

def monster_death(monster):
	#transform it into a nasty corpse! it doesn't block, can't be attacked, and doesn't move
	gfx.message(monster.name.capitalize() + ' is dead!', libtcod.orange)
	monster.char = '%'
	monster.color = libtcod.dark_red
	monster.blocks = False
	monster.fighter = None
	monster.ai = None
	monster.name = 'remains of ' + monster.name
	monster.send_to_back()

def remove_armor():
	#check for equipped armor and remove it
	for i in config.inventory:
		if i.item.armor and i.item.equipped:
			i.item.equipped = False
			i.name = i.name.replace(' (worn)', '')

def remove_weapons():
	#check for equipped weapons and remove it
	for i in config.inventory:
		if i.item.weapon and i.item.equipped:
			i.item.equipped = False
			i.name = i.name.replace(' (wielded)', '')