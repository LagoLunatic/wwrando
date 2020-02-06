
import os
from io import BytesIO

from fs_helpers import *
from wwlib.yaz0 import Yaz0

from wwlib.dzx import DZx
from wwlib.events import EventList
from wwlib.bmg import BMG
from wwlib.charts import ChartList
from wwlib.j3d import BDL, BMD, BMT
from wwlib.bti import BTIFile

class RARC:
  def __init__(self, data):
    self.data = data
    
    if try_read_str(self.data, 0, 4) == "Yaz0":
      self.data = Yaz0.decompress(self.data)
    
    data = self.data
    
    self.magic = read_str(data, 0, 4)
    assert self.magic == "RARC"
    self.size = read_u32(data, 4)
    self.file_data_list_offset = read_u32(data, 0xC) + 0x20
    self.file_data_total_size = read_u32(data, 0x10)
    self.file_data_total_size_2 = read_u32(data, 0x14)
    self.file_data_total_size_3 = read_u32(data, 0x18)
    num_nodes = read_u32(data, 0x20)
    node_list_offset = 0x40
    self.total_num_file_entries = read_u32(data, 0x28)
    file_entries_list_offset = read_u32(data, 0x2C) + 0x20
    self.string_list_offset = read_u32(data, 0x34) + 0x20
    
    self.nodes = []
    for node_index in range(0, num_nodes):
      offset = node_list_offset + node_index*0x10
      node = Node(data, offset, self)
      self.nodes.append(node)
    
    self.file_entries = []
    for node in self.nodes:
      for file_index in range(node.first_file_index, node.first_file_index+node.num_files):
        file_entry_offset = file_entries_list_offset + file_index*0x14
        
        file_entry = FileEntry(data, file_entry_offset, self)
        self.file_entries.append(file_entry)
        node.files.append(file_entry)
    
    self.instantiated_object_files = {}
  
  def extract_all_files_to_disk_flat(self, output_directory):
    # Does not preserve directory structure.
    if not os.path.isdir(output_directory):
      os.mkdir(output_directory)
    
    for file_entry in self.file_entries:
      if file_entry.is_dir:
        continue
      
      output_file_path = os.path.join(output_directory, file_entry.name)
      
      file_entry.data.seek(0)
      with open(output_file_path, "wb") as f:
        f.write(file_entry.data.read())
  
  def extract_all_files_to_disk(self, output_directory):
    # Preserves directory structure.
    root_node = self.nodes[0]
    self.extract_node_to_disk(root_node, output_directory)
  
  def extract_node_to_disk(self, node, path):
    if not os.path.isdir(path):
      os.mkdir(path)
    
    for file in node.files:
      if file.is_dir:
        if file.name not in [".", ".."]:
          subdir_path = os.path.join(path, file.name)
          subdir_node = self.nodes[file.node_index]
          self.extract_node_to_disk(subdir_node, subdir_path)
      else:
        file_path = os.path.join(path, file.name)
        file.data.seek(0)
        with open(file_path, "wb") as f:
          f.write(file.data.read())
  
  def import_all_files_from_disk(self, input_directory):
    root_node = self.nodes[0]
    return self.import_node_from_disk(root_node, input_directory)
  
  def import_node_from_disk(self, node, path):
    num_files_overwritten = 0
    
    for file in node.files:
      if file.is_dir:
        if file.name not in [".", ".."]:
          subdir_path = os.path.join(path, file.name)
          subdir_node = self.nodes[file.node_index]
          num_files_overwritten += self.import_node_from_disk(subdir_node, subdir_path)
      else:
        file_path = os.path.join(path, file.name)
        if os.path.isfile(file_path):
          with open(file_path, "rb") as f:
            data = BytesIO(f.read())
            file.data = data
            num_files_overwritten += 1
    
    return num_files_overwritten
  
  def save_changes(self):
    # Repacks the .arc file.
    # Supports files changing in size but not changing filenames or adding/removing files.
    
    # Cut off the file data first since we're replacing this data entirely.
    self.data.truncate(self.file_data_list_offset)
    self.data.seek(self.file_data_list_offset)
    
    next_file_data_offset = 0
    for file_entry in self.file_entries:
      if file_entry.is_dir:
        continue
      
      data_size = data_len(file_entry.data)
      file_entry.data_offset = next_file_data_offset
      file_entry.data_size = data_size
      file_entry.save_changes()
      
      self.data.seek(self.file_data_list_offset + file_entry.data_offset)
      file_entry.data.seek(0)
      self.data.write(file_entry.data.read())
      
      # Pad start of the next file to the next 0x20 bytes.
      padded_data_size = (data_size + 0x1F) & ~0x1F
      next_file_data_offset += padded_data_size
      padding_size_needed = padded_data_size - data_size
      self.data.write(b"\0"*padding_size_needed)
    
    # Update rarc's size fields.
    self.size = self.file_data_list_offset + next_file_data_offset
    write_u32(self.data, 4, self.size)
    self.file_data_total_size = next_file_data_offset
    write_u32(self.data, 0x10, self.file_data_total_size)
    if self.file_data_total_size_2 != 0:
      # Unknown what this is for, but it must be properly set for arcs except for RELS.arc
      self.file_data_total_size_2 = self.file_data_total_size
      write_u32(self.data, 0x14, self.file_data_total_size_2)
    if self.file_data_total_size_3 != 0:
      # Unknown what this is for, but it must be properly set for RELS.arc
      self.file_data_total_size_3 = self.file_data_total_size
      write_u32(self.data, 0x18, self.file_data_total_size_3)
  
  def get_file_entry(self, file_name):
    for file_entry in self.file_entries:
      if file_entry.name == file_name:
        return file_entry
    return None
  
  def get_file(self, file_name):
    if file_name in self.instantiated_object_files:
      return self.instantiated_object_files[file_name]
    
    file_entry = self.get_file_entry(file_name)
    if file_entry is None:
      return None
    
    if file_name.endswith(".dzs"):
      dzx = DZx(file_entry)
      self.instantiated_object_files[file_name] = dzx
      return dzx
    elif file_name.endswith(".dzr"):
      dzx = DZx(file_entry)
      self.instantiated_object_files[file_name] = dzx
      return dzx
    elif file_name == "event_list.dat":
      event_list = EventList(file_entry)
      self.instantiated_object_files[file_name] = event_list
      return event_list
    elif file_name.endswith(".bmg"):
      bmg = BMG(file_entry)
      self.instantiated_object_files[file_name] = bmg
      return bmg
    elif file_name.endswith(".bdl"):
      bdl = BDL(file_entry)
      self.instantiated_object_files[file_name] = bdl
      return bdl
    elif file_name.endswith(".bmd"):
      bmd = BMD(file_entry)
      self.instantiated_object_files[file_name] = bmd
      return bmd
    elif file_name.endswith(".bmt"):
      bmt = BMT(file_entry)
      self.instantiated_object_files[file_name] = bmt
      return bmt
    elif file_name.endswith(".bti"):
      bti = BTIFile(file_entry)
      self.instantiated_object_files[file_name] = bti
      return bti
    elif file_name == "cmapdat.bin":
      chart_list = ChartList(file_entry)
      self.instantiated_object_files[file_name] = chart_list
      return chart_list
    else:
      raise Exception("Unknown file type: %s" % file_name)

class Node:
  def __init__(self, rarc_data, offset, rarc):
    self.type = read_str(rarc_data, offset, 4)
    self.name_offset = read_u32(rarc_data, offset+4)
    self.name_hash = read_u16(rarc_data, offset+8)
    self.num_files = read_u16(rarc_data, offset+0xA)
    self.first_file_index = read_u32(rarc_data, offset+0xC)
    
    self.name = read_str_until_null_character(rarc_data, rarc.string_list_offset + self.name_offset)
    
    self.files = [] # This will be populated after the file entries have been read.

class FileEntry:
  def __init__(self, rarc_data, entry_offset, rarc):
    self.entry_offset = entry_offset
    self.rarc = rarc
    
    self.id = read_u16(rarc_data, entry_offset)
    self.name_hash = read_u16(rarc_data, entry_offset + 2)
    type_and_name_offset = read_u32(rarc_data, entry_offset + 4)
    data_offset_or_node_index = read_u32(rarc_data, entry_offset + 8)
    self.data_size = read_u32(rarc_data, entry_offset + 0xC)
    
    self.type = ((type_and_name_offset & 0xFF000000) >> 24)
    # Type is a bitfield. Bits:
    #   01 - File?
    #   02 - Directory.
    #   04 - Compressed.
    #   10 - Data file? (As opposed to a REL file)
    #   20 - For dynamic link libraries, aka REL files?
    #   80 - Yaz0 compressed (as opposed to Yay0?).
    self.is_dir = (self.type & 0x02) != 0
    
    self.name_offset = type_and_name_offset & 0x00FFFFFF
    self.name = read_str_until_null_character(rarc_data, rarc.string_list_offset + self.name_offset)
    
    if self.is_dir:
      self.node_index = data_offset_or_node_index
      self.data = None
    else:
      self.data_offset = data_offset_or_node_index
      rarc_data.seek(rarc.file_data_list_offset + self.data_offset)
      self.data = BytesIO(rarc_data.read(self.data_size))
  
  def decompress_data_if_necessary(self):
    if try_read_str(self.data, 0, 4) == "Yaz0":
      self.data = Yaz0.decompress(self.data)
      self.type &= ~0x84 # Clear compressed type bits
  
  def save_changes(self):
    rarc_data = self.rarc.data
    
    hash = 0
    for char in self.name:
      char = char.lower()
      hash *= 3
      hash += ord(char)
      hash &= 0xFFFF
    self.name_hash = hash
    
    # Set or clear compressed type bits
    if Yaz0.check_is_compressed(self.data):
      self.type |= 0x84
    else:
      self.type &= ~0x84
    
    type_and_name_offset = (self.type << 24) | (self.name_offset & 0x00FFFFFF)
    
    if self.is_dir:
      data_offset_or_node_index = self.node_index
    else:
      data_offset_or_node_index = self.data_offset
    
    self.data_size = data_len(self.data)
    
    write_u16(rarc_data, self.entry_offset+0x2, self.name_hash)
    write_u32(rarc_data, self.entry_offset+0x4, type_and_name_offset)
    write_u32(rarc_data, self.entry_offset+0x8, data_offset_or_node_index)
    write_u32(rarc_data, self.entry_offset+0xC, self.data_size)
