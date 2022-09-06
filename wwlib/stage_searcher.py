
import os
import re
from collections import OrderedDict

from fs_helpers import *

from data_tables import DataTables
from wwlib.dzb import DZB
from wwlib.j3d import BMD, BDL, BPRegister, XFRegister

def try_int_convert(string):
  if string.isdigit():
    return int(string)
  else:
    return string

def split_string_for_natural_sort(string):
  return [try_int_convert(c) for c in re.split("([0-9]+)", string)]

def each_stage_and_room(self, exclude_stages=False, exclude_rooms=False, stage_name_to_limit_to=None, exclude_unused=True):
  all_filenames = list(self.gcm.files_by_path.keys())
  
  # Sort the file names for determinism. And use natural sorting so the room numbers are in order.
  all_filenames.sort(key=lambda filename: split_string_for_natural_sort(filename))
  
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
      if self.stage_names[stage_name] == "Broken" or (exclude_unused and self.stage_names[stage_name] == "Unused"):
        # Don't iterate through unused stages. Not only would they be useless, but some unused stages have slightly different stage formats that the rando can't read.
        continue
      if stage_name_to_limit_to and stage_name_to_limit_to != stage_name:
        continue
      all_stage_arc_paths.append(filename)
    
    if room_match:
      stage_name = room_match.group(1)
      if self.stage_names[stage_name] == "Broken" or (exclude_unused and self.stage_names[stage_name] == "Unused"):
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

def each_stage(self, exclude_unused=True):
  return each_stage_and_room(self, exclude_rooms=True, exclude_unused=exclude_unused)

def each_room(self, exclude_unused=True):
  return each_stage_and_room(self, exclude_stages=True, exclude_unused=exclude_unused)

def each_stage_with_rooms(self, exclude_unused=True):
  for dzs, stage_arc_path in each_stage(self, exclude_unused=exclude_unused):
    match = re.search(r"files/res/Stage/([^/]+)/Stage.arc", stage_arc_path, re.IGNORECASE)
    stage_name = match.group(1)
    
    rooms = []
    for dzr, room_arc_path in each_stage_and_room(self, exclude_stages=True, stage_name_to_limit_to=stage_name, exclude_unused=exclude_unused):
      rooms.append((dzr, room_arc_path))
    yield(dzs, stage_arc_path, rooms)

def print_all_used_switches(self):
  used_switches_by_stage_id = {}
  used_switches_by_stage_id_unused = {}
  def add_used_switch(switch, stage_id, stage_name, room_no, location_identifier, is_unused):
    if is_unused:
      used_switches_list = used_switches_by_stage_id_unused
    else:
      used_switches_list = used_switches_by_stage_id
    
    if room_no is None:
      room_arc_path_short = None
    else:
      room_arc_path_short = "%s/Room%d" % (stage_name, room_no)
    
    if switch < 0xE0: # Only door-cleared zone bit switches (E0-EF) are local to the room
      room_arc_path_short = None
    
    if stage_id not in used_switches_list:
      used_switches_list[stage_id] = {}
    if room_arc_path_short not in used_switches_list[stage_id]:
      used_switches_list[stage_id][room_arc_path_short] = []
    
    used_switches_list[stage_id][room_arc_path_short].append((switch, location_identifier))
  
  for dzs, stage_arc_path, rooms in each_stage_with_rooms(self, exclude_unused=False):
    match = re.search(r"files/res/Stage/([^/]+)/Stage.arc", stage_arc_path, re.IGNORECASE)
    stage_name = match.group(1)
    stage_info = dzs.entries_by_type("STAG")[0]
    stage_id = stage_info.stage_id
    
    if self.stage_names[stage_name] == "Unused":
      is_unused = True
    else:
      is_unused = False
    
    for dzx, arc_path in [(dzs, stage_arc_path)]+rooms:
      arc_path_short = arc_path[len("files/res/Stage/"):-len(".arc")]
      _, arc_name = arc_path_short.split("/", 1)
      room_match = re.search(r"^Room(\d+)$", arc_name, re.IGNORECASE)
      if room_match:
        room_no = int(room_match.group(1))
      else: # Stage.arc
        room_no = None
      
      if stage_name in ["H_test", "DmSpot0", "morocam"]:
        # Uses an old EVNT format, cannot be read.
        evnts = []
      else:
        evnts = dzx.entries_by_type("EVNT")
      
      for evnt in evnts:
        switch = evnt.event_seen_switch_index
        if switch == 0xFF:
          continue
        
        location_identifier = " from % 15s" % evnt.name
        location_identifier += "  in " + arc_path_short
        location_identifier += " (Event)"
        
        add_used_switch(switch, stage_id, stage_name, evnt.room_index, location_identifier, is_unused)
      
      for layer in [None] + list(range(11+1)):
        actors = []
        actors += dzx.entries_by_type_and_layer("ACTR", layer)
        actors += dzx.entries_by_type_and_layer("TGOB", layer)
        actors += dzx.entries_by_type_and_layer("TRES", layer)
        actors += dzx.entries_by_type_and_layer("PLYR", layer)
        actors += dzx.entries_by_type_and_layer("SCOB", layer)
        actors += dzx.entries_by_type_and_layer("TGSC", layer)
        actors += dzx.entries_by_type_and_layer("DOOR", layer)
        actors += dzx.entries_by_type_and_layer("TGDR", layer)
        
        for actor in actors:
          if actor.name not in DataTables.actor_name_to_class_name:
            continue
          class_name = DataTables.actor_name_to_class_name[actor.name]
          
          location_identifier = " from % 15s" % actor.name
          location_identifier += "  in " + arc_path_short
          if layer is not None:
            location_identifier += "/Layer%X" % layer
          
          #param_bitfield_masks_unused = {}
          #param_bitfield_values_unused = {}
          #for field_name in ["params", "x_rot", "z_rot"]:
          #  if field_name == "params":
          #    param_bitfield_masks_unused[field_name] = 0xFFFFFFFF
          #  else:
          #    param_bitfield_masks_unused[field_name] = 0xFFFF
          #  param_bitfield_values_unused[field_name] = getattr(actor, field_name)
          #for attr_name in actor.param_fields:
          #  params_bitfield_name, mask = actor.param_fields[attr_name]
          #  param_bitfield_masks_unused[params_bitfield_name] &= ~mask
          #  param_bitfield_values_unused[params_bitfield_name] &= ~mask
          #
          #any_field_is_not_null = False
          #for field_name in ["params", "x_rot", "z_rot"]:
          #  if param_bitfield_values_unused[field_name] not in [0, param_bitfield_masks_unused[field_name]]:
          #    any_field_is_not_null = True
          #if any_field_is_not_null:
          #  print(actor.name)
          #  print("params:       %08X" % param_bitfield_values_unused["params"])
          #  print("x_rot: %04X" % param_bitfield_values_unused["x_rot"])
          #  print("z_rot: %04X" % param_bitfield_values_unused["z_rot"])
          #  print()
          
          # Hardcoded switches.
          if class_name == "d_a_npc_ah":
            if actor.message_id == 2: # Message ID 14003
              add_used_switch(0x6C, stage_id, stage_name, room_no, location_identifier, is_unused)
            elif actor.message_id == 5: # Message ID 14006
              add_used_switch(0x10, stage_id, stage_name, room_no, location_identifier, is_unused)
          
          for attr_name in actor.param_fields:
            stage_id_for_param = stage_id
            room_no_for_param = room_no
            
            params_bitfield_name, mask = actor.param_fields[attr_name]
            amount_to_shift = actor.get_lowest_set_bit(mask)
            num_bits = (mask >> amount_to_shift).bit_length()
            
            if num_bits < 8:
              # Too small to hold a switch value.
              continue
            
            #if attr_name.startswith("unknown_param_"):
            #  # Some hacky code to try to look for unknown params that are switches.
            #  if stage_id == 0:
            #    param_val = getattr(actor, attr_name)
            #    if param_val in [2]:
            #      print("!!!! %02X %s %s %s" % (param_val, actor.name, attr_name, arc_path))
            
            if "switch" in attr_name and "num_switches" not in attr_name:
              if attr_name in ["invert_spawn_condition_switch", "dont_check_enable_spawn_switch"]:
                continue
              
              switch = getattr(actor, attr_name)
              if switch == 0xFF:
                continue
              
              if class_name == "d_a_tbox":
                if attr_name == "appear_condition_switch" and actor.behavior_type not in [1, 2, 3, 4, 6, 8]:
                  # Not a type that cares about the appear condition switch
                  continue
                room_no_for_param = actor.room_num
              elif class_name == "d_a_salvage":
                if attr_name == "switch_to_check" and actor.salvage_type != 2:
                  # Not the type that checks the switch
                  continue
              elif class_name in ["d_a_andsw0", "d_a_andsw2"] and attr_name == "first_switch_to_check":
                for switch in range(actor.first_switch_to_check, actor.first_switch_to_check+actor.num_switches_to_check):
                  add_used_switch(switch, stage_id_for_param, stage_name, room_no_for_param, location_identifier, is_unused)
                continue
              elif class_name == "d_a_tag_md_cb" and attr_name == "first_switch_to_check":
                if actor.name in ["TagMd15", "TagMd16", "TagCb13"]:
                  for switch in range(actor.first_switch_to_check, actor.first_switch_to_check+actor.num_switches_to_check):
                    add_used_switch(switch, stage_id_for_param, stage_name, room_no_for_param, location_identifier, is_unused)
                  continue
              elif class_name == "d_a_cc":
                if attr_name == "enable_spawn_switch" and actor.behavior_type == 3:
                  # Blue ChuChu's switch to keep track of whether you own its Blue Chu Jelly.
                  stage_id_for_param = 0xE
              elif class_name == "d_a_obj_warpt":
                if actor.type >= 2:
                  # Cyclic warp pot.
                  if attr_name.startswith("noncyclic_"):
                    continue
                else:
                  # Noncyclic warp pot.
                  if attr_name.startswith("cyclic_"):
                    continue
              elif class_name == "d_a_obj_swlight":
                if attr_name == "other_switch" and actor.is_paired == 0:
                  continue
              elif class_name == "d_a_door10":
                room_no_for_param = actor.from_room_num
                # TODO: other doors
              elif class_name == "d_a_obj_swflat":
                if attr_name == "disabled_switch" and actor.type != 2:
                  # Not a type that cares about the disabled switch
                  continue
              elif class_name == "d_a_hmlif":
                if attr_name == "eye_shot_switch" and actor.type == 0:
                  # Not a type that has an eye
                  continue
              elif class_name == "d_a_obj_bemos":
                if attr_name == "barrier_deactivated_switch" and actor.type != 2:
                  # Only the laser barrier type uses this switch
                  continue
              elif class_name == "d_a_npc_ah":
                if actor.message_id != 9: # Message ID 14010
                  # Other types don't use the switch param.
                  continue
              elif class_name == "d_a_agbsw0":
                if attr_name == "bombed_switch" and actor.type != 6:
                  # Only the Tingle Bomb Trigger type uses this switch
                  continue
                # TODO: other agbsw types
              elif class_name == "d_a_rd" and attr_name in ["disable_spawn_on_death_switch"]:
                # Added by the randomizer.
                continue
              elif class_name == "d_a_ph" and attr_name in ["disable_spawn_on_death_switch", "enable_spawn_switch"]:
                # Added by the randomizer.
                continue
              
              add_used_switch(switch, stage_id_for_param, stage_name, room_no_for_param, location_identifier, is_unused)
  
  def write_used_switches_to_file(used_switches_dict, filename):
    used_switches_dict = OrderedDict(sorted(
      used_switches_dict.items(), key=lambda x: x[0]
    ))
    
    with open(filename, "w") as f:
      f.write("Switches:\n")
      for stage_id, used_switches_for_room in used_switches_dict.items():
        used_switches_for_room = OrderedDict(sorted(
          used_switches_for_room.items(),
          key=lambda x: (x[0] is not None, split_string_for_natural_sort(str(x[0])))
        ))
        
        for room_arc_path_short, used_switches in used_switches_for_room.items():
          if room_arc_path_short == None:
            f.write("Stage ID: %02X\n" % stage_id)
          else:
            f.write("Room %s\n" % room_arc_path_short)
          used_switches.sort(key=lambda tuple: tuple[0])
          for switch, location_identifier in used_switches:
            f.write("  %02X %s\n" % (switch, location_identifier))
  
  write_used_switches_to_file(used_switches_by_stage_id, "Used switches by stage ID.txt")
  write_used_switches_to_file(used_switches_by_stage_id_unused, "Used switches by stage ID (unused stages).txt")

def print_all_used_item_pickup_flags(self):
  used_item_flags_by_stage_id = {}
  used_item_flags_by_stage_id_unused = {}
  for dzs, stage_arc_path, rooms in each_stage_with_rooms(self, exclude_unused=False):
    match = re.search(r"files/res/Stage/([^/]+)/Stage.arc", stage_arc_path, re.IGNORECASE)
    stage_name = match.group(1)
    stage_info = dzs.entries_by_type("STAG")[0]
    stage_id = stage_info.stage_id
    
    if self.stage_names[stage_name] == "Unused":
      is_unused = True
    else:
      is_unused = False
    
    if is_unused:
      if stage_id not in used_item_flags_by_stage_id_unused:
        used_item_flags_by_stage_id_unused[stage_id] = []
    else:
      if stage_id not in used_item_flags_by_stage_id:
        used_item_flags_by_stage_id[stage_id] = []
    
    for dzx, arc_path in [(dzs, stage_arc_path)]+rooms:
      for layer in [None] + list(range(11+1)):
        actors = []
        actors += dzx.entries_by_type_and_layer("ACTR", layer)
        actors += dzx.entries_by_type_and_layer("TGOB", layer)
        actors += dzx.entries_by_type_and_layer("TRES", layer)
        actors += dzx.entries_by_type_and_layer("PLYR", layer)
        actors += dzx.entries_by_type_and_layer("SCOB", layer)
        actors += dzx.entries_by_type_and_layer("TGSC", layer)
        actors += dzx.entries_by_type_and_layer("DOOR", layer)
        actors += dzx.entries_by_type_and_layer("TGDR", layer)
        
        for actor in actors:
          for attr_name in actor.param_fields:
            #if attr_name.startswith("unknown_param_"):
            #  # Some hacky code to try to look for unknown params that are item pickup flags.
            #  if stage_id == 3:
            #    class_name = DataTables.actor_name_to_class_name[actor.name]
            #    param_fields = DataTables.actor_parameters[class_name]
            #    params_bitfield_name, mask = param_fields[param_name]
            #    amount_to_shift = actor.get_lowest_set_bit(mask)
            #    if (mask >> amount_to_shift) < 0x7F: # Need at least 0x7F to hold an item pickup flag
            #      continue
            #    if getattr(actor, param_name) == 5:
            #      print("!!!! %s %s %s" % (actor.name, param_name, arc_path))
            #  
            #  continue
            
            if "item_pickup_flag" in attr_name:
              item_flag = getattr(actor, attr_name) & 0x7F
              if item_flag == 0x7F:
                continue
              
              class_name = DataTables.actor_name_to_class_name[actor.name]
              
              if class_name in ["d_a_item", "d_a_race_item", "d_a_tag_kb_item"]:
                item_name = self.item_names[actor.item_id]
              elif class_name in ["d_a_tsubo", "d_a_switem", "d_a_obj_barrel2", "d_a_obj_movebox", "d_a_obj_homen", "d_a_stone", "d_a_stone2"]:
                if actor.item_id < 0x20:
                  item_name = self.item_names[actor.item_id]
                else:
                  item_name = "Random drop type 0x%02X" % (actor.item_id - 0x20)
              elif class_name == "d_a_obj_bemos":
                if actor.beamos_item_id < 0x20:
                  item_name = self.item_names[actor.beamos_item_id]
                else:
                  item_name = "Random drop type 0x%02X" % (actor.item_id - 0x20)
              elif class_name == "d_a_deku_item":
                item_name = self.item_names[0x34]
              else:
                raise Exception("Unknown actor class: %s" % class_name)
              
              location_identifier = " from % 7s" % actor.name
              location_identifier += "  in " + arc_path[len("files/res/Stage/"):-len(".arc")]
              if layer is not None:
                location_identifier += "/Layer%X" % layer
              
              if is_unused:
                used_item_flags_by_stage_id_unused[stage_id].append((item_flag, item_name, location_identifier))
              else:
                used_item_flags_by_stage_id[stage_id].append((item_flag, item_name, location_identifier))
  
  def write_used_item_flags_to_file(used_item_flags_dict, filename):
    used_item_flags_dict = OrderedDict(sorted(
      used_item_flags_dict.items(), key=lambda x: x[0]
    ))
    
    with open(filename, "w") as f:
      f.write("Item flags:\n")
      for stage_id, item_flags in used_item_flags_dict.items():
        f.write("Stage ID: %02X\n" % stage_id)
        item_flags.sort(key=lambda tuple: tuple[0])
        for item_flag, item_name, location_identifier in item_flags:
          f.write("  %02X for  % -21s %s\n" % (item_flag, item_name, location_identifier))
  
  write_used_item_flags_to_file(used_item_flags_by_stage_id, "Used item pickup flags by stage ID.txt")
  write_used_item_flags_to_file(used_item_flags_by_stage_id_unused, "Used item pickup flags by stage ID (unused stages).txt")

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
  
  for dzs, stage_arc_path, rooms in each_stage_with_rooms(self, exclude_unused=False):
    stage_arc = self.get_arc(stage_arc_path)
    event_list = stage_arc.get_file("event_list.dat")
    if event_list is None:
      continue
    
    match = re.search(r"files/res/Stage/([^/]+)/Stage.arc", stage_arc_path, re.IGNORECASE)
    stage_name = match.group(1)
    
    for event in event_list.events:
      for actor in event.actors:
        if actor.name not in all_actors:
          all_actors[actor.name] = OrderedDict()
        
        for action in actor.actions:
          if action.name not in all_actors[actor.name]:
            all_actors[actor.name][action.name] = OrderedDict()
          
          for prop in action.properties:
            if prop.name not in all_actors[actor.name][action.name]:
              all_actors[actor.name][action.name][prop.name] = OrderedDict()
            
            prop_value_str = repr(prop.value)
            if prop_value_str not in all_actors[actor.name][action.name][prop.name]:
              all_actors[actor.name][action.name][prop.name][prop_value_str] = []
            
            stage_and_event_name = "%s:%s" % (stage_name, event.name)
            if stage_and_event_name not in all_actors[actor.name][action.name][prop.name][prop_value_str]:
              all_actors[actor.name][action.name][prop.name][prop_value_str].append(stage_and_event_name)
  
  # Sort everything alphanumerically instead of by the order they first appeared in the game's files.
  all_actors = OrderedDict(sorted(all_actors.items(), key=lambda x: x[0]))
  for actor_name, actions in all_actors.items():
    actions = OrderedDict(sorted(actions.items(), key=lambda x: x[0]))
    all_actors[actor_name] = actions
    for action_name, props in actions.items():
      props = OrderedDict(sorted(props.items(), key=lambda x: x[0]))
      all_actors[actor_name][action_name] = props
  
  with open("All Event List Actions.txt", "w") as f:
    for actor_name, actions in all_actors.items():
      f.write("%s:\n" % actor_name)
      for action_name, props in actions.items():
        f.write("  %s:\n" % action_name)
        for prop_name, values in props.items():
          f.write("    %s\n" % prop_name)
  
  with open("All Event List Actions - With Property Examples.txt", "w") as f:
    for actor_name, actions in all_actors.items():
      f.write("%s:\n" % actor_name)
      for action_name, props in actions.items():
        f.write("  %s:\n" % action_name)
        for prop_name, values in props.items():
          f.write("    %s:\n" % prop_name)
          for value in values:
            f.write("      " + str(value) + "\n")
  
  with open("All Event List Actions - With Property Appearances.txt", "w") as f:
    for actor_name, actions in all_actors.items():
      f.write("%s:\n" % actor_name)
      for action_name, props in actions.items():
        f.write("  %s:\n" % action_name)
        for prop_name, values in props.items():
          f.write("    %s:\n" % prop_name)
          max_value_length = max(len(str(val)) for val in values.keys())
          for value, stage_and_event_names in values.items():
            line = "      "
            line += str(value)
            line += " "*(max_value_length - len(str(value)))
            stage_and_event_names_str = ", ".join(stage_and_event_names)
            if len(stage_and_event_names_str) > 250:
              # Limit crazy lengths
              stage_and_event_names_str = stage_and_event_names_str[:250]
              stage_and_event_names_str += " ..."
            line += " # Appears in: " + stage_and_event_names_str
            f.write(line + "\n")

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
      item_occs = OrderedDict()
      offset = 0x10 + i*0x10
      for j in range(0x10):
        item_id = read_u8(item_table_data, offset + j)
        if item_id == 0xFF:
          item_name = "(Nothing)"
        else:
          item_name = self.item_names[item_id]
        
        if item_name not in item_occs:
          item_occs[item_name] = 0
        item_occs[item_name] += 1
        
      f.write("Drop type 0x%02X:\n" % i)
      for item_name, occs in item_occs.items():
        if i >= 0x0B and i <= 0x14:
          # For drop types 0B-14, it spawns all of the listed items.
          # The number of occurrences is the number of the item to spawn.
          if item_name == "(Nothing)":
            continue
          f.write("  % 6dx %s\n" % (occs, item_name))
        else:
          # For drop types 00-0A and 15-1E, it picks one of the items at random to spawn.
          # The number of occurrences is the weighted chance of it being chosen.
          f.write("  % 6.2f%% %s\n" % (occs/0x10*100, item_name))

def print_actor_info(self):
  actor_id_to_rel_filename_mapping_addr = 0x803398D8 # DynamicNameTable
  actr_name_to_actor_info_mapping_addr = 0x80372818 # l_objectName
  
  actor_id_to_rel_filename = OrderedDict()
  
  i = 0
  while True:
    address = actor_id_to_rel_filename_mapping_addr + i*8
    actor_id = self.dol.read_data(read_u16, address)
    if actor_id == 0xFFFF:
      break # End marker
    if actor_id in actor_id_to_rel_filename:
      print("Warning, duplicate actor ID in rel filename list: %04X" % padding)
    padding = self.dol.read_data(read_u16, address+2)
    if padding != 0:
      print("Warning, nonzero padding: %04X" % padding)
    
    rel_filename_pointer = self.dol.read_data(read_u32, address+4)
    rel_filename = self.dol.read_data(read_str_until_null_character, rel_filename_pointer)
    
    actor_id_to_rel_filename[actor_id] = rel_filename
    
    i += 1
  
  with open("Actor Info.txt", "w") as f:
    done_actor_ids = []
    for i in range(0x339):
      address = actr_name_to_actor_info_mapping_addr + i*0xC
      
      actr_name = self.dol.read_data(read_str, address, 8)
      actor_id = self.dol.read_data(read_u16, address+8)
      subtype_index = self.dol.read_data(read_u8, address+0xA)
      gba_name = self.dol.read_data(read_u8, address+0xB)
      
      if actor_id in actor_id_to_rel_filename:
        rel_filename = actor_id_to_rel_filename[actor_id]
      else:
        rel_filename = "[none]"
      
      # Condensed dump format for human readability and searching.
      f.write("%7s:   ID %04X,   Subtype %02X,   GBAName %02X,   REL %s\n" % (
        actr_name,
        actor_id,
        subtype_index,
        gba_name,
        rel_filename
      ))
      
      # Alternate dump format as YAML to be read by the randomizer.
      #f.write("%s:\n  Class Name: %s\n  Actor ID: 0x%04X\n  Subtype: 0x%02X\n  GBA Name: 0x%02X\n" % (
      #  actr_name,
      #  rel_filename,
      #  actor_id,
      #  subtype_index,
      #  gba_name
      #))
      
      done_actor_ids.append(actor_id)
    
    for actor_id, rel_filename in actor_id_to_rel_filename.items():
      if actor_id not in done_actor_ids:
        # Print nameless actors
        f.write(" [none]:   ID %04X,   Subtype [],   GBAName [],   REL %s\n" % (
          actor_id,
          rel_filename
        ))
      

def print_all_entity_params(self):
  with open("All Entity Params.txt", "w") as f:
    f.write("   name   params xrot zrot    stage/arc    chunk/index\n")
    for dzs, stage_arc_path, rooms in each_stage_with_rooms(self, exclude_unused=False):
      stage_and_rooms = [(dzs, stage_arc_path)] + rooms
      for dzx, arc_path in stage_and_rooms:
        for chunk_type in ["ACTR", "SCOB", "TRES", "TGOB", "TGSC", "DOOR", "TGDR"]:
          for layer in [None] + list(range(11+1)):
            for i, entity in enumerate(dzx.entries_by_type_and_layer(chunk_type, layer)):
              arc_path_short = arc_path[len("files/res/Stage/"):-len(".arc")]
              location_identifier = arc_path_short
              location_identifier += " %s/" % chunk_type
              if layer is not None:
                location_identifier += "Layer%X/" % layer
              location_identifier += "%03X" % i
              out_str = "% 7s %08X %04X %04X in %s" % (entity.name, entity.params, entity.x_rot, entity.z_rot, location_identifier)
              #print(out_str)
              f.write(out_str + "\n")


def print_all_actor_instance_sizes(self):
  all_filenames = list(self.gcm.files_by_path.keys())
  
  # Sort the file names for determinism. And use natural sorting so the room numbers are in order.
  all_filenames.sort(key=lambda filename: split_string_for_natural_sort(filename))
  
  rel_paths = []
  for filename in all_filenames:
    if not filename.startswith("files/rels/"):
      continue
    rel_paths.append(filename)
  
  rels_arc = self.get_arc("files/RELS.arc")
  for file_entry in rels_arc.file_entries:
    if file_entry.is_dir:
      continue
    if file_entry.name == "f_pc_profile_lst.rel":
      continue
    rel_paths.append("files/rels/%s" % file_entry.name)
  
  profile_name_to_actor_size = []
  for rel_path in rel_paths:
    rel = self.get_rel(rel_path)
    basename = os.path.splitext(os.path.basename(rel_path))[0]
    #print(basename)
    
    symbols = self.get_symbol_map("files/maps/%s.map" % basename)
    profile_name = None
    for symbol_name, symbol_address in symbols.items():
      if symbol_name.startswith("g_profile_"):
        profile_name = symbol_name
    
    #print(profile_name)
    profile_offset = symbols[profile_name]
    actor_size = rel.read_data(read_u32, profile_offset+0x10)
    #print("%X" % actor_size)
    
    profile_name_to_actor_size.append((profile_name, actor_size))
  
  main_symbols = self.get_symbol_map("files/maps/framework.map")
  for symbol_name, symbol_address in main_symbols.items():
    if symbol_name.startswith("g_profile_"):
      actor_size = self.dol.read_data(read_u32, symbol_address+0x10)
      profile_name_to_actor_size.append((symbol_name, actor_size))
  
  profile_name_to_actor_size.sort(key=lambda x: -x[1])
  
  with open("Actor Instance Sizes.txt", "w") as f:
    for profile_name, actor_size in profile_name_to_actor_size:
      assert profile_name.startswith("g_profile_")
      class_name = profile_name[len("g_profile_"):]
      f.write("%-19s: %5X\n" % (class_name, actor_size))

def print_actor_class_occurrences(self):
  occs = {}
  for class_name in DataTables.actor_parameters:
    if class_name in ["d_a_switch_op"]:
      continue
    occs[class_name] = 0
  for dzs, stage_arc_path, rooms in each_stage_with_rooms(self, exclude_unused=False):
    stage_and_rooms = [(dzs, stage_arc_path)] + rooms
    classes_seen_in_stage = []
    for dzx, arc_path in stage_and_rooms:
      #classes_seen_in_room = []
      for chunk_type in ["ACTR", "SCOB", "TRES", "TGOB", "TGSC", "DOOR", "TGDR"]:
        for layer in [None] + list(range(11+1)):
          for i, entity in enumerate(dzx.entries_by_type_and_layer(chunk_type, layer)):
            if entity.name not in DataTables.actor_name_to_class_name:
              print("Unknown actor name: %s" % entity.name)
              continue
            class_name = DataTables.actor_name_to_class_name[entity.name]
            if class_name in classes_seen_in_stage:
              continue
            #if class_name in classes_seen_in_room:
            #  continue
            if class_name not in occs:
              occs[class_name] = 0
            occs[class_name] += 1
            classes_seen_in_stage.append(class_name)
            #classes_seen_in_room.append(class_name)
  
  occs = list(occs.items())
  occs.sort(key=lambda occ: (-occ[1], occ[0]))
  with open("Actor Class Stage Occurrences.txt", "w") as f:
    for k, v in occs:
      f.write("%20s: %d\n" % (k, v))

def search_all_bmds(self):
  all_filenames = list(self.gcm.files_by_path.keys())
  
  # Sort the file names for determinism. And use natural sorting so the room numbers are in order.
  all_filenames.sort(key=lambda filename: split_string_for_natural_sort(filename))
  
  for arc_path in all_filenames:
    if not arc_path.endswith(".arc"):
      continue
    for file_entry in self.get_arc(arc_path).file_entries:
      if not file_entry.name.endswith(".bmd") and not file_entry.name.endswith(".bdl"):
        continue
      if arc_path == "files/res/Stage/A_R00/Room0.arc" and file_entry.name == "model.bmd":
        # Text file incorrectly given .bmd extension.
        continue
      
      print(arc_path)
      print(file_entry.name)
      if file_entry.name.endswith(".bmd"):
        bmd = BMD(file_entry)
      else:
        bmd = BDL(file_entry)
      
      if not "MDL3" in bmd.chunk_by_type:
        continue
      
      for i, mdl_entry in enumerate(bmd.mdl3.entries):
        print(bmd.mat3.mat_names[i])
        for bp_command in mdl_entry.bp_commands:
          print(BPRegister(bp_command.register))
        for xf_command in mdl_entry.xf_commands:
          print(XFRegister(xf_command.register))

def search_all_dzb_properties(self):
  all_filenames = list(self.gcm.files_by_path.keys())
  
  # Sort the file names for determinism. And use natural sorting so the room numbers are in order.
  all_filenames.sort(key=lambda filename: split_string_for_natural_sort(filename))
  
  seen_cam_behavior_vals = []
  for arc_path in all_filenames:
    if not arc_path.endswith(".arc"):
      continue
    for file_entry in self.get_arc(arc_path).file_entries:
      if not file_entry.name.endswith(".dzb"):
        continue
      
      dzb = DZB()
      dzb.read(file_entry.data)
      
      for property in dzb.properties:
        pass
        #if property.sound_id in [24]:
        #  print(arc_path, "Property-%02X" % (dzb.properties.index(property)))
        #if property.camera_behavior not in seen_cam_behavior_vals:
        #  seen_cam_behavior_vals.append(property.camera_behavior)
        #  print("{0:08b}".format(property.camera_behavior))
        #if property.hookshot_stick:
        #  face = next(face for face in dzb.faces if face.property_index == dzb.properties.index(property))
        #  group = dzb.groups[face.group_index]
        #  print("%02X" % property.camera_behavior, arc_path, group.name, "Property-%02X" % (dzb.properties.index(property)))
        #if property.camera_behavior > 0xFF:
        #  print("%08X" % property.camera_behavior)
        #if property.unknown_1 != 0:
        #  print("%X" % property.unknown_1)
        #if property.special_type == 5:
        #  face = next(face for face in dzb.faces if face.property_index == dzb.properties.index(property))
        #  group = dzb.groups[face.group_index]
        #  print("%02X" % property.special_type, arc_path, group.name, "Property-%02X" % (dzb.properties.index(property)))
        #if property.poly_color != 0xFF:
        #  face = next(face for face in dzb.faces if face.property_index == dzb.properties.index(property))
        #  group = dzb.groups[face.group_index]
        #  print("%02X" % property.poly_color, arc_path, group.name, "Property-%02X" % (dzb.properties.index(property)))
        #if property.room_path_id != 0xFF:
        #  face = next(face for face in dzb.faces if face.property_index == dzb.properties.index(property))
        #  group = dzb.groups[face.group_index]
        #  print("%02X" % property.room_path_id, arc_path, group.name, "Property-%02X" % (dzb.properties.index(property)))
        #if property.room_path_point_no != 0xFF:
        #  face = next(face for face in dzb.faces if face.property_index == dzb.properties.index(property))
        #  group = dzb.groups[face.group_index]
        #  print("%02X" % property.room_path_point_no, arc_path, group.name, "Property-%02X" % (dzb.properties.index(property)))

def print_all_used_particle_banks(self):
  for dzs, stage_arc_path, rooms in each_stage_with_rooms(self, exclude_unused=False):
    match = re.search(r"files/res/Stage/([^/]+)/Stage.arc", stage_arc_path, re.IGNORECASE)
    stage_name = match.group(1)
    particle_bank = dzs.entries_by_type("STAG")[0].loaded_particle_bank
    if particle_bank == 0xFF:
      for dzr, room_arc_path in rooms:
        match = re.search(r"files/res/Stage/([^/]+)/([^.]+).arc", room_arc_path, re.IGNORECASE)
        room_name = match.group(2)
        particle_bank = dzr.entries_by_type("FILI")[0].loaded_particle_bank
        if particle_bank == 0xFF:
          continue
        jpc_path = "files/res/Particle/Pscene%03d.jpc" % particle_bank
        print("% 14s: %s" % (stage_name + "/" + room_name, jpc_path))
        if jpc_path not in self.gcm.files_by_path:
          raise Exception("%s does not exist" % jpc_path)
    else:
      jpc_path = "files/res/Particle/Pscene%03d.jpc" % particle_bank
      print("% 14s: %s" % (stage_name, jpc_path))
      if jpc_path not in self.gcm.files_by_path:
        raise Exception("%s does not exist" % jpc_path)
