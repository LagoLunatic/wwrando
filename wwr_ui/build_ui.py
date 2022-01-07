
from subprocess import call
import glob
import os

for input_path in glob.glob('*.ui'):
  base_name = os.path.splitext(input_path)[0]
  output_path = "ui_%s.py" % base_name
  
  command = [
    "pyside6-uic",
    input_path,
    "-o", output_path
  ]
  result = call(command)
