from wwrando import make_argparser
from randomizer import WWRandomizer
from options.wwrando_options import Options, SwordMode, EntranceMixMode, TrickDifficulty
from enum import StrEnum

def rando_with_options(options) -> WWRandomizer:
  args = make_argparser().parse_args(args=["--dry", "--nologs"])
  rando_kwargs = {
    "seed": "pytestseed",
    "clean_iso_path": None,
    "randomized_output_folder": "./rando_output",
    "options": options,
    "permalink": None,
    "cmd_line_args": args,
  }
  return WWRandomizer(**rando_kwargs)

def test_rando_default_options():
  options = Options()
  rando = rando_with_options(options)
  all(rando.randomize())

def test_rando_all_options():
  options = Options()
  
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
  
  # options.randomize_enemies = True # TODO: fails with swordless
  
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
  
  rando = rando_with_options(options)
  all(rando.randomize())

def test_entrance_rando_enables():
  options = Options()
  options.randomize_dungeon_entrances = True
  rando = rando_with_options(options)
  assert rando.entrances.is_enabled()

def test_trick_logic_checks():
  options = Options()
  options.logic_obscurity = TrickDifficulty.HARD
  options.logic_precision = TrickDifficulty.NORMAL
  rando = rando_with_options(options)
  assert rando.logic.check_requirement_met("Obscure 2")
  assert not rando.logic.check_requirement_met("Obscure 3")
  assert rando.logic.check_requirement_met("Precise 1")
  assert not rando.logic.check_requirement_met("Precise 2")

def test_parse_string_option_to_enum():
  options = Options()
  options.logic_precision = "Normal"
  rando = rando_with_options(options)
  assert isinstance(rando.options.logic_precision, StrEnum)
