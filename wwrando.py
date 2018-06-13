
from PySide.QtGui import *
from PySide.QtCore import *

import sys
import ctypes

from ui.randomizer_window import WWRandomizerWindow

# Setting the app user model ID is necessary for Windows to display a custom taskbar icon when running the randomizer from source.
app_id = "LagoLunatic.WindWakerRandomizer"
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)

qApp = QApplication(sys.argv)
window = WWRandomizerWindow()
sys.exit(qApp.exec_())
