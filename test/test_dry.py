import os
import pytest
from wwrando import make_argparser
from randomizer import TooFewProgressionLocationsError, WWRandomizer
from options.wwrando_options import Options, TrickDifficulty
from enum import StrEnum
from test_helpers import *

def dry_rando_with_options(options) -> WWRandomizer:
  args = make_argparser().parse_args(args=["--dry"])
  rando_kwargs = {
    "seed": "pytestseed",
    "clean_iso_path": None,
    "randomized_output_folder": os.environ["WW_RANDO_OUTPUT_DIR"],
    "options": options,
    "cmd_line_args": args,
  }
  return WWRandomizer(**rando_kwargs)

def test_dry_default_options():
  options = Options()
  rando = dry_rando_with_options(options)
  rando.randomize_all()

def test_dry_all_options():
  options = Options()
  enable_all_options(options)
  rando = dry_rando_with_options(options)
  rando.randomize_all()

def test_tricks_precise_no_obscure():
  options = Options()
  enable_all_progression_location_options(options)
  options.logic_obscurity = TrickDifficulty.NONE
  options.logic_precision = TrickDifficulty.VERY_HARD
  rando = dry_rando_with_options(options)
  rando.randomize_all()

def test_tricks_obscure_no_precise():
  options = Options()
  enable_all_progression_location_options(options)
  options.logic_obscurity = TrickDifficulty.VERY_HARD
  options.logic_precision = TrickDifficulty.NONE
  rando = dry_rando_with_options(options)
  rando.randomize_all()

def test_entrance_rando_enables():
  options = Options()
  options.randomize_dungeon_entrances = True
  rando = dry_rando_with_options(options)
  assert rando.entrances.is_enabled()

def test_regression_entrance_inner_rando():
  # https://github.com/LagoLunatic/wwrando/pull/390
  
  options = Options()
  disable_all_progression_location_options(options)
  options.progression_dungeons = True
  options.progression_dungeon_secrets = True
  options.progression_free_gifts = True
  options.progression_misc = True
  
  options.randomize_secret_cave_inner_entrances = True
  
  options.randomize_boss_entrances = True
  options.required_bosses = True
  options.num_required_bosses = 3
  
  rando = dry_rando_with_options(options)
  rando.randomize_all()

def test_trick_logic_checks():
  options = Options()
  options.logic_obscurity = TrickDifficulty.HARD
  options.logic_precision = TrickDifficulty.NORMAL
  rando = dry_rando_with_options(options)
  assert rando.logic.check_requirement_met("Obscure 2")
  assert not rando.logic.check_requirement_met("Obscure 3")
  assert rando.logic.check_requirement_met("Precise 1")
  assert not rando.logic.check_requirement_met("Precise 2")

def test_parse_string_option_to_enum():
  options = Options()
  options.logic_precision = "Normal" # pyright: ignore [reportAttributeAccessIssue]
  rando = dry_rando_with_options(options)
  assert isinstance(rando.options.logic_precision, StrEnum)

def test_convert_options_to_dict_and_back():
  default_options = Options()
  orig_options = Options(progression_dungeons=False, num_required_bosses=2, logic_precision=TrickDifficulty.HARD)
  options_dict = orig_options.dict()
  converted_options = Options(**options_dict)
  assert converted_options == orig_options
  assert orig_options != default_options
  assert converted_options != default_options

def test_convert_options_to_permalink_and_back():
  default_options = Options()
  orig_options = Options(progression_dungeons=False, num_required_bosses=2, logic_precision=TrickDifficulty.HARD)
  orig_seed = "test"
  permalink = WWRandomizer.encode_permalink(orig_seed, orig_options)
  converted_seed, converted_options = WWRandomizer.decode_permalink(permalink)
  assert converted_seed == orig_seed
  assert converted_options == orig_options
  assert orig_options != default_options
  assert converted_options != default_options

def test_exclude_overworld_locations():
  locations_to_exclude = [
    "Windfall Island - 5 Rupee Auction",
    "Windfall Island - 40 Rupee Auction",
    "Windfall Island - 60 Rupee Auction",
    "Windfall Island - 80 Rupee Auction",
  ]
  
  options = Options()
  options.progression_minigames = True
  options.progression_expensive_purchases = True
  options.excluded_locations = locations_to_exclude
  rando = dry_rando_with_options(options)
  rando.randomize_all()
  progress_locations, non_progress_locations = rando.logic.get_progress_and_non_progress_locations()
  assert all(location not in progress_locations for location in locations_to_exclude)
  assert all(location in non_progress_locations for location in locations_to_exclude)

def test_exclude_dungeon_locations():
  locations_to_exclude = [
    "Earth Temple - Transparent Chest In Warp Pot Room",
    "Earth Temple - Behind Curtain In Warp Pot Room",
    "Earth Temple - Chest Behind Destructible Walls",
    "Earth Temple - Chest In Three Blocks Room",
    "Earth Temple - Chest Behind Statues",
    "Earth Temple - Stalfos Miniboss Room",
    "Earth Temple - Tingle Statue Chest",
    "Earth Temple - Kill All Floormasters in Foggy Room",
    "Earth Temple - Behind Curtain Next to Hammer Button",
    "Earth Temple - Chest in Third Crypt",
  ]
  
  options = Options()
  options.progression_dungeons = True
  options.progression_tingle_chests = True
  options.progression_dungeon_secrets = True
  options.keylunacy = False
  options.excluded_locations = locations_to_exclude
  rando = dry_rando_with_options(options)
  rando.randomize_all()
  progress_locations, non_progress_locations = rando.logic.get_progress_and_non_progress_locations()
  assert all(location not in progress_locations for location in locations_to_exclude)
  assert all(location in non_progress_locations for location in locations_to_exclude)

def test_exclude_secret_cave_locations():
  locations_to_exclude = [
    "Outset Island - Savage Labyrinth - Floor 50",
    "Stone Watcher Island - Cave",
    "Overlook Island - Cave",
    "Bomb Island - Cave",
  ]
  
  options = Options()
  options.progression_puzzle_secret_caves = True
  options.progression_combat_secret_caves = True
  options.progression_savage_labyrinth = True
  options.excluded_locations = locations_to_exclude
  rando = dry_rando_with_options(options)
  rando.randomize_all()
  progress_locations, non_progress_locations = rando.logic.get_progress_and_non_progress_locations()
  assert all(location not in progress_locations for location in locations_to_exclude)
  assert all(location in non_progress_locations for location in locations_to_exclude)

def test_exclude_required_boss_locations():
  locations_to_exclude = [
    "Dragon Roost Cavern - Gohma Heart Container",
    "Forbidden Woods - Kalle Demos Heart Container",
    "Tower of the Gods - Gohdan Heart Container",
    "Forsaken Fortress - Helmaroc King Heart Container",
    "Earth Temple - Jalhalla Heart Container",
    "Wind Temple - Molgera Heart Container",
  ]
  
  options = Options()
  options.progression_dungeons = True
  options.required_bosses = True
  options.num_required_bosses = 4
  options.excluded_locations = locations_to_exclude
  rando = dry_rando_with_options(options)
  rando.randomize_all()
  progress_locations, non_progress_locations = rando.logic.get_progress_and_non_progress_locations()
  assert all(location not in progress_locations for location in locations_to_exclude)
  assert all(location in non_progress_locations for location in locations_to_exclude)

def test_exclude_sunken_treasure_locations():
  locations_to_exclude = [
    "Forsaken Fortress Sector - Sunken Treasure",
    "Mother and Child Isles - Sunken Treasure",
    "Tingle Island - Sunken Treasure",
    "Tower of the Gods Sector - Sunken Treasure",
    "Bomb Island - Sunken Treasure",
    "Cliff Plateau Isles - Sunken Treasure",
    "Outset Island - Sunken Treasure",
  ]
  
  options = Options()
  options.progression_dungeons = False
  options.progression_triforce_charts = True
  options.progression_treasure_charts = True
  options.excluded_locations = locations_to_exclude
  rando = dry_rando_with_options(options)
  rando.randomize_all()
  progress_locations = rando.logic.filter_locations_for_progression(rando.logic.item_locations.keys())
  assert all(location not in progress_locations for location in locations_to_exclude)

def test_exclude_sunken_treasure_locations_with_randomized_charts():
  locations_to_exclude = [
    "Forsaken Fortress Sector - Sunken Treasure",
    "Mother and Child Isles - Sunken Treasure",
    "Tingle Island - Sunken Treasure",
    "Tower of the Gods Sector - Sunken Treasure",
    "Bomb Island - Sunken Treasure",
    "Cliff Plateau Isles - Sunken Treasure",
    "Outset Island - Sunken Treasure",
  ]
  
  options = Options()
  options.progression_triforce_charts = True
  options.progression_treasure_charts = True
  options.randomize_charts = True
  options.excluded_locations = locations_to_exclude
  rando = dry_rando_with_options(options)
  rando.randomize_all()
  progress_locations = rando.logic.filter_locations_for_progression(rando.logic.item_locations.keys())
  assert all(location not in progress_locations for location in locations_to_exclude)

def test_exclude_all_locations():
  options = Options()
  options.excluded_locations = options.progression_locations
  with pytest.raises(TooFewProgressionLocationsError):
    rando = dry_rando_with_options(options)

def test_exclude_insufficient_dungeon_locations():
  locations_to_exclude = [
    "Dragon Roost Cavern - First Room",
  ]
  
  options = Options()
  options.keylunacy = False
  options.excluded_locations = locations_to_exclude
  rando = dry_rando_with_options(options)
  
  with pytest.raises(Exception):
    rando.randomize_all()

def test_exclude_location_and_check_chest_type():
  locations_to_exclude = [
    "Tingle Island - Ankle - Reward for All Tingle Statues",
  ]
  items_to_check = [
    ("Dragon Tingle Statue", 0),
    ("Forbidden Tingle Statue", 0),
    ("Goddess Tingle Statue", 0),
    ("Earth Tingle Statue", 0),
    ("Wind Tingle Statue", 0),
  ]
  
  options = Options()
  options.progression_misc = True
  options.excluded_locations = locations_to_exclude
  rando = dry_rando_with_options(options)
  rando.randomize_all()
  assert all(rando.items.get_ctmc_chest_type_for_item(item) == chest_type for item, chest_type in items_to_check)

def test_exclude_location_and_check_hints():
  locations_to_exclude = [
    "Ganon's Tower - Maze Chest",
  ]
  
  options = Options()
  options.progression_dungeons = True
  options.korl_hints = True
  options.num_location_hints = 1
  options.prioritize_remote_hints = True
  options.excluded_locations = locations_to_exclude
  rando = dry_rando_with_options(options)
  rando.randomize_all()
  all_hints = [rando.hints.octo_fairy_hint]
  for hints_for_placement in rando.hints.hints_per_placement.values():
    all_hints += hints_for_placement
  assert all(hint.place not in locations_to_exclude for hint in all_hints)
