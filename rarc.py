
from dzx import DZx
from events import EventList
from fs_helpers import *

class RARC:
  def __init__(self, file_path):
    self.file_path = file_path
    
    with open(self.file_path, "rb") as file:
      self.data = file.read()
    
    data = self.data
    
    file_data_list_offset = read_u32(data, 0xC) + 0x20
    num_nodes = read_u32(data, 0x20)
    node_list_offset = 0x40
    file_entries_list_offset = read_u32(data, 0x2C) + 0x20
    string_list_offset = read_u32(data, 0x34) + 0x20
    
    self.dzx_files = []
    self.event_list_files = []
    for node_index in range(0, num_nodes):
      node_offset = node_list_offset + node_index*0x10
      node_name = read_str(data, node_offset, 4)
      
      num_files_in_node = read_u16(data, node_offset + 0xA)
      first_file_index_in_node = read_u32(data, node_offset + 0xC)
      for file_index in range(first_file_index_in_node, first_file_index_in_node+num_files_in_node):
        file_entry_offset = file_entries_list_offset + file_index*0x14
        
        file_id = read_u16(data, file_entry_offset)
        if file_id == 0xFFFF:
          continue
        
        file_name_offset = string_list_offset + read_u16(data, file_entry_offset + 6)
        file_data_offset = file_data_list_offset + read_u32(data, file_entry_offset + 8)
        file_data_size = read_u32(data, file_entry_offset + 0xC)
        
        file_name = read_str_until_null_character(data, file_name_offset)
        
        file_data = data[file_data_offset:file_data_offset+file_data_size]
        
        if node_name == "DZS " and file_name.endswith(".dzs"):
          dzx = DZx(file_data)
          self.dzx_files.append(dzx)
        elif node_name == "DZR " and file_name.endswith(".dzr"):
          dzx = DZx(file_data)
          self.dzx_files.append(dzx)
        elif node_name == "DAT " and file_name == "event_list.dat":
          event_list = EventList(file_data)
          self.event_list_files.append(event_list)
  
  def save(self):
    with open(self.file_path, "wb") as file:
      file.write(self.data)
