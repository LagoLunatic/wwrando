from qtpy.QtGui import *
from qtpy.QtCore import *
from qtpy.QtWidgets import *
from wwr_ui.qt_init import load_ui_file

from wwr_ui.update_checker import check_for_updates, LATEST_RELEASE_DOWNLOAD_PAGE_URL
from wwr_ui.inventory import INVENTORY_ITEMS, DEFAULT_STARTING_ITEMS, DEFAULT_RANDOMIZED_ITEMS

import os
import sys
import traceback
from enum import StrEnum
from collections import Counter

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError
yaml_dumper = YAML(typ="rt") # Use RoundTripDumper for pretty-formatted dumps.

from options.wwrando_options import Options, SwordMode
from randomizer import WWRandomizer, TooFewProgressionLocationsError, InvalidCleanISOError, PermalinkWrongVersionError, PermalinkWrongCommitError
from version import VERSION
from wwrando_paths import SETTINGS_PATH, ASSETS_PATH, IS_RUNNING_FROM_SOURCE, RANDO_ROOT_PATH
from seedgen import seedgen
from logic.logic import Logic

import typing
from typing import TYPE_CHECKING, Type, TypeVar
T = TypeVar('T')

if os.environ["QT_API"] == "pyside6":
  from wwr_ui.uic.ui_randomizer_window import Ui_MainWindow
else:
  Ui_MainWindow = load_ui_file(os.path.join(RANDO_ROOT_PATH, "wwr_ui", "randomizer_window.ui"))

class WWRandomizerWindow(QMainWindow):
  def __init__(self, cmd_line_args):
    super(WWRandomizerWindow, self).__init__()
    self.ui = Ui_MainWindow()
    self.ui.setupUi(self)
    
    self.ui.tab_player_customization.initialize_from_rando_window(self)
    
    self.randomizer_thread = None
    
    self.cmd_line_args = cmd_line_args
    self.profiling = self.cmd_line_args.profile
    self.auto_seed = self.cmd_line_args.autoseed
    
    self.ui.add_gear.clicked.connect(self.add_to_starting_gear)
    self.randomized_gear_model = QStringListModel()
    self.randomized_gear_model.setStringList(DEFAULT_RANDOMIZED_ITEMS.copy())
    
    self.filtered_rgear = ModelFilterOut()
    self.filtered_rgear.setSourceModel(self.randomized_gear_model)
    
    self.ui.randomized_gear.setModel(self.filtered_rgear)
    self.ui.remove_gear.clicked.connect(self.remove_from_starting_gear)
    self.starting_gear_model = QStringListModel()
    self.starting_gear_model.setStringList(DEFAULT_STARTING_ITEMS.copy())
    self.ui.starting_gear.setModel(self.starting_gear_model)
    
    # We use an Options instance to represent the defaults instead of directly accessing each options default so that
    # default_factory works correctly.
    self.default_options = Options()
    
    self.initialize_option_widgets()
    
    # Set the default custom_colors dict after initializing the widgets just to be safe.
    # We want to be sure the selected model and preset are the default.
    self.default_options.custom_colors = self.ui.tab_player_customization.get_all_colors()
    
    self.load_settings()
    
    self.cached_item_locations = Logic.load_and_parse_item_locations()
    
    self.ui.starting_pohs.valueChanged.connect(self.update_health_label)
    self.ui.starting_hcs.valueChanged.connect(self.update_health_label)
    
    self.ui.clean_iso_path.editingFinished.connect(self.update_settings)
    self.ui.output_folder.editingFinished.connect(self.update_settings)
    self.ui.seed.editingFinished.connect(self.update_settings)
    self.ui.clean_iso_path_browse_button.clicked.connect(self.browse_for_clean_iso)
    self.ui.output_folder_browse_button.clicked.connect(self.browse_for_output_folder)
    self.ui.permalink.textEdited.connect(self.permalink_modified)
    
    self.ui.label_for_clean_iso_path.linkActivated.connect(self.show_clean_iso_explanation)
    
    for option in Options.all():
      if option.name == "custom_colors":
        continue
      widget = self.findChild(QWidget, option.name)
      label_for_option = self.findChild(QLabel, "label_for_" + option.name)
      
      # Connect signals to detect when the user changes each option.
      if isinstance(widget, QAbstractButton):
        widget.clicked.connect(self.update_settings)
      elif isinstance(widget, QComboBox):
        widget.currentIndexChanged.connect(self.update_settings)
        if option.choice_descriptions:
          widget.highlighted.connect(self.update_choice_highlighted_description)
      elif isinstance(widget, QListView):
        pass
      elif isinstance(widget, QSpinBox):
        widget.valueChanged.connect(self.update_settings)
      else:
        raise Exception("Option widget is invalid: %s" % option.name)
      
      # Install event filters to detect when the user hovers over each option.
      widget.installEventFilter(self)
      if label_for_option:
        label_for_option.installEventFilter(self)
    
    self.ui.generate_seed_button.clicked.connect(self.generate_seed)
    
    self.ui.randomize_button.clicked.connect(self.randomize)
    self.ui.reset_settings_to_default.clicked.connect(self.reset_settings_to_default)
    self.ui.about_button.clicked.connect(self.open_about)
    
    self.set_option_description(None)
    
    self.update_settings()
    self.update_health_label()
    
    self.setWindowTitle("Wind Waker Randomizer %s" % VERSION)
    
    icon_path = os.path.join(ASSETS_PATH, "icon.ico")
    self.setWindowIcon(QIcon(icon_path))
    
    if self.cmd_line_args.seed:
      self.ui.seed.setText(self.cmd_line_args.seed)
    
    if self.auto_seed:
      self.generate_seed()
    
    if self.cmd_line_args.permalink:
      self.ui.permalink.setText(self.cmd_line_args.permalink)
      self.permalink_modified()
    
    self.show()
    
    if not IS_RUNNING_FROM_SOURCE:
      self.update_checker_thread = UpdateCheckerThread()
      self.update_checker_thread.finished_checking_for_updates.connect(self.show_update_check_results)
      self.update_checker_thread.start()
    else:
      self.ui.update_checker_label.setText("(Running from source, skipping release update check.)")
  
  def generate_seed(self):
    seed = seedgen.make_random_seed_name()
    seed = WWRandomizer.sanitize_seed(seed)
    
    self.settings["seed"] = seed
    self.ui.seed.setText(seed)
    self.update_settings()
  
  def append_row(self, model: QAbstractListModel, value):
    model.insertRow(model.rowCount())
    newrow = model.index(model.rowCount() - 1, 0)
    model.setData(newrow, value)
  
  def move_selected_rows(self, source: QListView, dest: QListView):
    selection = source.selectionModel().selectedIndexes()
    # Remove starting from the last so the previous indices remain valid
    selection.sort(reverse = True, key = lambda x: x.row())
    for item in selection:
      value = item.data()
      source.model().removeRow(item.row())
      self.append_row(dest.model(), value)
  
  def add_to_starting_gear(self):
    self.move_selected_rows(self.ui.randomized_gear, self.ui.starting_gear)
    self.ui.starting_gear.model().sort(0)
    self.update_settings()
  
  def remove_from_starting_gear(self):
    self.move_selected_rows(self.ui.starting_gear, self.ui.randomized_gear)
    self.ui.randomized_gear.model().sourceModel().sort(0)
    self.update_settings()
  
  def update_health_label(self):
    pohs = self.ui.starting_pohs.value()
    hcs = self.ui.starting_hcs.value() * 4
    
    health = hcs + pohs
    pieces = health % 4
    
    text = "Current Starting Health: %d hearts" % (health // 4) # full hearts
    
    if pieces != 0:
      if pieces == 1: # grammar check
        text += " and 1 piece"
      else:
        text += " and %d pieces" % pieces
    
    self.ui.current_health.setText(text)
  
  def randomize(self):
    clean_iso_path = self.settings["clean_iso_path"].strip()
    output_folder = self.settings["output_folder"].strip()
    self.settings["clean_iso_path"] = clean_iso_path
    self.settings["output_folder"] = output_folder
    self.ui.clean_iso_path.setText(clean_iso_path)
    self.ui.output_folder.setText(output_folder)
    
    if not self.settings["dry_run"] and not os.path.isfile(clean_iso_path):
      QMessageBox.warning(self, "Vanilla ISO path not specified", "Must specify path to your vanilla Wind Waker ISO (North American version).")
      return
    if not os.path.isdir(output_folder):
      QMessageBox.warning(self, "No output folder specified", "Must specify a valid output folder for the randomized files.")
      return
    
    seed = self.settings["seed"]
    seed = WWRandomizer.sanitize_seed(seed)
    
    if not seed:
      self.generate_seed()
      seed = self.settings["seed"]
    
    self.settings["seed"] = seed
    self.ui.seed.setText(seed)
    self.update_settings()
    
    options = self.get_all_options_from_widget_values()
    
    options.custom_colors = self.ui.tab_player_customization.get_all_colors()
    
    self.progress_dialog = RandomizerProgressDialog(self, "Randomizing", "Initializing...")
    
    try:
      rando = WWRandomizer(seed, clean_iso_path, output_folder, options, cmd_line_args=self.cmd_line_args)
    except (TooFewProgressionLocationsError, InvalidCleanISOError) as e:
      error_message = str(e)
      self.randomization_failed(error_message)
      return
    except Exception as e:
      stack_trace = traceback.format_exc()
      error_message = "Randomization failed with error:\n" + str(e) + "\n\n" + stack_trace
      self.randomization_failed(error_message)
      return
    
    self.progress_dialog.setMaximum(rando.get_max_progress_length())
    self.randomizer_thread = RandomizerThread(rando, profiling=self.profiling)
    self.randomizer_thread.update_progress.connect(self.update_progress_dialog)
    self.randomizer_thread.randomization_complete.connect(self.randomization_complete)
    self.randomizer_thread.randomization_failed.connect(self.randomization_failed)
    self.randomizer_thread.start()
  
  def update_progress_dialog(self, next_option_description, progress_completed):
    if progress_completed > self.progress_dialog.maximum():
      # This shouldn't happen if the max estimate was correct, but if it did just snap the progress bar to the end.
      # Without this, the progress going past the max would cause the bar to get stuck at the last valid position.
      progress_completed = self.progress_dialog.maximum()
    self.progress_dialog.setLabelText(next_option_description)
    self.progress_dialog.setValue(progress_completed)
  
  def randomization_complete(self):
    self.progress_dialog.reset()
    
    text = """Randomization complete.<br><br>
      If you get stuck, check the progression spoiler log in the output folder."""
    if self.randomizer_thread.randomizer.dry_run:
      text = """Randomization complete.<br><br>
      Note: You chose to do a dry run, meaning <u>no playable ISO was generated</u>.<br>
      To actually play the randomizer, uncheck the Dry Run checkbox in the Advanced Options tab, then click Randomize again."""
    
    self.randomizer_thread = None
    
    self.complete_dialog = QMessageBox()
    self.complete_dialog.setTextFormat(Qt.TextFormat.RichText)
    self.complete_dialog.setWindowTitle("Randomization complete")
    self.complete_dialog.setText(text)
    self.complete_dialog.setWindowIcon(self.windowIcon())
    self.complete_dialog.show()
  
  def randomization_failed(self, error_message):
    self.progress_dialog.reset()
    
    if self.randomizer_thread is not None:
      self.randomizer_thread.terminate()
      try:
        self.randomizer_thread.randomizer.write_error_log(error_message)
      except Exception as e:
        # If an error happened when writing the error log just print it and then ignore it.
        stack_trace = traceback.format_exc()
        other_error_message = "Failed to write error log:\n" + str(e) + "\n\n" + stack_trace
        print(other_error_message)
    
    self.randomizer_thread = None
    
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
  
  def initialize_option_widgets(self):
    for option in Options.all():
      if option.name == "custom_colors":
        continue
      widget = self.findChild(QWidget, option.name)
      if isinstance(widget, QAbstractButton):
        assert issubclass(option.type, bool)
      elif isinstance(widget, QComboBox):
        assert issubclass(option.type, str)
        if widget.objectName() not in ["custom_player_model", "custom_color_preset"]:
          assert issubclass(option.type, StrEnum)
          assert widget.count() == len(option.type)
          for i, enum_value in enumerate(option.type):
            # Make sure the text of each choice in the combobox matches the string enum value of the option.
            widget.setItemText(i, enum_value.value)
      elif isinstance(widget, QListView):
        assert issubclass(typing.get_origin(option.type) or option.type, list)
      elif isinstance(widget, QSpinBox):
        assert issubclass(option.type, int)
        widget.setMinimum(option.minimum)
        widget.setMaximum(option.maximum)
      else:
        raise Exception("Option widget is invalid: %s" % option.name)
      
      # Make sure the initial values of all the GUI widgets match the defaults for the options.
      default_value = self.default_options[option.name]
      self.set_option_value(option.name, default_value)
  
  def reset_settings_to_default(self):
    options = self.get_all_options_from_widget_values()
    if options == self.default_options:
      QMessageBox.information(self,
        "Settings already default",
        "You already have all the default randomization settings."
      )
      return
    
    for option in Options.all():
      if option.name == "custom_colors":
        self.ui.tab_player_customization.reset_color_selectors_to_model_default_colors()
        continue
      default_value = self.default_options[option.name]
      current_value = self.get_option_value(option.name)
      if default_value != current_value:
        self.set_option_value(option.name, default_value)
    
    self.update_settings()
  
  def load_settings(self):
    if os.path.isfile(SETTINGS_PATH):
      try:
        with open(SETTINGS_PATH) as f:
          self.settings = yaml_dumper.load(f)
      except YAMLError as e:
        QMessageBox.critical(
          self, "Invalid settings.txt",
          "Failed to load settings from settings.txt.\n\n"
          "Remove the corrupted settings.txt before trying to load the randomizer again.\n"
        )
        sys.exit(1)
      if self.settings is None:
        self.settings = {}
    else:
      self.settings = {}
    
    if "clean_iso_path" in self.settings:
      self.ui.clean_iso_path.setText(self.settings["clean_iso_path"])
    if "output_folder" in self.settings:
      self.ui.output_folder.setText(self.settings["output_folder"])
    if "seed" in self.settings:
      self.ui.seed.setText(self.settings["seed"])
    
    for option in Options.all():
      if option.name in self.settings:
        if option.name in ["custom_color_preset", "custom_colors"]:
          # Colors and color presents not loaded yet, handle this later
          continue
        self.set_option_value(option.name, self.settings[option.name])
    
    self.ui.tab_player_customization.load_custom_colors_from_settings()
  
  def save_settings(self):
    with open(SETTINGS_PATH, "w") as f:
      yaml_dumper.dump(self.settings, f)
  
  def update_settings(self):
    self.settings["clean_iso_path"] = self.ui.clean_iso_path.text()
    self.settings["output_folder"] = self.ui.output_folder.text()
    self.settings["seed"] = self.ui.seed.text()
    
    self.ensure_valid_combination_of_options()
    self.ui.tab_player_customization.disable_invalid_cosmetic_options()
    
    for option in Options.all():
      self.settings[option.name] = self.get_option_value(option.name)
    
    self.save_settings()
    
    self.encode_permalink()
    
    self.update_total_progress_locations()
  
  def update_total_progress_locations(self):
    options = self.get_all_options_from_widget_values()
    num_progress_locations = Logic.get_num_progression_locations_static(self.cached_item_locations, options)
    
    text = "Progression Locations: Where Should Progress Items Be Placed? " \
      f"(Selected: {num_progress_locations} Locations Available)"
    self.ui.progression_locations_groupbox.setTitle(text)
  
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
    seed = WWRandomizer.sanitize_seed(seed)
    if not seed:
      self.ui.permalink.setText("")
      return
    
    options = self.get_all_options_from_widget_values()
    base64_encoded_permalink = WWRandomizer.encode_permalink(seed, options)
    self.ui.permalink.setText(base64_encoded_permalink)
  
  def decode_permalink(self, base64_encoded_permalink):
    base64_encoded_permalink = base64_encoded_permalink.strip()
    if not base64_encoded_permalink:
      # Empty
      return
    
    options = self.get_all_options_from_widget_values()
    
    try:
      seed, options = WWRandomizer.decode_permalink(base64_encoded_permalink, options)
    except PermalinkWrongVersionError as e:
      message = str(e)
      QMessageBox.critical(self, "Invalid permalink", message)
      return
    except PermalinkWrongCommitError as e:
      message = str(e)
      message += "\n\nBecause only the commit is different, the permalink may or may not still be compatible. Would you like to try loading this permalink anyway?"
      response = QMessageBox.question(
        self, "Potentially invalid permalink",
        message,
        QMessageBox.Cancel | QMessageBox.Yes,
        QMessageBox.Cancel
      )
      if response == QMessageBox.Cancel:
        return
      
      options = self.get_all_options_from_widget_values()
      seed, options = WWRandomizer.decode_permalink(base64_encoded_permalink, options, allow_different_commit=True)
    
    self.ui.seed.setText(seed)
    for option in Options.all():
      if option.permalink:
        self.set_option_value(option.name, options[option.name])
    
    self.update_settings()
  
  def show_clean_iso_explanation(self):
    QMessageBox.information(
      self, "Vanilla Wind Waker ISO",
      "To use the randomizer, you need to have a copy of the North American GameCube version of The Legend of Zelda: The Wind Waker.\n\n" +
      "The European and Japanese versions of Wind Waker are not supported.\nWind Waker HD is also not supported.\n\n" +
      "The ISO should ideally be a vanilla/unmodified copy of the game to guarantee the randomizer works with no " +
      "conflicts, but Wind Waker mods that do not conflict with the randomizer can also be used."
    )
  
  def browse_for_clean_iso(self):
    if self.settings["clean_iso_path"] and os.path.isfile(self.settings["clean_iso_path"]):
      default_dir = os.path.dirname(self.settings["clean_iso_path"])
    else:
      default_dir = None
    
    clean_iso_path, selected_filter = QFileDialog.getOpenFileName(self, "Select vanilla Wind Waker ISO", default_dir, "GC ISO Files (*.iso *.gcm)")
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
  
  def get_option_from_widget(self, widget: QObject):
    option_name = widget.objectName().removeprefix("label_for_")
    if option_name in Options.by_name():
      return Options.by_name()[option_name]
    else:
      return None
  
  def eventFilter(self, target: QObject, event: QEvent):
    if event.type() == QEvent.Type.Enter:
      option = self.get_option_from_widget(target)
      if option:
        self.set_option_description(option.description)
      else:
        self.set_option_description(None)
      return True
    elif event.type() == QEvent.Type.Leave:
      self.set_option_description(None)
      return True
    
    return QMainWindow.eventFilter(self, target, event)
  
  def update_choice_highlighted_description(self, index):
    option = self.get_option_from_widget(self.sender())
    assert option
    assert issubclass(option.type, StrEnum)
    enum_values = [val for val in option.type]
    highlighted_value = enum_values[index]
    
    if highlighted_value in option.choice_descriptions:
      desc = option.choice_descriptions[highlighted_value]
    else:
      desc = None
    
    self.set_option_description(desc)
  
  def get_option_value(self, option_name):
    if option_name == "custom_colors":
      return self.ui.tab_player_customization.get_all_colors()
    
    widget = self.findChild(QWidget, option_name)
    option = Options.by_name()[option_name]
    if isinstance(widget, QCheckBox) or isinstance(widget, QRadioButton):
      return widget.isChecked()
    elif isinstance(widget, QComboBox):
      if issubclass(option.type, StrEnum):
        index = widget.currentIndex()
        enum_values = [val for val in option.type]
        curr_value = enum_values[index]
        return curr_value
      elif issubclass(option.type, str):
        return widget.itemText(widget.currentIndex())
      else:
        print(f"Invalid type for combobox option: {option.type}")
    elif isinstance(widget, QSpinBox):
      return widget.value()
    elif isinstance(widget, QListView):
      if widget.model() is None:
        return []
      model = widget.model()
      if isinstance(model, ModelFilterOut):
        model = model.sourceModel()
      model.sort(0)
      return [model.data(model.index(i, 0), Qt.ItemDataRole.DisplayRole) for i in range(model.rowCount())]
    else:
      print("Option widget is invalid: %s" % option_name)
    
    return None
  
  def set_option_value(self, option_name, new_value):
    if option_name == "custom_colors":
      print("Setting custom_colors via set_option_value not supported")
      return
    
    widget = self.findChild(QWidget, option_name)
    option = Options.by_name()[option_name]
    if isinstance(widget, QCheckBox) or isinstance(widget, QRadioButton):
      widget.setChecked(bool(new_value))
    elif isinstance(widget, QComboBox):
      index_of_value = None
      if issubclass(option.type, StrEnum) and isinstance(new_value, option.type):
        enum_values = [val for val in option.type]
        index_of_value = enum_values.index(new_value)
      elif isinstance(new_value, str):
        index_of_value = None
        for i in range(widget.count()):
          text = widget.itemText(i)
          if text == new_value:
            index_of_value = i
            break
      else:
        print(f"Invalid type for combobox option: {option.type}")
      
      if index_of_value is None or index_of_value >= widget.count() or index_of_value < 0:
        print("Cannot find value %s in combobox %s" % (new_value, option_name))
        index_of_value = 0
      
      widget.setCurrentIndex(index_of_value)
    elif isinstance(widget, QSpinBox):
      new_value = int(new_value)
      if new_value < widget.minimum() or new_value > widget.maximum():
        print("Value %s out of range for spinbox %s" % (new_value, option_name))
        new_value = self.default_options[option_name] # reset to default in case 0 is not default or in normal range

      widget.setValue(new_value)
    elif isinstance(widget, QListView):
      if not isinstance(new_value, list):
        new_value = self.default_options[option_name]
      
      if widget.model() is not None:
        model = widget.model()
        if isinstance(model, QSortFilterProxyModel):
          model = model.sourceModel()
        model.setStringList(new_value)
        model.sort(0)
    else:
      print("Option widget is invalid: %s" % option_name)
  
  def set_option_description(self, new_description):
    if new_description is None:
      self.ui.option_description.setText("(Hover over an option to see a description of what it does.)")
      self.ui.option_description.setStyleSheet("color: grey;")
    else:
      self.ui.option_description.setText(new_description)
      self.ui.option_description.setStyleSheet("")
  
  def get_all_options_from_widget_values(self):
    options_dict = {}
    for option in Options.all():
      options_dict[option.name] = self.get_option_value(option.name)
    options = Options(**options_dict)
    return options
  
  def ensure_valid_combination_of_options(self):
    items_to_filter_out = []
    should_enable_options = {}
    for option in Options.all():
      should_enable_options[option.name] = True
    
    options = self.get_all_options_from_widget_values()
    
    if not options.progression_dungeons:
      should_enable_options["required_bosses"] = False
    
    if options.sword_mode == SwordMode.SWORDLESS:
      items_to_filter_out += ["Hurricane Spin"]
    if options.sword_mode in [SwordMode.SWORDLESS, SwordMode.NO_STARTING_SWORD]:
      items_to_filter_out += 3 * ["Progressive Sword"]
    
    if not options.required_bosses:
      should_enable_options["num_required_bosses"] = False
      should_enable_options["prioritize_required_bosses"] = False
    
    if options.num_location_hints == 0:
      should_enable_options["prioritize_remote_hints"] = False
    
    dungeon_entrances_random = any([
      options.randomize_dungeon_entrances,
      options.randomize_miniboss_entrances,
      options.randomize_boss_entrances,
    ])
    non_dungeon_entrances_random = any([
      options.randomize_secret_cave_entrances,
      options.randomize_secret_cave_inner_entrances,
      options.randomize_fairy_fountain_entrances,
    ])
    if not (dungeon_entrances_random and non_dungeon_entrances_random):
      should_enable_options["mix_entrances"] = False
    
    self.filtered_rgear.setFilterStrings(items_to_filter_out)
    
    for item in items_to_filter_out:
      if item in options.randomized_gear:
        options.randomized_gear.remove(item)
      elif item in options.starting_gear:
        options.starting_gear.remove(item)
    options.randomized_gear += items_to_filter_out
    
    self.set_option_value("starting_gear", options.starting_gear)
    self.set_option_value("randomized_gear", options.randomized_gear)
    
    all_gear = self.get_option_value("starting_gear") + self.get_option_value("randomized_gear")
    
    if Counter(all_gear) != Counter(INVENTORY_ITEMS):
      print("Gear list invalid, resetting")
      for opt in ["randomized_gear", "starting_gear"]:
        self.set_option_value(opt, self.default_options[opt])
    
    for option in Options.all():
      if option.name == "custom_colors":
        continue
      widget = self.findChild(QWidget, option.name)
      label_for_option = self.findChild(QLabel, "label_for_" + option.name)
      if should_enable_options[option.name]:
        widget.setEnabled(True)
        if label_for_option:
          label_for_option.setEnabled(True)
      else:
        widget.setEnabled(False)
        if isinstance(widget, QAbstractButton):
          widget.setChecked(False)
        if label_for_option:
          label_for_option.setEnabled(False)
      
      if option.unbeatable and not IS_RUNNING_FROM_SOURCE:
        # Disable options that produce unbeatable seeds when not running from source.
        if self.get_option_value(option.name):
          self.set_option_value(option.name, False)
          self.update_settings()
      
      if option.hidden:
        # Hide certain options from the GUI (still accessible via settings.txt and permalinks).
        if self.get_option_value(option.name):
          widget.show()
        else:
          widget.hide()
  
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
    if self.randomizer_thread is not None:
      self.randomizer_thread.terminate()
    if not IS_RUNNING_FROM_SOURCE:
      # Need to wait for the update checker before exiting, or the program will crash when closing.
      self.update_checker_thread.quit()
      self.update_checker_thread.wait()
    event.accept()
  
  if TYPE_CHECKING:
    # Fake override for type checker because PySide6 doesn't use TypeVar.
    def findChild(self, type: Type[T], name: str = ..., options: Qt.FindChildOption = ...) -> T: ...

class ModelFilterOut(QSortFilterProxyModel):
  def __init__(self):
    super(ModelFilterOut, self).__init__()
    self.filter_strings = []
  
  def setFilterStrings(self, fstr):
    self.filter_strings = fstr
    self.invalidateFilter()
  
  def filterAcceptsRow(self, sourceRow, sourceParent):
    index0 = self.sourceModel().index(sourceRow, 0, sourceParent)
    data = self.sourceModel().data(index0, Qt.ItemDataRole.DisplayRole)
    num_occurrences = self.filter_strings.count(data)
    for i in range(sourceRow):
      cur_index = self.sourceModel().index(i, 0, sourceParent)
      cur_data = self.sourceModel().data(cur_index, Qt.ItemDataRole.DisplayRole)
      if cur_data == data:
        num_occurrences -= 1
    return num_occurrences <= 0

class RandomizerProgressDialog(QProgressDialog):
  def __init__(self, rando_window: WWRandomizerWindow, title, description):
    QProgressDialog.__init__(self)
    self.rando_window = rando_window
    self.setWindowTitle(title)
    self.setLabelText(description)
    self.setWindowModality(Qt.ApplicationModal)
    self.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowTitleHint)
    self.setFixedSize(self.size())
    self.setAutoReset(False)
    self.setCancelButton(None) # Disable cancellation via cancel button.
    self.show()
  
  def keyPressEvent(self, e: QKeyEvent):
    # Disable cancellation via escape key.
    if e.key() == Qt.Key.Key_Escape:
      e.ignore()
  
  def closeEvent(self, e: QCloseEvent):
    # Although we could disable cancellation via Alt+F4, this would not be good design as it would
    # prevent the user from escaping from a randomization that got stuck in a loop somehow.
    # Instead, we reroute the Alt+F4 press to close the entire randomizer window instead of just the
    # progress bar. The window will forcibly kill the randomization attempt before it closes.
    self.rando_window.close()

class RandomizerThread(QThread):
  update_progress = Signal(str, int)
  randomization_complete = Signal()
  randomization_failed = Signal(str)
  
  def __init__(self, randomizer, profiling=False):
    QThread.__init__(self)
    
    self.randomizer = randomizer
    self.profiling = profiling
  
  def run(self):
    if self.profiling:
      import cProfile, pstats
      profiler = cProfile.Profile()
      profiler.enable()
    
    try:
      for next_option_description, progress_completed in self.randomizer.randomize():
        self.update_progress.emit(next_option_description, progress_completed)
    except Exception as e:
      stack_trace = traceback.format_exc()
      error_message = "Randomization failed with error:\n" + str(e) + "\n\n" + stack_trace
      self.randomization_failed.emit(error_message)
      return
    
    if self.profiling:
      profiler.disable()
      with open("profileresults.txt", "w") as f:
        ps = pstats.Stats(profiler, stream=f).sort_stats("cumulative")
        ps.print_stats()
    
    self.randomization_complete.emit()

class UpdateCheckerThread(QThread):
  finished_checking_for_updates = Signal(str)
  
  def run(self):
    new_version = check_for_updates()
    self.finished_checking_for_updates.emit(new_version)

# Allows yaml to dump StrEnums as strings.
yaml_dumper.representer.add_multi_representer(
  StrEnum,
  lambda dumper, data: dumper.represent_scalar('tag:yaml.org,2002:str', str(data.value))
)
