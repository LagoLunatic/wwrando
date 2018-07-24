
import os
import re
import yaml
from collections import OrderedDict
from io import BytesIO

from fs_helpers import *
from wwlib import texture_utils
from paths import ASSETS_PATH

VANILLA_LINK_METADATA = {
  "hero_custom_colors": OrderedDict([
    ("Hair",  [255, 238, 16]),
    ("Shirt", [90, 178, 74]),
    ("Pants", [255, 255, 255]),
  ]),
  "casual_custom_colors": OrderedDict([
    ("Hair",  [255, 238, 16]),
    ("Shirt", [74, 117, 172]),
    ("Pants", [255, 161, 0]),
  ]),
  "hero_color_mask_paths": OrderedDict([
    ("Hair", os.path.join(ASSETS_PATH,  "link_hero_hair_mask.png")),
    ("Shirt", os.path.join(ASSETS_PATH, "link_hero_shirt_mask.png")),
    ("Pants", os.path.join(ASSETS_PATH, "link_hero_pants_mask.png")),
  ]),
  "casual_color_mask_paths": OrderedDict([
    ("Hair", os.path.join(ASSETS_PATH,  "link_casual_hair_mask.png")),
    ("Shirt", os.path.join(ASSETS_PATH, "link_casual_shirt_mask.png")),
    ("Pants", os.path.join(ASSETS_PATH, "link_casual_pants_mask.png")),
  ]),
}

def get_model_metadata(custom_model_name):
  if custom_model_name == "Link":
    return VANILLA_LINK_METADATA
  else:
    metadata_path = "./models/%s/metadata.txt" % custom_model_name
    if not os.path.isfile(metadata_path):
      return None
    
    with open(metadata_path) as f:
      metadata = yaml.load(f, YamlOrderedDictLoader)
    
    hero_color_mask_paths = OrderedDict()
    casual_color_mask_paths = OrderedDict()
    
    for key, value in metadata.items():
      if key in ["hero_custom_colors", "casual_custom_colors"]:
        for custom_color_name, hex_color in value.items():
          hex_color = str(hex_color)
          match = re.search(r"^([0-9A-F]{2})([0-9A-F]{2})([0-9A-F]{2})$", hex_color, re.IGNORECASE)
          if match:
            r, g, b = int(match.group(1), 16), int(match.group(2), 16), int(match.group(3), 16)
            value[custom_color_name] = [r, g, b]
          
          if key == "casual_custom_colors":
            path = os.path.join("models", custom_model_name, "color_masks", "casual_%s.png" % custom_color_name)
            casual_color_mask_paths[custom_color_name] = path
          else:
            path = os.path.join("models", custom_model_name, "color_masks", "hero_%s.png" % custom_color_name)
            hero_color_mask_paths[custom_color_name] = path
    
    metadata["hero_color_mask_paths"] = hero_color_mask_paths
    metadata["casual_color_mask_paths"] = casual_color_mask_paths
    
    return metadata

def replace_link_model(self):
  custom_model_name = self.options.get("custom_player_model", "Link")
  if custom_model_name == "Link":
    return
  
  if custom_model_name == "Random":
    custom_model_paths = glob.glob("./models/*/Link.arc")
    if not custom_model_paths:
      raise Exception("No custom models to randomly choose from in the /models folder.")
    
    custom_model_paths = [
      os.path.dirname(link_arc_path) + "/" for link_arc_path in custom_model_paths
    ]
    
    custom_model_paths.append(None) # Dummy entry to represent not changing Link's model
    
    temp_rng = Random()
    temp_rng.seed(self.integer_seed)
    
    custom_model_path = temp_rng.choice(custom_model_paths)
    
    if custom_model_path == None:
      return
  else:
    custom_model_path = "./models/%s/" % custom_model_name
  
  custom_link_arc_path = custom_model_path + "Link.arc"
  if not os.path.isfile(custom_link_arc_path):
    raise Exception("Custom model is missing Link.arc: %s" % custom_model_path)
  
  with open(custom_link_arc_path, "rb") as f:
    custom_link_arc_data = BytesIO(f.read())
  self.replace_arc("files/res/Object/Link.arc", custom_link_arc_data)
  
  # The texture shown on the wall when reflecting light with the mirror shield is separate from Link.arc.
  mirror_shield_reflection_image_path = custom_model_path + "shmref.bti"
  if os.path.isfile(mirror_shield_reflection_image_path):
    with open(mirror_shield_reflection_image_path, "rb") as f:
      reflection_image_data = BytesIO(f.read())
    always_arc = self.get_arc("files/res/Object/Always.arc")
    always_arc.get_file_entry("shmref.bti").data = reflection_image_data

def change_player_clothes_color(self):
  custom_model_name = self.options.get("custom_player_model", "Link")
  custom_model_metadata = get_model_metadata(custom_model_name)
  
  link_arc = self.get_arc("files/res/Object/Link.arc")
  link_main_model = link_arc.get_file("cl.bdl")
  
  if self.options.get("player_in_casual_clothes"):
    is_casual = True
    prefix = "casual"
    link_main_textures = [link_arc.get_file("linktexbci4.bti")]
  else:
    is_casual = False
    prefix = "hero"
    link_main_textures = link_main_model.tex1.textures_by_name["linktexS3TC"]
  
  first_texture = link_main_textures[0]
  link_main_image = first_texture.render()
  
  replaced_any = False
  custom_colors = custom_model_metadata.get(prefix + "_custom_colors", {})
  has_colored_eyebrows = custom_model_metadata.get("has_colored_eyebrows", False)
  for custom_color_basename, base_color in custom_colors.items():
    custom_color = self.options.get("custom_colors", {}).get(custom_color_basename, None)
    if custom_color is None:
      continue
    custom_color = tuple(custom_color)
    if custom_color == base_color:
      continue
    
    mask_path = custom_model_metadata[prefix + "_color_mask_paths"][custom_color_basename]
    
    link_main_image = texture_utils.color_exchange(link_main_image, base_color, custom_color, mask_path=mask_path)
    replaced_any = True
    
    # Recolor the eyebrows.
    if has_colored_eyebrows and custom_color_basename == "Hair":
      for i in range(1, 6+1):
        textures = link_main_model.tex1.textures_by_name["mayuh.%d" % i]
        eyebrow_image = textures[0].render()
        eyebrow_image = texture_utils.color_exchange(eyebrow_image, base_color, custom_color)
        for texture in textures:
          texture.image_format = 6
          texture.palette_format = 0
          texture.replace_image(eyebrow_image)
    
    # Recolor the back hair for casual Link.
    if is_casual and custom_color_basename == "Hair":
      link_hair_model = link_arc.get_file("katsura.bdl")
      link_hair_textures = link_hair_model.tex1.textures_by_name["katsuraS3TC"]
      first_texture = link_hair_textures[0]
      back_hair_image = first_texture.render()
      
      back_hair_image.paste(custom_color, [0, 0, 8, 8])
      
      for texture in link_hair_textures:
        if texture.image_format == 0xE:
          texture.image_format = 9
          texture.palette_format = 1
        texture.replace_image(back_hair_image)
      link_hair_model.save_changes()
  
  if not replaced_any:
    return
  
  for texture in link_main_textures:
    is_cmpr = (texture.image_format == 0xE)
    try:
      if is_cmpr:
        texture.image_format = 9
        texture.palette_format = 1
      texture.replace_image(link_main_image)
    except texture_utils.TooManyColorsError:
      if is_cmpr:
        texture.image_format = 4
        texture.palette_format = 0
      texture.replace_image(link_main_image)
    
    if is_casual:
      texture.save_changes()
  
  link_main_model.save_changes()


class YamlOrderedDictLoader(yaml.SafeLoader):
  pass

YamlOrderedDictLoader.add_constructor(
  yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
  lambda loader, node: OrderedDict(loader.construct_pairs(node))
)
