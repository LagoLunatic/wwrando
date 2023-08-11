
import os
import re
import yaml
from collections import OrderedDict
from io import BytesIO
import glob
from PIL import Image

from gclib import fs_helpers as fs
from gclib import texture_utils
from gclib.bti import BTI
from gclib.j3d import BDL
from gclib.texture_utils import ImageFormat, PaletteFormat
from gclib.gx_enums import GXAttr
from wwrando_paths import ASSETS_PATH, CUSTOM_MODELS_PATH

ORIG_LINK_ARC_FILE_SIZE_IN_BYTES  = 1308608
ORIG_LKANM_ARC_FILE_SIZE_IN_BYTES = 1842464
ORIG_LKD00_ARC_FILE_SIZE_IN_BYTES = 1228256
ORIG_LKD01_ARC_FILE_SIZE_IN_BYTES = 1149280
ORIG_SHIP_ARC_FILE_SIZE_IN_BYTES  =  191520
# Allow the above arcs combined to increase in filesize by at most 0.202 mebibytes.
# In other words, the same amount of increase as when the 1.24MiB original Link.arc is increased to 1.44MiB.
MAX_ALLOWED_TOTAL_ARC_FILE_SIZE_SUM_INCREASE_IN_BYTES = 1525678 - ORIG_LINK_ARC_FILE_SIZE_IN_BYTES

HARDCODED_COLORS_WITH_ALPHA_KEY_NAMES = [
  "sword_slash_trail_color",
  "elixir_soup_sword_trail_color",
  "parrying_sword_trail_color",
  "boomerang_trail_color",
  "arrow_trail_color",
]

class InvalidColorError(Exception):
  pass

cached_model_metadata = {}

def get_model_metadata(custom_model_name):
  if custom_model_name == "Random":
    return {}
  elif custom_model_name in cached_model_metadata:
    return cached_model_metadata[custom_model_name]
  else:
    if custom_model_name == "Link":
      metadata_path = os.path.join(ASSETS_PATH, "link_metadata.txt")
      color_masks_path = os.path.join(ASSETS_PATH, "link_color_masks")
      previews_path = os.path.join(ASSETS_PATH, "link_preview")
    else:
      metadata_path = os.path.join(CUSTOM_MODELS_PATH, custom_model_name, "metadata.txt")
      color_masks_path = os.path.join(CUSTOM_MODELS_PATH, custom_model_name, "color_masks")
      previews_path = os.path.join(CUSTOM_MODELS_PATH, custom_model_name, "preview")
    
    if not os.path.isfile(metadata_path):
      return {}
    
    use_old_color_format = False
    try:
      with open(metadata_path) as f:
        metadata_str = f.read()
      
      # Automatically convert any tabs in the metadata to two spaces since pyyaml doesn't like tabs.
      metadata_str = metadata_str.replace("\t", "  ")
      
      old_format_match = re.search(r"^ +\S[^:]*: +[0-9A-F]{6}$", metadata_str, re.IGNORECASE | re.MULTILINE)
      new_format_match = re.search(r"^ +\S[^:]*: +0x[0-9A-F]{6}$", metadata_str, re.IGNORECASE | re.MULTILINE)
      if old_format_match and not new_format_match:
        use_old_color_format = True
      
      metadata = yaml.load(metadata_str, YamlOrderedDictLoader)
    except Exception as e:
      error_message = str(e)
      return {
        "error_message": error_message,
      }
    
    metadata["preview_hero"] = os.path.join(previews_path, "preview_hero.png")
    metadata["preview_casual"] = os.path.join(previews_path, "preview_casual.png")
    
    metadata["hero_color_mask_paths"] = OrderedDict()
    metadata["casual_color_mask_paths"] = OrderedDict()
    metadata["hands_hero_color_mask_paths"] = OrderedDict()
    metadata["hands_casual_color_mask_paths"] = OrderedDict()
    metadata["hitomi_hero_color_mask_paths"] = OrderedDict()
    metadata["hitomi_casual_color_mask_paths"] = OrderedDict()
    metadata["preview_hero_color_mask_paths"] = OrderedDict()
    metadata["preview_casual_color_mask_paths"] = OrderedDict()
    metadata["mouth_color_mask_paths"] = []
    metadata["mouth_color_mask_paths"].append(None) # Dummy entry for mouth number 0, which doesn't exist
    for i in range(1, 9+1):
      metadata["mouth_color_mask_paths"].append(OrderedDict())
    
    for key, value in metadata.items():
      if key in ["hero_custom_colors", "casual_custom_colors"]:
        prefix = key.split("_")[0]
        
        for custom_color_name, hex_color in value.items():
          try:
            value[custom_color_name] = parse_hex_color(hex_color, use_old_color_format)
          except InvalidColorError:
            error_message = "Custom color \"%s\" has an invalid base color specified in metadata.txt: \"%s\"" % (custom_color_name, repr(hex_color))
            return {
              "error_message": error_message,
            }
          
          mask_path = os.path.join(color_masks_path, "%s_%s.png" % (prefix, custom_color_name))
          metadata["%s_color_mask_paths" % prefix][custom_color_name] = mask_path
          hands_mask_path = os.path.join(color_masks_path, "hands_%s_%s.png" % (prefix, custom_color_name))
          metadata["hands_%s_color_mask_paths" % prefix][custom_color_name] = hands_mask_path
          hitomi_mask_path = os.path.join(color_masks_path, "hitomi_%s_%s.png" % (prefix, custom_color_name))
          metadata["hitomi_%s_color_mask_paths" % prefix][custom_color_name] = hitomi_mask_path
          preview_mask_path = os.path.join(previews_path, "preview_%s_%s.png" % (prefix, custom_color_name))
          metadata["preview_%s_color_mask_paths" % prefix][custom_color_name] = preview_mask_path
          
          for i in range(1, 9+1):
            mouth_mask_path = os.path.join(color_masks_path, "mouths", "mouthS3TC.%d_%s.png" % (i, custom_color_name))
            metadata["mouth_color_mask_paths"][i][custom_color_name] = mouth_mask_path
      
      if key in ["hero_color_presets", "casual_color_presets"]:
        prefix = key.split("_")[0]
        
        for preset_name, preset in value.items():
          for custom_color_name, hex_color in preset.items():
            try:
              preset[custom_color_name] = parse_hex_color(hex_color, use_old_color_format)
            except InvalidColorError:
              error_message = "Color preset \"%s\"'s color \"%s\" has an invalid base color specified in metadata.txt: \"%s\"" % (preset_name, custom_color_name, repr(hex_color))
              return {
                "error_message": error_message,
              }
    
    for key in HARDCODED_COLORS_WITH_ALPHA_KEY_NAMES:
      if key in metadata:
        hex_color = metadata[key]
        metadata[key] = parse_hex_color_with_alpha(hex_color)
    
    cached_model_metadata[custom_model_name] = metadata
    
    return metadata

def parse_hex_color(hex_color, use_old_color_format):
  if use_old_color_format:
    return parse_hex_color_old_format(hex_color)
  
  if isinstance(hex_color, int) and (0x000000 <= hex_color <= 0xFFFFFF):
    r = (hex_color & 0xFF0000) >> 16
    g = (hex_color & 0x00FF00) >> 8
    b = (hex_color & 0x0000FF) >> 0
    return [r, g, b]
  else:
    raise InvalidColorError()

def parse_hex_color_old_format(hex_color):
  if isinstance(hex_color, int):
    hex_color_string = "%06d" % hex_color
  elif isinstance(hex_color, str):
    hex_color_string = hex_color
  else:
    raise InvalidColorError()

  match = re.search(r"^([0-9A-F]{2})([0-9A-F]{2})([0-9A-F]{2})$", hex_color_string, re.IGNORECASE)
  if match:
    r, g, b = int(match.group(1), 16), int(match.group(2), 16), int(match.group(3), 16)
    return [r, g, b]
  else:
    raise InvalidColorError()

def parse_hex_color_with_alpha(hex_color):
  if isinstance(hex_color, int) and (0x00000000 <= hex_color <= 0xFFFFFFFF):
    r = (hex_color & 0xFF000000) >> 24
    g = (hex_color & 0x00FF0000) >> 16
    b = (hex_color & 0x0000FF00) >> 8
    a = (hex_color & 0x000000FF) >> 0
    return [r, g, b, a]
  else:
    raise InvalidColorError()

def get_all_custom_model_names():
  custom_model_names = []
  custom_model_paths = glob.glob(glob.escape(CUSTOM_MODELS_PATH) + "/*/Link.arc")
  for link_arc_path in custom_model_paths:
    folder_name = os.path.basename(os.path.dirname(link_arc_path))
    if folder_name in ["Link", "Random"]:
      continue
    custom_model_names.append(folder_name)
  return custom_model_names

def decide_on_link_model(self):
  custom_model_name = self.options.get("custom_player_model", "Link")
  if custom_model_name == "Link":
    return
  
  if custom_model_name == "Random" or custom_model_name == "Random (exclude Link)":
    custom_model_names = get_all_custom_model_names()
    if not custom_model_names:
      raise Exception("No custom models to randomly choose from in the /models folder.")
    
    if custom_model_name == "Random":
      custom_model_names.append(None) # Dummy entry to represent not changing Link's model
    
    temp_rng = self.get_new_rng()
    custom_model_name = temp_rng.choice(custom_model_names)
    
    if custom_model_name == None:
      return
  
  # Remember what custom model was chosen so code in various places can access the metadata for the proper model.
  self.custom_model_name = custom_model_name

def replace_link_model(self):
  if self.custom_model_name == "Link":
    return
  
  custom_model_path = os.path.join(CUSTOM_MODELS_PATH, self.custom_model_name)
  
  custom_link_arc_path = os.path.join(custom_model_path, "Link.arc")
  if not os.path.isfile(custom_link_arc_path):
    raise Exception("Custom model is missing Link.arc: %s" % custom_model_path)
  
  orig_sum_of_changed_arc_sizes = 0
  new_sum_of_changed_arc_sizes = 0
  checked_arc_names = []
  
  with open(custom_link_arc_path, "rb") as f:
    custom_link_arc_data = BytesIO(f.read())
  orig_link_arc = self.get_arc("files/res/Object/Link.arc")
  self.replace_arc("files/res/Object/Link.arc", custom_link_arc_data)
  custom_link_arc = self.get_arc("files/res/Object/Link.arc")
  
  revert_bck_files_in_arc_to_original(orig_link_arc, custom_link_arc)
  
  if self.options.get("disable_custom_player_items"):
    revert_item_models_in_arc_to_original(orig_link_arc, custom_link_arc)
  
  orig_sum_of_changed_arc_sizes += ORIG_LINK_ARC_FILE_SIZE_IN_BYTES
  custom_link_arc.save_changes()
  new_sum_of_changed_arc_sizes += fs.data_len(custom_link_arc.data)
  checked_arc_names.append("Link.arc")
  check_changed_archives_over_filesize_limit(orig_sum_of_changed_arc_sizes, new_sum_of_changed_arc_sizes, checked_arc_names)
  
  
  def replace_animation_arc(anim_arc_name, orig_anim_arc_file_size, revert_totals_after=False):
    nonlocal orig_sum_of_changed_arc_sizes
    nonlocal new_sum_of_changed_arc_sizes
    
    anim_arc_path = os.path.join(custom_model_path, anim_arc_name)
    if os.path.isfile(anim_arc_path):
      with open(anim_arc_path, "rb") as f:
        custom_anim_arc_data = BytesIO(f.read())
      orig_anim_arc = self.get_arc("files/res/Object/" + anim_arc_name)
      self.replace_arc("files/res/Object/" + anim_arc_name, custom_anim_arc_data)
      custom_anim_arc = self.get_arc("files/res/Object/" + anim_arc_name)
      
      revert_bck_files_in_arc_to_original(orig_anim_arc, custom_anim_arc)
      
      orig_sum_of_changed_arc_sizes += orig_anim_arc_file_size
      custom_anim_arc.save_changes()
      new_sum_of_changed_arc_sizes += fs.data_len(custom_anim_arc.data)
      checked_arc_names.append(anim_arc_name)
      check_changed_archives_over_filesize_limit(orig_sum_of_changed_arc_sizes, new_sum_of_changed_arc_sizes, checked_arc_names)
      
      if revert_totals_after:
        # For LkD00, it's not actually always loaded, since only one of the two Link cutscene animation arcs are ever loaded at a given time.
        # So we stop including LkD00's size in the total as soon as we've checked its size.
        # We uncount LkD00 specifically because in the randomizer, LkD01 is always loaded. LkD00 is only relevant for the first half of the vanilla game.
        orig_sum_of_changed_arc_sizes -= orig_anim_arc_file_size
        new_sum_of_changed_arc_sizes -= fs.data_len(custom_anim_arc.data)
        checked_arc_names.remove(anim_arc_name)
  
  # Replace Link's gameplay animations.
  replace_animation_arc("LkAnm.arc", ORIG_LKANM_ARC_FILE_SIZE_IN_BYTES)
  
  # Replace Link's cutscene animations.
  replace_animation_arc("LkD00.arc", ORIG_LKD00_ARC_FILE_SIZE_IN_BYTES, revert_totals_after=True)
  replace_animation_arc("LkD01.arc", ORIG_LKD01_ARC_FILE_SIZE_IN_BYTES)
  
  # Replace KoRL.
  ship_path = os.path.join(custom_model_path, "Ship.arc")
  if os.path.isfile(ship_path):
    with open(ship_path, "rb") as f:
      custom_ship_arc_data = BytesIO(f.read())
    orig_ship_arc = self.get_arc("files/res/Object/Ship.arc")
    self.replace_arc("files/res/Object/Ship.arc", custom_ship_arc_data)
    custom_ship_arc = self.get_arc("files/res/Object/Ship.arc")
    
    revert_bck_files_in_arc_to_original(orig_ship_arc, custom_ship_arc)
    
    orig_sum_of_changed_arc_sizes += ORIG_SHIP_ARC_FILE_SIZE_IN_BYTES
    custom_ship_arc.save_changes()
    new_sum_of_changed_arc_sizes += fs.data_len(custom_ship_arc.data)
    checked_arc_names.append("Ship.arc")
    check_changed_archives_over_filesize_limit(orig_sum_of_changed_arc_sizes, new_sum_of_changed_arc_sizes, checked_arc_names)
    
    orig_sail_tex = orig_ship_arc.get_file("new_ho1.bti", BTI)
    custom_sail_tex = custom_ship_arc.get_file("new_ho1.bti", BTI)
    if fs.read_all_bytes(custom_sail_tex.data) != fs.read_all_bytes(orig_sail_tex.data) or orig_sail_tex.image_format != custom_sail_tex.image_format:
      # Don't allow the swift sail tweak to replace this custom texture with the swift sail texture.
      self.using_custom_sail_texture = True
  
  # The texture shown on the wall when reflecting light with the mirror shield is separate from Link.arc.
  mirror_shield_reflection_image_path = os.path.join(custom_model_path, "shmref.bti")
  if os.path.isfile(mirror_shield_reflection_image_path):
    with open(mirror_shield_reflection_image_path, "rb") as f:
      reflection_image_data = BytesIO(f.read())
    always_arc = self.get_arc("files/res/Object/Always.arc")
    always_arc.get_file_entry("shmref.bti").data = reflection_image_data
  
  if not self.options.get("disable_custom_player_voice"):
    # Replace voice sound effects.
    jaiinit_aaf_path = os.path.join(custom_model_path, "sound/JaiInit.aaf")
    voice_aw_path = os.path.join(custom_model_path, "sound/voice_0.aw")
    ganont_aw_path = os.path.join(custom_model_path, "sound/GanonT_0.aw")
    if os.path.isfile(jaiinit_aaf_path) and os.path.isfile(voice_aw_path):
      with open(jaiinit_aaf_path, "rb") as f:
        jaiinit_aaf_data = BytesIO(f.read())
      self.replace_raw_file("files/Audiores/JaiInit.aaf", jaiinit_aaf_data)
      with open(voice_aw_path, "rb") as f:
        voice_aw_data = BytesIO(f.read())
      self.replace_raw_file("files/Audiores/Banks/voice_0.aw", voice_aw_data)
      if os.path.isfile(ganont_aw_path):
        with open(ganont_aw_path, "rb") as f:
          ganont_aw_data = BytesIO(f.read())
        self.replace_raw_file("files/Audiores/Banks/GanonT_0.aw", ganont_aw_data)

def revert_bck_files_in_arc_to_original(orig_arc, custom_arc):
  # Revert all BCK animations in a custom arc to the original ones.
  # This is because BCK animations can change gameplay, which we don't want to allow cosmetic mods to do.
  for orig_file_entry in orig_arc.file_entries:
    basename, file_ext = os.path.splitext(orig_file_entry.name)
    if file_ext == ".bck":
      custom_file_entry = custom_arc.get_file_entry(orig_file_entry.name)
      custom_file_entry.data = orig_file_entry.data

def revert_item_models_in_arc_to_original(orig_arc, custom_arc):
  # Optionally revert all item models to the original ones.
  # Hero's Charm, Power Bracelets, Iron Boots, and Magic Armor shell are excluded, since the vanilla ones wouldn't fit well on custom models.
  # Also revert blur.bti (sword/boomerang afterimage texture) and rock_mark.bti (hookshot ready reticule).
  # Also revert the BRK/BTK animations for reverted items. (All BCK animations are already reverted separately.)
  for orig_file_entry in orig_arc.file_entries:
    basename, file_ext = os.path.splitext(orig_file_entry.name)
    revert = False
    if file_ext == ".bdl" and basename not in ["cl", "katsura", "hands", "yamu", "pring", "hboots", "ymgcs00"]:
      revert = True
    if file_ext == ".bti" and basename not in ["linktexbci4"]:
      revert = True
    if file_ext == ".brk" and basename not in ["ymgcs00_ms", "ymgcs00_ts"]:
      revert = True
    if file_ext == ".btk" and basename not in ["ymgcs00"]:
      revert = True
    if revert:
      custom_file_entry = custom_arc.get_file_entry(orig_file_entry.name)
      custom_file_entry.data = orig_file_entry.data

def check_changed_archives_over_filesize_limit(orig_sum_of_changed_arc_sizes, new_sum_of_changed_arc_sizes, checked_arc_names):
  # Validate the filesize didn't increase enough to cause memory issues.
  max_sum_of_changed_arc_sizes = orig_sum_of_changed_arc_sizes + MAX_ALLOWED_TOTAL_ARC_FILE_SIZE_SUM_INCREASE_IN_BYTES
  if new_sum_of_changed_arc_sizes > max_sum_of_changed_arc_sizes:
    error_message = "The chosen custom player model's filesize is too large and may cause crashes or other issues in game.\n\n"
    error_message += "Archives: %s\n" % (", ".join(checked_arc_names))
    error_message += "Max combined size of the above archives: %.2fMiB\n" % (max_sum_of_changed_arc_sizes / (1024*1024))
    error_message += "Combined size of selected model's archives: %.2fMiB\n" % (new_sum_of_changed_arc_sizes / (1024*1024))
    raise Exception(error_message)

def change_player_custom_colors(self):
  custom_model_metadata = get_model_metadata(self.custom_model_name)
  disable_casual_clothes = custom_model_metadata.get("disable_casual_clothes", False)
  
  sword_slash_trail_color = custom_model_metadata.get("sword_slash_trail_color")
  elixir_soup_sword_trail_color = custom_model_metadata.get("elixir_soup_sword_trail_color")
  parrying_sword_trail_color = custom_model_metadata.get("parrying_sword_trail_color")
  boomerang_trail_color = custom_model_metadata.get("boomerang_trail_color")
  arrow_trail_color = custom_model_metadata.get("arrow_trail_color")
  if sword_slash_trail_color:
    self.dol.write_data(fs.write_and_pack_bytes, 0x803F62AC, sword_slash_trail_color, "BBBB")
  if elixir_soup_sword_trail_color:
    self.dol.write_data(fs.write_and_pack_bytes, 0x803F62B0, elixir_soup_sword_trail_color, "BBBB")
  if parrying_sword_trail_color:
    self.dol.write_data(fs.write_and_pack_bytes, 0x803F62B4, parrying_sword_trail_color, "BBBB")
  if boomerang_trail_color:
    self.dol.write_data(fs.write_and_pack_bytes, 0x803F6268, boomerang_trail_color, "BBBB")
  if arrow_trail_color:
    common_jpc = self.get_jpc("files/res/Particle/common.jpc")
    particle = common_jpc.particles_by_id[0x48]
    particle.bsp1.color_prm = tuple(arrow_trail_color)
  
  link_arc = self.get_arc("files/res/Object/Link.arc")
  link_main_model = link_arc.get_file("cl.bdl", BDL)
  
  if self.options.get("player_in_casual_clothes") and not disable_casual_clothes:
    is_casual = True
    prefix = "casual"
    link_main_textures = [link_arc.get_file("linktexbci4.bti", BTI)]
  else:
    is_casual = False
    prefix = "hero"
    link_main_textures = link_main_model.tex1.textures_by_name["linktexS3TC"]
  
  first_texture = link_main_textures[0]
  link_main_image = first_texture.render()
  
  hitomi_textures = link_main_model.tex1.textures_by_name["hitomi"]
  hitomi_image = hitomi_textures[0].render()
  
  hands_model = link_arc.get_file("hands.bdl", BDL)
  hands_textures = hands_model.tex1.textures_by_name["handsS3TC"]
  hands_image = hands_textures[0].render()
  
  all_mouth_textures = OrderedDict()
  all_mouth_images = OrderedDict()
  
  replaced_any = False
  replaced_any_hands = False
  custom_colors = custom_model_metadata.get(prefix + "_custom_colors", {})
  has_colored_eyebrows = custom_model_metadata.get("has_colored_eyebrows", False)
  hands_color_name = custom_model_metadata.get(prefix + "_hands_color_name", "Skin")
  mouth_color_name = custom_model_metadata.get(prefix + "_mouth_color_name", "Skin")
  hitomi_color_name = custom_model_metadata.get(prefix + "_hitomi_color_name", "Eyes")
  eyebrow_color_name = custom_model_metadata.get(prefix + "_eyebrow_color_name", "Hair")
  casual_hair_color_name = custom_model_metadata.get("casual_hair_color_name", "Hair")
  
  # The "_color_name" fields will be completely ignored if that type of texture has even a single mask present.
  for custom_color_basename in custom_colors:
    for i in range(1, 9+1):
      mouth_mask_path = custom_model_metadata["mouth_color_mask_paths"][i][custom_color_basename]
      if os.path.isfile(mouth_mask_path):
        mouth_color_name = None
    
    hands_mask_path = custom_model_metadata["hands_" + prefix + "_color_mask_paths"][custom_color_basename]
    if os.path.isfile(hands_mask_path):
      hands_color_name = None
    
    hitomi_mask_path = custom_model_metadata["hitomi_" + prefix + "_color_mask_paths"][custom_color_basename]
    if os.path.isfile(hitomi_mask_path):
      hitomi_color_name = None
  
  for custom_color_basename, base_color in custom_colors.items():
    custom_color = self.options.get("custom_colors", {}).get(custom_color_basename, None)
    if custom_color is None:
      continue
    custom_color = tuple(custom_color)
    base_color = tuple(base_color)
    if custom_color == base_color:
      continue
    
    # Recolor the pupils.
    replaced_any_pupils_for_this_color = False
    
    hitomi_mask_path = custom_model_metadata["hitomi_" + prefix + "_color_mask_paths"][custom_color_basename]
    if os.path.isfile(hitomi_mask_path) or custom_color_basename == hitomi_color_name:
      replaced_any_pupils_for_this_color = True
      
      if os.path.isfile(hitomi_mask_path):
        check_valid_mask_path(hitomi_mask_path)
        hitomi_image = texture_utils.color_exchange(hitomi_image, base_color, custom_color, mask_path=hitomi_mask_path)
      elif custom_color_basename == hitomi_color_name:
        hitomi_image = texture_utils.color_exchange(hitomi_image, base_color, custom_color, ignore_bright=True)
      
      for hitomi_texture in hitomi_textures:
        hitomi_texture.replace_image(hitomi_image)
    
    # Recolor the main player body texture.
    mask_path = custom_model_metadata[prefix + "_color_mask_paths"][custom_color_basename]
    
    if not os.path.isfile(mask_path) and replaced_any_pupils_for_this_color:
      # Normally we throw an error for any color that doesn't have a mask for the main body texture, but if it's an eye color, we ignore it.
      pass
    else:
      check_valid_mask_path(mask_path)
      link_main_image = texture_utils.color_exchange(link_main_image, base_color, custom_color, mask_path=mask_path)
    replaced_any = True
    
    # Recolor the eyebrows.
    if has_colored_eyebrows and custom_color_basename == eyebrow_color_name:
      for i in range(1, 6+1):
        eyebrow_textures = link_main_model.tex1.textures_by_name["mayuh.%d" % i]
        eyebrow_image = eyebrow_textures[0].render()
        eyebrow_image = texture_utils.color_exchange(eyebrow_image, base_color, custom_color)
        for eyebrow_texture in eyebrow_textures:
          if eyebrow_texture.is_greyscale():
            raise Exception("Eyebrows use a greyscale image format, but metadata.txt specified the model should have colored eyebrows.")
          eyebrow_texture.replace_image(eyebrow_image)
    
    # Recolor the back hair for casual Link.
    if is_casual and custom_color_basename == casual_hair_color_name:
      link_hair_model = link_arc.get_file("katsura.bdl", BDL)
      link_hair_textures = link_hair_model.tex1.textures_by_name["katsuraS3TC"]
      first_texture = link_hair_textures[0]
      back_hair_image = first_texture.render()
      
      back_hair_image.paste(custom_color, [0, 0, 8, 8])
      
      for link_hair_texture in link_hair_textures:
        link_hair_texture.replace_image(back_hair_image)
      link_hair_model.save_changes()
    
    # Recolor the mouth.
    for i in range(1, 9+1):
      mouth_mask_path = custom_model_metadata["mouth_color_mask_paths"][i][custom_color_basename]
      if os.path.isfile(mouth_mask_path) or custom_color_basename == mouth_color_name:
        if i not in all_mouth_textures:
          all_mouth_textures[i] = link_main_model.tex1.textures_by_name["mouthS3TC.%d" % i]
          all_mouth_images[i] = all_mouth_textures[i][0].render()
        
        if os.path.isfile(mouth_mask_path):
          check_valid_mask_path(mouth_mask_path)
          all_mouth_images[i] = texture_utils.color_exchange(all_mouth_images[i], base_color, custom_color, mask_path=mouth_mask_path)
        elif custom_color_basename == mouth_color_name:
          all_mouth_images[i] = texture_utils.color_exchange(all_mouth_images[i], base_color, custom_color)
    
    # Recolor the hands.
    hands_mask_path = custom_model_metadata["hands_" + prefix + "_color_mask_paths"][custom_color_basename]
    if os.path.isfile(hands_mask_path):
      check_valid_mask_path(hands_mask_path)
      hands_image = texture_utils.color_exchange(hands_image, base_color, custom_color, mask_path=hands_mask_path)
      replaced_any_hands = True
    elif custom_color_basename == hands_color_name:
      hands_image = texture_utils.color_exchange(hands_image, base_color, custom_color)
      replaced_any_hands = True
  
  if not replaced_any:
    return
  
  if self.custom_model_name == "Link":
    # The vanilla Link model UV-mapped Link's hat and tunic to the same part of the texture.
    # We want the hat and tunic colors to be customizable separately, so we modify the UVs.
    # We edit the VTX1 section to move the hat UV coords to a vertical column on the right.
    texcoords = link_main_model.vtx1.attributes[GXAttr.Tex0]
    # Make sure this is the vanilla Link VTX1 section by checking the number of UV coords.
    # If the number of coords doesn't match this is probably a custom model, so skip it.
    # 810 is the correct number of coords, 816 is if you count padding too. Check both.
    if len(texcoords) in [810, 816]:
      hat_uv_indexes = slice(226, 293)
      for i, (u, v) in enumerate(texcoords[hat_uv_indexes]):
        texcoords[hat_uv_indexes.start+i] = (0.995, v)
  
  for texture in link_main_textures:
    if self.custom_model_name == "Link" and is_casual and texture.image_format == ImageFormat.C4:
      # Change the casual clothes texture to use C8 instead of C4 to increase the potential colors from 16 to 256.
      # This is only done for the vanilla Link model that comes with the game, not for custom models, since custom model creators could just change it themselves if they want to.
      texture.image_format = ImageFormat.C8
    elif self.custom_model_name == "Link" and not is_casual and texture.image_format == ImageFormat.CMPR:
      # Change the hero's clothes texture to use C8 instead of CMPR to prevent the lossy compression from creating seams.
      # This is only done for the vanilla Link model that comes with the game, not for custom models, since custom model creators could just change it themselves if they want to.
      texture.image_format = ImageFormat.C8
      texture.palette_format = PaletteFormat.RGB565
    
    texture.replace_image(link_main_image)
    
    if is_casual:
      texture.save_changes()
  
  for i, mouth_textures in all_mouth_textures.items():
    mouth_image = all_mouth_images[i]
    for mouth_texture in mouth_textures:
      mouth_texture.replace_image(mouth_image)
  
  if replaced_any_hands:
    for hands_texture in hands_textures:
      hands_texture.replace_image(hands_image)
    hands_model.save_changes()
  
  link_main_model.save_changes()

def get_model_preview_image(custom_model_name, prefix, selected_colors):
  custom_model_metadata = get_model_metadata(custom_model_name)
  
  if "preview_hero" not in custom_model_metadata:
    return None
  
  preview_image_path = custom_model_metadata["preview_%s" % prefix]
  if not os.path.isfile(preview_image_path):
    return None
  
  preview_image = Image.open(preview_image_path)
  
  custom_colors = custom_model_metadata.get(prefix + "_custom_colors", {})
  for custom_color_basename, base_color in custom_colors.items():
    custom_color = selected_colors.get(custom_color_basename, None)
    if custom_color is None:
      continue
    custom_color = tuple(custom_color)
    base_color = tuple(base_color)
    if custom_color == base_color:
      continue
    
    mask_path = custom_model_metadata["preview_" + prefix + "_color_mask_paths"][custom_color_basename]
    check_valid_mask_path(mask_path)
    
    preview_image = texture_utils.color_exchange(preview_image, base_color, custom_color, mask_path=mask_path, validate_mask_colors=False)
  
  return preview_image

def check_valid_mask_path(mask_path):
  if not os.path.isfile(mask_path):
    raise Exception("Color mask not found: %s" % mask_path)
  given_filename = os.path.basename(mask_path)
  
  mask_dir = os.path.dirname(mask_path)
  files_in_mask_folder = os.listdir(mask_dir)
  true_filename = next(filename for filename in files_in_mask_folder if filename.lower() == given_filename.lower())
  
  if given_filename != true_filename:
    raise Exception("Color mask path's actual capitalization differs from the capitalization given in metadata.txt.\nGiven: %s, actual: %s" % (given_filename, true_filename))

def get_default_colors(self):
  custom_model_metadata = get_model_metadata(self.custom_model_name)
  disable_casual_clothes = custom_model_metadata.get("disable_casual_clothes", False)
  
  if self.options.get("player_in_casual_clothes") and not disable_casual_clothes:
    prefix = "casual"
  else:
    prefix = "hero"
  
  custom_colors = custom_model_metadata.get(prefix + "_custom_colors", {})
  
  return custom_colors

class YamlOrderedDictLoader(yaml.SafeLoader):
  pass

YamlOrderedDictLoader.add_constructor(
  yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
  lambda loader, node: OrderedDict(loader.construct_pairs(node))
)
