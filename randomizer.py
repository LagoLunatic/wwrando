
import os
from io import BytesIO
import shutil
from pathlib import Path
import re
import random
from collections import OrderedDict
import copy

from fs_helpers import *
from wwlib.yaz0_decomp import Yaz0Decompressor
from wwlib.rarc import RARC
from wwlib.rel import REL
from wwlib.gcm import GCM
import tweaks
from logic.logic import Logic

VERSION = "0.2-BETA"

class Randomizer:
  def __init__(self, seed, clean_iso_path, randomized_output_folder, options):
    self.randomized_output_folder = randomized_output_folder
    self.options = options
    self.seed = seed
    self.rng = random.Random()
    self.rng.seed(self.seed)
    
    self.verify_supported_version(clean_iso_path)
    
    self.gcm = GCM(clean_iso_path)
    self.gcm.read_entire_disc()
    
    self.read_text_file_lists()
    self.logic = Logic(self)
    
    self.logic.add_owned_item("Wind Waker")
    self.logic.add_owned_item("Wind's Requiem")
    self.logic.add_owned_item("Ballad of Gales")
    self.logic.add_owned_item("Progressive Sword")
    self.logic.add_owned_item("Hero's Shield")
    self.logic.add_owned_item("Boat's Sail")
    
    self.arcs_by_path = {}
    self.raw_files_by_path = {}
    
    self.chart_list = self.get_arc("files/res/Msg/fmapres.arc").chart_lists[0]
    self.bmg = self.get_arc("files/res/Msg/bmgres.arc").bmg_files[0]
  
  def randomize(self):
    self.apply_necessary_tweaks()
    
    if self.options.get("swift_sail"):
      tweaks.make_sail_behave_like_swift_sail(self)
    if self.options.get("instant_text_boxes"):
      tweaks.make_all_text_instant(self)
    if self.options.get("reveal_full_sea_chart"):
      tweaks.apply_patch(self, "reveal_sea_chart")
    
    if self.options.get("randomize_charts"):
      self.randomize_charts()
    
    if self.options.get("randomize_starting_island"):
      self.randomize_starting_island()
    
    self.randomize_items()
    
    self.write_changed_items()
    
    self.write_spoiler_log()
    
    self.save_randomized_iso()
  
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
      location_name = self.rng.choice(accessible_undone_locations)
      self.logic.set_location_to_item(location_name, item_name)
    
    accessible_undone_locations = self.logic.get_accessible_remaining_locations()
    inaccessible_locations = [loc for loc in self.logic.remaining_item_locations if loc not in accessible_undone_locations]
    if inaccessible_locations:
      print("Inaccessible locations:")
      for location_name in inaccessible_locations:
        print(location_name)
    
    # Fill remaining unused locations with consumables (Rupees and Spoils).
    locations_to_place_consumables_at = self.logic.remaining_item_locations.copy()
    for location_name in locations_to_place_consumables_at:
      item_name = self.rng.choice(self.logic.consumable_items)
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
          and self.logic.item_locations[loc]["Type"] != "Tingle Statue Chest"
        ]
        location_name = self.rng.choice(possible_locations)
        self.logic.set_location_to_item(location_name, item_name)
    
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
      
      must_place_useful_item = False
      should_place_useful_item = False
      
      if len(accessible_undone_locations) == 1 and len(self.logic.unplaced_progress_items) > 1:
        must_place_useful_item = True
      elif self.rng.random() < 0.5: # 50% chance to place an item that opens up new locations
        should_place_useful_item = True
      
      if must_place_useful_item or should_place_useful_item:
        shuffled_list = self.logic.unplaced_progress_items.copy()
        self.rng.shuffle(shuffled_list)
        item_name = self.logic.get_first_useful_item(shuffled_list)
        if item_name is None:
          if must_place_useful_item:
            raise Exception("No useful progress items to place!")
          else:
            item_name = self.rng.choice(self.logic.unplaced_progress_items)
      else:
        item_name = self.rng.choice(self.logic.unplaced_progress_items)
      
      # We weight it so newly accessible locations are 10x more likely to be chosen.
      # This way there is still a good chance it will not choose a new location.
      possible_locations_with_weighting = []
      newly_accessible_undone_locations = [
        loc for loc in accessible_undone_locations
        if loc not in previously_accessible_undone_locations
      ]
      for location_name in accessible_undone_locations:
        if location_name in newly_accessible_undone_locations:
          weight = 10
        else:
          weight = 1
        possible_locations_with_weighting += [location_name]*weight
      
      location_name = self.rng.choice(possible_locations_with_weighting)
      self.logic.set_location_to_item(location_name, item_name)
      
      previously_accessible_undone_locations = accessible_undone_locations
    
    # Make sure locations that shouldn't be randomized aren't, even if above logic missed them for some reason.
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
    starting_island_room_index = self.rng.randrange(1, 49+1)
    tweaks.set_new_game_starting_room_index(self, starting_island_room_index)
    tweaks.change_ship_starting_island(self, starting_island_room_index)
  
  def write_spoiler_log(self):
    spoiler_log = ""
    
    spoiler_log += "Wind Waker Randomizer Version %s\n" % VERSION
    
    spoiler_log += "Options selected:\n  "
    true_options = [name for name in self.options if self.options[name]]
    spoiler_log += ", ".join(true_options)
    spoiler_log += "\n\n\n"
    
    # Write item locations.
    zones = OrderedDict()
    max_location_name_length = 0
    for location_name in self.logic.done_item_locations:
      zone_name, specific_location_name = self.logic.split_location_name_by_zone(location_name)
      
      if zone_name not in zones:
        zones[zone_name] = []
      zones[zone_name].append((location_name, specific_location_name))
      
      if len(specific_location_name) > max_location_name_length:
        max_location_name_length = len(specific_location_name)
    
    format_string = "    %-" + str(max_location_name_length+1) + "s %s\n"
    
    for zone_name, locations_in_zone in zones.items():
      spoiler_log += zone_name + ":\n"
      
      for (location_name, specific_location_name) in locations_in_zone:
        item_name = self.logic.done_item_locations[location_name]
        spoiler_log += format_string % (specific_location_name + ":", item_name)
    
    spoiler_log += "\n\n"
    
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
