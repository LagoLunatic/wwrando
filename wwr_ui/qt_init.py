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

def load_ui_file(ui_file_path: str):
  import re
  from io import BytesIO
  from qtpy.uic import loadUiType # loadUi doesn't seem to work, so use loadUiType instead.
  
  with open(ui_file_path, "r", encoding="utf-8") as f:
    ui_file_contents = f.read()
  
  # PyQt5 doesn't support enums and set values in the form "Qt::TextFormat::PlainText" and expects "Qt::PlainText" instead.
  # However, Qt Designer generates the form qualified with both namespaces as of Qt 6.
  # In order to support both, we use a regex hack to remove the second namespace from the .ui files before passing it to loadUiType.
  qt5_ui_file_contents = re.sub(r"(<(?:enum|set)>[^:<]+)::[^:<]+::([^:<]+</(?:enum|set)>)", "\\1::\\2", ui_file_contents)
  
  qt5_ui_file_contents_bytes_io = BytesIO(qt5_ui_file_contents.encode("utf-8"))
  form_class, base_class = loadUiType(qt5_ui_file_contents_bytes_io)
  
  return form_class
