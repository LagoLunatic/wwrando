
from collections import namedtuple

DungeonEntrance = namedtuple(
  "DungeonEntrance",
  "stage_name room_num scls_exit_index spawn_id entrance_name island_name warp_out_stage_name warp_out_room_num warp_out_spawn_id"
)
DUNGEON_ENTRANCES = [
  DungeonEntrance("Adanmae", 0, 2, 2, "Dungeon Entrance On Dragon Roost Island", "Dragon Roost Island", "sea", 13, 211),
  DungeonEntrance("sea", 41, 6, 6, "Dungeon Entrance In Forest Haven Sector", "Forest Haven", "Omori", 0, 215),
  DungeonEntrance("sea", 26, 0, 2, "Dungeon Entrance In Tower of the Gods Sector", "Tower of the Gods", "sea", 26, 1),
  DungeonEntrance("Edaichi", 0, 0, 1, "Dungeon Entrance On Headstone Island", "Headstone Island", "sea", 45, 229),
  DungeonEntrance("Ekaze", 0, 0, 1, "Dungeon Entrance On Gale Isle", "Gale Isle", "sea", 4, 232),
]

DungeonExit = namedtuple(
  "DungeonExit",
  "stage_name room_num scls_exit_index spawn_id dungeon_name boss_stage_name"
)
DUNGEON_EXITS = [
  DungeonExit("M_NewD2", 0, 0, 0, "Dragon Roost Cavern", "M_DragB"),
  DungeonExit("kindan", 0, 0, 0, "Forbidden Woods", "kinBOSS"),
  DungeonExit("Siren", 0, 1, 0, "Tower of the Gods", "SirenB"),
  DungeonExit("M_Dai", 0, 0, 0, "Earth Temple", "M_DaiB"),
  DungeonExit("kaze", 15, 0, 15, "Wind Temple", "kazeB"),
]

def randomize_dungeon_entrances(self):
  # First we need to check how many locations the player can access at the start of the game (excluding dungeons since they're not randomized yet).
  # If the player can't access any locations outside of dungeons, we need to limit the possibilities for what we allow the first dungeon (on DRI) to be.
  # If that first dungeon is TotG, the player can't get any items because they need bombs.
  # If that first dungeon is ET or WT, the player can't get any items because they need the command melody (and even with that they would only be able to access one single location).
  # If that first dungeon is FW, the player can access a couple chests, but that's not enough to give the randomizer enough breathing space.
  # So in that case we limit the first dungeon to only be DRC.
  self.logic.temporarily_make_dungeon_entrance_macros_impossible()
  accessible_undone_locations = self.logic.get_accessible_remaining_locations(for_progression=True)
  if len(accessible_undone_locations) == 0:
    should_limit_first_dungeon_possibilities = True
  else:
    should_limit_first_dungeon_possibilities = False
  
  remaining_exits = DUNGEON_EXITS.copy()
  for dungeon_entrance in DUNGEON_ENTRANCES:
    if should_limit_first_dungeon_possibilities and dungeon_entrance.entrance_name == "Dungeon Entrance On Dragon Roost Island":
      possible_remaining_exits = []
      for dungeon_exit in remaining_exits:
        if dungeon_exit.dungeon_name in ["Dragon Roost Cavern"]:
          possible_remaining_exits.append(dungeon_exit)
    else:
      possible_remaining_exits = remaining_exits
    
    dungeon_exit = self.rng.choice(possible_remaining_exits)
    remaining_exits.remove(dungeon_exit)
    
    # Update the dungeon this entrance takes you into.
    entrance_dzx_path = "files/res/Stage/%s/Room%d.arc" % (dungeon_entrance.stage_name, dungeon_entrance.room_num)
    entrance_dzx = self.get_arc(entrance_dzx_path).dzx_files[0]
    entrance_scls = entrance_dzx.entries_by_type("SCLS")[dungeon_entrance.scls_exit_index]
    entrance_scls.dest_stage_name = dungeon_exit.stage_name
    entrance_scls.room_index = dungeon_exit.room_num
    entrance_scls.spawn_id = dungeon_exit.spawn_id
    entrance_scls.save_changes()
    
    # Update the DRI spawn to not have spawn ID 5.
    # If the DRI entrance was connected to the TotG dungeon, then exiting TotG while riding KoRL would crash the game.
    entrance_spawns = entrance_dzx.entries_by_type("PLYR")
    entrance_spawn = next(spawn for spawn in entrance_spawns if spawn.spawn_id == dungeon_entrance.spawn_id)
    if entrance_spawn.spawn_type == 5:
      entrance_spawn.spawn_type = 1
      entrance_spawn.save_changes()
    
    # Update the entrance you're put at when leaving the dungeon.
    exit_dzx_path = "files/res/Stage/%s/Room%d.arc" % (dungeon_exit.stage_name, dungeon_exit.room_num)
    exit_dzx = self.get_arc(exit_dzx_path).dzx_files[0]
    exit_scls = exit_dzx.entries_by_type("SCLS")[dungeon_exit.scls_exit_index]
    exit_scls.dest_stage_name = dungeon_entrance.stage_name
    exit_scls.room_index = dungeon_entrance.room_num
    exit_scls.spawn_id = dungeon_entrance.spawn_id
    exit_scls.save_changes()
    
    # Update the wind warp out event to take you to the correct island.
    boss_stage_arc_path = "files/res/Stage/%s/Stage.arc" % dungeon_exit.boss_stage_name
    event_list = self.get_arc(boss_stage_arc_path).event_list_files[0]
    warp_out_event = event_list.events_by_name["WARP_WIND_AFTER"]
    director = next(actor for actor in warp_out_event.actors if actor.name == "DIRECTOR")
    stage_change_action = next(action for action in director.actions if action.name == "NEXT")
    stage_name_prop = next(prop for prop in stage_change_action.properties if prop.name == "Stage")
    event_list.set_property_value(stage_name_prop.property_index, dungeon_entrance.warp_out_stage_name)
    room_num_prop = next(prop for prop in stage_change_action.properties if prop.name == "RoomNo")
    event_list.set_property_value(room_num_prop.property_index, dungeon_entrance.warp_out_room_num)
    spawn_id_prop = next(prop for prop in stage_change_action.properties if prop.name == "StartCode")
    event_list.set_property_value(spawn_id_prop.property_index, dungeon_entrance.warp_out_spawn_id)
    
    self.dungeon_entrances[dungeon_entrance.entrance_name] = dungeon_exit.dungeon_name
    self.dungeon_island_locations[dungeon_exit.dungeon_name] = dungeon_entrance.island_name
  
  self.logic.update_dungeon_entrance_macros()
