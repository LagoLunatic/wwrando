
import struct
from fs_helpers import *

class Yaz0Decompressor:
  def decompress(comp_data):
    if read_str(comp_data, 0, 4) != "Yaz0":
      print("File is not compressed.")
      return comp_data
    
    uncomp_size = read_u32(comp_data, 4)
    comp_size = comp_data.seek(0, 2)
    
    comp = read_bytes(comp_data, 0, comp_size, "B"*comp_size)
    
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
    
    return uncomp_data
