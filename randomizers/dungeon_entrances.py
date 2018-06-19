
DUNGEON_ENTRANCES = [
  # Stage name, room index, SCLS entry index, spawn ID when exiting, entrance name for macro, island name entrance is on, post-boss warp out destination stage name, room number, and spawn ID
  ("Adanmae", 0, 2, 2, "Dungeon Entrance On Dragon Roost Island", "Dragon Roost Island", "sea", 13, 211),
  ("sea", 41, 6, 6, "Dungeon Entrance In Forest Haven Sector", "Forest Haven", "Omori", 0, 215),
  ("sea", 26, 0, 2, "Dungeon Entrance In Tower of the Gods Sector", "Tower of the Gods", "sea", 26, 1),
  ("Edaichi", 0, 0, 1, "Dungeon Entrance On Headstone Island", "Headstone Island", "sea", 45, 229),
  ("Ekaze", 0, 0, 1, "Dungeon Entrance On Gale Isle", "Gale Isle", "sea", 4, 232),
]
DUNGEON_EXITS = [
  # Stage name, room index, SCLS entry index, spawn ID when entering, dungeon name for macro, boss stage name
  ("M_NewD2", 0, 0, 0, "Dragon Roost Cavern", "M_DragB"),
  ("kindan", 0, 0, 0, "Forbidden Woods", "kinBOSS"),
  ("Siren", 0, 1, 0, "Tower of the Gods", "SirenB"),
  ("M_Dai", 0, 0, 0, "Earth Temple", "M_DaiB"),
  ("kaze", 15, 0, 15, "Wind Temple", "kazeB"),
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
  for entrance_stage_name, entrance_room_index, entrance_scls_index, entrance_spawn_id, entrance_name, island_name, warp_out_stage_name, warp_out_room_number, warp_out_spawn_id in DUNGEON_ENTRANCES:
    if should_limit_first_dungeon_possibilities and entrance_name == "Dungeon Entrance On Dragon Roost Island":
      possible_remaining_exits = []
      for exit_tuple in remaining_exits:
        _, _, _, _, dungeon_name, _ = exit_tuple
        if dungeon_name in ["Dragon Roost Cavern"]:
          possible_remaining_exits.append(exit_tuple)
    else:
      possible_remaining_exits = remaining_exits
    
    random_dungeon_exit = self.rng.choice(possible_remaining_exits)
    remaining_exits.remove(random_dungeon_exit)
    exit_stage_name, exit_room_index, exit_scls_index, exit_spawn_id, dungeon_name, boss_stage_name = random_dungeon_exit
    
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
    
    # Update the wind warp out event to take you to the correct island.
    boss_stage_arc_path = "files/res/Stage/%s/Stage.arc" % boss_stage_name
    event_list = self.get_arc(boss_stage_arc_path).event_list_files[0]
    warp_out_event = event_list.events_by_name["WARP_WIND_AFTER"]
    director = next(actor for actor in warp_out_event.actors if actor.name == "DIRECTOR")
    stage_change_action = next(action for action in director.actions if action.name == "NEXT")
    stage_name_prop = next(prop for prop in stage_change_action.properties if prop.name == "Stage")
    event_list.set_property_value(stage_name_prop.property_index, warp_out_stage_name)
    room_num_prop = next(prop for prop in stage_change_action.properties if prop.name == "RoomNo")
    event_list.set_property_value(room_num_prop.property_index, warp_out_room_number)
    spawn_id_prop = next(prop for prop in stage_change_action.properties if prop.name == "StartCode")
    event_list.set_property_value(spawn_id_prop.property_index, warp_out_spawn_id)
    
    self.dungeon_entrances[entrance_name] = dungeon_name
    self.dungeon_island_locations[dungeon_name] = island_name
  
  self.logic.update_dungeon_entrance_macros()
