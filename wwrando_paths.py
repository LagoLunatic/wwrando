
import os
import platform

import appdirs

try:
  from sys import _MEIPASS
  RANDO_ROOT_PATH = _MEIPASS
  IS_RUNNING_FROM_SOURCE = False
  if platform.system() == "Darwin":
    userdata_path = appdirs.user_data_dir("wwrando", "wwrando")
    SETTINGS_PATH = os.path.join(userdata_path, "settings.txt")
    CUSTOM_MODELS_PATH = os.path.join(userdata_path, "models")
    if not os.path.isdir(CUSTOM_MODELS_PATH):
      os.mkdir(CUSTOM_MODELS_PATH)
  else:
    CUSTOM_MODELS_PATH = os.path.join(".", "models")
    SETTINGS_PATH = os.path.join(".", "settings.txt")
except ImportError:
  RANDO_ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
  IS_RUNNING_FROM_SOURCE = True
  SETTINGS_PATH = os.path.join(RANDO_ROOT_PATH, "settings.txt")
  CUSTOM_MODELS_PATH = os.path.join(RANDO_ROOT_PATH, "models")

ASSETS_PATH = os.path.join(RANDO_ROOT_PATH, "assets")
DATA_PATH = os.path.join(RANDO_ROOT_PATH, "data")
LOGIC_PATH = os.path.join(RANDO_ROOT_PATH, "logic")
ASM_PATH = os.path.join(RANDO_ROOT_PATH, "asm")
SEEDGEN_PATH = os.path.join(RANDO_ROOT_PATH, "seedgen")
