
import os
from fs_helpers import *

class GCM:
  def __init__(self, file_path):
    self.file_path = file_path
  
  def extract_disc(self, output_dir):
    if os.path.exists(output_dir):
      raise Exception("Output directory already exists: %s" % output_dir)
    os.makedirs(output_dir)
    
    self.iso_file = open(self.file_path, "rb")
    
    try:
      files_path = os.path.join(output_dir, "files")
      sys_path = os.path.join(output_dir, "sys")
      self.fst_offset = read_u32(self.iso_file, 0x424)
      self.extract_filesystem(files_path)
      self.extract_system_data(sys_path)
    finally:
      self.iso_file.close()
  
  def extract_filesystem(self, output_dir):
    self.file_entries = []
    num_file_entries = read_u32(self.iso_file, self.fst_offset + 8)
    self.fnt_offset = self.fst_offset + num_file_entries*0xC
    for i in range(num_file_entries):
      file_entry_offset = self.fst_offset + i * 0xC
      file_entry = FileEntry(i, self.iso_file, file_entry_offset, self.fnt_offset)
      self.file_entries.append(file_entry)
    
    root_file_entry = self.file_entries[0]
    self.extract_directory(root_file_entry, output_dir)
  
  def extract_directory(self, directory_file_entry, output_dir):
    assert directory_file_entry.is_dir
    
    i = directory_file_entry.file_index + 1
    while i < directory_file_entry.next_fst_index:
      file_entry = self.file_entries[i]
      if file_entry.is_dir:
        subdir_path = os.path.join(output_dir, file_entry.name)
        #print("Writing directory %s" % subdir_path)
        os.makedirs(subdir_path)
        self.extract_directory(file_entry, subdir_path)
        i = file_entry.next_fst_index
      else:
        file_path = os.path.join(output_dir, file_entry.name)
        #print("Writing file %s" % file_path)
        file_data = read_bytes(self.iso_file, file_entry.file_data_offset, file_entry.file_size)
        with open(file_path, "wb") as f:
          f.write(file_data)
        i += 1
  
  def extract_system_data(self, output_dir):
    os.makedirs(output_dir)
    
    self.extract_file(0, 0x440, os.path.join(output_dir, "boot.bin"))
    self.extract_file(0x440, 0x2000, os.path.join(output_dir, "bi2.bin"))
    
    apploader_header_size = 0x20
    apploader_size = read_u32(self.iso_file, 0x2440 + 0x14)
    apploader_trailer_size = read_u32(self.iso_file, 0x2440 + 0x18)
    apploader_full_size = apploader_header_size + apploader_size + apploader_trailer_size
    self.extract_file(0x2440, apploader_full_size, os.path.join(output_dir, "apploader.img"))
    
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
    self.extract_file(dol_offset, main_dol_size, os.path.join(output_dir, "main.dol"))
    
    fst_size = read_u32(self.iso_file, 0x428)
    self.extract_file(self.fst_offset, fst_size, os.path.join(output_dir, "fst.bin"))
  
  def extract_file(self, offset, size, output_path):
    data = read_bytes(self.iso_file, offset, size)
    with open(output_path, "wb") as f:
      f.write(data)

class FileEntry:
  def __init__(self, file_index, iso_file, file_entry_offset, fnt_offset):
    self.file_index = file_index
    
    is_dir_and_name_offset = read_u32(iso_file, file_entry_offset)
    file_data_offset = read_u32(iso_file, file_entry_offset+4)
    file_size_or_next_fst_index = read_u32(iso_file, file_entry_offset+8)
    
    self.is_dir = ((is_dir_and_name_offset & 0xFF000000) != 0)
    self.name_offset = (is_dir_and_name_offset & 0x00FFFFFF)
    self.name = ""
    self.file_data_offset = file_data_offset
    if self.is_dir:
      self.next_fst_index = file_size_or_next_fst_index
    else:
      self.file_size = file_size_or_next_fst_index
    
    if file_index == 0:
      self.name = "" # Root
    else:
      self.name = read_str_until_null_character(iso_file, fnt_offset + self.name_offset)
