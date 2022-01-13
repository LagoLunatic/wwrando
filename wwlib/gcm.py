
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
    self.changed_files = {}
  
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
    root_file_entry.file_path = "files"
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
        file_entry.file_path = subdir_path
        self.read_directory(file_entry, subdir_path)
        i = file_entry.next_fst_index
      else:
        file_path = dir_path + "/" + file_entry.name
        self.files_by_path[file_path] = file_entry
        file_entry.file_path = file_path
        i += 1
  
  def read_system_data(self):
    self.files_by_path["sys/boot.bin"] = SystemFile(0, 0x440, "boot.bin")
    self.files_by_path["sys/bi2.bin"] = SystemFile(0x440, 0x2000, "bi2.bin")
    
    apploader_header_size = 0x20
    apploader_size = read_u32(self.iso_file, 0x2440 + 0x14)
    apploader_trailer_size = read_u32(self.iso_file, 0x2440 + 0x18)
    apploader_full_size = apploader_header_size + apploader_size + apploader_trailer_size
    self.files_by_path["sys/apploader.img"] = SystemFile(0x2440, apploader_full_size, "apploader.img")
    
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
    self.files_by_path["sys/main.dol"] = SystemFile(dol_offset, main_dol_size, "main.dol")
    
    self.files_by_path["sys/fst.bin"] = SystemFile(self.fst_offset, self.fst_size, "fst.bin")
    
    self.system_files = [
      self.files_by_path["sys/boot.bin"],
      self.files_by_path["sys/bi2.bin"],
      self.files_by_path["sys/apploader.img"],
      self.files_by_path["sys/main.dol"],
      self.files_by_path["sys/fst.bin"],
    ]
  
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
  
  def get_or_create_dir_file_entry(self, dir_path):
    if dir_path.lower() in self.dirs_by_path_lowercase:
      return self.dirs_by_path_lowercase[dir_path.lower()]
    else:
      return self.add_new_directory(dir_path)
  
  def import_all_files_from_disk(self, input_directory):
    num_files_overwritten = 0
    
    for file_path, file_entry in self.files_by_path.items():
      full_file_path = os.path.join(input_directory, file_path)
      if os.path.isfile(full_file_path):
        with open(full_file_path, "rb") as f:
          self.changed_files[file_path] = BytesIO(f.read())
          num_files_overwritten += 1
    
    return num_files_overwritten
  
  def export_disc_to_folder_with_changed_files(self, output_folder_path, only_changed_files=False):
    files_done = 0
    
    for file_path, file_entry in self.files_by_path.items():
      full_file_path = os.path.join(output_folder_path, file_path)
      dir_name = os.path.dirname(full_file_path)
      
      if file_path in self.changed_files:
        if not os.path.isdir(dir_name):
          os.makedirs(dir_name)
        
        file_data = self.changed_files[file_path]
        with open(full_file_path, "wb") as f:
          file_data.seek(0)
          f.write(file_data.read())
      else:
        if only_changed_files:
          continue
        if not os.path.isdir(dir_name):
          os.makedirs(dir_name)
        
        # Need to avoid reading enormous files all at once
        size_remaining = file_entry.file_size
        offset_in_file = 0
        with open(full_file_path, "wb") as f:
          while size_remaining > 0:
            size_to_read = min(size_remaining, MAX_DATA_SIZE_TO_READ_AT_ONCE)
            
            with open(self.iso_path, "rb") as iso_file:
              data = read_bytes(iso_file, file_entry.file_data_offset + offset_in_file, size_to_read)
            f.write(data)
            
            size_remaining -= size_to_read
            offset_in_file += size_to_read
      
      files_done += 1
      yield(file_path, files_done)
    
    yield("Done", -1)
  
  def export_disc_to_iso_with_changed_files(self, output_file_path):
    if os.path.realpath(self.iso_path) == os.path.realpath(output_file_path):
      raise Exception("Input ISO path and output ISO path are the same. Aborting.")
    
    self.output_iso = open(output_file_path, "wb")
    try:
      self.export_system_data_to_iso()
      yield("sys/main.dol", 5) # 5 system files
      
      generator = self.export_filesystem_to_iso()
      while True:
        # Need to use a while loop to go through the generator instead of a for loop, as a for loop would silently exit if a StopIteration error ever happened for any reason.
        next_progress_text, files_done = next(generator)
        if files_done == -1:
          break
        yield(next_progress_text, 5+files_done)
      
      self.align_output_iso_to_nearest(2048)
      self.output_iso.close()
      self.output_iso = None
      yield("Done", -1)
    except Exception:
      print("Error writing GCM, removing failed ISO.")
      self.output_iso.close()
      self.output_iso = None
      os.remove(output_file_path)
      raise
  
  def get_changed_file_data(self, file_path):
    if file_path in self.changed_files:
      return self.changed_files[file_path]
    else:
      return self.read_file_data(file_path)
  
  def add_new_directory(self, dir_path):
    assert dir_path.lower() not in self.dirs_by_path_lowercase
    
    parent_dir_name = os.path.dirname(dir_path)
    new_dir_name = os.path.basename(dir_path)
    
    new_dir = FileEntry()
    new_dir.is_dir = True
    new_dir.name = new_dir_name
    new_dir.file_path = dir_path
    new_dir.parent_fst_index = None # Recalculated if needed
    new_dir.next_fst_index = None # Recalculated if needed
    new_dir.children = []
    
    parent_dir = self.get_or_create_dir_file_entry(parent_dir_name)
    parent_dir.children.append(new_dir)
    new_dir.parent = parent_dir
    
    self.dirs_by_path[dir_path] = new_dir
    self.dirs_by_path_lowercase[dir_path.lower()] = new_dir
    
    return new_dir
  
  def add_new_file(self, file_path, file_data=None):
    assert file_path.lower() not in self.files_by_path_lowercase
    
    dirname = os.path.dirname(file_path)
    basename = os.path.basename(file_path)
    
    new_file = FileEntry()
    new_file.name = basename
    new_file.file_path = file_path
    # file_data_offset is used for ordering the files in the new ISO, so we give it a huge value so new files are placed after vanilla files.
    new_file.file_data_offset = (1<<32)
    new_file.file_size = None # No original file size.
    
    parent_dir = self.get_or_create_dir_file_entry(dirname)
    parent_dir.children.append(new_file)
    new_file.parent = parent_dir
    
    if file_data is None:
      self.changed_files[file_path] = None
    else:
      self.changed_files[file_path] = file_data
    
    self.files_by_path[file_path] = new_file
    self.files_by_path_lowercase[file_path.lower()] = new_file
    
    return new_file
  
  def delete_directory(self, dir_entry):
    # Delete all children first.
    # Note that looping over a copy of the children list is necessary because the list gets modified as each child is removed.
    for child_entry in dir_entry.children.copy():
      if child_entry.is_dir:
        self.delete_directory(child_entry)
      else:
        self.delete_file(child_entry)
        
    parent_dir = dir_entry.parent
    parent_dir.children.remove(dir_entry)
    
    del self.dirs_by_path[dir_entry.file_path]
    del self.dirs_by_path_lowercase[dir_entry.file_path.lower()]
  
  def delete_file(self, file_entry):
    parent_dir = file_entry.parent
    parent_dir.children.remove(file_entry)
    
    del self.files_by_path[file_entry.file_path]
    del self.files_by_path_lowercase[file_entry.file_path.lower()]
    if file_entry.file_path in self.changed_files:
      del self.changed_files[file_entry.file_path]
  
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
    file_entries_by_data_order.sort(key=lambda fe: fe.file_data_offset)
    
    files_done = 0
    
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
      write_u32(self.output_iso, file_entry_offset+4, current_file_start_offset)
      if file_entry.file_path in self.changed_files:
        file_size = data_len(self.changed_files[file_entry.file_path])
      else:
        file_size = file_entry.file_size
      write_u32(self.output_iso, file_entry_offset+8, file_size)
      
      # Note: The file_data_offset and file_size fields of the FileEntry must not be updated, they refer only to the offset and size of the file data in the input ISO, not this output ISO.
      
      self.output_iso.seek(current_file_start_offset + file_size)
      
      self.align_output_iso_to_nearest(4)
      
      files_done += 1
      yield(file_entry.file_path, files_done)
    
    yield("Done", -1)

class FileEntry:
  def __init__(self):
    self.file_index = None
    
    self.is_dir = False
    self.is_system_file = False
  
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
      self.file_size = file_size_or_next_fst_index
    self.parent = None
    
    if file_index == 0:
      self.name = "" # Root
    else:
      self.name = read_str_until_null_character(iso_file, fnt_offset + self.name_offset)

class SystemFile:
  def __init__(self, file_data_offset, file_size, name):
    self.file_data_offset = file_data_offset
    self.file_size = file_size
    
    self.name = name
    self.file_path = "sys/" + name
    
    self.is_dir = False
    self.is_system_file = True
