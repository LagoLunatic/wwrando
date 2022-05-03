from math import gcd

def get_hint_item_name(item_name):
  if item_name.startswith("Triforce Chart"):
    return "Triforce Chart"
  if item_name.startswith("Treasure Chart"):
    return "Treasure Chart"
  if item_name.endswith("Small Key"):
    return "Small Key"
  if item_name.endswith("Big Key"):
    return "Big Key"
  return item_name

def get_formatted_hint_text(hint, prefix="", suffix="", delay=30):
  item_hint_name, island_hint_name = hint
  
  # Create formatted hint string
  hint_string = "%s\\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00} is located in \\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00}%s" % (prefix, item_hint_name, island_hint_name, suffix)
  
  # Cap delay to "FF"
  delay = min(delay, 255)
  
  # Add a wait command (delay) to prevent the player from skipping over the hint accidentally.
  if delay > 0:
    hint_string += "\\{1A 07 00 00 07 00 %02X}" % delay
  
  return hint_string

def generate_item_hints(self, num_hints):
  hints = []
  unique_items_given_hint_for = []
  possible_item_locations = list(self.logic.done_item_locations.keys())
  self.rng.shuffle(possible_item_locations)
  min_num_hints_needed = 1 + 1
  while True:
    if not possible_item_locations:
      if len(hints) >= min_num_hints_needed:
        break
      elif len(hints) >= 1:
        # Succeeded at making at least 1 hint but not enough to reach the minimum.
        # So duplicate the hint(s) we DID make to fill up the missing slots.
        unique_hints = hints.copy()
        while len(hints) < min_num_hints_needed:
          hints += unique_hints
        hints = hints[:min_num_hints_needed]
        break
      else:
        raise Exception("No valid items to give hints for")
    
    location_name = possible_item_locations.pop()
    if location_name in self.race_mode_required_locations:
      # You already know which boss locations have a required item and which don't in race mode by looking at the sea chart.
      continue
    if location_name == "Two-Eye Reef - Big Octo Great Fairy":
      # We don't want this Great Fairy to hint at her own item.
      continue
    
    item_name = self.logic.done_item_locations[location_name]
    if item_name not in self.logic.all_progress_items:
      continue
    if self.logic.is_dungeon_item(item_name) and not self.options.get("keylunacy"):
      continue
    
    item_name = get_hint_item_name(item_name)
    if item_name == "Bait Bag" and self.options.get("hint_placement") == "Fishmen":
      # Can't access fishmen hints until you already have the bait bag
      continue
    if len(hints) >= num_hints:
      break
    
    zone_name, specific_location_name = self.logic.split_location_name_by_zone(location_name)
    if location_name == "Pawprint Isle - Wizzrobe Cave":
      # Distinguish between the two Pawprint Isle entrances
      zone_name = "Pawprint Isle Side Isle"
    if zone_name in self.dungeon_and_cave_island_locations and self.logic.is_dungeon_or_cave(location_name):
      # If the location is in a dungeon or cave, use the hint for whatever island the dungeon/cave is located on.
      island_name = self.dungeon_and_cave_island_locations[zone_name]
      island_hint_name = self.island_name_hints[island_name]
    elif zone_name in self.island_name_hints:
      island_name = zone_name
      island_hint_name = self.island_name_hints[island_name]
    elif zone_name in self.logic.DUNGEON_NAMES.values():
      continue
    else:
      continue
    
    if (item_name, island_name) in unique_items_given_hint_for: # Don't give hint for same type of item in same zone
      continue
    
    item_hint_name = self.progress_item_hints[item_name]
    
    hints.append((item_hint_name, island_hint_name))
    
    unique_items_given_hint_for.append((item_name, island_name))
  
  return hints

def distribute_hints_on_hohos(self, item_hints, n_attempts=100):
  if len(item_hints) == 0:
    return item_hints
  
  # Determine the number of times we need to replicate the hints to distribute them evenly among the Old Man Hohos
  n_replicates = 10 // gcd(len(item_hints), 10)
  
  # Determine the number of hints each Old Man Hoho will provide
  n_hints_per_hoho = (len(item_hints) * n_replicates) // 10
  
  # Attempt to assign hints to the Old Man Hoho without duplicates on a single Old Man Hoho
  # If we fail to find a valid assignment after 100 tries, we will just go with the most recent assignment
  all_hint_indices = []
  for i in range(n_attempts):
    # Shuffle which hints are assigned to which Old Man Hoho
    hint_indices = list(range(len(item_hints))) * n_replicates
    self.rng.shuffle(hint_indices)
    
    # Split the list into 10 groups, sorting the hints internally for each Old Man Hoho by their index
    all_hint_indices = [sorted(hint_indices[i:i+n_hints_per_hoho]) for i in range(0, len(hint_indices), n_hints_per_hoho)]
    
    # Check if any Old Man Hoho is assigned with two or more of the same hint; if not, we can break
    has_no_duplicates = all(len(set(hoho_indices)) == len(hoho_indices) for hoho_indices in all_hint_indices)
    if has_no_duplicates:
      break
  
  # Replace the indices of the hints with actual hints
  hoho_hints = []
  for hoho_indices in all_hint_indices:
    hints_for_hoho = []
    for hint_index in hoho_indices:
      hints_for_hoho.append(item_hints[hint_index])
    hoho_hints.append(hints_for_hoho)
  
  return hoho_hints
