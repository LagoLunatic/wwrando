
from fs_helpers import *

class EventList:
  def __init__(self, data):
    self.action_list_offset = read_u32(data, 0x10)
    self.num_actions = read_u32(data, 0x14)
    self.actions = []
    for action_index in range(0, self.num_actions):
      offset = self.action_list_offset + action_index * Action.DATA_SIZE
      action = Action(data, offset)
      self.actions.append(action)
    
    self.property_list_offset = read_u32(data, 0x18)
    self.num_properties = read_u32(data, 0x1C)
    self.properties = []
    for property_index in range(0, self.num_properties):
      offset = self.property_list_offset + property_index * Property.DATA_SIZE
      property = Property(data, offset)
      self.properties.append(property)
    
    self.integer_list_offset = read_u32(data, 0x28)
    self.num_integers = read_u32(data, 0x2C)
    self.integers = []
    for integer_index in range(0, self.num_integers):
      offset = self.integer_list_offset + integer_index * 4
      integer = read_u32(data, offset)
      self.integers.append(integer)

class Action:
  DATA_SIZE = 0x50
  
  def __init__(self, data, offset):
    self.name = read_str(data, offset, 0x20)
    
    self.property_index = read_u32(data, offset+0x38)

class Property:
  DATA_SIZE = 0x40
  
  def __init__(self, data, offset):
    self.name = read_str(data, offset, 0x20)
    
    self.data_type = read_u32(data, offset+0x24)
    self.data_index = read_u32(data, offset+0x28)
    
    self.next_property_index = read_u32(data, offset+0x30)
