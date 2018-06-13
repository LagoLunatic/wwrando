
import os

try:
  from sys import _MEIPASS
  ASSETS_PATH = os.path.join(_MEIPASS, "assets")
  DATA_PATH = os.path.join(_MEIPASS, "data")
  LOGIC_PATH = os.path.join(_MEIPASS, "logic")
  ASM_PATH = os.path.join(_MEIPASS, "asm")
  SEEDGEN_PATH = os.path.join(_MEIPASS, "seedgen")
except ImportError:
  ASSETS_PATH = "assets"
  DATA_PATH = "data"
  LOGIC_PATH = "logic"
  ASM_PATH = "asm"
  SEEDGEN_PATH = "seedgen"
