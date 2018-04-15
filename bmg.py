
import os
from io import BytesIO

from fs_helpers import *

class BMG:
  def __init__(self, file_entry):
    self.file_entry = file_entry
    data = self.file_entry.data
    
    self.magic = read_str(data, 0, 8)
    self.length = read_u32(data, 8)
    self.num_sections = read_u32(data, 0x0C)
    
    self.messages = []
    offset = 0x20
    for section_index in range(self.num_sections):
      section_magic = read_str(data, offset, 4)
      section_size = read_u32(data, offset+4)
      
      if section_magic == "INF1":
        num_messages = read_u16(data, offset+8)
        message_length = read_u16(data, offset+0x0A)
        for message_index in range(num_messages):
          message = Message(file_entry, offset+0x10+message_index*message_length)
          self.messages.append(message)
      elif section_magic == "DAT1":
        pass
      
      offset += section_size

class Message:
  def __init__(self, file_entry, offset):
    self.file_entry = file_entry
    data = self.file_entry.data
    self.offset = offset
    
    self.string_offset = read_u32(data, offset)
    self.message_id = read_u16(data, offset+4)
    self.item_price = read_u16(data, offset+6)
    self.next_message_id = read_u16(data, offset+8)
    
    self.text_box_type = read_u8(data, offset+0x0C)
    self.initial_draw_type = read_u8(data, offset+0x0D)
    self.text_box_position = read_u8(data, offset+0x0E)
    self.display_item_id = read_u8(data, offset+0x0F)

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
