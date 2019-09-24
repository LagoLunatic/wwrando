
import copy

from wwlib import stage_searcher

ENEMIES_TO_RANDOMIZE_FROM = [
  "Bk",
  "c_blue",
  "c_green",
  "c_kiiro",
  "c_red",
  "c_black",
  "Bb",
  "mo2",
  "Tn",
  "bbaba",
  "p_hat",
  "Puti",
  "amos",
  "amos2",
  "nezumi",
  "Hmos1",
  "Hmos2",
  "Sss",
  "Stal",
  "Fmaster",
  "Fmastr1",
  "Fmastr2",
  "magtail",
  "keeth",
  "Fkeeth",
  "Oq",
  "Oqw",
  "wiz_r",
  "wiz_s",
  "wiz_m",
  "wiz_o",
  "Rdead1",
  "Rdead2",
  "sea_hat",
  "pow",
  "bable",
  "gmos",
  "kuro_s",
  "kuro_t",
  "GyCtrl",
  "GyCtrlB",
]

def randomize_enemies(self):
  for dzx, arc_path in stage_searcher.each_stage_and_room(self):
    actors = dzx.entries_by_type("ACTR")
    enemies = [actor for actor in actors if actor.name in ENEMIES_TO_RANDOMIZE_FROM]
    
    actor_names_in_this_room = []
    for enemy in enemies:
      if len(actor_names_in_this_room) >= 8:
        filtered_enemy_types_data = [data for data in self.enemy_types if data["Actor name"] in actor_names_in_this_room]
        new_enemy_data = self.rng.choice(filtered_enemy_types_data)
      else:
        new_enemy_data = self.rng.choice(self.enemy_types)
      
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
  print("% 7s  % 8s  % 4s  % 4s  %s" % ("name", "params", "aux1", "aux2", "path"))
  for dzx, arc_path in stage_searcher.each_stage_and_room(self):
    actors = dzx.entries_by_type("ACTR")
    enemies = [actor for actor in actors if actor.name in ENEMIES_TO_RANDOMIZE_FROM]
    for enemy in enemies:
      print("% 7s  %08X  %04X  %04X  %s" % (enemy.name, enemy.params, enemy.auxilary_param, enemy.auxilary_param_2, arc_path))
