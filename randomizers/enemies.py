
import os
import copy
import re
from collections import OrderedDict

from wwlib import stage_searcher
from logic.logic import Logic

def randomize_enemies(self):
  self.enemy_locations = Logic.load_and_parse_enemy_locations()
  
  enemies_to_randomize_to = [
    data for data in self.enemy_types
    if data["Allow randomizing to"]
  ]
  
  enemy_datas_by_pretty_name = {}
  for enemy_data in self.enemy_types:
    pretty_name = enemy_data["Pretty name"]
    enemy_datas_by_pretty_name[pretty_name] = enemy_data
  
  enemy_actor_names_placed_in_stage = {}
  particles_to_load_for_each_jpc_index = OrderedDict()
  
  for enemy_group in self.enemy_locations:
    original_req_string = enemy_group["Original requirements"]
    #if original_req_string == "Nothing":
    #  print(enemy_group)
    enemies_to_randomize_to_for_this_group = self.logic.filter_out_enemies_that_add_new_requirements(original_req_string, enemies_to_randomize_to)
    #print("Original: %s" % (original_req_string))
    #print("New allowed:")
    #for enemy_data in enemies_to_randomize_to_for_this_group:
    #  print("  " + enemy_data["Pretty name"])
    #print("New disallowed:")
    #enemies_not_allowed_in_this_group = [
    #  data for data in enemies_to_randomize_to
    #  if data not in enemies_to_randomize_to_for_this_group
    #]
    #for enemy_data in enemies_not_allowed_in_this_group:
    #  print("  " + enemy_data["Pretty name"])
    
    enemy_actor_names_placed_in_this_group = []
    
    for enemy_location in enemy_group["Enemies"]:
      enemy, arc_name = get_enemy_and_arc_name_for_path(self, enemy_location["Path"])
      stage_name, room_arc_name = arc_name.split("/")
      
      if stage_name != "sea":
        if stage_name not in enemy_actor_names_placed_in_stage:
          enemy_actor_names_placed_in_stage[stage_name] = []
        
        if len(enemy_actor_names_placed_in_stage[stage_name]) >= 10:
          # Placed a lot of different enemy types in this stage already.
          # Instead of placing yet another new type, reuse a type we already used to prevent loading too many different particle IDs for this stage or making the stage feel too chaotic.
          enemies_to_randomize_to_for_this_group = [
            data for data in enemies_to_randomize_to_for_this_group
            if data["Actor name"] in enemy_actor_names_placed_in_stage[stage_name]
          ]
          if len(enemies_to_randomize_to_for_this_group) == 0:
            raise Exception("Cannot place any more enemy species in stage %s but the existing ones aren't logically allowed")
      
      if len(enemy_actor_names_placed_in_this_group) >= 5:
        # Placed a lot of different enemy types in this room already.
        # Instead of placing yet another new type, reuse a type we already used to prevent overloading the available RAM or making combat in this room too chaotic.
        filtered_enemy_types_data = [
          data for data in enemies_to_randomize_to_for_this_group
          if data["Actor name"] in enemy_actor_names_placed_in_this_group
        ]
        new_enemy_data = self.rng.choice(filtered_enemy_types_data)
      else:
        new_enemy_data = self.rng.choice(enemies_to_randomize_to_for_this_group)
      
      #new_enemy_data = enemy_datas_by_pretty_name["Wizzrobe"]
      
      if False:
        print("Putting a %s (param:%08X) in %s" % (new_enemy_data["Actor name"], new_enemy_data["Params"], arc_path))
      
      enemy.name = new_enemy_data["Actor name"]
      enemy.params = new_enemy_data["Params"]
      enemy.auxilary_param = new_enemy_data["Aux params"]
      enemy.auxilary_param_2 = new_enemy_data["Aux params 2"]
      enemy.save_changes()
      if new_enemy_data["Actor name"] not in enemy_actor_names_placed_in_this_group:
        # TODO: we should consider 2 different names that are the same actor to be the same...
        enemy_actor_names_placed_in_this_group.append(new_enemy_data["Actor name"])
      if stage_name != "sea" and new_enemy_data["Actor name"] not in enemy_actor_names_placed_in_stage[stage_name]:
        enemy_actor_names_placed_in_stage[stage_name].append(new_enemy_data["Actor name"])
      #print("% 7s  %08X  %s" % (enemy.name, enemy.params, arc_path))
      
      if stage_name == "sea":
        dzr = self.get_arc("files/res/Stage/sea/" + room_arc_name).get_file("room.dzr")
        dest_jpc_index = dzr.entries_by_type("FILI")[0].loaded_particle_bank
      else:
        dzs = self.get_arc("files/res/Stage/" + stage_name + "/Stage.arc").get_file("stage.dzs")
        dest_jpc_index = dzs.entries_by_type("STAG")[0].loaded_particle_bank
      
      if dest_jpc_index not in particles_to_load_for_each_jpc_index:
        particles_to_load_for_each_jpc_index[dest_jpc_index] = []
      for particle_id in new_enemy_data["Required particle IDs"]:
        if particle_id not in particles_to_load_for_each_jpc_index[dest_jpc_index]:
          particles_to_load_for_each_jpc_index[dest_jpc_index].append(particle_id)
  
  update_loaded_particles(self, particles_to_load_for_each_jpc_index)

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
    if enemy.bokoblin_type == 3:
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
