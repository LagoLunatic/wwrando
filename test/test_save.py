import os
from wwrando import make_argparser
from randomizer import WWRandomizer
from options.wwrando_options import Options
from test_helpers import *

def rando_with_options(options) -> WWRandomizer:
  args = make_argparser().parse_args(args=["--nologs"])
  rando_kwargs = {
    "seed": "pytestseed",
    "clean_iso_path": os.environ["WW_GZLE01_STRIPPED_PATH"],
    "randomized_output_folder": os.environ["WW_RANDO_OUTPUT_DIR"],
    "options": options,
    "cmd_line_args": args,
  }
  os.makedirs(rando_kwargs["randomized_output_folder"], exist_ok=True)
  return WWRandomizer(**rando_kwargs)

def test_save_default_options():
  options = Options()
  rando = rando_with_options(options)
  rando.randomize_all()

def test_save_all_options():
  options = Options()
  enable_all_options(options)
  rando = rando_with_options(options)
  rando.randomize_all()
