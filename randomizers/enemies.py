
import os
import copy
import re
from collections import OrderedDict

from wwlib import stage_searcher
from logic.logic import Logic

# Limit the number of species that appear in a given stage to prevent issues loading too many particles and to prevent stages from feeling too chaotic.
# (This limit does not apply to the sea.)
MAX_ENEMY_SPECIES_PER_STAGE = 10

# Limit the number of species in a single room at a time too.
MAX_ENEMY_SPECIES_PER_GROUP = 5

def randomize_enemies(self):
  self.enemy_locations = Logic.load_and_parse_enemy_locations()
  
  self.enemies_to_randomize_to = [
    data for data in self.enemy_types
    if data["Allow randomizing to"]
  ]
  
  self.enemy_datas_by_pretty_name = {}
  for enemy_data in self.enemy_types:
    pretty_name = enemy_data["Pretty name"]
    self.enemy_datas_by_pretty_name[pretty_name] = enemy_data
  
  self.particles_to_load_for_each_jpc_index = OrderedDict()
  
  decide_on_enemy_pools_for_each_stage(self)
  
  for stage_folder, enemy_locations in self.enemy_locations.items():
    for enemy_group in enemy_locations:
      randomize_enemy_group(self, stage_folder, enemy_group)
  
  update_loaded_particles(self, self.particles_to_load_for_each_jpc_index)

def decide_on_enemy_pools_for_each_stage(self):
  # First decide on the enemy pools that will be available in each stage in advance.
  # This is so we can guarantee every room in each stage will be able to have at least one enemy, instead of later rooms being limited to no enemies that work by a combination of their logic, their placement categories, and enemies that were already placed in other rooms of that stage.
  self.enemy_pool_for_stage = OrderedDict()
  #enemies_logically_allowed_for_group = {}
  for stage_folder, enemy_locations in self.enemy_locations.items():
    if stage_folder == "sea":
      # The sea stage should have no limit on the number of enemies in it.
      # Particle banks are loaded per-room on the sea.
      self.enemy_pool_for_stage[stage_folder] = self.enemies_to_randomize_to
      continue
    
    category_and_logic_combos_needed = []
    for enemy_group in enemy_locations:
      original_req_string = enemy_group["Original requirements"]
      enemies_logically_allowed_in_this_group = self.logic.filter_out_enemies_that_add_new_requirements(original_req_string, self.enemies_to_randomize_to)
      #enemies_logically_allowed_for_group[enemy_group] = enemies_logically_allowed_in_this_group # Cache
      
      for enemy_location in enemy_group["Enemies"]:
        category_and_logic_combo = (enemy_location["Placement category"], enemies_logically_allowed_in_this_group)
        if category_and_logic_combo not in category_and_logic_combos_needed:
          category_and_logic_combos_needed.append(category_and_logic_combo)
    
    # First build a minimum list of enemies to allow in this stage to make sure every location in it can have at least one possible enemy there.
    self.enemy_pool_for_stage[stage_folder] = []
    all_enemies_possible_for_this_stage = []
    for category, enemies_logically_allowed in category_and_logic_combos_needed:
      enemies_allowed_for_combo = [
        enemy_data for enemy_data in enemies_logically_allowed
        if category in enemy_data["Placement categories"]
      ]
      
      for enemy_data in enemies_allowed_for_combo:
        if enemy_data not in all_enemies_possible_for_this_stage:
          all_enemies_possible_for_this_stage.append(enemy_data)
      
      enemies_allowed_already_in_pool = [
        enemy_data for enemy_data in enemies_allowed_for_combo
        if enemy_data in self.enemy_pool_for_stage[stage_folder]
      ]
      if enemies_allowed_already_in_pool:
        # One of the other category/logic combos we added an enemy for also happened to fulfill this combo.
        # No need to add another.
        continue
      
      chosen_enemy = self.rng.choice(enemies_allowed_for_combo)
      self.enemy_pool_for_stage[stage_folder].append(chosen_enemy)
    
    num_species_chosen = len(self.enemy_pool_for_stage[stage_folder])
    if num_species_chosen > MAX_ENEMY_SPECIES_PER_STAGE:
      raise Exception("Enemy species pool for %s has %d species in it instead of %d" % (stage_folder, num_species_chosen, MAX_ENEMY_SPECIES_PER_STAGE))
    elif num_species_chosen < MAX_ENEMY_SPECIES_PER_STAGE:
      # Fill up the pool with other random enemies that can go in this stage.
      for i in range(MAX_ENEMY_SPECIES_PER_STAGE-num_species_chosen):
        enemies_possible_for_this_stage_minus_chosen = [
          enemy_data for enemy_data in all_enemies_possible_for_this_stage
          if enemy_data not in self.enemy_pool_for_stage[stage_folder]
        ]
        
        if not enemies_possible_for_this_stage_minus_chosen:
          # The number of enemy species that can actually be placed in this stage is less than the max species per stage.
          # Just exit early with a pool smaller than normal in this case.
          break
        
        chosen_enemy = self.rng.choice(enemies_possible_for_this_stage_minus_chosen)
        self.enemy_pool_for_stage[stage_folder].append(chosen_enemy)
  
def randomize_enemy_group(self, stage_folder, enemy_group):
  original_req_string = enemy_group["Original requirements"]
  enemies_logically_allowed_in_this_group = self.logic.filter_out_enemies_that_add_new_requirements(original_req_string, self.enemies_to_randomize_to)
  
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
      if category in enemy_data["Placement categories"]
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
  
  for enemy_location in enemy_group["Enemies"]:
    enemy, arc_name = get_enemy_and_arc_name_for_path(self, enemy_location["Path"])
    stage_folder, room_arc_name = arc_name.split("/")
    
    enemies_to_randomize_to_for_this_location = [
      data for data in enemy_pool_for_group
      if enemy_location["Placement category"] in data["Placement categories"]
    ]
    
    if len(enemies_to_randomize_to_for_this_location) == 0:
      error_msg = "No possible enemies to place in %s of the correct category\n" % arc_name
      enemy_pretty_names_in_this_stage_pool = [
        enemy_data["Pretty name"]
        for enemy_data in self.enemy_pool_for_stage[stage_folder]
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
        if enemy_location["Placement category"] in data["Placement categories"]:
          if data["Actor name"] not in enemy_actor_names_of_correct_category:
            enemy_actor_names_of_correct_category.append(data["Actor name"])
      error_msg += "Enemies of the correct category (%s): %s" % (enemy_location["Placement category"], ", ".join(enemy_actor_names_of_correct_category))
      raise Exception(error_msg)
    
    new_enemy_data = self.rng.choice(enemies_to_randomize_to_for_this_location)
    
    #new_enemy_data = self.enemy_datas_by_pretty_name["Wizzrobe"]
    
    if False:
      print("Putting a %s (param:%08X) in %s" % (new_enemy_data["Actor name"], new_enemy_data["Params"], arc_name))
    
    enemy.name = new_enemy_data["Actor name"]
    enemy.params = new_enemy_data["Params"]
    enemy.auxilary_param = new_enemy_data["Aux params"]
    enemy.auxilary_param_2 = new_enemy_data["Aux params 2"]
    set_enemy_params_for_placement_category(self, new_enemy_data, enemy, enemy_location["Placement category"])
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
      print("% 7s  %08X  %04X  %04X  %s" % (enemy.name, enemy.params, enemy.auxilary_param, enemy.auxilary_param_2, arc_path))

def print_all_enemy_locations(self):
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
      output_str += "  Original requirements:\n"
      output_str += "    " + "\n    & ".join(defeat_reqs_for_this_layer) + "\n"
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
  
  if enemy.name == "Bk":
    if enemy.bokoblin_type == 0xB:
      return enemy_datas_by_pretty_name["Pink Bokoblin"]
    elif enemy.bokoblin_is_green != 0:
      return enemy_datas_by_pretty_name["Green Bokoblin"]
    else:
      return enemy_datas_by_pretty_name["Blue Bokoblin"]
  elif enemy.name == "mo2":
    if enemy.moblin_type == 0:
      return enemy_datas_by_pretty_name["Moblin"]
    elif enemy.moblin_type == 1:
      return enemy_datas_by_pretty_name["Lantern Moblin"]
    elif enemy.moblin_type in [0xF, 0xFF]:
      return enemy_datas_by_pretty_name["Blue Moblin"]
  elif enemy.name == "p_hat":
    if enemy.peahat_type in [0xFF, 0]:
      return enemy_datas_by_pretty_name["Peahat"]
    elif enemy.peahat_type == 1:
      return enemy_datas_by_pretty_name["Seahat"]
  elif enemy.name == "amos2":
    if enemy.armos_switch_type == 1 and enemy.armos_switch_index == 0x80:
      return enemy_datas_by_pretty_name["Inanimate Armos"]
    else:
      return enemy_datas_by_pretty_name["Armos"]
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
  elif enemy.name == "Tn":
    if enemy.darknut_behavior_type == 0:
      return enemy_datas_by_pretty_name["Darknut"]
    elif enemy.darknut_behavior_type == 4:
      return enemy_datas_by_pretty_name["Shield Darknut"]
    elif enemy.darknut_behavior_type == 0xD:
      return enemy_datas_by_pretty_name["Mini-Boss Darknut"]
    elif enemy.darknut_behavior_type == 0xE:
      return enemy_datas_by_pretty_name["Mighty Darknut"]
    elif enemy.darknut_behavior_type == 0xF:
      return enemy_datas_by_pretty_name["Frozen Darknut"]
  elif enemy.name == "bable":
    if enemy.bubble_type in [0, 2, 0xFF]:
      return enemy_datas_by_pretty_name["Red Bubble"]
    elif enemy.bubble_type in [1, 3]:
      return enemy_datas_by_pretty_name["Blue Bubble"]
    elif enemy.bubble_type == 0x80:
      return enemy_datas_by_pretty_name["Inanimate Bubble"]
  elif enemy.name == "gmos":
    if enemy.mothula_type == 0:
      return enemy_datas_by_pretty_name["Mini-Boss Winged Mothula"]
    elif enemy.mothula_type == 1:
      return enemy_datas_by_pretty_name["Wingless Mothula"]
    elif enemy.mothula_type == 2:
      return enemy_datas_by_pretty_name["Winged Mothula"]
  
  raise Exception("Unknown enemy subspecies: actor name \"%s\", params %08X, aux params %04X, aux params 2 %04X" % (enemy.name, enemy.params, enemy.auxilary_param, enemy.auxilary_param_2))

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
    if enemy.kargaroc_behavior_type in [4, 7]:
      return "Ground"
    else:
      return "Air"
  elif enemy.name in ["kuro_s", "kuro_t"]:
    if enemy.morth_behavior_type == 6:
      return "Pot"
    else:
      return "Ground"
  
  raise Exception("Unknown placement category for enemy: actor name \"%s\", params %08X, aux params %04X, aux params 2 %04X" % (enemy.name, enemy.params, enemy.auxilary_param, enemy.auxilary_param_2))

def set_enemy_params_for_placement_category(self, enemy_data, enemy, category):
  if enemy.name == "Bk":
    if category == "Pot":
      enemy.bokoblin_type = 3
  elif enemy.name in ["c_green", "c_red", "c_kiiro", "c_blue", "c_black"]:
    if category == "Ceiling":
      enemy.chuchu_behavior_type = 1
    elif category == "Pot":
      enemy.chuchu_behavior_type = 4
  elif enemy.name == "Bb":
    if category == "Ground":
      enemy.kargaroc_behavior_type = 4
  elif enemy.name in ["kuro_s", "kuro_t"]:
    if category == "Pot":
      enemy.morth_behavior_type = 6

def get_enemy_and_arc_name_for_path(self, path):
  match = re.search(r"^([^/]+/[^/]+\.arc)(?:/Layer([0-9a-b]))?/Actor([0-9A-F]{3})$", path)
  if not match:
    raise Exception("Invalid enemy path: %s" % path)
  
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
  
  return (enemy, arc_name)
