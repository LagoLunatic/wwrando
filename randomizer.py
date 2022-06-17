
import os
import re
from random import Random
from collections import OrderedDict
import hashlib
import yaml

from fs_helpers import *
from wwlib.yaz0 import Yaz0
from wwlib.rarc import RARC
from wwlib.dol import DOL
from wwlib.rel import REL, RELRelocation, RELRelocationType
from wwlib.gcm import GCM
from wwlib.jpc import JPC
import tweaks
from asm import patcher
from logic.logic import Logic
from wwrando_paths import DATA_PATH, ASM_PATH, RANDO_ROOT_PATH, IS_RUNNING_FROM_SOURCE
import customizer
from wwlib import stage_searcher
from asm import disassemble

try:
  from keys.seed_key import SEED_KEY
except ImportError:
  SEED_KEY = ""

from randomizers import items
from randomizers import charts
from randomizers import starting_island
from randomizers import entrances
from randomizers import music
from randomizers import enemies
from randomizers import palettes

with open(os.path.join(RANDO_ROOT_PATH, "version.txt"), "r") as f:
  VERSION = f.read().strip()

VERSION_WITHOUT_COMMIT = VERSION

# Try to add the git commit hash to the version number if running from source.
if IS_RUNNING_FROM_SOURCE:
  version_suffix = "_NOGIT"
  
  git_commit_head_file = os.path.join(RANDO_ROOT_PATH, ".git", "HEAD")
  if os.path.isfile(git_commit_head_file):
    with open(git_commit_head_file, "r") as f:
      head_file_contents = f.read().strip()
    if head_file_contents.startswith("ref: "):
      # Normal head, HEAD file has a reference to a branch which contains the commit hash
      relative_path_to_hash_file = head_file_contents[len("ref: "):]
      path_to_hash_file = os.path.join(RANDO_ROOT_PATH, ".git", relative_path_to_hash_file)
      if os.path.isfile(path_to_hash_file):
        with open(path_to_hash_file, "r") as f:
          hash_file_contents = f.read()
        version_suffix = "_" + hash_file_contents[:7]
    elif re.search(r"^[0-9a-f]{40}$", head_file_contents):
      # Detached head, commit hash directly in the HEAD file
      version_suffix = "_" + head_file_contents[:7]
  
  VERSION += version_suffix

CLEAN_WIND_WAKER_ISO_MD5 = 0xd8e4d45af2032a081a0f446384e9261b

# The below are options that could be used to cheat in races.
# They do not naturally change algorithmic item distribution, but do change the availability of information on item distribution.
# To prevent this possibility, we change the RNG seed itself for each one of these options that is selected.
# This ensures that item distribution is different between people with the same seed but different hints, for example.
RNG_CHANGING_OPTIONS = [
  "fishmen_hints",
  "hoho_hints",
  "korl_hints",
  "num_hints",
  "do_not_generate_spoiler_log",
]

class TooFewProgressionLocationsError(Exception):
  pass

class InvalidCleanISOError(Exception):
  pass

class Randomizer:
  def __init__(self, seed, clean_iso_path, randomized_output_folder, options, permalink=None, cmd_line_args=OrderedDict()):
    self.randomized_output_folder = randomized_output_folder
    self.options = options
    self.seed = seed
    self.permalink = permalink
    self.seed_hash = None
    
    self.dry_run = ("-dry" in cmd_line_args)
    self.disassemble = ("-disassemble" in cmd_line_args)
    self.export_disc_to_folder = ("-exportfolder" in cmd_line_args)
    self.no_logs = ("-nologs" in cmd_line_args)
    self.bulk_test = ("-bulk" in cmd_line_args)
    if self.bulk_test:
      self.dry_run = True
      self.no_logs = True
    self.print_used_flags = ("-printflags" in cmd_line_args)
    if ("-noitemrando" in cmd_line_args) and IS_RUNNING_FROM_SOURCE:
      self.randomize_items = False
    else:
      self.randomize_items = True
    self.map_select = ("-mapselect" in cmd_line_args)
    self.heap_display = ("-heap" in cmd_line_args)
    
    self.test_room_args = None
    if "-test" in cmd_line_args:
      args = cmd_line_args["-test"]
      if args is not None:
        stage, room, spawn = args.split(",")
        self.test_room_args = {"stage": stage, "room": int(room), "spawn": int(spawn)}
    
    seed_string = self.seed
    if self.options.get("do_not_generate_spoiler_log"):
      seed_string += SEED_KEY
    
    self.integer_seed = self.convert_string_to_integer_md5(seed_string)
    self.rng = self.get_new_rng()
    
    self.arcs_by_path = {}
    self.jpcs_by_path = {}
    self.rels_by_path = {}
    self.symbol_maps_by_path = {}
    self.raw_files_by_path = {}
    self.used_actor_ids = list(range(0x1F6))
    
    self.read_text_file_lists()
    
    if not self.dry_run:
      if not os.path.isfile(clean_iso_path):
        raise InvalidCleanISOError("Clean WW ISO does not exist: %s" % clean_iso_path)
      
      self.verify_supported_version(clean_iso_path)
      
      self.gcm = GCM(clean_iso_path)
      self.gcm.read_entire_disc()
      
      dol_data = self.gcm.read_file_data("sys/main.dol")
      self.dol = DOL()
      self.dol.read(dol_data)
      
      try:
        self.chart_list = self.get_arc("files/res/Msg/fmapres.arc").get_file("cmapdat.bin")
      except (InvalidOffsetError, AssertionError):
        # An invalid offset error when reading fmapres.arc seems to happen when the user has a corrupted clean ISO.
        # Alternatively, fmapres.arc's magic bytes not being RARC can also happen here, also caused by a corrupted clean ISO.
        # The reason for this is unknown, but when this happens check the ISO's MD5 and if it's wrong say so in an error message.
        self.verify_correct_clean_iso_md5(clean_iso_path)
        
        # But if the ISO's MD5 is correct just raise the normal offset error.
        raise
      
      self.bmg = self.get_arc("files/res/Msg/bmgres.arc").get_file("zel_00.bmg")
      
      if self.disassemble:
        self.disassemble_all_code()
      if self.print_used_flags:
        stage_searcher.print_all_used_item_pickup_flags(self)
        stage_searcher.print_all_used_chest_open_flags(self)
        stage_searcher.print_all_event_flags_used_by_stb_cutscenes(self)
    
    # Starting items. This list is read by the Logic when initializing your currently owned items list.
    self.starting_items = [
      "Wind Waker",
      "Wind's Requiem",
      "Ballad of Gales",
      "Song of Passing",
      "Boat's Sail",
    ]
    self.starting_items += self.options.get("starting_gear", [])
    
    if self.options.get("sword_mode") == "Start with Hero's Sword":
      self.starting_items.append("Progressive Sword")
    # Add starting Triforce Shards.
    num_starting_triforce_shards = int(self.options.get("num_starting_triforce_shards", 0))
    for i in range(num_starting_triforce_shards):
      self.starting_items.append("Triforce Shard %d" % (i+1))
    
    starting_pohs = self.options.get("starting_pohs")
    for i in range(starting_pohs):
      self.starting_items.append("Piece of Heart")
    
    starting_hcs = self.options.get("starting_hcs")
    for i in range(starting_hcs):
      self.starting_items.append("Heart Container")
    
    # Default entrances connections to be used if the entrance randomizer is not on.
    self.entrance_connections = OrderedDict([
      ("Dungeon Entrance On Dragon Roost Island", "Dragon Roost Cavern"),
      ("Dungeon Entrance In Forest Haven Sector", "Forbidden Woods"),
      ("Dungeon Entrance In Tower of the Gods Sector", "Tower of the Gods"),
      ("Dungeon Entrance On Headstone Island", "Earth Temple"),
      ("Dungeon Entrance On Gale Isle", "Wind Temple"),
      
      ("Secret Cave Entrance on Outset Island", "Savage Labyrinth"),
      ("Secret Cave Entrance on Dragon Roost Island", "Dragon Roost Island Secret Cave"),
      ("Secret Cave Entrance on Fire Mountain", "Fire Mountain Secret Cave"),
      ("Secret Cave Entrance on Ice Ring Isle", "Ice Ring Isle Secret Cave"),
      ("Secret Cave Entrance on Private Oasis", "Cabana Labyrinth"),
      ("Secret Cave Entrance on Needle Rock Isle", "Needle Rock Isle Secret Cave"),
      ("Secret Cave Entrance on Angular Isles", "Angular Isles Secret Cave"),
      ("Secret Cave Entrance on Boating Course", "Boating Course Secret Cave"),
      ("Secret Cave Entrance on Stone Watcher Island", "Stone Watcher Island Secret Cave"),
      ("Secret Cave Entrance on Overlook Island", "Overlook Island Secret Cave"),
      ("Secret Cave Entrance on Bird's Peak Rock", "Bird's Peak Rock Secret Cave"),
      ("Secret Cave Entrance on Pawprint Isle", "Pawprint Isle Chuchu Cave"),
      ("Secret Cave Entrance on Pawprint Isle Side Isle", "Pawprint Isle Wizzrobe Cave"),
      ("Secret Cave Entrance on Diamond Steppe Island", "Diamond Steppe Island Warp Maze Cave"),
      ("Secret Cave Entrance on Bomb Island", "Bomb Island Secret Cave"),
      ("Secret Cave Entrance on Rock Spire Isle", "Rock Spire Isle Secret Cave"),
      ("Secret Cave Entrance on Shark Island", "Shark Island Secret Cave"),
      ("Secret Cave Entrance on Cliff Plateau Isles", "Cliff Plateau Isles Secret Cave"),
      ("Secret Cave Entrance on Horseshoe Island", "Horseshoe Island Secret Cave"),
      ("Secret Cave Entrance on Star Island", "Star Island Secret Cave"),
    ])
    self.dungeon_and_cave_island_locations = OrderedDict([
      ("Dragon Roost Cavern", "Dragon Roost Island"),
      ("Forbidden Woods", "Forest Haven"),
      ("Tower of the Gods", "Tower of the Gods"),
      ("Earth Temple", "Headstone Island"),
      ("Wind Temple", "Gale Isle"),
      
      ("Secret Cave Entrance on Outset Island", "Outset Island"),
      ("Secret Cave Entrance on Dragon Roost Island", "Dragon Roost Island"),
      ("Secret Cave Entrance on Fire Mountain", "Fire Mountain"),
      ("Secret Cave Entrance on Ice Ring Isle", "Ice Ring Isle"),
      ("Secret Cave Entrance on Private Oasis", "Private Oasis"),
      ("Secret Cave Entrance on Needle Rock Isle", "Needle Rock Isle"),
      ("Secret Cave Entrance on Angular Isles", "Angular Isles"),
      ("Secret Cave Entrance on Boating Course", "Boating Course"),
      ("Secret Cave Entrance on Stone Watcher Island", "Stone Watcher Island"),
      ("Secret Cave Entrance on Overlook Island", "Overlook Island"),
      ("Secret Cave Entrance on Bird's Peak Rock", "Bird's Peak Rock"),
      ("Secret Cave Entrance on Pawprint Isle", "Pawprint Isle"),
      ("Secret Cave Entrance on Pawprint Isle Side Isle", "Pawprint Isle"),
      ("Secret Cave Entrance on Diamond Steppe Island", "Diamond Steppe Island"),
      ("Secret Cave Entrance on Bomb Island", "Bomb Island"),
      ("Secret Cave Entrance on Rock Spire Isle", "Rock Spire Isle"),
      ("Secret Cave Entrance on Shark Island", "Shark Island"),
      ("Secret Cave Entrance on Cliff Plateau Isles", "Cliff Plateau Isles"),
      ("Secret Cave Entrance on Horseshoe Island", "Horseshoe Island"),
      ("Secret Cave Entrance on Star Island", "Star Island"),
    ])
    
    # Default starting island (Outset) if the starting island randomizer is not on.
    self.starting_island_index = 44
    
    # Default charts for each island.
    self.island_number_to_chart_name = OrderedDict([
      (1, "Treasure Chart 25"),
      (2, "Treasure Chart 7"),
      (3, "Treasure Chart 24"),
      (4, "Triforce Chart 2"),
      (5, "Treasure Chart 11"),
      (6, "Triforce Chart 7"),
      (7, "Treasure Chart 13"),
      (8, "Treasure Chart 41"),
      (9, "Treasure Chart 29"),
      (10, "Treasure Chart 22"),
      (11, "Treasure Chart 18"),
      (12, "Treasure Chart 30"),
      (13, "Treasure Chart 39"),
      (14, "Treasure Chart 19"),
      (15, "Treasure Chart 8"),
      (16, "Treasure Chart 2"),
      (17, "Treasure Chart 10"),
      (18, "Treasure Chart 26"),
      (19, "Treasure Chart 3"),
      (20, "Treasure Chart 37"),
      (21, "Treasure Chart 27"),
      (22, "Treasure Chart 38"),
      (23, "Triforce Chart 1"),
      (24, "Treasure Chart 21"),
      (25, "Treasure Chart 6"),
      (26, "Treasure Chart 14"),
      (27, "Treasure Chart 34"),
      (28, "Treasure Chart 5"),
      (29, "Treasure Chart 28"),
      (30, "Treasure Chart 35"),
      (31, "Triforce Chart 3"),
      (32, "Triforce Chart 6"),
      (33, "Treasure Chart 1"),
      (34, "Treasure Chart 20"),
      (35, "Treasure Chart 36"),
      (36, "Treasure Chart 23"),
      (37, "Treasure Chart 12"),
      (38, "Treasure Chart 16"),
      (39, "Treasure Chart 4"),
      (40, "Treasure Chart 17"),
      (41, "Treasure Chart 31"),
      (42, "Triforce Chart 5"),
      (43, "Treasure Chart 9"),
      (44, "Triforce Chart 4"),
      (45, "Treasure Chart 40"),
      (46, "Triforce Chart 8"),
      (47, "Treasure Chart 15"),
      (48, "Treasure Chart 32"),
      (49, "Treasure Chart 33"),
    ])
    
    # This list will hold the randomly selected dungeon boss locations that are required in race mode.
    # If race mode is not on, this list will remain empty.
    self.race_mode_required_locations = []
    # This list will hold the dungeon names of the race mode required locations.
    # If race mode is not on, this list will remain empty.
    self.race_mode_required_dungeons = []
    # This list will hold all item location names that should not have any items in them in race mode.
    # If race mode is not on, this list will remain empty.
    self.race_mode_banned_locations = []
    
    self.custom_model_name = self.options.get("custom_player_model", "Link")
    self.using_custom_sail_texture = False
    
    self.logic = Logic(self)
    
    num_progress_locations = self.logic.get_num_progression_locations()
    max_race_mode_banned_locations = self.logic.get_max_race_mode_banned_locations()
    num_progress_items = self.logic.get_num_progression_items()
    if num_progress_locations - max_race_mode_banned_locations < num_progress_items: 
      error_message = "Not enough progress locations to place all progress items.\n\n"
      error_message += "Total progress items: %d\n" % num_progress_items
      error_message += "Progress locations with current options: %d\n" % num_progress_locations
      if max_race_mode_banned_locations > 0:
        error_message += "Maximum Race Mode banned locations: %d\n" % max_race_mode_banned_locations
      error_message += "\nYou need to check more of the progress location options in order to give the randomizer enough space to place all the items."
      raise TooFewProgressionLocationsError(error_message)
    
    # We need to determine if the user's selected options result in a dungeons-only-start.
    # Dungeons-only-start meaning that the only locations accessible at the start of the run are dungeon locations.
    # e.g. If the user selects Dungeons, Expensive Purchases, and Sunken Treasures, the dungeon locations are the only ones the player can check first.
    # We need to distinguish this situation because it can cause issues for the randomizer's item placement logic (specifically when placing keys in DRC).
    self.logic.temporarily_make_dungeon_entrance_macros_impossible()
    accessible_undone_locations = self.logic.get_accessible_remaining_locations(for_progression=True)
    if len(accessible_undone_locations) == 0:
      self.dungeons_only_start = True
    else:
      self.dungeons_only_start = False
    self.logic.update_entrance_connection_macros() # Reset the dungeon entrance macros.
    
    # Also determine if these options result in a dungeons-and-caves-only-start.
    # Dungeons-and-caves-only-start means the only locations accessible at the start of the run are dungeon or secret cave locations.
    # This situation can also cause issues for the item placement logic (specifically when placing the first item of the run).
    self.logic.temporarily_make_entrance_macros_impossible()
    accessible_undone_locations = self.logic.get_accessible_remaining_locations(for_progression=True)
    if len(accessible_undone_locations) == 0:
      self.dungeons_and_caves_only_start = True
    else:
      self.dungeons_and_caves_only_start = False
    self.logic.update_entrance_connection_macros() # Reset the entrance macros.
  
  def randomize(self):
    options_completed = 0
    yield("Modifying game code...", options_completed)
    
    customizer.decide_on_link_model(self)
    
    if not self.dry_run:
      self.apply_necessary_tweaks()
      
      if self.options.get("swift_sail"):
        tweaks.make_sail_behave_like_swift_sail(self)
      if self.options.get("instant_text_boxes"):
        tweaks.make_all_text_instant(self)
      if self.options.get("reveal_full_sea_chart"):
        patcher.apply_patch(self, "reveal_sea_chart")
      if self.options.get("add_shortcut_warps_between_dungeons"):
        tweaks.add_inter_dungeon_warp_pots(self)
      if self.options.get("invert_camera_x_axis"):
        patcher.apply_patch(self, "invert_camera_x_axis")
      if self.options.get("invert_sea_compass_x_axis"):
        patcher.apply_patch(self, "invert_sea_compass_x_axis")
      tweaks.update_skip_rematch_bosses_game_variable(self)
      tweaks.update_sword_mode_game_variable(self)
      if self.options.get("sword_mode") == "Swordless":
        patcher.apply_patch(self, "swordless")
        tweaks.update_text_for_swordless(self)
      tweaks.update_starting_gear(self)
      if self.options.get("chest_type_matches_contents"):
        tweaks.replace_dark_wood_chest_texture(self)
      if self.options.get("remove_title_and_ending_videos"):
        tweaks.remove_title_and_ending_videos(self)
      if self.options.get("remove_music"):
        patcher.apply_patch(self, "remove_music")
      if self.map_select:
        patcher.apply_patch(self, "map_select")
      if IS_RUNNING_FROM_SOURCE or "BETA" in VERSION_WITHOUT_COMMIT:
        tweaks.enable_developer_mode(self)
      if self.heap_display:
        tweaks.enable_heap_display(self)
      
      if self.test_room_args is not None:
        tweaks.test_room(self)
    options_completed += 1
    
    yield("Randomizing...", options_completed)
    
    if self.options.get("randomize_charts"):
      self.reset_rng()
      charts.randomize_charts(self)
    
    if self.options.get("randomize_starting_island"):
      self.reset_rng()
      starting_island.randomize_starting_island(self)
    
    if self.options.get("randomize_entrances") not in ["Disabled", None]:
      self.reset_rng()
      entrances.randomize_entrances(self)
    
    if self.options.get("randomize_music"):
      self.reset_rng()
      music.randomize_music(self)
    
    if not self.dry_run:
      # Randomize the color of the big pig on Outset by setting the bitfield of which pigs were captured in the prologue.
      self.reset_rng()
      captured_pigs_bitfield = self.rng.choice([
        0x01, # Pink only
        0x02, # Speckled only
        0x04, # Black only
      ])
      captured_prologue_pigs_bitfield_address = self.main_custom_symbols["captured_prologue_pigs_bitfield"]
      self.dol.write_data(write_u8, captured_prologue_pigs_bitfield_address, captured_pigs_bitfield)
    
    options_completed += 1
    
    # Enemies must be randomized before items in order for the enemy logic to properly take into account what items you do and don't start with.
    if self.options.get("randomize_enemies"):
      yield("Randomizing enemy locations...", options_completed)
      self.reset_rng()
      enemies.randomize_enemies(self)
    
    if self.options.get("randomize_enemy_palettes"):
      yield("Randomizing enemy colors...", options_completed)
      self.reset_rng()
      palettes.randomize_enemy_palettes(self)
      options_completed += 10
    
    yield("Randomizing items...", options_completed)
    if self.randomize_items:
      self.reset_rng()
      items.randomize_items(self)
    
    options_completed += 2
    
    yield("Saving items...", options_completed)
    if self.randomize_items and not self.dry_run:
      items.write_changed_items(self)
      tweaks.randomize_and_update_hints(self)
    
    if not self.dry_run:
      self.apply_necessary_post_randomization_tweaks()
    options_completed += 7
    
    yield("Saving randomized ISO...", options_completed)
    if not self.dry_run:
      generator = self.save_randomized_iso()
      while True:
        # Need to use a while loop to go through the generator instead of a for loop, as a for loop would silently exit if a StopIteration error ever happened for any reason.
        next_progress_text, files_done = next(generator)
        if files_done == -1:
          break
        percentage_done = files_done/len(self.gcm.files_by_path)
        yield("Saving randomized ISO...", options_completed+int(percentage_done*9))
    options_completed += 9
    yield("Writing logs...", options_completed)
    
    if self.randomize_items:
      if not self.options.get("do_not_generate_spoiler_log"):
        self.write_spoiler_log()
      self.write_non_spoiler_log()
    
    yield("Done", -1)
  
  def apply_necessary_tweaks(self):
    patcher.apply_patch(self, "custom_data")
    patcher.apply_patch(self, "custom_funcs")
    patcher.apply_patch(self, "make_game_nonlinear")
    patcher.apply_patch(self, "remove_cutscenes")
    patcher.apply_patch(self, "flexible_item_locations")
    patcher.apply_patch(self, "fix_vanilla_bugs")
    patcher.apply_patch(self, "misc_rando_features")
    tweaks.add_custom_actor_rels(self)
    tweaks.skip_wakeup_intro_and_start_at_dock(self)
    tweaks.start_ship_at_outset(self)
    tweaks.fix_deku_leaf_model(self)
    tweaks.allow_all_items_to_be_field_items(self)
    tweaks.remove_shop_item_forced_uniqueness_bit(self)
    tweaks.remove_forsaken_fortress_2_cutscenes(self)
    tweaks.make_items_progressive(self)
    tweaks.add_ganons_tower_warp_to_ff2(self)
    tweaks.add_chest_in_place_medli_grappling_hook_gift(self)
    tweaks.add_chest_in_place_queen_fairy_cutscene(self)
    #tweaks.add_cube_to_earth_temple_first_room(self)
    tweaks.add_more_magic_jars(self)
    tweaks.modify_title_screen_logo(self)
    tweaks.update_game_name_icon_and_banners(self)
    tweaks.allow_dungeon_items_to_appear_anywhere(self)
    #tweaks.remove_ballad_of_gales_warp_in_cutscene(self)
    tweaks.fix_shop_item_y_offsets(self)
    tweaks.shorten_zephos_event(self)
    tweaks.update_korl_dialogue(self)
    tweaks.set_num_starting_triforce_shards(self)
    tweaks.set_starting_health(self)
    tweaks.add_pirate_ship_to_windfall(self)
    tweaks.remove_makar_kidnapping_event(self)
    tweaks.increase_player_movement_speeds(self)
    tweaks.add_chart_number_to_item_get_messages(self)
    tweaks.increase_grapple_animation_speed(self)
    tweaks.increase_block_moving_animation(self)
    tweaks.increase_misc_animations(self)
    tweaks.shorten_auction_intro_event(self)
    tweaks.disable_invisible_walls(self)
    tweaks.add_hint_signs(self)
    tweaks.prevent_door_boulder_softlocks(self)
    tweaks.update_tingle_statue_item_get_funcs(self)
    patcher.apply_patch(self, "tingle_chests_without_tuner")
    tweaks.make_tingle_statue_reward_rupee_rainbow_colored(self)
    tweaks.show_seed_hash_on_name_entry_screen(self)
    tweaks.fix_ghost_ship_chest_crash(self)
    tweaks.implement_key_bag(self)
    tweaks.add_chest_in_place_of_jabun_cutscene(self)
    tweaks.add_chest_in_place_of_master_sword(self)
    tweaks.update_beedle_spoil_selling_text(self)
    tweaks.fix_totg_warp_out_spawn_pos(self)
    tweaks.remove_phantom_ganon_requirement_from_eye_reefs(self)
    tweaks.fix_forsaken_fortress_door_softlock(self)
    tweaks.add_new_bog_warp(self)
    tweaks.make_rat_holes_visible_from_behind(self)
    tweaks.add_failsafe_id_0_spawns(self)
    tweaks.remove_minor_panning_cutscenes(self)
    tweaks.fix_message_closing_sound_on_quest_status_screen(self)
    tweaks.fix_stone_head_bugs(self)
    tweaks.show_number_of_tingle_statues_on_quest_status_screen(self)
    patcher.apply_patch(self, "flexible_enemies")
    tweaks.add_shortcut_warps_into_dungeons(self)
    
    customizer.replace_link_model(self)
    tweaks.change_starting_clothes(self)
    tweaks.check_hide_ship_sail(self)
    customizer.change_player_custom_colors(self)
  
  def apply_necessary_post_randomization_tweaks(self):
    if self.randomize_items:
      tweaks.update_shop_item_descriptions(self)
      tweaks.update_auction_item_names(self)
      tweaks.update_battlesquid_item_names(self)
      tweaks.update_item_names_in_letter_advertising_rock_spire_shop(self)
      tweaks.update_savage_labyrinth_hint_tablet(self)
    tweaks.show_quest_markers_on_sea_chart_for_dungeons(self, dungeon_names=self.race_mode_required_dungeons)
    tweaks.prevent_fire_mountain_lava_softlock(self)
  
  def verify_supported_version(self, clean_iso_path):
    with open(clean_iso_path, "rb") as f:
      game_id = try_read_str(f, 0, 6)
    if game_id != "GZLE01":
      if game_id and game_id.startswith("GZL"):
        raise InvalidCleanISOError("Invalid version of Wind Waker. Only the USA version is supported by this randomizer.")
      else:
        raise InvalidCleanISOError("Invalid game given as the clean ISO. You must specify a Wind Waker ISO (USA version).")
  
  def verify_correct_clean_iso_md5(self, clean_iso_path):
    md5 = hashlib.md5()
    
    with open(clean_iso_path, "rb") as f:
      while True:
        chunk = f.read(1024*1024)
        if not chunk:
          break
        md5.update(chunk)
    
    integer_md5 = int(md5.hexdigest(), 16)
    if integer_md5 != CLEAN_WIND_WAKER_ISO_MD5:
      raise InvalidCleanISOError("Invalid clean Wind Waker ISO. Your ISO may be corrupted.\n\nCorrect ISO MD5 hash: %x\nYour ISO's MD5 hash: %x" % (CLEAN_WIND_WAKER_ISO_MD5, integer_md5))
  
  def read_text_file_lists(self):
    # Get item names.
    self.item_names = {}
    self.item_name_to_id = {}
    with open(os.path.join(DATA_PATH, "item_names.txt"), "r") as f:
      matches = re.findall(r"^([0-9a-f]{2}) - (.+)$", f.read(), re.IGNORECASE | re.MULTILINE)
    for item_id, item_name in matches:
      if item_name:
        item_id = int(item_id, 16)
        self.item_names[item_id] = item_name
        if item_name in self.item_name_to_id:
          raise Exception("Duplicate item name: " + item_name)
        self.item_name_to_id[item_name] = item_id
    
    # Get stage and island names for debug purposes.
    self.stage_names = {}
    with open(os.path.join(DATA_PATH, "stage_names.txt"), "r") as f:
      while True:
        stage_folder = f.readline()
        if not stage_folder:
          break
        stage_name = f.readline()
        self.stage_names[stage_folder.strip()] = stage_name.strip()
    self.island_names = {}
    self.island_number_to_name = {}
    self.island_name_to_number = {}
    with open(os.path.join(DATA_PATH, "island_names.txt"), "r") as f:
      while True:
        room_arc_name = f.readline()
        if not room_arc_name:
          break
        island_name = f.readline().strip()
        self.island_names[room_arc_name.strip()] = island_name
        island_number = int(re.search(r"Room(\d+)", room_arc_name).group(1))
        self.island_number_to_name[island_number] = island_name
        self.island_name_to_number[island_name] = island_number
    
    self.item_ids_without_a_field_model = []
    with open(os.path.join(DATA_PATH, "items_without_field_models.txt"), "r") as f:
      matches = re.findall(r"^([0-9a-f]{2}) ", f.read(), re.IGNORECASE | re.MULTILINE)
    for item_id in matches:
      if item_name:
        item_id = int(item_id, 16)
        self.item_ids_without_a_field_model.append(item_id)
    
    self.arc_name_pointers = {}
    with open(os.path.join(DATA_PATH, "item_resource_arc_name_pointers.txt"), "r") as f:
      matches = re.findall(r"^([0-9a-f]{2}) ([0-9a-f]{8}) ", f.read(), re.IGNORECASE | re.MULTILINE)
    for item_id, arc_name_pointer in matches:
      item_id = int(item_id, 16)
      arc_name_pointer = int(arc_name_pointer, 16)
      self.arc_name_pointers[item_id] = arc_name_pointer
    
    self.icon_name_pointer = {}
    with open(os.path.join(DATA_PATH, "item_resource_icon_name_pointers.txt"), "r") as f:
      matches = re.findall(r"^([0-9a-f]{2}) ([0-9a-f]{8}) ", f.read(), re.IGNORECASE | re.MULTILINE)
    for item_id, icon_name_pointer in matches:
      item_id = int(item_id, 16)
      icon_name_pointer = int(icon_name_pointer, 16)
      self.icon_name_pointer[item_id] = icon_name_pointer
    
    with open(os.path.join(ASM_PATH, "custom_symbols.txt"), "r") as f:
      self.custom_symbols = yaml.safe_load(f)
    self.main_custom_symbols = self.custom_symbols["sys/main.dol"]
    
    with open(os.path.join(ASM_PATH, "free_space_start_offsets.txt"), "r") as f:
      self.free_space_start_offsets = yaml.safe_load(f)
    
    with open(os.path.join(DATA_PATH, "progress_item_hints.txt"), "r") as f:
      self.progress_item_hints = yaml.safe_load(f)
    
    with open(os.path.join(DATA_PATH, "island_name_hints.txt"), "r") as f:
      self.island_name_hints = yaml.safe_load(f)
    
    with open(os.path.join(DATA_PATH, "enemy_types.txt"), "r") as f:
      self.enemy_types = yaml.safe_load(f)
    
    with open(os.path.join(DATA_PATH, "palette_randomizable_files.txt"), "r") as f:
      self.palette_randomizable_files = yaml.safe_load(f)
  
  def register_renamed_item(self, item_id, item_name):
    self.item_name_to_id[item_name] = item_id
    self.item_names[item_id] = item_name
  
  def get_arc(self, arc_path):
    arc_path = arc_path.replace("\\", "/")
    
    if arc_path in self.arcs_by_path:
      return self.arcs_by_path[arc_path]
    else:
      data = self.gcm.read_file_data(arc_path)
      arc = RARC()
      arc.read(data)
      self.arcs_by_path[arc_path] = arc
      return arc
  
  def get_jpc(self, jpc_path):
    jpc_path = jpc_path.replace("\\", "/")
    
    if jpc_path in self.jpcs_by_path:
      return self.jpcs_by_path[jpc_path]
    else:
      data = self.gcm.read_file_data(jpc_path)
      jpc = JPC(data)
      self.jpcs_by_path[jpc_path] = jpc
      return jpc
  
  def get_rel(self, rel_path):
    rel_path = rel_path.replace("\\", "/")
    
    if rel_path in self.rels_by_path:
      return self.rels_by_path[rel_path]
    else:
      if not rel_path.startswith("files/rels/"):
        raise Exception("Invalid REL path: %s" % rel_path)
      
      rel_name = os.path.basename(rel_path)
      rels_arc = self.get_arc("files/RELS.arc")
      rel_file_entry = rels_arc.get_file_entry(rel_name)
      
      if rel_file_entry:
        rel_file_entry.decompress_data_if_necessary()
        data = rel_file_entry.data
      else:
        data = self.gcm.read_file_data(rel_path)
      
      rel = REL()
      rel.read(data)
      self.rels_by_path[rel_path] = rel
      return rel
  
  def get_symbol_map(self, map_path):
    map_path = map_path.replace("\\", "/")
    
    if map_path in self.symbol_maps_by_path:
      return self.symbol_maps_by_path[map_path]
    else:
      data = self.gcm.read_file_data(map_path)
      map_text = read_all_bytes(data).decode("ascii")
      
      if map_path == "files/maps/framework.map":
        addr_to_name_map = disassemble.get_main_symbols(map_text)
      else:
        rel_name = os.path.splitext(os.path.basename(map_path))[0]
        rel = self.get_rel("files/rels/%s.rel" % rel_name)
        addr_to_name_map = disassemble.get_rel_symbols(rel, map_text)
      
      symbol_map = {}
      for address, name in addr_to_name_map.items():
        symbol_map[name] = address
      
      self.symbol_maps_by_path[map_path] = symbol_map
      return symbol_map
  
  def get_raw_file(self, file_path):
    file_path = file_path.replace("\\", "/")
    
    if file_path in self.raw_files_by_path:
      return self.raw_files_by_path[file_path]
    else:
      if file_path.startswith("files/rels/"):
        raise Exception("Cannot read a REL as a raw file.")
      elif file_path == "sys/main.dol":
        raise Exception("Cannot read the DOL as a raw file.")
      
      data = self.gcm.read_file_data(file_path)
      
      if Yaz0.check_is_compressed(data):
        data = Yaz0.decompress(data)
      
      self.raw_files_by_path[file_path] = data
      return data
  
  def replace_arc(self, arc_path, new_data):
    if arc_path not in self.gcm.files_by_path:
      raise Exception("Cannot replace RARC that doesn't exist: " + arc_path)
    
    arc = RARC()
    arc.read(new_data)
    self.arcs_by_path[arc_path] = arc
  
  def replace_raw_file(self, file_path, new_data):
    if file_path not in self.gcm.files_by_path:
      raise Exception("Cannot replace file that doesn't exist: " + file_path)
    
    self.raw_files_by_path[file_path] = new_data
  
  def add_new_raw_file(self, file_path, new_data):
    if file_path.lower() in self.gcm.files_by_path_lowercase:
      raise Exception("Cannot add a new file that has the same path and name as an existing one: " + file_path)
    
    self.gcm.add_new_file(file_path, new_data)
    self.raw_files_by_path[file_path] = new_data
  
  def add_new_rel(self, rel_path, new_rel, section_index_of_actor_profile, offset_of_actor_profile):
    if not rel_path.startswith("files/rels/"):
      raise Exception("Cannot add a new REL to a folder besides files/rels/: " + rel_path)
    if rel_path.lower() in self.gcm.files_by_path_lowercase:
      raise Exception("Cannot add a new REL that has the same name as an existing one: " + rel_path)
    
    # Read the actor ID out of the actor profile.
    section_data_actor_profile = new_rel.sections[section_index_of_actor_profile].data
    new_actor_id = read_u16(section_data_actor_profile, offset_of_actor_profile+8)
    
    if new_actor_id in self.used_actor_ids:
      raise Exception("Cannot add a new REL with an actor ID that is already used:\nActor ID: %03X\nNew REL path: %s" % (new_actor_id, rel_path))
    
    # We need to add the new REL to the profile list.
    profile_list = self.get_rel("files/rels/f_pc_profile_lst.rel")
    
    rel_relocation = RELRelocation()
    rel_relocation.relocation_type = RELRelocationType.R_PPC_ADDR32
    
    rel_relocation.curr_section_num = 4 # List section
    rel_relocation.relocation_offset = new_actor_id*4 # Offset in the list
    
    # Write a null placeholder for the pointer to the profile that will be relocated.
    list_data = profile_list.sections[rel_relocation.curr_section_num].data
    write_u32(list_data, new_actor_id*4, 0)
    # For some reason, there's an extra four 0x00 bytes after the last entry in the list, so we put that there just to be safe.
    write_u32(list_data, new_actor_id*4+4, 0)
    
    rel_relocation.section_num_to_relocate_against = section_index_of_actor_profile
    rel_relocation.symbol_address = offset_of_actor_profile
    
    if new_rel.id in profile_list.relocation_entries_for_module:
      raise Exception("Cannot add a new REL with a unique ID that is already present in the profile list:\nREL ID: %03X\nNew REL path: %s" % (new_rel.id, rel_path))
    
    profile_list.relocation_entries_for_module[new_rel.id] = [rel_relocation]
    
    # Then add the REL to the game's filesystem.
    self.gcm.add_new_file(rel_path)
    self.rels_by_path[rel_path] = new_rel
    
    # Don't allow this actor ID to be used again by any more custom RELs we add.
    self.used_actor_ids.append(new_actor_id)
  
  def save_randomized_iso(self):
    self.bmg.save_changes()
    
    for file_path, data in self.raw_files_by_path.items():
      self.gcm.changed_files[file_path] = data
    
    self.dol.save_changes()
    self.gcm.changed_files["sys/main.dol"] = self.dol.data
    
    for rel_path, rel in self.rels_by_path.items():
      rel.save_changes(preserve_section_data_offsets=True)
      
      rel_name = os.path.basename(rel_path)
      rels_arc = self.get_arc("files/RELS.arc")
      rel_file_entry = rels_arc.get_file_entry(rel_name)
      if rel_file_entry:
        # The REL already wrote to the same BytesIO object as the file entry uses, so no need to do anything more here.
        assert rel_file_entry.data == rel.data
      else:
        self.gcm.changed_files[rel_path] = rel.data
    
    for arc_path, arc in self.arcs_by_path.items():
      for file_name, instantiated_file in arc.instantiated_object_files.items():
        if file_name == "event_list.dat":
          instantiated_file.save_changes()
      
      arc.save_changes()
      self.gcm.changed_files[arc_path] = arc.data
    
    for jpc_path, jpc in self.jpcs_by_path.items():
      jpc.save_changes()
      self.gcm.changed_files[jpc_path] = jpc.data
    
    if self.export_disc_to_folder:
      output_folder_path = os.path.join(self.randomized_output_folder, "WW Random %s" % self.seed)
      generator = self.gcm.export_disc_to_folder_with_changed_files(output_folder_path)
    else:
      output_file_path = os.path.join(self.randomized_output_folder, "WW Random %s.iso" % self.seed)
      generator = self.gcm.export_disc_to_iso_with_changed_files(output_file_path)
    
    while True:
      # Need to use a while loop to go through the generator instead of a for loop, as a for loop would silently exit if a StopIteration error ever happened for any reason.
      next_progress_text, files_done = next(generator)
      if files_done == -1:
        break
      yield(next_progress_text, files_done)
    yield("Done", -1)
  
  def convert_string_to_integer_md5(self, string):
    return int(hashlib.md5(string.encode('utf-8')).hexdigest(), 16)
  
  def get_new_rng(self):
    rng = Random()
    rng.seed(self.integer_seed)
    
    # Further change the RNG based on which RNG-changing options are enabled
    for i, option in enumerate(RNG_CHANGING_OPTIONS):
      value = self.options.get(option)
      for j in range(1, 100 + i):
        rng.getrandbits(value + 20 * i + j)
    
    return rng
  
  def reset_rng(self):
    self.rng = self.get_new_rng()
  
  def calculate_playthrough_progression_spheres(self):
    progression_spheres = []
    
    logic = Logic(self)
    previously_accessible_locations = []
    game_beatable = False
    while logic.unplaced_progress_items:
      progress_items_in_this_sphere = OrderedDict()
      
      accessible_locations = logic.get_accessible_remaining_locations()
      locations_in_this_sphere = [
        loc for loc in accessible_locations
        if loc not in previously_accessible_locations
      ]
      if not locations_in_this_sphere:
        raise Exception("Failed to calculate progression spheres")
      
      
      if not self.options.get("keylunacy"):
        # If the player gained access to any small keys, we need to give them the keys without counting that as a new sphere.
        newly_accessible_predetermined_item_locations = [
          loc for loc in locations_in_this_sphere
          if loc in self.logic.prerandomization_item_locations
        ]
        newly_accessible_small_key_locations = [
          loc for loc in newly_accessible_predetermined_item_locations
          if self.logic.prerandomization_item_locations[loc].endswith(" Small Key")
        ]
        if newly_accessible_small_key_locations:
          for small_key_location_name in newly_accessible_small_key_locations:
            item_name = self.logic.prerandomization_item_locations[small_key_location_name]
            assert item_name.endswith(" Small Key")
            
            logic.add_owned_item(item_name)
          
          previously_accessible_locations += newly_accessible_small_key_locations
          continue # Redo this loop iteration with the small key locations no longer being considered 'remaining'.
      
      
      # Hide duplicated progression items (e.g. Empty Bottles) when they are placed in non-progression locations to avoid confusion and inconsistency.
      locations_in_this_sphere = logic.filter_locations_for_progression(locations_in_this_sphere)
      
      for location_name in locations_in_this_sphere:
        item_name = self.logic.done_item_locations[location_name]
        if item_name in logic.all_progress_items:
          progress_items_in_this_sphere[location_name] = item_name
      
      if not game_beatable:
        game_beatable = logic.check_requirement_met("Can Reach and Defeat Ganondorf")
        if game_beatable:
          progress_items_in_this_sphere["Ganon's Tower - Rooftop"] = "Defeat Ganondorf"
      
      progression_spheres.append(progress_items_in_this_sphere)
      
      for location_name, item_name in progress_items_in_this_sphere.items():
        if item_name == "Defeat Ganondorf":
          continue
        logic.add_owned_item(item_name)
      for group_name, item_names in logic.progress_item_groups.items():
        entire_group_is_owned = all(item_name in logic.currently_owned_items for item_name in item_names)
        if entire_group_is_owned and group_name in logic.unplaced_progress_items:
          logic.unplaced_progress_items.remove(group_name)
      
      previously_accessible_locations = accessible_locations
    
    if not game_beatable:
      # If the game wasn't already beatable on a previous progression sphere but it is now we add one final one just for this.
      game_beatable = logic.check_requirement_met("Can Reach and Defeat Ganondorf")
      if game_beatable:
        final_progression_sphere = OrderedDict([
          ("Ganon's Tower - Rooftop", "Defeat Ganondorf"),
        ])
        progression_spheres.append(final_progression_sphere)
    
    return progression_spheres
  
  def get_log_header(self):
    header = ""
    
    header += "Wind Waker Randomizer Version %s\n" % VERSION
    
    if self.permalink:
      header += "Permalink: %s\n" % self.permalink
    
    if self.seed_hash:
      header += "Seed Hash: %s\n" % self.seed_hash

    header += "Seed: %s\n" % self.seed
    
    header += "Options selected:\n  "
    non_disabled_options = [
      name for name in self.options
      if self.options[name] not in [False, [], {}, OrderedDict()]
      and name != "randomized_gear" # Just takes up space
    ]
    option_strings = []
    for option_name in non_disabled_options:
      if isinstance(self.options[option_name], bool):
        option_strings.append(option_name)
      else:
        if option_name == "custom_colors":
          # Only show non-default colors.
          default_colors = customizer.get_default_colors(self)
          value = OrderedDict()
          for custom_color_name, custom_color_value in self.options[option_name].items():
            if custom_color_value != default_colors[custom_color_name]:
              value[custom_color_name] = custom_color_value
          if value == OrderedDict():
            # No colors changed from default, don't show it at all.
            continue
        else:
          value = self.options[option_name]
        option_strings.append("%s: %s" % (option_name, value))
    header += ", ".join(option_strings)
    header += "\n\n\n"
    
    return header
  
  def get_zones_and_max_location_name_len(self, locations):
    zones = OrderedDict()
    max_location_name_length = 0
    for location_name in locations:
      zone_name, specific_location_name = self.logic.split_location_name_by_zone(location_name)
      
      if zone_name not in zones:
        zones[zone_name] = []
      zones[zone_name].append((location_name, specific_location_name))
      
      if len(specific_location_name) > max_location_name_length:
        max_location_name_length = len(specific_location_name)
    
    return (zones, max_location_name_length)
  
  def write_non_spoiler_log(self):
    if self.no_logs:
      return
    
    log_str = self.get_log_header()
    
    progress_locations, nonprogress_locations = self.logic.get_progress_and_non_progress_locations()
    
    zones, max_location_name_length = self.get_zones_and_max_location_name_len(self.logic.done_item_locations)
    format_string = "    %s\n"
    
    # Write progress item locations.
    log_str += "### Locations that may or may not have progress items in them on this run:\n"
    for zone_name, locations_in_zone in zones.items():
      if not any(loc for (loc, _) in locations_in_zone if loc in progress_locations):
        # No progress locations for this zone.
        continue
      
      log_str += zone_name + ":\n"
      
      for (location_name, specific_location_name) in locations_in_zone:
        if location_name in progress_locations:
          item_name = self.logic.done_item_locations[location_name]
          log_str += format_string % specific_location_name
    
    log_str += "\n\n"
    
    
    # Write nonprogress item locations.
    log_str += "### Locations that cannot have progress items in them on this run:\n"
    for zone_name, locations_in_zone in zones.items():
      if not any(loc for (loc, _) in locations_in_zone if loc in nonprogress_locations):
        # No nonprogress locations for this zone.
        continue
      
      log_str += zone_name + ":\n"
      
      for (location_name, specific_location_name) in locations_in_zone:
        if location_name in nonprogress_locations:
          item_name = self.logic.done_item_locations[location_name]
          log_str += format_string % specific_location_name
    
    nonspoiler_log_output_path = os.path.join(self.randomized_output_folder, "WW Random %s - Non-Spoiler Log.txt" % self.seed)
    with open(nonspoiler_log_output_path, "w") as f:
      f.write(log_str)
  
  def write_spoiler_log(self):
    if self.no_logs:
      # We still calculate progression spheres even if we're not going to write them anywhere to catch more errors in testing.
      self.calculate_playthrough_progression_spheres()
      return
    
    spoiler_log = self.get_log_header()
    
    # Write progression spheres.
    spoiler_log += "Playthrough:\n"
    progression_spheres = self.calculate_playthrough_progression_spheres()
    all_progression_sphere_locations = [loc for locs in progression_spheres for loc in locs]
    zones, max_location_name_length = self.get_zones_and_max_location_name_len(all_progression_sphere_locations)
    format_string = "      %-" + str(max_location_name_length+1) + "s %s\n"
    for i, progression_sphere in enumerate(progression_spheres):
      spoiler_log += "%d:\n" % (i+1)
      
      for zone_name, locations_in_zone in zones.items():
        if not any(loc for (loc, _) in locations_in_zone if loc in progression_sphere):
          # No locations in this zone are used in this sphere.
          continue
        
        spoiler_log += "  %s:\n" % zone_name
        
        for (location_name, specific_location_name) in locations_in_zone:
          if location_name in progression_sphere:
            if location_name == "Ganon's Tower - Rooftop":
              item_name = "Defeat Ganondorf"
            else:
              item_name = self.logic.done_item_locations[location_name]
            spoiler_log += format_string % (specific_location_name + ":", item_name)
      
    spoiler_log += "\n\n\n"
    
    # Write item locations.
    spoiler_log += "All item locations:\n"
    zones, max_location_name_length = self.get_zones_and_max_location_name_len(self.logic.done_item_locations)
    format_string = "    %-" + str(max_location_name_length+1) + "s %s\n"
    for zone_name, locations_in_zone in zones.items():
      spoiler_log += zone_name + ":\n"
      
      for (location_name, specific_location_name) in locations_in_zone:
        item_name = self.logic.done_item_locations[location_name]
        spoiler_log += format_string % (specific_location_name + ":", item_name)
    
    spoiler_log += "\n\n\n"
    
    # Write starting island.
    spoiler_log += "Starting island: "
    spoiler_log += self.island_number_to_name[self.starting_island_index]
    spoiler_log += "\n"
    
    spoiler_log += "\n\n\n"
    
    # Write dungeon/secret cave entrances.
    spoiler_log += "Entrances:\n"
    for entrance_name, dungeon_or_cave_name in self.entrance_connections.items():
      spoiler_log += "  %-48s %s\n" % (entrance_name+":", dungeon_or_cave_name)
    
    spoiler_log += "\n\n\n"
    
    # Write treasure charts.
    spoiler_log += "Charts:\n"
    chart_name_to_island_number = {}
    for island_number in range(1, 49+1):
      chart_name = self.logic.macros["Chart for Island %d" % island_number][0]
      chart_name_to_island_number[chart_name] = island_number
    for chart_number in range(1, 49+1):
      if chart_number <= 8:
        chart_name = "Triforce Chart %d" % chart_number
      else:
        chart_name = "Treasure Chart %d" % (chart_number-8)
      island_number = chart_name_to_island_number[chart_name]
      island_name = self.island_number_to_name[island_number]
      spoiler_log += "  %-18s %s\n" % (chart_name+":", island_name)
    
    spoiler_log_output_path = os.path.join(self.randomized_output_folder, "WW Random %s - Spoiler Log.txt" % self.seed)
    with open(spoiler_log_output_path, "w") as f:
      f.write(spoiler_log)
  
  def write_error_log(self, error_message):
    if self.no_logs:
      return
    
    error_log_str = ""
    try:
      error_log_str += self.get_log_header()
    except Exception as e:
      print("Error getting log header for error log: " + str(e))
    
    error_log_str += error_message
    
    error_log_output_path = os.path.join(self.randomized_output_folder, "WW Random %s - Error Log.txt" % self.seed)
    with open(error_log_output_path, "w") as f:
      f.write(error_log_str)
  
  def disassemble_all_code(self):
    disassemble.disassemble_all_code(self)
