
import glob
import re
from subprocess import call
import os
import tempfile
import shutil
from collections import OrderedDict
import struct
import yaml

# Allow yaml to dump OrderedDicts for the diffs.
yaml.CDumper.add_representer(
  OrderedDict,
  lambda dumper, data: dumper.represent_dict(data.items())
)

temp_dir = tempfile.mkdtemp()
print(temp_dir)
print()

custom_symbols = OrderedDict()

try:
  with open("linker.ld") as f:
    linker_script = f.read()
  
  all_asm_files = glob.glob('*.asm')
  all_asm_files.remove("custom_funcs.asm")
  # Always do custom_funcs first so the custom symbols are defined for all the other patches to use.
  all_asm_files = ["custom_funcs.asm"] + all_asm_files
  
  for filename in all_asm_files:
    print("Assembling " + filename)
    with open(filename) as f:
      asm = f.read()
    basename = os.path.splitext(filename)[0]
    
    temp_linker_script = linker_script + "\n"
    # Add custom function symbols to the temporary linker script.
    for symbol_name, symbol_address in custom_symbols.items():
      temp_linker_script += "%s = 0x%s;\n" % (symbol_name, symbol_address)
    
    code_chunks = OrderedDict()
    most_recent_file_path = None
    most_recent_org_offset = None
    for line in asm.splitlines():
      line = re.sub(r";.+$", "", line)
      line = line.strip()
      
      open_file_match = re.match(r"\.open\s+\"([^\"]+)\"$", line, re.IGNORECASE)
      org_match = re.match(r"\.org\s+0x([0-9a-f]+)$", line, re.IGNORECASE)
      branch_match = re.match(r"(?:b|beq|bne|blt|bgt|ble|bge)\s+0x([0-9a-f]+)(?:$|\s)", line, re.IGNORECASE)
      if open_file_match:
        relative_file_path = open_file_match.group(1)
        if relative_file_path not in code_chunks:
          code_chunks[relative_file_path] = OrderedDict()
        most_recent_file_path = relative_file_path
        continue
      elif org_match:
        if not most_recent_file_path:
          raise Exception("Found .org directive before any .open directive")
        
        org_offset = int(org_match.group(1), 16)
        code_chunks[most_recent_file_path][org_offset] = ""
        most_recent_org_offset = org_offset
        continue
      elif branch_match:
        # Replace branches to specific addresses with labels, and define the address of those labels in the linker script.
        branch_dest = int(branch_match.group(1), 16)
        branch_temp_label = "branch_label_%X" % branch_dest
        temp_linker_script += "%s = 0x%X;" % (branch_temp_label, branch_dest)
        line = re.sub(r"0x" + branch_match.group(1), branch_temp_label, line, 1)
      elif not line:
        # Blank line
        continue
      
      if not most_recent_file_path:
        raise Exception("Found code before any .open directive")
      if not most_recent_org_offset:
        raise Exception("Found code before any .org directive")
      
      code_chunks[most_recent_file_path][most_recent_org_offset] += line + "\n"
    
    if not code_chunks:
      raise Exception("No code found")
    
    temp_linker_name = os.path.join(temp_dir, "tmp_linker.ld")
    with open(temp_linker_name, "w") as f:
      f.write(temp_linker_script)
    
    diffs = OrderedDict()
    for file_path, code_chunks_for_file in code_chunks.items():
      for org_offset, temp_asm in code_chunks_for_file.items():
        temp_asm_name = os.path.join(temp_dir, "tmp_" + basename + "_%08X.asm" % org_offset)
        with open(temp_asm_name, "w") as f:
          f.write(temp_asm)
        
        o_name = os.path.join(temp_dir, "tmp_" + basename + "_%08X.o" % org_offset)
        command = [
          r"C:\devkitPro\devkitPPC\bin\powerpc-eabi-as.exe", "-mregnames", "-m750cl",
          temp_asm_name, "-o", o_name
        ]
        print(" ".join(command))
        print()
        result = call(command)
        if result != 0:
          raise Exception("Assembler call failed")
        
        bin_name = os.path.join(temp_dir, "tmp_" + basename + "_%08X.bin" % org_offset)
        map_name = os.path.join(temp_dir, "tmp_" + basename + ".map")
        command = [
          r"C:\devkitPro\devkitPPC\bin\powerpc-eabi-ld.exe",
          "-Ttext", "%X" % org_offset,
          "-T", temp_linker_name,
          "--oformat", "binary",
          "-Map=" + map_name,
          o_name,
          "-o", bin_name
        ]
        print(" ".join(command))
        print()
        result = call(command)
        if result != 0:
          raise Exception("Linker call failed")
        
        # Keep track of custom symbols so they can be passed in the linker script to future assembler calls.
        with open(map_name) as f:
          on_custom_symbols = False
          for line in f.read().splitlines():
            if line.startswith(" .text          "):
              on_custom_symbols = True
              continue
            
            if on_custom_symbols:
              if not line:
                break
              match = re.search(r" +0x([0-9a-f]{8}) +(\S+)", line)
              symbol_address = match.group(1)
              symbol_name = match.group(2)
              custom_symbols[symbol_name] = symbol_address
        
        # Keep track of changed bytes.
        if file_path not in diffs:
          diffs[file_path] = OrderedDict()
        
        if org_offset in diffs[file_path]:
          raise Exception("Duplicate .org directive: %X" % org_offset)
        
        with open(bin_name, "rb") as f:
          binary_data = f.read()
        
        bytes = list(struct.unpack("B"*len(binary_data), binary_data))
        diffs[file_path][org_offset] = bytes
    
    diff_name = basename + "_diff.txt"
    with open(diff_name, "w") as f:
      f.write(yaml.dump(diffs, Dumper=yaml.CDumper))
finally:
  shutil.rmtree(temp_dir)

with open("./custom_symbols.txt", "w") as f:
  for symbol_name, symbol_address in custom_symbols.items():
    f.write("%s %s\n" % (symbol_address, symbol_name))
