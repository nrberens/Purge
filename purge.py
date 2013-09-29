#P U R G E
#a game by Nathaniel Berens

#v0.19
#Last updated 9/20/13

#based on code by Jotaf
#powered by libtcod, written by Jice
#python wrapper by Jotaf

#Mouse context popout menu
#	right-click to bring up possible actions
#	left-click on action to do it

#Experiment with real time
#	Branch code?

#Spacebar performs primary context action (list first on context menu)

#0.12 - Added Cave Generation and O2 - 8/7/13
#0.13 - Added Scanner, changed FOV rules - 8/8/13
#0.14 - Added Water and Rivers
#0.15 - Added Beast and simple AI - 8/22/13
#0.16 - Added corpses that contain items = 8/26/2013
#0.17 - Split into multiple modules and reworked all variable/function/method namespaces
#0.18 - Added win condition - progess past level 20 to win
#0.19 - Added several items - oxygen tank, siphon, headlamp
#0.20 - Added flares and scanner nodes


import libtcodpy as libtcod
import math
import shelve
import pdb
import random

import config
import gfx
import mapgen
import game

def new_game():
	global birthdaysuit, barehands

	config.turns = 0
	
	#create the dungeon floor list
	config.floors = []
	config.current_floor = 0

	#create list of nodes
	config.nodes = []
	config.flares = []
	
	#create object representing the player
	armor_component = game.Armor(ac=0)
	item_component = game.Item(armor=armor_component)
	birthdaysuit = game.Object(0, 0, '[', 'Birthday Suit (worn)', libtcod.dark_orange, item = item_component)
	
	weapon_component = game.Weapon(mindmg=1, maxdmg=3, hitdie=2)
	item_component = game.Item(weapon=weapon_component)
	barehands = game.Object(0, 0, ')', 'Bare hands (wielded)', libtcod.light_blue, item = item_component)
	
	scanner_component = game.Scanner()
	item_component = game.Item(scanner=scanner_component)
	def_scanner = game.Object(0, 0, 's', 'Scanner', libtcod.dark_green, item = item_component)
	
	fighter_component = game.Fighter(plclass='Hellstronaut', ac=0, str=10, dex=10, con=10, int=10, fth=10, per=10, equipweapon=barehands, 
								equiparmor=birthdaysuit, equipscanner=def_scanner, equipheadlamp=None, equiptank=None, equipcamo=None, 
								hitdie = 0, mindmg = 0, maxdmg = 0, hp=100, defense=2, power=5, o2=200, death_function=game.player_death)
	config.player = game.Object(0, 0, '@', 'Dwayne', libtcod.white, blocks=True, fighter=fighter_component)
			
	mapgen.make_map()
	
	config.floors.append([config.map, config.objects, config.nodes, config.flares])
	
	gfx.initialize_fov()
	
	#create inventory
	config.inventory = []
	config.inventory.append(def_scanner)
	def_scanner.item.equip_scanner()
	
	#create the list of game messages and their colors, starts empty
	config.game_msgs = []
	
	config.game_state = 'playing'
	
	#a warm welcoming message!
	gfx.message('Welcome to Hell.', libtcod.red)

def play_game():
	
	player_action = None
	
	key = libtcod.Key()
	mouse = libtcod.Mouse()
	
	while not libtcod.console_is_window_closed():																#MAIN LOOP

		libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE,key,mouse)
		
		gfx.render_all()
		
		#flush console to screen
		libtcod.console_flush()
		
		#clear object positions
		for object in config.objects:
			object.clear()
		
		player_action = game.handle_keys(key)
		
		if player_action == 'exit':
			save_game()
			break

		if player_action == 'win':
			win_game()
			break

		#let monsters take their turn
		if config.game_state == 'playing' and player_action != 'didnt-take-turn':
			game.handle_time()
			for object in config.objects:
				if object.ai:
					object.ai.take_turn()

def win_game():
	win_con = libtcod.console_new(config.SCREEN_WIDTH, config.SCREEN_HEIGHT)

	while not libtcod.console_is_window_closed():

		libtcod.console_set_default_foreground(win_con, libtcod.black)
		libtcod.console_print(win_con, config.SCREEN_WIDTH/2, config.SCREEN_HEIGHT/2-4, 'Y O U   W I N')
		libtcod.console_set_default_foreground(win_con, libtcod.white)
		libtcod.console_print(win_con, config.SCREEN_WIDTH/2, config.SCREEN_HEIGHT-2, 'Congrats, duder!')

		libtcod.console_blit(win_con, 0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT, 0, 0, 0, 1.0, 1.0)

		libtcod.console_flush()

		libtcod.console_wait_for_keypress(True)
		main_menu()
		break

def save_game():
	#open a new empty shelve (possibly overwriting an old one) to write the game data
	file = shelve.open('savegame', 'n')
	file['map'] = config.map
	file['objects'] = config.objects
	file['player_index'] = config.objects.index(config.player)  #index of player in objects list
	file['beast_index'] = config.objects.index(config.beast) #index of beast in objects list
	file['floors'] = config.floors
	file['current_floor'] = config.current_floor
	file['inventory'] = config.inventory
	file['config.game_msgs'] = config.game_msgs
	file['config.game_state'] = config.game_state
	file.close()

def load_game():
	#open the previously saved shelve and load the game data
	
	file = shelve.open('savegame', 'r')
	config.map = file['map']
	config.objects = file['objects']
	config.player = config.objects[file['player_index']]  #get index of player in objects list and access it
	config.beast = config.objects[file['player_index']] #get index of player in objects list and access it
	config.floors = file['floors']
	config.current_floor = file['current_floor']
	config.inventory = file['inventory']
	config.game_msgs = file['config.game_msgs']
	config.game_state = file['config.game_state']
	file.close()
	
	gfx.initialize_fov()

def main_menu():
	img = libtcod.image_load('menu_background1.png')
	
	while not  libtcod.console_is_window_closed():
		#show the background image, at twice the regular console resolution
		libtcod.image_blit_2x(img, 0, 0, 0)
		
		#show the game's title, and some credits!
		libtcod.console_set_default_foreground(0, libtcod.black)
		libtcod.console_print(0, config.SCREEN_WIDTH/2, config.SCREEN_HEIGHT/2-4, 'P U R G E')
		libtcod.console_set_default_foreground(0, libtcod.white)
		libtcod.console_print(0, config.SCREEN_WIDTH/2, config.SCREEN_HEIGHT-2, 'By Nathaniel Berens')
		
		#show options and wait for the player's choice
		choice = gfx.menu(' ', ['Play a new game', 'Continue last game', 'Quit'], 24)
		
		if choice == 0: #new game
			new_game()
			play_game()	
		elif choice == 1: #load last game
			try:
				load_game()
			except:
				gfx.msgbox('\n No saved game to load. \n', 24)
				continue
			play_game()
		elif choice == 2: #quit
			break

#INITIALIZATION AND MAIN LOOP
#------------------------------------------------------------#

gfx.init_gfx()
main_menu()