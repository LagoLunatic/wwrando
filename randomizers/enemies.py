
import os
import copy

from wwlib import stage_searcher

def randomize_enemies(self):
  enemy_actor_names_to_randomize_from = [
    data["Actor name"] for data in self.enemy_types
    if data["Allow randomizing from"]
  ]
  enemy_actor_names_to_randomize_from = list(set(enemy_actor_names_to_randomize_from)) # Remove duplicates
  
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
  all_enemy_actor_names = [
    data["Actor name"] for data in self.enemy_types
  ]
  all_enemy_actor_names = list(set(all_enemy_actor_names)) # Remove duplicates
  
  print("% 7s  % 8s  % 4s  % 4s  %s" % ("name", "params", "aux1", "aux2", "path"))
  for dzx, arc_path in stage_searcher.each_stage_and_room(self):
    actors = dzx.entries_by_type("ACTR")
    enemies = [actor for actor in actors if actor.name in all_enemy_actor_names]
    for enemy in enemies:
      print("% 7s  %08X  %04X  %04X  %s" % (enemy.name, enemy.params, enemy.auxilary_param, enemy.auxilary_param_2, arc_path))

def print_all_enemy_locations(self):
  all_enemy_actor_names = [
    data["Actor name"] for data in self.enemy_types
  ]
  all_enemy_actor_names = list(set(all_enemy_actor_names)) # Remove duplicates
  
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
      
      actor_names_in_this_room = []
      for enemy in enemies:
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
        
        enemy_data = next(data for data in self.enemy_types if data["Actor name"] == enemy.name)
        
        enemy_pretty_name = enemy_data["Pretty name"]
        
        logic_macro = enemy_data["Logic macro"]
        
        layer_name = ""
        if layer != None:
          layer_name = "/Layer%X" % layer
        actor_index = actors.index(enemy)
        enemy_loc_path = relative_arc_path + layer_name + "/Actor%03X" % actor_index
        
        output_str += "-\n"
        output_str += "  Original enemy: " + enemy_pretty_name + "\n"
        output_str += "  Need: " + logic_macro + "\n"
        output_str += "  Path: " + enemy_loc_path + "\n"
  
  with open("enemy_locations.txt", "w") as f:
    f.write(output_str)
