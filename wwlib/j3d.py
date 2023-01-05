
from enum import Enum, IntEnum
from io import BytesIO
from collections import OrderedDict
from dataclasses import dataclass, field

from fs_helpers import *
from wwlib.bti import BTI
from wwlib.yaz0 import Yaz0
from wwlib.gx_enums import GXAttr, GXComponentCount, GXCompType

IMPLEMENTED_CHUNK_TYPES = [
  #"INF1",
  "VTX1",
  "TEX1",
  "MAT3",
  "MDL3",
  
  "TRK1",
  "TTK1",
]

class J3DFile:
  def __init__(self, data):
    if Yaz0.check_is_compressed(data):
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
    
    self.bck_sound_data_offset = read_u32(data, 0x1C)
    if self.file_type == "bck1" and self.bck_sound_data_offset != 0xFFFFFFFF:
      num_bck_sound_data_entries = read_u16(data, self.bck_sound_data_offset)
      bck_sound_data_length = 8 + num_bck_sound_data_entries*0x20
      self.bck_sound_data = read_bytes(data, self.bck_sound_data_offset, bck_sound_data_length)
    else:
      self.bck_sound_data = None
    
    self.chunks: list[J3DChunk] = []
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
    
    if self.bck_sound_data is not None:
      self.bck_sound_data_offset = data_len(data)
      write_bytes(data, self.bck_sound_data_offset, self.bck_sound_data)
      
      # Pad the size of the whole file to the next 0x20 bytes.
      align_data_to_nearest(data, 0x20, padding_bytes=b'\0')
    
    self.length = data_len(data)
    self.num_chunks = len(self.chunks)
    
    write_magic_str(data, 0, self.magic, 4)
    write_magic_str(data, 4, self.file_type, 4)
    write_u32(data, 8, self.length)
    write_u32(data, 0xC, self.num_chunks)
    write_u32(data, 0x1C, self.bck_sound_data_offset)

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
    assert self.file_type == "bmd3" or self.file_type == "bmd2"

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

class BTK(J3DFileEntry):
  def __init__(self, file_entry):
    super().__init__(file_entry)
    
    assert self.magic == "J3D1"
    assert self.file_type == "btk1"



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
    #padding = read_u16(self.data, string_table_offset+0x02)
    #assert padding == 0xFFFF
    
    strings = []
    offset = string_table_offset + 4
    for i in range(num_strings):
      #string_hash = read_u16(self.data, offset+0x00)
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

class INF1(J3DChunk):
  # TODO: this does not properly read the hierarchy. test on tetra player model for an error.
  def read_chunk_specific_data(self):
    self.hierarchy_data_offset = read_u32(self.data, 0x14)
    
    offset = self.hierarchy_data_offset
    self.flat_hierarchy = []
    self.hierarchy = []
    parent_node = None
    prev_node = None
    while True:
      if offset >= self.size:
        raise Exception("No INF1 end node found")
      
      node = INF1Node(self.data)
      node.read(offset)
      self.flat_hierarchy.append(node)
      offset += INF1Node.DATA_SIZE
      
      if node.type == INF1NodeType.FINISH:
        break
      elif node.type in [INF1NodeType.JOINT, INF1NodeType.MATERIAL, INF1NodeType.SHAPE]:
        node.parent = parent_node
        if parent_node:
          parent_node.children.append(node)
        else:
          self.hierarchy.append(node)
      elif node.type == INF1NodeType.OPEN_CHILD:
        parent_node = prev_node
      elif node.type == INF1NodeType.CLOSE_CHILD:
        parent_node = parent_node.parent
      
      prev_node = node
    
    #self.print_hierarchy_recursive(self.hierarchy)
  
  def print_hierarchy_recursive(self, nodes, indent=0):
    for node in nodes:
      print(("  "*indent) + "%s %X" % (node.type.name, node.index))
      self.print_hierarchy_recursive(node.children, indent=indent+1)
  
  def save_chunk_specific_data(self):
    pass

class INF1NodeType(Enum):
  FINISH      = 0x00
  OPEN_CHILD  = 0x01
  CLOSE_CHILD = 0x02
  JOINT       = 0x10
  MATERIAL    = 0x11
  SHAPE       = 0x12

class INF1Node:
  DATA_SIZE = 4
  
  def __init__(self, data):
    self.data = data
  
  def read(self, offset):
    self.type = INF1NodeType(read_u16(self.data, offset+0x00))
    self.index = read_u16(self.data, offset+0x02)
    
    self.parent = None
    self.children = []
  
  def save(self, offset):
    pass


class VTX1DataOffsetIndex(IntEnum):
  PositionData  = 0x0
  NormalData    = 0x1
  NBTData       = 0x2
  Color0Data    = 0x3
  Color1Data    = 0x4
  TexCoord0Data = 0x5
  TexCoord1Data = 0x6
  TexCoord2Data = 0x7
  TexCoord3Data = 0x8
  TexCoord4Data = 0x9
  TexCoord5Data = 0xA
  TexCoord6Data = 0xB
  TexCoord7Data = 0xC

GXAttr_TO_VTX1DataOffsetIndex = {
  GXAttr.Position: VTX1DataOffsetIndex.PositionData,
  GXAttr.Normal  : VTX1DataOffsetIndex.NormalData,
  GXAttr.Color0  : VTX1DataOffsetIndex.Color0Data,
  GXAttr.Color1  : VTX1DataOffsetIndex.Color1Data,
  GXAttr.Tex0    : VTX1DataOffsetIndex.TexCoord0Data,
  GXAttr.Tex1    : VTX1DataOffsetIndex.TexCoord1Data,
  GXAttr.Tex2    : VTX1DataOffsetIndex.TexCoord2Data,
  GXAttr.Tex3    : VTX1DataOffsetIndex.TexCoord3Data,
  GXAttr.Tex4    : VTX1DataOffsetIndex.TexCoord4Data,
  GXAttr.Tex5    : VTX1DataOffsetIndex.TexCoord5Data,
  GXAttr.Tex6    : VTX1DataOffsetIndex.TexCoord6Data,
  GXAttr.Tex7    : VTX1DataOffsetIndex.TexCoord7Data,
}

GXCompType_TO_COMPONENT_BYTE_SIZE = {
  GXCompType.Unsigned8 : 1,
  GXCompType.Signed8   : 1,
  GXCompType.Unsigned16: 2,
  GXCompType.Signed16  : 2,
  GXCompType.Float32   : 4,
}

@dataclass
class VertexFormat:
  DATA_SIZE = 0x10
  
  data: BytesIO = field(repr=False)
  attribute_type: GXAttr
  component_count_type: GXComponentCount
  component_type: GXCompType
  component_shift: int
  
  def __init__(self, data):
    self.data = data
  
  def read(self, offset):
    self.attribute_type = GXAttr(read_u32(self.data, offset))
    self.component_count_type = GXComponentCount(read_u32(self.data, offset+4))
    self.component_type = GXCompType(read_u32(self.data, offset+8))
    self.component_shift = read_u8(self.data, offset+0xC)
  
  def save(self, offset):
    write_u32(self.data, offset+0x0, self.attribute_type.value)
    write_u32(self.data, offset+0x4, self.component_count_type.value)
    write_u32(self.data, offset+0x8, self.component_type.value)
    write_u8(self.data, offset+0xC, self.component_shift)
    align_data_to_nearest(self.data, 0x10, b'\xff')
  
  @property
  def data_offset_index(self):
    return GXAttr_TO_VTX1DataOffsetIndex[self.attribute_type]
  
  @property
  def component_count(self):
    match self.attribute_type:
      case GXAttr.Position:
        match self.component_count_type:
          case GXComponentCount.Position_XY:
            return 2
          case GXComponentCount.Position_XYZ:
            return 3
      case GXAttr.Normal:
        match self.component_count_type:
          case GXComponentCount.Normal_XYZ:
            return 3
      case GXAttr.Tex0|GXAttr.Tex1|GXAttr.Tex2|GXAttr.Tex3|GXAttr.Tex4|GXAttr.Tex5|GXAttr.Tex6|GXAttr.Tex7:
        match self.component_count_type:
          case GXComponentCount.TexCoord_S:
            return 1
          case GXComponentCount.TexCoord_ST:
            return 2
    
    raise NotImplementedError

class VTX1(J3DChunk):
  def read_chunk_specific_data(self):
    self.vertex_formats_start_offset = read_u32(self.data, 0x08)
    
    self.vertex_data_offsets = []
    for i in range(13):
      vertex_data_offset = read_u32(self.data, 0x0C+i*4)
      self.vertex_data_offsets.append(vertex_data_offset)
    
    self.vertex_formats: list[VertexFormat] = []
    current_vertex_format_offset = self.vertex_formats_start_offset
    while True:
      vertex_format = VertexFormat(self.data)
      vertex_format.read(current_vertex_format_offset)
      current_vertex_format_offset += VertexFormat.DATA_SIZE
      self.vertex_formats.append(vertex_format)
      if vertex_format.attribute_type == GXAttr.NULL:
        break
    
    self.attributes: dict[GXAttr, list] = {}
    for vertex_format in self.vertex_formats:
      if vertex_format.attribute_type == GXAttr.NULL:
        break
      
      self.load_attribute_data(vertex_format)
  
  def get_attribute_data_count(self, offset_index, component_count, component_size):
    """Attempts to guess at the number of entries this VTX1 section has for a particular attribute."""
    
    entry_size = component_count * component_size
    
    data_start_offset = self.vertex_data_offsets[offset_index]
    
    data_end_offset_index = offset_index + 1
    data_end_offset = 0
    while data_end_offset == 0:
      if data_end_offset_index == len(self.vertex_data_offsets):
        data_end_offset = self.size
        break
      data_end_offset = self.vertex_data_offsets[data_end_offset_index]
      data_end_offset_index += 1
    
    data_size = (data_end_offset - data_start_offset)
    
    # Floor-divide to remove any bytes at the end that can't possibly be data and must be padding.
    data_count = data_size // entry_size
    
    if entry_size <= 0x10:
      # Attempt to remove more bytes that are very likely to be padding by checking if they match known padding strings.
      # If each entry in the list is half the padding size (0x20) or less, there's a possible problem that can occur.
      # We can't tell for sure if the data_count we currently have is accurate or if the padding at the end is giving
      # the illusion that there are more entries than there really are.
      # For example, if each entry is 0xC bytes, and the total data size is 0x40, we don't know if that means the number
      # of entries is 3, 4, or 5, as all of those would pad up to 0x40 bytes.
      # So we check all of the possible entry counts we're unsure of to see if the data from that point to the end
      # happens to match the padding bytes. If it does, it is extremely likely (though not 100% certain) to be padding.
      # In testing, this results in all VTX1 sections in vanilla Wind Waker repacking correctly (including padding).
      KNOWN_PADDING_BYTES = [b"This is padding data to alignme", b"Model made with SuperBMD by Gamma."]
      first_unsure_index = ((data_size-0x20) // entry_size) + 1
      for i in range(first_unsure_index, data_count):
        check_offset = data_start_offset + i*entry_size
        maybe_pad = read_bytes(self.data, check_offset, data_end_offset-check_offset)
        if maybe_pad is None:
          continue
        if any(padding_bytes.startswith(maybe_pad) for padding_bytes in KNOWN_PADDING_BYTES):
          data_size = (check_offset - data_start_offset)
          data_count = data_size // entry_size
          break
    
    return data_count
  
  def load_attribute_data(self, vertex_format: VertexFormat):
    self.attributes[vertex_format.attribute_type] = self.load_attribute_list(
      vertex_format.data_offset_index,
      vertex_format.component_count,
      vertex_format.component_type,
      vertex_format.component_shift,
    )
  
  def load_attribute_list(self, offset_index, component_count, component_type, comp_shift):
    data_offset = self.vertex_data_offsets[offset_index]
    component_size = GXCompType_TO_COMPONENT_BYTE_SIZE[component_type]
    attrib_count = self.get_attribute_data_count(offset_index, component_count, component_size)
    attr_data = []
    for i in range(0, attrib_count):
      components = self.read_components(component_count, component_type, comp_shift, data_offset)
      attr_data.append(components)
      data_offset += component_count * component_size
    return attr_data
  
  def read_components(self, component_count, component_type, component_shift, data_offset):
    divisor = (1 << component_shift)
    components = []
    for i in range(component_count):
      match component_type:
        case GXCompType.Signed16:
          components.append(read_s16(self.data, data_offset) / divisor)
        case GXCompType.Float32:
          components.append(read_float(self.data, data_offset) / divisor)
        case _:
          raise NotImplementedError
      data_offset += GXCompType_TO_COMPONENT_BYTE_SIZE[component_type]
    return tuple(components)
  
  def save_chunk_specific_data(self):
    # Cut off all the data, we're rewriting it entirely.
    self.data.truncate(0)
    
    # Placeholder for the header.
    self.data.seek(0)
    self.data.write(b"\0"*0x40)
    
    offset = self.data.tell()
    self.vertex_formats_start_offset = offset
    
    for vertex_format in self.vertex_formats:
      vertex_format.save(offset)
      offset += VertexFormat.DATA_SIZE
    align_data_to_nearest(self.data, 0x20)
    offset = self.data.tell()
    
    self.vertex_data_offsets = [0]*13
    
    for vertex_format in self.vertex_formats:
      if vertex_format.attribute_type == GXAttr.NULL:
        break
      
      offset = self.save_attribute_data(vertex_format, offset)
      align_data_to_nearest(self.data, 0x20)
      offset = data_len(self.data)
  
    # Write the header.
    write_magic_str(self.data, 0, "VTX1", 4)
    
    write_u32(self.data, 0x08, self.vertex_formats_start_offset)
    for i, vertex_data_offset in enumerate(self.vertex_data_offsets):
      write_u32(self.data, 0x0C+i*4, vertex_data_offset)
  
  def save_attribute_data(self, vertex_format: VertexFormat, data_offset):
    self.vertex_data_offsets[vertex_format.data_offset_index] = data_offset
    data_offset = self.save_attribute_list(
      self.attributes[vertex_format.attribute_type],
      vertex_format.component_count,
      vertex_format.component_type,
      vertex_format.component_shift,
      data_offset,
    )
    return data_offset
  
  def save_attribute_list(self, attr_data, component_count, component_type: GXCompType, component_shift, data_offset):
    for components in attr_data:
      assert len(components) == component_count
      data_offset = self.save_components(component_type, component_shift, components, data_offset)
    return data_offset
  
  def save_components(self, component_type: GXCompType, component_shift, components, data_offset):
    divisor = (1 << component_shift)
    for component in components:
      match component_type:
        case GXCompType.Signed16:
          write_s16(self.data, data_offset, round(component*divisor))
        case GXCompType.Float32:
          write_float(self.data, data_offset, component*divisor)
        case _:
          raise NotImplementedError
      data_offset += GXCompType_TO_COMPONENT_BYTE_SIZE[component_type]
    return data_offset

class TEX1(J3DChunk):
  def read_chunk_specific_data(self):
    self.textures: list[BTI] = []
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
    
    next_available_data_offset = 0x20 + self.num_textures*0x20 # Right after the last header ends
    self.data.truncate(next_available_data_offset)
    self.data.seek(next_available_data_offset)
    
    image_data_offsets = {}
    for i, texture in enumerate(self.textures):
      filename = self.texture_names[i]
      format_and_filename = "%X_%s" % (texture.image_format.value, filename)
      if format_and_filename in image_data_offsets:
        texture.image_data_offset = image_data_offsets[format_and_filename] - texture.header_offset
        continue
      
      self.data.seek(next_available_data_offset)
      
      texture.image_data_offset = next_available_data_offset - texture.header_offset
      image_data_offsets[format_and_filename] = next_available_data_offset
      texture.image_data.seek(0)
      self.data.write(texture.image_data.read())
      align_data_to_nearest(self.data, 0x20)
      next_available_data_offset = data_len(self.data)
    
    palette_data_offsets = {}
    for i, texture in enumerate(self.textures):
      filename = self.texture_names[i]
      format_and_filename = "%X_%s" % (texture.palette_format.value, filename)
      if format_and_filename in palette_data_offsets:
        texture.palette_data_offset = palette_data_offsets[format_and_filename] - texture.header_offset
        continue
      
      self.data.seek(next_available_data_offset)
      
      if texture.needs_palettes():
        texture.palette_data_offset = next_available_data_offset - texture.header_offset
        palette_data_offsets[format_and_filename] = next_available_data_offset
        texture.palette_data.seek(0)
        self.data.write(texture.palette_data.read())
        align_data_to_nearest(self.data, 0x20)
        next_available_data_offset = data_len(self.data)
      else:
        # If the image doesn't use palettes its palette offset is just the same as the first texture's image offset.
        first_texture = self.textures[0]
        texture.palette_data_offset = first_texture.image_data_offset + first_texture.header_offset - texture.header_offset
        palette_data_offsets[format_and_filename] = first_texture.image_data_offset + first_texture.header_offset
    
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
    
    self.string_table_offset = read_u32(self.data, 0x14)
    self.mat_names = self.read_string_table(self.string_table_offset)
  
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
    
    self.entries: list[MDLEntry] = []
    packet_offset = self.packets_offset
    for i in range(self.num_entries):
      entry_offset = read_u32(self.data, packet_offset + 0x00)
      entry_size = read_u32(self.data, packet_offset + 0x04)
      entry = MDLEntry(self.data, entry_offset+packet_offset, entry_size)
      self.entries.append(entry)
      packet_offset += 8
    
    self.string_table_offset = read_u32(self.data, 0x20)
    self.mat_names = self.read_string_table(self.string_table_offset)
  
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
    self.bp_commands: list[BPCommand] = []
    self.xf_commands: list[XFCommand] = []
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

class BPRegister(Enum):
  GEN_MODE = 0x00
  
  IND_MTXA0 = 0x06
  IND_MTXB0 = 0x07
  IND_MTXC0 = 0x08
  IND_MTXA1 = 0x09
  IND_MTXB1 = 0x0A
  IND_MTXC1 = 0x0B
  IND_MTXA2 = 0x0C
  IND_MTXB2 = 0x0D
  IND_MTXC2 = 0x0E
  IND_IMASK = 0x0F
  
  IND_CMD0 = 0x10
  IND_CMD1 = 0x11
  IND_CMD2 = 0x12
  IND_CMD3 = 0x13
  IND_CMD4 = 0x14
  IND_CMD5 = 0x15
  IND_CMD6 = 0x16
  IND_CMD7 = 0x17
  IND_CMD8 = 0x18
  IND_CMD9 = 0x19
  IND_CMDA = 0x1A
  IND_CMDB = 0x1B
  IND_CMDC = 0x1C
  IND_CMDD = 0x1D
  IND_CMDE = 0x1E
  IND_CMDF = 0x1F
  
  SCISSOR_0 = 0x20
  SCISSOR_1 = 0x21
  
  SU_LPSIZE = 0x22
  SU_COUNTER = 0x23
  RAS_COUNTER = 0x24
  
  RAS1_SS0 = 0x25
  RAS1_SS1 = 0x26
  RAS1_IREF = 0x27
  
  RAS1_TREF0 = 0x28
  RAS1_TREF1 = 0x29
  RAS1_TREF2 = 0x2A
  RAS1_TREF3 = 0x2B
  RAS1_TREF4 = 0x2C
  RAS1_TREF5 = 0x2D
  RAS1_TREF6 = 0x2E
  RAS1_TREF7 = 0x2F
  
  SU_SSIZE0 = 0x30
  SU_TSIZE0 = 0x31
  SU_SSIZE1 = 0x32
  SU_TSIZE1 = 0x33
  SU_SSIZE2 = 0x34
  SU_TSIZE2 = 0x35
  SU_SSIZE3 = 0x36
  SU_TSIZE3 = 0x37
  SU_SSIZE4 = 0x38
  SU_TSIZE4 = 0x39
  SU_SSIZE5 = 0x3A
  SU_TSIZE5 = 0x3B
  SU_SSIZE6 = 0x3C
  SU_TSIZE6 = 0x3D
  SU_SSIZE7 = 0x3E
  SU_TSIZE7 = 0x3F
  
  PE_ZMODE = 0x40
  PE_CMODE0 = 0x41
  PE_CMODE1 = 0x42
  PE_CONTROL = 0x43
  field_mask = 0x44
  PE_DONE = 0x45
  clock = 0x46
  PE_TOKEN = 0x47
  PE_TOKEN_INT = 0x48
  EFB_SOURCE_RECT_TOP_LEFT = 0x49
  EFB_SOURCE_RECT_WIDTH_HEIGHT = 0x4A
  XFB_TARGET_ADDRESS = 0x4B
  
  DISP_COPY_Y_SCALE = 0x4E
  PE_COPY_CLEAR_AR = 0x4F
  PE_COPY_CLEAR_GB = 0x50
  PE_COPY_CLEAR_Z = 0x51
  PE_COPY_EXECUTE = 0x52
  
  SCISSOR_BOX_OFFSET = 0x59
  
  TEX_LOADTLUT0 = 0x64
  TEX_LOADTLUT1 = 0x65
  
  TX_SET_MODE0_I0 = 0x80
  TX_SET_MODE0_I1 = 0x81
  TX_SET_MODE0_I2 = 0x82
  TX_SET_MODE0_I3 = 0x83
  TX_SET_MODE1_I0 = 0x84
  TX_SET_MODE1_I1 = 0x85
  TX_SET_MODE1_I2 = 0x86
  TX_SET_MODE1_I3 = 0x87
  
  TX_SETIMAGE0_I0 = 0x88
  TX_SETIMAGE0_I1 = 0x89
  TX_SETIMAGE0_I2 = 0x8A
  TX_SETIMAGE0_I3 = 0x8B
  TX_SETIMAGE1_I0 = 0x8C
  TX_SETIMAGE1_I1 = 0x8D
  TX_SETIMAGE1_I2 = 0x8E
  TX_SETIMAGE1_I3 = 0x8F
  TX_SETIMAGE2_I0 = 0x90
  TX_SETIMAGE2_I1 = 0x91
  TX_SETIMAGE2_I2 = 0x92
  TX_SETIMAGE2_I3 = 0x93
  TX_SETIMAGE3_I0 = 0x94
  TX_SETIMAGE3_I1 = 0x95
  TX_SETIMAGE3_I2 = 0x96
  TX_SETIMAGE3_I3 = 0x97
  
  TX_LOADTLUT0 = 0x98
  TX_LOADTLUT1 = 0x99
  TX_LOADTLUT2 = 0x9A
  TX_LOADTLUT3 = 0x9B
  
  TX_SET_MODE0_I4 = 0xA0
  TX_SET_MODE0_I5 = 0xA1
  TX_SET_MODE0_I6 = 0xA2
  TX_SET_MODE0_I7 = 0xA3
  TX_SET_MODE1_I4 = 0xA4
  TX_SET_MODE1_I5 = 0xA5
  TX_SET_MODE1_I6 = 0xA6
  TX_SET_MODE1_I7 = 0xA7
  
  TX_SETIMAGE0_I4 = 0xA8
  TX_SETIMAGE0_I5 = 0xA9
  TX_SETIMAGE0_I6 = 0xAA
  TX_SETIMAGE0_I7 = 0xAB
  TX_SETIMAGE1_I4 = 0xAC
  TX_SETIMAGE1_I5 = 0xAD
  TX_SETIMAGE1_I6 = 0xAE
  TX_SETIMAGE1_I7 = 0xAF
  TX_SETIMAGE2_I4 = 0xB0
  TX_SETIMAGE2_I5 = 0xB1
  TX_SETIMAGE2_I6 = 0xB2
  TX_SETIMAGE2_I7 = 0xB3
  TX_SETIMAGE3_I4 = 0xB4
  TX_SETIMAGE3_I5 = 0xB5
  TX_SETIMAGE3_I6 = 0xB6
  TX_SETIMAGE3_I7 = 0xB7
  
  TX_SETTLUT_I4 = 0xB8
  TX_SETTLUT_I5 = 0xB9
  TX_SETTLUT_I6 = 0xBA
  TX_SETTLUT_I7 = 0xBB
  
  TEV_COLOR_ENV_0 = 0xC0
  TEV_ALPHA_ENV_0 = 0xC1
  TEV_COLOR_ENV_1 = 0xC2
  TEV_ALPHA_ENV_1 = 0xC3
  TEV_COLOR_ENV_2 = 0xC4
  TEV_ALPHA_ENV_2 = 0xC5
  TEV_COLOR_ENV_3 = 0xC6
  TEV_ALPHA_ENV_3 = 0xC7
  TEV_COLOR_ENV_4 = 0xC8
  TEV_ALPHA_ENV_4 = 0xC9
  TEV_COLOR_ENV_5 = 0xCA
  TEV_ALPHA_ENV_5 = 0xCB
  TEV_COLOR_ENV_6 = 0xCC
  TEV_ALPHA_ENV_6 = 0xCD
  TEV_COLOR_ENV_7 = 0xCE
  TEV_ALPHA_ENV_7 = 0xCF
  TEV_COLOR_ENV_8 = 0xD0
  TEV_ALPHA_ENV_8 = 0xD1
  TEV_COLOR_ENV_9 = 0xD2
  TEV_ALPHA_ENV_9 = 0xD3
  TEV_COLOR_ENV_A = 0xD4
  TEV_ALPHA_ENV_A = 0xD5
  TEV_COLOR_ENV_B = 0xD6
  TEV_ALPHA_ENV_B = 0xD7
  TEV_COLOR_ENV_C = 0xD8
  TEV_ALPHA_ENV_C = 0xD9
  TEV_COLOR_ENV_D = 0xDA
  TEV_ALPHA_ENV_D = 0xDB
  TEV_COLOR_ENV_E = 0xDC
  TEV_ALPHA_ENV_E = 0xDD
  TEV_COLOR_ENV_F = 0xDE
  TEV_ALPHA_ENV_F = 0xDF
  
  TEV_REGISTERL_0 = 0xE0
  TEV_REGISTERH_0 = 0xE1
  TEV_REGISTERL_1 = 0xE2
  TEV_REGISTERH_1 = 0xE3
  TEV_REGISTERL_2 = 0xE4
  TEV_REGISTERH_2 = 0xE5
  TEV_REGISTERL_3 = 0xE6
  TEV_REGISTERH_3 = 0xE7
  
  FOG_RANGE = 0xE8
  FOG_RANGE_ADJ_0 = 0xE9
  FOG_RANGE_ADJ_1 = 0xEA
  FOG_RANGE_ADJ_2 = 0xEB
  FOG_RANGE_ADJ_3 = 0xEC
  FOG_RANGE_ADJ_4 = 0xED
  
  TEV_FOG_PARAM_0 = 0xEE
  TEV_FOG_PARAM_1 = 0xEF
  TEV_FOG_PARAM_2 = 0xF0
  TEV_FOG_PARAM_3 = 0xF1
  
  TEV_FOG_COLOR = 0xF2
  
  TEV_ALPHAFUNC = 0xF3
  TEV_Z_ENV_0 = 0xF4
  TEV_Z_ENV_1 = 0xF5
  
  TEV_KSEL_0 = 0xF6
  TEV_KSEL_1 = 0xF7
  TEV_KSEL_2 = 0xF8
  TEV_KSEL_3 = 0xF9
  TEV_KSEL_4 = 0xFA
  TEV_KSEL_5 = 0xFB
  TEV_KSEL_6 = 0xFC
  TEV_KSEL_7 = 0xFD
  
  BP_MASK = 0xFE

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

class XFRegister(Enum):
  TEXMTX0 = 0x0078
  TEXMTX1 = 0x0084
  TEXMTX2 = 0x0090
  TEXMTX3 = 0x009C
  TEXMTX4 = 0x00A8
  TEXMTX5 = 0x00B4
  TEXMTX6 = 0x00C0
  TEXMTX7 = 0x00CC
  TEXMTX8 = 0x00D8
  TEXMTX9 = 0x00E4
  
  # 0x600-0x67F are 8 lights. Each is 0x10 bytes, the first 3 bytes are unused.
  LIGHT0_COLOR = 0x0603
  LIGHT0_A0 = 0x0604 # Cosine attenuation
  LIGHT0_A1 = 0x0605
  LIGHT0_A2 = 0x0606
  LIGHT0_K0 = 0x0607 # Distance attenuation
  LIGHT0_K1 = 0x0608
  LIGHT0_K2 = 0x0609
  LIGHT0_LPX = 0x060A
  LIGHT0_LPY = 0x060B
  LIGHT0_LPZ = 0x060C
  LIGHT0_DHX = 0x060D
  LIGHT0_DHY = 0x060E
  LIGHT0_DHZ = 0x060F
  
  NUMCHAN = 0x1009
  CHAN0_AMBCOLOR = 0x100A
  CHAN0_MATCOLOR = 0x100C
  CHAN0_COLOR = 0x100E
  NUMTEXGENS = 0x103F
  TEXMTXINFO = 0x1040
  POSMTXINFO = 0x1050

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
    
    reg_animations: list[ColorAnimation] = []
    konst_animations: list[ColorAnimation] = []
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
    
    # Remap tables always written as identity, remapping not supported.
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

class TTK1(J3DChunk):
  def read_chunk_specific_data(self):
    assert read_str(self.data, 0, 4) == "TTK1"
    
    self.loop_mode = LoopMode(read_u8(self.data, 0x08))
    self.rotation_frac = read_u8(self.data, 0x09)
    self.duration = read_u16(self.data, 0x0A)
    
    keyframe_count = read_u16(self.data, 0x0C)
    anims_count = keyframe_count//3
    
    scale_table_count = read_u16(self.data, 0x0E)
    rotation_table_count = read_u16(self.data, 0x10)
    translation_table_count = read_u16(self.data, 0x12)
    
    anims_offset = read_u32(self.data, 0x14)
    
    remap_table_offset = read_u32(self.data, 0x18)
    
    mat_names_table_offset = read_u32(self.data, 0x1C)
    
    tex_gen_index_table_offset = read_u32(self.data, 0x20)
    center_coord_table_offset = read_u32(self.data, 0x24)
    scale_table_offset = read_u32(self.data, 0x28)
    rotation_table_offset = read_u32(self.data, 0x2C)
    translation_table_offset = read_u32(self.data, 0x30)
    
    self.post_matrix_data = read_bytes(self.data, 0x34, 0x28)
    
    if read_u32(self.data, 0x5C) == 1:
      self.matrix_mode = MatrixMode.MAYA_MODE
    else:
      self.matrix_mode = MatrixMode.BASIC_MODE
    
    # Ensure the remap tables are identity.
    # Actual remapping not currently supported by this implementation.
    for i in range(anims_count):
      assert i == read_u16(self.data, remap_table_offset+i*2)
    
    mat_names = self.read_string_table(mat_names_table_offset)
    
    tex_gen_indexes = []
    for i in range(anims_count):
      tex_gen_index = read_u8(self.data, tex_gen_index_table_offset+i)
      tex_gen_indexes.append(tex_gen_index)
    center_coords_data = []
    for i in range(anims_count):
      center_s = read_float(self.data, center_coord_table_offset+i*0xC+0)
      center_t = read_float(self.data, center_coord_table_offset+i*0xC+4)
      center_q = read_float(self.data, center_coord_table_offset+i*0xC+8)
      center_coords_data.append((center_s, center_t, center_q))
    scale_track_data = []
    for i in range(scale_table_count):
      scale = read_float(self.data, scale_table_offset+i*4)
      scale_track_data.append(scale)
    rotation_track_data = []
    for i in range(rotation_table_count):
      rotation = read_s16(self.data, rotation_table_offset+i*2)
      rotation_track_data.append(rotation)
    translation_track_data = []
    for i in range(translation_table_count):
      translation = read_float(self.data, translation_table_offset+i*4)
      translation_track_data.append(translation)
    
    animations = []
    self.mat_name_to_anims = OrderedDict()
    
    offset = anims_offset
    for i in range(anims_count):
      anim = UVAnimation()
      anim.read(self.data, offset, tex_gen_indexes, center_coords_data, scale_track_data, rotation_track_data, translation_track_data)
      offset += UVAnimation.DATA_SIZE
      
      animations.append(anim)
      
      mat_name = mat_names[i]
      if mat_name not in self.mat_name_to_anims:
        self.mat_name_to_anims[mat_name] = []
      self.mat_name_to_anims[mat_name].append(anim)
  
  def save_chunk_specific_data(self):
    # Cut off all the data, we're rewriting it entirely.
    self.data.truncate(0)
    
    # Placeholder for the header.
    self.data.seek(0)
    self.data.write(b"\0"*0x60)
    
    align_data_to_nearest(self.data, 0x20)
    offset = self.data.tell()
    
    animations: list[UVAnimation] = []
    mat_names = []
    for mat_name, anims in self.mat_name_to_anims.items():
      for anim in anims:
        animations.append(anim)
        mat_names.append(mat_name)
    
    tex_gen_indexes = []
    center_coords_data = []
    scale_track_data = []
    rotation_track_data = []
    translation_track_data = []
    anims_offset = offset
    if not animations:
      anims_offset = 0
    for anim in animations:
      anim.save_changes(self.data, offset, tex_gen_indexes, center_coords_data, scale_track_data, rotation_track_data, translation_track_data)
      offset += UVAnimation.DATA_SIZE
    
    align_data_to_nearest(self.data, 4)
    offset = self.data.tell()
    
    # Remap tables always written as identity, remapping not supported.
    remap_table_offset = offset
    if not animations:
      remap_table_offset = 0
    for i in range(len(animations)):
      write_u16(self.data, offset, i)
      offset += 2
    
    align_data_to_nearest(self.data, 4)
    offset = self.data.tell()
    
    mat_names_table_offset = offset
    self.write_string_table(mat_names_table_offset, mat_names)
    
    align_data_to_nearest(self.data, 4)
    offset = self.data.tell()
    tex_gen_index_table_offset = offset
    if not tex_gen_indexes:
      tex_gen_index_table_offset = 0
    for tex_gen_index in tex_gen_indexes:
      write_u8(self.data, offset, tex_gen_index)
      offset += 1
    
    align_data_to_nearest(self.data, 4)
    offset = self.data.tell()
    center_coord_table_offset = offset
    if not center_coords_data:
      center_coord_table_offset = 0
    for center_coords in center_coords_data:
      write_float(self.data, offset+0, center_coords[0])
      write_float(self.data, offset+4, center_coords[1])
      write_float(self.data, offset+8, center_coords[2])
      offset += 0xC
    
    align_data_to_nearest(self.data, 4)
    offset = self.data.tell()
    scale_table_offset = offset
    if not scale_track_data:
      scale_table_offset = 0
    for scale in scale_track_data:
      write_float(self.data, offset, scale)
      offset += 4
    
    align_data_to_nearest(self.data, 4)
    offset = self.data.tell()
    rotation_table_offset = offset
    if not rotation_track_data:
      rotation_table_offset = 0
    for rotation in rotation_track_data:
      write_s16(self.data, offset, rotation)
      offset += 2
    
    align_data_to_nearest(self.data, 4)
    offset = self.data.tell()
    translation_table_offset = offset
    if not translation_track_data:
      translation_table_offset = 0
    for translation in translation_track_data:
      write_float(self.data, offset, translation)
      offset += 4
    
    
    # Write the header.
    write_magic_str(self.data, 0, "TTK1", 4)
    
    write_u8(self.data, 0x08, self.loop_mode.value)
    write_u8(self.data, 0x09, self.rotation_frac)
    write_u16(self.data, 0x0A, self.duration)
    
    write_u16(self.data, 0x0C, len(animations)*3)
    
    write_s16(self.data, 0x0E, len(scale_track_data))
    write_s16(self.data, 0x10, len(rotation_track_data))
    write_s16(self.data, 0x12, len(translation_track_data))
    
    write_u32(self.data, 0x14, anims_offset)
    
    write_u32(self.data, 0x18, remap_table_offset)
    
    write_u32(self.data, 0x1C, mat_names_table_offset)
    
    write_u32(self.data, 0x20, tex_gen_index_table_offset)
    write_u32(self.data, 0x24, center_coord_table_offset)
    write_u32(self.data, 0x28, scale_table_offset)
    write_u32(self.data, 0x2C, rotation_table_offset)
    write_u32(self.data, 0x30, translation_table_offset)
    
    assert len(self.post_matrix_data) == 0x28
    write_bytes(self.data, 0x34, self.post_matrix_data)
  
class LoopMode(Enum):
  ONCE = 0
  ONCE_AND_RESET = 1
  REPEAT = 2
  MIRRORED_ONCE = 3
  MIRRORED_REPEAT = 4

class MatrixMode(Enum):
  BASIC_MODE = 0
  MAYA_MODE = 1

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
    
    self.index = None
    # Try to find if this track's data is already in the full track list to avoid duplicating data.
    # Note: This deduplication is not entirely accurate to how the vanilla files deduplicated data.
    # Vanilla files did deduplicate data somewhat, but not all of it, resulting in repacked files being smaller than vanilla.
    # It's not currently known exactly how Nintendo's tools determined which data should be deduplicated.
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

class Animation:
  def __init__(self):
    self.tracks = OrderedDict()
  
  def read_track(self, track_name, data, offset, track_data):
    self.tracks[track_name] = AnimationTrack()
    self.tracks[track_name].read(data, offset, track_data)
    offset += AnimationTrack.DATA_SIZE
    return offset
  
  def save_track(self, track_name, data, offset, track_data):
    self.tracks[track_name].save_changes(data, offset, track_data)
    offset += AnimationTrack.DATA_SIZE
    return offset
  
  def __getattr__(self, attr_name):
    if attr_name != "tracks" and attr_name in self.tracks:
      return self.tracks[attr_name]
    else:
      return super(self.__class__, self).__getattribute__(attr_name)

class UVAnimation(Animation):
  DATA_SIZE = 3*3*AnimationTrack.DATA_SIZE
  
  def read(self, data, offset, tex_gen_indexes, center_coords_data, scale_track_data, rotation_track_data, translation_track_data):
    self.tex_gen_index = tex_gen_indexes.pop(0)
    self.center_coords = center_coords_data.pop(0)
    
    offset = self.read_track("scale_s",       data, offset, scale_track_data)
    offset = self.read_track("rotation_s",    data, offset, rotation_track_data)
    offset = self.read_track("translation_s", data, offset, translation_track_data)
    offset = self.read_track("scale_t",       data, offset, scale_track_data)
    offset = self.read_track("rotation_t",    data, offset, rotation_track_data)
    offset = self.read_track("translation_t", data, offset, translation_track_data)
    offset = self.read_track("scale_q",       data, offset, scale_track_data)
    offset = self.read_track("rotation_q",    data, offset, rotation_track_data)
    offset = self.read_track("translation_q", data, offset, translation_track_data)
  
  def save_changes(self, data, offset, tex_gen_indexes, center_coords_data, scale_track_data, rotation_track_data, translation_track_data):
    tex_gen_indexes.append(self.tex_gen_index)
    center_coords_data.append(self.center_coords)
    
    offset = self.save_track("scale_s",       data, offset, scale_track_data)
    offset = self.save_track("rotation_s",    data, offset, rotation_track_data)
    offset = self.save_track("translation_s", data, offset, translation_track_data)
    offset = self.save_track("scale_t",       data, offset, scale_track_data)
    offset = self.save_track("rotation_t",    data, offset, rotation_track_data)
    offset = self.save_track("translation_t", data, offset, translation_track_data)
    offset = self.save_track("scale_q",       data, offset, scale_track_data)
    offset = self.save_track("rotation_q",    data, offset, rotation_track_data)
    offset = self.save_track("translation_q", data, offset, translation_track_data)

class ColorAnimation(Animation):
  DATA_SIZE = 4*AnimationTrack.DATA_SIZE + 4
  
  def read(self, data, offset, r_track_data, g_track_data, b_track_data, a_track_data):
    offset = self.read_track("r", data, offset, r_track_data)
    offset = self.read_track("g", data, offset, g_track_data)
    offset = self.read_track("b", data, offset, b_track_data)
    offset = self.read_track("a", data, offset, a_track_data)
    
    self.color_id = read_u8(data, offset)
    offset += 4
  
  def save_changes(self, data, offset, r_track_data, g_track_data, b_track_data, a_track_data):
    offset = self.save_track("r", data, offset, r_track_data)
    offset = self.save_track("g", data, offset, g_track_data)
    offset = self.save_track("b", data, offset, b_track_data)
    offset = self.save_track("a", data, offset, a_track_data)
    
    write_u8(data, offset, self.color_id)
    write_u8(data, offset+1, 0xFF)
    write_u8(data, offset+2, 0xFF)
    write_u8(data, offset+3, 0xFF)
    offset += 4
