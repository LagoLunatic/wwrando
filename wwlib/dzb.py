
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
    
    self.num_properties = read_u32(data, 0x20)
    self.property_list_offset = read_u32(data, 0x24)
    
    self.vertices = []
    offset = self.vertex_list_offset
    for vertex_index in range(0, self.num_vertices):
      vertex = Vertex(data, offset)
      self.vertices.append(vertex)
      
      offset += 0xC
  
  def save_changes(self):
    pass

class Vertex:
  def __init__(self, dzb_data, vertex_offset):
    self.x_pos = read_float(dzb_data, vertex_offset+0)
    self.y_pos = read_float(dzb_data, vertex_offset+4)
    self.z_pos = read_float(dzb_data, vertex_offset+8)
    
    self.dzb_data = dzb_data
    self.vertex_offset = vertex_offset
  
  def save_changes(self):
    write_float(self.dzb_data, self.vertex_offset+0, self.x_pos)
    write_float(self.dzb_data, self.vertex_offset+4, self.y_pos)
    write_float(self.dzb_data, self.vertex_offset+8, self.z_pos)

class Face:
  pass

class Octree:
  pass

class Property:
  pass

class Group:
  pass
