
from collections import OrderedDict

from randomizers.base_randomizer import BaseRandomizer
from gclib import fs_helpers as fs

BOSS_NAME_TO_SEA_CHART_QUEST_MARKER_INDEX = OrderedDict([
  ("Gohma", 7),
  ("Kalle Demos", 5),
  ("Gohdan", 3), # Originally Southern Triangle Island
  ("Helmaroc King", 2), # Originally Eastern Triangle Island
  ("Jalhalla", 0),
  ("Molgera", 1),
])
# Note: 4 is Northern Triangle Island and 6 is Greatfish Isle, these are not currently used by the randomizer.

class BossRewardRandomizer(BaseRandomizer):
  def __init__(self, rando):
    super().__init__(rando)
    
    # These variables will remain as empty lists if race mode is off.
    # The randomly selected dungeon boss locations that are required in race mode.
    self.required_locations = []
    # The dungeons corresponding to the race mode required boss locations.
    self.required_dungeons = []
    # The bosses required in race mode.
    self.required_bosses = []
    # The item locations that should not have any items in them in race mode.
    self.banned_locations = []
    # The dungeons that are guaranteed to not have anything important in race mode.
    self.banned_dungeons = []
    # The bosses that are guaranteed to not have anything important in race mode.
    self.banned_bosses = []
  
  def _randomize(self):
    # Try to generate dungeon boss reward locations until a valid set of locations is found.
    for i in range(50):
      if self.try_randomize_boss_rewards():
        return
    raise Exception("Cannot randomize boss rewards! Please try randomizing with a different seed.")
  
  def _save(self):
    self.show_quest_markers_on_sea_chart_for_dungeons()
  
  def write_to_spoiler_log(self):
    spoiler_log = ""
    spoiler_log += "Required dungeons:\n"
    for dungeon_name in self.required_dungeons:
      spoiler_log += f"  {dungeon_name}\n"
    spoiler_log += "\n"
    spoiler_log += "Non-required dungeons:\n"
    for dungeon_name in self.banned_dungeons:
      spoiler_log += f"  {dungeon_name}\n"
    
    spoiler_log += "\n\n\n"
    return spoiler_log
  

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
      if self.rando.dungeons_only_start and "Dragon Roost Cavern - Gohma Heart Container" in possible_boss_locations:
        location_name = "Dragon Roost Cavern - Gohma Heart Container"
      elif self.rando.dungeons_only_start and "Forbidden Woods - Kalle Demos Heart Container" in possible_boss_locations:
        location_name = "Forbidden Woods - Kalle Demos Heart Container"
      else:
        location_name = self.rng.choice(possible_boss_locations)
      possible_boss_locations.remove(location_name)
      boss_reward_locations[location_name] = item_name
    
    # Verify that the dungeon boss rewards were placed in a way that allows them all to be accessible.
    locations_valid = self.validate_boss_reward_locations(boss_reward_locations)
    
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
      self.required_locations.append(location_name)
      
      dungeon_name, _ = self.logic.split_location_name_by_zone(location_name)
      self.required_dungeons.append(dungeon_name)
      
      _, specific_location_name = self.logic.split_location_name_by_zone(location_name)
      assert specific_location_name.endswith(" Heart Container")
      boss_name = specific_location_name.removesuffix(" Heart Container")
      self.required_bosses.append(boss_name)
    
    for boss_location_name in possible_boss_locations:
      dungeon_name, _ = self.logic.split_location_name_by_zone(boss_location_name)
      self.banned_dungeons.append(dungeon_name)
    
    banned_dungeons = self.banned_dungeons
    for location_name in self.logic.item_locations:
      zone_name, specific_location_name = self.logic.split_location_name_by_zone(location_name)
      
      if self.logic.is_dungeon_location(location_name) and zone_name in banned_dungeons:
        self.banned_locations.append(location_name)
      elif location_name == "Mailbox - Letter from Orca" and "Forbidden Woods" in banned_dungeons:
        self.banned_locations.append(location_name)
      elif location_name == "Mailbox - Letter from Baito" and "Earth Temple" in banned_dungeons:
        self.banned_locations.append(location_name)
      elif location_name == "Mailbox - Letter from Aryll" and "Forsaken Fortress" in banned_dungeons:
        self.banned_locations.append(location_name)
      elif location_name == "Mailbox - Letter from Tingle" and "Forsaken Fortress" in banned_dungeons:
        self.banned_locations.append(location_name)
      
      if "Boss" in self.logic.item_locations[location_name]["Types"] and zone_name in banned_dungeons:
        assert specific_location_name.endswith(" Heart Container")
        boss_name = specific_location_name.removesuffix(" Heart Container")
        self.banned_bosses.append(boss_name)
    
    return True

  def validate_boss_reward_locations(self, boss_reward_locations: dict):
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
  
  def show_quest_markers_on_sea_chart_for_dungeons(self):
    # Uses the blue quest markers on the sea chart to highlight certain dungeons.
    # This is done by toggling visibility on them and moving some Triangle Island ones around to repurpose them as dungeon ones.
    # When the dungeon entrance rando is on, different entrances can lead into dungeons, so the positions of the markers are updated to point to the appropriate island in that case (including secret cave entrances).
    
    sea_chart_ui = self.rando.get_arc("files/res/Msg/fmapres.arc").get_file_entry("f_map.blo")
    sea_chart_ui.decompress_data_if_necessary()
    first_quest_marker_pic1_offset = 0x43B0
    
    for boss_name in self.required_bosses:
      quest_marker_index = BOSS_NAME_TO_SEA_CHART_QUEST_MARKER_INDEX[boss_name]
      offset = first_quest_marker_pic1_offset + quest_marker_index*0x40
      
      # Make the quest marker icon be visible.
      fs.write_u8(sea_chart_ui.data, offset+9, 1)
      
      if boss_name == "Helmaroc King":
        island_name = "Forsaken Fortress"
      else:
        boss_arena_name = f"{boss_name} Boss Arena"
        island_name = self.rando.entrances.dungeon_and_cave_island_locations[boss_arena_name]
      island_number = self.rando.island_name_to_number[island_name]
      sector_x = (island_number-1) % 7
      sector_y = (island_number-1) // 7
      
      fs.write_s16(sea_chart_ui.data, offset+0x10, sector_x*0x37-0xFA)
      fs.write_s16(sea_chart_ui.data, offset+0x12, sector_y*0x38-0xBC)
