
import os
import shutil
from pathlib import Path
from fs_helpers import *
from yaz0_decomp import Yaz0Decompressor
from rarc import RARC

class Randomizer:
  def __init__(self):
    self.clean_base_dir = "../Wind Waker Files"
    self.randomized_base_dir = "../Wind Waker Files Randomized"
    
    # TODO: if dest dir already exists, don't overwrite most files since they wouldn't be changed. only overwrite randomized stage files.
    #print("Copying clean files...")
    #shutil.copytree(self.clean_base_dir, self.randomized_base_dir)
    
    stage_dir = os.path.join(self.randomized_base_dir, "files", "res", "Stage")
    arc_pathlist = Path(stage_dir).glob("**/*.arc")
    
    # Decompress any compressed arcs.
    #print("Decompressing archives...")
    #for arc_path in arc_pathlist:
    #  arc_path_str = str(arc_path)
    #  with open(arc_path_str, "rb") as file:
    #    data = file.read()
    #  if read_str(data, 0, 4) == "Yaz0":
    #    #print("  ", arc_path_str)
    #    decomp_data = Yaz0Decompressor.decompress(data)
    #    with open(arc_path_str, "wb") as file:
    #      file.write(decomp_data)
    #return
    
    # Get item names for debug purposes.
    self.item_names = {}
    with open("items.txt", "r") as f:
      for line in f:
        item_id = int(line[:2], 16)
        item_name = line[5:].rstrip()
        self.item_names[item_id] = item_name
    
    # Randomize.
    print("Randomizing...")
    for arc_path in arc_pathlist:
      arc_path_str = str(arc_path)
      self.randomize_arc(arc_path_str)
  
  def randomize_arc(self, arc_path):
    print("On", arc_path)
    
    rarc = RARC(arc_path)
    
    for dzr_or_dzs_file in rarc.dzx_files:
      for chunk in dzr_or_dzs_file.chunks:
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
    
    rarc.save_to_disk()

if __name__ == "__main__":
  Randomizer()
