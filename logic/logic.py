
import yaml
import re

import os

from logic.item_types import PROGRESS_ITEMS, NONPROGRESS_ITEMS, CONSUMABLE_ITEMS

from rarc import RARC
from rel import REL

class Logic:
  def __init__(self, rando):
    self.rando = rando
    
    self.unplaced_progress_items = list(PROGRESS_ITEMS)
    self.unplaced_nonprogress_items = list(NONPROGRESS_ITEMS)
    self.consumable_items = list(CONSUMABLE_ITEMS)
    
    with open("./logic/item_locations.txt") as f:
      self.item_locations = yaml.safe_load(f)
    
    self.remaining_item_locations = list(self.item_locations.keys())
    # Dict keys are not in a consistent order so we have to sort it so random seeding works consistently.
    self.remaining_item_locations.sort()
    
    self.done_item_locations = {}
    for location_name in self.item_locations:
      self.done_item_locations[location_name] = None
  
  def set_location_to_item(self, location_name, item_name):
    if self.done_item_locations[location_name]:
      raise Exception("Location was used twice: " + location_name)
    
    paths = self.item_locations[location_name]["Paths"]
    for path in paths:
      self.rando.change_item(path, item_name)
    
    self.done_item_locations[location_name] = item_name
    self.remaining_item_locations.remove(location_name)
    
    self.mark_item_as_placed(item_name)
    
    spoiler_log_entry = "Placed %s at %s\n" % (item_name, location_name)
    self.rando.spoiler_log += spoiler_log_entry
  
  def mark_item_as_placed(self, item_name):
    if item_name in self.unplaced_progress_items:
      self.unplaced_progress_items.remove(item_name)
    if item_name in self.unplaced_nonprogress_items:
      self.unplaced_nonprogress_items.remove(item_name)
  
  def generate_empty_progress_reqs_file(self):
    output_str = ""
    
    found_items = []
    expected_duplicate_items = ["Piece of Heart", "Joy Pendant", "Small Key", "Dungeon Map", "Compass", "Golden Feather", "Boko Baba Seed", "Skull Necklace", "Big Key", "Knight's Crest"]
    
    known_unused_locations = ["sea/Room22.arc/ScalableObject014", "Siren/Stage.arc/Chest003"]
    
    for arc_path in self.rando.arc_paths:
      relative_arc_path = os.path.relpath(arc_path, self.rando.stage_dir)
      stage_folder, arc_name = os.path.split(relative_arc_path)
      stage_path = stage_folder + "/" + arc_name
      
      stage_name = self.rando.stage_names[stage_folder]
      if stage_name == "Unused":
        continue
      elif stage_name == "The Great Sea" and arc_name in self.rando.island_names:
        stage_name = self.rando.island_names[arc_name]
      
      locations_for_this_arc = []
      
      rarc = RARC(arc_path)
      
      if rarc.dzx_files:
        dzx = rarc.dzx_files[0]
        
        for i, chest in enumerate(dzx.entries_by_type("TRES")):
          if chest.item_id == 0xFF:
            #print("Item ID FF: ", stage_name, "Chest%03X" % i)
            continue
          item_name = self.rando.item_names.get(chest.item_id, "")
          locations_for_this_arc.append((item_name, ["Chest%03X" % i]))
        
        for i, actr in enumerate(dzx.entries_by_type("ACTR")):
          if actr.name == "item":
            item_id = actr.params & 0xFF
            item_name = self.rando.item_names.get(item_id, "")
            if "Rupee" in item_name or "Pickup" in item_name:
              continue
            locations_for_this_arc.append((item_name, ["Actor%03X" % i]))
        
        scobs = dzx.entries_by_type("SCOB")
        for i, scob in enumerate(scobs):
          if scob.is_salvage():
            item_name = self.rando.item_names.get(scob.salvage_item_id, "")
            if not item_name:
              continue
            if scob.salvage_type == 0:
              # The type of salvage point you need a treasure chart to get.
              if scob.salvage_duplicate_id == 0:
                all_four_duplicate_salvages = [
                  "ScalableObject%03X" % i
                  for i, other_scob
                  in enumerate(scobs)
                  if other_scob.is_salvage() and other_scob.salvage_type == 0 and other_scob.salvage_chart_index_plus_1 == scob.salvage_chart_index_plus_1
                ]
                locations_for_this_arc.append((item_name, all_four_duplicate_salvages))
            elif "Rupee" not in item_name:
              locations_for_this_arc.append((item_name, ["ScalableObject%03X" % i]))
      
      for event_list in rarc.event_list_files:
        for event_index, event in enumerate(event_list.events):
          for actor_index, actor in enumerate(event.actors):
            if actor is None:
              continue
            
            for action_index, action in enumerate(actor.actions):
              action_path_string = "Event%03X:%s/Actor%03X/Action%03X" % (event_index, event.name, actor_index, action_index)
              if action.name in ["011get_item", "011_get_item"]:
                if action.property_index == 0xFFFFFFFF:
                  continue
                
                item_id = event_list.get_property_value(action.property_index)
                if item_id == 0x100:
                  #print("Item ID 100: ", stage_name, "EventAction%03X" % i)
                  continue
                
                item_name = self.rando.item_names.get(item_id, "")
                locations_for_this_arc.append((item_name, [action_path_string]))
              elif action.name == "059get_dance":
                song_index = event_list.get_property_value(action.property_index)
                item_name = self.rando.item_names.get(0x6D+song_index)
                locations_for_this_arc.append((item_name, [action_path_string]))
      
      for original_item_name, locations in locations_for_this_arc:
        if not original_item_name:
          print("Unknown item at: ", stage_folder + "/" + locations[0])
          continue
        
        if any(stage_path + "/" + location in known_unused_locations for location in locations):
          print("Unused locations in " + stage_path)
          continue
        
        if original_item_name in found_items and "Rupee" not in original_item_name and original_item_name not in expected_duplicate_items:
          print("Duplicate item: " + original_item_name)
        found_items.append(original_item_name)
        
        output_str += stage_name + ":\n"
        output_str += "  Need: \n"
        output_str += "  Original item: " + original_item_name + "\n"
        output_str += "  Location:\n"
        for location in locations:
          output_str += "    - " + stage_path + "/" + location + "\n"
    
    with open("progress_reqs.txt", "w") as f:
      f.write(output_str)
