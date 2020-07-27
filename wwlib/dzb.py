
from io import BytesIO

from fs_helpers import *

class DZB:
  def __init__(self):
    self.data = BytesIO()
    
    self.num_vertices = 0
    self.vertex_list_offset = None
    
    self.num_faces = 0
    self.face_list_offset = None
    
    self.num_octree_blocks = 0
    self.octree_block_list_offset = None
    self.num_octree_nodes = 0
    self.octree_node_list_offset = None
    
    self.num_groups = 0
    self.group_list_offset = None
    
    self.num_properties = 0
    self.property_list_offset = None
    
    self.unknown_1 = 0
    
    self.vertices = []
    self.faces = []
    self.octree_blocks = []
    self.octree_nodes = []
    self.groups = []
    self.properties = []
  
  def read(self, data):
    self.data = data
    
    self.num_vertices = read_u32(data, 0x00)
    self.vertex_list_offset = read_u32(data, 0x04)
    
    self.num_faces = read_u32(data, 0x08)
    self.face_list_offset = read_u32(data, 0x0C)
    
    self.num_octree_blocks = read_u32(data, 0x10)
    self.octree_block_list_offset = read_u32(data, 0x14)
    self.num_octree_nodes = read_u32(data, 0x18)
    self.octree_node_list_offset = read_u32(data, 0x1C)
    
    self.num_groups = read_u32(data, 0x20)
    self.group_list_offset = read_u32(data, 0x24)
    
    self.num_properties = read_u32(data, 0x28)
    self.property_list_offset = read_u32(data, 0x2C)
    
    self.unknown_1 = read_u32(data, 0x30)
    
    self.vertices = []
    offset = self.vertex_list_offset
    for vertex_index in range(0, self.num_vertices):
      vertex = Vertex(data)
      vertex.read(offset)
      self.vertices.append(vertex)
      offset += Vertex.DATA_SIZE
    
    self.faces = []
    offset = self.face_list_offset
    for face_index in range(0, self.num_faces):
      face = Face(data)
      face.read(offset)
      self.faces.append(face)
      offset += Face.DATA_SIZE
    
    self.octree_blocks = []
    offset = self.octree_block_list_offset
    for block_index in range(0, self.num_octree_blocks):
      block = OctreeBlock(self.data)
      block.read(offset)
      self.octree_blocks.append(block)
      offset += OctreeBlock.DATA_SIZE
    
    self.octree_nodes = []
    offset = self.octree_node_list_offset
    for node_index in range(0, self.num_octree_nodes):
      node = OctreeNode(self.data)
      node.read(offset)
      self.octree_nodes.append(node)
      offset += OctreeNode.DATA_SIZE
    
    self.groups = []
    offset = self.group_list_offset
    for group_index in range(0, self.num_groups):
      group = Group(data)
      group.read(offset)
      self.groups.append(group)
      offset += Group.DATA_SIZE
    
    self.properties = []
    offset = self.property_list_offset
    for property_index in range(0, self.num_properties):
      property = Property(data)
      property.read(offset)
      self.properties.append(property)
      offset += Property.DATA_SIZE
    
    # Populate each face's extra attributes.
    for face in self.faces:
      face.vertices.append(self.vertices[face.vertex_1_index])
      face.vertices.append(self.vertices[face.vertex_2_index])
      face.vertices.append(self.vertices[face.vertex_3_index])
      face.property = self.properties[face.property_index]
      face.group = self.groups[face.group_index]
    
    # Populate each octree block's faces.
    for block_index, block in enumerate(self.octree_blocks):
      if block_index == len(self.octree_blocks)-1:
        next_block_first_face_index = len(self.faces)
      else:
        next_block = self.octree_blocks[block_index+1]
        next_block_first_face_index = next_block.first_face_index
      
      for face_index in range(block.first_face_index, next_block_first_face_index):
        face = self.faces[face_index]
        block.faces.append(face)
    
    # Populate each octree node's children.
    for node in self.octree_nodes:
      if node.is_leaf:
        node.block = self.octree_blocks[node.child_indexes[0]]
      else:
        for child_index in node.child_indexes:
          if child_index == -1:
            child_node = None
          else:
            child_node = self.octree_nodes[child_index]
          node.child_nodes.append(child_node)
    
    # Populate each group's relationships.
    for group in self.groups:
      if group.parent_group_index != -1:
        self.parent_group = self.groups[group.parent_group_index]
    for group in self.groups:
      self.children = [g for g in self.groups if g.parent_group == group]
  
  def save_changes(self):
    self.data.truncate(0)
    data = self.data
    write_bytes(data, 0x00, b'\0'*0x34) # Header placeholder
    
    self.regenerate_octree()
    
    self.vertex_list_offset = data.tell()
    offset = self.vertex_list_offset
    for vertex in self.vertices:
      vertex.offset = offset
      vertex.save_changes()
      offset += Vertex.DATA_SIZE
      
    self.face_list_offset = data.tell()
    offset = self.face_list_offset
    for face in self.faces:
      face.offset = offset
      face.vertex_1_index = self.vertices.index(face.vertices[0])
      face.vertex_2_index = self.vertices.index(face.vertices[1])
      face.vertex_3_index = self.vertices.index(face.vertices[2])
      face.property_index = self.properties.index(face.property)
      face.group_index    = self.groups.index(face.group)
      
      face.save_changes()
      offset += Face.DATA_SIZE
    
    self.octree_node_list_offset = data.tell()
    offset = self.octree_node_list_offset
    for node in self.octree_nodes:
      node.child_indexes = []
      if node.is_leaf:
        child_index = self.octree_blocks.index(node.block)
        node.child_indexes = [child_index] + [-1]*7
      else:
        for child_node in node.child_nodes:
          if child_node is None:
            child_index = -1
          else:
            child_index = self.octree_nodes.index(child_node)
          node.child_indexes.append(child_index)
      
      node.offset = offset
      node.save_changes()
      offset += OctreeNode.DATA_SIZE
    
    align_data_to_nearest(data, 4, padding_bytes=b'\xFF')
    self.property_list_offset = data.tell()
    offset = self.property_list_offset
    for property in self.properties:
      property.offset = offset
      property.save_changes()
      offset += Property.DATA_SIZE
    
    self.octree_block_list_offset = data.tell()
    offset = self.octree_block_list_offset
    for block in self.octree_blocks:
      block.first_face_index = self.faces.index(block.faces[0])
      
      block.offset = offset
      block.save_changes()
      offset += OctreeBlock.DATA_SIZE
    
    # Assign the group offsets to each group, but don't actually save them yet.
    align_data_to_nearest(data, 4, padding_bytes=b'\xFF')
    self.group_list_offset = data.tell()
    offset = self.group_list_offset
    for group in self.groups:
      group.parent_group_index = -1
      group.next_sibling_group_index = -1
      group.first_child_group_index = -1
      if group.parent_group:
        group.parent_group_index = self.groups.index(group.parent_group)
        siblings = group.parent_group.children
        index_among_siblings_siblings = siblings.index(group)
        if index_among_siblings_siblings+1 < len(siblings):
          next_sibling = siblings[index_among_siblings_siblings+1]
          group.next_sibling_group_index = self.groups.index(next_sibling)
      if group.children:
        group.first_child_group_index = self.groups.index(group.children[0])
      
      group.offset = offset
      offset += Group.DATA_SIZE
    
    # Then write the group names, and save the groups.
    for group in self.groups:
      group.name_offset = offset
      write_str_with_null_byte(data, group.name_offset, group.name)
      group.save_changes()
      offset += len(group.name) + 1
    
    align_data_to_nearest(data, 0x20, padding_bytes=b'\xFF')
    
    self.num_vertices = len(self.vertices)
    write_u32(data, 0x00, self.num_vertices)
    write_u32(data, 0x04, self.vertex_list_offset)
    
    self.num_faces = len(self.faces)
    write_u32(data, 0x08, self.num_faces)
    write_u32(data, 0x0C, self.face_list_offset)
    
    self.num_octree_blocks = len(self.octree_blocks)
    write_u32(data, 0x10, self.num_octree_blocks)
    write_u32(data, 0x14, self.octree_block_list_offset)
    
    self.num_octree_nodes = len(self.octree_nodes)
    write_u32(data, 0x18, self.num_octree_nodes)
    write_u32(data, 0x1C, self.octree_node_list_offset)
    
    self.num_groups = len(self.groups)
    write_u32(data, 0x20, self.num_groups)
    write_u32(data, 0x24, self.group_list_offset)
    
    self.num_properties = len(self.properties)
    write_u32(data, 0x28, self.num_properties)
    write_u32(data, 0x2C, self.property_list_offset)
    
    write_u32(data, 0x30, self.unknown_1)
  
  def add_group(self, name):
    group = Group(self.data)
    self.groups.append(group)
    group.name = name
    
    return group
  
  def add_property(self):
    property = Property(self.data)
    self.properties.append(property)
    
    return property
  
  def add_face(self, vertex_positions, property, group):
    assert len(vertex_positions) == 3
    
    face = Face(self.data)
    self.faces.append(face)
    face.property = property
    face.group = group
    
    for x, y, z in vertex_positions:
      vertex = next((
        v for v in self.vertices
        if v.x_pos == x and v.y_pos == y and v.z_pos == z
      ), None)
      
      if vertex is None:
        vertex = Vertex(self.data)
        self.vertices.append(vertex)
        vertex.x_pos = x
        vertex.y_pos = y
        vertex.z_pos = z
      
      face.vertices.append(vertex)
    
    return face
  
  def regenerate_octree(self):
    self.octree_nodes = []
    self.octree_blocks = []
    
    for group in self.groups:
      faces = [f for f in self.faces if f.group == group]
      #print([self.faces.index(face) for face in faces])
      if not faces:
        continue
      
      block = OctreeBlock(self.data)
      self.octree_blocks.append(block)
      for face in faces:
        block.faces.append(face)
      
      node = OctreeNode(self.data)
      self.octree_nodes.append(node)
      node.is_leaf = True
      node.block = block
      
      group.octree_root_node_index = self.octree_nodes.index(node)
      
      # TODO: properly split each group's root octree node into eighths recursively.

class Vertex:
  DATA_SIZE = 0xC
  
  def __init__(self, dzb_data):
    self.dzb_data = dzb_data
  
  def read(self, offset):
    self.offset = offset
    
    self.x_pos = read_float(self.dzb_data, self.offset+0)
    self.y_pos = read_float(self.dzb_data, self.offset+4)
    self.z_pos = read_float(self.dzb_data, self.offset+8)
  
  def save_changes(self):
    write_float(self.dzb_data, self.offset+0, self.x_pos)
    write_float(self.dzb_data, self.offset+4, self.y_pos)
    write_float(self.dzb_data, self.offset+8, self.z_pos)

class Face:
  DATA_SIZE = 0xA
  
  def __init__(self, dzb_data):
    self.dzb_data = dzb_data
    
    self.vertices = []
    self.property = None
    self.group = None
  
  def read(self, offset):
    self.offset = offset
    
    self.vertex_1_index = read_u16(self.dzb_data, self.offset+0)
    self.vertex_2_index = read_u16(self.dzb_data, self.offset+2)
    self.vertex_3_index = read_u16(self.dzb_data, self.offset+4)
    self.property_index = read_u16(self.dzb_data, self.offset+6)
    self.group_index    = read_u16(self.dzb_data, self.offset+8)
    
    # These will be populated by the DZB initialization function.
    self.vertices = []
    self.property = None
    self.group = None
  
  def save_changes(self):
    write_u16(self.dzb_data, self.offset+0, self.vertex_1_index)
    write_u16(self.dzb_data, self.offset+2, self.vertex_2_index)
    write_u16(self.dzb_data, self.offset+4, self.vertex_3_index)
    write_u16(self.dzb_data, self.offset+6, self.property_index)
    write_u16(self.dzb_data, self.offset+8, self.group_index)

class OctreeBlock:
  DATA_SIZE = 2
  
  def __init__(self, dzb_data):
    self.dzb_data = dzb_data
    
    self.first_face_index = 0xFFFF
    self.faces = []
  
  def read(self, offset):
    self.offset = offset
    
    self.first_face_index = read_u16(self.dzb_data, self.offset+0x00)
    
    # This will be populated by the DZB initialization function.
    self.faces = []
  
  def save_changes(self):
    write_u16(self.dzb_data, self.offset+0x00, self.first_face_index)

class OctreeNode:
  DATA_SIZE = 0x14
  
  def __init__(self, dzb_data):
    self.dzb_data = dzb_data
    
    self.is_leaf = False
    
    self.parent_node_index = -1
    
    self.child_indexes = [-1]*8
  
  def read(self, offset):
    self.offset = offset
    
    flags = read_u16(self.dzb_data, self.offset+0x00)
    self.is_leaf = (flags & 0x0001) != 0
    assert (flags & 0xFFFE) == 0x0100
    
    self.parent_node_index = read_s16(self.dzb_data, self.offset+0x02)
    
    self.child_indexes = []
    for i in range(8):
      child_index = read_s16(self.dzb_data, self.offset+0x04 + i*2)
      self.child_indexes.append(child_index)
      if self.is_leaf and i > 1:
        assert child_index == -1
    
    # One of these will be populated by the DZB initialization function.
    if self.is_leaf:
      self.block = None
    else:
      self.child_nodes = []
  
  def save_changes(self):
    flags = 0x0100
    if self.is_leaf:
      flags |= 0x0001
    write_u16(self.dzb_data, self.offset+0x00, flags)
    
    write_s16(self.dzb_data, self.offset+0x02, self.parent_node_index)
    
    for i in range(8):
      child_index = self.child_indexes[i]
      write_s16(self.dzb_data, self.offset+0x04 + i*2, child_index)

class Group:
  DATA_SIZE = 0x34
  
  def __init__(self, dzb_data):
    self.dzb_data = dzb_data
    
    self.name_offset = None
    self.name = None
    
    self.x_scale = 1.0
    self.y_scale = 1.0
    self.z_scale = 1.0
    
    self.x_rot = 0
    self.y_rot = 0
    self.z_rot = 0
    
    self.unknown_1 = 0xFFFF
    
    self.x_translation = 0.0
    self.y_translation = 0.0
    self.z_translation = 0.0
    
    self.parent_group_index       = -1
    self.next_sibling_group_index = -1
    self.first_child_group_index  = -1
    
    self.parent_group = None
    self.children = []
    
    self.room_index             = -1
    self.unknown_2              = 0
    self.octree_root_node_index = -1
    
    self.rtbl_index = 0xFF
    self.is_water   = False
    self.is_lava    = False
    self.unused_1   = False
    self.sound_id   = 0
    self.unused_2   = 0
  
  def read(self, offset):
    self.offset = offset
    
    self.name_offset = read_u32(self.dzb_data, self.offset+0x00)
    self.name = read_str_until_null_character(self.dzb_data, self.name_offset)
    
    self.x_scale = read_float(self.dzb_data, self.offset+0x04)
    self.y_scale = read_float(self.dzb_data, self.offset+0x08)
    self.z_scale = read_float(self.dzb_data, self.offset+0x0C)
    
    self.x_rot = read_u16(self.dzb_data, self.offset+0x10)
    self.y_rot = read_u16(self.dzb_data, self.offset+0x12)
    self.z_rot = read_u16(self.dzb_data, self.offset+0x14)
    
    self.unknown_1 = read_u16(self.dzb_data, self.offset+0x16) # Usually 0xFFFF, but sometimes 0xDCDC.
    
    self.x_translation = read_float(self.dzb_data, self.offset+0x18)
    self.y_translation = read_float(self.dzb_data, self.offset+0x1C)
    self.z_translation = read_float(self.dzb_data, self.offset+0x20)
    
    self.parent_group_index       = read_s16(self.dzb_data, self.offset+0x24)
    self.next_sibling_group_index = read_s16(self.dzb_data, self.offset+0x26)
    self.first_child_group_index  = read_s16(self.dzb_data, self.offset+0x28)
    
    # These will be populated by the DZB initialization function.
    self.parent_group = None
    self.children = None
    
    self.room_index             = read_s16(self.dzb_data, self.offset+0x2A)
    self.unknown_2              = read_u16(self.dzb_data, self.offset+0x2C)
    self.octree_root_node_index = read_s16(self.dzb_data, self.offset+0x2E)
    
    bitfield = read_u32(self.dzb_data, self.offset+0x30)
    self.rtbl_index = (bitfield & 0x000000FF) >> 0
    self.is_water   = (bitfield & 0x00000100) != 0
    self.is_lava    = (bitfield & 0x00000200) != 0
    self.unused_1   = (bitfield & 0x00000400) != 0
    self.sound_id   = (bitfield & 0x0007F800) >> 11
    self.unused_2   = (bitfield & 0xFFF80000) >> 19
  
  def save_changes(self):
    write_u32(self.dzb_data, self.offset+0x00, self.name_offset)
    
    write_float(self.dzb_data, self.offset+0x04, self.x_scale)
    write_float(self.dzb_data, self.offset+0x08, self.y_scale)
    write_float(self.dzb_data, self.offset+0x0C, self.z_scale)
    
    write_u16(self.dzb_data, self.offset+0x10, self.x_rot)
    write_u16(self.dzb_data, self.offset+0x12, self.y_rot)
    write_u16(self.dzb_data, self.offset+0x14, self.z_rot)
    
    write_u16(self.dzb_data, self.offset+0x16, self.unknown_1)
    
    write_float(self.dzb_data, self.offset+0x18, self.x_translation)
    write_float(self.dzb_data, self.offset+0x1C, self.y_translation)
    write_float(self.dzb_data, self.offset+0x20, self.z_translation)
    
    write_s16(self.dzb_data, self.offset+0x24, self.parent_group_index)
    write_s16(self.dzb_data, self.offset+0x26, self.next_sibling_group_index)
    write_s16(self.dzb_data, self.offset+0x28, self.first_child_group_index)
    
    write_s16(self.dzb_data, self.offset+0x2A, self.room_index)
    write_u16(self.dzb_data, self.offset+0x2C, self.unknown_2)
    write_s16(self.dzb_data, self.offset+0x2E, self.octree_root_node_index)
    
    bitfield = 0
    bitfield |= (self.rtbl_index << 0)  & 0x000000FF
    bitfield |= (self.is_water   << 8)  & 0x00000100
    bitfield |= (self.is_lava    << 9)  & 0x00000200
    bitfield |= (self.unused_1   << 10) & 0x00000400
    bitfield |= (self.sound_id   << 11) & 0x0007F800
    bitfield |= (self.unused_2   << 19) & 0xFFF80000
    write_u32(self.dzb_data, self.offset+0x30, bitfield)

class Property:
  DATA_SIZE = 0x10
  
  def __init__(self, dzb_data):
    self.dzb_data = dzb_data
    
    self.cam_id     = 0xFF
    self.sound_id   = 0
    self.exit_index = 0x3F
    self.poly_color = 0xFF
    self.unknown_1  = 0
    
    self.link_no        = 0xFF
    self.wall_type      = 0
    self.special_type   = 0
    self.attribute_type = 0
    self.ground_type    = 0
    self.unknown_2      = 0
    
    self.cam_move_bg        = 0
    self.room_cam_id        = 0xFF
    self.room_path_id       = 0xFF
    self.room_path_point_no = 0xFF
    
    self.camera_behavior = 0
  
  def read(self, offset):
    self.offset = offset
    
    bitfield_1 = read_u32(self.dzb_data, self.offset+0x00)
    self.cam_id     = (bitfield_1 & 0x000000FF) >> 0
    self.sound_id   = (bitfield_1 & 0x00001F00) >> 8
    self.exit_index = (bitfield_1 & 0x0007E000) >> 13
    self.poly_color = (bitfield_1 & 0x07F80000) >> 19
    self.unknown_1  = (bitfield_1 & 0xF8000000) >> 27
    
    bitfield_2 = read_u32(self.dzb_data, self.offset+0x04)
    self.link_no        = (bitfield_2 & 0x000000FF) >> 0
    self.wall_type      = (bitfield_2 & 0x00000F00) >> 8
    self.special_type   = (bitfield_2 & 0x0000F000) >> 12
    self.attribute_type = (bitfield_2 & 0x001F0000) >> 16
    self.ground_type    = (bitfield_2 & 0x03E00000) >> 21
    self.unknown_2      = (bitfield_2 & 0xFC000000) >> 26
    
    bitfield_3 = read_u32(self.dzb_data, self.offset+0x08)
    self.cam_move_bg        = (bitfield_3 & 0x000000FF) >> 0
    self.room_cam_id        = (bitfield_3 & 0x0000FF00) >> 8
    self.room_path_id       = (bitfield_3 & 0x00FF0000) >> 16
    self.room_path_point_no = (bitfield_3 & 0xFF000000) >> 24
    
    self.camera_behavior = read_u32(self.dzb_data, self.offset+0x0C)
  
  def save_changes(self):
    bitfield_1 = 0
    bitfield_1 |= (self.cam_id     << 0 ) & 0x000000FF
    bitfield_1 |= (self.sound_id   << 8 ) & 0x00001F00
    bitfield_1 |= (self.exit_index << 13) & 0x0007E000
    bitfield_1 |= (self.poly_color << 19) & 0x07F80000
    bitfield_1 |= (self.unknown_1  << 27) & 0xF8000000
    write_u32(self.dzb_data, self.offset+0x00, bitfield_1)
    
    bitfield_2 = 0
    bitfield_2 |= (self.link_no        << 0 ) & 0x000000FF
    bitfield_2 |= (self.wall_type      << 8 ) & 0x00000F00
    bitfield_2 |= (self.special_type   << 12) & 0x0000F000
    bitfield_2 |= (self.attribute_type << 16) & 0x001F0000
    bitfield_2 |= (self.ground_type    << 21) & 0x03E00000
    bitfield_2 |= (self.unknown_2      << 26) & 0xFC000000
    write_u32(self.dzb_data, self.offset+0x04, bitfield_2)
    
    bitfield_3 = 0
    bitfield_3 |= (self.cam_move_bg        << 0 ) & 0x000000FF
    bitfield_3 |= (self.room_cam_id        << 8 ) & 0x0000FF00
    bitfield_3 |= (self.room_path_id       << 16) & 0x00FF0000
    bitfield_3 |= (self.room_path_point_no << 24) & 0xFF000000
    write_u32(self.dzb_data, self.offset+0x08, bitfield_3)
    
    write_u32(self.dzb_data, self.offset+0x0C, self.camera_behavior)
