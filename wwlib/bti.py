
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
  
  
  
  def read_palettes(self):
    if self.image_format not in self.IMAGE_FORMATS_THAT_USE_PALETTES:
      self.colors = None
      return
    
    self.colors = []
    offset = 0
    for i in range(self.num_colors):
      raw_color = read_u16(self.palette_data, offset)
      if self.palette_format == 0:
        color = convert_ia8_to_color(raw_color)
      elif self.palette_format == 1:
        color = convert_rgb565_to_color(raw_color)
      elif self.palette_format == 2:
        color = convert_rgb5a3_to_color(raw_color)
      self.colors.append(color)
      offset += 2
  
  
  
  def render(self):
    self.read_palettes()
    
    image = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
    pixels = image.load()
    offset = 0
    block_x = 0
    block_y = 0
    while block_y < self.height:
      pixel_color_data = self.render_block(offset)
      
      for i, color in enumerate(pixel_color_data):
        x_in_block = i % self.block_width
        y_in_block = i // self.block_width
        x = block_x+x_in_block
        y = block_y+y_in_block
        if x >= self.width or y >= self.height:
          continue
        
        pixels[x,y] = color
      
      offset += self.block_data_size
      block_x += self.block_width
      if block_x >= self.width:
        block_x = 0
        block_y += self.block_height
    
    return image
  
  def render_block(self, offset):
    if self.image_format == 0:
      return self.render_i4_block(offset)
    elif self.image_format == 1:
      return self.render_i8_block(offset)
    elif self.image_format == 2:
      return self.render_ia4_block(offset)
    elif self.image_format == 3:
      return self.render_ia8_block(offset)
    elif self.image_format == 4:
      return self.render_rgb565_block(offset)
    elif self.image_format == 5:
      return self.render_rgb5a3_block(offset)
    elif self.image_format == 6:
      return self.render_rgba32_block(offset)
    elif self.image_format == 8:
      return self.render_c4_block(offset)
    elif self.image_format == 9:
      return self.render_c8_block(offset)
    elif self.image_format == 0xA:
      return self.render_c14x2_block(offset)
    elif self.image_format == 0xE:
      return self.render_cmpr_block(offset)
    else:
      raise Exception("Unknown image format: %X" % self.image_format)
  
  def render_i4_block(self, offset):
    pixel_color_data = []
    
    for byte_index in range(self.block_data_size):
      byte = read_u8(self.image_data, offset+byte_index)
      for nibble_index in range(2):
        i4 = (byte >> (1-nibble_index)*4) & 0xF
        color = convert_i4_to_color(i4)
        
        pixel_color_data.append(color)
    
    return pixel_color_data
  
  def render_i8_block(self, offset):
    pixel_color_data = []
    
    for i in range(self.block_data_size):
      i8 = read_u8(self.image_data, offset+i)
      color = convert_i8_to_color(i8)
      
      pixel_color_data.append(color)
    
    return pixel_color_data
  
  def render_ia4_block(self, offset):
    pixel_color_data = []
    
    for i in range(self.block_data_size):
      ia4 = read_u8(self.image_data, offset+i)
      color = convert_ia4_to_color(ia4)
      
      pixel_color_data.append(color)
    
    return pixel_color_data
  
  def render_ia8_block(self, offset):
    pixel_color_data = []
    
    for i in range(self.block_data_size//2):
      ia8 = read_u16(self.image_data, offset+i*2)
      color = convert_ia8_to_color(ia8)
      
      pixel_color_data.append(color)
    
    return pixel_color_data
  
  def render_rgb565_block(self, offset):
    pixel_color_data = []
    
    for i in range(self.block_data_size//2):
      rgb565 = read_u16(self.image_data, offset+i*2)
      color = convert_rgb565_to_color(rgb565)
      
      pixel_color_data.append(color)
    
    return pixel_color_data
  
  def render_rgb5a3_block(self, offset):
    pixel_color_data = []
    
    for i in range(self.block_data_size//2):
      rgb5a3 = read_u16(self.image_data, offset+i*2)
      color = convert_rgb5a3_to_color(rgb5a3)
      
      pixel_color_data.append(color)
    
    return pixel_color_data
  
  def render_rgba32_block(self, offset):
    pixel_color_data = []
    
    for i in range(16):
      a = read_u8(self.image_data, offset+(i*2))
      r = read_u8(self.image_data, offset+(i*2)+1)
      g = read_u8(self.image_data, offset+(i*2)+32)
      b = read_u8(self.image_data, offset+(i*2)+33)
      color = (r, g, b, a)
      
      pixel_color_data.append(color)
    
    return pixel_color_data
  
  def render_c4_block(self, offset):
    pixel_color_data = []
    
    for byte_index in range(self.block_data_size):
      byte = read_u8(self.image_data, offset+byte_index)
      for nibble_index in range(2):
        color_index = (byte >> (1-nibble_index)*4) & 0xF
        color = self.colors[color_index]
        
        pixel_color_data.append(color)
    
    return pixel_color_data
  
  def render_c8_block(self, offset):
    pixel_color_data = []
    
    for i in range(self.block_data_size):
      color_index = read_u8(self.image_data, offset+i)
      if color_index == 0xFF:
        # This block bleeds past the edge of the image
        color = None
      else:
        color = self.colors[color_index]
      
      pixel_color_data.append(color)
    
    return pixel_color_data
  
  def render_c14x2_block(self, offset):
    pixel_color_data = []
    
    for i in range(self.block_data_size//2):
      color_index = read_u16(self.image_data, offset+i*2) & 0x3FFF
      if color_index == 0x3FFF:
        # This block bleeds past the edge of the image
        color = None
      else:
        color = self.colors[color_index]
      
      pixel_color_data.append(color)
    
    return pixel_color_data
  
  def render_cmpr_block(self, offset):
    pixel_color_data = [None]*64
    
    subblock_offset = offset
    for subblock_index in range(4):
      subblock_x = (subblock_index%2)*4
      subblock_y = (subblock_index//2)*4
      
      color_0_rgb565 = read_u16(self.image_data, subblock_offset)
      color_1_rgb565 = read_u16(self.image_data, subblock_offset+2)
      colors = get_interpolated_cmpr_colors(color_0_rgb565, color_1_rgb565)
      
      color_indexes = read_u32(self.image_data, subblock_offset+4)
      for i in range(16):
        color_index = ((color_indexes >> ((15-i)*2)) & 3)
        color = colors[color_index]
        
        x_in_subblock = i % 4
        y_in_subblock = i // 4
        pixel_index_in_block = subblock_x + subblock_y*8 + y_in_subblock*8 + x_in_subblock
        
        pixel_color_data[pixel_index_in_block] = color
      
      subblock_offset += 8
    
    return pixel_color_data
  
  def replace_image(self, new_image_file_path):
    self.image_data, self.palette_data, self.colors = encode_image(new_image_file_path, self.image_format, self.palette_format)
    self.num_colors = len(self.colors)

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
