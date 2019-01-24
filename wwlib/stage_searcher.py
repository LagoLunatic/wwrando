
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
  print("Item flags:")
  for stage_id, item_flags in used_item_flags_by_stage_id.items():
    print("Stage id: %02X" % stage_id)
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
    if stage_id == 9:
      print(stage_arc_path)
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
    print("Stage id: %02X" % stage_id)
    chest_flags.sort(key=lambda tuple: tuple[0])
    for chest_flag, item_name, arc_path in chest_flags:
      arc_path_short = arc_path[len("files/res/Stage/"):-len(".arc")]
      print("  %02X (Item: %s) in %s" % (chest_flag, item_name, arc_path_short))

def print_all_event_flags_used_by_stb_cutscenes(self):
  for dzs, stage_arc_path in each_stage(self):
    event_list = self.get_arc(stage_arc_path).get_file("event_list.dat")
    for event in event_list.events:
      package = [x for x in event.actors if x.name == "PACKAGE"]
      if package:
        package = package[0]
        play = next(x for x in package.actions if x.name == "PLAY")
        prop = play.get_prop("EventFlag")
        if prop:
          print(stage_arc_path)
          print(event.name)
          print("%04X" % prop.value)
          print()
