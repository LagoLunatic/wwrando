
import os
from io import BytesIO
import shutil
from pathlib import Path
import re

from fs_helpers import *
from yaz0_decomp import Yaz0Decompressor
from rarc import RARC
from rel import REL
import tweaks

class Randomizer:
  def __init__(self):
    clean_base_dir = "../Wind Waker Files"
    self.randomized_base_dir = "../Wind Waker Files Randomized"
    
    copy_and_decompress_clean_files = True
    
    if copy_and_decompress_clean_files:
      print("Copying clean files...")
      shutil.copytree(clean_base_dir, self.randomized_base_dir)
    
    self.stage_dir = os.path.join(self.randomized_base_dir, "files", "res", "Stage")
    self.rels_dir = os.path.join(self.randomized_base_dir, "files", "rels")
    
    if copy_and_decompress_clean_files:
      # Extract all the extra rel files from RELS.arc.
      print("Extracting rels...")
      rels_arc_path = os.path.join(self.randomized_base_dir, "files", "RELS.arc")
      rels_arc = RARC(rels_arc_path)
      rels_arc.extract_all_files_to_disk(self.rels_dir)
      # And then delete RELS.arc. If we don't do this then the original rels inside it will take precedence over the modified ones we extracted.
      os.remove(rels_arc_path)
      rels_arc = None
    
    arc_paths = Path(self.stage_dir).glob("**/*.arc")
    self.arc_paths = [str(arc_path) for arc_path in arc_paths]
    
    if copy_and_decompress_clean_files:
      # Decompress any compressed arcs.
      print("Decompressing archives...")
      for arc_path in self.arc_paths:
        with open(arc_path, "rb") as file:
          data = BytesIO(file.read())
        if try_read_str(data, 0, 4) == "Yaz0":
          decomp_data = Yaz0Decompressor.decompress(data)
          with open(arc_path, "wb") as file:
            file.write(decomp_data)
    
    rel_paths = Path(self.rels_dir).glob("**/*.rel")
    self.rel_paths = [str(rel_path) for rel_path in rel_paths]
    
    if copy_and_decompress_clean_files:
      # Decompress any compressed rels.
      print("Decompressing rels...")
      for rel_path in self.rel_paths:
        with open(rel_path, "rb") as file:
          data = BytesIO(file.read())
        if try_read_str(data, 0, 4) == "Yaz0":
          decomp_data = Yaz0Decompressor.decompress(data)
          with open(rel_path, "wb") as file:
            file.write(decomp_data)
    
    # Get item names for debug purposes.
    self.item_names = {}
    with open("./data/item_names.txt", "r") as f:
      matches = re.findall(r"^([0-9a-f]{2}) - (.+)$", f.read(), re.IGNORECASE | re.MULTILINE)
      for item_id, item_name in matches:
        item_id = int(item_id, 16)
        self.item_names[item_id] = item_name
    
    # Get function names for debug purposes.
    self.function_names = {}
    with open(os.path.join(self.randomized_base_dir, "files", "maps", "framework.map"), "r") as f:
      matches = re.findall(r"^  [0-9a-f]{8} [0-9a-f]{6} ([0-9a-f]{8})  4 (\S+) 	\S+ $", f.read(), re.IGNORECASE | re.MULTILINE)
      for match in matches:
        address, name = match
        address = int(address, 16)
        self.function_names[address] = name
    
    # Get stage and island names for debug purposes.
    self.stage_names = {}
    with open("./data/stage_names.txt", "r") as f:
      while True:
        stage_folder = f.readline()
        if not stage_folder:
          break
        stage_name = f.readline()
        self.stage_names[stage_folder.strip()] = stage_name.strip()
    self.island_names = {}
    with open("./data/island_names.txt", "r") as f:
      while True:
        room_arc_name = f.readline()
        if not room_arc_name:
          break
        island_name = f.readline()
        self.island_names[room_arc_name.strip()] = island_name.strip()
    
    tweaks.modify_new_game_start_code(self)
    tweaks.remove_story_railroading(self)
    tweaks.skip_wakeup_intro(self)
    tweaks.start_ship_at_outset(self)
    tweaks.make_all_text_instant(self)
    
    #self.generate_empty_progress_reqs_file()
    
    # Randomize.
    #print("Randomizing...")
    #for arc_path in self.arc_paths:
    #  self.randomize_arc(arc_path)
  
  def randomize_arc(self, arc_path):
    if arc_path != r"..\Wind Waker Files Randomized\files\res\Stage\sea\Stage.arc":
      return
    
    print("On", arc_path)
    
    rarc = RARC(arc_path)
    
    if rarc.dzx_files:
      dzx_file = rarc.dzx_files[0]
      for chest in dzx_file.entries_by_type("TRES"):
        for chest in chunk.entries:
          print("Chest with item ID: %02X, type: %02X, appear condition: %02X, %02X, name: %s" % (
            chest.item_id,
            chest.chest_type,
            chest.appear_condition,
            chest.appear_condition_flag_id,
            self.item_names.get(chest.item_id, "")
          ))
    
    if rarc.event_list_files:
      event_list = rarc.event_list_files[0]
      for action in event_list.actions:
        if action.name == "011get_item":
          if action.property_index == 0xFFFFFFFF:
            continue
          
          property = event_list.properties[action.property_index]
          if property.data_type != 3:
            raise "A 011get_item action has a property that is not of type integer."
          
          item_id = event_list.integers[property.data_index]
          print("Event that gives item ID: %02X, name: %s" % (
            item_id,
            self.item_names.get(item_id, "")
          ))
          
          #event_list.integers[property.data_index] = 0x100
      #event_list.save_changes()
    
    #rarc.save_to_disk()
  
  def generate_empty_progress_reqs_file(self):
    output_str = ""
    
    found_items = []
    expected_duplicate_items = ["Piece of Heart", "Joy Pendant", "Small Key", "Dungeon Map", "Compass", "Golden Feather", "Boko Baba Seed", "Skull Necklace", "Big Key", "Knight's Crest"]
    
    known_unused_locations = ["sea/Room22.arc/ScalableObject014", "Siren/Stage.arc/Chest003"]
    
    for arc_path in self.arc_paths:
      relative_arc_path = os.path.relpath(arc_path, self.stage_dir)
      stage_folder, arc_name = os.path.split(relative_arc_path)
      stage_path = stage_folder + "/" + arc_name
      
      stage_name = self.stage_names[stage_folder]
      if stage_name == "Unused":
        continue
      elif stage_name == "The Great Sea" and arc_name in self.island_names:
        stage_name = self.island_names[arc_name]
      
      locations_for_this_arc = []
      
      rarc = RARC(arc_path)
      
      if rarc.dzx_files:
        dzx = rarc.dzx_files[0]
        
        for i, chest in enumerate(dzx.entries_by_type("TRES")):
          if chest.item_id == 0xFF:
            #print("Item ID FF: ", stage_name, "Chest%03X" % i)
            continue
          item_name = self.item_names.get(chest.item_id, "")
          locations_for_this_arc.append((item_name, ["Chest%03X" % i]))
        
        for i, actr in enumerate(dzx.entries_by_type("ACTR")):
          if actr.name == "item":
            item_id = actr.params & 0xFF
            item_name = self.item_names.get(item_id, "")
            if "Rupee" in item_name or "Pickup" in item_name:
              continue
            locations_for_this_arc.append((item_name, ["Actor%03X" % i]))
        
        scobs = dzx.entries_by_type("SCOB")
        for i, scob in enumerate(scobs):
          if scob.is_salvage():
            item_name = self.item_names.get(scob.item_id, "")
            if not item_name:
              continue
            if scob.salvage_type == 0:
              # The type of salvage point you need a treasure chart to get.
              if scob.duplicate_id == 0:
                all_four_duplicate_salvages = [
                  "ScalableObject%03X" % i
                  for i, other_scob
                  in enumerate(scobs)
                  if other_scob.is_salvage() and other_scob.salvage_type == 0 and other_scob.chart_index_plus_1 == scob.chart_index_plus_1
                ]
                #locations_for_this_arc.append((item_name, all_four_duplicate_salvages))
            elif "Rupee" not in item_name:
              locations_for_this_arc.append((item_name, ["ScalableObject%03X" % i]))
      
      for event_list in rarc.event_list_files:
        for event_index, event in enumerate(event_list.events):
          for actor_index, actor in enumerate(event.actors):
            if actor is None:
              continue
            
            for action_index, action in enumerate(actor.actions):
              #action_path_string = "EventAction%03X" % i
              action_path_string = "Event%03X:%s/Actor%03X/Action%03X" % (event_index, event.name, actor_index, action_index)
              if action.name in ["011get_item", "011_get_item"]:
                if action.property_index == 0xFFFFFFFF:
                  continue
                
                item_id = event_list.get_property_value(action.property_index)
                if item_id == 0x100:
                  #print("Item ID 100: ", stage_name, "EventAction%03X" % i)
                  continue
                
                item_name = self.item_names.get(item_id, "")
                locations_for_this_arc.append((item_name, [action_path_string]))
              elif action.name == "059get_dance":
                song_index = event_list.get_property_value(action.property_index)
                item_name = self.item_names.get(0x6D+song_index)
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
  
  
if __name__ == "__main__":
  Randomizer()
