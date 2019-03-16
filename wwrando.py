#!/usr/bin/python3.6

from PySide2.QtGui import *
from PySide2.QtCore import *
from PySide2.QtWidgets import *

import sys

from wwr_ui.randomizer_window import WWRandomizerWindow

# Allow keyboard interrupts on the command line to instantly close the program.
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

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

cmd_line_args = sys.argv[1:]

qApp = QApplication(sys.argv)
window = WWRandomizerWindow(cmd_line_args=cmd_line_args)
sys.exit(qApp.exec_())
