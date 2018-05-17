
from PySide.QtGui import *
from PySide.QtCore import *

from ui.ui_randomizer_window import Ui_MainWindow
from ui.options import OPTIONS

import random
from collections import OrderedDict
import os
import yaml
import traceback

from randomizer import Randomizer, VERSION

class WWRandomizerWindow(QMainWindow):
  def __init__(self):
    super(WWRandomizerWindow, self).__init__()
    self.ui = Ui_MainWindow()
    self.ui.setupUi(self)
    
    self.load_settings()
    
    self.ui.clean_iso_path.editingFinished.connect(self.update_settings)
    self.ui.output_folder.editingFinished.connect(self.update_settings)
    self.ui.seed.editingFinished.connect(self.update_settings)
    self.ui.clean_iso_path_browse_button.clicked.connect(self.browse_for_clean_iso)
    self.ui.output_folder_browse_button.clicked.connect(self.browse_for_output_folder)
    
    for option_name in OPTIONS:
      getattr(self.ui, option_name).clicked.connect(self.update_settings)
    
    self.ui.generate_seed_button.clicked.connect(self.generate_seed)
    
    self.ui.randomize_button.clicked.connect(self.randomize)
    self.ui.about_button.clicked.connect(self.open_about)
    
    for option_name in OPTIONS:
      getattr(self.ui, option_name).installEventFilter(self)
    self.set_option_description(None)
    
    self.update_settings()
    
    self.setWindowTitle("Wind Waker Randomizer %s" % VERSION)
    
    self.show()
  
  def generate_seed(self):
    random.seed(None)
    seed = random.randrange(0, 1000000)
    seed = str(seed)
    self.settings["seed"] = seed
    self.ui.seed.setText(seed)
    self.save_settings()
  
  def randomize(self):
    clean_iso_path = self.settings["clean_iso_path"].strip()
    output_folder = self.settings["output_folder"].strip()
    self.settings["clean_iso_path"] = clean_iso_path
    self.settings["output_folder"] = output_folder
    self.ui.clean_iso_path.setText(clean_iso_path)
    self.ui.output_folder.setText(output_folder)
    
    if not os.path.isfile(clean_iso_path):
      QMessageBox.warning(self, "Clean ISO path not specified", "Must specify path to clean your Wind Waker ISO (USA).")
      return
    if not os.path.isdir(output_folder):
      QMessageBox.warning(self, "No output folder specified", "Must specify a valid output folder for the randomized files.")
      return
    
    seed = self.settings["seed"].strip()
    if not seed:
      self.generate_seed()
      seed = self.settings["seed"]
    self.settings["seed"] = seed
    self.ui.seed.setText(seed)
    self.save_settings()
    
    options = OrderedDict()
    for option_name in OPTIONS:
      options[option_name] = getattr(self.ui, option_name).isChecked()
    
    seed_output_folder = os.path.join(output_folder, "WW Random %s" % seed)
    
    try:
      rando = Randomizer(int(seed), clean_iso_path, seed_output_folder, options)
      rando.randomize()
    except Exception as e:
      stack_trace = traceback.format_exc()
      print(stack_trace)
      QMessageBox.critical(
        self, "Randomization Failed",
        "Randomization failed with error:\n" + str(e)
        + "\n\n" + stack_trace
      )
      return
    
    msg = "Randomization complete."
    QMessageBox.information(self, "Done", msg)
  
  def load_settings(self):
    self.settings_path = "settings.txt"
    if os.path.isfile(self.settings_path):
      with open(self.settings_path) as f:
        self.settings = yaml.safe_load(f)
      if self.settings is None:
        self.settings = OrderedDict()
    else:
      self.settings = OrderedDict()
    
    if "clean_iso_path" in self.settings:
      self.ui.clean_iso_path.setText(self.settings["clean_iso_path"])
    if "output_folder" in self.settings:
      self.ui.output_folder.setText(self.settings["output_folder"])
    if "seed" in self.settings:
      self.ui.seed.setText(self.settings["seed"])
    
    for option_name in OPTIONS:
      if option_name in self.settings:
        getattr(self.ui, option_name).setChecked(self.settings[option_name])
  
  def save_settings(self):
    with open(self.settings_path, "w") as f:
      yaml.dump(self.settings, f, default_flow_style=False, Dumper=yaml.CDumper)
  
  def update_settings(self):
    self.settings["clean_iso_path"] = self.ui.clean_iso_path.text()
    self.settings["output_folder"] = self.ui.output_folder.text()
    self.settings["seed"] = self.ui.seed.text()
    
    for option_name in OPTIONS:
      self.settings[option_name] = getattr(self.ui, option_name).isChecked()
    
    self.save_settings()
  
  def browse_for_clean_iso(self):
    if self.settings["clean_iso_path"] and os.path.isfile(self.settings["clean_iso_path"]):
      default_dir = os.path.dirname(self.settings["clean_iso_path"])
    else:
      default_dir = None
    
    clean_iso_path, selected_filter = QFileDialog.getOpenFileName(self, "Select clean Wind Waker ISO", default_dir, "GC ISO Files (*.iso *.gcm)")
    if not clean_iso_path:
      return
    self.ui.clean_iso_path.setText(clean_iso_path)
    self.update_settings()
  
  def browse_for_output_folder(self):
    if self.settings["output_folder"] and os.path.isdir(self.settings["output_folder"]):
      default_dir = self.settings["output_folder"]
    else:
      default_dir = None
    
    output_folder_path = QFileDialog.getExistingDirectory(self, "Select output folder", default_dir)
    if not output_folder_path:
      return
    self.ui.output_folder.setText(output_folder_path)
    self.update_settings()
  
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
    text = """Wind Waker Randomizer Version %s<br><br>
      Created by LagoLunatic<br><br>
      Report issues here:<br><a href=\"https://github.com/LagoLunatic/wwrando/issues\">https://github.com/LagoLunatic/wwrando/issues</a><br><br>
      Source code:<br><a href=\"https://github.com/LagoLunatic/wwrando\">https://github.com/LagoLunatic/wwrando</a>""" % VERSION
    
    self.about_dialog = QMessageBox()
    self.about_dialog.setTextFormat(Qt.TextFormat.RichText)
    self.about_dialog.setWindowTitle("Wind Waker Randomizer")
    self.about_dialog.setText(text)
    self.about_dialog.show()

# Allow yaml to load and dump OrderedDicts.
yaml.SafeLoader.add_constructor(
  yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
  lambda loader, node: OrderedDict(loader.construct_pairs(node))
)
yaml.CDumper.add_representer(
  OrderedDict,
  lambda dumper, data: dumper.represent_dict(data.items())
)
