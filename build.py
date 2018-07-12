
from zipfile import ZipFile

from randomizer import VERSION

base_name = "Wind Waker Randomizer"
base_name_with_version = base_name + " " + VERSION
zip_name = base_name_with_version.replace(" ", "_") + ".zip"

with ZipFile("./dist/" + zip_name, "w") as zip:
  zip.write("./dist/%s.exe" % base_name_with_version, arcname="%s.exe" % base_name)
  zip.write("README.txt")
