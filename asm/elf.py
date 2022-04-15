
from enum import Enum
from io import BytesIO
from collections import OrderedDict

from fs_helpers import *

class ELF:
  def read_from_file(self, file_path):
    with open(file_path, "rb") as f:
      self.data = BytesIO(f.read())
    
    self.section_headers_table_offset = read_u32(self.data, 0x20)
    self.num_section_headers = read_u16(self.data, 0x30)
    self.section_header_string_table_section_index = read_u16(self.data, 0x32)
    
    self.sections = []
    for i in range(self.num_section_headers):
      section = ELFSection()
      section.read(self.data, self.section_headers_table_offset + i*ELFSection.ENTRY_SIZE)
      self.sections.append(section)
    
    section_header_string_table_offset = self.sections[self.section_header_string_table_section_index].section_offset
    for section in self.sections:
      section.name = read_str_until_null_character(self.data, section_header_string_table_offset+section.name_offset)
    
    self.sections_by_name = OrderedDict()
    for section in self.sections:
      self.sections_by_name[section.name] = section
    
    self.relocations = OrderedDict()
    for section in self.sections:
      if section.type == ELFSectionType.SHT_RELA:
        self.relocations[section.name] = []
        for i in range(section.size//ELFRelocation.ENTRY_SIZE):
          relocation = ELFRelocation()
          relocation.read(self.data, section.section_offset + i*ELFRelocation.ENTRY_SIZE)
          self.relocations[section.name].append(relocation)
    
    self.symbols = OrderedDict()
    self.symbols_by_name = OrderedDict()
    for section in self.sections:
      if section.type == ELFSectionType.SHT_SYMTAB:
        self.symbols[section.name] = []
        self.symbols_by_name[section.name] = OrderedDict()
        for i in range(section.size//ELFSymbol.ENTRY_SIZE):
          symbol = ELFSymbol()
          symbol.read(self.data, section.section_offset + i*ELFSymbol.ENTRY_SIZE)
          symbol.name = self.read_string_from_table(symbol.name_offset)
          self.symbols[section.name].append(symbol)
          self.symbols_by_name[section.name][symbol.name] = symbol
  
  def read_string_from_table(self, string_offset):
    offset = self.sections_by_name[".strtab"].section_offset + string_offset
    return read_str_until_null_character(self.data, offset)

class ELFSection:
  ENTRY_SIZE = 0x28
  
  def read(self, elf_data, header_offset):
    self.header_offset = header_offset
    
    self.name_offset = read_u32(elf_data, self.header_offset+0x00)
    self.type = ELFSectionType(read_u32(elf_data, self.header_offset+0x04))
    self.flags = read_u32(elf_data, self.header_offset+0x08)
    self.address = read_u32(elf_data, self.header_offset+0x0C)
    self.section_offset = read_u32(elf_data, self.header_offset+0x10)
    self.size = read_u32(elf_data, self.header_offset+0x14)
    self.link = read_u32(elf_data, self.header_offset+0x18)
    self.info = read_u32(elf_data, self.header_offset+0x1C)
    self.addr_align = read_u32(elf_data, self.header_offset+0x20)
    self.entry_size = read_u32(elf_data, self.header_offset+0x24)
    
    self.data = BytesIO(read_bytes(elf_data, self.section_offset, self.size))

class ELFRelocation:
  ENTRY_SIZE = 0xC
  
  def read(self, elf_data, offset):
    self.offset = offset
    
    self.relocation_offset = read_u32(elf_data, self.offset + 0x00)
    info = read_u32(elf_data, self.offset + 0x04)
    self.type = ELFRelocationType(info & 0x000000FF)
    self.symbol_index = (info & 0xFFFFFF00) >> 8
    self.addend = read_u32(elf_data, self.offset + 0x08)

class ELFSymbol:
  ENTRY_SIZE = 0x10
  
  def read(self, elf_data, offset):
    self.offset = offset
    
    self.name_offset = read_u32(elf_data, self.offset + 0x00)
    self.address = read_u32(elf_data, self.offset + 0x04)
    self.size = read_u32(elf_data, self.offset + 0x08)
    info = read_u8(elf_data, self.offset + 0x0C)
    self.type = ElfSymbolType(info & 0x0F)
    self.binding = ElfSymbolBinding((info & 0xF0) >> 4)
    self.other = read_u8(elf_data, self.offset + 0x0D)
    self.section_index = read_u16(elf_data, self.offset + 0x0E)

class ELFSectionType(Enum):
  SHT_NULL = 0x0
  SHT_PROGBITS = 0x1
  SHT_SYMTAB = 0x2
  SHT_STRTAB = 0x3
  SHT_RELA = 0x4
  SHT_HASH = 0x5
  SHT_DYNAMIC = 0x6
  SHT_NOTE = 0x7
  SHT_NOBITS = 0x8
  SHT_REL = 0x9
  SHT_SHLIB = 0x0A
  SHT_DYNSYM = 0x0B
  SHT_INIT_ARRAY = 0x0E
  SHT_FINI_ARRAY = 0x0F
  SHT_PREINIT_ARRAY = 0x10
  SHT_GROUP = 0x11
  SHT_SYMTAB_SHNDX = 0x12
  SHT_NUM = 0x13
  
  UNK_1 = 0x6FFFFFF5

class ELFSectionFlags(Enum):
  SHF_WRITE            = 0x00000001
  SHF_ALLOC            = 0x00000002
  SHF_EXECINSTR        = 0x00000004
  SHF_MERGE            = 0x00000010
  SHF_STRINGS          = 0x00000020
  SHF_INFO_LINK        = 0x00000040
  SHF_LINK_ORDER       = 0x00000080
  SHF_OS_NONCONFORMING = 0x00000100
  SHF_GROUP            = 0x00000200
  SHF_TLS              = 0x00000400
  SHF_MASKOS           = 0x0FF00000
  SHF_MASKPROC         = 0xF0000000
  SHF_ORDERED          = 0x04000000
  SHF_EXCLUDE          = 0x08000000

class ELFRelocationType(Enum):
  R_PPC_NONE = 0x00
  R_PPC_ADDR32 = 0x01
  R_PPC_ADDR24 = 0x02
  R_PPC_ADDR16 = 0x03
  R_PPC_ADDR16_LO = 0x04
  R_PPC_ADDR16_HI = 0x05
  R_PPC_ADDR16_HA = 0x06
  R_PPC_ADDR14 = 0x07
  R_PPC_ADDR14_BRTAKEN = 0x08
  R_PPC_ADDR14_BRNTAKEN = 0x09
  R_PPC_REL24 = 0x0A
  R_PPC_REL14 = 0x0B
  R_PPC_REL14_BRTAKEN = 0x0C
  R_PPC_REL14_BRNTAKEN = 0x0D
  
  R_PPC_REL32 = 0x1A

class ELFSymbolSpecialSection(Enum):
  SHN_UNDEF     = 0x0000
  SHN_LORESERVE = 0xFF00
  SHN_LOPROC    = 0xFF00
  SHN_HIPROC    = 0xFF1F
  SHN_LOOS      = 0xFF20
  SHN_HIOS      = 0xFF3F
  SHN_ABS       = 0xFFF1
  SHN_COMMON    = 0xFFF2
  SHN_XINDEX    = 0xFFFF
  SHN_HIRESERVE = 0xFFFF

class ElfSymbolType(Enum):
  STT_NOTYPE         = 0
  STT_OBJECT         = 1
  STT_FUNC           = 2
  STT_SECTION        = 3
  STT_FILE           = 4
  STT_COMMON         = 5
  STT_TLS            = 6
  STT_LOOS           = 10
  STT_HIOS           = 12
  STT_LOPROC         = 13
  STT_SPARC_REGISTER = 13
  STT_HIPROC         = 15

class ElfSymbolBinding(Enum):
  STB_LOCAL  = 0
  STB_GLOBAL = 1
  STB_WEAK   = 2
  STB_LOOS   = 10
  STB_HIOS   = 12
  STB_LOPROC = 13
  STB_HIPROC = 15
