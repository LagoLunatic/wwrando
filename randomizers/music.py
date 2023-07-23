
from collections import OrderedDict

from gclib import fs_helpers as fs

from randomizers.music_constants import *

def randomize_music(self):
  stage_bgm_info_list_start = 0x8039C30C
  island_bgm_info_list_start = 0x8039C4F0
  
  
  jaiseqs = self.get_arc("files/Audiores/Seqs/JaiSeqs.arc")
  
  bgm_name_to_file_id = {}
  bgm_file_id_to_name = {}
  for file in jaiseqs.file_entries:
    if file.is_dir:
      continue
    bgm_name_to_file_id[file.name] = file.id
    bgm_file_id_to_name[file.id] = file.name
  
  
  aaf_data = self.get_raw_file("files/Audiores/JaiInit.aaf")
  bgm_category_index = 0x10
  
  sound_categories_offset = fs.read_u32(aaf_data, 4)
  num_bgms = fs.read_u16(aaf_data, sound_categories_offset+6 + bgm_category_index*4 + 0)
  first_bgm_sound_index = fs.read_u16(aaf_data, sound_categories_offset+6 + bgm_category_index*4 + 2)
  first_sound_info_offset = sound_categories_offset + 0x50
  
  bgm_index_to_name = {}
  bgm_name_to_index = {}
  for bgm_index in range(num_bgms):
    sound_index = first_bgm_sound_index + bgm_index
    file_id = fs.read_u16(aaf_data, first_sound_info_offset + sound_index*0x10 + 6)
    bgm_name = bgm_file_id_to_name[file_id]
    bgm_index_to_name[bgm_index] = bgm_name
    bgm_name_to_index[bgm_name] = bgm_index
  
  
  # First we initialize the list of what a BGM can be replaced with to all other BGMs in the same group as it.
  # We will later filter these lists down.
  bgm_replacements_that_work = OrderedDict()
  for bgm_randomization_group in BGM_RANDOMIZATION_GROUPS:
    for bgm_name in bgm_randomization_group:
      bgm_replacements_that_work[bgm_name] = bgm_randomization_group.copy()
  
  all_stage_names_that_use_bgm = OrderedDict()
  all_island_nums_that_use_bgm = OrderedDict()
  for bgm_name in bgm_name_to_index:
    all_stage_names_that_use_bgm[bgm_name] = []
    all_island_nums_that_use_bgm[bgm_name] = []
  
  def filter_invalid_replacements_for_location(
    bgm_info_pointer,
    loc_needed_first_scene_wave,
    loc_needed_second_scene_wave,
    hardcoded_bgm_names
  ):
    orig_default_bgm_id = self.dol.read_data(fs.read_u16, bgm_info_pointer + 0)
    
    if orig_default_bgm_id >= 0x0100:
      orig_default_bgm_index = SPECIAL_BGM_ID_TO_BGM_INDEX[orig_default_bgm_id]
    else:
      orig_default_bgm_index = orig_default_bgm_id
    
    if orig_default_bgm_index == 0x0000:
      # Maybe assign a default BGM index for places like islands that originally had none
      pass
    
    orig_default_bgm_name = bgm_index_to_name[orig_default_bgm_index]
    
    orig_bgm_names_for_location = hardcoded_bgm_names.copy()
    if orig_default_bgm_name != "defaultse.bms" and orig_default_bgm_name not in orig_bgm_names_for_location:
      orig_bgm_names_for_location.append(orig_default_bgm_name)
    
    for orig_bgm_name in orig_bgm_names_for_location:
      # Don't put a BGM here that needs a scene wave if this location also needs a scene wave in that same first/second slot.
      if loc_needed_first_scene_wave is not None:
        for bgm_name, bgm_needed_first_scene_wave in FIRST_SCENE_WAVE_NEEDED_FOR_BGM.items():
          if bgm_needed_first_scene_wave != loc_needed_first_scene_wave:
            if bgm_name in bgm_replacements_that_work[orig_bgm_name]:
              bgm_replacements_that_work[orig_bgm_name].remove(bgm_name)
      
      if loc_needed_second_scene_wave is not None:
        for bgm_name, bgm_needed_second_scene_wave in SECOND_SCENE_WAVE_NEEDED_FOR_BGM.items():
          if bgm_needed_second_scene_wave != loc_needed_second_scene_wave:
            if bgm_name in bgm_replacements_that_work[orig_bgm_name]:
              bgm_replacements_that_work[orig_bgm_name].remove(bgm_name)
    
    return orig_bgm_names_for_location
  
  
  # Also keep track of the randomly determined first/second scene waves for each location.
  decided_first_scene_wave_for_stage = {}
  decided_first_scene_wave_for_island = {}
  decided_second_scene_wave_for_stage = {}
  decided_second_scene_wave_for_island = {}
  
  stage_name_to_bgm_info_pointer = OrderedDict()
  island_num_to_bgm_info_pointer = OrderedDict()
  
  for spot_index in range(1, 0x78+1):
    if spot_index <= 0:
      stage_name = "[NULL]"
    else:
      stage_name_address = self.dol.read_data(fs.read_u32, 0x8039C5B8 + (spot_index-1)*4)
      stage_name = self.dol.read_data(fs.read_str_until_null_character, stage_name_address)
    
    first_scene_wave = FIRST_SCENE_WAVE_NEEDED_FOR_STAGE.get(stage_name)
    second_scene_wave = SECOND_SCENE_WAVE_NEEDED_FOR_STAGE.get(stage_name)
    hardcoded_bgm_names = BGMS_HARDCODED_TO_PLAY_FOR_STAGE.get(stage_name, [])
    
    decided_first_scene_wave_for_stage[stage_name] = first_scene_wave
    decided_second_scene_wave_for_stage[stage_name] = second_scene_wave
    
    bgm_info_pointer = stage_bgm_info_list_start + spot_index*4
    
    stage_name_to_bgm_info_pointer[stage_name] = bgm_info_pointer
    
    orig_bgm_names_for_location = filter_invalid_replacements_for_location(
      bgm_info_pointer, first_scene_wave, second_scene_wave, hardcoded_bgm_names
    )
    
    for bgm_name in orig_bgm_names_for_location:
      all_stage_names_that_use_bgm[bgm_name].append(stage_name)
  
  for island_num in range(1, 49+1):
    first_scene_wave = FIRST_SCENE_WAVE_NEEDED_FOR_ISLAND.get(island_num)
    second_scene_wave = SECOND_SCENE_WAVE_NEEDED_FOR_ISLAND.get(island_num)
    hardcoded_bgm_names = BGMS_HARDCODED_TO_PLAY_FOR_ISLAND.get(island_num, [])
    
    decided_first_scene_wave_for_island[island_num] = first_scene_wave
    decided_second_scene_wave_for_island[island_num] = second_scene_wave
    
    bgm_info_pointer = island_bgm_info_list_start + island_num*4
    
    island_num_to_bgm_info_pointer[island_num] = bgm_info_pointer
    
    orig_bgm_names_for_location = filter_invalid_replacements_for_location(
      bgm_info_pointer, first_scene_wave, second_scene_wave, hardcoded_bgm_names
    )
    
    for bgm_name in orig_bgm_names_for_location:
      all_island_nums_that_use_bgm[bgm_name].append(island_num)
  
  
  def check_bgm_conflicts_with_orig_bgm(bgm_name, orig_bgm_name):
    if bgm_name in FIRST_SCENE_WAVE_NEEDED_FOR_BGM:
      new_first_wave_index = FIRST_SCENE_WAVE_NEEDED_FOR_BGM[bgm_name]
      
      for stage_name in all_stage_names_that_use_bgm[orig_bgm_name]:
        decided_first_wave = decided_first_scene_wave_for_stage[stage_name]
        if decided_first_wave is not None and decided_first_wave != new_first_wave_index:
          return True
      
      for island_num in all_island_nums_that_use_bgm[orig_bgm_name]:
        decided_first_wave = decided_first_scene_wave_for_island[island_num]
        if decided_first_wave is not None and decided_first_wave != new_first_wave_index:
          return True
    
    if bgm_name in SECOND_SCENE_WAVE_NEEDED_FOR_BGM:
      new_second_wave_index = SECOND_SCENE_WAVE_NEEDED_FOR_BGM[bgm_name]
      
      for stage_name in all_stage_names_that_use_bgm[orig_bgm_name]:
        decided_second_wave = decided_second_scene_wave_for_stage[stage_name]
        if decided_second_wave is not None and decided_second_wave != new_second_wave_index:
          return True
      
      for island_num in all_island_nums_that_use_bgm[orig_bgm_name]:
        decided_second_wave = decided_second_scene_wave_for_island[island_num]
        if decided_second_wave is not None and decided_second_wave != new_second_wave_index:
          return True
    
    # No conflicts found
    return False
  
  
  orig_sound_infos = []
  for bgm_index in range(num_bgms):
    sound_index = first_bgm_sound_index + bgm_index
    sound_info_bytes = fs.read_bytes(aaf_data, first_sound_info_offset + sound_index*0x10, 0x10)
    orig_sound_infos.append(sound_info_bytes)
  
  # TODO: don't allow replacing BGMs that can happen anywhere (like item get, common enemy fight, sailing, etc) with BGMs that require specific scene waves to work
  # (though is there maybe some way to allow that to work...? having dragon roost island music for sailing for example would be great. maybe for sailing, have a 20% chance per seed that the first scene wave for ALL islands is just set to one for a specific BGM...? but that wouldn't work well for FF or windfall, which require a first scene wave for other purposes...)
  
  used_bgm_names = []
  for orig_bgm_name, new_possible_bgm_names in bgm_replacements_that_work.items():
    #print(orig_bgm_name)
    #print(new_possible_bgm_names)
    
    if orig_bgm_name not in new_possible_bgm_names:
      raise Exception("BGM \"%s\" cannot be replaced with itself?" % orig_bgm_name)
    if len(new_possible_bgm_names) == 1:
      raise Exception("BGM \"%s\" only has 1 valid replacement" % orig_bgm_name)
    
    new_possible_bgm_names = [
      bgm_name for bgm_name in new_possible_bgm_names
      if not check_bgm_conflicts_with_orig_bgm(bgm_name, orig_bgm_name)
    ]
    
    #print(new_possible_bgm_names)
    
    if not new_possible_bgm_names:
      raise Exception("BGM \"%s\" has no valid replacements" % orig_bgm_name)
    
    # Try to limit using the same BGM in multiple places when possible.
    new_possible_bgm_names_not_used_yet = [
      bgm_name for bgm_name in new_possible_bgm_names
      if bgm_name not in used_bgm_names
    ]
    if new_possible_bgm_names_not_used_yet:
      new_possible_bgm_names = new_possible_bgm_names_not_used_yet
    
    new_bgm_name = self.rng.choice(new_possible_bgm_names)
    
    orig_bgm_index = bgm_name_to_index[orig_bgm_name]
    new_bgm_index = bgm_name_to_index[new_bgm_name]
    
    if new_bgm_name not in used_bgm_names:
      used_bgm_names.append(new_bgm_name)
    
    #print("%s -> %s" % (orig_bgm_name, new_bgm_name))
    
    sound_index = first_bgm_sound_index + orig_bgm_index
    new_sound_info_bytes = orig_sound_infos[new_bgm_index]
    fs.write_bytes(aaf_data, first_sound_info_offset + sound_index*0x10, new_sound_info_bytes)
    
    
    # Assign the first/second waves to load for all stages/islands that use this BGM.
    if new_bgm_name in FIRST_SCENE_WAVE_NEEDED_FOR_BGM:
      new_first_wave_index = FIRST_SCENE_WAVE_NEEDED_FOR_BGM[new_bgm_name]
      
      for stage_name in all_stage_names_that_use_bgm[orig_bgm_name]:
        decided_first_wave = decided_first_scene_wave_for_stage[stage_name]
        if decided_first_wave is not None and decided_first_wave != new_first_wave_index:
          raise Exception("Tried to assign two first scene waves to stage %s" % stage_name)
        decided_first_scene_wave_for_stage[stage_name] = new_first_wave_index
      
      for island_num in all_island_nums_that_use_bgm[orig_bgm_name]:
        decided_first_wave = decided_first_scene_wave_for_island[island_num]
        if decided_first_wave is not None and decided_first_wave != new_first_wave_index:
          raise Exception("Tried to assign two first scene waves to island %d" % island_num)
        decided_first_scene_wave_for_island[island_num] = new_first_wave_index
    
    if new_bgm_name in SECOND_SCENE_WAVE_NEEDED_FOR_BGM:
      new_second_wave_index = SECOND_SCENE_WAVE_NEEDED_FOR_BGM[new_bgm_name]
      
      for stage_name in all_stage_names_that_use_bgm[orig_bgm_name]:
        decided_second_wave = decided_second_scene_wave_for_stage[stage_name]
        if decided_second_wave is not None and decided_second_wave != new_second_wave_index:
          raise Exception("Tried to assign two second scene waves to stage %s" % stage_name)
        decided_second_scene_wave_for_stage[stage_name] = new_second_wave_index
      
      for island_num in all_island_nums_that_use_bgm[orig_bgm_name]:
        decided_second_wave = decided_second_scene_wave_for_island[island_num]
        if decided_second_wave is not None and decided_second_wave != new_second_wave_index:
          raise Exception("Tried to assign two second scene waves to island %d" % island_num)
        decided_second_scene_wave_for_island[island_num] = new_second_wave_index
  
  
  # Update the first/second scene waves loaded for each stage/island.
  for stage_name, bgm_info_pointer in stage_name_to_bgm_info_pointer.items():
    first_wave_index = decided_first_scene_wave_for_stage[stage_name]
    if first_wave_index is None:
      first_wave_index = 0
    self.dol.write_data(fs.write_u8, bgm_info_pointer + 2, first_wave_index)
    
    second_wave_index = decided_second_scene_wave_for_stage[stage_name]
    if second_wave_index is None:
      second_wave_index = 0
    self.dol.write_data(fs.write_u8, bgm_info_pointer + 3, second_wave_index)
  
  for island_num, bgm_info_pointer in island_num_to_bgm_info_pointer.items():
    first_wave_index = decided_first_scene_wave_for_island[island_num]
    if first_wave_index is None:
      first_wave_index = 0
    self.dol.write_data(fs.write_u8, bgm_info_pointer + 2, first_wave_index)
    
    second_wave_index = decided_second_scene_wave_for_island[island_num]
    if second_wave_index is None:
      second_wave_index = 0
    self.dol.write_data(fs.write_u8, bgm_info_pointer + 3, second_wave_index)
