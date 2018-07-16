
import os
import re
import yaml

from paths import ASSETS_PATH

VANILLA_LINK_METADATA = {
  "hero_shirt_color": [90, 178, 74],
  "hero_pants_color": [255, 255, 255],
  "hero_hair_color": [255, 238, 16],
  "hero_shirt_mask": os.path.join(ASSETS_PATH, "link_hero_shirt_mask.png"),
  "hero_pants_mask": os.path.join(ASSETS_PATH, "link_hero_pants_mask.png"),
  "hero_hair_mask": os.path.join(ASSETS_PATH, "link_hero_hair_mask.png"),
  "casual_shirt_color": [74, 117, 172],
  "casual_pants_color": [255, 161, 0],
  "casual_hair_color": [255, 238, 16],
  "casual_shirt_mask": os.path.join(ASSETS_PATH, "link_casual_shirt_mask.png"),
  "casual_pants_mask": os.path.join(ASSETS_PATH, "link_casual_pants_mask.png"),
  "casual_hair_mask": os.path.join(ASSETS_PATH, "link_casual_hair_mask.png"),
}

def get_model_metadata(custom_model_name):
  if custom_model_name == "Link":
    return VANILLA_LINK_METADATA
  else:
    metadata_path = "./models/%s/metadata.txt" % custom_model_name
    if not os.path.isfile(metadata_path):
      return None
    
    with open(metadata_path) as f:
      metadata = yaml.load(f)
    
    for key, value in metadata.items():
      if key.endswith("_color"):
        value = str(value)
        match = re.search(r"^([0-9A-F]{2})([0-9A-F]{2})([0-9A-F]{2})$", value, re.IGNORECASE)
        if match:
          r, g, b = int(match.group(1), 16), int(match.group(2), 16), int(match.group(3), 16)
          metadata[key] = [r, g, b]
    
    metadata["hero_shirt_mask"]   = "./models/%s/hero_shirt_mask.png"   % custom_model_name
    metadata["hero_pants_mask"]   = "./models/%s/hero_pants_mask.png"   % custom_model_name
    metadata["hero_hair_mask"]    = "./models/%s/hero_hair_mask.png"    % custom_model_name
    metadata["casual_shirt_mask"] = "./models/%s/casual_shirt_mask.png" % custom_model_name
    metadata["casual_pants_mask"] = "./models/%s/casual_pants_mask.png" % custom_model_name
    metadata["casual_hair_mask"]  = "./models/%s/casual_hair_mask.png"  % custom_model_name
    
    return metadata
