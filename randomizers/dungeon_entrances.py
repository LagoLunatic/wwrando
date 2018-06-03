
DUNGEON_ENTRANCES = [
  # Stage name, room index, SCLS entry index, spawn ID when exiting, entrance name for macro
  ("Adanmae", 0, 2, 2, "Dungeon Entrance On Dragon Roost Island"),
  ("sea", 41, 6, 6, "Dungeon Entrance In Forest Haven Sector"),
  ("sea", 26, 0, 2, "Dungeon Entrance In Tower of the Gods Sector"),
  ("Edaichi", 0, 0, 1, "Dungeon Entrance On Headstone Island"),
  ("Ekaze", 0, 0, 1, "Dungeon Entrance On Gale Isle"),
]
DUNGEON_EXITS = [
  # Stage name, room index, SCLS entry index, spawn ID when entering, dungeon name for macro
  ("M_NewD2", 0, 0, 0, "Dragon Roost Cavern"),
  ("kindan", 0, 0, 0, "Forbidden Woods"),
  ("Siren", 0, 1, 0, "Tower of the Gods"),
  ("M_Dai", 0, 0, 0, "Earth Temple"),
  ("kaze", 15, 0, 15, "Wind Temple"),
]

def randomize_dungeon_entrances(self):
  # First we need to check how many locations the player can access at the start of the game (excluding dungeons since they're not randomized yet).
  # If the player can't access any locations outside of dungeons, we need to limit the possibilities for what we allow the first dungeon (on DRI) to be.
  # If that first dungeon is TotG, the player can't get any items because they need bombs.
  # If that first dungeon is ET or WT, the player can't get any items because they need the command melody (and even with that they would only be able to access one single location).
  # So in that case we limit the first dungeon to either be DRC or FW.
  self.logic.temporarily_make_dungeon_entrance_macros_impossible()
  accessible_undone_locations = self.logic.get_accessible_remaining_locations(for_progression=True)
  if len(accessible_undone_locations) == 0:
    should_limit_first_dungeon_possibilities = True
  else:
    should_limit_first_dungeon_possibilities = False
  
  remaining_exits = DUNGEON_EXITS.copy()
  for entrance_stage_name, entrance_room_index, entrance_scls_index, entrance_spawn_id, entrance_name in DUNGEON_ENTRANCES:
    if should_limit_first_dungeon_possibilities and entrance_name == "Dungeon Entrance On Dragon Roost Island":
      possible_remaining_exits = []
      for exit_tuple in remaining_exits:
        _, _, _, _, dungeon_name = exit_tuple
        if dungeon_name in ["Dragon Roost Cavern", "Forbidden Woods"]:
          possible_remaining_exits.append(exit_tuple)
    else:
      possible_remaining_exits = remaining_exits
    
    random_dungeon_exit = self.rng.choice(possible_remaining_exits)
    remaining_exits.remove(random_dungeon_exit)
    exit_stage_name, exit_room_index, exit_scls_index, exit_spawn_id, dungeon_name = random_dungeon_exit
    
    # Update the dungeon this entrance takes you into.
    entrance_dzx_path = "files/res/Stage/%s/Room%d.arc" % (entrance_stage_name, entrance_room_index)
    entrance_dzx = self.get_arc(entrance_dzx_path).dzx_files[0]
    entrance_scls = entrance_dzx.entries_by_type("SCLS")[entrance_scls_index]
    entrance_scls.dest_stage_name = exit_stage_name
    entrance_scls.room_index = exit_room_index
    entrance_scls.spawn_id = exit_spawn_id
    entrance_scls.save_changes()
    
    # Update the entrance you're put at when leaving the dungeon.
    exit_dzx_path = "files/res/Stage/%s/Room%d.arc" % (exit_stage_name, exit_room_index)
    exit_dzx = self.get_arc(exit_dzx_path).dzx_files[0]
    exit_scls = exit_dzx.entries_by_type("SCLS")[exit_scls_index]
    exit_scls.dest_stage_name = entrance_stage_name
    exit_scls.room_index = entrance_room_index
    exit_scls.spawn_id = entrance_spawn_id
    exit_scls.save_changes()
    
    self.dungeon_entrances[entrance_name] = dungeon_name
  
  self.logic.update_dungeon_entrance_macros()
