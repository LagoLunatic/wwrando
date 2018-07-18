
from PySide.QtGui import *
from PySide.QtCore import *

import sys

from ui.randomizer_window import WWRandomizerWindow

try:
  from sys import _MEIPASS
except ImportError:
  # Setting the app user model ID is necessary for Windows to display a custom taskbar icon when running the randomizer from source.
  import ctypes
  app_id = "LagoLunatic.WindWakerRandomizer"
  try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
  except AttributeError:
    # Versions of Windows before Windows 7 don't support SetCurrentProcessExplicitAppUserModelID, so just swallow the error.
    pass

qApp = QApplication(sys.argv)
window = WWRandomizerWindow()
sys.exit(qApp.exec_())
