
import os
import yaml
import re

from fs_helpers import *
from paths import ASM_PATH
from wwlib.rel import REL, RELSection, RELRelocation, RELRelocationType

ORIGINAL_FREE_SPACE_RAM_ADDRESS = 0x803FCFA8
ORIGINAL_DOL_SIZE = 0x3A52C0

def split_pointer_into_high_and_low_half_for_hardcoding(pointer):
  high_halfword = (pointer & 0xFFFF0000) >> 16
  low_halfword = pointer & 0xFFFF
  
  if low_halfword >= 0x8000:
    # If the low halfword has the highest bit set, it will be considered a negative number.
    # Therefore we need to add 1 to the high halfword (equivalent to adding 0x10000) to compensate for the low halfword being negated.
    high_halfword = high_halfword+1
  
  return high_halfword, low_halfword

def apply_patch(self, patch_name):
  with open(os.path.join(ASM_PATH, "patch_diffs", patch_name + "_diff.txt")) as f:
    diffs = yaml.safe_load(f)
  
  for file_path, diffs_for_file in diffs.items():
    for org_address, patchlet in diffs_for_file.items():
      new_bytes = patchlet["Data"]
      
      free_space_start = self.free_space_start_offsets[file_path]
      
      if file_path == "sys/main.dol":
        if org_address >= free_space_start:
          add_or_extend_main_dol_free_space_section(self, new_bytes, org_address)
          continue
        else:
          self.dol.write_data(write_and_pack_bytes, org_address, new_bytes, "B"*len(new_bytes))
      else:
        assert file_path.endswith(".rel")
        offset = org_address
        relocations = patchlet.get("Relocations", [])
        
        rel = self.get_rel(file_path)
        if offset >= free_space_start:
          apply_free_space_patchlet_to_rel(self, file_path, offset, new_bytes, relocations)
        else:
          rel.write_data(write_and_pack_bytes, offset, new_bytes, "B"*len(new_bytes))
          
          rel.delete_relocation_in_range(offset, len(new_bytes))
          
          if relocations:
            rel_section_index, offset_into_section = rel.convert_rel_offset_to_section_index_and_relative_offset(offset)
            add_relocations_to_rel(self, file_path, rel_section_index, offset_into_section, relocations)

def add_or_extend_main_dol_free_space_section(self, new_bytes, org_address):
  dol_section = self.dol.sections[2]
  patch_length = len(new_bytes)
  
  if patch_length == 0:
    # Can't add a section of size 0.
    return
  
  if org_address != ORIGINAL_FREE_SPACE_RAM_ADDRESS + dol_section.size:
    raise Exception("Attempted to add or extend a main.dol free space section at address 0x%08X, when the next main.dol free space address was expected to be at 0x%08X" % (org_address, ORIGINAL_FREE_SPACE_RAM_ADDRESS + dol_section.size))
  
  new_total_section_size = dol_section.size + patch_length
  
  # First add a new text section to the dol (Text2).
  dol_section.offset = ORIGINAL_DOL_SIZE # Set the file offset of new Text2 section (which will be the original end of the file, where we put the new section)
  dol_section.address = ORIGINAL_FREE_SPACE_RAM_ADDRESS # Write loading address of the new Text2 section
  dol_section.size = new_total_section_size # Write length of the new Text2 section
  
  # Next write our custom code to the end of the dol file.
  self.dol.write_data(write_and_pack_bytes, org_address, new_bytes, "B"*len(new_bytes))
  
  # Next we need to change a hardcoded pointer to where free space begins. Otherwise the game will overwrite the custom code.
  padded_section_size = ((new_total_section_size + 3) & ~3) # Pad length of new section to next 4 just in case
  new_start_pointer_for_default_thread = ORIGINAL_FREE_SPACE_RAM_ADDRESS + padded_section_size # New free space pointer after our custom code
  high_halfword, low_halfword = split_pointer_into_high_and_low_half_for_hardcoding(new_start_pointer_for_default_thread)
  # Now update the asm instructions that load this hardcoded pointer.
  self.dol.write_data(write_u32, 0x80307954, 0x3C600000 | high_halfword)
  self.dol.write_data(write_u32, 0x8030795C, 0x38030000 | low_halfword)
  # We also update another pointer which seems like it should remain at 0x10000 later in RAM from the pointer we updated.
  # (This pointer was originally 0x8040CFA8.)
  # Updating this one may not actually be necessary to update, but this is to be safe.
  new_end_pointer_for_default_thread = new_start_pointer_for_default_thread + 0x10000
  high_halfword, low_halfword = split_pointer_into_high_and_low_half_for_hardcoding(new_end_pointer_for_default_thread)
  self.dol.write_data(write_u32, 0x8030794C, 0x3C600000 | high_halfword)
  self.dol.write_data(write_u32, 0x80307950, 0x38030000 | low_halfword)
  self.dol.write_data(write_u32, 0x80301854, 0x3C600000 | high_halfword)
  self.dol.write_data(write_u32, 0x80301858, 0x38630000 | low_halfword)
  high_halfword = (new_end_pointer_for_default_thread & 0xFFFF0000) >> 16
  low_halfword = new_end_pointer_for_default_thread & 0xFFFF
  self.dol.write_data(write_u32, 0x80003278, 0x3C200000 | high_halfword)
  self.dol.write_data(write_u32, 0x8000327C, 0x60210000 | low_halfword)
  # We also update another pointer which seems like it should remain at 0x12000 later in RAM from the pointer we updated.
  # (This pointer was originally 0x8040EFA8.)
  # Updating this one is definitely not necessary since the function it's in (InitMetroTRK) is never called, and was likely for debugging. But we update it anyway just for completeness' sake.
  new_pointer_for_metro_trk = new_start_pointer_for_default_thread + 0x12000
  high_halfword = (new_pointer_for_metro_trk & 0xFFFF0000) >> 16
  low_halfword = new_pointer_for_metro_trk & 0xFFFF
  self.dol.write_data(write_u32, 0x803370A8, 0x3C200000 | high_halfword)
  self.dol.write_data(write_u32, 0x803370AC, 0x60210000 | low_halfword)
  
  # Original thread start pointer: 803FCFA8 (must be updated)
  # Original stack end pointer (r1): 8040CFA8 (must be updated)
  # Original rtoc pointer (r2): 803FFD00 (must NOT be updated)
  # Original read-write small data area pointer (r13): 803FE0E0 (must NOT be updated)

def apply_free_space_patchlet_to_rel(self, file_path, offset, new_bytes, relocations):
  # We add a new section to the REL to hold our custom code.
  
  rel = self.get_rel(file_path)
  
  # Use REL section 7 for any custom code we add into RELs.
  # REL sections 7-0x10 were present in all RELs in the original game, but always uninitialized, so we can use them freely.
  # (REL section 0 was also present in all RELs but uninitialized, but that one seems to be necessary for some reason.)
  rel_section_index = 7
  rel_section = rel.sections[rel_section_index]
  if rel_section.is_uninitialized:
    # This is the first free space patchlet we're applying to this REL, so initialize the section.
    add_free_space_section_to_rel(self, file_path)
  
  section_relative_offset = offset - rel_section.offset
  write_and_pack_bytes(rel_section.data, section_relative_offset, new_bytes, "B"*len(new_bytes))
  
  if relocations:
    add_relocations_to_rel(self, file_path, rel_section_index, patchlet_offset_into_curr_section, relocations)

def add_free_space_section_to_rel(self, file_path):
  rel = self.get_rel(file_path)
  
  rel_section_index = 7
  rel_section = rel.sections[rel_section_index]
  
  assert not rel_section.is_bss
  rel_section.is_uninitialized = False
  rel_section.is_executable = True
  rel_section.data = BytesIO()
  
  # We could leave it to the REL implementation's saving logic to decide where to place the free space, but to be on the safe side, instead use the free space offset from free_space_start_offsets.txt, because that's the offset that was used for linking the code.
  rel_section.offset = self.free_space_start_offsets[file_path]

def add_relocations_to_rel(self, file_path, rel_section_index, offset_into_section, relocations):
  # Create the new REL relocations.
  
  rel = self.get_rel(file_path)
  
  main_symbols = self.get_symbol_map("files/maps/framework.map")
  
  free_space_start = self.free_space_start_offsets[file_path]
  
  for relocation_dict in relocations:
    symbol_name = relocation_dict["SymbolName"]
    relocation_offset = relocation_dict["Offset"]
    relocation_type = relocation_dict["Type"]
    
    relocation_offset += offset_into_section
    
    rel_relocation = RELRelocation()
    rel_relocation.relocation_type = RELRelocationType[relocation_type]
    
    branch_label_match = re.search(r"^branch_label_([0-9A-F]+)$", symbol_name, re.IGNORECASE)
    if symbol_name in self.main_custom_symbols:
      # Custom symbol located in main.dol.
      module_num = 0
      
      rel_relocation.symbol_address = self.main_custom_symbols[symbol_name]
      
      # I don't think this value is used for dol relocations.
      # In vanilla, this was written as 4 for some reason?
      rel_relocation.section_num_to_relocate_against = 0
    elif symbol_name in self.custom_symbols.get(file_path, {}):
      # Custom symbol located in the current REL.
      custom_symbol_offset = self.custom_symbols[file_path][symbol_name]
      
      module_num = rel.id
      
      if custom_symbol_offset >= free_space_start:
        # In our custom free space section.
        other_rel_section_index = 7
        relative_offset = custom_symbol_offset - free_space_start
      else:
        other_rel_section_index, relative_offset = rel.convert_rel_offset_to_section_index_and_relative_offset(custom_symbol_offset)
      
      rel_relocation.section_num_to_relocate_against = other_rel_section_index
      rel_relocation.symbol_address = relative_offset
    elif ":" in symbol_name:
      # Vanilla symbol located in a REL.
      # We use a colon to signify rel_name:symbol_name.
      # (This is because we don't necessarily know for sure that the REL is calling a function inside of itself, it's possible to call a function in another REL.)
      rel_name, symbol_name = symbol_name.split(":", 1)
      other_rel = self.get_rel("files/rels/%s.rel" % rel_name)
      other_rel_symbols = self.get_symbol_map("files/maps/%s.map" % rel_name)
      
      if symbol_name not in other_rel_symbols:
        raise Exception("Symbol \"%s\" could not be found in the symbol map for REL %s.rel" % (symbol_name, rel_name))
      
      module_num = other_rel.id
      
      other_rel_section_index, relative_offset = other_rel.convert_rel_offset_to_section_index_and_relative_offset(other_rel_symbols[symbol_name])
      rel_relocation.section_num_to_relocate_against = other_rel_section_index
      rel_relocation.symbol_address = relative_offset
    elif branch_label_match:
      # Relative branch. The destination must be in the current REL.
      branch_dest_offset = int(branch_label_match.group(1), 16)
      
      module_num = rel.id
      
      other_rel_section_index, relative_offset = rel.convert_rel_offset_to_section_index_and_relative_offset(branch_dest_offset)
      rel_relocation.section_num_to_relocate_against = other_rel_section_index
      rel_relocation.symbol_address = relative_offset
    elif symbol_name in main_symbols:
      # Vanilla symbol located in main.dol.
      module_num = 0
      
      rel_relocation.symbol_address = main_symbols[symbol_name]
      
      # I don't think this value is used for dol relocations.
      # In vanilla, it was written as some kind of section index in the DOL (e.g. 4 for .text, 7 for .rodata), but this doesn't seem necessary.
      rel_relocation.section_num_to_relocate_against = 0
    else:
      raise Exception("Could not find symbol name: %s" % symbol_name)
    
    rel_relocation.relocation_offset = relocation_offset
    rel_relocation.curr_section_num = rel_section_index
    
    if module_num not in rel.relocation_entries_for_module:
      rel.relocation_entries_for_module[module_num] = []
    rel.relocation_entries_for_module[module_num].append(rel_relocation)
