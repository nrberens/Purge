PURGE Alpha
v.20a
9/23/2013
Nathaniel Berens

libtcod library by Jice
libtcod python wrapper by Jotaf
http://doryen.eptalys.net/libtcod/

based on code by Jotaf
http://roguebasin.roguelikedevelopment.org/index.php?title=Complete_Roguelike_Tutorial,_using_python%2Blibtcod

GAMEPLAY:
There are 21 floors. Each floor (currently) contains the corpse of a fellow scientist, a bomb component, and The Beast.

Find the corpses -- they have items on them. Experiment with the items. They'll help you survive.

Find the bomb components. Once you collect 5, you'll have an armed nuclear bomb. Plant the bomb to DESTROY HELL.

You have limited oxygen. Some corpses will contain tanks you can siphon from. The caverns also contain a fungus that emanates oxygen. Walking over it will allow your suit to refill it's oxygen.

Avoid The Beast. He doesn't like you, and you can't hurt him. HINT: He doesn't like water or strong light.

CONTROLS:

Arrow Keys to move
 I to access (I)nventory menu
 G to (G)et items
 D to (D)rop an item
 P to (P)ing the map with your Scanner
 O to (O)pen doors
 > to Descend stairs
 < to Ascend stairs
ESC to reach Main Menu


KNOWN BUGS:

* Changes to the FOV calculations do not update until after the next character input
* Maps occasionally do not spawn the Beast or Explorer Corpses
* Items occasionally spawn in walls
* Bomb does not need to be planted on final floor, any floor counts as a win
* Win screen exits immediately to main menu

TO DO:

* Shit tons -- no variation in level generation, no difficulty curve, no narrative, no tileset, etc.
