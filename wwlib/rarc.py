
import os
from io import BytesIO
from enum import IntFlag

from fs_helpers import *
from wwlib.yaz0 import Yaz0

from wwlib.dzx import DZx
from wwlib.events import EventList
from wwlib.bmg import BMG
from wwlib.charts import ChartList
from wwlib.j3d import BDL, BMD, BMT, BRK, BTK
from wwlib.bti import BTIFileEntry

class RARC:
  def __init__(self):
    self.data = BytesIO()
    
    self.magic = "RARC"
    self.size = None
    self.data_header_offset = None
    self.file_data_list_offset = None
    self.total_file_data_size = None
    self.mram_file_data_size = None
    self.aram_file_data_size = None
    self.unknown_1 = 0
    
    self.num_nodes = 0
    self.node_list_offset = None
    self.total_num_file_entries = 0
    self.file_entries_list_offset = None
    self.string_list_size = None
    self.string_list_offset = None
    self.next_free_file_id = 0
    self.keep_file_ids_synced_with_indexes = 1
    self.unknown_2 = 0
    self.unknown_3 = 0
    
    self.nodes = []
    self.file_entries = []
    self.instantiated_object_files = {}
  
  def read(self, data):
    self.data = data
    
    if Yaz0.check_is_compressed(self.data):
      self.data = Yaz0.decompress(self.data)
    
    data = self.data
    
    # Read header.
    self.magic = read_str(data, 0, 4)
    assert self.magic == "RARC"
    self.size = read_u32(data, 4)
    self.data_header_offset = read_u32(data, 0x8)
    assert self.data_header_offset == 0x20
    self.file_data_list_offset = read_u32(data, 0xC) + self.data_header_offset
    self.total_file_data_size = read_u32(data, 0x10)
    self.mram_file_data_size = read_u32(data, 0x14)
    self.aram_file_data_size = read_u32(data, 0x18)
    self.unknown_1 = read_u32(data, 0x1C)
    assert self.unknown_1 == 0
    
    # Read data header.
    self.num_nodes = read_u32(data, self.data_header_offset + 0x00)
    self.node_list_offset = read_u32(data, self.data_header_offset + 0x04) + self.data_header_offset
    self.total_num_file_entries = read_u32(data, self.data_header_offset + 0x08)
    self.file_entries_list_offset = read_u32(data, self.data_header_offset + 0x0C) + self.data_header_offset
    self.string_list_size = read_u32(data, self.data_header_offset + 0x10)
    self.string_list_offset = read_u32(data, self.data_header_offset + 0x14) + self.data_header_offset
    self.next_free_file_id = read_u16(data, self.data_header_offset + 0x18)
    self.keep_file_ids_synced_with_indexes = read_u8(data, self.data_header_offset + 0x1A)
    self.unknown_2 = read_u8(data, self.data_header_offset + 0x1B)
    assert self.unknown_2 == 0
    self.unknown_3 = read_u32(data, self.data_header_offset + 0x1C)
    assert self.unknown_3 == 0
    
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
      
      if file_entry.is_dir and file_entry.node_index != 0xFFFFFFFF:
        file_entry.node = self.nodes[file_entry.node_index]
        if file_entry.name not in [".", ".."]:
          assert file_entry.node.dir_entry is None
          file_entry.node.dir_entry = file_entry
    
    for node in self.nodes:
      for file_index in range(node.first_file_index, node.first_file_index+node.num_files):
        file_entry = self.file_entries[file_index]
        file_entry.parent_node = node
        node.files.append(file_entry)
    
    self.instantiated_object_files = {}
  
  def add_root_directory(self):
    root_node = Node(self)
    root_node.type = "ROOT"
    root_node.name = "archive"
    self.nodes.append(root_node)
    
    dot_entry = FileEntry(self)
    dot_entry.name = "."
    dot_entry.type = RARCFileAttrType.DIRECTORY
    dot_entry.node = root_node
    dot_entry.parent_node = root_node
    
    dotdot_entry = FileEntry(self)
    dotdot_entry.name = ".."
    dotdot_entry.type = RARCFileAttrType.DIRECTORY
    dotdot_entry.node = None
    dotdot_entry.parent_node = root_node
    
    root_node.files.append(dot_entry)
    root_node.files.append(dotdot_entry)
    
    self.regenerate_all_file_entries_list()
  
  def add_new_directory(self, dir_name, node_type, parent_node):
    if len(node_type) > 4:
      raise Exception("Node type must not be longer than 4 characters: %s" % node_type)
    if len(node_type) < 4:
      spaces_to_add = 4-len(node_type)
      node_type += " "*spaces_to_add
    
    node = Node(self)
    node.type = node_type
    node.name = dir_name
    
    dir_entry = FileEntry(self)
    dir_entry.name = dir_name
    dir_entry.type = RARCFileAttrType.DIRECTORY
    dir_entry.node = node
    dir_entry.parent_node = parent_node
    
    dot_entry = FileEntry(self)
    dot_entry.name = "."
    dot_entry.type = RARCFileAttrType.DIRECTORY
    dot_entry.node = node
    dot_entry.parent_node = node
    
    dotdot_entry = FileEntry(self)
    dotdot_entry.name = ".."
    dotdot_entry.type = RARCFileAttrType.DIRECTORY
    dotdot_entry.node = parent_node
    dotdot_entry.parent_node = node
    
    self.nodes.append(node)
    parent_node.files.append(dir_entry)
    node.files.append(dot_entry)
    node.files.append(dotdot_entry)
    node.dir_entry = dir_entry
    
    self.regenerate_all_file_entries_list()
    
    return dir_entry, node
  
  def add_new_file(self, file_name, file_data, node):
    file_entry = FileEntry(self)
    
    if not self.keep_file_ids_synced_with_indexes:
      if self.next_free_file_id == 0xFFFF:
        raise Exception("Next free file ID in RARC is 0xFFFF. Cannot add new file.")
      file_entry.id = self.next_free_file_id
      self.next_free_file_id += 1
    
    file_entry.type = RARCFileAttrType.FILE
    if file_name.endswith(".rel"):
      file_entry.type |= RARCFileAttrType.PRELOAD_TO_ARAM
    else:
      file_entry.type |= RARCFileAttrType.PRELOAD_TO_MRAM
    
    file_entry.name = file_name
    
    file_entry.data = file_data
    file_entry.data_size = data_len(file_entry.data)
    
    file_entry.parent_node = node
    node.files.append(file_entry)
    
    self.regenerate_all_file_entries_list()
    
    return file_entry
  
  def delete_directory(self, dir_entry):
    node = dir_entry.node
    
    dir_entry.parent_node.files.remove(dir_entry)
    
    self.nodes.remove(node)
    
    # Recursively delete subdirectories.
    for file_entry in node.files:
      if file_entry.is_dir and not file_entry.name in [".", ".."]:
        self.delete_directory(file_entry)
    
    self.regenerate_all_file_entries_list()
  
  def delete_file(self, file_entry):
    file_entry.parent_node.files.remove(file_entry)
    
    self.regenerate_all_file_entries_list()
  
  def regenerate_all_file_entries_list(self):
    # Regenerate the list of all file entries so they're all together for the nodes, and update the first_file_index of the nodes.
    self.file_entries = []
    self.regenerate_files_list_for_node(self.nodes[0])
    
    if self.keep_file_ids_synced_with_indexes:
      self.next_free_file_id = len(self.file_entries)
      
      for file_entry in self.file_entries:
        if not file_entry.is_dir:
          file_entry.id = self.file_entries.index(file_entry)
  
  def regenerate_files_list_for_node(self, node):
    # Sort the . and .. directory entries to be at the end of the node's file list.
    rel_dir_entries = []
    for file_entry in node.files:
      if file_entry.is_dir and file_entry.name in [".", ".."]:
        rel_dir_entries.append(file_entry)
    for rel_dir_entry in rel_dir_entries:
      node.files.remove(rel_dir_entry)
      node.files.append(rel_dir_entry)
    
    node.first_file_index = len(self.file_entries)
    self.file_entries += node.files
    
    # Recursively add this directory's subdirectory nodes.
    for file_entry in node.files:
      if file_entry.is_dir and file_entry.name not in [".", ".."]:
        self.regenerate_files_list_for_node(file_entry.node)
  
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
    
    # Cut off all the data since we're replacing it entirely.
    self.node_list_offset = 0x40
    self.data.truncate(0)
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
    # Main RAM file entries must all be in a row before the ARAM file entries.
    align_data_to_nearest(self.data, 0x20)
    self.file_data_list_offset = self.data.tell()
    mram_preload_file_entries = []
    aram_preload_file_entries = []
    no_preload_file_entries = []
    for file_entry in self.file_entries:
      if file_entry.is_dir:
        if file_entry.node is None:
          file_entry.node_index = 0xFFFFFFFF
        else:
          file_entry.node_index = self.nodes.index(file_entry.node)
        
        file_entry.save_changes()
      else:
        if file_entry.type & RARCFileAttrType.PRELOAD_TO_MRAM != 0:
          mram_preload_file_entries.append(file_entry)
        elif file_entry.type & RARCFileAttrType.PRELOAD_TO_ARAM != 0:
          aram_preload_file_entries.append(file_entry)
        elif file_entry.type & RARCFileAttrType.LOAD_FROM_DVD != 0:
          no_preload_file_entries.append(file_entry)
        else:
          raise Exception("File entry %s is not set as being loaded into any type of RAM." % file_entry.name)
    
    def write_file_entry_data(file_entry):
      nonlocal next_file_data_offset
      
      if self.keep_file_ids_synced_with_indexes:
        file_entry.id = self.file_entries.index(file_entry)
      
      file_entry.data_offset = next_file_data_offset
      file_entry.save_changes()
      
      self.data.seek(self.file_data_list_offset + file_entry.data_offset)
      file_entry.data.seek(0)
      self.data.write(file_entry.data.read())
      
      next_file_data_offset += file_entry.data_size
      
      # Pad start of the next file to the next 0x20 bytes.
      align_data_to_nearest(self.data, 0x20)
      next_file_data_offset = self.data.tell() - self.file_data_list_offset
    
    next_file_data_offset = 0
    
    for file_entry in mram_preload_file_entries:
      write_file_entry_data(file_entry)
    self.mram_file_data_size = next_file_data_offset
  
    for file_entry in aram_preload_file_entries:
      write_file_entry_data(file_entry)
    self.aram_file_data_size = next_file_data_offset - self.mram_file_data_size
    
    for file_entry in no_preload_file_entries:
      write_file_entry_data(file_entry)
    
    self.total_file_data_size = next_file_data_offset
    
    # Update the header.
    write_magic_str(self.data, 0x00, self.magic, 4)
    self.size = self.file_data_list_offset + self.total_file_data_size
    write_u32(self.data, 0x04, self.size)
    self.data_header_offset = 0x20
    write_u32(self.data, 0x08, self.data_header_offset)
    write_u32(self.data, 0x0C, self.file_data_list_offset-0x20)
    write_u32(self.data, 0x10, self.total_file_data_size)
    write_u32(self.data, 0x14, self.mram_file_data_size)
    write_u32(self.data, 0x18, self.aram_file_data_size)
    write_u32(self.data, 0x1C, 0)
    
    # Update the data header.
    self.num_nodes = len(self.nodes)
    write_u32(self.data, self.data_header_offset + 0x00, self.num_nodes)
    self.total_num_file_entries = len(self.file_entries)
    write_u32(self.data, self.data_header_offset + 0x04, self.node_list_offset - self.data_header_offset)
    write_u32(self.data, self.data_header_offset + 0x08, self.total_num_file_entries)
    write_u32(self.data, self.data_header_offset + 0x0C, self.file_entries_list_offset - self.data_header_offset)
    self.string_list_size = self.file_data_list_offset - self.string_list_offset
    write_u32(self.data, self.data_header_offset + 0x10, self.string_list_size)
    write_u32(self.data, self.data_header_offset + 0x14, self.string_list_offset - self.data_header_offset)
    write_u16(self.data, self.data_header_offset + 0x18, self.next_free_file_id)
    write_u8(self.data, self.data_header_offset + 0x1A, self.keep_file_ids_synced_with_indexes)
    write_u8(self.data, self.data_header_offset + 0x1B, 0)
    write_u32(self.data, self.data_header_offset + 0x1C, 0)
  
  def get_node_by_path(self, path):
    if path in ["", "."]:
      # Root node
      return self.nodes[0]
    
    for node in self.nodes[1:]:
      curr_path = node.dir_entry.name
      curr_node = node.dir_entry.parent_node
      while curr_node is not None:
        if curr_node == self.nodes[0]:
          # Root node
          break
        curr_path = "%s/%s" % (curr_node.dir_entry.name, curr_path)
        curr_node = curr_node.dir_entry.parent_node
      
      if curr_path == path:
        return node
  
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
    elif file_name.endswith(".btk"):
      btk = BTK(file_entry)
      self.instantiated_object_files[file_name] = btk
      return btk
    elif file_name.endswith(".bti"):
      bti = BTIFileEntry(file_entry)
      self.instantiated_object_files[file_name] = bti
      return bti
    elif file_name == "cmapdat.bin":
      chart_list = ChartList(file_entry)
      self.instantiated_object_files[file_name] = chart_list
      return chart_list
    elif file_name.endswith(".arc"):
      inner_rarc = RARC()
      inner_rarc.read(file_entry.data)
      self.instantiated_object_files[file_name] = inner_rarc
      return inner_rarc
    else:
      raise Exception("Unknown file type: %s" % file_name)

class Node:
  ENTRY_SIZE = 0x10
  
  def __init__(self, rarc):
    self.rarc = rarc
    
    self.files = [] # This will be populated after the file entries have been read.
    self.num_files = 0
    self.first_file_index = None
    self.dir_entry = None # This will be populated when the corresponding directory entry is read.
  
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
    
    write_magic_str(self.rarc.data, self.node_offset+0x00, self.type, 4)
    write_u32(self.rarc.data, self.node_offset+0x04, self.name_offset)
    write_u16(self.rarc.data, self.node_offset+0x08, self.name_hash)
    write_u16(self.rarc.data, self.node_offset+0x0A, self.num_files)
    write_u32(self.rarc.data, self.node_offset+0x0C, self.first_file_index)

class FileEntry:
  ENTRY_SIZE = 0x14
  
  def __init__(self, rarc):
    self.rarc = rarc
    
    self.parent_node = None
    self.id = 0xFFFF
    self.data = None
  
  def read(self, entry_offset):
    self.entry_offset = entry_offset
    
    self.id = read_u16(self.rarc.data, entry_offset)
    self.name_hash = read_u16(self.rarc.data, entry_offset + 2)
    type_and_name_offset = read_u32(self.rarc.data, entry_offset + 4)
    data_offset_or_node_index = read_u32(self.rarc.data, entry_offset + 8)
    self.data_size = read_u32(self.rarc.data, entry_offset + 0xC)
    
    self.type = RARCFileAttrType((type_and_name_offset & 0xFF000000) >> 24)
    
    self.name_offset = type_and_name_offset & 0x00FFFFFF
    self.name = read_str_until_null_character(self.rarc.data, self.rarc.string_list_offset + self.name_offset)
    
    if self.is_dir:
      assert self.data_size == 0x10
      self.node_index = data_offset_or_node_index
      self.node = None # This will be populated later.
      self.data = None
    else:
      self.data_offset = data_offset_or_node_index
      absolute_data_offset = self.rarc.file_data_list_offset + self.data_offset
      self.rarc.data.seek(absolute_data_offset)
      self.data = BytesIO(self.rarc.data.read(self.data_size))
  
  @property
  def is_dir(self):
    return (self.type & RARCFileAttrType.DIRECTORY) != 0
  
  @is_dir.setter
  def is_dir(self, value):
    if value:
      self.type |= RARCFileAttrType.DIRECTORY
    else:
      self.type &= ~RARCFileAttrType.DIRECTORY
  
  def decompress_data_if_necessary(self):
    if Yaz0.check_is_compressed(self.data):
      self.data = Yaz0.decompress(self.data)
      self.update_compression_flags_from_data()
  
  def update_compression_flags_from_data(self):
    if self.is_dir:
      self.type &= ~RARCFileAttrType.COMPRESSED
      self.type &= ~RARCFileAttrType.YAZ0_COMPRESSED
      return
    
    if Yaz0.check_is_compressed(self.data):
      self.type |= RARCFileAttrType.COMPRESSED
      self.type |= RARCFileAttrType.YAZ0_COMPRESSED
    elif try_read_str(self.data, 0, 4) == "Yay0":
      self.type |= RARCFileAttrType.COMPRESSED
      self.type &= ~RARCFileAttrType.YAZ0_COMPRESSED
    else:
      self.type &= ~RARCFileAttrType.COMPRESSED
      self.type &= ~RARCFileAttrType.YAZ0_COMPRESSED
  
  def save_changes(self):
    hash = 0
    for char in self.name:
      hash *= 3
      hash += ord(char)
      hash &= 0xFFFF
    self.name_hash = hash
    
    self.update_compression_flags_from_data()
    
    type_and_name_offset = (self.type << 24) | (self.name_offset & 0x00FFFFFF)
    
    if self.is_dir:
      data_offset_or_node_index = self.node_index
      self.data_size = 0x10
    else:
      data_offset_or_node_index = self.data_offset
      self.data_size = data_len(self.data)
    
    write_u16(self.rarc.data, self.entry_offset+0x00, self.id)
    write_u16(self.rarc.data, self.entry_offset+0x02, self.name_hash)
    write_u32(self.rarc.data, self.entry_offset+0x04, type_and_name_offset)
    write_u32(self.rarc.data, self.entry_offset+0x08, data_offset_or_node_index)
    write_u32(self.rarc.data, self.entry_offset+0x0C, self.data_size)
    write_u32(self.rarc.data, self.entry_offset+0x10, 0) # Pointer to the file's data, filled at runtime.

class RARCFileAttrType(IntFlag):
  FILE            = 0x01
  DIRECTORY       = 0x02
  COMPRESSED      = 0x04
  PRELOAD_TO_MRAM = 0x10
  PRELOAD_TO_ARAM = 0x20
  LOAD_FROM_DVD   = 0x40
  YAZ0_COMPRESSED = 0x80
