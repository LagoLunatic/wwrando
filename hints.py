import os
from collections import Counter, OrderedDict
from enum import Enum
from math import sqrt

import yaml

from logic.item_types import CONSUMABLE_ITEMS, DUNGEON_NONPROGRESS_ITEMS, DUNGEON_PROGRESS_ITEMS
from logic.logic import Logic
from wwrando_paths import DATA_PATH
import tweaks

ITEM_LOCATION_NAME_TO_EXIT_ZONE_NAME_OVERRIDES = {
  "Pawprint Isle - Wizzrobe Cave": "Pawprint Isle Side Isle",
}


class HintType(Enum):
  PATH = 0
  BARREN = 1
  ITEM = 2
  LOCATION = 3


class Hint:
  def __init__(self, type: HintType, place, reward=None):
    self.type = type
    self.place = place
    self.reward = reward
  
  def __str__(self):
    return "<HINT: %s, (%s, %s)>" % (str(self.type), self.place, self.reward)
  
  def __repr__(self):
    return "Hint(%s, %s, %s)" % (str(self.type), repr(self.place), repr(self.reward))


class Hints:
  # A dictionary mapping dungeon name to the dungeon boss.
  # The boss name is used as the path goal in the hint text.
  DUNGEON_NAME_TO_BOSS_NAME = {
    "Dragon Roost Cavern": "Gohma",
    "Forbidden Woods": "Kalle Demos",
    "Tower of the Gods": "Gohdan",
    "Forsaken Fortress": "Helmaroc King",
    "Earth Temple": "Jalhalla",
    "Wind Temple": "Molgera",
    "Hyrule": "Hyrule",
    "Ganon's Tower": "Ganondorf",
  }
  
  # A dictionary mapping dungeon name to the requirement name.
  # This dictionary is used when determining which items are on the path to a goal.
  DUNGEON_NAME_TO_REQUIREMENT_NAME = {
    "Dragon Roost Cavern": "Can Access Other Location \"Dragon Roost Cavern - Gohma Heart Container\"",
    "Forbidden Woods": "Can Access Other Location \"Forbidden Woods - Kalle Demos Heart Container\"",
    "Tower of the Gods": "Can Access Other Location \"Tower of the Gods - Gohdan Heart Container\"",
    "Forsaken Fortress": "Can Access Other Location \"Forsaken Fortress - Helmaroc King Heart Container\"",
    "Earth Temple": "Can Access Other Location \"Earth Temple - Jalhalla Heart Container\"",
    "Wind Temple": "Can Access Other Location \"Wind Temple - Molgera Heart Container\"",
    "Hyrule": "Can Access Hyrule",
    "Ganon's Tower": "Can Reach and Defeat Ganondorf",
  }
  
  def __init__(self, rando):
    self.rando = rando
    self.logic = rando.logic
    self.options = rando.options
    
    self.path_logic = Logic(self.rando)
    self.path_logic_initial_state = self.path_logic.save_simulated_playthrough_state()
    
    # Define instance variable shortcuts for hint distribution options.
    self.max_path_hints = int(self.options.get("num_path_hints", 0))
    self.max_barren_hints = int(self.options.get("num_barren_hints", 0))
    self.max_location_hints = int(self.options.get("num_location_hints", 0))
    self.max_item_hints = int(self.options.get("num_item_hints", 0))
    self.total_num_hints = self.max_path_hints + self.max_barren_hints + self.max_location_hints + self.max_item_hints
    
    self.clearer_hints = self.options.get("clearer_hints")
    self.use_always_hints = self.options.get("use_always_hints")
    
    # Import dictionaries used to build hints from files.
    with open(os.path.join(DATA_PATH, "progress_item_hints.txt"), "r") as f:
      self.progress_item_hints = yaml.safe_load(f)
    with open(os.path.join(DATA_PATH, "zone_name_hints.txt"), "r") as f:
      self.zone_name_hints = yaml.safe_load(f)
    with open(os.path.join(DATA_PATH, "location_hints.txt"), "r") as f:
      self.location_hints = yaml.safe_load(f)
    
    # Validate location names in location hints file.
    for location_name in self.location_hints:
      assert location_name in rando.logic.item_locations
    
    # Define a dictionary mapping charts to their sunken treasure.
    # This will be used to check whether or not the chart leads to a junk item. If so, the chart itself can be
    # considered junk.
    self.chart_name_to_sunken_treasure = {}
  
  @staticmethod
  def get_hint_item_name(item_name):
    if item_name.startswith("Triforce Chart"):
      return "Triforce Chart"
    if item_name.startswith("Triforce Shard"):
      return "Triforce Shard"
    if item_name.startswith("Treasure Chart"):
      return "Treasure Chart"
    if item_name.endswith("Tingle Statue"):
      return "Tingle Statue"
    if item_name.endswith("Small Key"):
      return "Small Key"
    if item_name.endswith("Big Key"):
      return "Big Key"
    return item_name
  
  @staticmethod
  def get_formatted_hint_text(hint, prefix="They say that ", suffix=".", delay=30):
    place = hint.place
    if place == "Mailbox":
      place = "the mail"
    elif place == "The Great Sea":
      place = "a location on the open seas"
    elif place == "Tower of the Gods Sector":
      place = "the Tower of the Gods sector"
    
    if hint.type == HintType.PATH:
      place_preposition = "at"
      if place in ["the mail", "the Tower of the Gods sector"]:
        place_preposition = "in"
      hint_string = (
        "%san item found %s \\{1A 06 FF 00 00 05}%s\\{1A 06 FF 00 00 00} is on the path to \\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00}%s"
        % (prefix, place_preposition, place, hint.reward, suffix)
      )
    elif hint.type == HintType.BARREN:
      verb = "visiting"
      if place == "the mail":
        verb = "checking"
      hint_string = (
        "%s%s \\{1A 06 FF 00 00 03}%s\\{1A 06 FF 00 00 00} is a foolish choice%s"
        % (prefix, verb, place, suffix)
      )
    elif hint.type == HintType.LOCATION:
      hint_string = (
        "%s\\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00} rewards \\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00}%s"
        % (prefix, place, hint.reward, suffix)
      )
    elif hint.type == HintType.ITEM:
      hint_string = (
        "%s\\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00} is located in \\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00}%s"
        % (prefix, hint.reward, place, suffix)
      )
    else:
      hint_string = ""
    
    # Add a wait command (delay) to prevent the player from skipping over the hint accidentally.
    delay = max(0, min(0xFFFF, delay)) # Clamp within valid range.
    if delay > 0:
      hint_string += "\\{1A 07 00 00 07 %02X %02X}" % (delay >> 8, delay & 0xFF)
    
    return hint_string
  
  @staticmethod
  def get_clearer_item_name(item_name):
    if item_name.endswith("Small Key"):
      short_dungeon_name = item_name.split(" Small Key")[0]
      dungeon_name = Logic.DUNGEON_NAMES[short_dungeon_name]
      return "%s small key" % dungeon_name
    if item_name.endswith("Big Key"):
      short_dungeon_name = item_name.split(" Big Key")[0]
      dungeon_name = Logic.DUNGEON_NAMES[short_dungeon_name]
      return "%s Big Key" % dungeon_name
    if item_name.endswith("Dungeon Map"):
      short_dungeon_name = item_name.split(" Dungeon Map")[0]
      dungeon_name = Logic.DUNGEON_NAMES[short_dungeon_name]
      return "%s Dungeon Map" % dungeon_name
    if item_name.endswith("Compass"):
      short_dungeon_name = item_name.split(" Compass")[0]
      dungeon_name = Logic.DUNGEON_NAMES[short_dungeon_name]
      return "%s Compass" % dungeon_name
    return item_name
  
  
  def get_entrance_zone(self, location_name):
    # Helper function to return the entrance zone name for the location.
    #
    # For non-dungeon and non-cave locations, the entrance zone name is simply the zone (island) name. However, when
    # entrances are randomized, the entrance zone name may differ from the zone name for dungeons and caves.
    # As a special case, if the entrance zone is Tower of the Gods or the location name is "Tower of the Gods - Sunken
    # Treasure", the entrance zone name is "Tower of the Gods Sector" to differentiate between the dungeon and the
    # entrance.
    
    zone_name, specific_location_name = self.logic.split_location_name_by_zone(location_name)
    
    if location_name in ITEM_LOCATION_NAME_TO_EXIT_ZONE_NAME_OVERRIDES:
      zone_name = ITEM_LOCATION_NAME_TO_EXIT_ZONE_NAME_OVERRIDES[location_name]
    
    if zone_name in self.rando.dungeon_and_cave_island_locations and self.logic.is_dungeon_or_cave(location_name):
      # If the location is in a dungeon or cave, use the hint for whatever island the dungeon/cave is located on.
      entrance_zone = self.rando.dungeon_and_cave_island_locations[zone_name]
      
      # Special case for Tower of the Gods to use Tower of the Gods Sector when refering to the entrance, not the dungeon
      if entrance_zone == "Tower of the Gods":
        entrance_zone = "Tower of the Gods Sector"
    else:
      # Otherwise, for non-dungeon and non-cave locations, just use the zone name.
      entrance_zone = zone_name
      
      # Special case for Tower of the Gods to use Tower of the Gods Sector when refering to the Sunken Treasure
      if location_name == "Tower of the Gods - Sunken Treasure":
        entrance_zone = "Tower of the Gods Sector"
      # Note that Forsaken Fortress - Sunken Treasure has a similar issue, but there are no randomized entrances on
      # Forsaken Fortress, so we won't make that distinction here.
    return entrance_zone
  
  def build_sunken_treasure_mapping(self):
    # Helper function to create a mapping of treasure charts to their respective sunken treasure.
    
    chart_name_to_island_number = {}
    for island_number in range(1, 49+1):
      chart_name = self.logic.macros["Chart for Island %d" % island_number][0]
      chart_name_to_island_number[chart_name] = island_number
    
    chart_name_to_sunken_treasure = {}
    for chart_number in range(1, 49+1):
      if chart_number <= 8:
        chart_name = "Triforce Chart %d" % chart_number
      else:
        chart_name = "Treasure Chart %d" % (chart_number-8)
      island_number = chart_name_to_island_number[chart_name]
      island_name = self.rando.island_number_to_name[island_number]
      chart_name_to_sunken_treasure[chart_name] = "%s - Sunken Treasure" % island_name
    
    return chart_name_to_sunken_treasure
  
  def check_location_required_for_paths(self, location_to_check, paths_to_check):
    # To check whether the location is required or not, we simulate a playthrough and remove the item the player would
    # receive at that location immediately after they receive it. If the player can still fulfill the requirement 
    # despite not having this item, the location is not required.
    
    # If the item is not a progress item, there's no way it's required.
    item_name = self.logic.done_item_locations[location_to_check]
    if item_name not in self.logic.all_progress_items:
      return {}
    
    # Reuse a single Logic instance over multiple calls to this function for performance reasons.
    self.path_logic.load_simulated_playthrough_state(self.path_logic_initial_state)
    previously_accessible_locations = []
    
    while self.path_logic.unplaced_progress_items:
      progress_items_in_this_sphere = OrderedDict()
      
      accessible_locations = self.path_logic.get_accessible_remaining_locations()
      locations_in_this_sphere = [
        loc for loc in accessible_locations
        if loc not in previously_accessible_locations
      ]
      if not locations_in_this_sphere:
        break
      
      
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
            
            self.path_logic.add_owned_item(item_name)
            # Remove small key from owned items if it was from the location we want to check
            if small_key_location_name == location_to_check:
              self.path_logic.remove_owned_item(item_name)
          
          previously_accessible_locations += newly_accessible_small_key_locations
          continue # Redo this loop iteration with the small key locations no longer being considered 'remaining'.
      
      
      # Hide duplicated progression items (e.g. Empty Bottles) when they are placed in non-progression locations to avoid confusion and inconsistency.
      locations_in_this_sphere = self.path_logic.filter_locations_for_progression(locations_in_this_sphere)
      
      for location_name in locations_in_this_sphere:
        item_name = self.logic.done_item_locations[location_name]
        if item_name in self.path_logic.all_progress_items:
          progress_items_in_this_sphere[location_name] = item_name
      
      for location_name, item_name in progress_items_in_this_sphere.items():
        self.path_logic.add_owned_item(item_name)
        # Remove item from owned items if it was from the location we want to check.
        if location_name == location_to_check:
          self.path_logic.remove_owned_item(item_name)
      for group_name, item_names in self.path_logic.progress_item_groups.items():
        entire_group_is_owned = all(item_name in self.path_logic.currently_owned_items for item_name in item_names)
        if entire_group_is_owned and group_name in self.path_logic.unplaced_progress_items:
          self.path_logic.unplaced_progress_items.remove(group_name)
      
      previously_accessible_locations = accessible_locations
    
    requirements_met = {
      path_name: not self.path_logic.check_requirement_met(self.DUNGEON_NAME_TO_REQUIREMENT_NAME[path_name])
      for path_name in paths_to_check
    }
    return requirements_met
  
  def get_required_locations_for_paths(self):
    # Add all race-mode dungeons as paths, in addition to Hyrule and Ganon's Tower.
    dungeon_paths = self.rando.race_mode_required_dungeons.copy()
    non_dungeon_paths = ["Hyrule", "Ganon's Tower"]
    path_goals = dungeon_paths + non_dungeon_paths
    required_locations_for_paths = {goal: [] for goal in path_goals}
    
    # Determine which locations are required to beat the seed.
    # Items are implicitly referred to by their location to handle duplicate item names (i.e., progressive items and
    # small keys). Basically, we remove the item from that location and see if the seed is still beatable. If not, then
    # we consider the item as required.
    progress_locations, non_progress_locations = self.logic.get_progress_and_non_progress_locations()
    for location_name in progress_locations:
      # Ignore race-mode-banned locations.
      if location_name in self.rando.race_mode_banned_locations:
        continue
      
      # Build a list of required locations, along with the item at that location.
      item_name = self.logic.done_item_locations[location_name]
      if (
        location_name not in self.rando.race_mode_required_locations          # Ignore boss Heart Containers in race mode, even if it's required.
        and (self.options.get("keylunacy") or not item_name.endswith(" Key")) # Keys are only considered in key-lunacy.
        and item_name in self.logic.all_progress_items                        # Required locations always contain progress items (by definition).
      ):
        # Determine the item name for the given location.
        zone_name, specific_location_name = self.logic.split_location_name_by_zone(location_name)
        entrance_zone = self.get_entrance_zone(location_name)
        item_tuple = (zone_name, entrance_zone, specific_location_name, item_name)
        
        # Check and record if the location is required for path goals.
        requirements_met = self.check_location_required_for_paths(location_name, path_goals)
        for goal_name, requirement_met in requirements_met.items():
          if requirement_met:
            required_locations_for_paths[goal_name].append(item_tuple)
        
        # Add items that are path to race mode dungeons to the Hyrule and Ganon's Tower paths
        for dungeon_path_name in dungeon_paths:
          for item_tuple in required_locations_for_paths[dungeon_path_name]:
            for non_dungeon_path_name in non_dungeon_paths:
              if item_tuple not in required_locations_for_paths[non_dungeon_path_name]:
                required_locations_for_paths[non_dungeon_path_name].append(item_tuple)
    
    return required_locations_for_paths
  
  def get_path_hint(self, unhinted_locations, hinted_locations, path_name):
    valid_path_hint = False
    while not valid_path_hint:
      # If there are no hintable locations, return `None`.
      if len(unhinted_locations) == 0:
        return None, None
      
      # Pick a location uniformly at random from the list of hintable locations.
      zone_name, entrance_zone, specific_location_name, item_name = self.rando.rng.choice(unhinted_locations)
      hinted_location = "%s - %s" % (zone_name, specific_location_name)
      
      # Regardless of whether we use the location, remove that location from being hinted.
      unhinted_locations.remove((zone_name, entrance_zone, specific_location_name, item_name))
      
      # The location is a valid hint if it has not already been hinted at.
      if hinted_location not in hinted_locations:
        valid_path_hint = True
    
    # Record hinted zone, item, and path goal.
    # If it's a dungeon, use the dungeon name. If it's a cave, use the entrance zone name.
    if zone_name in self.logic.DUNGEON_NAMES.values():
      if zone_name == "Tower of the Gods" and specific_location_name == "Sunken Treasure":
        # Special case: if location is Tower of the Gods - Sunken Treasure, use "Tower of the Gods Sector" as the hint.
        return Hint(HintType.PATH, "Tower of the Gods Sector", self.DUNGEON_NAME_TO_BOSS_NAME[path_name]), hinted_location
      else:
        return Hint(HintType.PATH, zone_name, self.DUNGEON_NAME_TO_BOSS_NAME[path_name]), hinted_location
    else:
      return Hint(HintType.PATH, entrance_zone, self.DUNGEON_NAME_TO_BOSS_NAME[path_name]), hinted_location
  
  
  def determine_junk_items(self):
    # Helper method which returns a set of guaranteed unrequired items in the seed.
    
    junk_items = set(self.logic.all_nonprogress_items)  # Start with all non-progress items in the seed.
    junk_items |= set(CONSUMABLE_ITEMS)                 # Add consumables like Heart Containers and Rupees.
    junk_items |= set(DUNGEON_NONPROGRESS_ITEMS)        # Add dungeon items (Dungeon Maps and Compasses).
    if not self.options.get("keylunacy"):
      junk_items |= set(DUNGEON_PROGRESS_ITEMS)         # Consider Small and Big Keys junk when key-lunacy is off.
    
    # Consider Empty Bottles junk only if none are logical.
    if "Empty Bottle" in self.rando.logic.all_progress_items and "Empty Bottle" in junk_items:
      junk_items.remove("Empty Bottle")
    # Consider Progressive Quiver junk only if none are logical.
    if "Progressive Quiver" in self.rando.logic.all_progress_items and "Progressive Quiver" in junk_items:
      junk_items.remove("Progressive Quiver")
    # Consider Progressive Wallet junk only if none are logical.
    if "Progressive Wallet" in self.rando.logic.all_progress_items and "Progressive Wallet" in junk_items:
      junk_items.remove("Progressive Wallet")
    
    # Consider Small and Big Keys for non-required race mode dungeons as junk when key-lunacy is on.
    if self.options.get("race_mode") and self.options.get("keylunacy"):
      race_mode_banned_dungeons = set(self.logic.DUNGEON_NAMES.values()) - set(self.rando.race_mode_required_dungeons)
      if "Dragon Roost Cavern" in race_mode_banned_dungeons:
        junk_items.add("DRC Small Key")
        junk_items.add("DRC Big Key")
      if "Forbidden Woods" in race_mode_banned_dungeons:
        junk_items.add("FW Small Key")
        junk_items.add("FW Big Key")
      if "Tower of the Gods" in race_mode_banned_dungeons:
        junk_items.add("TotG Small Key")
        junk_items.add("TotG Big Key")
      if "Earth Temple" in race_mode_banned_dungeons:
        junk_items.add("ET Small Key")
        junk_items.add("ET Big Key")
      if "Wind Temple" in race_mode_banned_dungeons:
        junk_items.add("WT Small Key")
        junk_items.add("WT Big Key")
    
    # Special cases: Loop here until the list of junk items stops changing.
    junk_items_changed = True
    while junk_items_changed:
      junk_items_changed = False
      
      # Loop through charts when sunken treasure on and consider any charts that lead to immediately to junk as junk.
      if self.options.get("progression_triforce_charts") or self.options.get("progression_treasure_charts"):
        for chart_name, sunken_treasure in self.chart_name_to_sunken_treasure.items():
          if chart_name not in junk_items:
            item_name = self.logic.done_item_locations[sunken_treasure]
            if item_name in junk_items:
              junk_items.add(chart_name)
              junk_items_changed = True
      
      # Check Maggie's and Moblin's Letters and if they lead to junk, consider them junk as well.
      if self.options.get("progression_short_sidequests"):
        item_name = self.logic.done_item_locations["Windfall Island - Cafe Bar - Postman"]
        if "Maggie's Letter" not in junk_items and item_name in junk_items:
          junk_items.add("Maggie's Letter")
          junk_items_changed = True
        item_name = self.logic.done_item_locations["Windfall Island - Maggie - Delivery Reward"]
        if "Moblin's Letter" not in junk_items and item_name in junk_items:
          junk_items.add("Moblin's Letter")
          junk_items_changed = True
      
      # Check the two 12-eye octos and if both lead to junk, consider both quivers as junk.
      if self.options.get("progression_big_octos_gunboats"):
        octo1_item_name = self.logic.done_item_locations["Tingle Island - Big Octo"]
        octo2_item_name = self.logic.done_item_locations["Seven-Star Isles - Big Octo"]
        if "Progressive Quiver" not in junk_items and octo1_item_name in junk_items and octo2_item_name in junk_items:
          junk_items.add("Progressive Quiver")
          junk_items_changed = True
      
      if self.options.get("progression_misc"):
        # Check Tingle statues.
        item_name = self.logic.done_item_locations["Tingle Island - Ankle - Reward for All Tingle Statues"]
        if "Dragon Tingle Statue" not in junk_items and item_name in junk_items:
          junk_items.add("Dragon Tingle Statue")
          junk_items.add("Forbidden Tingle Statue")
          junk_items.add("Goddess Tingle Statue")
          junk_items.add("Earth Tingle Statue")
          junk_items.add("Wind Tingle Statue")
          junk_items_changed = True
        
        # Check Ghost Ship Chart.
        item_name = self.logic.done_item_locations["The Great Sea - Ghost Ship"]
        if "Ghost Ship Chart" not in junk_items and item_name in junk_items:
          junk_items.add("Ghost Ship Chart")
          junk_items_changed = True
        
    return junk_items
  
  def get_barren_zones(self, progress_locations):
    # Helper function to build a list of barren zones in this seed.
    # The list includes only zones which are allowed to be hinted at as barren.
    
    # To determine a list of candidate barren zones, we first construct a list of guaranteed junk items. The remaining
    # set of items may or may not be required, so the zones that contain them won't be hinted barren. We do this because
    # the player may have multiple paths to beat the seed. So if we only used non-path locations, we may hint at all
    # paths as barren (since one particular path is not strictly required).
    # Technically, this is an overestimate (a superset) of actual barren locations, but it should suffice.
    junk_items = self.determine_junk_items()
    
    # We don't want to have barren/always hints overlap if hints are on.
    # For instance, consider a Ganon's Tower always hint. If you get that hint and a barren hint for Ganon's Tower, it's
    # effectively the same hint. However, if there's a Blue Chu Jelly hint, a Windfall barren hint would still be
    # helpful since Green Chu Jelly is at least another check on Windfall.
    always_hint_locations = []
    if self.use_always_hints:
      always_hint_locations = list(filter(
        lambda location_name: location_name in self.location_hints
        and self.location_hints[location_name]["Type"] == "Always",
        progress_locations,
      ))
    
    # Initialize possibly-required zones to all logical zones in this seed.
    # `possibly_required_zones` contains a mapping of zones -> possibly-required items.
    # `possibly_required_zones_no_always` contains a mapping of zones with always locations ignored -> possibly-required items.
    possibly_required_zones = {}
    possibly_required_zones_no_always = {}
    for location_name in progress_locations:
      zone_name, specific_location_name = self.logic.split_location_name_by_zone(location_name)
      
      # Consider dungeons as a separate zone.
      key_name = ""
      if zone_name in self.logic.DUNGEON_NAMES.values():
        if location_name == "Tower of the Gods - Sunken Treasure":
          key_name = "Tower of the Gods Sector"
        else:
          key_name = zone_name
      else:
        entrance_zone = self.get_entrance_zone(location_name)
        key_name = entrance_zone
      
      possibly_required_zones[key_name] = set()
      if location_name not in always_hint_locations:
        possibly_required_zones_no_always[key_name] = set()
    
    # Loop through all progress locations, recording only possibly-required items in our dictionary.
    for location_name in progress_locations:
      item_name = self.logic.done_item_locations[location_name]
      if location_name not in self.rando.race_mode_required_locations and item_name not in junk_items:
        zone_name, specific_location_name = self.logic.split_location_name_by_zone(location_name)
        
        # Consider dungeons as a separate zone.
        if zone_name in self.logic.DUNGEON_NAMES.values():
          if location_name == "Tower of the Gods - Sunken Treasure":
            possibly_required_zones["Tower of the Gods Sector"].add(item_name)
          else:
            possibly_required_zones[zone_name].add(item_name)
        else:
          entrance_zone = self.get_entrance_zone(location_name)
          possibly_required_zones[entrance_zone].add(item_name)
        
        # Include dungeon-related mail with its dungeon, in addition to Mailbox.
        if location_name == "Mailbox - Letter from Baito":
          possibly_required_zones["Earth Temple"].add(item_name)
          entrance_zone = self.get_entrance_zone("Earth Temple - Jalhalla Heart Container")
          if entrance_zone in possibly_required_zones:
            possibly_required_zones[entrance_zone].add(item_name)
        if location_name == "Mailbox - Letter from Orca":
          possibly_required_zones["Forbidden Woods"].add(item_name)
          entrance_zone = self.get_entrance_zone("Forbidden Woods - Kalle Demos Heart Container")
          if entrance_zone in possibly_required_zones:
            possibly_required_zones[entrance_zone].add(item_name)
        if location_name == "Mailbox - Letter from Aryll" or location_name == "Mailbox - Letter from Tingle":
          possibly_required_zones["Forsaken Fortress"].add(item_name)
    
    # The zones with zero possibly-required items makes up our initial set of barren zones.
    # We also check whether there are any non-always hinted locations there. If not, then don't hint at that zone since
    # it'd be covered already by the always hint(s).
    barren_zones = list(filter(
      lambda x: x[0] in possibly_required_zones_no_always and len(x[1]) == 0,
      possibly_required_zones.items()
    ))
    barren_zones = set(zone_name for zone_name, empty_set in barren_zones)
    
    # Prevent the entrances of possibly-required dungeons from being hinted at as barren.
    possibly_required_dungeons = list(filter(
      lambda x: len(x[1]) != 0
      and x[0] in self.logic.DUNGEON_NAMES.values(),
      possibly_required_zones.items(),
    ))
    for dungeon_name, items_set in possibly_required_dungeons:
      if dungeon_name == "Dragon Roost Cavern":
        entrance_zone = self.get_entrance_zone("Dragon Roost Cavern - Gohma Heart Container")
        barren_zones.discard(entrance_zone)
      if dungeon_name == "Forbidden Woods":
        entrance_zone = self.get_entrance_zone("Forbidden Woods - Kalle Demos Heart Container")
        barren_zones.discard(entrance_zone)
      if dungeon_name == "Tower of the Gods":
        entrance_zone = self.get_entrance_zone("Tower of the Gods - Gohdan Heart Container")
        barren_zones.discard(entrance_zone)
      if dungeon_name == "Earth Temple":
        entrance_zone = self.get_entrance_zone("Earth Temple - Jalhalla Heart Container")
        barren_zones.discard(entrance_zone)
      if dungeon_name == "Wind Temple":
        entrance_zone = self.get_entrance_zone("Wind Temple - Molgera Heart Container")
        barren_zones.discard(entrance_zone)
    
    # Remove race-mode banned dungeons from being hinted at as barren.
    if self.options.get("race_mode"):
      race_mode_banned_dungeons = set(self.logic.DUNGEON_NAMES.values()) - set(self.rando.race_mode_required_dungeons)
      barren_zones = barren_zones - race_mode_banned_dungeons
    
    # Return the list of barren zones sorted to maintain consistent ordering.
    return list(sorted(barren_zones))
  
  def get_barren_hint(self, unhinted_zones, zone_weights):
    # If there are no hintable locations, return `None`.
    if len(unhinted_zones) == 0:
      return None
    
    # Remove a barren zone at random from the list, using the weights provided.
    zone_name = self.rando.rng.choices(unhinted_zones, weights=zone_weights)[0]
    unhinted_zones.remove(zone_name)
    
    return Hint(HintType.BARREN, zone_name)
  
  
  def filter_legal_item_hint(self, location_name, progress_locations, previously_hinted_locations):
    return (
      # Don't hint at non-progress items.
      self.logic.done_item_locations[location_name] in self.logic.all_progress_items and
      
      # Don't hint at item in non-progress locations.
      location_name in progress_locations and
      
      # Don't hint at dungeon maps and compasses, and don't hint at dungeon keys when key-lunacy is not enabled.
      (self.options.get("keylunacy") or not self.logic.is_dungeon_item(self.logic.done_item_locations[location_name])) and
      
      # You already know which boss locations have a required item and which don't in race mode by looking at the sea chart.
      location_name not in self.rando.race_mode_required_locations and
      
      # Remove locations that are included in always hints.
      not (location_name in self.location_hints and self.location_hints[location_name]["Type"] == "Always") and
      
      # Remove locations in race-mode banned dungeons.
      location_name not in self.rando.race_mode_banned_locations and
      
      # Remove locations for items that were previously hinted.
      location_name not in previously_hinted_locations
    )
  
  def get_legal_item_hints(self, progress_locations, hinted_barren_zones, previously_hinted_locations):
    # Helper function to build a list of locations which may be hinted as item hints in this seed.
    
    # Filter out locations which are invalid to be hinted at for item hints.
    hintable_locations = list(filter(lambda location_name: self.filter_legal_item_hint(
      location_name, progress_locations, previously_hinted_locations), self.logic.done_item_locations.keys()))
    
    # Remove locations in hinted barren areas.
    new_hintable_locations = []
    barrens = [hint.place for hint in hinted_barren_zones]
    for location_name in hintable_locations:
      # Catch Mailbox cases.
      if (
          (location_name == "Mailbox - Letter from Baito" and "Earth Temple" in barrens)
          or (location_name == "Mailbox - Letter from Orca" and "Forbidden Woods" in barrens)
          or (location_name == "Mailbox - Letter from Aryll" and "Forsaken Fortress" in barrens)
          or (location_name == "Mailbox - Letter from Tingle" and "Forsaken Fortress" in barrens)
      ):
        continue
      
      # Catch locations which are hinted at in barren dungeons.
      zone_name, specific_location_name = self.logic.split_location_name_by_zone(location_name)
      if zone_name in self.logic.DUNGEON_NAMES.values() and zone_name in barrens:
        continue
      
      # Catch locations which are hinted at in barren zones.
      entrance_zone = self.get_entrance_zone(location_name)
      if entrance_zone not in barrens:
        new_hintable_locations.append(location_name)
    
    return new_hintable_locations
  
  def get_item_hint(self, hintable_locations):
    # If there are no hintable locations, return `None`.
    if len(hintable_locations) == 0:
      return None
    
    # Pick a location at which to hint at random.
    location_name = self.rando.rng.choice(hintable_locations)
    hintable_locations.remove(location_name)
    
    item_name = self.logic.done_item_locations[location_name]
    entrance_zone = self.get_entrance_zone(location_name)
    
    # Simplify entrance zone name
    if entrance_zone == "Tower of the Gods Sector":
      entrance_zone = "Tower of the Gods"
    
    return Hint(HintType.ITEM, entrance_zone, item_name), location_name
  
  
  def get_legal_location_hints(self, progress_locations, hinted_barren_zones, previously_hinted_locations):
    # Helper function to build a list of locations which may be hinted as location hints in this seed.
    
    hintable_locations = list(filter(lambda loc: loc in self.location_hints.keys(), progress_locations))
    
    # Identify valid always hints for this seed.
    always_hintable_locations = list(filter(lambda loc: self.location_hints[loc]["Type"] == "Always", hintable_locations))
    # The remaining locations are potential sometimes hints.
    hintable_locations = list(filter(lambda loc: self.location_hints[loc]["Type"] == "Sometimes", hintable_locations))
    
    # If we're not using always hints, consider them as sometimes hints instead.
    if not self.use_always_hints:
      hintable_locations += always_hintable_locations
      always_hintable_locations = []
    
    # Remove locations in race-mode banned dungeons.
    hintable_locations = list(filter(lambda location_name: location_name not in self.rando.race_mode_banned_locations, hintable_locations))
    
    # Remove locations for items that were previously hinted.
    hintable_locations = list(filter(lambda loc: loc not in previously_hinted_locations, hintable_locations))
    
    # Remove locations in hinted barren areas.
    sometimes_hintable_locations = []
    barrens = [hint.place for hint in hinted_barren_zones]
    for location_name in hintable_locations:
      # Catch Mailbox cases.
      if (
          (location_name == "Mailbox - Letter from Baito" and "Earth Temple" in barrens)
          or (location_name == "Mailbox - Letter from Orca" and "Forbidden Woods" in barrens)
          or (location_name == "Mailbox - Letter from Aryll" and "Forsaken Fortress" in barrens)
          or (location_name == "Mailbox - Letter from Tingle" and "Forsaken Fortress" in barrens)
      ):
        continue
      
      # Catch locations which are hinted at in barren dungeons.
      zone_name, specific_location_name = self.logic.split_location_name_by_zone(location_name)
      if zone_name in self.logic.DUNGEON_NAMES.values() and zone_name in barrens:
        continue
      
      # Catch locations which are hinted at in barren zones.
      entrance_zone = self.get_entrance_zone(location_name)
      if entrance_zone not in barrens:
        sometimes_hintable_locations.append(location_name)
    
    return always_hintable_locations, sometimes_hintable_locations
  
  def get_location_hint(self, hintable_locations):
    # If there are no hintable locations, return `None`.
    if len(hintable_locations) == 0:
      return None
    
    # Pick a location at which to hint at random.
    location_name = self.rando.rng.choice(hintable_locations)
    hintable_locations.remove(location_name)
    
    # Apply cryptic text to the location name, unless the clearer hints option is selected.
    item_name = self.logic.done_item_locations[location_name]
    item_name = Hints.get_clearer_item_name(item_name)
    item_name = tweaks.add_article_before_item_name(item_name)
    if not self.clearer_hints:
      location_name = self.location_hints[location_name]["Text"]
    
    return Hint(HintType.LOCATION, location_name, item_name)
  
  
  def generate_octo_fairy_hint(self):
    # Get an item hint for a random progress item.
    # Note that this hint is completely independant of all other hints.
    progress_locations, non_progress_locations = self.logic.get_progress_and_non_progress_locations()
    hintable_locations = self.get_legal_item_hints(progress_locations, [], [])
    if len(hintable_locations) == 0:
      raise Exception("No valid items to give hints for")
    
    item_hint, location_name = self.get_item_hint(hintable_locations)
    # We don't want this Great Fairy to hint at her own item.
    if location_name == "Two-Eye Reef - Big Octo Great Fairy":
      item_hint, location_name = self.get_item_hint(hintable_locations)
    
    # Apply cryptic text, unless the clearer hints option is selected.
    if self.clearer_hints:
      item_hint.reward = Hints.get_clearer_item_name(item_hint.reward)
      item_hint.reward = tweaks.add_article_before_item_name(item_hint.reward)
    else:
      item_hint.reward = self.progress_item_hints[Hints.get_hint_item_name(item_hint.reward)]
      item_hint.place = self.zone_name_hints[item_hint.place]
    
    return item_hint
  
  def generate_savage_labyrinth_hints(self):
    # Get an item hint for the two checks in Savage Labyrinth.
    floor_30_item_name = self.logic.done_item_locations["Outset Island - Savage Labyrinth - Floor 30"]
    floor_50_item_name = self.logic.done_item_locations["Outset Island - Savage Labyrinth - Floor 50"]
    
    floor_30_is_progress = (floor_30_item_name in self.logic.all_progress_items)
    floor_50_is_progress = (floor_50_item_name in self.logic.all_progress_items)
    
    floor_30_hint = None
    if floor_30_is_progress:
      # Apply cryptic text, unless the clearer hints option is selected.
      if self.clearer_hints:
        floor_30_item_name = Hints.get_clearer_item_name(floor_30_item_name)
        floor_30_item_name = tweaks.add_article_before_item_name(floor_30_item_name)
      else:
        if not floor_30_item_name in self.progress_item_hints:
          raise Exception("Could not find progress item hint for item: %s" % floor_30_item_name)
        floor_30_item_name = self.progress_item_hints[Hints.get_hint_item_name(floor_30_item_name)]
      
      floor_30_hint = Hint(HintType.ITEM, None, floor_30_item_name)
    
    floor_50_hint = None
    if floor_50_is_progress:
      # Apply cryptic text, unless the clearer hints option is selected.
      if self.clearer_hints:
        floor_50_item_name = Hints.get_clearer_item_name(floor_50_item_name)
        floor_50_item_name = tweaks.add_article_before_item_name(floor_50_item_name)
      else:
        if not floor_50_item_name in self.progress_item_hints:
          raise Exception("Could not find progress item hint for item: %s" % floor_50_item_name)
        floor_50_item_name = self.progress_item_hints[Hints.get_hint_item_name(floor_50_item_name)]
      
      floor_50_hint = Hint(HintType.ITEM, None, floor_50_item_name)
    
    return floor_30_hint, floor_50_hint
  
  def generate_hints(self):
    # Create a mapping for chart name -> sunken treasure
    self.chart_name_to_sunken_treasure = self.build_sunken_treasure_mapping()
    
    # Build of list of progress locations for this seed.
    progress_locations, non_progress_locations = self.logic.get_progress_and_non_progress_locations()
    
    # Get all entrance zones for progress locations in this seed.
    all_world_areas = []
    for location_name in progress_locations:
      if self.logic.is_dungeon_location(location_name):
        zone_name, specific_location_name = self.logic.split_location_name_by_zone(location_name)
        all_world_areas.append(zone_name)
      else:
        all_world_areas.append(self.get_entrance_zone(location_name))
    
    # Get a counter for the number of locations associated with each zone, used for weighing.
    location_counter = Counter(all_world_areas)
    
    # Determine which locations are required for each path goal.
    # Items are implicitly referred to by their location to handle duplicate item names (i.e., progressive items and
    # small keys). Basically, we remove the item from that location and see if the path goal is still achievable. If
    # not, then we consider the item as required.
    required_locations_for_paths = {}
    if self.max_path_hints > 0:
      required_locations_for_paths = self.get_required_locations_for_paths()
    
    # Generate path hints.
    # We hint at max `self.max_path_hints` zones at random. We start by hinted each of the race mode dungeons once.
    # After that, we repeatedly select a path goal at random and use that to form another hint. Zones are weighted by
    # the number of required locations at that zone. The more required locations, the more likely that zone will be
    # chosen.
    dungeon_paths = self.rando.race_mode_required_dungeons.copy()
    self.rando.rng.shuffle(dungeon_paths)
    
    # If race mode is on, then remove items that are hinted on the path to a race mode dungeon from paths to Hyrule and
    # Ganondorf. This way, the path to the race mode dungeon takes hint priority for that item.
    if self.max_path_hints > 0:
      for dungeon_name in dungeon_paths:
        for item_tuple in required_locations_for_paths[dungeon_name]:
          if item_tuple in required_locations_for_paths["Hyrule"]:
            required_locations_for_paths["Hyrule"].remove(item_tuple)
          if item_tuple in required_locations_for_paths["Ganon's Tower"]:
            required_locations_for_paths["Ganon's Tower"].remove(item_tuple)
    
    # Likewise, remove items that are hinted on the path to Hyrule from the path to Ganondorf. This way, the path to
    # Hyrule takes hint priority over the path to Ganondorf for that item.
    if self.max_path_hints > 0:
      for item_tuple in required_locations_for_paths["Hyrule"]:
        if item_tuple in required_locations_for_paths["Ganon's Tower"]:
          required_locations_for_paths["Ganon's Tower"].remove(item_tuple)
    
    hinted_path_zones = []
    previously_hinted_locations = []
    
    # Generate a path hint for each race-mode dungeon.
    for dungeon_name in dungeon_paths:
      # If there are no hintable locations for path hints, skip to barren hints.
      if len(required_locations_for_paths) == 0:
        break
      
      if len(hinted_path_zones) < self.max_path_hints:
        path_hint, location_name = self.get_path_hint(required_locations_for_paths[dungeon_name], previously_hinted_locations, dungeon_name)
        
        # Unable to generate a path hint for the dungeon, so remove path goal and move on to the next.
        if path_hint is None:
          del required_locations_for_paths[dungeon_name]
          continue
        
        # Remove locations that are hinted in always hints from being hinted path.
        if not self.use_always_hints or (location_name not in self.location_hints or self.location_hints[location_name]["Type"] != "Always"):
          # Apply cryptic text, unless the clearer hints option is selected.
          if not self.clearer_hints:
            path_hint.place = self.zone_name_hints[path_hint.place]
          
          hinted_path_zones.append(path_hint)
          previously_hinted_locations.append(location_name)
    
    while len(required_locations_for_paths) > 0 and len(hinted_path_zones) < self.max_path_hints:
      path_name = self.rando.rng.choice(list(required_locations_for_paths.keys()))
      path_hint, location_name = self.get_path_hint(required_locations_for_paths[path_name], previously_hinted_locations, path_name)
      
      # Unable to generate a path hint for the dungeon, so remove path goal.
      if path_hint is None:
        del required_locations_for_paths[path_name]
      else:
        # Remove locations that are hinted in always hints from being hinted path.
        if not self.use_always_hints or (location_name not in self.location_hints or self.location_hints[location_name]["Type"] != "Always"):
          # Apply cryptic text, unless the clearer hints option is selected.
          if not self.clearer_hints:
            path_hint.place = self.zone_name_hints[path_hint.place]
          
          hinted_path_zones.append(path_hint)
          previously_hinted_locations.append(location_name)
    
    # Generate barren hints.
    # We select at most `self.max_barren_hints` zones at random to hint as barren. Barren zones are weighted by the
    # square root of the number of locations at that zone.
    unhinted_barren_zones = self.get_barren_zones(progress_locations)
    hinted_barren_zones = []
    while len(unhinted_barren_zones) > 0 and len(hinted_barren_zones) < self.max_barren_hints:
      # Weight each barren zone by the square root of the number of locations there.
      zone_weights = [sqrt(location_counter[zone]) for zone in unhinted_barren_zones]
      
      barren_hint = self.get_barren_hint(unhinted_barren_zones, zone_weights)
      if barren_hint is not None:
        # Apply cryptic text, unless the clearer hints option is selected.
        if not self.clearer_hints:
          barren_hint.place = self.zone_name_hints[barren_hint.place]
        
        hinted_barren_zones.append(barren_hint)
    
    # Generate item hints.
    # We select at most `self.max_item_hints` items at random to hint at. We do not want to hint at items already
    # covered by the path hints, nor do we want to hint at items in barren-hinted locations.
    hintable_locations = self.get_legal_item_hints(progress_locations, hinted_barren_zones, previously_hinted_locations)
    
    hinted_item_locations = []
    while len(hintable_locations) > 0 and len(hinted_item_locations) < self.max_item_hints:
      item_hint, location_name = self.get_item_hint(hintable_locations)
      
      # Apply cryptic text, unless the clearer hints option is selected.
      if self.clearer_hints:
        item_hint.reward = Hints.get_clearer_item_name(item_hint.reward)
        item_hint.reward = tweaks.add_article_before_item_name(item_hint.reward)
      else:
        item_hint.reward = self.progress_item_hints[Hints.get_hint_item_name(item_hint.reward)]
        item_hint.place = self.zone_name_hints[item_hint.place]
      
      hinted_item_locations.append(item_hint)
      previously_hinted_locations.append(location_name)
    
    # Generate location hints.
    # We try to generate location hints until we get to `self.total_num_hints` total hints, but if there are not enough
    # valid hintable locations, then we have no choice but to return less than the desired amount of hints.
    always_hintable_locations, sometimes_hintable_locations = self.get_legal_location_hints(progress_locations, hinted_barren_zones, previously_hinted_locations)
    hinted_locations = []
    remaining_hints_desired = self.total_num_hints - len(hinted_path_zones) - len(hinted_barren_zones) - len(hinted_item_locations)
    
    # Start by exhausting the list of always hints.
    while len(always_hintable_locations) > 0 and remaining_hints_desired > 0:
      remaining_hints_desired -= 1
      location_hint = self.get_location_hint(always_hintable_locations)
      hinted_locations.append(location_hint)
    
    # Fill out the remaining hint slots with sometimes hints.
    while len(sometimes_hintable_locations) > 0 and remaining_hints_desired > 0:
      remaining_hints_desired -= 1
      location_hint = self.get_location_hint(sometimes_hintable_locations)
      hinted_locations.append(location_hint)
    
    return hinted_path_zones + hinted_barren_zones + hinted_item_locations + hinted_locations
