
import os
import re

from logic.logic import Logic

from gclib import fs_helpers as fs
from randomizers.base_randomizer import BaseRandomizer
from wwlib.dzx import DZx, ACTR, SCOB, TRES, DZxLayer
from wwlib.events import EventList
from tweaks import add_trap_chest_event_to_stage

class ItemRandomizer(BaseRandomizer):
  def __init__(self, rando):
    super().__init__(rando)
    
    self.drc_failsafe_location = None
  
  def is_enabled(self) -> bool:
    return bool(self.rando.randomize_items)
  
  @property
  def progress_randomize_duration_weight(self) -> int:
    return 400
  
  @property
  def progress_save_duration_weight(self) -> int:
    return 100
  
  @property
  def progress_randomize_text(self) -> str:
    return "Randomizing items..."
  
  @property
  def progress_save_text(self) -> str:
    return "Saving items..."
  
  def _randomize(self):
    self.logic.initialize_from_randomizer_state()
    
    if not self.options.keylunacy:
      self.randomize_dungeon_items()
    
    self.randomize_progression_items_forward_fill()
    
    self.randomize_unique_nonprogress_items()
    
    accessible_undone_locations = self.logic.get_accessible_remaining_locations(for_progression=False)
    inaccessible_locations = [loc for loc in self.logic.remaining_item_locations if loc not in accessible_undone_locations]
    if inaccessible_locations:
      print("Inaccessible locations:")
      for location_name in inaccessible_locations:
        print(location_name)
    
    self.randomize_consumable_items()
  
  def _save(self):
    for location_name, item_name in self.logic.done_item_locations.items():
      paths = self.logic.item_locations[location_name]["Paths"]
      for path in paths:
        self.change_item(path, item_name)
  
  def write_to_non_spoiler_log(self) -> str:
    log_str = ""
    
    progress_locations, nonprogress_locations = self.logic.get_progress_and_non_progress_locations()
    
    log_str += "### Locations that may or may not have progress items in them on this run:\n"
    log_str += self.write_list_of_location_names_to_log(progress_locations)
    log_str += "\n\n"
    
    log_str += "### Locations that cannot have progress items in them on this run:\n"
    log_str += self.write_list_of_location_names_to_log(nonprogress_locations)
    
    return log_str
  
  def write_to_spoiler_log(self) -> str:
    spoiler_log = ""
    
    spoiler_log += self.write_progression_spheres_to_log()
    
    spoiler_log += self.write_item_location_spoilers_to_log()
    
    return spoiler_log
  
  
  #region Randomization
  def randomize_dungeon_items(self):
    # Places dungeon-specific items first so all the dungeon locations don't get used up by other items.
    
    # Temporarily add all items except for dungeon keys while we randomize them.
    items_to_temporarily_add = [
      item_name for item_name in (self.logic.unplaced_progress_items + self.logic.unplaced_nonprogress_items)
      if not self.logic.is_dungeon_item(item_name)
    ]
    for item_name in items_to_temporarily_add:
      self.logic.add_owned_item(item_name)
    
    # Temporarily remove all requirements for entering all dungeons while we randomize them.
    # This is for when dungeons are nested. Simply having all items except keys isn't enough if a dungeon is locked behind another dungeon.
    self.logic.temporarily_make_dungeon_entrance_macros_accessible()
    
    if self.rando.dungeons_and_caves_only_start:
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
      self.place_dungeon_item(item_name)
      self.logic.add_owned_item(item_name) # Temporarily add small keys to the player's inventory while placing them.
    
    # Randomize big keys.
    big_keys_to_place = [
      item_name for item_name in (self.logic.unplaced_progress_items + self.logic.unplaced_nonprogress_items)
      if item_name.endswith(" Big Key")
    ]
    assert len(big_keys_to_place) > 0
    for item_name in big_keys_to_place:
      self.place_dungeon_item(item_name)
      self.logic.add_owned_item(item_name) # Temporarily add big keys to the player's inventory while placing them.
    
    # Randomize dungeon maps and compasses.
    other_dungeon_items_to_place = [
      item_name for item_name in (self.logic.unplaced_progress_items + self.logic.unplaced_nonprogress_items)
      if item_name.endswith(" Dungeon Map")
      or item_name.endswith(" Compass")
    ]
    for item_name in other_dungeon_items_to_place:
      self.place_dungeon_item(item_name)
    
    # Remove the items we temporarily added.
    for item_name in items_to_temporarily_add:
      self.logic.remove_owned_item(item_name)
    for item_name in small_keys_to_place:
      self.logic.remove_owned_item(item_name)
    for item_name in big_keys_to_place:
      self.logic.remove_owned_item(item_name)
    
    # Reset the dungeon entrance macros.
    self.logic.update_entrance_connection_macros()

  def place_dungeon_item(self, item_name):
    if self.options.progression_dungeons:
      # If dungeons themselves are progress, do not allow dungeon items to appear in any dungeon
      # locations that are nonprogress (e.g. Tingle Chests).
      for_progression = True
    else:
      # But if dungeons are nonprogress, dungeon items can appear in nonprogress locations.
      for_progression = False
    
    accessible_undone_locations = self.logic.get_accessible_remaining_locations(for_progression=for_progression)
    
    accessible_undone_locations = [
      loc for loc in accessible_undone_locations
      if loc not in self.logic.prerandomization_item_locations
    ]
    
    possible_locations = self.logic.filter_locations_valid_for_item(accessible_undone_locations, item_name)
    
    if self.rando.dungeons_and_caves_only_start and item_name == "DRC Small Key":
      # If we're in a dungeons-only-start, we have to ban small keys from appearing in the path that sequence breaks the hanging platform.
      # A key you need to progress appearing there can cause issues that dead-end the item placement logic when there are no locations outside DRC for the randomizer to give you other items at.
      possible_locations = [
        loc for loc in possible_locations
        if loc not in ["Dragon Roost Cavern - Big Key Chest", "Dragon Roost Cavern - Tingle Statue Chest"]
      ]
    if self.rando.dungeons_and_caves_only_start and item_name in ["DRC Big Key", "DRC Dungeon Map", "DRC Compass"]:
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
  
  def randomize_progression_items_forward_fill(self):
    accessible_undone_locations = self.logic.get_accessible_remaining_locations(for_progression=True)
    if self.logic.unplaced_progress_items and len(accessible_undone_locations) == 0:
      raise Exception("No progress locations are accessible at the very start of the game!")
    
    # Place progress items.
    location_weights = {}
    current_weight = 1
    while self.logic.unplaced_progress_items:
      accessible_undone_locations = self.logic.get_accessible_remaining_locations(for_progression=True)
      
      if self.options.required_bosses:
        # Filter out item locations that have been banned by required bosses mode. We don't want any
        # progress items being placed there.
        # However, we do still keep prerandomized banned locations in for e.g. small keys. If these
        # were excluded the logic would not know how to place them and error out.
        accessible_undone_locations = [
          loc for loc in accessible_undone_locations
          if loc not in self.rando.boss_reqs.banned_locations
          or loc in self.logic.prerandomization_item_locations
        ]
      
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
        raise Exception("Not enough valid locations left for any of the unplaced progress items!")
      
      # Remove duplicates from the list so items like swords and bows aren't so likely to show up early.
      # We exclude dungeon items from this so that small keys can still be front-loaded in Key-Lunacy.
      # With small keys de-duplicated too, dungeons can be inaccessible until late in the seed (especially when nested).
      unique_possible_items = []
      for item_name in possible_items:
        if self.logic.is_dungeon_item(item_name) or item_name not in unique_possible_items:
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
            
            item_by_usefulness_fraction = self.logic.get_items_by_usefulness_fraction(
              possible_items,
              filter_sunken_treasure=False,
            )
            
            # We want to limit it to choosing items at the maximum usefulness fraction.
            # Since the values we have are the denominator of the fraction, we actually call min() instead of max().
            max_usefulness = min(item_by_usefulness_fraction.values())
            items_at_max_usefulness = [
              item_name for item_name, usefulness in item_by_usefulness_fraction.items()
              if usefulness == max_usefulness
            ]
            
            item_name = self.rng.choice(items_at_max_usefulness)
      else:
        item_name = self.rng.choice(possible_items)
      
      possible_locations = self.logic.filter_locations_valid_for_item(accessible_undone_locations, item_name)
      
      # Try to prevent chains of charts that lead to sunken treasures with more charts in them.
      # If the only locations we have available are sunken treasures we don't have much choice though, so still allow it then.
      if item_name.startswith("Treasure Chart") or item_name.startswith("Triforce Chart"):
        possible_locations_without_sunken_treasures = [
          loc for loc in possible_locations
          if "Sunken Treasure" not in self.logic.item_locations[loc]["Types"]
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
  
  def randomize_unique_nonprogress_items(self):
    while self.logic.unplaced_nonprogress_items:
      accessible_undone_locations = self.logic.get_accessible_remaining_locations(for_progression=False)
      
      item_name = self.rng.choice(self.logic.unplaced_nonprogress_items)
      
      possible_locations = self.logic.filter_locations_valid_for_item(accessible_undone_locations, item_name)
      
      if not possible_locations:
        raise Exception("No valid locations left to place non-progress items!")
      
      location_name = self.rng.choice(possible_locations)
      self.logic.set_location_to_item(location_name, item_name)
  
  def randomize_consumable_items(self):
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
  #endregion
  
  
  #region Saving
  def change_item(self, path, item_name):
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
      self.change_hardcoded_item_in_rel(path, offset, item_name)
    elif main_dol_match:
      address = int(main_dol_match.group(1), 16)
      self.change_hardcoded_item_in_dol(address, item_name)
    elif custom_symbol_match:
      custom_symbol = custom_symbol_match.group(1)
      found_custom_symbol = False
      for file_path, custom_symbols_for_file in self.rando.custom_symbols.items():
        if custom_symbol in custom_symbols_for_file:
          found_custom_symbol = True
          if file_path == "sys/main.dol":
            address = custom_symbols_for_file[custom_symbol]
            self.change_hardcoded_item_in_dol(address, item_name)
          else:
            offset = custom_symbols_for_file[custom_symbol]
            self.change_hardcoded_item_in_rel(file_path, offset, item_name)
          break
      if not found_custom_symbol:
        raise Exception("Invalid custom symbol: %s" % custom_symbol)
    elif chest_match:
      arc_path = "files/res/Stage/" + chest_match.group(1)
      layer = DZxLayer(chest_match.group(2))
      chest_index = int(chest_match.group(3), 16)
      self.change_chest_item(arc_path, chest_index, layer, item_name)
    elif event_match:
      arc_path = "files/res/Stage/" + event_match.group(1)
      event_index = int(event_match.group(2), 16)
      actor_index = int(event_match.group(3), 16)
      action_index = int(event_match.group(4), 16)
      self.change_event_item(arc_path, event_index, actor_index, action_index, item_name)
    elif scob_match:
      arc_path = "files/res/Stage/" + scob_match.group(1)
      layer = DZxLayer(scob_match.group(2))
      scob_index = int(scob_match.group(3), 16)
      self.change_scob_item(arc_path, scob_index, layer, item_name)
    elif actor_match:
      arc_path = "files/res/Stage/" + actor_match.group(1)
      layer = DZxLayer(actor_match.group(2))
      actor_index = int(actor_match.group(3), 16)
      self.change_actor_item(arc_path, actor_index, layer, item_name)
    else:
      raise Exception("Invalid item path: " + path)

  def change_hardcoded_item_in_dol(self, address, item_name: str):
    item_id = self.rando.item_name_to_id[item_name]
    self.rando.dol.write_data(fs.write_u8, address, item_id)

  def change_hardcoded_item_in_rel(self, path, offset, item_name: str):
    item_id = self.rando.item_name_to_id[item_name]
    rel = self.rando.get_rel(path)
    rel.write_data(fs.write_u8, offset, item_id)

  def change_chest_item(self, arc_path: str, chest_index: int, layer: DZxLayer, item_name: str):
    if arc_path.endswith("Stage.arc"):
      dzx = self.rando.get_arc(arc_path).get_file("stage.dzs", DZx)
    else:
      dzx = self.rando.get_arc(arc_path).get_file("room.dzr", DZx)
    
    chest = dzx.entries_by_type_and_layer(TRES, layer=layer)[chest_index]
    
    if item_name.endswith(" Trap Chest"):
      # The vanilla game stores the chest behavior type in a bitfield
      # with a mask of 0x7F. However, the devs only used the values 0x00 to 0x08.
      # So, in the custom chest code, the behavior type has been reduced to a mask
      # of 0x3F, leaving a single bit with a mask of 0x40 to serve as a flag
      # indicating whether the chest is trapped (set) or normal (unset).
      
      # Here, we set that custom trap flag.
      chest.behavior_type |= 0x40

      stage_name = arc_path.split("/")[-2]
      add_trap_chest_event_to_stage(self.rando, stage_name)
    else:
      item_id = self.rando.item_name_to_id[item_name]
      chest.item_id = item_id
    
    if self.options.chest_type_matches_contents:
      chest.chest_type = self.get_ctmc_chest_type_for_item(item_name)
    
    chest.save_changes()

  def get_ctmc_chest_type_for_item(self, item_name: str):
    if item_name not in self.logic.all_progress_items:
      return 0 # Light wood chests for non-progress items and consumables
    if not item_name.endswith(" Key"):
      return 2 # Metal chests for progress items
    if not self.options.required_bosses:
      return 1 # Dark wood chest for Small and Big Keys
    
    # In required bosses mode, only put the dungeon keys for required dungeons in dark wood chests.
    # The other keys go into light wood chests.
    dungeon_short_name = item_name.split()[0]
    if self.logic.DUNGEON_NAMES[dungeon_short_name] in self.rando.boss_reqs.required_dungeons:
      return 1
    else:
      return 0

  def change_event_item(self, arc_path: str, event_index: int, actor_index: int, action_index: int, item_name: str):
    item_id = self.rando.item_name_to_id[item_name]
    
    event_list = self.rando.get_arc(arc_path).get_file("event_list.dat", EventList)
    action = event_list.events[event_index].actors[actor_index].actions[action_index]
    
    if 0x6D <= item_id <= 0x72: # Song
      action.name = "059get_dance"
      action.properties[0].value = [item_id-0x6D]
    else:
      action.name = "011get_item"
      action.properties[0].value = [item_id]

  def change_scob_item(self, arc_path: str, scob_index: int, layer: DZxLayer, item_name: str):
    item_id = self.rando.item_name_to_id[item_name]
    
    if arc_path.endswith("Stage.arc"):
      dzx = self.rando.get_arc(arc_path).get_file("stage.dzs", DZx)
    else:
      dzx = self.rando.get_arc(arc_path).get_file("room.dzr", DZx)
    
    scob = dzx.entries_by_type_and_layer(SCOB, layer=layer)[scob_index]
    if scob.actor_class_name in ["d_a_salvage", "d_a_tag_kb_item"]:
      scob.item_id = item_id
      scob.save_changes()
    else:
      raise Exception("%s/SCOB%03X is an unknown type of SCOB" % (arc_path, scob_index))

  def change_actor_item(self, arc_path: str, actor_index: int, layer: DZxLayer, item_name: str):
    item_id = self.rando.item_name_to_id[item_name]
    
    if arc_path.endswith("Stage.arc"):
      dzx = self.rando.get_arc(arc_path).get_file("stage.dzs", DZx)
    else:
      dzx = self.rando.get_arc(arc_path).get_file("room.dzr", DZx)
    
    actr = dzx.entries_by_type_and_layer(ACTR, layer=layer)[actor_index]
    if actr.actor_class_name in ["d_a_item", "d_a_boss_item"]:
      actr.item_id = item_id
      if actr.actor_class_name == "d_a_item" and actr.behavior_type == 0:
        # Change field items with the fade out behavior type to have the don't fade out type instead.
        # This affects the "Earth Temple - Casket in Second Crypt" item (though that one would only
        # fade out after opening the casket and reloading the room).
        actr.behavior_type = 3
    elif actr.actor_class_name in ["d_a_tsubo", "d_a_obj_homen"]:
      if item_id == 0x00:
        # Special case - our custom item_id param for these classes uses 0x00 to mean null, so use the vanilla param.
        actr.dropped_item_id = item_id
        actr.item_id = 0x00
      else:
        actr.dropped_item_id = 0x3F
        actr.item_id = item_id
    else:
      raise Exception("%s/ACTR%03X is not an item" % (arc_path, actor_index))
    
    actr.save_changes()
  #endregion
  
  
  #region Logs
  def get_zones_and_max_location_name_len(self, locations):
    zones = {}
    max_location_name_length = 0
    for location_name in locations:
      zone_name, specific_location_name = self.logic.split_location_name_by_zone(location_name)
      
      if zone_name not in zones:
        zones[zone_name] = []
      zones[zone_name].append((location_name, specific_location_name))
      
      if len(specific_location_name) > max_location_name_length:
        max_location_name_length = len(specific_location_name)
    
    return (zones, max_location_name_length)
  
  def write_list_of_location_names_to_log(self, locations) -> str:
    log_str = ""
    
    zones, _ = self.get_zones_and_max_location_name_len(locations)
    format_string = "    %s\n"
    
    for zone_name, locations_in_zone in zones.items():
      if not any(loc for (loc, _) in locations_in_zone if loc in locations):
        # No locations for this zone.
        continue
      
      log_str += zone_name + ":\n"
      
      for (location_name, specific_location_name) in locations_in_zone:
        if location_name in locations:
          log_str += format_string % specific_location_name
    
    return log_str
  
  def write_progression_spheres_to_log(self):
    spoiler_log = "Playthrough progression spheres:\n"
    progression_spheres = self.calculate_playthrough_progression_spheres()
    all_progression_sphere_locations = [loc for locs in progression_spheres for loc in locs]
    zones, max_location_name_length = self.get_zones_and_max_location_name_len(all_progression_sphere_locations)
    format_string = "      %-" + str(max_location_name_length+1) + "s %s\n"
    for i, progression_sphere in enumerate(progression_spheres):
      spoiler_log += "%d:\n" % (i+1)
      
      for zone_name, locations_in_zone in zones.items():
        if not any(loc for (loc, _) in locations_in_zone if loc in progression_sphere):
          # No locations in this zone are used in this sphere.
          continue
        
        spoiler_log += "  %s:\n" % zone_name
        
        for (location_name, specific_location_name) in locations_in_zone:
          if location_name in progression_sphere:
            item_name = progression_sphere[location_name]
            spoiler_log += format_string % (specific_location_name + ":", item_name)
      
    spoiler_log += "\n\n\n"
    return spoiler_log
  
  def write_item_location_spoilers_to_log(self):
    spoiler_log = "All item locations:\n"
    zones, max_location_name_length = self.get_zones_and_max_location_name_len(self.logic.done_item_locations)
    format_string = "    %-" + str(max_location_name_length+1) + "s %s\n"
    for zone_name, locations_in_zone in zones.items():
      spoiler_log += zone_name + ":\n"
      
      for (location_name, specific_location_name) in locations_in_zone:
        item_name = self.logic.done_item_locations[location_name]
        spoiler_log += format_string % (specific_location_name + ":", item_name)
    
    spoiler_log += "\n\n\n"
    return spoiler_log
  #endregion
  
  
  def calculate_playthrough_progression_spheres(self):
    progression_spheres = []
    
    logic = Logic(self.rando)
    previously_accessible_locations = []
    game_beatable = False
    while True:
      progress_items_in_this_sphere = {}
      
      accessible_locations = logic.get_accessible_remaining_locations(for_progression=False)
      locations_in_this_sphere = [
        loc for loc in accessible_locations
        if loc not in previously_accessible_locations
      ]
      if not locations_in_this_sphere:
        if logic.unplaced_progress_items:
          raise Exception("Failed to calculate progression spheres")
        else:
          remaining_inaccessible_locations = [
            loc for loc in logic.filter_locations_for_progression(logic.remaining_item_locations, filter_sunken_treasure=True)
            if loc not in previously_accessible_locations
          ]
          if remaining_inaccessible_locations:
            raise Exception("Failed to calculate progression spheres")
          else:
            break
      
      
      if not self.options.keylunacy:
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
            
            logic.add_owned_item(item_name)
          
          previously_accessible_locations += newly_accessible_small_key_locations
          continue # Redo this loop iteration with the small key locations no longer being considered 'remaining'.
      
      
      # Hide duplicated progression items (e.g. Empty Bottles) when they are placed in non-progression locations to avoid confusion and inconsistency.
      locations_in_this_sphere = logic.filter_locations_for_progression(locations_in_this_sphere)
      
      added_any_reqbosses_this_sphere = False
      for location_name in locations_in_this_sphere:
        zone_name, specific_location_name = self.logic.split_location_name_by_zone(location_name)
        if specific_location_name.endswith(" Heart Container"):
          boss_name = specific_location_name.removesuffix(" Heart Container")
          progress_items_in_this_sphere[f"{zone_name} - Boss"] = f"Defeat {boss_name}"
          if boss_name in self.rando.boss_reqs.required_bosses:
            # Have to keep track of this so we can split Defeat Ganondorf into a separate sphere.
            # We don't want it in the same sphere as defeating the final required bosses.
            added_any_reqbosses_this_sphere = True
        
        item_name = self.logic.done_item_locations[location_name]
        if item_name in logic.all_progress_items:
          progress_items_in_this_sphere[location_name] = item_name
      
      if not game_beatable and not added_any_reqbosses_this_sphere:
        game_beatable = logic.check_requirement_met("Can Reach and Defeat Ganondorf")
        if game_beatable:
          progress_items_in_this_sphere["Ganon's Tower - Rooftop"] = "Defeat Ganondorf"
      
      progression_spheres.append(progress_items_in_this_sphere)
      
      for location_name, item_name in progress_items_in_this_sphere.items():
        if item_name.startswith("Defeat "):
          continue
        logic.add_owned_item(item_name)
      
      previously_accessible_locations = accessible_locations
    
    if not game_beatable:
      # If the game wasn't already beatable on a previous progression sphere but it is now we add one final one just for this.
      game_beatable = logic.check_requirement_met("Can Reach and Defeat Ganondorf")
      if game_beatable:
        final_progression_sphere = {"Ganon's Tower - Rooftop": "Defeat Ganondorf"}
        progression_spheres.append(final_progression_sphere)
    
    return progression_spheres
