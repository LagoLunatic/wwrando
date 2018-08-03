
from subprocess import call
import tempfile
import os
import re

from fs_helpers import *
from wwlib.yaz0_decomp import Yaz0Decompressor
from wwlib.rel import REL

def disassemble_all_code(self):
  rels_arc = self.get_arc("files/RELS.arc")
  out_dir = os.path.join(self.randomized_output_folder, "disassemble")
  if not os.path.isdir(out_dir):
    os.mkdir(out_dir)
  main_symbols = get_main_symbols(self)
  
  
  files_to_disassemble = get_list_of_all_rels(self)
  files_to_disassemble.append("sys/main.dol")
  
  for file_path in files_to_disassemble:
    basename_with_ext = os.path.basename(file_path)
    print(basename_with_ext)
    
    rel_file_entry = rels_arc.get_file_entry(basename_with_ext)
    if rel_file_entry:
      rel_file_entry.decompress_data_if_necessary()
      data = rel_file_entry.data
    else:
      data = self.gcm.read_file_data(file_path)
      if try_read_str(data, 0, 4) == "Yaz0":
        data = Yaz0Decompressor.decompress(data)
    
    basename, file_ext = os.path.splitext(basename_with_ext)
    
    is_rel = (file_ext == ".rel")
    
    
    bin_path = os.path.join(out_dir, basename_with_ext)
    with open(bin_path, "wb") as f:
      data.seek(0)
      f.write(data.read())
    
    asm_path = os.path.join(out_dir, basename + ".asm")
    
    disassemble_file(bin_path, asm_path)
    
    if is_rel:
      rel_map_data = self.gcm.read_file_data("files/maps/" + basename + ".map")
      rel_map_data.seek(0)
      rel_map_data = rel_map_data.read()
      
      # Copy the map file to the output directory
      rel_map_path = os.path.join(out_dir, basename + ".map")
      with open(rel_map_path, "wb") as f:
        f.write(rel_map_data)
      
      rel_map_data = rel_map_data.decode("ascii")
      add_relocations_and_symbols_to_rel(asm_path, bin_path, main_symbols, rel_map_data)
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
    result = call(command, stdout=f)
  if result != 0:
    raise Exception("Disassembler call failed")

def add_relocations_and_symbols_to_rel(asm_path, rel_path, main_symbols, rel_map_data):
  rel = REL(rel_path)
  replacements = {}
  replacement_offsets = {}
  for module_num, relocation_entries in rel.relocation_entries_for_module.items():
    for relocation_data_entry in relocation_entries:
      #print("Type: %X" % relocation_data_entry.relocation_type)
      curr_section = rel.sections[relocation_data_entry.curr_section_num]
      curr_section_offset = curr_section.offset
      #print(rel_name)
      replacement_location = curr_section_offset+relocation_data_entry.relocation_offset
      rounded_down_location = replacement_location & (~3) # round down to nearest 4
      #print("location of replacement: %04X" % replacement_location)
      if module_num == 0:
        #print("symbol address: %X  %s" % (relocation_data_entry.symbol_address, main_symbols.get(relocation_data_entry.symbol_address, "")))
        symbol_name = main_symbols.get(relocation_data_entry.symbol_address, "")
        replacements[rounded_down_location] = "%X  %s" % (relocation_data_entry.symbol_address, symbol_name)
      else:
        section_to_relocate_against = rel.sections[relocation_data_entry.section_num_to_relocate_against]
        section_offset_to_relocate_against = section_to_relocate_against.offset
        #print("address: %04X" % (section_offset_to_relocate_against + relocation_data_entry.symbol_address))
        #replacements[rounded_down_location] = section_offset_to_relocate_against + relocation_data_entry.symbol_address
        replacements[rounded_down_location] = "%X (%X + %X)" % (
          section_offset_to_relocate_against + relocation_data_entry.symbol_address,
          section_offset_to_relocate_against,
          relocation_data_entry.symbol_address,
        )
        replacement_offsets[rounded_down_location] = (section_offset_to_relocate_against + relocation_data_entry.symbol_address)
      #print()
  
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
  current_section_offset = None
  for line in rel_map_lines:
    section_header_match = re.search(r"^\.(text|ctors|dtors|rodata|data|bss) section layout$", line)
    if section_header_match:
      current_section_name = section_header_match.group(1)
      if current_section_name in section_name_to_section_index:
        current_section_index = section_name_to_section_index[current_section_name]
        #print(current_section_name, current_section_index, all_valid_sections)
        current_section_offset = all_valid_sections[current_section_index].offset
        if current_section_offset == 0 and current_section_name == "bss":
          current_section_index = None
          current_section_offset = None
      else:
        current_section_index = None
        current_section_offset = None
    symbol_entry_match = re.search(r"^  [0-9a-f]{8} [0-9a-f]{6} ([0-9a-f]{8})  \d (\S+)", line, re.IGNORECASE)
    if current_section_offset is not None and symbol_entry_match:
      if current_section_offset == 0:
        raise Exception("Found symbol in section with offset 0")
      symbol_offset = symbol_entry_match.group(1)
      symbol_offset = int(symbol_offset, 16)
      symbol_offset += current_section_offset
      symbol_name = symbol_entry_match.group(2)
      rel_symbol_names[symbol_offset] = symbol_name
      #print("%08X  %s" % (symbol_offset, symbol_name))
  
  #print(rel_symbol_names)
  
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
          out_str += "; SYMBOL: %X    %s\n" % (offset, symbol_name)
    
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
      else:
        branch_match = re.search(r"\s(bl|b|beq|bne|blt|bgt|ble|bge)\s+0x([0-9a-f]+)", line, re.IGNORECASE)
        if branch_match:
          branch_offset = int(branch_match.group(2), 16)
          if branch_offset in rel_symbol_names:
            symbol_name = rel_symbol_names[branch_offset]
            out_str += "      ; " + symbol_name
    
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
      
      match = re.search(r"^\s+([0-9a-f]+):\s", line, re.IGNORECASE)
      #print(match)
      if match:
        offset = int(match.group(1), 16)
        address = convert_offset_to_address(offset)
        if address in main_symbols:
          symbol_name = main_symbols[address]
          out_str += "; FUNCSTART: %08X    %s\n" % (address, symbol_name)
      
      match = re.search(r"\s(bl|b|beq|bne|blt|bgt|ble|bge)\s+0x([0-9a-f]+)", line, re.IGNORECASE)
      #print(match)
      out_str += line
      if match:
        offset = int(match.group(2), 16)
        address = convert_offset_to_address(offset)
        if address in main_symbols:
          symbol_name = main_symbols[address]
          #print(symbol_name)
          out_str += "      ; %08X    %s" % (address, symbol_name)
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

def get_main_symbols(self):
  main_symbols = {}
  framework_map_contents = self.gcm.read_file_data("files/maps/framework.map")
  framework_map_contents.seek(0)
  framework_map_contents = framework_map_contents.read().decode("ascii")
  matches = re.findall(r"^  [0-9a-f]{8} [0-9a-f]{6} ([0-9a-f]{8})  \d (\S+)", framework_map_contents, re.IGNORECASE | re.MULTILINE)
  for match in matches:
    address, name = match
    address = int(address, 16)
    main_symbols[address] = name
  return main_symbols

def convert_offset_to_address(offset):
  return offset - 0x2620 + 0x800056E0
