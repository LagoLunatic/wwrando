
import os
import copy

from wwlib import stage_searcher

def randomize_enemies(self):
  enemy_actor_names_to_randomize_from = []
  for data in self.enemy_types:
    if data["Allow randomizing from"] and data not in enemy_actor_names_to_randomize_from:
      enemy_actor_names_to_randomize_from.append(data)
  
  enemies_to_randomize_to = [
    data for data in self.enemy_types
    if data["Allow randomizing to"]
  ]
  
  for dzx, arc_path in stage_searcher.each_stage_and_room(self):
    actors = dzx.entries_by_type("ACTR")
    enemies = [actor for actor in actors if actor.name in enemy_actor_names_to_randomize_from]
    
    actor_names_in_this_room = []
    for enemy in enemies:
      if len(actor_names_in_this_room) >= 8:
        filtered_enemy_types_data = [
          data for data in enemies_to_randomize_to
          if data["Actor name"] in actor_names_in_this_room
        ]
        new_enemy_data = self.rng.choice(filtered_enemy_types_data)
      else:
        new_enemy_data = self.rng.choice(enemies_to_randomize_to)
      
      if "sea/Room13" in arc_path:
        print("Putting a %s (param:%08X) in %s" % (new_enemy_data["Actor name"], new_enemy_data["Params"], arc_path))
      
      enemy.name = new_enemy_data["Actor name"]
      enemy.params = new_enemy_data["Params"]
      enemy.auxilary_param = new_enemy_data["Aux params"]
      enemy.auxilary_param_2 = new_enemy_data["Aux params 2"]
      enemy.save_changes()
      if new_enemy_data["Actor name"] not in actor_names_in_this_room:
        # TODO: we should consider 2 different names that are the same actor to be the same...
        actor_names_in_this_room.append(new_enemy_data["Actor name"])
      #print("% 7s  %08X  %s" % (enemy.name, enemy.params, arc_path))
  
  
  
  et_jpc = self.get_jpc("files/res/Particle/Pscene060.jpc")
  chuchu_jpc = self.get_jpc("files/res/Particle/Pscene203.jpc")
  
  for particle_id in [0x8122, 0x8123, 0x8124]:
    particle = et_jpc.particles_by_id[particle_id]
    
    for dest_jpc in [chuchu_jpc]:
      copied_particle = copy.deepcopy(particle)
      dest_jpc.add_particle(copied_particle)
      
      for texture_filename in copied_particle.tdb1.texture_filenames:
        if texture_filename not in dest_jpc.textures_by_filename:
          texture = et_jpc.textures_by_filename[texture_filename]
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
      enemies = [actor for actor in actors if actor.name in all_enemy_actor_names]
      
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
      logic_macros_for_this_layer = []
      for enemy in enemies:
        logic_macro = get_enemy_data_for_actor(self, enemy)["Logic macro"]
        if logic_macro not in logic_macros_for_this_layer:
          logic_macros_for_this_layer.append(logic_macro)
      output_str += "-\n"
      output_str += "  Original requirements:\n"
      output_str += "    " + "\n    & ".join(logic_macros_for_this_layer) + "\n"
      output_str += "  Enemies:\n"
      
      # Then write each of the individual enemies in the group.
      for enemy in enemies:
        enemy_data = get_enemy_data_for_actor(self, enemy)
        
        enemy_pretty_name = enemy_data["Pretty name"]
        
        logic_macro = enemy_data["Logic macro"]
        
        layer_name = ""
        if layer != None:
          layer_name = "/Layer%X" % layer
        actor_index = actors.index(enemy)
        enemy_loc_path = relative_arc_path + layer_name + "/Actor%03X" % actor_index
        
        output_str += "    -\n"
        output_str += "      Original enemy: " + enemy_pretty_name + "\n"
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
