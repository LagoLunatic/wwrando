
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
    
    self.messages = []
    self.messages_by_id = {}
    self.string_pool_offset = None
    offset = 0x20
    for section_index in range(self.num_sections):
      section_magic = read_str(data, offset, 4)
      section_size = read_u32(data, offset+4)
      
      if section_magic == "INF1":
        num_messages = read_u16(data, offset+8)
        message_length = read_u16(data, offset+0x0A)
        for message_index in range(num_messages):
          message = Message(file_entry, offset+0x10+message_index*message_length, self)
          self.messages.append(message)
          self.messages_by_id[message.message_id] = message
      elif section_magic == "DAT1":
        self.string_pool_offset = offset+8
      
      offset += section_size
    
    assert self.string_pool_offset
    
    for message in self.messages:
      message.read_string()

class Message:
  def __init__(self, file_entry, offset, bmg):
    self.file_entry = file_entry
    data = self.file_entry.data
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
    data = self.file_entry.data
    
    self.string = ""
    byte_offset = self.bmg.string_pool_offset+self.string_offset
    
    byte = read_u8(data, byte_offset)
    byte_offset += 1
    while byte != 0:
      if byte == 0x1A:
        # Control code.
        control_code_size = read_u8(data, byte_offset)
        byte_offset += 1
        
        self.string += "\\{%02X %02X" % (byte, control_code_size)
        
        for i in range(control_code_size-2):
          contrl_code_data_byte = read_u8(data, byte_offset)
          byte_offset += 1
          self.string += " %02X" % contrl_code_data_byte
        self.string += "}"
      else:
        # Normal character.
        self.string += chr(byte)
      
      byte = read_u8(data, byte_offset)
      byte_offset += 1
    
    self.original_string_length = byte_offset
  
  def save_changes(self):
    data = self.file_entry.data
    
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
    data = self.file_entry.data
    
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
          print(byte)
          print(substr)
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
    
    str_start_offset = self.bmg.string_pool_offset+self.string_offset
    write_and_pack_bytes(data, str_start_offset, bytes_to_write, "B"*len(bytes_to_write))
