
from fs_helpers import *
from tweaks import address_to_offset

def randomize_bgm(self):
  dol_data = self.get_raw_file("sys/main.dol")
  stage_bgm_info_list_start = 0x8039C30C
  island_bgm_info_list_start = 0x8039C4F0
  spot_name_list_start = 0x8039C5B8
  
  spot_id_to_name = {}
  for i in range(0x78):
    spot_name_ptr = read_u32(dol_data, address_to_offset(spot_name_list_start + i*4))
    spot_name = read_str_until_null_character(dol_data, address_to_offset(spot_name_ptr))
    spot_id = i + 1
    spot_id_to_name[spot_id] = spot_name
    #print("% 4d %02X %s" % (spot_id, spot_id, spot_name))
  
  valid_bgm_infos = []
  for spot_index in range(1, 0x78+1):
    bgm_info = read_u32(dol_data, address_to_offset(stage_bgm_info_list_start + spot_index*4))
    print("%08X - %s" % (bgm_info, spot_id_to_name[spot_index]))
    if bgm_info & 0xFFFF0000 == 0:
      # Don't include blank BGMs (BGM ID 0)
      continue
    if bgm_info in valid_bgm_infos:
      # Don't include the exact same BGM info more than once
      continue
    valid_bgm_infos.append(bgm_info)
  for island_num in range(1, 49+1):
    bgm_info = read_u32(dol_data, address_to_offset(island_bgm_info_list_start + island_num*4))
    print("%08X - %s" % (bgm_info, self.island_number_to_name[island_num]))
    if bgm_info & 0xFFFF0000 == 0:
      # Don't include blank BGMs (BGM ID 0)
      continue
    if bgm_info in valid_bgm_infos:
      # Don't include the exact same BGM info more than once
      continue
    valid_bgm_infos.append(bgm_info)
  
  for spot_index in range(1, 0x78+1):
    bgm_info = self.rng.choice(valid_bgm_infos)
    write_u32(dol_data, address_to_offset(stage_bgm_info_list_start + spot_index*4), bgm_info)
    print("Setting spot ID %d to BGM info %08X" % (spot_index, bgm_info))
  for island_num in range(1, 49+1):
    bgm_info = self.rng.choice(valid_bgm_infos)
    write_u32(dol_data, address_to_offset(island_bgm_info_list_start + island_num*4), bgm_info)
    print("Setting island number %d to BGM info %08X" % (island_num, bgm_info))
