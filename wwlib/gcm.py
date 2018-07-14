
import os
from io import BytesIO

from fs_helpers import *

MAX_DATA_SIZE_TO_READ_AT_ONCE = 64*1024*1024 # 64MB

class GCM:
  def __init__(self, iso_path):
    self.iso_path = iso_path
    self.files_by_path = {}
    self.files_by_path_lowercase = {}
  
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
  
  def read_filesystem(self):
    self.file_entries = []
    num_file_entries = read_u32(self.iso_file, self.fst_offset + 8)
    self.fnt_offset = self.fst_offset + num_file_entries*0xC
    for i in range(num_file_entries):
      file_entry_offset = self.fst_offset + i * 0xC
      file_entry = FileEntry(i, self.iso_file, file_entry_offset, self.fnt_offset)
      self.file_entries.append(file_entry)
    
    root_file_entry = self.file_entries[0]
    self.read_directory(root_file_entry, "files")
  
  def read_directory(self, directory_file_entry, dir_path):
    assert directory_file_entry.is_dir
    
    i = directory_file_entry.file_index + 1
    while i < directory_file_entry.next_fst_index:
      file_entry = self.file_entries[i]
      if file_entry.is_dir:
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
  
  def export_iso_with_changed_files(self, output_file_path, changed_files):
    self.output_iso = open(output_file_path, "wb")
    self.changed_files = changed_files
    try:
      self.export_system_data_to_iso()
      self.export_filesystem_to_iso()
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
    
    # This just writes the original FST to the ISO.
    # This will be updated with proper offsets as each file itself is written to the ISO.
    self.fst_offset = self.output_iso.tell()
    fst_data = self.get_changed_file_data("sys/fst.bin")
    self.fst_size = data_len(fst_data)
    fst_data.seek(0)
    self.output_iso.write(fst_data.read())
    write_u32(self.output_iso, 0x424, self.fst_offset)
    self.output_iso.seek(self.fst_offset + self.fst_size)
  
  def export_filesystem_to_iso(self):
    # Updates file offsets and sizes in the FST, and writes the files to the ISO.
    # Note that adding/removing/renaming files is not supported.
    
    file_data_start_offset = self.fst_offset + self.fst_size
    self.output_iso.seek(file_data_start_offset)
    self.align_output_iso_to_nearest(4)
    
    for file_entry in self.file_entries:
      if file_entry.is_dir:
        continue
      
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
      
      self.output_iso.seek(current_file_start_offset + file_size)
      
      self.align_output_iso_to_nearest(4)

class FileEntry:
  def __init__(self, file_index, iso_file, file_entry_offset, fnt_offset):
    self.file_index = file_index
    
    is_dir_and_name_offset = read_u32(iso_file, file_entry_offset)
    self.file_data_offset = read_u32(iso_file, file_entry_offset+4)
    file_size_or_next_fst_index = read_u32(iso_file, file_entry_offset+8)
    
    self.is_dir = ((is_dir_and_name_offset & 0xFF000000) != 0)
    self.name_offset = (is_dir_and_name_offset & 0x00FFFFFF)
    self.name = ""
    if self.is_dir:
      self.next_fst_index = file_size_or_next_fst_index
    else:
      self.file_size = file_size_or_next_fst_index
    
    if file_index == 0:
      self.name = "" # Root
    else:
      self.name = read_str_until_null_character(iso_file, fnt_offset + self.name_offset)

class SystemFile:
  def __init__(self, file_data_offset, file_size):
    self.file_data_offset = file_data_offset
    self.file_size = file_size
