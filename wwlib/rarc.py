
import os
from io import BytesIO

from fs_helpers import *
from wwlib.yaz0 import Yaz0

from wwlib.dzx import DZx
from wwlib.events import EventList
from wwlib.bmg import BMG
from wwlib.charts import ChartList
from wwlib.j3d import BDL, BMD, BMT, BRK
from wwlib.bti import BTIFileEntry

class RARC:
  def __init__(self, data):
    self.data = data
    
    if try_read_str(self.data, 0, 4) == "Yaz0":
      self.data = Yaz0.decompress(self.data)
    
    data = self.data
    
    self.magic = read_str(data, 0, 4)
    assert self.magic == "RARC"
    self.size = read_u32(data, 4)
    self.node_list_offset = 0x40
    self.file_data_list_offset = read_u32(data, 0xC) + 0x20
    self.file_data_total_size = read_u32(data, 0x10)
    self.file_data_total_size_2 = read_u32(data, 0x14)
    self.file_data_total_size_3 = read_u32(data, 0x18)
    self.num_nodes = read_u32(data, 0x20)
    self.total_num_file_entries = read_u32(data, 0x28)
    self.file_entries_list_offset = read_u32(data, 0x2C) + 0x20
    self.string_list_size = read_u32(data, 0x30)
    self.string_list_offset = read_u32(data, 0x34) + 0x20
    self.next_free_file_id = read_u16(data, 0x38)
    self.keep_file_ids_synced_with_indexes = read_u8(data, 0x3A)
    
    self.nodes = []
    for node_index in range(self.num_nodes):
      offset = self.node_list_offset + node_index*Node.ENTRY_SIZE
      node = Node(self)
      node.read(offset)
      self.nodes.append(node)
    
    self.file_entries = []
    for file_index in range(self.total_num_file_entries):
      file_entry_offset = self.file_entries_list_offset + file_index*FileEntry.ENTRY_SIZE
      file_entry = FileEntry(self)
      file_entry.read(file_entry_offset)
      self.file_entries.append(file_entry)
    
    for node in self.nodes:
      for file_index in range(node.first_file_index, node.first_file_index+node.num_files):
        file_entry = self.file_entries[file_index]
        file_entry.parent_node = node
        node.files.append(file_entry)
    
    self.instantiated_object_files = {}
  
  def add_new_node(self, type, name):
    node = Node(self)
    
    node.type = type
    node.name = name
    
    return node
  
  def add_new_file(self, file_name, file_data, node):
    file_entry = FileEntry(self)
    
    if self.next_free_file_id == 0xFFFF:
      raise Exception("Next free file ID in RARC is 0xFFFF. Cannot add new file.")
    file_entry.id = self.next_free_file_id
    self.next_free_file_id += 1
    
    file_entry.type = 0x01
    if file_name.endswith(".rel"):
      file_entry.type |= 0x20
    else:
      file_entry.type |= 0x10
    
    file_entry.name = file_name
    
    file_entry.data = file_data
    file_entry.data_size = data_len(file_entry.data)
    
    file_entry.parent_node = node
    self.file_entries.append(file_entry)
    node.files.append(file_entry)
    
    self.regenerate_all_file_entries_list()
    
    return file_entry
  
  def delete_file(self, file_entry):
    file_entry.parent_node.files.remove(file_entry)
    
    self.regenerate_all_file_entries_list()
  
  def regenerate_all_file_entries_list(self):
    # Regenerate the list of all file entries so they're all together for the nodes, and update the first_file_index of the nodes.
    self.file_entries = []
    for node in self.nodes:
      node.first_file_index = len(self.file_entries)
      self.file_entries += node.files
  
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
    # Supports files changing size, name, files being added or removed, nodes being added or removed, etc.
    
    # Cut off all the data after the header since we're replacing it entirely.
    self.data.truncate(self.node_list_offset)
    self.data.seek(self.node_list_offset)
    
    # Assign the node offsets for each node, but don't actually save them yet because we need to write their names first.
    next_node_offset = self.node_list_offset
    for node in self.nodes:
      node.node_offset = next_node_offset
      self.data.seek(node.node_offset)
      self.data.write(b'\0'*Node.ENTRY_SIZE)
      next_node_offset += Node.ENTRY_SIZE
    
    # Reorders the self.file_entries list and sets the first_file_index field for each node.
    self.regenerate_all_file_entries_list()
    
    # Assign the entry offsets for each file entry, but don't actually save them yet because we need to write their data and names first.
    align_data_to_nearest(self.data, 0x20, padding_bytes=b'\0')
    self.file_entries_list_offset = self.data.tell()
    next_file_entry_offset = self.file_entries_list_offset
    for file_entry in self.file_entries:
      file_entry.entry_offset = next_file_entry_offset
      self.data.seek(file_entry.entry_offset)
      self.data.write(b'\0'*FileEntry.ENTRY_SIZE)
      next_file_entry_offset += FileEntry.ENTRY_SIZE
    
    # Write the strings for the node names and file entry names.
    align_data_to_nearest(self.data, 0x20)
    self.string_list_offset = self.data.tell()
    offsets_for_already_written_strings = {}
    # The dots for the current and parent directories are always written first.
    write_str_with_null_byte(self.data, self.string_list_offset+0, ".")
    offsets_for_already_written_strings["."] = 0
    write_str_with_null_byte(self.data, self.string_list_offset+2, "..")
    offsets_for_already_written_strings[".."] = 2
    next_string_offset = 5
    for file_entry in self.nodes + self.file_entries:
      string = file_entry.name
      if string in offsets_for_already_written_strings:
        offset = offsets_for_already_written_strings[string]
      else:
        offset = next_string_offset
        write_str_with_null_byte(self.data, self.string_list_offset+offset, string)
        next_string_offset += len(string) + 1
        offsets_for_already_written_strings[string] = offset
      file_entry.name_offset = offset
    
    # Save the nodes.
    for node in self.nodes:
      node.save_changes()
    
    # Write the file data, and save the file entries as well.
    align_data_to_nearest(self.data, 0x20)
    self.file_data_list_offset = self.data.tell()
    next_file_data_offset = 0
    for file_entry in self.file_entries:
      if file_entry.is_dir:
        file_entry.save_changes()
        continue
      
      data_size = data_len(file_entry.data)
      file_entry.data_offset = next_file_data_offset
      file_entry.data_size = data_size
      file_entry.save_changes()
      
      self.data.seek(self.file_data_list_offset + file_entry.data_offset)
      file_entry.data.seek(0)
      self.data.write(file_entry.data.read())
      
      next_file_data_offset += data_size
      
      # Pad start of the next file to the next 0x20 bytes.
      align_data_to_nearest(self.data, 0x20)
      next_file_data_offset = self.data.tell() - self.file_data_list_offset
    
    # Update the header.
    write_str(self.data, 0x00, "RARC", 4)
    write_u32(self.data, 0x0C, self.file_data_list_offset-0x20)
    self.num_nodes = len(self.nodes)
    write_u32(self.data, 0x20, self.num_nodes)
    self.total_num_file_entries = len(self.file_entries)
    write_u32(self.data, 0x28, self.total_num_file_entries)
    write_u32(self.data, 0x2C, self.file_entries_list_offset-0x20)
    self.string_list_size = self.file_data_list_offset - self.string_list_offset
    write_u32(self.data, 0x30, self.string_list_size)
    write_u32(self.data, 0x34, self.string_list_offset-0x20)
    write_u16(self.data, 0x38, self.next_free_file_id)
    write_u8(self.data, 0x3A, self.keep_file_ids_synced_with_indexes)
    
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
    elif file_name.endswith(".brk"):
      brk = BRK(file_entry)
      self.instantiated_object_files[file_name] = brk
      return brk
    elif file_name.endswith(".bti"):
      bti = BTIFileEntry(file_entry)
      self.instantiated_object_files[file_name] = bti
      return bti
    elif file_name == "cmapdat.bin":
      chart_list = ChartList(file_entry)
      self.instantiated_object_files[file_name] = chart_list
      return chart_list
    else:
      raise Exception("Unknown file type: %s" % file_name)

class Node:
  ENTRY_SIZE = 0x10
  
  def __init__(self, rarc):
    self.rarc = rarc
    
    self.files = [] # This will be populated after the file entries have been read.
    self.num_files = 0
    self.first_file_index = None
  
  def read(self, node_offset):
    self.node_offset = node_offset
    
    self.type = read_str(self.rarc.data, self.node_offset+0x00, 4)
    self.name_offset = read_u32(self.rarc.data, self.node_offset+0x04)
    self.name_hash = read_u16(self.rarc.data, self.node_offset+0x08)
    self.num_files = read_u16(self.rarc.data, self.node_offset+0x0A)
    self.first_file_index = read_u32(self.rarc.data, self.node_offset+0x0C)
    
    self.name = read_str_until_null_character(self.rarc.data, self.rarc.string_list_offset + self.name_offset)
  
  def save_changes(self):
    hash = 0
    for char in self.name:
      hash *= 3
      hash += ord(char)
      hash &= 0xFFFF
    self.name_hash = hash
    
    self.num_files = len(self.files)
    
    write_str(self.rarc.data, self.node_offset+0x00, self.type, 4)
    write_u32(self.rarc.data, self.node_offset+0x04, self.name_offset)
    write_u16(self.rarc.data, self.node_offset+0x08, self.name_hash)
    write_u16(self.rarc.data, self.node_offset+0x0A, self.num_files)
    write_u32(self.rarc.data, self.node_offset+0x0C, self.first_file_index)

class FileEntry:
  ENTRY_SIZE = 0x14
  
  def __init__(self, rarc):
    self.rarc = rarc
    
    self.parent_node = None
  
  def read(self, entry_offset):
    self.entry_offset = entry_offset
    
    self.id = read_u16(self.rarc.data, entry_offset)
    self.name_hash = read_u16(self.rarc.data, entry_offset + 2)
    type_and_name_offset = read_u32(self.rarc.data, entry_offset + 4)
    data_offset_or_node_index = read_u32(self.rarc.data, entry_offset + 8)
    self.data_size = read_u32(self.rarc.data, entry_offset + 0xC)
    
    self.type = ((type_and_name_offset & 0xFF000000) >> 24)
    # Type is a bitfield. Bits:
    #   01 - File.
    #   02 - Directory.
    #   04 - Compressed.
    #   10 - Data file (as opposed to a REL file).
    #   20 - For dynamic link libraries, aka REL files.
    #   80 - Yaz0 compressed (as opposed to Yay0).
    
    self.name_offset = type_and_name_offset & 0x00FFFFFF
    self.name = read_str_until_null_character(self.rarc.data, self.rarc.string_list_offset + self.name_offset)
    
    if self.is_dir:
      assert self.data_size == 0x10
      self.node_index = data_offset_or_node_index
      self.data = None
    else:
      self.data_offset = data_offset_or_node_index
      self.rarc.data.seek(self.rarc.file_data_list_offset + self.data_offset)
      self.data = BytesIO(self.rarc.data.read(self.data_size))
  
  @property
  def is_dir(self):
    return (self.type & 0x02) != 0
  
  @is_dir.setter
  def is_dir(self, value):
    if value:
      self.type |= 0x02
    else:
      self.type &= ~0x02
  
  def decompress_data_if_necessary(self):
    if try_read_str(self.data, 0, 4) == "Yaz0":
      self.data = Yaz0.decompress(self.data)
      self.type &= ~0x84 # Clear compressed type bits
  
  def save_changes(self):
    hash = 0
    for char in self.name:
      hash *= 3
      hash += ord(char)
      hash &= 0xFFFF
    self.name_hash = hash
    
    # Set or clear compressed type bits
    if not self.is_dir and Yaz0.check_is_compressed(self.data):
      self.type |= 0x84
    else:
      self.type &= ~0x84
    
    type_and_name_offset = (self.type << 24) | (self.name_offset & 0x00FFFFFF)
    
    if self.is_dir:
      data_offset_or_node_index = self.node_index
    else:
      data_offset_or_node_index = self.data_offset
    
    if self.is_dir:
      self.data_size = 0x10
    else:
      self.data_size = data_len(self.data)
    
    write_u16(self.rarc.data, self.entry_offset+0x00, self.id)
    write_u16(self.rarc.data, self.entry_offset+0x02, self.name_hash)
    write_u32(self.rarc.data, self.entry_offset+0x04, type_and_name_offset)
    write_u32(self.rarc.data, self.entry_offset+0x08, data_offset_or_node_index)
    write_u32(self.rarc.data, self.entry_offset+0x0C, self.data_size)
    write_u32(self.rarc.data, self.entry_offset+0x10, 0) # Unused?
