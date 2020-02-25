
from subprocess import call
from subprocess import DEVNULL
import tempfile
import os
import re
from io import BytesIO
from collections import OrderedDict

from fs_helpers import *
from wwlib.yaz0 import Yaz0
from wwlib.rel import REL
from paths import ASM_PATH
from tweaks import offset_to_address

def disassemble_all_code(self):
  if not os.path.isfile(r"C:\devkitPro\devkitPPC\bin\powerpc-eabi-objdump.exe"):
    raise Exception(r"Failed to disassemble code: Could not find devkitPPC. devkitPPC should be installed to: C:\devkitPro\devkitPPC")
  
  rels_arc = self.get_arc("files/RELS.arc")
  out_dir = os.path.join(self.randomized_output_folder, "disassemble")
  if not os.path.isdir(out_dir):
    os.mkdir(out_dir)
  main_symbols = get_main_symbols(self)
  
  
  all_rel_paths = get_list_of_all_rels(self)
  files_to_disassemble = all_rel_paths.copy()
  files_to_disassemble.append("sys/main.dol")
  
  for file_path_in_gcm in files_to_disassemble:
    basename_with_ext = os.path.basename(file_path_in_gcm)
    
    rel_file_entry = rels_arc.get_file_entry(basename_with_ext)
    if rel_file_entry:
      rel_file_entry.decompress_data_if_necessary()
      data = rel_file_entry.data
    else:
      data = self.gcm.read_file_data(file_path_in_gcm)
      if try_read_str(data, 0, 4) == "Yaz0":
        data = Yaz0.decompress(data)
    
    basename, file_ext = os.path.splitext(basename_with_ext)
    
    bin_path = os.path.join(out_dir, basename_with_ext)
    with open(bin_path, "wb") as f:
      data.seek(0)
      f.write(data.read())
  
  all_rels_by_path = OrderedDict()
  all_rel_symbols_by_path = OrderedDict()
  for file_path_in_gcm in all_rel_paths:
    basename_with_ext = os.path.basename(file_path_in_gcm)
    basename, file_ext = os.path.splitext(basename_with_ext)
    
    
    bin_path = os.path.join(out_dir, basename_with_ext)
    rel = REL(bin_path)
    all_rels_by_path[file_path_in_gcm] = rel
    
    
    demangled_map_path = os.path.join(ASM_PATH, "maps-out", basename + ".map.out")
    if os.path.isfile(demangled_map_path):
      with open(demangled_map_path, "rb") as f:
        rel_map_data = BytesIO(f.read())
    else:
      rel_map_data = self.gcm.read_file_data("files/maps/" + basename + ".map")
    rel_map_data.seek(0)
    rel_map_data = rel_map_data.read()
    
    # Copy the map file to the output directory
    rel_map_path = os.path.join(out_dir, basename + ".map")
    with open(rel_map_path, "wb") as f:
      f.write(rel_map_data)
    
    rel_map_data = rel_map_data.decode("ascii")
    
    all_rel_symbols_by_path[file_path_in_gcm] = get_rel_symbols(rel, rel_map_data)
  
  for file_path_in_gcm in files_to_disassemble:
    basename_with_ext = os.path.basename(file_path_in_gcm)
    print(basename_with_ext)
    
    basename, file_ext = os.path.splitext(basename_with_ext)
    
    bin_path = os.path.join(out_dir, basename_with_ext)
    asm_path = os.path.join(out_dir, basename + ".asm")
    
    disassemble_file(bin_path, asm_path)
    
    is_rel = (file_ext == ".rel")
    if is_rel:
      add_relocations_and_symbols_to_rel(asm_path, bin_path, file_path_in_gcm, main_symbols, all_rel_symbols_by_path, all_rels_by_path)
    else:
      add_symbols_to_main(asm_path, main_symbols)

def disassemble_file(bin_path, asm_path):
  command = [
    r"C:\devkitPro\devkitPPC\bin\powerpc-eabi-objdump.exe",
    "--disassemble-zeroes",
    "-m", "powerpc",
    "-D",
    "-b", "binary",
    "-EB",
    bin_path
  ]
  
  print(" ".join(command))
  print()
  with open(asm_path, "wb") as f:
    result = call(command, stdout=f, stdin=DEVNULL, stderr=DEVNULL)
  if result != 0:
    raise Exception("Disassembler call failed")

def add_relocations_and_symbols_to_rel(asm_path, rel_path, file_path_in_gcm, main_symbols, all_rel_symbols_by_path, all_rels_by_path):
  rel = all_rels_by_path[file_path_in_gcm]
  rel_symbol_names = all_rel_symbols_by_path[file_path_in_gcm]
  
  replacements = {}
  replacement_offsets = {}
  for module_num, relocation_entries in rel.relocation_entries_for_module.items():
    for relocation_data_entry in relocation_entries:
      #print("Type: %X" % relocation_data_entry.relocation_type)
      curr_section = rel.sections[relocation_data_entry.curr_section_num]
      curr_section_offset = curr_section.offset
      replacement_location = curr_section_offset+relocation_data_entry.relocation_offset
      rounded_down_location = replacement_location & (~3) # round down to nearest 4
      #print("location of replacement: %04X" % replacement_location)
      #print("module num: %02X" % module_num)
      if module_num == 0:
        #print("symbol address: %X  %s" % (relocation_data_entry.symbol_address, main_symbols.get(relocation_data_entry.symbol_address, "")))
        symbol_name = main_symbols.get(relocation_data_entry.symbol_address, "")
        replacements[rounded_down_location] = "%X  %s" % (relocation_data_entry.symbol_address, symbol_name)
      else:
        if module_num == rel.id:
          section_to_relocate_against = rel.sections[relocation_data_entry.section_num_to_relocate_against]
          section_offset_to_relocate_against = section_to_relocate_against.offset
          #print("address: %04X (%X + %X)" % (section_offset_to_relocate_against + relocation_data_entry.symbol_address, section_offset_to_relocate_against, relocation_data_entry.symbol_address))
          #print("section #%X; section offset %X" % (relocation_data_entry.section_num_to_relocate_against, section_offset_to_relocate_against))
          replacements[rounded_down_location] = "%X (%X + %X)" % (
            section_offset_to_relocate_against + relocation_data_entry.symbol_address,
            section_offset_to_relocate_against,
            relocation_data_entry.symbol_address,
          )
          replacement_offsets[rounded_down_location] = (section_offset_to_relocate_against + relocation_data_entry.symbol_address)
        else:
          other_rel, other_rel_path_in_gcm = find_rel_by_module_num(all_rels_by_path, module_num)
          other_rel_symbol_names = all_rel_symbols_by_path[other_rel_path_in_gcm]
          other_rel_name = os.path.basename(other_rel_path_in_gcm)
          
          section_to_relocate_against = other_rel.sections[relocation_data_entry.section_num_to_relocate_against]
          section_offset_to_relocate_against = section_to_relocate_against.offset
          #print("address: %04X (%X + %X)" % (section_offset_to_relocate_against + relocation_data_entry.symbol_address, section_offset_to_relocate_against, relocation_data_entry.symbol_address))
          #print("section #%X; section offset %X" % (relocation_data_entry.section_num_to_relocate_against, section_offset_to_relocate_against))
          
          relocated_offset = section_offset_to_relocate_against + relocation_data_entry.symbol_address
          symbol_name = other_rel_symbol_names.get(relocated_offset, "")
          replacements[rounded_down_location] = "%s:      %X (%X + %X)      %s" % (
            other_rel_name,
            relocated_offset,
            section_offset_to_relocate_against,
            relocation_data_entry.symbol_address,
            symbol_name,
          )
          if other_rel.bss_section_index and relocated_offset >= other_rel.fix_size:
            replacements[rounded_down_location] += "    [BSS]"
  
  
  with open(asm_path) as f:
    asm = f.read()
  out_str = ""
  for line in asm.splitlines():
    match = re.search(r"^ +([0-9a-f]+):\s.+", line)
    if match:
      word_offset = int(match.group(1), 16)
      for offset in range(word_offset, word_offset+4):
        if offset in rel_symbol_names:
          symbol_name = rel_symbol_names[offset]
          out_str += "; SYMBOL: %X    %s" % (offset, symbol_name)
          if rel.bss_section_index and offset >= rel.fix_size:
            out_str += "    [BSS symbol, value initialized at runtime]"
          out_str += "\n"
    
    out_str += line
    
    if match:
      offset = int(match.group(1), 16)
      if offset in replacements:
        out_str += "      ; "
        replacement = replacements[offset]
        out_str += replacement
        if offset in replacement_offsets:
          relocated_offset = replacement_offsets[offset]
          if relocated_offset in rel_symbol_names:
            symbol_name = rel_symbol_names[relocated_offset]
            out_str += "      " + symbol_name
            if rel.bss_section_index and relocated_offset >= rel.fix_size:
              out_str += "    [BSS]"
      else:
        branch_match = re.search(r"\s(bl|b|beq|bne|blt|bgt|ble|bge|bdnz|bdz)\s+0x([0-9a-f]+)", line, re.IGNORECASE)
        if branch_match:
          branch_offset = int(branch_match.group(2), 16)
          if branch_offset in rel_symbol_names:
            symbol_name = rel_symbol_names[branch_offset]
            out_str += "      ; " + symbol_name
            if rel.bss_section_index and branch_offset >= rel.fix_size:
              out_str += "    [BSS]"
        else:
          out_str += get_extra_comment_for_asm_line(line)
    
    out_str += "\n"
    
    if line.endswith("blr"):
      out_str += "\n" # Separate functions
  with open(asm_path, "w") as f:
    f.write(out_str)

def add_symbols_to_main(asm_path, main_symbols):
  out_str = ""
  with open(asm_path) as f:
    for line in f:
      line = line.rstrip("\r\n")
      
      match = re.search(r"^\s+([0-9a-f]+)(:\s.+)$", line, re.IGNORECASE)
      #print(match)
      if match:
        offset = int(match.group(1), 16)
        address = offset_to_address(offset)
        if address is not None:
          if address in main_symbols:
            symbol_name = main_symbols[address]
            out_str += "; SYMBOL: %08X    %s\n" % (address, symbol_name)
          
          # Convert the displayed main.dol offset to an address in RAM.
          line_after_offset = match.group(2)
          line = "%08X%s" % (address, line_after_offset)
      
      match = re.search(r"^(.+ \t(?:bl|b|beq|bne|blt|bgt|ble|bge|bdnz|bdz)\s+0x)([0-9a-f]+)$", line, re.IGNORECASE)
      #print(match)
      if match:
        line_before_offset = match.group(1)
        offset = int(match.group(2), 16)
        address = offset_to_address(offset)
        if address is not None:
          line = "%s%08X" % (line_before_offset, address)
          out_str += line
          if address in main_symbols:
            symbol_name = main_symbols[address]
            #print(symbol_name)
            out_str += "      ; %08X    %s" % (address, symbol_name)
        else:
          out_str += line
      else:
        out_str += line
        
        out_str += get_extra_comment_for_asm_line(line)
      out_str += "\n"
      if line.endswith("blr"):
        out_str += "\n" # Separate functions
  with open(asm_path, "w") as f:
    f.write(out_str)


def get_list_of_all_rels(self):
  all_rel_paths = []
  
  for file_path in self.gcm.files_by_path:
    if file_path.startswith("files/rels/"):
      all_rel_paths.append(file_path)
  
  rels_arc = self.get_arc("files/RELS.arc")
  for file_entry in rels_arc.file_entries:
    if file_entry.name.endswith(".rel"):
      all_rel_paths.append("files/rels/" + file_entry.name)
  
  return all_rel_paths

def find_rel_by_module_num(all_rels_by_path, module_num):
  for rel_path, rel in all_rels_by_path.items():
    if rel.id == module_num:
      return (rel, rel_path)
  return (None, None)

def get_main_symbols(self):
  main_symbols = {}
  demangled_map_path = os.path.join(ASM_PATH, "maps-out", "framework.map.out")
  if os.path.isfile(demangled_map_path):
    with open(demangled_map_path, "rb") as f:
      framework_map_contents = BytesIO(f.read())
  else:
    framework_map_contents = self.gcm.read_file_data("files/maps/framework.map")
  framework_map_contents.seek(0)
  framework_map_contents = framework_map_contents.read().decode("ascii")
  matches = re.findall(r"^  [0-9a-f]{8} [0-9a-f]{6} ([0-9a-f]{8})(?: +\d+)? (.+?) \t", framework_map_contents, re.IGNORECASE | re.MULTILINE)
  for match in matches:
    address, name = match
    address = int(address, 16)
    main_symbols[address] = name
  return main_symbols

def get_rel_symbols(rel, rel_map_data):
  rel_map_lines = rel_map_data.splitlines()
  found_memory_map = False
  next_section_index = 0
  section_name_to_section_index = {}
  for line in rel_map_lines:
    if line.strip() == "Memory map:":
      found_memory_map = True
    if found_memory_map:
      section_match = re.search(r"^ +\.(text|ctors|dtors|rodata|data|bss)  [0-9a-f]{8} ([0-9a-f]{8}) [0-9a-f]{8}$", line)
      if section_match:
        section_name = section_match.group(1)
        section_size = int(section_match.group(2), 16)
        if section_size > 0:
          section_name_to_section_index[section_name] = next_section_index
          next_section_index += 1
  if not found_memory_map:
    raise Exception("Failed to find memory map")
  
  rel_symbol_names = {}
  all_valid_sections = []
  for section in rel.sections:
    if section.length != 0:
      all_valid_sections.append(section)
  current_section_name = None
  current_section_index = None
  current_section = None
  for line in rel_map_lines:
    section_header_match = re.search(r"^\.(text|ctors|dtors|rodata|data|bss) section layout$", line)
    if section_header_match:
      current_section_name = section_header_match.group(1)
      if current_section_name in section_name_to_section_index:
        current_section_index = section_name_to_section_index[current_section_name]
        #print(current_section_name, current_section_index, all_valid_sections)
        current_section = all_valid_sections[current_section_index]
      else:
        current_section_index = None
        current_section = None
    symbol_entry_match = re.search(r"^  [0-9a-f]{8} [0-9a-f]{6} ([0-9a-f]{8})(?: +\d+)? (.+?) \t", line, re.IGNORECASE)
    if current_section is not None and symbol_entry_match:
      current_section_offset = current_section.offset
      if current_section_offset == 0:
        raise Exception("Found symbol in section with offset 0")
      symbol_offset = symbol_entry_match.group(1)
      symbol_offset = int(symbol_offset, 16)
      symbol_offset += current_section_offset
      symbol_name = symbol_entry_match.group(2)
      rel_symbol_names[symbol_offset] = symbol_name
      #print("%08X  %s" % (symbol_offset, symbol_name))
  
  #print(rel_symbol_names)
  
  return rel_symbol_names

def get_extra_comment_for_asm_line(line):
  comment = ""
  
  rlwinm_match = re.search(r"^.+ \t(?:rlwinm\.?)\s+(r\d+),(r\d+),(\d+),(\d+),(\d+)$", line, re.IGNORECASE)
  clrlwi_match = re.search(r"^.+ \t(?:clrlwi\.?)\s+(r\d+),(r\d+),(\d+)$", line, re.IGNORECASE)
  rotlwi_match = re.search(r"^.+ \t(?:rotlwi\.?)\s+(r\d+),(r\d+),(\d+)$", line, re.IGNORECASE)
  
  # TODO: rlwimi
  
  if rlwinm_match or clrlwi_match or rotlwi_match:
    if rlwinm_match:
      dst_reg = rlwinm_match.group(1)
      src_reg = rlwinm_match.group(2)
      l_shift = int(rlwinm_match.group(3))
      first_mask_bit = int(rlwinm_match.group(4))
      last_mask_bit = int(rlwinm_match.group(5))
    elif clrlwi_match:
      dst_reg = clrlwi_match.group(1)
      src_reg = clrlwi_match.group(2)
      l_shift = 0
      first_mask_bit = int(clrlwi_match.group(3))
      last_mask_bit = 31
    elif rotlwi_match:
      dst_reg = rotlwi_match.group(1)
      src_reg = rotlwi_match.group(2)
      l_shift = int(rotlwi_match.group(3))
      first_mask_bit = 0
      last_mask_bit = 31
    else:
      raise Exception("Unknown rlwinm opcode")
    
    if first_mask_bit <= last_mask_bit:
      mask_length = (last_mask_bit - first_mask_bit) + 1
      mask = (1 << mask_length) - 1
      mask <<= (31 - last_mask_bit)
    else:
      # Mask with a gap in the middle, but bits set at the beginning and end
      first_inverse_mask_bit = last_mask_bit + 1
      last_inverse_mask_bit = first_mask_bit - 1
      inverse_mask_length = (last_inverse_mask_bit - first_inverse_mask_bit) + 1
      inverse_mask = (1 << inverse_mask_length) - 1
      inverse_mask <<= (31 - last_inverse_mask_bit)
      mask = (~inverse_mask) & 0xFFFFFFFF
    
    # Undo the shifting operation on the mask so we can present the mask as if it was ANDed pre-shift (it's actually post-shift).
    mask = (mask >> l_shift) | (mask << (32 - l_shift))
    mask &= 0xFFFFFFFF
    
    # Represent right shifting as a negative number.
    if l_shift != 0 and first_mask_bit - l_shift >= 0:
      l_shift = -(32 - l_shift)
    
    if l_shift == 0:
      comment += "%s = (%s & 0x%08X)" % (dst_reg, src_reg, mask)
    elif l_shift < 0:
      comment += "%s = (%s & 0x%08X) >> 0x%02X" % (dst_reg, src_reg, mask, -l_shift)
    else:
      comment += "%s = (%s & 0x%08X) << 0x%02X" % (dst_reg, src_reg, mask, l_shift)
  
  if comment:
    comment = "      ; " + comment
  
  return comment
