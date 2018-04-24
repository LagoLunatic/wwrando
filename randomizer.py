
import os
from io import BytesIO
import shutil
from pathlib import Path
import re
import random
from collections import OrderedDict
import copy

from fs_helpers import *
from yaz0_decomp import Yaz0Decompressor
from rarc import RARC
from rel import REL
import tweaks
from logic.logic import Logic

class Randomizer:
  def __init__(self, seed):
    clean_base_dir = "../Wind Waker Files"
    self.randomized_base_dir = "../Wind Waker Files Randomized"
    self.seed = seed
    random.seed(self.seed)
    
    self.stage_dir = os.path.join(self.randomized_base_dir, "files", "res", "Stage")
    self.rels_dir = os.path.join(self.randomized_base_dir, "files", "rels")
    
    self.copy_and_extract_files(clean_base_dir)
    
    self.read_text_file_lists()
    self.logic = Logic(self)
    
    self.logic.add_owned_item("Wind Waker")
    self.logic.add_owned_item("Wind's Requiem")
    self.logic.add_owned_item("Ballad of Gales")
    self.logic.add_owned_item("Hero's Sword")
    self.logic.add_owned_item("Hero's Shield")
    self.logic.add_owned_item("Boat's Sail")
    
    arc_paths = Path(self.stage_dir).glob("**/*.arc")
    self.arc_paths = [str(arc_path) for arc_path in arc_paths]
    rel_paths = Path(self.rels_dir).glob("**/*.rel")
    self.rel_paths = [str(rel_path) for rel_path in rel_paths]
    
    #self.decompress_files()
    
    self.arcs_by_path = {}
    self.raw_files_by_path = {}
    
    self.chart_list = self.get_arc("files/res/Msg/fmapres.arc").chart_lists[0]
  
  def randomize(self):
    self.apply_necessary_tweaks()
    
    tweaks.make_all_text_instant(self)
    tweaks.start_with_sea_chart_fully_revealed(self)
    
    self.randomize_charts()
    
    self.randomize_items()
    
    self.write_changed_items()
    
    self.write_spoiler_log()
    
    self.save_changed_files()
  
  def apply_necessary_tweaks(self):
    tweaks.modify_new_game_start_code(self)
    tweaks.remove_story_railroading(self)
    tweaks.skip_wakeup_intro_and_start_at_dock(self)
    tweaks.start_ship_at_outset(self)
    tweaks.make_fairy_upgrades_unconditional(self)
    tweaks.make_fishmen_active_before_gohma(self)
    tweaks.fix_zephos_double_item(self)
    tweaks.fix_deku_leaf_model(self)
    tweaks.allow_all_items_to_be_field_items(self)
    tweaks.allow_changing_boss_drop_items(self)
    tweaks.skip_post_boss_warp_cutscenes(self)
    tweaks.remove_shop_item_forced_uniqueness_bit(self)
    tweaks.allow_randomizing_magic_meter_upgrade_item(self)
    tweaks.fix_triforce_charts_not_needing_to_be_deciphered(self)
    tweaks.remove_forsaken_fortress_2_cutscenes(self)
    tweaks.remove_medli_that_gives_fathers_letter(self)
    tweaks.medli_remains_after_master_sword_upgrade(self)
  
  def copy_and_extract_files(self, clean_base_dir):
    # Copy the vanilla files to the randomized directory.
    if not os.path.isdir(self.randomized_base_dir):
      print("Copying clean files...")
      shutil.copytree(clean_base_dir, self.randomized_base_dir)
    
    # Extract all the extra rel files from RELS.arc.
    rels_arc_path = os.path.join(self.randomized_base_dir, "files", "RELS.arc")
    if os.path.isfile(rels_arc_path):
      print("Extracting rels...")
      rels_arc = RARC(rels_arc_path)
      rels_arc.extract_all_files_to_disk_flat(self.rels_dir)
      # And then delete RELS.arc. If we don't do this then the original rels inside it will take precedence over the modified ones we extracted.
      os.remove(rels_arc_path)
      rels_arc = None
  
  def decompress_files(self):
    # Decompress any compressed arcs.
    print("Decompressing archives...")
    for arc_path in self.arc_paths:
      with open(arc_path, "rb") as file:
        data = BytesIO(file.read())
      if try_read_str(data, 0, 4) == "Yaz0":
        decomp_data = Yaz0Decompressor.decompress(data)
        with open(arc_path, "wb") as file:
          file.write(decomp_data)
    
    # Decompress any compressed rels.
    print("Decompressing rels...")
    for rel_path in self.rel_paths:
      with open(rel_path, "rb") as file:
        data = BytesIO(file.read())
      if try_read_str(data, 0, 4) == "Yaz0":
        decomp_data = Yaz0Decompressor.decompress(data)
        with open(rel_path, "wb") as file:
          file.write(decomp_data)
  
  def read_text_file_lists(self):
    # Get item names.
    self.item_names = {}
    self.item_name_to_id = {}
    with open("./data/item_names.txt", "r") as f:
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
    with open(os.path.join(self.randomized_base_dir, "files", "maps", "framework.map"), "r") as f:
      matches = re.findall(r"^  [0-9a-f]{8} [0-9a-f]{6} ([0-9a-f]{8})  4 (\S+) 	\S+ $", f.read(), re.IGNORECASE | re.MULTILINE)
    for match in matches:
      address, name = match
      address = int(address, 16)
      self.function_names[address] = name
    
    # Get stage and island names for debug purposes.
    self.stage_names = {}
    with open("./data/stage_names.txt", "r") as f:
      while True:
        stage_folder = f.readline()
        if not stage_folder:
          break
        stage_name = f.readline()
        self.stage_names[stage_folder.strip()] = stage_name.strip()
    self.island_names = {}
    self.island_number_to_name = {}
    with open("./data/island_names.txt", "r") as f:
      while True:
        room_arc_name = f.readline()
        if not room_arc_name:
          break
        island_name = f.readline().strip()
        self.island_names[room_arc_name.strip()] = island_name
        island_number = int(re.search(r"Room(\d+)", room_arc_name).group(1))
        self.island_number_to_name[island_number] = island_name
    
    self.item_ids_without_a_field_model = []
    with open("./data/items_without_field_models.txt", "r") as f:
      matches = re.findall(r"^([0-9a-f]{2}) ", f.read(), re.IGNORECASE | re.MULTILINE)
    for item_id in matches:
      if item_name:
        item_id = int(item_id, 16)
        self.item_ids_without_a_field_model.append(item_id)
  
  def get_arc(self, arc_path):
    arc_path = arc_path.replace("\\", "/")
    
    if arc_path in self.arcs_by_path:
      return self.arcs_by_path[arc_path]
    else:
      full_path = os.path.join(self.randomized_base_dir, arc_path)
      arc = RARC(full_path)
      self.arcs_by_path[arc_path] = arc
      return arc
  
  def get_raw_file(self, file_path):
    file_path = file_path.replace("\\", "/")
    
    if file_path in self.raw_files_by_path:
      return self.raw_files_by_path[file_path]
    else:
      full_path = os.path.join(self.randomized_base_dir, file_path)
      with open(full_path, "rb") as f:
        data = BytesIO(f.read())
      
      if try_read_str(data, 0, 4) == "Yaz0":
        data = BytesIO(Yaz0Decompressor.decompress(data))
      
      self.raw_files_by_path[file_path] = data
      return data
  
  def save_changed_files(self):
    for arc_path, arc in self.arcs_by_path.items():
      arc.save_to_disk()
    for file_path, data in self.raw_files_by_path.items():
      full_path = os.path.join(self.randomized_base_dir, file_path)
      with open(full_path, "wb") as f:
        data.seek(0)
        f.write(data.read())

  def change_item(self, path, item_name):
    item_id = self.item_name_to_id[item_name]
    
    rel_match = re.search(r"^(rels/[^.]+\.rel)@([0-9A-F]{4})$", path)
    main_dol_match = re.search(r"^main.dol@([0-9A-F]{6})$", path)
    chest_match = re.search(r"^([^/]+/[^/]+\.arc)/Chest([0-9A-F]{3})$", path)
    event_match = re.search(r"^([^/]+/[^/]+\.arc)/Event([0-9A-F]{3}):[^/]+/Actor([0-9A-F]{3})/Action([0-9A-F]{3})$", path)
    scob_match = re.search(r"^([^/]+/[^/]+\.arc)/ScalableObject([0-9A-F]{3})$", path)
    actor_match = re.search(r"^([^/]+/[^/]+\.arc)/Actor([0-9A-F]{3})$", path)
    
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
      chest_index = int(chest_match.group(2), 16)
      self.change_chest_item(arc_path, chest_index, item_id)
    elif event_match:
      arc_path = "files/res/Stage/" + event_match.group(1)
      event_index = int(event_match.group(2), 16)
      actor_index = int(event_match.group(3), 16)
      action_index = int(event_match.group(4), 16)
      self.change_event_item(arc_path, event_index, actor_index, action_index, item_id)
    elif scob_match:
      arc_path = "files/res/Stage/" + scob_match.group(1)
      scob_index = int(scob_match.group(2), 16)
      self.change_scob_item(arc_path, scob_index, item_id)
    elif actor_match:
      arc_path = "files/res/Stage/" + actor_match.group(1)
      actor_index = int(actor_match.group(2), 16)
      self.change_actor_item(arc_path, actor_index, item_id)
    else:
      raise Exception("Invalid item path: " + path)

  def change_hardcoded_item(self, path, offset, item_id):
    data = self.get_raw_file(path)
    write_u8(data, offset, item_id)

  def change_chest_item(self, arc_path, chest_index, item_id):
    dzx = self.get_arc(arc_path).dzx_files[0]
    chest = dzx.entries_by_type("TRES")[chest_index]
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

  def change_scob_item(self, arc_path, scob_index, item_id):
    dzx = self.get_arc(arc_path).dzx_files[0]
    scob = dzx.entries_by_type("SCOB")[scob_index]
    if scob.is_salvage():
      scob.salvage_item_id = item_id
      scob.save_changes()
    elif scob.is_buried_pig_item():
      scob.buried_pig_item_id = item_id
      scob.save_changes()
    else:
      raise Exception("%s/SCOB%03X is an unknown type of SCOB" % (arc_path, scob_index))

  def change_actor_item(self, arc_path, actor_index, item_id):
    dzx = self.get_arc(arc_path).dzx_files[0]
    actr = dzx.entries_by_type("ACTR")[actor_index]
    if actr.is_item():
      actr.item_id = item_id
    elif actr.is_boss_item():
      actr.boss_item_id = item_id
    else:
      raise Exception("%s/ACTR%03X is not an item" % (arc_path, actor_index))
    
    actr.save_changes()
  
  def randomize_items(self):
    print("Randomizing items...")
    
    if True:
      # Don't randomize dungeon keys.
      for location_name, item_location in self.logic.item_locations.items():
        orig_item = item_location["Original item"]
        if orig_item in ["Small Key", "Big Key"]:
          self.logic.add_unrandomized_location(location_name)
    
    # Place progress items.
    while self.logic.unplaced_progress_items:
      accessible_locations = self.logic.get_accessible_remaining_locations()
      
      if not accessible_locations:
        raise Exception("No locations left to place progress items!")
      
      # If the player gained access to any unrandomized locations, we need to give them those items.
      newly_accessible_unrandomized_locations = [
        loc for loc in accessible_locations
        if loc in self.logic.unrandomized_item_locations
      ]
      if newly_accessible_unrandomized_locations:
        for unrandomized_location_name in newly_accessible_unrandomized_locations:
          unrandomized_item_name = self.logic.item_locations[unrandomized_location_name]["Original item"]
          self.logic.set_location_to_item(unrandomized_location_name, unrandomized_item_name)
        
        continue # Redo this loop iteration with the unrandomized locations no longer being considered 'remaining'.
      
      # TODO: prioritize useful items over useless items
      item_name = random.choice(self.logic.unplaced_progress_items)
      
      location_name = random.choice(accessible_locations)
      self.logic.set_location_to_item(location_name, item_name)
    
    # Place unique non-progress items.
    while self.logic.unplaced_nonprogress_items:
      item_name = random.choice(self.logic.unplaced_nonprogress_items)
      location_name = random.choice(self.logic.remaining_item_locations)
      self.logic.set_location_to_item(location_name, item_name)
    
    # Fill remaining unused locations with consumables (Rupees and Spoils).
    locations_to_place_consumables_at = list(self.logic.remaining_item_locations)
    for location_name in locations_to_place_consumables_at:
      item_name = random.choice(self.logic.consumable_items)
      self.logic.set_location_to_item(location_name, item_name)
  
  def write_changed_items(self):
    for location_name, item_name in self.logic.done_item_locations:
      paths = self.logic.item_locations[location_name]["Paths"]
      for path in paths:
        self.change_item(path, item_name)
  
  def randomize_charts(self):
    # Shuffles around which chart points to each sector.
    
    randomizable_charts = [chart for chart in self.chart_list.charts if chart.type in [0, 1, 2, 6]]
    
    original_charts = copy.deepcopy(randomizable_charts)
    # Sort the charts by their texture ID so we get the same results even if we randomize them multiple times.
    original_charts.sort(key=lambda chart: chart.texture_id)
    random.shuffle(original_charts)
    
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
  
  def write_spoiler_log(self):
    spoiler_log = ""
    
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
    
    # Write treasure charts.
    spoiler_log += "Charts:\n"
    for chart_number in range(1, 49+1):
      chart = self.chart_list.find_chart_by_chart_number(chart_number)
      island_name = self.island_number_to_name[chart.island_number]
      spoiler_log += "  %-18s %s\n" % (chart.item_name+":", island_name)
    
    spoiler_log_output_path = "../WW - %s - Spoiler Log.txt" % self.seed
    with open(spoiler_log_output_path, "w") as f:
      f.write(spoiler_log)

if __name__ == "__main__":
  rando = Randomizer(1)
  rando.randomize()
