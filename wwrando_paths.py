
import os
import sys

import appdirs

try:
  from sys import _MEIPASS
  RANDO_ROOT_PATH = _MEIPASS
  IS_RUNNING_FROM_SOURCE = False
  SETTINGS_PATH = os.path.join(".", "settings.txt")
  CUSTOM_MODELS_PATH = os.path.join(".", "models")
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
USERDATA_PATH = appdirs.user_data_dir("wwrando", "wwrando")
if os.path.isdir("./models/"):
  MODEL_PATH = "./models/"
else:
  MODEL_PATH = os.path.join(USERDATA_PATH, "models")
