import libtcodpy as libtcod
import textwrap
import config
import pdb

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
color_light_water = libtcod.Color(17,70,68)
panel_color = libtcod.Color(26,13,22)

#Tutorial
# color_dark_wall = libtcod.Color(0, 0, 100)
# color_light_wall = libtcod.Color(130, 110, 50)
# color_dark_ground = libtcod.Color(50, 50, 150)
# color_light_ground = libtcod.Color(200, 180, 50)

def message(new_msg, color = libtcod.white):
	#split the message if necessary, among multiple lines
	new_msg_lines = textwrap.wrap(new_msg, config.MSG_WIDTH)
	
	for line in new_msg_lines:
		#if the buffer is full, remove the first line to make room for the new one
		if len(config.game_msgs) == config.MSG_HEIGHT:
			del config.game_msgs[0]
		
		#add the new line as a tuple, with the text and the color
		config.game_msgs.append( (line, color) )

def menu(header, options, width):
	global con

	if len(options) > 26: raise ValueError('Cannot have a menu with more than 26 options.')
	
	#calculate the total height for the header (after auto-wrap) and one line per option
	header_height = libtcod.console_get_height_rect(con, 0, 0, width, config.SCREEN_HEIGHT, header)
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
	x = config.SCREEN_WIDTH/2 - width/2
	y = config.SCREEN_HEIGHT/2 - height/2
	libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)
	
	#present the root console to the config.player and wait for a key-press
	libtcod.console_flush()
	key = libtcod.console_wait_for_keypress(True)
	
	if key.vk == libtcod.KEY_ENTER and key.lalt:  #(special case) Alt+Enter: toggle fullscreen
		libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
	
	#convert the ASCII code to an index; if it corresponds to an option, return it
	index = key.c - ord('a')
	if index >= 0 and index < len(options): return index
	return None

def inventory_menu(header):
	#show a menu with each item of the config.inventory as an option
	if len(config.inventory) == 0:
		options = ['config.Inventory is empty.']
	else:
		options = [item.name for item in config.inventory]
	
	index = menu(header, options, config.INVENTORY_WIDTH)
	
	#if an item was chosen, return it
	if index is None or len(config.inventory) == 0: return None
	return config.inventory[index].item

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
	window = libtcod.console_new(30, 20)
	
	#print config.player stats
	libtcod.console_set_default_foreground(window, libtcod.white)
	libtcod.console_print_ex(window, 1, 1, libtcod.BKGND_NONE, libtcod.LEFT, 'STR:' + str(config.player.fighter.str))
	libtcod.console_print_ex(window, 1, 2, libtcod.BKGND_NONE, libtcod.LEFT, 'DEX:' + str(config.player.fighter.dex))
	libtcod.console_print_ex(window, 1, 3, libtcod.BKGND_NONE, libtcod.LEFT, 'CON:' + str(config.player.fighter.con))
	libtcod.console_print_ex(window, 1, 4, libtcod.BKGND_NONE, libtcod.LEFT, 'INT:' + str(config.player.fighter.int))
	libtcod.console_print_ex(window, 1, 5, libtcod.BKGND_NONE, libtcod.LEFT, 'FTH:' + str(config.player.fighter.fth))
	libtcod.console_print_ex(window, 1, 6, libtcod.BKGND_NONE, libtcod.LEFT, 'PER:' + str(config.player.fighter.per))
	
	libtcod.console_print_ex(window, 1, 9, libtcod.BKGND_NONE, libtcod.LEFT, 'Encumbrance: ')
	
	#blit the contents of "window" to the root console
	libtcod.console_blit(window, 0, 0, 30, 20, 0, 1, 7, 1.0, 0.7)
	
	#present the root console to the config.player and wait for a key-press
	libtcod.console_flush()
	key = libtcod.console_wait_for_keypress(True)
	
	if key.vk == libtcod.KEY_ENTER and key.lalt:  #(special case) Alt+Enter: toggle fullscreen
		libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
	
	return None

def render_bar(x, y, total_width, name, value, maximum, bar_color, back_color):
	global top_panel, bottom_panel
	#render a bar (HP, experience, etc.) first calculate the width of the bar
	config.bar_width = int(float(value) / maximum * total_width)
	
	#render the background first
	libtcod.console_set_default_background(top_panel, back_color)
	libtcod.console_rect(top_panel, x, y, total_width, 1, False)
	
	#now render the bar on top
	libtcod.console_set_default_background(top_panel, bar_color)
	if config.bar_width > 0:
		libtcod.console_rect(top_panel, x, y, config.bar_width, 1, False)
	
	#finally, some centered text with the values
	libtcod.console_set_default_foreground(top_panel, libtcod.white)
	libtcod.console_print(top_panel, x + total_width / 2, y, name +
							': ' + str(value) + '/' + str(maximum))

def render_all():
	global color_dark_wall, color_light_wall
	global color_dark_ground, color_light_ground
	global top_panel, bottom_panel
	global con

	if config.fov_recompute:
		#recompute FOV if needed (the config.player moved or something)
		config.fov_recompute = False
		libtcod.map_compute_fov(config.fov_map, config.player.x, config.player.y, config.fov_radius, config.FOV_LIGHT_WALLS, config.FOV_ALGO)
		libtcod.map_compute_fov(config.beast_fov_map, config.beast.x, config.beast.y, config.beast_fov_radius, config.FOV_LIGHT_WALLS, config.FOV_ALGO)

		for n in config.nodes:
			libtcod.map_compute_fov(n.node.fov_map, n.x, n.y, config.NODE_SIGHT_RADIUS, config.FOV_LIGHT_WALLS, config.FOV_ALGO)

		for f in config.flares:
			libtcod.map_compute_fov(f.flare.fov_map, f.x, f.y, config.FLARE_RADIUS, config.FOV_LIGHT_WALLS, config.FOV_ALGO)
		
		#go through all tiles, and set their background color
		for y in range(config.MAP_HEIGHT):
			for x in range(config.MAP_WIDTH):
				visible = False
				flared = False
				wall = False
				water = False

				if libtcod.map_is_in_fov(config.fov_map, x, y):
					visible = True

				for n in config.nodes:
					if libtcod.map_is_in_fov(n.node.fov_map, x, y):
						visible = True

				for f in config.flares:
					if libtcod.map_is_in_fov(f.flare.fov_map, x, y):
						config.map[x][y].flared = True

				wall = config.map[x][y].block_sight
				water = config.map[x][y].water
				flared = config.map[x][y].flared
				if not visible:
					#if it's not visible right now, the config.player can only see it if it's explored
					if config.map[x][y].explored and config.map[x][y].scanned:
						if wall:
							libtcod.console_set_char_background(con, x, y, color_dark_wall, libtcod.BKGND_SET)
						else:
							libtcod.console_set_char_background(con, x, y, color_dark_ground, libtcod.BKGND_SET)
					else:
						libtcod.console_set_char_background(con, x, y, libtcod.Color(0,0,0), libtcod.BKGND_SET)
				else:
					#it's visible
					if wall:
						libtcod.console_set_char_background(con, x, y, color_light_wall, libtcod.BKGND_SET )
					else:
						libtcod.console_set_char_background(con, x, y, color_light_ground, libtcod.BKGND_SET )

					if flared:
						libtcod.console_set_char_background(con, x, y, libtcod.Color(80,80,40), libtcod.BKGND_SCREEN)

					if water: 
						libtcod.console_set_char_background(con, x, y, color_light_water, libtcod.BKGND_SET)
					#since it's visible, explore it
					config.map[x][y].explored = True
				
				#DEBUG: NO FOG OF WAR
				# if wall:
				# 	libtcod.console_set_char_background(con, x, y, color_light_wall, libtcod.BKGND_SET )
				# elif water: 
				# 	libtcod.console_set_char_background(con, x, y, color_light_water, libtcod.BKGND_SET)
				# else:
				# 	libtcod.console_set_char_background(con, x, y, color_light_ground, libtcod.BKGND_SET )
	
	#draw all objects
	for object in config.objects:
		if object != config.player:
			if (object.stairs or object.door) and config.map[object.x][object.y].explored:
				libtcod.console_set_default_foreground(con, object.color)
				libtcod.console_put_char(con, object.x, object.y, object.char, libtcod.BKGND_NONE)
			else:
				object.draw()
			#DEBUG: NO FOG OF WAR
			#object.draw()
	config.player.draw()
	
	#blit 'con' to '0'
	libtcod.console_blit(con, 0, 0, config.MAP_WIDTH, config.MAP_HEIGHT, 0, 0, config.PANEL_HEIGHT)
	
	#prepare to render the GUI panels
	libtcod.console_set_default_background(top_panel, panel_color)
	libtcod.console_set_default_background(bottom_panel, panel_color)
	libtcod.console_clear(top_panel)
	libtcod.console_clear(bottom_panel)
	
	#print the game messages, one line at a time
	y = 1
	for (line, color) in config.game_msgs:
		libtcod.console_set_default_foreground(bottom_panel, color)
		libtcod.console_print_ex(bottom_panel, config.MSG_X, y, libtcod.BKGND_NONE, libtcod.LEFT, line)
		y += 1
	
	#show the config.player's stats
	libtcod.console_print_ex(top_panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT, config.player.name + ' the ' + config.player.fighter.plclass)
	render_bar(1, 1, config.BAR_WIDTH, 'HP', config.player.fighter.hp, config.player.fighter.max_hp, libtcod.light_red, libtcod.darker_red)
	render_bar(1, 2, config.BAR_WIDTH, '02', config.player.fighter.o2, config.max_o2, libtcod.light_blue, libtcod.darker_blue)
	#render_bar(1, 3, config.BAR_WIDTH, 'Level', 100, 100, libtcod.light_green, libtcod.darker_green)
	#libtcod.console_print_ex(top_panel, 1, 3, libtcod.BKGND_NONE, libtcod.LEFT, get_names_under_mouse())
	
	#show the currently equipped weapon's stats
	# new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)
	# libtcod.console_print_ex(top_panel, 30, 0, libtcod.BKGND_NONE, libtcod.LEFT, config.player.fighter.equipweapon.name[:-9])
	# libtcod.console_print_ex(top_panel, 30, 1, libtcod.BKGND_NONE, libtcod.LEFT, 'Hit %: ' + str((20-config.player.fighter.hitdie)*5))
	# libtcod.console_print_ex(top_panel, 30, 2, libtcod.BKGND_NONE, libtcod.LEFT, 'Damage: ' + str(config.player.fighter.mindmg) + ' - ' + str(config.player.fighter.maxdmg))
	libtcod.console_print_ex(top_panel, 30, 0, libtcod.BKGND_NONE, libtcod.LEFT, 'Equipped:')
	libtcod.console_print_ex(top_panel, 30, 1, libtcod.BKGND_NONE, libtcod.LEFT, 'Space Suit')	
	if config.player.fighter.equipcamo:
		libtcod.console_print_ex(top_panel, 30, 2, libtcod.BKGND_NONE, libtcod.LEFT, "Refractive Camouflage")
	if config.player.fighter.equipheadlamp:
		libtcod.console_print_ex(top_panel, 30, 3, libtcod.BKGND_NONE, libtcod.LEFT, "Headlamp")
	if config.player.fighter.equiptank:
		libtcod.console_print_ex(top_panel, 30, 4, libtcod.BKGND_NONE, libtcod.LEFT, "Oxygen Tank")
	#if config.player.fighter.equipdrill:
	#	libtcod.console_print_ex(top_panel, 30, 5, libtcod.BKGND_NONE, libtcod.LEFT, "Mining Drill")

	#Show Bomb Components found
	libtcod.console_print_ex(top_panel, 50, 0, libtcod.BKGND_NONE, libtcod.LEFT, "Bomb Components: " + str(config.bomb_parts_collected) + "/" + str(config.TOTAL_BOMB_PARTS))
	
	#show the currently equipped armor's stats
	# libtcod.console_print_ex(top_panel, 50, 0, libtcod.BKGND_NONE, libtcod.LEFT, config.player.fighter.equiparmor.name[:-7])
	# libtcod.console_print_ex(top_panel, 50, 1, libtcod.BKGND_NONE, libtcod.LEFT, 'AC: ' + str(config.player.fighter.ac))
	
	#show the currently equipped spell (not implemented yet)
	# libtcod.console_print_ex(top_panel, 70, 0, libtcod.BKGND_NONE, libtcod.LEFT, 'Fireball')
	
	libtcod.console_set_default_foreground(bottom_panel, libtcod.light_gray)
	libtcod.console_print_ex(bottom_panel, 1, 2, libtcod.BKGND_NONE, libtcod.LEFT, 'Current floor: ' + str(config.current_floor))
	
	#blit the contents of "panel" to the root console
	libtcod.console_blit(top_panel, 0, 0, config.SCREEN_WIDTH, config.PANEL_HEIGHT, 0, 0, 0)
	libtcod.console_blit(bottom_panel, 0, 0, config.SCREEN_WIDTH, config.PANEL_HEIGHT, 0, 0, config.PANEL_Y)

def initialize_fov():
	config.fov_radius = config.TORCH_RADIUS
	config.beast_fov_radius = config.BEAST_SIGHT_RADIUS
	config.fov_recompute = True
	
	#create FOV map
	config.fov_map = libtcod.map_new(config.MAP_WIDTH, config.MAP_HEIGHT)
	for y in range(config.MAP_HEIGHT):
		for x in range(config.MAP_WIDTH):
			libtcod.map_set_properties(config.fov_map, x, y, not config.map[x][y].block_sight, not config.map[x][y].blocked)
			
	#create beast's FOV map
	config.beast_fov_map = libtcod.map_new(config.MAP_WIDTH, config.MAP_HEIGHT)
	for y in range(config.MAP_HEIGHT):
		for x in range(config.MAP_WIDTH):
			libtcod.map_set_properties(config.beast_fov_map, x, y, not config.map[x][y].block_sight, not config.map[x][y].blocked)
	
	libtcod.console_clear(con)  #unexplored areas start black (which is the default background color)

def init_gfx():
	global con, top_panel, bottom_panel

	libtcod.console_set_custom_font('arial12x12.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD) 	#init custom font
	libtcod.console_init_root(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, 'PURGE', False)								  	#init console
	con = libtcod.console_new(config.MAP_WIDTH, config.MAP_HEIGHT)														#init off-screen console
	top_panel = libtcod.console_new(config.SCREEN_WIDTH, config.PANEL_HEIGHT)												#init top panel
	bottom_panel = libtcod.console_new(config.SCREEN_WIDTH, config.PANEL_HEIGHT)											#init bottom panel
	libtcod.sys_set_fps(config.LIMIT_FPS)																			#limit fps
	libtcod.console_set_alignment(0, libtcod.CENTER)																		#set console alignment
