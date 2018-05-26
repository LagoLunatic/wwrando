
import yaml
import re
from collections import OrderedDict

import os

from logic.item_types import PROGRESS_ITEMS, NONPROGRESS_ITEMS, CONSUMABLE_ITEMS

from wwlib.rarc import RARC
from wwlib.rel import REL

class Logic:
  DUNGEON_NAMES = OrderedDict([
    ("DRC",  "Dragon Roost Cavern"),
    ("FW",   "Forbidden Woods"),
    ("TotG", "Tower of the Gods"),
    ("FF",   "Forsaken Fortress"),
    ("ET",   "Earth Temple"),
    ("WT",   "Wind Temple"),
  ])
  
  def __init__(self, rando):
    self.rando = rando
    
    self.all_progress_items = PROGRESS_ITEMS.copy()
    self.all_nonprogress_items = NONPROGRESS_ITEMS.copy()
    self.consumable_items = CONSUMABLE_ITEMS.copy()
    
    self.triforce_chart_names = []
    self.treasure_chart_names = []
    for i in range(1, 8+1):
      self.triforce_chart_names.append("Triforce Chart %d" % i)
    for i in range(1, 41+1):
      self.treasure_chart_names.append("Treasure Chart %d" % i)
    
    if self.rando.options.get("progression_triforce_charts"):
      self.all_progress_items += self.triforce_chart_names
    else:
      self.all_nonprogress_items += self.triforce_chart_names
    if self.rando.options.get("progression_treasure_charts"):
      self.all_progress_items += self.treasure_chart_names
    else:
      self.all_nonprogress_items += self.treasure_chart_names
    
    self.unplaced_progress_items = self.all_progress_items.copy()
    self.unplaced_nonprogress_items = self.all_nonprogress_items.copy()
    
    self.currently_owned_items = []
    
    self.progressive_items_owned = {
      "Progressive Sword": 0,
      "Progressive Bow": 0,
      "Progressive Wallet": 0,
      "Progressive Bomb Bag": 0,
      "Progressive Quiver": 0,
      "Progressive Picto Box": 0,
    }
    
    self.small_keys_owned_by_dungeon = {}
    self.big_key_owned_by_dungeon = {}
    for short_dungeon_name, dungeon_name in self.DUNGEON_NAMES.items():
      self.small_keys_owned_by_dungeon[dungeon_name] = 0
      self.big_key_owned_by_dungeon[dungeon_name] = False
    
    self.all_cleaned_item_names = []
    for item_name in (self.all_progress_items + self.all_nonprogress_items + self.consumable_items):
      cleaned_item_name = self.clean_item_name(item_name)
      if cleaned_item_name not in self.all_cleaned_item_names:
        self.all_cleaned_item_names.append(cleaned_item_name)
    
    self.load_and_parse_item_locations()
    
    self.locations_by_zone_name = OrderedDict()
    for location_name in self.item_locations:
      zone_name, specific_location_name = self.split_location_name_by_zone(location_name)
      if zone_name not in self.locations_by_zone_name:
        self.locations_by_zone_name[zone_name] = []
      self.locations_by_zone_name[zone_name].append(location_name)
    
    self.remaining_item_locations = list(self.item_locations.keys())
    self.unrandomized_item_locations = []
    
    self.done_item_locations = OrderedDict()
    for location_name in self.item_locations:
      self.done_item_locations[location_name] = None
    
    self.rock_spire_shop_ship_locations = []
    for location_name, location in self.item_locations.items():
      if location["Type"] == "Expensive Purchase":
        self.rock_spire_shop_ship_locations.append(location_name)
  
  def set_location_to_item(self, location_name, item_name):
    if self.done_item_locations[location_name]:
      raise Exception("Location was used twice: " + location_name)
    
    self.done_item_locations[location_name] = item_name
    self.remaining_item_locations.remove(location_name)
    
    if "Key" in item_name:
      # TODO: Will need to change this if implementing key randomization outside the normal dungeon the keys would appear in.
      dungeon_name = location_name.split(" - ", 1)[0]
      self.add_owned_key_for_dungeon(item_name, dungeon_name)
    elif item_name in ["Dungeon Map", "Compass"]:
      # No need to keep track of these in the logic.
      pass
    else:
      self.add_owned_item(item_name)
  
  def add_owned_item(self, item_name):
    cleaned_item_name = self.clean_item_name(item_name)
    if cleaned_item_name not in self.all_cleaned_item_names:
      raise Exception("Unknown item name: " + item_name)
    
    if cleaned_item_name in self.progressive_items_owned:
      self.progressive_items_owned[cleaned_item_name] += 1
    else:
      self.currently_owned_items.append(cleaned_item_name)
    
    if item_name in self.unplaced_progress_items:
      self.unplaced_progress_items.remove(item_name)
    elif item_name in self.unplaced_nonprogress_items:
      self.unplaced_nonprogress_items.remove(item_name)
  
  def add_owned_key_for_dungeon(self, item_name, dungeon_name):
    if item_name == "Small Key":
      self.small_keys_owned_by_dungeon[dungeon_name] += 1
    elif item_name == "Big Key":
      self.big_key_owned_by_dungeon[dungeon_name] = True
    else:
      raise "Unknown key item: " + item_name
  
  def remove_owned_item(self, item_name):
    cleaned_item_name = self.clean_item_name(item_name)
    if cleaned_item_name not in self.all_cleaned_item_names:
      raise Exception("Unknown item name: " + item_name)
    
    if cleaned_item_name in self.progressive_items_owned:
      assert self.progressive_items_owned[cleaned_item_name] > 0
      self.progressive_items_owned[cleaned_item_name] -= 1
    else:
      self.currently_owned_items.remove(cleaned_item_name)
    
    if item_name in self.all_progress_items:
      self.unplaced_progress_items.append(item_name)
    elif item_name in self.all_nonprogress_items:
      self.unplaced_nonprogress_items.append(item_name)
  
  def get_accessible_remaining_locations(self, for_progression=False):
    accessible_location_names = []
    
    locations_to_check = self.remaining_item_locations
    if for_progression:
      locations_to_check = self.filter_locations_for_progression(locations_to_check)
    
    for location_name in locations_to_check:
      requirement_expression = self.item_locations[location_name]["Need"]
      if self.check_logical_expression_req(requirement_expression):
        accessible_location_names.append(location_name)
    
    return accessible_location_names
  
  def get_first_useful_item(self, items_to_check):
    # Searches through a given list of items and returns the first one that opens up at least 1 new location.
    # The randomizer shuffles the list before passing it to this function, so in effect it picks a random useful item.
    
    accessible_undone_locations = self.get_accessible_remaining_locations()
    inaccessible_undone_item_locations = []
    for location_name in self.remaining_item_locations:
      if location_name not in accessible_undone_locations:
        inaccessible_undone_item_locations.append(location_name)
    
    for item_name in items_to_check:
      self.add_owned_item(item_name)
      
      for location_name in inaccessible_undone_item_locations:
        requirement_expression = self.item_locations[location_name]["Need"]
        if self.check_logical_expression_req(requirement_expression):
          self.remove_owned_item(item_name)
          return item_name
      
      self.remove_owned_item(item_name)
    
    return None
  
  def filter_locations_for_progression(self, locations_to_filter):
    filtered_locations = []
    for location_name in locations_to_filter:
      type = self.item_locations[location_name]["Type"]
      if type == "No progression":
        continue
      if type == "Dungeon" and not self.rando.options.get("progression_dungeons"):
        continue
      if type == "Secret Cave" and not self.rando.options.get("progression_secret_caves"):
        continue
      if type == "Sidequest" and not self.rando.options.get("progression_sidequests"):
        continue
      if type == "Minigame" and not self.rando.options.get("progression_minigames"):
        continue
      if type in ["Platform", "Raft"] and not self.rando.options.get("progression_platforms_rafts"):
        continue
      if type == "Submarine" and not self.rando.options.get("progression_submarines"):
        continue
      if type == "Eye Reef Chest" and not self.rando.options.get("progression_eye_reef_chests"):
        continue
      if type in ["Big Octo", "Gunboat"] and not self.rando.options.get("progression_big_octos_gunboats"):
        continue
      if type == "Expensive Purchase" and not self.rando.options.get("progression_expensive_purchases"):
        continue
      if type == "Free Gift" and not self.rando.options.get("progression_gifts"):
        continue
      if type == "Mail" and not self.rando.options.get("progression_mail"):
        continue
      if type in ["Other Chest", "Misc"] and not self.rando.options.get("progression_misc"):
        continue
      # Note: The Triforce/Treasure Chart sunken treasures are not filtered here.
      # Instead they are handled by not considering the charts themselves to be progress items.
      # This results in the item randomizer considering these locations inaccessible until after all progress items are placed.
      
      filtered_locations.append(location_name)
    
    return filtered_locations
  
  def check_item_valid_in_location(self, item_name, location_name):
    # Beedle's shop does not work properly if the same item is in multiple slots of the same shop.
    # Ban the Bait Bag slot from having bait.
    if location_name == "The Great Sea - Beedle's Shop Ship - Bait Bag" and item_name in ["All-Purpose Bait", "Hyoi Pear"]:
      return False
    
    # Also ban the same item from appearing more than once in the rock spire shop ship.
    if location_name in self.rock_spire_shop_ship_locations:
      for other_location_name in self.rock_spire_shop_ship_locations:
        if other_location_name == location_name:
          continue
        if other_location_name in self.done_item_locations:
          other_item_name = self.done_item_locations[other_location_name]
          if item_name == other_item_name:
            return False
    
    return True
  
  def filter_items_by_any_valid_location(self, items, locations):
    # Filters out items that cannot be in any of the given possible locations.
    valid_items = []
    for item_name in items:
      for location_name in locations:
        if self.check_item_valid_in_location(item_name, location_name):
          valid_items.append(item_name)
          break
    return valid_items
  
  def filter_locations_valid_for_item(self, locations, item_name):
    valid_locations = []
    for location_name in locations:
      if self.check_item_valid_in_location(item_name, location_name):
        valid_locations.append(location_name)
    return valid_locations
  
  def filter_items_valid_for_location(self, items, location_name):
    valid_items = []
    for item_name in items:
      if self.check_item_valid_in_location(item_name, location_name):
        valid_items.append(item_name)
    return valid_items
  
  def add_unrandomized_location(self, location_name):
    # For locations that should not be randomized on this seed, e.g. dungeon keys.
    assert location_name in self.item_locations
    self.unrandomized_item_locations.append(location_name)
  
  def load_and_parse_item_locations(self):
    try:
      from sys import _MEIPASS
      logic_path = os.path.join(_MEIPASS, "logic")
    except ImportError:
      logic_path = "logic"
    
    with open(os.path.join(logic_path, "item_locations.txt")) as f:
      self.item_locations = yaml.load(f, YamlOrderedDictLoader)
    for location_name in self.item_locations:
      req_string = self.item_locations[location_name]["Need"]
      if req_string is None:
        # TODO, blank reqs should be an error. Temporarily we will just consider them to be impossible.
        self.item_locations[location_name]["Need"] = self.parse_logic_expression("TODO")
      else:
        self.item_locations[location_name]["Need"] = self.parse_logic_expression(req_string)
      
      if "Type" not in self.item_locations[location_name]:
        self.item_locations[location_name]["Type"] = None
    
    with open(os.path.join(logic_path, "macros.txt")) as f:
      macro_strings = yaml.safe_load(f)
    self.macros = {}
    for name, string in macro_strings.items():
      self.macros[name] = self.parse_logic_expression(string)
  
  def clean_item_name(self, item_name):
    # Remove parentheses from any item names that may have them. (Formerly Master Swords, though that's not an issue anymore.)
    return item_name.replace("(", "").replace(")", "")
  
  def split_location_name_by_zone(self, location_name):
    if " - " in location_name:
      zone_name, specific_location_name = location_name.split(" - ", 1)
    else:
      zone_name = specific_location_name = location_name
    
    return zone_name, specific_location_name
  
  def parse_logic_expression(self, string):
    tokens = [str.strip() for str in re.split("([&|()])", string)]
    tokens = [token for token in tokens if token != ""]
    
    stack = []
    for token in tokens:
      if token == "(":
        stack.append("(")
      elif token == ")":
        nested_tokens = []
        
        while len(stack) != 0:
          exp = stack.pop()
          if exp == "(":
            break
          nested_tokens.append(exp)
        
        nested_tokens.reverse()
        stack.append("(")
        stack.append(nested_tokens)
        stack.append(")")
      else:
        stack.append(token)
    
    return stack
  
  def check_requirement_met(self, req_name):
    if req_name.startswith("Progressive "):
      return self.check_progressive_item_req(req_name)
    elif req_name in self.all_cleaned_item_names:
      return req_name in self.currently_owned_items
    elif "Small Key" in req_name:
      return self.check_small_key_req(req_name)
    elif "Big Key" in req_name:
      return self.check_big_key_req(req_name)
    elif req_name in self.macros:
      logical_expression = self.macros[req_name]
      return self.check_logical_expression_req(logical_expression)
    elif req_name.startswith("Chart for Island "):
      return self.check_chart_req(req_name)
    elif req_name == "Nothing":
      return True
    elif req_name == "Impossible":
      return False
    else:
      raise Exception("Unknown requirement name: " + req_name)
  
  def check_logical_expression_req(self, logical_expression):
    expression_type = None
    subexpression_results = []
    tokens = logical_expression.copy()
    tokens.reverse()
    while tokens:
      token = tokens.pop()
      if token == "|":
        if expression_type == "AND":
          raise Exception("Error parsing progression requirements: & and | must not be within the same nesting level.")
        expression_type = "OR"
      elif token == "&":
        if expression_type == "OR":
          raise Exception("Error parsing progression requirements: & and | must not be within the same nesting level.")
        expression_type = "AND"
      elif token == "(":
        nested_expression = tokens.pop()
        if nested_expression == "(":
          # Nested parentheses
          nested_expression = ["("] + tokens.pop()
        result = self.check_logical_expression_req(nested_expression)
        subexpression_results.append(result)
        assert tokens.pop() == ")"
      else:
        # Subexpression.
        result = self.check_requirement_met(token)
        subexpression_results.append(result)
    
    if expression_type == "OR":
      return any(subexpression_results)
    else:
      return all(subexpression_results)
  
  def check_progressive_item_req(self, req_name):
    match = re.search(r"^(Progressive .+) x(\d+)$", req_name)
    item_name = match.group(1)
    num_required = int(match.group(2))
    
    num_owned = self.progressive_items_owned[item_name]
    return num_owned >= num_required
  
  def check_small_key_req(self, req_name):
    match = re.search(r"^(.+) Small Key x(\d+)$", req_name)
    short_dungeon_name = match.group(1)
    dungeon_name = self.DUNGEON_NAMES[short_dungeon_name]
    num_keys_required = int(match.group(2))
    
    num_small_keys_owned = self.small_keys_owned_by_dungeon[dungeon_name]
    return num_small_keys_owned >= num_keys_required
  
  def check_big_key_req(self, req_name):
    match = re.search(r"^(.+) Big Key$", req_name)
    short_dungeon_name = match.group(1)
    dungeon_name = self.DUNGEON_NAMES[short_dungeon_name]
    
    return self.big_key_owned_by_dungeon[dungeon_name]
  
  def check_chart_req(self, req_name):
    match = re.search(r"^Chart for Island (\d+)$", req_name)
    island_number = int(match.group(1))
    assert 1 <= island_number <= 49
    
    chart = self.rando.chart_list.find_chart_for_island_number(island_number)
    chart_name = chart.item_name
    assert chart_name in self.all_cleaned_item_names
    
    if chart_name not in self.currently_owned_items:
      return False
    if "Triforce Chart" in chart_name:
      # Must have a wallet upgrade to get Triforce Charts deciphered by Tingle.
      return self.check_requirement_met("Any Wallet Upgrade")
    
    return True
  
  def generate_empty_progress_reqs_file(self):
    output_str = ""
    
    found_items = []
    expected_duplicate_items = ["Piece of Heart", "Joy Pendant", "Small Key", "Dungeon Map", "Compass", "Golden Feather", "Boko Baba Seed", "Skull Necklace", "Big Key", "Knight's Crest"]
    
    known_unused_locations = ["sea/Room22.arc/ScalableObject014", "Siren/Stage.arc/Chest003"]
    
    for arc_path in self.rando.arc_paths:
      relative_arc_path = os.path.relpath(arc_path, self.rando.stage_dir)
      stage_folder, arc_name = os.path.split(relative_arc_path)
      stage_path = stage_folder + "/" + arc_name
      
      stage_name = self.rando.stage_names[stage_folder]
      if stage_name == "Unused":
        continue
      elif stage_name == "The Great Sea" and arc_name in self.rando.island_names:
        stage_name = self.rando.island_names[arc_name]
      
      locations_for_this_arc = []
      
      rarc = RARC(arc_path)
      
      if rarc.dzx_files:
        dzx = rarc.dzx_files[0]
        
        for i, chest in enumerate(dzx.entries_by_type("TRES")):
          if chest.item_id == 0xFF:
            #print("Item ID FF: ", stage_name, "Chest%03X" % i)
            continue
          item_name = self.rando.item_names.get(chest.item_id, "")
          locations_for_this_arc.append((item_name, ["Chest%03X" % i]))
        
        for i, actr in enumerate(dzx.entries_by_type("ACTR")):
          if actr.name == "item":
            item_id = actr.params & 0xFF
            item_name = self.rando.item_names.get(item_id, "")
            if "Rupee" in item_name or "Pickup" in item_name:
              continue
            locations_for_this_arc.append((item_name, ["Actor%03X" % i]))
        
        scobs = dzx.entries_by_type("SCOB")
        for i, scob in enumerate(scobs):
          if scob.is_salvage():
            item_name = self.rando.item_names.get(scob.salvage_item_id, "")
            if not item_name:
              continue
            if scob.salvage_type == 0:
              # The type of salvage point you need a treasure chart to get.
              if scob.salvage_duplicate_id == 0:
                all_four_duplicate_salvages = [
                  "ScalableObject%03X" % i
                  for i, other_scob
                  in enumerate(scobs)
                  if other_scob.is_salvage() and other_scob.salvage_type == 0 and other_scob.salvage_chart_index_plus_1 == scob.salvage_chart_index_plus_1
                ]
                locations_for_this_arc.append((item_name, all_four_duplicate_salvages))
            elif "Rupee" not in item_name:
              locations_for_this_arc.append((item_name, ["ScalableObject%03X" % i]))
      
      for event_list in rarc.event_list_files:
        for event_index, event in enumerate(event_list.events):
          for actor_index, actor in enumerate(event.actors):
            if actor is None:
              continue
            
            for action_index, action in enumerate(actor.actions):
              action_path_string = "Event%03X:%s/Actor%03X/Action%03X" % (event_index, event.name, actor_index, action_index)
              if action.name in ["011get_item", "011_get_item"]:
                if action.property_index == 0xFFFFFFFF:
                  continue
                
                item_id = event_list.get_property_value(action.property_index)
                if item_id == 0x100:
                  #print("Item ID 100: ", stage_name, "EventAction%03X" % i)
                  continue
                
                item_name = self.rando.item_names.get(item_id, "")
                locations_for_this_arc.append((item_name, [action_path_string]))
              elif action.name == "059get_dance":
                song_index = event_list.get_property_value(action.property_index)
                item_name = self.rando.item_names.get(0x6D+song_index, "")
                locations_for_this_arc.append((item_name, [action_path_string]))
              elif action.name == "046pget":
                item_id = event_list.get_property_value(action.property_index)
                item_name = self.rando.item_names.get(item_id, "")
                locations_for_this_arc.append((item_name, [action_path_string]))
      
      for original_item_name, locations in locations_for_this_arc:
        if not original_item_name:
          print("Unknown item at: ", stage_folder + "/" + locations[0])
          continue
        
        if any(stage_path + "/" + location in known_unused_locations for location in locations):
          print("Unused locations in " + stage_path)
          continue
        
        if original_item_name in found_items and "Rupee" not in original_item_name and original_item_name not in expected_duplicate_items:
          print("Duplicate item: " + original_item_name)
        found_items.append(original_item_name)
        
        output_str += stage_name + ":\n"
        output_str += "  Need: \n"
        output_str += "  Original item: " + original_item_name + "\n"
        output_str += "  Location:\n"
        for location in locations:
          output_str += "    - " + stage_path + "/" + location + "\n"
    
    with open("progress_reqs.txt", "w") as f:
      f.write(output_str)

class YamlOrderedDictLoader(yaml.SafeLoader):
  pass

YamlOrderedDictLoader.add_constructor(
  yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
  lambda loader, node: OrderedDict(loader.construct_pairs(node))
)
