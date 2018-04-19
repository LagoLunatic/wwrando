
import os
from io import BytesIO

from fs_helpers import *
from yaz0_decomp import Yaz0Decompressor

from dzx import DZx
from events import EventList
from bmg import BMG
from charts import ChartList

class RARC:
  def __init__(self, file_path):
    self.file_path = file_path
    with open(self.file_path, "rb") as file:
      self.data = BytesIO(file.read())
    
    if try_read_str(self.data, 0, 4) == "Yaz0":
      self.data = BytesIO(Yaz0Decompressor.decompress(self.data))
    
    data = self.data
    
    self.size = read_u32(data, 4)
    self.file_data_list_offset = read_u32(data, 0xC) + 0x20
    self.file_data_total_size = read_u32(data, 0x10)
    self.file_data_total_size_2 = read_u32(data, 0x14)
    num_nodes = read_u32(data, 0x20)
    node_list_offset = 0x40
    self.total_num_file_entries = read_u32(data, 0x28)
    file_entries_list_offset = read_u32(data, 0x2C) + 0x20
    self.string_list_offset = read_u32(data, 0x34) + 0x20
    
    self.nodes = []
    for node_index in range(0, num_nodes):
      offset = node_list_offset + node_index*0x10
      node = Node(data, offset)
      self.nodes.append(node)
    
    self.file_entries = []
    self.dzx_files = []
    self.event_list_files = []
    self.bmg_files = []
    self.chart_lists = []
    for node in self.nodes:
      for file_index in range(node.first_file_index, node.first_file_index+node.num_files):
        file_entry_offset = file_entries_list_offset + file_index*0x14
        
        file_entry = FileEntry(data, file_entry_offset, self)
        self.file_entries.append(file_entry)
        node.files.append(file_entry)
        
        if file_entry.id == 0xFFFF:
          # Directory
          continue
        
        if file_entry.name.endswith(".dzs"):
          dzx = DZx(file_entry)
          self.dzx_files.append(dzx)
        elif file_entry.name.endswith(".dzr"):
          dzx = DZx(file_entry)
          self.dzx_files.append(dzx)
        elif file_entry.name == "event_list.dat":
          event_list = EventList(file_entry)
          self.event_list_files.append(event_list)
        elif file_entry.name.endswith(".bmg"):
          bmg = BMG(file_entry)
          self.bmg_files.append(bmg)
        elif file_entry.name == "cmapdat.bin":
          chart_list = ChartList(file_entry)
          self.chart_lists.append(chart_list)
  
  def extract_all_files_to_disk_flat(self, output_directory):
    # Does not preserve directory structure.
    for file_entry in self.file_entries:
      if file_entry.id == 0xFFFF: # Directory
        continue
      
      output_file_path = os.path.join(output_directory, file_entry.name)
      
      file_entry.data.seek(0)
      with open(output_file_path, "wb") as f:
        f.write(file_entry.data.read())
  
  def extract_all_files_to_disk(self, output_directory=None):
    # Preserves directory structure.
    if output_directory is None:
      output_directory, _ = os.path.splitext(self.file_path)
    
    root_node = self.nodes[0]
    self.extract_node_to_disk(root_node, output_directory)
  
  def extract_node_to_disk(self, node, path):
    if not os.path.isdir(path):
      os.mkdir(path)
    
    for file in node.files:
      if file.id == 0xFFFF:
        # Directory
        if file.name not in [".", ".."]:
          subdir_path = os.path.join(path, file.name)
          subdir_node = self.nodes[file.node_index]
          self.extract_node_to_disk(subdir_node, subdir_path)
      else:
        file_path = os.path.join(path, file.name)
        file.data.seek(0)
        with open(file_path, "wb") as f:
          f.write(file.data.read())
  
  def save_to_disk(self):
    # Saves a modified .arc file to the disk. Supports files changing in size.
    
    # Cut off the file data first since we're replacing this data entirely.
    self.data.truncate(self.file_data_list_offset)
    
    next_file_data_offset = 0
    for file_entry in self.file_entries:
      if file_entry.id == 0xFFFF: # Directory
        continue
      
      data_size = file_entry.data.seek(0, 2)
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
    self.file_data_total_size_2 = self.file_data_total_size
    write_u32(self.data, 0x14, self.file_data_total_size_2)
    
    with open(self.file_path, "wb") as file:
      self.data.seek(0)
      file.write(self.data.read())

class Node:
  def __init__(self, data, offset):
    self.type = read_str(data, offset, 4)
    self.name_offset = read_u32(data, offset+4)
    self.name_hash = read_u16(data, offset+8)
    self.num_files = read_u16(data, offset+0xA)
    self.first_file_index = read_u32(data, offset+0xC)
    
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
    #   10 - File?
    #   80 - Yaz0 compressed (as opposed to Yay0?).
    
    self.name_offset = type_and_name_offset & 0x00FFFFFF
    self.name = read_str_until_null_character(rarc_data, rarc.string_list_offset + self.name_offset)
    
    if self.id == 0xFFFF:
      # Directory
      self.node_index = data_offset_or_node_index
      self.data = None
    else:
      self.data_offset = data_offset_or_node_index
      rarc_data.seek(rarc.file_data_list_offset + self.data_offset)
      self.data = BytesIO(rarc_data.read(self.data_size))
  
  def decompress_data_if_necessary(self):
    if try_read_str(self.data, 0, 4) == "Yaz0":
      self.data = BytesIO(Yaz0Decompressor.decompress(self.data))
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
    
    type_and_name_offset = (self.type << 24) | (self.name_offset & 0x00FFFFFF)
    
    if self.id == 0xFFFF:
      data_offset_or_node_index = self.node_index
    else:
      data_offset_or_node_index = self.data_offset
    
    write_u16(rarc_data, self.entry_offset+0x2, self.name_hash)
    write_u32(rarc_data, self.entry_offset+0x4, type_and_name_offset)
    write_u32(rarc_data, self.entry_offset+0x8, data_offset_or_node_index)
    write_u32(rarc_data, self.entry_offset+0xC, self.data_size)
