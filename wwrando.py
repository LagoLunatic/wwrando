#!/usr/bin/python3.6

try:
  from PySide2.QtWidgets import QApplication
except ImportError:
  from PyQt5.QtWidgets import QApplication

import sys
from collections import OrderedDict

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

cmd_line_args = OrderedDict()
for arg in sys.argv[1:]:
  arg_parts = arg.split("=", 1)
  if len(arg_parts) == 1:
    cmd_line_args[arg_parts[0]] = None
  else:
    cmd_line_args[arg_parts[0]] = arg_parts[1]

qApp = QApplication(sys.argv)
window = WWRandomizerWindow(cmd_line_args=cmd_line_args)
sys.exit(qApp.exec_())
