
from PySide.QtGui import *
from PySide.QtCore import *

from ui.ui_randomizer_window import Ui_MainWindow
from ui.options import OPTIONS, NON_PERMALINK_OPTIONS, COLOR_SELECTOR_OPTIONS
from ui.update_checker import check_for_updates, LATEST_RELEASE_DOWNLOAD_PAGE_URL

import random
from collections import OrderedDict
import os
import traceback
import string
import struct
import base64
import glob

import yaml
try:
  from yaml import CDumper as Dumper
except ImportError:
  from yaml import Dumper

from randomizer import Randomizer, VERSION, TooFewProgressionLocationsError
from paths import ASSETS_PATH, SEEDGEN_PATH
import customizer

class WWRandomizerWindow(QMainWindow):
  VALID_SEED_CHARACTERS = "-_'%%.%s%s" % (string.ascii_letters, string.digits)
  
  def __init__(self):
    super(WWRandomizerWindow, self).__init__()
    self.ui = Ui_MainWindow()
    self.ui.setupUi(self)
    
    self.custom_colors = {}
    self.initialize_custom_player_model_list()
    
    self.preserve_default_settings()
    
    self.load_settings()
    
    self.ui.clean_iso_path.editingFinished.connect(self.update_settings)
    self.ui.output_folder.editingFinished.connect(self.update_settings)
    self.ui.seed.editingFinished.connect(self.update_settings)
    self.ui.clean_iso_path_browse_button.clicked.connect(self.browse_for_clean_iso)
    self.ui.output_folder_browse_button.clicked.connect(self.browse_for_output_folder)
    self.ui.permalink.textEdited.connect(self.permalink_modified)
    
    self.ui.custom_player_model.currentIndexChanged.connect(self.player_model_changed)
    self.ui.player_in_casual_clothes.clicked.connect(self.player_model_changed)
    
    for option_name in OPTIONS:
      widget = getattr(self.ui, option_name)
      if isinstance(widget, QAbstractButton):
        widget.clicked.connect(self.update_settings)
      elif isinstance(widget, QComboBox):
        widget.currentIndexChanged.connect(self.update_settings)
      else:
        raise Exception("Option widget is invalid: %s" % option_name)
    
    for option_name in COLOR_SELECTOR_OPTIONS:
      button = getattr(self.ui, option_name)
      button.clicked.connect(self.open_custom_color_chooser)
    
    self.ui.generate_seed_button.clicked.connect(self.generate_seed)
    
    self.ui.randomize_button.clicked.connect(self.randomize)
    self.ui.reset_settings_to_default.clicked.connect(self.reset_settings_to_default)
    self.ui.about_button.clicked.connect(self.open_about)
    
    for option_name in OPTIONS:
      getattr(self.ui, option_name).installEventFilter(self)
      label_for_option = getattr(self.ui, "label_for_" + option_name, None)
      if label_for_option:
        label_for_option.installEventFilter(self)
    self.set_option_description(None)
    
    self.update_settings()
    
    self.setWindowTitle("Wind Waker Randomizer %s" % VERSION)
    
    icon_path = os.path.join(ASSETS_PATH, "icon.ico")
    self.setWindowIcon(QIcon(icon_path))
    
    self.show()
    
    self.update_checker_thread = UpdateCheckerThread()
    self.update_checker_thread.finished_checking_for_updates.connect(self.show_update_check_results)
    self.update_checker_thread.start()
  
  def generate_seed(self):
    random.seed(None)
    
    with open(os.path.join(SEEDGEN_PATH, "adjectives.txt")) as f:
      adjectives = random.sample(f.read().splitlines(), 2)
    noun_file_to_use = random.choice(["nouns.txt", "names.txt"])
    with open(os.path.join(SEEDGEN_PATH, noun_file_to_use)) as f:
      noun = random.choice(f.read().splitlines())
    words = adjectives + [noun]
    capitalized_words = []
    for word in words:
      capitalized_word = ""
      seen_first_letter = False
      for char in word:
        if char in string.ascii_letters and not seen_first_letter:
          capitalized_word += char.capitalize()
          seen_first_letter = True
        else:
          capitalized_word += char
      capitalized_words.append(capitalized_word)
    seed = "".join(capitalized_words)
    
    seed = self.sanitize_seed(seed)
    
    self.settings["seed"] = seed
    self.ui.seed.setText(seed)
    self.update_settings()
  
  def sanitize_seed(self, seed):
    seed = str(seed)
    seed = seed.strip()
    seed = "".join(char for char in seed if char in self.VALID_SEED_CHARACTERS)
    return seed
  
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
    
    seed = self.settings["seed"]
    seed = self.sanitize_seed(seed)
    
    if not seed:
      self.generate_seed()
      seed = self.settings["seed"]
    
    self.settings["seed"] = seed
    self.ui.seed.setText(seed)
    self.update_settings()
    
    options = OrderedDict()
    for option_name in OPTIONS:
      options[option_name] = self.get_option_value(option_name)
    
    permalink = self.ui.permalink.text()
    
    max_progress_val = 20
    self.progress_dialog = RandomizerProgressDialog("Randomizing", "Initializing...", max_progress_val)
    
    try:
      rando = Randomizer(seed, clean_iso_path, output_folder, options, permalink=permalink)
    except TooFewProgressionLocationsError as e:
      error_message = str(e)
      self.randomization_failed(error_message)
      return
    except Exception as e:
      stack_trace = traceback.format_exc()
      error_message = "Randomization failed with error:\n" + str(e) + "\n\n" + stack_trace
      self.randomization_failed(error_message)
      return
    
    self.randomizer_thread = RandomizerThread(rando)
    self.randomizer_thread.update_progress.connect(self.update_progress_dialog)
    self.randomizer_thread.randomization_complete.connect(self.randomization_complete)
    self.randomizer_thread.randomization_failed.connect(self.randomization_failed)
    self.randomizer_thread.start()
  
  def update_progress_dialog(self, next_option_description, options_finished):
    self.progress_dialog.setLabelText(next_option_description)
    self.progress_dialog.setValue(options_finished)
  
  def randomization_complete(self):
    self.progress_dialog.reset()
    
    msg = "Randomization complete.\n\n"
    msg += "If you get stuck, check the progression spoiler log in the output folder."
    QMessageBox.information(self, "Done", msg)
  
  def randomization_failed(self, error_message):
    self.progress_dialog.reset()
    
    try:
      self.randomizer_thread.randomizer.write_error_log(error_message)
    except:
      # If an error happened when writing the error log just ignore it.
      pass
    
    print(error_message)
    QMessageBox.critical(
      self, "Randomization Failed",
      error_message
    )
  
  def show_update_check_results(self, new_version):
    if not new_version:
      self.ui.update_checker_label.setText("No new updates to the randomizer are available.")
    elif new_version == "error":
      self.ui.update_checker_label.setText("There was an error checking for updates.")
    else:
      new_text = "<b>Version %s of the randomizer is available!</b>" % new_version
      new_text += " <a href=\"%s\">Click here</a> to go to the download page." % LATEST_RELEASE_DOWNLOAD_PAGE_URL
      self.ui.update_checker_label.setText(new_text)
  
  def preserve_default_settings(self):
    self.default_settings = OrderedDict()
    for option_name in OPTIONS:
      self.default_settings[option_name] = self.get_option_value(option_name)
  
  def reset_settings_to_default(self):
    any_setting_changed = False
    for option_name in OPTIONS:
      if option_name in self.default_settings:
        default_value = self.default_settings[option_name]
        current_value = self.get_option_value(option_name)
        if default_value != current_value:
          any_setting_changed = True
        self.set_option_value(option_name, default_value)
    
    self.update_settings()
    
    if not any_setting_changed:
      QMessageBox.information(self,
        "Settings already default",
        "You already have all the default randomization settings."
      )
  
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
        self.set_option_value(option_name, self.settings[option_name])
  
  def save_settings(self):
    with open(self.settings_path, "w") as f:
      yaml.dump(self.settings, f, default_flow_style=False, Dumper=yaml.Dumper)
  
  def update_settings(self):
    self.settings["clean_iso_path"] = self.ui.clean_iso_path.text()
    self.settings["output_folder"] = self.ui.output_folder.text()
    self.settings["seed"] = self.ui.seed.text()
    
    for option_name in OPTIONS:
      self.settings[option_name] = self.get_option_value(option_name)
    
    self.save_settings()
    
    self.encode_permalink()
  
  def permalink_modified(self):
    permalink = self.ui.permalink.text()
    try:
      self.decode_permalink(permalink)
    except Exception as e:
      stack_trace = traceback.format_exc()
      error_message = "Failed to parse permalink:\n" + str(e) + "\n\n" + stack_trace
      print(error_message)
      QMessageBox.critical(
        self, "Invalid permalink",
        "The permalink you pasted is invalid."
      )
    
    self.encode_permalink()
  
  def encode_permalink(self):
    seed = self.settings["seed"]
    seed = self.sanitize_seed(seed)
    if not seed:
      self.ui.permalink.setText("")
      return
    
    permalink = b""
    permalink += VERSION.encode("ascii")
    permalink += b"\0"
    permalink += seed.encode("ascii")
    permalink += b"\0"
    
    option_bytes = []
    current_byte = 0
    current_bit_index = 0
    for option_name in OPTIONS:
      if option_name in NON_PERMALINK_OPTIONS:
        continue
      
      value = self.settings[option_name]
      
      widget = getattr(self.ui, option_name)
      if isinstance(widget, QAbstractButton):
        if current_bit_index >= 8:
          option_bytes.append(current_byte)
          current_bit_index = 0
          current_byte = 0
        
        current_byte |= (int(value) << current_bit_index)
        current_bit_index += 1
      elif isinstance(widget, QComboBox):
        if current_bit_index > 0:
          # End the current bitfield byte.
          option_bytes.append(current_byte)
          current_bit_index = 0
          current_byte = 0
        
        value = int(value)
        assert 0 <= value <= 255
        option_bytes.append(value)
    
    if current_bit_index > 0:
      # End the current bitfield byte.
      option_bytes.append(current_byte)
    
    for byte in option_bytes:
      permalink += struct.pack(">B", byte)
    base64_encoded_permalink = base64.b64encode(permalink).decode("ascii")
    self.ui.permalink.setText(base64_encoded_permalink)
  
  def decode_permalink(self, base64_encoded_permalink):
    base64_encoded_permalink = base64_encoded_permalink.strip()
    if not base64_encoded_permalink:
      # Empty
      return
    
    permalink = base64.b64decode(base64_encoded_permalink)
    given_version_num, seed, options_bytes = permalink.split(b"\0", 2)
    given_version_num = given_version_num.decode("ascii")
    seed = seed.decode("ascii")
    if given_version_num != VERSION:
      QMessageBox.critical(
        self, "Invalid permalink",
        "The permalink you pasted is for version %s of the randomizer, it cannot be used with the version you are currently using (%s)." % (given_version_num, VERSION)
      )
      return
    
    self.ui.seed.setText(seed)
    
    option_bytes = struct.unpack(">" + "B"*len(options_bytes), options_bytes)
    
    current_byte_index = 0
    current_bit_index = 0
    for option_name in OPTIONS:
      if option_name in NON_PERMALINK_OPTIONS:
        continue
      
      if current_bit_index >= 8:
        current_byte_index += 1
        current_bit_index = 0
      
      widget = getattr(self.ui, option_name)
      if isinstance(widget, QAbstractButton):
        current_byte = option_bytes[current_byte_index]
        current_bit = ((current_byte >> current_bit_index) & 1)
        current_bit_index += 1
        
        boolean_value = bool(current_bit)
        self.set_option_value(option_name, boolean_value)
      elif isinstance(widget, QComboBox):
        if current_bit_index > 0:
          # End the current bitfield byte.
          current_byte_index += 1
          current_bit_index = 0
        current_byte = option_bytes[current_byte_index]
        
        integer_value = str(current_byte)
        self.set_option_value(option_name, integer_value)
        current_byte_index += 1
        current_bit_index = 0
    
    self.update_settings()
  
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
      
      if option_name.startswith("label_for_"):
        option_name = option_name[len("label_for_"):]
      
      if option_name in OPTIONS:
        self.set_option_description(OPTIONS[option_name])
      else:
        self.set_option_description(None)
      return True
    elif event.type() == QEvent.Leave:
      self.set_option_description(None)
      return True
    
    return QMainWindow.eventFilter(self, target, event)
  
  def get_option_value(self, option_name):
    widget = getattr(self.ui, option_name)
    if isinstance(widget, QCheckBox) or isinstance(widget, QRadioButton):
      return widget.isChecked()
    elif isinstance(widget, QComboBox):
      return widget.itemText(widget.currentIndex())
    elif isinstance(widget, QPushButton) and option_name in COLOR_SELECTOR_OPTIONS:
      return self.custom_colors[option_name]
    else:
      print("Option widget is invalid: %s" % option_name)
  
  def set_option_value(self, option_name, new_value):
    widget = getattr(self.ui, option_name)
    if isinstance(widget, QCheckBox) or isinstance(widget, QRadioButton):
      widget.setChecked(new_value)
    elif isinstance(widget, QComboBox):
      index_of_value = None
      for i in range(widget.count()):
        text = widget.itemText(i)
        if text == new_value:
          index_of_value = i
          break
      
      if index_of_value is None:
        print("Cannot find value %s in combobox %s" % (new_value, option_name))
        index_of_value = 0
      
      widget.setCurrentIndex(index_of_value)
    elif isinstance(widget, QPushButton) and option_name in COLOR_SELECTOR_OPTIONS:
      self.set_color(option_name, new_value)
    else:
      print("Option widget is invalid: %s" % option_name)
  
  def set_option_description(self, new_description):
    if new_description is None:
      self.ui.option_description.setText("(Hover over an option to see a description of what it does.)")
      self.ui.option_description.setStyleSheet("color: grey;")
    else:
      self.ui.option_description.setText(new_description)
      self.ui.option_description.setStyleSheet("")
  
  def initialize_custom_player_model_list(self):
    self.ui.custom_player_model.addItem("Link")
    
    custom_model_paths = glob.glob("./models/*/Link.arc")
    for link_arc_path in custom_model_paths:
      folder_name = os.path.basename(os.path.dirname(link_arc_path))
      self.ui.custom_player_model.addItem(folder_name)
    
    if custom_model_paths:
      #self.ui.custom_player_model.addItem("Random")
      pass
    else:
      self.ui.custom_player_model.setEnabled(False)
    
    default_shirt_color = customizer.get_model_metadata("Link")["hero_shirt_color"]
    self.set_color("player_shirt_color", default_shirt_color)
    default_shirt_color = customizer.get_model_metadata("Link")["hero_pants_color"]
    self.set_color("player_pants_color", default_shirt_color)
    default_shirt_color = customizer.get_model_metadata("Link")["hero_hair_color"]
    self.set_color("player_hair_color", default_shirt_color)
  
  def player_model_changed(self):
    custom_model_name = self.get_option_value("custom_player_model")
    is_casual = self.get_option_value("player_in_casual_clothes")
    if is_casual:
      prefix = "casual"
    else:
      prefix = "hero"
    
    metadata = customizer.get_model_metadata(custom_model_name)
    
    if metadata is None:
      metadata = customizer.get_model_metadata("Link")
    
    default_shirt_color = metadata["%s_shirt_color" % prefix]
    self.set_color("player_shirt_color", default_shirt_color)
    default_shirt_color = metadata["%s_pants_color" % prefix]
    self.set_color("player_pants_color", default_shirt_color)
    default_shirt_color = metadata["%s_hair_color" % prefix]
    self.set_color("player_hair_color", default_shirt_color)
  
  def set_color(self, option_name, color):
    color_button = getattr(self.ui, option_name)
    color_button.setStyleSheet("background-color: rgb(%d, %d, %d)" % tuple(color))
    self.custom_colors[option_name] = color
  
  def open_custom_color_chooser(self):
    option_name = self.sender().objectName()
    
    r, g, b = self.custom_colors[option_name]
    initial_color = QColor(r, g, b, 255)
    color = QColorDialog.getColor(initial_color, self, "Select color")
    if not color.isValid():
      return
    r = color.red()
    g = color.green()
    b = color.blue()
    self.set_color(option_name, [r, g, b])
    self.update_settings()
  
  def open_about(self):
    text = """Wind Waker Randomizer Version %s<br><br>
      Created by LagoLunatic<br><br>
      Report issues here:<br><a href=\"https://github.com/LagoLunatic/wwrando/issues\">https://github.com/LagoLunatic/wwrando/issues</a><br><br>
      Source code:<br><a href=\"https://github.com/LagoLunatic/wwrando\">https://github.com/LagoLunatic/wwrando</a>""" % VERSION
    
    self.about_dialog = QMessageBox()
    self.about_dialog.setTextFormat(Qt.TextFormat.RichText)
    self.about_dialog.setWindowTitle("Wind Waker Randomizer")
    self.about_dialog.setText(text)
    self.about_dialog.setWindowIcon(self.windowIcon())
    self.about_dialog.show()
  
  def keyPressEvent(self, event):
    if event.key() == Qt.Key_Escape:
      self.close()

class RandomizerProgressDialog(QProgressDialog):
  def __init__(self, title, description, max_val):
    QProgressDialog.__init__(self)
    self.setWindowTitle(title)
    self.setLabelText(description)
    self.setMaximum(max_val)
    self.setWindowModality(Qt.ApplicationModal)
    self.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowTitleHint)
    self.setFixedSize(self.size())
    self.setAutoReset(False)
    self.setCancelButton(None)
    self.show()

class RandomizerThread(QThread):
  update_progress = Signal(str, int)
  randomization_complete = Signal()
  randomization_failed = Signal(str)
  
  def __init__(self, randomizer):
    QThread.__init__(self)
    
    self.randomizer = randomizer
  
  def run(self):
    try:
      randomizer_generator = self.randomizer.randomize()
      while True:
        # Need to use a while loop to go through the generator instead of a for loop, as a for loop would silently exit if a StopIteration error ever happened for any reason.
        next_option_description, options_finished = next(randomizer_generator)
        if options_finished == -1:
          break
        self.update_progress.emit(next_option_description, options_finished)
    except Exception as e:
      stack_trace = traceback.format_exc()
      error_message = "Randomization failed with error:\n" + str(e) + "\n\n" + stack_trace
      self.randomization_failed.emit(error_message)
      return
    
    self.randomization_complete.emit()

class UpdateCheckerThread(QThread):
  finished_checking_for_updates = Signal(str)
  
  def run(self):
    new_version = check_for_updates()
    self.finished_checking_for_updates.emit(new_version)

# Allow yaml to load and dump OrderedDicts.
yaml.SafeLoader.add_constructor(
  yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
  lambda loader, node: OrderedDict(loader.construct_pairs(node))
)
yaml.Dumper.add_representer(
  OrderedDict,
  lambda dumper, data: dumper.represent_dict(data.items())
)
