import os
from collections import Counter, deque, OrderedDict
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
  def __init__(self, type: HintType, is_cryptic, place, reward=None):
    self.type = type
    self.is_cryptic = is_cryptic
    self.place = place
    self.reward = reward
  
  @property
  def formatted_place(self):
    if not self.is_cryptic:
      return self.place
    
    match self.type:
      case HintType.PATH | HintType.BARREN | HintType.ITEM:
        return HintManager.cryptic_zone_hints[self.place]
      case HintType.LOCATION:
        return HintManager.location_hints[self.place]["Text"]
      case _:
        raise NotImplementedError
  
  @property
  def formatted_reward(self):
    match self.type:
      case HintType.PATH | HintType.BARREN:
        return self.reward
      case HintType.ITEM:
        if self.is_cryptic:
          return HintManager.cryptic_item_hints[HintManager.get_hint_item_name(self.reward)]
        else:
          return HintManager.get_formatted_item_name(self.reward)
      case HintType.LOCATION:
        # Never use cryptic item names for location hints.
        return HintManager.get_formatted_item_name(self.reward)
      case _:
        raise NotImplementedError
  
  def __str__(self):
    suffix = ", (CRYPTIC)" if self.is_cryptic else ""
    return "<HINT: %s, (%s, %s)%s>" % (self.type.name, self.formatted_place, self.formatted_reward, suffix)
  
  def __repr__(self):
    return "Hint(%s, %s, %s, %s)" % (str(self.type), repr(self.is_cryptic), repr(self.place), repr(self.reward))


class HintManager:
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
  
  cryptic_item_hints = None
  cryptic_zone_hints = None
  location_hints = None
  
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
    
    self.cryptic_hints = self.options.get("cryptic_hints")
    self.prioritize_remote_hints = self.options.get("prioritize_remote_hints")
    
    HintManager.load_hint_text_files()
    
    # Validate location names in location hints file.
    for location_name in self.location_hints:
      assert location_name in rando.logic.item_locations
    
    # Define a dictionary mapping charts to their sunken treasure.
    # This will be used to check whether or not the chart leads to a junk item. If so, the chart itself can be
    # considered junk.
    self.chart_name_to_sunken_treasure = {}
  
  @staticmethod
  def load_hint_text_files():
    if HintManager.cryptic_item_hints and HintManager.cryptic_zone_hints and HintManager.location_hints:
      return
    with open(os.path.join(DATA_PATH, "progress_item_hints.txt"), "r") as f:
      HintManager.cryptic_item_hints = yaml.safe_load(f)
    with open(os.path.join(DATA_PATH, "zone_name_hints.txt"), "r") as f:
      HintManager.cryptic_zone_hints = yaml.safe_load(f)
    with open(os.path.join(DATA_PATH, "location_hints.txt"), "r") as f:
      HintManager.location_hints = yaml.safe_load(f)
  
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
  def get_formatted_hint_text(hint: Hint, prefix="They say that ", suffix=".", delay=30):
    place = hint.formatted_place
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
        % (prefix, place_preposition, place, hint.formatted_reward, suffix)
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
        % (prefix, place, hint.formatted_reward, suffix)
      )
    elif hint.type == HintType.ITEM:
      copula = "is"
      if hint.formatted_reward in ["Power Bracelets", "Iron Boots", "Bombs"]:
        copula = "are"
      hint_string = (
        "%s\\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00} %s located in \\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00}%s"
        % (prefix, hint.formatted_reward, copula, place, suffix)
      )
    else:
      hint_string = ""
    
    # Add a wait command (delay) to prevent the player from skipping over the hint accidentally.
    delay = max(0, min(0xFFFF, delay)) # Clamp within valid range.
    if delay > 0:
      hint_string += "\\{1A 07 00 00 07 %02X %02X}" % (delay >> 8, delay & 0xFF)
    
    return hint_string
  
  @staticmethod
  def get_formatted_item_name(item_name):
    if item_name.endswith("Small Key"):
      short_dungeon_name = item_name.split(" Small Key")[0]
      dungeon_name = Logic.DUNGEON_NAMES[short_dungeon_name]
      item_name = "%s small key" % dungeon_name
    elif item_name.endswith("Big Key"):
      short_dungeon_name = item_name.split(" Big Key")[0]
      dungeon_name = Logic.DUNGEON_NAMES[short_dungeon_name]
      item_name = "%s Big Key" % dungeon_name
    elif item_name.endswith("Dungeon Map"):
      short_dungeon_name = item_name.split(" Dungeon Map")[0]
      dungeon_name = Logic.DUNGEON_NAMES[short_dungeon_name]
      item_name = "%s Dungeon Map" % dungeon_name
    elif item_name.endswith("Compass"):
      short_dungeon_name = item_name.split(" Compass")[0]
      dungeon_name = Logic.DUNGEON_NAMES[short_dungeon_name]
      item_name = "%s Compass" % dungeon_name
    
    item_name = tweaks.add_article_before_item_name(item_name)
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
    if hinted_location == "Tower of the Gods - Sunken Treasure":
      # Special case: if location is Tower of the Gods - Sunken Treasure, use "Tower of the Gods Sector" as the hint.
      hint_zone = "Tower of the Gods Sector"
    elif self.logic.is_dungeon_location(hinted_location):
      # If it's a dungeon, use the dungeon name.
      hint_zone = zone_name
    else:
      # Otherwise, use the entrance zone name.
      hint_zone = entrance_zone
    
    path_hint = Hint(HintType.PATH, self.cryptic_hints, hint_zone, self.DUNGEON_NAME_TO_BOSS_NAME[path_name])
    
    return path_hint, hinted_location
  
  
  def get_barren_zones(self, progress_locations, hinted_remote_locations):
    # Helper function to build a list of barren zones in this seed.
    # The list includes only zones which are allowed to be hinted at as barren.
    
    # To start, exclude locations in non race mode dungeons from being considered as a progress location.
    progress_locations = set(progress_locations) - set(self.rando.race_mode_banned_locations)
    
    # Next, create a dictionary mapping all progress items to their randomized locations. The values in this dictionary
    # will be lists since an item can be in multiple locations if it is progressive or a small key.
    progress_items = {}
    for location_name in progress_locations:
      item_name = self.logic.done_item_locations[location_name]
      if item_name in self.rando.logic.all_progress_items:
        if item_name in progress_items:
          progress_items[item_name].append(location_name)
        else:
          progress_items[item_name] = [location_name]
    
    # Next, we build a list of items that may be used to beat the seed. These items include hard-required items, such as
    # Triforce shards, but also items that might be used. For example, if there is a choice between which wallet to get,
    # both will be included in this list. As another example, if there is a choice between getting Bombs or Power
    # Bracelets to beat the seed, both will be included in this list. We do this by going backward from the 'Can Reach
    # and Defeat Ganondorf" requirement and checking items needed to fulfill that requirement. We then use a queue to
    # check item requirements to get those items, and so on.
    self.path_logic.load_simulated_playthrough_state(self.path_logic_initial_state)
    items_needed = deque(self.path_logic.get_item_names_by_req_name("Can Reach and Defeat Ganondorf"))
    items_checked = []
    useful_locations = set()
    while len(items_needed) > 0:
      # Dequeue one item from the queue.
      item_name = items_needed.popleft()
      
      # Don't consider the same item more than once or items which are not in the list of randomized progress items.
      if item_name in items_checked or item_name not in progress_items:
        continue
      
      # Don't consider dungeon keys when keylunacy is not enabled.
      if self.logic.is_dungeon_item(item_name) and not self.options.get("keylunacy"):
          continue
      
      items_checked.append(item_name)
      
      # Consider all instances of this item, even if those extra copies might not be required.
      item_locations = progress_items[item_name]
      for location_name in item_locations:
        requirement_name = "Can Access Other Location \"%s\"" % location_name
        other_items_needed = self.path_logic.get_item_names_by_req_name(requirement_name)
        items_needed.extend(other_items_needed)
      
      # The set of "useful locations" is the set of all locations which contain these "useful" items.
      useful_locations |= set(item_locations)
    
    # Subtracting the set of useful locations from the set of progress locations gives us our set of barren locations.
    barren_locations = set(progress_locations) - useful_locations
    
    # Since we hint at zones as barren, we next construct a set of zones which contain at least one useful item.
    zones_with_useful_locations = set()
    for location_name in useful_locations:
      # Don't consider race mode dungeon bosses, as those are implicity required.
      if location_name in self.rando.race_mode_required_locations:
        continue
      
      zones_with_useful_locations.add(self.get_entrance_zone(location_name))
      # For dungeon locations, both the dungeon and its entrance should be considered useful.
      if self.logic.is_dungeon_location(location_name):
        zone_name, specific_location_name = self.logic.split_location_name_by_zone(location_name)
        zones_with_useful_locations.add(zone_name)
      
      # Include dungeon-related mail with its dungeon, in addition to Mailbox.
      if location_name == "Mailbox - Letter from Baito":
        zones_with_useful_locations.add("Earth Temple")
        zones_with_useful_locations.add(self.get_entrance_zone("Earth Temple - Jalhalla Heart Container"))
      if location_name == "Mailbox - Letter from Orca":
        zones_with_useful_locations.add("Forbidden Woods")
        zones_with_useful_locations.add(self.get_entrance_zone("Forbidden Woods - Kalle Demos Heart Container"))
      if location_name == "Mailbox - Letter from Aryll" or location_name == "Mailbox - Letter from Tingle":
        zones_with_useful_locations.add("Forsaken Fortress")
    
    # Now, we do the same with barren locations, identifying which zones have barren locations.
    zones_with_barren_locations = set()
    for location_name in barren_locations:
      # Don't consider locations hinted through remote location hints, as those are explicity barren.
      if location_name in hinted_remote_locations:
        continue
      
      zones_with_barren_locations.add(self.get_entrance_zone(location_name))
      # For dungeon locations, both the dungeon and its entrance should be considered barren.
      if self.logic.is_dungeon_location(location_name):
        zone_name, specific_location_name = self.logic.split_location_name_by_zone(location_name)
        zones_with_barren_locations.add(zone_name)
      
      # Include dungeon-related mail with its dungeon, in addition to Mailbox.
      if location_name == "Mailbox - Letter from Baito":
        zones_with_barren_locations.add("Earth Temple")
        zones_with_barren_locations.add(self.get_entrance_zone("Earth Temple - Jalhalla Heart Container"))
      if location_name == "Mailbox - Letter from Orca":
        zones_with_barren_locations.add("Forbidden Woods")
        zones_with_barren_locations.add(self.get_entrance_zone("Forbidden Woods - Kalle Demos Heart Container"))
      if location_name == "Mailbox - Letter from Aryll" or location_name == "Mailbox - Letter from Tingle":
        zones_with_barren_locations.add("Forsaken Fortress")
    
    # Finally, the difference between the zones with barren locations and the zones with useful locations gives us our
    # set of hintable barren zones.
    barren_zones = zones_with_barren_locations - zones_with_useful_locations
    
    # Return the list of barren zones sorted to maintain consistent ordering.
    return sorted(barren_zones)
  
  def get_barren_hint(self, unhinted_zones, zone_weights):
    if len(unhinted_zones) == 0:
      return None
    
    # Remove a barren zone at random from the list, using the weights provided.
    zone_name = self.rando.rng.choices(unhinted_zones, weights=zone_weights)[0]
    unhinted_zones.remove(zone_name)
    
    barren_hint = Hint(HintType.BARREN, self.cryptic_hints, zone_name)
    
    return barren_hint
  
  
  def filter_out_hinted_barren_locations(self, hintable_locations, hinted_barren_zones):
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
      if self.logic.is_dungeon_location(location_name):
        zone_name, specific_location_name = self.logic.split_location_name_by_zone(location_name)
        if zone_name in barrens:
          continue
      
      # Catch locations which are hinted at in barren zones.
      entrance_zone = self.get_entrance_zone(location_name)
      if entrance_zone not in barrens:
        new_hintable_locations.append(location_name)
    
    return new_hintable_locations
  
  def check_is_legal_item_hint(self, location_name, progress_locations, previously_hinted_locations):
    item_name = self.logic.done_item_locations[location_name]
    
    # Don't hint at non-progress items.
    if item_name not in self.logic.all_progress_items:
      return False
    
    # Don't hint at item in non-progress locations.
    if location_name not in progress_locations:
      return False
    
    # Don't hint at dungeon keys when key-lunacy is not enabled.
    if self.logic.is_dungeon_item(item_name) and not self.options.get("keylunacy"):
      return False
    
    # You already know which boss locations have a required item and which don't in race mode by looking at the sea chart.
    if location_name in self.rando.race_mode_required_locations:
      return False
    
    # Remove locations in race-mode banned dungeons.
    if location_name in self.rando.race_mode_banned_locations:
      return False
    
    # Remove locations for items that were previously hinted.
    if location_name in previously_hinted_locations:
      return False
    
    return True
  
  def get_legal_item_hints(self, progress_locations, hinted_barren_zones, previously_hinted_locations):
    # Helper function to build a list of locations which may be hinted as item hints in this seed.
    
    # Filter out locations which are invalid to be hinted at for item hints.
    hintable_locations = [
      loc for loc in self.logic.done_item_locations
      if self.check_is_legal_item_hint(loc, progress_locations, previously_hinted_locations)
    ]
    
    new_hintable_locations = self.filter_out_hinted_barren_locations(hintable_locations, hinted_barren_zones)
    
    return new_hintable_locations
  
  def get_item_hint(self, hintable_locations):
    if len(hintable_locations) == 0:
      return None, None
    
    # Pick a location at which to hint at random.
    location_name = self.rando.rng.choice(hintable_locations)
    hintable_locations.remove(location_name)
    
    item_name = self.logic.done_item_locations[location_name]
    entrance_zone = self.get_entrance_zone(location_name)
    
    # Simplify entrance zone name
    if entrance_zone == "Tower of the Gods Sector":
      entrance_zone = "Tower of the Gods"
    
    item_hint = Hint(HintType.ITEM, self.cryptic_hints, entrance_zone, item_name)
    
    return item_hint, location_name
  
  
  def get_legal_location_hints(self, progress_locations, hinted_barren_zones, previously_hinted_locations):
    # Helper function to build a list of locations which may be hinted as location hints in this seed.
    
    hintable_locations = [loc for loc in progress_locations if loc in self.location_hints]
    
    # Identify valid remote hints for this seed.
    remote_hintable_locations = [loc for loc in hintable_locations if self.location_hints[loc]["Type"] == "Remote"]
    # The remaining locations are potential standard location hints.
    hintable_locations = [loc for loc in hintable_locations if self.location_hints[loc]["Type"] == "Standard"]
    
    # If we're not prioritizing remote hints, consider them as standard location hints instead.
    if not self.prioritize_remote_hints:
      hintable_locations += remote_hintable_locations
      remote_hintable_locations = []
    
    # Remove locations in race-mode banned dungeons.
    hintable_locations = [loc for loc in hintable_locations if loc not in self.rando.race_mode_banned_locations]
    
    # Remove locations for items that were previously hinted.
    hintable_locations = [loc for loc in hintable_locations if loc not in previously_hinted_locations]
    
    standard_hintable_locations = self.filter_out_hinted_barren_locations(hintable_locations, hinted_barren_zones)
    
    return remote_hintable_locations, standard_hintable_locations
  
  def get_location_hint(self, hintable_locations):
    if len(hintable_locations) == 0:
      return None
    
    # Pick a location at which to hint at random.
    location_name = self.rando.rng.choice(hintable_locations)
    hintable_locations.remove(location_name)
    
    item_name = self.logic.done_item_locations[location_name]
    
    location_hint = Hint(HintType.LOCATION, self.cryptic_hints, location_name, item_name)
    
    return location_hint, location_name
  
  
  def generate_octo_fairy_hint(self):
    # Get an item hint for a random progress item.
    # Note that this hint is completely independant of all other hints.
    progress_locations, non_progress_locations = self.logic.get_progress_and_non_progress_locations()
    hintable_locations = self.get_legal_item_hints(progress_locations, [], [])
    if "Two-Eye Reef - Big Octo Great Fairy" in hintable_locations:
      # We don't want this Great Fairy to hint at her own item.
      hintable_locations.remove("Two-Eye Reef - Big Octo Great Fairy")
    if len(hintable_locations) == 0:
      raise Exception("No valid items to give hints for")
    
    item_hint, location_name = self.get_item_hint(hintable_locations)
    
    return item_hint
  
  def generate_savage_labyrinth_hints(self):
    # Get an item hint for the two checks in Savage Labyrinth.
    floor_30_item_name = self.logic.done_item_locations["Outset Island - Savage Labyrinth - Floor 30"]
    floor_50_item_name = self.logic.done_item_locations["Outset Island - Savage Labyrinth - Floor 50"]
    
    floor_30_is_progress = (floor_30_item_name in self.logic.all_progress_items)
    floor_50_is_progress = (floor_50_item_name in self.logic.all_progress_items)
    
    floor_30_hint = None
    if floor_30_is_progress:
      floor_30_hint = Hint(HintType.ITEM, self.cryptic_hints, None, floor_30_item_name)
    
    floor_50_hint = None
    if floor_50_is_progress:
      floor_50_hint = Hint(HintType.ITEM, self.cryptic_hints, None, floor_50_item_name)
    
    return floor_30_hint, floor_50_hint
  
  def generate_hints(self):
    previously_hinted_locations = []
    
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
    
    # Generate remote location hints.
    # First, we generate remote location hints, up to the total amount that can be generated based on the settings, and
    # based on the number of location hints the user wishes to generate. We need to generate these first before any
    # other hint type.
    hinted_remote_locations = []
    if self.prioritize_remote_hints:
      remote_hintable_locations, standard_hintable_locations = self.get_legal_location_hints(progress_locations, [], [])
      while len(remote_hintable_locations) > 0 and len(hinted_remote_locations) < self.max_location_hints:
        location_hint, location_name = self.get_location_hint(remote_hintable_locations)
        
        hinted_remote_locations.append(location_hint)
        previously_hinted_locations.append(location_name)
    
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
    
    # Generate a path hint for each race-mode dungeon.
    hinted_path_zones = []
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
        
        # Remove locations that have already been hinted.
        if location_name not in previously_hinted_locations:
          hinted_path_zones.append(path_hint)
          previously_hinted_locations.append(location_name)
    
    while len(required_locations_for_paths) > 0 and len(hinted_path_zones) < self.max_path_hints:
      path_name = self.rando.rng.choice(list(required_locations_for_paths.keys()))
      path_hint, location_name = self.get_path_hint(required_locations_for_paths[path_name], previously_hinted_locations, path_name)
      
      # Unable to generate a path hint for the dungeon, so remove path goal.
      if path_hint is None:
        del required_locations_for_paths[path_name]
      else:
        # Remove locations that have already been hinted.
        if location_name not in previously_hinted_locations:
          hinted_path_zones.append(path_hint)
          previously_hinted_locations.append(location_name)
    
    # Generate barren hints.
    # We select at most `self.max_barren_hints` zones at random to hint as barren. Barren zones are weighted by the
    # square root of the number of locations at that zone.
    unhinted_barren_zones = self.get_barren_zones(progress_locations, [hint.place for hint in hinted_remote_locations])
    hinted_barren_zones = []
    while len(unhinted_barren_zones) > 0 and len(hinted_barren_zones) < self.max_barren_hints:
      # Weight each barren zone by the square root of the number of locations there.
      zone_weights = [sqrt(location_counter[zone]) for zone in unhinted_barren_zones]
      
      barren_hint = self.get_barren_hint(unhinted_barren_zones, zone_weights)
      if barren_hint is not None:
        hinted_barren_zones.append(barren_hint)
    
    # Generate item hints.
    # We select at most `self.max_item_hints` items at random to hint at. We do not want to hint at items already
    # covered by the path hints, nor do we want to hint at items in barren-hinted locations.
    hintable_locations = self.get_legal_item_hints(progress_locations, hinted_barren_zones, previously_hinted_locations)
    
    hinted_item_locations = []
    while len(hintable_locations) > 0 and len(hinted_item_locations) < self.max_item_hints:
      item_hint, location_name = self.get_item_hint(hintable_locations)
      
      hinted_item_locations.append(item_hint)
      previously_hinted_locations.append(location_name)
    
    # Generate standard location hints.
    # We try to generate location hints until we get to `self.total_num_hints` total hints, but if there are not enough
    # valid hintable locations, then we have no choice but to return less than the desired amount of hints.
    remote_hintable_locations, standard_hintable_locations = self.get_legal_location_hints(progress_locations, hinted_barren_zones, previously_hinted_locations)
    hinted_standard_locations = []
    remaining_hints_desired = self.total_num_hints - len(hinted_path_zones) - len(hinted_barren_zones) - len(hinted_item_locations) - len(hinted_remote_locations)
    
    # Fill out the remaining hint slots with standard location hints.
    while len(standard_hintable_locations) > 0 and remaining_hints_desired > 0:
      remaining_hints_desired -= 1
      location_hint, location_name = self.get_location_hint(standard_hintable_locations)
      
      hinted_standard_locations.append(location_hint)
      previously_hinted_locations.append(location_name)
    
    return hinted_path_zones + hinted_barren_zones + hinted_item_locations + hinted_remote_locations + hinted_standard_locations
