from dataclasses import dataclass, KW_ONLY
from enum import StrEnum

from options.base_options import BaseOptions, option

from wwr_ui.inventory import DEFAULT_STARTING_ITEMS, DEFAULT_RANDOMIZED_ITEMS

class SwordMode(StrEnum):
  START_WITH_SWORD = "Start with Hero's Sword"
  NO_STARTING_SWORD = "No Starting Sword"
  SWORDLESS = "Swordless"

class EntranceMixMode(StrEnum):
  SEPARATE_DUNGEONS = "Separate Dungeons From Caves & Fountains"
  MIX_DUNGEONS = "Mix Dungeons & Caves & Fountains"

class TrickDifficulty(StrEnum):
  NONE = "None"
  NORMAL = "Normal"
  HARD = "Hard"
  VERY_HARD = "Very Hard"

def get_default_progression_locations():
  from logic.logic import Logic # lazy import
  
  return list(Logic.load_and_parse_item_locations().keys())

@dataclass
class Options(BaseOptions):
  #region Progress locations
  progression_dungeons: bool = option(
    default=True,
    description="This controls whether dungeons can contain progress items.<br>"
      "<u>If this is not checked, dungeons will still be randomized</u>, but will only contain optional items you don't need to beat the game.",
  )
  progression_tingle_chests: bool = option(
    default=False,
    description="Tingle Chests that are hidden in dungeons and must be bombed to make them appear. (2 in DRC, 1 each in FW, TotG, ET, and WT).<br>"
      "<u>If this is not checked, they will still be randomized</u>, but will only contain optional items you don't need to beat the game.",
  )
  progression_dungeon_secrets: bool = option(
    default=False,
    description="DRC, FW, TotG, ET, and WT each have 2-3 secret items within them (11 in total). This controls whether they can be progress items.<br>"
      "The items are fairly well-hidden (they aren't in chests), so don't select this option unless you're prepared to search each dungeon high and low!",
  )
  progression_puzzle_secret_caves: bool = option(
    default=True,
    description="This controls whether puzzle-focused secret caves can contain progress items.<br>"
      "<u>If this is not checked, they will still be randomized</u>, but will only contain optional items you don't need to beat the game.",
  )
  progression_combat_secret_caves: bool = option(
    default=False,
    description="This controls whether combat-focused secret caves (besides Savage Labyrinth) can contain progress items.<br>"
      "<u>If this is not checked, they will still be randomized</u>, but will only contain optional items you don't need to beat the game.",
  )
  progression_savage_labyrinth: bool = option(
    default=False,
    description="This controls whether the Savage Labyrinth can contain progress items.<br>"
      "<u>If this is not checked, it will still be randomized</u>, but will only contain optional items you don't need to beat the game.",
  )
  progression_great_fairies: bool = option(
    default=True,
    description="This controls whether the items given by Great Fairies can be progress items.<br>"
      "<u>If this is not checked, they will still be randomized</u>, but will only contain optional items you don't need to beat the game.",
  )
  progression_short_sidequests: bool = option(
    default=False,
    description="This controls whether sidequests that can be completed quickly can reward progress items.<br>"
      "<u>If this is not checked, they will still be randomized</u>, but will only reward optional items you don't need to beat the game.",
  )
  progression_long_sidequests: bool = option(
    default=False,
    description="This controls whether long sidequests (e.g. Lenzo's assistant, withered trees, goron trading) can reward progress items.<br>"
      "<u>If this is not checked, they will still be randomized</u>, but will only reward optional items you don't need to beat the game.",
  )
  progression_spoils_trading: bool = option(
    default=False,
    description="This controls whether the items you get by trading in spoils to NPCs can be progress items.<br>"
      "<u>If this is not checked, they will still be randomized</u>, but will only reward optional items you don't need to beat the game.",
  )
  progression_minigames: bool = option(
    default=False,
    description="This controls whether most minigames can reward progress items (auctions, mail sorting, barrel shooting, bird-man contest).<br>"
      "<u>If this is not checked, minigames will still be randomized</u>, but will only reward optional items you don't need to beat the game.",
  )
  progression_battlesquid: bool = option(
    default=False,
    description="This controls whether the Windfall battleship minigame can reward progress items.<br>"
      "<u>If this is not checked, it will still be randomized</u>, but will only reward optional items you don't need to beat the game.",
  )
  progression_free_gifts: bool = option(
    default=True,
    description="This controls whether gifts freely given by NPCs can be progress items (Tott, Salvage Corp, imprisoned Tingle).<br>"
      "<u>If this is not checked, they will still be randomized</u>, but will only be optional items you don't need to beat the game.",
  )
  progression_mail: bool = option(
    default=False,
    description="This controls whether mail can contain progress items.<br>"
      "<u>If this is not checked, mail will still be randomized</u>, but will only contain optional items you don't need to beat the game.",
  )
  progression_platforms_rafts: bool = option(
    default=False,
    description="This controls whether lookout platforms and rafts can contain progress items.<br>"
      "<u>If this is not checked, they will still be randomized</u>, but will only contain optional items you don't need to beat the game.",
  )
  progression_submarines: bool = option(
    default=False,
    description="This controls whether submarines can contain progress items.<br>"
      "<u>If this is not checked, submarines will still be randomized</u>, but will only contain optional items you don't need to beat the game.",
  )
  progression_eye_reef_chests: bool = option(
    default=False,
    description="This controls whether the chests that appear after clearing out the eye reefs can contain progress items.<br>"
      "<u>If this is not checked, they will still be randomized</u>, but will only contain optional items you don't need to beat the game.",
  )
  progression_big_octos_gunboats: bool = option(
    default=False,
    description="This controls whether the items dropped by Big Octos and Gunboats can contain progress items.<br>"
      "<u>If this is not checked, they will still be randomized</u>, but will only contain optional items you don't need to beat the game.",
  )
  progression_triforce_charts: bool = option(
    default=False,
    description="This controls whether the sunken treasure chests marked on Triforce Charts can contain progress items.<br>"
      "<u>If this is not checked, they will still be randomized</u>, but will only contain optional items you don't need to beat the game.",
  )
  progression_treasure_charts: bool = option(
    default=False,
    description="This controls whether the sunken treasure chests marked on Treasure Charts can contain progress items.<br>"
      "<u>If this is not checked, they will still be randomized</u>, but will only contain optional items you don't need to beat the game.",
  )
  progression_expensive_purchases: bool = option(
    default=True,
    description="This controls whether items that cost a lot of rupees can be progress items (Rock Spire shop, auctions, Tingle's letter, trading quest).<br>"
      "<u>If this is not checked, they will still be randomized</u>, but will only be optional items you don't need to beat the game.",
  )
  progression_island_puzzles: bool = option(
    default=False,
    description="This controls whether various island puzzles can contain progress items (e.g. chests hidden in unusual places).<br>"
      "<u>If this is not checked, they will still be randomized</u>, but will only contain optional items you don't need to beat the game.",
  )
  progression_misc: bool = option(
    default=True,
    description="Miscellaneous locations that don't fit into any of the above categories (outdoors chests, wind shrine, Cyclos, etc).<br>"
      "<u>If this is not checked, they will still be randomized</u>, but will only contain optional items you don't need to beat the game.",
  )
  
  progression_locations: list[str] = option(
    default_factory=lambda: get_default_progression_locations(),
    description="Randomized locations that can have progress items.",
  )
  excluded_locations: list[str] = option(
    default_factory=lambda: [],
    description="Randomized locations that cannot have progress items.",
  )
  #endregion
  
  #region Modes
  keylunacy: bool = option(
    default=False,
    description="Allows dungeon keys (as well as maps and compasses) to appear anywhere in the game, not just in the dungeon they're for.",
  )
  sword_mode: SwordMode = option(
    default=SwordMode.START_WITH_SWORD,
    description="Controls whether you start with the Hero's Sword, the Hero's Sword is randomized, or if there are no swords in the entire game.<br>"
      "Swordless and No Starting Sword are challenge modes. (For Swordless, Phantom Ganon at FF is vulnerable to Skull Hammer.)",
    choice_descriptions={
      SwordMode.START_WITH_SWORD:
        "Start with Hero's Sword: You will start the game with the basic Hero's Sword already in your inventory (the default).",
      SwordMode.NO_STARTING_SWORD:
        "No Starting Sword: You will start the game with no sword, and have to find it somewhere in the world like other randomized items.",
      SwordMode.SWORDLESS:
        "Swordless: You will start the game with no sword, and won't be able to find it anywhere. You have to beat the entire game using other items as weapons instead of the sword.<br>"
        "(Note that Phantom Ganon in FF becomes vulnerable to Skull Hammer in this mode.)",
    },
  )
  required_bosses: bool = option(
    default=False,
    description="In this mode, you will not be allowed to beat the game until certain randomly-chosen bosses are defeated. Nothing in dungeons for other bosses will ever be required.<br>"
      "You can see which islands have the required bosses on them by opening the sea chart and checking which islands have blue quest markers.",
  )
  num_required_bosses: int = option(
    default=4,
    minimum=1,
    maximum=6,
    description="Select the number of randomly-chosen bosses that are required in Required Bosses Mode.<br>"
      "The door to Puppet Ganon will not unlock until you've defeated all of these bosses. Nothing in dungeons for other bosses will ever be required.",
  )
  chest_type_matches_contents: bool = option(
    default=False,
    description="Changes the chest type to reflect its contents. A metal chest has a progress item, a wooden chest has a non-progress item or a consumable, and a green chest has a potentially required dungeon key.",
  )
  trap_chests: bool = option(
    default=False,
    description="Allows the randomizer to place several trapped chests across the game that do not give you items.<br>"
      "Perfect for spicing up any run!",
  )
  #endregion
  
  #region Difficulty
  hero_mode: bool = option(
    default=False,
    description="In Hero Mode, you take four times more damage than normal and heart refills will not drop.",
  )
  logic_obscurity: TrickDifficulty = option(
    default=TrickDifficulty.NONE,
    description="Obscure tricks are ways of obtaining items that are not obvious and may involve thinking outside the box.<br>"
      "This option controls the maximum difficulty of obscure tricks the randomizer will require you to do to beat the game.",
  )
  logic_precision: TrickDifficulty = option(
    default=TrickDifficulty.NONE,
    description="Precise tricks are ways of obtaining items that involve difficult inputs such as accurate aiming or perfect timing.<br>"
      "This option controls the maximum difficulty of precise tricks the randomizer will require you to do to beat the game.",
  )
  #endregion
  
  #region Entrance randomizer
  randomize_dungeon_entrances: bool = option(
    default=False,
    description="Shuffles around which dungeon entrances take you into which dungeons.<br>"
      "(No effect on Forsaken Fortress or Ganon's Tower.)",
  )
  randomize_secret_cave_entrances: bool = option(
    default=False,
    description="Shuffles around which secret cave entrances take you into which secret caves.",
  )
  randomize_miniboss_entrances: bool = option(
    default=False,
    description="Allows dungeon miniboss doors to act as entrances to be randomized.<br>"
      "If this option is enabled with random dungeon entrances, dungeons may nest within each other, forming chains of connected dungeons.",
  )
  randomize_boss_entrances: bool = option(
    default=False,
    description="Allows dungeon boss doors to act as entrances to be randomized.<br>"
      "If this option is enabled with random dungeon entrances, dungeons may nest within each other, forming chains of connected dungeons.",
  )
  randomize_secret_cave_inner_entrances: bool = option(
    default=False,
    description="Allows the pit in Ice Ring Isle's secret cave and the rear exit out of Cliff Plateau Isles' secret cave to act as entrances to be randomized.",
  )
  randomize_fairy_fountain_entrances: bool = option(
    default=False,
    description="Allows the pits that lead down into Fairy Fountains to act as entrances to be randomized.",
  )
  mix_entrances: EntranceMixMode = option(
    default=EntranceMixMode.SEPARATE_DUNGEONS,
    description="Controls whether dungeons should be separated from other randomized entrances, or if all types of randomized entrances can lead into each other.",
    choice_descriptions={
      EntranceMixMode.SEPARATE_DUNGEONS:
        "Dungeon entrances will only be randomized to lead into other dungeons.",
      EntranceMixMode.MIX_DUNGEONS:
        "Dungeon entrances may be randomized to lead into areas that are not dungeons too.",
    },
  )
  #endregion
  
  #region Other randomizers
  randomize_enemies: bool = option(
    default=False,
    hidden=True,
    unbeatable=True,
    description="Randomizes the placement of non-boss enemies.",
  )
  randomize_enemy_palettes: bool = option(
    default=False,
    permalink=True, # TODO: Has special logic to be in when enemy rando is on, but just a placeholder otherwise. How to handle this?
    description="Gives all the enemies in the game random colors.",
  )
  # randomize_music: bool = option(
  #   default=False,
  #   permalink=True, # Music duration affects gameplay (e.g. item get textbox speed).
  #   hidden=True,
  #   description="Shuffles around all the music in the game. This affects background music, combat music, fanfares, etc.",
  # ),
  randomize_starting_island: bool = option(
    default=False,
    description="Randomizes which island you start the game on.",
  )
  randomize_charts: bool = option(
    default=False,
    description="Randomizes which sector is drawn on each Triforce/Treasure Chart.",
  )
  #endregion
  
  #region Hints
  hoho_hints: bool = option(
    default=True,
    description="Places hints on Old Man Ho Ho. Old Man Ho Ho appears at 10 different islands in the game. Talk to Old Man Ho Ho to get hints.",
  )
  fishmen_hints: bool = option(
    default=True,
    description="Places hints on the fishmen. There is one fishman at each of the 49 islands of the Great Sea. Each fishman must be fed an All-Purpose Bait before he will give a hint.",
  )
  korl_hints: bool = option(
    default=False,
    description="Places hints on the King of Red Lions. Talk to the King of Red Lions to get hints.",
  )
  num_item_hints: int = option(
    default=15,
    minimum=0,
    maximum=15,
    description="The number of item hints that will be placed. Item hints tell you which area contains a particular progress item in this seed.<br>"
      "If multiple hint placement options are selected, the hint count will be split evenly among the placement options.",
  )
  num_location_hints: int = option(
    default=5,
    minimum=0,
    maximum=15,
    description="The number of location hints that will be placed. Location hints tell you what item is at a specific location in this seed.<br>"
      "If multiple hint placement options are selected, the hint count will be split evenly among the placement options.",
  )
  num_barren_hints: int = option(
    default=0,
    minimum=0,
    maximum=15,
    description="The number of barren hints that will be placed. Barren hints tell you that an area does not contain any required items in this seed.<br>"
      "If multiple hint placement options are selected, the hint count will be split evenly among the placement options.",
  )
  num_path_hints: int = option(
    default=0,
    minimum=0,
    maximum=15,
    description="The number of path hints that will be placed. Path hints tell you that an area contains an item that is required to reach a particular goal in this seed.<br>"
      "If multiple hint placement options are selected, the hint count will be split evenly among the placement options.",
  )
  cryptic_hints: bool = option(
    default=True,
    description="When this option is selected, all hints will be phrased cryptically instead of telling you the names of locations and items directly.",
  )
  prioritize_remote_hints: bool = option(
    default=False,
    description="When this option is selected, certain locations that are out of the way and time-consuming to complete will take precedence over normal location hints.",
  )
  #endregion
  
  #region Tweaks
  swift_sail: bool = option(
    default=True,
    description="Sailing speed is doubled and the direction of the wind is always at your back as long as the sail is out.",
  )
  instant_text_boxes: bool = option(
    default=True,
    description="Text appears instantly.<br>"
      "Also, the B button is changed to instantly skip through text as long as you hold it down.",
  )
  reveal_full_sea_chart: bool = option(
    default=True,
    description="Start the game with the sea chart fully drawn out.",
  )
  add_shortcut_warps_between_dungeons: bool = option(
    default=False,
    description="Adds new warp pots that act as shortcuts connecting dungeons to each other directly. (DRC, FW, TotG, and separately FF, ET, WT.)<br>"
      "Each pot must be unlocked before it can be used, so you cannot use them to access dungeons you wouldn't already have access to.",
  )
  skip_rematch_bosses: bool = option(
    default=True,
    description="Removes the door in Ganon's Tower that only unlocks when you defeat the rematch versions of Gohma, Kalle Demos, Jalhalla, and Molgera.",
  )
  invert_camera_x_axis: bool = option(
    default=False,
    permalink=False,
    description="Inverts the horizontal axis of camera movement.",
  )
  invert_sea_compass_x_axis: bool = option(
    default=False,
    permalink=False,
    description="Inverts the east-west direction of the compass that shows while at sea.",
  )
  remove_title_and_ending_videos: bool = option(
    default=True,
    permalink=False,
    description="Removes the two prerendered videos that play if you wait on the title screen and after you beat the game. (This cuts the ISO's filesize in half.)<br>"
      "If you keep these videos in, they won't reflect your custom player model or colors.",
  )
  remove_music: bool = option(
    default=False,
    permalink=True, # Music duration affects gameplay (e.g. item get textbox speed).
    description="Mutes all ingame music.",
  )
  switch_targeting_mode: bool = option(
    default=False,
    permalink=False,
    description="Changes the default L-targeting mode when starting a new save file from 'Hold' to 'Switch'.",
  )
  #endregion
  
  #region Starting items
  randomized_gear: list[str] = option(
    default_factory=lambda: sorted(DEFAULT_RANDOMIZED_ITEMS),
    description="Inventory items that will be randomized.",
  )
  starting_gear: list[str] = option(
    default_factory=lambda: sorted(DEFAULT_STARTING_ITEMS),
    description="Items that will be in your inventory at the start of a new game.",
  )
  num_starting_triforce_shards: int = option(
    default=0,
    minimum=0,
    maximum=8,
    description="Change the number of Triforce Shards you start the game with.<br>"
      "The higher you set this, the fewer you will need to find placed randomly to beat the game.",
  )
  starting_pohs: int = option(
    default=0,
    minimum=0,
    maximum=44,
    description="Amount of extra pieces of heart that you start with.",
  )
  starting_hcs: int = option(
    default=3,
    minimum=1,
    maximum=9,
    description="Amount of extra heart containers that you start with.",
  )
  num_extra_starting_items: int = option(
    default=0,
    minimum=0,
    maximum=3,
    description="Amount of extra random progression items that you start with.<br>"
      "Guaranteed to unlock at least one additional location at the start.",
  )
  #endregion
  
  #region Cosmetic
  custom_player_model: str = option(
    default="Link",
    permalink=False,
    description="Replaces Link's model with a custom player model.<br>"
      "These are loaded from the /models folder.",
  )
  player_in_casual_clothes: bool = option(
    default=False,
    permalink=False,
    description="Enable this if you want to wear your casual clothes instead of the Hero's Clothes.",
  )
  disable_custom_player_voice: bool = option(
    default=False,
    permalink=False,
    description="If the chosen custom model comes with custom voice files, you can check this option to turn them off and use Link's normal voice instead.",
  )
  disable_custom_player_items: bool = option(
    default=False,
    permalink=False,
    description="If the chosen custom model comes with custom item models, you can check this option to turn them off and use Link's normal item models instead.",
  )
  custom_color_preset: str = option(
    default="Default",
    permalink=False,
    description="This allows you to select from preset color combinations chosen by the author of the selected player model.",
  )
  custom_colors: dict[str, list] = option(
    default_factory=dict,
    permalink=False,
  )
  #endregion
  
  #region Meta
  do_not_generate_spoiler_log: bool = option(
    default=False,
    description="Prevents the randomizer from generating a text file listing out the locations of all items in this seed. (Also changes where items are placed in this seed.)<br>"
      "<u>Generating a spoiler log is highly recommended even if you don't intend to use it</u>, just in case you get completely stuck.",
  )
  dry_run: bool = option(
    default=False,
    permalink=False,
    description="If this option is selected, <u>no playable ISO will be generated</u>, but the log files will still be created.<br>"
      "This can be useful if you want to generate a spoiler log on a computer where you do not have a vanilla Wind Waker ISO.",
  )
  #endregion
