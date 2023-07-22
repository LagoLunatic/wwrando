from dataclasses import dataclass
from enum import Enum
from collections import defaultdict
from PIL import Image
import struct

from fs_helpers import *
from gclib.j3d import J3DChunk
from gclib.texture_utils import ImageFormat, IMAGE_FORMATS_THAT_USE_PALETTES, decode_image

class BFN:
  IMPLEMENTED_CHUNK_TYPES = [
    "INF1",
    "GLY1",
    "MAP1",
    "WID1",
  ]
  
  def __init__(self, data):
    self.data = data
    
    self.inf1s: list[INF1] = []
    self.gly1s: list[GLY1] = []
    self.map1s: list[MAP1] = []
    self.wid1s: list[WID1] = []
  
  def read(self):
    self.magic = read_str(self.data, 0, 4)
    assert self.magic == "FONT"
    self.format_version = read_str(self.data, 4, 4)
    assert self.format_version == "bfn1"
    self.length = read_u32(self.data, 8)
    self.num_chunks = read_u32(self.data, 0x0C)
    
    self.chunks = []
    self.chunks_by_type = defaultdict(list)
    offset = 0x20
    for chunk_index in range(self.num_chunks):
      chunk_magic = read_str(self.data, offset, 4)
      if chunk_magic in BFN.IMPLEMENTED_CHUNK_TYPES:
        chunk_class = globals().get(chunk_magic, None)
      else:
        chunk_class = J3DChunk
      chunk = chunk_class()
      chunk.read(self.data, offset)
      self.chunks.append(chunk)
      self.chunks_by_type[chunk.magic].append(chunk)
      
      if chunk.magic in BFN.IMPLEMENTED_CHUNK_TYPES:
        getattr(self, chunk.magic.lower() + "s").append(chunk)
      
      offset += chunk.size
  
  def encode_char_to_ordinal(self, char: str):
    match self.inf1s[0].encoding_type:
      case EncodingType.SINGLE_BYTE:
        return char.encode("cp1252")[0]
      case EncodingType.TWO_BYTE:
        raise NotImplementedError
      case EncodingType.SHIFT_JIS:
        encoded_char = char.encode("shift_jis")
        # Shift JIS characters can be either one or two bytes.
        if len(encoded_char) == 1:
          return encoded_char[0]
        else:
          return struct.unpack(">H", encoded_char)[0]
      case _:
        raise NotImplementedError
  
  def get_char_code(self, char: str):
    char_code = None
    try:
      char_ord = self.encode_char_to_ordinal(char)
      for map1 in self.map1s:
        if char_ord in map1.char_ord_to_code:
          char_code = map1.char_ord_to_code[char_ord]
          break
    except UnicodeEncodeError:
      print(f"Could not encode character: {repr(char)}")
    if char_code is None:
      print(f"Defaulting to the replacement code for character: {repr(char)}")
      char_code = self.inf1s[0].replacement_code
    return char_code
  
  def get_char_width(self, char: str):
    char_code = self.get_char_code(char)
    width_info = self.wid1s[0].code_to_width_info[char_code]
    return width_info.width

  def word_wrap_string(self, string: str, max_line_length: int) -> str:
    index_in_str = 0
    wordwrapped_str = ""
    current_word = ""
    current_word_length = 0
    length_of_curr_line = 0
    while index_in_str < len(string):
      char = string[index_in_str]
      
      if char == "\\":
        assert string[index_in_str+1] == "{"
        substr = string[index_in_str:]
        control_code_str_len = substr.index("}") + 1
        substr = substr[:control_code_str_len]
        current_word += substr
        index_in_str += control_code_str_len
      elif char == "\n":
        wordwrapped_str += current_word
        wordwrapped_str = wordwrapped_str.rstrip(" ")
        wordwrapped_str += char
        length_of_curr_line = 0
        current_word = ""
        current_word_length = 0
        index_in_str += 1
      elif char == " ":
        wordwrapped_str += current_word
        length_of_curr_line += current_word_length
        current_word = ""
        current_word_length = 0
        index_in_str += 1
        
        if length_of_curr_line + self.get_char_width(char) >= max_line_length:
          wordwrapped_str += "\n"
          length_of_curr_line = 0
        else:
          wordwrapped_str += char
          length_of_curr_line += self.get_char_width(char)
      else:
        current_word += char
        current_word_length += self.get_char_width(char)
        index_in_str += 1
        
        if length_of_curr_line + current_word_length > max_line_length:
          wordwrapped_str = wordwrapped_str.rstrip(" ")
          if wordwrapped_str and wordwrapped_str[-1] != "\n":
            wordwrapped_str += "\n"
          length_of_curr_line = 0
          
          if current_word_length >= max_line_length:
            wordwrapped_str += current_word + "\n"
            current_word = ""
            current_word_length = 0
    
    wordwrapped_str += current_word
    
    return wordwrapped_str
  
  def render_string(self, string, max_line_length: int):
    string = self.word_wrap_string(string, max_line_length)
    lines = string.split("\n")
    
    gly1: GLY1 = self.gly1s[0]
    gly1.render_sheets()
    
    image = Image.new("RGBA", (640, 480))
    y = 0
    for line in lines:
      cursor_x = 0
      for char in line:
        code = self.get_char_code(char)
        if code < gly1.first_code or code > gly1.last_code:
          raise Exception(f"Unknown character code: {repr(char)} (0x{code:04X})")
        index = code - gly1.first_code
        
        width_info = self.wid1s[0].code_to_width_info[code]
        
        sheet_index, index_on_sheet = divmod(index, gly1.cells_per_sheet)
        y_on_sheet, x_on_sheet = divmod(index_on_sheet, gly1.cols_per_sheet)
        
        sheet_image = gly1.sheet_images[sheet_index]
        x = cursor_x
        x_on_sheet *= gly1.cell_width
        y_on_sheet *= gly1.cell_height
        x -= width_info.kerning
        image.alpha_composite(
          sheet_image,
          (x, y),
          (x_on_sheet, y_on_sheet, x_on_sheet+gly1.cell_width, y_on_sheet+gly1.cell_height)
        )
        
        cursor_x += width_info.width
      
      # Using the INF1's leading doesn't seem to give the exact same result as ingame.
      # The lines are farther apart ingame.
      y += self.inf1s[0].leading
      # Using ascent + descent gives the same result as leading.
      #y += self.inf1s[0].ascent + self.inf1s[0].descent
    
    return image

class EncodingType(Enum):
  SINGLE_BYTE = 0 # CP-1252
  TWO_BYTE = 1
  SHIFT_JIS = 2 # Characters can be either one byte or two bytes

@dataclass
class INF1(J3DChunk):
  encoding_type: EncodingType = None
  ascent: int = None
  descent: int = None
  char_width: int = None
  leading: int = None
  replacement_code: int = None
  
  def read_chunk_specific_data(self):
    self.encoding_type = EncodingType(read_u16(self.data, 0x08))
    self.ascent = read_u16(self.data, 0x0A)
    self.descent = read_u16(self.data, 0x0C)
    self.char_width = read_u16(self.data, 0x0E)
    self.leading = read_u16(self.data, 0x10) # Line height (seems to be ascent + descent)
    self.replacement_code = read_u16(self.data, 0x12)

class BFNMappingType(Enum):
  LINEAR_MAPPED = 0
  SJIS_MAPPED   = 1
  TABLE_MAPPED  = 2
  MAP_MAPPED    = 3

@dataclass
class GLY1(J3DChunk):
  first_code: int = None
  last_code: int = None
  cell_width: int = None
  cell_height: int = None
  sheet_byte_size: int = None
  image_format: ImageFormat = None
  rows_per_sheet: int = None
  cols_per_sheet: int = None
  sheet_width: int = None
  sheet_height: int = None
  sheet_images: list[Image.Image] = None
  
  def read_chunk_specific_data(self):
    self.first_code = read_u16(self.data, 0x08)
    self.last_code = read_u16(self.data, 0x0A)
    self.cell_width = read_u16(self.data, 0x0C)
    self.cell_height = read_u16(self.data, 0x0E)
    self.sheet_byte_size = read_u32(self.data, 0x10)
    self.image_format = ImageFormat(read_u16(self.data, 0x14))
    self.rows_per_sheet = read_u16(self.data, 0x16)
    self.cols_per_sheet = read_u16(self.data, 0x18)
    self.sheet_width = read_u16(self.data, 0x1A)
    self.sheet_height = read_u16(self.data, 0x1C)
    
    assert self.image_format not in IMAGE_FORMATS_THAT_USE_PALETTES
  
  @property
  def cells_per_sheet(self):
    return (self.rows_per_sheet * self.cols_per_sheet)
  
  def render_sheets(self):
    if self.sheet_images:
      return
    
    sheet_count = ((self.last_code - self.first_code) // (self.rows_per_sheet * self.cols_per_sheet)) + 1
    assert(self.size == 0x20 + sheet_count*self.sheet_byte_size)
    
    self.sheet_images = []
    offset = 0x20
    for i in range(sheet_count):
      image_data = BytesIO(read_bytes(self.data, offset, self.sheet_byte_size))
      sheet_image = decode_image(
        image_data, BytesIO(),
        self.image_format, None, None,
        self.sheet_width, self.sheet_height
      )
      self.sheet_images.append(sheet_image)
      offset += self.sheet_byte_size

@dataclass
class MAP1(J3DChunk):
  mapping_type: BFNMappingType = None
  first_character: int = None
  last_character: int = None
  entry_count: int = None
  
  def read_chunk_specific_data(self):
    self.mapping_type = BFNMappingType(read_u16(self.data, 0x08))
    self.first_character = read_u16(self.data, 0x0A)
    self.last_character = read_u16(self.data, 0x0C)
    self.entry_count = read_u16(self.data, 0x0E)
    
    self.read_char_code_mapping()
  
  def read_char_code_mapping(self):
    self.char_ord_to_code = {}
    self.code_to_char_ord = {}
    match self.mapping_type:
      case BFNMappingType.LINEAR_MAPPED:
        assert self.entry_count == 0
        for char_ord in range(self.first_character, self.last_character+1):
          code = char_ord-self.first_character
          self.char_ord_to_code[char_ord] = code
          self.code_to_char_ord[code] = char_ord
      case BFNMappingType.SJIS_MAPPED:
        assert self.entry_count == 0
        base_code = 796
        for char_ord in range(self.first_character, self.last_character+1):
          lead_byte = (char_ord & 0xFF00) >> 8
          trail_byte = (char_ord & 0x00FF) >> 0
          index = trail_byte - 64
          if index >= 64:
            index -= 1
          code = base_code + index + ((lead_byte - 136) * 188 - 94)
          self.char_ord_to_code[char_ord] = code
          self.code_to_char_ord[code] = char_ord
      case BFNMappingType.TABLE_MAPPED:
        assert self.entry_count == (self.last_character - self.first_character)+1
        table_offset = 0x10
        for index in range(self.entry_count):
          char_ord = self.first_character + index
          code = read_u16(self.data, table_offset+index*2)
          self.char_ord_to_code[char_ord] = code
          self.code_to_char_ord[code] = char_ord
      case BFNMappingType.MAP_MAPPED:
        table_offset = 0x10
        for index in range(self.entry_count):
          char_ord = read_u16(self.data, table_offset+index*4+0)
          code = read_u16(self.data, table_offset+index*4+2)
          self.char_ord_to_code[char_ord] = code
          self.code_to_char_ord[code] = char_ord
      case _:
        raise NotImplementedError

@dataclass
class CodeWidthInfo:
  DATA_SIZE = 2
  
  kerning: int
  width: int
  
  def __init__(self, data):
    self.data = data
  
  def read(self, offset):
    self.kerning = read_u8(self.data, offset+0)
    self.width = read_u8(self.data, offset+1)

@dataclass
class WID1(J3DChunk):
  first_code: int = None
  last_code: int = None
  code_to_width_info: dict[int, CodeWidthInfo] = None
  
  def read_chunk_specific_data(self):
    self.first_code = read_u16(self.data, 0x08)
    self.last_code = read_u16(self.data, 0x0A)
    
    self.code_to_width_info = {}
    offset = 0x0C
    for i in range(self.last_code-self.first_code):
      width_info = CodeWidthInfo(self.data)
      width_info.read(offset)
      self.code_to_width_info[self.first_code+i] = width_info
      offset += CodeWidthInfo.DATA_SIZE
