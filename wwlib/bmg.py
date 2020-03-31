
import os
from io import BytesIO
import re

from fs_helpers import *

class BMG:
  def __init__(self, file_entry):
    self.file_entry = file_entry
    data = self.file_entry.data
    
    self.magic = read_str(data, 0, 8)
    assert self.magic == "MESGbmg1"
    self.length = read_u32(data, 8)
    self.num_sections = read_u32(data, 0x0C)
    
    self.sections = []
    offset = 0x20
    for section_index in range(self.num_sections):
      section = BMGSection(data, offset, self)
      self.sections.append(section)
      
      if section.magic == "INF1":
        self.inf1 = section
      elif section.magic == "DAT1":
        self.dat1 = section
      
      offset += section.size
    
    assert self.inf1
    assert self.dat1
    
    for message in self.messages:
      message.read_string()
  
  def save_changes(self):
    data = self.file_entry.data
    
    # Cut off the section data first since we're replacing this data entirely.
    data.truncate(0x20)
    data.seek(0x20)
    
    for section in self.sections:
      section.save_changes()
      
      section.data.seek(0)
      section_data = section.data.read()
      data.write(section_data)
  
  @property
  def messages(self):
    return self.inf1.messages
  
  @messages.setter
  def messages(self, value):
    self.inf1.messages = value
  
  @property
  def messages_by_id(self):
    return self.inf1.messages_by_id
  
  @messages_by_id.setter
  def messages_by_id(self, value):
    self.inf1.messages_by_id = value
  
  @property
  def add_new_message(self):
    return self.inf1.add_new_message

class BMGSection:
  def __init__(self, bmg_data, section_offset, bmg):
    self.bmg = bmg
    
    self.magic = read_str(bmg_data, section_offset, 4)
    self.size = read_u32(bmg_data, section_offset+4)
    
    bmg_data.seek(section_offset)
    self.data = BytesIO(bmg_data.read(self.size))
    
    if self.magic == "INF1":
      self.read_inf1()
  
  def save_changes(self):
    if self.magic == "INF1":
      self.save_inf1()
    
    # Pad the size of this section to the next 0x20 bytes.
    align_data_to_nearest(self.data, 0x20)
    
    self.size = data_len(self.data)
    write_magic_str(self.data, 0, self.magic, 4)
    write_u32(self.data, 4, self.size)
  
  def read_inf1(self):
    self.messages = []
    self.messages_by_id = {}
    
    num_messages = read_u16(self.data, 8)
    message_length = read_u16(self.data, 0x0A)
    for message_index in range(num_messages):
      message = Message(self.data, self.bmg)
      message.read(0x10+message_index*message_length)
      self.messages.append(message)
      self.messages_by_id[message.message_id] = message
  
  def save_inf1(self):
    num_messages = len(self.messages)
    write_u16(self.data, 8, num_messages)
    
    message_length = read_u16(self.data, 0x0A)
    next_message_offset = 0x10
    next_string_offset = 9
    self.data.truncate(next_message_offset)
    self.data.seek(next_message_offset)
    self.bmg.dat1.data.truncate(next_string_offset)
    self.bmg.dat1.data.seek(next_string_offset)
    for message in self.messages:
      message.offset = next_message_offset
      message.string_offset = next_string_offset
      message.save_changes()
      
      next_message_offset += message_length
      next_string_offset += message.encoded_string_length
  
  def add_new_message(self, message_id):
    if message_id in self.messages_by_id:
      raise Exception("Tried to add a new message with ID %d, but a message with that ID already exists" % message_id)
    
    message = Message(self.data, self.bmg)
    message.message_id = message_id
    
    self.messages.append(message)
    self.messages_by_id[message.message_id] = message
    
    return message
  
class Message:
  def __init__(self, data, bmg):
    self.data = data
    self.bmg = bmg
    
    self.string_offset = None
    self.message_id = None
    self.item_price = 0
    self.next_message_id = 0
    
    self.unknown_1 = 0x60
    
    self.text_box_type = 0
    self.initial_draw_type = 0
    self.text_box_position = 3
    self.display_item_id = 0xFF
    self.text_alignment = 0
    
    self.initial_sound = 0
    self.initial_camera_behavior = 0
    self.initial_speaker_anim = 0
    
    self.unknown_3 = 0
    
    self.num_lines_per_box = 4
    
    self.unknown_4 = 0
  
  def read(self, offset):
    self.offset = offset
    
    data = self.data
    
    self.string_offset = read_u32(data, offset)
    self.message_id = read_u16(data, offset+4)
    self.item_price = read_u16(data, offset+6)
    self.next_message_id = read_u16(data, offset+8)
    self.unknown_1 = read_u16(data, offset+0x0A)
    
    self.text_box_type = read_u8(data, offset+0x0C)
    self.initial_draw_type = read_u8(data, offset+0x0D)
    self.text_box_position = read_u8(data, offset+0x0E)
    self.display_item_id = read_u8(data, offset+0x0F)
    
    self.text_alignment = read_u8(data, offset+0x10)
    self.initial_sound = read_u8(data, offset+0x11)
    self.initial_camera_behavior = read_u8(data, offset+0x12)
    self.initial_speaker_anim = read_u8(data, offset+0x13)
    
    self.unknown_3 = read_u8(data, offset+0x14)
    self.num_lines_per_box = read_u16(data, offset+0x15)
    self.unknown_4 = read_u8(data, offset+0x17)
    
    self.string = None # Will be set after all messages are read.
  
  def save_changes(self):
    data = self.data
    
    write_u32(data, self.offset, self.string_offset)
    write_u16(data, self.offset+4, self.message_id)
    write_u16(data, self.offset+6, self.item_price)
    write_u16(data, self.offset+8, self.next_message_id)
    write_u16(data, self.offset+0x0A, self.unknown_1)
    
    write_u8(data, self.offset+0x0C, self.text_box_type)
    write_u8(data, self.offset+0x0D, self.initial_draw_type)
    write_u8(data, self.offset+0x0E, self.text_box_position)
    write_u8(data, self.offset+0x0F, self.display_item_id)
    
    write_u8(data, self.offset+0x10, self.text_alignment)
    write_u8(data, self.offset+0x11, self.initial_sound)
    write_u8(data, self.offset+0x12, self.initial_camera_behavior)
    write_u8(data, self.offset+0x13, self.initial_speaker_anim)
    
    write_u8(data, self.offset+0x14, self.unknown_3)
    write_u16(data, self.offset+0x15, self.num_lines_per_box)
    write_u8(data, self.offset+0x17, self.unknown_4)
    
    self.write_string()
  
  def read_string(self):
    string_pool_data = self.bmg.dat1.data
    
    self.string = ""
    initial_byte_offset = 8 + self.string_offset
    byte_offset = initial_byte_offset
    
    byte = read_u8(string_pool_data, byte_offset)
    byte_offset += 1
    while byte != 0:
      if byte == 0x1A:
        # Control code.
        control_code_size = read_u8(string_pool_data, byte_offset)
        byte_offset += 1
        
        self.string += "\\{%02X %02X" % (byte, control_code_size)
        
        for i in range(control_code_size-2):
          control_code_data_byte = read_u8(string_pool_data, byte_offset)
          byte_offset += 1
          self.string += " %02X" % control_code_data_byte
        self.string += "}"
      else:
        # Normal character.
        self.string += chr(byte)
      
      byte = read_u8(string_pool_data, byte_offset)
      byte_offset += 1
    
    self.encoded_string_length = byte_offset - initial_byte_offset
  
  def write_string(self):
    data = self.data
    
    is_escaped_char = False
    index_in_str = 0
    bytes_to_write = []
    while index_in_str < len(self.string):
      char = self.string[index_in_str]
      if char == "\\":
        is_escaped_char = True
        index_in_str += 1
        continue
      
      if is_escaped_char and char == "{":
        substr = self.string[index_in_str:]
        control_code_str_len = substr.index("}") - 1
        substr = substr[1:control_code_str_len+1]
        
        control_code_byte_strs = re.findall(r"[0-9a-f]+", substr, re.IGNORECASE)
        for control_code_byte_str in control_code_byte_strs:
          byte = int(control_code_byte_str, 16)
          assert 0 <= byte <= 255
          bytes_to_write.append(byte)
        
        index_in_str += (2 + control_code_str_len)
        continue
      
      byte = ord(char)
      bytes_to_write.append(byte)
      
      index_in_str += 1
    bytes_to_write.append(0)
    
    self.encoded_string_length = len(bytes_to_write)
    
    string_pool_data = self.bmg.dat1.data
    str_start_offset = 8 + self.string_offset
    write_and_pack_bytes(string_pool_data, str_start_offset, bytes_to_write, "B"*len(bytes_to_write))
