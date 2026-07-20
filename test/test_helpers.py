from options.wwrando_options import Options, SwordMode, EntranceMixMode, TrickDifficulty

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
  options.prioritize_required_bosses = True
  
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
  options.hint_importance = True
  
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
