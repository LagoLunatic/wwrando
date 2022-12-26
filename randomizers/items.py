
import os
import re
from collections import OrderedDict

from fs_helpers import *

def randomize_items(self):
  print("Randomizing items...")
  
  if self.options.get("progression_dungeons") and self.options.get("race_mode"):
    randomize_boss_rewards(self)
  
  if not self.options.get("keylunacy"):
    randomize_dungeon_items(self)
  
  randomize_progression_items(self)
  
  # Place unique non-progress items.
  while self.logic.unplaced_nonprogress_items:
    accessible_undone_locations = self.logic.get_accessible_remaining_locations()
    
    item_name = self.rng.choice(self.logic.unplaced_nonprogress_items)
    
    possible_locations = self.logic.filter_locations_valid_for_item(accessible_undone_locations, item_name)
    
    if not possible_locations:
      raise Exception("No valid locations left to place non-progress items!")
    
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
    possible_items = self.logic.filter_items_valid_for_location(self.logic.unplaced_fixed_consumable_items, location_name)
    if len(possible_items) == 0:
      possible_items = self.logic.filter_items_valid_for_location(self.logic.duplicatable_consumable_items, location_name)
      if len(possible_items) == 0:
        raise Exception("No valid consumable items for location %s" % location_name)
    
    item_name = self.rng.choice(possible_items)
    self.logic.set_location_to_item(location_name, item_name)

def randomize_boss_rewards(self):
  # Try to generate dungeon boss reward locations until a valid set of locations is found.
  for i in range(50):
    if try_randomize_boss_rewards(self):
      return
  raise Exception("Cannot randomize boss rewards! Please try randomizing with a different seed.")

def try_randomize_boss_rewards(self):
  if not self.options.get("progression_dungeons"):
    raise Exception("Cannot randomize boss rewards when progress items are not allowed in dungeons.")
  
  boss_reward_items = []
  total_num_rewards = int(self.options.get("num_race_mode_dungeons"))
  
  unplaced_progress_items_degrouped = []
  for item_name in self.logic.unplaced_progress_items:
    if item_name in self.logic.progress_item_groups:
      unplaced_progress_items_degrouped += self.logic.progress_item_groups[item_name]
    else:
      unplaced_progress_items_degrouped.append(item_name)
  
  # Try to make all the rewards be Triforce Shards.
  # May not be possible if the player chose to start with too many shards.
  num_additional_rewards_needed = total_num_rewards
  triforce_shards = [
    item_name for item_name in unplaced_progress_items_degrouped
    if item_name.startswith("Triforce Shard ")
  ]
  self.rng.shuffle(triforce_shards)
  boss_reward_items += triforce_shards[0:num_additional_rewards_needed]
  
  # If we still need more rewards, use sword upgrades.
  # May still not fill up all 4 slots if the player starts with 8 shards and a sword.
  num_additional_rewards_needed = total_num_rewards - len(boss_reward_items)
  if num_additional_rewards_needed > 0:
    sword_upgrades = [
      item_name for item_name in unplaced_progress_items_degrouped
      if item_name == "Progressive Sword"
    ]
    boss_reward_items += sword_upgrades[0:num_additional_rewards_needed]
  
  # If we still need more rewards, use bow upgrades.
  # May still not fill up all 4 slots if the player starts with 8 shards and is in swordless mode.
  num_additional_rewards_needed = total_num_rewards - len(boss_reward_items)
  if num_additional_rewards_needed > 0:
    bow_upgrades = [
      item_name for item_name in unplaced_progress_items_degrouped
      if item_name == "Progressive Bow"
    ]
    boss_reward_items += bow_upgrades[0:num_additional_rewards_needed]
  
  possible_additional_rewards = ["Hookshot", "Progressive Shield", "Boomerang"]
  
  # If we STILL need more rewards, use the Hookshot, Mirror Shield, and Boomerang.
  num_additional_rewards_needed = total_num_rewards - len(boss_reward_items)
  if num_additional_rewards_needed > 0:
    additional_rewards = [
      item_name for item_name in unplaced_progress_items_degrouped
      if item_name in possible_additional_rewards
    ]
    boss_reward_items += additional_rewards[0:num_additional_rewards_needed]
  
  self.rng.shuffle(boss_reward_items)
  
  if len(boss_reward_items) != total_num_rewards:
    raise Exception("Number of boss reward items is incorrect: " + ", ".join(boss_reward_items))
  
  possible_boss_locations = [
    loc for loc in self.logic.remaining_item_locations
    if self.logic.item_locations[loc]["Original item"] == "Heart Container"
  ]
  
  if len(possible_boss_locations) != 6:
    raise Exception("Number of boss item locations is incorrect: " + ", ".join(possible_boss_locations))
  
  boss_reward_locations = OrderedDict()
  
  # Decide what reward item to place in each boss location.
  for item_name in boss_reward_items:    
    if self.dungeons_only_start and "Dragon Roost Cavern - Gohma Heart Container" in possible_boss_locations:
      location_name = "Dragon Roost Cavern - Gohma Heart Container"
    elif self.dungeons_only_start and "Forbidden Woods - Kalle Demos Heart Container" in possible_boss_locations:
      location_name = "Forbidden Woods - Kalle Demos Heart Container"
    else:
      location_name = self.rng.choice(possible_boss_locations)
    possible_boss_locations.remove(location_name)
    boss_reward_locations[location_name] = item_name
  
  # Verify that the dungeon boss rewards were placed in a way that allows them all to be accessible.
  locations_valid = validate_boss_reward_locations(self, boss_reward_locations)
  
  # If the dungeon boss reward locations are not valid, a new set of dungeon boss reward locations will be generated.
  if not locations_valid:
    return False
  
  # Remove any Triforce Shards we're about to use from the progress item group, and add them as ungrouped progress items instead.
  for group_name, group_item_names in self.logic.progress_item_groups.items():
    items_to_remove_from_group = [
      item_name for item_name in group_item_names
      if item_name in boss_reward_items
    ]
    for item_name in items_to_remove_from_group:
      self.logic.progress_item_groups[group_name].remove(item_name)
    if group_name in self.logic.unplaced_progress_items:
      for item_name in items_to_remove_from_group:
        self.logic.unplaced_progress_items.append(item_name)
    
    if len(self.logic.progress_item_groups[group_name]) == 0:
      if group_name in self.logic.unplaced_progress_items:
        self.logic.unplaced_progress_items.remove(group_name)
  
  for location_name, item_name in boss_reward_locations.items():
    self.logic.set_prerandomization_item_location(location_name, item_name)
    self.race_mode_required_locations.append(location_name)
    
    dungeon_name, _ = self.logic.split_location_name_by_zone(location_name)
    self.race_mode_required_dungeons.append(dungeon_name)
  
  banned_dungeons = []
  for boss_location_name in possible_boss_locations:
    dungeon_name, _ = self.logic.split_location_name_by_zone(boss_location_name)
    banned_dungeons.append(dungeon_name)
  
  for location_name in self.logic.item_locations:
    zone_name, _ = self.logic.split_location_name_by_zone(location_name)
    if self.logic.is_dungeon_location(location_name) and zone_name in banned_dungeons:
      self.race_mode_banned_locations.append(location_name)
    elif location_name == "Mailbox - Letter from Orca" and "Forbidden Woods" in banned_dungeons:
      self.race_mode_banned_locations.append(location_name)
    elif location_name == "Mailbox - Letter from Baito" and "Earth Temple" in banned_dungeons:
      self.race_mode_banned_locations.append(location_name)
    elif location_name == "Mailbox - Letter from Aryll" and "Forsaken Fortress" in banned_dungeons:
      self.race_mode_banned_locations.append(location_name)
    elif location_name == "Mailbox - Letter from Tingle" and "Forsaken Fortress" in banned_dungeons:
      self.race_mode_banned_locations.append(location_name)
  
  return True

def validate_boss_reward_locations(self, boss_reward_locations):
  boss_reward_items = list(boss_reward_locations.values())
  
  # Temporarily own every item that is not a dungeon boss reward.
  items_to_temporarily_add = self.logic.unplaced_progress_items.copy()
  
  for item_name in boss_reward_items:
    if item_name in items_to_temporarily_add:
      items_to_temporarily_add.remove(item_name)
  
  for item_name in items_to_temporarily_add:
    self.logic.add_owned_item_or_item_group(item_name)
  
  locations_valid = True
  temporary_boss_reward_items = []
  remaining_boss_reward_items = boss_reward_items.copy()
  remaining_boss_locations = list(boss_reward_locations.keys())
  
  while remaining_boss_reward_items:
    # Consider a dungeon boss reward to be accessible when every location in the dungeon is accessible.
    accessible_undone_locations = self.logic.get_accessible_remaining_locations()    
    inaccessible_dungeons = []
    for location_name in self.logic.remaining_item_locations:
      if self.logic.is_dungeon_location(location_name) and location_name not in accessible_undone_locations:
        dungeon_name, _ = self.logic.split_location_name_by_zone(location_name)
        inaccessible_dungeons.append(dungeon_name)
    
    newly_accessible_boss_locations = []
    for boss_location in remaining_boss_locations:
      dungeon_name, _ = self.logic.split_location_name_by_zone(boss_location)
      
      if dungeon_name not in inaccessible_dungeons:
        newly_accessible_boss_locations.append(boss_location)
    
    # If there are no more accessible dungeon boss rewards, consider the dungeon boss locations to be invalid.
    if not newly_accessible_boss_locations:
      locations_valid = False
      break
    
    # Temporarily own dungeon boss rewards that are now accessible.
    for location_name in newly_accessible_boss_locations:
      item_name = boss_reward_locations[location_name]
      if item_name in self.logic.unplaced_progress_items:
        self.logic.add_owned_item_or_item_group(item_name)
      temporary_boss_reward_items.append(item_name)
      remaining_boss_reward_items.remove(item_name)
      remaining_boss_locations.remove(location_name)
  
  # Remove temporarily owned items.
  for item_name in items_to_temporarily_add:
    self.logic.remove_owned_item_or_item_group(item_name)
  for item_name in temporary_boss_reward_items:
    if item_name in self.logic.currently_owned_items:
      self.logic.remove_owned_item_or_item_group(item_name)
  
  return locations_valid

def randomize_dungeon_items(self):
  # Places dungeon-specific items first so all the dungeon locations don't get used up by other items.
  
  # Temporarily add all items except for dungeon keys while we randomize them.
  items_to_temporarily_add = [
    item_name for item_name in (self.logic.unplaced_progress_items + self.logic.unplaced_nonprogress_items)
    if not self.logic.is_dungeon_item(item_name)
  ]
  for item_name in items_to_temporarily_add:
    self.logic.add_owned_item_or_item_group(item_name)
  
  if self.dungeons_only_start:
    # Choose a random location out of the 6 easiest locations to access in DRC.
    # This location will not have the big key, dungeon map, or compass on this seed. (But can still have small keys/non-dungeon items.)
    # This is to prevent a rare error in dungeons-only-start.
    self.drc_failsafe_location = self.rng.choice([
      "Dragon Roost Cavern - First Room",
      "Dragon Roost Cavern - Alcove With Water Jugs",
      "Dragon Roost Cavern - Boarded Up Chest",
      "Dragon Roost Cavern - Rat Room",
      "Dragon Roost Cavern - Rat Room Boarded Up Chest",
      "Dragon Roost Cavern - Bird's Nest",
    ])
  
  # Randomize small keys.
  small_keys_to_place = [
    item_name for item_name in (self.logic.unplaced_progress_items + self.logic.unplaced_nonprogress_items)
    if item_name.endswith(" Small Key")
  ]
  assert len(small_keys_to_place) > 0
  for item_name in small_keys_to_place:
    place_dungeon_item(self, item_name)
    self.logic.add_owned_item(item_name) # Temporarily add small keys to the player's inventory while placing them.
  
  # Randomize big keys.
  big_keys_to_place = [
    item_name for item_name in (self.logic.unplaced_progress_items + self.logic.unplaced_nonprogress_items)
    if item_name.endswith(" Big Key")
  ]
  assert len(big_keys_to_place) > 0
  for item_name in big_keys_to_place:
    place_dungeon_item(self, item_name)
    self.logic.add_owned_item(item_name) # Temporarily add big keys to the player's inventory while placing them.
  
  # Randomize dungeon maps and compasses.
  other_dungeon_items_to_place = [
    item_name for item_name in (self.logic.unplaced_progress_items + self.logic.unplaced_nonprogress_items)
    if item_name.endswith(" Dungeon Map")
    or item_name.endswith(" Compass")
  ]
  for item_name in other_dungeon_items_to_place:
    place_dungeon_item(self, item_name)
  
  # Remove the items we temporarily added.
  for item_name in items_to_temporarily_add:
    self.logic.remove_owned_item_or_item_group(item_name)
  for item_name in small_keys_to_place:
    self.logic.remove_owned_item(item_name)
  for item_name in big_keys_to_place:
    self.logic.remove_owned_item(item_name)

def place_dungeon_item(self, item_name):
  accessible_undone_locations = self.logic.get_accessible_remaining_locations()
  accessible_undone_locations = [
    loc for loc in accessible_undone_locations
    if loc not in self.logic.prerandomization_item_locations
  ]
  if not self.options.get("progression_tingle_chests"):
    accessible_undone_locations = [
      loc for loc in accessible_undone_locations
      if not "Tingle Chest" in self.logic.item_locations[loc]["Types"]
    ]
  possible_locations = self.logic.filter_locations_valid_for_item(accessible_undone_locations, item_name)
  
  if self.dungeons_only_start and item_name == "DRC Small Key":
    # If we're in a dungeons-only-start, we have to ban small keys from appearing in the path that sequence breaks the hanging platform.
    # A key you need to progress appearing there can cause issues that dead-end the item placement logic when there are no locations outside DRC for the randomizer to give you other items at.
    possible_locations = [
      loc for loc in possible_locations
      if not loc in ["Dragon Roost Cavern - Big Key Chest", "Dragon Roost Cavern - Tingle Statue Chest"]
    ]
  if self.dungeons_only_start and item_name in ["DRC Big Key", "DRC Dungeon Map", "DRC Compass"]:
    # If we're in a dungeons-only start, we have to ban dungeon items except small keys from appearing in all 6 of the 6 easiest locations to access in DRC.
    # If we don't do this, there is a small chance that those 6 locations will be filled with 3 small keys, the dungeon map, and the compass. The 4th small key will be in the path that sequence breaks the hanging platform, but there will be no open spots to put any non-dungeon items like grappling hook.
    # To prevent this specific problem, one location (chosen randomly) is not allowed to have these items at all in dungeons-only-start. It can still have small keys and non-dungeon items.
    possible_locations = [
      loc for loc in possible_locations
      if loc != self.drc_failsafe_location
    ]
  
  if not possible_locations:
    raise Exception("No valid locations left to place dungeon items!")
  
  location_name = self.rng.choice(possible_locations)
  self.logic.set_prerandomization_item_location(location_name, item_name)

def randomize_progression_items(self):
  accessible_undone_locations = self.logic.get_accessible_remaining_locations(for_progression=True)
  if len(accessible_undone_locations) == 0:
    raise Exception("No progress locations are accessible at the very start of the game!")
  
  # Place progress items.
  location_weights = {}
  current_weight = 1
  while self.logic.unplaced_progress_items:
    accessible_undone_locations = self.logic.get_accessible_remaining_locations(for_progression=True)
    
    if not accessible_undone_locations:
      raise Exception("No locations left to place progress items!")
    
    # If the player gained access to any predetermined item locations, we need to give them those items.
    newly_accessible_predetermined_item_locations = [
      loc for loc in accessible_undone_locations
      if loc in self.logic.prerandomization_item_locations
    ]
    if newly_accessible_predetermined_item_locations:
      for predetermined_item_location_name in newly_accessible_predetermined_item_locations:
        predetermined_item_name = self.logic.prerandomization_item_locations[predetermined_item_location_name]
        self.logic.set_location_to_item(predetermined_item_location_name, predetermined_item_name)
      
      continue # Redo this loop iteration with the predetermined item locations no longer being considered 'remaining'.
    
    for location in accessible_undone_locations:
      if location not in location_weights:
        location_weights[location] = current_weight
      elif location_weights[location] > 1:
        location_weights[location] -= 1
    current_weight += 1
    
    possible_items = self.logic.unplaced_progress_items.copy()
    
    # Don't randomly place items that already had their location predetermined.
    unfound_prerand_locs = [
      loc for loc in self.logic.prerandomization_item_locations
      if loc in self.logic.remaining_item_locations
    ]
    for location_name in unfound_prerand_locs:
      prerand_item = self.logic.prerandomization_item_locations[location_name]
      if prerand_item not in self.logic.all_progress_items:
        continue
      possible_items.remove(prerand_item)
    
    if len(possible_items) == 0:
      raise Exception("Only items left to place are predetermined items at inaccessible locations!")
    
    # Filter out items that are not valid in any of the locations we might use.
    possible_items = self.logic.filter_items_by_any_valid_location(possible_items, accessible_undone_locations)
    
    if len(possible_items) == 0:
      raise Exception("No valid locations left for any of the unplaced progress items!")
    
    # Remove duplicates from the list so items like swords and bows aren't so likely to show up early.
    unique_possible_items = []
    for item_name in possible_items:
      if item_name not in unique_possible_items:
        unique_possible_items.append(item_name)
    possible_items = unique_possible_items
    
    must_place_useful_item = False
    should_place_useful_item = True
    if len(accessible_undone_locations) == 1 and len(possible_items) > 1:
      # If we're on the last accessible location but not the last item we HAVE to place an item that unlocks new locations.
      # (Otherwise we will still try to place a useful item, but failing will not result in an error.)
      must_place_useful_item = True
    elif len(accessible_undone_locations) >= 17:
      # If we have a lot of locations open, we don't need to be so strict with prioritizing currently useful items.
      # This can give the randomizer a chance to place things like Delivery Bag or small keys for dungeons that need x2 to do anything.
      should_place_useful_item = False
    
    # If we wind up placing a useful item it can be a single item or a group.
    # But if we place an item that is not yet useful, we need to exclude groups that are not useful.
    # This is so that a group doesn't wind up taking every single possible remaining location while not opening up new ones.
    possible_groups = [name for name in possible_items if name in self.logic.progress_item_groups]
    useless_groups = self.logic.get_all_useless_items(possible_groups)
    possible_items_when_not_placing_useful = [name for name in possible_items if name not in useless_groups]
    # Only exception is when there's exclusively groups left to place. Then we allow groups even if they're not useful.
    if len(possible_items_when_not_placing_useful) == 0 and len(possible_items) > 0:
      possible_items_when_not_placing_useful = possible_items
    
    if must_place_useful_item or should_place_useful_item:
      shuffled_list = possible_items.copy()
      self.rng.shuffle(shuffled_list)
      item_name = self.logic.get_first_useful_item(shuffled_list)
      if item_name is None:
        if must_place_useful_item:
          raise Exception("No useful progress items to place!")
        else:
          # We'd like to be placing a useful item, but there are no useful items to place.
          # Instead we choose an item that isn't useful yet by itself, but has a high usefulness fraction.
          # In other words, which item has the smallest number of other items needed before it becomes useful?
          # We'd prefer to place an item which is 1/2 of what you need to access a new location over one which is 1/5 for example.
          
          item_by_usefulness_fraction = self.logic.get_items_by_usefulness_fraction(possible_items_when_not_placing_useful)
          
          # We want to limit it to choosing items at the maximum usefulness fraction.
          # Since the values we have are the denominator of the fraction, we actually call min() instead of max().
          max_usefulness = min(item_by_usefulness_fraction.values())
          items_at_max_usefulness = [
            item_name for item_name, usefulness in item_by_usefulness_fraction.items()
            if usefulness == max_usefulness
          ]
          
          item_name = self.rng.choice(items_at_max_usefulness)
    else:
      item_name = self.rng.choice(possible_items_when_not_placing_useful)
    
    if self.options.get("race_mode"):
      locations_filtered = [
        loc for loc in accessible_undone_locations
        if loc not in self.race_mode_banned_locations
      ]
      if item_name in self.logic.progress_item_groups:
        num_locs_needed = len(self.logic.progress_item_groups[item_name])
      else:
        num_locs_needed = 1
      if len(locations_filtered) >= num_locs_needed:
        accessible_undone_locations = locations_filtered
      else:
        raise Exception("Failed to prevent progress items from appearing in unchosen dungeons for race mode.")
    
    if item_name in self.logic.progress_item_groups:
      # If we're placing an entire item group, we use different logic for deciding the location.
      # We do not weight towards newly accessible locations.
      # And we have to select multiple different locations, one for each item in the group.
      group_name = item_name
      possible_locations_for_group = accessible_undone_locations.copy()
      self.rng.shuffle(possible_locations_for_group)
      self.logic.set_multiple_locations_to_group(possible_locations_for_group, group_name)
    else:
      possible_locations = self.logic.filter_locations_valid_for_item(accessible_undone_locations, item_name)
      
      # Try to prevent chains of charts that lead to sunken treasures with more charts in them.
      # If the only locations we have available are sunken treasures we don't have much choice though, so still allow it then.
      if item_name.startswith("Treasure Chart") or item_name.startswith("Triforce Chart"):
        possible_locations_without_sunken_treasures = [
          loc for loc in possible_locations
          if not "Sunken Treasure" in self.logic.item_locations[loc]["Types"]
        ]
        if possible_locations_without_sunken_treasures:
          possible_locations = possible_locations_without_sunken_treasures
      
      # We weight it so newly accessible locations are more likely to be chosen.
      # This way there is still a good chance it will not choose a new location.
      possible_locations_with_weighting = []
      for location_name in possible_locations:
        weight = location_weights[location_name]
        possible_locations_with_weighting += [location_name]*weight
      
      location_name = self.rng.choice(possible_locations_with_weighting)
      self.logic.set_location_to_item(location_name, item_name)
  
  # Make sure locations that should have predetermined items in them have them properly placed, even if the above logic missed them for some reason.
  for location_name in self.logic.prerandomization_item_locations:
    if location_name in self.logic.remaining_item_locations:
      dungeon_item_name = self.logic.prerandomization_item_locations[location_name]
      self.logic.set_location_to_item(location_name, dungeon_item_name)
  
  game_beatable = self.logic.check_requirement_met("Can Reach and Defeat Ganondorf")
  if not game_beatable:
    raise Exception("Game is not beatable on this seed! This error shouldn't happen.")




def write_changed_items(self):
  for location_name, item_name in self.logic.done_item_locations.items():
    paths = self.logic.item_locations[location_name]["Paths"]
    for path in paths:
      change_item(self, path, item_name)

def change_item(self, path, item_name):
  item_id = self.item_name_to_id[item_name]
  
  rel_match = re.search(r"^(rels/[^.]+\.rel)@([0-9A-F]{4})$", path)
  main_dol_match = re.search(r"^main.dol@(8[0-9A-F]{7})$", path)
  custom_symbol_match = re.search(r"^CustomSymbol:(.+)$", path)
  chest_match = re.search(r"^([^/]+/[^/]+\.arc)(?:/Layer([0-9a-b]))?/Chest([0-9A-F]{3})$", path)
  event_match = re.search(r"^([^/]+/[^/]+\.arc)/Event([0-9A-F]{3}):[^/]+/Actor([0-9A-F]{3})/Action([0-9A-F]{3})$", path)
  scob_match = re.search(r"^([^/]+/[^/]+\.arc)(?:/Layer([0-9a-b]))?/ScalableObject([0-9A-F]{3})$", path)
  actor_match = re.search(r"^([^/]+/[^/]+\.arc)(?:/Layer([0-9a-b]))?/Actor([0-9A-F]{3})$", path)
  
  if rel_match:
    rel_path = rel_match.group(1)
    offset = int(rel_match.group(2), 16)
    path = os.path.join("files", rel_path)
    change_hardcoded_item_in_rel(self, path, offset, item_id)
  elif main_dol_match:
    address = int(main_dol_match.group(1), 16)
    change_hardcoded_item_in_dol(self, address, item_id)
  elif custom_symbol_match:
    custom_symbol = custom_symbol_match.group(1)
    found_custom_symbol = False
    for file_path, custom_symbols_for_file in self.custom_symbols.items():
      if custom_symbol in custom_symbols_for_file:
        found_custom_symbol = True
        if file_path == "sys/main.dol":
          address = custom_symbols_for_file[custom_symbol]
          change_hardcoded_item_in_dol(self, address, item_id)
        else:
          offset = custom_symbols_for_file[custom_symbol]
          change_hardcoded_item_in_rel(self, file_path, offset, item_id)
        break
    if not found_custom_symbol:
      raise Exception("Invalid custom symbol: %s" % custom_symbol)
  elif chest_match:
    arc_path = "files/res/Stage/" + chest_match.group(1)
    if chest_match.group(2):
      layer = int(chest_match.group(2), 16)
    else:
      layer = None
    chest_index = int(chest_match.group(3), 16)
    change_chest_item(self, arc_path, chest_index, layer, item_id, item_name)
  elif event_match:
    arc_path = "files/res/Stage/" + event_match.group(1)
    event_index = int(event_match.group(2), 16)
    actor_index = int(event_match.group(3), 16)
    action_index = int(event_match.group(4), 16)
    change_event_item(self, arc_path, event_index, actor_index, action_index, item_id)
  elif scob_match:
    arc_path = "files/res/Stage/" + scob_match.group(1)
    if scob_match.group(2):
      layer = int(scob_match.group(2), 16)
    else:
      layer = None
    scob_index = int(scob_match.group(3), 16)
    change_scob_item(self, arc_path, scob_index, layer, item_id)
  elif actor_match:
    arc_path = "files/res/Stage/" + actor_match.group(1)
    if actor_match.group(2):
      layer = int(actor_match.group(2), 16)
    else:
      layer = None
    actor_index = int(actor_match.group(3), 16)
    change_actor_item(self, arc_path, actor_index, layer, item_id)
  else:
    raise Exception("Invalid item path: " + path)

def change_hardcoded_item_in_dol(self, address, item_id):
  self.dol.write_data(write_u8, address, item_id)

def change_hardcoded_item_in_rel(self, path, offset, item_id):
  rel = self.get_rel(path)
  rel.write_data(write_u8, offset, item_id)

def change_chest_item(self, arc_path, chest_index, layer, item_id, item_name):
  if arc_path.endswith("Stage.arc"):
    dzx = self.get_arc(arc_path).get_file("stage.dzs")
  else:
    dzx = self.get_arc(arc_path).get_file("room.dzr")
  chest = dzx.entries_by_type_and_layer("TRES", layer)[chest_index]
  chest.item_id = item_id
  if self.options.get("chest_type_matches_contents"):
    chest.chest_type = get_ctmc_chest_type_for_item(self, item_name)
  chest.save_changes()

def get_ctmc_chest_type_for_item(self, item_name):
  if item_name not in self.logic.all_progress_items:
    return 0 # Light wood chests for non-progress items and consumables
  if not item_name.endswith(" Key"):
    return 2 # Metal chests for progress items
  if not self.options.get("race_mode"):
    return 1 # Dark wood chest for Small and Big Keys
  
  # In race mode, only put the dungeon keys for required dungeons in dark wood chests.
  # The other keys go into light wood chests.
  dungeon_short_name = item_name.split()[0]
  if self.logic.DUNGEON_NAMES[dungeon_short_name] in self.race_mode_required_dungeons:
    return 1
  else:
    return 0

def change_event_item(self, arc_path, event_index, actor_index, action_index, item_id):
  event_list = self.get_arc(arc_path).get_file("event_list.dat")
  action = event_list.events[event_index].actors[actor_index].actions[action_index]
  
  if 0x6D <= item_id <= 0x72: # Song
    action.name = "059get_dance"
    action.properties[0].value = [item_id-0x6D]
  else:
    action.name = "011get_item"
    action.properties[0].value = [item_id]

def change_scob_item(self, arc_path, scob_index, layer, item_id):
  if arc_path.endswith("Stage.arc"):
    dzx = self.get_arc(arc_path).get_file("stage.dzs")
  else:
    dzx = self.get_arc(arc_path).get_file("room.dzr")
  scob = dzx.entries_by_type_and_layer("SCOB", layer)[scob_index]
  if scob.actor_class_name in ["d_a_salvage", "d_a_tag_kb_item"]:
    scob.item_id = item_id
    scob.save_changes()
  else:
    raise Exception("%s/SCOB%03X is an unknown type of SCOB" % (arc_path, scob_index))

def change_actor_item(self, arc_path, actor_index, layer, item_id):
  if arc_path.endswith("Stage.arc"):
    dzx = self.get_arc(arc_path).get_file("stage.dzs")
  else:
    dzx = self.get_arc(arc_path).get_file("room.dzr")
  actr = dzx.entries_by_type_and_layer("ACTR", layer)[actor_index]
  if actr.actor_class_name in ["d_a_item", "d_a_boss_item"]:
    actr.item_id = item_id
  else:
    raise Exception("%s/ACTR%03X is not an item" % (arc_path, actor_index))
  
  actr.save_changes()
