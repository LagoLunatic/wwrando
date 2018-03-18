
import os
import shutil
from pathlib import Path
from fs_helpers import *
from io import BytesIO
from yaz0_decomp import Yaz0Decompressor
from rarc import RARC

class Randomizer:
  def __init__(self):
    self.clean_base_dir = "../Wind Waker Files"
    self.randomized_base_dir = "../Wind Waker Files Randomized"
    
    # TODO: if dest dir already exists, don't overwrite most files since they wouldn't be changed. only overwrite randomized stage files.
    #print("Copying clean files...")
    #shutil.copytree(self.clean_base_dir, self.randomized_base_dir)
    
    self.stage_dir = os.path.join(self.randomized_base_dir, "files", "res", "Stage")
    arc_paths = Path(self.stage_dir).glob("**/*.arc")
    self.arc_paths = [str(arc_path) for arc_path in arc_paths]
    
    # Decompress any compressed arcs.
    #print("Decompressing archives...")
    #for arc_path in self.arc_paths:
    #  with open(arc_path, "rb") as file:
    #    data = BytesIO(file.read())
    #  if read_str(data, 0, 4) == "Yaz0":
    #    #print("  ", arc_path)
    #    decomp_data = Yaz0Decompressor.decompress(data)
    #    with open(arc_path, "wb") as file:
    #      file.write(decomp_data)
    #return
    
    # Get item names for debug purposes.
    self.item_names = {}
    with open("items.txt", "r") as f:
      for line in f:
        item_id = int(line[:2], 16)
        item_name = line[5:].rstrip()
        self.item_names[item_id] = item_name
    
    self.generate_empty_progress_reqs_file()
    
    # Randomize.
    #print("Randomizing...")
    #for arc_path in self.arc_paths:
    #  self.randomize_arc(arc_path)
  
  def randomize_arc(self, arc_path):
    if arc_path != r"..\Wind Waker Files Randomized\files\res\Stage\sea\Stage.arc":
      return
    
    print("On", arc_path)
    
    rarc = RARC(arc_path)
    
    for dzx_file in rarc.dzx_files:
      for chunk in dzx_file.chunks:
        if chunk.chunk_type == "TRES":
          for chest in chunk.entries:
            print("Chest with item ID: %02X, type: %02X, appear condition: %02X, %02X, name: %s" % (
              chest.item_id,
              chest.chest_type,
              chest.appear_condition,
              chest.appear_condition_flag_id,
              self.item_names.get(chest.item_id, "")
            ))
    
    for event_list in rarc.event_list_files:
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
    for arc_path in self.arc_paths:
      relative_arc_path = os.path.relpath(arc_path, self.stage_dir)
      stage_folder, arc_name = os.path.split(relative_arc_path)
      
      lines_for_this_arc = []
      
      rarc = RARC(arc_path)
      
      chests = []
      for dzx_file in rarc.dzx_files:
        for chunk in dzx_file.chunks:
          if chunk.chunk_type == "TRES":
            for i, chest in enumerate(chunk.entries):
              item_name = self.item_names.get(chest.item_id, "")
              lines_for_this_arc.append("  Chest %03X (%s): " % (i, item_name))
      
      for event_list in rarc.event_list_files:
        for i, action in enumerate(event_list.actions):
          if action.name == "011get_item":
            if action.property_index == 0xFFFFFFFF:
              continue
            
            property = event_list.properties[action.property_index]
            if property.data_type != 3:
              raise "A 011get_item action has a property that is not of type integer."
            
            item_id = event_list.integers[property.data_index]
            if item_id == 0x100: # ??? TODO
              continue
            
            item_name = self.item_names.get(item_id, "")
            lines_for_this_arc.append("  Event action %03X (%s): " % (i, item_name))
      
      if any(lines_for_this_arc):
        print(stage_folder + "/" + arc_name + ":")
        for line in lines_for_this_arc:
          print(line)

if __name__ == "__main__":
  Randomizer()
