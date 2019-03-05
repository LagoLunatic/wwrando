
from zipfile import ZipFile

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

zip_name = base_zip_name.replace(" ", "_") + ".zip"

with ZipFile("./dist/" + zip_name, "w") as zip:
  zip.write("./dist/%s" % base_name_with_version, arcname="%s" % base_name)
  zip.write("README.md", arcname="README.txt")
  zip.write("./models/About Custom Models.txt", arcname="./models/About Custom Models.txt")
