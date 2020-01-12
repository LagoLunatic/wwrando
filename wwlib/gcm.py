
import os
from io import BytesIO

from fs_helpers import *

MAX_DATA_SIZE_TO_READ_AT_ONCE = 64*1024*1024 # 64MB

class GCM:
  def __init__(self, iso_path):
    self.iso_path = iso_path
    self.files_by_path = {}
    self.files_by_path_lowercase = {}
    self.dirs_by_path = {}
    self.dirs_by_path_lowercase = {}
  
  def read_entire_disc(self):
    self.iso_file = open(self.iso_path, "rb")
    
    try:
      self.fst_offset = read_u32(self.iso_file, 0x424)
      self.fst_size = read_u32(self.iso_file, 0x428)
      self.read_filesystem()
      self.read_system_data()
    finally:
      self.iso_file.close()
      self.iso_file = None
    
    for file_path, file_entry in self.files_by_path.items():
      self.files_by_path_lowercase[file_path.lower()] = file_entry
    for dir_path, file_entry in self.dirs_by_path.items():
      self.dirs_by_path_lowercase[dir_path.lower()] = file_entry
  
  def read_filesystem(self):
    self.file_entries = []
    num_file_entries = read_u32(self.iso_file, self.fst_offset + 8)
    self.fnt_offset = self.fst_offset + num_file_entries*0xC
    for file_index in range(num_file_entries):
      file_entry_offset = self.fst_offset + file_index * 0xC
      file_entry = FileEntry()
      file_entry.read(file_index, self.iso_file, file_entry_offset, self.fnt_offset)
      self.file_entries.append(file_entry)
    
    root_file_entry = self.file_entries[0]
    self.read_directory(root_file_entry, "files")
  
  def read_directory(self, directory_file_entry, dir_path):
    assert directory_file_entry.is_dir
    self.dirs_by_path[dir_path] = directory_file_entry
    
    i = directory_file_entry.file_index + 1
    while i < directory_file_entry.next_fst_index:
      file_entry = self.file_entries[i]
      
      # Set parent/children relationships
      file_entry.parent = directory_file_entry
      directory_file_entry.children.append(file_entry)
      
      if file_entry.is_dir:
        assert directory_file_entry.file_index == file_entry.parent_fst_index
        subdir_path = dir_path + "/" + file_entry.name
        self.read_directory(file_entry, subdir_path)
        i = file_entry.next_fst_index
      else:
        file_path = dir_path + "/" + file_entry.name
        self.files_by_path[file_path] = file_entry
        file_entry.file_path = file_path
        i += 1
  
  def read_system_data(self):
    self.files_by_path["sys/boot.bin"] = SystemFile(0, 0x440)
    self.files_by_path["sys/bi2.bin"] = SystemFile(0x440, 0x2000)
    
    apploader_header_size = 0x20
    apploader_size = read_u32(self.iso_file, 0x2440 + 0x14)
    apploader_trailer_size = read_u32(self.iso_file, 0x2440 + 0x18)
    apploader_full_size = apploader_header_size + apploader_size + apploader_trailer_size
    self.files_by_path["sys/apploader.img"] = SystemFile(0x2440, apploader_full_size)
    
    dol_offset = read_u32(self.iso_file, 0x420)
    main_dol_size = 0
    for i in range(7): # Text sections
      section_offset = read_u32(self.iso_file, dol_offset + 0x00 + i*4)
      section_size = read_u32(self.iso_file, dol_offset + 0x90 + i*4)
      section_end_offset = section_offset + section_size
      if section_end_offset > main_dol_size:
        main_dol_size = section_end_offset
    for i in range(11): # Data sections
      section_offset = read_u32(self.iso_file, dol_offset + 0x1C + i*4)
      section_size = read_u32(self.iso_file, dol_offset + 0xAC + i*4)
      section_end_offset = section_offset + section_size
      if section_end_offset > main_dol_size:
        main_dol_size = section_end_offset
    self.files_by_path["sys/main.dol"] = SystemFile(dol_offset, main_dol_size)
    
    self.files_by_path["sys/fst.bin"] = SystemFile(self.fst_offset, self.fst_size)
  
  def read_file_data(self, file_path):
    file_path = file_path.lower()
    if file_path not in self.files_by_path_lowercase:
      raise Exception("Could not find file: " + file_path)
    
    file_entry = self.files_by_path_lowercase[file_path]
    if file_entry.file_size > MAX_DATA_SIZE_TO_READ_AT_ONCE:
      raise Exception("Tried to read a very large file all at once")
    with open(self.iso_path, "rb") as iso_file:
      data = read_bytes(iso_file, file_entry.file_data_offset, file_entry.file_size)
    data = BytesIO(data)
    
    return data
  
  def read_file_raw_data(self, file_path):
    file_path = file_path.lower()
    if file_path not in self.files_by_path_lowercase:
      raise Exception("Could not find file: " + file_path)
    
    file_entry = self.files_by_path_lowercase[file_path]
    with open(self.iso_path, "rb") as iso_file:
      data = read_bytes(iso_file, file_entry.file_data_offset, file_entry.file_size)
    
    return data
  
  def get_dir_file_entry(self, dir_path):
    dir_path = dir_path.lower()
    if dir_path not in self.dirs_by_path_lowercase:
      raise Exception("Could not find directory: " + dir_path)
    
    file_entry = self.dirs_by_path_lowercase[dir_path]
    return file_entry
  
  def export_disc_to_folder_with_changed_files(self, output_folder_path, changed_files):
    self.changed_files = changed_files
    for file_path, file_entry in self.files_by_path.items():
      full_file_path = os.path.join(output_folder_path, file_path)
      dir_name = os.path.dirname(full_file_path)
      if not os.path.isdir(dir_name):
        os.makedirs(dir_name)
      
      file_data = self.get_changed_file_data(file_path)
      with open(full_file_path, "wb") as f:
        file_data.seek(0)
        f.write(file_data.read())
  
  def export_disc_to_iso_with_changed_files(self, output_file_path, changed_files):
    self.changed_files = changed_files
    
    # Check the changed_files dict for files that didn't originally exist, and add them.
    for file_path in self.changed_files:
      if file_path.lower() in self.files_by_path_lowercase:
        # Existing file
        continue
      
      self.add_new_file(file_path)
    
    self.output_iso = open(output_file_path, "wb")
    try:
      self.export_system_data_to_iso()
      self.export_filesystem_to_iso()
      self.align_output_iso_to_nearest(2048)
    except:
      self.output_iso.close()
      os.remove(output_file_path)
      raise
    finally:
      self.output_iso.close()
      self.output_iso = None
      self.changed_files = None
  
  def get_changed_file_data(self, file_path):
    if file_path in self.changed_files:
      return self.changed_files[file_path]
    else:
      return self.read_file_data(file_path)
  
  def add_new_file(self, file_path):
    assert file_path.lower() not in self.files_by_path_lowercase
    
    dirname = os.path.dirname(file_path)
    basename = os.path.basename(file_path)
    
    new_file = FileEntry()
    new_file.name = basename
    new_file.file_path = file_path
    new_file.file_data_offset = None
    new_file.file_size = None
    new_file.vanilla_file_data_offset = (1<<32) # Order new files to be written after vanilla files in the ISO
    
    parent_dir = self.get_dir_file_entry(dirname)
    parent_dir.children.append(new_file)
    new_file.parent = parent_dir
  
  def pad_output_iso_by(self, amount):
    self.output_iso.write(b"\0"*amount)
  
  def align_output_iso_to_nearest(self, size):
    current_offset = self.output_iso.tell()
    next_offset = current_offset + (size - current_offset % size) % size
    padding_needed = next_offset - current_offset
    self.pad_output_iso_by(padding_needed)
  
  def export_system_data_to_iso(self):
    boot_bin_data = self.get_changed_file_data("sys/boot.bin")
    assert data_len(boot_bin_data) == 0x440
    self.output_iso.seek(0)
    boot_bin_data.seek(0)
    self.output_iso.write(boot_bin_data.read())
    
    bi2_data = self.get_changed_file_data("sys/bi2.bin")
    assert data_len(bi2_data) == 0x2000
    self.output_iso.seek(0x440)
    bi2_data.seek(0)
    self.output_iso.write(bi2_data.read())
    
    apploader_data = self.get_changed_file_data("sys/apploader.img")
    apploader_header_size = 0x20
    apploader_size = read_u32(apploader_data, 0x14)
    apploader_trailer_size = read_u32(apploader_data, 0x18)
    apploader_full_size = apploader_header_size + apploader_size + apploader_trailer_size
    assert data_len(apploader_data) == apploader_full_size
    self.output_iso.seek(0x2440)
    apploader_data.seek(0)
    self.output_iso.write(apploader_data.read())
    
    self.pad_output_iso_by(0x20)
    self.align_output_iso_to_nearest(0x100)
    
    dol_offset = self.output_iso.tell()
    dol_data = self.get_changed_file_data("sys/main.dol")
    dol_size = data_len(dol_data)
    dol_data.seek(0)
    self.output_iso.write(dol_data.read())
    write_u32(self.output_iso, 0x420, dol_offset)
    self.output_iso.seek(dol_offset + dol_size)
    
    self.pad_output_iso_by(0x20)
    self.align_output_iso_to_nearest(0x100)
    
    
    # Write the FST and FNT to the ISO.
    # File offsets and file sizes are left at 0, they will be filled in as the actual file data is written to the ISO.
    self.recalculate_file_entry_indexes()
    self.fst_offset = self.output_iso.tell()
    write_u32(self.output_iso, 0x424, self.fst_offset)
    self.fnt_offset = self.fst_offset + len(self.file_entries)*0xC
    
    file_entry_offset = self.fst_offset
    next_name_offset = self.fnt_offset
    for file_index, file_entry in enumerate(self.file_entries):
      file_entry.name_offset = next_name_offset - self.fnt_offset
      
      is_dir_and_name_offset = 0
      if file_entry.is_dir:
        is_dir_and_name_offset |= 0x01000000
      is_dir_and_name_offset |= (file_entry.name_offset & 0x00FFFFFF)
      write_u32(self.output_iso, file_entry_offset, is_dir_and_name_offset)
      
      if file_entry.is_dir:
        write_u32(self.output_iso, file_entry_offset+4, file_entry.parent_fst_index)
        write_u32(self.output_iso, file_entry_offset+8, file_entry.next_fst_index)
      
      file_entry_offset += 0xC
      
      if file_index != 0: # Root doesn't have a name
        write_str_with_null_byte(self.output_iso, next_name_offset, file_entry.name)
        next_name_offset += len(file_entry.name)+1
    
    self.fst_size = self.output_iso.tell() - self.fst_offset
    write_u32(self.output_iso, 0x428, self.fst_size)
    write_u32(self.output_iso, 0x42C, self.fst_size) # Seems to be a duplicate size field that must also be updated
    self.output_iso.seek(self.fst_offset + self.fst_size)
  
  def recalculate_file_entry_indexes(self):
    root = self.file_entries[0]
    assert root.file_index == 0
    self.file_entries = []
    self.recalculate_file_entry_indexes_recursive(root)
  
  def recalculate_file_entry_indexes_recursive(self, curr_file_entry):
    curr_file_entry.file_index = len(self.file_entries)
    self.file_entries.append(curr_file_entry)
    if curr_file_entry.is_dir:
      if curr_file_entry.file_index != 0: # Root has no parent
        curr_file_entry.parent_fst_index = curr_file_entry.parent.file_index
      
      for child_file_entry in curr_file_entry.children:
        self.recalculate_file_entry_indexes_recursive(child_file_entry)
      
      curr_file_entry.next_fst_index = len(self.file_entries)
  
  def export_filesystem_to_iso(self):
    # Updates file offsets and sizes in the FST, and writes the files to the ISO.
    
    file_data_start_offset = self.fst_offset + self.fst_size
    self.output_iso.seek(file_data_start_offset)
    self.align_output_iso_to_nearest(4)
    
    # Instead of writing the file data in the order of file entries, write them in the order they were written in the vanilla ISO.
    # This increases the speed the game loads file for some unknown reason.
    file_entries_by_data_order = [
      file_entry for file_entry in self.file_entries
      if not file_entry.is_dir
    ]
    file_entries_by_data_order.sort(key=lambda fe: fe.vanilla_file_data_offset)
    
    for file_entry in file_entries_by_data_order:
      current_file_start_offset = self.output_iso.tell()
      
      if file_entry.file_path in self.changed_files:
        file_data = self.changed_files[file_entry.file_path]
        file_data.seek(0)
        self.output_iso.write(file_data.read())
      else:
        # Unchanged file.
        # Most of the game's data falls into this category, so we read the data directly instead of calling read_file_data which would create a BytesIO object, which would add unnecessary performance overhead.
        # Also, we need to read very large files in chunks to avoid running out of memory.
        size_remaining = file_entry.file_size
        offset_in_file = 0
        while size_remaining > 0:
          size_to_read = min(size_remaining, MAX_DATA_SIZE_TO_READ_AT_ONCE)
          
          with open(self.iso_path, "rb") as iso_file:
            data = read_bytes(iso_file, file_entry.file_data_offset + offset_in_file, size_to_read)
          self.output_iso.write(data)
          
          size_remaining -= size_to_read
          offset_in_file += size_to_read
      
      file_entry_offset = self.fst_offset + file_entry.file_index*0xC
      file_entry.file_data_offset = current_file_start_offset
      write_u32(self.output_iso, file_entry_offset+4, current_file_start_offset)
      if file_entry.file_path in self.changed_files:
        file_size = data_len(self.changed_files[file_entry.file_path])
      else:
        file_size = file_entry.file_size
      file_entry.file_size = file_size
      write_u32(self.output_iso, file_entry_offset+8, file_size)
      
      self.output_iso.seek(current_file_start_offset + file_size)
      
      self.align_output_iso_to_nearest(4)

class FileEntry:
  def __init__(self):
    self.file_index = None
    
    self.is_dir = False
  
  def read(self, file_index, iso_file, file_entry_offset, fnt_offset):
    self.file_index = file_index
    
    is_dir_and_name_offset = read_u32(iso_file, file_entry_offset)
    file_data_offset_or_parent_fst_index = read_u32(iso_file, file_entry_offset+4)
    file_size_or_next_fst_index = read_u32(iso_file, file_entry_offset+8)
    
    self.is_dir = ((is_dir_and_name_offset & 0xFF000000) != 0)
    self.name_offset = (is_dir_and_name_offset & 0x00FFFFFF)
    self.name = ""
    if self.is_dir:
      self.parent_fst_index = file_data_offset_or_parent_fst_index
      self.next_fst_index = file_size_or_next_fst_index
      self.children = []
    else:
      self.file_data_offset = file_data_offset_or_parent_fst_index
      self.vanilla_file_data_offset = file_data_offset_or_parent_fst_index
      self.file_size = file_size_or_next_fst_index
    self.parent = None
    
    if file_index == 0:
      self.name = "" # Root
    else:
      self.name = read_str_until_null_character(iso_file, fnt_offset + self.name_offset)

class SystemFile:
  def __init__(self, file_data_offset, file_size):
    self.file_data_offset = file_data_offset
    self.file_size = file_size
