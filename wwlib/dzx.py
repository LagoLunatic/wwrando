
from fs_helpers import *

class DZx: # DZR or DZS, same format
  def __init__(self, file_entry):
    self.file_entry = file_entry
    data = self.file_entry.data
    
    num_chunks = read_u32(data, 0)
    
    self.chunks = []
    for chunk_index in range(0, num_chunks):
      offset = 4 + chunk_index*0xC
      chunk = Chunk(self.file_entry)
      chunk.read(offset)
      self.chunks.append(chunk)
  
  def entries_by_type(self, chunk_type):
    entries = []
    for chunk in self.chunks:
      if chunk_type == chunk.chunk_type:
        entries += chunk.entries
    return entries
  
  def entries_by_type_and_layer(self, chunk_type, layer):
    entries = []
    for chunk in self.chunks:
      if chunk_type == chunk.chunk_type and layer == chunk.layer:
        entries += chunk.entries
    return entries
  
  def add_entity(self, chunk_type, layer=None):
    chunk_to_add_entity_to = None
    for chunk in self.chunks:
      if chunk_type == chunk.chunk_type and layer == chunk.layer:
        chunk_to_add_entity_to = chunk
        break
    
    if chunk_to_add_entity_to is None:
      chunk_to_add_entity_to = Chunk(self.file_entry)
      chunk_to_add_entity_to.chunk_type = chunk_type
      chunk_to_add_entity_to.layer = layer
      self.chunks.append(chunk_to_add_entity_to)
    
    entity = chunk_to_add_entity_to.entry_class(self.file_entry)
    chunk_to_add_entity_to.entries.append(entity)
    
    return entity
  
  def remove_entity(self, entity, chunk_type, layer=None):
    chunk_to_remove_entity_from = None
    for chunk in self.chunks:
      if chunk_type == chunk.chunk_type and layer == chunk.layer:
        chunk_to_remove_entity_from = chunk
        break
    
    if chunk_to_remove_entity_from is None:
      raise Exception("Could not find chunk of type %s on layer %s" % (chunk_type, layer))
    
    chunk_to_remove_entity_from.entries.remove(entity)
  
  def save_changes(self):
    data = self.file_entry.data
    data.truncate(0)
    
    offset = 0
    write_u32(data, offset, len(self.chunks))
    offset += 4
    
    for chunk in self.chunks:
      chunk.offset = offset
      write_str(data, chunk.offset, chunk.fourcc, 4)
      write_u32(data, chunk.offset+4, len(chunk.entries))
      write_u32(data, chunk.offset+8, 0) # Placeholder for first entry offset
      offset += 0xC
    
    for chunk in self.chunks:
      first_entry_offset = offset
      write_u32(data, chunk.offset+8, first_entry_offset)
      
      for entry in chunk.entries:
        if entry is None:
          raise Exception("Tried to save unknown chunk type: %s" % chunk.chunk_type)
        
        entry.offset = offset
        
        offset += chunk.entry_class.DATA_SIZE
      
      if chunk.fourcc == "RTBL":
        # Assign offsets for RTBL sub entries.
        for rtbl_entry in chunk.entries:
          rtbl_entry.sub_entry.offset = offset
          offset += rtbl_entry.sub_entry.DATA_SIZE
        
        # Assign offsets for RTBL sub entry adjacent rooms.
        for rtbl_entry in chunk.entries:
          rtbl_entry.sub_entry.adjacent_rooms_list_offset = offset
          for adjacent_room in rtbl_entry.sub_entry.adjacent_rooms:
            adjacent_room.offset = offset
            offset += adjacent_room.DATA_SIZE
        
        # Pad the end of the adjacent rooms list to 4 bytes.
        file_size = offset
        padded_file_size = (file_size + 3) & ~3
        padding_size_needed = padded_file_size - file_size
        write_bytes(data, offset, b"\xFF"*padding_size_needed)
        offset += padding_size_needed
      
      for entry in chunk.entries:
        entry.save_changes()
    
    # Pad the length of this file to 0x20 bytes.
    file_size = offset
    padded_file_size = (file_size + 0x1F) & ~0x1F
    padding_size_needed = padded_file_size - file_size
    write_bytes(data, offset, b"\xFF"*padding_size_needed)

class Chunk:
  LAYER_CHAR_TO_LAYER_INDEX = {'0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'a': 10, 'b': 11}
  
  
  def __init__(self, file_entry):
    self.file_entry = file_entry
    
    self.entries = []
    self.layer = None
  
  def read(self, offset):
    self.offset = offset
    data = self.file_entry.data
    
    self.chunk_type = read_str(data, self.offset, 4)
    num_entries = read_u32(data, self.offset+4)
    first_entry_offset = read_u32(data, self.offset+8)
    
    # Some types of chunks are conditional and only appear on certain layers. The 4th character of their type determines what letter they appear on.
    if self.chunk_type.startswith("TRE") or self.chunk_type.startswith("ACT") or self.chunk_type.startswith("SCO"):
      layer_char = self.chunk_type[3]
      if layer_char in self.LAYER_CHAR_TO_LAYER_INDEX:
        self.layer = self.LAYER_CHAR_TO_LAYER_INDEX[layer_char]
    if self.chunk_type.startswith("TRE"):
      self.chunk_type = "TRES"
    if self.chunk_type.startswith("ACT"):
      self.chunk_type = "ACTR"
    if self.chunk_type.startswith("SCO"):
      self.chunk_type = "SCOB"
    
    if self.entry_class is None:
      #raise Exception("Unknown chunk type: " + self.chunk_type)
      self.entries = [None]*num_entries
      return
    
    #print("First entry offset: %X" % first_entry_offset)
    
    entry_size = self.entry_class.DATA_SIZE
    
    for entry_index in range(0, num_entries):
      entry_offset = first_entry_offset + entry_index*entry_size
      entry = self.entry_class(self.file_entry)
      entry.read(entry_offset)
      self.entries.append(entry)
  
  @property
  def entry_class(self):
    class_name = self.chunk_type
    if class_name[0].isdigit():
      class_name = "_" + class_name
    return globals().get(class_name, None)
  
  @property
  def fourcc(self):
    fourcc = self.chunk_type
    if self.layer:
      assert 0 <= self.layer <= 11
      fourcc = fourcc[:3]
      fourcc += "%x" % self.layer
    return fourcc

class ChunkEntry:
  PARAMS = {}
  
  def __getattr__(self, name):
    if name in self.PARAMS:
      mask = self.PARAMS[name]
      amount_to_shift = self.get_lowest_set_bit(mask)
      return ((self.params & mask) >> amount_to_shift)
    else:
      return super(self.__class__, self).__getattribute__(name)
  
  def __setattr__(self, name, value):
    if name in self.PARAMS:
      mask = self.PARAMS[name]
      amount_to_shift = self.get_lowest_set_bit(mask)
      self.params = (self.params & (~mask)) | ((value << amount_to_shift) & mask)
    else:
      self.__dict__[name] = value
  
  @staticmethod
  def get_lowest_set_bit(integer):
    lowest_set_bit_index = None
    for bit_index in range(32):
      if integer & (1 << bit_index):
        lowest_set_bit_index = bit_index
        break
    if lowest_set_bit_index is None:
      raise Exception("Invalid mask: %08X" % mask)
    return lowest_set_bit_index

class TRES(ChunkEntry):
  DATA_SIZE = 0x20
  
  PARAMS = {
    "chest_type":              0x00F00000,
    "appear_condition_switch": 0x000FF000,
    "opened_flag":             0x00000F80,
    "appear_condition_type":   0x0000007F,
  }
  
  def __init__(self, file_entry):
    self.file_entry = file_entry
  
  def read(self, offset):
    self.offset = offset
    data = self.file_entry.data
    
    self.name = read_str(data, offset, 8)
    
    self.params = read_u32(data, offset+8)
    
    self.x_pos = read_float(data, offset+0x0C)
    self.y_pos = read_float(data, offset+0x10)
    self.z_pos = read_float(data, offset+0x14)
    self.room_num = read_u16(data, offset+0x18)
    self.y_rot = read_u16(data, offset+0x1A)
    
    self.item_id = read_u8(data, offset+0x1C)
    self.flag_id = read_u8(data, offset+0x1D)
    
    self.padding = read_u16(data, offset + 0x1E)
    
  def save_changes(self):
    data = self.file_entry.data
    
    write_str(data, self.offset, self.name, 8)
    
    write_u32(data, self.offset+0x08, self.params)
    
    write_float(data, self.offset+0x0C, self.x_pos)
    write_float(data, self.offset+0x10, self.y_pos)
    write_float(data, self.offset+0x14, self.z_pos)
    write_u16(data, self.offset+0x18, self.room_num)
    write_u16(data, self.offset+0x1A, self.y_rot)
    
    write_u8(data, self.offset+0x1C, self.item_id)
    write_u8(data, self.offset+0x1D, self.flag_id)
    
    write_u16(data, self.offset+0x1E, self.padding)

class SCOB(ChunkEntry):
  DATA_SIZE = 0x24
  
  PARAMS = {
    "salvage_type":               0xF0000000,
    "salvage_chart_index_plus_1": 0x0FF00000,
    "salvage_item_id":            0x00000FF0,
    
    "buried_pig_item_id":         0x000000FF,
  }
  
  SALVAGE_NAMES = [
    "Salvage",
    "SwSlvg",
    "Salvag2",
    "SalvagN",
    "SalvagE",
    "SalvFM",
  ]
  
  BURIED_PIG_ITEM_NAMES = [
    "TagKb",
  ]
  
  def __init__(self, file_entry):
    self.file_entry = file_entry
  
  def read(self, offset):
    self.offset = offset
    data = self.file_entry.data
    
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
    
  def save_changes(self):
    data = self.file_entry.data
    
    write_str(data, self.offset, self.name, 8)
    
    write_u32(data, self.offset+0x08, self.params)
    
    write_float(data, self.offset+0x0C, self.x_pos)
    write_float(data, self.offset+0x10, self.y_pos)
    write_float(data, self.offset+0x14, self.z_pos)
    write_u16(data, self.offset+0x18, self.auxilary_param)
    write_u16(data, self.offset+0x1A, self.y_rot)
    
    write_u16(data, self.offset+0x1C, self.unknown_1)
    write_u16(data, self.offset+0x1E, self.unknown_2)
    
    write_u8(data, self.offset+0x20, self.scale_x)
    write_u8(data, self.offset+0x21, self.scale_y)
    write_u8(data, self.offset+0x22, self.scale_z)
    write_u8(data, self.offset+0x23, self.padding)
  
  def is_salvage(self):
    return self.name in self.SALVAGE_NAMES
  
  @property
  def salvage_duplicate_id(self):
    return (self.unknown_1 & 0x0003)
  
  @salvage_duplicate_id.setter
  def salvage_duplicate_id(self, value):
    self.unknown_1 = (self.unknown_1 & (~0x0003)) | (value&0x0003)
  
  def is_buried_pig_item(self):
    return self.name in self.BURIED_PIG_ITEM_NAMES

class ACTR(ChunkEntry):
  DATA_SIZE = 0x20
  
  PARAMS = {
    "item_id":   0x000000FF,
    "item_flag": 0x0000FF00,
    
    "boss_item_stage_id": 0x000000FF,
    # The below boss_item_id parameter did not exist for boss items in the vanilla game.
    # The randomizer adds it so that boss items can be randomized and are not just always heart containers.
    "boss_item_id":       0x0000FF00,
    
    "bridge_rpat_index": 0x00FF0000,
    
    "pot_item_id":   0x0000003F,
    "pot_item_flag": 0x007F0000,
    
    "pirate_ship_door_type": 0x0000FF00,
    
    "warp_pot_type":            0x0000000F,
    "warp_pot_event_reg_index": 0x000000F0,
    "warp_pot_dest_1":          0x0000FF00,
    "warp_pot_dest_2":          0x00FF0000,
    "warp_pot_dest_3":          0xFF000000,
  }
  
  ITEM_NAMES = [
    "item",
    "itemFLY",
  ]
  
  BOSS_ITEM_NAMES = [
    "Bitem",
  ]
  
  POT_NAMES = [
    "kotubo",
    "ootubo1",
    "Kmtub",
    "Ktaru",
    "Ostool",
    "Odokuro",
    "Okioke",
    "Kmi02",
    "Ptubo",
    "KkibaB",
    "Kmi00",
    "Hbox2S",
  ]
  
  def __init__(self, file_entry):
    self.file_entry = file_entry
    
    self.name = ""
    self.params = 0
    self.x_pos = 0
    self.y_pos = 0
    self.z_pos = 0
    self.auxilary_param = 0
    self.y_rot = 0
    self.auxilary_param_2 = 0
    self.enemy_number = 0xFFFF
  
  def read(self, offset):
    self.offset = offset
    data = self.file_entry.data
    
    self.name = read_str(data, offset, 8)
    
    self.params = read_u32(data, offset + 8)
    
    self.x_pos = read_float(data, offset + 0x0C)
    self.y_pos = read_float(data, offset + 0x10)
    self.z_pos = read_float(data, offset + 0x14)
    
    self.auxilary_param = read_u16(data, offset + 0x18)
    
    self.y_rot = read_u16(data, offset + 0x1A)
    
    self.auxilary_param_2 = read_u16(data, offset + 0x1C)
    self.enemy_number = read_u16(data, offset + 0x1E)
  
  def save_changes(self):
    data = self.file_entry.data
    
    write_str(data, self.offset, self.name, 8)
    
    write_u32(data, self.offset+0x08, self.params)
    
    write_float(data, self.offset+0x0C, self.x_pos)
    write_float(data, self.offset+0x10, self.y_pos)
    write_float(data, self.offset+0x14, self.z_pos)
    
    write_u16(data, self.offset+0x18, self.auxilary_param)
    
    write_u16(data, self.offset+0x1A, self.y_rot)
    
    write_u16(data, self.offset+0x1C, self.auxilary_param_2)
    write_u16(data, self.offset+0x1E, self.enemy_number)
  
  def is_item(self):
    return self.name in self.ITEM_NAMES
  
  def is_boss_item(self):
    return self.name in self.BOSS_ITEM_NAMES
  
  def is_pot(self):
    return self.name in self.POT_NAMES

class PLYR(ChunkEntry):
  DATA_SIZE = 0x20
  
  def __init__(self, file_entry):
    self.file_entry = file_entry
    
    self.name = "Link"
    self.event_index = 0xFF
    self.unknown1 = 0xFF
    self.spawn_type = 0
    self.room_num = 0
    
    self.x_pos = 0
    self.y_pos = 0
    self.z_pos = 0
    self.unknown2 = 0
    self.y_rot = 0
    
    self.unknown3 = 0xFF
    self.spawn_id = 0
    self.unknown4 = 0xFFFF
  
  def read(self, offset):
    self.offset = offset
    data = self.file_entry.data
    
    self.name = read_str(data, offset, 8)
    
    self.event_index = read_u8(data, offset + 8)
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
    
    write_u8(data, self.offset+0x08, self.event_index)
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

class SCLS(ChunkEntry):
  DATA_SIZE = 0xC
  
  def __init__(self, file_entry):
    self.file_entry = file_entry
    
    self.dest_stage_name = ""
    self.spawn_id = 0
    self.room_index = 0
    self.fade_type = 0
    self.padding = 0xFF
  
  def read(self, offset):
    self.offset = offset
    data = self.file_entry.data
    
    self.dest_stage_name = read_str(data, offset, 8)
    self.spawn_id = read_u8(data, offset+8)
    self.room_index = read_u8(data, offset+9)
    self.fade_type = read_u8(data, offset+0xA)
    self.padding = read_u8(data, offset+0xB)
  
  def save_changes(self):
    data = self.file_entry.data
    
    write_str(data, self.offset, self.dest_stage_name, 8)
    write_u8(data, self.offset+0x8, self.spawn_id)
    write_u8(data, self.offset+0x9, self.room_index)
    write_u8(data, self.offset+0xA, self.fade_type)
    write_u8(data, self.offset+0xB, self.padding)

class STAG(ChunkEntry):
  DATA_SIZE = 0x14
  
  def __init__(self, file_entry):
    self.file_entry = file_entry
  
  def read(self, offset):
    self.offset = offset
    data = self.file_entry.data
    
    self.depth_min = read_float(data, offset)
    self.depth_max = read_float(data, offset+4)
    self.unknown_1 = read_u8(data, offset+8)
    
    is_dungeon_and_stage_id = read_u8(data, offset+9)
    self.is_dungeon = is_dungeon_and_stage_id & 1
    self.stage_id = is_dungeon_and_stage_id >> 1
    
    self.loaded_particle_bank = read_u16(data, offset+0xA)
    self.property_index = read_u16(data, offset+0xC)
    self.unknown_2 = read_u8(data, offset+0xE)
    self.unknown_3 = read_u8(data, offset+0xF)
    self.unknown_4 = read_u8(data, offset+0x10)
    self.unknown_5 = read_u8(data, offset+0x11)
    self.draw_range = read_u16(data, offset+0x12)
  
  def save_changes(self):
    data = self.file_entry.data
    
    write_float(data, self.offset, self.depth_min)
    write_float(data, self.offset+4, self.depth_max)
    write_u8(data, self.offset+8, self.unknown_1)
    
    is_dungeon_and_stage_id = (self.stage_id << 1) | (self.is_dungeon & 1)
    write_u16(data, self.offset+8, is_dungeon_and_stage_id)
    
    write_u16(data, self.offset+0xA, self.loaded_particle_bank)
    write_u16(data, self.offset+0xC, self.property_index)
    write_u8(data, self.offset+0xE, self.unknown_2)
    write_u8(data, self.offset+0xF, self.unknown_3)
    write_u8(data, self.offset+0x10, self.unknown_4)
    write_u8(data, self.offset+0x11, self.unknown_5)
    write_u16(data, self.offset+0x12, self.draw_range)

class SHIP(ChunkEntry):
  DATA_SIZE = 0x10
  
  def __init__(self, file_entry):
    self.file_entry = file_entry
  
  def read(self, offset):
    self.offset = offset
    data = self.file_entry.data
    
    self.x_pos = read_float(data, offset + 0x00)
    self.y_pos = read_float(data, offset + 0x04)
    self.z_pos = read_float(data, offset + 0x08)
    self.y_rot = read_u16(data, offset + 0x0C)
    self.ship_id = read_u8(data, offset + 0x0E)
    self.unknown = read_u8(data, offset + 0x0F)
  
  def save_changes(self):
    data = self.file_entry.data
    
    write_float(data, self.offset+0x00, self.x_pos)
    write_float(data, self.offset+0x04, self.y_pos)
    write_float(data, self.offset+0x08, self.z_pos)
    write_u16(data, self.offset+0x0C, self.y_rot)
    write_u8(data, self.offset+0x0E, self.ship_id)
    write_u8(data, self.offset+0x0F, self.unknown)

class RTBL(ChunkEntry):
  DATA_SIZE = 0x4
  
  def __init__(self, file_entry):
    self.file_entry = file_entry
  
  def read(self, offset):
    self.offset = offset
    data = self.file_entry.data
    
    sub_entry_offset = read_u32(data, offset)
    self.sub_entry = RTBL_SubEntry(self.file_entry)
    self.sub_entry.read(sub_entry_offset)
  
  def save_changes(self):
    data = self.file_entry.data
    
    write_u32(data, self.offset, self.sub_entry.offset)
    
    self.sub_entry.save_changes()

class RTBL_SubEntry:
  DATA_SIZE = 0x8
  
  def __init__(self, file_entry):
    self.file_entry = file_entry
  
  def read(self, offset):
    self.offset = offset
    data = self.file_entry.data
    
    num_rooms = read_u8(data, offset)
    self.reverb_amount = read_u8(data, offset+1)
    self.does_time_pass = read_u8(data, offset+2)
    self.unknown = read_u8(data, offset+3)
    
    self.adjacent_rooms_list_offset = read_u32(data, offset+4)
    self.adjacent_rooms = []
    for i in range(num_rooms):
      adjacent_room = RTBL_AdjacentRoom(self.file_entry)
      adjacent_room.read(self.adjacent_rooms_list_offset + i)
      self.adjacent_rooms.append(adjacent_room)
  
  def save_changes(self):
    data = self.file_entry.data
    
    num_rooms = len(self.adjacent_rooms)
    write_u8(data, self.offset, num_rooms)
    write_u8(data, self.offset+1, self.reverb_amount)
    write_u8(data, self.offset+2, self.does_time_pass)
    write_u8(data, self.offset+3, self.unknown)
    
    write_u32(data, self.offset+4, self.adjacent_rooms_list_offset)
    
    for adjacent_room in self.adjacent_rooms:
      adjacent_room.save_changes()

class RTBL_AdjacentRoom:
  DATA_SIZE = 0x1
  
  def __init__(self, file_entry):
    self.file_entry = file_entry
  
  def read(self, offset):
    self.offset = offset
    data = self.file_entry.data
    
    byte = read_u8(data, offset)
    self.should_load_room = ((byte & 0x80) != 0)
    self.unknown = ((byte & 0x40) != 0)
    self.room_index = (byte & 0x3F)
  
  def save_changes(self):
    data = self.file_entry.data
    
    byte = (self.room_index & 0x3F)
    if self.should_load_room:
      byte |= 0x80
    if self.unknown:
      byte |= 0x40
    
    write_u8(data, self.offset, byte)

class RPAT(ChunkEntry):
  DATA_SIZE = 0xC
  
  def __init__(self, file_entry):
    self.file_entry = file_entry
    
    self.num_points = 0
    self.next_path_index = 0xFFFF
    self.unknown = 0xFF
    self.is_loop = 0
    self.padding = 0xFFFF
    self.first_waypoint_offset = 0
  
  def read(self, offset):
    self.offset = offset
    data = self.file_entry.data
    
    self.num_points = read_u16(data, self.offset)
    self.next_path_index = read_u16(data, self.offset+2)
    self.unknown = read_u8(data, self.offset+4)
    self.is_loop = read_u8(data, self.offset+5)
    self.padding = read_u16(data, self.offset+6)
    self.first_waypoint_offset = read_u32(data, self.offset+8)
  
  def save_changes(self):
    data = self.file_entry.data
    
    write_u16(data, self.offset, self.num_points)
    write_u16(data, self.offset+2, self.next_path_index)
    write_u8(data, self.offset+4, self.unknown)
    write_u8(data, self.offset+5, self.is_loop)
    write_u16(data, self.offset+6, self.padding)
    write_u32(data, self.offset+8, self.first_waypoint_offset)

class RPPN(ChunkEntry):
  DATA_SIZE = 0x10
  
  def __init__(self, file_entry):
    self.file_entry = file_entry
    
    self.unknown = 0xFFFFFFFF
    self.x_pos = 0
    self.y_pos = 0
    self.z_pos = 0
  
  def read(self, offset):
    self.offset = offset
    data = self.file_entry.data
    
    self.unknown = read_u32(data, self.offset)
    self.x_pos = read_float(data, self.offset+4)
    self.y_pos = read_float(data, self.offset+8)
    self.z_pos = read_float(data, self.offset+0xC)
  
  def save_changes(self):
    data = self.file_entry.data
    
    write_u32(data, self.offset, self.unknown)
    write_float(data, self.offset+4, self.x_pos)
    write_float(data, self.offset+8, self.y_pos)
    write_float(data, self.offset+0xC, self.z_pos)

class TGOB(ChunkEntry):
  DATA_SIZE = 0x20
  
  def __init__(self, file_entry):
    self.file_entry = file_entry
    
    self.name = ""
    self.params = 0
    self.x_pos = 0
    self.y_pos = 0
    self.z_pos = 0
    self.x_rot = 0
    self.y_rot = 0
    self.z_rot = 0
    self.padding = 0xFFFF
  
  def read(self, offset):
    self.offset = offset
    data = self.file_entry.data
    
    self.name = read_str(data, offset, 8)
    
    self.params = read_u32(data, offset + 8)
    
    self.x_pos = read_float(data, offset + 0x0C)
    self.y_pos = read_float(data, offset + 0x10)
    self.z_pos = read_float(data, offset + 0x14)
    self.x_rot = read_u16(data, offset + 0x18)
    self.y_rot = read_u16(data, offset + 0x1A)
    self.z_rot = read_u16(data, offset + 0x1C)
    
    self.padding = read_u16(data, offset + 0x1E)
  
  def save_changes(self):
    data = self.file_entry.data
    
    write_str(data, self.offset, self.name, 8)
    
    write_u32(data, self.offset+0x08, self.params)
    
    write_float(data, self.offset+0x0C, self.x_pos)
    write_float(data, self.offset+0x10, self.y_pos)
    write_float(data, self.offset+0x14, self.z_pos)
    write_u16(data, self.offset+0x18, self.x_rot)
    write_u16(data, self.offset+0x1A, self.y_rot)
    write_u16(data, self.offset+0x1C, self.z_rot)
    
    write_u16(data, self.offset+0x1E, self.padding)

class DummyEntry(ChunkEntry):
  def __init__(self, file_entry):
    self.file_entry = file_entry
  
  def read(self, offset):
    self.offset = offset
    data = self.file_entry.data
    
    self.raw_data_bytes = read_bytes(data, self.offset, self.DATA_SIZE)
  
  def save_changes(self):
    data = self.file_entry.data
    
    write_bytes(data, self.offset, self.raw_data_bytes)

class FILI(DummyEntry):
  DATA_SIZE = 8

class FLOR(DummyEntry):
  DATA_SIZE = 0x14

class _2DMA(DummyEntry):
  DATA_SIZE = 0x38

class LBNK(DummyEntry):
  DATA_SIZE = 0x1

class SOND(DummyEntry):
  DATA_SIZE = 0x1C

class RCAM(DummyEntry):
  DATA_SIZE = 0x14

class RARO(DummyEntry):
  DATA_SIZE = 0x14

class EVNT(DummyEntry):
  DATA_SIZE = 0x18

class TGDR(DummyEntry):
  DATA_SIZE = 0x24

class MULT(DummyEntry):
  DATA_SIZE = 0xC

class DMAP(DummyEntry):
  DATA_SIZE = 0x10

class EnvR(DummyEntry):
  DATA_SIZE = 0x8

class Colo(DummyEntry):
  DATA_SIZE = 0xC

class Pale(DummyEntry):
  DATA_SIZE = 0x2C

class Virt(DummyEntry):
  DATA_SIZE = 0x24

class LGHT(DummyEntry):
  DATA_SIZE = 0x1C

class LGTV(DummyEntry):
  DATA_SIZE = 0x1C

class MECO(DummyEntry):
  DATA_SIZE = 0x2

class MEMA(DummyEntry):
  DATA_SIZE = 0x4
