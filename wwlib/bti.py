
from PIL import Image
from io import BytesIO

from fs_helpers import *
from wwlib.color_helpers import *

class BTI:
  def __init__(self, data, header_offset=0):
    self.data = data
    self.header_offset = header_offset
    
    self.image_format = read_u8(data, header_offset+0)
    
    self.alpha_enabled = bool(read_u8(data, header_offset+1))
    self.width = read_u16(data, header_offset+2)
    self.height = read_u16(data, header_offset+4)
    
    self.palettes_enabled = bool(read_u8(data, header_offset+8))
    self.palette_format = read_u8(data, header_offset+9)
    if not self.palette_format in [0, 1, 2]:
      raise Exception("Unknown palette format: %X" % self.palette_format)
    self.num_colors = read_u16(data, header_offset+0xA)
    
    self.palette_data_offset = read_u32(data, header_offset+0xC)
    self.image_data_offset = read_u32(data, header_offset+0x1C)
    
    blocks_wide = (self.width + (self.block_width-1)) // self.block_width
    blocks_tall = (self.height + (self.block_height-1)) // self.block_height
    image_data_size = blocks_wide*blocks_tall*self.block_data_size
    self.image_data = BytesIO(read_bytes(data, header_offset+self.image_data_offset, image_data_size))
    
    palette_data_size = self.num_colors*2
    self.palette_data = BytesIO(read_bytes(data, header_offset+self.palette_data_offset, palette_data_size))
  
  def save_header_changes(self):
    write_u8(self.data, self.header_offset+0, self.image_format)
    write_u16(self.data, self.header_offset+2, self.width)
    write_u16(self.data, self.header_offset+4, self.height)
    self.palettes_enabled = self.needs_palettes()
    write_u8(self.data, self.header_offset+8, int(self.palettes_enabled))
    write_u8(self.data, self.header_offset+9, self.palette_format)
    write_u16(self.data, self.header_offset+0xA, self.num_colors)
    write_u32(self.data, self.header_offset+0xC, self.palette_data_offset)
    write_u32(self.data, self.header_offset+0x1C, self.image_data_offset)
  
  @property
  def block_width(self):
    return BLOCK_WIDTHS[self.image_format]
  
  @property
  def block_height(self):
    return BLOCK_HEIGHTS[self.image_format]
  
  @property
  def block_data_size(self):
    return BLOCK_DATA_SIZES[self.image_format]
  
  def needs_palettes(self):
    return self.image_format in IMAGE_FORMATS_THAT_USE_PALETTES
  
  def render(self):
    image = decode_image(
      self.image_data, self.palette_data,
      self.image_format, self.palette_format,
      self.num_colors,
      self.width, self.height
    )
    return image
  
  def replace_image(self, new_image_file_path):
    self.image_data, self.palette_data, colors = encode_image(new_image_file_path, self.image_format, self.palette_format)
    self.num_colors = len(colors)

class BTIFile(BTI): # For standalone .bti files (as opposed to textures embedded in .bdl models)
  def __init__(self, file_entry):
    self.file_entry = file_entry
    self.file_entry.decompress_data_if_necessary()
    super(BTIFile, self).__init__(self.file_entry.data)
  
  def save_changes(self):
    # Cut off the image and palette data first since we're replacing this data entirely.
    self.data.truncate(0x20)
    self.data.seek(0x20)
    
    self.image_data_offset = 0x20
    self.image_data.seek(0)
    self.data.write(self.image_data.read())
    
    if self.needs_palettes():
      self.palette_data_offset = 0x20 + data_len(self.image_data)
      self.palette_data.seek(0)
      self.data.write(self.palette_data.read())
    else:
      self.palette_data_offset = 0
    
    self.save_header_changes()
