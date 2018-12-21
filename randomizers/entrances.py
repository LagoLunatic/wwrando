
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
  remaining_exits = DUNGEON_EXITS.copy()
  for dungeon_entrance in DUNGEON_ENTRANCES:
    if self.dungeons_only_start and dungeon_entrance.entrance_name == "Dungeon Entrance On Dragon Roost Island":
      # If we're in a dungeons-only-start, we have to force the first dungeon to be DRC.
      # Any other dungeon would cause problems for the item placement logic:
      # If the first dungeon is TotG, the player can't get any items because they need bombs.
      # If the first dungeon is ET or WT, the player can't get any items because they need the command melody (and even with that they would only be able to access one single location).
      # If the first dungeon is FW, the player can access a couple chests, but that's not enough to give the randomizer enough breathing space.
      possible_remaining_exits = []
      for dungeon_exit in remaining_exits:
        if dungeon_exit.dungeon_name in ["Dragon Roost Cavern"]:
          possible_remaining_exits.append(dungeon_exit)
    else:
      possible_remaining_exits = remaining_exits
    
    dungeon_exit = self.rng.choice(possible_remaining_exits)
    remaining_exits.remove(dungeon_exit)
    
    self.dungeon_entrances[dungeon_entrance.entrance_name] = dungeon_exit.dungeon_name
    self.dungeon_island_locations[dungeon_exit.dungeon_name] = dungeon_entrance.island_name
    
    if not self.dry_run:
      # Update the dungeon this entrance takes you into.
      entrance_dzx_path = "files/res/Stage/%s/Room%d.arc" % (dungeon_entrance.stage_name, dungeon_entrance.room_num)
      entrance_dzx = self.get_arc(entrance_dzx_path).get_file("room.dzr")
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
      exit_dzx = self.get_arc(exit_dzx_path).get_file("room.dzr")
      exit_scls = exit_dzx.entries_by_type("SCLS")[dungeon_exit.scls_exit_index]
      exit_scls.dest_stage_name = dungeon_entrance.stage_name
      exit_scls.room_index = dungeon_entrance.room_num
      exit_scls.spawn_id = dungeon_entrance.spawn_id
      exit_scls.save_changes()
      
      # Update the wind warp out event to take you to the correct island.
      boss_stage_arc_path = "files/res/Stage/%s/Stage.arc" % dungeon_exit.boss_stage_name
      event_list = self.get_arc(boss_stage_arc_path).get_file("event_list.dat")
      warp_out_event = event_list.events_by_name["WARP_WIND_AFTER"]
      director = next(actor for actor in warp_out_event.actors if actor.name == "DIRECTOR")
      stage_change_action = next(action for action in director.actions if action.name == "NEXT")
      stage_name_prop = next(prop for prop in stage_change_action.properties if prop.name == "Stage")
      stage_name_prop.value = dungeon_entrance.warp_out_stage_name
      room_num_prop = next(prop for prop in stage_change_action.properties if prop.name == "RoomNo")
      room_num_prop.value = dungeon_entrance.warp_out_room_num
      spawn_id_prop = next(prop for prop in stage_change_action.properties if prop.name == "StartCode")
      spawn_id_prop.value = dungeon_entrance.warp_out_spawn_id
  
  self.logic.update_dungeon_entrance_macros()
