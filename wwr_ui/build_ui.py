#!/usr/bin/python3.11

from subprocess import call
import glob
import os

ui_dir = os.path.dirname(__file__)
for input_path in glob.glob(glob.escape(ui_dir) + "/*.ui"):
  base_name = os.path.splitext(os.path.basename(input_path))[0]
  
  command = [
    "pyside6-uic",
    input_path,
    "-o", ui_dir + "/uic/ui_%s.py" % base_name
  ]
  result = call(command)
