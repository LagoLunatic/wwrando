
from io import BytesIO
from enum import Enum

from fs_helpers import *
from wwlib.texture_utils import *

class WrapMode(Enum):
  ClampToEdge    = 0
  Repeat         = 1
  MirroredRepeat = 2

class FilterMode(Enum):
  Nearest              = 0
  Linear               = 1
  NearestMipmapNearest = 2
  NearestMipmapLinear  = 3
  LinearMipmapNearest  = 4
  LinearMipmapLinear   = 5

class BTI:
  def __init__(self, data, header_offset=0):
    self.data = data
    self.header_offset = header_offset
    
    self.image_format = ImageFormat(read_u8(data, header_offset+0))
    
    self.alpha_setting = read_u8(data, header_offset+1)
    self.width = read_u16(data, header_offset+2)
    self.height = read_u16(data, header_offset+4)
    
    self.wrap_s = WrapMode(read_u8(data, header_offset+6))
    self.wrap_t = WrapMode(read_u8(data, header_offset+7))
    
    self.palettes_enabled = bool(read_u8(data, header_offset+8))
    self.palette_format = PaletteFormat(read_u8(data, header_offset+9))
    self.num_colors = read_u16(data, header_offset+0xA)
    self.palette_data_offset = read_u32(data, header_offset+0xC)
    
    self.mag_filter = FilterMode(read_u8(data, header_offset+0x14))
    self.min_filter = FilterMode(read_u8(data, header_offset+0x15))
    
    self.unknown_2 = read_u16(data, header_offset+0x16)
    self.mipmap_count = read_u8(data, header_offset+0x18)
    self.unknown_3 = read_u8(data, header_offset+0x19)
    self.lod_bias = read_u16(data, header_offset+0x1A)
    
    self.image_data_offset = read_u32(data, header_offset+0x1C)
    
    blocks_wide = (self.width + (self.block_width-1)) // self.block_width
    blocks_tall = (self.height + (self.block_height-1)) // self.block_height
    image_data_size = blocks_wide*blocks_tall*self.block_data_size
    self.image_data = BytesIO(read_bytes(data, header_offset+self.image_data_offset, image_data_size))
    
    palette_data_size = self.num_colors*2
    self.palette_data = BytesIO(read_bytes(data, header_offset+self.palette_data_offset, palette_data_size))
  
  def save_header_changes(self):
    write_u8(self.data, self.header_offset+0, self.image_format.value)
    
    write_u8(self.data, self.header_offset+1, self.alpha_setting)
    write_u16(self.data, self.header_offset+2, self.width)
    write_u16(self.data, self.header_offset+4, self.height)
    
    write_u8(self.data, self.header_offset+6, self.wrap_s.value)
    write_u8(self.data, self.header_offset+7, self.wrap_t.value)
    
    self.palettes_enabled = self.needs_palettes()
    write_u8(self.data, self.header_offset+8, int(self.palettes_enabled))
    write_u8(self.data, self.header_offset+9, self.palette_format.value)
    write_u16(self.data, self.header_offset+0xA, self.num_colors)
    write_u32(self.data, self.header_offset+0xC, self.palette_data_offset)
    
    write_u8(self.data, self.header_offset+0x14, self.mag_filter.value)
    write_u8(self.data, self.header_offset+0x15, self.min_filter.value)
    
    write_u16(self.data, self.header_offset+0x16, self.unknown_2)
    write_u8(self.data, self.header_offset+0x18, self.mipmap_count)
    write_u8(self.data, self.header_offset+0x19, self.unknown_3)
    write_u16(self.data, self.header_offset+0x1A, self.lod_bias)
    
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
  
  def is_greyscale(self):
    if self.needs_palettes():
      return self.palette_format in GREYSCALE_PALETTE_FORMATS
    else:
      return self.image_format in GREYSCALE_IMAGE_FORMATS
  
  def render(self):
    image = decode_image(
      self.image_data, self.palette_data,
      self.image_format, self.palette_format,
      self.num_colors,
      self.width, self.height
    )
    return image
  
  def replace_image_from_path(self, new_image_file_path):
    self.image_data, self.palette_data, encoded_colors = encode_image_from_path(
      new_image_file_path, self.image_format, self.palette_format
    )
    self.num_colors = len(encoded_colors)
  
  def replace_image(self, new_image):
    self.image_data, self.palette_data, encoded_colors = encode_image(
      new_image, self.image_format, self.palette_format
    )
    self.num_colors = len(encoded_colors)
    self.width = new_image.width
    self.height = new_image.height

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
