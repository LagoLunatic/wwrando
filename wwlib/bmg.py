
import os
from io import BytesIO
import re

from fs_helpers import *

class BMG:
  def __init__(self, file_entry):
    self.file_entry = file_entry
    data = self.file_entry.data
    
    self.magic = read_str(data, 0, 8)
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
    # Pad the size of this section to the next 0x20 bytes.
    align_data_to_nearest(self.data, 0x20)
    
    self.size = data_len(self.data)
    write_str(self.data, 0, self.magic, 4)
    write_u32(self.data, 4, self.size)
  
  def read_inf1(self):
    self.messages = []
    self.messages_by_id = {}
    
    num_messages = read_u16(self.data, 8)
    message_length = read_u16(self.data, 0x0A)
    for message_index in range(num_messages):
      message = Message(self.data, 0x10+message_index*message_length, self.bmg)
      self.messages.append(message)
      self.messages_by_id[message.message_id] = message
  
class Message:
  def __init__(self, data, offset, bmg):
    self.data = data
    self.offset = offset
    self.bmg = bmg
    
    self.string_offset = read_u32(data, offset)
    self.message_id = read_u16(data, offset+4)
    self.item_price = read_u16(data, offset+6)
    self.next_message_id = read_u16(data, offset+8)
    
    self.text_box_type = read_u8(data, offset+0x0C)
    self.initial_draw_type = read_u8(data, offset+0x0D)
    self.text_box_position = read_u8(data, offset+0x0E)
    self.display_item_id = read_u8(data, offset+0x0F)
    
    self.string = None # Will be set after all messages are read.
  
  def read_string(self):
    string_pool_data = self.bmg.dat1.data
    
    self.string = ""
    byte_offset = 8 + self.string_offset
    
    byte = read_u8(string_pool_data, byte_offset)
    byte_offset += 1
    while byte != 0:
      if byte == 0x1A:
        # Control code.
        control_code_size = read_u8(string_pool_data, byte_offset)
        byte_offset += 1
        
        self.string += "\\{%02X %02X" % (byte, control_code_size)
        
        for i in range(control_code_size-2):
          contrl_code_data_byte = read_u8(string_pool_data, byte_offset)
          byte_offset += 1
          self.string += " %02X" % contrl_code_data_byte
        self.string += "}"
      else:
        # Normal character.
        self.string += chr(byte)
      
      byte = read_u8(string_pool_data, byte_offset)
      byte_offset += 1
    
    self.original_string_length = byte_offset
  
  def save_changes(self):
    data = self.data
    
    write_u32(data, self.offset, self.string_offset)
    write_u16(data, self.offset+4, self.message_id)
    write_u16(data, self.offset+6, self.item_price)
    write_u16(data, self.offset+8, self.next_message_id)
    
    write_u8(data, self.offset+0x0C, self.text_box_type)
    write_u8(data, self.offset+0x0D, self.initial_draw_type)
    write_u8(data, self.offset+0x0E, self.text_box_position)
    write_u8(data, self.offset+0x0F, self.display_item_id)
    
    self.write_string()
  
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
    
    if len(bytes_to_write) > self.original_string_length:
      raise Exception("Length of string was increased")
    
    string_pool_data = self.bmg.dat1.data
    str_start_offset = 8 + self.string_offset
    write_and_pack_bytes(string_pool_data, str_start_offset, bytes_to_write, "B"*len(bytes_to_write))
