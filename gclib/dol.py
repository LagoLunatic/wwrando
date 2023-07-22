
from fs_helpers import *

class DOL:
  TEXT_SECTION_COUNT = 7
  DATA_SECTION_COUNT = 11
  
  def __init__(self):
    self.data = BytesIO()
    
    self.sections = []
    
    self.bss_address = 0
    self.bss_size = 0
    self.entry_point_address = 0
  
  def read(self, data):
    self.data = data
    
    self.sections = []
    for section_index in range(DOL.TEXT_SECTION_COUNT + DOL.DATA_SECTION_COUNT):
      section_offset  = read_u32(data, 0x00 + section_index*4)
      section_address = read_u32(data, 0x48 + section_index*4)
      section_size    = read_u32(data, 0x90 + section_index*4)
      
      section = DOLSection(section_offset, section_address, section_size)
      self.sections.append(section)
    
    self.bss_address = read_u32(data, 0xD8)
    self.bss_size = read_u32(data, 0xDC)
    self.entry_point_address = read_u32(data, 0xE0)
    
    for i in range(7):
      assert read_u32(data, 0xE4 + i*4) == 0
  
  def convert_address_to_offset(self, address):
    for section in self.sections:
      if section.contains_address(address):
        offset = address - section.address + section.offset
        return offset
    
    return None
  
  def convert_offset_to_address(self, offset):
    for section in self.sections:
      if section.contains_offset(offset):
        address = offset - section.offset + section.address
        return address
    
    return None
  
  def convert_offset_to_section_index(self, offset):
    for section_index, section in enumerate(self.sections):
      if section.contains_offset(offset):
        return section_index
    
    return None
  
  def read_data(self, read_callback, address, *args):
    # This function allows reading from the DOL using the RAM address, instead of needing to know the offset within the DOL.
    
    offset = self.convert_address_to_offset(address)
    
    if offset is None:
      raise Exception("Address %08X is not in the data for any of the DOL sections" % address)
    
    return read_callback(self.data, offset, *args)
  
  def write_data(self, write_callback, address, *args):
    # This function allows writing to the DOL using the RAM address, instead of needing to know the offset within the DOL.
    
    offset = self.convert_address_to_offset(address)
    
    if offset is None:
      raise Exception("Address %08X is not in the data for any of the DOL sections" % address)
    
    write_callback(self.data, offset, *args)
  
  def save_changes(self):
    data = self.data
    
    for section_index, section in enumerate(self.sections):
      write_u32(data, 0x00 + section_index*4, section.offset)
      write_u32(data, 0x48 + section_index*4, section.address)
      write_u32(data, 0x90 + section_index*4, section.size)
    
    write_u32(data, 0xD8, self.bss_address)
    write_u32(data, 0xDC, self.bss_size)
    write_u32(data, 0xE0, self.entry_point_address)

class DOLSection:
  def __init__(self, offset, address, size):
    self.offset = offset
    self.address = address
    self.size = size
  
  def contains_address(self, address):
    if self.address <= address < self.address+self.size:
      return True
    else:
      return False
  
  def contains_offset(self, offset):
    if self.offset <= offset < self.offset+self.size:
      return True
    else:
      return False
