
from PIL import Image
from io import BytesIO

from fs_helpers import *

class BTI:
  IMAGE_FORMATS_THAT_USE_PALETTES = [8, 9, 0xA]
  
  MAX_COLORS_FOR_IMAGE_FORMAT = {
    0x8: 1<<4, # C4
    0x9: 1<<8, # C8
    0xA: 1<<14, # C14X2
  }
  
  def __init__(self, data, header_offset=0):
    self.data = data
    self.header_offset = header_offset
    
    self.image_format = read_u8(data, header_offset+0)
    
    if self.image_format in [3, 4, 5, 6, 0xA]:
      self.block_width = 4
      self.block_height = 4
    elif self.image_format in [0, 8, 0xE]:
      self.block_width = 8
      self.block_height = 8
    elif self.image_format in [1, 2, 9]:
      self.block_width = 8
      self.block_height = 4
    else:
      raise Exception("Unknown image format: %X" % self.image_format)
    if self.image_format == 6:
      self.block_data_size = 64
    else:
      self.block_data_size = 32
    
    self.alpha_enabled = bool(read_u8(data, header_offset+1))
    self.width = read_u16(data, header_offset+2)
    self.height = read_u16(data, header_offset+4)
    
    self.palette_format = read_u8(data, header_offset+9)
    if not self.palette_format in [0, 1, 2]:
      raise Exception("Unknown palette format: %X" % self.palette_format)
    self.num_colors = read_u16(data, header_offset+0xA)
    
    self.palette_data_offset = read_u32(data, header_offset+0xC)
    self.image_data_offset = read_u32(data, header_offset+0x1C)
    
    blocks_wide = (self.width + (self.block_width-1)) // self.block_width
    blocks_tall = (self.height + (self.block_height-1)) // self.block_height
    image_data_size = blocks_wide*blocks_tall*self.block_data_size
    self.image_data = read_bytes(data, header_offset+self.image_data_offset, image_data_size)
    
    palette_data_size = self.num_colors*2
    self.palette_data = read_bytes(data, header_offset+self.palette_data_offset, palette_data_size)
  
  def save_header_changes(self):
    write_u16(self.data, self.header_offset+2, self.width)
    write_u16(self.data, self.header_offset+4, self.height)
    write_u16(self.data, self.header_offset+0xA, self.num_colors)
    write_u32(self.data, self.header_offset+0xC, self.palette_data_offset)
    write_u32(self.data, self.header_offset+0x1C, self.image_data_offset)
  
  
  
  @staticmethod
  def convert_rgb565_to_color(rgb565):
    r = ((rgb565 >> 11) & 0x1F)
    g = ((rgb565 >> 5) & 0x3F)
    b = ((rgb565 >> 0) & 0x1F)
    r = r*255//0x1F
    g = g*255//0x3F
    b = b*255//0x1F
    return (r, g, b, 255)
  
  @staticmethod
  def convert_color_to_rgb565(color):
    r, g, b, a = color
    r = r*0x1F//255
    g = g*0x3F//255
    b = b*0x1F//255
    rgb565 = 0x0000
    rgb565 |= ((r & 0x1F) << 11)
    rgb565 |= ((g & 0x3F) << 5)
    rgb565 |= ((b & 0x1F) << 0)
    return rgb565
  
  @staticmethod
  def convert_rgb5a3_to_color(rgb5a3):
    # RGB5A3 format.
    # Each color takes up two bytes.
    # Format depends on the most significant bit. Two possible formats:
    # Top bit is 0: 0AAARRRRGGGGBBBB
    # Top bit is 1: 1RRRRRGGGGGBBBBB (Alpha set to 0xff)
    if (rgb5a3 & 0x8000) == 0:
      a = ((rgb5a3 >> 12) & 0x7)
      r = ((rgb5a3 >> 8) & 0xF)
      g = ((rgb5a3 >> 4) & 0xF)
      b = ((rgb5a3 >> 0) & 0xF)
      a = a*255//7
      r = r*255//0xF
      g = g*255//0xF
      b = b*255//0xF
    else:
      a = 255
      r = ((rgb5a3 >> 10) & 0x1F)
      g = ((rgb5a3 >> 5) & 0x1F)
      b = ((rgb5a3 >> 0) & 0x1F)
      r = r*255//0x1F
      g = g*255//0x1F
      b = b*255//0x1F
    return (r, g, b, a)
  
  @staticmethod
  def convert_color_to_rgb5a3(color):
    r, g, b, a = color
    if a != 255:
      a = a*0x7//255
      r = r*0xF//255
      g = g*0xF//255
      b = b*0xF//255
      rgb5a3 = 0x0000
      rgb5a3 |= ((a & 0x7) << 12)
      rgb5a3 |= ((r & 0xF) << 8)
      rgb5a3 |= ((g & 0xF) << 4)
      rgb5a3 |= ((b & 0xF) << 0)
    else:
      r = r*0x1F//255
      g = g*0x1F//255
      b = b*0x1F//255
      rgb5a3 = 0x8000
      rgb5a3 |= ((r & 0x1F) << 10)
      rgb5a3 |= ((g & 0x1F) << 5)
      rgb5a3 |= ((b & 0x1F) << 0)
    return rgb5a3
  
  @staticmethod
  def convert_ia4_to_color(ia4):
    low_nibble = ia4 & 0xF
    high_nibble = (ia4 >> 4) & 0xF
    
    r = g = b = low_nibble*0x11
    a = high_nibble*0x11
    
    return (r, g, b, a)
  
  @staticmethod
  def convert_ia8_to_color(ia8):
    low_byte = ia8 & 0xFF
    high_byte = (ia8 >> 8) & 0xFF
    
    r = g = b = low_byte
    a = high_byte
    
    return (r, g, b, a)
  
  @staticmethod
  def convert_color_to_ia8(color):
    r, g, b, a = color
    assert r == g == b
    ia8 = 0x0000
    ia8 |= (r & 0xFF)
    ia8 |= ((a & 0xFF) << 8)
    return ia8
  
  @staticmethod
  def convert_i4_to_color(i4):
    r = g = b = i4*0x11
    a = 255
    
    return (r, g, b, a)
  
  @staticmethod
  def convert_i8_to_color(i8):
    r = g = b = i8
    a = 255
    
    return (r, g, b, a)
  
  def read_palettes(self):
    if self.image_format not in self.IMAGE_FORMATS_THAT_USE_PALETTES:
      self.colors = None
      return
    
    self.colors = []
    offset = self.palette_data_offset + self.header_offset
    for i in range(self.num_colors):
      raw_color = read_u16(self.data, offset)
      if self.palette_format == 0:
        color = BTI.convert_ia8_to_color(raw_color)
      elif self.palette_format == 1:
        color = BTI.convert_rgb565_to_color(raw_color)
      elif self.palette_format == 2:
        color = BTI.convert_rgb5a3_to_color(raw_color)
      self.colors.append(color)
      offset += 2
  
  def generate_new_palettes_from_image(self, image):
    if self.image_format not in self.IMAGE_FORMATS_THAT_USE_PALETTES:
      self.colors = None
      return
    
    pixels = image.load()
    width, height = image.size
    new_colors = []
    for y in range(height):
      for x in range(width):
        color = pixels[x,y]
        if color not in new_colors:
          new_colors.append(color)
    
    if len(new_colors) > self.MAX_COLORS_FOR_IMAGE_FORMAT[self.image_format]:
      raise Exception(
        "Maximum number of colors supported by image format %d is %d, but replacement image has %d colors" % (
          self.image_format, self.MAX_COLORS_FOR_IMAGE_FORMAT[self.image_format], len(new_colors)
        )
      )
    
    self.colors = new_colors
    self.num_colors = len(self.colors)
  
  def save_palettes(self):
    if self.image_format not in self.IMAGE_FORMATS_THAT_USE_PALETTES:
      self.colors = None
      return
    
    if len(self.colors) > self.MAX_COLORS_FOR_IMAGE_FORMAT[self.image_format]:
      raise Exception(
        "Maximum number of colors supported by image format %d is %d, but replacement image has %d colors" % (
          self.image_format, self.MAX_COLORS_FOR_IMAGE_FORMAT[self.image_format], len(self.colors)
        )
      )
    
    offset = 0
    new_palette_data = BytesIO()
    for color in self.colors:
      if self.palette_format == 0:
        raw_color = BTI.convert_color_to_ia8(color)
      elif self.palette_format == 1:
        raw_color = BTI.convert_color_to_rgb565(color)
      elif self.palette_format == 2:
        raw_color = BTI.convert_color_to_rgb5a3(color)
      
      write_u16(new_palette_data, offset, raw_color)
      offset += 2
    
    if len(self.colors) < self.num_colors:
      # Pad out with dummy colors if there aren't enough.
      for i in range(self.num_colors - len(self.colors)):
        write_u16(new_palette_data, offset, 0xFFFF)
        offset += 2
    
    new_palette_data.seek(0)
    self.palette_data = new_palette_data.read()
  
  
  
  def render(self):
    self.read_palettes()
    
    image = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
    pixels = image.load()
    offset = self.image_data_offset + self.header_offset
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
      byte = read_u8(self.data, offset+byte_index)
      for nibble_index in range(2):
        i4 = (byte >> (1-nibble_index)*4) & 0xF
        color = BTI.convert_i4_to_color(i4)
        
        pixel_color_data.append(color)
    
    return pixel_color_data
  
  def render_i8_block(self, offset):
    pixel_color_data = []
    
    for i in range(self.block_data_size):
      i8 = read_u8(self.data, offset+i)
      color = BTI.convert_i8_to_color(i8)
      
      pixel_color_data.append(color)
    
    return pixel_color_data
  
  def render_ia4_block(self, offset):
    pixel_color_data = []
    
    for i in range(self.block_data_size):
      ia4 = read_u8(self.data, offset+i)
      color = BTI.convert_ia4_to_color(ia4)
      
      pixel_color_data.append(color)
    
    return pixel_color_data
  
  def render_ia8_block(self, offset):
    pixel_color_data = []
    
    for i in range(self.block_data_size//2):
      ia8 = read_u16(self.data, offset+i*2)
      color = BTI.convert_ia8_to_color(ia8)
      
      pixel_color_data.append(color)
    
    return pixel_color_data
  
  def render_rgb565_block(self, offset):
    pixel_color_data = []
    
    for i in range(self.block_data_size//2):
      rgb565 = read_u16(self.data, offset+i*2)
      color = BTI.convert_rgb565_to_color(rgb565)
      
      pixel_color_data.append(color)
    
    return pixel_color_data
  
  def render_rgb5a3_block(self, offset):
    pixel_color_data = []
    
    for i in range(self.block_data_size//2):
      rgb5a3 = read_u16(self.data, offset+i*2)
      color = BTI.convert_rgb5a3_to_color(rgb5a3)
      
      pixel_color_data.append(color)
    
    return pixel_color_data
  
  def render_rgba32_block(self, offset):
    pixel_color_data = []
    
    for i in range(16):
      a = read_u8(self.data, offset+(i*2))
      r = read_u8(self.data, offset+(i*2)+1)
      g = read_u8(self.data, offset+(i*2)+32)
      b = read_u8(self.data, offset+(i*2)+33)
      color = (r, g, b, a)
      
      pixel_color_data.append(color)
    
    return pixel_color_data
  
  def render_c4_block(self, offset):
    pixel_color_data = []
    
    for byte_index in range(self.block_data_size):
      byte = read_u8(self.data, offset+byte_index)
      for nibble_index in range(2):
        color_index = (byte >> (1-nibble_index)*4) & 0xF
        color = self.colors[color_index]
        
        pixel_color_data.append(color)
    
    return pixel_color_data
  
  def render_c8_block(self, offset):
    pixel_color_data = []
    
    for i in range(self.block_data_size):
      color_index = read_u8(self.data, offset+i)
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
      color_index = read_u16(self.data, offset+i*2) & 0x3FFF
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
      
      color_0_rgb565 = read_u16(self.data, subblock_offset)
      color_1_rgb565 = read_u16(self.data, subblock_offset+2)
      color_0 = BTI.convert_rgb565_to_color(color_0_rgb565)
      color_1 = BTI.convert_rgb565_to_color(color_1_rgb565)
      r0, g0, b0, _ = color_0
      r1, g1, b1, _ = color_1
      if color_0_rgb565 > color_1_rgb565:
        color_2 = (
          (2*r0 + 1*r1)//3,
          (2*g0 + 1*g1)//3,
          (2*b0 + 1*b1)//3,
          255
        )
        color_3 = (
          (1*r0 + 2*r1)//3,
          (1*g0 + 2*g1)//3,
          (1*b0 + 2*b1)//3,
          255
        )
      else:
        color_2 = (r0//2+r1//2, g0//2+g1//2, b0//2+b1//2, 255)
        color_3 = (0, 0, 0, 0)
      colors = [color_0, color_1, color_2, color_3]
      
      color_indexes = read_u32(self.data, subblock_offset+4)
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
    if self.image_format not in [5, 9]:
      raise Exception("Not implemented, cannot save image in format: %d" % self.image_format)
    
    image = Image.open(new_image_file_path)
    new_image_width, new_image_height = image.size
    self.width = new_image_width
    self.height = new_image_height
    
    self.generate_new_palettes_from_image(image)
    
    pixels = image.load()
    offset_in_image_data = 0
    block_x = 0
    block_y = 0
    new_image_data = BytesIO()
    while block_y < self.height:
      block_data = self.convert_image_to_block(pixels, block_x, block_y)
      
      write_bytes(new_image_data, offset_in_image_data, block_data)
      
      offset_in_image_data += self.block_data_size
      block_x += self.block_width
      if block_x >= self.width:
        block_x = 0
        block_y += self.block_height
    
    self.save_palettes()
    
    new_image_data.seek(0)
    self.image_data = new_image_data.read()
  
  def convert_image_to_block(self, pixels, block_x, block_y):
    if self.image_format == 5:
      return self.convert_image_to_rgb5a3_block(pixels, block_x, block_y)
    elif self.image_format == 9:
      return self.convert_image_to_c8_block(pixels, block_x, block_y)
    else:
      raise Exception("Unknown image format: %X" % self.image_format)
  
  def convert_image_to_rgb5a3_block(self, pixels, block_x, block_y):
    new_data = BytesIO()
    offset = 0
    for y in range(block_y, block_y+self.block_height):
      for x in range(block_x, block_x+self.block_width):
        color = pixels[x,y]
        rgb5a3 = BTI.convert_color_to_rgb5a3(color)
        write_u16(new_data, offset, rgb5a3)
        offset += 2
    
    new_data.seek(0)
    return new_data.read()
  
  def convert_image_to_c8_block(self, pixels, block_x, block_y):
    new_data = BytesIO()
    offset = 0
    for y in range(block_y, block_y+self.block_height):
      for x in range(block_x, block_x+self.block_width):
        if x >= self.width or y >= self.height:
          # This block bleeds past the edge of the image
          color_index = 0xFF
        else:
          color = pixels[x,y]
          color_index = self.colors.index(color)
        write_u8(new_data, offset, color_index)
        offset += 1
    
    new_data.seek(0)
    return new_data.read()

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
    self.data.write(self.image_data)
    
    if self.image_format in BTI.IMAGE_FORMATS_THAT_USE_PALETTES:
      self.palette_data_offset = 0x20 + len(self.image_data)
      self.data.write(self.palette_data)
    else:
      self.palette_data_offset = 0
    
    self.save_header_changes()
