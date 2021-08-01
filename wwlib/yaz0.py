
import struct
from io import BytesIO

from fs_helpers import *

class Yaz0:
  MAX_RUN_LENGTH = 0xFF + 0x12
  
  # How far back to search when compressing.
  # Can search as far back as 0x1000 bytes, but the farther back we search the slower it is.
  DEFAULT_SEARCH_DEPTH = 0x1000
  
  # Variables to hold the reserved next match across loops.
  next_num_bytes = 0
  next_match_pos = 0
  next_flag = False
  
  @staticmethod
  def check_is_compressed(comp_data):
    if try_read_str(comp_data, 0, 4) != "Yaz0":
      return False
    
    return True
  
  @staticmethod
  def decompress(comp_data):
    if try_read_str(comp_data, 0, 4) != "Yaz0":
      print("File is not compressed.")
      return comp_data
    
    uncomp_size = read_u32(comp_data, 4)
    comp_size = comp_data.seek(0, 2)
    
    comp = read_and_unpack_bytes(comp_data, 0, comp_size, "B"*comp_size)
    
    output = []
    output_len = 0
    src_offset = 0x10
    valid_bit_count = 0
    curr_code_byte = 0
    while output_len < uncomp_size:
      if valid_bit_count == 0:
        curr_code_byte = comp[src_offset]
        src_offset += 1
        valid_bit_count = 8
      
      if curr_code_byte & 0x80 != 0:
        output.append(comp[src_offset])
        src_offset += 1
        output_len += 1
      else:
        byte1 = comp[src_offset]
        byte2 = comp[src_offset+1]
        src_offset += 2
        
        dist = ((byte1&0xF) << 8) | byte2
        copy_src_offset = output_len - (dist + 1)
        num_bytes = (byte1 >> 4)
        if num_bytes == 0:
          num_bytes = comp[src_offset] + 0x12
          src_offset += 1
        else:
          num_bytes += 2
        
        for i in range(0, num_bytes):
          output.append(output[copy_src_offset])
          output_len += 1
          copy_src_offset += 1
      
      curr_code_byte = (curr_code_byte << 1)
      valid_bit_count -= 1
    
    uncomp_data = struct.pack("B"*output_len, *output)
    
    return BytesIO(uncomp_data)
  
  @staticmethod
  def compress(uncomp_data, search_depth=DEFAULT_SEARCH_DEPTH, should_pad_data=False):
    comp_data = BytesIO()
    write_magic_str(comp_data, 0, "Yaz0", 4)
    
    uncomp_size = data_len(uncomp_data)
    write_u32(comp_data, 4, uncomp_size)
    
    write_u32(comp_data, 8, 0)
    write_u32(comp_data, 0xC, 0)
    
    Yaz0.next_num_bytes = 0
    Yaz0.next_match_pos = None
    Yaz0.next_flag = False
    
    uncomp_offset = 0
    uncomp = read_and_unpack_bytes(uncomp_data, 0, uncomp_size, "B"*uncomp_size)
    comp_offset = 0x10
    dst = []
    valid_bit_count = 0
    curr_code_byte = 0
    while uncomp_offset < uncomp_size:
      num_bytes, match_pos = Yaz0.get_num_bytes_and_match_pos(uncomp, uncomp_offset, search_depth=search_depth)
      
      if num_bytes < 3:
        # Copy the byte directly
        dst.append(uncomp[uncomp_offset])
        uncomp_offset += 1
        
        curr_code_byte |= (0x80 >> valid_bit_count)
      else:
        dist = (uncomp_offset - match_pos - 1)
        
        if num_bytes >= 0x12:
          dst.append((dist & 0xFF00) >> 8)
          dst.append((dist & 0x00FF))
          
          if num_bytes > Yaz0.MAX_RUN_LENGTH:
            num_bytes = Yaz0.MAX_RUN_LENGTH
          dst.append(num_bytes - 0x12)
        else:
          byte = (((num_bytes - 2) << 4) | (dist >> 8) & 0x0F)
          dst.append(byte)
          dst.append(dist & 0xFF)
        
        uncomp_offset += num_bytes
      
      valid_bit_count += 1
      
      if valid_bit_count == 8:
        # Finished 8 codes, so write this block
        write_u8(comp_data, comp_offset, curr_code_byte)
        comp_offset += 1
        
        for byte in dst:
          write_u8(comp_data, comp_offset, byte)
          comp_offset += 1
        
        curr_code_byte = 0
        valid_bit_count = 0
        dst = []
    
    if valid_bit_count > 0:
      # Still some codes leftover that weren't written yet, so write them now.
      write_u8(comp_data, comp_offset, curr_code_byte)
      comp_offset += 1
      
      for byte in dst:
        write_u8(comp_data, comp_offset, byte)
        comp_offset += 1
    else:
      # If there are no codes leftover to be written, we instead write a single zero at the end for some reason.
      # I don't think it's necessary in practice, but we do it for maximum accuracy with the original algorithm.
      write_u8(comp_data, comp_offset, 0)
      comp_offset += 1
    
    if should_pad_data:
      align_data_to_nearest(comp_data, 0x20, padding_bytes=b'\0')
    
    return comp_data
  
  @staticmethod
  def get_num_bytes_and_match_pos(uncomp, uncomp_offset, search_depth=DEFAULT_SEARCH_DEPTH):
    num_bytes = 1
    
    if Yaz0.next_flag:
      Yaz0.next_flag = False
      return (Yaz0.next_num_bytes, Yaz0.next_match_pos)
    
    Yaz0.next_flag = False
    num_bytes, match_pos = Yaz0.simple_rle_encode(uncomp, uncomp_offset, search_depth=search_depth)
    
    if num_bytes >= 3:
      # Check if the next byte has a match that would compress better than the current byte.
      Yaz0.next_num_bytes, Yaz0.next_match_pos = Yaz0.simple_rle_encode(uncomp, uncomp_offset+1, search_depth=search_depth)
      
      if Yaz0.next_num_bytes >= num_bytes+2:
        # If it does, then only copy one byte for this match and reserve the next match for later so we save more space.
        num_bytes = 1
        match_pos = None
        Yaz0.next_flag = True
    
    return (num_bytes, match_pos)
  
  @staticmethod
  def simple_rle_encode(uncomp, uncomp_offset, search_depth=DEFAULT_SEARCH_DEPTH):
    start_offset = uncomp_offset - search_depth
    if start_offset < 0:
      start_offset = 0
    
    num_bytes = 0
    match_pos = None
    max_num_bytes_to_check = len(uncomp) - uncomp_offset
    if max_num_bytes_to_check > Yaz0.MAX_RUN_LENGTH:
      max_num_bytes_to_check = Yaz0.MAX_RUN_LENGTH
    
    for possible_match_pos in range(start_offset, uncomp_offset):
      for index_in_match in range(max_num_bytes_to_check):
        if uncomp[possible_match_pos + index_in_match] != uncomp[uncomp_offset + index_in_match]:
          break
        
        num_bytes_matched = index_in_match + 1
        if num_bytes_matched > num_bytes:
          num_bytes = num_bytes_matched
          match_pos = possible_match_pos
    
    return (num_bytes, match_pos)
