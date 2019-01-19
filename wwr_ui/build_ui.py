
from pyside2uic import compileUi
import glob
import os

for input_path in glob.glob('*.ui'):
  base_name = os.path.splitext(input_path)[0]
  output_path = "ui_%s.py" % base_name
  with open(output_path, "w") as output_file:
    compileUi(input_path, output_file)
