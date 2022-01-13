
### Next version (in progress, not released yet)

New features:
* The randomizer now officially supports Mac and Linux and offers release builds for those platforms.
* Added a button to the top of the Player Customization tab to automatically install a custom player model or pack of multiple custom player models from a .zip file.
* Added an optional tweak to invert the X axis of the compass on the sea so that it works more intuitively.
* Forest Haven's shore now has a warp which acts as a shortcut allowing you to quickly re-enter the dungeon entrance from the sea after you've already reached it the normal way once.
* Custom model authors can now change the colors of the sword's slash trail when parrying and when under the Elixir Soup effect.
* Added a command line argument `-autoseed` that generates a random seed name instead of loading the last used one from settings.txt.

Changes:
* The "seed hash" the randomizer adds to the name entry screen is now also included in log files.
* Removed several minor cutscenes from Forest Haven where the camera panned around.
* Inter-dungeon warp pots now have red-colored smoke to differentiate them from other warp pots.

Bug fixes:
* Fixed permalinks not being properly decoded in some cases when Swordless mode is enabled and starting gear is customized.
* Fixed the Song of Passing being logically required for Letter from Baito, even though you do not actually need to wait for time to pass for that letter.
* Fixed the chest the randomizer adds to the DRC miniboss room not appearing on the compass when in a different room.
* Fixed the number of Tingle Statues you own being displayed incorrectly on the Tingle Tuner's GBA screen.

Removed:
* 32-bit builds of the randomizer are no longer offered.

### Version 1.9.0 (released 2021-02-23)

New features:
* When Race Mode is enabled, you can now choose for the number of required dungeons to be anywhere from 1 to 6, instead of only 4 dungeons.
* You can now choose to randomize the Hero's Shield instead of starting the game with it.
* Custom model authors can now change the colors of the sword's slash trail, the boomerang's trail, and arrow trails.
* Slightly increased the speed at which Link sidles along walls.
* The Nintendo Gallery is now unlocked from the start of the game.
* Added a counter showing the number of Tingle Statues you own to the Quest Status screen. This allows you to easily check how many you've picked up without going to Tingle Island. (This replaces the Treasure Chart counter on that screen, but you can still view the number of charts you own in the charts menu.)

Changes:
* Moved the inter-dungeon warp pot in Earth Temple from the fourth room to the second room so that it can be accessed with fewer items than before.
* The option to remove the title/ending videos and the enemy palette randomizer no longer affect the permalink.
* For progress items that have extra duplicates, the randomizer now only guarantees that the required number of them are in progression locations. For example, out of the four Empty Bottles, one will be placed in a progression location if it's needed, but the other three can be placed in either progression or non-progression locations, as if those three were non-progress items.
* Defeating the Mighty Darknuts in the Master Sword chamber with no weapon besides Skull Hammer can no longer be required by the logic.
* Defeating Big Octos that have 12 eyes with arrows can now only be required if you have either the 60 arrow quiver or Light Arrows.
* Renamed "Randomized Sword" to "No Starting Sword" and "Start with Sword" to "Start with Hero's Sword".
* Renamed a few item locations to be more clear.
* The item given for hitting Orca 500 times can now only be consumable items such as rupees (previously it could be anything except progress items).
* The Windfall bomb shop owner now sells bomb refills at reasonable prices from the start of the game, instead of setting the prices to be unaffordable before you own Nayru's Pearl.
* The progress bar now updates incrementally as the randomized ISO is being written.

Bug fixes:
* Fixed a bug where release executables were not properly encrypted, allowing them to be extracted and used to generate spoiler logs for non-spoiler log seeds.
* Fixed a bug where saving the game inside the Pirate Ship on Windfall would cause you to appear on Southern Fairy Island when you reload the game.
* Fixed a bug where certain types of items could be incorrectly counted as progress items regardless of settings if you chose to start with at least 1 of that item but not all of them (e.g. Empty Bottles).
* Fixed a bug where custom player models with tons of color presets built in would cause the randomizer's UI to be very slow when changing custom color options.
* Fixed an error occurring during randomization if your seed name was exactly 42 characters long (the maximum seed length).
* Fixed an error occurring when using a custom ship model that uses the same sail texture as the vanilla ship model.
* Fixed a vanilla bug where mini-boss music would continue to play even after leaving the room if you killed the mini-boss with Light Arrows, or left the room without killing the mini-boss at all.
* Fixed various bugs that could occur when the Fire Mountain and Ice Ring Isle cave entrances were randomized.

### Version 1.8.0 (released 2020-05-15)

New features:
* Implemented color presets for custom player models. The model's author can optionally include sets of colors with the model that can be selected via a dropdown in the randomizer's UI.
  * For example, the vanilla Link model now comes with the following color presets: Dark Link, Smash Dark Link, Green Link, Red Link, Blue Link, Purple Link, Shadow Link.
* Custom player models can now optionally include a custom ship model for the player to ride.
* Custom player models can now allow recoloring the player's sclera.
* Added an option to remove all music from the game.
* Added an option to disable custom item models that come with custom player models.

Changes:
* 14 item locations previously under the Miscellaneous category are now under a new Island Puzzles category.
* The Pirate Ship item location on Windfall is now part of the Minigames category.
* The trigger for the Phantom Ganon fight at Forsaken Fortress no longer extends infinitely upwards above Phantom Ganon like it did in vanilla. This means you can fight Helmaroc King without first defeating Phantom Ganon (which can now be required by the logic).
* Removed the minor cutscenes in DRC, FW, TotG, and ET where the camera panned around the hub room.
* Prevented the cutscene where Ivan tells you about Mrs. Marie's birthday from triggering automatically as you leave the school. (You can still trigger it manually by talking to Ivan, in case you want to get the unrandomized Joy Pendant in the tree.)
* When the Swift Sail tweak is enabled, the ship's cruising speed is now also increased.
* When the randomizer runs out of items to place (e.g. because you started with extra gear) it will now place various consumables randomly to fill the locations up, instead of only using red rupees.
* Hyrule Castle now has Moblins and Darknuts in it. (Killing them is not necessary to progress like in vanilla.)
* Outset will now play its alternate theme once you've opened a certain chest.
* Drastically improved the performance of recoloring the player model preview image in the randomizer's UI, especially when lots of different color options are changed from the model's defaults.
* Added more custom color options for the vanilla Link model.
* The "Generate Spoiler Log" option is now worded as "Do Not Generate Spoiler Log" and unchecked by default. Its effect is the same, just flipped.

Bug fixes:
* Fixed a bug introduced in 1.7.0 where slightly recoloring certain grey colors on player models would make them appear as extremely saturated colors.
* Fixed a vanilla bug where respawning Magtails that are killed by shooting them in the head with Light Arrows would not respawn.
* Fixed a vanilla bug where the stone faces in the Tall Basement Room of Wind Temple that spawn Bokoblins wouldn't allow the chest in that room to spawn until you look at the empty spot where the stone face fell and broke apart after you kill its Bokoblin.
* Potentially fixed a vanilla issue when sailing on the sea for a long time that could result in the game running out of memory and reloading the sea with a fade to white.
* Fixed Big Octo eyes not changing color very much when destroyed if the enemy palette randomizer was on.
* Fixed Mighty Darknut and Phantom Ganon's capes sometimes being transparent when the enemy palette randomizer was on.
* Fixed the floor of the roof of Forsaken Fortress's tower being recolored along with Helmaroc King when the enemy palette randomizer was on.
* Fixed a bug introduced in 1.5.0 where the Grappling Hook's hook would visually appear slightly detached from the rope when Link holds it at his side.
* Fixed a bug introduced in 1.5.0 where the Grappling Hook used by Salvage Corp would be the wrong color when using a player model that comes with a custom model for the Grappling Hook.



### Version 1.7.0 (released 2020-02-16)

New features:
* Added a new Ballad of Gales warp point to the Forsaken Fortress sector.
* Added an option to randomize all enemy colors.
* You can now choose how many Heart Containers and Heart Pieces you want to start the game with.
* The Magic Meter Upgrade is now included in the list of items you can choose to start the game with.
* Added buttons to randomize the selected player model's custom colors.
* Custom player models can now allow recoloring Link's pupils, as well as allow changing skin color without recoloring the inside of Link's mouth.
* Custom player models can now optionally include a custom LkAnm.arc file to change Link's animations. (Only animations that change textures. The randomizer will ignore changed bone animations and use the originals since bone animations can affect gameplay.)

There are also a number of new player models made by members of the community: Ganondorf, Colette, Samus, Cloud, Chocobo, Ashley, Vaati, Conductor Link, Tri Suit Link, Squall, Marth, Agent 9, Erdrick, Picori, Captain Falcon, Tingle, and Beedle. Download all the models here: https://github.com/Sage-of-Mirrors/Custom-Wind-Waker-Player-Models

Changes:
* The logic can now require you to use the Hookshot to skip fighting the Earth Temple Stalfos mini-boss fight when you don't have a sword.
* Killing the respawning Darknuts in Wind Temple, Stone Watcher Island, and Overlook Island can now be required by the logic when farming for Knight's Crests.
* The item given by the final withered tree is now properly launched out with momentum like in the vanilla game instead of simply falling down.
* Whether you choose for the player to wear casual clothes or hero's clothes is now always respected. This option now overrides Second Quest forcing you into casual clothes, as well as loading a save file where you started with the opposite option selected.
* Renamed several Windfall item locations to be more descriptive.
* Removing the videos from the title screen and ending is now optional instead of always being enabled.

Bug fixes:
* Fixed a vanilla softlock when re-entering Forsaken Fortress via the left half of the big door on the second floor.
* Fixed a vanilla bug where Morths that fall out of bounds would not be considered dead. They are now automatically killed after falling out of bounds. In practice this should fix chests not spawning/doors not opening in locations where Wizzrobes spawn Morths: the Pawprint Isle Wizzrobe Cave, the Tall Basement Room in Wind Temple, and one of the rooms in the Overlook Island secret cave.
* Fixed a vanilla softlock where cutting a Stalfos in half and then killing its upper half with Light Arrows would not also kill its lower half, making it impossible to kill all enemies in the room. (Because this bug is now fixed, the randomizer's workaround to avoid this where Stalfos were made completely immune to Light Arrows has been reverted, so Stalfos can be killed with them again like in vanilla.)
* Fixed a vanilla bug where non-respawning Miniblins would not be fully considered dead when killed with Light Arrows. This affects Miniblins in the Shark Island cave, and the first Miniblin in the Crescent Moon Island submarine.
* Fixed a bug in the vanilla code where Jalhalla would not consider his spawned Poes dead and decrease his HP if they are killed with Light Arrows.
* Fixed memory corruption that occurred when the randomizer's custom code spawned the item given by the final withered tree, which was likely the cause of extremely rare and inconsistent bugs happening then or shortly after, such as the game softlocking or crashing.
* Fixed a bug where Beedle would not tell you the total price he is willing to pay you for spoils you offer him.
* When sequence breaking DRC and going backwards, the game will no longer stutter for a second when you approach the back side of a door that has a boulder on the other side of it while the randomizer's custom actor is deleting the boulder.
* Fixed a bug where being sucked into the center of the Outset whirlpool would not stop the whirlpool music from playing.
* Fixed colored lines appearing on the vanilla Link model when you select certain custom color combinations.



### Version 1.6.1 (released 2019-08-10)

Changes:
* When a spoiler log is not generated, the random item layout of a given seed will now be different between the release and the source versions of the randomizer, in order to prevent cheating by learning the item layouts from the source version and using that information for races with the release version.
* Added an option to make Tingle Chests not materialize when you use the Tingle Tuner's bombs on them, so you must find the normal bombs item to access them.
* Item location hints will no longer hint at the location of boss reward items when race mode is on.
* Each fishman hint is now duplicated about the same number of times across all islands, instead of some hints being duplicated much more than others.
* Removed some unnecessary information from the "Options selected" section of the logs.

Bug fixes:
* Fixed an issue with swordless logic where you could be required to get to floor 30 of Savage Labyrinth with the fully upgraded bow as your only weapon and no grappling hook, which could be impossible on some seeds with only 30 arrows and no way to replenish them.
* The randomizer will no longer allow you to use a custom player model if its filesize is so large that it could cause the game to crash or bug out.
* The randomizer will now show an error during randomization if the chosen custom player model's color masks have invalid colors in them instead of silently ignoring the issue.

There are also a number of new player models made by members of the community: Ganondorf, Colette, Samus, Cloud, Chocobo, Ashley, and Vaati. Download all the models here: https://github.com/Sage-of-Mirrors/Custom-Wind-Waker-Player-Models



### Version 1.6.0 (released 2019-04-18)

New features:
* Added a randomized item in a chest to Jabun's cave.
* Added a randomized item in a chest to the Master Sword chamber in Hyrule.
* Randomized the items Doc Bandam gives you the first time you give him green/blue chu jelly and he makes a green/blue potion.
* You can now choose what items you want to start the game with.

There are also a number of new player models made by members of the community: Saria, ToonFlips, Grandma, Din, Poor Maggie, Kass, Shaggy, and Pit. Plus Medli and Tetra now have more custom color options. Download all the models here: https://github.com/Sage-of-Mirrors/Custom-Wind-Waker-Player-Models

Changes:
* You no longer need the full Master Sword to access the warp to Hyrule. (You still need it to break the barrier in Hyrule.)
* The boomerang now oneshots mounted cannons instead of twoshotting them.
* You no longer need to defeat Phantom Ganon at Forsaken Fortress for the eye reefs to become active.
* The Hurricane Spin now has a custom item model instead of using the Hero's Sword model.
* The vanilla Link model now has more custom color options.
* The warp out of TotG when you beat Gohdan no longer puts you right on top of the warp to Hyrule.
* Added support for custom models having multiple color masks for the model's hands texture.
* Added a few guaranteed magic drops to the grass on the small islands around Dragon Roost Island that you fly around with Deku Leaf.
* Removed the events where Medli and Makar would call to you from within jail.
* Renamed Salvatore's "Sinking Ships" minigame to "Battlesquid" and his "Target Shooting" minigame to "Barrel Shooting".
* The Great Fairy inside a Big Octo now hints at the location of a random item, instead of the vanilla hint as to where Fire & Ice Arrows are.
* The fishmen now have a total of 15 unique item hints per seed, instead of 3.
* Improved ingame loading times somewhat.

Bug fixes:
* Fixed exiting Savage Labyrinth when secret cave entrances are randomized not taking you to the proper entrance.
* Fixed a softlock that could happen outside Fire Mountain when secret cave entrances are randomized where the player would get stuck in an infinite loop of taking damage from lava (really this time).
* Fixed the sound from the prologue playing whenever you enter the Fairy Woods.
* Fixed Komali existing in two places at once.
* Fixed a vanilla bug where the Deluxe Picto Box did not automatically equip itself if you have the regular Picto Box equipped when you get the Deluxe one.
* Fixed the lava in front of DRC's entrance automatically solidifying once you own Din's Pearl.



### Version 1.5.1 (released 2019-01-31):

Bug fixes:
* Fixed a softlock that could happen when secret cave entrances are randomized where Power Bracelets could be locked behind the cave on Outset.
* Fixed a softlock that could happen outside Fire Mountain when secret cave entrances are randomized where the player would get stuck in an infinite loop of taking damage from lava.

Changes:
* When Race Mode is on and secret cave entrances are randomized together with dungeon entrances, two dungeons can no longer appear on the same island (e.g. one in the Dragon Roost Cavern dungeon entrance and the other in the Dragon Roost Island secret cave entrance). Previously if there was a required dungeon and a non-required dungeon on the same island you had no way of knowing which one was required as the markers on the sea chart only tell you what island to go to.



### Version 1.5.0 (released 2019-01-20):

New features:
* Implemented a Secret Cave Entrance Randomizer which shuffles around which secret cave entrances take you into which secret caves. You can also choose to combine this with the Dungeon Entrance Randomizer so that dungeon entrances may lead into secret caves and vice versa.
* Implemented Race Mode. In this mode, 4 of the 6 dungeons are randomly chosen, and the bosses of those dungeons drop an item which is definitely required to beat the game. The 4 chosen dungeons are marked on the sea chart. The 2 dungeons that were not chosen will not have any progress items anywhere in them, so you don't even need to enter those dungeons.
* Sped up several animations, including the grappling animation, block pushing/pulling animations, and climbing animations.
* Implemented a Key Bag, accessible on the Quest Status screen, which tells you how many unused small keys you currently have and whether you have the big key or not for each dungeon. With this, you don't need to be inside the dungeon to know what keys you have.
* Medli and Makar now follow you out of warp pots within their respective dungeons, so you don't need to manually carry them through the whole dungeon every time you re-enter the dungeon.

There are also a number of new player models made by members of the community: Goku, Fox Link, Zora Link, and Poor Mila. Plus custom voices to go with the Medli model. Download all the models here: https://github.com/Sage-of-Mirrors/Custom-Wind-Waker-Player-Models

Changes:
* Changed the way the randomizer decides how to place progress items, so that the bias towards locations accessible early on is now less extreme than before.
* Savage Labyrinth is now a separate progression option, instead of being under Combat Secret Caves. The Sinking Ships minigame is also now a separate progression option, instead of being under Minigames.
* Changed some location categories: Lenzo's two chests, the Windfall transparent chest, and the item Zunari gives you after you stock the Exotic Flower are now all under Short Sidequests.
* Added support for custom models to mask parts of the hand texture for custom colors.
* Added an option to the UI to disable custom voices that come with custom models.
* Removed a few more unnecessary short cutscenes from dungeons.
* Changed the distribution of randomized rupees so that silver rupees are no longer the most common, and purple and orange rupees are now more common.

Bug fixes:
* Fixed a vanilla crash that would occur when jump attacking on top of the Ghost Ship chest.
* Fixed very old versions of Dolphin not being able to boot the randomized game up.
* Fixed the normal item get music playing when you get a song instead of the special music.
* Fixed an error preventing you from choosing Swordless mode and starting with 8 Triforce shards together.
* Fixed an error when Tingle statues appear in Savage Labyrinth.



### Version 1.4.1 (released 2018-10-14):

Bug fixes:
* Fixed an error when trying to change custom colors for the default Link model.



### Version 1.4.0 (released 2018-10-13):

New features:
* Tingle Statues are now randomized into the item pool and can appear anywhere, not just in Tingle Chests.
* The reward Ankle gives you for finding all 5 Tingle Statues is also randomized (under Miscellaneous).
* The special rupee worth 500 rupees Ankle originally gave as a reward is also now randomized into the item pool. (Because this rupee originally looked identical to an orange rupee, it's been changed to cycle through all rupee colors in a rainbow to distinguish it.)
* Tingle Chests now have their contents randomized.
* Tingle Chests can now be made to appear with normal bombs, so using the Tingle Tuner is not required. Also, they now show up on the dungeon's compass.
* Added the ability to show a preview of the selected custom model and colors in the randomizer window.
* Added the ability to load custom voice files along with a custom model.
* Added an option to invert the camera's X axis.
* Added a "seed hash" to the name entry screen - two random character names that vary depending on your seed and selected options. Multiple people trying to play the same seed can use this to verify if they really booted the same seed up or not.

There are also a number of new custom player models made by members of the community: Aryll, Fado, Cheerleader Link, Sans, and Lucario. Download all the models here: <https://github.com/Sage-of-Mirrors/Custom-Wind-Waker-Player-Models>

Changes:
* Progress items that don't help you progress with your selected options are no longer considered progress items (e.g. Picto Box when you don't select sidequests). Because there are now less items in the progress item pool, it's now possible to select options that result in fewer progress locations than in previous versions if you want - for example, you can select just Great Fairies, Free Gifts, Minigames, and Mail for 23 locations, while previously that wouldn't have been nearly enough.
* Removed the item get animation for the first time you get each type of spoil.
* Several changes and fixes to progression logic and location names.
* A 64-bit build of the randomizer is now offered, which should be less likely to trigger false positives in antivirus programs than the 32-bit build.

Bug fixes:
* Fixed various bugs that could result in the randomizer throwing error messages on some Dungeons-only seeds due to the item placement logic backing itself into a dead-end.
* Fixed a bug causing the dungeon in the Tower of the Gods sector to be less likely to have required items in it than the other dungeons.
* Fixed Maggie's father not giving you red rupees for skull necklaces if you try to skip his dialogue too quickly.
* Fixed the normal item get music playing when you get a Goddess Pearl instead of the special music.
* Fixed a crash that occurred during the auction on real hardware.
* Fixed softlocks that could occur when you sequence break in DRC and then go backwards, then open a door that has a boulder blocking it from the wrong side. Now instead of the player being stuck walking into the boulder forever, the boulder will despawn.
* Fixed Orca's dialogue after he teaches you the Hurricane Spin being repeated an extra time.



### Version 1.3.0 (released 2018-09-01):

New features:
* Added Swordless mode - a challenge mode in which you must beat the whole game without a sword. Several things change in swordless:
  * Phantom Ganon is vulnerable to the Skull Hammer instead of the Master Sword.
  * The warp down to Hyrule only requires the 8 Triforce Shards, not the Master Sword.
  * You will be given a temporary Hero's Sword while in Ganondorf and Orca's rooms.
* Added Randomized Sword mode - in this mode you start without the Hero's Sword, but must still find it randomly placed somewhere. (This mode doesn't have the same changes that Swordless mode does.)
* Added an option to skip the rematch bosses in Ganon's Tower.
* Implemented turning while swinging on ropes.
* Added skin color to customizable player colors.

The Tetra and Medli player models have been updated as well, make sure to re-download them if you intend to use them: https://github.com/Sage-of-Mirrors/Custom-Wind-Waker-Player-Models

Changes:
* You now start with Song of Passing.
* Separated Phantom Ganon 2 from Phantom Ganon 3 - so if you have Light Arrows, you can skip doing the maze entirely.
* Your magic meter is now refilled to full when you load a save.
* Made all chests open quickly, without the dramatic dark room animation.
* Dungeon maps and compasses can now be dropped by the dungeon boss even when key-lunacy is off.
* Removed the camera panning around the bidders at the start of each auction.
* Removed Outset and DRC invisible walls that arbitrarily prevented sequence breaking.
* Removed the blue main quest markers from the sea chart.
* Adjusted the UI to work better on low resolution monitors.
* Custom player colors can now alternatively be input as hex codes.
* Numerous changes and fixes to progression logic and location names.

Bug fixes:
* Greatly reduced the filesize of custom player models and recolored player textures, hopefully fixing crashes that could occur sometimes.
* Fixed most items shooting out of Gohdan's nose too far.
* Fixed many randomized items on the ground not being picked up properly when you grab them with the boomerang.
* Fixed small keys dropped by a boss in key-lunacy not being added to your inventory if the small key was for the same dungeon as the one you're in.
* Fixed Picto Box related things acting already completed in New Game+.



### Version 1.2.0 (released 2018-07-31):

New features:
* Added support for loading custom player models in place of Link - currently Tetra and Medli models have been made. Custom models must be downloaded separately from the randomizer, [here](https://github.com/Sage-of-Mirrors/Custom-Wind-Waker-Player-Models).
* You can now change the color of the player's hair and clothing to be any color you want. (Works with both Link and custom models.)
* Added an option for the player to wear their casual clothes instead of their hero's clothes.
* The number of progress locations you have selected is now displayed in the UI.
* Added an option to not generate a spoiler log, which also changes the random placement of items on a given seed.

Changes:
* The Sidequests category has been split into Short Sidequests, Long Sidequests, and Spoils Trading.
* The Secret Caves category has been split into Puzzle Secret Caves and Combat Secret Caves.
* Great Fairies are now their own category.
* Cyclos has been moved to the Miscellaneous category.
* The letter advertising the Rock Spire shop ship now has item names updated depending on what items were placed in the shop.
* Numerous changes and fixes to progression logic and location names.
* Removed the cutscene after defeating Puppet Ganon.

Bug fixes:
* Fixed a bug where you would get locked out of playing hide and seek if you talked to Lenzo without the picto box first.
* Fixed a crash when the hookshot targeting reticule is pointed at the broken shards of Helmaroc King's mask.
* Fixed an error when the randomizer tried to place big keys in Savage Labyrinth.
* Blue Chu Jelly is no longer randomly placed since it can cause bugs.
* Complimentary ID is no longer placed anywhere in the game to prevent softlocks when the Delivery Bag is too full to obtain new items.



### Version 1.1.0 (released 2018-07-12):

Changes:
* Goddess Pearls are now placed automatically as soon as you get them, and Tower of the Gods is raised automatically when you get all 3.
* The spoiler and non-spoiler logs now include the permalink.
* When swift sail is enabled, the ship now comes to a stop faster when Link is knocked out or the player holds down A.
* When progression charts are enabled, reduced the chance of chains of charts leading to sunken treasures with more charts in them.
* Changed the Savage Labyrinth hint tablet to always list 2 things in order, so you can tell whether the important item is on floor 30 or floor 50 without going down there.
* Big octos and gunboats are no longer enabled under the default options.
* Letter from Hoskit's Girlfriend is considered both mail and a sidequest now.
* Renamed the "Everywhere Else" option to "Miscellaneous".
* Hookshot can be required instead of Grappling Hook/Deku Leaf for getting across the lava pit in front of the DRC boss door.
* Light arrows can be required instead of Mirror Shield for killing rematch Jalhalla.

Bug fixes:
* Fixed a softlock where the game would void out infinitely because Medli/Makar would spawn out of bounds if you saved the game when they're in a room with a warp pot, reloaded, then took other warp pots to come out of the warp pot in the same room that they were originally in.
* Fixed the auto update checker being weird when there are no new updates available.
* Removed the event where Makar thanks you for saving him after killing Kalle Demos, which could sometimes softlock the game.
* Possibly fixed a rare crash when having the pig dig up the buried item.



### Version 1.0.0 (released 2018-07-05):
First public release of Wind Waker Randomizer.
* Unreverted changes to roll speed back to 0.9.2 behavior.



### Beta version 0.9.3 (released 2018-07-04):
* Fixed a vanilla crash when you heal grandma and quickly unequip the fairy bottle.
* Fixed B to skip dialogue not working during the final 2 cutscenes of the game.
* Reverted changes to roll speed back to vanilla.



### Beta version 0.9.2 (released 2018-06-30):
* Fixed a crash when Dragon Roost Island's dungeon entrance leads to Tower of the Gods, and then you leave Tower of the Gods while on the ship.
* Added automatic update checking. (Until the randomizer is publicly released it will say that there was an error checking for updates.)
* Fixed Medli and Makar so they don't get reset to the first room of the dungeon when you go in the mini-boss room or void out. Now they reset only when you leave and re-enter the dungeon, save and reload, or get a game over.
* Fixed the position that the item given by the withered trees spawns at so that it falls in front of Link instead of getting stuck inside the tree trunk.
* Fixed improper word wrapping with the fishmen hints.
* Increased player crawling speed and minimum rolling speed.



### Beta version 0.9.1 (released 2018-06-27):
* Fixed warp pots in TotG and FF missing particles, which caused the game to crash on real hardware.
* Changed Medli and Makar to reset themselves to the first room of the dungeon when you save and reload or exit and re-enter the dungeon.
* Removed the event where Makar is kidnapped by Floormasters.
* Removed the cube from the first room of Earth Temple since it's not necessary when Medli is there.



### Beta version 0.9.0 (released 2018-06-25):
* Added an option to choose how many Triforce Shards you start the game with - you can pick any number from 0 to 8.
* Added the pirate ship to Windfall, and randomized the item inside it.
* Added an option to add new warp pots to each dungeon, which act as shortcuts to easily travel between dungeons. The warp pots must all be unlocked before you can use them so you cannot access dungeons early by using these.
* Added permalinks to the randomizer program, which can be copy pasted in order to share seeds between people - the permalink includes not just the seed but which options you have selected.
* Made Stalfos immune to Light Arrows to avoid a vanilla softlock that could happen if you killed the upper half of a Stalfos that is separated from its lower half.
* The "Playthrough" section of the spoiler log now mentions when you can beat Ganondorf.
* Tingle Statues are no longer randomized, since they didn't work properly when found randomly. They're now always found in their vanilla locations.
* Fixed arrow refills in the shop appearing too high up.



### Beta version 0.8.1 (released 2018-06-21):
* Fixed a crash when Fire & Ice or Light Arrows are on the ground.



### Beta version 0.8 (released 2018-06-21):
* The tablet on the first floor of Savage Labyrinth now hints at what items are inside the labyrinth.
* The fishmen now give hints as to which island progress items are on. Only 3 progress items are hinted at per seed, and you need to talk to multiple fishmen to see all 3 hints.
* The B button now acts as a skip button during dialogue - simply hold down B and every line of text will advance frame-perfectly. (If you want to actually read the text, you can still press the A button like before.)
* Progressive items now have their appearance and text change as you get each tier, instead of always looking like the tier-1 item. (Except swords, those still have the tier-1 model for the time being.)
* Fixed progressive items tier-2+ not playing out the item get animation when you buy them from the shop.
* Removed the Ballad of Gales warping out cutscene.
* Removed the automated song replay after the player manually plays a song.
* Removed the second half of the Zephos item cutscene.
* Tott now only dances once when teaching you his song.
* Fixed items appearing halfway inside shop/auction pedestals.
* The shop/auction/sinking squids minigame now show the correct name for randomized items.
* Fixed DRC map, DRC compass, and FW small key having the item get messages of pieces of heart.
* Item get messages for dungeon items are now properly wordwrapped.
* The logic now requires Song of Passing for locations where a set amount of time needs to pass.
* Removed boss intro cutscenes.
* Fixed Jalhalla not dropping his item if you picked up a specific blue rupee earlier on in Earth Temple.
* Fixed the second hammer button in Earth Temple not being accounted for in the logic.
* The warp after beating a boss now takes you to the correct island when dungeon entrances are randomized.



### Beta version 0.7 (released 2018-06-15):
* Small keys are now randomized.
* Added Key-Lunacy mode. In this mode, dungeon keys, maps, and compasses can appear anywhere in the world, not just in their own dungeon.
* Progression items are now allowed to appear in the mail.
* In order to get mail working in the randomizer some conditions were changed from vanilla: You no longer need Din's Pearl for the mailbox to give you letters that have been sent to you; Orca now sends his letter when you kill Kalle Demos instead of when you watch a cutscene on Greatfish; Aryll and Tingle now send their letters when you kill Helmaroc King instead of when you watch a cutscene in Hyrule 2.
* All remaining text boxes are now instant.
* Fixed the Rito postman on Windfall disappearing if you get an item from Hoskit.
* Fixed Lenzo not letting you start his quest if you already own Deluxe Picto Box.
* Fixed boss item drops disappearing if you happened to get a heart container elsewhere in the dungeon.
* Fixed boss item drops not disappearing when you take them, allowing you to get them over and over again.
* "Expensive Purchases" now includes auctions and the letter from Tingle. "Minigames" now includes auctions.
* Magic Meter Upgrade now uses the green potion model instead of large magic refill jar.
* The randomizer now has different icons from the vanilla game in the game list/memory card, and randomizer saves are now separate from vanilla saves.
* The randomizer will not require you to farm spoils until you have the Grappling Hook now.
* Added a README.



### Beta version 0.6 (released 2018-06-10):
* Big Keys are now randomized (within their original dungeons).
* Fixed Zunari, Salvage Corp, Maggie, and the Rito postman on Windfall giving you their item over and over again.
* Fixed the items given by Maggie and the Rito postman on Windfall being permanently missable.
* If you fall in the water in between Forest Haven and Forbidden woods you now die and respawn, like in the vanilla game, instead of needing to redo Forest Haven.
* The Swift Sail now changes the wind in 45 degree increments (so the windmill works correctly with it).
* Removed the title and ending movies in order to reduce file size and make randomization faster.
* Changed the Swift Sail's textures to look like the HD Swift Sail.
* Added a custom subtitle on the title screen.
* The randomizer now writes an error log if randomization fails (in the same folder as the spoiler log).
* Added a program icon to the randomizer.



### Beta version 0.5 (released 2018-06-01):
* Added a dungeon entrance randomizer option. (Does not randomize Forsaken Fortress or Ganon's Tower.)
* Added a 'playthrough' section to the spoiler log which lists the order you can obtain progress items in and from where.
* Fixed music not playing on Windfall.
* Fixed Hyrule being black and white.
* Fixed a bug where the player's whole inventory would be wiped out if the player skipped a boss, fought the recollection form of that boss, then fought the recollection form of a boss which the player did not skip the original form of.



### Beta version 0.4.1 (released 2018-05-27):
* Fixed a bug that made some seeds unwinnable when progress items are in Tower of the Gods.



### Beta version 0.4 (released 2018-05-27):
* Fixed various bugs in Beedle's shops.
* Added more options to fully control what types of locations progression items appear in. For example you can now limit progress items to appearing only in dungeons.
* Seeds are now random words instead of numbers.
* Added magic refill jars to Dragon Roost Cavern so you don't run out of MP to use Deku Leaf.
* Changed the distribution of consumable items, good ones like silver rupees should now be much more common than bad ones like green rupees.
* Added a non-spoiler log which lists all item locations without spoiling what the random item in that location is.



### Beta version 0.3 (released 2018-05-25):
* Added options to ban progress items from many types of locations.
* Fixed a softlock in the first room of earth temple without Medli (added a box to that room you can climb on).
* Fixed enemies not dropping spoils if you don't own spoils bag.
* Added starting island randomizer.



### Beta version 0.2 (released 2018-05-21):
* The randomizer now outputs an ISO instead of a folder of extracted files.
* Dungeon maps and compasses are now randomized.



### Beta version 0.1 (released 2018-05-17):
First beta release of the randomizer, features:
* Items are randomized.
* Can select whether both Triforce and Treasure Charts, only Triforce Charts, or neither should lead to progress items.
* Sailing speed is doubled and the direction of the wind is always at your back when the sail is out.
* Text appears instantly for most text boxes.
* Start the game with the sea chart fully drawn out.
