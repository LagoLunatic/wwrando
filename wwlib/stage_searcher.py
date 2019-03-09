
import re
from collections import OrderedDict

def each_stage_and_room(self, exclude_stages=False, exclude_rooms=False, stage_name_to_limit_to=None):
  all_filenames = list(self.gcm.files_by_path.keys())
  
  # Sort the file names for determinism. And use natural sorting so the room numbers are in order.
  try_int_convert = lambda string: int(string) if string.isdigit() else string
  all_filenames.sort(key=lambda filename: [try_int_convert(c) for c in re.split("([0-9]+)", filename)])
  
  all_stage_arc_paths = []
  all_room_arc_paths = []
  for filename in all_filenames:
    stage_match = re.search(r"files/res/Stage/([^/]+)/Stage.arc", filename, re.IGNORECASE)
    room_match = re.search(r"files/res/Stage/([^/]+)/Room\d+.arc", filename, re.IGNORECASE)
    
    if stage_match and exclude_stages:
      continue
    if room_match and exclude_rooms:
      continue
    
    if stage_match:
      stage_name = stage_match.group(1)
      if self.stage_names[stage_name] in ["Unused", "Broken"]:
        # Don't iterate through unused stages. Not only would they be useless, but some unused stages have slightly different stage formats that the rando can't read.
        continue
      if stage_name_to_limit_to and stage_name_to_limit_to != stage_name:
        continue
      all_stage_arc_paths.append(filename)
    
    if room_match:
      stage_name = room_match.group(1)
      if self.stage_names[stage_name] in ["Unused", "Broken"]:
        # Don't iterate through unused stages. Not only would they be useless, but some unused stages have slightly different stage formats that the rando can't read.
        continue
      if stage_name_to_limit_to and stage_name_to_limit_to != stage_name:
        continue
      all_room_arc_paths.append(filename)
  
  for stage_arc_path in all_stage_arc_paths:
    dzs = self.get_arc(stage_arc_path).get_file("stage.dzs")
    if dzs is None:
      continue
    yield(dzs, stage_arc_path)
  for room_arc_path in all_room_arc_paths:
    dzr = self.get_arc(room_arc_path).get_file("room.dzr")
    if dzr is None:
      continue
    yield(dzr, room_arc_path)

def each_stage(self):
  return each_stage_and_room(self, exclude_rooms=True)

def each_room(self):
  return each_stage_and_room(self, exclude_stages=True)

def each_stage_with_rooms(self):
  for dzs, stage_arc_path in each_stage(self):
    match = re.search(r"files/res/Stage/([^/]+)/Stage.arc", stage_arc_path, re.IGNORECASE)
    stage_name = match.group(1)
    
    rooms = []
    for dzr, room_arc_path in each_stage_and_room(self, exclude_stages=True, stage_name_to_limit_to=stage_name):
      rooms.append((dzr, room_arc_path))
    yield(dzs, stage_arc_path, rooms)

def print_all_used_item_pickup_flags(self):
  used_item_flags_by_stage_id = {}
  for dzs, stage_arc_path, rooms in each_stage_with_rooms(self):
    stage_info = dzs.entries_by_type("STAG")[0]
    stage_id = stage_info.stage_id
    if stage_id not in used_item_flags_by_stage_id:
      used_item_flags_by_stage_id[stage_id] = []
    
    for dzx, arc_path in [(dzs, stage_arc_path)]+rooms:
      items = [actor for actor in dzx.entries_by_type("ACTR") if actor.is_item()]
      pots = [actor for actor in dzx.entries_by_type("ACTR") if actor.is_pot()]
      
      for item in items:
        if item.item_flag == 0xFF:
          continue
        item_name = self.item_names[item.item_id]
        used_item_flags_by_stage_id[stage_id].append((item.item_flag, item_name, arc_path))
      for pot in pots:
        if pot.pot_item_flag == 0x7F:
          continue
        if pot.pot_item_id < 0x20:
          item_name = self.item_names[pot.pot_item_id]
        else:
          item_name = "Pot drop type 0x%02X" % pot.pot_item_id
        used_item_flags_by_stage_id[stage_id].append((pot.pot_item_flag, item_name, arc_path))
  
  used_item_flags_by_stage_id = OrderedDict(sorted(
    used_item_flags_by_stage_id.items(), key=lambda x: x[0]
  ))
  print()
  print("Item flags:")
  for stage_id, item_flags in used_item_flags_by_stage_id.items():
    print("Stage ID: %02X" % stage_id)
    item_flags.sort(key=lambda tuple: tuple[0])
    for item_flag, item_name, arc_path in item_flags:
      arc_path_short = arc_path[len("files/res/Stage/"):-len(".arc")]
      print("  %02X (Item: %s) in %s" % (item_flag, item_name, arc_path_short))

def print_all_used_chest_open_flags(self):
  used_chest_flags_by_stage_id = {}
  used_chest_flags_by_stage_id[1] = []
  for dzs, stage_arc_path, rooms in each_stage_with_rooms(self):
    stage_info = dzs.entries_by_type("STAG")[0]
    stage_id = stage_info.stage_id
    if stage_id not in used_chest_flags_by_stage_id:
      used_chest_flags_by_stage_id[stage_id] = []
    
    for dzx, arc_path in [(dzs, stage_arc_path)]+rooms:
      chests = dzx.entries_by_type("TRES")
      
      for chest in chests:
        if chest.item_id in self.item_names:
          item_name = self.item_names[chest.item_id]
        else:
          item_name = "INVALID ID 0x%02X" % chest.item_id
        if chest.behavior_type in [7, 8]:
          stage_id_for_chest = 1
        else:
          stage_id_for_chest = stage_id
        used_chest_flags_by_stage_id[stage_id_for_chest].append((chest.opened_flag, item_name, arc_path))
  
  used_chest_flags_by_stage_id = OrderedDict(sorted(
    used_chest_flags_by_stage_id.items(), key=lambda x: x[0]
  ))
  print()
  print("Chest opened flags:")
  for stage_id, chest_flags in used_chest_flags_by_stage_id.items():
    print("Stage ID: %02X" % stage_id)
    chest_flags.sort(key=lambda tuple: tuple[0])
    for chest_flag, item_name, arc_path in chest_flags:
      arc_path_short = arc_path[len("files/res/Stage/"):-len(".arc")]
      print("  %02X (Item: %s) in %s" % (chest_flag, item_name, arc_path_short))

def print_all_event_flags_used_by_stb_cutscenes(self):
  print()
  print("Event flags:")
  for dzs, stage_arc_path in each_stage(self):
    event_list = self.get_arc(stage_arc_path).get_file("event_list.dat")
    for event in event_list.events:
      package = [x for x in event.actors if x.name == "PACKAGE"]
      if package:
        package = package[0]
        play = next(x for x in package.actions if x.name == "PLAY")
        prop = play.get_prop("EventFlag")
        if prop:
          print("Event name: %s" % event.name)
          print("  Event flag: %04X" % prop.value)
          print("  File path: " + stage_arc_path)

def print_all_event_list_actions(self):
  # Build a list of all actions used by all actors in the game.
  all_actors = OrderedDict()
  
  for dzs, stage_arc_path, rooms in each_stage_with_rooms(self):
    stage_arc = self.get_arc(stage_arc_path)
    event_list = stage_arc.get_file("event_list.dat")
    if event_list is None:
      continue
    
    for event in event_list.events:
      for actor in event.actors:
        if actor.name not in all_actors:
          all_actors[actor.name] = OrderedDict()
        
        for action in actor.actions:
          if action.name not in all_actors[actor.name]:
            all_actors[actor.name][action.name] = OrderedDict()
          
          for prop in action.properties:
            if prop.name not in all_actors[actor.name][action.name]:
              all_actors[actor.name][action.name][prop.name] = []
            
            if prop.value not in all_actors[actor.name][action.name][prop.name]:
              all_actors[actor.name][action.name][prop.name].append(prop.value)
  
  # Sort everything alphanumerically instead of by the order they first appeared in the game's files.
  all_actors = OrderedDict(sorted(all_actors.items(), key=lambda x: x[0]))
  for actor_name, actions in all_actors.items():
    actions = OrderedDict(sorted(actions.items(), key=lambda x: x[0]))
    all_actors[actor_name] = actions
    for action_name, props in actions.items():
      props = OrderedDict(sorted(props.items(), key=lambda x: x[0]))
      all_actors[actor_name][action_name] = props
      #for prop_name, values in props.items():
      #  values.sort(key=lambda x: repr(x)) # ???
  
  with open("All Event List Actions - With Property Examples.txt", "w") as f:
    for actor_name, actions in all_actors.items():
      f.write("%s:\n" % actor_name)
      for action_name, props in actions.items():
        f.write("  %s:\n" % action_name)
        for prop_name, values in props.items():
          f.write("    %s:\n" % prop_name)
          for value in values:
            f.write("      " + repr(value) + "\n")
  
  with open("All Event List Actions.txt", "w") as f:
    for actor_name, actions in all_actors.items():
      f.write("%s:\n" % actor_name)
      for action_name, props in actions.items():
        f.write("  %s:\n" % action_name)
        for prop_name, values in props.items():
          f.write("    %s\n" % prop_name)

def print_stages_for_each_stage_id(self):
  stage_names_by_stage_id = {}
  for dzs, stage_arc_path, rooms in each_stage_with_rooms(self):
    stage_info = dzs.entries_by_type("STAG")[0]
    stage_id = stage_info.stage_id
    if stage_id not in stage_names_by_stage_id:
      stage_names_by_stage_id[stage_id] = []
    
    match = re.search(r"files/res/Stage/([^/]+)/Stage.arc", stage_arc_path, re.IGNORECASE)
    stage_name = match.group(1)
    stage_names_by_stage_id[stage_id].append(stage_name)
  
  stage_names_by_stage_id = OrderedDict(sorted(
    stage_names_by_stage_id.items(), key=lambda x: x[0]
  ))
  print()
  print("Stages with each stage ID:")
  for stage_id, stage_names in stage_names_by_stage_id.items():
    print("Stage ID: %02X" % stage_id)
    stage_names.sort(key=lambda tuple: tuple[0])
    for stage_name in stage_names:
      print("  %s" % (stage_name))

def print_item_table(self):
  item_table_data = self.get_raw_file("files/res/ItemTable/item_table.bin")
  num_entries = read_u16(item_table_data, 0xA)
  
  with open("Item Table.txt", "w") as f:
    for i in range(num_entries):
      drop_chances = OrderedDict()
      offset = 0x10 + i*0x10
      for j in range(0x10):
        item_id = read_u8(item_table_data, offset + j)
        if item_id == 0xFF:
          item_name = "(Nothing)"
        else:
          item_name = self.item_names[item_id]
        
        if item_name not in drop_chances:
          drop_chances[item_name] = 0
        drop_chances[item_name] += 1
        
      f.write("Drop type 0x%02X:\n" % (0x20+i))
      for item_name, chance in drop_chances.items():
        f.write("  % 6.2f%% %s\n" % (chance/0x10*100, item_name))

def print_actor_info(self):
  actor_id_to_rel_filename_mapping_offset = tweaks.address_to_offset(0x803398D8) # DynamicNameTable
  actr_name_to_actor_info_mapping_offset = tweaks.address_to_offset(0x80372818) # l_objectName
  dol_data = self.get_raw_file("sys/main.dol")
  
  actor_id_to_rel_filename = {}
  
  i = 0
  while True:
    offset = actor_id_to_rel_filename_mapping_offset + i*8
    actor_id = read_u16(dol_data, offset)
    if actor_id == 0xFFFF:
      break # End marker
    if actor_id in actor_id_to_rel_filename:
      print("Warning, duplicate actor ID in rel filename list: %04X" % padding)
    padding = read_u16(dol_data, offset+2)
    if padding != 0:
      print("Warning, nonzero padding: %04X" % padding)
    
    rel_filename_pointer = read_u32(dol_data, offset+4)
    rel_filename_offset = tweaks.address_to_offset(rel_filename_pointer)
    rel_filename = read_str_until_null_character(dol_data, rel_filename_offset)
    
    actor_id_to_rel_filename[actor_id] = rel_filename
    
    i += 1
  
  with open("Actor Info.txt", "w") as f:
    for i in range(0x339):
      offset = actr_name_to_actor_info_mapping_offset + i*0xC
      
      actr_name = read_str(dol_data, offset, 8)
      actor_id = read_u16(dol_data, offset+8)
      subtype_index = read_u8(dol_data, offset+0xA)
      unknown = read_u8(dol_data, offset+0xB)
      
      if actor_id in actor_id_to_rel_filename:
        rel_filename = actor_id_to_rel_filename[actor_id]
      else:
        rel_filename = "[none]"
      
      f.write("%7s:   ID %04X,   Subtype %02X,   Unknown %02X,   REL %s\n" % (
        actr_name,
        actor_id,
        subtype_index,
        unknown,
        rel_filename
      ))
