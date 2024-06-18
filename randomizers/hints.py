import os
from collections import Counter, deque
from enum import Enum
import math
import yaml

from logic.logic import Logic
from randomizers.base_randomizer import BaseRandomizer
from wwlib.dzx import DZx, ACTR, MULT
from wwrando_paths import DATA_PATH
import tweaks
from asm import patcher


class HintType(Enum):
  PATH = 0
  BARREN = 1
  ITEM = 2
  LOCATION = 3
  FIXED_LOCATION = 4


class ItemImportance(Enum):
  REQUIRED = 0
  POSSIBLY_REQUIRED = 1
  NOT_REQUIRED = 2


class Hint:
  def __init__(self, type: HintType, place, reward=None, importance=None):
    assert place is not None
    if type == HintType.BARREN: assert reward is None
    if type != HintType.BARREN: assert reward is not None
    self.type = type
    self.place = place
    self.reward = reward
    self.importance = importance
  
  def formatted_place(self, is_cryptic: bool):
    if not is_cryptic:
      return self.place
    
    match self.type:
      case HintType.PATH | HintType.BARREN | HintType.ITEM:
        return HintsRandomizer.cryptic_zone_hints[self.place]
      case HintType.LOCATION:
        return HintsRandomizer.location_hints[self.place]["Text"]
      case _:
        raise NotImplementedError
  
  def formatted_reward(self, is_cryptic: bool):
    match self.type:
      case HintType.PATH | HintType.BARREN:
        return self.reward
      case HintType.ITEM | HintType.FIXED_LOCATION:
        if is_cryptic:
          return HintsRandomizer.get_cryptic_item_hint(self.reward)
        else:
          return HintsRandomizer.get_formatted_item_name(self.reward)
      case HintType.LOCATION:
        # Never use cryptic item names for location hints.
        return HintsRandomizer.get_formatted_item_name(self.reward)
      case _:
        raise NotImplementedError
  
  def formatted_importance(self):
    match self.importance:
      case None:
        return ""
      case ItemImportance.REQUIRED:
        return "required"
      case ItemImportance.POSSIBLY_REQUIRED:
        return "possibly required"
      case ItemImportance.NOT_REQUIRED:
        return "not required"
      case _:
        raise NotImplementedError
  
  def __str__(self):
    return "<HINT: %s, (%s, %s, %s)>" % (
      self.type.name,
      self.formatted_place(False),
      self.formatted_reward(False),
      self.formatted_importance(),
    )
  
  def __repr__(self):
    return "Hint(%s, %s, %s, %s)" % (
      str(self.type),
      repr(self.place),
      repr(self.reward),
      repr(self.importance),
    )


class HintsRandomizer(BaseRandomizer):
  #region Constants
  
  # A dictionary mapping dungeon name to the dungeon boss.
  # The boss name is used as the path goal in the hint text.
  DUNGEON_NAME_TO_BOSS_NAME = {
    "Dragon Roost Cavern": "Gohma",
    "Forbidden Woods": "Kalle Demos",
    "Tower of the Gods": "Gohdan",
    "Forsaken Fortress": "Helmaroc King",
    "Earth Temple": "Jalhalla",
    "Wind Temple": "Molgera",
    "Hyrule": "Hyrule",
    "Ganon's Tower": "Ganondorf",
  }
  
  # A dictionary mapping dungeon name to the requirement name.
  # This dictionary is used when determining which items are on the path to a goal.
  DUNGEON_NAME_TO_REQUIREMENT_NAME = {
    "Dragon Roost Cavern": "Can Access Item Location \"Dragon Roost Cavern - Gohma Heart Container\"",
    "Forbidden Woods": "Can Access Item Location \"Forbidden Woods - Kalle Demos Heart Container\"",
    "Tower of the Gods": "Can Access Item Location \"Tower of the Gods - Gohdan Heart Container\"",
    "Forsaken Fortress": "Can Access Item Location \"Forsaken Fortress - Helmaroc King Heart Container\"",
    "Earth Temple": "Can Access Item Location \"Earth Temple - Jalhalla Heart Container\"",
    "Wind Temple": "Can Access Item Location \"Wind Temple - Molgera Heart Container\"",
    "Hyrule": "Can Access Hyrule",
    "Ganon's Tower": "Can Reach and Defeat Ganondorf",
  }
  
  HOHO_INDEX_TO_ISLAND_NUM = {
    0: 34,
    1: 14,
    2: 44, # On multiple layers
    3: 1,
    4: 5,
    5: 33,
    6: 3,
    7: 43,
    8: 31,
    9: 46,
  }
  
  #endregion
  
  
  cryptic_item_hints = None
  cryptic_zone_hints = None
  location_hints = None
  
  def __init__(self, rando):
    super().__init__(rando)
    self.path_logic = None
    self.path_logic_initial_state = None
    
    # Define instance variable shortcuts for hint distribution options.
    self.max_path_hints = self.options.num_path_hints
    self.max_barren_hints = self.options.num_barren_hints
    self.max_location_hints = self.options.num_location_hints
    self.max_item_hints = self.options.num_item_hints
    self.total_num_hints = self.max_path_hints + self.max_barren_hints + self.max_location_hints + self.max_item_hints
    
    self.cryptic_hints = self.options.cryptic_hints
    self.prioritize_remote_hints = self.options.prioritize_remote_hints
    self.hint_importance = self.options.hint_importance
    
    self.path_locations: set[str] = None
    self.barren_locations: set[str] = None
    
    self.floor_30_hint: Hint = None
    self.floor_50_hint: Hint = None
    self.octo_fairy_hint: Hint = None
    self.hints_per_placement: dict[str, list[Hint]] = {}
    self.island_to_fishman_hint: dict[int, Hint] = {}
    self.hoho_index_to_hints: dict[int, list[Hint]] = {}
    
    HintsRandomizer.load_hint_text_files()
    
    for item_name in self.logic.all_progress_items:
      if self.check_item_can_be_hinted_at(item_name):
        item_name = HintsRandomizer.get_hint_item_name(item_name)
        assert item_name in HintsRandomizer.cryptic_item_hints, f"Progress item is missing hint text: {item_name!r}"
    
    # Validate location names in location hints file.
    for location_name in self.location_hints:
      assert location_name in rando.logic.item_locations, f"Invalid location name in hints file: {location_name!r}"
    
    # Define a dictionary mapping charts to their sunken treasure.
    # This will be used to check whether or not the chart leads to a junk item. If so, the chart itself can be
    # considered junk.
    self.chart_name_to_sunken_treasure = {}
  
  def is_enabled(self) -> bool:
    return bool(self.rando.randomize_items)
  
  @property
  def progress_randomize_duration_weight(self) -> int:
    return 500
  
  @property
  def progress_save_duration_weight(self) -> int:
    return 50
  
  @property
  def progress_randomize_text(self) -> str:
    return "Generating hints..."
  
  @property
  def progress_save_text(self) -> str:
    return "Saving hints..."
  
  def _randomize(self):
    self.path_logic = Logic(self.rando)
    self.path_logic_initial_state = self.path_logic.save_simulated_playthrough_state()
    
    # Generate the hints that will be distributed over the hint placement options
    hints = self.generate_hints()
    
    self.floor_30_hint = self.generate_savage_labyrinth_hint("Outset Island - Savage Labyrinth - Floor 30")
    self.floor_50_hint = self.generate_savage_labyrinth_hint("Outset Island - Savage Labyrinth - Floor 50")
    
    if not any(self.check_item_can_be_hinted_at(item_name) for item_name in self.rando.all_randomized_progress_items):
      # If the player chose to start the game with every single progress item, there will be no way
      # to generate any hints. Therefore we leave all the hint location text as the vanilla text,
      # except Savage Labyrinth's hint tablet.
      return
    
    self.octo_fairy_hint = self.generate_octo_fairy_hint()
    
    variable_hint_placement_options = ("fishmen_hints", "hoho_hints", "korl_hints")
    self.hints_per_placement.clear()
    for option_name in variable_hint_placement_options:
      if self.options[option_name]:
        self.hints_per_placement[option_name] = []
    
    hint_placement_options = list(self.hints_per_placement.keys())
    if self.total_num_hints == 0 or len(hint_placement_options) == 0:
      return
    
    # If there are less hints than placement options, duplicate the hints so that all selected
    # placement options have at least one hint.
    duplicated_hints = []
    while len(hints) + len(duplicated_hints) < len(hint_placement_options):
      duplicated_hints += self.rng.sample(hints, len(hints))
    hints += duplicated_hints[:(len(hint_placement_options) - len(hints))]
    
    # Distribute the hints among the enabled hint placement options
    self.rng.shuffle(hint_placement_options)
    for i, hint in enumerate(hints):
      self.hints_per_placement[hint_placement_options[i % len(hint_placement_options)]].append(hint)
    
    if "fishmen_hints" in self.hints_per_placement:
      self.distribute_fishmen_hints(self.hints_per_placement["fishmen_hints"])
    if "hoho_hints" in self.hints_per_placement:
      self.distribute_hoho_hints(self.hints_per_placement["hoho_hints"])
  
  def distribute_fishmen_hints(self, hints: list[Hint]):
    assert hints
    
    islands = list(range(1, 49+1))
    self.rng.shuffle(islands)
    
    self.island_to_fishman_hint.clear()
    for fishman_hint_number, fishman_island_number in enumerate(islands):
      self.island_to_fishman_hint[fishman_island_number] = hints[fishman_hint_number % len(hints)]
  
  def distribute_hoho_hints(self, hints: list[Hint]):
    assert hints
    
    hohos = list(range(10))
    self.rng.shuffle(hohos)
    
    self.hoho_index_to_hints.clear()
    for i in range(len(hohos)):
      self.hoho_index_to_hints[i] = []
    
    # Distribute the hints to each Hoho.
    # We want each hint to be duplicated as few times as possible, while still ensuring all Hohos
    # give the same number of hints.
    hint_index = 0
    while hint_index < len(hints):
      for hoho_index in hohos:
        hint = hints[hint_index % len(hints)]
        self.hoho_index_to_hints[hoho_index].append(hint)
        hint_index += 1
    
  def _save(self):
    self.update_savage_labyrinth_hint_tablet(self.floor_30_hint, self.floor_50_hint, self.hint_importance)
    
    if not any(self.check_item_can_be_hinted_at(item_name) for item_name in self.rando.all_randomized_progress_items):
      # See above.
      return
    
    patcher.apply_patch(self.rando, "flexible_hint_locations")
    
    self.update_big_octo_great_fairy_item_name_hint(self.octo_fairy_hint, self.hint_importance)
    
    # Send the list of hints for each hint placement option to its respective distribution function.
    # Each hint placement option will handle how to place the hints in-game in their own way.
    for hint_placement in self.hints_per_placement:
      if hint_placement == "fishmen_hints":
        self.update_fishmen_hints()
      elif hint_placement == "hoho_hints":
        self.update_hoho_hints()
      elif hint_placement == "korl_hints":
        self.update_korl_hints(self.hints_per_placement["korl_hints"])
      else:
        print("Invalid hint placement option: %s" % hint_placement)
  
  def write_to_spoiler_log(self) -> str:
    rows = []
    
    for savage_hint in [self.floor_30_hint, self.floor_50_hint]:
      savage_hint_is_valid = self.check_item_can_be_hinted_at(savage_hint.reward)
      rows.append((savage_hint.place, savage_hint.reward if savage_hint_is_valid else "Nothing"))
    
    all_hints = [self.octo_fairy_hint]
    for hints_for_placement in self.hints_per_placement.values():
      all_hints += hints_for_placement
    
    for hint in all_hints:
      rows.append((hint.place, hint.reward or "Nothing"))
    
    spoiler_log = "Hints:\n"
    col_widths = tuple(max(len(x) for x in (row[i] for row in rows)) for i in range(2))
    for row in rows:
      spoiler_log += f"{row[0]:>{col_widths[0]}}: {row[1]}\n"
    
    spoiler_log += "\n\n\n"
    
    return spoiler_log
  
  
  #region Saving
  def update_savage_labyrinth_hint_tablet(self, floor_30_hint: Hint, floor_50_hint: Hint, importance: bool):
    # Update the tablet on the first floor of savage labyrinth to give hints as to the items inside the labyrinth.
    
    floor_30_is_valid = self.check_item_can_be_hinted_at(floor_30_hint.reward)
    floor_50_is_valid = self.check_item_can_be_hinted_at(floor_50_hint.reward)
    
    if importance:
      floor_30_item_importance = floor_30_hint.formatted_importance()
      if floor_30_hint.importance == ItemImportance.REQUIRED:
        floor_30_item_importance = " (\\{1A 06 FF 00 00 02}%s\\{1A 06 FF 00 00 00})" % floor_30_item_importance
      elif floor_30_hint.importance == ItemImportance.POSSIBLY_REQUIRED:
        floor_30_item_importance = " (\\{1A 06 FF 00 00 04}%s\\{1A 06 FF 00 00 00})" % floor_30_item_importance
      elif floor_30_hint.importance == ItemImportance.NOT_REQUIRED:
        floor_30_item_importance = " (\\{1A 06 FF 00 00 07}%s\\{1A 06 FF 00 00 00})" % floor_30_item_importance
      
      floor_50_item_importance = floor_50_hint.formatted_importance()
      if floor_50_hint.importance == ItemImportance.REQUIRED:
        floor_50_item_importance = " (\\{1A 06 FF 00 00 02}%s\\{1A 06 FF 00 00 00})" % floor_50_item_importance
      elif floor_50_hint.importance == ItemImportance.POSSIBLY_REQUIRED:
        floor_50_item_importance = " (\\{1A 06 FF 00 00 04}%s\\{1A 06 FF 00 00 00})" % floor_50_item_importance
      elif floor_50_hint.importance == ItemImportance.NOT_REQUIRED:
        floor_50_item_importance = " (\\{1A 06 FF 00 00 07}%s\\{1A 06 FF 00 00 00})" % floor_50_item_importance
    else:
      floor_30_item_importance = ""
      floor_50_item_importance = ""
    
    if floor_30_is_valid and floor_50_is_valid:
      hint = "\\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00}%s" % (floor_30_hint.formatted_reward(self.cryptic_hints), floor_30_item_importance)
      hint += " and "
      hint += "\\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00}%s" % (floor_50_hint.formatted_reward(self.cryptic_hints), floor_50_item_importance)
      hint += " await"
    elif floor_30_is_valid:
      hint = "\\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00}%s" % (floor_30_hint.formatted_reward(self.cryptic_hints), floor_30_item_importance)
      hint += " and "
      hint += "challenge"
      hint += " await"
    elif floor_50_is_valid:
      hint = "challenge"
      hint += " and "
      hint += "\\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00}%s" % (floor_50_hint.formatted_reward(self.cryptic_hints), floor_50_item_importance)
      hint += " await"
    else:
      hint = "challenge"
      hint += " awaits"
    
    msg = self.rando.bmg.messages_by_id[837]
    msg.string = "\\{1A 07 FF 00 01 00 96}\\{1A 06 FF 00 00 01}The Savage Labyrinth\n\\{1A 07 FF 00 01 00 64}\n\n\n"
    msg.string += "\\{1A 06 FF 00 00 00}Deep in the never-ending darkness, the way to %s." % hint
    msg.word_wrap_string(self.rando.bfn)
  
  def update_big_octo_great_fairy_item_name_hint(self, hint: Hint, importance: bool):
    # The Octo Great Fairy must hint at a progress item
    assert hint.importance is not None
    
    msg = self.rando.bmg.messages_by_id[12015]
    msg.string = "\\{1A 06 FF 00 00 05}In \\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 05}, you will find an item." % hint.formatted_place(self.cryptic_hints)
    msg.word_wrap_string(self.rando.bfn)
    
    msg = self.rando.bmg.messages_by_id[12016]
    reward = tweaks.upper_first_letter(hint.formatted_reward(self.cryptic_hints))
    if importance:
      copula = "is"
      if hint.reward in ["Power Bracelets", "Iron Boots", "Bombs"]:
        copula = "are"
      
      if hint.importance == ItemImportance.REQUIRED:
        item_importance = "\\{1A 06 FF 00 00 02}%s\\{1A 06 FF 00 00 05}" % hint.formatted_importance()
      elif hint.importance == ItemImportance.POSSIBLY_REQUIRED:
        item_importance = "\\{1A 06 FF 00 00 04}%s\\{1A 06 FF 00 00 05}" % hint.formatted_importance()
      elif hint.importance == ItemImportance.NOT_REQUIRED:
        item_importance = "\\{1A 06 FF 00 00 07}%s\\{1A 06 FF 00 00 05}" % hint.formatted_importance()
      
      msg.string = "\\{1A 06 FF 00 00 05}...\\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 05}, which %s %s in your quest." % (reward, copula, item_importance)
    else:
      msg.string = "\\{1A 06 FF 00 00 05}...\\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 05}, which may help you on your quest." % reward
    msg.word_wrap_string(self.rando.bfn)
    
    msg = self.rando.bmg.messages_by_id[12017]
    if importance and hint.importance == ItemImportance.NOT_REQUIRED:
      # If the item is not required and the player is told so, change the post-hint message to be more appropriate.
      msg.string = "\\{1A 06 FF 00 00 05}Though if you still desire such an item, you must journey to that place."
    else:
      msg.string = "\\{1A 06 FF 00 00 05}When you find you have need of such an item, you must journey to that place."
    msg.word_wrap_string(self.rando.bfn)
  
  def update_fishmen_hints(self):
    for fishman_island_number, hint in self.island_to_fishman_hint.items():
      hint_lines = []
      hint_lines.append(HintsRandomizer.get_formatted_hint_text(hint, self.cryptic_hints, self.hint_importance, prefix="I've heard from my sources that ", suffix=".", delay=60))
      
      if self.cryptic_hints and (hint.type == HintType.ITEM or hint.type == HintType.LOCATION):
        hint_lines.append("Could be worth a try checking that place out. If you know where it is, of course.")
      
        if self.options.instant_text_boxes:
          # If instant text mode is on, we need to reset the text speed to instant after the wait command messed it up.
          hint_lines[-1] = "\\{1A 05 00 00 01}" + hint_lines[-1]
      
      msg_id = 13026 + fishman_island_number
      msg = self.rando.bmg.messages_by_id[msg_id]
      msg.construct_string_from_parts(self.rando.bfn, hint_lines)

  def update_hoho_hints(self):
    for hoho_index, hints_for_hoho in self.hoho_index_to_hints.items():
      hint_lines = []
      for i, hint in enumerate(hints_for_hoho):
        # Determine the prefix and suffix for the hint
        hint_prefix = "\\{1A 05 01 01 03}Ho ho! To think that " if i == 0 else "and that "
        hint_suffix = "..." if i == len(hints_for_hoho) - 1 else ","
        
        hint_lines.append(HintsRandomizer.get_formatted_hint_text(hint, self.cryptic_hints, self.hint_importance, prefix=hint_prefix, suffix=hint_suffix))
        
        if self.options.instant_text_boxes and i > 0:
          # If instant text mode is on, we need to reset the text speed to instant after the wait command messed it up.
          hint_lines[-1] = "\\{1A 05 00 00 01}" + hint_lines[-1]
      
      msg_id = 14001 + hoho_index
      msg = self.rando.bmg.messages_by_id[msg_id]
      msg.construct_string_from_parts(self.rando.bfn, hint_lines)
      
      self.rotate_hoho_to_face_hint(hoho_index, hints_for_hoho)
    
  def rotate_hoho_to_face_hint(self, hoho_index: int, hints_for_hoho: list[Hint]):
    """Attempt to rotate the Hoho of a particular index to look towards the island he is hinting at.
    Will make him face the first hint in his list that corresponds to an island."""
    
    sea_dzs = self.rando.get_arc("files/res/Stage/sea/Stage.arc").get_file("stage.dzs", DZx)
    mults = sea_dzs.entries_by_type(MULT)
    
    island_num_to_look_towards = None
    for hint in hints_for_hoho:
      if hint.type in [HintType.PATH, HintType.BARREN, HintType.ITEM]:
        zone_name = hint.place
      elif hint.type == HintType.LOCATION:
        zone_name = self.rando.entrances.get_entrance_zone_for_item_location(hint.place)
      
      if zone_name == "Ganon's Tower":
        zone_name = "Tower of the Gods Sector"
      if zone_name in self.rando.island_name_to_number:
        island_num_to_look_towards = self.rando.island_name_to_number[zone_name]
        break
    
    if island_num_to_look_towards is None:
      # Some hints, such as mail, don't correspond to any particular island.
      # If all of this Hoho's hints are of that type, don't rotate him. Leave his vanilla rotation.
      return
    
    island_num = self.HOHO_INDEX_TO_ISLAND_NUM[hoho_index]
    island_dzr = self.rando.get_arc("files/res/Stage/sea/Room%d.arc" % island_num).get_file("room.dzr", DZx)
    island_actors = island_dzr.entries_by_type(ACTR)
    hoho_actors = [x for x in island_actors if x.name == "Ah"]
    assert len(hoho_actors) > 0
    
    dest_sector_mult = next(mult for mult in mults if mult.room_index == island_num_to_look_towards)
    
    for hoho_actor in hoho_actors:
      assert hoho_actor.which_hoho == hoho_index
      angle_rad = math.atan2(dest_sector_mult.x_pos - hoho_actor.x_pos, dest_sector_mult.z_pos - hoho_actor.z_pos)
      angle_u16 = int(angle_rad * (0x8000 / math.pi)) % 0x10000
      hoho_actor.y_rot = angle_u16
    
    island_dzr.save_changes()

  def update_korl_hints(self, hints: list[Hint]):
    assert hints
    
    hint_lines = []
    for i, hint in enumerate(hints):
      # Have no delay with KoRL text since he potentially has a lot of textboxes
      hint_prefix = "They say that " if i == 0 else "and that "
      hint_suffix = "." if i == len(hints) - 1 else ","
      hint_lines.append(HintsRandomizer.get_formatted_hint_text(hint, self.cryptic_hints, self.hint_importance, prefix=hint_prefix, suffix=hint_suffix, delay=0))
    
    for msg_id in (1502, 3443, 3444, 3445, 3446, 3447, 3448):
      msg = self.rando.bmg.messages_by_id[msg_id]
      msg.construct_string_from_parts(self.rando.bfn, hint_lines)
  #endregion
  
  
  #region Static methods
  @staticmethod
  def load_hint_text_files():
    if HintsRandomizer.cryptic_item_hints and HintsRandomizer.cryptic_zone_hints and HintsRandomizer.location_hints:
      return
    with open(os.path.join(DATA_PATH, "progress_item_hints.txt"), "r") as f:
      HintsRandomizer.cryptic_item_hints = yaml.safe_load(f)
    with open(os.path.join(DATA_PATH, "zone_name_hints.txt"), "r") as f:
      HintsRandomizer.cryptic_zone_hints = yaml.safe_load(f)
    with open(os.path.join(DATA_PATH, "location_hints.txt"), "r") as f:
      HintsRandomizer.location_hints = yaml.safe_load(f)
  
  @staticmethod
  def get_hint_item_name(item_name):
    if item_name.startswith("Triforce Chart"):
      return "Triforce Chart"
    if item_name.startswith("Triforce Shard"):
      return "Triforce Shard"
    if item_name.startswith("Treasure Chart"):
      return "Treasure Chart"
    if item_name.endswith("Tingle Statue"):
      return "Tingle Statue"
    if item_name.endswith("Small Key"):
      return "Small Key"
    if item_name.endswith("Big Key"):
      return "Big Key"
    return item_name
  
  @staticmethod
  def get_formatted_hint_text(hint: Hint, cryptic: bool, importance: bool, prefix="They say that ", suffix=".", delay=30):
    place = hint.formatted_place(cryptic)
    if place == "Mailbox":
      place = "the mail"
    elif place == "Tower of the Gods Sector":
      place = "the Tower of the Gods sector"
    elif place == "Forsaken Fortress Sector":
      place = "the Forsaken Fortress sector"
    
    reward = hint.formatted_reward(cryptic)
    
    if importance:
      item_importance = hint.formatted_importance()
      if hint.importance == ItemImportance.REQUIRED:
        item_importance = " (\\{1A 06 FF 00 00 02}%s\\{1A 06 FF 00 00 00})" % item_importance
      elif hint.importance == ItemImportance.POSSIBLY_REQUIRED:
        item_importance = " (\\{1A 06 FF 00 00 04}%s\\{1A 06 FF 00 00 00})" % item_importance
      elif hint.importance == ItemImportance.NOT_REQUIRED:
        item_importance = " (\\{1A 06 FF 00 00 07}%s\\{1A 06 FF 00 00 00})" % item_importance
    else:
      item_importance = ""
    
    if hint.type == HintType.PATH:
      place_preposition = "at"
      if place in ["the mail", "the Tower of the Gods sector", "the Forsaken Fortress sector"]:
        place_preposition = "in"
      hint_string = (
        "%san item found %s \\{1A 06 FF 00 00 05}%s\\{1A 06 FF 00 00 00} is on the path to \\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00}%s"
        % (prefix, place_preposition, place, reward, suffix)
      )
    elif hint.type == HintType.BARREN:
      verb = "visiting"
      if place == "the mail":
        verb = "checking"
      if place == "a location on the open seas":
        place = "locations on the open seas"
      hint_string = (
        "%s%s \\{1A 06 FF 00 00 03}%s\\{1A 06 FF 00 00 00} is a foolish choice%s"
        % (prefix, verb, place, suffix)
      )
    elif hint.type == HintType.LOCATION:
      hint_string = (
        "%s\\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00} rewards \\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00}%s%s"
        % (prefix, place, reward, item_importance, suffix)
      )
    elif hint.type == HintType.ITEM:
      copula = "is"
      if reward in ["Power Bracelets", "Iron Boots", "Bombs"]:
        copula = "are"
      hint_string = (
        "%s\\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00}%s %s located in \\{1A 06 FF 00 00 01}%s\\{1A 06 FF 00 00 00}%s"
        % (prefix, reward, item_importance, copula, place, suffix)
      )
    else:
      hint_string = ""
    
    # Add a wait command (delay) to prevent the player from skipping over the hint accidentally.
    delay = max(0, min(0xFFFF, delay)) # Clamp within valid range.
    if delay > 0:
      hint_string += "\\{1A 07 00 00 07 %02X %02X}" % (delay >> 8, delay & 0xFF)
    
    return hint_string
  
  @staticmethod
  def get_formatted_item_name(item_name):
    if item_name.endswith("Small Key"):
      short_dungeon_name = item_name.split(" Small Key")[0]
      dungeon_name = Logic.DUNGEON_NAMES[short_dungeon_name]
      item_name = "%s small key" % dungeon_name
    elif item_name.endswith("Big Key"):
      short_dungeon_name = item_name.split(" Big Key")[0]
      dungeon_name = Logic.DUNGEON_NAMES[short_dungeon_name]
      item_name = "%s Big Key" % dungeon_name
    elif item_name.endswith("Dungeon Map"):
      short_dungeon_name = item_name.split(" Dungeon Map")[0]
      dungeon_name = Logic.DUNGEON_NAMES[short_dungeon_name]
      item_name = "%s Dungeon Map" % dungeon_name
    elif item_name.endswith("Compass"):
      short_dungeon_name = item_name.split(" Compass")[0]
      dungeon_name = Logic.DUNGEON_NAMES[short_dungeon_name]
      item_name = "%s Compass" % dungeon_name
    
    item_name = tweaks.add_article_before_item_name(item_name)
    return item_name
  
  @staticmethod
  def get_cryptic_item_hint(item_name):
    item_name = HintsRandomizer.get_hint_item_name(item_name)
    return HintsRandomizer.cryptic_item_hints[item_name]
  #endregion
  
  
  #region Hint generation
  def check_location_required_for_paths(self, location_to_check, paths_to_check):
    # To check whether the location is required or not, we simulate a playthrough and remove the
    # item the player would receive at that location immediately after they receive it.
    # If the player can still fulfill the requirement despite not having this item, the location is
    # not required.
    
    # If the item is not a progress item, there's no way it's required.
    item_name = self.logic.done_item_locations[location_to_check]
    if item_name not in self.logic.all_progress_items:
      return {}
    
    # Reuse a single Logic instance over multiple calls to this function for performance reasons.
    self.path_logic.load_simulated_playthrough_state(self.path_logic_initial_state)
    previously_accessible_locations = []
    
    while self.path_logic.unplaced_progress_items:
      progress_items_in_this_sphere = {}
      
      accessible_locations = self.path_logic.get_accessible_remaining_locations(for_progression=False)
      locations_in_this_sphere = [
        loc for loc in accessible_locations
        if loc not in previously_accessible_locations
      ]
      if not locations_in_this_sphere:
        break
      
      
      if not self.options.keylunacy:
        # If the player gained access to any small keys, we need to give them the keys without counting that as a new sphere.
        newly_accessible_predetermined_item_locations = [
          loc for loc in locations_in_this_sphere
          if loc in self.logic.prerandomization_item_locations
        ]
        newly_accessible_small_key_locations = [
          loc for loc in newly_accessible_predetermined_item_locations
          if self.logic.prerandomization_item_locations[loc].endswith(" Small Key")
        ]
        if newly_accessible_small_key_locations:
          for small_key_location_name in newly_accessible_small_key_locations:
            item_name = self.logic.prerandomization_item_locations[small_key_location_name]
            assert item_name.endswith(" Small Key")
            
            self.path_logic.add_owned_item(item_name)
            # Remove small key from owned items if it was from the location we want to check
            if small_key_location_name == location_to_check:
              self.path_logic.remove_owned_item(item_name)
          
          previously_accessible_locations += newly_accessible_small_key_locations
          continue # Redo this loop iteration with the small key locations no longer being considered 'remaining'.
      
      
      # Hide duplicated progression items (e.g. Empty Bottles) when they are placed in non-progression locations to avoid confusion and inconsistency.
      locations_in_this_sphere = self.path_logic.filter_locations_for_progression(locations_in_this_sphere)
      
      for location_name in locations_in_this_sphere:
        item_name = self.logic.done_item_locations[location_name]
        if item_name in self.path_logic.all_progress_items:
          progress_items_in_this_sphere[location_name] = item_name
      
      for location_name, item_name in progress_items_in_this_sphere.items():
        self.path_logic.add_owned_item(item_name)
        # Remove item from owned items if it was from the location we want to check.
        if location_name == location_to_check:
          self.path_logic.remove_owned_item(item_name)
      
      previously_accessible_locations = accessible_locations
    
    requirements_met = {
      path_name: not self.path_logic.check_requirement_met(self.DUNGEON_NAME_TO_REQUIREMENT_NAME[path_name])
      for path_name in paths_to_check
    }
    return requirements_met
  
  def get_required_locations_for_paths(self):
    # Add all required bosses mode dungeons as paths, in addition to Hyrule and Ganon's Tower.
    dungeon_paths = self.rando.boss_reqs.required_dungeons.copy()
    non_dungeon_paths = ["Hyrule", "Ganon's Tower"]
    path_goals = dungeon_paths + non_dungeon_paths
    required_locations_for_paths = {goal: [] for goal in path_goals}
    
    # Determine which locations are required to beat the seed.
    # Items are implicitly referred to by their location to handle duplicate item names (i.e., progressive items and
    # small keys). Basically, we remove the item from that location and see if the seed is still beatable. If not, then
    # we consider the item as required.
    progress_locations, non_progress_locations = self.logic.get_progress_and_non_progress_locations()
    for location_name in progress_locations:
      item_name = self.logic.done_item_locations[location_name]
      
      # Ignore required bosses mode banned locations.
      if location_name in self.rando.boss_reqs.banned_locations:
        continue
      
      # Required locations always contain progress items by definition, so ignore nonprogress items.
      if item_name not in self.logic.all_progress_items:
        continue
      
      # Determine the item name for the given location.
      zone_name, specific_location_name = self.logic.split_location_name_by_zone(location_name)
      entrance_zone = self.rando.entrances.get_entrance_zone_for_item_location(location_name)
      item_tuple = (zone_name, entrance_zone, specific_location_name, item_name)
      
      # Check and record if the location is required for path goals.
      requirements_met = self.check_location_required_for_paths(location_name, path_goals)
      for goal_name, requirement_met in requirements_met.items():
        if requirement_met:
          required_locations_for_paths[goal_name].append(item_tuple)
      
      # Add items that are on paths to required bosses mode dungeons to the Hyrule and Ganon's Tower paths.
      for dungeon_path_name in dungeon_paths:
        for item_tuple in required_locations_for_paths[dungeon_path_name]:
          for non_dungeon_path_name in non_dungeon_paths:
            if item_tuple not in required_locations_for_paths[non_dungeon_path_name]:
              required_locations_for_paths[non_dungeon_path_name].append(item_tuple)
    
    return required_locations_for_paths
  
  def get_path_hint(self, unhinted_locations, hinted_locations, path_name):
    valid_path_hint = False
    while not valid_path_hint:
      if len(unhinted_locations) == 0:
        return None, None
      
      # Pick a location uniformly at random from the list of hintable locations.
      zone_name, entrance_zone, specific_location_name, item_name = self.rng.choice(unhinted_locations)
      hinted_location = "%s - %s" % (zone_name, specific_location_name)
      
      # Regardless of whether we use the location, remove that location from being hinted.
      unhinted_locations.remove((zone_name, entrance_zone, specific_location_name, item_name))
      
      # The location is a valid hint if it has not already been hinted at.
      if hinted_location not in hinted_locations:
        valid_path_hint = True
    
    # Record hinted zone, item, and path goal.
    if self.logic.is_dungeon_location(hinted_location):
      # If it's a dungeon, use the dungeon name.
      hint_zone = zone_name
    else:
      # Otherwise, use the entrance zone name.
      hint_zone = entrance_zone
    
    path_hint = Hint(HintType.PATH, hint_zone, self.DUNGEON_NAME_TO_BOSS_NAME[path_name])
    
    return path_hint, hinted_location
  
  
  def get_barren_zones(self, progress_locations, hinted_remote_locations):
    # Helper function to build a list of barren zones in this seed.
    # The list includes only zones which are allowed to be hinted at as barren.
    
    # To start, exclude locations in non required bosses mode dungeons from being considered as progress locations.
    progress_locations = set(progress_locations) - set(self.rando.boss_reqs.banned_locations)
    
    # Next, create a dictionary mapping all progress items to their randomized locations. The values in this dictionary
    # will be lists since an item can be in multiple locations if it is progressive or a small key.
    progress_items = {}
    for location_name in progress_locations:
      item_name = self.logic.done_item_locations[location_name]
      if item_name in self.rando.logic.all_progress_items:
        if item_name in progress_items:
          progress_items[item_name].append(location_name)
        else:
          progress_items[item_name] = [location_name]
    
    # Next, we build a list of items that may be used to beat the seed. These items include hard-required items, such as
    # Triforce shards, but also items that might be used. For example, if there is a choice between which wallet to get,
    # both will be included in this list. As another example, if there is a choice between getting Bombs or Power
    # Bracelets to beat the seed, both will be included in this list. We do this by going backward from the 'Can Reach
    # and Defeat Ganondorf" requirement and checking items needed to fulfill that requirement. We then use a queue to
    # check item requirements to get those items, and so on.
    self.path_logic.load_simulated_playthrough_state(self.path_logic_initial_state)
    items_needed = deque(self.path_logic.get_item_names_by_req_name("Can Reach and Defeat Ganondorf"))
    items_checked = []
    useful_locations = set()
    while len(items_needed) > 0:
      # Dequeue one item from the queue.
      item_name = items_needed.popleft()
      
      # Don't consider the same item more than once or items which are not in the list of randomized progress items.
      if item_name in items_checked or item_name not in progress_items:
        continue
      
      # Don't consider dungeon keys when keylunacy is not enabled.
      if self.logic.is_dungeon_item(item_name) and not self.options.keylunacy:
        continue
      
      items_checked.append(item_name)
      
      # Consider all instances of this item, even if those extra copies might not be required.
      item_locations = progress_items[item_name]
      for location_name in item_locations:
        requirement_name = "Can Access Item Location \"%s\"" % location_name
        other_items_needed = self.path_logic.get_item_names_by_req_name(requirement_name)
        items_needed.extend(other_items_needed)
      
      # The set of "useful locations" is the set of all locations which contain these "useful" items.
      useful_locations |= set(item_locations)
    
    # Subtracting the set of useful locations from the set of progress locations gives us our set of barren locations.
    self.barren_locations = set(progress_locations) - useful_locations
    
    # Since we hint at zones as barren, we next construct a set of zones which contain at least one useful item.
    zones_with_useful_locations = set()
    for location_name in sorted(useful_locations):
      zones_with_useful_locations.update(self.rando.entrances.get_all_zones_for_item_location(location_name))
    
    # Now, we do the same with barren locations, identifying which zones have barren locations.
    zones_with_barren_locations = set()
    for location_name in sorted(self.barren_locations):
      # Don't consider locations hinted through remote location hints, as those are explicity barren.
      if location_name in hinted_remote_locations:
        continue
      
      zones_with_barren_locations.update(self.rando.entrances.get_all_zones_for_item_location(location_name))
    
    # Finally, the difference between the zones with barren locations and the zones with useful locations gives us our
    # set of hintable barren zones.
    barren_zones = zones_with_barren_locations - zones_with_useful_locations
    
    # Return the list of barren zones sorted to maintain consistent ordering.
    return sorted(barren_zones)
  
  def get_barren_hint(self, unhinted_zones, zone_weights):
    if len(unhinted_zones) == 0:
      return None
    
    # Remove a barren zone at random from the list, using the weights provided.
    zone_name = self.rng.choices(unhinted_zones, weights=zone_weights)[0]
    unhinted_zones.remove(zone_name)
    
    barren_hint = Hint(HintType.BARREN, zone_name)
    
    return barren_hint
  
  
  def filter_out_hinted_barren_locations(self, hintable_locations, hinted_barren_zones):
    # Remove locations in hinted barren areas.
    new_hintable_locations = []
    barrens = [hint.place for hint in hinted_barren_zones]
    for location_name in hintable_locations:
      entrance_zones = self.rando.entrances.get_all_zones_for_item_location(location_name)
      if not any(entrance_zone in barrens for entrance_zone in entrance_zones):
        new_hintable_locations.append(location_name)
    
    return new_hintable_locations
  
  def check_item_can_be_hinted_at(self, item_name: str):
    # Don't hint at non-progress items.
    if item_name not in self.logic.all_progress_items:
      return False
    
    # Don't hint at dungeon keys when key-lunacy is not enabled.
    if self.logic.is_dungeon_item(item_name) and not self.options.keylunacy:
      return False
    
    # Don't hint at the existence of traps.
    if item_name.endswith(" Trap Chest"):
      return False
    
    return True
  
  def get_importance_for_location(self, location_name):
    if self.path_locations is None:
      raise Exception("Path locations have not yet been initialized.")
    if self.barren_locations is None:
      raise Exception("Barren locations have not yet been initialized.")
    
    item_name = self.logic.done_item_locations[location_name]
    if item_name not in self.logic.all_progress_items:
      return None
    
    if location_name in self.path_locations:
      return ItemImportance.REQUIRED
    elif location_name in self.barren_locations:
      return ItemImportance.NOT_REQUIRED
    else:
      return ItemImportance.POSSIBLY_REQUIRED
  
  def check_is_legal_item_hint(self, location_name, progress_locations, previously_hinted_locations):
    item_name = self.logic.done_item_locations[location_name]
    
    if not self.check_item_can_be_hinted_at(item_name):
      return False
    
    # Don't hint at item in non-progress locations.
    if location_name not in progress_locations:
      return False
    
    # Remove locations in required bosses mode banned dungeons.
    if location_name in self.rando.boss_reqs.banned_locations:
      return False
    
    # Remove locations for items that were previously hinted.
    if location_name in previously_hinted_locations:
      return False
    
    return True
  
  def get_legal_item_hints(self, progress_locations, hinted_barren_zones, previously_hinted_locations):
    # Helper function to build a list of locations which may be hinted as item hints in this seed.
    
    # Filter out locations which are invalid to be hinted at for item hints.
    hintable_locations = [
      loc for loc in self.logic.done_item_locations
      if self.check_is_legal_item_hint(loc, progress_locations, previously_hinted_locations)
    ]
    
    new_hintable_locations = self.filter_out_hinted_barren_locations(hintable_locations, hinted_barren_zones)
    
    return new_hintable_locations
  
  def get_item_hint(self, hintable_locations):
    if len(hintable_locations) == 0:
      return None, None
    
    # Pick a location at which to hint at random.
    location_name = self.rng.choice(hintable_locations)
    hintable_locations.remove(location_name)
    
    item_name = self.logic.done_item_locations[location_name]
    entrance_zone = self.rando.entrances.get_entrance_zone_for_item_location(location_name)
    
    item_importance = self.get_importance_for_location(location_name)
    
    item_hint = Hint(HintType.ITEM, entrance_zone, item_name, item_importance)
    
    return item_hint, location_name
  
  
  def get_legal_location_hints(self, progress_locations, hinted_barren_zones, previously_hinted_locations):
    # Helper function to build a list of locations which may be hinted as location hints in this seed.
    
    hintable_locations = [loc for loc in progress_locations if loc in self.location_hints]
    
    # Identify valid remote hints for this seed.
    remote_hintable_locations = [loc for loc in hintable_locations if self.location_hints[loc]["Type"] == "Remote"]
    # The remaining locations are potential standard location hints.
    hintable_locations = [loc for loc in hintable_locations if self.location_hints[loc]["Type"] == "Standard"]
    
    # If we're not prioritizing remote hints, consider them as standard location hints instead.
    if not self.prioritize_remote_hints:
      hintable_locations += remote_hintable_locations
      remote_hintable_locations = []
    
    # Remove locations in required bosses mode banned dungeons.
    hintable_locations = [loc for loc in hintable_locations if loc not in self.rando.boss_reqs.banned_locations]
    
    # Remove locations for items that were previously hinted.
    hintable_locations = [loc for loc in hintable_locations if loc not in previously_hinted_locations]
    
    # Don't hint at the existence of traps.
    hintable_locations = [
      loc for loc in hintable_locations
      if not self.logic.done_item_locations[loc].endswith(" Trap Chest")
    ]
    
    standard_hintable_locations = self.filter_out_hinted_barren_locations(hintable_locations, hinted_barren_zones)
    
    return remote_hintable_locations, standard_hintable_locations
  
  def get_location_hint(self, hintable_locations, ignore_importance=False):
    if len(hintable_locations) == 0:
      return None
    
    # Pick a location at which to hint at random.
    location_name = self.rng.choice(hintable_locations)
    hintable_locations.remove(location_name)
    
    item_name = self.logic.done_item_locations[location_name]
    if ignore_importance:
      item_importance = None
    else:
      item_importance = self.get_importance_for_location(location_name)
    
    location_hint = Hint(HintType.LOCATION, location_name, item_name, item_importance)
    
    return location_hint, location_name
  
  
  def generate_octo_fairy_hint(self):
    # Get an item hint for a random progress item.
    # Note that this hint is completely independant of all other hints.
    progress_locations, non_progress_locations = self.logic.get_progress_and_non_progress_locations()
    hintable_locations = self.get_legal_item_hints(progress_locations, [], [])
    if "Two-Eye Reef - Big Octo Great Fairy" in hintable_locations:
      # We don't want this Great Fairy to hint at her own item.
      hintable_locations.remove("Two-Eye Reef - Big Octo Great Fairy")
    if len(hintable_locations) == 0:
      raise Exception("No valid items to give hints for")
    
    item_hint, location_name = self.get_item_hint(hintable_locations)
    
    return item_hint
  
  def generate_savage_labyrinth_hint(self, location_name):
    # Get an item hint for one of the two checks in Savage Labyrinth.
    item_name = self.logic.done_item_locations[location_name]
    item_importance = self.get_importance_for_location(location_name)
    hint = Hint(HintType.FIXED_LOCATION, location_name, item_name, item_importance)
    return hint
  
  def generate_hints(self):
    previously_hinted_locations = []
    
    # Create a mapping for chart name -> sunken treasure
    self.chart_name_to_sunken_treasure = self.rando.charts.build_chart_to_sunken_treasure_location_mapping()
    
    # Build of list of progress locations for this seed.
    progress_locations, non_progress_locations = self.logic.get_progress_and_non_progress_locations()
    
    # Get all entrance zones for progress locations in this seed.
    all_world_areas = []
    for location_name in progress_locations:
      if self.logic.is_dungeon_location(location_name):
        zone_name, specific_location_name = self.logic.split_location_name_by_zone(location_name)
        all_world_areas.append(zone_name)
      else:
        all_world_areas.append(self.rando.entrances.get_entrance_zone_for_item_location(location_name))
    
    # Get a counter for the number of locations associated with each zone, used for weighing.
    location_counter = Counter(all_world_areas)
    
    # Generate remote location hints.
    # First, we generate remote location hints, up to the total amount that can be generated based on the settings, and
    # based on the number of location hints the user wishes to generate. We need to generate these first before any
    # other hint type.
    hinted_remote_locations = []
    if self.prioritize_remote_hints:
      remote_hintable_locations, standard_hintable_locations = self.get_legal_location_hints(progress_locations, [], [])
      while len(remote_hintable_locations) > 0 and len(hinted_remote_locations) < self.max_location_hints:
        # Temporarily ignore item importance until later.
        location_hint, location_name = self.get_location_hint(remote_hintable_locations, ignore_importance=True)
        
        hinted_remote_locations.append(location_hint)
        previously_hinted_locations.append(location_name)
    
    # Determine which locations are required for each path goal.
    # Items are implicitly referred to by their location to handle duplicate item names (i.e., progressive items and
    # small keys). Basically, we remove the item from that location and see if the path goal is still achievable. If
    # not, then we consider the item as required.
    required_locations_for_paths = {}
    required_locations_for_paths = self.get_required_locations_for_paths()
    
    # Flatten the list of path locations for reference for hint importance
    self.path_locations = set()
    for goal_name, path_locations in required_locations_for_paths.items():
      for zone_name, entrance_zone, specific_location_name, item_name in path_locations:
        self.path_locations.add("%s - %s" % (zone_name, specific_location_name))
    
    # Filter out the locations of dungeon keys as being path when key-lunacy is disabled
    if not self.options.keylunacy:
      for dungeon_name, dungeon_paths in required_locations_for_paths.items():
        required_locations_for_paths[dungeon_name] = [item_tuple for item_tuple in dungeon_paths if not item_tuple[3].endswith(" Key")]
    
    # Generate path hints.
    # We hint at max `self.max_path_hints` zones at random.
    # We start by hinting each of the required bosses mode dungeons once.
    # After that, we repeatedly select a path goal at random and use that to form another hint. Zones are weighted by
    # the number of required locations at that zone. The more required locations, the more likely that zone will be
    # chosen.
    dungeon_paths = self.rando.boss_reqs.required_dungeons.copy()
    self.rng.shuffle(dungeon_paths)
    
    # If required bosses mode is on, then remove items that are hinted on the path to a required dungeon from paths to
    # Hyrule and Ganondorf. This way, the path to the required dungeon takes hint priority for that item.
    if self.max_path_hints > 0:
      for dungeon_name in dungeon_paths:
        for item_tuple in required_locations_for_paths[dungeon_name]:
          if item_tuple in required_locations_for_paths["Hyrule"]:
            required_locations_for_paths["Hyrule"].remove(item_tuple)
          if item_tuple in required_locations_for_paths["Ganon's Tower"]:
            required_locations_for_paths["Ganon's Tower"].remove(item_tuple)
    
    # Likewise, remove items that are hinted on the path to Hyrule from the path to Ganondorf. This way, the path to
    # Hyrule takes hint priority over the path to Ganondorf for that item.
    if self.max_path_hints > 0:
      for item_tuple in required_locations_for_paths["Hyrule"]:
        if item_tuple in required_locations_for_paths["Ganon's Tower"]:
          required_locations_for_paths["Ganon's Tower"].remove(item_tuple)
    
    # Generate a path hint for each required bosses mode dungeon.
    hinted_path_zones = []
    for dungeon_name in dungeon_paths:
      # If there are no hintable locations for path hints, skip to barren hints.
      if len(required_locations_for_paths) == 0:
        break
      
      if len(hinted_path_zones) < self.max_path_hints:
        path_hint, location_name = self.get_path_hint(required_locations_for_paths[dungeon_name], previously_hinted_locations, dungeon_name)
        
        # Unable to generate a path hint for the dungeon, so remove path goal and move on to the next.
        if path_hint is None:
          del required_locations_for_paths[dungeon_name]
          continue
        
        # Remove locations that have already been hinted.
        if location_name not in previously_hinted_locations:
          hinted_path_zones.append(path_hint)
          previously_hinted_locations.append(location_name)
    
    while len(required_locations_for_paths) > 0 and len(hinted_path_zones) < self.max_path_hints:
      path_name = self.rng.choice(list(required_locations_for_paths.keys()))
      path_hint, location_name = self.get_path_hint(required_locations_for_paths[path_name], previously_hinted_locations, path_name)
      
      # Unable to generate a path hint for the dungeon, so remove path goal.
      if path_hint is None:
        del required_locations_for_paths[path_name]
      else:
        # Remove locations that have already been hinted.
        if location_name not in previously_hinted_locations:
          hinted_path_zones.append(path_hint)
          previously_hinted_locations.append(location_name)
    
    # Generate barren hints.
    # We select at most `self.max_barren_hints` zones at random to hint as barren. Barren zones are weighted by the
    # square root of the number of locations at that zone.
    unhinted_barren_zones = self.get_barren_zones(progress_locations, [hint.place for hint in hinted_remote_locations])
    hinted_barren_zones = []
    while len(unhinted_barren_zones) > 0 and len(hinted_barren_zones) < self.max_barren_hints:
      # Weight each barren zone by the square root of the number of locations there.
      zone_weights = [math.sqrt(location_counter[zone]) for zone in unhinted_barren_zones]
      if sum(zone_weights) == 0:
        break
      
      barren_hint = self.get_barren_hint(unhinted_barren_zones, zone_weights)
      if barren_hint is not None:
        hinted_barren_zones.append(barren_hint)
    
    # Update remote location hints with importance information
    for hint in hinted_remote_locations:
      hint.importance = self.get_importance_for_location(hint.place)
    
    # Generate item hints.
    # We select at most `self.max_item_hints` items at random to hint at. We do not want to hint at items already
    # covered by the path hints, nor do we want to hint at items in barren-hinted locations.
    hintable_locations = self.get_legal_item_hints(progress_locations, hinted_barren_zones, previously_hinted_locations)
    
    hinted_item_locations = []
    while len(hintable_locations) > 0 and len(hinted_item_locations) < self.max_item_hints:
      item_hint, location_name = self.get_item_hint(hintable_locations)
      
      hinted_item_locations.append(item_hint)
      previously_hinted_locations.append(location_name)
    
    # Generate standard location hints.
    # We try to generate location hints until we get to `self.total_num_hints` total hints, but if there are not enough
    # valid hintable locations, then we have no choice but to return less than the desired amount of hints.
    remote_hintable_locations, standard_hintable_locations = self.get_legal_location_hints(progress_locations, hinted_barren_zones, previously_hinted_locations)
    hinted_standard_locations = []
    remaining_hints_desired = self.total_num_hints - len(hinted_path_zones) - len(hinted_barren_zones) - len(hinted_item_locations) - len(hinted_remote_locations)
    
    # Fill out the remaining hint slots with standard location hints.
    while len(standard_hintable_locations) > 0 and remaining_hints_desired > 0:
      remaining_hints_desired -= 1
      location_hint, location_name = self.get_location_hint(standard_hintable_locations)
      
      hinted_standard_locations.append(location_hint)
      previously_hinted_locations.append(location_name)
    
    return hinted_path_zones + hinted_barren_zones + hinted_item_locations + hinted_remote_locations + hinted_standard_locations
  #endregion
