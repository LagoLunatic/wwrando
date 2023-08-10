
from collections import OrderedDict

from gclib import fs_helpers as fs

class EventList:
  TOTAL_NUM_FLAGS = 0x2800
  
  def __init__(self, file_entry):
    self.file_entry = file_entry
    data = self.file_entry.data
    
    event_list_offset = fs.read_u32(data, 0x00)
    num_events = fs.read_u32(data, 0x04)
    actor_list_offset = fs.read_u32(data, 0x08)
    num_actors = fs.read_u32(data, 0x0C)
    action_list_offset = fs.read_u32(data, 0x10)
    num_actions = fs.read_u32(data, 0x14)
    property_list_offset = fs.read_u32(data, 0x18)
    num_properties = fs.read_u32(data, 0x1C)
    self.float_list_offset = fs.read_u32(data, 0x20)
    num_floats = fs.read_u32(data, 0x24)
    self.integer_list_offset = fs.read_u32(data, 0x28)
    num_integers = fs.read_u32(data, 0x2C)
    self.string_list_offset = fs.read_u32(data, 0x30)
    string_list_total_size = fs.read_u32(data, 0x34)
    self.header_padding = fs.read_bytes(data, 0x38, 8)
    
    self.events: list[Event] = []
    self.events_by_name: dict[str, Event] = {}
    for event_index in range(0, num_events):
      offset = event_list_offset + event_index * Event.DATA_SIZE
      event = Event(self)
      event.read(offset)
      self.events.append(event)
      if event.name in self.events_by_name:
        raise Exception("Duplicate event name: %s" % event.name)
      self.events_by_name[event.name] = event
    
    all_actors = []
    for actor_index in range(0, num_actors):
      offset = actor_list_offset + actor_index * Actor.DATA_SIZE
      actor = Actor(self)
      actor.read(offset)
      all_actors.append(actor)
    
    all_actions = []
    for action_index in range(0, num_actions):
      offset = action_list_offset + action_index * Action.DATA_SIZE
      action = Action(self)
      action.read(offset)
      all_actions.append(action)
    
    # Populate each events's list of actors.
    for event in self.events:
      found_blank = False
      for actor_index in event.actor_indexes:
        if actor_index == -1:
          pass # Blank actor spot
          found_blank = True
        else:
          if found_blank:
            raise Exception("Found a non-blank actor after a blank actor in an event's actor indexes list")
          actor = all_actors[actor_index]
          event.actors.append(actor)
    
    # Populate each actor's list of actions.
    for actor in all_actors:
      actor.initial_action = all_actions[actor.initial_action_index]
      actor.actions.append(actor.initial_action)
      action = actor.initial_action
      while action.next_action_index != -1:
        next_action = all_actions[action.next_action_index]
        action.next_action = next_action
        actor.actions.append(next_action)
        action = next_action
    
    all_properties = []
    for property_index in range(0, num_properties):
      offset = property_list_offset + property_index * Property.DATA_SIZE
      property = Property(self)
      property.read(offset)
      all_properties.append(property)
    
    # Populate each action's list of properties.
    for action in all_actions:
      if action.first_property_index == -1:
        continue
      first_property = all_properties[action.first_property_index]
      action.properties.append(first_property)
      property = first_property
      while property.next_property_index != -1:
        next_property = all_properties[property.next_property_index]
        property.next_property = next_property
        action.properties.append(next_property)
        property = next_property
    
    all_floats = []
    for float_index in range(0, num_floats):
      offset = self.float_list_offset + float_index * 4
      float_val = fs.read_float(data, offset)
      all_floats.append(float_val)
    
    all_integers = []
    for integer_index in range(0, num_integers):
      offset = self.integer_list_offset + integer_index * 4
      integer = fs.read_s32(data, offset)
      all_integers.append(integer)
    
    all_strings_by_offset = OrderedDict()
    offset = self.string_list_offset
    while offset < self.string_list_offset+string_list_total_size:
      string = fs.read_str_until_null_character(data, offset)
      all_strings_by_offset[offset-self.string_list_offset] = string
      string_length_with_null = len(string)+1
      offset += string_length_with_null
      
      # These strings are padded with null bytes to the next 8 bytes in length, so we skip the padding bytes.
      if string_length_with_null % 8 != 0:
        padding_bytes_to_skip = (8 - (string_length_with_null % 8))
        
        # To be safe ensure that the bytes we skip are actually all null bytes.
        for i in range(padding_bytes_to_skip):
          padding_byte = fs.read_u8(data, offset+i)
          assert padding_byte == 0
        
        offset += padding_bytes_to_skip
    
    # Assign each property's value.
    for property in all_properties:
      if property.data_type == 0:
        property.value = []
        for i in range(property.data_size):
          property.value.append(all_floats[property.data_index+i])
        if property.data_size == 1:
          property.value = property.value[0]
      elif property.data_type == 1:
        property.value = []
        for i in range(property.data_size):
          x = all_floats[property.data_index+i*3]
          y = all_floats[property.data_index+i*3+1]
          z = all_floats[property.data_index+i*3+2]
          property.value.append((x, y, z))
        if property.data_size == 1:
          property.value = property.value[0]
      elif property.data_type == 3:
        property.value = []
        for i in range(property.data_size):
          property.value.append(all_integers[property.data_index+i])
        if property.data_size == 1:
          property.value = property.value[0]
      elif property.data_type == 4:
        property.value = all_strings_by_offset[property.data_index]
      else:
        raise Exception("Reading property data type %d not implemented" % property.data_type)
    
    # Keep track of which flag IDs haven't been used yet in case we need to add new actors/actions.
    self.unused_flag_ids = list(range(self.TOTAL_NUM_FLAGS))
    for event in self.events:
      for actor in event.actors:
        self.unused_flag_ids.remove(actor.flag_id_to_set)
        for action in actor.actions:
          self.unused_flag_ids.remove(action.flag_id_to_set)
  
  def save_changes(self):
    data = self.file_entry.data
    
    # Cut off all the data after the header first since we're completely replacing this data.
    data.truncate(0x40)
    data.seek(0x40)
    
    offset = 0x40
    
    all_events = self.events
    all_actors = []
    all_actions = []
    all_properties = []
    all_floats = []
    all_integers = []
    all_strings = []
    
    event_list_offset = offset
    num_events = len(all_events)
    for i, event in enumerate(all_events):
      event.offset = offset
      event.event_index = i
      
      offset += Event.DATA_SIZE
      
      all_actors += event.actors
    
    actor_list_offset = offset
    num_actors = len(all_actors)
    for i, actor in enumerate(all_actors):
      actor.offset = offset
      actor.actor_index = i
      
      offset += Actor.DATA_SIZE
      
      for i, action in enumerate(actor.actions):
        all_actions.append(action)
        if i == len(actor.actions)-1:
          action.next_action = None
        else:
          action.next_action = actor.actions[i+1]
    
    action_list_offset = offset
    num_actions = len(all_actions)
    for i, action in enumerate(all_actions):
      action.offset = offset
      action.action_index = i
      
      offset += Action.DATA_SIZE
      
      for i, property in enumerate(action.properties):
        all_properties.append(property)
        if i == len(action.properties)-1:
          property.next_property = None
        else:
          property.next_property = action.properties[i+1]
    
    property_list_offset = offset
    num_properties = len(all_properties)
    for i, property in enumerate(all_properties):
      property.offset = offset
      property.property_index = i
      
      offset += Property.DATA_SIZE
      
      property_value = property.value
      if property_value.__class__ in [float, int, tuple]:
        property_value = [property_value]
      
      if isinstance(property_value, str):
        property.data_type = 4
        # The string offset and length will be set when writing the string itself.
        property.data_index = None
        property.data_size = None
        
        all_strings.append(property_value)
      elif isinstance(property_value, list):
        property.data_size = len(property_value)
        if len(property_value) == 0:
          # Default to int for empty properties
          first_val_class = int
        else:
          first_val_class = property_value[0].__class__
        if first_val_class == float:
          property.data_type = 0
          property.data_index = len(all_floats)
          
          for float_val in property_value:
            all_floats.append(float_val)
        elif first_val_class == tuple:
          property.data_type = 1
          property.data_index = len(all_floats)
          
          for vector3 in property_value:
            assert len(vector3) == 3
            x, y, z = vector3
            all_floats.append(x)
            all_floats.append(y)
            all_floats.append(z)
        elif first_val_class == int:
          property.data_type = 3
          property.data_index = len(all_integers)
          
          for integer in property_value:
            all_integers.append(integer)
        else:
          raise Exception("Unknown type of property %s: %s" % (property.name, repr(property_value)))
      else:
        raise Exception("Unknown type of property %s: %s" % (property.name, repr(property_value)))
    
    self.float_list_offset = offset
    num_floats = len(all_floats)
    for float_val in all_floats:
      fs.write_float(data, offset, float_val)
      offset += 4
    
    self.integer_list_offset = offset
    num_integers = len(all_integers)
    for integer in all_integers:
      fs.write_s32(data, offset, integer)
      offset += 4
    
    self.string_list_offset = offset
    for property in all_properties:
      if property.data_type == 4:
        string = property.value
        fs.write_str_with_null_byte(data, offset, string)
        new_relative_string_offset = offset-self.string_list_offset
        
        string_length_with_null = len(string)+1
        offset += string_length_with_null
        
        # These strings are padded to the next 8 bytes in length.
        if string_length_with_null % 8 != 0:
          padding_bytes_needed = (8 - (string_length_with_null % 8))
          padding = b"\0"*padding_bytes_needed
          fs.write_bytes(data, offset, padding)
          offset += padding_bytes_needed
          string_length_with_padding = string_length_with_null + padding_bytes_needed
        else:
          string_length_with_padding = string_length_with_null
        
        property.data_index = new_relative_string_offset
        property.data_size = string_length_with_padding
    string_list_total_size = offset - self.string_list_offset
    
    for event in all_events:
      event.save_changes()
    for actor in all_actors:
      actor.save_changes()
    for action in all_actions:
      action.save_changes()
    for property in all_properties:
      property.save_changes()
    
    fs.write_u32(data, 0x00, event_list_offset)
    fs.write_u32(data, 0x04, num_events)
    fs.write_u32(data, 0x08, actor_list_offset)
    fs.write_u32(data, 0x0C, num_actors)
    fs.write_u32(data, 0x10, action_list_offset)
    fs.write_u32(data, 0x14, num_actions)
    fs.write_u32(data, 0x18, property_list_offset)
    fs.write_u32(data, 0x1C, num_properties)
    fs.write_u32(data, 0x20, self.float_list_offset)
    fs.write_u32(data, 0x24, num_floats)
    fs.write_u32(data, 0x28, self.integer_list_offset)
    fs.write_u32(data, 0x2C, num_integers)
    fs.write_u32(data, 0x30, self.string_list_offset)
    fs.write_u32(data, 0x34, string_list_total_size)
    fs.write_bytes(data, 0x38, self.header_padding)
  
  def add_event(self, name):
    assert name not in self.events_by_name
    event = Event(self)
    event.name = name
    self.events.append(event)
    self.events_by_name[name] = event
    return event
  
  def get_unused_flag_id(self):
    if not self.unused_flag_ids:
      raise Exception("No unused flags left for adding new actor/action to event_list.dat!")
    
    return self.unused_flag_ids.pop(0)

class Event:
  DATA_SIZE = 0xB0
  
  def __init__(self, event_list):
    self.event_list = event_list
    
    self.name = None
    self.event_index = None
    self.unknown1 = 0
    self.priority = 0
    self.actor_indexes = [-1]*0x14
    self.num_actors = 0
    self.starting_flags = [-1, -1]
    self.ending_flags = [-1, -1, -1]
    self.play_jingle = False
    self.zero_initialized_runtime_data = b"\0"*0x1B
    self.actors = []
  
  def read(self, offset):
    data = self.event_list.file_entry.data
    self.offset = offset
    
    self.name = fs.read_str(data, offset, 0x20)
    self.event_index = fs.read_s32(data, offset+0x20)
    self.unknown1 = fs.read_u32(data, offset+0x24)
    self.priority = fs.read_u32(data, offset+0x28)
    
    self.actor_indexes = []
    for i in range(0x14):
      actor_index = fs.read_s32(data, offset+0x2C+i*4)
      self.actor_indexes.append(actor_index)
    self.num_actors = fs.read_u32(data, offset+0x7C)
    
    self.starting_flags = []
    for i in range(2):
      flag_id = fs.read_s32(data, offset+0x80+i*4)
      self.starting_flags.append(flag_id)
    
    self.ending_flags = []
    for i in range(3):
      flag_id = fs.read_s32(data, offset+0x88+i*4)
      self.ending_flags.append(flag_id)
    
    self.play_jingle = bool(fs.read_u8(data, offset+0x94))
    
    self.zero_initialized_runtime_data = fs.read_bytes(data, offset+0x95, 0x1B)
    
    self.actors = [] # This will be populated by the event list after it reads the actors.
  
  def save_changes(self):
    data = self.event_list.file_entry.data
    
    fs.write_str(data, self.offset, self.name, 0x20)
    fs.write_s32(data, self.offset+0x20, self.event_index)
    fs.write_u32(data, self.offset+0x24, self.unknown1)
    fs.write_u32(data, self.offset+0x28, self.priority)
    
    for i in range(0x14):
      if i >= len(self.actors):
        actor_index = -1
      else:
        actor_index = self.actors[i].actor_index
      self.actor_indexes[i] = actor_index
      fs.write_s32(data, self.offset+0x2C+i*4, actor_index)
    self.num_actors = len(self.actors)
    fs.write_u32(data, self.offset+0x7C, self.num_actors)
    
    for i in range(2):
      flag_id = self.starting_flags[i]
      fs.write_s32(data, self.offset+0x80+i*4, flag_id)
    
    for i in range(3):
      flag_id = self.ending_flags[i]
      fs.write_s32(data, self.offset+0x88+i*4, flag_id)
    
    fs.write_u8(data, self.offset+0x94, int(self.play_jingle))
    
    fs.write_bytes(data, self.offset+0x95, self.zero_initialized_runtime_data)
  
  def add_actor(self, name):
    actor = Actor(self.event_list)
    actor.name = name
    actor.flag_id_to_set = self.event_list.get_unused_flag_id()
    self.actors.append(actor)
    return actor

class Actor:
  DATA_SIZE = 0x50
  
  def __init__(self, event_list):
    self.event_list = event_list
    
    self.name = None
    self.staff_identifier = 0
    self.actor_index = None
    self.flag_id_to_set = None
    self.staff_type = 0
    self.initial_action_index = None
    self.zero_initialized_runtime_data = b"\0"*0x1C
    self.actions = []
    self.initial_action = None
  
  def read(self, offset):
    data = self.event_list.file_entry.data
    self.offset = offset
    
    self.name = fs.read_str(data, offset, 0x20)
    self.staff_identifier = fs.read_u32(data, offset+0x20)
    self.actor_index = fs.read_s32(data, offset+0x24)
    self.flag_id_to_set = fs.read_s32(data, offset+0x28)
    self.staff_type = fs.read_u32(data, offset+0x2C)
    self.initial_action_index = fs.read_s32(data, offset+0x30)
    
    self.zero_initialized_runtime_data = fs.read_bytes(data, offset+0x34, 0x1C)
    
    # These will be populated by the event list initialization function.
    self.actions = []
    self.initial_action = None
  
  def save_changes(self):
    data = self.event_list.file_entry.data
    
    if len(self.actions) == 0:
      raise Exception("Cannot save actor with no actions!")
    
    fs.write_str(data, self.offset, self.name, 0x20)
    fs.write_u32(data, self.offset+0x20, self.staff_identifier)
    fs.write_s32(data, self.offset+0x24, self.actor_index)
    fs.write_s32(data, self.offset+0x28, self.flag_id_to_set)
    fs.write_u32(data, self.offset+0x2C, self.staff_type)
    
    self.initial_action = self.actions[0]
    self.initial_action_index = self.initial_action.action_index
    fs.write_s32(data, self.offset+0x30, self.initial_action_index)
    
    fs.write_bytes(data, self.offset+0x34, self.zero_initialized_runtime_data)
  
  def add_action(self, name, properties=[]):
    action = Action(self.event_list)
    action.name = name
    action.flag_id_to_set = self.event_list.get_unused_flag_id()
    self.actions.append(action)
    for prop_name, prop_value in properties:
      prop = action.add_property(prop_name)
      prop.value = prop_value
    return action

class Action:
  DATA_SIZE = 0x50
  
  def __init__(self, event_list):
    self.event_list = event_list
    
    self.name = None
    self.duplicate_id = 0
    self.action_index = None
    self.starting_flags = [-1, -1, -1]
    self.flag_id_to_set = None
    self.first_property_index = None
    self.next_action_index = None
    self.zero_initialized_runtime_data = b"\0"*0x10
    self.properties = []
    self.next_action = None
  
  def read(self, offset):
    data = self.event_list.file_entry.data
    self.offset = offset
    
    self.name = fs.read_str(data, offset, 0x20)
    self.duplicate_id = fs.read_u32(data, offset+0x20)
    self.action_index = fs.read_s32(data, offset+0x24)
    
    self.starting_flags = []
    for i in range(3):
      flag_id = fs.read_s32(data, offset+0x28+i*4)
      self.starting_flags.append(flag_id)
    
    self.flag_id_to_set = fs.read_s32(data, offset+0x34)
    self.first_property_index = fs.read_s32(data, offset+0x38)
    self.next_action_index = fs.read_s32(data, offset+0x3C)
    
    self.zero_initialized_runtime_data = fs.read_bytes(data, offset+0x40, 0x10)
    
    # These will be populated by the event list initialization function.
    self.properties = []
    self.next_action = None
  
  def save_changes(self):
    data = self.event_list.file_entry.data
    
    fs.write_str(data, self.offset, self.name, 0x20)
    fs.write_u32(data, self.offset+0x20, self.duplicate_id)
    fs.write_s32(data, self.offset+0x24, self.action_index)
    
    for i in range(3):
      flag_id = self.starting_flags[i]
      fs.write_s32(data, self.offset+0x28+i*4, flag_id)
    
    fs.write_s32(data, self.offset+0x34, self.flag_id_to_set)
    
    if len(self.properties) == 0:
      self.first_property_index = -1
    else:
      self.first_property_index = self.properties[0].property_index
    fs.write_s32(data, self.offset+0x38, self.first_property_index)
    
    if self.next_action is None:
      self.next_action_index = -1
    else:
      self.next_action_index = self.next_action.action_index
    fs.write_s32(data, self.offset+0x3C, self.next_action_index)
    
    fs.write_bytes(data, self.offset+0x40, self.zero_initialized_runtime_data)
  
  def get_prop(self, prop_name):
    return next((prop for prop in self.properties if prop.name == prop_name), None)
   
  def add_property(self, name):
    prop = Property(self.event_list)
    prop.name = name
    self.properties.append(prop)
    return prop

class Property:
  DATA_SIZE = 0x40
  
  def __init__(self, event_list):
    self.event_list = event_list
    
    self.name = None
    self.property_index = None
    self.data_type = None
    self.data_index = None
    self.data_size = None
    self.next_property_index = None
    self.zero_initialized_runtime_data = b"\0"*0xC
    self.next_property = None
    self.value = None
  
  def read(self, offset):
    data = self.event_list.file_entry.data
    self.offset = offset
    
    self.name = fs.read_str(data, offset, 0x20)
    
    self.property_index = fs.read_s32(data, offset+0x20)
    self.data_type = fs.read_u32(data, offset+0x24)
    self.data_index = fs.read_u32(data, offset+0x28)
    self.data_size = fs.read_u32(data, offset+0x2C)
    self.next_property_index = fs.read_s32(data, offset+0x30)
    
    self.zero_initialized_runtime_data = fs.read_bytes(data, offset+0x34, 0xC)
    
    # These will be populated by the event list initialization function.
    self.next_property = None
    self.value = None
  
  def save_changes(self):
    data = self.event_list.file_entry.data
    
    fs.write_str(data, self.offset, self.name, 0x20)
    fs.write_s32(data, self.offset+0x20, self.property_index)
    fs.write_u32(data, self.offset+0x24, self.data_type)
    fs.write_u32(data, self.offset+0x28, self.data_index)
    fs.write_u32(data, self.offset+0x2C, self.data_size)
    
    if self.next_property is None:
      self.next_property_index = -1
    else:
      self.next_property_index = self.next_property.property_index
    fs.write_s32(data, self.offset+0x30, self.next_property_index)
    
    fs.write_bytes(data, self.offset+0x34, self.zero_initialized_runtime_data)

try:
  from gclib.rarc import RARC
  RARC.FILE_NAME_TO_CLASS["event_list.dat"] = EventList
except ImportError:
  print(f"Could not register file name with RARC in file {__file__}")
