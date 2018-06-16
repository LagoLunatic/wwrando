
import os

try:
  from sys import _MEIPASS
  RANDO_ROOT_PATH = _MEIPASS
  ASSETS_PATH = os.path.join(_MEIPASS, "assets")
  DATA_PATH = os.path.join(_MEIPASS, "data")
  LOGIC_PATH = os.path.join(_MEIPASS, "logic")
  ASM_PATH = os.path.join(_MEIPASS, "asm")
  SEEDGEN_PATH = os.path.join(_MEIPASS, "seedgen")
except ImportError:
  RANDO_ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
  ASSETS_PATH = os.path.join(RANDO_ROOT_PATH, "assets")
  DATA_PATH = os.path.join(RANDO_ROOT_PATH, "data")
  LOGIC_PATH = os.path.join(RANDO_ROOT_PATH, "logic")
  ASM_PATH = os.path.join(RANDO_ROOT_PATH, "asm")
  SEEDGEN_PATH = os.path.join(RANDO_ROOT_PATH, "seedgen")
