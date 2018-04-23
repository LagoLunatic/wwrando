
import yaml
import re
from collections import OrderedDict

import os

from logic.item_types import PROGRESS_ITEMS, NONPROGRESS_ITEMS, CONSUMABLE_ITEMS

from rarc import RARC
from rel import REL

class Logic:
  DUNGEON_NAMES = {
    "DRC":  "Dragon Roost Cavern",
    "FW":   "Forbidden Woods",
    "TotG": "Tower of the Gods",
    "ET":   "Earth Temple",
    "WT":   "Wind Temple",
  }
  
  def __init__(self, rando):
    self.rando = rando
    
    self.unplaced_progress_items = list(PROGRESS_ITEMS)
    self.unplaced_nonprogress_items = list(NONPROGRESS_ITEMS)
    self.consumable_items = list(CONSUMABLE_ITEMS)
    
    self.currently_owned_items = []
    
    self.small_keys_owned_by_dungeon = {}
    self.big_key_owned_by_dungeon = {}
    for short_dungeon_name, dungeon_name in self.DUNGEON_NAMES.items():
      self.small_keys_owned_by_dungeon[dungeon_name] = 0
      self.big_key_owned_by_dungeon[dungeon_name] = False
    
    self.all_cleaned_item_names = []
    for item_id, item_name in self.rando.item_names.items():
      cleaned_item_name = self.clean_item_name(item_name)
      self.all_cleaned_item_names.append(cleaned_item_name)
    
    self.load_and_parse_item_locations()
    
    self.remaining_item_locations = list(self.item_locations.keys())
    self.unrandomized_item_locations = []
    
    self.done_item_locations = OrderedDict()
    for location_name in self.item_locations:
      self.done_item_locations[location_name] = None
  
  def set_location_to_item(self, location_name, item_name):
    if self.done_item_locations[location_name]:
      raise Exception("Location was used twice: " + location_name)
    
    self.done_item_locations[location_name] = item_name
    self.remaining_item_locations.remove(location_name)
    
    if "Key" in item_name:
      # TODO: Will need to change this if implementing key randomization outside the normal dungeon the keys would appear in.
      dungeon_name = location_name.split(" - ", 1)[0]
      self.add_owned_key_for_dungeon(item_name, dungeon_name)
    else:
      self.add_owned_item(item_name)
  
  def add_owned_item(self, item_name):
    cleaned_item_name = self.clean_item_name(item_name)
    if cleaned_item_name not in self.all_cleaned_item_names:
      raise Exception("Unknown item name: " + item_name)
    self.currently_owned_items.append(cleaned_item_name)
    
    if item_name in self.unplaced_progress_items:
      self.unplaced_progress_items.remove(item_name)
    if item_name in self.unplaced_nonprogress_items:
      self.unplaced_nonprogress_items.remove(item_name)
  
  def add_owned_key_for_dungeon(self, item_name, dungeon_name):
    if item_name == "Small Key":
      self.small_keys_owned_by_dungeon[dungeon_name] += 1
    elif item_name == "Big Key":
      self.big_key_owned_by_dungeon[dungeon_name] = True
    else:
      raise "Unknown key item: " + item_name
  
  def get_accessible_remaining_locations(self):
    accessible_location_names = []
    
    for location_name in self.remaining_item_locations:
      requirement_expression = self.item_locations[location_name]["Need"]
      if self.check_logical_expression_req(requirement_expression):
        accessible_location_names.append(location_name)
    
    return accessible_location_names
  
  def add_unrandomized_location(self, location_name):
    # For locations that should not be randomized on this seed, e.g. dungeon keys.
    assert location_name in self.item_locations
    self.unrandomized_item_locations.append(location_name)
  
  def load_and_parse_item_locations(self):
    with open("./logic/item_locations.txt") as f:
      self.item_locations = yaml.load(f, YamlOrderedDictLoader)
    for location_name in self.item_locations:
      req_string = self.item_locations[location_name]["Need"]
      if req_string is None:
        # TODO, blank reqs should be an error. Temporarily we will just consider them to be impossible.
        self.item_locations[location_name]["Need"] = self.parse_logic_expression("TODO")
      else:
        self.item_locations[location_name]["Need"] = self.parse_logic_expression(req_string)
    
    with open("./logic/macros.txt") as f:
      macro_strings = yaml.safe_load(f)
    self.macros = {}
    for name, string in macro_strings.items():
      self.macros[name] = self.parse_logic_expression(string)
  
  def clean_item_name(self, item_name):
    # Remove parentheses from Master Sword and other names.
    return item_name.replace("(", "").replace(")", "")
  
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
    if req_name in self.all_cleaned_item_names:
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
    tokens = list(logical_expression)
    tokens.reverse()
    while len(tokens) != 0:
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
