import os

if "QT_API" not in os.environ:
  os.environ["QT_API"] = "pyside6"
