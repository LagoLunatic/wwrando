
from fs_helpers import *
from wwlib.yaz0 import Yaz0

from io import BytesIO
from collections import OrderedDict
from enum import Enum

class REL:
  def __init__(self):
    self.id = None
    self.sections = []
    self.name_offset = 0
    self.name_length = 0
    self.rel_format_version = 3
    
    self.relocation_entries_for_module = OrderedDict()
    
    self.prolog_section = 0
    self.epilog_section = 0
    self.unresolved_section = 0
    self.prolog_offset = 0
    self.epilog_offset = 0
    self.unresolved_offset = 0
    
    self.alignment = 8
    self.bss_alignment = 1
    self.fix_size = 0
  
  def read_from_file(self, file_path):
    with open(file_path, "rb") as file:
      data = BytesIO(file.read())
    
    self.read(data)
  
  def read(self, data):
    self.data = data
    
    if try_read_str(self.data, 0, 4) == "Yaz0":
      self.data = Yaz0.decompress(self.data)
    
    data = self.data
    
    self.id = read_u32(data, 0)
    
    self.sections = []
    self.num_sections = read_u32(data, 0xC)
    self.section_info_table_offset = read_u32(data, 0x10)
    for section_index in range(0, self.num_sections):
      section_info_offset = self.section_info_table_offset + section_index*RELSection.ENTRY_SIZE
      section = RELSection()
      section.read(data, section_info_offset)
      self.sections.append(section)
    
    self.name_offset = read_u32(data, 0x14)
    self.name_length = read_u32(data, 0x18)
    self.rel_format_version = read_u32(data, 0x1C)
    
    relocation_data_offset_for_module = OrderedDict()
    self.relocation_table_offset = read_u32(data, 0x24)
    self.imp_table_offset = read_u32(data, 0x28)
    self.imp_table_length = read_u32(data, 0x2C)
    offset = self.imp_table_offset
    while offset < self.imp_table_offset + self.imp_table_length:
      module_num = read_u32(data, offset)
      relocation_data_offset = read_u32(data, offset+4)
      relocation_data_offset_for_module[module_num] = relocation_data_offset
      offset += 8
    
    self.relocation_entries_for_module = OrderedDict()
    curr_section_num = None
    for module_num, relocation_data_offset in relocation_data_offset_for_module.items():
      self.relocation_entries_for_module[module_num] = []
      
      offset = relocation_data_offset
      prev_relocation_offset = 0
      while True:
        relocation_type = RELRelocationType(read_u8(data, offset+2))
        if relocation_type == RELRelocationType.R_DOLPHIN_END:
          break
        
        relocation_data_entry = RELRelocation()
        relocation_data_entry.read(data, offset, prev_relocation_offset, curr_section_num)
        prev_relocation_offset = relocation_data_entry.relocation_offset
        
        if relocation_data_entry.relocation_type == RELRelocationType.R_DOLPHIN_SECTION:
          curr_section_num = relocation_data_entry.section_num_to_relocate_against
          prev_relocation_offset = 0
        else:
          self.relocation_entries_for_module[module_num].append(relocation_data_entry)
        
        offset += RELRelocation.ENTRY_SIZE
    
    self.prolog_section = read_u8(data, 0x30)
    self.epilog_section = read_u8(data, 0x31)
    self.unresolved_section = read_u8(data, 0x32)
    self.prolog_offset = read_u32(data, 0x34)
    self.epilog_offset = read_u32(data, 0x38)
    self.unresolved_offset = read_u32(data, 0x3C)
    
    self.alignment = read_u32(data, 0x40)
    self.bss_alignment = read_u32(data, 0x44)
    
    # Space after this fix_size offset can be reused for other purposes.
    # Such as using the space that originally had the relocations list for .bss static variables instead.
    self.fix_size = read_u32(data, 0x48)
    self.fix_size = (self.fix_size + 0x1F) & ~(0x1F) # Round up to nearest 0x20
    
    self.bss_section_index = None # The byte at offset 0x33 in the REL is reserved for this value at runtime.
    for section_index, section in enumerate(self.sections):
      if section.is_bss:
        self.bss_section_index = section_index
        section.offset = self.fix_size
        break
  
  def save_to_file(self, file_path):
    self.save_changes()
    
    with open(file_path, "wb") as f:
      f.write(read_all_bytes(self.data))
  
  def save_changes(self):
    self.data.truncate(0)
    data = self.data
    
    write_u32(data, 0x00, self.id)
    write_u32(data, 0x04, 0)
    write_u32(data, 0x08, 0)
    self.num_sections = len(self.sections)
    write_u32(data, 0x0C, self.num_sections)
    write_u32(data, 0x14, self.name_offset)
    write_u32(data, 0x18, self.name_length)
    write_u32(data, 0x1C, self.rel_format_version)
    
    self.section_info_table_offset = 0x4C
    write_u32(data, 0x10, self.section_info_table_offset)
    next_section_info_offset = self.section_info_table_offset
    next_section_data_offset = self.section_info_table_offset + self.num_sections*RELSection.ENTRY_SIZE
    next_section_data_offset = pad_offset_to_nearest(next_section_data_offset, 4) # TODO why is 4 more accurate here than the 8 from self.alignment?
    for section in self.sections:
      section.save(data, next_section_info_offset, next_section_data_offset, 4)
      next_section_info_offset += RELSection.ENTRY_SIZE
      next_section_data_offset += section.length
    
    self.imp_table_offset = data_len(data)
    imp_table_size = len(self.relocation_entries_for_module)*8
    imp_table_end = self.imp_table_offset + imp_table_size
    self.relocation_table_offset = imp_table_end
    write_u32(data, 0x24, self.relocation_table_offset)
    write_u32(data, 0x28, self.imp_table_offset)
    write_u32(data, 0x2C, imp_table_size)
    next_imp_offset = self.imp_table_offset
    next_relocation_entry_offset = self.relocation_table_offset
    for module_num, relocation_data_entries in self.relocation_entries_for_module.items():
      write_u32(data, next_imp_offset+0x00, module_num)
      write_u32(data, next_imp_offset+0x04, next_relocation_entry_offset)
      next_imp_offset += 8
      
      # TODO: sort the relocation_data_entries by curr_section_num to reduce the number of section number switches we need to do
      curr_section_num = None
      prev_relocation_offset = 0
      for relocation_data_entry in relocation_data_entries:
        if relocation_data_entry.curr_section_num != curr_section_num:
          curr_section_num = relocation_data_entry.curr_section_num
          prev_relocation_offset = 0
          
          section_start_entry = RELRelocation()
          section_start_entry.relocation_type = RELRelocationType.R_DOLPHIN_SECTION
          section_start_entry.section_num_to_relocate_against = curr_section_num
          
          section_start_entry.save(data, next_relocation_entry_offset)
          next_relocation_entry_offset += RELRelocation.ENTRY_SIZE
        
        offset_diff = relocation_data_entry.relocation_offset - prev_relocation_offset
        while offset_diff > 0xFFFF:
          # The offset change is stored as a halfword, so if the gap is too large, we must insert a NOP command (or several) to bridge the gap.
          nop_entry = RELRelocation()
          nop_entry.relocation_type = RELRelocationType.R_DOLPHIN_NOP
          
          relocation_data_entry.relocation_offset = prev_relocation_offset + 0xFFFF
          relocation_data_entry.offset_of_curr_relocation_from_prev = 0xFFFF
          nop_entry.save(data, next_relocation_entry_offset)
          prev_relocation_offset = relocation_data_entry.relocation_offset
          next_relocation_entry_offset += RELRelocation.ENTRY_SIZE
          
          offset_diff -= 0xFFFF
        
        relocation_data_entry.offset_of_curr_relocation_from_prev = offset_diff
        relocation_data_entry.save(data, next_relocation_entry_offset)
        prev_relocation_offset = relocation_data_entry.relocation_offset
        next_relocation_entry_offset += RELRelocation.ENTRY_SIZE
      
      table_end_entry = RELRelocation()
      table_end_entry.relocation_type = RELRelocationType.R_DOLPHIN_END
      table_end_entry.section_num_to_relocate_against = curr_section_num
      
      table_end_entry.save(data, next_relocation_entry_offset)
      next_relocation_entry_offset += RELRelocation.ENTRY_SIZE
    
    write_u8(data, 0x30, self.prolog_section)
    write_u8(data, 0x31, self.epilog_section)
    write_u8(data, 0x32, self.unresolved_section)
    write_u32(data, 0x34, self.prolog_offset)
    write_u32(data, 0x38, self.epilog_offset)
    write_u32(data, 0x3C, self.unresolved_offset)
    
    write_u32(data, 0x40, self.alignment)
    write_u32(data, 0x44, self.bss_alignment)
    # TODO: align bss to the bss_alignment
    
    if self.fix_size == 0:
      # TODO how to properly detect what fix_size should be? this current method is a total hack
      self.fix_size = self.relocation_table_offset
    write_u32(data, 0x48, self.fix_size)

class RELSection:
  ENTRY_SIZE = 8
  
  def __init__(self):
    self.offset = None
    self.is_executable = False
    self.length = 0
    self.is_uninitialized = True
    self.is_bss = False
    self.data = BytesIO()
  
  def read(self, rel_data, info_offset):
    self.info_offset = info_offset
    
    mult_vals = read_u32(rel_data, info_offset + 0x00)
    self.offset = mult_vals & 0xFFFFFFFC
    if mult_vals & 1:
      self.is_executable = True
    else:
      self.is_executable = False
    self.length = read_u32(rel_data, info_offset + 0x04)
    
    if self.offset == 0:
      self.is_uninitialized = True
    else:
      self.is_uninitialized = False
    
    if self.is_uninitialized and not self.is_executable and self.length != 0:
      self.is_bss = True
    else:
      self.is_bss = False
      
      if self.length != 0:
        self.data = BytesIO(read_bytes(rel_data, self.offset, self.length))
  
  def save(self, rel_data, info_offset, next_section_data_offset, alignment):
    if self.is_uninitialized:
      self.offset = 0
    else:
      self.offset = next_section_data_offset & 0xFFFFFFFC
    mult_vals = self.offset
    if self.is_executable:
      mult_vals |= 1
    write_u32(rel_data, info_offset+0x00, mult_vals)
    
    align_data_to_nearest(self.data, alignment)
    self.length = data_len(self.data)
    write_u32(rel_data, info_offset+0x04, self.length)
    
    if not self.is_bss and self.length != 0 and not self.is_uninitialized:
      write_bytes(rel_data, self.offset, read_all_bytes(self.data))

class RELRelocation:
  ENTRY_SIZE = 8
  
  def __init__(self):
    self.offset = None
    self.relocation_type = None
    self.section_num_to_relocate_against = None
    self.symbol_address = None
    self.relocation_offset = None
    self.curr_section_num = None
  
  def read(self, rel_data, offset, prev_relocation_offset, curr_section_num):
    self.offset_of_curr_relocation_from_prev = read_u16(rel_data, offset+0x00)
    self.relocation_type = RELRelocationType(read_u8(rel_data, offset+0x02))
    self.section_num_to_relocate_against = read_u8(rel_data, offset+0x03)
    self.symbol_address = read_u32(rel_data, offset+0x04)
    
    self.relocation_offset = self.offset_of_curr_relocation_from_prev + prev_relocation_offset
    self.curr_section_num = curr_section_num
  
  def save(self, rel_data, offset):
    if self.relocation_type == RELRelocationType.R_DOLPHIN_SECTION:
      self.offset_of_curr_relocation_from_prev = 0
      self.symbol_address = 0
    elif self.relocation_type == RELRelocationType.R_DOLPHIN_END:
      self.offset_of_curr_relocation_from_prev = 0
      self.section_num_to_relocate_against = 0
      self.symbol_address = 0
    elif self.relocation_type == RELRelocationType.R_DOLPHIN_NOP:
      self.section_num_to_relocate_against = 0
      self.symbol_address = 0
    
    write_u16(rel_data, offset+0x00, self.offset_of_curr_relocation_from_prev)
    write_u8(rel_data, offset+0x02, self.relocation_type.value)
    write_u8(rel_data, offset+0x03, self.section_num_to_relocate_against)
    write_u32(rel_data, offset+0x04, self.symbol_address)

class RELRelocationType(Enum):
  R_PPC_NONE = 0x00
  R_PPC_ADDR32 = 0x01
  R_PPC_ADDR24 = 0x02
  R_PPC_ADDR16 = 0x03
  R_PPC_ADDR16_LO = 0x04
  R_PPC_ADDR16_HI = 0x05
  R_PPC_ADDR16_HA = 0x06
  R_PPC_ADDR14 = 0x07
  R_PPC_ADDR14_BRTAKEN = 0x08
  R_PPC_ADDR14_BRNTAKEN = 0x09
  R_PPC_REL24 = 0x0A
  R_PPC_REL14 = 0x0B
  R_PPC_REL14_BRTAKEN = 0x0C
  R_PPC_REL14_BRNTAKEN = 0x0D
  
  R_DOLPHIN_NOP = 0xC9
  R_DOLPHIN_SECTION = 0xCA
  R_DOLPHIN_END = 0xCB
  R_DOLPHIN_MRKREF = 0xCC
