
import re

def each_stage_and_room(self, exclude_stages=False, exclude_rooms=False):
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
      all_stage_arc_paths.append(filename)
    
    if room_match:
      stage_name = room_match.group(1)
      if self.stage_names[stage_name] in ["Unused", "Broken"]:
        # Don't iterate through unused stages. Not only would they be useless, but some unused stages have slightly different stage formats that the rando can't read.
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
