
import glob
import re
from subprocess import call
import os
import tempfile
import shutil

temp_dir = tempfile.mkdtemp()
print(temp_dir)
print()

custom_symbols = []

try:
  with open("linker.ld") as f:
    linker_script = f.read()
  
  for filename in glob.glob('*.asm'):
    print("Assembling " + filename)
    with open(filename) as f:
      asm = f.read()
    
    temp_asm = ""
    temp_linker_script = linker_script + "\n"
    org_offset = None
    for line in asm.splitlines():
      line = line.strip()
      line = line.replace(";", "#")
      
      org_match = re.match(r"\.org\s+0x([0-9a-f]+)$", line, re.IGNORECASE)
      branch_match = re.match(r"(?:b|beq|bne|blt|bgt|ble|bge)\s+0x([0-9a-f]+)(?:$|\s)", line, re.IGNORECASE)
      if org_match and not org_offset:
        org_offset = int(org_match.group(1), 16)
        temp_asm += "\n"
      elif org_match and org_offset:
        raise Exception("Found more than one .org directive")
      elif branch_match:
        # Replace branches to specific addresses with labels, and define the address of those labels in the linker script.
        branch_dest = int(branch_match.group(1), 16)
        branch_temp_label = "branch_label_%X" % branch_dest
        temp_linker_script += "%s = 0x%X;" % (branch_temp_label, branch_dest)
        line = re.sub(r"0x" + branch_match.group(1), branch_temp_label, line, 1)
        temp_asm += line + "\n"
      else:
        temp_asm += line + "\n"
    
    if org_offset is None:
      raise Exception("Could not find .org directive")
    
    temp_asm_name = os.path.join(temp_dir, "tmp_" + filename)
    with open(temp_asm_name, "w") as f:
      f.write(temp_asm)
    temp_linker_name = os.path.join(temp_dir, "tmp_linker.ld")
    with open(temp_linker_name, "w") as f:
      f.write(temp_linker_script)
    
    o_name = os.path.join(temp_dir, "tmp_" + os.path.splitext(filename)[0] + ".o")
    command = [
      r"C:\devkitPro\devkitPPC\bin\powerpc-eabi-as.exe", "-mregnames", "-m750cl",
      temp_asm_name, "-o", o_name
    ]
    print(" ".join(command))
    print()
    result = call(command)
    if result != 0:
      raise Exception("Assembler call failed")
    
    bin_name = os.path.splitext(filename)[0] + ".bin"
    map_name = os.path.join(temp_dir, "tmp_" + os.path.splitext(filename)[0] + ".map")
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
          custom_symbols.append((symbol_address, symbol_name))
finally:
  shutil.rmtree(temp_dir)

with open("./custom_symbols.txt", "w") as f:
  for symbol_address, symbol_name in custom_symbols:
    f.write("%s %s\n" % (symbol_address, symbol_name))
