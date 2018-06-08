
import os
from enum import Enum
from io import BytesIO

from wwlib.bti import BTI

from fs_helpers import *

class BDL:
  def __init__(self, file_entry):
    self.file_entry = file_entry
    self.file_entry.decompress_data_if_necessary()
    data = self.file_entry.data
    
    self.magic = read_str(data, 0, 4)
    self.model_type = read_str(data, 4, 4)
    self.length = read_u32(data, 8)
    self.num_chunks = read_u32(data, 0x0C)
    
    self.chunks = []
    offset = 0x20
    for chunk_index in range(self.num_chunks):
      chunk = BDLChunk(data, offset)
      self.chunks.append(chunk)
      
      if chunk.magic == "TEX1":
        self.tex1 = chunk
      
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

class BDLChunk:
  def __init__(self, bdl_data, chunk_offset):
    self.magic = read_str(bdl_data, chunk_offset, 4)
    self.size = read_u32(bdl_data, chunk_offset+4)
    
    bdl_data.seek(chunk_offset)
    self.data = BytesIO(bdl_data.read(self.size))
    
    if self.magic == "TEX1":
      self.read_tex1()
  
  def save_changes(self):
    write_str(self.data, 0, self.magic, 4)
    write_u32(self.data, 4, self.size)
    
    if self.magic == "TEX1":
      self.save_tex1()
  
  def read_tex1(self):
    self.textures = []
    self.num_textures = read_u16(self.data, 8)
    self.texture_header_list_offset = read_u32(self.data, 0x0C)
    for texture_index in range(self.num_textures):
      bti_header_offset = self.texture_header_list_offset + texture_index*0x20
      texture = BTI(self.data, bti_header_offset)
      self.textures.append(texture)
  
  def save_tex1(self):
    # Does not support adding new textures currently.
    assert len(self.textures) == self.num_textures
    
    next_available_data_offset = self.texture_header_list_offset + self.num_textures*0x20 # Right after the last header ends
    self.data.truncate(next_available_data_offset)
    self.data.seek(next_available_data_offset)
    for texture in self.textures:
      self.data.seek(next_available_data_offset)
      
      texture.image_data_offset = next_available_data_offset - texture.header_offset
      self.data.write(texture.image_data)
      next_available_data_offset += len(texture.image_data)
      
      if texture.image_format in BTI.IMAGE_FORMATS_THAT_USE_PALETTES:
        texture.palette_data_offset = next_available_data_offset - texture.header_offset
        self.data.write(texture.palette_data)
        next_available_data_offset += len(texture.palette_data)
      else:
        # If the image doesn't use palettes its palette offset is just the same as the first texture's image offset.
        first_texture = self.textures[0]
        texture.palette_data_offset = first_texture.image_data_offset + first_texture.header_offset - texture.header_offset
      
      texture.save_header_changes()
