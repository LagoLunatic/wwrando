
import os
import copy
import re
from collections import OrderedDict
import math

from wwlib import stage_searcher
from logic.logic import Logic

# Limit the number of species that appear in a given stage to prevent issues loading too many particles and to prevent stages from feeling too chaotic.
# (This limit does not apply to the sea.)
MAX_ENEMY_SPECIES_PER_STAGE = 10

# Limit the number of species in a single room at a time too.
MAX_ENEMY_SPECIES_PER_GROUP = 5

MAX_RANDOMIZATION_REDOS_PER_STAGE = 50
MAX_RANDOMIZATION_REDOS_PER_ROOM = 20

# We can't let the free memory get all the way down to 0.
# We need at least 37kb free to take out Grappling Hook, and having other items out at the same time like Bombs and Boomerang can use even more, up to about 46kb.
# We use 60kb as the amount we always leave free in case the estimated amounts of memory each enemy uses are off by a bit.
MIN_FREE_SPACE_TO_LEAVE_PER_ROOM = 60000

# Stages where the game can temporarily have the entities for two rooms loaded at once while the player is moving through a door.
# These stages can pose a problem when it comes to calculating how much free memory we have to work with for enemies, so we need to be extra careful with them.
STAGE_NAMES_WHERE_MULTIPLE_ROOMS_CAN_BE_LOADED_AT_ONCE = [
  "M_NewD2",
  "kindan",
  "Siren",
  "majroom",
  "ma2room",
  "ma3room",
  "M_Dai",
  "kaze",
  "GanonA",
  "GanonJ",
  "GanonM",
  "Cave01",
  "TF_01",
  "TF_02",
  "TF_06",
]

def randomize_enemies(self):
  self.enemy_locations = Logic.load_and_parse_enemy_locations()
  
  # We must compile the human-written placement categories each enemy type is allowed in to account for extra category limitations (like locations where the enemy is required to set a switch on death).
  for enemy_type in self.enemy_types:
    enemy_type["Compiled categories"] = []
    for placement_category in enemy_type["Placement categories"]:
      compiled_category = EnemyCategory(placement_category, enemy_type)
      enemy_type["Compiled categories"].append(compiled_category)
  
  self.enemies_to_randomize_to = [
    data for data in self.enemy_types
    if data["Allow randomizing to"]
  ]
  self.enemies_to_randomize_to_when_all_enemies_must_be_killed = [
    data for data in self.enemy_types
    if data["Allow randomizing to"]
    # Ban Morths from being in rooms where you have to kill all enemies, since they don't count as a living enemy, and it would be weird for the player to not be required to kill an enemy placed there.
    and "Morth" not in data["Pretty name"]
  ]
  
  self.enemy_datas_by_pretty_name = {}
  for enemy_data in self.enemy_types:
    pretty_name = enemy_data["Pretty name"]
    self.enemy_datas_by_pretty_name[pretty_name] = enemy_data
  
  self.all_enemy_actor_names = []
  for data in self.enemy_types:
    if data["Actor name"] not in self.all_enemy_actor_names:
      self.all_enemy_actor_names.append(data["Actor name"])
  
  self.done_enemy_locations = []
  
  self.particles_to_load_for_each_jpc_index = OrderedDict()
  
  for stage_folder, enemy_locations in self.enemy_locations.items():
    stage_attempts = 0
    max_stage_attempts = MAX_RANDOMIZATION_REDOS_PER_STAGE
    if stage_folder == "sea":
      # Sea stage doesn't use an enemy pool, so there's no need to retry it
      max_stage_attempts = 1
    
    while True:
      done_enemy_locations_for_stage = randomize_enemy_groups_for_stage(self, stage_folder, enemy_locations)
      
      stage_attempts += 1
      if done_enemy_locations_for_stage != False:
        self.done_enemy_locations += done_enemy_locations_for_stage
        break
      elif stage_attempts >= max_stage_attempts:
        raise Exception("Enemy rando failed %d times for one stage (%s)" % (stage_attempts, stage_folder))
  
  # Now that all randomized enemy locations have been decided successfully, actually save the changed enemies.
  save_changed_enemies_and_randomize_their_params(self)
  
  add_modify_and_replace_actors_for_enemy_rando(self)
  
  update_loaded_particles(self, self.particles_to_load_for_each_jpc_index)

def decide_on_enemy_pool_for_stage(self, stage_folder, enemy_locations):
  # Decide on the enemy pool that will be available in this stage.
  # This is so we can guarantee every room in the stage will be able to have at least one enemy, instead of later rooms being limited to no enemies that work by a combination of their logic, their placement categories, and enemies that were already placed in other rooms of that stage.
  enemy_pool_for_stage = []
  
  if stage_folder == "sea":
    # The sea stage should have no limit on the number of enemies in it.
    # Particle banks are loaded per-room on the sea.
    return self.enemies_to_randomize_to
  
  category_and_logic_combos_needed = []
  for enemy_group in enemy_locations:
    if enemy_group["Must defeat enemies"]:
      original_req_string = enemy_group["Original requirements"]
      enemies_logically_allowed_in_this_group = self.logic.filter_out_enemies_that_add_new_requirements(original_req_string, self.enemies_to_randomize_to_when_all_enemies_must_be_killed)
    else:
      # For rooms where defeating the enemies is not required to progress, don't limit what enemies to put here by logic item requirements.
      enemies_logically_allowed_in_this_group = self.enemies_to_randomize_to
    
    for enemy_location in enemy_group["Enemies"]:
      category_and_logic_combo = (enemy_location["Placement category"], enemies_logically_allowed_in_this_group)
      if category_and_logic_combo not in category_and_logic_combos_needed:
        category_and_logic_combos_needed.append(category_and_logic_combo)
  
  # First build a minimum list of enemies to allow in this stage to make sure every location in it can have at least one possible enemy there.
  all_enemies_possible_for_this_stage = []
  for category, enemies_logically_allowed in category_and_logic_combos_needed:
    enemies_allowed_for_combo = [
      enemy_data for enemy_data in enemies_logically_allowed
      if is_enemy_allowed_in_placement_category(enemy_data, category)
    ]
    
    for enemy_data in enemies_allowed_for_combo:
      if enemy_data not in all_enemies_possible_for_this_stage:
        all_enemies_possible_for_this_stage.append(enemy_data)
    
    enemies_allowed_already_in_pool = [
      enemy_data for enemy_data in enemies_allowed_for_combo
      if enemy_data in enemy_pool_for_stage
    ]
    if enemies_allowed_already_in_pool:
      # One of the other category/logic combos we added an enemy for also happened to fulfill this combo.
      # No need to add another.
      continue
    
    chosen_enemy = self.rng.choice(enemies_allowed_for_combo)
    enemy_pool_for_stage.append(chosen_enemy)
  
  num_species_chosen = len(enemy_pool_for_stage)
  if num_species_chosen > MAX_ENEMY_SPECIES_PER_STAGE:
    raise Exception("Enemy species pool for %s has %d species in it instead of %d" % (stage_folder, num_species_chosen, MAX_ENEMY_SPECIES_PER_STAGE))
  elif num_species_chosen < MAX_ENEMY_SPECIES_PER_STAGE:
    # Fill up the pool with other random enemies that can go in this stage.
    for i in range(MAX_ENEMY_SPECIES_PER_STAGE-num_species_chosen):
      enemies_possible_for_this_stage_minus_chosen = [
        enemy_data for enemy_data in all_enemies_possible_for_this_stage
        if enemy_data not in enemy_pool_for_stage
      ]
      
      if not enemies_possible_for_this_stage_minus_chosen:
        # The number of enemy species that can actually be placed in this stage is less than the max species per stage.
        # Just exit early with a pool smaller than normal in this case.
        break
      
      chosen_enemy = self.rng.choice(enemies_possible_for_this_stage_minus_chosen)
      enemy_pool_for_stage.append(chosen_enemy)
  
  return enemy_pool_for_stage

def randomize_enemy_groups_for_stage(self, stage_folder, enemy_locations):
  done_enemy_locations_for_stage = []
  
  enemy_pool_for_stage = decide_on_enemy_pool_for_stage(self, stage_folder, enemy_locations)
  for enemy_group in enemy_locations:
    room_attempts = 0
    room_failures = 0
    max_room_attempts = MAX_RANDOMIZATION_REDOS_PER_ROOM
    if stage_folder == "sea":
      max_room_attempts *= 5 # Give sea rooms more attempts to compensate for the lack of stage attempts.
    
    while True:
      done_enemy_locations_for_room = randomize_enemy_group(self, stage_folder, enemy_group, enemy_pool_for_stage)
      
      room_attempts += 1
      if done_enemy_locations_for_room != False:
        done_enemy_locations_for_stage += done_enemy_locations_for_room
        break
      elif room_attempts >= max_room_attempts:
        #print("Enemy rando failed %d times for one room (%s)" % (room_attempts, enemy_group["Enemies"][0]["Path"]))
        return False
  
  return done_enemy_locations_for_stage

def randomize_enemy_group(self, stage_folder, enemy_group, enemy_pool_for_stage):
  done_enemy_locations_for_room = []
  
  free_memory = get_free_memory_for_group(enemy_group)
  if stage_folder in STAGE_NAMES_WHERE_MULTIPLE_ROOMS_CAN_BE_LOADED_AT_ONCE:
    # In stages where there can be two rooms loaded at once, consider the real amount of free space half of the documented amount.
    # This probably isn't a very accurate way to emulate this, but it will have to do since we don't know how much memory enemies in the rooms connected to this room take up, since the other rooms may not be randomized yet.
    free_memory = free_memory / 2
  if False:
    print("/".join(enemy_group["Enemies"][0]["Path"].split("/")[0:-1]))
    print("Initial free memory: %d" % free_memory)
  
  if enemy_group["Must defeat enemies"]:
    original_req_string = enemy_group["Original requirements"]
    enemies_logically_allowed_in_this_group = self.logic.filter_out_enemies_that_add_new_requirements(original_req_string, self.enemies_to_randomize_to_when_all_enemies_must_be_killed)
  else:
    enemies_logically_allowed_in_this_group = self.enemies_to_randomize_to
  
  unique_categories_in_this_group = []
  for enemy_location in enemy_group["Enemies"]:
    if enemy_location["Placement category"] not in unique_categories_in_this_group:
      unique_categories_in_this_group.append(enemy_location["Placement category"])
  
  # First build a minimum list of enemies to allow in this group to make sure every location in it can have at least one possible enemy there.
  enemy_pool_for_group = []
  enemies_logically_allowed_in_this_group_not_yet_in_pool = enemies_logically_allowed_in_this_group.copy()
  all_enemies_possible_for_this_group = []
  for category in unique_categories_in_this_group:
    enemies_allowed = [
      enemy_data for enemy_data in enemies_logically_allowed_in_this_group_not_yet_in_pool
      if is_enemy_allowed_in_placement_category(enemy_data, category)
      and enemy_data in enemy_pool_for_stage
    ]
    
    for enemy_data in enemies_allowed:
      if enemy_data not in all_enemies_possible_for_this_group:
        all_enemies_possible_for_this_group.append(enemy_data)
    
    enemies_allowed_already_in_pool = [
      enemy_data for enemy_data in enemies_allowed
      if enemy_data in enemy_pool_for_group
    ]
    if enemies_allowed_already_in_pool:
      # One of the other categories we added an enemy for also happened to fulfill this category.
      # No need to add another.
      continue
    
    chosen_enemy = self.rng.choice(enemies_allowed)
    enemy_pool_for_group.append(chosen_enemy)
  
  num_species_chosen = len(enemy_pool_for_group)
  if num_species_chosen > MAX_ENEMY_SPECIES_PER_GROUP:
    raise Exception("Enemy species pool for group has %d species in it instead of %d" % (num_species_chosen, MAX_ENEMY_SPECIES_PER_GROUP))
  elif num_species_chosen < MAX_ENEMY_SPECIES_PER_GROUP:
    # Fill up the pool with other random enemies that can go in this group.
    for i in range(MAX_ENEMY_SPECIES_PER_GROUP-num_species_chosen):
      enemies_possible_for_this_group_minus_chosen = [
        enemy_data for enemy_data in all_enemies_possible_for_this_group
        if enemy_data not in enemy_pool_for_group
      ]
      
      if not enemies_possible_for_this_group_minus_chosen:
        # The number of enemy species that can actually be placed in this group is less than the max species per group.
        # Just exit early with a pool smaller than normal in this case.
        break
      
      chosen_enemy = self.rng.choice(enemies_possible_for_this_group_minus_chosen)
      enemy_pool_for_group.append(chosen_enemy)
  
  # Then decide what enemy species will be placed in each enemy location in this group.
  enemy_actor_names_already_placed_in_room = []
  for enemy_location in enemy_group["Enemies"]:
    enemy, arc_name, dzx, layer = get_enemy_instance_by_path(self, enemy_location["Path"])
    _, room_arc_name = arc_name.split("/")
    
    enemies_to_randomize_to_for_this_location = [
      data for data in enemy_pool_for_group
      if is_enemy_allowed_in_placement_category(data, enemy_location["Placement category"])
    ]
    
    if len(enemies_to_randomize_to_for_this_location) == 0:
      error_msg = "No possible enemies to place in %s of the correct category\n" % arc_name
      enemy_pretty_names_in_this_stage_pool = [
        enemy_data["Pretty name"]
        for enemy_data in enemy_pool_for_stage
      ]
      error_msg += "Enemies in this stage's enemy pool: %s\n" % ", ".join(enemy_pretty_names_in_this_stage_pool)
      enemy_actor_names_logically_allowed_in_this_group = []
      for data in enemies_logically_allowed_in_this_group:
        if data["Actor name"] not in enemy_actor_names_logically_allowed_in_this_group:
          enemy_actor_names_logically_allowed_in_this_group.append(data["Actor name"])
      error_msg += "Enemies logically allowed in this group: %s\n" % ", ".join(enemy_actor_names_logically_allowed_in_this_group)
      enemy_pretty_names_in_this_group_pool = [
        enemy_data["Pretty name"]
        for enemy_data in enemy_pool_for_group
      ]
      error_msg += "Enemies in this group's enemy pool: %s\n" % ", ".join(enemy_pretty_names_in_this_group_pool)
      enemy_actor_names_of_correct_category = []
      for data in self.enemy_types:
        if is_enemy_allowed_in_placement_category(data, enemy_location["Placement category"]):
          if data["Actor name"] not in enemy_actor_names_of_correct_category:
            enemy_actor_names_of_correct_category.append(data["Actor name"])
      error_msg += "Enemies of the correct category (%s): %s" % (enemy_location["Placement category"], ", ".join(enemy_actor_names_of_correct_category))
      raise Exception(error_msg)
    
    new_enemy_data = self.rng.choice(enemies_to_randomize_to_for_this_location)
    
    #new_enemy_data = self.enemy_datas_by_pretty_name["Lantern Moblin"]
    
    # Account for the amount of memory used up by this enemy instance.
    free_memory -= get_amount_of_memory_for_enemy(new_enemy_data, enemy_actor_names_already_placed_in_room)
    if False:
      print("Enemy placed: %s" % new_enemy_data["Pretty name"])
      print("Free memory: %d" % free_memory)
      print("Subtracted: %d" % get_amount_of_memory_for_enemy(new_enemy_data, enemy_actor_names_already_placed_in_room))
    
    if free_memory < MIN_FREE_SPACE_TO_LEAVE_PER_ROOM:
      # Not enough memory left in this room. Give up early.
      return False
    
    if new_enemy_data["Actor name"] not in enemy_actor_names_already_placed_in_room:
      # TODO: maybe use rel name instead of actor name...?
      enemy_actor_names_already_placed_in_room.append(new_enemy_data["Actor name"])
    
    done_enemy_locations_for_room.append((enemy_location, new_enemy_data))
  
  return done_enemy_locations_for_room

def save_changed_enemies_and_randomize_their_params(self):
  # Finally actually save the enemies, since there was no issue in deciding what any of them should be.
  last_printed_group_path = None
  for enemy_location, new_enemy_data in self.done_enemy_locations:
    path = enemy_location["Path"]
    placement_category = enemy_location["Placement category"]
    enemy, arc_name, dzx, layer = get_enemy_instance_by_path(self, path)
    stage_folder, room_arc_name = arc_name.split("/")
    
    if False:
      group_path = "/".join(path.split("/")[0:-1])
      if group_path != last_printed_group_path:
        print()
      last_printed_group_path = group_path
      print("Putting a %s (param:%08X) in %s" % (new_enemy_data["Actor name"], new_enemy_data["Params"], path))
    
    death_switch_to_set = None
    if ":" in placement_category:
      category_string, conditions_string = placement_category.split(":", 1)
      conditions = conditions_string.split(",")
      
      if "SetsDeathSwitch" in conditions:
        # We need
        original_enemy_type = get_enemy_data_for_actor(self, enemy)
        death_switch_param_name = original_enemy_type["Death switch param name"]
        
        if death_switch_param_name is None:
          raise Exception("An enemy location specified that it must set a switch on death, but the original enemy there is not documented to be able to set a switch on death.")
        
        death_switch_to_set = getattr(enemy, death_switch_param_name)
        if death_switch_to_set in [0x00, 0x80, 0xFF] or death_switch_to_set >= 0xF0:
          raise Exception("Switch index to set on enemy death is not valid for all enemy types: %02X" % death_switch_to_set)
    
    enemy.name = new_enemy_data["Actor name"]
    enemy.params = new_enemy_data["Params"]
    enemy.aux_params_1 = new_enemy_data["Aux params"]
    enemy.aux_params_2 = new_enemy_data["Aux params 2"]
    
    if "Position" in enemy_location:
      x, y, z = enemy_location["Position"]
      enemy.x_pos = x
      enemy.y_pos = y
      enemy.z_pos = z
    elif "Position offset" in enemy_location:
      x, y, z = enemy_location["Position offset"]
      enemy.x_pos += x
      enemy.y_pos += y
      enemy.z_pos += z
    if "Y Rotation" in enemy_location:
      enemy.y_rot = enemy_location["Y Rotation"]
    elif "Y Rotation offset" in enemy_location:
      enemy.y_rot += enemy_location["Y Rotation offset"]
      enemy.y_rot &= 0xFFFF
    
    randomize_enemy_params(self, new_enemy_data, enemy, placement_category, dzx, layer)
    adjust_enemy(self, new_enemy_data, enemy, placement_category, dzx, layer)
    
    if death_switch_to_set is not None:
      death_switch_param_name = new_enemy_data["Death switch param name"]
      if death_switch_param_name is None:
        raise Exception("Tried to place an enemy type that cannot set a switch on death in a location that requires a switch be set on death: %s" % enemy.name)
      setattr(enemy, death_switch_param_name, death_switch_to_set)
    
    enemy.save_changes()
    
    if stage_folder == "sea":
      dzr = self.get_arc("files/res/Stage/sea/" + room_arc_name).get_file("room.dzr")
      dest_jpc_index = dzr.entries_by_type("FILI")[0].loaded_particle_bank
    else:
      dzs = self.get_arc("files/res/Stage/" + stage_folder + "/Stage.arc").get_file("stage.dzs")
      dest_jpc_index = dzs.entries_by_type("STAG")[0].loaded_particle_bank
    
    if dest_jpc_index not in self.particles_to_load_for_each_jpc_index:
      self.particles_to_load_for_each_jpc_index[dest_jpc_index] = []
    for particle_id in new_enemy_data["Required particle IDs"]:
      if particle_id not in self.particles_to_load_for_each_jpc_index[dest_jpc_index]:
        self.particles_to_load_for_each_jpc_index[dest_jpc_index].append(particle_id)

def add_modify_and_replace_actors_for_enemy_rando(self):
  # Change certain actors that checked something incompatible with enemy randomizer and set a switch to an entity that simply checks if every enemy in the room is dead and sets a switch instead.
  for stage_folder, enemy_locations in self.enemy_locations.items():
    for enemy_group in enemy_locations:
      if "Actors to replace with ALLdies" not in enemy_group:
        continue
      
      actor_paths = enemy_group["Actors to replace with ALLdies"]
      for actor_path in actor_paths:
        actor = get_actor_by_path(self, actor_path)
        
        if actor.name == "AND_SW0":
          switch_to_set = actor.switch_to_set
        elif actor.name == "AND_SW2":
          switch_to_set = actor.switch_to_set
        elif actor.name in ["AND_SW0", "AND_SW2", "Kbota_A", "Kbota_B", "KbotaC"]:
          switch_to_set = actor.switch_to_set
        else:
          raise Exception("Unimplemented switch-setting actor name: %s" % actor.name)
        
        actor.name = "ALLdie"
        actor.params = 0xFFFFFFFF
        actor.aux_params_1 = 0
        actor.aux_params_2 = 0
        actor.switch_to_set = switch_to_set
        actor.save_changes()
  
  # Make specific changes to existing actors.
  for stage_folder, enemy_locations in self.enemy_locations.items():
    for enemy_group in enemy_locations:
      if "Existing actors to modify" not in enemy_group:
        continue
      
      existing_actor_datas = enemy_group["Existing actors to modify"]
      for existing_actor_data in existing_actor_datas:
        actor = get_actor_by_path(self, existing_actor_data["Path"])
        
        if "Name" in existing_actor_data:
          actor.name = existing_actor_data["Name"]
        if "Params" in existing_actor_data:
          actor.params = existing_actor_data["Params"]
        if "Aux Params 1" in existing_actor_data:
          actor.aux_params_1 = existing_actor_data["Aux Params 1"]
        if "Aux Params 2" in existing_actor_data:
          actor.aux_params_2 = existing_actor_data["Aux Params 2"]
        if "Position" in existing_actor_data:
          x, y, z = existing_actor_data["Position"]
          actor.x_pos = x
          actor.y_pos = y
          actor.z_pos = z
        if "Y Rotation" in existing_actor_data:
          actor.y_rot = existing_actor_data["Y Rotation"]
        
        actor.save_changes()
  
  # Add brand new actors when necessary.
  for stage_folder, enemy_locations in self.enemy_locations.items():
    for enemy_group in enemy_locations:
      if "New actors to add" not in enemy_group:
        continue
      
      new_actor_datas = enemy_group["New actors to add"]
      for new_actor_data in new_actor_datas:
        dzx, _, layer = get_dzx_fourcc_and_layer_by_path(self, enemy_group["Enemies"][0]["Path"])
        actor = dzx.add_entity("ACTR", layer=layer)
        
        actor.name = new_actor_data["Name"]
        actor.params = new_actor_data["Params"]
        if "Aux Params 1" in new_actor_data:
          actor.aux_params_1 = new_actor_data["Aux Params 1"]
        if "Aux Params 2" in new_actor_data:
          actor.aux_params_2 = new_actor_data["Aux Params 2"]
        if "Position" in new_actor_data:
          x, y, z = new_actor_data["Position"]
          actor.x_pos = x
          actor.y_pos = y
          actor.z_pos = z
        if "Y Rotation" in new_actor_data:
          actor.y_rot = new_actor_data["Y Rotation"]
        
        dzx.save_changes()
  
  # Remove actors when necessary.
  for stage_folder, enemy_locations in self.enemy_locations.items():
    for enemy_group in enemy_locations:
      if "Actors to remove" not in enemy_group:
        continue
      
      actor_paths = enemy_group["Actors to remove"]
      for actor_path in actor_paths:
        dzx, fourcc, layer = get_dzx_fourcc_and_layer_by_path(self, actor_path)
        actor = get_actor_by_path(self, actor_path)
        
        dzx.remove_entity(actor, fourcc, layer=layer)

def update_loaded_particles(self, particles_to_load_for_each_jpc_index):
  # Copy particles to stages that need them for the new enemies we placed.
  particle_and_textures_by_id = {}
  for dest_jpc_index, particle_ids in particles_to_load_for_each_jpc_index.items():
    for particle_id in particle_ids:
      dest_jpc_path = "files/res/Particle/Pscene%03d.jpc" % dest_jpc_index
      dest_jpc = self.get_jpc(dest_jpc_path)
      if particle_id in dest_jpc.particles_by_id:
        continue
      
      if particle_id in particle_and_textures_by_id:
        particle, textures = particle_and_textures_by_id[particle_id]
      else:
        particle = None
        for i in range(255):
          src_jpc_path = "files/res/Particle/Pscene%03d.jpc" % i
          if src_jpc_path.lower() not in self.gcm.files_by_path_lowercase:
            continue
          src_jpc = self.get_jpc(src_jpc_path)
          if particle_id not in src_jpc.particles_by_id:
            continue
          particle = src_jpc.particles_by_id[particle_id]
          textures = [
            src_jpc.textures_by_filename[texture_filename]
            for texture_filename in particle.tdb1.texture_filenames
          ]
          break
        
        if particle is None:
          raise Exception("Failed to find a particle with ID %04X in any of the game's JPC files." % particle_id)
        particle_and_textures_by_id[particle_id] = (particle, textures)
      
      copied_particle = copy.deepcopy(particle)
      dest_jpc.add_particle(copied_particle)
      
      for texture in textures:
        if texture.filename not in dest_jpc.textures_by_filename:
          copied_texture = copy.deepcopy(texture)
          dest_jpc.add_texture(copied_texture)

def print_all_enemy_params(self):
  all_enemy_actor_names = []
  for data in self.enemy_types:
    if data["Actor name"] not in all_enemy_actor_names:
      all_enemy_actor_names.append(data["Actor name"])
  
  print("% 7s  % 8s  % 4s  % 4s  %s" % ("name", "params", "aux1", "aux2", "path"))
  for dzx, arc_path in stage_searcher.each_stage_and_room(self):
    actors = dzx.entries_by_type("ACTR")
    enemies = [actor for actor in actors if actor.name in all_enemy_actor_names]
    for enemy in enemies:
      print("% 7s  %08X  %04X  %04X  %s" % (enemy.name, enemy.params, enemy.aux_params_1, enemy.aux_params_2, arc_path))

def print_all_enemy_locations(self):
  # Autogenerates an enemy_locations.txt file.
  
  all_enemy_actor_names = []
  for data in self.enemy_types:
    if data["Actor name"] not in all_enemy_actor_names:
      all_enemy_actor_names.append(data["Actor name"])
  
  output_str = ""
  prev_stage_folder = None
  prev_arc_name = None
  for dzx, arc_path in stage_searcher.each_stage_and_room(self):
    for layer in ([None] + list(range(11+1))):
      relative_arc_path = os.path.relpath(arc_path, "files/res/Stage")
      stage_folder, arc_name = os.path.split(relative_arc_path)
      relative_arc_path = stage_folder + "/" + arc_name
      
      actors = dzx.entries_by_type_and_layer("ACTR", layer)
      enemies = [
        actor for actor in actors
        if actor.name in all_enemy_actor_names
        and get_enemy_data_for_actor(self, actor)["Allow randomizing from"] # Don't list unrandomizable enemies
      ]
      
      if not enemies:
        continue
      
      # Add a comment before the start of each stage (or island) with its name.
      if stage_folder != prev_stage_folder or (stage_folder == "sea" and arc_name != prev_arc_name):
        if stage_folder == "sea" and arc_name != "Stage.arc":
          stage_name = self.island_names[arc_name]
        else:
          stage_name = self.stage_names[stage_folder]
        output_str += "\n"
        output_str += "\n"
        output_str += "# " + stage_name + "\n"
        if stage_folder == "sea":
          output_str += stage_folder + "/" + arc_name + ":\n"
        else:
          output_str += stage_folder + ":\n"
        prev_stage_folder = stage_folder
        prev_arc_name = arc_name
      
      # Start a new enemy group.
      # An enemy group is a list of enemies together in the same spot that must be killed together to progress. This is so the logic can be done for each group of enemies instead of each individual enemy, giving more room for enemy randomization variet.
      # This function simply creates one group for every layer that has enemies for each room, and sets the original vanilla logic requirements for the group to the combination of all the unique enemy species that were in that room.
      # This way is not necessarily correct in 100% of cases, you could have a room with some enemies you need to kill but some you don't, or a room where you need to kill enemies from both the default layer and a conditional layer to progress. Or you could have rooms where you don't need to kill any of the enemies to progress at all.
      # Therefore the groups and logic will need to be manually adjusted after the fact, this function just creates the base to work off of.
      defeat_reqs_for_this_layer = []
      for enemy in enemies:
        defeat_reqs = get_enemy_data_for_actor(self, enemy)["Requirements to defeat"]
        if defeat_reqs not in defeat_reqs_for_this_layer:
          defeat_reqs_for_this_layer.append(defeat_reqs)
      output_str += "-\n"
      output_str += "  Must defeat enemies: Yes\n"
      output_str += "  Original requirements:\n"
      output_str += "    " + "\n    & ".join(defeat_reqs_for_this_layer) + "\n"
      
      and_sws = [
        actor for actor in actors
        if actor.name in ["AND_SW0", "AND_SW2"]
      ]
      if and_sws:
        output_str += "  Actors to replace with ALLdies:\n"
        for and_sw in and_sws:
          layer_name = ""
          if layer != None:
            layer_name = "/Layer%x" % layer
          actor_index = actors.index(and_sw)
          and_sw_path = relative_arc_path + layer_name + "/Actor%03X" % actor_index
          
          output_str += "    - " + and_sw_path + "\n"
      
      output_str += "  Enemies:\n"
      
      # Then write each of the individual enemies in the group.
      for enemy in enemies:
        enemy_data = get_enemy_data_for_actor(self, enemy)
        
        placement_category = get_placement_category_for_vanilla_enemy_location(self, enemy_data, enemy)
        
        enemy_pretty_name = enemy_data["Pretty name"]
        
        defeat_reqs = enemy_data["Requirements to defeat"]
        
        layer_name = ""
        if layer != None:
          layer_name = "/Layer%x" % layer
        actor_index = actors.index(enemy)
        enemy_loc_path = relative_arc_path + layer_name + "/Actor%03X" % actor_index
        
        output_str += "    -\n"
        output_str += "      Original enemy: " + enemy_pretty_name + "\n"
        output_str += "      Placement category: " + placement_category + "\n"
        output_str += "      Path: " + enemy_loc_path + "\n"
  
  with open("enemy_locations.txt", "w") as f:
    f.write(output_str)

def get_enemy_data_for_actor(self, enemy):
  # This function determines the specific subspecies of enemy by looking at the enemy's actor name and parameters.
  enemy_datas_for_actor_name = [
    enemy_data
    for enemy_data in self.enemy_types
    if enemy_data["Actor name"] == enemy.name
  ]
  
  if len(enemy_datas_for_actor_name) == 0:
    raise Exception("Not a known enemy type: " + enemy.name)
  elif len(enemy_datas_for_actor_name) == 1:
    return enemy_datas_for_actor_name[0]
  
  enemy_datas_by_pretty_name = {}
  for enemy_data in enemy_datas_for_actor_name:
    pretty_name = enemy_data["Pretty name"]
    enemy_datas_by_pretty_name[pretty_name] = enemy_data
  
  if enemy.name == "mo2":
    if enemy.moblin_type == 1:
      return enemy_datas_by_pretty_name["Lantern Moblin"]
    elif enemy.moblin_type in [0, 0xF, 0xFF]:
      return enemy_datas_by_pretty_name["Blue Moblin"]
  if enemy.name == "p_hat":
    if enemy.peahat_type in [0xFF, 0]:
      return enemy_datas_by_pretty_name["Peahat"]
    elif enemy.peahat_type == 1:
      return enemy_datas_by_pretty_name["Seahat"]
  elif enemy.name == "amos2":
    if enemy.switch_type == 1 and enemy.switch_index == 0x80:
      return enemy_datas_by_pretty_name["Inanimate Armos"]
    else:
      return enemy_datas_by_pretty_name["Armos"]
  elif enemy.name == "Oqw":
    if enemy.octorok_type == 3:
      return enemy_datas_by_pretty_name["Saltwater Octorok Spawner"]
    else:
      return enemy_datas_by_pretty_name["Saltwater Octorok"]
  elif enemy.name == "nezumi":
    if enemy.rat_type in [0, 0xFF]:
      return enemy_datas_by_pretty_name["Rat"]
    elif enemy.rat_type == 1:
      return enemy_datas_by_pretty_name["Bombchu"]
  elif enemy.name == "nezuana":
    if enemy.rat_hole_type == 0 or enemy.rat_hole_type >= 3:
      return enemy_datas_by_pretty_name["Rat Hole"]
    elif enemy.rat_hole_type == 1:
      return enemy_datas_by_pretty_name["Bombchu Hole"]
    elif enemy.rat_hole_type == 2:
      return enemy_datas_by_pretty_name["Rat and Bombchu Hole"]
  elif enemy.name == "bbaba":
    if enemy.boko_bud_type in [0, 0xFF]:
      return enemy_datas_by_pretty_name["Boko Baba"]
    else:
      return enemy_datas_by_pretty_name["Boko Bud Boko Baba"]
  elif enemy.name == "bable":
    if enemy.bubble_type in [0, 2, 0xFF]:
      return enemy_datas_by_pretty_name["Red Bubble"]
    elif enemy.bubble_type in [1, 3]:
      return enemy_datas_by_pretty_name["Blue Bubble"]
    elif enemy.bubble_type == 0x80:
      return enemy_datas_by_pretty_name["Inanimate Bubble"]
  elif enemy.name == "gmos":
    if enemy.mothula_type == 1:
      return enemy_datas_by_pretty_name["Wingless Mothula"]
    elif enemy.mothula_type in [0, 2]:
      return enemy_datas_by_pretty_name["Winged Mothula"]
  
  raise Exception("Unknown enemy subspecies: actor name \"%s\", params %08X, aux params %04X, aux params 2 %04X" % (enemy.name, enemy.params, enemy.aux_params_1, enemy.aux_params_2))

def get_placement_category_for_vanilla_enemy_location(self, enemy_data, enemy):
  if len(enemy_data["Placement categories"]) == 1:
    # For enemy types that only have a single placement category, we don't need to check their params to know which one this is.
    return enemy_data["Placement categories"][0]
  
  if enemy.name == "Bk":
    if enemy.bokoblin_type in [2, 3]:
      return "Pot"
    else:
      return "Ground"
  elif enemy.name in ["c_green", "c_red", "c_kiiro", "c_blue", "c_black"]:
    if enemy.chuchu_behavior_type == 1:
      return "Ceiling"
    elif enemy.chuchu_behavior_type == 4:
      return "Pot"
    else:
      return "Ground"
  elif enemy.name == "Bb":
    if enemy.behavior_type in [4, 7]:
      return "Ground"
    else:
      return "Air"
  elif enemy.name in ["keeth", "Fkeeth"]:
    if enemy.behavior_type in [0, 0x80]:
      return "Ceiling"
    else:
      return "Air"
  elif enemy.name == "wiz_r":
    return "Ground"
    # Wizzrobes can appear on the ground or in the air, but we can't detect this by their params.
    # Will need to manually set air locations in enemy_locations.txt.
    # When doing this, will also need to change the logic from "Can Defeat Wizzrobes" to "Can Defeat Wizzrobes at Range".
  elif enemy.name in ["kuro_s", "kuro_t"]:
    if enemy.behavior_type == 6:
      return "Pot"
    else:
      return "Ground"
  elif enemy.name == "bable":
    if enemy.bubble_should_float == 1:
      return "Air"
    else:
      return "Ground"
  
  raise Exception("Unknown placement category for enemy: actor name \"%s\", params %08X, aux params %04X, aux params 2 %04X" % (enemy.name, enemy.params, enemy.aux_params_1, enemy.aux_params_2))

def is_enemy_allowed_in_placement_category(enemy_data, category):
  enemy_categories = enemy_data["Compiled categories"]
  
  return category in enemy_categories

def get_amount_of_memory_for_enemy(enemy_data, enemy_actor_names_already_placed_in_room):
  # The first enemy of a species placed in a room uses more than the subsequent ones.
  if enemy_data["Actor name"] in enemy_actor_names_already_placed_in_room:
    return enemy_data["Memory used by subequent ones"]
  else:
    return enemy_data["Memory used by first one"]

def get_free_memory_for_group(enemy_group):
  if "Free memory" in enemy_group:
    return enemy_group["Free memory"]
  else:
    # Default to 1mb free for rooms that don't have their actual amount documented.
    return 1000000

def randomize_enemy_params(self, enemy_data, enemy, category, dzx, layer):
  if enemy.name == "Bk":
    color = self.rng.choice(["blue", "green", "pink"])
    if category == "Pot":
      # The category (being in a pot) must take precedence.
      # Since being in a pot and being pink are both types, pink Bokoblins cannot be in pots.
      enemy.bokoblin_type = self.rng.choice([2, 3])
    elif color == "pink":
      enemy.bokoblin_type = 0xB
    else:
      enemy.bokoblin_type = self.rng.choice([0, 4])
    if color == "green":
      enemy.is_green = 1
    else:
      enemy.is_green = 0
    
    enemy.weapon = self.rng.choice([
      0, # Unlit torch
      1, # Machete
      2, # Lit torch
      3, # Machete
    ])
  elif enemy.name in ["c_green", "c_red", "c_kiiro", "c_blue", "c_black"]:
    if category == "Ceiling":
      enemy.chuchu_behavior_type = 1
    elif category == "Pot":
      enemy.chuchu_behavior_type = 4
    else:
      enemy.chuchu_behavior_type = 0
  elif enemy.name == "Bb":
    if category == "Ground":
      enemy.behavior_type = self.rng.choice([4, 7])
    elif category == "Air":
      enemy.behavior_type = self.rng.choice([0, 1, 2, 3])
    elif category == "Ceiling":
      # For locations where the enemy is placed up on the ceiling but is supposed to fall down, allow type 3 (flying and immediately flies down to the player) and types 4 and 7 (sitting, but targets the player when they get close enough). The other types (flying around) will never come down to fight the player and may even clip out of bounds.
      enemy.behavior_type = self.rng.choice([3, 4, 7])
  elif enemy.name == "mo2":
    enemy.moblin_type = self.rng.choice([0, 1])
  elif enemy.name == "p_hat":
    if category == "Ceiling":
      enemy.horizontal_range = 20
      enemy.vertical_range = 50
  elif enemy.name == "amos":
    enemy.behavior_type = self.rng.choice([
      0, # Normal
      1, # Guards an area and returns to its spawn point when Link leaves the area
    ])
  elif enemy.name == "amos2":
    pass
  elif enemy.name == "Sss":
    pass
  elif enemy.name in ["keeth", "Fkeeth"]:
    if category == "Ceiling":
      enemy.behavior_type = 0
      enemy.range = 2 # Increase range to 1500.0
    else:
      enemy.behavior_type = 1
  elif enemy.name == "Oq":
    # Freshwater Octorok.
    enemy.octorok_projectile_type = self.rng.choice([
      0, # Shoots rocks
      1, # Shoots bombs
    ])
  elif enemy.name == "Oqw":
    # Saltwater Octorok.
    if enemy_data["Pretty name"] == "Saltwater Octorok":
      enemy.octorok_type = self.rng.choice([
        1, # Single one that shoots at a certain range.
        4, # Single one that shoots after a certain delay.
      ])
    elif enemy_data["Pretty name"] == "Saltwater Octorok Spawner":
      enemy.octorok_type = 3 # Spawner
  elif enemy.name == "wiz_r":
    pass
  elif enemy.name in ["Rdead1", "Rdead2"]:
    enemy.idle_animation = self.rng.choice([0, 1])
  elif enemy.name == "pow":
    enemy.poe_type = self.rng.choice([
      0, # Visible from start
      1, # Invisible until noticing player
      2, # Poe invisible until noticing player but lantern always visible
    ])
    enemy.poe_floats = self.rng.choice([0, 1]) # 0 here will make it hover down if it's placed in the air (though the rando won't place them in the air so it shouldn't change anything).
    enemy.poe_color = self.rng.choice([0, 1, 2, 3, 4, 5])
  elif enemy.name in ["kuro_s", "kuro_t"]:
    if category == "Pot":
      enemy.behavior_type = 6
      
      # Three possible ranges to notice the player at and escape from the pot:
      # 0 (don't escape, wait for Link to break the pot), 20 (escape when Link is right next to the pot), and 60 (escape when Link is anywhere near the pot).
      enemy.pot_notice_range = self.rng.choice([0, 20, 60])
    else:
      enemy.behavior_type = self.rng.choice([0, 1])
    
    enemy.num_morths_in_group = self.rng.randrange(1, 10+1)
  elif enemy.name == "Puti":
    enemy.initial_spawn_delay = self.rng.choice([
      0, # Spawned from the start
      1, # Doesn't spawn until the player looks away from it
    ])
    
    # TODO: allow miniblin spawners in rooms where you don't need to kill all enemies. they should be a separate enemy type for randomization purposes.
  elif enemy.name == "nezumi":
    pass
  elif enemy.name == "nezuana":
    enemy.num_spawned_rats = self.rng.randrange(1, 5+1)
  elif enemy.name == "Stal":
    enemy.stalfos_type = self.rng.choice([
      0, # Normal
      1, # Underground
      0xE, # Upper half of body only
    ])
  elif enemy.name == "Tn":
    enemy.behavior_type = self.rng.choice([0, 4])
    enemy.color = self.rng.randrange(0, 5+1)
    enemy.equipment = self.rng.randrange(0, 5+1)
  elif enemy.name == "bbaba":
    pass
  elif enemy.name == "magtail":
    pass
  elif enemy.name == "bable":
    if category == "Air":
      enemy.bubble_should_float = 1
    elif category in ["Ground", "Ceiling"]:
      enemy.bubble_should_float = 0
  elif enemy.name == "gmos":
    if enemy_data["Pretty name"] == "Winged Mothula":
      number_of_wings_to_have = self.rng.choice([1, 2, 2, 3, 3, 4, 4, 4, 4, 4])
      number_of_wings_to_be_missing = 4 - number_of_wings_to_have
      
      wing_indexes_to_be_missing = [0, 1, 2, 3]
      self.rng.shuffle(wing_indexes_to_be_missing)
      wing_indexes_to_be_missing = wing_indexes_to_be_missing[0:number_of_wings_to_be_missing]
      
      enemy.mothula_initially_missing_wings = 0
      for wing_index in wing_indexes_to_be_missing:
        enemy.mothula_initially_missing_wings |= (1 << wing_index)
  elif enemy.name in ["GyCtrl", "GyCtrlB"]:
    enemy.num_spawned_gyorgs = self.rng.choice([1, 1, 1, 1, 2, 2, 3, 3, 4, 5])
  elif enemy.name in ["Fmaster", "Fmastr1", "Fmastr2"]:
    enemy.targeting_behavior_type = self.rng.choice([
      0, # Prioritize Medli/Makar over Link if they're present
      1, # Target only Link
      # 2, # Target only Medli/Makar (Do not allow this one because the floormaster would never come up and be killable if not in a stage with a partner)
    ])
    # TODO maybe set the floormaster's exit index to take medli/makar in when capturing them if in earth or wind temple. and what happens if medli/makar is captured by a floormaster with that not set?

def adjust_enemy(self, enemy_data, enemy, category, dzx, layer):
  if category == "Ceiling" and "Ceiling" not in enemy_data["Placement categories"]:
    # Placing Air enemies in Ceiling locations can cause them to clip out of bounds.
    # Move them down to avoid this.
    enemy.y_pos -= 500.0
  
  if enemy.name == "magtail":
    # Magtails wind up being slightly inside the floor for some reason, so bump them up a bit.
    enemy.y_pos += 50.0
  elif enemy.name in ["c_green", "c_red", "c_kiiro", "c_blue", "c_black"] and category == "Pot":
    # ChuChus in pots will only appear if the pot has the EXACT same position as the ChuChu, just being very close is not enough.
    pots_on_same_layer = [
      actor for actor in dzx.entries_by_type_and_layer("ACTR", layer)
      if actor.actor_class_name == "d_a_tsubo"
    ]
    if not pots_on_same_layer:
      raise Exception("No pots on same layer as ChuChu in a pot")
    closest_pot = min(pots_on_same_layer, key=lambda pot: distance_between_entities(enemy, pot))
    enemy.x_pos = closest_pot.x_pos
    enemy.y_pos = closest_pot.y_pos
    enemy.z_pos = closest_pot.z_pos

def get_enemy_instance_by_path(self, path):
  match = re.search(r"^([^/]+/[^/]+\.arc)(?:/Layer([0-9a-b]))?/Actor([0-9A-F]{3})$", path)
  if not match:
    raise Exception("Invalid actor path: %s" % path)
  
  arc_name = match.group(1)
  arc_path = "files/res/Stage/" + arc_name
  if match.group(2):
    layer = int(match.group(2), 16)
  else:
    layer = None
  actor_index = int(match.group(3), 16)
  
  if arc_path.endswith("Stage.arc"):
    dzx = self.get_arc(arc_path).get_file("stage.dzs")
  else:
    dzx = self.get_arc(arc_path).get_file("room.dzr")
  enemy = dzx.entries_by_type_and_layer("ACTR", layer)[actor_index]
  
  if enemy.name not in self.all_enemy_actor_names:
    raise Exception("Enemy location path %s points to a %s actor, not an enemy!" % (path, enemy.name))
  
  return (enemy, arc_name, dzx, layer)

def get_fourcc_by_english_chunk_name(dzx_chunk_type_name):
  if dzx_chunk_type_name == "Actor":
    return "ACTR"
  elif dzx_chunk_type_name == "ScalableObject":
    return "SCOB"
  elif dzx_chunk_type_name == "Door":
    return "DOOR"
  elif dzx_chunk_type_name == "ScalableDoor":
    return "TGDR"
  else:
    raise Exception("Unknown DZx chunk type name: %s" % dzx_chunk_type_name)

def get_actor_by_path(self, path):
  match = re.search(r"^([^/]+/[^/]+\.arc)(?:/Layer([0-9a-b]))?/(Actor|ScalableObject|Door|ScalableDoor)([0-9A-F]{3})$", path)
  if not match:
    raise Exception("Invalid actor path: %s" % path)
  
  arc_name = match.group(1)
  arc_path = "files/res/Stage/" + arc_name
  if match.group(2):
    layer = int(match.group(2), 16)
  else:
    layer = None
  dzx_chunk_type_name = match.group(3)
  fourcc = get_fourcc_by_english_chunk_name(dzx_chunk_type_name)
  actor_index = int(match.group(4), 16)
  
  if arc_path.endswith("Stage.arc"):
    dzx = self.get_arc(arc_path).get_file("stage.dzs")
  else:
    dzx = self.get_arc(arc_path).get_file("room.dzr")
  actor = dzx.entries_by_type_and_layer(fourcc, layer)[actor_index]
  
  return actor

def get_dzx_fourcc_and_layer_by_path(self, path):
  match = re.search(r"^([^/]+/[^/]+\.arc)(?:/Layer([0-9a-b]))?/(Actor|ScalableObject|Door|ScalableDoor)([0-9A-F]{3})$", path)
  if not match:
    raise Exception("Invalid actor path: %s" % path)
  
  arc_name = match.group(1)
  arc_path = "files/res/Stage/" + arc_name
  if match.group(2):
    layer = int(match.group(2), 16)
  else:
    layer = None
  
  if arc_path.endswith("Stage.arc"):
    dzx = self.get_arc(arc_path).get_file("stage.dzs")
  else:
    dzx = self.get_arc(arc_path).get_file("room.dzr")
  
  dzx_chunk_type_name = match.group(3)
  fourcc = get_fourcc_by_english_chunk_name(dzx_chunk_type_name)
  
  return (dzx, fourcc, layer)

def distance_between_entities(entity_1, entity_2):
  x1, y1, z1 = entity_1.x_pos, entity_1.y_pos, entity_1.z_pos
  x2, y2, z2 = entity_2.x_pos, entity_2.y_pos, entity_2.z_pos
  
  return math.sqrt((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)


class EnemyCategory:
  def __init__(self, category_string, enemy_type=None):
    self.category_string = category_string
    
    if enemy_type is None:
      # When enemy_type is not passed (e.g. `EnemyCategory("Pot")`) default to assuming the most flexible possible enemy.
      self.can_set_switch = True
    else:
      if enemy_type["Death switch param name"] is None:
        self.can_set_switch = False
      else:
        self.can_set_switch = True
  
  def __eq__(self, other):
    if not isinstance(other, str):
      raise NotImplementedError()
    
    if ":" in other:
      other_category_string, other_conditions_string = other.split(":", 1)
      other_conditions = other_conditions_string.split(",")
    else:
      other_category_string = other
      other_conditions = []
    
    for other_condition in other_conditions:
      if other_condition == "SetsDeathSwitch":
        if not self.can_set_switch:
          return False
      else:
        raise NotImplementedError("Enemy placement category condition type not implemented: %s" % other_condition)
    
    if other_category_string == self.category_string:
      return True
    
    if other_category_string == "Pot" and self.category_string == "Ground":
      return True
    
    if other_category_string in ["Ground", "Pot"] and self.category_string == "Air":
      return True
    
    if other_category_string == "StationaryAir" and self.category_string == "Air":
      return True
    
    return False
  
  def __str__(self):
    return "EnemyCategory(%s, DeathSwitch: %s)" % (self.category_string, self.can_set_switch)
  
  def __repr__(self):
    return self.__str__()
