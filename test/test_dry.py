import os
from wwrando import make_argparser
from randomizer import WWRandomizer
from options.wwrando_options import Options, TrickDifficulty
from enum import StrEnum
from test_helpers import *

def dry_rando_with_options(options) -> WWRandomizer:
  args = make_argparser().parse_args(args=["--dry", "--nologs"])
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
  options.logic_precision = "Normal"
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
