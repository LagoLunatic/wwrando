
from collections import OrderedDict

OPTIONS = OrderedDict([
  (
    "progression_dungeons",
    "This controls whether dungeons can contain progress items.<br><u>If this is not checked, dungeons will still be randomized</u>, but will only contain optional items you don't need to beat the game."
  ),
  (
    "progression_great_fairies",
    "This controls whether the items given by Great Fairies can be progress items.<br><u>If this is not checked, they will still be randomized</u>, but will only contain optional items you don't need to beat the game."
  ),
  (
    "progression_puzzle_secret_caves",
    "This controls whether puzzle-focused secret caves can contain progress items.<br><u>If this is not checked, they will still be randomized</u>, but will only contain optional items you don't need to beat the game."
  ),
  (
    "progression_combat_secret_caves",
    "This controls whether combat-focused secret caves (besides Savage Labyrinth) can contain progress items.<br><u>If this is not checked, they will still be randomized</u>, but will only contain optional items you don't need to beat the game."
  ),
  (
    "progression_short_sidequests",
    "This controls whether sidequests that can be completed quickly can reward progress items.<br><u>If this is not checked, they will still be randomized</u>, but will only reward optional items you don't need to beat the game."
  ),
  (
    "progression_long_sidequests",
    "This controls whether long sidequests (e.g. Lenzo's assistant, withered trees, goron trading) can reward progress items.<br><u>If this is not checked, they will still be randomized</u>, but will only reward optional items you don't need to beat the game."
  ),
  (
    "progression_spoils_trading",
    "This controls whether the items you get by trading in spoils to NPCs can be progress items.<br><u>If this is not checked, they will still be randomized</u>, but will only reward optional items you don't need to beat the game."
  ),
  (
    "progression_minigames",
    "This controls whether most minigames can reward progress items (auctions, mail sorting, barrel shooting, bird-man contest).<br><u>If this is not checked, minigames will still be randomized</u>, but will only reward optional items you don't need to beat the game."
  ),
  (
    "progression_free_gifts",
    "This controls whether gifts freely given by NPCs can be progress items (Tott, Salvage Corp, imprisoned Tingle).<br><u>If this is not checked, they will still be randomized</u>, but will only be optional items you don't need to beat the game."
  ),
  (
    "progression_mail",
    "This controls whether mail can contain progress items.<br><u>If this is not checked, mail will still be randomized</u>, but will only contain optional items you don't need to beat the game."
  ),
  (
    "progression_platforms_rafts",
    "This controls whether lookout platforms and rafts can contain progress items.<br><u>If this is not checked, they will still be randomized</u>, but will only contain optional items you don't need to beat the game."
  ),
  (
    "progression_submarines",
    "This controls whether submarines can contain progress items.<br><u>If this is not checked, submarines will still be randomized</u>, but will only contain optional items you don't need to beat the game."
  ),
  (
    "progression_eye_reef_chests",
    "This controls whether the chests that appear after clearing out the eye reefs can contain progress items.<br><u>If this is not checked, they will still be randomized</u>, but will only contain optional items you don't need to beat the game."
  ),
  (
    "progression_big_octos_gunboats",
    "This controls whether the items dropped by Big Octos and Gunboats can contain progress items.<br><u>If this is not checked, they will still be randomized</u>, but will only contain optional items you don't need to beat the game."
  ),
  (
    "progression_triforce_charts",
    "This controls whether the sunken treasure chests marked on Triforce Charts can contain progress items.<br><u>If this is not checked, they will still be randomized</u>, but will only contain optional items you don't need to beat the game."
  ),
  (
    "progression_treasure_charts",
    "This controls whether the sunken treasure chests marked on Treasure Charts can contain progress items.<br><u>If this is not checked, they will still be randomized</u>, but will only contain optional items you don't need to beat the game."
  ),
  (
    "progression_expensive_purchases",
    "This controls whether items that cost a lot of rupees can be progress items (Rock Spire shop, auctions, Tingle's letter, trading quest).<br><u>If this is not checked, they will still be randomized</u>, but will only be optional items you don't need to beat the game."
  ),
  (
    "progression_misc",
    "Miscellaneous locations that don't fit into any of the above categories (outdoors chests, wind shrine, Cyclos, etc).<br><u>If this is not checked, they will still be randomized</u>, but will only contain optional items you don't need to beat the game."
  ),
  (
    "progression_tingle_chests",
    "Tingle Chests that are hidden in dungeons and must be bombed to make them appear. (2 in DRC, 1 each in FW, TotG, ET, and WT).<br><u>If this is not checked, they will still be randomized</u>, but will only contain optional items you don't need to beat the game."
  ),
  (
    "progression_battlesquid",
    "This controls whether the Windfall battleship minigame can reward progress items.<br><u>If this is not checked, it will still be randomized</u>, but will only reward optional items you don't need to beat the game."
  ),
  (
    "progression_savage_labyrinth",
    "This controls whether the Savage Labyrinth can contain progress items.<br><u>If this is not checked, it will still be randomized</u>, but will only contain optional items you don't need to beat the game."
  ),
  (
    "progression_island_puzzles",
    "This controls whether various island puzzles can contain progress items (e.g. chests hidden in unusual places).<br><u>If this is not checked, they will still be randomized</u>, but will only contain optional items you don't need to beat the game."
  ),
  
  
  (
    "keylunacy",
    "Allows dungeon keys (as well as maps and compasses) to appear anywhere in the game, not just in the dungeon they're for."
  ),
  (
    "randomize_entrances",
    "Shuffles around which dungeon entrances/secret cave entrances take you into which dungeons/secret caves.\n(No effect on Forsaken Fortress or Ganon's Tower.)"
  ),
  (
    "randomize_charts",
    "Randomizes which sector is drawn on each Triforce/Treasure Chart."
  ),
  (
    "randomize_starting_island",
    "Randomizes which island you start the game on."
  ),
  (
    "chest_type_matches_contents",
    "Changes the chest type to reflect its contents. A metal chest has a progress item, a key chest has a dungeon key, and a wooden chest has a non-progress item or a consumable.\nKey chests are dark wood chests that use a custom texture based on Big Key chests. Keys for non-required dungeons in race mode will be in wooden chests."
  ),
  (
    "fishmen_hints",
    "Places hints on the fishmen. There is one fishman at each of the 49 islands of the Great Sea. Each fishman must be fed an All-Purpose Bait before he will give a hint.",
  ),
  (
    "hoho_hints",
    "Places hints on Old Man Ho Ho. Old Man Ho Ho appears at 10 different islands in the game. Simply talk to Old Man Ho Ho to get hints.",
  ),
  (
    "korl_hints",
    "Places hints on the King of Red Lions. Talk to the King of Red Lions to get hints.",
  ),
  (
    "num_hints",
    "Determines the number of hints that will be placed in the game. This option does not affect Wallet mail, Big Octo Great Fairy, or Savage Labyrinth hints.\nIf multiple hint placement options are selected, the hint count will be split evenly among the placement options.",
  ),
  
  
  (
    "swift_sail",
    "Sailing speed is doubled and the direction of the wind is always at your back as long as the sail is out."
  ),
  (
    "instant_text_boxes",
    "Text appears instantly.<br>Also, the B button is changed to instantly skip through text as long as you hold it down."
  ),
  (
    "reveal_full_sea_chart",
    "Start the game with the sea chart fully drawn out."
  ),
  (
    "num_starting_triforce_shards",
    "Change the number of Triforce Shards you start the game with.<br>The higher you set this, the fewer you will need to find placed randomly."
  ),
  (
    "add_shortcut_warps_between_dungeons",
    "Adds new warp pots that act as shortcuts connecting dungeons to each other directly. (DRC, FW, TotG, and separately FF, ET, WT.)\nEach pot must be unlocked before it can be used, so you cannot use them to access dungeons you wouldn't already have access to."
  ),
  (
    "do_not_generate_spoiler_log",
    "Prevents the randomizer from generating a text file listing out the location of every single item for this seed. (This also changes where items are placed in this seed.)<br><u>Generating a spoiler log is highly recommended even if you don't intend to use it</u>, just in case you get completely stuck."
  ),
  (
    "sword_mode",
    "Controls whether you start with the Hero's Sword, the Hero's Sword is randomized, or if there are no swords in the entire game.\nSwordless and No Starting Sword are challenge modes, not recommended for your first run. Also, FF's Phantom Ganon is vulnerable to Skull Hammer in Swordless mode only."
  ),
  (
    "skip_rematch_bosses",
    "Removes the door in Ganon's Tower that only unlocks when you defeat the rematch versions of Gohma, Kalle Demos, Jalhalla, and Molgera."
  ),
  (
    "invert_camera_x_axis",
    "Inverts the horizontal axis of camera movement.",
  ),
  (
    "invert_sea_compass_x_axis",
    "Inverts the east-west direction of the compass that shows while at sea.",
  ),
  (
    "race_mode",
    "In Race Mode, certain randomly chosen dungeon bosses will drop required items (e.g. Triforce Shards). Nothing in the other dungeons will ever be required.\nYou can see which islands have the required dungeons on them by opening the sea chart and checking which islands have blue quest markers.",
  ),
  (
    "num_race_mode_dungeons",
    "Select the number of dungeons that are required in Race Mode.\nRequired dungeon bosses will drop required items (e.g. Triforce Shards). Nothing in the other dungeons will ever be required.",
  ),
  (
    "randomize_music",
    "Shuffles around all the music in the game. This affects background music, combat music, fanfares, etc.",
  ),
  (
    "disable_tingle_chests_with_tingle_bombs",
    "This prevents the Tingle Tuner's bombs from revealing Tingle Chests, meaning the only way to access these chests is to find the normal bombs item.\n(The randomizer makes normal bombs work on Tingle Chests regardless of this option.)",
  ),
  (
    "randomize_enemy_palettes",
    "Gives all the enemies in the game random colors.",
  ),
  (
    "remove_title_and_ending_videos",
    "Removes the two prerendered videos that play if you wait on the title screen and after you beat the game. (Decreases randomized ISO's filesize by about 600MB.)\nIf you keep these videos in, they won't reflect your custom player model or colors.",
  ),
  
  
  (
    "custom_player_model",
    "Replaces Link's model with a custom player model.\nThese are loaded from the /models folder."
  ),
  (
    "player_in_casual_clothes",
    "Enable this if you want to wear your casual clothes instead of the Hero's Clothes."
  ),
  (
    "disable_custom_player_voice",
    "If the chosen custom model comes with custom voice files, you can check this option to turn them off and simply use Link's normal voice instead."
  ),
  (
    "disable_custom_player_items",
    "If the chosen custom model comes with custom item models, you can check this option to turn them off and simply use Link's normal item models instead."
  ),
  (
    "custom_color_preset",
    "This allows you to select from preset color combinations chosen by the author of the selected player model."
  ),
  (
    "randomized_gear",
    "Inventory items that will be randomized."
  ),
  (
    "starting_gear",
    "Items that will be in Link's inventory at the start of a new game."
  ),
  (
    "starting_pohs",
    "Amount of extra pieces of heart that you start with."
  ),
  (
    "starting_hcs",
    "Amount of extra heart containers that you start with."
  ),
  (
    "remove_music",
    "Mutes all ingame music."
  ),
  (
    "randomize_enemies",
    "Randomizes the placement of non-boss enemies."
  ),
])

NON_PERMALINK_OPTIONS = [
  "invert_camera_x_axis",
  "invert_sea_compass_x_axis",
  "custom_player_model",
  "player_in_casual_clothes",
  "disable_custom_player_voice",
  "disable_custom_player_items",
  "custom_color_preset",
  "remove_title_and_ending_videos",
  # Note: Options that affect music must be included in the permalink because music duration affects gameplay in some cases, like not being allowed to close the item get textbox until the item get jingle has finished playing.
  # Note: randomize_enemy_palettes has special logic to be in the permalink when enemy rando is on, but otherwise just have an unused placeholder in the permalink.
]

HIDDEN_OPTIONS = [
  "disable_tingle_chests_with_tingle_bombs",
  "randomize_music",
  "randomize_enemies",
]

POTENTIALLY_UNBEATABLE_OPTIONS = [
  "randomize_enemies",
]
