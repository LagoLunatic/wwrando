#!/usr/bin/python3

import glob
import re
from subprocess import call
import os
import tempfile
import shutil
import struct
import yaml
import traceback
import sys

asm_dir = os.path.dirname(__file__)

sys.path.insert(0, asm_dir + "/../gclib")
from gclib import fs_helpers as fs
from elf import ELF, ELFSectionType, ELFRelocationType, ELFSectionFlags, ElfSymbolBinding

if sys.platform == "win32":
  devkitbasepath = r"C:\devkitPro\devkitPPC\bin"
else:
  if "DEVKITPPC" not in os.environ:
    raise Exception(r"Could not find devkitPPC. Path to devkitPPC should be in the DEVKITPPC env var")
  devkitbasepath = os.environ.get("DEVKITPPC") + "/bin"

def get_bin(name):
  if sys.platform != "win32":
    return os.path.join(devkitbasepath, name)
  return os.path.join(devkitbasepath, name + ".exe")

if not os.path.isfile(get_bin("powerpc-eabi-as")):
  raise Exception(r"Failed to assemble code: Could not find devkitPPC. devkitPPC should be installed to: C:\devkitPro\devkitPPC")

# Change how yaml dumps lists so each element isn't on a separate line.
yaml.Dumper.add_representer(
  list,
  lambda dumper, data: dumper.represent_sequence(u'tag:yaml.org,2002:seq', data, flow_style=True)
)

# Output integers as hexadecimal.
yaml.Dumper.add_representer(
  int,
  lambda dumper, data: yaml.ScalarNode('tag:yaml.org,2002:int', "0x%02X" % data)
)

temp_dir = tempfile.mkdtemp()
print(temp_dir)
print()

custom_symbols = {}
custom_symbols["sys/main.dol"] = {}

with open(asm_dir + "/free_space_start_offsets.txt", "r") as f:
  free_space_start_offsets = yaml.safe_load(f)

next_free_space_offsets = {}
for file_path, offset in free_space_start_offsets.items():
  next_free_space_offsets[file_path] = offset

def parse_includes(asm):
  asm_with_includes = ""
  for line in asm.splitlines():
    include_match = re.search(r"^\s*\.include\s+\"([^\"]+)\"\s*$", line, re.IGNORECASE)
    if include_match:
      relative_file_path = include_match.group(1)
      file_path = os.path.join(asm_dir, relative_file_path)
      
      file_ext = os.path.splitext(file_path)[1]
      if file_ext == ".asm":
        with open(file_path) as f:
          included_file_contents = f.read()
        included_asm = included_file_contents
        included_asm = parse_includes(included_asm) # Parse recursive includes
      elif file_ext == ".c":
        included_asm = compile_c_to_asm(file_path)
      else:
        raise Exception("Included file with unknown extension: %s" % relative_file_path)
      
      asm_with_includes += included_asm + "\n"
      asm_with_includes += ".section \".text\"\n"
    else:
      asm_with_includes += line + "\n"
  
  return asm_with_includes

def make_compiled_c_asm_more_readable(compiled_asm):
  # Change the formatting of ASM output by GCC to match my ASM style (register names, hex numbers, spacing, etc).
  readable_asm = ""
  for line in compiled_asm.splitlines():
    pieces = []
    for piece in re.split(r"(\s|,|\(|\)|\"[^\"]+\")", line):
      if piece and piece[0] not in ['"', "'"]: # Don't modify strings
        piece = re.sub(r"%((?:r|f|cr)\d+)", "\\1", piece)
        piece = re.sub(r"\b(\d+)\b", lambda match: "0x%X" % int(match.group(1)), piece)
        piece = re.sub(r",", ", ", piece)
        piece = re.sub(r"\(", " (", piece)
        if piece == "r1":
          piece = "sp"
      pieces.append(piece)
    line = ''.join(pieces)
    readable_asm += line + "\n"
  return readable_asm

def compile_c_to_asm(c_src_path):
  basename = os.path.basename(c_src_path)
  basename_no_ext = os.path.splitext(basename)[0]
  asm_path = os.path.join(temp_dir, basename_no_ext + ".asm")
  command = [
    get_bin("powerpc-eabi-gcc"),
    "-mcpu=750",
    "-fno-inline",
    "-Wall",
    "-Werror",
    "-Og",
    "-fshort-enums",
    "-mregnames",
    "-S",
    "-fno-asynchronous-unwind-tables", # Needed to get rid of unnecessary .eh_frame section from the ELF.
    "-c", c_src_path,
    "-o", asm_path,
  ]
  print(" ".join(command))
  print()
  result = call(command)
  if result != 0:
    raise Exception("Compiler call failed")
  
  with open(asm_path) as f:
    compiled_asm = f.read()
  
  # Uncomment the below to debug the compiled ASM.
  #readable_asm = make_compiled_c_asm_more_readable(compiled_asm)
  #with open("compiled_c_asm - %s.asm" % basename_no_ext, "w") as f:
  #  f.write(readable_asm)
  
  return compiled_asm

def get_code_and_relocations_from_elf(bin_name):
  elf = ELF()
  elf.read_from_file(bin_name)
  
  relocations_in_elf = []
  
  for elf_section in elf.sections:
    # TODO: Maybe support multiple sections, not just .text, such as .data?
    found_text_section = False
    if elf_section.name == ".text":
      assert not found_text_section
      found_text_section = True
      # Get the code and overwrite the ELF file with just the raw binary code.
      with open(bin_name, "wb") as f:
        f.write(fs.read_all_bytes(elf_section.data))
    elif elf_section.type == ELFSectionType.SHT_RELA:
      # Get the relocations.
      assert elf_section.name.startswith(".rela")
      relocated_section_name = elf_section.name[len(".rela"):]
      assert relocated_section_name == ".text"
      
      for elf_relocation in elf.relocations[elf_section.name]:
        elf_symbol = elf.symbols[".symtab"][elf_relocation.symbol_index]
        is_local_relocation = try_apply_local_relocation(bin_name, elf_relocation, elf_symbol)
        
        if not is_local_relocation:
          relocations_in_elf.append({
            "SymbolName": elf_symbol.name,
            "Offset"    : elf_relocation.relocation_offset,
            "Type"      : elf_relocation.type.name,
          })
  
  return relocations_in_elf

def try_apply_local_relocation(bin_name, elf_relocation, elf_symbol):
  branch_label_match = re.search(r"^branch_label_([0-9A-F]+)$", elf_symbol.name, re.IGNORECASE)
  if branch_label_match:
    # We should relocate the relative branches within this REL ourselves so the game doesn't need to do it at runtime.
    branch_src_offset = org_offset + elf_relocation.relocation_offset
    branch_dest_offset = int(branch_label_match.group(1), 16)
    relative_branch_offset = ((branch_dest_offset - branch_src_offset) // 4) << 2
    
    if elf_relocation.type == ELFRelocationType.R_PPC_REL24:
      if relative_branch_offset > 0x1FFFFFF or relative_branch_offset < -0x2000000:
        raise Exception("Relocation failed: Cannot branch from %X to %X with a 24-bit relative offset." % (branch_src_offset, branch_dest_offset))
      
      with open(bin_name, "r+b") as f:
        instruction = fs.read_u32(f, elf_relocation.relocation_offset)
        instruction &= ~0x03FFFFFC
        instruction |= relative_branch_offset & 0x03FFFFFC
        fs.write_u32(f, elf_relocation.relocation_offset, instruction)
      
      return True
    elif elf_relocation.type == ELFRelocationType.R_PPC_REL14:
      if relative_branch_offset > 0x7FFF or relative_branch_offset < -0x8000:
        raise Exception("Relocation failed: Cannot branch from %X to %X with a 14-bit relative offset." % (branch_src_offset, branch_dest_offset))
      
      with open(bin_name, "r+b") as f:
        instruction = fs.read_u32(f, elf_relocation.relocation_offset)
        instruction &= ~0x0000FFFC
        instruction |= relative_branch_offset & 0x0000FFFC
        fs.write_u32(f, elf_relocation.relocation_offset, instruction)
      
      return True
  
  if elf_relocation.type == ELFRelocationType.R_PPC_ADDR32:
    # Also relocate absolute pointers into main.dol.
    
    with open(bin_name, "r+b") as f:
      fs.write_u32(f, elf_relocation.relocation_offset, elf_symbol.address)
    
    return True
  
  return False

try:
  # First delete any old patch diffs.
  for diff_path in glob.glob(glob.escape(asm_dir) + "/asm/patch_diffs/*_diff.txt"):
    os.remove(diff_path)
  
  with open(asm_dir + "/linker.ld") as f:
    linker_script = f.read()
  
  with open(asm_dir + "/asm_macros.asm") as f:
    asm_macros = f.read()
  
  all_asm_file_paths = glob.glob(glob.escape(asm_dir) + "/patches/*.asm")
  all_asm_files = [os.path.basename(asm_path) for asm_path in all_asm_file_paths]
  all_asm_files.sort()
  # Always put the custom data and funcs first so their custom symbols are defined for all the other patches to use.
  all_asm_files.remove("custom_data.asm")
  all_asm_files.remove("custom_funcs.asm")
  all_asm_files = ["custom_data.asm", "custom_funcs.asm"] + all_asm_files
  
  # First parse all the asm files into code chunks.
  code_chunks = {}
  local_branches_linker_script_for_file = {}
  next_free_space_id_for_file = {}
  constant_definitions = ""
  for patch_filename in all_asm_files:
    print("Assembling " + patch_filename)
    patch_path = os.path.join(asm_dir, "patches", patch_filename)
    with open(patch_path) as f:
      asm = f.read()
    
    asm_with_includes = parse_includes(asm)
    #print(asm_with_includes)
    
    patch_name = os.path.splitext(patch_filename)[0]
    code_chunks[patch_name] = {}
    
    most_recent_file_path = None
    most_recent_org_offset = None
    for line in asm_with_includes.splitlines():
      line = re.sub(r";.+$", "", line)
      line = line.strip()
      
      open_file_match = re.search(r"^\s*\.open\s+\"([^\"]+)\"$", line, re.IGNORECASE)
      org_match = re.search(r"^\s*\.org\s+0x([0-9a-f]+)(?:,\s\.area\s+0x([0-9a-f]+))?$", line, re.IGNORECASE)
      org_symbol_match = re.search(r"^\s*\.org\s+([\._a-z][\._a-z0-9]+|@NextFreeSpace)(?:,\s\.area\s+0x([0-9a-f]+))?$", line, re.IGNORECASE)
      branch_match = re.search(r"^\s*(?:b|beq|bne|blt|bgt|ble|bge)\s+0x([0-9a-f]+)(?:$|\s)", line, re.IGNORECASE)
      if open_file_match:
        relative_file_path = open_file_match.group(1)
        if most_recent_file_path or most_recent_org_offset is not None:
          raise Exception("File %s was not closed before opening new file %s" % (most_recent_file_path, relative_file_path))
        if relative_file_path not in code_chunks[patch_name]:
          code_chunks[patch_name][relative_file_path] = {}
        if relative_file_path not in local_branches_linker_script_for_file:
          local_branches_linker_script_for_file[relative_file_path] = ""
        most_recent_file_path = relative_file_path
        continue
      elif org_match:
        if not most_recent_file_path:
          raise Exception("Found .org directive when no file was open")
        
        org_offset = int(org_match.group(1), 16)
        area_size = org_match.group(2)
        if area_size is not None:
          area_size = int(area_size, 16)
        
        if org_offset >= free_space_start_offsets[most_recent_file_path]:
          raise Exception(
            f"Tried to manually set the origin point to after the start of free space.\n"
            f".org offset: 0x{org_offset:X}\n"
            f"File path: {most_recent_file_path}\n\n"
            f"Use \".org @NextFreeSpace\" instead to get an automatically assigned free space offset."
          )
        if org_offset in code_chunks[patch_name][most_recent_file_path]:
          raise Exception(f"Duplicate .org offset.\n.org offset: 0x{org_offset:X}\nFile path: {most_recent_file_path}")
        
        code_chunks[patch_name][most_recent_file_path][org_offset] = {
          "area_size": area_size,
          "temp_asm": "",
        }
        most_recent_org_offset = org_offset
        continue
      elif org_symbol_match:
        if not most_recent_file_path:
          raise Exception("Found .org directive when no file was open")
        
        org_symbol = org_symbol_match.group(1)
        area_size = org_symbol_match.group(2)
        if area_size is not None:
          area_size = int(area_size, 16)
        
        if org_symbol == "@NextFreeSpace":
          # Need to make each instance of @NextFreeSpace into a unique label.
          if most_recent_file_path not in next_free_space_id_for_file:
            next_free_space_id_for_file[most_recent_file_path] = 1
          org_symbol = "@FreeSpace_%d" % next_free_space_id_for_file[most_recent_file_path]
          next_free_space_id_for_file[most_recent_file_path] += 1
        
        if org_symbol in code_chunks[patch_name][most_recent_file_path]:
          raise Exception(f"Duplicate .org symbol.\n.org symbol: {org_symbol}\nFile path: {most_recent_file_path}")
        
        code_chunks[patch_name][most_recent_file_path][org_symbol] = {
          "area_size": area_size,
          "temp_asm": "",
        }
        most_recent_org_offset = org_symbol
        continue
      elif branch_match:
        # Replace branches to specific addresses with labels, and define the address of those labels in the linker script.
        branch_dest = int(branch_match.group(1), 16)
        branch_temp_label = "branch_label_%X" % branch_dest
        local_branches_linker_script_for_file[most_recent_file_path] += "%s = 0x%X;\n" % (branch_temp_label, branch_dest)
        line = re.sub(r"0x" + branch_match.group(1), branch_temp_label, line, 1)
      elif line.startswith(".equ "):
        constant_definitions += line + "\n"
        continue
      elif line == ".close":
        most_recent_file_path = None
        most_recent_org_offset = None
        continue
      elif not line:
        # Blank line
        continue
      
      if not most_recent_file_path:
        if line[0] == ";":
          # Comment
          continue
        if line == ".section \".text\"":
          # Ignore the failsafe section reset after an include
          continue
        raise Exception("Found code when no file was open:\n%s" % line)
      if most_recent_org_offset is None:
        if line[0] == ";":
          # Comment
          continue
        if line == ".section \".text\"":
          # Ignore the failsafe section reset after an include
          continue
        raise Exception("Found code before any .org directive:\n%s" % line)
      
      code_chunks[patch_name][most_recent_file_path][most_recent_org_offset]["temp_asm"] += line + "\n"
    
    if not code_chunks[patch_name]:
      raise Exception("No code found")
    
    if most_recent_file_path or most_recent_org_offset is not None:
      raise Exception("File %s was not closed before the end of the file" % most_recent_file_path)
  
  for patch_name, code_chunks_for_patch in code_chunks.items():
    diffs = {}
    
    for file_path, code_chunks_for_file in code_chunks_for_patch.items():
      if file_path not in custom_symbols:
        custom_symbols[file_path] = {}
      custom_symbols_for_file = custom_symbols[file_path]
      
      # Sort code chunks in this patch so that free space chunks come first.
      # This is necessary so non-free-space chunks can branch to the free space chunks.
      def free_space_org_list_sorter(code_chunk_tuple):
        org_offset_or_symbol, temp_asm = code_chunk_tuple
        if isinstance(org_offset_or_symbol, int):
          return 0
        else:
          org_symbol = org_offset_or_symbol
          free_space_match = re.search(r"@FreeSpace_\d+", org_symbol)
          if free_space_match:
            return -1
          else:
            return 0
      code_chunks_for_file_sorted = list(code_chunks_for_file.items())
      code_chunks_for_file_sorted.sort(key=free_space_org_list_sorter)
      
      temp_linker_script = linker_script + "\n"
      # Add custom symbols in the current file to the temporary linker script.
      for symbol_name, symbol_address in custom_symbols[file_path].items():
        temp_linker_script += "%s = 0x%08X;\n" % (symbol_name, symbol_address)
      # And add any local branches inside this file.
      temp_linker_script += local_branches_linker_script_for_file[file_path]
      if file_path != "sys/main.dol":
        # Also add custom symbols in main.dol for all files.
        for symbol_name, symbol_address in custom_symbols["sys/main.dol"].items():
          temp_linker_script += "%s = 0x%08X;\n" % (symbol_name, symbol_address)
      
      for org_offset_or_symbol, chunk_info in code_chunks_for_file_sorted:
        area_size = chunk_info["area_size"]
        temp_asm = chunk_info["temp_asm"]
        
        using_free_space = False
        if isinstance(org_offset_or_symbol, int):
          org_offset = org_offset_or_symbol
        else:
          org_symbol = org_offset_or_symbol
          free_space_match = re.search(r"@FreeSpace_\d+", org_symbol)
          if free_space_match:
            org_offset = next_free_space_offsets[file_path]
            using_free_space = True
          else:
            if org_symbol not in custom_symbols_for_file:
              raise Exception(".org specified an invalid custom symbol: %s" % org_symbol)
            org_offset = custom_symbols_for_file[org_symbol]
        
        temp_linker_name = os.path.join(temp_dir, "tmp_linker.ld")
        with open(temp_linker_name, "w") as f:
          f.write(temp_linker_script)
        
        temp_asm_name = os.path.join(temp_dir, "tmp_" + patch_name + "_%08X.asm" % org_offset)
        with open(temp_asm_name, "w") as f:
          # Add our custom asm macros and constant definitions to all asm at the start.
          f.write(asm_macros)
          f.write("\n")
          f.write(constant_definitions)
          f.write("\n")
          f.write(temp_asm)
        
        o_name = os.path.join(temp_dir, "tmp_" + patch_name + "_%08X.o" % org_offset)
        command = [
          get_bin("powerpc-eabi-as"),
          "-mregnames",
          "-m750cl",
          temp_asm_name,
          "-o", o_name
        ]
        print(" ".join(command))
        print()
        result = call(command)
        if result != 0:
          raise Exception("Assembler call failed")
        
        # Determine the org offset for each individual section.
        elf = ELF()
        elf.read_from_file(o_name)
        org_offset_for_section_by_name = {}
        curr_org_offset = org_offset
        for elf_section in elf.sections:
          if elf_section.flags & ELFSectionFlags.SHF_ALLOC.value != 0:
            # Round the section's address up so it's properly aligned.
            align_size = elf_section.addr_align
            curr_org_offset = curr_org_offset + (align_size - curr_org_offset % align_size) % align_size
            
            org_offset_for_section_by_name[elf_section.name] = curr_org_offset
            #print("%s %04X %04X" % (elf_section.name, curr_org_offset, elf_section.size))
            
            curr_org_offset += elf_section.size
        code_chunk_size_in_bytes = (curr_org_offset - org_offset)
        
        if area_size is not None:
          if code_chunk_size_in_bytes > area_size:
            if isinstance(org_offset_or_symbol, int):
              org_str = f".org offset: 0x{org_offset_or_symbol:X}"
            else:
              org_str = f".org symbol: {org_offset_or_symbol}"
            raise Exception(
              f"The final byte size exceeded the end of the specified .area.\n"
              f".area max size: 0x{area_size:X}\n"
              f"Used size: 0x{code_chunk_size_in_bytes:X}\n"
              f"{org_str}\n"
              f"File path: {file_path}"
            )
        
        # Check to be sure that the code we just assembled didn't redefine any already defined global custom symbols.
        # If it does raise an error so the user can fix the duplicate name in their code.
        for elf_symbol in elf.symbols.get(".symtab", []):
          if elf_symbol.section_index >= 0xFF00:
            # Special section index (e.g. FFF1 is a filename).
            continue
          if elf.sections[elf_symbol.section_index].name == ".text":
            if elf_symbol.binding == ElfSymbolBinding.STB_GLOBAL:
              if elf_symbol.name in custom_symbols_for_file:
                raise Exception("Duplicate symbol %s in %s (org offset: %X)" % (elf_symbol.name, file_path, org_offset))
        
        code_chunk_filename = "tmp_%s_%08X" % (patch_name, org_offset)
        bin_name = os.path.join(temp_dir, code_chunk_filename + ".bin")
        map_name = os.path.join(temp_dir, code_chunk_filename + ".map")
        relocations = []
        command = [
          get_bin("powerpc-eabi-ld"),
          "-T", temp_linker_name,
          "-Map=" + map_name,
          o_name,
          "-o", bin_name
        ]
        # Set the section start arguments for each section.
        command += [
          "--section-start=%s=%X" % (section_name, section_org_offset)
          for section_name, section_org_offset in org_offset_for_section_by_name.items()
        ]
        if file_path.endswith(".rel"):
          # Output an ELF with relocations for RELs.
          command += ["--relocatable"]
        else:
          # For main, just output the raw binary code, not an ELF.
          command += ["--oformat", "binary"]
        print(" ".join(command))
        print()
        result = call(command)
        if result != 0:
          raise Exception("Linker call failed")
        
        # Keep track of custom symbols so they can be passed in the linker script to future assembler calls.
        with open(map_name) as f:
          on_custom_symbols = False
          for line in f.read().splitlines():
            if re.search(r"^ .\S+ +0x", line):
              on_custom_symbols = True
              continue
            
            if on_custom_symbols:
              match = re.search(r"^ +0x(?:00000000)?([0-9a-f]{8}) {16,}(\S+)", line)
              if not match:
                continue
              symbol_address = int(match.group(1), 16)
              symbol_name = match.group(2)
              custom_symbols_for_file[symbol_name] = symbol_address
              temp_linker_script += "%s = 0x%08X;\n" % (symbol_name, symbol_address)
        
        # Uncomment the below to debug the linker's map file.
        #shutil.copyfile(map_name, code_chunk_filename + ".map")
        
        if file_path.endswith(".rel"):
          # This is for a REL, so we can't link it.
          # Instead read the ELF to get the assembled code and relocations out of it directly.
          relocations += get_code_and_relocations_from_elf(bin_name)
        
        # Keep track of changed bytes.
        if file_path not in diffs:
          diffs[file_path] = {}
        
        if org_offset in diffs[file_path]:
          raise Exception("Duplicate .org directive within a single asm patch: %X" % org_offset)
        
        with open(bin_name, "rb") as f:
          binary_data = f.read()
        
        bin_size = len(binary_data)
        # The chunk size can be larger than the bin if the last section was a .bss section. But it can't be smaller.
        assert code_chunk_size_in_bytes >= bin_size
        
        if bin_size >= 0x80000000:
          raise Exception("The assembled code binary is much too large. This is probably a bug in the assembler.")
        
        if using_free_space:
          next_free_space_offsets[file_path] += code_chunk_size_in_bytes
        
        bytes = list(struct.unpack("B"*bin_size, binary_data))
        diffs[file_path][org_offset] = {}
        diffs[file_path][org_offset]["Data"] = bytes
        if relocations:
          diffs[file_path][org_offset]["Relocations"] = relocations
    
    diff_path = os.path.join(asm_dir, "patch_diffs", patch_name + "_diff.txt")
    with open(diff_path, "w", newline='\n') as f:
      f.write(yaml.dump(diffs, default_flow_style=False, sort_keys=False))
  
  # Write the custom symbols to a text file.
  # Delete any entries in custom_symbols that have no custom symbols to avoid clutter.
  output_custom_symbols = {}
  for file_path, custom_symbols_for_file in custom_symbols.items():
    if file_path != "sys/main.dol" and len(custom_symbols_for_file) == 0:
      continue
    
    output_custom_symbols[file_path] = custom_symbols_for_file
  
  with open(asm_dir + "/custom_symbols.txt", "w", newline='\n') as f:
    f.write(yaml.dump(output_custom_symbols, default_flow_style=False, sort_keys=False))
except Exception as e:
  stack_trace = traceback.format_exc()
  error_message = str(e) + "\n\n" + stack_trace
  print(error_message)
  input()
  raise
finally:
  shutil.rmtree(temp_dir)
