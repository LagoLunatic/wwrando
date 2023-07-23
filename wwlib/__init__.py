
import os
import glob

__all__ = []
for module_path in glob.glob(glob.escape(os.path.dirname(__file__)) + "/*.py"):
  module_name, file_ext = os.path.splitext(os.path.basename(module_path))
  assert file_ext == ".py"
  if module_name == "__init__":
    continue
  __all__.append(module_name)

# We need to import all the file types so that they register themselves with the RARC class.
from . import *
