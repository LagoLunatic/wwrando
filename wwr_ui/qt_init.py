import os

if "QT_API" not in os.environ:
  try:
    import PySide6 # pyright: ignore [reportMissingImports]
    os.environ["QT_API"] = "pyside6"
  except ImportError:
    pass

if "QT_API" not in os.environ:
  try:
    import PyQt6 # pyright: ignore [reportMissingImports]
    os.environ["QT_API"] = "pyqt6"
  except ImportError:
    pass

if "QT_API" not in os.environ:
  try:
    import PySide2 # pyright: ignore [reportMissingImports]
    os.environ["QT_API"] = "pyside2"
  except ImportError:
    pass

if "QT_API" not in os.environ:
  try:
    import PyQt5 # pyright: ignore [reportMissingImports]
    os.environ["QT_API"] = "pyqt5"
  except ImportError:
    pass
