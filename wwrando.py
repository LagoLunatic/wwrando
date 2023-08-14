#!/usr/bin/python3.11

import sys
sys.path.insert(0, "./gclib")

# Allow keyboard interrupts on the command line to instantly close the program.
import signal
def signal_handler(sig, frame):
  print("Interrupt")
  sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

def run_bulk_test(bulk_test_size, rando_kwargs):
  from randomizer import WWRandomizer
  import traceback
  
  failures_done = 0
  total_done = 0
  for i in range(bulk_test_size):
    temp_seed = str(i)
    rando_kwargs["seed"] = temp_seed
    rando = None
    try:
      rando = WWRandomizer(**rando_kwargs)
      all(rando.randomize())
    except Exception as e:
      stack_trace = traceback.format_exc()
      error_message = f"Error on seed {temp_seed}:\n{e}\n\n{stack_trace}"
      print(error_message)
      if rando is not None:
        rando.write_error_log(error_message)
      failures_done += 1
    total_done += 1
    yield(failures_done, total_done)

def run_no_ui(args):
  from randomizer import WWRandomizer
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
  
  if "-bulk" in args:
    bulk_test_size = 100
    progress_bar = tqdm(run_bulk_test(bulk_test_size, rando_kwargs), total=bulk_test_size)
    for failures_done, total_done in progress_bar:
      progress_bar.set_description(f"{failures_done}/{total_done} seeds failed")
  else:
    rando = WWRandomizer(**rando_kwargs)
    with tqdm(total=rando.get_max_progress_length()) as progress_bar:
      prev_val = 0
      for next_option_description, options_finished in rando.randomize():
        progress_bar.update(options_finished-prev_val)
        prev_val = options_finished
        progress_bar.set_description(next_option_description)

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
