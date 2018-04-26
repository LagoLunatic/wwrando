
from PySide.QtGui import *
from PySide.QtCore import *

import sys

from ui.randomizer_window import WWRandomizerWindow

qApp = QApplication(sys.argv)
window = WWRandomizerWindow()
sys.exit(qApp.exec_())
