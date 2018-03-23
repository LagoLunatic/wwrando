
from fs_helpers import *
from io import BytesIO

class EventList:
  def __init__(self, file_entry):
    self.file_entry = file_entry
    data = self.file_entry.data
    
    self.action_list_offset = read_u32(data, 0x10)
    self.num_actions = read_u32(data, 0x14)
    self.property_list_offset = read_u32(data, 0x18)
    self.num_properties = read_u32(data, 0x1C)
    self.integer_list_offset = read_u32(data, 0x28)
    self.num_integers = read_u32(data, 0x2C)
    self.string_list_offset = read_u32(data, 0x30)
    self.string_list_total_size = read_u32(data, 0x34)
    
    self.actions = []
    for action_index in range(0, self.num_actions):
      offset = self.action_list_offset + action_index * Action.DATA_SIZE
      action = Action(data, offset)
      self.actions.append(action)
    
    self.properties = []
    for property_index in range(0, self.num_properties):
      offset = self.property_list_offset + property_index * Property.DATA_SIZE
      property = Property(data, offset)
      self.properties.append(property)
    
    self.integers = []
    for integer_index in range(0, self.num_integers):
      offset = self.integer_list_offset + integer_index * 4
      integer = read_u32(data, offset)
      self.integers.append(integer)
  
  def save_changes(self):
    data = self.file_entry.data
    
    write_u32(data, 0x10, self.action_list_offset)
    write_u32(data, 0x14, self.num_actions)
    write_u32(data, 0x18, self.property_list_offset)
    write_u32(data, 0x1C, self.num_properties)
    write_u32(data, 0x28, self.integer_list_offset)
    write_u32(data, 0x2C, self.num_integers)
    
    offset = self.integer_list_offset
    for integer in self.integers:
      write_u32(data, offset, integer)
      offset += 4
  
  def get_property_value(self, property_index):
    property = self.properties[property_index]
    
    if property.data_type == 1:
      return self.floats[property.data_index]
    elif property.data_type == 3:
      return self.integers[property.data_index]
    elif property.data_type == 4:
      string_pointer = self.string_list_offset + property.data_index
      string = read_str(self.file_entry.data, string_pointer, property.data_size)
      return string

class Action:
  DATA_SIZE = 0x50
  
  def __init__(self, data, offset):
    self.offset = offset
    
    self.name = read_str(data, offset, 0x20)
    self.duplicate_id = read_u32(data, offset+0x20)
    self.action_index = read_u32(data, offset+0x24)
    self.flag_id_to_set = read_u32(data, offset+0x34)
    self.property_index = read_u32(data, offset+0x38)
    self.next_action_index = read_u32(data, offset+0x3C)

class Property:
  DATA_SIZE = 0x40
  
  def __init__(self, data, offset):
    self.name = read_str(data, offset, 0x20)
    
    self.data_type = read_u32(data, offset+0x24)
    self.data_index = read_u32(data, offset+0x28)
    self.data_size = read_u32(data, offset+0x2C)
    self.next_property_index = read_u32(data, offset+0x30)
