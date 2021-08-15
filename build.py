
import os
import platform
import shutil

from randomizer import VERSION_WITHOUT_COMMIT

base_name = "Wind Waker Randomizer"
base_name_with_version = base_name + " " + VERSION_WITHOUT_COMMIT

import struct
if (struct.calcsize("P") * 8) == 64:
  bitness_suffix = "_64bit"
else:
  bitness_suffix = "_32bit"

exe_ext = ""
if platform.system() == "Windows":
  exe_ext = ".exe"
  platform_name = "win"
if platform.system() == "Darwin":
  exe_ext = ".app"
  platform_name = "mac"
if platform.system() == "Linux":
  platform_name = "linux"

exe_path = os.path.join(".", "dist", base_name_with_version + bitness_suffix + exe_ext)
if not (os.path.isfile(exe_path) or os.path.isdir(exe_path)):
  raise Exception("Executable not found: %s" % exe_path)

release_archive_path = os.path.join(".", "dist", "release_archive" + bitness_suffix)

if os.path.exists(release_archive_path) and os.path.isdir(release_archive_path):
  shutil.rmtree(release_archive_path)

os.mkdir(release_archive_path)
shutil.copyfile("README.md", os.path.join(release_archive_path, "README.txt"))

if platform.system() == "Darwin":
  shutil.copytree(exe_path, os.path.join(release_archive_path, base_name + exe_ext))
  shutil.copyfile(os.path.join(".", "models", "About Custom Models.txt"), os.path.join(release_archive_path, "About Custom Models.txt"))
else:
  os.mkdir(os.path.join(release_archive_path, "models"))
  shutil.copyfile(exe_path, os.path.join(release_archive_path, base_name + exe_ext))
  shutil.copyfile(os.path.join(".", "models", "About Custom Models.txt"), os.path.join(release_archive_path, "models", "About Custom Models.txt"))
