
from PySide.QtGui import *
from PySide.QtCore import *

from ui.ui_randomizer_window import Ui_MainWindow
from ui.options import OPTIONS

import random
from collections import OrderedDict
import os

from randomizer import Randomizer

class WWRandomizerWindow(QMainWindow):
  def __init__(self):
    super(WWRandomizerWindow, self).__init__()
    self.ui = Ui_MainWindow()
    self.ui.setupUi(self)
    
    self.ui.generate_seed_button.clicked.connect(self.generate_seed)
    
    self.ui.randomize_button.clicked.connect(self.randomize)
    self.ui.about_button.clicked.connect(self.open_about)
    
    for option_name in OPTIONS:
      getattr(self.ui, option_name).installEventFilter(self)
    self.set_option_description(None)
    
    self.show()
  
  def generate_seed(self):
    random.seed(None)
    seed = random.randrange(0, 1000000)
    seed = str(seed)
    self.ui.seed.setText(seed)
  
  def randomize(self):
    clean_files_path = self.ui.clean_files_path.text().strip()
    output_folder = self.ui.output_folder.text().strip()
    self.ui.clean_files_path.setText(clean_files_path)
    self.ui.output_folder.setText(output_folder)
    if not os.path.isdir(clean_files_path):
      QMessageBox.warning(self, "Clean files path not specified", "Must specify path to clean your Wind Waker files.")
      return
    if not os.path.isdir(output_folder):
      QMessageBox.warning(self, "No output folder specified", "Must specify a valid output folder for the randomized files.")
      return
    
    seed = self.ui.seed.text().strip()
    if not seed:
      self.generate_seed()
      seed = self.ui.seed.text().strip()
    seed = int(seed)
    
    options = OrderedDict()
    for option_name in OPTIONS:
      options[option_name] = getattr(self.ui, option_name).isChecked()
    
    rando = Randomizer(seed, clean_files_path, output_folder, options)
    #rando.randomize()
  
  def eventFilter(self, target, event):
    if event.type() == QEvent.Enter:
      option_name = target.objectName()
      if option_name in OPTIONS:
        self.set_option_description(OPTIONS[option_name])
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
