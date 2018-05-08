
from PySide.QtGui import *
from PySide.QtCore import *

from ui.ui_randomizer_window import Ui_MainWindow
from ui.option_descriptions import OPTION_DESCRIPTIONS

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
    
    self.ui.short_mode.installEventFilter(self)
    self.ui.swift_sail.installEventFilter(self)
    self.ui.instant_text_boxes.installEventFilter(self)
    self.ui.reveal_full_sea_chart.installEventFilter(self)
    self.set_option_description(None)
    
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
  
  def eventFilter(self, target, event):
    if event.type() == QEvent.Enter:
      option_name = target.objectName()
      if option_name in OPTION_DESCRIPTIONS:
        self.set_option_description(OPTION_DESCRIPTIONS[option_name])
      else:
        self.set_option_description(None)
      return True
    elif event.type() == QEvent.Leave:
      self.set_option_description(None)
      return True
    
    return QMainWindow.eventFilter(self, target, event)
  
  def set_option_description(self, new_description):
    if new_description is None:
      self.ui.option_description.setText("(Hover over an option to see a description of what it does.)")
      self.ui.option_description.setStyleSheet("color: grey;")
    else:
      self.ui.option_description.setText(new_description)
      self.ui.option_description.setStyleSheet("")
  
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
