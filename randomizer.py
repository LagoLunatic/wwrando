
import os
from io import BytesIO
import shutil
from pathlib import Path
import re
from random import Random
from collections import OrderedDict
import copy
import hashlib

from fs_helpers import *
from wwlib.yaz0_decomp import Yaz0Decompressor
from wwlib.rarc import RARC
from wwlib.rel import REL
from wwlib.gcm import GCM
import tweaks
from logic.logic import Logic

VERSION = "0.4.1-BETA"

class TooFewProgressionLocationsError(Exception):
  pass

class Randomizer:
  def __init__(self, seed, clean_iso_path, randomized_output_folder, options):
    self.randomized_output_folder = randomized_output_folder
    self.options = options
    self.seed = seed
    
    self.integer_seed = int(hashlib.md5(self.seed.encode('utf-8')).hexdigest(), 16)
    self.rng = Random()
    self.rng.seed(self.integer_seed)
    
    self.verify_supported_version(clean_iso_path)
    
    self.gcm = GCM(clean_iso_path)
    self.gcm.read_entire_disc()
    
    self.read_text_file_lists()
    
    # Starting items. This list is read by the Logic when initializing your currently owned items list.
    self.starting_items = [
      "Wind Waker",
      "Wind's Requiem",
      "Ballad of Gales",
      "Progressive Sword",
      "Hero's Shield",
      "Boat's Sail",
    ]
    # Default dungeon entrances to be used if dungeon entrance randomizer is not on.
    self.dungeon_entrances = OrderedDict([
      ("Dungeon Entrance On Dragon Roost Island", "Dragon Roost Cavern"),
      ("Dungeon Entrance In Forest Haven Sector", "Forbidden Woods"),
      ("Dungeon Entrance In Tower of the Gods Sector", "Tower of the Gods"),
      ("Dungeon Entrance On Headstone Island", "Earth Temple"),
      ("Dungeon Entrance On Gale Isle", "Wind Temple"),
    ])
    # Default starting island (Outset) if the starting island randomizer is not on.
    self.starting_island_index = 44
    
    self.logic = Logic(self)
    
    num_progress_locations = self.logic.get_num_progression_locations()
    num_progress_items = self.logic.get_num_progression_items()
    if num_progress_locations < num_progress_items: 
      error_message = "Not enough progress locations to place all progress items.\n\n"
      error_message += "Total progress items: %d\n" % num_progress_items
      error_message += "Progress locations with current options: %d\n\n" % num_progress_locations
      error_message += "You need to check more of the progress location options in order to give the randomizer enough space to place all the items."
      raise TooFewProgressionLocationsError(error_message)
    
    self.arcs_by_path = {}
    self.raw_files_by_path = {}
    
    self.chart_list = self.get_arc("files/res/Msg/fmapres.arc").chart_lists[0]
    self.bmg = self.get_arc("files/res/Msg/bmgres.arc").bmg_files[0]
  
  def randomize(self):
    options_completed = 0
    yield("Modifying game code...", options_completed)
    
    self.apply_necessary_tweaks()
    
    if self.options.get("swift_sail"):
      tweaks.make_sail_behave_like_swift_sail(self)
    if self.options.get("instant_text_boxes"):
      tweaks.make_all_text_instant(self)
    if self.options.get("reveal_full_sea_chart"):
      tweaks.apply_patch(self, "reveal_sea_chart")
    
    options_completed += 1
    yield("Randomizing...", options_completed)
    
    if self.options.get("randomize_charts"):
      self.randomize_charts()
    
    if self.options.get("randomize_starting_island"):
      self.randomize_starting_island()
    
    if self.options.get("randomize_dungeon_entrances"):
      self.randomize_dungeon_entrances()
    
    self.randomize_items()
    
    self.write_changed_items()
    
    options_completed += 9
    yield("Saving randomized ISO...", options_completed)
    
    self.update_game_name_in_banner()
    
    self.save_randomized_iso()
    
    self.write_spoiler_log()
    self.write_non_spoiler_log()
  
  def apply_necessary_tweaks(self):
    tweaks.apply_patch(self, "custom_funcs")
    tweaks.apply_patch(self, "necessary_fixes")
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
    tweaks.add_cube_to_earth_temple_first_room(self)
    tweaks.add_more_magic_jars_to_dungeons(self)
  
  def verify_supported_version(self, clean_iso_path):
    if not os.path.isfile(clean_iso_path):
      raise Exception("Clean WW ISO does not exist: %s" % clean_iso_path)
    
    with open(clean_iso_path, "rb") as f:
      game_id = read_str(f, 0, 6)
    if game_id != "GZLE01":
      if game_id.startswith("GZL"):
        raise Exception("Invalid version of Wind Waker. Only the USA version is supported by this randomizer.")
      else:
        raise Exception("Invalid game given as the clean ISO. You must specify a Wind Waker ISO (USA version).")
  
  def read_text_file_lists(self):
    try:
      from sys import _MEIPASS
      data_path = os.path.join(_MEIPASS, "data")
      asm_path = os.path.join(_MEIPASS, "asm")
    except ImportError:
      data_path = "data"
      asm_path = "asm"
    
    # Get item names.
    self.item_names = {}
    self.item_name_to_id = {}
    with open(os.path.join(data_path, "item_names.txt"), "r") as f:
      matches = re.findall(r"^([0-9a-f]{2}) - (.+)$", f.read(), re.IGNORECASE | re.MULTILINE)
    for item_id, item_name in matches:
      if item_name:
        item_id = int(item_id, 16)
        self.item_names[item_id] = item_name
        if item_name in self.item_name_to_id:
          raise Exception("Duplicate item name: " + item_name)
        self.item_name_to_id[item_name] = item_id
    
    # Get function names for debug purposes.
    self.function_names = {}
    framework_map_contents = self.gcm.read_file_data("files/maps/framework.map")
    framework_map_contents.seek(0)
    framework_map_contents = framework_map_contents.read().decode("ascii")
    matches = re.findall(r"^  [0-9a-f]{8} [0-9a-f]{6} ([0-9a-f]{8})  \d (\S+)", framework_map_contents, re.IGNORECASE | re.MULTILINE)
    for match in matches:
      address, name = match
      address = int(address, 16)
      self.function_names[address] = name
    
    # Get stage and island names for debug purposes.
    self.stage_names = {}
    with open(os.path.join(data_path, "stage_names.txt"), "r") as f:
      while True:
        stage_folder = f.readline()
        if not stage_folder:
          break
        stage_name = f.readline()
        self.stage_names[stage_folder.strip()] = stage_name.strip()
    self.island_names = {}
    self.island_number_to_name = {}
    with open(os.path.join(data_path, "island_names.txt"), "r") as f:
      while True:
        room_arc_name = f.readline()
        if not room_arc_name:
          break
        island_name = f.readline().strip()
        self.island_names[room_arc_name.strip()] = island_name
        island_number = int(re.search(r"Room(\d+)", room_arc_name).group(1))
        self.island_number_to_name[island_number] = island_name
    
    self.item_ids_without_a_field_model = []
    with open(os.path.join(data_path, "items_without_field_models.txt"), "r") as f:
      matches = re.findall(r"^([0-9a-f]{2}) ", f.read(), re.IGNORECASE | re.MULTILINE)
    for item_id in matches:
      if item_name:
        item_id = int(item_id, 16)
        self.item_ids_without_a_field_model.append(item_id)
    
    self.arc_name_pointers = {}
    with open(os.path.join(data_path, "item_resource_arc_name_pointers.txt"), "r") as f:
      matches = re.findall(r"^([0-9a-f]{2}) ([0-9a-f]{8}) ", f.read(), re.IGNORECASE | re.MULTILINE)
    for item_id, arc_name_pointer in matches:
      item_id = int(item_id, 16)
      arc_name_pointer = int(arc_name_pointer, 16)
      self.arc_name_pointers[item_id] = arc_name_pointer
    
    self.custom_symbols = {}
    with open(os.path.join(asm_path, "custom_symbols.txt"), "r") as f:
      matches = re.findall(r"^([0-9a-f]{8}) (\S+)", f.read(), re.IGNORECASE | re.MULTILINE)
    for symbol_address, symbol_name in matches:
      self.custom_symbols[symbol_name] = int(symbol_address, 16)
  
  def get_arc(self, arc_path):
    arc_path = arc_path.replace("\\", "/")
    
    if arc_path in self.arcs_by_path:
      return self.arcs_by_path[arc_path]
    else:
      if arc_path in self.raw_files_by_path:
        raise Exception("File opened as both an arc and a raw file: " + file_path)
      
      data = self.gcm.read_file_data(arc_path)
      arc = RARC(data)
      self.arcs_by_path[arc_path] = arc
      return arc
  
  def get_raw_file(self, file_path):
    file_path = file_path.replace("\\", "/")
    
    if file_path in self.raw_files_by_path:
      return self.raw_files_by_path[file_path]
    else:
      if file_path in self.arcs_by_path:
        raise Exception("File opened as both an arc and a raw file: " + file_path)
      
      if file_path.startswith("files/rels/"):
        rel_name = os.path.basename(file_path)
        rels_arc = self.get_arc("files/RELS.arc")
        rel_file_entry = rels_arc.get_file_entry_by_name(rel_name)
      else:
        rel_file_entry = None
      
      if rel_file_entry:
        rel_file_entry.decompress_data_if_necessary()
        data = rel_file_entry.data
      else:
        data = self.gcm.read_file_data(file_path)
      
      if try_read_str(data, 0, 4) == "Yaz0":
        data = Yaz0Decompressor.decompress(data)
      
      self.raw_files_by_path[file_path] = data
      return data
  
  def update_game_name_in_banner(self):
    new_game_name = "Wind Waker Randomized %s" % self.seed
    
    banner_data = self.get_raw_file("files/opening.bnr")
    write_str(banner_data, 0x1860, new_game_name, 0x40)
  
  def save_randomized_iso(self):
    changed_files = {}
    for file_path, data in self.raw_files_by_path.items():
      if file_path.startswith("files/rels/"):
        rel_name = os.path.basename(file_path)
        rels_arc = self.get_arc("files/RELS.arc")
        rel_file_entry = rels_arc.get_file_entry_by_name(rel_name)
        if rel_file_entry:
          # Modify the RELS.arc entry for this rel.
          rel_file_entry.data = data
          continue
      
      changed_files[file_path] = data
    for arc_path, arc in self.arcs_by_path.items():
      arc.save_changes()
      changed_files[arc_path] = arc.data
    
    output_file_path = os.path.join(self.randomized_output_folder, "WW Random %s.iso" % self.seed)
    self.gcm.export_iso_with_changed_files(output_file_path, changed_files)

  def change_item(self, path, item_name):
    item_id = self.item_name_to_id[item_name]
    
    rel_match = re.search(r"^(rels/[^.]+\.rel)@([0-9A-F]{4})$", path)
    main_dol_match = re.search(r"^main.dol@([0-9A-F]{6})$", path)
    chest_match = re.search(r"^([^/]+/[^/]+\.arc)(?:/Layer([0-9a-b]))?/Chest([0-9A-F]{3})$", path)
    event_match = re.search(r"^([^/]+/[^/]+\.arc)/Event([0-9A-F]{3}):[^/]+/Actor([0-9A-F]{3})/Action([0-9A-F]{3})$", path)
    scob_match = re.search(r"^([^/]+/[^/]+\.arc)(?:/Layer([0-9a-b]))?/ScalableObject([0-9A-F]{3})$", path)
    actor_match = re.search(r"^([^/]+/[^/]+\.arc)(?:/Layer([0-9a-b]))?/Actor([0-9A-F]{3})$", path)
    
    if rel_match:
      rel_path = rel_match.group(1)
      offset = int(rel_match.group(2), 16)
      path = os.path.join("files", rel_path)
      self.change_hardcoded_item(path, offset, item_id)
    elif main_dol_match:
      offset = int(main_dol_match.group(1), 16)
      path = os.path.join("sys", "main.dol")
      self.change_hardcoded_item(path, offset, item_id)
    elif chest_match:
      arc_path = "files/res/Stage/" + chest_match.group(1)
      if chest_match.group(2):
        layer = int(chest_match.group(2), 16)
      else:
        layer = None
      chest_index = int(chest_match.group(3), 16)
      self.change_chest_item(arc_path, chest_index, layer, item_id)
    elif event_match:
      arc_path = "files/res/Stage/" + event_match.group(1)
      event_index = int(event_match.group(2), 16)
      actor_index = int(event_match.group(3), 16)
      action_index = int(event_match.group(4), 16)
      self.change_event_item(arc_path, event_index, actor_index, action_index, item_id)
    elif scob_match:
      arc_path = "files/res/Stage/" + scob_match.group(1)
      if scob_match.group(2):
        layer = int(scob_match.group(2), 16)
      else:
        layer = None
      scob_index = int(scob_match.group(3), 16)
      self.change_scob_item(arc_path, scob_index, layer, item_id)
    elif actor_match:
      arc_path = "files/res/Stage/" + actor_match.group(1)
      if actor_match.group(2):
        layer = int(actor_match.group(2), 16)
      else:
        layer = None
      actor_index = int(actor_match.group(3), 16)
      self.change_actor_item(arc_path, actor_index, layer, item_id)
    else:
      raise Exception("Invalid item path: " + path)

  def change_hardcoded_item(self, path, offset, item_id):
    data = self.get_raw_file(path)
    write_u8(data, offset, item_id)

  def change_chest_item(self, arc_path, chest_index, layer, item_id):
    dzx = self.get_arc(arc_path).dzx_files[0]
    chest = dzx.entries_by_type_and_layer("TRES", layer)[chest_index]
    chest.item_id = item_id
    chest.save_changes()

  def change_event_item(self, arc_path, event_index, actor_index, action_index, item_id):
    event_list = self.get_arc(arc_path).event_list_files[0]
    action = event_list.events[event_index].actors[actor_index].actions[action_index]
    
    if 0x6D <= item_id <= 0x72: # Song
      action.name = "059get_dance"
      event_list.set_property_value(action.property_index, item_id-0x6D)
    else:
      action.name = "011get_item"
      event_list.set_property_value(action.property_index, item_id)
    action.save_changes()

  def change_scob_item(self, arc_path, scob_index, layer, item_id):
    dzx = self.get_arc(arc_path).dzx_files[0]
    scob = dzx.entries_by_type_and_layer("SCOB", layer)[scob_index]
    if scob.is_salvage():
      scob.salvage_item_id = item_id
      scob.save_changes()
    elif scob.is_buried_pig_item():
      scob.buried_pig_item_id = item_id
      scob.save_changes()
    else:
      raise Exception("%s/SCOB%03X is an unknown type of SCOB" % (arc_path, scob_index))

  def change_actor_item(self, arc_path, actor_index, layer, item_id):
    dzx = self.get_arc(arc_path).dzx_files[0]
    actr = dzx.entries_by_type_and_layer("ACTR", layer)[actor_index]
    if actr.is_item():
      actr.item_id = item_id
    elif actr.is_boss_item():
      actr.boss_item_id = item_id
    else:
      raise Exception("%s/ACTR%03X is not an item" % (arc_path, actor_index))
    
    actr.save_changes()
  
  def randomize_items(self):
    print("Randomizing items...")
    
    self.randomize_progression_items()
    
    # Place unique non-progress items.
    while self.logic.unplaced_nonprogress_items:
      accessible_undone_locations = self.logic.get_accessible_remaining_locations()
      
      item_name = self.rng.choice(self.logic.unplaced_nonprogress_items)
      
      possible_locations = self.logic.filter_locations_valid_for_item(accessible_undone_locations, item_name)
      
      location_name = self.rng.choice(possible_locations)
      self.logic.set_location_to_item(location_name, item_name)
    
    accessible_undone_locations = self.logic.get_accessible_remaining_locations()
    inaccessible_locations = [loc for loc in self.logic.remaining_item_locations if loc not in accessible_undone_locations]
    if inaccessible_locations:
      print("Inaccessible locations:")
      for location_name in inaccessible_locations:
        print(location_name)
    
    # Fill remaining unused locations with consumables (Rupees, spoils, and bait).
    locations_to_place_consumables_at = self.logic.remaining_item_locations.copy()
    for location_name in locations_to_place_consumables_at:
      possible_items = self.logic.filter_items_valid_for_location(self.logic.unplaced_consumable_items, location_name)
      item_name = self.rng.choice(possible_items)
      self.logic.set_location_to_item(location_name, item_name)
  
  def randomize_progression_items(self):
    if True:
      # Don't randomize dungeon keys.
      for location_name, item_location in self.logic.item_locations.items():
        orig_item = item_location["Original item"]
        if orig_item in ["Small Key", "Big Key"]:
          self.logic.add_unrandomized_location(location_name)
    
    # Places one dungeon map and compass in each dungeon.
    for dungeon_name in self.logic.DUNGEON_NAMES.values():
      locations_for_dungeon = self.logic.locations_by_zone_name[dungeon_name]
      for item_name in ["Dungeon Map", "Compass"]:
        possible_locations = [
          loc for loc in locations_for_dungeon
          if loc in self.logic.remaining_item_locations
          and not loc in self.logic.unrandomized_item_locations
          and self.logic.item_locations[loc]["Type"] not in ["Tingle Statue Chest", "Sunken Treasure"]
        ]
        if dungeon_name == "Forsaken Fortress":
          # These are outdoors, which means their stage ID is not properly set to be Forsaken Fortress. This means the map/compass wouldn't work properly if placed here.
          possible_locations.remove("Forsaken Fortress - Phantom Ganon")
          possible_locations.remove("Forsaken Fortress - Helmaroc King Heart Container")
        location_name = self.rng.choice(possible_locations)
        self.logic.set_location_to_item(location_name, item_name)
    
    accessible_undone_locations = self.logic.get_accessible_remaining_locations(for_progression=True)
    if len(accessible_undone_locations) == 0:
      raise Exception("No progress locations are accessible at the very start of the game!")
    
    # Place progress items.
    previously_accessible_undone_locations = []
    while self.logic.unplaced_progress_items:
      accessible_undone_locations = self.logic.get_accessible_remaining_locations(for_progression=True)
      
      if not accessible_undone_locations:
        raise Exception("No locations left to place progress items!")
      
      # If the player gained access to any unrandomized locations, we need to give them those items.
      newly_accessible_unrandomized_locations = [
        loc for loc in accessible_undone_locations
        if loc in self.logic.unrandomized_item_locations
      ]
      if newly_accessible_unrandomized_locations:
        for unrandomized_location_name in newly_accessible_unrandomized_locations:
          unrandomized_item_name = self.logic.item_locations[unrandomized_location_name]["Original item"]
          self.logic.set_location_to_item(unrandomized_location_name, unrandomized_item_name)
        
        continue # Redo this loop iteration with the unrandomized locations no longer being considered 'remaining'.
      
      # Filter out items that are not valid in any of the locations we might use.
      possible_items = self.logic.filter_items_by_any_valid_location(self.logic.unplaced_progress_items, accessible_undone_locations)
      
      must_place_useful_item = False
      should_place_useful_item = False
      if len(accessible_undone_locations) == 1 and len(possible_items) > 1:
        # If we're on the last accessible location but not the last item we HAVE to place an item that unlocks new locations.
        must_place_useful_item = True
      else:
        # Otherwise we will still try to place a useful item, but failing will not result in an error.
        should_place_useful_item = True
      
      # If we wind up placing a useful item it can be a single item or a group.
      # But if we place an item that is not yet useful, we need to exclude groups.
      # This is so that a group doesn't wind up taking every single possible remaining location while not opening up new ones.
      possible_items_when_not_placing_useful = [name for name in possible_items if name not in self.logic.PROGRESS_ITEM_GROUPS]
      # Only exception is when there's exclusively groups left to place. Then we allow groups even if they're not useful.
      if len(possible_items_when_not_placing_useful) == 0 and len(possible_items) > 0:
        possible_items_when_not_placing_useful = possible_items
      
      if must_place_useful_item or should_place_useful_item:
        shuffled_list = possible_items.copy()
        self.rng.shuffle(shuffled_list)
        item_name = self.logic.get_first_useful_item(shuffled_list, for_progression=True)
        if item_name is None:
          if must_place_useful_item:
            raise Exception("No useful progress items to place!")
          else:
            item_name = self.rng.choice(possible_items_when_not_placing_useful)
      else:
        item_name = self.rng.choice(possible_items_when_not_placing_useful)
      
      if item_name in self.logic.PROGRESS_ITEM_GROUPS:
        # If we're placing an entire item group, we use different logic for deciding the location.
        # We do not weight towards newly accessible locations.
        # And we have to select multiple different locations, one for each item in the group.
        group_name = item_name
        possible_locations_for_group = accessible_undone_locations.copy()
        self.rng.shuffle(possible_locations_for_group)
        self.logic.set_multiple_locations_to_group(possible_locations_for_group, group_name)
      else:
        possible_locations = self.logic.filter_locations_valid_for_item(accessible_undone_locations, item_name)
        
        # We weight it so newly accessible locations are 10x more likely to be chosen.
        # This way there is still a good chance it will not choose a new location.
        possible_locations_with_weighting = []
        for location_name in possible_locations:
          if location_name not in previously_accessible_undone_locations:
            weight = 10
          else:
            weight = 1
          possible_locations_with_weighting += [location_name]*weight
        
        location_name = self.rng.choice(possible_locations_with_weighting)
        self.logic.set_location_to_item(location_name, item_name)
      
      previously_accessible_undone_locations = accessible_undone_locations
    
    # Make sure locations that shouldn't be randomized aren't, even if the above logic missed them for some reason.
    for location_name in self.logic.unrandomized_item_locations:
      if location_name in self.logic.remaining_item_locations:
        unrandomized_item_name = self.logic.item_locations[location_name]["Original item"]
        self.logic.set_location_to_item(location_name, unrandomized_item_name)
    
    game_beatable = self.logic.check_requirement_met("Can Reach and Defeat Ganondorf")
    if not game_beatable:
      raise Exception("Game is not beatable on this seed! This error shouldn't happen.")
  
  def write_changed_items(self):
    for location_name, item_name in self.logic.done_item_locations.items():
      paths = self.logic.item_locations[location_name]["Paths"]
      for path in paths:
        self.change_item(path, item_name)
  
  def randomize_charts(self):
    # Shuffles around which chart points to each sector.
    
    randomizable_charts = [chart for chart in self.chart_list.charts if chart.type in [0, 1, 2, 6]]
    
    original_charts = copy.deepcopy(randomizable_charts)
    # Sort the charts by their texture ID so we get the same results even if we randomize them multiple times.
    original_charts.sort(key=lambda chart: chart.texture_id)
    self.rng.shuffle(original_charts)
    
    for chart in randomizable_charts:
      chart_to_copy_from = original_charts.pop()
      
      chart.texture_id = chart_to_copy_from.texture_id
      chart.sector_x = chart_to_copy_from.sector_x
      chart.sector_y = chart_to_copy_from.sector_y
      
      for random_pos_index in range(4):
        possible_pos = chart.possible_random_positions[random_pos_index]
        possible_pos_to_copy_from = chart_to_copy_from.possible_random_positions[random_pos_index]
        
        possible_pos.chart_texture_x_offset = possible_pos_to_copy_from.chart_texture_x_offset
        possible_pos.chart_texture_y_offset = possible_pos_to_copy_from.chart_texture_y_offset
        possible_pos.salvage_x_pos = possible_pos_to_copy_from.salvage_x_pos
        possible_pos.salvage_y_pos = possible_pos_to_copy_from.salvage_y_pos
      
      chart.save_changes()
      
      # Then update the salvage object on the sea so it knows what chart corresponds to it now.
      dzx = self.get_arc("files/res/Stage/sea/Room%d.arc" % chart.island_number).dzx_files[0]
      for scob in dzx.entries_by_type("SCOB"):
        if scob.is_salvage() and scob.salvage_type == 0:
          scob.salvage_chart_index_plus_1 = chart.owned_chart_index_plus_1
          scob.save_changes()
  
  def randomize_starting_island(self):
    possible_starting_islands = list(range(1, 49+1))
    
    # Don't allow Forsaken Fortress to be the starting island.
    # It wouldn't really cause problems, but it would be weird because you normally need bombs to get in, and you would need to use Ballad of Gales to get out.
    possible_starting_islands.remove(1)
    
    starting_island_room_index = self.rng.choice(possible_starting_islands)
    tweaks.set_new_game_starting_room_index(self, starting_island_room_index)
    tweaks.change_ship_starting_island(self, starting_island_room_index)
    
    self.starting_island_index = starting_island_room_index
  
  DUNGEON_ENTRANCES = [
    # Stage name, room index, SCLS entry index, spawn ID when exiting, entrance name for macro
    ("Adanmae", 0, 2, 2, "Dungeon Entrance On Dragon Roost Island"),
    ("sea", 41, 6, 6, "Dungeon Entrance In Forest Haven Sector"),
    ("sea", 26, 0, 2, "Dungeon Entrance In Tower of the Gods Sector"),
    ("Edaichi", 0, 0, 1, "Dungeon Entrance On Headstone Island"),
    ("Ekaze", 0, 0, 1, "Dungeon Entrance On Gale Isle"),
  ]
  DUNGEON_EXITS = [
    # Stage name, room index, SCLS entry index, spawn ID when entering, dungeon name for macro
    ("M_NewD2", 0, 0, 0, "Dragon Roost Cavern"),
    ("kindan", 0, 0, 0, "Forbidden Woods"),
    ("Siren", 0, 1, 0, "Tower of the Gods"),
    ("M_Dai", 0, 0, 0, "Earth Temple"),
    ("kaze", 15, 0, 15, "Wind Temple"),
  ]
  
  def randomize_dungeon_entrances(self):
    # First we need to check how many locations the player can access at the start of the game (excluding dungeons since they're not randomized yet).
    # If the player can't access any locations outside of dungeons, we need to limit the possibilities for what we allow the first dungeon (on DRI) to be.
    # If that first dungeon is TotG, the player can't get any items because they need bombs.
    # If that first dungeon is ET or WT, the player can't get any items because they need the command melody (and even with that they would only be able to access one single location).
    # So in that case we limit the first dungeon to either be DRC or FW.
    self.logic.temporarily_make_dungeon_entrance_macros_impossible()
    accessible_undone_locations = self.logic.get_accessible_remaining_locations(for_progression=True)
    if len(accessible_undone_locations) == 0:
      should_limit_first_dungeon_possibilities = True
    else:
      should_limit_first_dungeon_possibilities = False
    
    remaining_exits = self.DUNGEON_EXITS.copy()
    for entrance_stage_name, entrance_room_index, entrance_scls_index, entrance_spawn_id, entrance_name in self.DUNGEON_ENTRANCES:
      if should_limit_first_dungeon_possibilities and entrance_name == "Dungeon Entrance On Dragon Roost Island":
        possible_remaining_exits = []
        for exit_tuple in remaining_exits:
          _, _, _, _, dungeon_name = exit_tuple
          if dungeon_name in ["Dragon Roost Cavern", "Forbidden Woods"]:
            possible_remaining_exits.append(exit_tuple)
      else:
        possible_remaining_exits = remaining_exits
      
      random_dungeon_exit = self.rng.choice(possible_remaining_exits)
      remaining_exits.remove(random_dungeon_exit)
      exit_stage_name, exit_room_index, exit_scls_index, exit_spawn_id, dungeon_name = random_dungeon_exit
      
      # Update the dungeon this entrance takes you into.
      entrance_dzx_path = "files/res/Stage/%s/Room%d.arc" % (entrance_stage_name, entrance_room_index)
      entrance_dzx = self.get_arc(entrance_dzx_path).dzx_files[0]
      entrance_scls = entrance_dzx.entries_by_type("SCLS")[entrance_scls_index]
      entrance_scls.dest_stage_name = exit_stage_name
      entrance_scls.room_index = exit_room_index
      entrance_scls.spawn_id = exit_spawn_id
      entrance_scls.save_changes()
      
      # Update the entrance you're put at when leaving the dungeon.
      exit_dzx_path = "files/res/Stage/%s/Room%d.arc" % (exit_stage_name, exit_room_index)
      exit_dzx = self.get_arc(exit_dzx_path).dzx_files[0]
      exit_scls = exit_dzx.entries_by_type("SCLS")[exit_scls_index]
      exit_scls.dest_stage_name = entrance_stage_name
      exit_scls.room_index = entrance_room_index
      exit_scls.spawn_id = entrance_spawn_id
      exit_scls.save_changes()
      
      self.dungeon_entrances[entrance_name] = dungeon_name
    
    self.logic.update_dungeon_entrance_macros()
  
  def calculate_playthrough_progression_spheres(self):
    progression_spheres = []
    
    logic = Logic(self)
    previously_accessible_locations = []
    while logic.unplaced_progress_items:
      progress_items_in_this_sphere = OrderedDict()
      
      accessible_locations = logic.get_accessible_remaining_locations()
      locations_in_this_sphere = [
        loc for loc in accessible_locations
        if loc not in previously_accessible_locations
      ]
      
      
      # If the player gained access to any unrandomized locations, we need to give them those items without counting that as a new sphere.
      newly_accessible_unrandomized_locations = [
        loc for loc in locations_in_this_sphere
        if loc in self.logic.unrandomized_item_locations
      ]
      if newly_accessible_unrandomized_locations:
        for unrandomized_location_name in newly_accessible_unrandomized_locations:
          unrandomized_item_name = self.logic.item_locations[unrandomized_location_name]["Original item"]
          if "Key" in unrandomized_item_name:
            dungeon_name, _ = logic.split_location_name_by_zone(unrandomized_location_name)
            logic.add_owned_key_for_dungeon(unrandomized_item_name, dungeon_name)
          else:
            raise Exception("Unrandomized item is not a key.")
        
        previously_accessible_locations += newly_accessible_unrandomized_locations
        continue # Redo this loop iteration with the unrandomized locations no longer being considered 'remaining'.
      
      
      for location_name in locations_in_this_sphere:
        item_name = self.logic.done_item_locations[location_name]
        if item_name in logic.all_progress_items:
          progress_items_in_this_sphere[location_name] = item_name
      
      progression_spheres.append(progress_items_in_this_sphere)
      
      for location_name, item_name in progress_items_in_this_sphere.items():
        logic.add_owned_item(item_name)
      for group_name, item_names in logic.PROGRESS_ITEM_GROUPS.items():
        entire_group_is_owned = all(item_name in logic.currently_owned_items for item_name in item_names)
        if entire_group_is_owned and group_name in logic.unplaced_progress_items:
          logic.unplaced_progress_items.remove(group_name)
      
      previously_accessible_locations = accessible_locations
    
    return progression_spheres
  
  def get_log_header(self):
    header = ""
    
    header += "Wind Waker Randomizer Version %s\n" % VERSION
    header += "Seed: %s\n" % self.seed
    
    header += "Options selected:\n  "
    true_options = [name for name in self.options if self.options[name]]
    header += ", ".join(true_options)
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
    
    # Write treasure charts.
    spoiler_log += "Charts:\n"
    for chart_number in range(1, 49+1):
      chart = self.chart_list.find_chart_by_chart_number(chart_number)
      island_name = self.island_number_to_name[chart.island_number]
      spoiler_log += "  %-18s %s\n" % (chart.item_name+":", island_name)
    
    spoiler_log_output_path = os.path.join(self.randomized_output_folder, "WW Random %s - Spoiler Log.txt" % self.seed)
    with open(spoiler_log_output_path, "w") as f:
      f.write(spoiler_log)

if __name__ == "__main__":
  rando = Randomizer(1, "../Wind Waker Files", "../Wind Waker Files Randomized", {
    "progression_charts_none": True,
    "swift_sail": True,
    "instant_text_boxes": True,
    "reveal_full_sea_chart": True,
  })
  rando.randomize()
