
from fs_helpers import *

class DZx: # DZR or DZS, same format
  def __init__(self, file_entry):
    self.file_entry = file_entry
    data = self.file_entry.data
    
    num_chunks = read_u32(data, 0)
    
    self.chunks = []
    for chunk_index in range(0, num_chunks):
      offset = 4 + chunk_index*0xC
      chunk = Chunk(self.file_entry, offset)
      self.chunks.append(chunk)

  def save_changes(self):
    data = self.file_entry.data
    
    # TODO

class Chunk:
  def __init__(self, file_entry, offset):
    self.file_entry = file_entry
    data = self.file_entry.data
    self.offset = offset
    
    self.chunk_type = read_str(data, self.offset, 4)
    num_entries = read_u32(data, self.offset+4)
    first_entry_offset = read_u32(data, self.offset+8)
    
    self.entries = []
    
    entry_class = {
      "TRES": TRES,
    }.get(self.chunk_type, None)
    
    if entry_class is None:
      #print("Unknown chunk type:", self.chunk_type)
      return
    
    #print("First entry offset: %X" % first_entry_offset)
    
    entry_size = entry_class.DATA_SIZE
    
    for entry_index in range(0, num_entries):
      entry_offset = first_entry_offset + entry_index*entry_size
      entry = entry_class(self.file_entry, entry_offset)
      self.entries.append(entry)

class TRES:
  DATA_SIZE = 0x20
  
  def __init__(self, file_entry, offset):
    self.file_entry = file_entry
    data = self.file_entry.data
    self.offset = offset
    
    self.name = read_str(data, offset, 8)
    
    chest_type_and_prereq_upper_nibble = read_u8(data, offset+9)
    prereq_lower_nibble_and_unknown = read_u8(data, offset+0xA)
    self.chest_type = (chest_type_and_prereq_upper_nibble >> 4)
    self.appear_condition_flag_id = ((chest_type_and_prereq_upper_nibble & 0xF) << 4) | (prereq_lower_nibble_and_unknown >> 4)
    self.unknown = (prereq_lower_nibble_and_unknown & 0xF) # flag for having picked this up?
    
    self.appear_condition = read_u8(data, offset+0xB)
    
    self.item_id = read_u8(data, offset+0x1C)
    self.flag_id = read_u8(data, offset+0x1D) # nothing??
    
  def save_changes(self):
    data = self.file_entry.data
    
    chest_type_and_prereq_upper_nibble = (self.chest_type << 4)
    chest_type_and_prereq_upper_nibble |= ((self.appear_condition_flag_id >> 4) & 0xF)
    write_u8(data, self.offset+0x09, chest_type_and_prereq_upper_nibble)
    prereq_lower_nibble_and_unknown = ((self.appear_condition_flag_id & 0xF) << 4)
    prereq_lower_nibble_and_unknown |= (self.unknown & 0xF)
    write_u8(data, self.offset+0x0A, prereq_lower_nibble_and_unknown)
    
    write_u8(data, self.offset+0x0B, self.appear_condition)
    write_u8(data, self.offset+0x1C, self.item_id)
    write_u8(data, self.offset+0x1D, self.flag_id)
