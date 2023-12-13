
def test_rando():
  from wwrando import make_argparser
  from randomizer import WWRandomizer
  args = make_argparser().parse_args(args=["--dry", "--nologs"])
  # TODO: remove this after the options refactor, this is a temporary hack to get it to run
  rando_kwargs = {
    "seed": "pytestseed",
    "clean_iso_path": None,
    "randomized_output_folder": "./rando_output",
    "options": {
      "progression_dungeons": True,
      "progression_puzzle_secret_caves": True,
      "randomize_dungeon_entrances": True,
      "mix_entrances": "Separate Dungeons From Caves & Fountains",
      "required_bosses": True,
      "num_required_bosses": 4,
      "randomize_enemies": True,
      "randomize_enemy_palettes": True,
      "starting_pohs": 0,
      "starting_hcs": 0,
      "fishmen_hints": False,
      "hoho_hints": False,
      "korl_hints": False,
      "num_path_hints": 0,
      "num_barren_hints": 0,
      "num_location_hints": 0,
      "num_item_hints": 0,
      "cryptic_hints": False,
      "prioritize_remote_hints": False,
      "do_not_generate_spoiler_log": False,
    },
    "permalink": None,
    "cmd_line_args": args,
  }
  rando = WWRandomizer(**rando_kwargs)
  all(rando.randomize())
