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
  octo_fairy_hint = None
  fishmen_hints = []
  hoho_hints = []
  unique_items_given_hint_for = []
  
  # Identify where the user wishes hints to be located
  variable_hint_placement_options = ["fishmen_hints", "hoho_hints"]
  num_hint_placements = sum(self.options.get(option) for option in variable_hint_placement_options)
  
  # Always assign one hint to the Big Octo Great Fairy
  hints_remaining_per_placement = {"octo_fairy": 1}
  num_hints -= 1
  
  # Distribute the remaining hints among the enabled hint placement options
  if num_hint_placements > 0:
    for option in variable_hint_placement_options:
      if self.options.get(option):
        hints_remaining_per_placement[option] = num_hints // num_hint_placements
    num_hints_remaining = num_hints % num_hint_placements
    for option in variable_hint_placement_options:
      if num_hints_remaining == 0:
        break
      if self.options.get(option):
        hints_remaining_per_placement[option] += 1
        num_hints_remaining -= 1
  
  # Create and shuffle a list of randomized item locations
  possible_item_locations = list(self.logic.done_item_locations.keys())
  self.rng.shuffle(possible_item_locations)
  
  current_placement_index = 0
  hints_placement_options = list(hints_remaining_per_placement.keys())
  while True:
    # We've run out of items at which to hint, or we've made the sufficient amount of hints, so break.
    if not possible_item_locations or sum(hints_remaining_per_placement.values()) == 0:
      break
    
    # Check if we need to distribute any more hints for this placement option
    current_hint_placement = hints_placement_options[current_placement_index]
    if hints_remaining_per_placement[current_hint_placement] == 0:
      current_placement_index = (current_placement_index + 1) % len(hints_placement_options)
      continue
    
    location_name = possible_item_locations.pop()
    if location_name in self.race_mode_required_locations:
      # You already know which boss locations have a required item and which don't in race mode by looking at the sea chart.
      continue
    if current_hint_placement == "octo_fairy" and location_name == "Two-Eye Reef - Big Octo Great Fairy":
      # We don't want this Great Fairy to hint at her own item.
      continue
    
    item_name = self.logic.done_item_locations[location_name]
    if item_name not in self.logic.all_progress_items:
      # Don't hint at non-progress items
      continue
    if self.logic.is_dungeon_item(item_name) and not self.options.get("keylunacy"):
      # Don't hint at dungeon maps and compasses, and don't hint at dungeon keys when key-lunacy is not enabled
      continue
    if current_hint_placement == "fishmen_hints" and item_name == "Bait Bag":
      # Can't access fishmen hints until you already have the bait bag
      continue
    
    zone_name, specific_location_name = self.logic.split_location_name_by_zone(location_name)
    if self.options.get("randomize_entrances") not in ["Disabled", "Dungeons", None] and location_name == "Pawprint Isle - Wizzrobe Cave":
      # Distinguish between the two Pawprint Isle entrances
      zone_name = "Pawprint Isle Side Isle"
    if zone_name in self.dungeon_and_cave_island_locations and self.logic.is_dungeon_or_cave(location_name):
      # If the location is in a dungeon or cave, use the hint for whatever island the dungeon/cave is located on.
      item_name = get_hint_item_name(item_name)
      island_name = self.dungeon_and_cave_island_locations[zone_name]
    elif zone_name in self.island_name_hints:
      item_name = get_hint_item_name(item_name)
      island_name = zone_name
    elif zone_name in self.logic.DUNGEON_NAMES.values():
      continue
    else:
      continue
    
    # Don't give hint for same type of item in same zone
    item_hint = (item_name, island_name)
    if item_hint in unique_items_given_hint_for:
      continue
    unique_items_given_hint_for.append(item_hint)
    
    # Assign the hint to the appropriate hint placement
    if current_hint_placement == "octo_fairy":
      octo_fairy_hint = item_hint
    elif current_hint_placement == "fishmen_hints":
      fishmen_hints.append(item_hint)
    elif current_hint_placement == "hoho_hints":
      hoho_hints.append(item_hint)
    
    # Move the next hint placement
    hints_remaining_per_placement[current_hint_placement] -= 1
    current_placement_index = (current_placement_index + 1) % len(hints_placement_options)
  
  if octo_fairy_hint is None:
    # Failed at making a hint for the Big Octo Great Fairy.
    raise Exception("No valid items to give hints for")
  
  if self.options.get("fishmen_hints") and len(fishmen_hints) == 0:
    # Unable to make a hint for the fishmen, but was able to make one for the Big Octo Great Fairy.
    # Duplicate the Big Octo Great Fairy hint, unless it's for the Bait Bag.
    if octo_fairy_hint[0] == "Bait Bag":
      raise Exception("No valid items to give hints for")
    else:
      fishmen_hints.append(octo_fairy_hint)
  
  if self.options.get("hoho_hints") and len(hoho_hints) == 0:
    # Unable to make a hint for Old Man Ho Ho, but was able to make one for the Big Octo Great Fairy and the fishmen.
    # Duplicate a hint that we've already made.
    hoho_hints.append(self.rng.choice([octo_fairy_hint] + fishmen_hints))
  
  # Loop through the hints, converting the item and location names to hint strings
  octo_fairy_hint = (self.progress_item_hints[octo_fairy_hint[0]], self.island_name_hints[octo_fairy_hint[1]])
  for i, hint in enumerate(fishmen_hints):
    fishmen_hints[i] = (self.progress_item_hints[hint[0]], self.island_name_hints[hint[1]])
  for i, hint in enumerate(hoho_hints):
    hoho_hints[i] = (self.progress_item_hints[hint[0]], self.island_name_hints[hint[1]])
  
  return octo_fairy_hint, fishmen_hints, hoho_hints

def distribute_hints_on_hohos(self, item_hints, n_attempts=100):
  if len(item_hints) == 0:
    return item_hints
  
  # Determine the number of times we need to replicate the hints to distribute them evenly among the Old Man Hohos
  n_replicates = (10 - (len(item_hints) % 10)) % 10
  
  # Determine the number of hints each Old Man Hoho will provide
  n_hints_per_hoho = (len(item_hints) + n_replicates) // 10
  
  # Attempt to assign hints to the Old Man Hoho without duplicates on a single Old Man Hoho
  all_hint_indices = []
  for n_tries in range(0, n_attempts + 1):
    if n_tries == n_attempts:
      # If we fail to find a valid assignment after `n_attempts` tries, we will just iteratively assign hints to the Old Man Hoho
      starting_hint_index = 0
      all_hint_indices = []
      for i in range(10):
        hints_for_hoho = list(range(starting_hint_index, starting_hint_index + n_hints_per_hoho))
        hints_for_hoho = [hint_index % len(item_hints) for hint_index in hints_for_hoho]
        all_hint_indices.append(hints_for_hoho)
        starting_hint_index = (starting_hint_index + n_hints_per_hoho) % len(item_hints)
      break
    
    # Shuffle which hints are assigned to which Old Man Hoho
    hint_indices = list(range(len(item_hints))) + list(range(n_replicates))
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
    hints_for_hoho = set()
    for hint_index in hoho_indices:
      hints_for_hoho.add(item_hints[hint_index])
    hoho_hints.append(list(hints_for_hoho))
  
  return hoho_hints
