
from zipfile import ZipFile

from randomizer import VERSION

base_name = "Wind Waker Randomizer " + VERSION

with ZipFile("./dist/%s.zip" % base_name, "w") as zip:
  zip.write("./dist/%s.exe" % base_name, arcname="%s.exe" % base_name)
  zip.write("README.txt")
