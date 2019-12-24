
from io import BytesIO

from fs_helpers import *

class DZB:
  def __init__(self, data):
    self.data = data
    
    self.num_vertices = read_u32(data, 0)
    self.vertex_list_offset = read_u32(data, 4)
    
    self.num_faces = read_u32(data, 8)
    self.face_list_offset = read_u32(data, 0xC)
    
    self.num_octree_indexes = read_u32(data, 0x10)
    self.octree_index_list_offset = read_u32(data, 0x14)
    self.num_octree_nodes = read_u32(data, 0x18)
    self.octree_node_list_offset = read_u32(data, 0x1C)
    
    self.num_groups = read_u32(data, 0x20)
    self.group_list_offset = read_u32(data, 0x24)
    
    self.num_properties = read_u32(data, 0x28)
    self.property_list_offset = read_u32(data, 0x2C)
    
    self.vertices = []
    offset = self.vertex_list_offset
    for vertex_index in range(0, self.num_vertices):
      vertex = Vertex(data, offset)
      self.vertices.append(vertex)
      
      offset += 0xC
    
    self.groups = []
    offset = self.group_list_offset
    for group_index in range(0, self.num_groups):
      group = Group(data, offset)
      self.groups.append(group)
      
      offset += 0x34
  
  def save_changes(self):
    pass

class Vertex:
  def __init__(self, dzb_data, offset):
    self.dzb_data = dzb_data
    self.offset = offset
    
    self.x_pos = read_float(dzb_data, self.offset+0)
    self.y_pos = read_float(dzb_data, self.offset+4)
    self.z_pos = read_float(dzb_data, self.offset+8)
  
  def save_changes(self):
    write_float(self.dzb_data, self.offset+0, self.x_pos)
    write_float(self.dzb_data, self.offset+4, self.y_pos)
    write_float(self.dzb_data, self.offset+8, self.z_pos)

class Face:
  pass

class Octree:
  pass

class Property:
  pass

class Group:
  def __init__(self, dzb_data, offset):
    self.dzb_data = dzb_data
    self.offset = offset
    
    # WARNING: Incomplete implementation!
    
    self.room_index = read_u16(dzb_data, self.offset+0x2A)
    
    group_info = read_u32(dzb_data, self.offset+0x30)
    self.rtbl_index = (group_info & 0x000000FF) >> 0
    self.is_water   = (group_info & 0x00000100) >> 8
    self.is_lava    = (group_info & 0x00000200) >> 9
    self.unused_1   = (group_info & 0x00000400) >> 10
    self.sound_id   = (group_info & 0x0007F800) >> 11
    self.unused_2   = (group_info & 0xFFF80000) >> 19
  
  def save_changes(self):
    write_u16(self.dzb_data, self.offset+0x2A, self.room_index)
    
    group_info = 0
    group_info |= (self.rtbl_index << 0)  & 0x000000FF
    group_info |= (self.is_water   << 8)  & 0x00000100
    group_info |= (self.is_lava    << 9)  & 0x00000200
    group_info |= (self.unused_1   << 10) & 0x00000400
    group_info |= (self.sound_id   << 11) & 0x0007F800
    group_info |= (self.unused_2   << 19) & 0xFFF80000
    write_u32(self.dzb_data, self.offset+0x30, group_info)
