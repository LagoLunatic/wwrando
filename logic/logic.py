
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
  
  PROGRESS_ITEM_GROUPS = OrderedDict([
    ("Triforce Shards",  [
      "Triforce Shard 1",
      "Triforce Shard 2",
      "Triforce Shard 3",
      "Triforce Shard 4",
      "Triforce Shard 5",
      "Triforce Shard 6",
      "Triforce Shard 7",
      "Triforce Shard 8",
    ]),
    ("Goddess Pearls",  [
      "Nayru's Pearl",
      "Din's Pearl",
      "Farore's Pearl",
    ]),
  ])
  
  def __init__(self, rando):
    self.rando = rando
    
    self.all_progress_items = PROGRESS_ITEMS.copy()
    self.all_nonprogress_items = NONPROGRESS_ITEMS.copy()
    self.all_consumable_items = CONSUMABLE_ITEMS.copy()
    
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
    self.unplaced_consumable_items = self.all_consumable_items.copy()
    
    # Replace progress items that are part of a group with the group name instead.
    for group_name, item_names in self.PROGRESS_ITEM_GROUPS.items():
      for item_name in item_names:
        self.unplaced_progress_items.remove(item_name)
    self.unplaced_progress_items += self.PROGRESS_ITEM_GROUPS.keys()
    
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
    for item_name in (self.all_progress_items + self.all_nonprogress_items + self.all_consumable_items):
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
    self.prerandomization_dungeon_item_locations = OrderedDict()
    
    self.done_item_locations = OrderedDict()
    for location_name in self.item_locations:
      self.done_item_locations[location_name] = None
    
    self.rock_spire_shop_ship_locations = []
    for location_name, location in self.item_locations.items():
      if location["Type"] == "Expensive Purchase":
        self.rock_spire_shop_ship_locations.append(location_name)
    
    self.update_dungeon_entrance_macros()
    
    for item_name in self.rando.starting_items:
      self.add_owned_item(item_name)
  
  def set_location_to_item(self, location_name, item_name):
    #print("Setting %s to %s" % (location_name, item_name))
    
    if self.done_item_locations[location_name]:
      raise Exception("Location was used twice: " + location_name)
    
    self.done_item_locations[location_name] = item_name
    self.remaining_item_locations.remove(location_name)
    
    if "Key" in item_name:
      # TODO: Will need to change this if implementing key randomization outside the normal dungeon the keys would appear in.
      dungeon_name, _ = self.split_location_name_by_zone(location_name)
      self.add_owned_key_for_dungeon(item_name, dungeon_name)
    elif item_name in ["Dungeon Map", "Compass"]:
      # No need to keep track of these in the logic.
      pass
    else:
      self.add_owned_item(item_name)
  
  def set_multiple_locations_to_group(self, available_locations, group_name):
    items_in_group = self.PROGRESS_ITEM_GROUPS[group_name]
    
    if len(available_locations) < len(items_in_group):
      raise Exception("Not enough locations to place all items in group %s" % group_name)
    
    for i, item_name in enumerate(items_in_group):
      location_name = available_locations[i]
      self.set_location_to_item(location_name, item_name)
    
    self.unplaced_progress_items.remove(group_name)
  
  def set_prerandomization_dungeon_item_location(self, location_name, item_name):
    # Temporarily keep track of where dungeon-specific items are placed before the main progression item randomization loop starts.
    assert item_name in ["Small Key", "Big Key", "Dungeon Map", "Compass"]
    assert location_name in self.item_locations
    self.prerandomization_dungeon_item_locations[location_name] = item_name
  
  def get_num_progression_items(self):
    num_progress_items = 0
    for item_name in self.unplaced_progress_items:
      if item_name in self.PROGRESS_ITEM_GROUPS:
        group_name = item_name
        for item_name in self.PROGRESS_ITEM_GROUPS[group_name]:
          num_progress_items += 1
      else:
        num_progress_items += 1
    
    return num_progress_items
  
  def get_num_progression_locations(self):
    progress_locations = self.filter_locations_for_progression(self.item_locations.keys(), filter_sunken_treasure=True)
    num_progress_locations = len(progress_locations)
    if self.rando.options.get("progression_triforce_charts"):
      num_progress_locations += 8
    if self.rando.options.get("progression_treasure_charts"):
      num_progress_locations += 41
    
    return num_progress_locations
  
  def get_progress_and_non_progress_locations(self):
    all_locations = self.item_locations.keys()
    progress_locations = self.filter_locations_for_progression(all_locations, filter_sunken_treasure=True)
    nonprogress_locations = []
    for location_name in all_locations:
      if location_name in progress_locations:
        continue
      
      type = self.item_locations[location_name]["Type"]
      if type == "Sunken Treasure":
        chart_name = self.chart_name_for_location(location_name)
        if "Triforce Chart" in chart_name:
          if self.rando.options.get("progression_triforce_charts"):
            progress_locations.append(location_name)
          else:
            nonprogress_locations.append(location_name)
        else:
          if self.rando.options.get("progression_treasure_charts"):
            progress_locations.append(location_name)
          else:
            nonprogress_locations.append(location_name)
      else:
        nonprogress_locations.append(location_name)
    
    return (progress_locations, nonprogress_locations)
  
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
    elif item_name in self.unplaced_consumable_items:
      self.unplaced_consumable_items.remove(item_name)
  
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
    elif item_name in self.all_consumable_items:
      self.unplaced_consumable_items.append(item_name)
  
  def add_owned_item_or_item_group(self, item_name):
    if item_name in self.PROGRESS_ITEM_GROUPS:
      group_name = item_name
      for item_name in self.PROGRESS_ITEM_GROUPS[group_name]:
        if item_name in self.progressive_items_owned:
          self.progressive_items_owned[item_name] += 1
        else:
          self.currently_owned_items.append(item_name)
    else:
      self.add_owned_item(item_name)
  
  def remove_owned_item_or_item_group(self, item_name):
    if item_name in self.PROGRESS_ITEM_GROUPS:
      group_name = item_name
      for item_name in self.PROGRESS_ITEM_GROUPS[group_name]:
        if item_name in self.progressive_items_owned:
          assert self.progressive_items_owned[item_name] > 0
          self.progressive_items_owned[item_name] -= 1
        else:
          self.currently_owned_items.remove(item_name)
    else:
      self.remove_owned_item(item_name)
  
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
  
  def get_first_useful_item(self, items_to_check, for_progression=False):
    # Searches through a given list of items and returns the first one that opens up at least 1 new location.
    # The randomizer shuffles the list before passing it to this function, so in effect it picks a random useful item.
    
    accessible_undone_locations = self.get_accessible_remaining_locations(for_progression=for_progression)
    inaccessible_undone_item_locations = []
    locations_to_check = self.remaining_item_locations
    if for_progression:
      locations_to_check = self.filter_locations_for_progression(locations_to_check)
    for location_name in locations_to_check:
      if location_name not in accessible_undone_locations:
        inaccessible_undone_item_locations.append(location_name)
    
    for item_name in items_to_check:
      self.add_owned_item_or_item_group(item_name)
      
      for location_name in inaccessible_undone_item_locations:
        requirement_expression = self.item_locations[location_name]["Need"]
        if self.check_logical_expression_req(requirement_expression):
          self.remove_owned_item_or_item_group(item_name)
          return item_name
      
      self.remove_owned_item_or_item_group(item_name)
    
    return None
  
  def filter_locations_for_progression(self, locations_to_filter, filter_sunken_treasure=False):
    filtered_locations = []
    for location_name in locations_to_filter:
      type = self.item_locations[location_name]["Type"]
      if type == "No progression":
        continue
      if type == "Tingle Statue Chest":
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
      if type == "Sunken Treasure" and filter_sunken_treasure:
        continue
      # Note: The Triforce/Treasure Chart sunken treasures are handled differently from other types.
      # During randomization they are handled by not considering the charts themselves to be progress items.
      # That results in the item randomizer considering these locations inaccessible until after all progress items are placed.
      # But when calculating the total number of progression locations, sunken treasures are filtered out entirely here so they can be specially counted elsewhere.
      
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
    
    # Our code to fix Zunari's Magic Armor item gift relies on the items Zunari gives all having different IDs.
    # There for we don't allow the other two items Zunari gives to be placed in the Magic Armor slot.
    if location_name == "Windfall Island - Zunari - Stock Exotic Flower in Zunari's Shop" and item_name in ["Town Flower", "Boat's Sail"]:
      return False
    
    return True
  
  def filter_items_by_any_valid_location(self, items, locations):
    # Filters out items that cannot be in any of the given possible locations.
    valid_items = []
    for item_name in items:
      if item_name in self.PROGRESS_ITEM_GROUPS:
        group_name = item_name
        items_in_group = self.PROGRESS_ITEM_GROUPS[group_name]
        if len(items_in_group) > len(locations):
          # Not enough locations to place all items in this group.
          continue
        # If the number of locations is sufficient, we consider this group able to be placed.
        # NOTE: We do not check if each individual item in the group can also be placed.
        # This is fine for shards and pearls, but would be incorrect for items that actually have location restrictions.
        valid_items.append(group_name)
      else:
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
    
    with open(os.path.join(logic_path, "macros.txt")) as f:
      macro_strings = yaml.safe_load(f)
    self.macros = {}
    for macro_name, req_string in macro_strings.items():
      self.set_macro(macro_name, req_string)
  
  def set_macro(self, macro_name, req_string):
    self.macros[macro_name] = self.parse_logic_expression(req_string)
  
  def update_dungeon_entrance_macros(self):
    # Update all the dungeon access macros to take randomized entrances into account.
    for entrance_name, dungeon_name in self.rando.dungeon_entrances.items():
      dungeon_access_macro_name = "Can Access " + dungeon_name
      dungeon_entrance_access_macro_name = "Can Access " + entrance_name
      self.set_macro(dungeon_access_macro_name, dungeon_entrance_access_macro_name)
  
  def temporarily_make_dungeon_entrance_macros_impossible(self):
    # Update all the dungeon access macros to be considered "Impossible".
    # Useful when the dungeon entrance randomizer is selecting which dungeons should be allowed where.
    for entrance_name, dungeon_name in self.rando.dungeon_entrances.items():
      dungeon_access_macro_name = "Can Access " + dungeon_name
      self.set_macro(dungeon_access_macro_name, "Impossible")
  
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
  
  def chart_name_for_location(self, location_name):
    reqs = self.item_locations[location_name]["Need"]
    chart_req = next(req for req in reqs if req.startswith("Chart for Island "))
    
    match = re.search(r"^Chart for Island (\d+)$", chart_req)
    island_number = int(match.group(1))
    assert 1 <= island_number <= 49
    
    chart = self.rando.chart_list.find_chart_for_island_number(island_number)
    return chart.item_name

class YamlOrderedDictLoader(yaml.SafeLoader):
  pass

YamlOrderedDictLoader.add_constructor(
  yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
  lambda loader, node: OrderedDict(loader.construct_pairs(node))
)
