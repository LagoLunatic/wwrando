
from PySide.QtGui import *
from PySide.QtCore import *

from ui.ui_randomizer_window import Ui_MainWindow

import random

from randomizer import Randomizer

class WWRandomizerWindow(QMainWindow):
  def __init__(self):
    super(WWRandomizerWindow, self).__init__()
    self.ui = Ui_MainWindow()
    self.ui.setupUi(self)
    
    self.ui.generate_seed_button.clicked.connect(self.generate_seed)
    
    self.ui.randomize_button.clicked.connect(self.randomize)
    self.ui.about_button.clicked.connect(self.open_about)
    
    self.show()
  
  def generate_seed(self):
    random.seed(None)
    seed = random.randrange(0, 1000000)
    seed = str(seed)
    self.ui.seed.setText(seed)
  
  def randomize(self):
    seed = self.ui.seed.text().strip()
    if not seed:
      self.generate_seed()
      seed = self.ui.seed.text().strip()
    seed = int(seed)
    
    rando = Randomizer(seed, "../Wind Waker Files", "../Wind Waker Files Randomized")
    #rando.randomize()
  
  def open_about(self):
    text = """Wind Waker Randomizer<br><br>
      Created by LagoLunatic<br><br>
      Report issues here:<br><a href=\"https://github.com/LagoLunatic/wwrando/issues\">https://github.com/LagoLunatic/wwrando/issues</a><br><br>
      Source code:<br><a href=\"https://github.com/LagoLunatic/wwrando\">https://github.com/LagoLunatic/wwrando</a>"""
    
    self.about_dialog = QMessageBox()
    self.about_dialog.setTextFormat(Qt.TextFormat.RichText)
    self.about_dialog.setWindowTitle("Wind Waker Randomizer")
    self.about_dialog.setText(text)
    self.about_dialog.show()
