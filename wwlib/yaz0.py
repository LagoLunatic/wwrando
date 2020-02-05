
import struct
from io import BytesIO

from fs_helpers import *

class Yaz0:
  MAX_RUN_LENGTH = 0xFF + 0x12
  
  num_bytes_1 = 0
  match_pos = 0
  prev_flag = False
  
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
  def compress(uncomp_data):
    comp_data = BytesIO()
    write_str(comp_data, 0, "Yaz0", 4)
    
    uncomp_size = data_len(uncomp_data)
    write_u32(comp_data, 4, uncomp_size)
    
    write_u32(comp_data, 8, 0)
    write_u32(comp_data, 0xC, 0)
    
    Yaz0.num_bytes_1 = 0
    Yaz0.match_pos = 0
    Yaz0.prev_flag = False
    
    uncomp_offset = 0
    uncomp = read_and_unpack_bytes(uncomp_data, 0, uncomp_size, "B"*uncomp_size)
    comp_offset = 0x10
    dst = []
    valid_bit_count = 0
    curr_code_byte = 0
    while uncomp_offset < uncomp_size:
      num_bytes, match_pos = Yaz0.get_num_bytes_and_match_pos(uncomp, uncomp_offset)
      
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
          byte = (((num_bytes - 2) << 4) | (dist >> 8) & 0xFF)
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
    
    return comp_data
  
  @staticmethod
  def get_num_bytes_and_match_pos(uncomp, uncomp_offset):
    num_bytes = 1
    
    if Yaz0.prev_flag:
      Yaz0.prev_flag = False
      return (Yaz0.num_bytes_1, Yaz0.match_pos)
    
    Yaz0.prev_flag = False
    num_bytes, Yaz0.match_pos = Yaz0.simple_rle_encode(uncomp, uncomp_offset)
    match_pos = Yaz0.match_pos
    
    if num_bytes >= 3:
      Yaz0.num_bytes_1, Yaz0.match_pos = Yaz0.simple_rle_encode(uncomp, uncomp_offset+1)
      
      if Yaz0.num_bytes_1 >= num_bytes+2:
        num_bytes = 1
        Yaz0.prev_flag = True
    
    return (num_bytes, match_pos)
  
  @staticmethod
  def simple_rle_encode(uncomp, uncomp_offset):
    # How far back to search. Can search as far back as 0x1000 bytes, but the farther back we search the slower it is.
    start_offset = uncomp_offset - 0x400
    if start_offset < 0:
      start_offset = 0
    
    num_bytes = 1
    match_pos = 0
    
    for i in range(start_offset, uncomp_offset):
      for j in range(len(uncomp) - uncomp_offset):
        if uncomp[i + j] != uncomp[uncomp_offset + j]:
          break
        #if j == Yaz0.MAX_RUN_LENGTH:
        #  break
      
      if j > num_bytes:
        num_bytes = j
        match_pos = i
        
        #if num_bytes == Yaz0.MAX_RUN_LENGTH:
        #  break
    
    #if num_bytes == 2:
    #  num_bytes = 1
    
    return (num_bytes, match_pos)
