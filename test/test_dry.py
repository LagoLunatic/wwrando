from wwrando import make_argparser
from randomizer import WWRandomizer
from options.wwrando_options import Options, SwordMode, EntranceMixMode, TrickDifficulty
from enum import StrEnum

def dry_rando_with_options(options) -> WWRandomizer:
  args = make_argparser().parse_args(args=["--dry", "--nologs"])
  rando_kwargs = {
    "seed": "pytestseed",
    "clean_iso_path": None,
    "randomized_output_folder": "./rando_output",
    "options": options,
    "cmd_line_args": args,
  }
  return WWRandomizer(**rando_kwargs)

def enable_all_progression_location_options(options: Options):
  options.progression_dungeons = True
  options.progression_great_fairies = True
  options.progression_puzzle_secret_caves = True
  options.progression_combat_secret_caves = True
  options.progression_short_sidequests = True
  options.progression_long_sidequests = True
  options.progression_spoils_trading = True
  options.progression_minigames = True
  options.progression_free_gifts = True
  options.progression_mail = True
  options.progression_platforms_rafts = True
  options.progression_submarines = True
  options.progression_eye_reef_chests = True
  options.progression_big_octos_gunboats = True
  options.progression_triforce_charts = True
  options.progression_treasure_charts = True
  options.progression_expensive_purchases = True
  options.progression_misc = True
  options.progression_tingle_chests = True
  options.progression_battlesquid = True
  options.progression_savage_labyrinth = True
  options.progression_island_puzzles = True
  options.progression_dungeon_secrets = True

def disable_all_progression_location_options(options: Options):
  options.progression_dungeons = False
  options.progression_great_fairies = False
  options.progression_puzzle_secret_caves = False
  options.progression_combat_secret_caves = False
  options.progression_short_sidequests = False
  options.progression_long_sidequests = False
  options.progression_spoils_trading = False
  options.progression_minigames = False
  options.progression_free_gifts = False
  options.progression_mail = False
  options.progression_platforms_rafts = False
  options.progression_submarines = False
  options.progression_eye_reef_chests = False
  options.progression_big_octos_gunboats = False
  options.progression_triforce_charts = False
  options.progression_treasure_charts = False
  options.progression_expensive_purchases = False
  options.progression_misc = False
  options.progression_tingle_chests = False
  options.progression_battlesquid = False
  options.progression_savage_labyrinth = False
  options.progression_island_puzzles = False
  options.progression_dungeon_secrets = False

def enable_all_options(options: Options):
  enable_all_progression_location_options(options)
  
  options.sword_mode = SwordMode.SWORDLESS
  options.keylunacy = True
  
  options.mix_entrances = EntranceMixMode.MIX_DUNGEONS
  options.randomize_dungeon_entrances = True
  options.randomize_secret_cave_entrances = True
  options.randomize_miniboss_entrances = True
  options.randomize_boss_entrances = True
  options.randomize_secret_cave_inner_entrances = True
  options.randomize_fairy_fountain_entrances = True
  
  options.randomize_enemy_palettes = True
  
  options.randomize_enemies = True
  
  options.randomize_charts = True
  
  options.randomize_starting_island = True
  
  options.required_bosses = True
  options.num_required_bosses = 4
  
  options.chest_type_matches_contents = True
  
  options.trap_chests = True
  
  options.fishmen_hints = True
  options.hoho_hints = True
  options.korl_hints = True
  options.num_path_hints = 15
  options.num_barren_hints = 15
  options.num_location_hints = 15
  options.num_item_hints = 15
  options.cryptic_hints = True
  options.prioritize_remote_hints = True
  
  options.do_not_generate_spoiler_log = False
  
  options.swift_sail = True
  options.instant_text_boxes = True
  options.reveal_full_sea_chart = True
  options.add_shortcut_warps_between_dungeons = True
  options.skip_rematch_bosses = True
  options.invert_camera_x_axis = True
  options.invert_sea_compass_x_axis = True
  options.remove_title_and_ending_videos = True
  options.remove_music = True
  
  # options.custom_player_model
  # options.player_in_casual_clothes
  # options.disable_custom_player_voice
  # options.disable_custom_player_items
  # options.custom_color_preset
  # options.custom_colors
  
  options.num_starting_triforce_shards = 4
  # options.randomized_gear
  # options.starting_gear
  options.starting_pohs = 3
  options.starting_hcs = 2
  options.num_extra_starting_items = 3
  
  # options.dry_run
  
  options.logic_obscurity = TrickDifficulty.VERY_HARD
  options.logic_precision = TrickDifficulty.VERY_HARD
  options.hero_mode = True

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
