
from fs_helpers import *
from wwlib.yaz0_decomp import Yaz0Decompressor

from io import BytesIO

class REL:
  def __init__(self, file_path):
    self.file_path = file_path
    with open(self.file_path, "rb") as file:
      self.data = BytesIO(file.read())
    
    if try_read_str(self.data, 0, 4) == "Yaz0":
      self.data = Yaz0Decompressor.decompress(self.data)
    
    data = self.data
    
    self.id = read_u32(data, 0)
    
    self.sections = []
    self.num_sections = read_u32(data, 0xC)
    self.section_info_table_offset = read_u32(data, 0x10)
    for section_index in range(0, self.num_sections):
      section_info_offset = self.section_info_table_offset + section_index*8
      section = Section(data, section_info_offset)
      self.sections.append(section)
    
    self.relocation_data_offset_for_module = {}
    self.imp_table_offset = read_u32(data, 0x28)
    self.imp_table_length = read_u32(data, 0x2C)
    offset = self.imp_table_offset
    while offset < self.imp_table_offset + self.imp_table_length:
      module_num = read_u32(data, offset)
      relocation_data_offset = read_u32(data, offset+4)
      self.relocation_data_offset_for_module[module_num] = relocation_data_offset
      offset += 8
    
    self.relocation_entries_for_module = {}
    curr_section_num = None
    for module_num, relocation_data_offset in self.relocation_data_offset_for_module.items():
      self.relocation_entries_for_module[module_num] = []
      
      offset = relocation_data_offset
      prev_relocation_offset = 0
      while True:
        relocation_type = read_u8(data, offset+2)
        if relocation_type == 0xCB: # R_RVL_STOP
          break
        
        relocation_data_entry = RelocationDataEntry(data, offset, prev_relocation_offset, curr_section_num)
        prev_relocation_offset = relocation_data_entry.relocation_offset
        
        if relocation_data_entry.relocation_type == 0xCA: # R_RVL_SECT 
          curr_section_num = relocation_data_entry.section_num_to_relocate_against
          prev_relocation_offset = 0
        else:
          self.relocation_entries_for_module[module_num].append(relocation_data_entry)
        
        offset += 8

class Section:
  def __init__(self, data, info_offset):
    mult_vals = read_u32(data, info_offset)
    self.offset = mult_vals & 0xFFFFFFFC
    if mult_vals & 1:
      self.is_executable = True
    else:
      self.is_executable = False
    self.length = read_u32(data, info_offset+4)

class RelocationDataEntry:
  def __init__(self, data, offset, prev_relocation_offset, curr_section_num):
    self.offset = offset
    
    offset_of_curr_relocation_from_prev = read_u16(data, offset)
    self.relocation_type = read_u8(data, offset+2)
    self.section_num_to_relocate_against = read_u8(data, offset+3)
    self.symbol_address = read_u32(data, offset+4)
    
    self.relocation_offset = offset_of_curr_relocation_from_prev + prev_relocation_offset
    self.curr_section_num = curr_section_num
