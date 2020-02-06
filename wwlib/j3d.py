
import os
from enum import Enum
from io import BytesIO
from collections import OrderedDict

from wwlib.bti import BTI

from fs_helpers import *

IMPLEMENTED_CHUNK_TYPES = [
  "TEX1",
  "TRK1",
]

class J3DFile:
  def __init__(self, file_entry):
    self.file_entry = file_entry
    self.file_entry.decompress_data_if_necessary()
    data = self.file_entry.data
    
    self.magic = read_str(data, 0, 4)
    assert self.magic.startswith("J3D")
    self.file_type = read_str(data, 4, 4)
    self.length = read_u32(data, 8)
    self.num_chunks = read_u32(data, 0x0C)
    
    self.chunks = []
    self.chunk_by_type = {}
    offset = 0x20
    for chunk_index in range(self.num_chunks):
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
    data = self.file_entry.data
    
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
    
    write_str(data, 0, self.magic, 4)
    write_str(data, 4, self.file_type, 4)
    write_u32(data, 8, self.length)
    write_u32(data, 0xC, self.num_chunks)

class BDL(J3DFile):
  def __init__(self, file_entry):
    super().__init__(file_entry)
    
    assert self.magic == "J3D2"
    assert self.file_type == "bdl4"

class BMD(J3DFile):
  def __init__(self, file_entry):
    super().__init__(file_entry)
    
    assert self.magic == "J3D2"
    assert self.file_type == "bmd3"

class BMT(J3DFile):
  def __init__(self, file_entry):
    super().__init__(file_entry)
    
    assert self.magic == "J3D2"
    assert self.file_type == "bmt3"

class BRK(J3DFile):
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
    # The original J3D files used the repeating string "This is padding" for the padding, but we simply use null bytes instead.
    
    self.size = data_len(self.data)
    write_str(self.data, 0, self.magic, 4)
    write_u32(self.data, 4, self.size)
  
  def save_chunk_specific_data(self):
    pass

class TEX1(J3DChunk):
  def read_chunk_specific_data(self):
    self.textures = []
    self.num_textures = read_u16(self.data, 8)
    self.texture_header_list_offset = read_u32(self.data, 0x0C)
    for texture_index in range(self.num_textures):
      bti_header_offset = self.texture_header_list_offset + texture_index*0x20
      texture = BTI(self.data, bti_header_offset)
      self.textures.append(texture)
    
    self.string_section_offset = read_u32(self.data, 0x10)
    self.num_strings = read_u16(self.data, self.string_section_offset)
    self.string_unknown_1 = read_u16(self.data, self.string_section_offset+2)
    self.string_unknown_2 = read_u16(self.data, self.string_section_offset+4)
    self.string_data_offset = read_u16(self.data, self.string_section_offset+6)
    self.string_unknown_3 = read_bytes(self.data, self.string_section_offset+8, self.string_data_offset-8)
    
    self.texture_names = []
    self.textures_by_name = OrderedDict()
    offset_in_string_list = self.string_data_offset
    for texture in self.textures:
      filename = read_str_until_null_character(self.data, self.string_section_offset + offset_in_string_list)
      self.texture_names.append(filename)
      if filename not in self.textures_by_name:
        self.textures_by_name[filename] = []
      self.textures_by_name[filename].append(texture)
      
      offset_in_string_list += len(filename) + 1
  
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
    
    self.string_section_offset = next_available_data_offset
    write_u32(self.data, 0x10, self.string_section_offset)
    write_u16(self.data, self.string_section_offset, self.num_strings)
    write_u16(self.data, self.string_section_offset+2, self.string_unknown_1)
    write_u16(self.data, self.string_section_offset+4, self.string_unknown_2)
    write_u16(self.data, self.string_section_offset+6, self.string_data_offset)
    write_bytes(self.data, self.string_section_offset+8, self.string_unknown_3)
    
    offset_in_string_list = self.string_data_offset
    for i, texture in enumerate(self.textures):
      filename = self.texture_names[i]
      write_str_with_null_byte(self.data, self.string_section_offset+offset_in_string_list, filename)
      offset_in_string_list += len(filename) + 1

class TRK1(J3DChunk):
  def read_chunk_specific_data(self):
    self.reg_color_anims_count = read_u16(self.data, 0x0C)
    self.konst_color_anims_count = read_u16(self.data, 0x0E)
    
    self.reg_r_count = read_u16(self.data, 0x10)
    self.reg_g_count = read_u16(self.data, 0x12)
    self.reg_b_count = read_u16(self.data, 0x14)
    self.reg_a_count = read_u16(self.data, 0x16)
    self.konst_r_count = read_u16(self.data, 0x18)
    self.konst_g_count = read_u16(self.data, 0x1A)
    self.konst_b_count = read_u16(self.data, 0x1C)
    self.konst_a_count = read_u16(self.data, 0x1E)
    
    self.reg_color_anims_offset = read_u32(self.data, 0x20)
    self.konst_color_anims_offset = read_u32(self.data, 0x24)
    
    self.reg_r_offset = read_u32(self.data, 0x38)
    self.reg_g_offset = read_u32(self.data, 0x3C)
    self.reg_b_offset = read_u32(self.data, 0x40)
    self.reg_a_offset = read_u32(self.data, 0x44)
    self.konst_r_offset = read_u32(self.data, 0x48)
    self.konst_g_offset = read_u32(self.data, 0x4C)
    self.konst_b_offset = read_u32(self.data, 0x50)
    self.konst_a_offset = read_u32(self.data, 0x54)
    
    self.reg_rs = []
    for i in range(self.reg_r_count):
      r = read_s16(self.data, self.reg_r_offset+i*2)
      self.reg_rs.append(r)
    self.reg_gs = []
    for i in range(self.reg_g_count):
      g = read_s16(self.data, self.reg_g_offset+i*2)
      self.reg_gs.append(g)
    self.reg_bs = []
    for i in range(self.reg_b_count):
      b = read_s16(self.data, self.reg_b_offset+i*2)
      self.reg_bs.append(b)
    self.reg_as = []
    for i in range(self.reg_a_count):
      a = read_s16(self.data, self.reg_a_offset+i*2)
      self.reg_as.append(a)
    self.konst_rs = []
    for i in range(self.konst_r_count):
      r = read_s16(self.data, self.konst_r_offset+i*2)
      self.konst_rs.append(r)
    self.konst_gs = []
    for i in range(self.konst_g_count):
      g = read_s16(self.data, self.konst_g_offset+i*2)
      self.konst_gs.append(g)
    self.konst_bs = []
    for i in range(self.konst_b_count):
      b = read_s16(self.data, self.konst_b_offset+i*2)
      self.konst_bs.append(b)
    self.konst_as = []
    for i in range(self.konst_a_count):
      a = read_s16(self.data, self.konst_a_offset+i*2)
      self.konst_as.append(a)
  
  def save_chunk_specific_data(self):
    # Does not support adding new color entries currently.
    for i in range(self.reg_r_count):
      write_s16(self.data, self.reg_r_offset+i*2, self.reg_rs[i])
    for i in range(self.reg_g_count):
      write_s16(self.data, self.reg_g_offset+i*2, self.reg_gs[i])
    for i in range(self.reg_b_count):
      write_s16(self.data, self.reg_b_offset+i*2, self.reg_bs[i])
    for i in range(self.reg_a_count):
      write_s16(self.data, self.reg_a_offset+i*2, self.reg_as[i])
    for i in range(self.konst_r_count):
      write_s16(self.data, self.konst_r_offset+i*2, self.konst_rs[i])
    for i in range(self.konst_g_count):
      write_s16(self.data, self.konst_g_offset+i*2, self.konst_gs[i])
    for i in range(self.konst_b_count):
      write_s16(self.data, self.konst_b_offset+i*2, self.konst_bs[i])
    for i in range(self.konst_a_count):
      write_s16(self.data, self.konst_a_offset+i*2, self.konst_as[i])
