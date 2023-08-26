#!/usr/bin/python3.11

import sys
sys.path.insert(0, "./gclib")

# Allow keyboard interrupts on the command line to instantly close the program.
import signal
def signal_handler(sig, frame):
  print("Interrupt")
  sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

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

def run_all_bulk_tests(rando_kwargs):
  assert getattr(sys, "gettrace", None) is None or sys.gettrace() is None, "Launched bulk test in debug mode (slow)"
  
  from tqdm import tqdm
  from multiprocessing import Pool
  from collections import Counter
  from randomizer import WWRandomizer
  
  # Catch any init errors early
  WWRandomizer(**rando_kwargs)
  
  with Pool(4) as p:
    first_seed = 0
    num_tests = 100
    func_args = [(i, rando_kwargs) for i in range(first_seed, first_seed+num_tests)]
    progress_bar = tqdm(p.imap(run_single_bulk_test, func_args), total=num_tests)
    
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
      else:
        failures_done += 1
      progress_bar.set_description(f"{failures_done}/{total_done} seeds failed")
    
    if counts:
      print(counts)

def run_no_ui(args):
  from randomizer import WWRandomizer
  import traceback
  from wwrando_paths import SETTINGS_PATH
  from tqdm import tqdm
  import yaml
  
  with open(SETTINGS_PATH) as f:
    options: dict = yaml.safe_load(f)
  
  rando_kwargs = {
    "seed": options.pop("seed"), # TODO sanitize seed
    "clean_iso_path": options.pop("clean_iso_path").strip(),
    "randomized_output_folder": options.pop("output_folder"),
    "options": options, # TODO filter out invalid options
    "permalink": None, # TODO encode this
    "cmd_line_args": args,
  }
  
  # TODO profiling
  # TODO autoseed option
  
  if "-bulk" in args:
    run_all_bulk_tests(rando_kwargs)
  else:
    rando = WWRandomizer(**rando_kwargs)
    try:
      all(rando.randomize())
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
  args = {}
  for arg in sys.argv[1:]:
    arg_parts = arg.split("=", 1)
    if len(arg_parts) == 1:
      args[arg_parts[0]] = None
    else:
      args[arg_parts[0]] = arg_parts[1]
  
  if "-bulk" in args:
    args["-noui"] = None
  
  if "-noui" in args:
    run_no_ui(args)
  else:
    run_with_ui(args)
