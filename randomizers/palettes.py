
import os

from wwlib import texture_utils

from fs_helpers import *

def randomize_enemy_palettes(self):
  for randomizable_file_group in self.palette_randomizable_files:
    h_shift = self.rng.randint(20, 340)
    v_shift = self.rng.randint(-40, 40)
    #print(h_shift, v_shift)
    
    if randomizable_file_group["Name"] == "Darknut":
      shift_hardcoded_darknut_colors(self, h_shift, v_shift)
    elif randomizable_file_group["Name"] == "Moblin":
      shift_hardcoded_moblin_colors(self, h_shift, v_shift)
    elif randomizable_file_group["Name"] == "Stalfos":
      shift_hardcoded_stalfos_colors(self, h_shift, v_shift)
    elif randomizable_file_group["Name"] == "Rat":
      shift_hardcoded_rat_colors(self, h_shift, v_shift)
    elif randomizable_file_group["Name"] == "Puppet Ganon":
      shift_hardcoded_puppet_ganon_colors(self, h_shift, v_shift)
    elif randomizable_file_group["Name"] == "Ganondorf":
      shift_hardcoded_ganondorf_colors(self, h_shift, v_shift)
    
    if randomizable_file_group["Particle IDs"]:
      particle_ids = randomizable_file_group["Particle IDs"]
      for i in range(255):
        jpc_path = "files/res/Particle/Pscene%03d.jpc" % i
        if jpc_path.lower() not in self.gcm.files_by_path_lowercase:
          continue
        jpc = self.get_jpc(jpc_path)
        
        particle_ids_for_enemy_in_jpc = [particle_id for particle_id in jpc.particles_by_id if particle_id in particle_ids]
        if not particle_ids_for_enemy_in_jpc:
          continue
        
        for particle_id in particle_ids_for_enemy_in_jpc:
          particle = jpc.particles_by_id[particle_id]
          shift_all_colors_in_particle(self, particle, h_shift, v_shift)
    
    for rarc_data in randomizable_file_group["RARCs"]:
      rarc_name = rarc_data["Name"]
      #print(rarc_name)
      rarc = self.get_arc("files/res/Object/%s.arc" % rarc_name)
      
      for file_entry in rarc.file_entries:
        file_name = file_entry.name
        
        basename, file_ext = os.path.splitext(file_name)
        if file_ext not in [".bdl", ".bti", ".bmd", ".bmt", ".brk"]:
          continue
      
        if file_name in rarc_data["Excluded files"]:
          continue
        
        #print(file_name)
        
        j3d_file = rarc.get_file(file_name)
        
        if hasattr(j3d_file, "tex1"):
          shift_all_colors_in_tex1(self, file_name, j3d_file, h_shift, v_shift)
        
        if file_name.endswith(".bti"):
          shift_all_colors_in_bti(self, file_name, j3d_file, h_shift, v_shift)
        
        if hasattr(j3d_file, "mat3"):
          shift_all_colors_in_mat3(self, file_name, j3d_file, h_shift, v_shift)
        
        if hasattr(j3d_file, "mdl3"):
          shift_all_colors_in_mdl3(self, file_name, j3d_file, h_shift, v_shift)
        
        if hasattr(j3d_file, "trk1"):
          shift_all_colors_in_trk1(self, file_name, j3d_file, h_shift, v_shift)
        
        j3d_file.save_changes()

def shift_all_colors_in_tex1(self, file_name, j3d_file, h_shift, v_shift):
  for texture_name in j3d_file.tex1.textures_by_name:
    if "toon" in texture_name:
      # Special texture related to lighting
      continue
    
    textures = j3d_file.tex1.textures_by_name[texture_name]
    first_texture = textures[0]
    
    if first_texture.image_format in texture_utils.GREYSCALE_IMAGE_FORMATS:
      continue
    
    #if not os.path.isdir("./wip/enemy recolors/%s" % file_name):
    #  os.mkdir("./wip/enemy recolors/%s" % file_name)
    #first_texture.render().save("./wip/enemy recolors/%s/%s orig.png" % (file_name, texture_name))
    
    if first_texture.image_format in texture_utils.IMAGE_FORMATS_THAT_USE_PALETTES:
      if first_texture.palette_format in texture_utils.GREYSCALE_PALETTE_FORMATS:
        continue
      
      # Only modify the palette data without touching the image data.
      colors = first_texture.render_palette()
      colors = texture_utils.hsv_shift_palette(colors, h_shift, v_shift)
      for texture in textures:
        texture.replace_palette(colors)
    else:
      # Does not use palettes. Must modify the image data.
      image = first_texture.render()
      image = texture_utils.hsv_shift_image(image, h_shift, v_shift)
      for texture in textures:
        texture.replace_image(image)
    
    #first_texture.render().save("./wip/enemy recolors/%s/%s %d %d.png" % (file_name, texture_name, h_shift, v_shift))

def shift_all_colors_in_bti(self, texture_name, texture, h_shift, v_shift):
  if texture.image_format in texture_utils.GREYSCALE_IMAGE_FORMATS:
    return
  
  if texture.image_format in texture_utils.IMAGE_FORMATS_THAT_USE_PALETTES:
    if texture.palette_format in texture_utils.GREYSCALE_PALETTE_FORMATS:
      return
    
    # Only modify the palette data without touching the image data.
    colors = texture.render_palette()
    colors = texture_utils.hsv_shift_palette(colors, h_shift, v_shift)
    texture.replace_palette(colors)
  else:
    # Does not use palettes. Must modify the image data.
    image = texture.render()
    image = texture_utils.hsv_shift_image(image, h_shift, v_shift)
    texture.replace_image(image)

def shift_all_colors_in_mat3(self, file_name, j3d_file, h_shift, v_shift):
  for i, color in enumerate(j3d_file.mat3.reg_colors):
    r, g, b, a = color
    if r < 0 or g < 0 or b < 0:
      # Negative color? Skip it to avoid errors.
      continue
    r, g, b = texture_utils.hsv_shift_color((r, g, b), h_shift, v_shift)
    j3d_file.mat3.reg_colors[i] = (r, g, b, a)
  
  for i, color in enumerate(j3d_file.mat3.konst_colors):
    r, g, b, a = color
    r, g, b = texture_utils.hsv_shift_color((r, g, b), h_shift, v_shift)
    j3d_file.mat3.konst_colors[i] = (r, g, b, a)

def shift_all_colors_in_mdl3(self, file_name, j3d_file, h_shift, v_shift):
  for entry in j3d_file.mdl3.entries:
    tev_color_commands = [com for com in entry.bp_commands if com.register >= 0xE0 and com.register <= 0xE7]
    assert len(tev_color_commands) % 2 == 0 # They should come in pairs of low and high
    
    last_hi_command = None
    last_hi_command_orig_value = None
    for i in range(0, len(tev_color_commands), 2):
      lo_command = tev_color_commands[i+0]
      hi_command = tev_color_commands[i+1]
      
      if hi_command.register != lo_command.register+1:
        # The only time they're not properly paired is when the hi command gets duplicated an additional 2 times.
        assert last_hi_command is not None
        assert last_hi_command.register == hi_command.register == lo_command.register
        assert last_hi_command_orig_value == hi_command.value == lo_command.value
        
        # Update the color here too
        hi_command.value = last_hi_command.value
        lo_command.value = last_hi_command.value
        
        continue
      
      last_hi_command = hi_command
      last_hi_command_orig_value = hi_command.value
      
      r = (lo_command.value & 0x0007FF)
      g = (hi_command.value & 0x7FF000) >> 12
      b = (hi_command.value & 0x0007FF)
      a = (lo_command.value & 0x7FF000) >> 12
      
      r, g, b = texture_utils.hsv_shift_color((r, g, b), h_shift, v_shift)
      
      lo_command.value &= ~0x7FF7FF
      hi_command.value &= ~0x7FF7FF
      lo_command.value |= ((r <<  0) & 0x0007FF)
      hi_command.value |= ((g << 12) & 0x7FF000)
      hi_command.value |= ((b <<  0) & 0x0007FF)
      lo_command.value |= ((a << 12) & 0x7FF000)

def shift_all_colors_in_trk1(self, file_name, j3d_file, h_shift, v_shift):
  for anim_index, anim in enumerate(j3d_file.trk1.animations):
    if file_name == "cc.brk" and anim_index == 1:
      # ChuChu eyes material animation, doesn't look right recolored so we just recolor the texture instead
      continue
    
    if not len(anim.r.keyframes) == len(anim.g.keyframes) == len(anim.b.keyframes):
      # Can't properly adjust colors in HSV when RGB don't come together in sets.
      continue
    
    for i in range(len(anim.r.keyframes)):
      r = anim.r.keyframes[i].value & 0xFF
      g = anim.g.keyframes[i].value & 0xFF
      b = anim.b.keyframes[i].value & 0xFF
      r, g, b = texture_utils.hsv_shift_color((r, g, b), h_shift, v_shift)
      anim.r.keyframes[i].value = r
      anim.g.keyframes[i].value = g
      anim.b.keyframes[i].value = b

def shift_all_colors_in_particle(self, particle, h_shift, v_shift):
  #print("%04X" % particle_id)
  #print(particle.tdb1.texture_filenames)
  
  # Changing value/saturation of particle colors can sometimes make them disappear or be bigger/smaller than in vanilla if the changes are too extreme, so limit to hue shifting only for particles.
  v_shift = 0
  
  r, g, b, a = particle.bsp1.color_prm
  r, g, b = texture_utils.hsv_shift_color((r, g, b), h_shift, v_shift)
  particle.bsp1.color_prm = (r, g, b, a)
  
  r, g, b, a = particle.bsp1.color_env
  r, g, b = texture_utils.hsv_shift_color((r, g, b), h_shift, v_shift)
  particle.bsp1.color_env = (r, g, b, a)
  
  #print(particle.bsp1.color_prm_anm_data_count)
  for i in range(particle.bsp1.color_prm_anm_data_count):
    keyframe_time, (r, g, b, a) = particle.bsp1.color_prm_anm_table[i]
    r, g, b = texture_utils.hsv_shift_color((r, g, b), h_shift, v_shift)
    particle.bsp1.color_prm_anm_table[i] = (keyframe_time, (r, g, b, a))
  
  #print(particle.bsp1.color_env_anm_data_count)
  for i in range(particle.bsp1.color_env_anm_data_count):
    keyframe_time, (r, g, b, a) = particle.bsp1.color_env_anm_table[i]
    r, g, b = texture_utils.hsv_shift_color((r, g, b), h_shift, v_shift)
    particle.bsp1.color_env_anm_table[i] = (keyframe_time, (r, g, b, a))
  
  if hasattr(particle, "ssp1"):
    r, g, b, a = particle.ssp1.color_prm
    r, g, b = texture_utils.hsv_shift_color((r, g, b), h_shift, v_shift)
    particle.ssp1.color_prm = (r, g, b, a)
    
    r, g, b, a = particle.ssp1.color_env
    r, g, b = texture_utils.hsv_shift_color((r, g, b), h_shift, v_shift)
    particle.ssp1.color_env = (r, g, b, a)

def shift_hardcoded_color(data, offset, h_shift, v_shift):
  r = read_u8(data, offset + 0)
  g = read_u8(data, offset + 1)
  b = read_u8(data, offset + 2)
  r, g, b = texture_utils.hsv_shift_color((r, g, b), h_shift, v_shift)
  write_u8(data, offset + 0, r)
  write_u8(data, offset + 1, g)
  write_u8(data, offset + 2, b)

def shift_hardcoded_darknut_colors(self, h_shift, v_shift):
  # Update the RGB values for Darknut armor destroyed particles.
  darknut_data = self.get_raw_file("files/rels/d_a_tn.rel")
  offset = 0xE2AC
  for i in range(12):
    shift_hardcoded_color(darknut_data, offset+i*4, h_shift, v_shift)
  
  # Update the Darknut's cape colors
  cape_data = self.get_raw_file("files/rels/d_a_mant.rel")
  for palette_offset in [0x4540, 0x6560, 0x8580, 0xA5A0, 0xC5C0]:
    cape_data.seek(palette_offset)
    palette_data = BytesIO(cape_data.read(0x20))
    colors = texture_utils.decode_palettes(
      palette_data, texture_utils.PaletteFormat.RGB565,
      16, texture_utils.ImageFormat.C4
    )
    
    colors = texture_utils.hsv_shift_palette(colors, h_shift, v_shift)
    
    encoded_colors = texture_utils.generate_new_palettes_from_colors(colors, texture_utils.PaletteFormat.RGB565)
    palette_data = texture_utils.encode_palette(encoded_colors, texture_utils.PaletteFormat.RGB565, texture_utils.ImageFormat.C4)
    assert data_len(palette_data) == 0x20
    cape_data.seek(palette_offset)
    palette_data.seek(0)
    cape_data.write(palette_data.read())

def shift_hardcoded_moblin_colors(self, h_shift, v_shift):
  # Update the thread colors for the Moblin's spear
  for rel_name, offset in [("mo2", 0xD648), ("boko", 0x4488)]:
    data = self.get_raw_file("files/rels/d_a_%s.rel" % rel_name)
    shift_hardcoded_color(data, offset, h_shift, v_shift)

def shift_hardcoded_stalfos_colors(self, h_shift, v_shift):
  # Stalfos hat thread
  data = self.get_raw_file("files/rels/d_a_st.rel")
  offset = 0x9F30
  shift_hardcoded_color(data, offset, h_shift, v_shift)

def shift_hardcoded_rat_colors(self, h_shift, v_shift):
  # Rat tails
  data = self.get_raw_file("files/rels/d_a_nz.rel")
  offset = 0x8FB8
  shift_hardcoded_color(data, offset, h_shift, v_shift)
  
  data = self.get_raw_file("files/rels/d_a_npc_nz.rel")
  offset = 0x48C0
  shift_hardcoded_color(data, offset, h_shift, v_shift)

def shift_hardcoded_puppet_ganon_colors(self, h_shift, v_shift):
  # Puppet ganon's strings
  data = self.get_raw_file("files/rels/d_a_bgn.rel")
  offset = 0xF0A8
  shift_hardcoded_color(data, offset, h_shift, v_shift)
  offset = 0xF0B0
  shift_hardcoded_color(data, offset, h_shift, v_shift)
  
  data = self.get_raw_file("files/rels/d_a_bgn3.rel")
  r = read_u8(data, 0x2CF)
  g = read_u8(data, 0x2D7)
  b = read_u8(data, 0x2DF)
  r, g, b = texture_utils.hsv_shift_color((r, g, b), h_shift, v_shift)
  write_u8(data, 0x2CF, r)
  write_u8(data, 0x2D7, g)
  write_u8(data, 0x2DF, b)

def shift_hardcoded_ganondorf_colors(self, h_shift, v_shift):
  # Ganondorf's fancy threads
  data = self.get_raw_file("files/rels/d_a_gnd.rel")
  offset = 0x8F1C
  shift_hardcoded_color(data, offset, h_shift, v_shift)
