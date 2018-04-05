
from fs_helpers import *

class DZx: # DZR or DZS, same format
  def __init__(self, file_entry):
    self.file_entry = file_entry
    data = self.file_entry.data
    
    num_chunks = read_u32(data, 0)
    
    self.chunks = {}
    for chunk_index in range(0, num_chunks):
      offset = 4 + chunk_index*0xC
      chunk = Chunk(self.file_entry, offset)
      self.chunks[chunk.chunk_type] = chunk

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
      "SCOB": SCOB,
      "ACTR": ACTR,
      "PLYR": PLYR,
      "SCLS": SCLS,
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
    
    self.params = read_u8(data, offset+8)
    
    chest_type_and_prereq_upper_nibble = read_u8(data, offset+9)
    prereq_lower_nibble_and_unknown = read_u8(data, offset+0xA)
    self.chest_type = (chest_type_and_prereq_upper_nibble >> 4)
    self.appear_condition_flag_id = ((chest_type_and_prereq_upper_nibble & 0xF) << 4) | (prereq_lower_nibble_and_unknown >> 4)
    self.unknown = (prereq_lower_nibble_and_unknown & 0xF) # flag for having picked this up?
    
    self.appear_condition = read_u8(data, offset+0xB)
    
    self.x_pos = read_float(data, offset+0x0C)
    self.y_pos = read_float(data, offset+0x10)
    self.z_pos = read_float(data, offset+0x14)
    self.room_num = read_u16(data, offset+0x18)
    self.y_rot = read_u16(data, offset+0x1A)
    
    self.item_id = read_u8(data, offset+0x1C)
    self.flag_id = read_u8(data, offset+0x1D) # nothing??
    
    self.padding = read_u16(data, offset + 0x1E)
    
  def save_changes(self):
    data = self.file_entry.data
    
    write_str(data, self.offset, self.name, 8)
    
    write_u8(data, self.offset+0x08, self.params)
    
    chest_type_and_prereq_upper_nibble = (self.chest_type << 4)
    chest_type_and_prereq_upper_nibble |= ((self.appear_condition_flag_id >> 4) & 0xF)
    write_u8(data, self.offset+0x09, chest_type_and_prereq_upper_nibble)
    prereq_lower_nibble_and_unknown = ((self.appear_condition_flag_id & 0xF) << 4)
    prereq_lower_nibble_and_unknown |= (self.unknown & 0xF)
    write_u8(data, self.offset+0x0A, prereq_lower_nibble_and_unknown)
    
    write_u8(data, self.offset+0x0B, self.appear_condition)
    
    write_float(data, self.offset+0x0C, self.x_pos)
    write_float(data, self.offset+0x10, self.y_pos)
    write_float(data, self.offset+0x14, self.z_pos)
    write_u16(data, self.offset+0x18, self.room_num)
    write_u16(data, self.offset+0x1A, self.y_rot)
    
    write_u8(data, self.offset+0x1C, self.item_id)
    write_u8(data, self.offset+0x1D, self.flag_id)
    
    write_u16(data, self.offset+0x1E, self.padding)

class SCOB:
  DATA_SIZE = 0x24
  
  SALVAGE_NAMES = [
    "Salvage",
    "SwSlvg",
    "Salvag2",
    "SalvagN",
    "SalvagE",
    "SalvFM",
  ]
  
  def __init__(self, file_entry, offset):
    self.file_entry = file_entry
    data = self.file_entry.data
    self.offset = offset
    
    self.name = read_str(data, offset, 8)
    
    self.params = read_u32(data, offset + 8)
    
    self.x_pos = read_float(data, offset + 0x0C)
    self.y_pos = read_float(data, offset + 0x10)
    self.z_pos = read_float(data, offset + 0x14)
    
    self.auxilary_param = read_u16(data, offset + 0x18)
    
    self.y_rot = read_u16(data, offset + 0x1A)
    
    self.unknown_1 = read_u16(data, offset + 0x1C)
    self.unknown_2 = read_u16(data, offset + 0x1E)
    
    self.scale_x = read_u8(data, offset + 0x20)
    self.scale_y = read_u8(data, offset + 0x21)
    self.scale_z = read_u8(data, offset + 0x22)
    self.padding = read_u8(data, offset + 0x23)
    
    if self.is_salvage():
      self.salvage_type = ((self.params & 0xF0000000) >> 28)
      self.item_id = ((self.params & 0x00000FF0) >> 4)
      if self.salvage_type == 0:
        self.chart_index_plus_1 = ((self.params & 0x0FF00000) >> 20)
        self.duplicate_id = (self.unknown_1 & 3)
    
  def save_changes(self):
    pass
  
  def is_salvage(self):
    if self.name in self.SALVAGE_NAMES:
      return True
    else:
      return False

class ACTR:
  DATA_SIZE = 0x20
  
  def __init__(self, file_entry, offset):
    self.file_entry = file_entry
    data = self.file_entry.data
    self.offset = offset
    
    self.name = read_str(data, offset, 8)
    
    self.params = read_u32(data, offset + 8)
    
    self.x_pos = read_float(data, offset + 0x0C)
    self.y_pos = read_float(data, offset + 0x10)
    self.z_pos = read_float(data, offset + 0x14)
    self.x_rot = read_u16(data, offset + 0x18)
    self.y_rot = read_u16(data, offset + 0x1A)
    
    self.set_flag = read_u16(data, offset + 0x1C)
    self.enemy_number = read_u16(data, offset + 0x1E)
  
  def save_changes(self):
    data = self.file_entry.data
    
    write_str(data, self.offset, self.name, 8)
    
    write_u32(data, self.offset+0x08, self.params)
    
    write_float(data, self.offset+0x0C, self.x_pos)
    write_float(data, self.offset+0x10, self.y_pos)
    write_float(data, self.offset+0x14, self.z_pos)
    write_u16(data, self.offset+0x18, self.x_rot)
    write_u16(data, self.offset+0x1A, self.y_rot)
    
    write_u16(data, self.offset+0x1C, self.set_flag)
    write_u16(data, self.offset+0x1E, self.enemy_number)

class PLYR:
  DATA_SIZE = 0x20
  
  def __init__(self, file_entry, offset):
    self.file_entry = file_entry
    data = self.file_entry.data
    self.offset = offset
    
    self.name = read_str(data, offset, 8)
    
    self.event_index_to_play = read_u8(data, offset + 8)
    self.unknown1 = read_u8(data, offset + 9)
    self.spawn_type = read_u8(data, offset + 0x0A)
    self.room_num = read_u8(data, offset + 0x0B)
    
    self.x_pos = read_float(data, offset + 0x0C)
    self.y_pos = read_float(data, offset + 0x10)
    self.z_pos = read_float(data, offset + 0x14)
    self.unknown2 = read_u16(data, offset + 0x18)
    self.y_rot = read_u16(data, offset + 0x1A)
    
    self.unknown3 = read_u8(data, offset + 0x1C)
    self.spawn_id = read_u8(data, offset + 0x1D)
    self.unknown4 = read_u16(data, offset + 0x1E)
  
  def save_changes(self):
    data = self.file_entry.data
    
    write_str(data, self.offset, self.name, 8)
    
    write_u8(data, self.offset+0x08, self.event_index_to_play)
    write_u8(data, self.offset+0x09, self.unknown1)
    write_u8(data, self.offset+0x0A, self.spawn_type)
    write_u8(data, self.offset+0x0B, self.room_num)
    
    write_float(data, self.offset+0x0C, self.x_pos)
    write_float(data, self.offset+0x10, self.y_pos)
    write_float(data, self.offset+0x14, self.z_pos)
    write_u16(data, self.offset+0x18, self.unknown2)
    write_u16(data, self.offset+0x1A, self.y_rot)
    
    write_u8(data, self.offset+0x1C, self.unknown3)
    write_u8(data, self.offset+0x1D, self.spawn_id)
    write_u16(data, self.offset+0x1E, self.unknown4)

class SCLS:
  DATA_SIZE = 0xC
  
  def __init__(self, file_entry, offset):
    self.file_entry = file_entry
    data = self.file_entry.data
    self.offset = offset
    
    self.dest_stage_name = read_str(data, offset, 8)
    self.spawn_index = read_u8(data, offset+8)
    self.room_index = read_u8(data, offset+9)
    self.fade_type = read_u8(data, offset+0xA)
    self.padding = read_u8(data, offset+0xB)
  
  def save_changes(self):
    data = self.file_entry.data
    
    write_str(data, self.offset, self.dest_stage_name, 8)
    write_u8(data, self.offset+0x8, self.spawn_index)
    write_u8(data, self.offset+0x9, self.room_index)
    write_u8(data, self.offset+0xA, self.fade_type)
    write_u8(data, self.offset+0xB, self.padding)
