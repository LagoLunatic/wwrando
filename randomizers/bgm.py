
from fs_helpers import *
from tweaks import address_to_offset

SILENT_BGM_IDS = [
  0x0000,
]

EXTRA_BGM_INFOS = [
  0x00441B00, # Grandma's theme
  0x00330000, # Unused Tetra theme
  #0x00190105, # Miniboss theme (sounds wrong)
  #0x001A0605, # Miniboss theme (sounds wrong)
  0x00030101, # Gohma phase 1
  0x00100101, # Gohma phase 2
  0x0041020A, # Phantom Ganon (at Forsaken Fortress, with intro)
  0x0047180A, # Phantom Ganon (in Ganon's Tower, no intro)
  0x01150704, # Helmaroc chase up the tower
  0x004C0809, # Molgera
  0x004D2000, # Ganondorf fight
]

def randomize_bgm(self):
  dol_data = self.get_raw_file("sys/main.dol")
  stage_bgm_info_list_start = 0x8039C30C
  island_bgm_info_list_start = 0x8039C4F0
  
  valid_bgm_infos = []
  for spot_index in range(1, 0x78+1):
    bgm_info = read_u32(dol_data, address_to_offset(stage_bgm_info_list_start + spot_index*4))
    if ((bgm_info & 0xFFFF0000) >> 16) in SILENT_BGM_IDS:
      # Don't include silent BGMs
      continue
    if bgm_info in valid_bgm_infos:
      # Don't include the exact same BGM info more than once
      continue
    valid_bgm_infos.append(bgm_info)
  for island_num in range(1, 49+1):
    bgm_info = read_u32(dol_data, address_to_offset(island_bgm_info_list_start + island_num*4))
    if ((bgm_info & 0xFFFF0000) >> 16) in SILENT_BGM_IDS:
      # Don't include silent BGMs
      continue
    if bgm_info in valid_bgm_infos:
      # Don't include the exact same BGM info more than once
      continue
    valid_bgm_infos.append(bgm_info)
  
  valid_bgm_infos += EXTRA_BGM_INFOS
  
  for spot_index in range(1, 0x78+1):
    bgm_info = self.rng.choice(valid_bgm_infos)
    write_u32(dol_data, address_to_offset(stage_bgm_info_list_start + spot_index*4), bgm_info)
    #print("Setting spot ID %d to BGM info %08X" % (spot_index, bgm_info))
  for island_num in range(1, 49+1):
    bgm_info = self.rng.choice(valid_bgm_infos)
    write_u32(dol_data, address_to_offset(island_bgm_info_list_start + island_num*4), bgm_info)
    #print("Setting island number %d to BGM info %08X" % (island_num, bgm_info))
