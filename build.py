
import os
import platform
import shutil

from randomizer import VERSION_WITHOUT_COMMIT

base_name = "Wind Waker Randomizer"
base_name_with_version = base_name + " " + VERSION_WITHOUT_COMMIT

import struct
if (struct.calcsize("P") * 8) == 64:
  base_name_with_version += "_64bit"
  base_zip_name = base_name_with_version
else:
  base_name_with_version += "_32bit"
  base_zip_name = base_name_with_version

exe_ext = ""
if platform.system() == "Windows":
  exe_ext = ".exe"
  platform_name = "win"
if platform.system() == "Darwin":
  exe_ext = ".app"
  platform_name = "mac"
if platform.system() == "Linux":
  platform_name = "linux"

zip_name = os.path.join("./dist/", base_zip_name.replace(" ", "_") + "_" + platform_name)

exe_path = "./dist/%s" % base_name_with_version + exe_ext
if not (os.path.isfile(exe_path) or os.path.isdir(exe_path)):
  raise Exception("Executable not found: %s" % exe_path)

if os.path.exists("./dist/release_archive") and os.path.isdir("./dist/release_archive"):
  shutil.rmtree("./dist/release_archive")

os.mkdir("./dist/release_archive")
os.mkdir("./dist/release_archive/models")
shutil.copyfile("README.md", "./dist/release_archive/README.txt")
shutil.copyfile("./models/About Custom Models.txt", "./dist/release_archive/models/About Custom Models.txt")

if platform.system() == "Darwin":
  shutil.copytree(exe_path, "./dist/release_archive/%s" % base_name + exe_ext)
else:
  shutil.copyfile(exe_path, "./dist/release_archive/%s" % base_name + exe_ext)

shutil.make_archive(zip_name, 'zip', "./dist/release_archive")
shutil.rmtree("./dist/release_archive")
