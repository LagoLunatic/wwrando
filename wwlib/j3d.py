
import os
from enum import Enum
from io import BytesIO
from collections import OrderedDict
from enum import Enum

from wwlib.bti import BTI

from fs_helpers import *

IMPLEMENTED_CHUNK_TYPES = [
  "TEX1",
  "MAT3",
  "MDL3",
  "TRK1",
]

class J3DFile:
  def __init__(self, data):
    if try_read_str(data, 0, 4) == "Yaz0":
      data = Yaz0.decompress(data)
    self.data = data
    
    self.read()
  
  def read(self):
    data = self.data
    
    self.magic = read_str(data, 0, 4)
    assert self.magic.startswith("J3D")
    self.file_type = read_str(data, 4, 4)
    self.length = read_u32(data, 8)
    self.num_chunks = read_u32(data, 0x0C)
    
    self.chunks = []
    self.chunk_by_type = {}
    offset = 0x20
    for chunk_index in range(self.num_chunks):
      if offset == data_len(data):
        # Normally the number of chunks tells us when to stop reading.
        # But in rare cases like Bk.arc/bk_boko.bmt, the number of chunks can be greater than how many chunks are actually in the file, so we need to detect when we've reached the end of the file manually.
        break
      
      chunk_magic = read_str(data, offset, 4)
      if chunk_magic in IMPLEMENTED_CHUNK_TYPES:
        chunk_class = globals().get(chunk_magic, None)
      else:
        chunk_class = J3DChunk
      chunk = chunk_class()
      chunk.read(data, offset)
      self.chunks.append(chunk)
      self.chunk_by_type[chunk.magic] = chunk
      
      if chunk.magic in IMPLEMENTED_CHUNK_TYPES:
        setattr(self, chunk.magic.lower(), chunk)
      
      offset += chunk.size
  
  def save_changes(self):
    data = self.data
    
    # Cut off the chunk data first since we're replacing this data entirely.
    data.truncate(0x20)
    data.seek(0x20)
    
    for chunk in self.chunks:
      chunk.save_changes()
      
      chunk.data.seek(0)
      chunk_data = chunk.data.read()
      data.write(chunk_data)
    
    self.length = data_len(data)
    self.num_chunks = len(self.chunks)
    
    write_magic_str(data, 0, self.magic, 4)
    write_magic_str(data, 4, self.file_type, 4)
    write_u32(data, 8, self.length)
    write_u32(data, 0xC, self.num_chunks)

class J3DFileEntry(J3DFile):
  def __init__(self, file_entry):
    self.file_entry = file_entry
    self.file_entry.decompress_data_if_necessary()
    super(J3DFileEntry, self).__init__(self.file_entry.data)

class BDL(J3DFileEntry):
  def __init__(self, file_entry):
    super().__init__(file_entry)
    
    assert self.magic == "J3D2"
    assert self.file_type == "bdl4"

class BMD(J3DFileEntry):
  def __init__(self, file_entry):
    super().__init__(file_entry)
    
    assert self.magic == "J3D2"
    assert self.file_type == "bmd3"

class BMT(J3DFileEntry):
  def __init__(self, file_entry):
    super().__init__(file_entry)
    
    assert self.magic == "J3D2"
    assert self.file_type == "bmt3"

class BRK(J3DFileEntry):
  def __init__(self, file_entry):
    super().__init__(file_entry)
    
    assert self.magic == "J3D1"
    assert self.file_type == "brk1"



class J3DChunk:
  def __init__(self):
    self.magic = None
    self.size = None
    self.data = None
  
  def read(self, file_data, chunk_offset):
    self.magic = read_str(file_data, chunk_offset, 4)
    self.size = read_u32(file_data, chunk_offset+4)
    
    file_data.seek(chunk_offset)
    self.data = BytesIO(file_data.read(self.size))
    
    self.read_chunk_specific_data()
  
  def read_chunk_specific_data(self):
    pass
  
  def save_changes(self):
    self.save_chunk_specific_data()
    
    # Pad the size of this chunk to the next 0x20 bytes.
    align_data_to_nearest(self.data, 0x20)
    
    self.size = data_len(self.data)
    write_magic_str(self.data, 0, self.magic, 4)
    write_u32(self.data, 4, self.size)
  
  def save_chunk_specific_data(self):
    pass
  
  def read_string_table(self, string_table_offset):
    num_strings = read_u16(self.data, string_table_offset+0x00)
    padding = read_u16(self.data, string_table_offset+0x02)
    assert padding == 0xFFFF
    
    strings = []
    offset = string_table_offset + 4
    for i in range(num_strings):
      string_hash = read_u16(self.data, offset+0x00)
      string_data_offset = read_u16(self.data, offset+0x02)
      
      string = read_str_until_null_character(self.data, string_table_offset + string_data_offset)
      strings.append(string)
      
      offset += 4
    
    return strings
  
  def write_string_table(self, string_table_offset, strings):
    num_strings = len(strings)
    write_u16(self.data, string_table_offset+0x00, num_strings)
    write_u16(self.data, string_table_offset+0x02, 0xFFFF)
    
    offset = string_table_offset + 4
    next_string_data_offset = 4 + num_strings*4
    for string in strings:
      hash = 0
      for char in string:
        hash *= 3
        hash += ord(char)
        hash &= 0xFFFF
      
      write_u16(self.data, offset+0x00, hash)
      write_u16(self.data, offset+0x02, next_string_data_offset)
      
      write_str_with_null_byte(self.data, string_table_offset+next_string_data_offset, string)
      
      offset += 4
      next_string_data_offset += len(string) + 1

class TEX1(J3DChunk):
  def read_chunk_specific_data(self):
    self.textures = []
    self.num_textures = read_u16(self.data, 8)
    self.texture_header_list_offset = read_u32(self.data, 0x0C)
    for texture_index in range(self.num_textures):
      bti_header_offset = self.texture_header_list_offset + texture_index*0x20
      texture = BTI(self.data, bti_header_offset)
      self.textures.append(texture)
    
    self.string_table_offset = read_u32(self.data, 0x10)
    self.texture_names = self.read_string_table(self.string_table_offset)
    self.textures_by_name = OrderedDict()
    for i, texture in enumerate(self.textures):
      texture_name = self.texture_names[i]
      if texture_name not in self.textures_by_name:
        self.textures_by_name[texture_name] = []
      self.textures_by_name[texture_name].append(texture)
  
  def save_chunk_specific_data(self):
    # Does not support adding new textures currently.
    assert len(self.textures) == self.num_textures
    
    next_available_data_offset = self.texture_header_list_offset + self.num_textures*0x20 # Right after the last header ends
    self.data.truncate(next_available_data_offset)
    self.data.seek(next_available_data_offset)
    
    image_data_offsets = {}
    for i, texture in enumerate(self.textures):
      filename = self.texture_names[i]
      if filename in image_data_offsets:
        texture.image_data_offset = image_data_offsets[filename] - texture.header_offset
        continue
      
      self.data.seek(next_available_data_offset)
      
      texture.image_data_offset = next_available_data_offset - texture.header_offset
      image_data_offsets[filename] = next_available_data_offset
      texture.image_data.seek(0)
      self.data.write(texture.image_data.read())
      align_data_to_nearest(self.data, 0x20)
      next_available_data_offset = data_len(self.data)
    
    palette_data_offsets = {}
    for i, texture in enumerate(self.textures):
      filename = self.texture_names[i]
      if filename in palette_data_offsets:
        texture.palette_data_offset = palette_data_offsets[filename] - texture.header_offset
        continue
      
      self.data.seek(next_available_data_offset)
      
      if texture.needs_palettes():
        texture.palette_data_offset = next_available_data_offset - texture.header_offset
        palette_data_offsets[filename] = next_available_data_offset
        texture.palette_data.seek(0)
        self.data.write(texture.palette_data.read())
        align_data_to_nearest(self.data, 0x20)
        next_available_data_offset = data_len(self.data)
      else:
        # If the image doesn't use palettes its palette offset is just the same as the first texture's image offset.
        first_texture = self.textures[0]
        texture.palette_data_offset = first_texture.image_data_offset + first_texture.header_offset - texture.header_offset
        palette_data_offsets[filename] = first_texture.image_data_offset + first_texture.header_offset
    
    for texture in self.textures:
      texture.save_header_changes()
    
    self.string_table_offset = next_available_data_offset
    write_u32(self.data, 0x10, self.string_table_offset)
    self.write_string_table(self.string_table_offset, self.texture_names)

class MAT3(J3DChunk):
  def read_chunk_specific_data(self):
    self.tev_reg_colors_offset = read_u32(self.data, 0x50)
    self.tev_konst_colors_offset = read_u32(self.data, 0x54)
    self.tev_stages_offset = read_u32(self.data, 0x58)
    
    self.num_reg_colors = (self.tev_konst_colors_offset - self.tev_reg_colors_offset) // 8
    self.reg_colors = []
    for i in range(self.num_reg_colors):
      r = read_s16(self.data, self.tev_reg_colors_offset + i*8 + 0)
      g = read_s16(self.data, self.tev_reg_colors_offset + i*8 + 2)
      b = read_s16(self.data, self.tev_reg_colors_offset + i*8 + 4)
      a = read_s16(self.data, self.tev_reg_colors_offset + i*8 + 6)
      self.reg_colors.append((r, g, b, a))
    
    self.num_konst_colors = (self.tev_stages_offset - self.tev_konst_colors_offset) // 4
    self.konst_colors = []
    for i in range(self.num_konst_colors):
      r = read_u8(self.data, self.tev_konst_colors_offset + i*4 + 0)
      g = read_u8(self.data, self.tev_konst_colors_offset + i*4 + 1)
      b = read_u8(self.data, self.tev_konst_colors_offset + i*4 + 2)
      a = read_u8(self.data, self.tev_konst_colors_offset + i*4 + 3)
      self.konst_colors.append((r, g, b, a))
  
  def save_chunk_specific_data(self):
    for i in range(self.num_reg_colors):
      r, g, b, a = self.reg_colors[i]
      write_s16(self.data, self.tev_reg_colors_offset + i*8 + 0, r)
      write_s16(self.data, self.tev_reg_colors_offset + i*8 + 2, g)
      write_s16(self.data, self.tev_reg_colors_offset + i*8 + 4, b)
      write_s16(self.data, self.tev_reg_colors_offset + i*8 + 6, a)
    
    for i in range(self.num_konst_colors):
      r, g, b, a = self.konst_colors[i]
      write_u8(self.data, self.tev_konst_colors_offset + i*4 + 0, r)
      write_u8(self.data, self.tev_konst_colors_offset + i*4 + 1, g)
      write_u8(self.data, self.tev_konst_colors_offset + i*4 + 2, b)
      write_u8(self.data, self.tev_konst_colors_offset + i*4 + 3, a)

class MDL3(J3DChunk):
  def read_chunk_specific_data(self):
    self.num_entries = read_u16(self.data, 0x08)
    self.packets_offset = read_u32(self.data, 0x0C)
    
    self.entries = []
    packet_offset = self.packets_offset
    for i in range(self.num_entries):
      entry_offset = read_u32(self.data, packet_offset + 0x00)
      entry_size = read_u32(self.data, packet_offset + 0x04)
      entry = MDLEntry(self.data, entry_offset+packet_offset, entry_size)
      self.entries.append(entry)
      packet_offset += 8
  
  def save_chunk_specific_data(self):
    for entry in self.entries:
      entry.save_changes()
      
      entry.data.seek(0)
      entry_data = entry.data.read()
      self.data.seek(entry.entry_offset)
      self.data.write(entry_data)

class MDLEntry:
  def __init__(self, chunk_data, entry_offset, size):
    self.entry_offset = entry_offset
    self.size = size
    
    chunk_data.seek(self.entry_offset)
    self.data = BytesIO(chunk_data.read(self.size))
    
    self.read()
  
  def read(self):
    self.bp_commands = []
    self.xf_commands = []
    offset = 0
    while offset < self.size:
      command_type = read_u8(self.data, offset)
      if command_type == MDLCommandType.BP.value:
        command = BPCommand(self.data)
        offset = command.read(offset)
        self.bp_commands.append(command)
      elif command_type == MDLCommandType.XF.value:
        command = XFCommand(self.data)
        offset = command.read(offset)
        self.xf_commands.append(command)
      elif command_type == MDLCommandType.END_MARKER.value:
        break
      else:
        raise Exception("Invalid MDL3 command type: %02X" % command_type)
  
  def save_changes(self):
    offset = 0
    for command in self.bp_commands:
      offset = command.save(offset)
    for command in self.xf_commands:
      offset = command.save(offset)
    
    if offset % 0x20 != 0:
      padding_bytes_needed = (0x20 - (offset % 0x20))
      padding = b"\0"*padding_bytes_needed
      write_bytes(self.data, offset, padding)
      offset += padding_bytes_needed
    
    # Adding new commands not supported.
    assert offset <= self.size

class MDLCommandType(Enum):
  END_MARKER = 0x00
  XF = 0x10
  BP = 0x61

class BPCommand:
  def __init__(self, data):
    self.data = data
  
  def read(self, offset):
    assert read_u8(self.data, offset) == MDLCommandType.BP.value
    offset += 1
    
    bitfield = read_u32(self.data, offset)
    offset += 4
    self.register = (bitfield & 0xFF000000) >> 24
    self.value = (bitfield & 0x00FFFFFF)
    
    return offset
  
  def save(self, offset):
    write_u8(self.data, offset, MDLCommandType.BP.value)
    offset += 1
    
    bitfield = (self.register << 24) & 0xFF000000
    bitfield |= self.value & 0x00FFFFFF
    write_u32(self.data, offset, bitfield)
    offset += 4
    
    return offset

class XFCommand:
  def __init__(self, data):
    self.data = data
  
  def read(self, offset):
    assert read_u8(self.data, offset) == MDLCommandType.XF.value
    offset += 1
    
    num_args = read_u16(self.data, offset) + 1
    offset += 2
    self.register = read_u16(self.data, offset)
    offset += 2
    
    self.args = []
    for i in range(num_args):
      arg = read_u32(self.data, offset)
      offset += 4
      self.args.append(arg)
    
    return offset
  
  def save(self, offset):
    write_u8(self.data, offset, MDLCommandType.XF.value)
    offset += 1
    
    num_args = len(self.args)
    
    write_u16(self.data, offset, num_args-1)
    offset += 2
    write_u16(self.data, offset, self.register)
    offset += 2
    
    for arg in self.args:
      write_u32(self.data, offset, arg)
      offset += 4
    
    return offset

class TRK1(J3DChunk):
  def read_chunk_specific_data(self):
    assert read_str(self.data, 0, 4) == "TRK1"
    
    self.loop_mode = LoopMode(read_u8(self.data, 0x08))
    assert read_u8(self.data, 0x09) == 0xFF
    self.duration = read_u16(self.data, 0x0A)
    
    reg_color_anims_count = read_u16(self.data, 0x0C)
    konst_color_anims_count = read_u16(self.data, 0x0E)
    
    reg_r_count = read_u16(self.data, 0x10)
    reg_g_count = read_u16(self.data, 0x12)
    reg_b_count = read_u16(self.data, 0x14)
    reg_a_count = read_u16(self.data, 0x16)
    konst_r_count = read_u16(self.data, 0x18)
    konst_g_count = read_u16(self.data, 0x1A)
    konst_b_count = read_u16(self.data, 0x1C)
    konst_a_count = read_u16(self.data, 0x1E)
    
    reg_color_anims_offset = read_u32(self.data, 0x20)
    konst_color_anims_offset = read_u32(self.data, 0x24)
    
    reg_remap_table_offset = read_u32(self.data, 0x28)
    konst_remap_table_offset = read_u32(self.data, 0x2C)
    
    reg_mat_names_table_offset = read_u32(self.data, 0x30)
    konst_mat_names_table_offset = read_u32(self.data, 0x34)
    
    reg_r_offset = read_u32(self.data, 0x38)
    reg_g_offset = read_u32(self.data, 0x3C)
    reg_b_offset = read_u32(self.data, 0x40)
    reg_a_offset = read_u32(self.data, 0x44)
    konst_r_offset = read_u32(self.data, 0x48)
    konst_g_offset = read_u32(self.data, 0x4C)
    konst_b_offset = read_u32(self.data, 0x50)
    konst_a_offset = read_u32(self.data, 0x54)
    
    # Ensure the remap tables are identity.
    # Actual remapping not currently supported by this implementation.
    for i in range(reg_color_anims_count):
      assert i == read_u16(self.data, reg_remap_table_offset+i*2)
    for i in range(konst_color_anims_count):
      assert i == read_u16(self.data, konst_remap_table_offset+i*2)
    
    reg_mat_names = self.read_string_table(reg_mat_names_table_offset)
    konst_mat_names = self.read_string_table(konst_mat_names_table_offset)
    
    reg_r_track_data = []
    for i in range(reg_r_count):
      r = read_s16(self.data, reg_r_offset+i*2)
      reg_r_track_data.append(r)
    reg_g_track_data = []
    for i in range(reg_g_count):
      g = read_s16(self.data, reg_g_offset+i*2)
      reg_g_track_data.append(g)
    reg_b_track_data = []
    for i in range(reg_b_count):
      b = read_s16(self.data, reg_b_offset+i*2)
      reg_b_track_data.append(b)
    reg_a_track_data = []
    for i in range(reg_a_count):
      a = read_s16(self.data, reg_a_offset+i*2)
      reg_a_track_data.append(a)
    konst_r_track_data = []
    for i in range(konst_r_count):
      r = read_s16(self.data, konst_r_offset+i*2)
      konst_r_track_data.append(r)
    konst_g_track_data = []
    for i in range(konst_g_count):
      g = read_s16(self.data, konst_g_offset+i*2)
      konst_g_track_data.append(g)
    konst_b_track_data = []
    for i in range(konst_b_count):
      b = read_s16(self.data, konst_b_offset+i*2)
      konst_b_track_data.append(b)
    konst_a_track_data = []
    for i in range(konst_a_count):
      a = read_s16(self.data, konst_a_offset+i*2)
      konst_a_track_data.append(a)
    
    reg_animations = []
    konst_animations = []
    self.mat_name_to_reg_anims = OrderedDict()
    self.mat_name_to_konst_anims = OrderedDict()
    
    offset = reg_color_anims_offset
    for i in range(reg_color_anims_count):
      anim = ColorAnimation()
      anim.read(self.data, offset, reg_r_track_data, reg_g_track_data, reg_b_track_data, reg_a_track_data)
      offset += ColorAnimation.DATA_SIZE
      
      reg_animations.append(anim)
      
      mat_name = reg_mat_names[i]
      if mat_name not in self.mat_name_to_reg_anims:
        self.mat_name_to_reg_anims[mat_name] = []
      self.mat_name_to_reg_anims[mat_name].append(anim)
    
    offset = konst_color_anims_offset
    for i in range(konst_color_anims_count):
      anim = ColorAnimation()
      anim.read(self.data, offset, konst_r_track_data, konst_g_track_data, konst_b_track_data, konst_a_track_data)
      offset += ColorAnimation.DATA_SIZE
      
      konst_animations.append(anim)
      
      mat_name = konst_mat_names[i]
      if mat_name not in self.mat_name_to_konst_anims:
        self.mat_name_to_konst_anims[mat_name] = []
      self.mat_name_to_konst_anims[mat_name].append(anim)
  
  def save_chunk_specific_data(self):
    # Cut off all the data, we're rewriting it entirely.
    self.data.truncate(0)
    
    # Placeholder for the header.
    self.data.seek(0)
    self.data.write(b"\0"*0x58)
    
    align_data_to_nearest(self.data, 0x20)
    offset = self.data.tell()
    
    reg_animations = []
    konst_animations = []
    reg_mat_names = []
    konst_mat_names = []
    for mat_name, anims in self.mat_name_to_reg_anims.items():
      for anim in anims:
        reg_animations.append(anim)
        reg_mat_names.append(mat_name)
    for mat_name, anims in self.mat_name_to_konst_anims.items():
      for anim in anims:
        konst_animations.append(anim)
        konst_mat_names.append(mat_name)
    
    reg_r_track_data = []
    reg_g_track_data = []
    reg_b_track_data = []
    reg_a_track_data = []
    reg_color_anims_offset = offset
    if not reg_animations:
      reg_color_anims_offset = 0
    for anim in reg_animations:
      anim.save_changes(self.data, offset, reg_r_track_data, reg_g_track_data, reg_b_track_data, reg_a_track_data)
      offset += ColorAnimation.DATA_SIZE
    
    align_data_to_nearest(self.data, 4)
    offset = self.data.tell()
    
    konst_r_track_data = []
    konst_g_track_data = []
    konst_b_track_data = []
    konst_a_track_data = []
    konst_color_anims_offset = offset
    if not konst_animations:
      konst_color_anims_offset = 0
    for anim in konst_animations:
      anim.save_changes(self.data, offset, konst_r_track_data, konst_g_track_data, konst_b_track_data, konst_a_track_data)
      offset += ColorAnimation.DATA_SIZE
    
    align_data_to_nearest(self.data, 4)
    offset = self.data.tell()
    reg_r_offset = offset
    if not reg_r_track_data:
      reg_r_offset = 0
    for r in reg_r_track_data:
      write_s16(self.data, offset, r)
      offset += 2
    
    align_data_to_nearest(self.data, 4)
    offset = self.data.tell()
    reg_g_offset = offset
    if not reg_g_track_data:
      reg_g_offset = 0
    for g in reg_g_track_data:
      write_s16(self.data, offset, g)
      offset += 2
    
    align_data_to_nearest(self.data, 4)
    offset = self.data.tell()
    reg_b_offset = offset
    if not reg_b_track_data:
      reg_b_offset = 0
    for b in reg_b_track_data:
      write_s16(self.data, offset, b)
      offset += 2
    
    align_data_to_nearest(self.data, 4)
    offset = self.data.tell()
    reg_a_offset = offset
    if not reg_a_track_data:
      reg_a_offset = 0
    for a in reg_a_track_data:
      write_s16(self.data, offset, a)
      offset += 2
    
    align_data_to_nearest(self.data, 4)
    offset = self.data.tell()
    konst_r_offset = offset
    if not konst_r_track_data:
      konst_r_offset = 0
    for r in konst_r_track_data:
      write_s16(self.data, offset, r)
      offset += 2
    
    align_data_to_nearest(self.data, 4)
    offset = self.data.tell()
    konst_g_offset = offset
    if not konst_g_track_data:
      konst_g_offset = 0
    for g in konst_g_track_data:
      write_s16(self.data, offset, g)
      offset += 2
    
    align_data_to_nearest(self.data, 4)
    offset = self.data.tell()
    konst_b_offset = offset
    if not konst_b_track_data:
      konst_b_offset = 0
    for b in konst_b_track_data:
      write_s16(self.data, offset, b)
      offset += 2
    
    align_data_to_nearest(self.data, 4)
    offset = self.data.tell()
    konst_a_offset = offset
    if not konst_a_track_data:
      konst_a_offset = 0
    for a in konst_a_track_data:
      write_s16(self.data, offset, a)
      offset += 2
    
    align_data_to_nearest(self.data, 4)
    offset = self.data.tell()
    
    # Remaps tables always written as identity, remapping not supported.
    reg_remap_table_offset = offset
    if not reg_animations:
      reg_remap_table_offset = 0
    for i in range(len(reg_animations)):
      write_u16(self.data, offset, i)
      offset += 2
    
    konst_remap_table_offset = offset
    if not konst_animations:
      konst_remap_table_offset = 0
    for i in range(len(konst_animations)):
      write_u16(self.data, offset, i)
      offset += 2
    
    align_data_to_nearest(self.data, 4)
    offset = self.data.tell()
    
    reg_mat_names_table_offset = offset
    self.write_string_table(reg_mat_names_table_offset, reg_mat_names)
    
    align_data_to_nearest(self.data, 4)
    offset = self.data.tell()
    
    konst_mat_names_table_offset = offset
    self.write_string_table(konst_mat_names_table_offset, konst_mat_names)
    
    
    # Write the header.
    write_magic_str(self.data, 0, "TRK1", 4)
    
    write_u8(self.data, 0x08, self.loop_mode.value)
    write_u8(self.data, 0x09, 0xFF)
    write_u16(self.data, 0x0A, self.duration)
    
    write_u16(self.data, 0x0C, len(reg_animations))
    write_u16(self.data, 0x0E, len(konst_animations))
    
    write_s16(self.data, 0x10, len(reg_r_track_data))
    write_s16(self.data, 0x12, len(reg_g_track_data))
    write_s16(self.data, 0x14, len(reg_b_track_data))
    write_s16(self.data, 0x16, len(reg_a_track_data))
    write_s16(self.data, 0x18, len(konst_r_track_data))
    write_s16(self.data, 0x1A, len(konst_g_track_data))
    write_s16(self.data, 0x1C, len(konst_b_track_data))
    write_s16(self.data, 0x1E, len(konst_a_track_data))
    
    write_u32(self.data, 0x20, reg_color_anims_offset)
    write_u32(self.data, 0x24, konst_color_anims_offset)
    
    write_u32(self.data, 0x28, reg_remap_table_offset)
    write_u32(self.data, 0x2C, konst_remap_table_offset)
    
    write_u32(self.data, 0x30, reg_mat_names_table_offset)
    write_u32(self.data, 0x34, konst_mat_names_table_offset)
    
    write_u32(self.data, 0x38, reg_r_offset)
    write_u32(self.data, 0x3C, reg_g_offset)
    write_u32(self.data, 0x40, reg_b_offset)
    write_u32(self.data, 0x44, reg_a_offset)
    write_u32(self.data, 0x48, konst_r_offset)
    write_u32(self.data, 0x4C, konst_g_offset)
    write_u32(self.data, 0x50, konst_b_offset)
    write_u32(self.data, 0x54, konst_a_offset)

class LoopMode(Enum):
  ONCE = 0
  ONCE_AND_RESET = 1
  REPEAT = 2
  MIRRORED_ONCE = 3
  MIRRORED_REPEAT = 4

class TangentType(Enum):
  IN     =   0
  IN_OUT =   1

class AnimationTrack:
  DATA_SIZE = 6
  
  def __init__(self):
    self.tangent_type = TangentType.IN_OUT
    self.keyframes = []
  
  def read(self, data, offset, track_data):
    self.count = read_u16(data, offset+0)
    self.index = read_u16(data, offset+2)
    self.tangent_type = TangentType(read_u16(data, offset+4))
    
    self.keyframes = []
    if self.count == 1:
      keyframe = AnimationKeyframe(0, track_data[self.index], 0, 0)
      self.keyframes.append(keyframe)
    else:
      if self.tangent_type == TangentType.IN:
        for i in range(self.index, self.index + self.count*3, 3):
          keyframe = AnimationKeyframe(track_data[i+0], track_data[i+1], track_data[i+2], track_data[i+2])
          self.keyframes.append(keyframe)
      elif self.tangent_type == TangentType.IN_OUT:
        for i in range(self.index, self.index + self.count*4, 4):
          keyframe = AnimationKeyframe(track_data[i+0], track_data[i+1], track_data[i+2], track_data[i+3])
          self.keyframes.append(keyframe)
      else:
        raise Exception("Invalid tangent type")
  
  def save_changes(self, data, offset, track_data):
    self.count = len(self.keyframes)
    
    this_track_data = []
    
    if self.count == 1:
      this_track_data.append(self.keyframes[0].value)
    else:
      if self.tangent_type == TangentType.IN:
        for keyframe in self.keyframes:
          this_track_data.append(keyframe.time)
          this_track_data.append(keyframe.value)
          this_track_data.append(keyframe.tangent_in)
      elif self.tangent_type == TangentType.IN_OUT:
        for keyframe in self.keyframes:
          this_track_data.append(keyframe.time)
          this_track_data.append(keyframe.value)
          this_track_data.append(keyframe.tangent_in)
          this_track_data.append(keyframe.tangent_out)
      else:
        raise Exception("Invalid tangent type")
    
    # Try to find if this track's data is already in the full track list to avoid duplicating data.
    self.index = None
    for i in range(len(track_data) - len(this_track_data) + 1):
      found_match = True
      
      for j in range(len(this_track_data)):
        if track_data[i+j] != this_track_data[j]:
          found_match = False
          break
      
      if found_match:
        self.index = i
        break
    
    if self.index is None:
      # If this data isn't already in the list, we append it to the end.
      self.index = len(track_data)
      track_data += this_track_data
    
    write_u16(data, offset+0, self.count)
    write_u16(data, offset+2, self.index)
    write_u16(data, offset+4, self.tangent_type.value)

class AnimationKeyframe:
  def __init__(self, time, value, tangent_in, tangent_out):
    self.time = time
    self.value = value
    self.tangent_in = tangent_in
    self.tangent_out = tangent_out

class ColorAnimation:
  DATA_SIZE = 4*AnimationTrack.DATA_SIZE + 4
  
  def __init__(self):
    pass
  
  def read(self, data, offset, r_track_data, g_track_data, b_track_data, a_track_data):
    self.r = AnimationTrack()
    self.r.read(data, offset, r_track_data)
    offset += AnimationTrack.DATA_SIZE
    
    self.g = AnimationTrack()
    self.g.read(data, offset, g_track_data)
    offset += AnimationTrack.DATA_SIZE
    
    self.b = AnimationTrack()
    self.b.read(data, offset, b_track_data)
    offset += AnimationTrack.DATA_SIZE
    
    self.a = AnimationTrack()
    self.a.read(data, offset, a_track_data)
    offset += AnimationTrack.DATA_SIZE
    
    self.color_id = read_u8(data, offset)
    offset += 4
  
  def save_changes(self, data, offset, r_track_data, g_track_data, b_track_data, a_track_data):
    self.r.save_changes(data, offset, r_track_data)
    offset += AnimationTrack.DATA_SIZE
    
    self.g.save_changes(data, offset, g_track_data)
    offset += AnimationTrack.DATA_SIZE
    
    self.b.save_changes(data, offset, b_track_data)
    offset += AnimationTrack.DATA_SIZE
    
    self.a.save_changes(data, offset, a_track_data)
    offset += AnimationTrack.DATA_SIZE
    
    write_u8(data, offset, self.color_id)
    write_u8(data, offset+1, 0xFF)
    write_u8(data, offset+2, 0xFF)
    write_u8(data, offset+3, 0xFF)
    offset += 4
