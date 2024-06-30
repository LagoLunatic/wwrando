
import os
import re
from random import Random
import hashlib
import zlib
import yaml
import sys
from typing import TypeVar, Callable
from io import BytesIO
import string

from gclib import fs_helpers as fs
from gclib.bfn import BFN
from gclib.bmg import BMG
from gclib.yaz0_yay0 import Yaz0
from gclib.rarc import RARC
from gclib.dol import DOL
from gclib.rel import REL, RELRelocation, RELRelocationType
from gclib.gcm import GCM
from gclib.jpc import JPC100
import tweaks
from asm import patcher
from logic.logic import Logic
from wwlib.charts import ChartList
from wwrando_paths import DATA_PATH, ASM_PATH, IS_RUNNING_FROM_SOURCE, SEEDGEN_PATH
import customizer
from wwlib import stage_searcher
from asm import disassemble
from asm import elf2rel

from options.wwrando_options import Options, SwordMode
from wwr_ui.inventory import REGULAR_ITEMS, PROGRESSIVE_ITEMS
from packedbits import PackedBitsReader, PackedBitsWriter
import base64
import struct
import typing
from enum import StrEnum

try:
  from keys.seed_key import SEED_KEY # type: ignore
except ImportError:
  SEED_KEY = ""

from randomizers.base_randomizer import BaseRandomizer
from randomizers.items import ItemRandomizer
from randomizers.charts import ChartRandomizer
from randomizers.starting_island import StartingIslandRandomizer
from randomizers.entrances import EntranceRandomizer 
# from randomizers import music # Unfinished and needs to be rewritten from scratch
from randomizers.enemies import EnemyRandomizer
from randomizers.palettes import PaletteRandomizer
from randomizers.boss_reqs import RequiredBossesRandomizer
from randomizers.hints import HintsRandomizer
from randomizers.pigs import PigsRandomizer
from randomizers.extra_starting_items import ExtraStartingItemsRandomizer

from version import VERSION, VERSION_WITHOUT_COMMIT

# The below are options that could be used to cheat in races.
# They do not naturally change algorithmic item distribution, but do change the availability of information on item distribution.
# To prevent this possibility, we change the RNG seed itself for each one of these options that is selected.
# This ensures that item distribution is different between people with the same seed but different hints, for example.
RNG_CHANGING_OPTIONS = [
  "fishmen_hints",
  "hoho_hints",
  "korl_hints",
  "num_path_hints",
  "num_barren_hints",
  "num_location_hints",
  "num_item_hints",
  "cryptic_hints",
  "prioritize_remote_hints",
  "do_not_generate_spoiler_log",
]

class TooFewProgressionLocationsError(Exception): pass
class InvalidCleanISOError(Exception): pass
class PermalinkWrongVersionError(Exception): pass
class PermalinkWrongCommitError(Exception): pass

T = TypeVar('T')

class WWRandomizer:
  CLEAN_WIND_WAKER_ISO_MD5 = 0xd8e4d45af2032a081a0f446384e9261b
  VALID_SEED_CHARACTERS = "-_'%%.%s%s" % (string.ascii_letters, string.digits)
  MAX_SEED_LENGTH = 42 # Limited by maximum length of game name in banner
  
  def __init__(self, seed, clean_iso_path, randomized_output_folder, options: Options, cmd_line_args=None):
    self.fully_initialized = False
    
    options.validate()
    
    self.randomized_output_folder = randomized_output_folder
    self.logs_output_folder = self.randomized_output_folder
    self.options = options
    self.seed = self.sanitize_seed(seed)
    self.permalink = self.encode_permalink(self.seed, self.options)
    self.seed_hash = self.get_seed_hash()
    
    if cmd_line_args is None:
      cmd_line_args = {}
    if cmd_line_args.dry:
      self.options.dry_run = True
    self.dry_run = self.options.dry_run
    self.disassemble = cmd_line_args.disassemble
    self.export_disc_to_folder = cmd_line_args.exportfolder
    self.no_logs = cmd_line_args.nologs
    self.bulk_test = cmd_line_args.bulk
    if self.bulk_test:
      self.dry_run = True
      self.logs_output_folder = os.path.join(self.logs_output_folder, "bulk")
    self.print_used_flags = cmd_line_args.printflags
    if cmd_line_args.noitemrando and IS_RUNNING_FROM_SOURCE:
      self.randomize_items = False
    else:
      self.randomize_items = True
    self.map_select = cmd_line_args.mapselect
    self.heap_display = cmd_line_args.heap
    
    self.test_room_args = None
    if cmd_line_args.test:
      self.test_room_args = cmd_line_args.test
    
    seed_string = self.seed
    if self.options.do_not_generate_spoiler_log:
      seed_string += SEED_KEY
    
    self.integer_seed = self.convert_string_to_integer_md5(seed_string)
    
    self.arcs_by_path: dict[str, RARC] = {}
    self.jpcs_by_path: dict[str, JPC100] = {}
    self.rels_by_path: dict[str, REL] = {}
    self.symbol_maps_by_path: dict[str, dict[int, str]] = {}
    self.raw_files_by_path: dict[str, BytesIO] = {}
    self.used_actor_ids = list(range(0x1F6))
    
    self.read_text_file_lists()
    
    if not self.dry_run:
      if not os.path.isfile(clean_iso_path):
        raise InvalidCleanISOError("Vanilla WW ISO does not exist: %s" % clean_iso_path)
      
      self.verify_supported_version(clean_iso_path)
      
      self.gcm = GCM(clean_iso_path)
      self.gcm.read_entire_disc()
      
      dol_data = self.gcm.read_file_data("sys/main.dol")
      self.dol = DOL()
      self.dol.read(dol_data)
      
      try:
        self.chart_list = self.get_arc("files/res/Msg/fmapres.arc").get_file("cmapdat.bin", ChartList)
      except (fs.InvalidOffsetError, AssertionError):
        # An invalid offset error when reading fmapres.arc seems to happen when the user has a corrupted clean ISO.
        # Alternatively, fmapres.arc's magic bytes not being RARC can also happen here, also caused by a corrupted clean ISO.
        # The reason for this is unknown, but when this happens check the ISO's MD5 and if it's wrong say so in an error message.
        self.verify_correct_clean_iso_md5(clean_iso_path)
        
        # But if the ISO's MD5 is correct just raise the normal offset error.
        raise
      
      self.bmg = self.get_arc("files/res/Msg/bmgres.arc").get_file("zel_00.bmg", BMG)
      self.bfn = self.get_arc("files/res/Msg/fontres.arc").get_file("rock_24_20_4i_usa.bfn", BFN)
      
      if self.disassemble:
        self.disassemble_all_code()
        sys.exit(0)
      if self.print_used_flags:
        stage_searcher.print_all_used_item_pickup_flags(self)
        stage_searcher.print_all_used_chest_open_flags(self)
        stage_searcher.print_all_event_flags_used_by_stb_cutscenes(self)
        stage_searcher.print_all_used_switches(self)
        sys.exit(0)
    
    # Starting items. This list is read by the Logic when initializing your currently owned items list.
    self.starting_items = [
      "Wind Waker",
      "Wind's Requiem",
      "Boat's Sail",
    ]
    self.starting_items += self.options.starting_gear
    
    if self.options.sword_mode == SwordMode.START_WITH_SWORD:
      self.starting_items.append("Progressive Sword")
    # Add starting Triforce Shards.
    num_starting_triforce_shards = self.options.num_starting_triforce_shards
    for i in range(num_starting_triforce_shards):
      self.starting_items.append("Triforce Shard %d" % (i+1))
    
    for i in range(self.options.starting_pohs):
      self.starting_items.append("Piece of Heart")
    
    for i in range(self.options.starting_hcs):
      self.starting_items.append("Heart Container")
    
    
    self.custom_model_name = self.options.custom_player_model
    self.using_custom_sail_texture = False
    
    self.logic = Logic(self)
    
    self.items = ItemRandomizer(self)
    self.charts = ChartRandomizer(self)
    self.starting_island = StartingIslandRandomizer(self)
    self.entrances = EntranceRandomizer(self)
    self.enemies = EnemyRandomizer(self)
    self.palettes = PaletteRandomizer(self)
    self.boss_reqs = RequiredBossesRandomizer(self)
    self.hints = HintsRandomizer(self)
    self.pigs = PigsRandomizer(self)
    self.extra_start_items = ExtraStartingItemsRandomizer(self)
    
    # This list's order is the order these randomizers will be called in.
    self.randomizers: list[BaseRandomizer] = [
      self.charts,
      # self.music,
      self.boss_reqs,
      self.entrances,
      self.starting_island,
      self.pigs,
      # Extra Starting Items must be randomized before items and enemies which depend on the
      # starting items list, but after bosses and entrances since it needs logic.
      self.extra_start_items,
      # Enemies must be randomized before items in order for the enemy logic to properly take into
      # account what items you do and don't start with.
      self.enemies,
      self.palettes,
      self.items,
      self.hints,
    ]
    
    self.logic.initialize_from_randomizer_state()
    
    num_progress_locations = self.logic.get_num_progression_locations()
    max_required_bosses_banned_locations = self.logic.get_max_required_bosses_banned_locations()
    self.all_randomized_progress_items = self.logic.unplaced_progress_items.copy()
    if num_progress_locations - max_required_bosses_banned_locations < len(self.all_randomized_progress_items):
      error_message = "Not enough progress locations to place all progress items.\n\n"
      error_message += "Total progress items: %d\n" % len(self.all_randomized_progress_items)
      error_message += "Progress locations with current options: %d\n" % num_progress_locations
      if max_required_bosses_banned_locations > 0:
        error_message += "Maximum Required Bosses Mode banned locations: %d\n" % max_required_bosses_banned_locations
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
    
    self.fully_initialized = True
  
  def get_max_progress_length(self) -> int:
    max_progress_val = 0
    
    if not self.dry_run:
      max_progress_val += 1800 # Applying pre-randomization tweaks.
  
    for randomizer in self.randomizers:
      if randomizer.is_enabled():
        max_progress_val += randomizer.progress_randomize_duration_weight
        if not self.dry_run:
          max_progress_val += randomizer.progress_save_duration_weight
    
    if not self.dry_run:
      max_progress_val += 15 # Applying post-randomization tweaks.
      max_progress_val += 2000 # Saving the ISO.
    
    return max_progress_val
  
  def randomize_all(self):
    for _ in self.randomize(): pass
  
  def randomize(self):
    progress_completed = 0
    yield("Modifying game code...", progress_completed)
    
    # import time
    # start = time.perf_counter_ns()
    
    customizer.decide_on_link_model(self)
    
    if not self.dry_run:
      self.apply_necessary_tweaks()
      
      if self.options.swift_sail:
        tweaks.make_sail_behave_like_swift_sail(self)
      if self.options.reveal_full_sea_chart:
        patcher.apply_patch(self, "reveal_sea_chart")
      if self.options.add_shortcut_warps_between_dungeons:
        tweaks.add_inter_dungeon_warp_pots(self)
      if self.options.invert_camera_x_axis:
        patcher.apply_patch(self, "invert_camera_x_axis")
      if self.options.invert_sea_compass_x_axis:
        patcher.apply_patch(self, "invert_sea_compass_x_axis")
      tweaks.update_skip_rematch_bosses_game_variable(self)
      tweaks.update_sword_mode_game_variable(self)
      if self.options.sword_mode == SwordMode.SWORDLESS:
        patcher.apply_patch(self, "swordless")
        tweaks.update_text_for_swordless(self)
      tweaks.update_starting_gear(self, self.options.starting_gear)
      if self.options.chest_type_matches_contents:
        tweaks.replace_dark_wood_chest_texture(self)
      if self.options.remove_title_and_ending_videos:
        tweaks.remove_title_and_ending_videos(self)
      if self.options.remove_music:
        patcher.apply_patch(self, "remove_music")
      if self.options.hero_mode:
        tweaks.enable_hero_mode(self)
      if self.options.switch_targeting_mode:
        tweaks.set_default_targeting_mode_to_switch(self)
      
      if self.map_select:
        patcher.apply_patch(self, "map_select")
      if IS_RUNNING_FROM_SOURCE or "BETA" in VERSION_WITHOUT_COMMIT:
        tweaks.enable_developer_mode(self)
      if self.heap_display:
        tweaks.enable_heap_display(self)
      
      if self.test_room_args is not None:
        tweaks.test_room(self)
      
      progress_completed += 1800
    
    # print(f"{(time.perf_counter_ns()-start)//1_000_000:6d}: Pre-randomization tweaks")
    
    yield("Randomizing...", progress_completed)
    for randomizer in self.randomizers:
      if randomizer.is_enabled():
        yield(randomizer.progress_randomize_text, progress_completed)
        # start = time.perf_counter_ns()
        randomizer.randomize()
        # print(f"{(time.perf_counter_ns()-start)//1_000_000:6d}: {randomizer.__class__.__name__}.randomize")
        progress_completed += randomizer.progress_randomize_duration_weight
    
    yield("Applying changes...", progress_completed)
    if not self.dry_run:
      for randomizer in self.randomizers:
        if randomizer.is_enabled():
          yield(randomizer.progress_save_text, progress_completed)
          # start = time.perf_counter_ns()
          randomizer.save()
          # print(f"{(time.perf_counter_ns()-start)//1_000_000:6d}: {randomizer.__class__.__name__}.save")
          progress_completed += randomizer.progress_save_duration_weight
    
    # start = time.perf_counter_ns()
    if not self.dry_run:
      self.apply_necessary_post_randomization_tweaks()
      if self.options.instant_text_boxes:
        tweaks.make_all_text_instant(self)
      progress_completed += 15
    # print(f"{(time.perf_counter_ns()-start)//1_000_000:6d}: Post-randomization tweaks")
    
    # start = time.perf_counter_ns()
    yield("Saving randomized ISO...", progress_completed)
    if not self.dry_run:
      for next_progress_text, files_done in self.save_randomized_iso():
        percentage_done = files_done/len(self.gcm.files_by_path)
        yield("Saving randomized ISO...", progress_completed+int(percentage_done*9))
      progress_completed += 2000
    # print(f"{(time.perf_counter_ns()-start)//1_000_000:6d}: Saving ISO")
    
    yield("Writing logs...", progress_completed)
    if not self.options.do_not_generate_spoiler_log:
      self.write_spoiler_log()
    self.write_non_spoiler_log()
  
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
    if self.seed_hash is not None:
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
    tweaks.add_spawns_outside_boss_doors(self)
    tweaks.remove_minor_panning_cutscenes(self)
    tweaks.fix_message_closing_sound_on_quest_status_screen(self)
    tweaks.fix_stone_head_bugs(self)
    tweaks.show_number_of_tingle_statues_on_quest_status_screen(self)
    patcher.apply_patch(self, "flexible_enemies")
    tweaks.add_shortcut_warps_into_dungeons(self)
    tweaks.fix_needle_rock_island_salvage_flags(self)
    tweaks.allow_nonlinear_servants_of_the_towers(self)
    tweaks.fix_helmaroc_king_table_softlock(self)
    tweaks.make_dungeon_joy_pendant_locations_flexible(self)
    tweaks.prevent_fairy_island_softlocks(self)
    tweaks.give_fairy_fountains_distinct_colors(self)
    
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
    tweaks.prevent_fire_mountain_lava_softlock(self)
  
  @classmethod
  def sanitize_seed(cls, seed):
    seed = str(seed)
    seed = seed.strip()
    seed = "".join(char for char in seed if char in cls.VALID_SEED_CHARACTERS)
    seed = seed[:cls.MAX_SEED_LENGTH]
    return seed
  
  @classmethod
  def encode_permalink(cls, seed: str, options: Options):
    seed = cls.sanitize_seed(seed)
    
    permalink = b""
    permalink += VERSION.encode("ascii")
    permalink += b"\0"
    permalink += seed.encode("ascii")
    permalink += b"\0"
    
    bitswriter = PackedBitsWriter()
    for option in Options.all:
      if not option.permalink:
        continue
      
      value = options[option.name]
      
      if option.name == "randomize_enemy_palettes" and not options.randomize_enemies:
        # Enemy palette randomizer doesn't need to be in the permalink when enemy rando is off.
        # So just put a 0 bit as a placeholder.
        value = False
      
      if issubclass(option.type, bool):
        bitswriter.write(int(value), 1)
      elif issubclass(option.type, StrEnum):
        enum_values = [val for val in option.type]
        index_of_value = enum_values.index(value)
        maximum_index = len(enum_values) - 1
        max_bit_length = maximum_index.bit_length()
        assert 0 <= index_of_value <= maximum_index < (1 << max_bit_length)
        bitswriter.write(index_of_value, max_bit_length)
      elif issubclass(option.type, int):
        assert option.minimum is not None
        assert option.maximum is not None
        max_bit_length = (option.maximum - option.minimum).bit_length()
        adjusted_value = value - option.minimum
        assert 0 <= adjusted_value < (1 << max_bit_length)
        bitswriter.write(adjusted_value, max_bit_length)
      elif option.name == "starting_gear":
        assert issubclass(typing.get_origin(option.type) or option.type, list)
        for item_name in REGULAR_ITEMS:
          bit = item_name in value
          bitswriter.write(bit, 1)
        unique_progressive_items = list(set(PROGRESSIVE_ITEMS))
        unique_progressive_items.sort()
        for item_name in unique_progressive_items:
          bitswriter.write(value.count(item_name), 2)
      elif option.name == "randomized_gear":
        # Handled above.
        continue
      elif option.name == "excluded_locations":
        assert issubclass(typing.get_origin(option.type) or option.type, list)
        for location_name in Logic.load_and_parse_item_locations():
          bit = location_name in value
          bitswriter.write(bit, 1)
      elif option.name == "progression_locations":
        # Handled above.
        continue
      else:
        raise Exception(f"Option {option.name} of type {option.type} is not currently supported by the permalink system.")
    
    bitswriter.flush()
    
    for byte in bitswriter.bytes:
      permalink += struct.pack(">B", byte)
    base64_encoded_permalink = base64.b64encode(zlib.compress(permalink)).decode("ascii")
    return base64_encoded_permalink
  
  @classmethod
  def decode_permalink(cls, base64_encoded_permalink: str, options: Options = None, allow_different_commit=False):
    base64_encoded_permalink = base64_encoded_permalink.strip()
    if not base64_encoded_permalink:
      raise Exception(f"Permalink is blank.")
    
    permalink = zlib.decompress(base64.b64decode(base64_encoded_permalink))
    given_version_num, seed, options_bytes = permalink.split(b"\0", 2)
    given_version_num = given_version_num.decode("ascii")
    seed = seed.decode("ascii")
    if given_version_num != VERSION:
      if IS_RUNNING_FROM_SOURCE and VERSION.split("_")[0] == given_version_num.split("_")[0]:
        if not allow_different_commit:
          message = "The given permalink is for version %s of the randomizer, while you are currently using version %s." % (given_version_num, VERSION)
          raise PermalinkWrongCommitError(message)
      else:
        message = "The given permalink is for version %s of the randomizer, it cannot be used with the version you are currently using (%s)." % (given_version_num, VERSION)
        raise PermalinkWrongVersionError(message)
    
    if options is None:
      options = Options()
    
    option_bytes = struct.unpack(">" + "B"*len(options_bytes), options_bytes)
    
    prev_randomize_enemy_palettes_value = options.randomize_enemy_palettes
    
    bitsreader = PackedBitsReader(option_bytes)
    for option in Options.all:
      if not option.permalink:
        continue
      
      if issubclass(option.type, bool):
        boolean_value = bool(bitsreader.read(1))
        options[option.name] = boolean_value
      elif issubclass(option.type, StrEnum):
        enum_values = [val for val in option.type]
        maximum_index = len(enum_values) - 1
        max_bit_length = maximum_index.bit_length()
        index_of_value = bitsreader.read(max_bit_length)
        assert 0 <= index_of_value <= maximum_index < (1 << max_bit_length)
        enum_value = enum_values[index_of_value]
        options[option.name] = enum_value
      elif issubclass(option.type, int):
        assert option.minimum is not None
        assert option.maximum is not None
        max_bit_length = (option.maximum - option.minimum).bit_length()
        adjusted_value = bitsreader.read(max_bit_length)
        value = adjusted_value + option.minimum
        if value < option.minimum or value > option.maximum:
          value = option.default
        options[option.name] = value
      elif option.name == "starting_gear":
        # Reset model with only the regular items
        assert issubclass(typing.get_origin(option.type) or option.type, list)
        starting_list = []
        randomized_list = []
        for item_name in REGULAR_ITEMS:
          starting = bitsreader.read(1)
          if starting == 1:
            starting_list.append(item_name)
          else:
            randomized_list.append(item_name)
        # Progressive items are all after regular items
        unique_progressive_items = list(set(PROGRESSIVE_ITEMS))
        unique_progressive_items.sort()
        for item_name in unique_progressive_items:
          amount = bitsreader.read(2)
          randamount = PROGRESSIVE_ITEMS.count(item_name) - amount
          for i in range(amount):
            starting_list.append(item_name)
          for i in range(randamount):
            randomized_list.append(item_name)
        options.starting_gear = sorted(starting_list)
        options.randomized_gear = sorted(randomized_list)
      elif option.name == "randomized_gear":
        # Handled above.
        continue
      elif option.name == "excluded_locations":
        assert issubclass(typing.get_origin(option.type) or option.type, list)
        excluded_list = []
        progression_list = []
        for location_name in Logic.load_and_parse_item_locations():
          excluded = bitsreader.read(1)
          if excluded == 1:
            excluded_list.append(location_name)
          else:
            progression_list.append(location_name)
        options.excluded_locations = sorted(excluded_list)
      elif option.name == "progression_locations":
        # Use default for now. This option will be updated later.
        options.progression_locations = option.default_factory()
      else:
        raise Exception(f"Option {option.name} of type {option.type} is not currently supported by the permalink system.")
    
    if not options.randomize_enemies:
      # If a permalink with enemy rando off was pasted, we don't want to change enemy palette rando to match the permalink.
      # So revert it to the value from before reading the permalink.
      options.randomize_enemy_palettes = prev_randomize_enemy_palettes_value
    
    return seed, options
  
  def verify_supported_version(self, clean_iso_path):
    with open(clean_iso_path, "rb") as f:
      magic = fs.try_read_str(f, 0, 4)
      game_id = fs.try_read_str(f, 0, 6)
    if magic == "CISO":
      raise InvalidCleanISOError("This ISO is in CISO format. The randomizer only supports ISOs in GCM format.")
    if game_id != "GZLE01":
      if game_id and game_id.startswith("GZL"):
        raise InvalidCleanISOError("Invalid version of Wind Waker. Only the North American version is supported by this randomizer.")
      else:
        raise InvalidCleanISOError("Invalid game given as the vanilla ISO. You must specify a Wind Waker ISO (North American version).")
  
  def verify_correct_clean_iso_md5(self, clean_iso_path):
    md5 = hashlib.md5()
    
    with open(clean_iso_path, "rb") as f:
      while True:
        chunk = f.read(1024*1024)
        if not chunk:
          break
        md5.update(chunk)
    
    integer_md5 = int(md5.hexdigest(), 16)
    if integer_md5 != self.CLEAN_WIND_WAKER_ISO_MD5:
      raise InvalidCleanISOError(
        "Invalid vanilla Wind Waker ISO. Your ISO may be corrupted.\n\n"
        f"Correct ISO MD5 hash: {self.CLEAN_WIND_WAKER_ISO_MD5:x}\nYour ISO's MD5 hash: {integer_md5:x}"
      )
  
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
  
  def register_renamed_item(self, item_id, item_name):
    self.item_name_to_id[item_name] = item_id
    self.item_names[item_id] = item_name
  
  def get_arc(self, arc_path):
    arc_path = arc_path.replace("\\", "/")
    
    if arc_path in self.arcs_by_path:
      return self.arcs_by_path[arc_path]
    else:
      data = self.gcm.read_file_data(arc_path)
      arc = RARC(data)
      arc.read()
      self.arcs_by_path[arc_path] = arc
      return arc
  
  def get_jpc(self, jpc_path):
    jpc_path = jpc_path.replace("\\", "/")
    
    if jpc_path in self.jpcs_by_path:
      return self.jpcs_by_path[jpc_path]
    else:
      data = self.gcm.read_file_data(jpc_path)
      jpc = JPC100(data)
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
      map_text = fs.read_all_bytes(data).decode("ascii")
      
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
    
    arc = RARC(new_data)
    arc.read()
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
    new_actor_id = fs.read_u16(section_data_actor_profile, offset_of_actor_profile+8)
    
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
    fs.write_u32(list_data, new_actor_id*4, 0)
    # For some reason, there's an extra four 0x00 bytes after the last entry in the list, so we put that there just to be safe.
    fs.write_u32(list_data, new_actor_id*4+4, 0)
    
    rel_relocation.section_num_to_relocate_against = section_index_of_actor_profile
    rel_relocation.symbol_address = offset_of_actor_profile
    
    if new_rel.id in profile_list.relocation_entries_for_module:
      raise Exception("Cannot add a new REL with a unique ID that is already present in the profile list:\nREL ID: %03X\nNew REL path: %s" % (new_rel.id, rel_path))
    if new_rel.id not in new_rel.relocation_entries_for_module:
      raise Exception("Custom REL does not contain any relocations against itself! The REL's module ID is probably invalid.\nREL ID: %03X\nNew REL path: %s" % (new_rel.id, rel_path))
    
    profile_list.relocation_entries_for_module[new_rel.id] = [rel_relocation]
    
    # Then add the REL to the game's filesystem.
    self.gcm.add_new_file(rel_path)
    self.rels_by_path[rel_path] = new_rel
    
    # Don't allow this actor ID to be used again by any more custom RELs we add.
    self.used_actor_ids.append(new_actor_id)
  
  def replace_rel_from_elf(self, linked_elf_path, rel_path, actor_profile_name):
    orig_rel = self.get_rel(rel_path)
    rel_id = orig_rel.id
    main_symbols = self.get_symbol_map("files/maps/framework.map")
    new_rel, profile_section_index, profile_address = elf2rel.convert_elf_to_rel(linked_elf_path, rel_id, main_symbols, actor_profile_name)
    
    self.rels_by_path[rel_path] = new_rel
    
    # If this REL is in RELS.arc, we also need to update the file entry to know that it's associated with a different REL now.
    rel_name = os.path.basename(rel_path)
    rels_arc = self.get_arc("files/RELS.arc")
    rel_file_entry = rels_arc.get_file_entry(rel_name)
    if rel_file_entry:
      rel_file_entry.data = new_rel.data
    
    # We need to update the pointer to the REL's profile in the profile list.
    profile_list = self.get_rel("files/rels/f_pc_profile_lst.rel")
    if rel_id not in profile_list.relocation_entries_for_module:
      raise Exception("Tried to replace a REL that was not already in the profile list.")
    
    profile_relocation = profile_list.relocation_entries_for_module[new_rel.id][0]
    profile_relocation.section_num_to_relocate_against = profile_section_index
    profile_relocation.symbol_address = profile_address
    
    profile_list.save_changes(preserve_section_data_offsets=True)
  
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
      jpc.save()
      self.gcm.changed_files[jpc_path] = jpc.data
    
    if self.export_disc_to_folder:
      output_folder_path = os.path.join(self.randomized_output_folder, "WW Random %s" % self.seed)
      yield from self.gcm.export_disc_to_folder_with_changed_files(output_folder_path)
    else:
      output_file_path = os.path.join(self.randomized_output_folder, "WW Random %s.iso" % self.seed)
      yield from self.gcm.export_disc_to_iso_with_changed_files(output_file_path)
  
  def convert_string_to_integer_md5(self, string):
    return int(hashlib.md5(string.encode('utf-8')).hexdigest(), 16)
  
  def get_new_rng(self):
    rng = Random()
    rng.seed(self.integer_seed)
    
    # Further change the RNG based on which RNG-changing options are enabled
    for i, option in enumerate(RNG_CHANGING_OPTIONS):
      value = self.options[option]
      for j in range(1, 100 + i):
        rng.getrandbits(value + 20 * i + j)
    
    return rng
  
  def weighted_choice(self, rng: Random, seq: list[T], weight_conditions: list[tuple[int, Callable[[T], bool]]]) -> T:
    element_weights = []
    
    for element in seq:
      weight_for_element = 1
      
      for weight, condition_callback in weight_conditions:
        if condition_callback(element):
          weight_for_element *= weight
      
      element_weights.append(weight_for_element)
    
    return rng.sample(seq, 1, counts=element_weights)[0]
  
  def get_seed_hash(self):
    # Generate some text that will be shown on the name entry screen which has two random character names that vary based on the permalink (so the seed and settings both change it).
    # This is so two players intending to play the same seed can verify if they really are on the same seed or not.

    if not self.permalink:
      return None

    if not self.options.do_not_generate_spoiler_log:
      integer_seed = self.convert_string_to_integer_md5(self.permalink)
    else:
      # When no spoiler log is generated, the seed key also affects randomization, not just the data in the permalink.
      integer_seed = self.convert_string_to_integer_md5(self.permalink + SEED_KEY)
    temp_rng = Random()
    temp_rng.seed(integer_seed)

    with open(os.path.join(SEEDGEN_PATH, "names.txt")) as f:
      all_names = f.read().splitlines()
    valid_names = [name for name in all_names if len(name) <= 5]

    name_1, name_2 = temp_rng.sample(valid_names, 2)
    name_1 = tweaks.upper_first_letter(name_1)
    name_2 = tweaks.upper_first_letter(name_2)
    return name_1 + " " + name_2

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
      option.name for option in Options.all
      if self.options[option.name] not in [False, [], {}]
      and option.name not in ["randomized_gear", "progression_locations"] # Just takes up space
    ]
    option_strings = []
    for option_name in non_disabled_options:
      if isinstance(self.options[option_name], bool):
        option_strings.append(option_name)
      else:
        if option_name == "custom_colors":
          # Only show non-default colors.
          default_colors = customizer.get_default_colors(self)
          value = {}
          for custom_color_name, custom_color_value in self.options[option_name].items():
            if custom_color_value != default_colors[custom_color_name]:
              value[custom_color_name] = custom_color_value
          if value == {}:
            # No colors changed from default, don't show it at all.
            continue
        else:
          value = self.options[option_name]
        option_strings.append("%s: %s" % (option_name, value))
    header += ", ".join(option_strings)
    header += "\n\n\n"
    
    return header
  
  def write_non_spoiler_log(self):
    if self.no_logs:
      return
    
    log_str = self.get_log_header()
    
    log_str += self.items.write_to_non_spoiler_log()
    
    os.makedirs(self.logs_output_folder, exist_ok=True)
    nonspoiler_log_output_path = os.path.join(self.logs_output_folder, "WW Random %s - Non-Spoiler Log.txt" % self.seed)
    with open(nonspoiler_log_output_path, "w") as f:
      f.write(log_str)
  
  def write_spoiler_log(self):
    if self.no_logs:
      if self.randomize_items:
        # We still calculate progression spheres even if we're not going to write them anywhere to catch more errors in testing.
        self.items.calculate_playthrough_progression_spheres()
      return
    
    spoiler_log = self.get_log_header()

    if self.extra_start_items.is_enabled():
      spoiler_log += self.extra_start_items.write_to_spoiler_log()
    
    spoiler_log += self.boss_reqs.write_to_spoiler_log()
    
    if self.randomize_items:
      spoiler_log += self.items.write_to_spoiler_log()
    
    spoiler_log += self.starting_island.write_to_spoiler_log()
    
    spoiler_log += self.entrances.write_to_spoiler_log()
    
    spoiler_log += self.charts.write_to_spoiler_log()
    
    if self.randomize_items:
      spoiler_log += self.hints.write_to_spoiler_log()
    
    os.makedirs(self.logs_output_folder, exist_ok=True)
    spoiler_log_output_path = os.path.join(self.logs_output_folder, "WW Random %s - Spoiler Log.txt" % self.seed)
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
    
    os.makedirs(self.logs_output_folder, exist_ok=True)
    error_log_output_path = os.path.join(self.logs_output_folder, "WW Random %s - Error Log.txt" % self.seed)
    with open(error_log_output_path, "w") as f:
      f.write(error_log_str)
  
  def disassemble_all_code(self):
    disassemble.disassemble_all_code(self)
