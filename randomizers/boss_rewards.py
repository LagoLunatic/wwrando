from collections import Counter

from randomizers.base_randomizer import BaseRandomizer
from gclib import fs_helpers as fs
from wwlib.dzx import DZx, ACTR, TGOB, SCOB
from tweaks import switches_are_contiguous
from gclib.bmg import TextBoxType

BOSS_NAME_TO_SEA_CHART_QUEST_MARKER_INDEX = {
  "Gohma"        : 7,
  "Kalle Demos"  : 5,
  "Gohdan"       : 3, # Originally Southern Triangle Island
  "Helmaroc King": 2, # Originally Eastern Triangle Island
  "Jalhalla"     : 0,
  "Molgera"      : 1,
}
# Note: 4 is Northern Triangle Island and 6 is Greatfish Isle, these are not currently used by the randomizer.

BOSS_NAME_TO_STAGE_ID = {
  "Gohma"        : 3,
  "Kalle Demos"  : 4,
  "Gohdan"       : 5,
  "Helmaroc King": 2,
  "Jalhalla"     : 6,
  "Molgera"      : 7,
}

class BossRewardRandomizer(BaseRandomizer):
  def __init__(self, rando):
    super().__init__(rando)
    
    # These variables will remain empty if required bosses mode is off.
    # The randomly selected dungeon boss locations that are required in required bosses mode.
    self.required_locations = []
    # The dungeons corresponding to the required bosses mode required boss locations.
    self.required_dungeons = []
    # The bosses required in required bosses mode.
    self.required_bosses = []
    # The item locations that should not have any items in them in required bosses mode.
    self.banned_locations = []
    # The dungeons that are guaranteed to not have anything important in required bosses mode.
    self.banned_dungeons = []
    # The bosses that are guaranteed to not have anything important in required bosses mode.
    self.banned_bosses = []
    # Mapping of required locations to which item is placed there.
    self.boss_reward_locations = {}
  
  def is_enabled(self) -> bool:
    return bool(self.options.get("required_bosses"))
  
  def _randomize(self):
    self.randomize_boss_rewards()
  
  def _save(self):
    self.show_quest_markers_on_sea_chart_for_dungeons()
    self.update_puppet_ganon_door_unlock_requirements()
  
  def write_to_spoiler_log(self):
    if not self.is_enabled():
      return ""
    
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
  

  def randomize_boss_rewards(self):
    if not self.options.get("progression_dungeons"):
      raise Exception("Cannot randomize boss rewards when progress items are not allowed in dungeons.")
    
    boss_reward_items = []
    total_num_rewards = int(self.options.get("num_required_bosses"))
    
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
    
    self.boss_reward_locations.clear()
    
    # Decide what reward item to place in each boss location.
    for item_name in boss_reward_items:
      if self.rando.dungeons_and_caves_only_start and "Dragon Roost Cavern - Gohma Heart Container" in possible_boss_locations:
        location_name = "Dragon Roost Cavern - Gohma Heart Container"
      elif self.rando.dungeons_and_caves_only_start and "Forbidden Woods - Kalle Demos Heart Container" in possible_boss_locations:
        location_name = "Forbidden Woods - Kalle Demos Heart Container"
      else:
        location_name = self.rng.choice(possible_boss_locations)
      possible_boss_locations.remove(location_name)
      self.boss_reward_locations[location_name] = item_name
    
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
    
    for location_name, item_name in self.boss_reward_locations.items():
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

  def validate_boss_reward_locations(self):
    boss_reward_items = list(self.boss_reward_locations.values())
    
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
    remaining_boss_locations = list(self.boss_reward_locations.keys())
    
    all_locations = self.logic.item_locations.keys()
    all_progress_locations = self.logic.filter_locations_for_progression(all_locations, filter_sunken_treasure=True)
    
    while remaining_boss_reward_items:
      # Consider a dungeon boss reward to be accessible when every progress location in the dungeon is accessible.
      accessible_undone_locations = self.logic.get_accessible_remaining_locations(for_progression=False)
      inaccessible_dungeons = []
      for location_name in all_progress_locations:
        types = self.logic.item_locations[location_name]["Types"]
        if "Randomizable Miniboss Room" in types and self.options.get("randomize_miniboss_entrances"):
          # Don't consider miniboss rooms as part of the dungeon when they are randomized.
          continue
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
        item_name = self.boss_reward_locations[location_name]
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
    
    overlap_counts = Counter()
    overlap_count_to_extra_rotation = {
      0: 0,
      1: 45,
      2: 22,
      3: 68,
      4: 33,
      5: 56,
    }
    for boss_name in self.required_bosses:
      quest_marker_index = BOSS_NAME_TO_SEA_CHART_QUEST_MARKER_INDEX[boss_name]
      offset = first_quest_marker_pic1_offset + quest_marker_index*0x40
      
      # Make the quest marker icon be visible.
      fs.write_u8(sea_chart_ui.data, offset+9, 1)
      
      island_name = self.rando.entrances.get_entrance_zone_for_boss(boss_name)
      island_number = self.rando.island_name_to_number[island_name]
      sector_x = (island_number-1) % 7
      sector_y = (island_number-1) // 7
      
      fs.write_s16(sea_chart_ui.data, offset+0x10, sector_x*0x37-0xFA)
      fs.write_s16(sea_chart_ui.data, offset+0x12, sector_y*0x38-0xBC)
      
      # Rotate the quest markers so you can tell how many there are even if they overlap.
      # 55 is the base angle they display at in vanilla, and when they don't overlap.
      num_overlaps = overlap_counts[island_number]
      extra_angle = overlap_count_to_extra_rotation[num_overlaps]
      fs.write_u8(sea_chart_ui.data, offset+0x19, 55+extra_angle)
      
      overlap_counts[island_number] += 1
  
  def update_puppet_ganon_door_unlock_requirements(self):
    door_unlocked_switch = 0x19 # From vanilla, originally set when all enemies in the room are dead
    required_bosses_dead_switch = 0x25 # Unused in vanilla
    enemies_dead_switch = 0x26 # Unused in vanilla
    required_bosses_not_dead_switch = 0xE5 # Unused room-specific zone bit (temporary)
    
    stairway_dzr = self.rando.get_arc("files/res/Stage/GanonL/Room0.arc").get_file("room.dzr", DZx)
    
    barred_door = next(e for e in stairway_dzr.entries_by_type(TGOB) if e.name == "KGBdor")
    
    # Add a custom actor to check if the bosses are dead and sets a switch when they are.
    required_boss_stage_no_mask = 0x0000
    for boss_name in self.required_bosses:
      stage_id = BOSS_NAME_TO_STAGE_ID[boss_name]
      assert 0x00 <= stage_id <= 0x0F
      required_boss_stage_no_mask |= (1 << stage_id)
    dng_sw = stairway_dzr.add_entity(ACTR)
    dng_sw.name = "DngSw"
    dng_sw.flag_to_check = 3 # Boss is dead dungoen flag
    dng_sw.stage_no_bitmask = required_boss_stage_no_mask
    dng_sw.switch_to_set = required_bosses_dead_switch
    dng_sw.x_pos = 1800
    dng_sw.y_pos = 2000
    dng_sw.z_pos = -19000
    
    # Change the ALLdie that originally opened the door directly by setting switch 0x19 to instead
    # set an intermediate switch first.
    alldie = next(e for e in stairway_dzr.entries_by_type(ACTR) if e.name == "ALLdie")
    alldie.switch_to_set = enemies_dead_switch
    
    # Add a switch operator that checks that both all enemies in the current room are dead and the
    # required dungeon bosses are also dead.
    door_should_open_switches = [
      required_bosses_dead_switch,
      enemies_dead_switch,
    ]
    assert switches_are_contiguous(door_should_open_switches)
    sw_op = stairway_dzr.add_entity(ACTR)
    sw_op.name = "SwOp"
    sw_op.operation = 0 # AND
    sw_op.is_continuous = 0
    sw_op.num_switches_to_check = len(door_should_open_switches)
    sw_op.first_switch_to_check = min(door_should_open_switches)
    sw_op.switch_to_set = door_unlocked_switch
    sw_op.evnt_index = 0xFF
    sw_op.x_pos = 1800
    sw_op.y_pos = 2000
    sw_op.z_pos = -19200
    
    # Add a TagMsg on the door telling the player it's locked because they haven't defeated the required bosses yet.
    new_message_id = 851
    msg = self.rando.bmg.add_new_message(new_message_id)
    msg.text_box_type = TextBoxType.SPECIAL
    msg.initial_draw_type = 0 # Normal
    msg.text_alignment = 4 # Bottom text box
    msg.string = "You sense that this door will not open until the giant evils throughout the world have been defeated..."
    msg.word_wrap_string(self.rando.bfn)
    
    tag_msg = stairway_dzr.add_entity(SCOB)
    tag_msg.name = "TagMsg"
    tag_msg.type = 0
    tag_msg.message_id = new_message_id
    tag_msg.enable_spawn_switch = required_bosses_not_dead_switch
    tag_msg.switch_to_set = 0xFF
    tag_msg.evnt_index = 0xFF
    tag_msg.enable_spawn_event_bit = 0xFFFF
    tag_msg.x_pos = barred_door.x_pos
    tag_msg.y_pos = barred_door.y_pos + 200
    tag_msg.z_pos = barred_door.z_pos
    tag_msg.scale_x = 80
    tag_msg.scale_y = 255
    
    # We want the TagMsg to disappear once the required bosses are defeated, so add a NAND switch
    # operator that checks for the switch set by the dungeon flag checker and sets a switch if it's
    # NOT set.
    sw_op = stairway_dzr.add_entity(ACTR)
    sw_op.name = "SwOp"
    sw_op.operation = 1 # NAND
    sw_op.is_continuous = 0
    sw_op.num_switches_to_check = 1
    sw_op.first_switch_to_check = required_bosses_dead_switch
    sw_op.switch_to_set = required_bosses_not_dead_switch
    sw_op.evnt_index = 0xFF
    sw_op.x_pos = 1800
    sw_op.y_pos = 2000
    sw_op.z_pos = -19400
    
    stairway_dzr.save_changes()
