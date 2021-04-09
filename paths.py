
import os
import sys

try:
  from sys import _MEIPASS
  RANDO_ROOT_PATH = _MEIPASS
  IS_RUNNING_FROM_SOURCE = False
except ImportError:
  RANDO_ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
  IS_RUNNING_FROM_SOURCE = True

ASSETS_PATH = os.path.join(RANDO_ROOT_PATH, "assets")
DATA_PATH = os.path.join(RANDO_ROOT_PATH, "data")
LOGIC_PATH = os.path.join(RANDO_ROOT_PATH, "logic")
ASM_PATH = os.path.join(RANDO_ROOT_PATH, "asm")
SEEDGEN_PATH = os.path.join(RANDO_ROOT_PATH, "seedgen")
#Needed to correctly place settings.txt when bundled as a macOS app
if getattr(sys, 'frozen', False):
  CURRENT_PATH = os.path.dirname(sys.executable)
else:
  CURRENT_PATH = str(os.path.dirname(__file__))
