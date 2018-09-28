
from PySide2.QtGui import *
from PySide2.QtCore import *
from PySide2.QtWidgets import *

from ui.ui_randomizer_window import Ui_MainWindow
from ui.options import OPTIONS, NON_PERMALINK_OPTIONS
from ui.update_checker import check_for_updates, LATEST_RELEASE_DOWNLOAD_PAGE_URL

import random
from collections import OrderedDict
import os
import traceback
import string
import struct
import base64

import yaml
try:
  from yaml import CDumper as Dumper
except ImportError:
  from yaml import Dumper

from randomizer import Randomizer, VERSION, TooFewProgressionLocationsError
from paths import ASSETS_PATH, SEEDGEN_PATH
import customizer
from logic.logic import Logic

class WWRandomizerWindow(QMainWindow):
  VALID_SEED_CHARACTERS = "-_'%%.%s%s" % (string.ascii_letters, string.digits)
  MAX_SEED_LENGTH = 42 # Limited by maximum length of game name in banner
  
  def __init__(self):
    super(WWRandomizerWindow, self).__init__()
    self.ui = Ui_MainWindow()
    self.ui.setupUi(self)
    
    self.custom_color_selector_buttons = OrderedDict()
    self.custom_color_selector_hex_inputs = OrderedDict()
    self.custom_colors = OrderedDict()
    self.initialize_custom_player_model_list()
    
    self.preserve_default_settings()
    
    self.cached_item_locations = Logic.load_and_parse_item_locations()
    
    self.load_settings()
    
    self.ui.clean_iso_path.editingFinished.connect(self.update_settings)
    self.ui.output_folder.editingFinished.connect(self.update_settings)
    self.ui.seed.editingFinished.connect(self.update_settings)
    self.ui.clean_iso_path_browse_button.clicked.connect(self.browse_for_clean_iso)
    self.ui.output_folder_browse_button.clicked.connect(self.browse_for_output_folder)
    self.ui.permalink.textEdited.connect(self.permalink_modified)
    
    self.ui.custom_player_model.currentIndexChanged.connect(self.custom_model_changed)
    self.ui.player_in_casual_clothes.clicked.connect(self.custom_model_changed)
    
    for option_name in OPTIONS:
      widget = getattr(self.ui, option_name)
      if isinstance(widget, QAbstractButton):
        widget.clicked.connect(self.update_settings)
      elif isinstance(widget, QComboBox):
        widget.currentIndexChanged.connect(self.update_settings)
      else:
        raise Exception("Option widget is invalid: %s" % option_name)
    
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
    seed = seed[:self.MAX_SEED_LENGTH]
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
    options["custom_colors"] = self.custom_colors
    
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
    
    text = """Randomization complete.<br><br>
      If you get stuck, check the progression spoiler log in the output folder.<br><br>
      <b>If you try to load the game in Dolphin and get a black screen, you should update to the latest development build of Dolphin:<br><a href=\"https://en.dolphin-emu.org/download/\">https://en.dolphin-emu.org/download/</a></b>"""
    
    self.complete_dialog = QMessageBox()
    self.complete_dialog.setTextFormat(Qt.TextFormat.RichText)
    self.complete_dialog.setWindowTitle("Randomization complete")
    self.complete_dialog.setText(text)
    self.complete_dialog.setWindowIcon(self.windowIcon())
    self.complete_dialog.show()
  
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
    
    any_color_changed = self.reset_color_selectors_to_model_default_colors()
    if any_color_changed:
      any_setting_changed = True
    
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
    
    self.custom_model_changed()
    if "custom_colors" in self.settings:
      custom_colors_from_settings = self.settings["custom_colors"]
      for custom_color_name in self.custom_colors:
        if custom_color_name in custom_colors_from_settings:
          self.custom_colors[custom_color_name] = custom_colors_from_settings[custom_color_name]
      for custom_color_name, color in self.custom_colors.items():
        option_name = "custom_color_" + custom_color_name
        self.set_color(option_name, color, update_preview=False)
    
    self.update_model_preview()
  
  def save_settings(self):
    with open(self.settings_path, "w") as f:
      yaml.dump(self.settings, f, default_flow_style=False, Dumper=yaml.Dumper)
  
  def update_settings(self):
    self.settings["clean_iso_path"] = self.ui.clean_iso_path.text()
    self.settings["output_folder"] = self.ui.output_folder.text()
    self.settings["seed"] = self.ui.seed.text()
    
    self.disable_invalid_cosmetic_options()
    
    for option_name in OPTIONS:
      self.settings[option_name] = self.get_option_value(option_name)
    self.settings["custom_colors"] = self.custom_colors
    
    self.save_settings()
    
    self.encode_permalink()
    
    self.update_total_progress_locations()
  
  def update_total_progress_locations(self):
    options = OrderedDict()
    for option_name in OPTIONS:
      options[option_name] = self.get_option_value(option_name)
    num_progress_locations = Logic.get_num_progression_locations_static(self.cached_item_locations, options)
    
    text = "Where Should Progress Items Appear? (Selected: %d Possible Progression Locations)" % num_progress_locations
    self.ui.groupBox.setTitle(text)
  
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
        
        value = widget.currentIndex()
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
        
        index = current_byte
        if index >= widget.count() or index < 0:
          index = 0
        value = widget.itemText(index)
        self.set_option_value(option_name, value)
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
    
    custom_model_names = customizer.get_all_custom_model_names()
    for custom_model_name in custom_model_names:
      self.ui.custom_player_model.addItem(custom_model_name)
    
    if custom_model_names:
      self.ui.custom_player_model.addItem("Random")
      self.ui.custom_player_model.addItem("Random (exclude Link)")
    else:
      self.ui.custom_player_model.setEnabled(False)
  
  def custom_model_changed(self):
    self.disable_invalid_cosmetic_options()
    
    while self.ui.custom_colors_layout.count():
      item = self.ui.custom_colors_layout.takeAt(0)
      hlayout = item.layout()
      while hlayout.count():
        item = hlayout.takeAt(0)
        widget = item.widget()
        widget.deleteLater()
    self.custom_color_selector_buttons = OrderedDict()
    self.custom_color_selector_hex_inputs = OrderedDict()
    
    custom_model_name = self.get_option_value("custom_player_model")
    metadata = customizer.get_model_metadata(custom_model_name)
    if metadata is None:
      return
    if "error_message" in metadata:
      error_message = "YAML syntax error when trying to read custom model metadata for model: %s\n\n%s" %(custom_model_name, metadata["error_message"])
      print(error_message)
      QMessageBox.critical(
        self, "Failed to load model metadata",
        error_message
      )
    
    is_casual = self.get_option_value("player_in_casual_clothes")
    if is_casual:
      prefix = "casual"
    else:
      prefix = "hero"
    
    self.custom_colors = OrderedDict()
    custom_colors = metadata.get(prefix + "_custom_colors", {})
    
    for custom_color_name, default_color in custom_colors.items():
      option_name = "custom_color_" + custom_color_name
      hlayout = QHBoxLayout()
      label_for_color_selector = QLabel(self.ui.tab_2)
      label_for_color_selector.setText("Player %s Color" % custom_color_name)
      hlayout.addWidget(label_for_color_selector)
      color_hex_code_input = QLineEdit(self.ui.tab_2)
      color_hex_code_input.setText("")
      color_hex_code_input.setObjectName(option_name + "_hex_code_input")
      color_hex_code_input.setFixedWidth(52)
      hlayout.addWidget(color_hex_code_input)
      color_selector_button = QPushButton(self.ui.tab_2)
      color_selector_button.setText("Click to set color")
      color_selector_button.setObjectName(option_name)
      hlayout.addWidget(color_selector_button)
      
      self.custom_color_selector_buttons[option_name] = color_selector_button
      color_selector_button.clicked.connect(self.open_custom_color_chooser)
      self.custom_color_selector_hex_inputs[option_name] = color_hex_code_input
      color_hex_code_input.textEdited.connect(self.custom_color_hex_code_changed)
      color_hex_code_input.editingFinished.connect(self.custom_color_hex_code_finished_editing)
      
      self.ui.custom_colors_layout.addLayout(hlayout)
      
      self.set_color(option_name, default_color, update_preview=False)
    
    self.update_model_preview()
  
  def reset_color_selectors_to_model_default_colors(self):
    custom_model_name = self.get_option_value("custom_player_model")
    is_casual = self.get_option_value("player_in_casual_clothes")
    if is_casual:
      prefix = "casual"
    else:
      prefix = "hero"
    
    metadata = customizer.get_model_metadata(custom_model_name)
    if metadata is None:
      return
    
    custom_colors = metadata.get(prefix + "_custom_colors", {})
    
    any_color_changed = False
    for custom_color_name, default_color in custom_colors.items():
      if self.custom_colors[custom_color_name] != default_color:
        any_color_changed = True
      option_name = "custom_color_" + custom_color_name
      self.set_color(option_name, default_color, update_preview=False)
    
    if any_color_changed:
      self.update_model_preview()
    
    return any_color_changed
  
  def disable_invalid_cosmetic_options(self):
    custom_model_name = self.get_option_value("custom_player_model")
    metadata = customizer.get_model_metadata(custom_model_name)
    
    if metadata is None:
      self.ui.player_in_casual_clothes.setEnabled(True)
      self.set_option_value("player_in_casual_clothes", False)
    else:
      disable_casual_clothes = metadata.get("disable_casual_clothes", False)
      if disable_casual_clothes:
        self.ui.player_in_casual_clothes.setEnabled(False)
        self.ui.player_in_casual_clothes.setChecked(False)
      else:
        self.ui.player_in_casual_clothes.setEnabled(True)
  
  def set_color(self, option_name, color, update_preview=True):
    if not (isinstance(color, list) and len(color) == 3):
      color = [255, 255, 255]
    
    assert option_name.startswith("custom_color_")
    color_name = option_name[len("custom_color_"):]
    self.custom_colors[color_name] = color
    
    color_button = self.custom_color_selector_buttons[option_name]
    hex_input = self.custom_color_selector_hex_inputs[option_name]
    if color is None:
      color_button.setStyleSheet("")
      hex_input.setText("")
    else:
      color_button.setStyleSheet("background-color: rgb(%d, %d, %d)" % tuple(color))
      hex_input.setText("%02X%02X%02X" % tuple(color))
    
    if update_preview:
      self.update_model_preview()
  
  def open_custom_color_chooser(self):
    option_name = self.sender().objectName()
    
    assert option_name.startswith("custom_color_")
    color_name = option_name[len("custom_color_"):]
    
    r, g, b = self.custom_colors[color_name]
    initial_color = QColor(r, g, b, 255)
    color = QColorDialog.getColor(initial_color, self, "Select color")
    if not color.isValid():
      return
    r = color.red()
    g = color.green()
    b = color.blue()
    self.set_color(option_name, [r, g, b])
    self.update_settings()
  
  def custom_color_hex_code_changed(self):
    option_name = self.sender().objectName()
    
    assert option_name.endswith("_hex_code_input")
    option_name = option_name[:len(option_name)-len("_hex_code_input")]
    
    assert option_name.startswith("custom_color_")
    color_name = option_name[len("custom_color_"):]
    
    text = self.sender().text().strip().lstrip("#").upper()
    if len(text) != 6 or any(c for c in text if c not in "0123456789ABCDEF"):
      return False
    r = int(text[0:2], 16)
    g = int(text[2:4], 16)
    b = int(text[4:6], 16)
    self.set_color(option_name, [r, g, b])
    self.update_settings()
    return True
  
  def custom_color_hex_code_finished_editing(self):
    is_valid_color = self.custom_color_hex_code_changed()
    if not is_valid_color:
      # If the hex code is invalid reset the text to the correct hex code for the current color.
      self.set_color(option_name, self.custom_colors[color_name])
  
  def update_model_preview(self):
    custom_model_name = self.get_option_value("custom_player_model")
    custom_model_metadata = customizer.get_model_metadata(custom_model_name)
    disable_casual_clothes = custom_model_metadata.get("disable_casual_clothes", False)
    if self.get_option_value("player_in_casual_clothes") and not disable_casual_clothes:
      prefix = "casual"
    else:
      prefix = "hero"
    
    preview_image = customizer.get_model_preview_image(custom_model_name, prefix, self.custom_colors)
    
    if preview_image is None:
      self.ui.custom_model_preview_label.hide()
      return
    
    self.ui.custom_model_preview_label.show()
    
    data = preview_image.tobytes('raw', 'BGRA')
    qimage = QImage(data, preview_image.size[0], preview_image.size[1], QImage.Format_ARGB32)
    scaled_pixmap = QPixmap.fromImage(qimage).scaled(225, 350, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    self.ui.custom_model_preview_label.setPixmap(scaled_pixmap)
  
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
  
  def closeEvent(self, event):
    # Need to wait for the update checker before exiting, or the program will crash when closing.
    self.update_checker_thread.quit()
    self.update_checker_thread.wait()
    event.accept()

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
