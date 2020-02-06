
import os
import re
import yaml
from collections import OrderedDict
from io import BytesIO
import glob
from PIL import Image

from fs_helpers import *
from wwlib.texture_utils import *
from wwlib import texture_utils
from paths import ASSETS_PATH

MAX_ALLOWED_LINK_ARC_FILE_SIZE_IN_MEGABYTES = 1.45

def get_model_metadata(custom_model_name):
  if custom_model_name == "Random":
    return {}
  else:
    if custom_model_name == "Link":
      metadata_path = os.path.join(ASSETS_PATH, "link_metadata.txt")
      color_masks_path = os.path.join(ASSETS_PATH, "link_color_masks")
      previews_path = os.path.join(ASSETS_PATH, "link_preview")
    else:
      metadata_path = "./models/%s/metadata.txt" % custom_model_name
      color_masks_path = os.path.join("models", custom_model_name, "color_masks")
      previews_path = os.path.join("models", custom_model_name, "preview")
    
    if not os.path.isfile(metadata_path):
      return {}
    
    try:
      with open(metadata_path) as f:
        metadata = yaml.load(f, YamlOrderedDictLoader)
    except Exception as e:
      error_message = str(e)
      return {
        "error_message": error_message,
      }
    
    metadata["preview_hero"] = os.path.join(previews_path, "preview_hero.png")
    metadata["preview_casual"] = os.path.join(previews_path, "preview_casual.png")
    metadata["hands_hero_color_mask_path"] = os.path.join(color_masks_path, "hands_hero.png")
    metadata["hands_casual_color_mask_path"] = os.path.join(color_masks_path, "hands_casual.png")
    
    metadata["hero_color_mask_paths"] = OrderedDict()
    metadata["casual_color_mask_paths"] = OrderedDict()
    metadata["hands_hero_color_mask_paths"] = OrderedDict()
    metadata["hands_casual_color_mask_paths"] = OrderedDict()
    metadata["preview_hero_color_mask_paths"] = OrderedDict()
    metadata["preview_casual_color_mask_paths"] = OrderedDict()
    
    for key, value in metadata.items():
      if key in ["hero_custom_colors", "casual_custom_colors"]:
        prefix = key.split("_")[0]
        
        for custom_color_name, hex_color in value.items():
          if isinstance(hex_color, int):
            hex_color_string = "%06d" % hex_color
          elif isinstance(hex_color, str):
            hex_color_string = hex_color
          else:
            error_message = "Custom color \"%s\" has an invalid base color specified in metadata.txt: \"%s\"" % (custom_color_name, hex_color)
            return {
              "error_message": error_message,
            }
          
          match = re.search(r"^([0-9A-F]{2})([0-9A-F]{2})([0-9A-F]{2})$", hex_color_string, re.IGNORECASE)
          if match:
            r, g, b = int(match.group(1), 16), int(match.group(2), 16), int(match.group(3), 16)
            value[custom_color_name] = [r, g, b]
          else:
            error_message = "Custom color \"%s\" has an invalid base color specified in metadata.txt: \"%s\"" % (custom_color_name, hex_color_string)
            return {
              "error_message": error_message,
            }
          
          mask_path = os.path.join(color_masks_path, "%s_%s.png" % (prefix, custom_color_name))
          metadata["%s_color_mask_paths" % prefix][custom_color_name] = mask_path
          hands_mask_path = os.path.join(color_masks_path, "hands_%s_%s.png" % (prefix, custom_color_name))
          metadata["hands_%s_color_mask_paths" % prefix][custom_color_name] = hands_mask_path
          preview_mask_path = os.path.join(previews_path, "preview_%s_%s.png" % (prefix, custom_color_name))
          metadata["preview_%s_color_mask_paths" % prefix][custom_color_name] = preview_mask_path
    
    return metadata

def get_all_custom_model_names():
  custom_model_names = []
  custom_model_paths = glob.glob("./models/*/Link.arc")
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
  
  custom_model_path = "./models/%s/" % self.custom_model_name
  
  custom_link_arc_path = custom_model_path + "Link.arc"
  if not os.path.isfile(custom_link_arc_path):
    raise Exception("Custom model is missing Link.arc: %s" % custom_model_path)
  
  with open(custom_link_arc_path, "rb") as f:
    custom_link_arc_data = BytesIO(f.read())
  custom_link_arc_size_in_mb = data_len(custom_link_arc_data) / (1024 * 1024)
  if custom_link_arc_size_in_mb > MAX_ALLOWED_LINK_ARC_FILE_SIZE_IN_MEGABYTES+0.005:
    raise Exception("The chosen custom player model's filesize is too large and may cause crashes or other issues in game.\nMax size: %.2fMB\nSelected model size: %.2fMB" % (MAX_ALLOWED_LINK_ARC_FILE_SIZE_IN_MEGABYTES, custom_link_arc_size_in_mb))
  orig_link_arc = self.get_arc("files/res/Object/Link.arc")
  self.replace_arc("files/res/Object/Link.arc", custom_link_arc_data)
  custom_link_arc = self.get_arc("files/res/Object/Link.arc")
  
  # Revert all BCK animations in Link.arc to the original ones.
  # This is because BCK animations can change gameplay, which we don't want to allow cosmetic mods to do.
  for orig_file_entry in orig_link_arc.file_entries:
    basename, file_ext = os.path.splitext(orig_file_entry.name)
    if file_ext == ".bck":
      custom_file_entry = custom_link_arc.get_file_entry(orig_file_entry.name)
      custom_file_entry.data = orig_file_entry.data
  
  # Replace Link's animations.
  lkanm_path = custom_model_path + "LkAnm.arc"
  if os.path.isfile(lkanm_path):
    with open(lkanm_path, "rb") as f:
      custom_lkanm_arc_data = BytesIO(f.read())
    orig_lkanm_arc = self.get_arc("files/res/Object/LkAnm.arc")
    self.replace_arc("files/res/Object/LkAnm.arc", custom_lkanm_arc_data)
    custom_lkanm_arc = self.get_arc("files/res/Object/LkAnm.arc")
    
    # Revert all BCK animations in LkAnm.arc to the original ones.
    # This is because BCK animations can change gameplay, which we don't want to allow cosmetic mods to do.
    for orig_file_entry in orig_lkanm_arc.file_entries:
      basename, file_ext = os.path.splitext(orig_file_entry.name)
      if file_ext == ".bck":
        custom_file_entry = custom_lkanm_arc.get_file_entry(orig_file_entry.name)
        custom_file_entry.data = orig_file_entry.data
  
  # The texture shown on the wall when reflecting light with the mirror shield is separate from Link.arc.
  mirror_shield_reflection_image_path = custom_model_path + "shmref.bti"
  if os.path.isfile(mirror_shield_reflection_image_path):
    with open(mirror_shield_reflection_image_path, "rb") as f:
      reflection_image_data = BytesIO(f.read())
    always_arc = self.get_arc("files/res/Object/Always.arc")
    always_arc.get_file_entry("shmref.bti").data = reflection_image_data
  
  if not self.options.get("disable_custom_player_voice"):
    # Replace voice sound effects.
    jaiinit_aaf_path = custom_model_path + "sound/JaiInit.aaf"
    voice_aw_path = custom_model_path + "sound/voice_0.aw"
    ganont_aw_path = custom_model_path + "sound/GanonT_0.aw"
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

def change_player_clothes_color(self):
  custom_model_metadata = get_model_metadata(self.custom_model_name)
  disable_casual_clothes = custom_model_metadata.get("disable_casual_clothes", False)
  
  link_arc = self.get_arc("files/res/Object/Link.arc")
  link_main_model = link_arc.get_file("cl.bdl")
  
  if self.options.get("player_in_casual_clothes") and not disable_casual_clothes:
    is_casual = True
    prefix = "casual"
    link_main_textures = [link_arc.get_file("linktexbci4.bti")]
  else:
    is_casual = False
    prefix = "hero"
    link_main_textures = link_main_model.tex1.textures_by_name["linktexS3TC"]
  
  first_texture = link_main_textures[0]
  link_main_image = first_texture.render()
  
  hands_model = link_arc.get_file("hands.bdl")
  hands_textures = hands_model.tex1.textures_by_name["handsS3TC"]
  hands_image = hands_textures[0].render()
  
  replaced_any = False
  replaced_any_hands = False
  custom_colors = custom_model_metadata.get(prefix + "_custom_colors", {})
  has_colored_eyebrows = custom_model_metadata.get("has_colored_eyebrows", False)
  hands_color_name = custom_model_metadata.get(prefix + "_hands_color_name", "Skin")
  mouth_color_name = custom_model_metadata.get(prefix + "_mouth_color_name", "Skin")
  eyebrow_color_name = custom_model_metadata.get(prefix + "_eyebrow_color_name", "Hair")
  casual_hair_color_name = custom_model_metadata.get("casual_hair_color_name", "Hair")
  for custom_color_basename, base_color in custom_colors.items():
    custom_color = self.options.get("custom_colors", {}).get(custom_color_basename, None)
    if custom_color is None:
      continue
    custom_color = tuple(custom_color)
    base_color = tuple(base_color)
    if custom_color == base_color:
      continue
    
    mask_path = custom_model_metadata[prefix + "_color_mask_paths"][custom_color_basename]
    
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
      link_hair_model = link_arc.get_file("katsura.bdl")
      link_hair_textures = link_hair_model.tex1.textures_by_name["katsuraS3TC"]
      first_texture = link_hair_textures[0]
      back_hair_image = first_texture.render()
      
      back_hair_image.paste(custom_color, [0, 0, 8, 8])
      
      for link_hair_texture in link_hair_textures:
        link_hair_texture.replace_image(back_hair_image)
      link_hair_model.save_changes()
    
    # Recolor the mouth.
    if custom_color_basename == mouth_color_name:
      for i in range(1, 9+1):
        mouth_textures = link_main_model.tex1.textures_by_name["mouthS3TC.%d" % i]
        mouth_image = mouth_textures[0].render()
        mouth_image = texture_utils.color_exchange(mouth_image, base_color, custom_color)
        for mouth_texture in mouth_textures:
          mouth_texture.replace_image(mouth_image)
    
    # Recolor the hands.
    hands_mask_path = custom_model_metadata["hands_" + prefix + "_color_mask_paths"][custom_color_basename]
    if os.path.isfile(hands_mask_path):
      hands_image = texture_utils.color_exchange(hands_image, base_color, custom_color, mask_path=hands_mask_path)
      replaced_any_hands = True
    elif custom_color_basename == hands_color_name:
      hands_image = texture_utils.color_exchange(hands_image, base_color, custom_color)
      replaced_any_hands = True
  
  if not replaced_any:
    return
  
  for texture in link_main_textures:
    if self.custom_model_name == "Link" and is_casual and texture.image_format == ImageFormat.C4:
      # Change the casual clothes texture to use C8 instead of C4 to increase the potential colors from 16 to 256.
      # This is only done for the vanilla Link model that comes with the game, not for custom models, since custom model creators could just change it themselves if they want to.
      texture.image_format = ImageFormat.C8
    
    texture.replace_image(link_main_image)
    
    if is_casual:
      texture.save_changes()
  
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
