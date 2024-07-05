
import os
from ruamel.yaml import YAML
yaml = YAML(typ="safe")

from wwrando_paths import DATA_PATH

def read_actor_info():
  with open(os.path.join(DATA_PATH, "actor_info.txt"), "r") as f:
    actor_info = yaml.load(f)
  
  actor_name_to_class_name = {}
  for actor_name, actor_info in actor_info.items():
    class_name = actor_info["Class Name"]
    if class_name is not None:
      # Class name is case insensitive.
      class_name = class_name.lower()
    actor_name_to_class_name[actor_name] = class_name
  
  return actor_name_to_class_name

def read_actor_params():
  with open(os.path.join(DATA_PATH, "actor_parameters.txt"), "r") as f:
    case_sensitive_actor_parameters = yaml.load(f)
  
  actor_parameters = {}
  for class_name, params in case_sensitive_actor_parameters.items():
    # Class name is case insensitive.
    class_name = class_name.lower()
    
    actor_parameters[class_name] = {}
    for param_name, param_data in params.items():
      actor_parameters[class_name][param_name] = (param_data["Bitfield name"], param_data["Mask"])
  
  return actor_parameters

class DataTables:
  if os.path.isdir(DATA_PATH):
    actor_name_to_class_name = read_actor_info()
    actor_parameters = read_actor_params()
