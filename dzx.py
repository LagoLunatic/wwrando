
from fs_helpers import *

class DZx: # DZR or DZS, same format
  def __init__(self, data):
    num_chunks = read_u32(data, 0)
    
    self.chunks = []
    for chunk_index in range(0, num_chunks):
      offset = 4 + chunk_index*0xC
      chunk = Chunk(data, offset)
      self.chunks.append(chunk)

class Chunk:
  def __init__(self, data, offset):
    self.chunk_type = read_str(data, offset, 4)
    num_entries = read_u32(data, offset+4)
    first_entry_offset = read_u32(data, offset+8)
    
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
      entry = TRES(data, entry_offset)
      self.entries.append(entry)

class TRES:
  DATA_SIZE = 0x20
  
  def __init__(self, data, offset):
    self.name = read_str(data, offset, 8)
    
    chest_type_and_prereq_upper_nibble = read_u8(data, offset+9)
    prereq_lower_nibble_and_unknown = read_u8(data, offset+0xA)
    self.chest_type = (chest_type_and_prereq_upper_nibble >> 4)
    self.appear_condition_flag_id = ((chest_type_and_prereq_upper_nibble & 0xF) << 4) | (prereq_lower_nibble_and_unknown >> 4)
    self.unknown = (prereq_lower_nibble_and_unknown & 0xF) # flag for having picked this up?
    
    self.appear_condition = read_u8(data, offset+0xB)
    
    self.item_id = read_u8(data, offset+0x1C)
    self.flag_id = read_u8(data, offset+0x1D) # nothing??
    
