
from fs_helpers import *
from io import BytesIO

class EventList:
  def __init__(self, file_entry):
    self.file_entry = file_entry
    data = self.file_entry.data
    
    self.event_list_offset = read_u32(data, 0x00)
    self.num_events = read_u32(data, 0x04)
    self.actor_list_offset = read_u32(data, 0x08)
    self.num_actors = read_u32(data, 0x0C)
    self.action_list_offset = read_u32(data, 0x10)
    self.num_actions = read_u32(data, 0x14)
    self.property_list_offset = read_u32(data, 0x18)
    self.num_properties = read_u32(data, 0x1C)
    self.integer_list_offset = read_u32(data, 0x28)
    self.num_integers = read_u32(data, 0x2C)
    self.string_list_offset = read_u32(data, 0x30)
    self.string_list_total_size = read_u32(data, 0x34)
    
    self.events = []
    for event_index in range(0, self.num_events):
      offset = self.event_list_offset + event_index * Event.DATA_SIZE
      event = Event(self.file_entry, offset)
      self.events.append(event)
    
    self.actors = []
    for actor_index in range(0, self.num_actors):
      offset = self.actor_list_offset + actor_index * Actor.DATA_SIZE
      actor = Actor(self.file_entry, offset)
      self.actors.append(actor)
    
    self.actions = []
    for action_index in range(0, self.num_actions):
      offset = self.action_list_offset + action_index * Action.DATA_SIZE
      action = Action(self.file_entry, offset)
      self.actions.append(action)
    
    # Populate each events's list of actors.
    for event in self.events:
      for actor_index in event.actor_indexes:
        if actor_index == 0xFFFFFFFF:
          event.actors.append(None)
        else:
          actor = self.actors[actor_index]
          event.actors.append(actor)
    
    # Populate each actor's list of actions.
    for actor in self.actors:
      initial_action = self.actions[actor.initial_action_index]
      actor.actions.append(initial_action)
      action = initial_action
      while action.next_action_index != 0xFFFFFFFF:
        action = self.actions[action.next_action_index]
        actor.actions.append(action)
    
    self.properties = []
    for property_index in range(0, self.num_properties):
      offset = self.property_list_offset + property_index * Property.DATA_SIZE
      property = Property(self.file_entry, offset)
      self.properties.append(property)
    
    # Populate each action's list of properties.
    for action in self.actions:
      if action.property_index == 0xFFFFFFFF:
        continue
      first_property = self.properties[action.property_index]
      action.properties.append(first_property)
      property = first_property
      while property.next_property_index != 0xFFFFFFFF:
        property = self.properties[property.next_property_index]
        action.properties.append(property)
    
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
  
  def set_property_value(self, property_index, new_value):
    data = self.file_entry.data
    
    property = self.properties[property_index]
    
    if property.data_type == 1:
      pass # TODO
    elif property.data_type == 3:
      offset = self.integer_list_offset + property.data_index * 4
      write_u32(data, offset, new_value)
    elif property.data_type == 4:
      pass # TODO

class Event:
  DATA_SIZE = 0xB0
  
  def __init__(self, file_entry, offset):
    self.file_entry = file_entry
    data = self.file_entry.data
    self.offset = offset
    
    self.name = read_str(data, offset, 0x20)
    self.event_index = read_u32(data, offset+0x20)
    self.unknown1 = read_u32(data, offset+0x24)
    self.priority = read_u32(data, offset+0x28)
    self.actor_indexes = []
    for i in range(0x14):
      actor_index = read_u32(data, offset+0x2C+i*4)
      self.actor_indexes.append(actor_index)
    self.num_actors = read_u32(data, offset+0x7C)
    
    self.actors = [] # This will be populated by the event list after it reads the actors.

class Actor:
  DATA_SIZE = 0x50
  
  def __init__(self, file_entry, offset):
    self.file_entry = file_entry
    data = self.file_entry.data
    self.offset = offset
    
    self.name = read_str(data, offset, 0x20)
    self.staff_identifier = read_u32(data, offset+0x20)
    self.actor_index = read_u32(data, offset+0x24)
    self.flag_id_to_set = read_u32(data, offset+0x28)
    self.staff_type = read_u32(data, offset+0x2C)
    self.initial_action_index = read_u32(data, offset+0x30)
    
    self.actions = [] # This will be populated by the event list after it reads the actions.
  
  def save_changes(self):
    data = self.file_entry.data
    
    write_str(data, self.offset, self.name, 0x20)
    write_u32(data, self.offset+0x20, self.staff_identifier)
    write_u32(data, self.offset+0x24, self.actor_index)
    write_u32(data, self.offset+0x28, self.flag_id_to_set)
    write_u32(data, self.offset+0x2C, self.staff_type)
    write_u32(data, self.offset+0x30, self.initial_action_index)

class Action:
  DATA_SIZE = 0x50
  
  def __init__(self, file_entry, offset):
    self.file_entry = file_entry
    data = self.file_entry.data
    self.offset = offset
    
    self.name = read_str(data, offset, 0x20)
    self.duplicate_id = read_u32(data, offset+0x20)
    self.action_index = read_u32(data, offset+0x24)
    self.flag_id_to_set = read_u32(data, offset+0x34)
    self.property_index = read_u32(data, offset+0x38)
    self.next_action_index = read_u32(data, offset+0x3C)
    
    self.properties = [] # This will be populated by the event list after it reads the properties.
  
  def save_changes(self):
    data = self.file_entry.data
    
    write_str(data, self.offset, self.name, 0x20)
    write_u32(data, self.offset+0x20, self.duplicate_id)
    write_u32(data, self.offset+0x24, self.action_index)
    write_u32(data, self.offset+0x34, self.flag_id_to_set)
    write_u32(data, self.offset+0x38, self.property_index)
    write_u32(data, self.offset+0x3C, self.next_action_index)

class Property:
  DATA_SIZE = 0x40
  
  def __init__(self, file_entry, offset):
    self.file_entry = file_entry
    data = self.file_entry.data
    self.offset = offset
    
    self.name = read_str(data, offset, 0x20)
    
    self.property_index = read_u32(data, offset+0x20)
    self.data_type = read_u32(data, offset+0x24)
    self.data_index = read_u32(data, offset+0x28)
    self.data_size = read_u32(data, offset+0x2C)
    self.next_property_index = read_u32(data, offset+0x30)
  
  def save_changes(self):
    data = self.file_entry.data
    
    write_str(data, self.offset, self.name, 0x20)
    write_u32(data, self.offset+0x20, self.property_index)
    write_u32(data, self.offset+0x24, self.data_type)
    write_u32(data, self.offset+0x28, self.data_index)
    write_u32(data, self.offset+0x2C, self.data_size)
    write_u32(data, self.offset+0x30, self.next_property_index)
