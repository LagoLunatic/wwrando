
from collections import OrderedDict

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
    if "Boss" in self.logic.item_locations[loc]["Types"]
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
    
    _, specific_location_name = self.logic.split_location_name_by_zone(location_name)
    assert specific_location_name.endswith(" Heart Container")
    boss_name = specific_location_name.removesuffix(" Heart Container")
    self.race_mode_required_bosses.append(boss_name)
  
  for boss_location_name in possible_boss_locations:
    dungeon_name, _ = self.logic.split_location_name_by_zone(boss_location_name)
    self.race_mode_banned_dungeons.append(dungeon_name)
  
  banned_dungeons = self.race_mode_banned_dungeons
  for location_name in self.logic.item_locations:
    zone_name, specific_location_name = self.logic.split_location_name_by_zone(location_name)
    
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
    
    if "Boss" in self.logic.item_locations[location_name]["Types"] and zone_name in banned_dungeons:
      assert specific_location_name.endswith(" Heart Container")
      boss_name = specific_location_name.removesuffix(" Heart Container")
      self.race_mode_banned_bosses.append(boss_name)
  
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
