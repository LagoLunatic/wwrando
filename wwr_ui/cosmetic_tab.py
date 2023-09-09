from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from wwr_ui.uic.ui_cosmetic_tab import Ui_CosmeticTab

from typing import TYPE_CHECKING
if TYPE_CHECKING:
  from wwr_ui.randomizer_window import WWRandomizerWindow

import os
import yaml
import random
import colorsys
import zipfile
import shutil
import traceback

from wwrando_paths import ASSETS_PATH, CUSTOM_MODELS_PATH
import customizer
from gclib import texture_utils

class CosmeticTab(QWidget):
  def __init__(self):
    super().__init__()
    self.ui = Ui_CosmeticTab()
    self.ui.setupUi(self)
    
    self.rando_window: WWRandomizerWindow = None
    
    self.dice_icon = QIcon(os.path.join(ASSETS_PATH, "dice.png"))
    
    size_policy = self.ui.custom_model_preview_label.sizePolicy()
    size_policy.setRetainSizeWhenHidden(True)
    self.ui.custom_model_preview_label.setSizePolicy(size_policy)
    
    self.custom_color_selector_buttons = {}
    self.custom_color_reset_buttons = {}
    self.custom_colors = {}

    self.ui.install_custom_model.clicked.connect(self.install_custom_model_zip)
    self.ui.custom_player_model.currentIndexChanged.connect(self.custom_model_changed)
    self.ui.player_in_casual_clothes.toggled.connect(self.in_casual_clothes_changed)
    self.ui.randomize_all_custom_colors_together.clicked.connect(self.randomize_all_custom_colors_together)
    self.ui.randomize_all_custom_colors_separately.clicked.connect(self.randomize_all_custom_colors_separately)
    self.ui.custom_color_preset.currentIndexChanged.connect(self.color_preset_changed)
    self.ui.save_custom_color_preset.clicked.connect(self.save_custom_color_preset)
    self.ui.load_custom_color_preset.clicked.connect(self.load_custom_color_preset)
  
  def initialize_from_rando_window(self, rando_window: 'WWRandomizerWindow'):
    self.rando_window = rando_window
    
    self.initialize_custom_player_model_list()
    self.initialize_color_presets_list()
  
  def initialize_custom_player_model_list(self):
    self.ui.custom_player_model.blockSignals(True)
    
    self.ui.custom_player_model.addItem("Link")
    
    custom_model_names = customizer.get_all_custom_model_names()
    for custom_model_name in custom_model_names:
      self.ui.custom_player_model.addItem(custom_model_name)
    
    if custom_model_names:
      self.ui.custom_player_model.addItem("Random")
      self.ui.custom_player_model.addItem("Random (exclude Link)")
    else:
      self.ui.custom_player_model.setEnabled(False)
    
    self.ui.custom_player_model.blockSignals(False)
  
  def update_custom_player_model_list(self):
    self.ui.custom_player_model.clear()
    self.initialize_custom_player_model_list()
  
  def initialize_color_presets_list(self):
    self.ui.custom_color_preset.blockSignals(True)
    self.ui.custom_color_preset.addItem("Default")
    self.ui.custom_color_preset.addItem("Custom")
    self.ui.custom_color_preset.blockSignals(False)
    
    self.update_color_presets_list(reload_colors=False)
  
  def load_custom_colors_from_settings(self):
    self.reload_custom_model(update_preview=False)
    if "custom_colors" in self.rando_window.settings:
      custom_colors_from_settings = self.rando_window.settings["custom_colors"]
      
      # Only read colors into the self.custom_colors dict if they are valid colors for this model.
      for color_name, default_color in self.get_default_custom_colors_for_current_model().items():
        if color_name in custom_colors_from_settings:
          self.custom_colors[color_name] = custom_colors_from_settings[color_name]
        else:
          self.custom_colors[color_name] = default_color
      
      # Update the GUI buttons to match the custom colors (or the preset colors, if a preset is selected).
      for color_name in self.get_default_custom_colors_for_current_model():
        color = self.get_color(color_name)
        option_name = "custom_color_" + color_name
        self.set_color(option_name, color, update_preview=False, save_color_as_custom=False)
    
    if "custom_color_preset" in self.rando_window.settings:
      self.set_option_value("custom_color_preset", self.rando_window.settings["custom_color_preset"])
      self.reload_colors()
    
    self.update_model_preview()
  
  def get_option_value(self, option_name):
    # The rando window recursively searches its children for options.
    return self.rando_window.get_option_value(option_name)
  
  def set_option_value(self, option_name, new_value):
    # The rando window recursively searches its children for options.
    return self.rando_window.set_option_value(option_name, new_value)
  
  def get_color(self, color_name):
    preset_type = self.get_option_value("custom_color_preset")
    default_colors = self.get_default_custom_colors_for_current_model()
    if preset_type == "Default":
      return default_colors[color_name]
    elif preset_type == "Custom":
      if color_name in self.custom_colors:
        return self.custom_colors[color_name]
      else:
        return default_colors[color_name]
    else:
      color_presets = self.get_color_presets_for_current_model()
      if preset_type not in color_presets:
        print("Could not find color preset \"%s\" in the model's metadata.txt" % preset_type)
        return default_colors[color_name]
      
      preset = color_presets[preset_type]
      if color_name in preset:
        return preset[color_name]
      else:
        return default_colors[color_name]
  
  def set_color(self,
    option_name, color, update_preview=True,
    save_color_as_custom=True, move_other_non_custom_colors_to_custom=True
  ):
    if isinstance(color, tuple):
      color = list(color)
    if not (isinstance(color, list) and len(color) == 3):
      color = [255, 255, 255]
    
    assert option_name.startswith("custom_color_")
    color_name = option_name[len("custom_color_"):]
    
    color_button = self.custom_color_selector_buttons[option_name]
    reset_button = self.custom_color_reset_buttons[option_name]
    if color is None:
      color_button.setStyleSheet("")
      color_button.setText("")
    else:
      color_button.setText("#%02X%02X%02X" % tuple(color))
      
      r, g, b = color
      
      # Depending on the value of the background color of the button, we need to make the text color either black or white for contrast.
      h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
      if v > 0.7:
        text_color = (0, 0, 0)
      else:
        text_color = (255, 255, 255)
      
      color_button.setStyleSheet(
        "background-color: rgb(%d, %d, %d);" % (r, g, b) + \
        "color: rgb(%d, %d, %d);" % text_color,
      )
    
    default_colors = self.get_default_custom_colors_for_current_model()
    default_color = default_colors[color_name]
    if color == default_color:
      reset_button.setVisible(False)
    else:
      reset_button.setVisible(True)
    
    if save_color_as_custom:
      # First, save the color as a custom color.
      self.custom_colors[color_name] = color
      
      if self.get_option_value("custom_color_preset") != "Custom" and move_other_non_custom_colors_to_custom:
        # If the presets dropdown isn't already on Custom, we'll switch to to Custom automatically.
        
        # However, in order to prevent all the other colors besides this one from abruptly switching when we do that, we need to copy all of the currently visible default or preset colors (except this currently changing color) over to custom colors.
        for other_color_name in default_colors:
          if color_name == other_color_name:
            continue
          color = self.get_color(other_color_name)
          other_option_name = "custom_color_" + other_color_name
          self.set_color(other_option_name, color, update_preview=False, save_color_as_custom=True, move_other_non_custom_colors_to_custom=False)
        
        # Then we actually switch the presets dropdown to Custom.
        self.set_option_value("custom_color_preset", "Custom")
    
    if update_preview:
      self.update_model_preview()
  
  def open_custom_color_chooser(self):
    option_name = self.sender().objectName()
    
    assert option_name.startswith("custom_color_")
    color_name = option_name[len("custom_color_"):]
    
    r, g, b = self.get_color(color_name)
    initial_color = QColor(r, g, b, 255)
    color = QColorDialog.getColor(initial_color, self, "Select color")
    if not color.isValid():
      return
    r = color.red()
    g = color.green()
    b = color.blue()
    self.set_color(option_name, [r, g, b])
    self.rando_window.update_settings()
  
  def reset_one_custom_color(self):
    option_name, color_name = self.get_option_name_and_color_name_from_sender_object_name()
    
    default_colors = self.get_default_custom_colors_for_current_model()
    default_color = default_colors[color_name]
    
    if self.get_color(color_name) != default_color:
      self.set_color(option_name, default_color)
    
    self.rando_window.update_settings()
  
  def get_random_h_and_v_shifts_for_custom_color(self, default_color):
    r, g, b = default_color
    h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
    h = int(h*360)
    s = int(s*100)
    v = int(v*100)
    
    min_v_shift = -40
    max_v_shift = 40
    if s < 10:
      # For very unsaturated colors, we want to limit the range of value randomization to exclude results that wouldn't change anything anyway.
      # This effectively stops white and black from having a 50% chance to not change at all.
      min_v_shift = max(-40, 0-v)
      max_v_shift = min(40, 100-v)
    
    h_shift = random.randint(0, 359)
    v_shift = random.randint(min_v_shift, max_v_shift)
    
    return (h_shift, v_shift)
  
  def randomize_one_custom_color(self):
    option_name, color_name = self.get_option_name_and_color_name_from_sender_object_name()
    
    default_colors = self.get_default_custom_colors_for_current_model()
    default_color = default_colors[color_name]
    h_shift, v_shift = self.get_random_h_and_v_shifts_for_custom_color(default_color)
    color = texture_utils.hsv_shift_color(default_color, h_shift, v_shift)
    
    self.set_color(option_name, color)
    
    self.rando_window.update_settings()
  
  def randomize_all_custom_colors_together(self):
    default_colors = self.get_default_custom_colors_for_current_model()
    
    h_shift = random.randint(0, 359)
    v_shift = random.randint(-40, 40)
    for custom_color_name, default_color in default_colors.items():
      color = texture_utils.hsv_shift_color(default_color, h_shift, v_shift)
      
      option_name = "custom_color_" + custom_color_name
      self.set_color(option_name, color, update_preview=False)
    self.update_model_preview()
    
    self.rando_window.update_settings()
  
  def randomize_all_custom_colors_separately(self):
    default_colors = self.get_default_custom_colors_for_current_model()
    
    for custom_color_name, default_color in default_colors.items():
      h_shift, v_shift = self.get_random_h_and_v_shifts_for_custom_color(default_color)
      color = texture_utils.hsv_shift_color(default_color, h_shift, v_shift)
      
      option_name = "custom_color_" + custom_color_name
      self.set_color(option_name, color, update_preview=False)
    self.update_model_preview()
    
    self.rando_window.update_settings()
  
  def get_option_name_and_color_name_from_sender_object_name(self):
    object_name = self.sender().objectName()
    
    if object_name.endswith("_randomize_color"):
      option_name = object_name[:len(object_name)-len("_randomize_color")]
    elif object_name.endswith("_reset_color"):
      option_name = object_name[:len(object_name)-len("_reset_color")]
    else:
      raise Exception("Invalid custom color sender object name: %s" % object_name)
    
    assert option_name.startswith("custom_color_")
    color_name = option_name[len("custom_color_"):]
    
    return (option_name, color_name)
  
  def get_current_model_metadata_and_prefix(self):
    custom_model_name = self.get_option_value("custom_player_model")
    is_casual = self.get_option_value("player_in_casual_clothes")
    if is_casual:
      prefix = "casual"
    else:
      prefix = "hero"
    
    metadata = customizer.get_model_metadata(custom_model_name)
    if metadata is None:
      return ({}, prefix)
    return (metadata, prefix)
  
  def get_default_custom_colors_for_current_model(self):
    metadata, prefix = self.get_current_model_metadata_and_prefix()
    default_colors = metadata.get(prefix + "_custom_colors", {})
    return default_colors
  
  def get_color_presets_for_current_model(self):
    metadata, prefix = self.get_current_model_metadata_and_prefix()
    color_presets = metadata.get(prefix + "_color_presets", {})
    return color_presets
  
  def update_model_preview(self):
    custom_model_name = self.get_option_value("custom_player_model")
    custom_model_metadata = customizer.get_model_metadata(custom_model_name)
    disable_casual_clothes = custom_model_metadata.get("disable_casual_clothes", False)
    if self.get_option_value("player_in_casual_clothes") and not disable_casual_clothes:
      prefix = "casual"
    else:
      prefix = "hero"
    
    colors = {}
    for color_name in self.get_default_custom_colors_for_current_model():
      colors[color_name] = self.get_color(color_name)
    
    try:
      preview_image = customizer.get_model_preview_image(custom_model_name, prefix, colors)
    except Exception as e:
      stack_trace = traceback.format_exc()
      error_message = "Failed to load model preview image for model %s.\nError:\n" % (custom_model_name) + str(e) + "\n\n" + stack_trace
      print(error_message)
      QMessageBox.critical(
        self, "Failed to load model preview",
        error_message
      )
      return
    
    if preview_image is None:
      self.ui.custom_model_preview_label.hide()
      return
    
    self.ui.custom_model_preview_label.show()
    
    data = preview_image.tobytes('raw', 'BGRA')
    qimage = QImage(data, preview_image.width, preview_image.height, QImage.Format_ARGB32)
    scaled_pixmap = QPixmap.fromImage(qimage).scaled(225, 350, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    self.ui.custom_model_preview_label.setPixmap(scaled_pixmap)

  def install_custom_model_zip(self):
    try:
      zip_path, selected_filter = QFileDialog.getOpenFileName(self, "Select custom model zip file", CUSTOM_MODELS_PATH, "Zip Files (*.zip)")
      if not zip_path:
        return
      zip = zipfile.ZipFile(zip_path)
      try:
        top_level_dir = zipfile.Path(zip, zip.namelist()[0])
      except IndexError:
        QMessageBox.critical(
          self, "Incorrect archive structure",
          "Archive is empty"
        )
        return
      # Verify contents
      if top_level_dir.joinpath("models").is_dir():
        model_path = top_level_dir.joinpath("models")
        model_dir_list = list(model_path.iterdir())
        is_model_pack = True
      else:
        model_dir_list = [top_level_dir]
        is_model_pack = False
      expected_files = ["Link.arc", "metadata.txt"]
      for model_dir in model_dir_list:
        for f in expected_files:
          if not model_dir.joinpath(f).exists():
            QMessageBox.critical(
              self, "Incorrect archive structure",
              "Missing file: %s" % model_dir.joinpath(f).at
            )
            return
      zip.extractall(CUSTOM_MODELS_PATH)
      if not is_model_pack:
        install_result = model_dir_list[0].name
      else:
        for model_dir in model_dir_list:
          shutil.move(os.path.join(CUSTOM_MODELS_PATH, model_dir.at), os.path.join(CUSTOM_MODELS_PATH, model_dir.name))
        shutil.rmtree(os.path.join(CUSTOM_MODELS_PATH, top_level_dir.name))
        install_result = "%s models" % len(model_dir_list)
      QMessageBox.information(
        self, "Installation complete",
        "%s installed successfully." % install_result
      )
      self.update_custom_player_model_list()
      self.set_option_value("custom_player_model", model_dir_list[0].name)
    except zipfile.BadZipfile:
      stack_trace = traceback.format_exc()
      print(stack_trace)
      QMessageBox.critical(
        self, "Failed to unpack model archive",
        stack_trace
      )
  
  def update_color_presets_list(self, reload_colors=True):
    # Temporarily prevent the preset changing from regenerating the preview image since we'll be changing it several times in this function.
    self.ui.custom_color_preset.blockSignals(True)
    
    # Keep track of what the value of the presets dropdown was.
    prev_selected_preset_type = self.get_option_value("custom_color_preset")
    
    # Remove everything except "Default" and "Custom".
    for i in reversed(range(self.ui.custom_color_preset.count())):
      if self.ui.custom_color_preset.itemText(i) in ["Default", "Custom"]:
        continue
      self.ui.custom_color_preset.removeItem(i)
    
    # Add the presets specific to this model.
    presets = self.get_color_presets_for_current_model()
    for preset_name in presets:
      if preset_name in ["Default", "Custom"]:
        QMessageBox.warning(self, "Invalid color preset name", "The selected player model has a preset named \"%s\", which is a reserved name. This preset will be ignored." % preset_name)
        continue
      self.ui.custom_color_preset.addItem(preset_name)
    
    # If the new model has a preset with the same name as the selected preset for the previous model, set the dropdown back to that value.
    # This is so switching between hero/casual doesn't reset the preset you have selected, in cases where the same preset is specified for both hero and casual.
    # (This has the side effect of preserving the preset even across entirely different models if they happen to have presets of the same name.)
    if prev_selected_preset_type in presets:
      self.set_option_value("custom_color_preset", prev_selected_preset_type)
    else:
      # Otherwise switch to Default, since the Casual colors get cleared on model switch anyway.
      self.set_option_value("custom_color_preset", "Default")
    
    if reload_colors:
      # Because we blocked signals, we manually reload the color buttons, without generating the preview.
      self.reload_colors(update_preview=False)
    
    self.ui.custom_color_preset.blockSignals(False)
  
  def reload_custom_model(self, update_preview=True):
    self.disable_invalid_cosmetic_options()
    
    self.clear_layout_recursive(self.ui.custom_colors_layout)
    self.custom_color_selector_buttons = {}
    self.custom_color_selector_hex_inputs = {}
    self.custom_color_reset_buttons = {}
    
    custom_model_name = self.get_option_value("custom_player_model")
    metadata = customizer.get_model_metadata(custom_model_name)
    if metadata is None:
      return
    if "error_message" in metadata:
      error_message = "Syntax error when trying to read metadata.txt for custom model: %s\n\n%s" %(custom_model_name, metadata["error_message"])
      print(error_message)
      QMessageBox.critical(
        self, "Failed to load model metadata",
        error_message
      )
    
    model_author = metadata.get("author", None)
    model_comment = metadata.get("comment", None)
    comment_lines = []
    if model_author:
      comment_lines.append("Author: %s" % model_author)
    if model_comment:
      comment_lines.append("Author's comment: %s" % model_comment)
    self.ui.custom_model_comment.setText("\n".join(comment_lines))
    if len(comment_lines) <= 0:
      self.ui.custom_model_comment.hide()
    else:
      self.ui.custom_model_comment.show()
    
    # Allow customizing the text of the Casual Clothes checkbox.
    casual_clothes_option_text = str(metadata.get("casual_clothes_option_text", "Casual Clothes"))
    if len(casual_clothes_option_text) > 28:
      # 28 character maximum length.
      casual_clothes_option_text = casual_clothes_option_text[:28]
    self.ui.player_in_casual_clothes.setText(casual_clothes_option_text)
    
    is_casual = self.get_option_value("player_in_casual_clothes")
    if is_casual:
      prefix = "casual"
    else:
      prefix = "hero"
    
    self.custom_colors = {}
    custom_colors = metadata.get(prefix + "_custom_colors", {})
    
    curr_row_layout = None
    i = 0
    for custom_color_name, default_color in custom_colors.items():
      if i % 2 == 0:
        curr_row_layout = QHBoxLayout()
        self.ui.custom_colors_layout.addLayout(curr_row_layout)
      color_layout = self.make_layout_for_one_custom_color(custom_color_name, default_color)
      curr_row_layout.addLayout(color_layout)
      i += 1
    if i % 2 == 1:
      curr_row_layout.addWidget(QWidget())
    
    if len(custom_colors) == 0:
      # Need to push the preview over to the right even when there are no colors to do it, so add a spacer.
      hlayout = QHBoxLayout()
      hspacer = QSpacerItem(20, 40, QSizePolicy.Expanding, QSizePolicy.Minimum)
      hlayout.addItem(hspacer)
      self.ui.custom_colors_layout.addLayout(hlayout)
    
    self.update_color_presets_list()
    
    if update_preview:
      self.update_model_preview()
  
  def make_layout_for_one_custom_color(self, custom_color_name, default_color):
    option_name = "custom_color_" + custom_color_name
    hlayout = QHBoxLayout()
    hlayout.setSpacing(0)
    label_for_color_selector = QLabel(self)
    label_for_color_selector.setTextFormat(Qt.TextFormat.PlainText)
    label_for_color_selector.setText(custom_color_name)
    hlayout.addWidget(label_for_color_selector)
    
    color_selector_button = QPushButton(self)
    color_selector_button.setText("")
    color_selector_button.setObjectName(option_name)
    color_selector_button.setFixedWidth(QFontMetrics(QFont()).horizontalAdvance("#CCCCCC")+5)
    hlayout.addWidget(color_selector_button)
    
    color_randomize_button = QPushButton(self)
    color_randomize_button.setIcon(self.dice_icon)
    color_randomize_button.setObjectName(option_name + "_randomize_color")
    color_randomize_button.setFixedWidth(32)
    hlayout.addWidget(color_randomize_button)
    
    color_reset_button = QPushButton(self)
    color_reset_button.setText("X")
    color_reset_button.setObjectName(option_name + "_reset_color")
    color_reset_button.setFixedWidth(QFontMetrics(QFont()).horizontalAdvance("X")+11)
    size_policy = color_reset_button.sizePolicy()
    size_policy.setRetainSizeWhenHidden(True)
    color_reset_button.setSizePolicy(size_policy)
    color_reset_button.setVisible(False)
    hlayout.addWidget(color_reset_button)
    
    self.custom_color_selector_buttons[option_name] = color_selector_button
    color_selector_button.clicked.connect(self.open_custom_color_chooser)
    color_randomize_button.clicked.connect(self.randomize_one_custom_color)
    color_reset_button.clicked.connect(self.reset_one_custom_color)
    self.custom_color_reset_buttons[option_name] = color_reset_button
    
    self.set_color(option_name, default_color, update_preview=False, save_color_as_custom=False)
    
    return hlayout
  
  def reload_colors(self, update_preview=True):
    for color_name in self.get_default_custom_colors_for_current_model():
      color = self.get_color(color_name)
      self.set_color("custom_color_" + color_name, color, update_preview=False, save_color_as_custom=False)
    
    if update_preview:
      self.update_model_preview()
  
  def custom_model_changed(self, index):
    self.reload_custom_model()
  
  def in_casual_clothes_changed(self, checked):
    self.reload_custom_model()
  
  def color_preset_changed(self, index):
    self.reload_colors()
  
  def reset_color_selectors_to_model_default_colors(self):
    default_colors = self.get_default_custom_colors_for_current_model()
    
    any_color_changed = False
    for custom_color_name, default_color in default_colors.items():
      if custom_color_name in self.custom_colors and self.custom_colors[custom_color_name] != default_color:
        any_color_changed = True
      option_name = "custom_color_" + custom_color_name
      self.set_color(option_name, default_color, update_preview=False, save_color_as_custom=False)
    
    if any_color_changed:
      self.update_model_preview()
    
    return any_color_changed
  
  def save_custom_color_preset(self):
    preset_path, selected_filter = QFileDialog.getSaveFileName(self, "Save color preset", None, "Text Files (*.txt)")
    if not preset_path:
      return
    
    hex_custom_colors = {}
    for color_name, color_tuple in self.custom_colors.items():
      hex_custom_colors[color_name] = "0x%02X%02X%02X" % tuple(color_tuple)
    
    custom_preset = {}
    custom_preset["model_name"] = self.get_option_value("custom_player_model")
    custom_preset["colors"] = hex_custom_colors
    
    with open(preset_path, "w") as f:
      yaml.dump(custom_preset, f, default_flow_style=False, sort_keys=False)
    
    QMessageBox.information(
      self, "Custom colors saved",
      f"Your custom colors have been saved to the file:\n{preset_path}"
    )
  
  def load_custom_color_preset(self):
    preset_path, selected_filter = QFileDialog.getOpenFileName(self, "Load color preset", None, "Text Files (*.txt)")
    if not preset_path:
      return
    
    with open(preset_path) as f:
      custom_preset = yaml.safe_load(f)
    
    model_name = custom_preset["model_name"]
    custom_colors = custom_preset["colors"]
    
    custom_model_names = customizer.get_all_custom_model_names()
    
    if model_name not in custom_model_names:
      QMessageBox.critical(
        self, "Failed to load custom color preset",
        f"The color preset you loaded is for the custom model '{model_name}'.\n"
        "You do not have this model installed."
      )
      return
    
    if self.get_option_value("custom_player_model") != model_name:
      self.set_option_value("custom_player_model", model_name)
    
    custom_colors_to_set = {}
    
    # Only read colors if they are valid colors for this model.
    found_any_valid = False
    for color_name, default_color in self.get_default_custom_colors_for_current_model().items():
      if color_name not in custom_colors:
        custom_colors_to_set[color_name] = default_color
        continue
      hex_color = custom_colors[color_name]
      try:
        custom_colors_to_set[color_name] = customizer.parse_hex_color(hex_color, False)
        found_any_valid = True
      except customizer.InvalidColorError:
        error_message = "Custom color \"%s\" is invalid: \"%s\"" % (color_name, repr(hex_color))
        print(error_message)
        QMessageBox.critical(
          self, "Failed to load custom color preset",
          error_message
        )
        return
    
    if not found_any_valid:
      QMessageBox.warning(
        self, "Found no colors",
        "The preset didn't contain any colors that are valid for this model."
      )
      return
    
    for color_name, color_tuple in custom_colors_to_set.items():
      self.set_color(f"custom_color_{color_name}", color_tuple, update_preview=False)
    
    self.update_model_preview()
  
  def clear_layout_recursive(self, layout: QLayout):
    while layout.count():
      item = layout.takeAt(0)
      widget = item.widget()
      if widget:
        widget.deleteLater()
      sublayout = item.layout()
      if sublayout:
        self.clear_layout_recursive(sublayout)
  
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
    
    # Grey out the custom voice disable option for models that don't have custom voice files.
    if custom_model_name == "Random" or custom_model_name == "Random (exclude Link)":
      self.ui.disable_custom_player_voice.setEnabled(True)
    else:
      custom_model_path = os.path.join(CUSTOM_MODELS_PATH, custom_model_name)
      jaiinit_aaf_path = os.path.join(custom_model_path, "sound", "JaiInit.aaf")
      voice_aw_path = os.path.join(custom_model_path, "sound", "voice_0.aw")
      if os.path.isfile(jaiinit_aaf_path) and os.path.isfile(voice_aw_path):
        self.ui.disable_custom_player_voice.setEnabled(True)
      else:
        self.ui.disable_custom_player_voice.setEnabled(False)
    
    # Grey out the custom items disable option for Link, but not any other models (since we don't know which have custom items).
    if custom_model_name == "Link":
      self.ui.disable_custom_player_items.setEnabled(False)
    else:
      self.ui.disable_custom_player_items.setEnabled(True)
    
    if custom_model_name == "Random" or custom_model_name == "Random (exclude Link)":
      self.ui.save_custom_color_preset.setEnabled(False)
    else:
      self.ui.save_custom_color_preset.setEnabled(True)
  