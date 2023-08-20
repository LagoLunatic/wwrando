
import os
import yaml
from io import BytesIO

from gclib import texture_utils
from gclib.bti import BTI
from gclib.j3d import J3D, BPRegister
from gclib import fs_helpers as fs
from gclib.rel import REL

from randomizers.base_randomizer import BaseRandomizer
from wwrando_paths import DATA_PATH

class PaletteRandomizer(BaseRandomizer):
  def __init__(self, rando):
    super().__init__(rando)
    
    with open(os.path.join(DATA_PATH, "palette_randomizable_files.txt"), "r") as f:
      self.palette_randomizable_files: list[dict] = yaml.safe_load(f)
    
    self.file_group_name_to_hv_shift: dict[str, tuple] = {}
  
  def is_enabled(self) -> bool:
    return bool(self.options.get("randomize_enemy_palettes"))
  
  def _randomize(self):
    for randomizable_file_group in self.palette_randomizable_files:
      h_shift = self.rng.randint(20, 340)
      v_shift = self.rng.randint(-40, 40)
      
      group_name = randomizable_file_group["Name"]
      self.file_group_name_to_hv_shift[group_name] = (h_shift, v_shift)
  
  def _save(self):
    for randomizable_file_group in self.palette_randomizable_files:
      group_name = randomizable_file_group["Name"]
      h_shift, v_shift = self.file_group_name_to_hv_shift[group_name]
      
      self.shift_colors_for_file_group(randomizable_file_group, h_shift, v_shift)
  
  def write_to_spoiler_log(self) -> str:
    return super().write_to_spoiler_log()
  
  
  def shift_colors_for_file_group(self, randomizable_file_group: dict, h_shift: int, v_shift: int):
    #print(h_shift, v_shift)
    
    if randomizable_file_group["Name"] == "Darknut":
      self.shift_hardcoded_darknut_colors(h_shift, v_shift)
    elif randomizable_file_group["Name"] == "Moblin":
      self.shift_hardcoded_moblin_colors(h_shift, v_shift)
    elif randomizable_file_group["Name"] == "Stalfos":
      self.shift_hardcoded_stalfos_colors(h_shift, v_shift)
    elif randomizable_file_group["Name"] == "Rat":
      self.shift_hardcoded_rat_colors(h_shift, v_shift)
    elif randomizable_file_group["Name"] == "ChuChu":
      self.shift_hardcoded_chuchu_colors(h_shift, v_shift)
    elif randomizable_file_group["Name"] == "Puppet Ganon":
      self.shift_hardcoded_puppet_ganon_colors(h_shift, v_shift)
    elif randomizable_file_group["Name"] == "Ganondorf":
      self.shift_hardcoded_ganondorf_colors(h_shift, v_shift)
    
    if randomizable_file_group["Particle IDs"]:
      particle_ids = randomizable_file_group["Particle IDs"]
      for i in range(255):
        jpc_path = "files/res/Particle/Pscene%03d.jpc" % i
        if jpc_path.lower() not in self.rando.gcm.files_by_path_lowercase:
          continue
        jpc = self.rando.get_jpc(jpc_path)
        
        particle_ids_for_enemy_in_jpc = [particle_id for particle_id in jpc.particles_by_id if particle_id in particle_ids]
        if not particle_ids_for_enemy_in_jpc:
          continue
        
        for particle_id in particle_ids_for_enemy_in_jpc:
          particle = jpc.particles_by_id[particle_id]
          self.shift_all_colors_in_particle(particle, h_shift, v_shift)
    
    for rarc_data in randomizable_file_group["RARCs"]:
      rarc_name = rarc_data["Name"]
      #print(rarc_name)
      rarc = self.rando.get_arc("files/res/Object/%s.arc" % rarc_name)
      
      for file_entry in rarc.file_entries:
        file_name = file_entry.name
        
        basename, file_ext = os.path.splitext(file_name)
        if file_ext not in [".bdl", ".bti", ".bmd", ".bmt", ".brk"]:
          continue
      
        if file_name in rarc_data["Excluded files"]:
          continue
        
        #print(file_name)
        
        if file_ext == ".bti":
          bti_file = rarc.get_file(file_name, BTI)
          self.shift_all_colors_in_bti(file_name, bti_file, h_shift, v_shift)
          bti_file.save_changes()
        else:
          j3d_file = rarc.get_file(file_name, J3D)
          
          if hasattr(j3d_file, "tex1"):
            self.shift_all_colors_in_tex1(file_name, j3d_file, h_shift, v_shift)
          
          if hasattr(j3d_file, "mat3"):
            self.shift_all_colors_in_mat3(file_name, j3d_file, h_shift, v_shift)
          
          if hasattr(j3d_file, "mdl3"):
            self.shift_all_colors_in_mdl3(file_name, j3d_file, h_shift, v_shift)
          
          if hasattr(j3d_file, "trk1"):
            self.shift_all_colors_in_trk1(file_name, j3d_file, h_shift, v_shift)
          
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
      tev_color_commands = [
        com for com in entry.bp_commands
        if com.register >= BPRegister.TEV_REGISTERL_0.value and com.register <= BPRegister.TEV_REGISTERH_3.value
      ]
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
    animations = []
    for mat_name, anims in j3d_file.trk1.mat_name_to_reg_anims.items():
      animations += anims
    for mat_name, anims in j3d_file.trk1.mat_name_to_konst_anims.items():
      animations += anims
    
    for anim_index, anim in enumerate(animations):
      if file_name == "cc.brk" and anim_index == 1:
        # ChuChu eyes material animation, doesn't look right recolored so we just recolor the texture instead
        continue
      
      assert len(anim.r.keyframes) > 0 and len(anim.g.keyframes) > 0 and len(anim.b.keyframes) > 0
      
      # In some cases (specifically Gohma), there won't be an equal number of keyframes for R G and B, so we can't simply iterate over the list.
      
      # First make a list of what times are present on the timeline for this animation.
      unique_keyframe_times = []
      for keyframe in (anim.r.keyframes + anim.g.keyframes + anim.b.keyframes):
        if keyframe.time not in unique_keyframe_times:
          unique_keyframe_times.append(keyframe.time)
      unique_keyframe_times.sort()
      
      def get_keyframe_by_closest_time(keyframes, keyframe_time):
        return min(keyframes, key=lambda kf: abs(kf.time-keyframe_time))
      
      def get_keyframe_by_exact_time(keyframes, keyframe_time):
        return next((kf for kf in keyframes if kf.time == keyframe_time), None)
      
      # Then make a list of what the modified colors at each time will be, but don't actually modify them yet since we may need to re-read the values of previous times if the next time is missing a channel.
      modified_colors_by_time = {}
      for keyframe_time in unique_keyframe_times:
        #print("  %d" % keyframe_time)
        r = get_keyframe_by_closest_time(anim.r.keyframes, keyframe_time).value & 0xFF
        g = get_keyframe_by_closest_time(anim.g.keyframes, keyframe_time).value & 0xFF
        b = get_keyframe_by_closest_time(anim.b.keyframes, keyframe_time).value & 0xFF
        #print("    %d %d %d" % (r, g, b))
        r, g, b = texture_utils.hsv_shift_color((r, g, b), h_shift, v_shift)
        modified_colors_by_time[keyframe_time] = (r, g, b)
      
      # Then actually modify the colors.
      for keyframe_time in unique_keyframe_times:
        r, g, b = modified_colors_by_time[keyframe_time]
        r_keyframe = get_keyframe_by_exact_time(anim.r.keyframes, keyframe_time)
        if r_keyframe:
          r_keyframe.value = r
        g_keyframe = get_keyframe_by_exact_time(anim.g.keyframes, keyframe_time)
        if g_keyframe:
          g_keyframe.value = g
        b_keyframe = get_keyframe_by_exact_time(anim.b.keyframes, keyframe_time)
        if b_keyframe:
          b_keyframe.value = b

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
    for keyframe in particle.bsp1.color_prm_anm_table:
      r, g, b, a = keyframe.color
      r, g, b = texture_utils.hsv_shift_color((r, g, b), h_shift, v_shift)
      keyframe.color = (r, g, b, a)
    
    #print(particle.bsp1.color_env_anm_data_count)
    for keyframe in particle.bsp1.color_env_anm_table:
      r, g, b, a = keyframe.color
      r, g, b = texture_utils.hsv_shift_color((r, g, b), h_shift, v_shift)
      keyframe.color = (r, g, b, a)
    
    if hasattr(particle, "ssp1"):
      r, g, b, a = particle.ssp1.color_prm
      r, g, b = texture_utils.hsv_shift_color((r, g, b), h_shift, v_shift)
      particle.ssp1.color_prm = (r, g, b, a)
      
      r, g, b, a = particle.ssp1.color_env
      r, g, b = texture_utils.hsv_shift_color((r, g, b), h_shift, v_shift)
      particle.ssp1.color_env = (r, g, b, a)

  def shift_hardcoded_color_in_rel(self, rel: REL, offset, h_shift, v_shift):
    r = rel.read_data(fs.read_u8, offset + 0)
    g = rel.read_data(fs.read_u8, offset + 1)
    b = rel.read_data(fs.read_u8, offset + 2)
    r, g, b = texture_utils.hsv_shift_color((r, g, b), h_shift, v_shift)
    rel.write_data(fs.write_u8, offset + 0, r)
    rel.write_data(fs.write_u8, offset + 1, g)
    rel.write_data(fs.write_u8, offset + 2, b)

  def shift_hardcoded_darknut_colors(self, h_shift, v_shift):
    # Update the RGB values for Darknut armor destroyed particles.
    rel = self.rando.get_rel("files/rels/d_a_tn.rel")
    offset = 0xE2AC
    for i in range(12):
      self.shift_hardcoded_color_in_rel(rel, offset+i*4, h_shift, v_shift)
    
    # Update the Darknut's cape colors
    rel = self.rando.get_rel("files/rels/d_a_mant.rel")
    for palette_offset in [0x4540, 0x6560, 0x8580, 0xA5A0, 0xC5C0]:
      palette_data = BytesIO(rel.read_data(fs.read_bytes, palette_offset, 0x20))
      colors = texture_utils.decode_palettes(
        palette_data, texture_utils.PaletteFormat.RGB5A3,
        16, texture_utils.ImageFormat.C4
      )
      
      colors = texture_utils.hsv_shift_palette(colors, h_shift, v_shift)
      
      encoded_colors = texture_utils.generate_new_palettes_from_colors(colors, texture_utils.PaletteFormat.RGB5A3)
      palette_data = texture_utils.encode_palette(encoded_colors, texture_utils.PaletteFormat.RGB5A3, texture_utils.ImageFormat.C4)
      assert fs.data_len(palette_data) == 0x20
      rel.write_data(fs.write_bytes, palette_offset, fs.read_all_bytes(palette_data))

  def shift_hardcoded_moblin_colors(self, h_shift, v_shift):
    # Update the thread colors for the Moblin's spear
    for rel_name, offset in [("mo2", 0xD648), ("boko", 0x4488)]:
      rel = self.rando.get_rel("files/rels/d_a_%s.rel" % rel_name)
      self.shift_hardcoded_color_in_rel(rel, offset, h_shift, v_shift)

  def shift_hardcoded_stalfos_colors(self, h_shift, v_shift):
    # Stalfos hat thread
    rel = self.rando.get_rel("files/rels/d_a_st.rel")
    offset = 0x9F30
    self.shift_hardcoded_color_in_rel(rel, offset, h_shift, v_shift)

  def shift_hardcoded_rat_colors(self, h_shift, v_shift):
    # Rat tails
    rel = self.rando.get_rel("files/rels/d_a_nz.rel")
    offset = 0x8FB8
    self.shift_hardcoded_color_in_rel(rel, offset, h_shift, v_shift)
    
    rel = self.rando.get_rel("files/rels/d_a_npc_nz.rel")
    offset = 0x48C0
    self.shift_hardcoded_color_in_rel(rel, offset, h_shift, v_shift)

  def shift_hardcoded_chuchu_colors(self, h_shift, v_shift):
    # ChuChu particles
    rel = self.rando.get_rel("files/rels/d_a_cc.rel")
    offset = 0x7F88
    for i in range(5):
      self.shift_hardcoded_color_in_rel(rel, offset+i*4, h_shift, v_shift)
    
    # The particles that come off of Dark ChuChus when attacked where they temporarily break apart and reform are tricky.
    # That RGB value is stored as three multiplier floats instead of three bytes, and the red multiplier in the float constant bank is coincidentally reused by other things in the ChuChu code unrelated to color so we can't change that.
    # So we change the asm code to read the red multiplier from elsewhere, and then modify that instead.
    r = int(rel.read_data(fs.read_float, 0x7E9C))
    g = int(rel.read_data(fs.read_float, 0x7EBC))
    b = int(rel.read_data(fs.read_float, 0x7EC0))
    assert r != 0 # Make sure the asm patch was applied
    r, g, b = texture_utils.hsv_shift_color((r, g, b), h_shift, v_shift)
    rel.write_data(fs.write_float, 0x7E9C, r)
    rel.write_data(fs.write_float, 0x7EBC, g)
    rel.write_data(fs.write_float, 0x7EC0, b)

  def shift_hardcoded_puppet_ganon_colors(self, h_shift, v_shift):
    # Puppet ganon's strings
    rel = self.rando.get_rel("files/rels/d_a_bgn.rel")
    offset = 0xF0A8
    self.shift_hardcoded_color_in_rel(rel, offset, h_shift, v_shift)
    offset = 0xF0B0
    self.shift_hardcoded_color_in_rel(rel, offset, h_shift, v_shift)
    
    rel = self.rando.get_rel("files/rels/d_a_bgn3.rel")
    r = rel.read_data(fs.read_u8, 0x2CF)
    g = rel.read_data(fs.read_u8, 0x2D7)
    b = rel.read_data(fs.read_u8, 0x2DF)
    r, g, b = texture_utils.hsv_shift_color((r, g, b), h_shift, v_shift)
    rel.write_data(fs.write_u8, 0x2CF, r)
    rel.write_data(fs.write_u8, 0x2D7, g)
    rel.write_data(fs.write_u8, 0x2DF, b)

  def shift_hardcoded_ganondorf_colors(self, h_shift, v_shift):
    # Ganondorf's fancy threads
    rel = self.rando.get_rel("files/rels/d_a_gnd.rel")
    offset = 0x8F1C
    self.shift_hardcoded_color_in_rel(rel, offset, h_shift, v_shift)
