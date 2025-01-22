#!/usr/bin/env python3

from subprocess import call
import glob
import os

ui_dir = os.path.dirname(__file__)
output_dir = os.path.join(ui_dir, "uic")
os.makedirs(output_dir, exist_ok=True)

for input_path in glob.glob(glob.escape(ui_dir) + "/*.ui"):
  base_name = os.path.splitext(os.path.basename(input_path))[0]
  
  command = [
    "pyside6-uic",
    input_path,
    "-o", os.path.join(output_dir, "ui_%s.py" % base_name)
  ]
  result = call(command)
