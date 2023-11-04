
from gclib import fs_helpers as fs
from gclib.rel import REL, RELSection, RELRelocation, RELRelocationType
from asm.elf import ELF, ELFSectionType, ELFSectionFlags, ELFRelocationType, ELFSymbolSpecialSection

ALLOWED_SECTIONS = [
  ".text",
  ".ctors",
  ".dtors",
  ".rodata",
  ".data",
  ".bss",
  ".rodata.str1.4",
  ".rodata.cst4",
  ".rodata.cst8",
  ".sdata",
]

def convert_elf_to_rel(in_elf_path, rel_id, main_symbols, actor_profile_name):
  elf = ELF()
  elf.read_from_file(in_elf_path)
  
  rel = REL()
  
  rel.id = rel_id
  
  # First convert the sections we want to include in the REL from ELF sections to REL sections.
  section_name_to_rel_section = {}
  elf_section_index_to_rel_section = {}
  for elf_section_index, elf_section in enumerate(elf.sections):
    if elf_section.name in ALLOWED_SECTIONS or elf_section.type == ELFSectionType.SHT_NULL:
      # Sections we will add to the REL.
      rel_section = RELSection()
      rel_section.data = fs.make_copy_data(elf_section.data)
      rel.sections.append(rel_section)
      
      if elf_section.flags & ELFSectionFlags.SHF_EXECINSTR.value:
        rel_section.is_executable = True
      
      section_name_to_rel_section[elf_section.name] = rel_section
      elf_section_index_to_rel_section[elf_section_index] = rel_section
      
      if elf_section.type == ELFSectionType.SHT_NOBITS:
        assert elf_section.size > 0
        assert rel.bss_size == 0
        rel.bss_size = elf_section.size
        rel_section.is_uninitialized = True
        rel_section.is_bss = True
      elif elf_section.type == ELFSectionType.SHT_NULL:
        rel_section.is_uninitialized = True
        rel_section.is_bss = False
      else:
        rel_section.is_uninitialized = False
        rel_section.is_bss = False
  
  # Then generate the relocations.
  for elf_section in elf.sections:
    if elf_section.type == ELFSectionType.SHT_RELA:
      assert elf_section.name.startswith(".rela")
      relocated_section_name = elf_section.name[len(".rela"):]
      
      if relocated_section_name not in section_name_to_rel_section:
        # Ignored section
        continue
      
      rel_section = section_name_to_rel_section[relocated_section_name]
      section_index = rel.sections.index(rel_section)
      for elf_relocation in elf.relocations[elf_section.name]:
        rel_relocation = RELRelocation()
        
        elf_symbol = elf.symbols[".symtab"][elf_relocation.symbol_index]
        rel_relocation.relocation_type = RELRelocationType(elf_relocation.type.value)
        #print("%X" % elf_symbol.section_index)
        
        if elf_symbol.section_index == 0:
          if elf_symbol.name in main_symbols:
            elf_symbol.section_index = ELFSymbolSpecialSection.SHN_ABS.value
            elf_symbol.address = main_symbols[elf_symbol.name]
          else:
            raise Exception("Unresolved external symbol: %s" % elf_symbol.name)
        
        if elf_symbol.section_index == ELFSymbolSpecialSection.SHN_ABS.value:
          # Symbol is located in main.dol.
          module_num = 0
          
          # I don't think this value is used for dol relocations.
          # In vanilla, this was written as 4 for some reason?
          rel_relocation.section_num_to_relocate_against = 0
        elif elf_symbol.section_index >= 0xFF00:
          raise Exception("Special section number not implemented: %04X" % elf_symbol.section_index)
        else:
          # Symbol is located in the current REL.
          # TODO: support for relocating against other rels besides the current one
          module_num = rel.id
          
          section_name_to_relocate_against = elf.sections[elf_symbol.section_index].name
          if section_name_to_relocate_against not in section_name_to_rel_section:
            raise Exception("Section name \"%s\" could not be found for symbol \"%s\"" % (section_name_to_relocate_against, elf_symbol.name))
          rel_section_to_relocate_against = section_name_to_rel_section[section_name_to_relocate_against]
          rel_section_index_to_relocate_against = rel.sections.index(rel_section_to_relocate_against)
          rel_relocation.section_num_to_relocate_against = rel_section_index_to_relocate_against
        
        rel_relocation.symbol_address = elf_symbol.address + elf_relocation.addend
        rel_relocation.relocation_offset = elf_relocation.relocation_offset
        rel_relocation.curr_section_num = section_index
        
        if module_num not in rel.relocation_entries_for_module:
          rel.relocation_entries_for_module[module_num] = []
        rel.relocation_entries_for_module[module_num].append(rel_relocation)
  
  symbol = elf.symbols_by_name[".symtab"]["_prolog"]
  rel_section = elf_section_index_to_rel_section[symbol.section_index]
  rel_section_index = rel.sections.index(rel_section)
  rel.prolog_section = rel_section_index
  rel.prolog_offset = symbol.address
  
  symbol = elf.symbols_by_name[".symtab"]["_epilog"]
  rel_section = elf_section_index_to_rel_section[symbol.section_index]
  rel_section_index = rel.sections.index(rel_section)
  rel.epilog_section = rel_section_index
  rel.epilog_offset = symbol.address
  
  symbol = elf.symbols_by_name[".symtab"]["_unresolved"]
  rel_section = elf_section_index_to_rel_section[symbol.section_index]
  rel_section_index = rel.sections.index(rel_section)
  rel.unresolved_section = rel_section_index
  rel.unresolved_offset = symbol.address
  
  rel.save_changes()
  
  if actor_profile_name not in elf.symbols_by_name[".symtab"]:
    raise Exception("Could not find the actor profile. The specified symbol name for it was \"%s\", but that symbol could not be found in the ELF." % actor_profile_name)
  profile_section = section_name_to_rel_section[".rodata"]
  profile_section_index = rel.sections.index(profile_section)
  
  profile_symbol = elf.symbols_by_name[".symtab"][actor_profile_name]
  rel_section = elf_section_index_to_rel_section[profile_symbol.section_index]
  rel_section_index = rel.sections.index(rel_section)
  profile_section_index = rel_section_index
  profile_address = profile_symbol.address
  
  return rel, profile_section_index, profile_address
