#!/usr/bin/python3

import sys
sys.path.insert(0, "./gclib")

# Allow keyboard interrupts on the command line to instantly close the program.
import signal
def signal_handler(sig, frame):
  print("Interrupt")
  sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

import argparse
from version import VERSION

def parse_spawn(str_value):
  try:
    stage, room, spawn = str_value.split(",")
    room = int(room)
    spawn = int(spawn)
  except ValueError:
    raise argparse.ArgumentTypeError("Invalid test room spawn format. Should be in the format: StageName,RoomNum,SpawnID (e.g. 'kindan,5,0')")
  return {"stage": stage, "room": room, "spawn": spawn}

def make_argparser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(
    add_help=False,
    formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=52), # Force extra space for all option names.
  )
  
  parser.add_argument(
    '-h', '--help', action='help',
    help="Show this help message and exit.",
  )
  parser.add_argument(
    '-v', '--version', action='version', version=VERSION,
    help="Show program's version number and exit.",
  )
  parser.add_argument(
    '-n', '--noui', action='store_true',
    help="Skip loading GUI, randomize immediately with saved settings.",
  )
  parser.add_argument(
    '-d', '--dry', action='store_true',
    help="Randomize in-memory and write logs only, do not read or write any ISOs.",
  )
  parser.add_argument(
    '-a', '--autoseed', action='store_true',
    help="Use a random seed name instead of the last seed from saved settings.",
  )
  parser.add_argument(
    '-s', '--seed', type=str,
    help="Use the specified seed name instead of the last seed from saved settings.",
  )
  parser.add_argument(
    '-p', '--permalink', type=str,
    help="Use the seed and options from the specified permalink instead of the last saved settings.",
  )
  parser.add_argument(
    '-b', '--bulk', type=int, nargs='?', const=100, metavar="SEEDS",
    help="Randomize a large number of seeds (default 100) and save their logs only.",
  )
  parser.add_argument(
    '-t', '--test', type=parse_spawn, metavar="SPAWN",
    help="Playtest a specific player spawn. Format: StageName,RoomNum,SpawnID",
  )
  parser.add_argument(
    '-e', '--exportfolder', action='store_true',
    help="Save output game files to an extracted folder instead of a GCM ISO file.",
  )
  parser.add_argument(
    '-m', '--mapselect', action='store_true',
    help="Enable debug map select ingame by pressing Y, Z, and D-pad down.",
  )
  parser.add_argument(
    '-r', '--heap', action='store_true',
    help="Enable display of memory heaps onscreen during gameplay for debugging low RAM.",
  )
  parser.add_argument(
    '-i', '--noitemrando', action='store_true',
    help="Preserve vanilla item locations. This speeds up randomization. Source only.",
  )
  parser.add_argument(
    '--nologs', action='store_true',
    help="Skip writing all log files, including error logs.",
  )
  parser.add_argument(
    '--disassemble', action='store_true',
    help="Dump and disassemble all of the vanilla game's code, adding symbol names as comments.",
  )
  parser.add_argument(
    '--printflags', action='store_true',
    help="Print all documented flags used in the vanilla game to text files.",
  )
  parser.add_argument(
    '--stagesearch', type=str, metavar="SEARCHFUNC",
    help="Runs a custom dev script for searching the game's files.",
  )
  parser.add_argument(
    '--profile', action='store_true',
    help="Profile the randomization code and store the results to a file.",
  )
  
  return parser

def run_single_bulk_test(args):
  temp_seed, rando_kwargs = args
  
  from randomizer import WWRandomizer
  import traceback
  
  temp_seed = str(temp_seed)
  rando_kwargs["seed"] = temp_seed
  rando = None
  try:
    rando = WWRandomizer(**rando_kwargs)
    all(rando.randomize())
    return True, rando
  except Exception as e:
    stack_trace = traceback.format_exc()
    error_message = f"Error on seed {temp_seed}:\n{e}\n\n{stack_trace}"
    print()
    print(error_message)
    if rando is not None:
      rando.write_error_log(error_message)
    return False, rando

def run_all_bulk_tests(rando_kwargs, num_seeds):
  assert getattr(sys, "gettrace", None) is None or sys.gettrace() is None, "Launched bulk test in debug mode (slow)"
  
  from tqdm import tqdm
  from multiprocessing import Pool
  from collections import Counter
  from randomizer import WWRandomizer
  
  # Catch any init errors early
  WWRandomizer(**rando_kwargs)
  
  with Pool(4) as p:
    first_seed = 0
    func_args = [(i, rando_kwargs) for i in range(first_seed, first_seed+num_seeds)]
    progress_bar = tqdm(p.imap(run_single_bulk_test, func_args), total=num_seeds)
    
    total_done = 0
    failures_done = 0
    counts = Counter()
    for success, rando in progress_bar:
      total_done += 1
      if success:
        # Optionally put some code here to count something across all seeds to detect biased distributions.
        pass
      
        # for path in rando.entrances.nested_entrance_paths:
        #   counts[len(path)] += 1
        
        # for i in range(3, max(len(p) for p in rando.entrances.nested_entrance_paths)+1):
        #   counts[i] += 1
        
        # for path in rando.entrances.nested_entrance_paths:
        #   if path[-1].endswith(" Boss Arena"):
        #     counts[path[-2].split(" ")[0]] += 1
        
        # progress_locs = rando.logic.filter_locations_for_progression(rando.logic.item_locations)
        # for loc, item in rando.logic.done_item_locations.items():
        #   if not item.endswith(" Trap Chest"):
        #     continue
        #   if loc in progress_locs:
        #     counts["progress"] += 1
        #   else:
        #     counts["nonprogress"] += 1
      else:
        failures_done += 1
      progress_bar.set_description(f"{failures_done}/{total_done} seeds failed")
    
    if counts:
      print(counts)

def run_no_ui(args):
  from randomizer import WWRandomizer
  from options.wwrando_options import Options
  from seedgen import seedgen
  import traceback
  from wwrando_paths import SETTINGS_PATH, IS_RUNNING_FROM_SOURCE
  from tqdm import tqdm
  import yaml
  import cProfile, pstats
  
  options = Options()
  with open(SETTINGS_PATH) as f:
    settings: dict = yaml.safe_load(f)
    for option_name, option_value in settings.items():
      if option_name not in options.by_name:
        continue
      options[option_name] = option_value
  
  seed = settings["seed"]
  
  if args.permalink:
    seed, options = WWRandomizer.decode_permalink(args.permalink, options)
  
  if args.seed:
    seed = args.seed
  
  rando_kwargs = {
    "seed": seed,
    "clean_iso_path": settings["clean_iso_path"].strip(),
    "randomized_output_folder": settings["output_folder"],
    "options": options, # TODO filter out invalid options
    "cmd_line_args": args,
  }
  
  if args.autoseed:
    rando_kwargs["seed"] = seedgen.make_random_seed_name()
  
  if args.profile:
    profiler = cProfile.Profile()
    profiler.enable()
  
  if args.bulk:
    run_all_bulk_tests(rando_kwargs, args.bulk)
  elif args.stagesearch and IS_RUNNING_FROM_SOURCE:
    from wwlib import stage_searcher
    rando = WWRandomizer(**rando_kwargs)
    getattr(stage_searcher, args.stagesearch)(rando)
  else:
    rando = WWRandomizer(**rando_kwargs)
    try:
      all(rando.randomize())
      if rando.dry_run:
        print("Done (dry)")
      else:
        print("Done")
      # with tqdm(total=rando.get_max_progress_length()) as progress_bar:
      #   prev_val = 0
      #   for next_option_description, options_finished in rando.randomize():
      #     progress_bar.update(options_finished-prev_val)
      #     prev_val = options_finished
      #     progress_bar.set_description(next_option_description)
    except Exception as e:
      stack_trace = traceback.format_exc()
      error_message = f"Error on seed {rando_kwargs['seed']}:\n{e}\n\n{stack_trace}"
      if rando is not None:
        rando.write_error_log(error_message)
      raise e
  
  if args.profile:
    profiler.disable()
    profiler.dump_stats("profileresults.prof")
    with open("profileresults.txt", "w") as f:
      ps = pstats.Stats(profiler, stream=f).sort_stats("cumulative")
      ps.print_stats()

def try_fix_taskbar_icon():
  from wwrando_paths import IS_RUNNING_FROM_SOURCE
  if not IS_RUNNING_FROM_SOURCE:
    return
  
  # Setting the app user model ID is necessary for Windows to display a custom taskbar icon when running the randomizer from source.
  import ctypes
  app_id = "LagoLunatic.WindWakerRandomizer"
  try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
  except AttributeError:
    # Versions of Windows before Windows 7 don't support SetCurrentProcessExplicitAppUserModelID, so just swallow the error.
    pass

def run_with_ui(args):
  from PySide6.QtWidgets import QApplication
  from PySide6.QtCore import QTimer
  from wwr_ui.randomizer_window import WWRandomizerWindow

  try_fix_taskbar_icon()
  
  qApp = QApplication(sys.argv)

  # Have a timer updated frequently so keyboard interrupts always work.
  # 499 milliseconds seems to be the maximum value that works here, but use 100 to be safe.
  timer = QTimer()
  timer.start(100)
  timer.timeout.connect(lambda: None)

  window = WWRandomizerWindow(cmd_line_args=args)
  sys.exit(qApp.exec())

if __name__ == "__main__":
  args = make_argparser().parse_args()
  
  if args.bulk or args.stagesearch or args.printflags:
    args.noui = True
  
  if args.noui:
    run_no_ui(args)
  else:
    run_with_ui(args)
