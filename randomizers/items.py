
import os
import re

from fs_helpers import *
import tweaks

def randomize_items(self):
  print("Randomizing items...")
  
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
    possible_items = self.logic.filter_items_valid_for_location(self.logic.unplaced_consumable_items, location_name)
    item_name = self.rng.choice(possible_items)
    self.logic.set_location_to_item(location_name, item_name)

def randomize_dungeon_items(self):
  # Places dungeon-specific items first so all the dungeon locations don't get used up by other items.
  
  # Temporarily add all progress items except for dungeon keys while we randomize them.
  items_to_temporarily_add = [
    item_name for item_name in self.logic.unplaced_progress_items
    if " Key" not in item_name
  ]
  for item_name in items_to_temporarily_add:
    self.logic.add_owned_item_or_item_group(item_name)
  
  # Randomize small keys.
  small_keys_to_place = [
    item_name for item_name in (self.logic.unplaced_progress_items + self.logic.unplaced_nonprogress_items)
    if item_name.endswith(" Small Key")
  ]
  previously_accessible_undone_locations = []
  for item_name in small_keys_to_place:
    accessible_undone_locations = self.logic.get_accessible_remaining_locations()
    accessible_undone_locations = [
      loc for loc in accessible_undone_locations
      if loc not in self.logic.prerandomization_dungeon_item_locations
    ]
    accessible_undone_locations = [
      loc for loc in accessible_undone_locations
      if not "Tingle Statue Chest" in self.logic.item_locations[loc]["Types"]
    ]
    possible_locations = self.logic.filter_locations_valid_for_item(accessible_undone_locations, item_name)
    
    if not possible_locations:
      raise Exception("No valid locations left to place dungeon items!")
    
    location_name = self.rng.choice(possible_locations)
    self.logic.set_prerandomization_dungeon_item_location(location_name, item_name)
    
    self.logic.add_owned_item(item_name) # Temporarily add small keys to the player's inventory while placing them.
    
    previously_accessible_undone_locations = accessible_undone_locations
  
  # Randomize other dungeon items, big keys, dungeon maps, and compasses.
  other_dungeon_items_to_place = [
    item_name for item_name in (self.logic.unplaced_progress_items + self.logic.unplaced_nonprogress_items)
    if item_name.endswith(" Big Key")
    or item_name.endswith(" Dungeon Map")
    or item_name.endswith(" Compass")
  ]
  for item_name in other_dungeon_items_to_place:
    accessible_undone_locations = self.logic.get_accessible_remaining_locations()
    accessible_undone_locations = [
      loc for loc in accessible_undone_locations
      if loc not in self.logic.prerandomization_dungeon_item_locations
    ]
    accessible_undone_locations = [
      loc for loc in accessible_undone_locations
      if not "Tingle Statue Chest" in self.logic.item_locations[loc]["Types"]
    ]
    possible_locations = self.logic.filter_locations_valid_for_item(accessible_undone_locations, item_name)
    
    if not possible_locations:
      raise Exception("No valid locations left to place dungeon items!")
    
    location_name = self.rng.choice(possible_locations)
    self.logic.set_prerandomization_dungeon_item_location(location_name, item_name)
  
  # Remove the items we temporarily added.
  for item_name in items_to_temporarily_add:
    self.logic.remove_owned_item_or_item_group(item_name)
  for item_name in small_keys_to_place:
    self.logic.remove_owned_item(item_name)

def randomize_progression_items(self):
  accessible_undone_locations = self.logic.get_accessible_remaining_locations(for_progression=True)
  if len(accessible_undone_locations) == 0:
    raise Exception("No progress locations are accessible at the very start of the game!")
  
  # Place progress items.
  previously_accessible_undone_locations = []
  while self.logic.unplaced_progress_items:
    accessible_undone_locations = self.logic.get_accessible_remaining_locations(for_progression=True)
    
    if not accessible_undone_locations:
      raise Exception("No locations left to place progress items!")
    
    # If the player gained access to any dungeon item locations, we need to give them those items.
    newly_accessible_dungeon_item_locations = [
      loc for loc in accessible_undone_locations
      if loc in self.logic.prerandomization_dungeon_item_locations
    ]
    if newly_accessible_dungeon_item_locations:
      for dungeon_item_location_name in newly_accessible_dungeon_item_locations:
        dungeon_item_name = self.logic.prerandomization_dungeon_item_locations[dungeon_item_location_name]
        self.logic.set_location_to_item(dungeon_item_location_name, dungeon_item_name)
      
      continue # Redo this loop iteration with the dungeon item locations no longer being considered 'remaining'.
    
    possible_items = self.logic.unplaced_progress_items
    
    if not self.options.get("keylunacy"):
      # Don't randomly place dungeon items, it was already predetermined where they should be placed.
      possible_items = [
        item_name for item_name in self.logic.unplaced_progress_items
        if not self.logic.is_dungeon_item(item_name)
      ]
    
    # Filter out items that are not valid in any of the locations we might use.
    possible_items = self.logic.filter_items_by_any_valid_location(possible_items, accessible_undone_locations)
    
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
    # But if we place an item that is not yet useful, we need to exclude groups.
    # This is so that a group doesn't wind up taking every single possible remaining location while not opening up new ones.
    possible_items_when_not_placing_useful = [name for name in possible_items if name not in self.logic.PROGRESS_ITEM_GROUPS]
    # Only exception is when there's exclusively groups left to place. Then we allow groups even if they're not useful.
    if len(possible_items_when_not_placing_useful) == 0 and len(possible_items) > 0:
      possible_items_when_not_placing_useful = possible_items
    
    if must_place_useful_item or should_place_useful_item:
      shuffled_list = possible_items.copy()
      self.rng.shuffle(shuffled_list)
      item_name = self.logic.get_first_useful_item(shuffled_list, for_progression=True)
      if item_name is None:
        if must_place_useful_item:
          raise Exception("No useful progress items to place!")
        else:
          item_name = self.rng.choice(possible_items_when_not_placing_useful)
    else:
      item_name = self.rng.choice(possible_items_when_not_placing_useful)
    
    if item_name in self.logic.PROGRESS_ITEM_GROUPS:
      # If we're placing an entire item group, we use different logic for deciding the location.
      # We do not weight towards newly accessible locations.
      # And we have to select multiple different locations, one for each item in the group.
      group_name = item_name
      possible_locations_for_group = accessible_undone_locations.copy()
      self.rng.shuffle(possible_locations_for_group)
      self.logic.set_multiple_locations_to_group(possible_locations_for_group, group_name)
    else:
      possible_locations = self.logic.filter_locations_valid_for_item(accessible_undone_locations, item_name)
      
      # We weight it so newly accessible locations are more likely to be chosen.
      # This way there is still a good chance it will not choose a new location.
      possible_locations_with_weighting = []
      for location_name in possible_locations:
        if location_name not in previously_accessible_undone_locations:
          weight = 5
        else:
          weight = 1
        possible_locations_with_weighting += [location_name]*weight
      
      location_name = self.rng.choice(possible_locations_with_weighting)
      self.logic.set_location_to_item(location_name, item_name)
    
    previously_accessible_undone_locations = accessible_undone_locations
  
  # Make sure locations that should have dungeon items in them have them properly placed, even if the above logic missed them for some reason.
  for location_name in self.logic.prerandomization_dungeon_item_locations:
    if location_name in self.logic.remaining_item_locations:
      dungeon_item_name = self.logic.prerandomization_dungeon_item_locations[location_name]
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
  main_dol_match = re.search(r"^main.dol@([0-9A-F]{6})$", path)
  custom_symbol_match = re.search(r"^CustomSymbol:(.+)$", path)
  chest_match = re.search(r"^([^/]+/[^/]+\.arc)(?:/Layer([0-9a-b]))?/Chest([0-9A-F]{3})$", path)
  event_match = re.search(r"^([^/]+/[^/]+\.arc)/Event([0-9A-F]{3}):[^/]+/Actor([0-9A-F]{3})/Action([0-9A-F]{3})$", path)
  scob_match = re.search(r"^([^/]+/[^/]+\.arc)(?:/Layer([0-9a-b]))?/ScalableObject([0-9A-F]{3})$", path)
  actor_match = re.search(r"^([^/]+/[^/]+\.arc)(?:/Layer([0-9a-b]))?/Actor([0-9A-F]{3})$", path)
  
  if rel_match:
    rel_path = rel_match.group(1)
    offset = int(rel_match.group(2), 16)
    path = os.path.join("files", rel_path)
    change_hardcoded_item(self, path, offset, item_id)
  elif main_dol_match:
    offset = int(main_dol_match.group(1), 16)
    path = os.path.join("sys", "main.dol")
    change_hardcoded_item(self, path, offset, item_id)
  elif custom_symbol_match:
    custom_symbol = custom_symbol_match.group(1)
    if custom_symbol not in self.custom_symbols:
      raise Exception("Invalid custom symbol: %s" % custom_symbol)
    address = self.custom_symbols[custom_symbol]
    offset = address - tweaks.ORIGINAL_FREE_SPACE_RAM_ADDRESS + tweaks.ORIGINAL_DOL_SIZE
    path = os.path.join("sys", "main.dol")
    change_hardcoded_item(self, path, offset, item_id)
  elif chest_match:
    arc_path = "files/res/Stage/" + chest_match.group(1)
    if chest_match.group(2):
      layer = int(chest_match.group(2), 16)
    else:
      layer = None
    chest_index = int(chest_match.group(3), 16)
    change_chest_item(self, arc_path, chest_index, layer, item_id)
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

def change_hardcoded_item(self, path, offset, item_id):
  data = self.get_raw_file(path)
  write_u8(data, offset, item_id)

def change_chest_item(self, arc_path, chest_index, layer, item_id):
  dzx = self.get_arc(arc_path).dzx_files[0]
  chest = dzx.entries_by_type_and_layer("TRES", layer)[chest_index]
  chest.item_id = item_id
  chest.save_changes()

def change_event_item(self, arc_path, event_index, actor_index, action_index, item_id):
  event_list = self.get_arc(arc_path).event_list_files[0]
  action = event_list.events[event_index].actors[actor_index].actions[action_index]
  
  if 0x6D <= item_id <= 0x72: # Song
    action.name = "059get_dance"
    event_list.set_property_value(action.property_index, item_id-0x6D)
  else:
    action.name = "011get_item"
    event_list.set_property_value(action.property_index, item_id)
  action.save_changes()

def change_scob_item(self, arc_path, scob_index, layer, item_id):
  dzx = self.get_arc(arc_path).dzx_files[0]
  scob = dzx.entries_by_type_and_layer("SCOB", layer)[scob_index]
  if scob.is_salvage():
    scob.salvage_item_id = item_id
    scob.save_changes()
  elif scob.is_buried_pig_item():
    scob.buried_pig_item_id = item_id
    scob.save_changes()
  else:
    raise Exception("%s/SCOB%03X is an unknown type of SCOB" % (arc_path, scob_index))

def change_actor_item(self, arc_path, actor_index, layer, item_id):
  dzx = self.get_arc(arc_path).dzx_files[0]
  actr = dzx.entries_by_type_and_layer("ACTR", layer)[actor_index]
  if actr.is_item():
    actr.item_id = item_id
  elif actr.is_boss_item():
    actr.boss_item_id = item_id
  else:
    raise Exception("%s/ACTR%03X is not an item" % (arc_path, actor_index))
  
  actr.save_changes()
