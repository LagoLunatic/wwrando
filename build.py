
from zipfile import ZipFile

from randomizer import VERSION

base_name = "Wind Waker Randomizer " + VERSION
zip_name = base_name.replace(" ", "_") + ".zip"

with ZipFile("./dist/" + zip_name, "w") as zip:
  zip.write("./dist/%s.exe" % base_name, arcname="%s.exe" % base_name)
  zip.write("README.txt")
