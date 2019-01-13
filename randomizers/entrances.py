
from collections import namedtuple

ZoneEntrance = namedtuple(
  "ZoneEntrance",
  "stage_name room_num scls_exit_index spawn_id entrance_name island_name warp_out_stage_name warp_out_room_num warp_out_spawn_id"
)
DUNGEON_ENTRANCES = [
  ZoneEntrance("Adanmae", 0, 2, 2, "Dungeon Entrance On Dragon Roost Island", "Dragon Roost Island", "sea", 13, 211),
  ZoneEntrance("sea", 41, 6, 6, "Dungeon Entrance In Forest Haven Sector", "Forest Haven", "Omori", 0, 215),
  ZoneEntrance("sea", 26, 0, 2, "Dungeon Entrance In Tower of the Gods Sector", "Tower of the Gods", "sea", 26, 1),
  ZoneEntrance("Edaichi", 0, 0, 1, "Dungeon Entrance On Headstone Island", "Headstone Island", "sea", 45, 229),
  ZoneEntrance("Ekaze", 0, 0, 1, "Dungeon Entrance On Gale Isle", "Gale Isle", "sea", 4, 232),
]
SECRET_CAVE_ENTRANCES = [
  ZoneEntrance("sea", 44, 8, 10, "Secret Cave Entrance on Outset Island", "Outset Island", "sea", 44, 10),
  ZoneEntrance("sea", 13, 2, 5, "Secret Cave Entrance on Dragon Roost Island", "Dragon Roost Island", "sea", 13, 5),
  # Note: For Fire Mountain and Ice Ring Isle, the spawn ID specified is on the sea with KoRL instead of being at the cave entrance, since the player would get burnt/frozen if they were put at the entrance while the island is still active.
  ZoneEntrance("sea", 20, 0, 0, "Secret Cave Entrance on Fire Mountain", "Fire Mountain", "sea", 20, 0),
  ZoneEntrance("sea", 40, 0, 0, "Secret Cave Entrance on Ice Ring Isle", "Ice Ring Isle", "sea", 40, 0),
  ZoneEntrance("Abesso", 0, 1, 1, "Secret Cave Entrance on Private Oasis", "Private Oasis", "Abesso", 0, 1),
  ZoneEntrance("sea", 29, 0, 5, "Secret Cave Entrance on Needle Rock Isle", "Needle Rock Isle", "sea", 29, 5),
  ZoneEntrance("sea", 47, 1, 5, "Secret Cave Entrance on Angular Isles", "Angular Isles", "sea", 47, 5),
  ZoneEntrance("sea", 48, 0, 5, "Secret Cave Entrance on Boating Course", "Boating Course", "sea", 48, 5),
  ZoneEntrance("sea", 31, 0, 1, "Secret Cave Entrance on Stone Watcher Island", "Stone Watcher Island", "sea", 31, 1),
  ZoneEntrance("sea", 7, 0, 1, "Secret Cave Entrance on Overlook Island", "Overlook Island", "sea", 7, 1),
  ZoneEntrance("sea", 35, 0, 1, "Secret Cave Entrance on Bird's Peak Rock", "Bird's Peak Rock", "sea", 35, 1),
  ZoneEntrance("sea", 12, 0, 1, "Secret Cave Entrance on Pawprint Isle", "Pawprint Isle", "sea", 12, 1),
  ZoneEntrance("sea", 12, 1, 5, "Secret Cave Entrance on Pawprint Isle Side Isle", "Pawprint Isle", "sea", 12, 5),
  ZoneEntrance("sea", 36, 0, 1, "Secret Cave Entrance on Diamond Steppe Island", "Diamond Steppe Island", "sea", 36, 1),
  ZoneEntrance("sea", 34, 0, 1, "Secret Cave Entrance on Bomb Island", "Bomb Island", "sea", 34, 1),
  ZoneEntrance("sea", 16, 0, 1, "Secret Cave Entrance on Rock Spire Isle", "Rock Spire Isle", "sea", 16, 1),
  ZoneEntrance("sea", 38, 0, 5, "Secret Cave Entrance on Shark Island", "Shark Island", "sea", 38, 5),
  ZoneEntrance("sea", 42, 0, 2, "Secret Cave Entrance on Cliff Plateau Isles", "Cliff Plateau Isles", "sea", 42, 2),
  ZoneEntrance("sea", 43, 0, 5, "Secret Cave Entrance on Horseshoe Island", "Horseshoe Island", "sea", 43, 5),
  ZoneEntrance("sea", 2, 0, 1, "Secret Cave Entrance on Star Island", "Star Island", "sea", 2, 1),
]

ZoneExit = namedtuple(
  "ZoneExit",
  "stage_name room_num scls_exit_index spawn_id zone_name unique_name boss_stage_name"
)
DUNGEON_EXITS = [
  ZoneExit("M_NewD2", 0, 0, 0, "Dragon Roost Cavern", "Dragon Roost Cavern", "M_DragB"),
  ZoneExit("kindan", 0, 0, 0, "Forbidden Woods", "Forbidden Woods", "kinBOSS"),
  ZoneExit("Siren", 0, 1, 0, "Tower of the Gods", "Tower of the Gods", "SirenB"),
  ZoneExit("M_Dai", 0, 0, 0, "Earth Temple", "Earth Temple", "M_DaiB"),
  ZoneExit("kaze", 15, 0, 15, "Wind Temple", "Wind Temple", "kazeB"),
]
SECRET_CAVE_EXITS = [
  ZoneExit("Cave09", 0, 1, 0, "Outset Island", "Savage Labyrinth", None),
  ZoneExit("TF_06", 0, 0, 0, "Dragon Roost Island", "Dragon Roost Island Secret Cave", None),
  ZoneExit("MiniKaz", 0, 0, 0, "Fire Mountain", "Fire Mountain Secret Cave", None),
  ZoneExit("MiniHyo", 0, 0, 0, "Ice Ring Isle", "Ice Ring Isle Secret Cave", None),
  ZoneExit("TF_04", 0, 0, 0, "Private Oasis", "Cabana Labyrinth", None),
  ZoneExit("SubD42", 0, 0, 0, "Needle Rock Isle", "Needle Rock Isle Secret Cave", None),
  ZoneExit("SubD43", 0, 0, 0, "Angular Isles", "Angular Isles Secret Cave", None),
  ZoneExit("SubD71", 0, 0, 0, "Boating Course", "Boating Course Secret Cave", None),
  ZoneExit("TF_01", 0, 0, 0, "Stone Watcher Island", "Stone Watcher Island Secret Cave", None),
  ZoneExit("TF_02", 0, 0, 0, "Overlook Island", "Overlook Island Secret Cave", None),
  ZoneExit("TF_03", 0, 0, 0, "Bird's Peak Rock", "Bird's Peak Rock Secret Cave", None),
  ZoneExit("TyuTyu", 0, 0, 0, "Pawprint Isle", "Pawprint Isle Chuchu Cave", None),
  ZoneExit("Cave07", 0, 0, 0, "Pawprint Isle", "Pawprint Isle Wizzrobe Cave", None),
  ZoneExit("WarpD", 0, 0, 0, "Diamond Steppe Island", "Diamond Steppe Island Warp Maze Cave", None),
  ZoneExit("Cave01", 0, 0, 0, "Bomb Island", "Bomb Island Secret Cave", None),
  ZoneExit("Cave04", 0, 0, 0, "Rock Spire Isle", "Rock Spire Isle Secret Cave", None),
  ZoneExit("ITest63", 0, 0, 0, "Shark Island", "Shark Island Secret Cave", None),
  ZoneExit("Cave03", 0, 0, 0, "Cliff Plateau Isles", "Cliff Plateau Isles Secret Cave", None),
  ZoneExit("Cave05", 0, 0, 0, "Horseshoe Island", "Horseshoe Island Secret Cave", None),
  ZoneExit("Cave02", 0, 0, 0, "Star Island", "Star Island Secret Cave", None),
]

DUNGEON_ENTRANCE_NAMES_WITH_NO_REQUIREMENTS = [
  "Dungeon Entrance On Dragon Roost Island",
]
SECRET_CAVE_ENTRANCE_NAMES_WITH_NO_REQUIREMENTS = [
  "Secret Cave Entrance on Pawprint Isle",
  "Secret Cave Entrance on Cliff Plateau Isles",
]

DUNGEON_EXIT_NAMES_WITH_NO_REQUIREMENTS = [
  "Dragon Roost Cavern",
]
PUZZLE_SECRET_CAVE_EXIT_NAMES_WITH_NO_REQUIREMENTS = [
  "Pawprint Isle Chuchu Cave",
  "Ice Ring Isle Secret Cave",
  "Bird's Peak Rock Secret Cave", # Technically this has requirements, but it's just Wind Waker+Wind's Requiem.
  "Diamond Steppe Island Warp Maze Cave",
]
COMBAT_SECRET_CAVE_EXIT_NAMES_WITH_NO_REQUIREMENTS = [
  "Rock Spire Isle Secret Cave",
]

# TODO: Maybe make a separate list of entrances and exits that have no requirements when you start with a sword. (e.g. Cliff Plateau Isles Secret Cave.) Probably not necessary though.

def randomize_entrances(self):
  if self.options.get("randomize_entrances") == "Dungeons":
    randomize_one_set_of_entrances(self, include_dungeons=True, include_caves=False)
  elif self.options.get("randomize_entrances") == "Secret Caves":
    randomize_one_set_of_entrances(self, include_dungeons=False, include_caves=True)
  elif self.options.get("randomize_entrances") == "Dungeons & Secret Caves (Separately)":
    randomize_one_set_of_entrances(self, include_dungeons=True, include_caves=False)
    randomize_one_set_of_entrances(self, include_dungeons=False, include_caves=True)
  elif self.options.get("randomize_entrances") == "Dungeons & Secret Caves (Together)":
    randomize_one_set_of_entrances(self, include_dungeons=True, include_caves=True)
  else:
    raise Exception("Invalid entrance randomizer option: %s" % self.options.get("randomize_entrances"))

def randomize_one_set_of_entrances(self, include_dungeons=False, include_caves=False):
  relevant_entrances = []
  remaining_exits = []
  if include_dungeons:
    relevant_entrances += DUNGEON_ENTRANCES
    remaining_exits += DUNGEON_EXITS
  if include_caves:
    relevant_entrances += SECRET_CAVE_ENTRANCES
    remaining_exits += SECRET_CAVE_EXITS
  
  doing_progress_entrances_for_dungeons_and_caves_only_start = False
  if self.dungeons_and_caves_only_start:
    if include_dungeons and self.options.get("progression_dungeons"):
      doing_progress_entrances_for_dungeons_and_caves_only_start = True
    if include_caves and (self.options.get("progression_puzzle_secret_caves") \
        or self.options.get("progression_combat_secret_caves") \
        or self.options.get("progression_savage_labyrinth")):
      doing_progress_entrances_for_dungeons_and_caves_only_start = True
  
  if doing_progress_entrances_for_dungeons_and_caves_only_start:
    # If the player can't access any locations at the start besides dungeon/cave entrances, we choose an entrance with no requirements that will be the first place the player goes.
    # We will make this entrance lead to a dungeon/cave with no requirements so the player can actually get an item at the start.
    
    entrance_names_with_no_requirements = []
    if self.options.get("progression_dungeons"):
      entrance_names_with_no_requirements += DUNGEON_ENTRANCE_NAMES_WITH_NO_REQUIREMENTS
    if self.options.get("progression_puzzle_secret_caves") \
        or self.options.get("progression_combat_secret_caves") \
        or self.options.get("progression_savage_labyrinth"):
      entrance_names_with_no_requirements += SECRET_CAVE_ENTRANCE_NAMES_WITH_NO_REQUIREMENTS
    
    exit_names_with_no_requirements = []
    if self.options.get("progression_dungeons"):
      exit_names_with_no_requirements += DUNGEON_EXIT_NAMES_WITH_NO_REQUIREMENTS
    if self.options.get("progression_puzzle_secret_caves"):
      exit_names_with_no_requirements += PUZZLE_SECRET_CAVE_EXIT_NAMES_WITH_NO_REQUIREMENTS
    if self.options.get("progression_combat_secret_caves"):
      exit_names_with_no_requirements += COMBAT_SECRET_CAVE_EXIT_NAMES_WITH_NO_REQUIREMENTS
    # No need to check progression_savage_labyrinth, since neither of the items inside Savage have no requirements.
    
    possible_safety_entrances = [
      e for e in relevant_entrances
      if e.entrance_name in entrance_names_with_no_requirements
    ]
    safety_entrance = self.rng.choice(possible_safety_entrances)
    
    # In order to avoid using up all dungeons/caves with no requirements, we have to do this entrance first, so move it to the start of the array.
    relevant_entrances.remove(safety_entrance)
    relevant_entrances.insert(0, safety_entrance)
  
  for zone_entrance in relevant_entrances:
    if doing_progress_entrances_for_dungeons_and_caves_only_start and zone_entrance == safety_entrance:
      possible_remaining_exits = [e for e in remaining_exits if e.unique_name in exit_names_with_no_requirements]
    else:
      possible_remaining_exits = remaining_exits
    
    zone_exit = self.rng.choice(possible_remaining_exits)
    remaining_exits.remove(zone_exit)
    
    self.entrance_connections[zone_entrance.entrance_name] = zone_exit.unique_name
    self.dungeon_and_cave_island_locations[zone_exit.zone_name] = zone_entrance.island_name
    
    if not self.dry_run:
      # Update the stage this entrance takes you into.
      entrance_dzx_path = "files/res/Stage/%s/Room%d.arc" % (zone_entrance.stage_name, zone_entrance.room_num)
      entrance_dzx = self.get_arc(entrance_dzx_path).get_file("room.dzr")
      entrance_scls = entrance_dzx.entries_by_type("SCLS")[zone_entrance.scls_exit_index]
      entrance_scls.dest_stage_name = zone_exit.stage_name
      entrance_scls.room_index = zone_exit.room_num
      entrance_scls.spawn_id = zone_exit.spawn_id
      entrance_scls.save_changes()
      
      # Update the DRI spawn to not have spawn ID 5.
      # If the DRI entrance was connected to the TotG dungeon, then exiting TotG while riding KoRL would crash the game.
      entrance_spawns = entrance_dzx.entries_by_type("PLYR")
      entrance_spawn = next(spawn for spawn in entrance_spawns if spawn.spawn_id == zone_entrance.spawn_id)
      if entrance_spawn.spawn_type == 5:
        entrance_spawn.spawn_type = 1
        entrance_spawn.save_changes()
      
      # Update the entrance you're put at when leaving the dungeon.
      exit_dzx_path = "files/res/Stage/%s/Room%d.arc" % (zone_exit.stage_name, zone_exit.room_num)
      exit_dzx = self.get_arc(exit_dzx_path).get_file("room.dzr")
      exit_scls = exit_dzx.entries_by_type("SCLS")[zone_exit.scls_exit_index]
      exit_scls.dest_stage_name = zone_entrance.stage_name
      exit_scls.room_index = zone_entrance.room_num
      exit_scls.spawn_id = zone_entrance.spawn_id
      exit_scls.save_changes()
      
      if zone_exit in SECRET_CAVE_EXITS:
        # Update the sector coordinates in the 2DMA chunk so that save-and-quitting in a secret cave puts you on the correct island.
        exit_dzs_path = "files/res/Stage/%s/Stage.arc" % zone_exit.stage_name
        exit_dzs = self.get_arc(exit_dzs_path).get_file("stage.dzs")
        _2dma = exit_dzs.entries_by_type("2DMA")[0]
        island_number = self.island_name_to_number[zone_entrance.island_name]
        sector_x = (island_number-1) % 7
        sector_y = (island_number-1) // 7
        _2dma.sector_x = sector_x-3
        _2dma.sector_y = sector_y-3
        _2dma.save_changes()
      
      if zone_exit.boss_stage_name is not None:
        # Update the wind warp out event to take you to the correct island.
        boss_stage_arc_path = "files/res/Stage/%s/Stage.arc" % zone_exit.boss_stage_name
        event_list = self.get_arc(boss_stage_arc_path).get_file("event_list.dat")
        warp_out_event = event_list.events_by_name["WARP_WIND_AFTER"]
        director = next(actor for actor in warp_out_event.actors if actor.name == "DIRECTOR")
        stage_change_action = next(action for action in director.actions if action.name == "NEXT")
        stage_name_prop = next(prop for prop in stage_change_action.properties if prop.name == "Stage")
        stage_name_prop.value = zone_entrance.warp_out_stage_name
        room_num_prop = next(prop for prop in stage_change_action.properties if prop.name == "RoomNo")
        room_num_prop.value = zone_entrance.warp_out_room_num
        spawn_id_prop = next(prop for prop in stage_change_action.properties if prop.name == "StartCode")
        spawn_id_prop.value = zone_entrance.warp_out_spawn_id
  
  self.logic.update_entrance_connection_macros()
