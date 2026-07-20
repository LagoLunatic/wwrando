import os
import pytest

from wwrando import make_argparser
from randomizer import WWRandomizer
from options.wwrando_options import Options, DungeonItemShuffleMode
from test_helpers import disable_all_progression_location_options, enable_all_progression_location_options

ALL_MODES = list(DungeonItemShuffleMode)

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

@pytest.mark.parametrize("shuffle_small_keys", ALL_MODES)
@pytest.mark.parametrize("shuffle_big_keys", ALL_MODES)
def test_dungeon_item_shuffle(
  shuffle_small_keys: DungeonItemShuffleMode, shuffle_big_keys: DungeonItemShuffleMode
):
  options = Options()
  enable_all_progression_location_options(options)
  options.shuffle_small_keys = shuffle_small_keys
  options.shuffle_big_keys = shuffle_big_keys
  rando = dry_rando_with_options(options)
  rando.randomize_all()

@pytest.mark.thorough
@pytest.mark.parametrize("shuffle_small_keys", ALL_MODES)
@pytest.mark.parametrize("shuffle_big_keys", ALL_MODES)
def test_key_shuffle_with_required_bosses(
  shuffle_small_keys: DungeonItemShuffleMode, shuffle_big_keys: DungeonItemShuffleMode
):
  options = Options()
  enable_all_progression_location_options(options)
  options.shuffle_small_keys = shuffle_small_keys
  options.shuffle_big_keys = shuffle_big_keys
  options.required_bosses = True
  options.num_required_bosses = 4
  rando = dry_rando_with_options(options)
  rando.randomize_all()

@pytest.mark.thorough
@pytest.mark.parametrize("shuffle_small_keys", ALL_MODES)
@pytest.mark.parametrize("shuffle_big_keys", ALL_MODES)
def test_key_shuffle_with_minimum_required_bosses(
  shuffle_small_keys: DungeonItemShuffleMode, shuffle_big_keys: DungeonItemShuffleMode
):
  options = Options()
  enable_all_progression_location_options(options)
  options.shuffle_small_keys = shuffle_small_keys
  options.shuffle_big_keys = shuffle_big_keys
  options.required_bosses = True
  options.num_required_bosses = 1
  rando = dry_rando_with_options(options)
  rando.randomize_all()

@pytest.mark.thorough
@pytest.mark.parametrize("shuffle_small_keys", ALL_MODES)
@pytest.mark.parametrize("shuffle_big_keys", ALL_MODES)
def test_key_shuffle_with_dungeons_not_progression(
  shuffle_small_keys: DungeonItemShuffleMode, shuffle_big_keys: DungeonItemShuffleMode
):
  options = Options()
  enable_all_progression_location_options(options)
  options.progression_dungeons = False
  options.shuffle_small_keys = shuffle_small_keys
  options.shuffle_big_keys = shuffle_big_keys
  rando = dry_rando_with_options(options)
  rando.randomize_all()
